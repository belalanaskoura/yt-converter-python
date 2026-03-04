"""
yt_dlp_worker.py — Python sidecar for the Tauri YouTube downloader.

Communication protocol (newline-delimited JSON):
  stdin  ← {"action": "download", "url": "...", "format": "mp3", "quality": "192", "output_dir": "..."}
           {"action": "cancel"}
  stdout → {"type": "progress", "percent": 45.2, "speed": "1.2 MB/s"}
           {"type": "finished"}
           {"type": "complete", "filepath": "...", "title": "..."}
           {"type": "error", "message": "..."}
"""

import json
import sys
import threading
import time
from pathlib import Path

import yt_dlp

_cancel_flag = False
_first_stream_done = False  # True after first stream finishes; suppresses second-stream progress for video
# No client restriction — let yt-dlp auto-select the best working client.
# Hard-coding a specific client (android, ios, etc.) breaks whenever YouTube
# changes authentication requirements; yt-dlp's auto-selection handles this.
_AUDIO_EXTRACTOR_ARGS = {}


def emit(obj: dict):
    """Write a JSON event to stdout (flushed immediately)."""
    print(json.dumps(obj), flush=True)


def progress_hook(d: dict):
    global _first_stream_done
    if _cancel_flag:
        raise Exception("Download cancelled by user")

    if d["status"] == "downloading" and not _first_stream_done:
        try:
            percent = None
            downloaded_bytes = d.get("downloaded_bytes", 0)
            total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate", 0)

            if total_bytes:
                percent = (downloaded_bytes / total_bytes) * 100
            elif d.get("fragment_count"):
                percent = (d.get("fragment_index", 0) / d["fragment_count"]) * 100
            elif "_percent_str" in d:
                percent = float(d["_percent_str"].strip().replace("%", ""))

            bps = d.get("speed")
            if bps and bps >= 1_048_576:
                speed_str = f"{bps / 1_048_576:.1f} MB/s"
            elif bps and bps >= 1024:
                speed_str = f"{bps / 1024:.1f} KB/s"
            elif bps:
                speed_str = f"{bps:.0f} B/s"
            else:
                speed_str = ""

            emit({"type": "progress", "percent": round(percent, 1) if percent is not None else None, "speed": speed_str})
        except Exception:
            emit({"type": "progress", "percent": None, "speed": ""})

    elif d["status"] == "finished" and not _first_stream_done:
        # Mark first stream done — video has a second audio stream that would
        # otherwise reset progress to 0 and look like a duplicate download.
        _first_stream_done = True
        emit({"type": "finished"})


_COMMON_OPTS = {
    # Suppress yt-dlp's own stdout output so only our JSON lines appear there.
    # yt-dlp errors still come through via the progress_hook exception path.
    "quiet": True,
    "noprogress": True,
    # Download up to 16 fragments in parallel — YouTube uses DASH/HLS which
    # delivers video/audio as many small fragments; sequential download is slow.
    "concurrent_fragment_downloads": 16,
    # Download in 10 MB chunks instead of the default small chunks — reduces
    # per-request overhead and saturates bandwidth more effectively.
    "http_chunk_size": 10485760,
    # Increase timeouts and retries to handle slow/flaky connections.
    "socket_timeout": 60,
    "retries": 10,
    "fragment_retries": 10,
}


def _audio_opts(codec: str, quality: str | None, output_dir: str) -> dict:
    pp = {"key": "FFmpegExtractAudio", "preferredcodec": codec}
    if quality:
        pp["preferredquality"] = quality
    return {
        **_COMMON_OPTS,
        "format": "bestaudio/best",
        "postprocessors": [pp],
        "outtmpl": str(Path(output_dir) / "%(title)s.%(ext)s"),
        "progress_hooks": [progress_hook],
        **_AUDIO_EXTRACTOR_ARGS,
    }


def _video_opts(fmt: str, quality: str, output_dir: str) -> dict:
    quality_map = {
        "360p":       "bestvideo[height=360]+bestaudio/bestvideo[height<=360]+bestaudio/best",
        "480p":       "bestvideo[height=480]+bestaudio/bestvideo[height<=480]+bestaudio/best",
        "720p":       "bestvideo[height=720]+bestaudio/bestvideo[height<=720]+bestaudio/best",
        "1080p":      "bestvideo[height=1080]+bestaudio/bestvideo[height<=1080]+bestaudio/best",
        "1440p":      "bestvideo[height=1440]+bestaudio/bestvideo[height<=1440]+bestaudio/best",
        "2160p (4K)": "bestvideo[height=2160]+bestaudio/bestvideo[height>=1440]+bestaudio/bestvideo+bestaudio/best",
        "Best":       "bestvideo+bestaudio/best",
    }
    return {
        **_COMMON_OPTS,
        "format": quality_map.get(quality, quality_map["720p"]),
        "merge_output_format": fmt.lower(),
        "outtmpl": str(Path(output_dir) / "%(title)s.%(ext)s"),
        "progress_hooks": [progress_hook],
    }


def _stdin_cancel_watcher():
    """Background thread: watches for {"action":"cancel"} on stdin."""
    global _cancel_flag
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            if msg.get("action") == "cancel":
                _cancel_flag = True
        except Exception:
            pass


def run_download(cmd: dict):
    global _cancel_flag, _first_stream_done
    _cancel_flag = False
    _first_stream_done = False

    url = cmd.get("url", "").strip()
    fmt = cmd.get("format", "mp3").lower()
    quality = cmd.get("quality", "192")
    output_dir = cmd.get("output_dir", str(Path.home() / "Downloads"))

    if not url or not url.startswith(("http://", "https://")):
        emit({"type": "error", "message": "Invalid URL"})
        return

    if fmt == "mp3":
        ydl_opts = _audio_opts("mp3", quality, output_dir)
    elif fmt == "m4a":
        ydl_opts = _audio_opts("m4a", quality, output_dir)
    elif fmt == "wav":
        ydl_opts = _audio_opts("wav", None, output_dir)
    else:
        ydl_opts = _video_opts(fmt, quality, output_dir)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "Unknown") if info else "Unknown"
            thumbnail = info.get("thumbnail", "") if info else ""

        if not _cancel_flag:
            out_path = Path(output_dir)
            files = sorted(out_path.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True)
            filepath = str(files[0]) if files else ""
            emit({"type": "complete", "filepath": filepath, "title": title, "thumbnail": thumbnail})

    except Exception as e:
        err = str(e)
        if _cancel_flag:
            emit({"type": "cancelled"})
        else:
            emit({"type": "error", "message": err})


def main():
    # Start cancel-watcher thread only after we read the initial command
    # (so stdin isn't consumed by both threads at once).
    # Read the first line as the download command.
    first_line = sys.stdin.readline().strip()
    if not first_line:
        return

    try:
        cmd = json.loads(first_line)
    except Exception:
        emit({"type": "error", "message": "Invalid JSON command"})
        return

    if cmd.get("action") != "download":
        emit({"type": "error", "message": f"Unknown action: {cmd.get('action')}"})
        return

    # Start cancel watcher in background
    t = threading.Thread(target=_stdin_cancel_watcher, daemon=True)
    t.start()

    run_download(cmd)


if __name__ == "__main__":
    main()
