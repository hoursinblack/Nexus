@echo off
echo ============================================
echo   Nexus — Building standalone .exe
echo ============================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Install Python 3.11+ first.
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo [2/3] Building Nexus.exe with PyInstaller...
pyinstaller nexus.spec --noconfirm
if %errorlevel% neq 0 (
    echo ERROR: Build failed.
    pause
    exit /b 1
)

echo.
echo [3/3] Done!
echo.
echo   Output: dist\Nexus.exe
echo   Run it as Administrator (right-click → Run as administrator)
echo.
pause
