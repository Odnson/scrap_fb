@echo off
REM Facebook Group Scraper - Build Installer Script

echo ============================================================
echo Facebook Group Scraper - Build Installer
echo ============================================================
echo.

REM Cek PyInstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 goto install_pyi
goto check_iscc

:install_pyi
echo [INFO] Installing PyInstaller...
pip install pyinstaller
if errorlevel 1 goto err_pyi
goto check_iscc

:err_pyi
echo [ERROR] Gagal install PyInstaller.
pause
exit /b 1

:check_iscc
where iscc >nul 2>nul
if errorlevel 1 goto err_iscc
goto build_exe

:err_iscc
echo [ERROR] Inno Setup Compiler tidak ditemukan.
echo Download dari: https://jrsoftware.org/isdl.php
pause
exit /b 1

:build_exe
echo [1/3] Building EXE dengan PyInstaller...
echo.
echo 1 | python build_exe.py
if errorlevel 1 goto err_build
goto check_dist

:err_build
echo [ERROR] Build EXE gagal!
pause
exit /b 1

:check_dist
echo.
echo [2/3] Checking dist folder...
if not exist "dist\FacebookScraperGUI.exe" goto err_dist
goto build_inst

:err_dist
echo [ERROR] FacebookScraperGUI.exe tidak ditemukan di dist/
pause
exit /b 1

:build_inst
echo.
echo [3/3] Building installer dengan Inno Setup...
echo.
iscc installer.iss
if errorlevel 1 goto err_inst
goto success

:err_inst
echo [ERROR] Build installer gagal!
pause
exit /b 1

:success
echo.
echo ============================================================
echo [SUCCESS] Installer berhasil dibuat!
echo Lokasi: installer_output\FacebookGroupScraper_Setup.exe
echo ============================================================
echo.
pause
