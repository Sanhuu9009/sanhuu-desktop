# 三虎 Sanhuu —— Windows 一键构建:生成 dist\Sanhuu-Setup-1.0.0.exe
# 需要:Python 3.10+、Inno Setup 6(https://jrsoftware.org/isdl.php)、7-Zip(用于内置 rar 解压)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..\..")
python -m pip install -r requirements.txt pyinstaller
New-Item -ItemType Directory -Force vendor | Out-Null
$seven = Join-Path $env:ProgramFiles "7-Zip"
if (Test-Path "$seven\7z.exe") { Copy-Item "$seven\7z.exe","$seven\7z.dll" vendor -Force }
else { Write-Warning "没找到 7-Zip:安装包将不内置 rar 解压(用户电脑装了 7-Zip / WinRAR 时仍可用)" }
python -m PyInstaller --noconfirm packaging\sanhuu.spec
$iscc = @("${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw "没找到 Inno Setup 6 的 ISCC.exe,请先安装 Inno Setup 6" }
& $iscc packaging\windows\installer.iss
Write-Host "完成:dist\Sanhuu-Setup-1.0.0.exe"
