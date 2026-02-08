@echo off
title VN30 Trading Bot Manager
chcp 65001 >nul
cls

:menu
echo.
echo =================================================
echo    VN30 TRADING BOT - CONTROL PANEL
echo =================================================
echo 1. Start Bot (Auto Scheduler)
echo 2. Send Report NOW (Manual Trigger)
echo 3. Backfill Data (Last 5 Days)
echo 4. Exit
echo =================================================
set /p choice="Enter option (1-4): "

if "%choice%"=="1" goto scheduler
if "%choice%"=="2" goto report
if "%choice%"=="3" goto backfill
if "%choice%"=="4" goto exit

echo Invalid choice.
pause
goto menu

:scheduler
cls
echo [INFO] Starting Scheduler (Running every 60 mins)...
echo [INFO] Press Ctrl+C to stop.
"C:\Users\84378\.venv\Scripts\python.exe" -m src.app.cli.main schedule
pause
goto menu

:report
cls
echo [INFO] Generating Report and Sending to Telegram...
"C:\Users\84378\.venv\Scripts\python.exe" send_report_now.py
pause
goto menu

:backfill
cls
echo [INFO] Backfilling OHLCV Data (Last 5 Days)...
"C:\Users\84378\.venv\Scripts\python.exe" -m src.app.cli.main backfill-ohlcv --days 5
pause
goto menu

:exit
exit
