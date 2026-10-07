@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-duemap.ps1" %*
if errorlevel 1 (
  echo.
  echo DueMap could not start. See the message above for details.
  pause
)
endlocal
