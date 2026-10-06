@echo off
rem ===== XiaoBaiHu Desktop Pet launcher (Windows) =====
title XiaoBaiHu Pet
cd /d "%~dp0"

rem locate the html file in this folder (avoid non-ascii issues in batch)
set "FILE="
for %%f in ("%~dp0*.html") do set "FILE=%%~ff"
if not defined FILE (
  echo [Error] No .html file found in this folder.
  pause
  exit /b 1
)

set "URL=file:///%FILE:\=/%"
set "ARGS=--app=%URL% --window-size=480,700 --window-position=center --disable-features=Translate"

where chrome >nul 2>nul && (start "" chrome %ARGS% & exit /b)
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" %ARGS% & exit /b)
if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (start "" "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" %ARGS% & exit /b)
if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (start "" "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" %ARGS% & exit /b)

where msedge >nul 2>nul && (start "" msedge %ARGS% & exit /b)
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" %ARGS% & exit /b)
if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" (start "" "C:\Program Files\Microsoft\Edge\Application\msedge.exe" %ARGS% & exit /b)

echo [Error] Chrome / Edge not found. Please open the html file manually.
pause
