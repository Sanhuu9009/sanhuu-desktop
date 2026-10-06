@echo off
chcp 65001 >nul
title Sanhuu Pet - Installer (Windows)
setlocal
cd /d "%~dp0"
set "ROOT=%~dp0.."
set "DIR=%LOCALAPPDATA%\SanhuuPet"

rem 定位桌宠 HTML（排除介绍页 index.html）
set "HTML="
for %%f in ("%ROOT%\*.html") do (
  if /i not "%%~nxf"=="index.html" set "HTML=%%~ff"
)
if not defined HTML (
  echo [错误] 未找到 三虎桌宠.html，请确认安装包文件完整。
  pause
  exit /b 1
)

echo ==================================================
echo    三虎桌宠  Sanhuu Pet  -  Windows 一键安装
echo    美术素材版权 (c) 三虎 Sanhuu，保留所有权利
echo ==================================================
echo.
echo  安装目录 : %DIR%
echo  将创建   : 桌面快捷方式、开始菜单快捷方式、开机自动启动
echo.

rem ---------- 复制文件 ----------
if exist "%DIR%" rmdir /s /q "%DIR%" 2>nul
mkdir "%DIR%\assets" 2>nul
copy /y "%HTML%" "%DIR%\" >nul
copy /y "%ROOT%\assets\*.png" "%DIR%\assets\" >nul
copy /y "%~dp0*.ico" "%DIR%\icon.ico" >nul
echo  [OK] 文件已复制

rem ---------- 定位 Chrome / Edge ----------
set "CHROME="
for /f "delims=" %%i in ('where chrome 2^>nul') do if not defined CHROME set "CHROME=%%i"
if not defined CHROME if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" set "CHROME=C:\Program Files\Google\Chrome\Application\chrome.exe"
if not defined CHROME if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" set "CHROME=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if not defined CHROME if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set "CHROME=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
for /f "delims=" %%i in ('where msedge 2^>nul') do if not defined CHROME set "CHROME=%%i"
if not defined CHROME if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" set "CHROME=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not defined CHROME if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" set "CHROME=C:\Program Files\Microsoft\Edge\Application\msedge.exe"
if not defined CHROME (
  echo  [错误] 未找到 Chrome 或 Edge。桌宠需要浏览器运行，请先安装后再运行本安装包。
  pause
  exit /b 1
)

rem ---------- 生成快捷方式脚本 ----------
set "PS=%DIR%\mk.ps1"
> "%PS%" echo $ws = New-Object -ComObject WScript.Shell
>> "%PS%" echo $chrome = '%CHROME%'
>> "%PS%" echo $dir    = '%DIR%'
>> "%PS%" echo $url    = 'file:///%DIR:\=/%三虎桌宠.html'
>> "%PS%" echo $desk   = [Environment]::GetFolderPath('Desktop')
>> "%PS%" echo $menu   = $env:APPDATA + '\Microsoft\Windows\Start Menu\Programs'
>> "%PS%" echo $start  = $env:APPDATA + '\Microsoft\Windows\Start Menu\Programs\Startup'
>> "%PS%" echo foreach ($p in @($desk+'\Sanhuu Pet.lnk', $menu+'\Sanhuu Pet.lnk', $start+'\Sanhuu Pet.lnk')) {
>> "%PS%" echo   $l = $ws.CreateShortcut($p)
>> "%PS%" echo   $l.TargetPath = $chrome
>> "%PS%" echo   $l.Arguments = '--app="' + $url + '" --window-size=480,700 --window-position=center'
>> "%PS%" echo   $l.WorkingDirectory = $dir
>> "%PS%" echo   $l.IconLocation = $dir + '\icon.ico,0'
>> "%PS%" echo   $l.Description = 'Sanhuu Pet'
>> "%PS%" echo   $l.Save()
>> "%PS%" echo }
powershell -NoProfile -ExecutionPolicy Bypass -File "%PS%" >nul 2>nul
del /q "%PS%" >nul 2>nul
if not exist "%USERPROFILE%\Desktop\Sanhuu Pet.lnk" if not exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Sanhuu Pet.lnk" (
  echo  [警告] 快捷方式创建失败，请手动将 三虎桌宠.html 创建快捷方式。
)

rem ---------- 开机自启动 ----------
echo  [OK] 已设置开机自动启动（开始菜单 → 启动 文件夹）
echo.
echo  正在启动三虎桌宠…
start "" "%CHROME%" --app="file:///%DIR:\=/%三虎桌宠.html" --window-size=480,700 --window-position=center

echo.
echo  ==================================================
echo   安装完成！
echo   桌面与开始菜单已生成「Sanhuu Pet」快捷方式
echo   开机自动启动已启用
echo   卸载：运行 pack\卸载三虎桌宠-Windows.bat
echo  ==================================================
pause
