; 三虎桌宠 Sanhuu Pet · Windows 安装器（NSIS）
!include "MUI2.nsh"
!include "FileFunc.nsh"

Name "三虎桌宠 Sanhuu Pet"
OutFile "Sanhuu.Pet-${VERSION}-setup.exe"
InstallDir "$LOCALAPPDATA\SanhuuPet"
RequestExecutionLevel user

!define APP_EXE "SanhuuPet.exe"

; 页面
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "SimpChinese"

Section "Install"
  SetOutPath "$INSTDIR"
  File "dist\SanhuuPet.exe"

  ; 桌面快捷方式
  CreateShortCut "$DESKTOP\三虎桌宠.lnk" "$INSTDIR\${APP_EXE}"
  ; 开始菜单
  CreateDirectory "$SMPROGRAMS\三虎桌宠"
  CreateShortCut "$SMPROGRAMS\三虎桌宠\三虎桌宠.lnk" "$INSTDIR\${APP_EXE}"
  CreateShortCut "$SMPROGRAMS\三虎桌宠\卸载三虎桌宠.lnk" "$INSTDIR\uninstall.exe"

  ; 开机自启
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "SanhuuPet" '"$INSTDIR\${APP_EXE}"'

  ; 卸载信息
  WriteUninstaller "$INSTDIR\uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SanhuuPet" "DisplayName" "三虎桌宠 Sanhuu Pet"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SanhuuPet" "UninstallString" '"$INSTDIR\uninstall.exe"'
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\三虎桌宠.lnk"
  RMDir /r "$SMPROGRAMS\三虎桌宠"
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "SanhuuPet"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SanhuuPet"
  RMDir /r "$INSTDIR"
SectionEnd
