# Link to Media

A desktop YouTube downloader built with Tauri 2.0, React, and yt-dlp. Download audio or video in multiple formats and qualities with a clean dark interface.

## Features

- Download **Audio** (MP3, M4A, WAV) or **Video** (MP4, WEBM, MKV)
- Audio quality: 128–320 kbps or Lossless (WAV)
- Video quality: 360p to 4K
- Real-time progress bar with percentage and download speed
- Download history stored locally with SQLite
- Paste button for quick URL input
- Remembers your last save directory across sessions
- Cancellable downloads

## Requirements

- [Rust](https://rustup.rs/) (stable toolchain)
- [Node.js](https://nodejs.org/) 18+
- Python 3.8+ with [yt-dlp](https://github.com/yt-dlp/yt-dlp) installed
- [FFmpeg](https://ffmpeg.org/) — must be in PATH

```bash
pip install yt-dlp
```

**Install FFmpeg:**

| Platform | Command |
|----------|---------|
| Windows  | Download from [ffmpeg.org](https://ffmpeg.org/) and add to PATH |
| macOS    | `brew install ffmpeg` |
| Linux    | `sudo apt install ffmpeg` |

## Installation

```bash
git clone https://github.com/your-username/Link_to_Media.git
cd Link_to_Media/tauri-app
npm install
```

## Running

```bash
# From the repo root — double-click or run in terminal
run_app.bat

# Or manually
cd tauri-app
npm run tauri dev
```

The first run compiles the Rust backend (~1–2 min). Subsequent runs are fast.

## Usage

1. Paste a YouTube URL (or use the **Paste** button)
2. Select Type → Format → Quality
3. Optionally change the save directory (defaults to your system's Downloads folder)
4. Click **Download**

## Keeping yt-dlp up to date

YouTube frequently changes its API. If downloads fail, update yt-dlp:

```bash
pip install -U yt-dlp
```
