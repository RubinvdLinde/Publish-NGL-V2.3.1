@echo off
cd /d "%~dp0"
setlocal
python --version >nul 2>&1
if errorlevel 1 (
  echo Python was not found. Open the same Python installation you used for NGL.
  pause
  exit /b 1
)
python -c "from PIL import Image, ImageTk; import tkinter" >nul 2>&1
if errorlevel 1 (
  echo This cover updater needs Pillow for validating and previewing images.
  choice /C YN /M "Install Pillow using Python pip"
  if errorlevel 2 exit /b 1
  python -m pip install Pillow
  if errorlevel 1 (
    pause
    exit /b 1
  )
)
python replace_ngl_covers.py
pause
