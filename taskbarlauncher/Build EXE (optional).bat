@echo off
rem -----------------------------------------------------------------
rem  (Optional) Builds a standalone TaskBarLauncher.exe so you do NOT
rem  need Python installed. Only run this once, on a PC with Python.
rem  Needs:  pip install pyinstaller pillow
rem -----------------------------------------------------------------
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if not %errorlevel%==0 (
    echo Python was not found. Install it from https://www.python.org/downloads/
    pause & exit /b 1
)

python -m PyInstaller --version >nul 2>nul
if not %errorlevel%==0 (
    echo Installing pyinstaller and pillow...
    python -m pip install --user pyinstaller pillow
)

python -m PyInstaller --noconfirm --onefile --windowed ^
    --name TaskBarLauncher ^
    --icon launcher.ico ^
    launcher.pyw

if exist dist\TaskBarLauncher.exe (
    copy /y dist\TaskBarLauncher.exe . >nul
    echo.
    echo   All done!  TaskBarLauncher.exe is ready in this folder.
    echo   Double-click "Edit My Apps.bat" to change your apps, or open the exe.
) else (
    echo   Build failed - check the messages above.
)
pause
