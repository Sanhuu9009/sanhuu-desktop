use std::{
    io::Cursor,
    path::PathBuf,
    sync::mpsc,
    time::{Duration, Instant},
};

use base64::{engine::general_purpose::STANDARD as B64, Engine as _};
use serde::Serialize;
use tauri::{AppHandle, Manager};
use tauri_plugin_dialog::DialogExt;
use xcap::Window;

use crate::picker;

#[derive(Serialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct WinInfo {
    pub id: u32,
    pub title: String,
    pub x: i32,
    pub y: i32,
    pub width: u32,
    pub height: u32,
}

fn to_win_info(w: &Window) -> Option<WinInfo> {
    let title = w.title().ok()?;
    if title.is_empty() {
        return None;
    }
    Some(WinInfo {
        id: w.id().ok()?,
        title,
        x: w.x().ok()?,
        y: w.y().ok()?,
        width: w.width().ok()?,
        height: w.height().ok()?,
    })
}

/// 列出所有可见窗口
#[tauri::command]
pub fn list_windows() -> Result<Vec<WinInfo>, String> {
    let wins = Window::all().map_err(|e| e.to_string())?;
    Ok(wins.iter().filter_map(to_win_info).collect())
}

/// 鼠标当前所在的窗口（按窗口层级取最上层）
pub fn cursor_window_info() -> Option<WinInfo> {
    use device_query::{DeviceQuery, DeviceState};
    let dq = DeviceState::new();
    let (mx, my) = dq.get_mouse().coords;
    let (mx, my) = (i64::from(mx), i64::from(my));
    let wins = Window::all().ok()?;
    let mut best: Option<(i32, WinInfo)> = None;
    for w in &wins {
        let (x, y, ww, hh) = match (w.x(), w.y(), w.width(), w.height()) {
            (Ok(x), Ok(y), Ok(ww), Ok(hh)) => (x as i64, y as i64, ww as i64, hh as i64),
            _ => continue,
        };
        if ww <= 0 || hh <= 0 {
            continue;
        }
        if mx >= x && mx < x + ww && my >= y && my < y + hh {
            if let Some(info) = to_win_info(w) {
                let z = w.z().ok()?;
                if best.as_ref().map(|(bz, _)| z > *bz).unwrap_or(true) {
                    best = Some((z, info));
                }
            }
        }
    }
    best.map(|(_, i)| i)
}

/// 鼠标当前所在的窗口
#[tauri::command]
pub fn cursor_window() -> Result<Option<WinInfo>, String> {
    Ok(cursor_window_info())
}

fn capture_full() -> Result<image::RgbaImage, String> {
    let mons = xcap::Monitor::all().map_err(|e| e.to_string())?;
    if mons.is_empty() {
        return Err("未找到显示器".into());
    }
    mons[0].capture_image().map_err(|e| e.to_string())
}

fn capture_window(id: u32) -> Result<image::RgbaImage, String> {
    let wins = Window::all().map_err(|e| e.to_string())?;
    let w = wins
        .iter()
        .find(|w| w.id().ok() == Some(id))
        .ok_or("找不到该窗口")?;
    w.capture_image().map_err(|e| e.to_string())
}

/// 截全屏并弹出保存对话框
#[tauri::command]
pub async fn screenshot_full(app: AppHandle) -> Result<bool, String> {
    let img = tauri::async_runtime::spawn_blocking(capture_full)
        .await
        .map_err(|e| e.to_string())??;
    let png = encode_png(&img)?;
    save_bytes_dialog(app, png, "截图-全屏.png", "PNG 图片", "png").await
}

/// 截指定窗口并弹出保存对话框
#[tauri::command]
pub async fn screenshot_window(app: AppHandle, window_id: u32) -> Result<bool, String> {
    let img = tauri::async_runtime::spawn_blocking(move || capture_window(window_id))
        .await
        .map_err(|e| e.to_string())??;
    let png = encode_png(&img)?;
    save_bytes_dialog(app, png, "截图-窗口.png", "PNG 图片", "png").await
}

fn encode_png(img: &image::RgbaImage) -> Result<Vec<u8>, String> {
    let mut out = Cursor::new(Vec::new());
    image::DynamicImage::ImageRgba8(img.clone())
        .write_to(&mut out, image::ImageFormat::Png)
        .map_err(|e| e.to_string())?;
    Ok(out.into_inner())
}

/// 录制为 GIF：mode=full 全屏 / mode=window 指定窗口
#[tauri::command]
pub async fn record_gif(
    app: AppHandle,
    mode: String,
    window_id: Option<u32>,
    seconds: u32,
    fps: u32,
) -> Result<bool, String> {
    let secs = seconds.clamp(2, 60);
    let rate = fps.clamp(2, 10);
    let frames = secs * rate;
    let app2 = app.clone();
    let gif = tauri::async_runtime::spawn_blocking(move || -> Result<Vec<u8>, String> {
        let interval = Duration::from_millis(1000 / rate as u64);
        let mut out = Cursor::new(Vec::new());
        let mut last = Instant::now();
        let mut captured = 0usize;
        {
            let mut encoder = image::codecs::gif::GifEncoder::new(&mut out);
            encoder
                .set_repeat(image::codecs::gif::Repeat::Finite(0))
                .map_err(|err| err.to_string())?;
            for i in 0..frames {
                let target = last + interval;
                let now = Instant::now();
                if now < target {
                    std::thread::sleep(target - now);
                }
                last = Instant::now();
                let img = if mode == "window" {
                    let id = window_id.ok_or("缺少窗口 ID")?;
                    capture_window(id)?
                } else {
                    capture_full()?
                };
                // 降采样到宽 <= 960，控制体积
                let img = downscale(&img, 960);
                let fr = image::Frame::new(img);
                encoder.encode_frame(fr).map_err(|err| err.to_string())?;
                captured = i as usize + 1;
            }
        }
        if captured == 0 {
            return Err("未捕获到任何帧".into());
        }
        Ok(out.into_inner())
    })
    .await
    .map_err(|e| e.to_string())??;

    save_bytes_dialog(app2, gif, "录屏.gif", "GIF 动画", "gif").await
}

