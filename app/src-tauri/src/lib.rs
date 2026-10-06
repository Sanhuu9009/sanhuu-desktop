mod commands;
mod picker;

use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Emitter, Manager,
};

fn show_main(app: &tauri::AppHandle) {
    if let Some(w) = app.get_webview_window("main") {
        let _ = w.show();
        let _ = w.unminimize();
        let _ = w.set_focus();
    }
}

fn toggle_main(app: &tauri::AppHandle) {
    if let Some(w) = app.get_webview_window("main") {
        if w.is_visible().unwrap_or(false) {
            let _ = w.hide();
        } else {
            show_main(app);
        }
    }
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_autostart::init(
            tauri_plugin_autostart::MacosLauncher::LaunchAgent,
            None,
        ))
        .manage(picker::PickerState::default())
        .setup(|app| {
            // 托盘
            let show = MenuItem::with_id(app, "show", "显示 / 隐藏三虎", true, None::<&str>)?;
            let settings = MenuItem::with_id(app, "settings", "打开设置", true, None::<&str>)?;
            let quit = MenuItem::with_id(app, "quit", "退出三虎桌宠", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show, &settings, &quit])?;
            let _tray = TrayIconBuilder::with_id("main")
                .icon(app.default_window_icon().unwrap().clone())
                .tooltip("三虎桌宠 Sanhuu Pet")
                .menu(&menu)
                .show_menu_on_left_click(false)
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "show" => toggle_main(app),
                    "settings" => {
                        show_main(app);
                        let _ = app.emit("open-panel", "settings");
                    }
                    "quit" => app.exit(0),
                    _ => {}
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        toggle_main(tray.app_handle());
                    }
                })
                .build(app)?;

            // 主窗口：点关闭 = 隐藏到托盘
            if let Some(win) = app.get_webview_window("main") {
                let w = win.clone();
                win.on_window_event(move |event| {
                    if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                        api.prevent_close();
                        let _ = w.hide();
                    }
                });
            }

            // 高亮框窗口：点击穿透
            if let Some(ov) = app.get_webview_window("overlay") {
                let _ = ov.set_ignore_cursor_events(true);
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::list_windows,
            commands::cursor_window,
            commands::screenshot_full,
            commands::screenshot_window,
            commands::record_gif,
            commands::read_text_file,
            commands::open_file_dialog,
            commands::save_bytes,
            commands::set_autostart,
            commands::power_action,
            commands::start_picker,
            commands::stop_picker,
        ])
        .run(tauri::generate_context!())
        .expect("error while running sanhuu pet");
}
