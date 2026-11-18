#!/usr/bin/env bash
# Start the API and serve the dashboard at http://127.0.0.1:8000/
set -e
cd "$(dirname "$0")/.."
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