fn downscale(img: &image::RgbaImage, max_w: u32) -> image::RgbaImage {
    let (w, h) = img.dimensions();
    if w <= max_w {
        return img.clone();
    }
    let nw = max_w;
    let nh = (h as u64 * max_w as u64 / w as u64) as u32;
    image::imageops::resize(img, nw, nh, image::imageops::FilterType::Triangle)
}

/// 读取文本文件（格式转换用）
#[tauri::command]
pub fn read_text_file(path: String) -> Result<String, String> {
    std::fs::read_to_string(path).map_err(|e| e.to_string())
}

/// 打开系统文件选择对话框（解压用）
#[tauri::command]
pub async fn open_file_dialog(
    app: AppHandle,
    filter_name: Option<String>,
    filter_ext: Option<String>,
) -> Result<Option<String>, String> {
    use tauri_plugin_dialog::DialogExt;
    let mut dlg = app.dialog().file();
    if let (Some(n), Some(e)) = (filter_name, filter_ext) {
        dlg = dlg.add_filter(n, &[e.as_str()]);
    }
    let (tx, rx) = mpsc::channel::<Option<PathBuf>>();
    dlg.pick_file(move |p| {
        let _ = tx.send(p.and_then(|f| f.into_path().ok()));
    });
    let p = tauri::async_runtime::spawn_blocking(move || {
        rx.recv_timeout(Duration::from_secs(600)).unwrap_or(None)
    })
    .await
    .map_err(|e| e.to_string())?;
    Ok(p.map(|p| p.to_string_lossy().to_string()))
}

/// 弹保存对话框并把字节写入所选路径
pub async fn save_bytes_dialog(
    app: AppHandle,
    bytes: Vec<u8>,
    default_name: &str,
    filter_name: &str,
    filter_ext: &str,
) -> Result<bool, String> {
    let (tx, rx) = mpsc::channel::<Option<PathBuf>>();
    let dlg = app
        .dialog()
        .file()
        .set_file_name(default_name)
        .add_filter(filter_name, &[filter_ext]);
    dlg.save_file(move |p| {
        let _ = tx.send(p.and_then(|f| f.into_path().ok()));
    });
    let p = tauri::async_runtime::spawn_blocking(move || {
        rx.recv_timeout(Duration::from_secs(600)).unwrap_or(None)
    })
    .await
    .map_err(|e| e.to_string())?;
    match p {
        Some(path) => {
            std::fs::write(&path, &bytes).map_err(|e| e.to_string())?;
            Ok(true)
        }
        None => Ok(false),
    }
}

/// 前端转换完成后保存（base64 → 保存对话框 → 写文件）
#[tauri::command]
pub async fn save_bytes(
    app: AppHandle,
    data: String,
    default_name: String,
    filter_name: String,
    filter_ext: String,
) -> Result<bool, String> {
    let bytes = B64.decode(data).map_err(|e| e.to_string())?;
    save_bytes_dialog(app, bytes, &default_name, &filter_name, &filter_ext).await
}

/// 开机自启动开关
#[tauri::command]
pub fn set_autostart(app: AppHandle, enabled: bool) -> Result<bool, String> {
    use tauri_plugin_autostart::ManagerExt;
    let m = app.autolaunch();
    if enabled {
        m.enable().map_err(|e| e.to_string())?;
    } else {
        m.disable().map_err(|e| e.to_string())?;
    }
    let on = m.is_enabled().unwrap_or(false);
    Ok(on)
}

/// 电源操作：shutdown / restart / sleep
#[tauri::command]
pub fn power_action(action: String) -> Result<String, String> {
    #[cfg(target_os = "windows")]
    {
        let cmd = match action.as_str() {
            "shutdown" => "shutdown /s /t 60",
            "restart" => "shutdown /r /t 60",
            "sleep" => "rundll32.exe powrprof.dll,SetSuspendState 0,1,0",
            _ => return Err("未知操作".into()),
        };
        std::process::Command::new("cmd")
            .args(["/C", cmd])
            .spawn()
            .map_err(|e| e.to_string())?;
        Ok("已执行".into())
    }
    #[cfg(target_os = "macos")]
    {
        let script = match action.as_str() {
            "shutdown" => r#"tell application "System Events" to shut down"#,
            "restart" => r#"tell application "System Events" to restart"#,
            "sleep" => "pmset sleepnow",
            _ => return Err("未知操作".into()),
        };
        std::process::Command::new("osascript")
            .args(["-e", script])
            .spawn()
            .map_err(|e| e.to_string())?;
        Ok("已执行".into())
    }
    #[cfg(not(any(target_os = "windows", target_os = "macos")))]
    {
        let _ = action;
        Err("当前系统不支持".into())
    }
}

/// 开始窗口选择模式（鼠标跟踪 + 高亮框）
#[tauri::command]
pub fn start_picker(app: AppHandle) -> Result<(), String> {
    picker::start(&app);
    Ok(())
}

/// 结束窗口选择模式
#[tauri::command]
pub fn stop_picker(app: AppHandle) -> Result<(), String> {
    picker::stop(&app);
    Ok(())
}
