@echo off
title VN30 Data Update
echo ========================================
echo VN30 Data Update Utility
echo ========================================
echo.
echo Updating VN30 universe and data...
echo.

"C:\Users\84378\.venv\Scripts\python.exe" -m src.app.cli.main update-universe
"C:\Users\84378\.venv\Scripts\python.exe" -m src.app.cli.main backfill-ohlcv --days 365

echo.
echo ========================================
echo Data update completed!
echo ========================================
pause
