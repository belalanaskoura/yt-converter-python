# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Instructions for Claude

- **After every change, update this file** with what was changed: new files created, patterns discovered, bugs fixed, architecture decisions, or anything that would help in future sessions. Keep it current and accurate.
- **After every change, commit to GitHub** — stage all relevant files and push to `origin/main` under the user's git identity (no Co-Authored-By lines).

## Project Overview

Two apps in one repo:
- **`youtube_downloader.py`** — legacy Python/CustomTkinter fallback (keep untouched)
- **`tauri-app/`** — primary app: Tauri 2.0 + React + Tailwind v4 + Shadcn/UI

## Running the App

```bash
run_app.bat           # double-click or run in terminal — sets PATH and launches dev server
# or manually:
cd tauri-app
export PATH="$HOME/.cargo/bin:$PATH"
npm run tauri dev     # first run compiles Rust (~1-2 min); subsequent runs are fast
```

## Project Structure

```
Link_to_Media/
├── youtube_downloader.py          ← legacy fallback, do not modify
├── requirements.txt               ← pip deps for legacy app
├── config.json                    ← persists last save directory
├── run_app.bat                    ← launcher (sets cargo PATH, cd tauri-app, npm run tauri dev)
├── sidecar/
│   └── yt_dlp_worker.py          ← Python child process; communicates via stdin/stdout JSON
└── tauri-app/
    ├── src/                       ← React frontend
    │   ├── App.tsx                ← layout, SQLite init, Tauri event listeners
    │   ├── index.css              ← Tailwind v4 @theme dark variables (oklch)
    │   ├── components/
    │   │   ├── ui/                ← Shadcn-style: button, input, badge, select, scroll-area, separator
    │   │   ├── DownloadForm.tsx   ← URL input + Type/Format/Quality cascade + save location
    │   │   ├── ProgressCard.tsx   ← Framer Motion animated progress states
    │   │   └── Sidebar.tsx        ← Download history from SQLite
    │   └── lib/
    │       ├── types.ts           ← MediaType, MediaFormat, ProgressState, HistoryEntry
    │       └── utils.ts           ← cn(), formatRelativeTime(), formatFileSize()
    └── src-tauri/
        ├── src/lib.rs             ← Tauri commands + sidecar management
        ├── Cargo.toml             ← tauri-plugin-dialog, tauri-plugin-sql(sqlite), tauri-plugin-opener
        └── tauri.conf.json        ← productName "Link to Media", 960×640 window
```

## Tauri Backend (lib.rs)

Commands: `start_download`, `cancel_download`, `select_directory`, `open_folder`, `open_file`

Key helpers:
- `find_python()` — tries `python`, `py`, `python3`, then scans `C:\Python3XX\` paths
- `find_sidecar()` — walks up from `current_exe()` up to 4 levels to find `sidecar/yt_dlp_worker.py`
- stderr is `Stdio::null()` — discards yt-dlp warnings that would otherwise surface as errors
- Stdout is read line-by-line, parsed as JSON, re-emitted as Tauri events

Tauri events emitted:
- `download://progress` → `{ percent, speed }`
- `download://processing` → download finished, post-processing running
- `download://complete` → `{ filepath, title, thumbnail }`
- `download://cancelled` → `{}`
- `download://error` → `{ message }`

## IPC Protocol (Rust ↔ Python Sidecar)

stdin → sidecar (newline-delimited JSON):
```json
{"action": "download", "url": "...", "format": "mp3", "quality": "192", "output_dir": "..."}
{"action": "cancel"}
```

stdout ← sidecar (newline-delimited JSON):
```json
{"type": "progress", "percent": 45.2, "speed": "1.2 MB/s"}
{"type": "finished"}
{"type": "complete", "filepath": "/path/file.mp3", "title": "Song Title", "thumbnail": "https://..."}
{"type": "error", "message": "..."}
{"type": "cancelled"}
```

## Sidecar (yt_dlp_worker.py)

