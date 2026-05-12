"""
Scrape member dari Facebook group menggunakan Selenium
"""
import time
import csv
import json
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Konfigurasi
GROUP_MEMBERS_URL = "https://www.facebook.com/groups/894614057345113/members"
EMAIL = "hajibambang97@gmail.com"
PASSWORD = "matamu97"
COOKIES_FILE = "facebook_cookies.json"

def setup_driver():
    """Setup Chrome WebDriver dengan opsi yang diperlukan"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def load_cookies_from_file(driver, filename):
    """Muat cookies dari file"""
    try:
        with open(filename, 'r') as f:
            cookies = json.load(f)
        
        driver.get("https://www.facebook.com")
        for cookie in cookies:
            driver.add_cookie(cookie)
        
        driver.refresh()
        time.sleep(3)
        
        # Cek apakah masih login
        current_url = driver.current_url
        if "login" not in current_url:
            print("Berhasil login dengan cookies yang tersimpan!")
            return True
        else:
            print("Cookies tidak valid, perlu login ulang")
            return False
    except FileNotFoundError:
        print("File cookies tidak ditemukan")
        return False
    except Exception as e:
        print(f"Error memuat cookies: {e}")
        return False

def login_facebook(driver, email, password):
    """Login ke Facebook dengan email dan password"""
    try:
        print("Mencoba login ke Facebook...")
        driver.get("https://www.facebook.com")
        time.sleep(3)
        
        # Cari field email
        email_selectors = [
            (By.ID, "email"),
            (By.NAME, "email"),
            (By.CSS_SELECTOR, "input[name='email']"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.XPATH, "//input[@name='email']")
        ]
        
        email_field = None
        for selector_type, selector in email_selectors:
            try:
                email_field = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((selector_type, selector))
                )
                break
            except:
                continue
        
        if email_field:
            email_field.clear()
            for char in email:
                email_field.send_keys(char)
                time.sleep(0.1)
            time.sleep(1)
        
        # Cari field password
        password_selectors = [
            (By.ID, "pass"),
            (By.NAME, "pass"),
            (By.CSS_SELECTOR, "input[name='pass']"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.XPATH, "//input[@name='pass']")
        ]
        
        password_field = None
        for selector_type, selector in password_selectors:
            try:
                password_field = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((selector_type, selector))
                )
                break
            except:
                continue
        
        if password_field:
            password_field.clear()
            for char in password:
                password_field.send_keys(char)
                time.sleep(0.1)
            time.sleep(1)
        
        # Cari tombol login
        login_selectors = [
            (By.NAME, "login"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.CSS_SELECTOR, "button[name='login']"),
            (By.XPATH, "//button[@name='login']"),
            (By.XPATH, "//button[@type='submit']")
        ]
        
        login_button = None
        for selector_type, selector in login_selectors:
            try:
                login_button = driver.find_element(selector_type, selector)
                break
            except:
                continue
        
        if login_button:
            login_button.click()
            time.sleep(5)
        
        # Cek apakah login berhasil
        current_url = driver.current_url
        if "login" not in current_url:
            print("Login berhasil!")
            return True
        else:
            print("Login gagal, mencoba JavaScript...")
            driver.execute_script("""
                document.querySelector('input[name="email"]').value = arguments[0];
                document.querySelector('input[name="pass"]').value = arguments[1];
                document.querySelector('button[name="login"]').click();
            """, email, password)
            time.sleep(5)
            
            current_url = driver.current_url
            if "login" not in current_url:
                print("Login berhasil dengan JavaScript!")
                return True
        
        return False
    except Exception as e:
        print(f"Error saat login: {e}")
        return False

def scrape_group_members(driver, members_url, num_members=None, scroll_delay=3, members_callback=None, save_callback=None):
    """Scrape member dari Facebook group dengan infinity scroll"""
    print(f"Membuka halaman members: {members_url}")
    driver.get(members_url)
    time.sleep(10)  # Tunggu loading
    
    members_data = []
    scroll_count = 0
    no_new_members_count = 0
    max_no_new = 10  # Berhenti jika tidak ada member baru setelah 10 scroll
    last_save_count = 0
    
    while True:
        # Scroll ke bawah untuk memuat lebih banyak member
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_delay)
        
        # Cari elemen member
        member_selectors = [
            (By.CSS_SELECTOR, "[data-testid='mwt-card-list']"),
            (By.CSS_SELECTOR, "[data-testid='group_member_item']"),
            (By.CSS_SELECTOR, "[role='listitem']"),
            (By.CSS_SELECTOR, ".x1yztbdb .x1lliihq")
        ]
        
        member_elements = []
        for selector_type, selector in member_selectors:
            try:
                member_elements = driver.find_elements(selector_type, selector)
                if member_elements:
                    print(f"Ditemukan {len(member_elements)} elemen dengan selector: {selector}")
                    break
            except:
                continue
        
        if not member_elements:
            print("Tidak menemukan member dengan selector manapun")
            time.sleep(2)
            scroll_count += 1
            no_new_members_count += 1
            if no_new_members_count >= max_no_new:
                print(f"Tidak ada member baru setelah {max_no_new} scroll. Berhenti.")
                break
            continue
        
        # Ekstrak data member
        new_members_count = 0
        for member in member_elements:
            try:
                member_text = member.text.strip()
                
                # Filter teks yang terlalu pendek
                if member_text and len(member_text) > 2:
                    # Cari link profil member
                    profile_url = ''
                    try:
                        link_element = member.find_element(By.TAG_NAME, 'a')
                        profile_url = link_element.get_attribute('href')
                    except:
                        pass
                    
                    # Cek duplikat berdasarkan nama atau URL
                    is_duplicate = False
                    for existing in members_data:
                        if existing['name'] == member_text[:100] or (profile_url and existing['profile_url'] == profile_url):
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        members_data.append({
                            'name': member_text[:200] if len(member_text) > 200 else member_text,
                            'profile_url': profile_url
                        })
                        new_members_count += 1
                        print(f"Member {len(members_data)}: {member_text[:50]}... (URL: {profile_url[:30] if profile_url else 'No URL'}...)")
                        
                        # Update data secara real-time melalui callback
                        if members_callback:
                            members_callback(members_data)
                        
                        # Save partial setiap 10 member baru
                        if save_callback and len(members_data) - last_save_count >= 10:
                            save_callback(members_data)
                            last_save_count = len(members_data)
                        
                        if num_members and len(members_data) >= num_members:
                            break
            except:
                continue
        
        scroll_count += 1
        print(f"Scroll {scroll_count}, Total member: {len(members_data)}, Member baru: {new_members_count}")
        
        # Reset counter jika ada member baru
        if new_members_count > 0:
            no_new_members_count = 0
        else:
            no_new_members_count += 1
        
        # Berhenti jika tidak ada member baru setelah beberapa scroll
        if no_new_members_count >= max_no_new:
            print(f"Tidak ada member baru setelah {max_no_new} scroll. Berhenti.")
            break
        
        # Berhenti jika sudah mencapai jumlah member yang diinginkan
        if num_members and len(members_data) >= num_members:
            print(f"Sudah mencapai target {num_members} member. Berhenti.")
            break
    
    return members_data

def save_members_to_csv(members, filename, start_time=None, end_time=None):
    """Simpan member ke CSV file"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['no', 'name', 'profile_url', 'scrape_start_time',
                         'scrape_end_time', 'scraped_at']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for i, member in enumerate(members, 1):
                writer.writerow({
                    'no': i,
                    'name': member['name'],
                    'profile_url': member['profile_url'],
                    'scrape_start_time': start_time.strftime("%Y-%m-%d %H:%M:%S") if start_time else '',
                    'scrape_end_time': end_time.strftime("%Y-%m-%d %H:%M:%S") if end_time else now,
                    'scraped_at': now
                })
        print(f"Hasil disimpan ke: {filename}")
        return True
    except Exception as e:
        print(f"Error menyimpan ke CSV: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("Facebook Group Members Scraper")
    print("=" * 60)
    print("Tekan Ctrl+C untuk berhenti dan menyimpan hasil sementara")
    
    # Setup logging
    log_file = "facebook_group_members_log.txt"
    
    def log_message(message):
        """Log ke file dan console"""
        print(message)
        with open(log_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")
    
    # Track waktu
    start_time = datetime.now()
    log_message(f"Scrape dimulai: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_message(f"Group Members URL: {GROUP_MEMBERS_URL}")
    
    # Setup driver
    driver = setup_driver()
    members = []
    
    # Callback untuk update data secara real-time dan save partial
    def update_members(current_members):
        nonlocal members
        members = current_members.copy()
    
    def save_partial(data):
        """Save partial data"""
        if data:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"facebook_group_members_partial_{timestamp}.csv"
            save_members_to_csv(data, filename, start_time, datetime.now())
            log_message(f"Partial save: {len(data)} members")
    
    try:
        # Coba gunakan file cookies yang sudah tersimpan
        log_message("Mencoba menggunakan file cookies yang tersimpan...")
        if load_cookies_from_file(driver, COOKIES_FILE):
            log_message("Berhasil login dengan file cookies yang tersimpan!")
        else:
            log_message("File cookies tidak valid, mencoba login manual...")
            if not login_facebook(driver, EMAIL, PASSWORD):
                log_message("Gagal login ke Facebook")
                return
        
        # Scrape members dengan infinity scroll dan delay
        members = scrape_group_members(driver, GROUP_MEMBERS_URL, num_members=None, scroll_delay=3, members_callback=update_members, save_callback=save_partial)
        
        # Tampilkan hasil
        log_message("\n" + "=" * 50)
        log_message("HASIL SCRAPE MEMBER")
        log_message("=" * 50)
        for i, member in enumerate(members[:10], 1):
            log_message(f"\nMember {i}:")
            log_message(f"Name: {member['name']}")
            log_message(f"Profile URL: {member['profile_url']}")
        
        log_message(f"\nTotal member yang diambil: {len(members)}")
        
        # Simpan ke CSV
        if members:
            end_time = datetime.now()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"facebook_group_members_{timestamp}.csv"
            save_members_to_csv(members, filename, start_time, end_time)
            log_message(f"Scrape selesai: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            log_message(f"Total waktu: {end_time - start_time}")
            log_message(f"Total members: {len(members)}")
        
    except KeyboardInterrupt:
        end_time = datetime.now()
        log_message("\n[INTERRUPTED] Menyimpan member yang sudah diambil...")
        
        if members:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"facebook_group_members_{timestamp}_interrupted.csv"
            save_members_to_csv(members, filename, start_time, end_time)
            log_message(f"Total member yang disimpan: {len(members)}")
            log_message(f"Total waktu: {end_time - start_time}")
        else:
            log_message("Tidak ada data yang tersimpan")
        
    except Exception as e:
        print(f"Error: {e}")
        # Simpan data yang sudah terkumpul jika terjadi error
        if members:
            print("Menyimpan data yang sudah terkumpul...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"facebook_group_members_{timestamp}_error.csv"
            save_members_to_csv(members, filename)
    finally:
        # Tutup browser
        print("Menutup browser...")
        time.sleep(2)
        driver.quit()

if __name__ == "__main__":
    main()
