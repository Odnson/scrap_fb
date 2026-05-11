"""
Script untuk build EXE menggunakan PyInstaller
"""
import os
import sys
import subprocess

def build_gui():
    """Build GUI version ke EXE"""
    print("Building GUI version to EXE...")
    
    cmd = [
        "pyinstaller",
        "--name=FacebookScraperGUI",
        "--windowed",
        "--onefile",
        "--icon=icon.ico" if os.path.exists("icon.ico") else "",
        "--add-data=scrape_posts_v3.py;.",
        "--add-data=requirements.txt;.",
        "facebook_scraper_gui.py"
    ]
    
    # Hapus empty strings
    cmd = [c for c in cmd if c]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n[SUCCESS] GUI EXE berhasil dibuat di dist/FacebookScraperGUI.exe")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Build gagal: {e}")
        sys.exit(1)

def build_cli():
    """Build CLI version ke EXE"""
    print("Building CLI version to EXE...")
    
    cmd = [
        "pyinstaller",
        "--name=FacebookScraperCLI",
        "--onefile",
        "--icon=icon.ico" if os.path.exists("icon.ico") else "",
        "--add-data=requirements.txt;.",
        "scrape_posts_v3.py"
    ]
    
    # Hapus empty strings
    cmd = [c for c in cmd if c]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n[SUCCESS] CLI EXE berhasil dibuat di dist/FacebookScraperCLI.exe")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Build gagal: {e}")
        sys.exit(1)

def build_all():
    """Build kedua versi (GUI dan CLI)"""
    print("=" * 60)
    print("Facebook Scraper - Build Script")
    print("=" * 60)
    print("\n1. Build GUI version")
    print("2. Build CLI version")
    print("3. Build both")
    print("0. Exit")
    
    choice = input("\nPilih opsi: ")
    
    if choice == "1":
        build_gui()
    elif choice == "2":
        build_cli()
    elif choice == "3":
        build_gui()
        build_cli()
    elif choice == "0":
        sys.exit(0)
    else:
        print("Pilihan tidak valid!")

if __name__ == "__main__":
    # Cek apakah PyInstaller terinstall
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller belum terinstall.")
        print("Install dengan: pip install pyinstaller")
        sys.exit(1)
    
    build_all()
