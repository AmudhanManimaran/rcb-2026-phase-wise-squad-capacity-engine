#!/usr/bin/env bash
# Optional: serve the frontend separately on port 5500 (the API must run on 8000)
cd "$(dirname "$0")/../frontend"
python -m http.server 5500
