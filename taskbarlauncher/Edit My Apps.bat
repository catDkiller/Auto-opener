@echo off
rem -----------------------------------------------------------------
rem  Opens the TaskBar Launcher editor so you can change your apps.
rem  (Double-click this file any time you want to edit the list.)
rem ---------------------------------------------------------------
setlocal
cd /d "%~dp0"

rem Prefer pythonw.exe (no black console window), fall back to python.exe
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw launcher.pyw --edit
    exit /b
)

where python >nul 2>nul
if %errorlevel%==0 (
    start "" python launcher.pyw --edit
    exit /b
)

for /f "delims=" %%P in ('where /r "%LOCALAPPDATA%\Programs\Python" pythonw.exe 2^>nul') do (
    start "" "%%P" launcher.pyw --edit
    exit /b
)

echo Python was not found on this PC.
echo Please install Python from https://www.python.org/downloads/
echo (tick "Add Python to PATH" during the install), then run this again.
pause
