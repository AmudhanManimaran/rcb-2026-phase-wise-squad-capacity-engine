@echo off
REM Start the API and serve the dashboard at http://127.0.0.1:8000/
cd /d "%~dp0\.."
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
