@echo off
rem -----------------------------------------------------------------
rem  TaskBar Launcher - opens ALL apps from apps.txt with one click.
rem  This file is what you pin to the taskbar (no Python needed!).
rem -----------------------------------------------------------------
setlocal
cd /d "%~dp0"

if exist "apps.txt" goto run
echo # First run: creating a starter list...
start "" /min launcher.pyw --edit
goto :eof

:run
rem Prefer pythonw.exe so no console window flashes.
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw launcher.pyw
    goto :eof
)
where python >nul 2>nul
if %errorlevel%==0 (
    start "" python launcher.pyw
    goto :eof
)
for /f "delims=" %%P in ('where /r "%LOCALAPPDATA%\Programs\Python" pythonw.exe 2^>nul') do (
    start "" "%%P" launcher.pyw
    goto :eof
)
echo Python was not found. Install it from https://www.python.org/downloads/
pause
