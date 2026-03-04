# YouTube Downloader

A modern YouTube downloader built with Python, CustomTkinter, and yt-dlp. Download audio or video in multiple formats and qualities with a YouTube-styled dark interface.

## Features

- Download **Audio** (MP3, M4A, WAV) or **Video** (MP4, WEBM, MKV)
- Audio quality: 128–320 kbps or Lossless (WAV)
- Video quality: 360p to 4K
- Real-time progress bar showing percentage and download speed
- Paste button for quick URL input
- Remembers your last save directory across sessions
- On completion: save folder opens and file plays automatically in your default media player
- Cancellable downloads with responsive UI (multithreaded)

## Requirements

- Python 3.8+
- [FFmpeg](https://ffmpeg.org/) — must be installed and available in PATH

## Installation

```bash
git clone https://github.com/your-username/youtube-downloader.git
cd youtube-downloader
pip install -r requirements.txt
```

**Install FFmpeg:**

| Platform | Command |
|----------|---------|
| Windows  | Download from [ffmpeg.org](https://ffmpeg.org/) and add to PATH |
| macOS    | `brew install ffmpeg` |
| Linux    | `sudo apt install ffmpeg` |

## Usage

```bash
python youtube_downloader.py
```

1. Paste a YouTube URL (or use the **Paste** button)
2. Select Type → Format → Quality
3. Optionally change the save directory
4. Click **Download** — when done, the folder and file open automatically

## Keeping yt-dlp up to date

YouTube frequently changes its API. If downloads fail, update yt-dlp first:

```bash
pip install -U yt-dlp
```
