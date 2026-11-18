@echo off
REM Build the database, generate the synthetic season, run backtest and calibration.
cd /d "%~dp0\.."
python -m backend.generator.data_loader %*
