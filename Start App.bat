@echo off
setlocal

echo.
echo  ███╗   ██╗███████╗██╗   ██╗██████╗  ██████╗ ██████╗ ██╗   ██╗██╗     ███████╗███████╗
echo  ████╗  ██║██╔════╝██║   ██║██╔══██╗██╔═══██╗██╔══██╗██║   ██║██║     ██╔════╝██╔════╝
echo  ██╔██╗ ██║█████╗  ██║   ██║██████╔╝██║   ██║██████╔╝██║   ██║██║     ███████╗█████╗
echo  ██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔═══╝ ██║   ██║██║     ╚════██║██╔══╝
echo  ██║ ╚████║███████╗╚██████╔╝██║  ██║╚██████╔╝██║     ╚██████╔╝███████╗███████║███████╗
echo  ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝      ╚═════╝ ╚══════╝╚══════╝╚══════╝
echo.
echo  AI ^& Tech News — Powered by Gemini AI  ^|  40+ Sources  ^|  v2.0
echo  ====================================================================
echo.

echo [1/4] Checking Python environment...
if exist "venv\Scripts\activate.bat" goto :activate_venv

echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat
echo Installing dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: pip install failed. Make sure Python 3.10+ is installed and in PATH.
    pause
    exit /b 1
)
goto :env_ready

:activate_venv
call venv\Scripts\activate.bat

:env_ready

echo.
echo [2/4] Loading environment variables from .env ...
if not exist ".env" (
    echo WARNING: .env file not found! Copy .env.example to .env and add your API keys.
    echo          AI summarization will fall back to extractive mode.
    echo.
)

echo [3/4] Creating data directory and initialising database...
if not exist "data" mkdir data
python -c "from backend.database import init_db; init_db()"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Database init failed.
    pause
    exit /b 1
)

echo.
echo [4/4] Starting server...
echo.
echo  ✓ Open your browser at: http://localhost:8000
echo  ✓ First fetch + AI summarization starts in ~15 seconds
echo  ✓ Auto-refreshes every 2 hours
echo  ✓ Gemini AI key: loaded from .env
echo  ✓ Press Ctrl+C to stop
echo.

start http://localhost:8000
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

endlocal
