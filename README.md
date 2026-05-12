# Facebook Group Scraper - Multi-Run GUI

Facebook Group Scraper dengan GUI untuk konfigurasi credential dan cookies. Support multi-run (bisa menjalankan beberapa instance sekaligus).

## Fitur

- **GUI Configuration** - Konfigurasi group URL, cookies, output directory, dll melalui GUI
- **Multi-Run Support** - Jalankan beberapa instance scraper sekaligus
- **Cookies Support** - Support format TXT (Netscape) dan JSON
- **Config File** - Simpan konfigurasi di file JSON untuk penggunaan berulang
- **Graceful Interrupt** - Stop dengan Ctrl+C dan data tetap tersimpan

## Instalasi

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Build untuk Windows

#### Build EXE

Jalankan script build:

```bash
python build_exe.py
```

Pilih opsi:
1. Build GUI version
2. Build CLI version
3. Build both

EXE akan dibuat di folder `dist/`.

#### Build Installer (Windows)

Untuk membuat installer yang siap didistribusikan:

1. Install Inno Setup dari https://jrsoftware.org/isdl.php
2. Jalankan script batch:

```bash
build_installer.bat
```

Script ini akan:
- Build EXE dengan PyInstaller
- Build installer dengan Inno Setup
- Installer akan dibuat di folder `installer_output/`

Atau manual:
1. Build EXE dengan `python build_exe.py`
2. Jalankan `iscc installer.iss` (Inno Setup Compiler)

Installer akan bernama `FacebookGroupScraper_Setup.exe`.

### Build untuk macOS

#### Build .app

Jalankan script build:

```bash
python3 build_exe.py
```

Atau gunakan script khusus Mac:

```bash
chmod +x build_mac.sh
./build_mac.sh
```

Script `build_mac.sh` akan:
- Build .app bundle dengan PyInstaller
- Create .dmg image untuk distribusi
- .dmg akan dibuat di folder `FacebookGroupScraper_Setup.dmg`

#### Opsional: Install create-dmg untuk .dmg yang lebih bagus

```bash
brew install create-dmg
```

## Penggunaan

### GUI Version

1. Jalankan `FacebookScraperGUI.exe`
2. Tab **Konfigurasi**:
   - **Group URL**: URL group Facebook yang ingin di-scrape
   - **Tipe Cookies**: `txt` atau `json`
   - **File Cookies**: Pilih file cookies (cookies.txt atau facebook_cookies.json)
   - **Output Directory**: Folder untuk menyimpan hasil scrape
   - **Max Posts**: Jumlah maksimal post yang ingin di-scrape
   - **Buka Modal Komentar**: Centang jika ingin scrape semua komentar (lebih lambat)
3. Klik **Simpan Konfigurasi**
4. Tab **Multi-Run**:
   - **Jumlah Instance**: Jumlah instance yang ingin dijalankan (1-10)
   - Klik **Start Multi-Run** untuk memulai
   - Klik **Stop All** untuk menghentikan semua instance
5. Tab **Logs**: Lihat log running instances

### CLI Version

Jalankan `FacebookScraperCLI.exe` atau:

```bash
python scrape_posts_v3.py
```

Script akan otomatis membaca konfigurasi dari `scraper_config.json`.

## Format Cookies

### TXT Format (Netscape)

```
# Netscape HTTP Cookie File
# Facebook cookies only

.facebook.com	TRUE	/	TRUE	1793616437	sb	HyiiZwjEzXXWOEu9dfhNDIae
.facebook.com	TRUE	/	TRUE	1809926176	c_user	100052644802561
.facebook.com	TRUE	/	TRUE	0	presence	C%7B%22t3%22%3A%5B%5D%2C%22utc3%22%3A1778390176005%2C%22v%22%3A1%7D
.facebook.com	TRUE	/	TRUE	1786166176	fr	10LxnrcbKFeazY2f7.AWcNMhXa0n4bPWcSlBuamhzBCAALlNIzT8l4KVnpB1aJw82pB3M.BqABSM..AAA.0.0.BqABSM.AWdtI2mMiCq7AXq0BZXYnaJpWrY
.facebook.com	TRUE	/	TRUE	1809926176	xs	1%3Ab7pLIIEEVe-c0A%3A2%3A1759056435%3A-1%3A-1%3A%3AAczZvwhlElu8cFvSYxhTwdchdiGqd_80kBSd_A7JHbo
```

### JSON Format

```json
[
  {
    "name": "sb",
    "value": "HyiiZwjEzXXWOEu9dfhNDIae",
    "domain": ".facebook.com",
    "path": "/",
    "secure": true,
    "expiry": 1793616437
  },
  {
    "name": "c_user",
    "value": "100052644802561",
    "domain": ".facebook.com",
    "path": "/",
    "secure": true,
    "expiry": 1809926176
  }
]
```

## Output

Hasil scrape akan disimpan sebagai CSV dengan format:

| no | poster_name | poster_profile_url | post_content | post_image_urls | post_url | post_date | commenter_name | commenter_profile_url | comment_text | scraped_at |
|----|-------------|-------------------|--------------|-----------------|----------|-----------|----------------|----------------------|--------------|------------|

- **1 baris per komentar** - Jika post memiliki 5 komentar, akan ada 5 baris untuk post tersebut
- Jika post memiliki 0 komentar, tetap ada 1 baris dengan kolom commenter kosong

## Multi-Run

Multi-run memungkinkan menjalankan beberapa instance scraper sekaligus. Setiap instance akan:
- Menggunakan konfigurasi yang sama
- Menyimpan hasil ke file yang berbeda (dengan suffix instance number)
- Dapat dimonitor dan dihentikan dari GUI

Contoh:
- Instance 1: `facebook_posts_v3_instance_1_20260511_143807.csv`
- Instance 2: `facebook_posts_v3_instance_2_20260511_143807.csv`
- Instance 3: `facebook_posts_v3_instance_3_20260511_143807.csv`

## Troubleshooting

### Login Gagal

Pastikan cookies valid dan belum expired. Update cookies dari browser:
1. Login ke Facebook di browser
2. Export cookies (gunakan extension seperti "EditThisCookie")
3. Simpan sebagai cookies.txt atau facebook_cookies.json

### Scroll Tidak Load Post Baru

- Tunggu lebih lama antar scroll
- Kurangi jumlah instance jika multi-run
- Cek koneksi internet

### Modal Komentar Tidak Berfungsi

Matikan opsi "Buka Modal Komentar" dan gunakan mode komentar visible saja (lebih cepat).

## Catatan

- Gunakan dengan bijak dan sesuai dengan Terms of Service Facebook
- Jangan gunakan untuk spam atau aktivitas ilegal
- Script ini untuk educational purpose only

## License

MIT License
