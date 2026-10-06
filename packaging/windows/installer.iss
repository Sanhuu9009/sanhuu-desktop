; 三虎 Sanhuu 安装程序(Inno Setup 6)。编译:ISCC packaging\windows\installer.iss
; 美术素材版权 © 三虎 Sanhuu,保留所有权利。未经许可,禁止商用、二次修改、转载传播。
#define AppVer "1.0.0"

[Setup]
AppId={{8E3B6C1A-5A2F-4B7E-9C31-53414E485555}
AppName=三虎 Sanhuu
AppVersion={#AppVer}
AppVerName=三虎 Sanhuu {#AppVer}
AppPublisher=三虎 Sanhuu
AppCopyright=美术素材版权 © 三虎 Sanhuu,保留所有权利。
DefaultDirName={autopf}\Sanhuu
DefaultGroupName=三虎 Sanhuu
DisableProgramGroupPage=yes
DisableWelcomePage=no
PrivilegesRequired=lowest
OutputDir=..\..\dist
OutputBaseFilename=Sanhuu-Setup-{#AppVer}
SetupIconFile=..\..\assets\icon.ico
UninstallDisplayIcon={app}\Sanhuu.exe
WizardStyle=modern
WizardImageFile=..\..\assets\installer\wizard_164.bmp,..\..\assets\installer\wizard_328.bmp
WizardSmallImageFile=..\..\assets\installer\small_55.bmp,..\..\assets\installer\small_110.bmp
LicenseFile=..\..\COPYRIGHT.txt
Compression=lzma2/max
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes

[Languages]
Name: "zh"; MessagesFile: "compiler:Default.isl"

[Messages]
SetupWindowTitle=把三虎 Sanhuu 接回家
WelcomeLabel1=嗷呜!我是三虎 Sanhuu
WelcomeLabel2=一只白毛黑纹、橙色眼睛的像素小老虎,想搬到你的桌面上住。%n%n我会看天气、截图录屏、转格式、压缩解压,还能帮你记待办、定闹钟。%n%n点「下一步」,带我回家吧!
ButtonNext=下一步(&N) >
ButtonBack=< 上一步(&B)
ButtonInstall=接它回家(&I)
ButtonCancel=取消
ButtonFinish=完成(&F)
ButtonBrowse=浏览(&R)...
WizardLicense=版权声明
LicenseLabel=继续之前,请先看一眼三虎的版权声明。
LicenseLabel3=请阅读下面的版权声明。同意后才能继续安装。
LicenseAccepted=我知道了,并且同意(&A)
LicenseNotAccepted=我不同意(&D)
WizardSelectDir=三虎的小窝放在哪儿?
SelectDirDesc=选择三虎 Sanhuu 的安装位置
SelectDirLabel3=三虎会住进下面这个文件夹。
SelectDirBrowseLabel=点「下一步」继续;想换个地方,就点「浏览」。
WizardSelectTasks=再帮三虎做两个小决定
SelectTasksDesc=要不要顺手做这些事?
SelectTasksLabel2=勾选你想要的,然后点「下一步」。
WizardReady=准备好了
ReadyLabel1=马上就能把三虎接到你的电脑上。
ReadyLabel2a=点「接它回家」开始安装;想改设置就点「上一步」。
ReadyLabel2b=点「接它回家」开始安装。
WizardInstalling=三虎正在搬家
InstallingLabel=正在把行李(和尾巴)搬进来,请稍等……
FinishedHeadingLabel=三虎到家啦!
FinishedLabel=三虎 Sanhuu 已经住进你的电脑。单击它弹出菜单,双击它去溜达,把文件拖给它可以转格式。
FinishedLabelNoIcons=三虎 Sanhuu 已经住进你的电脑。
ClickFinish=点「完成」退出安装程序。
ExitSetupTitle=不带三虎回家了吗?
ExitSetupMessage=安装还没完成。现在退出的话,三虎就进不了家门了。%n%n确定要退出吗?

[Tasks]
Name: "desktopicon"; Description: "在桌面放一个三虎的图标"
Name: "autostart"; Description: "开机后三虎自动出来上班"

[Files]
Source: "..\..\dist\Sanhuu\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\..\COPYRIGHT.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\三虎 Sanhuu"; Filename: "{app}\Sanhuu.exe"
Name: "{group}\卸载三虎 Sanhuu"; Filename: "{uninstallexe}"
Name: "{autodesktop}\三虎 Sanhuu"; Filename: "{app}\Sanhuu.exe"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "Sanhuu"; ValueData: """{app}\Sanhuu.exe"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\Sanhuu.exe"; Description: "现在就把三虎放到桌面上"; Flags: nowait postinstall skipifsilent

[Code]
var
  CityPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  { 三虎主题色:橙色眼睛 = $1E57E8(BGR) }
  WizardForm.WelcomeLabel1.Font.Color := $1E57E8;
  WizardForm.FinishedHeadingLabel.Font.Color := $1E57E8;
  WizardForm.PageNameLabel.Font.Color := $1E57E8;
  CityPage := CreateInputQueryPage(wpSelectTasks,
    '三虎想知道你在哪座城市',
    '快下雨的时候,它会提前撑伞提醒你',
    '输入你所在的城市(中文、英文都可以)。也可以留空,之后在三虎的「天气」里再设置。');
  CityPage.Add('城市:', False);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Dir: String;
  Lines: TArrayOfString;
begin
  if (CurStep = ssPostInstall) and (Trim(CityPage.Values[0]) <> '') then
  begin
    Dir := ExpandConstant('{userappdata}\Sanhuu');
    ForceDirectories(Dir);
    SetArrayLength(Lines, 1);
    Lines[0] := Trim(CityPage.Values[0]);
    SaveStringsToUTF8File(Dir + '\installer_city.txt', Lines, False);
  end;
end;