- Must use `"quiet": True, "noprogress": True` in yt-dlp opts — otherwise yt-dlp's own stdout output pollutes the JSON stream and causes buffered/instant delivery
- `"concurrent_fragment_downloads": 5` in `_COMMON_OPTS` — YouTube delivers DASH/HLS as fragments; parallel download gives a significant speed improvement
- No client restriction (`_AUDIO_EXTRACTOR_ARGS = {}`) — lets yt-dlp auto-select the best working client
  - android requires GVS PO Token as of early 2026
  - ios had format availability issues
  - No restriction = yt-dlp's default fallback chain works best
- Cancellation via background thread reading stdin for `{"action": "cancel"}`
- `complete` event includes `thumbnail` field (yt-dlp `info["thumbnail"]` — YouTube CDN URL, stable and public)

## Frontend Patterns

- **Tailwind v4**: uses `@theme {}` in `index.css`, no `tailwind.config.ts` file, plugin is `@tailwindcss/vite`
- **Path alias**: `@/` → `./src/` (configured in both `vite.config.ts` and `tsconfig.json`)
- **History recording pattern**: `onDownloadStart(meta)` in `DownloadForm` passes `{url, format, quality}` up to `App.tsx`, stored in `pendingMeta` ref. On `download://complete`, `addHistoryEntryRef.current` is called with the stored meta + event payload. Using a ref avoids stale closure issues with the Tauri listener (which runs in a `useEffect` with `[]` deps).
- **Tauri event listener setup**: all `listen()` calls are wrapped in a single `Promise.all` with an `active` flag — prevents double-registration from React StrictMode's double-invoke of `useEffect`. If cleanup runs before promises resolve, `active=false` triggers immediate unlisten.
- **SQLite**: via `tauri-plugin-sql`. DB name: `sqlite:downloads.db`. Table: `downloads` with columns `id, title, url, filepath, format, quality, downloaded_at, file_size, thumbnail`. Requires `sql:allow-load`, `sql:allow-execute`, `sql:allow-select` in `capabilities/default.json`.
- **DB migration**: `ALTER TABLE downloads ADD COLUMN thumbnail TEXT DEFAULT ''` runs on every startup, wrapped in `.catch(() => {})` — no-ops if column already exists.
- **Default output dir**: initialized as `""`, immediately populated by `downloadDir()` from `@tauri-apps/api/path` — resolves to the OS user's Downloads folder for any user. No hardcoded paths.
- **On download complete**: `open_folder` is automatically invoked with the parent directory of the downloaded file.
- **History deletion**: `deleteEntry(id)` and `clearHistory()` callbacks in `App.tsx`, passed to `Sidebar`. Per-item Remove button (hover) + Clear all button in sidebar header.

## Environment

- Rust toolchain: `stable-x86_64-pc-windows-msvc` at `~/.cargo/bin`
- VS Build Tools 2022 at `C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools`
- MSVC link.exe: `.../VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/link.exe`
- Git Bash's `/usr/bin/link` (GNU hardlink) shadows MSVC link.exe — run_app.bat and PATH export fix this
- Python at `C:\Python314\python.exe` (or whatever `find_python()` resolves)
- yt-dlp version: `2026.3.3` (keep updated — YouTube breaks compatibility frequently)

## Legacy App Notes (youtube_downloader.py)

Single file, one class `YouTubeConverterGUI`:
- **`_audio_opts` / `_video_opts`**: Build yt-dlp option dicts
- **`progress_hook`**: Uses `downloaded_bytes/total_bytes` for percent (reliable for HLS), falls back to `fragment_index/fragment_count`, then `_percent_str`
- **`download_video`**: Background thread — calls yt-dlp, finds final file by most-recently-modified in output dir
- All GUI updates from download thread use `self.window.after(0, lambda: ...)` for thread safety
- Lambda exception bug: always capture `str(e)` into a local before using in `window.after` lambda
- Video format strings: `bestvideo[height=NNN]+bestaudio/bestvideo[height<=NNN]+bestaudio/best`
- 4K: `bestvideo[height=2160]+bestaudio/bestvideo[height>=1440]+bestaudio/bestvideo+bestaudio/best`
- Save dir persisted to `config.json` on every change
