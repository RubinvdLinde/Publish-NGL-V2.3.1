@echo off
cd /d "%~dp0"
python apply_ngl_new_games.py
if errorlevel 1 pause
