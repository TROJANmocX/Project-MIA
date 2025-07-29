@echo off
cd /d "%~dp0"
call .venv\Scripts\activate
python mia_launcher.py
pause
