@echo off
REM Optional: serve the frontend separately on port 5500 (the API must run on 8000)
cd /d "%~dp0\..\frontend"
python -m http.server 5500
