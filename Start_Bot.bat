@echo off
title VN30 Trading Bot - Auto Scheduler
echo Starting VN30 Bot...
"C:\Users\84378\.venv\Scripts\python.exe" -m src.app.cli.main schedule
pause
