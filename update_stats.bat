@echo off
cd /d "%~dp0"

py stat_pipeline.py
if %errorlevel% neq 0 (
  echo Export failed. Close Excel and try again.
  pause
  exit /b 1
)

git add data/*.json
git diff --cached --quiet
if %errorlevel%==0 (
  echo No JSON changes detected.
  pause
  exit /b 0
)

git commit -m "Update stats"
git push

echo Done. Website will update shortly.
pause