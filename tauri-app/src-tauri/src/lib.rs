use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use tauri::{AppHandle, Emitter};

// ── Shared sidecar state ──────────────────────────────────────────────────────

struct SidecarState {
    child: Mutex<Option<Child>>,
    stdin: Mutex<Option<std::process::ChildStdin>>,
}

impl Default for SidecarState {
    fn default() -> Self {
        Self {
            child: Mutex::new(None),
            stdin: Mutex::new(None),
        }
    }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/// Find a working Python executable name.
fn find_python() -> String {
    // Try launcher/aliases first, then fall back to common install paths
    for name in &["python", "py", "python3"] {
        if Command::new(name)
            .arg("--version")
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
            .and_then(|mut c| c.wait())
            .is_ok()
        {
            return name.to_string();
        }
    }
    // Hard-coded common Windows install paths
    for major in 9..=20u32 {
        for path in [
            format!("C:\\Python3{}\\python.exe", major),
            format!("C:\\Python31{}\\python.exe", major),
        ] {
            if std::path::Path::new(&path).exists() {
                return path;
            }
        }
    }
    "python".to_string()
}

/// Find the sidecar script by walking up from the running exe.
fn find_sidecar() -> Option<PathBuf> {
    let exe = std::env::current_exe().ok()?;
    let exe_dir = exe.parent()?;
    // dev:  .../tauri-app/src-tauri/target/debug/  (4 levels up → project root)
    // prod: next to exe or one level up
    let candidates = [
        exe_dir.join("../../../../sidecar/yt_dlp_worker.py"),
        exe_dir.join("../../../sidecar/yt_dlp_worker.py"),
        exe_dir.join("../../sidecar/yt_dlp_worker.py"),
        exe_dir.join("../sidecar/yt_dlp_worker.py"),
        exe_dir.join("sidecar/yt_dlp_worker.py"),
    ];
    candidates
        .iter()
        .find(|p| p.exists())
        .map(|p| p.canonicalize().unwrap_or(p.to_path_buf()))
}

// ── Tauri commands ────────────────────────────────────────────────────────────

#[derive(serde::Deserialize)]
pub struct DownloadPayload {
    pub url: String,
    pub format: String,
    pub quality: String,
    pub output_dir: String,
}

#[tauri::command]
async fn start_download(
    app: AppHandle,
    payload: DownloadPayload,
    state: tauri::State<'_, Arc<SidecarState>>,
) -> Result<(), String> {
    // Kill any existing sidecar
    {
        let mut child_guard = state.child.lock().unwrap();
        if let Some(ref mut c) = *child_guard {
            let _ = c.kill();
        }
        *child_guard = None;
        *state.stdin.lock().unwrap() = None;
    }

    let python = find_python();

    let sidecar_path = find_sidecar().ok_or_else(|| {
        format!(
            "Cannot find sidecar/yt_dlp_worker.py. Exe dir: {:?}",
            std::env::current_exe()
                .ok()
                .and_then(|e| e.parent().map(|p| p.to_path_buf()))
        )
    })?;

    let cmd_json = serde_json::json!({
        "action": "download",
        "url": payload.url,
        "format": payload.format,
        "quality": payload.quality,
        "output_dir": payload.output_dir,
    });

    // Ensure output directory exists
    let _ = std::fs::create_dir_all(&payload.output_dir);

    let mut child = Command::new(&python)
        .arg(&sidecar_path)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null()) // yt-dlp writes warnings to stderr; ignore them
        .spawn()
        .map_err(|e| format!("Failed to spawn Python ({python}): {e}"))?;

    // Write the download command to stdin
    {
        let mut s = child.stdin.take().ok_or("No stdin on sidecar")?;
        writeln!(s, "{}", cmd_json).map_err(|e| e.to_string())?;
        *state.stdin.lock().unwrap() = Some(s);
    }

    let stdout = child.stdout.take().ok_or("No stdout on sidecar")?;

    *state.child.lock().unwrap() = Some(child);

    // Thread: read stdout and emit progress events
    let app_clone = app.clone();
    let state_clone = Arc::clone(&state);
    std::thread::spawn(move || {
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            match line {
                Ok(l) if !l.trim().is_empty() => {
                    if let Ok(val) = serde_json::from_str::<serde_json::Value>(&l) {
                        match val["type"].as_str().unwrap_or("") {
                            "progress" => {
                                let _ = app_clone.emit("download://progress", &val);
                            }
                            "finished" => {
                                let _ = app_clone.emit("download://processing", &val);
                            }
                            "complete" => {
                                let _ = app_clone.emit("download://complete", &val);
                            }
                            "cancelled" => {
                                let _ = app_clone.emit(
                                    "download://cancelled",
                                    serde_json::json!({}),
                                );
                            }
                            "error" => {
                                let _ = app_clone.emit("download://error", &val);
                            }
                            _ => {}
                        }
                    }
                }
                _ => {}
            }
        }
        // Stdout closed — clean up
        let mut child_guard = state_clone.child.lock().unwrap();
        if let Some(ref mut c) = *child_guard {
            let _ = c.wait();
        }
        *child_guard = None;
    });

    Ok(())
}

#[tauri::command]
async fn cancel_download(
    state: tauri::State<'_, Arc<SidecarState>>,
) -> Result<(), String> {
    let mut stdin_guard = state.stdin.lock().unwrap();
    if let Some(ref mut s) = *stdin_guard {
        let _ = writeln!(s, "{}", serde_json::json!({"action": "cancel"}));
    }
    Ok(())
}

#[tauri::command]
async fn select_directory(app: AppHandle) -> Result<Option<String>, String> {
    use tauri_plugin_dialog::DialogExt;
    let path = app.dialog().file().blocking_pick_folder();
    Ok(path.map(|p| p.to_string()))
}

#[tauri::command]
async fn open_folder(path: String) -> Result<(), String> {
    #[cfg(target_os = "windows")]
    Command::new("explorer")
        .arg(&path)
        .spawn()
        .map_err(|e| e.to_string())?;
    #[cfg(target_os = "macos")]
    Command::new("open")
        .arg(&path)
        .spawn()
        .map_err(|e| e.to_string())?;
    #[cfg(target_os = "linux")]
    Command::new("xdg-open")
        .arg(&path)
        .spawn()
        .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
async fn open_file(path: String) -> Result<(), String> {
    #[cfg(target_os = "windows")]
    Command::new("cmd")
        .args(["/C", "start", "", &path])
        .spawn()
        .map_err(|e| e.to_string())?;
    #[cfg(target_os = "macos")]
    Command::new("open")
        .arg(&path)
        .spawn()
        .map_err(|e| e.to_string())?;
    #[cfg(target_os = "linux")]
    Command::new("xdg-open")
        .arg(&path)
        .spawn()
        .map_err(|e| e.to_string())?;
    Ok(())
}

// ── App entry point ───────────────────────────────────────────────────────────

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_sql::Builder::default().build())
        .manage(Arc::new(SidecarState::default()))
        .invoke_handler(tauri::generate_handler![
            start_download,
            cancel_download,
            select_directory,
            open_folder,
            open_file,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
