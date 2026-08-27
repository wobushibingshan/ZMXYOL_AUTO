@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo 未找到 python。请先安装 Python 3.12，并勾选 Add python.exe to PATH。
    exit /b 1
)

echo [1/2] 准备 OCR 模型
python tools\configure.py
if errorlevel 1 exit /b 1

echo [2/2] 同步到 D:\ZMXY_AUTO\ZMXYOL_AUTO-win-x86_64
python tools\sync_to_runtime.py --dest "D:\ZMXY_AUTO\ZMXYOL_AUTO-win-x86_64"
if errorlevel 1 exit /b 1

echo.
echo 同步完成。请关闭 MFA 后再打开 D:\ZMXY_AUTO\ZMXYOL_AUTO-win-x86_64\MFAAvalonia.exe
endlocal
