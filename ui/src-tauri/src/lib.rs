use tauri::Emitter;
use tauri_plugin_shell::process::CommandEvent;
use tauri_plugin_shell::ShellExt;

#[tauri::command]
async fn process_video(app: tauri::AppHandle, video_path: String) -> Result<(), String> {
    let sidecar_command = app
        .shell()
        .sidecar("engine")
        .map_err(|e| e.to_string())?
        .arg(video_path);

    let (mut rx, _child) = sidecar_command.spawn().map_err(|e| e.to_string())?;

    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line) => {
                    let line_str = String::from_utf8_lossy(&line).to_string();
                    // Split by newlines in case the engine sent multiple updates at once
                    for single_line in line_str.lines() {
                        let trimmed = single_line.trim();
                        if !trimmed.is_empty() {
                            println!("Sidecar: {}", trimmed); // Print to terminal for debugging
                            let _ = app.emit("engine-status", trimmed);
                        }
                    }
                }
                CommandEvent::Stderr(line) => {
                    let line_str = String::from_utf8_lossy(&line).to_string();
                    eprintln!("Sidecar Error: {}", line_str);
                }
                _ => {}
            }
        }
    });

    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![process_video])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
