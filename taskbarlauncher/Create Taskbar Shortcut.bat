@echo off
rem -----------------------------------------------------------------
rem  Creates a "TaskBar Launcher" shortcut on your Desktop and in the
rem  Start Menu. Right-click that shortcut and choose "Pin to taskbar".
rem  Works even if Python is not installed (falls back to the .bat).
rem -----------------------------------------------------------------
setlocal
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "Create Shortcut.ps1"

pause
