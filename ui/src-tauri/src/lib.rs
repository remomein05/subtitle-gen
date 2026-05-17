use tauri::Emitter;
use tauri_plugin_shell::process::CommandEvent;
use tauri_plugin_shell::ShellExt;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
struct ModelCheckResponse {
    downloaded: bool,
}

#[tauri::command]
async fn check_model(app: tauri::AppHandle, model_name: String) -> Result<bool, String> {
    let sidecar_command = app
        .shell()
        .sidecar("engine")
        .map_err(|e| e.to_string())?
        .args(["--check", &model_name]);

    let output = sidecar_command.output().await.map_err(|e| e.to_string())?;
    
    if output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        let response: ModelCheckResponse = serde_json::from_str(stdout.trim())
            .map_err(|e| format!("Failed to parse engine output: {}", e))?;
        Ok(response.downloaded)
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

#[tauri::command]
async fn process_video(app: tauri::AppHandle, video_path: String, model_name: String) -> Result<(), String> {
    let model_arg = format!("--model={}", model_name);
    let sidecar_command = app
        .shell()
        .sidecar("engine")
        .map_err(|e| e.to_string())?
        .arg(video_path)
        .arg(model_arg);

    let (mut rx, _child) = sidecar_command.spawn().map_err(|e| e.to_string())?;

    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line) => {
                    let line_str = String::from_utf8_lossy(&line).to_string();
                    for single_line in line_str.lines() {
                        let trimmed = single_line.trim();
                        if !trimmed.is_empty() {
                            println!("Sidecar: {}", trimmed);
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
        .invoke_handler(tauri::generate_handler![process_video, check_model])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
