@echo off
setlocal

REM Builds a Windows EXE and ensures the audios folder ships with it.
REM Run this from the repo root (same folder as exam_timer_app.py).

set "PYTHON=python"
where python >nul 2>nul
if errorlevel 1 (
  set "PYTHON=py -3"
)

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

%PYTHON% -m pip install --upgrade pip
%PYTHON% -m pip install -r requirements.txt
%PYTHON% -m pip install pyinstaller

%PYTHON% -m PyInstaller ^
  --noconsole ^
  --onefile ^
  --name ExamTimer ^
  --add-data "audios;audios" ^
  exam_timer_app.py

if not exist dist\ExamTimer.exe (
  echo Build failed: dist\ExamTimer.exe not found.
  exit /b 1
)

REM Also copy audios next to the EXE as a simple distribution layout.
xcopy /E /I /Y audios dist\audios >nul

echo.
echo Done.
echo - EXE:   dist\ExamTimer.exe
echo - Audio: dist\audios\
echo.
echo Distribute the dist\ folder contents together.

endlocal
