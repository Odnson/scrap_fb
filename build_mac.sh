#!/bin/bash
# Facebook Group Scraper - Build Script for macOS
# Script ini akan build .app bundle dan .dmg image

echo "============================================================"
echo "Facebook Group Scraper - Build for macOS"
echo "============================================================"
echo ""

# Cek PyInstaller
python3 -c "import PyInstaller" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[INFO] Installing PyInstaller..."
    pip3 install pyinstaller
    if [ $? -ne 0 ]; then
        echo "[ERROR] Gagal install PyInstaller."
        exit 1
    fi
fi

echo "[1/3] Building .app bundle with PyInstaller..."
echo ""
pyinstaller --name="FacebookScraperGUI" \
            --windowed \
            --onefile \
            --icon=icon.icns \
            --add-data=scrape_posts_v3.py:. \
            --add-data=requirements.txt:. \
            facebook_scraper_gui.py

if [ $? -ne 0 ]; then
    echo "[ERROR] Build .app gagal!"
    exit 1
fi

echo ""
echo "[2/3] Checking dist folder..."
if [ ! -f "dist/FacebookScraperGUI.app/Contents/MacOS/FacebookScraperGUI" ]; then
    echo "[ERROR] FacebookScraperGUI.app tidak ditemukan di dist/"
    exit 1
fi

echo ""
echo "[3/3] Creating .dmg image..."
echo ""

# Cek apakah create-dmg terinstall
if command -v create-dmg &> /dev/null; then
    # Gunakan create-dmg jika tersedia
    create-dmg --volname "Facebook Group Scraper" \
               --volicon "icon.icns" \
               --window-pos 200 120 \
               --window-size 600 300 \
               --icon-size 100 \
               --icon "FacebookScraperGUI.app" 175 120 \
               --hide-extension "FacebookScraperGUI.app" \
               --app-drop-link 425 120 \
               "FacebookGroupScraper_Setup.dmg" \
               "dist/"
else
    # Gunakan hdiutil bawaan macOS
    echo "[INFO] create-dmg tidak terinstall, menggunakan hdiutil..."
    mkdir -p dmg_temp
    cp -R dist/FacebookScraperGUI.app dmg_temp/
    hdiutil create -volname "Facebook Group Scraper" \
                   -srcfolder dmg_temp \
                   -ov \
                   -format UDZO \
                   FacebookGroupScraper_Setup.dmg
    rm -rf dmg_temp
fi

if [ $? -ne 0 ]; then
    echo "[ERROR] Build .dmg gagal!"
    exit 1
fi

echo ""
echo "============================================================"
echo "[SUCCESS] Build macOS berhasil!"
echo "Lokasi: FacebookGroupScraper_Setup.dmg"
echo "============================================================"
echo ""
