use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc, Mutex,
};
use std::time::Duration;

use tauri::{AppHandle, Emitter, Manager};

/// 窗口选择模式状态：停止标志（Arc 共享给线程）+ 是否在运行
#[derive(Default)]
pub struct PickerState {
    stop: Arc<AtomicBool>,
    running: Mutex<bool>,
}

/// 每 250ms 查询鼠标所在窗口，把矩形与标题发到前端（main 与 overlay 窗口）
fn picker_loop(app: AppHandle, stop: Arc<AtomicBool>) {
    while !stop.load(Ordering::Relaxed) {
        let info = crate::commands::cursor_window_info().map(|w| {
            serde_json::json!({
                "id": w.id,
                "title": w.title,
                "x": w.x,
                "y": w.y,
                "width": w.width,
                "height": w.height,
            })
        });
        let _ = app.emit("picker-window", info);
        std::thread::sleep(Duration::from_millis(250));
    }
}

pub fn start(app: &AppHandle) {
    let state: tauri::State<'_, PickerState> = app.state();
    {
        let mut running = state.running.lock().unwrap();
        if *running {
            return;
        }
        state.stop.store(false, Ordering::Relaxed);
        *running = true;
    }
    let app2 = app.clone();
    let stop = Arc::clone(&state.stop);
    std::thread::spawn(move || {
        picker_loop(app2, stop);
        if let Some(s) = app2.try_state::<PickerState>() {
            *s.running.lock().unwrap() = false;
        }
    });
}

pub fn stop(app: &AppHandle) {
    if let Some(s) = app.try_state::<PickerState>() {
        s.stop.store(true, Ordering::Relaxed);
    }
    let _ = app.emit("picker-window", serde_json::Value::Null);
    if let Some(ov) = app.get_webview_window("overlay") {
        let _ = ov.hide();
    }
}
