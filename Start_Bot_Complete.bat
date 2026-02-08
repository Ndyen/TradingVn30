@echo off
title VN30 Trading Bot - Complete Setup
echo ========================================
echo VN30 Trading Bot - Complete Setup
echo ========================================
echo.

echo Step 1: Updating VN30 universe...
"C:\Users\84378\.venv\Scripts\python.exe" -m src.app.cli.main update-universe
if errorlevel 1 (
    echo WARNING: Universe update failed
) else (
    echo SUCCESS: Universe updated
)
echo.

echo Step 2: Backfilling OHLCV data (365 days)...
"C:\Users\84378\.venv\Scripts\python.exe" -m src.app.cli.main backfill-ohlcv --days 365
if errorlevel 1 (
    echo WARNING: Backfill failed
) else (
    echo SUCCESS: Data backfilled
)
echo.

echo Step 3: Starting scheduler...
echo The bot will now run analysis every hour.
echo Press Ctrl+C to stop.
echo.
"C:\Users\84378\.venv\Scripts\python.exe" -m src.app.cli.main schedule
pause
