@echo off
cd /d "%~dp0"
start "" "http://localhost:8783/?v=2.3.1"
python -m http.server 8783 --bind 127.0.0.1
