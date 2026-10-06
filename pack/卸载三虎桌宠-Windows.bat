@echo off
chcp 65001 >nul
title Sanhuu Pet - Uninstall (Windows)
setlocal
set "DIR=%LOCALAPPDATA%\SanhuuPet"
echo ==================================================
echo    三虎桌宠  Sanhuu Pet  -  卸载
echo ==================================================
echo  将删除快捷方式、开机自启动项与安装目录
echo.
del "%USERPROFILE%\Desktop\Sanhuu Pet.lnk" 2>nul
del "%USERPROFILE%\OneDrive\Desktop\Sanhuu Pet.lnk" 2>nul
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Sanhuu Pet.lnk" 2>nul
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Sanhuu Pet.lnk" 2>nul
rmdir /s /q "%DIR%" 2>nul
echo  [OK] 已卸载三虎桌宠。
echo.
pause
