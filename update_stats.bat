@echo off
cd /d "%~dp0"

echo.
echo ===============================
echo Updating League Stats...
echo ===============================
echo.

py stat_pipeline.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Something went wrong.
    echo Make sure Excel is CLOSED.
    pause
    exit /b
)

echo.
echo Stats successfully updated!
echo.
echo Now upload the updated JSON files in the DATA folder to GitHub.
echo.
pause