
import json
import os
import subprocess
import customtkinter as ctk
import yt_dlp
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

CONFIG_FILE = Path(__file__).parent / "config.json"


class YouTubeConverterGUI:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("YouTube Downloader")
        self.window.geometry("520x560")
        self.window.resizable(False, False)

        ctk.set_appearance_mode("dark")

        self.output_dir = Path("downloads")
        self._load_config()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.downloading = False
        self.cancel_download = False
        self._final_filepath = None

        self.setup_ui()

    # ── Config persistence ───────────────────────────────────────────────────

    def _load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE) as f:
                    data = json.load(f)
                saved = Path(data.get("output_dir", ""))
                if saved.is_dir():
                    self.output_dir = saved
            except Exception:
                pass

    def _save_config(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump({"output_dir": str(self.output_dir)}, f)
        except Exception:
            pass

    # ── UI setup ─────────────────────────────────────────────────────────────

    def setup_ui(self):
        # Header
        header = ctk.CTkFrame(self.window, fg_color="#282828", corner_radius=0)
        header.pack(fill="x")

        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(pady=18)

        title_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        title_frame.pack()

        ctk.CTkLabel(
            title_frame,
            text="▶",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#FF0000",
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            title_frame,
            text="YouTube Downloader",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#FFFFFF",
        ).pack(side="left")

        # Main content
        content = ctk.CTkFrame(self.window, fg_color="#181818")
        content.pack(fill="both", expand=True)

        inner = ctk.CTkFrame(content, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24, pady=24)

        # URL row
        ctk.CTkLabel(
            inner,
            text="Video URL",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#AAAAAA",
            anchor="w",
        ).pack(anchor="w", pady=(0, 6))

        url_row = ctk.CTkFrame(inner, fg_color="transparent")
        url_row.pack(fill="x", pady=(0, 20))

        self.url_entry = ctk.CTkEntry(
            url_row,
            placeholder_text="Paste YouTube link here...",
            height=40,
            border_width=1,
            border_color="#303030",
            fg_color="#212121",
            text_color="#FFFFFF",
            placeholder_text_color="#717171",
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            url_row,
            text="Paste",
            width=64,
            height=40,
            fg_color="#303030",
            hover_color="#404040",
            text_color="#FFFFFF",
            command=self._paste_url,
            corner_radius=6,
        ).pack(side="right")

        # Type / Format / Quality row
        options_row = ctk.CTkFrame(inner, fg_color="transparent")
        options_row.pack(fill="x", pady=(0, 20))

        for col, (label, attr, values, default, cmd) in enumerate([
            ("Type",    "type_menu",    ["Audio", "Video"],                    "Audio",   self.update_format_options),
            ("Format",  "format_menu",  ["MP3", "M4A", "WAV"],                 "MP3",     self.update_quality_options),
            ("Quality", "quality_menu", ["128 kbps", "192 kbps", "256 kbps", "320 kbps"], "192 kbps", None),
        ]):
            section = ctk.CTkFrame(options_row, fg_color="transparent")
            padx = (0, 6) if col == 0 else (6, 6) if col == 1 else (6, 0)
            section.pack(side="left", fill="both", expand=True, padx=padx)

            ctk.CTkLabel(
                section,
                text=label,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#AAAAAA",
                anchor="w",
            ).pack(anchor="w", pady=(0, 6))

            var = ctk.StringVar(value=default)
            setattr(self, f"{attr.replace('_menu', '_var')}", var)
            menu = ctk.CTkOptionMenu(
                section,
                variable=var,
                values=values,
                fg_color="#212121",
                button_color="#303030",
                button_hover_color="#404040",
                dropdown_fg_color="#212121",
                dropdown_hover_color="#303030",
                text_color="#FFFFFF",
                command=cmd,
            )
            menu.pack(fill="x")
            setattr(self, attr, menu)

        # Save location
        ctk.CTkLabel(
            inner,
            text="Save Location",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#AAAAAA",
            anchor="w",
        ).pack(anchor="w", pady=(0, 6))

        location_frame = ctk.CTkFrame(
            inner, fg_color="#212121", border_width=1, border_color="#303030"
        )
        location_frame.pack(fill="x", pady=(0, 20))

        location_inner = ctk.CTkFrame(location_frame, fg_color="transparent")
        location_inner.pack(fill="x", padx=12, pady=10)

        self.dir_label = ctk.CTkLabel(
            location_inner,
            text=f"📁 {self.output_dir.name}",
            font=ctk.CTkFont(size=12),
            text_color="#AAAAAA",
            anchor="w",
        )
        self.dir_label.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            location_inner,
            text="Open",
            width=60,
            height=28,
            fg_color="#303030",
            hover_color="#404040",
            text_color="#FFFFFF",
            command=self._open_output_dir,
            corner_radius=4,
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            location_inner,
            text="Change",
            width=70,
            height=28,
            fg_color="#303030",
            hover_color="#404040",
            text_color="#FFFFFF",
            command=self.select_directory,
            corner_radius=4,
        ).pack(side="right")

        # Progress
        self.progress_bar = ctk.CTkProgressBar(
            inner, progress_color="#FF0000", fg_color="#303030"
        )
        self.progress_bar.pack(fill="x", pady=(0, 8))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            inner,
            text="Ready to download",
            font=ctk.CTkFont(size=12),
            text_color="#AAAAAA",
        )
        self.status_label.pack(pady=(0, 20))

        # Action buttons
        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack()

        self.download_btn = ctk.CTkButton(
            btn_row,
            text="Download",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
            width=200,
            fg_color="#FF0000",
            hover_color="#CC0000",
            text_color="#FFFFFF",
            command=self.start_download,
            corner_radius=22,
        )
        self.download_btn.pack(side="left", padx=(0, 10))

        self.stop_btn = ctk.CTkButton(
            btn_row,
            text="Cancel",
            font=ctk.CTkFont(size=14),
            height=44,
            width=100,
            fg_color="#303030",
            hover_color="#404040",
            text_color="#FFFFFF",
            command=self.stop_download,
            state="disabled",
            corner_radius=22,
        )
        self.stop_btn.pack(side="left")

    # ── Dropdown helpers ─────────────────────────────────────────────────────

    def update_format_options(self, choice=None):
        if self.type_var.get() == "Audio":
            self.format_menu.configure(values=["MP3", "M4A", "WAV"])
            self.format_var.set("MP3")
        else:
            self.format_menu.configure(values=["MP4", "WEBM", "MKV"])
            self.format_var.set("MP4")
        self.update_quality_options()

    def update_quality_options(self, choice=None):
        fmt = self.format_var.get()
        if fmt in ("MP3", "M4A"):
            self.quality_menu.configure(
                values=["128 kbps", "192 kbps", "256 kbps", "320 kbps"]
            )
            self.quality_var.set("192 kbps")
        elif fmt == "WAV":
            self.quality_menu.configure(values=["Lossless"])
            self.quality_var.set("Lossless")
        elif fmt in ("MP4", "WEBM", "MKV"):
            self.quality_menu.configure(
                values=["360p", "480p", "720p", "1080p", "1440p", "2160p (4K)", "Best"]
            )
            self.quality_var.set("720p")

    # ── UX actions ───────────────────────────────────────────────────────────

    def _paste_url(self):
        try:
            text = self.window.clipboard_get().strip()
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, text)
        except Exception:
            pass

    def _open_output_dir(self):
        path = str(self.output_dir)
        if os.name == "nt":
            os.startfile(path)
        elif os.uname().sysname == "Darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])

    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir = Path(directory)
            self.dir_label.configure(text=f"📁 {self.output_dir.name}")
            self._save_config()

    # ── yt-dlp opts builders ─────────────────────────────────────────────────

    # Use the android client to avoid JS-runtime requirement and YouTube's
    # SABR streaming restriction that causes 403 errors with web clients.
    # android client: bypasses JS requirement and SABR restriction — ideal for audio
    # Video uses yt-dlp's default client selection (no restriction) so it can
    # fall back across clients automatically as YouTube changes requirements.
    _AUDIO_EXTRACTOR_ARGS = {"extractor_args": {"youtube": {"player_client": ["android"]}}}

    def _audio_opts(self, codec, quality=None):
        pp = {"key": "FFmpegExtractAudio", "preferredcodec": codec}
        if quality:
            pp["preferredquality"] = quality
        return {
            "format": "bestaudio/best",
            "postprocessors": [pp],
            "outtmpl": str(self.output_dir / "%(title)s.%(ext)s"),
            "progress_hooks": [self.progress_hook],
            **self._AUDIO_EXTRACTOR_ARGS,
        }

    def _video_opts(self, fmt, quality):
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
            "format": quality_map.get(quality, quality_map["720p"]),
            "merge_output_format": fmt.lower(),
            "outtmpl": str(self.output_dir / "%(title)s.%(ext)s"),
            "progress_hooks": [self.progress_hook],
        }

    # ── Download logic ───────────────────────────────────────────────────────

    def progress_hook(self, d):
        if self.cancel_download:
            raise Exception("Download cancelled by user")

        if d["status"] == "downloading":
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

                if percent is not None:
                    self.window.after(0, lambda p=percent: self.progress_bar.set(p / 100))

                bps = d.get("speed")
                if bps and bps >= 1_048_576:
                    speed_str = f"{bps / 1_048_576:.1f} MB/s"
                elif bps and bps >= 1024:
                    speed_str = f"{bps / 1024:.1f} KB/s"
                elif bps:
                    speed_str = f"{bps:.0f} B/s"
                else:
                    speed_str = ""

                pct_str = f"{percent:.1f}%" if percent is not None else "..."
                text = f"Downloading  {pct_str}  {speed_str}".strip()

                self.window.after(0, lambda t=text: self.status_label.configure(text=t))
            except Exception:
                self.window.after(0, lambda: self.status_label.configure(text="Downloading..."))

        elif d["status"] == "finished":
            self.window.after(0, lambda: self.progress_bar.set(1))
            self.window.after(0, lambda: self.status_label.configure(text="Processing... Converting to final format"))

    def download_video(self):
        url = self.url_entry.get().strip()

        if not url or not url.startswith(("http://", "https://")):
            self.window.after(0, lambda: messagebox.showerror("Error", "Please enter a valid URL"))
            self._reset_ui()
            return

        fmt = self.format_var.get()
        quality = self.quality_var.get()

        if fmt == "MP3":
            ydl_opts = self._audio_opts("mp3", quality.split()[0])
        elif fmt == "M4A":
            ydl_opts = self._audio_opts("m4a", quality.split()[0])
        elif fmt == "WAV":
            ydl_opts = self._audio_opts("wav")
        else:
            ydl_opts = self._video_opts(fmt, quality)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title", "Unknown")

            if not self.cancel_download:
                files = sorted(
                    self.output_dir.iterdir(),
                    key=lambda f: f.stat().st_mtime,
                    reverse=True,
                )
                self._final_filepath = files[0] if files else None
                self.window.after(0, lambda: self.progress_bar.set(1))
                self.window.after(0, lambda: self.status_label.configure(text="✓ Download complete!"))
                self.window.after(0, self._on_download_success)

        except Exception as e:
            err_msg = str(e)
            if self.cancel_download:
                self.window.after(0, lambda: self.progress_bar.set(0))
                self.window.after(0, lambda: self.status_label.configure(text="Download cancelled"))
            else:
                self.window.after(0, lambda: self.progress_bar.set(0))
                self.window.after(0, lambda: self.status_label.configure(text="Download failed"))
                self.window.after(0, lambda msg=err_msg: messagebox.showerror("Error", f"Download failed:\n{msg}"))

        finally:
            self._reset_ui()

    def _on_download_success(self):
        def open_path(path):
            if os.name == "nt":
                os.startfile(str(path))
            elif hasattr(os, "uname") and os.uname().sysname == "Darwin":
                subprocess.run(["open", str(path)])
            else:
                subprocess.run(["xdg-open", str(path)])

        open_path(self.output_dir)
        if self._final_filepath and self._final_filepath.exists():
            open_path(self._final_filepath)

    def _reset_ui(self):
        self.downloading = False
        self.cancel_download = False
        self.window.after(0, lambda: self.download_btn.configure(state="normal", text="Download"))
        self.window.after(0, lambda: self.stop_btn.configure(state="disabled"))

    def start_download(self):
        if self.downloading:
            return
        self.downloading = True
        self.cancel_download = False
        self.download_btn.configure(state="disabled", text="Downloading...")
        self.stop_btn.configure(state="normal")
        self.progress_bar.set(0)
        self.status_label.configure(text="Starting download...")
        threading.Thread(target=self.download_video, daemon=True).start()

    def stop_download(self):
        if self.downloading:
            self.cancel_download = True
            self.status_label.configure(text="Cancelling...")
            self.stop_btn.configure(state="disabled")

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    app = YouTubeConverterGUI()
    app.run()
