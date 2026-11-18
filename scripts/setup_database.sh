#!/usr/bin/env bash
# Build the database, generate the synthetic season, run backtest and calibration.
set -e
cd "$(dirname "$0")/.."
python -m backend.generator.data_loader "$@"
