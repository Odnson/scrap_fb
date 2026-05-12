"""
Facebook Group Scraper V3 (berbasis V2 yang berhasil 300+ post)
- Text parsing untuk post content + komentar (logic V2)
- Tambahan: poster_profile_url, post_image_urls, commenter info dengan URL profile
- Format CSV: 1 baris per komentar (post dengan 3 komentar = 3 baris, info post sama)
- Jika post tanpa komentar, tetap 1 baris dengan kolom commenter kosong
- Menggunakan facebook-scraper library untuk mengambil komentar dari post URL (tanpa modal)
"""
import time
import csv
import json
import re
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Tambahkan path facebook-scraper
sys.path.insert(0, 'd:/FOREM-CLONE/web/scrap/facebook-scraper')
try:
    from facebook_scraper import get_posts
    FACEBOOK_SCRAPER_AVAILABLE = True
except:
    FACEBOOK_SCRAPER_AVAILABLE = False
    print("WARNING: facebook-scraper library tidak tersedia, mode komentar via URL dimatikan")

GROUP_URL = "https://www.facebook.com/groups/894614057345113"
COOKIES_FILE = "facebook_cookies.json"

UI_KEYWORDS = {
    'like', 'comment', 'share', 'send', 'reactions', 'view more', 'see more',
    'bagikan', 'suka', 'komentar', 'kirim', 'lihat', 'reply', 'balas',
    'all reactions', 'top fan', 'admin', 'follow', 'mengikuti',
    'lihat selengkapnya', 'edited', 'diedit', 'translate', 'lihat terjemahan',
    'see translation', 'most relevant', 'paling relevan', 'newest', 'all comments',
    'semua komentar', 'view replies', 'lihat balasan'
}

def setup_driver():
    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

def load_cookies(driver, filename, cookies_type='json'):
    """Load cookies dari file (txt atau json)"""
    try:
        if cookies_type == 'txt':
            # Load cookies dari format Netscape (txt)
            cookies = []
            with open(filename, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split('\t')
                    if len(parts) >= 7:
                        cookie = {
                            'name': parts[5],
                            'value': parts[6],
                            'domain': parts[0],
                            'path': parts[2] if len(parts) > 2 else '/',
                            'secure': parts[3] == 'TRUE' if len(parts) > 3 else False,
                            'expiry': int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else None
                        }
                        cookies.append(cookie)
        else:
            # Load cookies dari JSON
            with open(filename, 'r') as f:
                cookies = json.load(f)
        
        driver.get("https://www.facebook.com")
        for c in cookies:
            driver.add_cookie(c)
        driver.refresh()
        time.sleep(3)
        return "login" not in driver.current_url
    except Exception as e:
        print(f"Error load cookies: {e}")
        return False

def clean_url(url):
    if not url:
        return ''
    return url.split('?')[0].rstrip('/')

def collect_profile_links(post_element):
    """
    Kumpulkan semua link profile dari post: {nama_lower: url}
    Profile link biasanya: /groups/{id}/user/{uid}/ atau /profile.php?id={uid} atau /username
    """
    profile_map = {}
    try:
        links = post_element.find_elements(By.TAG_NAME, 'a')
        for link in links:
            try:
                href = link.get_attribute('href') or ''
                text = link.text.strip()
                if not text or len(text) < 2:
                    continue
                
                # Filter: harus link profile, bukan post/photo/group
                is_profile = False
                if '/groups/' in href and '/user/' in href:
                    is_profile = True
                elif 'profile.php' in href:
                    is_profile = True
                elif re.search(r'facebook\.com/[A-Za-z0-9._]+/?(?:\?|$)', href) and \
                     '/posts/' not in href and '/photo' not in href and \
                     '/groups/' not in href and '/videos/' not in href and \
                     '/reel' not in href and '/watch' not in href:
                    is_profile = True
                
                if is_profile:
                    key = text.lower()
                    if key not in profile_map:
                        profile_map[key] = clean_url(href)
            except:
                continue
    except:
        pass
    return profile_map

def extract_post_images(post_element):
    """Ambil URL gambar post (filter avatar) - cari img dalam link photo + standalone img"""
    urls = []
    try:
        # Strategi 1: img dalam link photo (paling akurat untuk gambar post)
        photo_links = post_element.find_elements(By.CSS_SELECTOR, 
            "a[href*='/photo'], a[href*='/photos/']")
        for link in photo_links:
            try:
                imgs = link.find_elements(By.TAG_NAME, 'img')
                for img in imgs:
                    src = img.get_attribute('src') or ''
                    if src and 'scontent' in src and '/emoji' not in src and src not in urls:
                        urls.append(src)
            except:
                continue
        
        # Strategi 2: semua img selain avatar
        if not urls:
            imgs = post_element.find_elements(By.TAG_NAME, 'img')
            for img in imgs:
                try:
                    src = img.get_attribute('src') or ''
                    if 'scontent' not in src:
                        continue
                    if '/emoji' in src or '/rsrc.php' in src:
                        continue
                    # Skip kecil (avatar biasanya <60px)
                    w = img.get_attribute('width')
                    h = img.get_attribute('height')
                    try:
                        if w and h and (int(w) < 80 or int(h) < 80):
                            continue
                    except:
                        pass
                    # Skip jika img dalam header (avatar poster)
                    try:
                        in_header = img.find_elements(By.XPATH, 
                            "./ancestor::h2 | ./ancestor::h3 | ./ancestor::h4")
                        if in_header:
                            continue
                    except:
                        pass
                    if src not in urls:
                        urls.append(src)
                except:
                    continue
    except:
        pass
    return urls[:10]

def extract_post_url(post_element):
    """Permalink post"""
    try:
        links = post_element.find_elements(By.CSS_SELECTOR, 
            "a[href*='/posts/'], a[href*='/permalink/']")
        for link in links:
            href = link.get_attribute('href') or ''
            if '/posts/' in href or '/permalink/' in href:
                return href.split('?')[0]
    except:
        pass
    return ''

def extract_post_id(post_url):
    """Extract post ID dari URL post"""
    if not post_url:
        return ''
    try:
        # URL format: https://www.facebook.com/groups/xxx/posts/123456789
        # atau: https://www.facebook.com/123456789/posts/987654321
        parts = post_url.split('/posts/')
        if len(parts) > 1:
            post_id = parts[1].split('/')[0].split('?')[0]
            return post_id
    except:
        pass
    return ''

def expand_post(driver, post_element):
    """Klik See more dan View more comments"""
    try:
        # See more (post content)
        see_mores = post_element.find_elements(By.XPATH,
            ".//div[@role='button'][contains(., 'See more') or contains(., 'Lihat selengkapnya') or contains(., 'Selengkapnya')]")
        for btn in see_mores[:3]:
            try:
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.3)
            except:
                pass
    except:
        pass
    
    try:
        # View more comments
        for _ in range(3):
            view_more = post_element.find_elements(By.XPATH,
                ".//div[@role='button'][contains(., 'View more comments') or contains(., 'Lihat lebih banyak komentar') or contains(., 'View previous')]")
            if not view_more:
                break
            for btn in view_more[:2]:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                    time.sleep(0.2)
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1)
                except:
                    pass
    except:
        pass

def is_main_post(post_element):
    """Cek apakah element ini post utama (bukan komentar)
    Hanya skip jika aria-label jelas 'Comment by ...'"""
    try:
        aria = post_element.get_attribute('aria-label') or ''
        aria_lower = aria.lower()
        if aria_lower.startswith('comment by') or aria_lower.startswith('komentar oleh') or aria_lower.startswith('reply'):
            return False
        return True
    except:
        return True

def extract_comments_from_dom(post_element, poster_name):
    """Ekstrak komentar dari nested article di dalam post utama"""
    comments = []
    seen = set()
    try:
        # Komentar = nested article dengan aria-label "Comment by ..."
        comment_articles = post_element.find_elements(By.CSS_SELECTOR,
            "[role='article'][aria-label]")
        
        for c_art in comment_articles:
            try:
                aria = c_art.get_attribute('aria-label') or ''
                aria_lower = aria.lower()
                if not (aria_lower.startswith('comment by') or aria_lower.startswith('komentar oleh') or 'reply' in aria_lower):
                    continue
                
                # Ekstrak nama commenter dari aria-label: "Comment by John Doe"
                m = re.match(r'(?:comment by|komentar oleh|reply by)\s+(.+)', aria, re.IGNORECASE)
                commenter_name = m.group(1).strip() if m else ''
                
                # Ambil URL profile dari link pertama dengan nama tsb
                commenter_url = ''
                links = c_art.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    try:
                        href = link.get_attribute('href') or ''
                        text = link.text.strip()
                        if commenter_name and text and text.lower() in commenter_name.lower():
                            if '/groups/' in href and '/user/' in href:
                                commenter_url = clean_url(href)
                                break
                            if 'profile.php' in href or (
                                'facebook.com/' in href and '/posts/' not in href and '/photo' not in href
                            ):
                                commenter_url = clean_url(href)
                                break
                    except:
                        continue
                
                # Ambil isi komentar dari text element (skip nama)
                full_text = c_art.text
                lines = [l.strip() for l in full_text.split('\n') if l.strip()]
                comment_text_parts = []
                for line in lines:
                    line_lower = line.lower()
                    if commenter_name and line == commenter_name:
                        continue
                    if line_lower in UI_KEYWORDS:
                        continue
                    if re.fullmatch(r'\d+\s*[mhdwy]', line_lower):
                        continue
                    if re.match(r'^\d+\s*(menit|jam|hari|minggu|bulan|tahun)', line_lower):
                        continue
                    if len(line) < 2:
                        continue
                    comment_text_parts.append(line)
                
                comment_text = ' '.join(comment_text_parts).strip()[:1000]
                
                if not comment_text and not commenter_name:
                    continue
                
                key = (commenter_name, comment_text[:50])
                if key in seen:
                    continue
                seen.add(key)
                
                comments.append({
                    'commenter_name': commenter_name,
                    'commenter_profile_url': commenter_url,
                    'comment_text': comment_text
                })
            except:
                continue
    except:
        pass
    return comments

def clean_anti_scraping_text(text):
    """Facebook menyisipkan huruf-huruf single char untuk anti-scraping.
    Gabungkan baris 1-char menjadi line valid."""
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip baris yang cuma 1 karakter (anti-scraping noise)
        if len(line) <= 1:
            continue
        cleaned.append(line)
    return cleaned

def open_comment_modal(driver, post_element):
    """Buka modal komentar dengan klik tombol komentar"""
    try:
        # Cari tombol komentar (berbagai selector)
        comment_btns = []
        
        # Selector 1: tombol dengan text "Komentar" / "Comment" / angka komentar
        comment_btns.extend(post_element.find_elements(By.XPATH,
            ".//div[@role='button'][contains(., 'Komentar') or contains(., 'Comment') or contains(., 'comment')]"))
        
        # Selector 2: span dengan text komentar
        comment_btns.extend(post_element.find_elements(By.XPATH,
            ".//span[contains(., 'Komentar') or contains(., 'Comment')]"))
        
        # Selector 3: aria-label comment
        comment_btns.extend(post_element.find_elements(By.CSS_SELECTOR,
            "[aria-label*='Komentar'], [aria-label*='Comment'], [aria-label*='comment']"))
        
        # Selector 4: tombol di bawah post (action buttons area)
        # Cari area action buttons (biasanya div dengan aria-label)
        action_area = post_element.find_elements(By.XPATH, 
            ".//div[contains(@aria-label, 'reaction') or contains(@aria-label, 'actions')]")
        if action_area:
            for area in action_area:
                comment_btns.extend(area.find_elements(By.XPATH,
                    ".//div[@role='button'][contains(., 'Komentar') or contains(., 'Comment')]"))
        
        # Filter unique
        seen_btns = []
        unique_btns = []
        for btn in comment_btns:
            try:
                btn_id = btn.id
                if btn_id not in seen_btns:
                    seen_btns.append(btn_id)
                    unique_btns.append(btn)
            except:
                unique_btns.append(btn)
        
        print(f"    Found {len(unique_btns)} comment buttons", end=' ')
        
        for btn in unique_btns[:5]:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                time.sleep(0.5)
                
                # Cek apakah tombol visible
                if not btn.is_displayed():
                    continue
                
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(2)
                
                # Cek apakah modal terbuka
                modal = driver.find_elements(By.CSS_SELECTOR, "[role='dialog']")
                if modal:
                    print(f"- modal opened!")
                    return True
            except Exception as e:
                print(f"  error clicking: {e}")
                continue
        
        print("- failed to open modal")
        return False
    except Exception as e:
        print(f"  error in open_comment_modal: {e}")
        return False

def extract_all_comments_from_modal(driver):
    """Ekstrak komentar dari modal dengan scroll agresif untuk load komentar"""
    comments = []
    seen = set()
    try:
        modal = driver.find_elements(By.CSS_SELECTOR, "[role='dialog']")
        if not modal:
            print("    No modal found")
            return comments
        
        modal = modal[0]
        print(f"    Modal found, scrolling to load comments...")
        
        # Scroll agresif di dalam modal untuk load komentar
        last_height = 0
        scroll_round = 0
        max_scroll = 15  # Max 15 scroll rounds
        
        while scroll_round < max_scroll:
            try:
                # Scroll ke bawah
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", modal)
                time.sleep(1)  # Tunggu untuk load komentar
                
                # Cek tinggi scroll
                new_height = driver.execute_script("return arguments[0].scrollHeight;", modal)
                
                # Re-find modal setelah scroll
                modal = driver.find_elements(By.CSS_SELECTOR, "[role='dialog']")
                if not modal:
                    break
                modal = modal[0]
                
                # Jika tinggi tidak berubah, coba scroll ke atas lalu ke bawah
                if new_height == last_height:
                    scroll_round += 1
                    # Coba scroll ke atas lalu ke bawah untuk trigger load
                    driver.execute_script("arguments[0].scrollTop = 0;", modal)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", modal)
                    time.sleep(0.5)
                else:
                    scroll_round = 0
                    last_height = new_height
                
                print(f"    Scroll round {scroll_round + 1}/{max_scroll}, height: {new_height}")
                
            except Exception as e:
                print(f"    Error scrolling round {scroll_round}: {e}")
                break
        
        print(f"    Finished scrolling, extracting comments...")
        
        # Coba berbagai selector untuk komentar di modal
        selectors = [
            "[role='article']",
            "div[data-visualcompletion='comment-dense-react-root']",
            "div[data-pagelet*='Comment']",
            "div[aria-label*='komentar']",
            "div[class*='comment']"
        ]
        
        comment_els = []
        for selector in selectors:
            try:
                els = modal.find_elements(By.CSS_SELECTOR, selector)
                if els:
                    print(f"    Selector '{selector}' found {len(els)} elements")
                    comment_els = els
                    break
            except:
                continue
        
        if not comment_els:
            print("    No comment elements found with any selector")
            # Fallback: text parsing dari modal
            modal_text = modal.text
            lines = [l.strip() for l in modal_text.split('\n') if l.strip()]
            print(f"    Fallback: parsing {len(lines)} lines from modal text")
            
            i = 0
            while i < len(lines):
                line = lines[i]
                line_lower = line.lower()
                
                # Skip UI keywords
                if line_lower in UI_KEYWORDS:
                    i += 1
                    continue
                if re.fullmatch(r'\d+\s*[mhdwy]', line_lower):
                    i += 1
                    continue
                if re.match(r'^\d+\s*(menit|jam|hari|minggu|bulan|tahun)', line_lower):
                    i += 1
                    continue
                
                # Cek apakah ini nama commenter (2-70 karakter)
                if 2 < len(line) < 70 and not re.match(r'^\d+$', line):
                    commenter_name = line
                    i += 1
                    
                    # Ambil isi komentar
                    comment_text_parts = []
                    max_lines = 5
                    while i < len(lines) and len(comment_text_parts) < max_lines:
                        next_line = lines[i]
                        next_lower = next_line.lower()
                        
                        if next_lower in UI_KEYWORDS:
                            i += 1
                            continue
                        if re.fullmatch(r'\d+\s*[mhdwy]', next_lower):
                            break
                        if re.match(r'^\d+\s*(menit|jam|hari|minggu|bulan|tahun)', next_lower):
                            i += 1
                            continue
                        if 2 < len(next_line) < 70 and not re.match(r'^\d+$', next_line):
                            if len(next_line) < 50 and next_lower != commenter_name.lower():
                                break
                        
                        if len(next_line) < 2:
                            i += 1
                            continue
                        
                        comment_text_parts.append(next_line)
                        i += 1
                    
                    comment_text = ' '.join(comment_text_parts).strip()[:1000]
                    if comment_text:
                        key = (commenter_name, comment_text[:50])
                        if key not in seen:
                            seen.add(key)
                            comments.append({
                                'commenter_name': commenter_name,
                                'commenter_profile_url': '',
                                'comment_text': comment_text
                            })
                else:
                    i += 1
        else:
            # Ekstrak dari DOM elements
            for c_el in comment_els:
                try:
                    text = c_el.text.strip()
                    if not text or len(text) < 5:
                        continue
                    
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    if len(lines) < 2:
                        continue
                    
                    commenter_name = lines[0]
                    text_lower = text.lower()
                    if any(k in text_lower for k in ['like', 'suka', 'reply', 'balas', 'translate', 'lihat', 'terjemahkan']):
                        continue
                    
                    comment_text_parts = []
                    for line in lines[1:]:
                        line_lower = line.lower()
                        if line_lower in UI_KEYWORDS:
                            continue
                        if re.fullmatch(r'\d+\s*[mhdwy]', line_lower):
                            continue
                        if re.match(r'^\d+\s*(menit|jam|hari|minggu|bulan|tahun)', line_lower):
                            continue
                        if len(line) < 2:
                            continue
                        if line == commenter_name:
                            continue
                        comment_text_parts.append(line)
                    
                    comment_text = ' '.join(comment_text_parts).strip()[:1000]
                    if not comment_text:
                        continue
                    
                    commenter_url = ''
                    links = c_el.find_elements(By.TAG_NAME, 'a')
                    for link in links:
                        try:
                            href = link.get_attribute('href') or ''
                            text = link.text.strip()
                            if text and text.lower() in commenter_name.lower():
                                if '/groups/' in href and '/user/' in href:
                                    commenter_url = clean_url(href)
                                    break
                                if 'profile.php' in href:
                                    commenter_url = clean_url(href)
                                    break
                        except:
                            continue
                    
                    key = (commenter_name, comment_text[:50])
                    if key in seen:
                        continue
                    seen.add(key)
                    
                    comments.append({
                        'commenter_name': commenter_name,
                        'commenter_profile_url': commenter_url,
                        'comment_text': comment_text
                    })
                except:
                    continue
        
        print(f"    Extracted {len(comments)} unique comments from modal")
    except Exception as e:
        print(f"    Error extracting from modal: {e}")
    return comments

def close_comment_modal(driver):
    """Tutup modal komentar dengan ESC atau klik X"""
    try:
        # Coba ESC key
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(0.5)
        
        # Cek apakah masih ada modal
        modal = driver.find_elements(By.CSS_SELECTOR, "[role='dialog']")
        if modal:
            # Cari tombol close
            close_btns = driver.find_elements(By.CSS_SELECTOR, "[aria-label='Close'], [aria-label='Tutup']")
            for btn in close_btns:
                try:
                    btn.click()
                    time.sleep(0.5)
                    break
                except:
                    continue
    except:
        pass

def extract_comments_from_url(post_url, cookies_file):
    """Gunakan facebook-scraper untuk mengambil komentar dari post URL"""
    comments = []
    if not FACEBOOK_SCRAPER_AVAILABLE or not post_url:
        return comments
    
    try:
        # Load cookies - facebook-scraper butuh path file cookies, bukan dict
        cookies = cookies_file if cookies_file else None
        
        # Gunakan facebook-scraper untuk mengambil post dengan komentar
        for post in get_posts(
            post_urls=[post_url],
            cookies=cookies,
            options={"comments": True, "progress": False}
        ):
            if 'comments' in post and post['comments']:
                for c in post['comments'][:50]:  # Batasi 50 komentar
                    commenter_name = c.get('commenter_name', '')
                    comment_text = c.get('comment_text', '')
                    commenter_url = c.get('commenter_url', '')
                    
                    if commenter_name and comment_text:
                        comments.append({
                            'commenter_name': commenter_name,
                            'commenter_profile_url': commenter_url,
                            'comment_text': comment_text[:1000]
                        })
            break  # Hanya ambil post pertama
    except Exception as e:
        print(f"    Error fetching comments via URL: {e}")
    return comments

def extract_post_data(driver, post_element, open_modal=False):
    """Ekstrak data dari post utama
    Args:
        open_modal: jika True, gunakan facebook-scraper untuk mengambil komentar via URL
    """
    try:
        # Baca text dulu, sebelum melakukan apapun yg bisa nge-stale element
        full_text = post_element.text
        lines = clean_anti_scraping_text(full_text)
        
        if not lines:
            return None
        
        # Ambil teks komentar dari nested article (untuk dipisah dari post content)
        comment_texts_set = set()
        try:
            comment_elements = post_element.find_elements(By.CSS_SELECTOR,
                "[role='article'][aria-label]")
            for c in comment_elements:
                try:
                    aria = c.get_attribute('aria-label') or ''
                    if 'comment' in aria.lower() or 'komentar' in aria.lower() or 'reply' in aria.lower():
                        for line in c.text.split('\n'):
                            line = line.strip()
                            if line:
                                comment_texts_set.add(line)
                except:
                    continue
        except:
            pass
        
        # === Poster name (baris pertama yang valid) ===
        poster_name = 'Unknown'
        for line in lines[:5]:
            if 2 < len(line) < 60 and not re.match(r'^\d', line) and 'admin' not in line.lower():
                poster_name = line
                break
        
        # === Date ===
        post_date = 'Unknown'
        date_pattern = re.compile(
            r'(\d+\s*(?:menit|jam|hari|minggu|bulan|tahun|m|h|d|w|y)\s*(?:yang lalu|ago)?|\d+\s*[mhdwy]\b|kemarin|yesterday|baru saja|just now)',
            re.IGNORECASE)
        for line in lines[:10]:
            m = date_pattern.search(line)
            if m:
                post_date = m.group(0).strip()
                break
        
        # === Post content: ambil dari data-ad-rendering-role story_message (paling akurat) ===
        post_content = ''
        try:
            content_els = post_element.find_elements(By.CSS_SELECTOR,
                "div[data-ad-rendering-role='story_message'], div[data-ad-preview='message']")
            if content_els:
                content_text = content_els[0].text
                content_lines = clean_anti_scraping_text(content_text)
                post_content = ' '.join(content_lines).strip()[:2000]
        except:
            pass
        
        # Fallback: filter text-parsing seperti V2 jika story_message kosong
        if not post_content:
            post_lines = []
            for line in lines[1:]:
                line_lower = line.lower()
                if line in comment_texts_set:
                    continue
                if line_lower in UI_KEYWORDS:
                    continue
                if date_pattern.fullmatch(line) or re.fullmatch(r'\d+\s*[mhdwy]', line_lower):
                    continue
                if re.search(r'\b(all comments|semua komentar|most relevant|paling relevan|view \d+|view more|lihat \d+|tulis komentar)\b', line_lower):
                    continue
                if len(line) < 3:
                    continue
                post_lines.append(line)
            post_content = ' '.join(post_lines).strip()[:2000]
        
        # === DOM enrichment ===
        profile_map = collect_profile_links(post_element)
        post_images = extract_post_images(post_element)
        post_url = extract_post_url(post_element)
        post_id = extract_post_id(post_url)
        
        # Poster URL: cari di profile_map berdasarkan nama
        poster_url = profile_map.get(poster_name.lower(), '')
        
        # === Komentar dari DOM (visible comments) ===
        comments = extract_comments_from_dom(post_element, poster_name)
        
        # === Buka post URL di tab baru untuk scrap komentar (jika open_modal=True) ===
        # Skip jika komentar visible sudah >= 2 atau 0 komentar
        if open_modal and 0 < len(comments) < 2 and post_url:
            print(f"    Membuka post URL di tab baru...", end=' ')
            try:
                # Buka tab baru
                driver.execute_script("window.open(arguments[0]);", post_url)
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(2)
                
                # Scroll untuk load komentar
                for _ in range(5):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                
                # Ekstrak komentar dari halaman post
                page_comments = extract_comments_from_dom(driver.find_element(By.TAG_NAME, 'body'), poster_name)
                print(f"found {len(page_comments)} comments from post page")
                
                # Merge dengan existing comments
                existing_keys = {(c['commenter_name'], c['comment_text'][:50]) for c in comments}
                for pc in page_comments:
                    key = (pc['commenter_name'], pc['comment_text'][:50])
                    if key not in existing_keys:
                        comments.append(pc)
                        print(f"      + {pc['commenter_name']}: {pc['comment_text'][:30]}...")
                
                # Tutup tab dan kembali ke tab utama
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(0.5)
            except Exception as e:
                print(f"Error: {e}")
                try:
                    driver.switch_to.window(driver.window_handles[0])
                except:
                    pass
        elif open_modal:
            if len(comments) >= 2:
                print(f"    Skip modal (komentar visible: {len(comments)})")
            else:
                print(f"    Skip modal (0 komentar atau no post_url)")
        
        return {
            'poster_name': poster_name,
            'poster_profile_url': poster_url,
            'post_content': post_content,
            'post_image_urls': ' | '.join(post_images),
            'post_url': post_url,
            'post_id': post_id,
            'post_date': post_date,
            'comments': comments
        }
    except Exception as e:
        import traceback
        print(f"  Error extract: {e}")
        traceback.print_exc()
        return None

def scrape_while_scroll(driver, group_url, max_no_new=8, scroll_delay=3, save_callback=None, open_modal=False):
    print(f"\n[SCRAPE] Membuka group...")
    driver.get(group_url)
    time.sleep(8)
    
    results = []
    seen = set()
    no_new_count = 0
    scroll_round = 0
    
    while no_new_count < max_no_new:
        try:
            # Selector baru: post utama = direct children dari [role='feed']
            posts = driver.find_elements(By.CSS_SELECTOR, "[role='feed'] > div")
            print(f"\nScroll #{scroll_round} - Post di feed: {len(posts)}")
            
            new_this_round = 0
            for post in posts:
                try:
                    data = extract_post_data(driver, post, open_modal=open_modal)
                    if not data:
                        continue
                    
                    # Skip header sortir
                    if 'urutkan' in data['poster_name'].lower() or 'sort' in data['poster_name'].lower():
                        continue
                    
                    key = data['post_url'] or f"{data['poster_name']}|{data['post_content'][:80]}"
                    if key in seen:
                        continue
                    seen.add(key)
                    
                    imgs = len(data['post_image_urls'].split(' | ')) if data['post_image_urls'] else 0
                    
                    # Skip jika benar-benar kosong (no content, no images, no comments)
                    if not data['post_content'] and not data['post_image_urls'] and not data['comments']:
                        continue
                    
                    results.append(data)
                    new_this_round += 1
                    print(f"  [{len(results)}] {data['poster_name']}: {data['post_content'][:50]}... (img:{imgs}, cmt:{len(data['comments'])})")
                except Exception as e:
                    continue
            
            print(f"  Post baru: {new_this_round}, Total: {len(results)}")
            
            # Scroll yang lebih lembut untuk menghindari refresh halaman
            try:
                # Scroll ke bawah sedikit-sedikit
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                # Scroll ke element terakhir jika ada
                if posts:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block:'end'});", posts[-1])
                        time.sleep(0.5)
                    except:
                        pass
            except:
                pass
            time.sleep(scroll_delay)
            scroll_round += 1
            
            if new_this_round == 0:
                no_new_count += 1
            else:
                no_new_count = 0
            
            # Simpan berkala setiap 10 post
            if save_callback and len(results) > 0 and len(results) % 10 == 0:
                save_callback(results)
                
        except KeyboardInterrupt:
            print(f"\n[INTERRUPTED dalam loop] Menghentikan scroll...")
            break
        except Exception as e:
            print(f"  Error scroll round: {e}")
            break
    
    print(f"\n[SELESAI] Total post: {len(results)}")
    return results

def save_to_csv(posts, filename, start_time=None, end_time=None):
    """1 baris per komentar (jika 0 komentar, tetap 1 baris dengan kolom commenter kosong)"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['no', 'post_id', 'poster_name', 'poster_profile_url', 'post_content',
                          'post_image_urls', 'post_url', 'post_date', 'scrape_start_time',
                          'scrape_end_time', 'commenter_name', 'commenter_profile_url',
                          'comment_text', 'scraped_at']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            row_no = 0
            for p in posts:
                base = {
                    'post_id': p.get('post_id', ''),
                    'poster_name': p['poster_name'],
                    'poster_profile_url': p['poster_profile_url'],
                    'post_content': p['post_content'],
                    'post_image_urls': p['post_image_urls'],
                    'post_url': p['post_url'],
                    'post_date': p['post_date'],
                    'scrape_start_time': start_time.strftime("%Y-%m-%d %H:%M:%S") if start_time else '',
                    'scrape_end_time': end_time.strftime("%Y-%m-%d %H:%M:%S") if end_time else now,
                    'scraped_at': now
                }
                
                if p['comments']:
                    for c in p['comments']:
                        row_no += 1
                        writer.writerow({**base, 'no': row_no, **c})
                else:
                    row_no += 1
                    writer.writerow({**base, 'no': row_no, 'commenter_name': '',
                                    'commenter_profile_url': '', 'comment_text': ''})
        
        print(f"\nDisimpan ke: {filename} ({row_no} baris)")
        return True
    except Exception as e:
        print(f"Error CSV: {e}")
        return False

def load_config():
    """Load config dari file JSON jika ada"""
    config_file = "scraper_config.json"
    default_config = {
        "group_url": "https://www.facebook.com/groups/894614057345113",
        "cookies_type": "txt",
        "cookies_file": "cookies.txt",
        "output_dir": ".",
        "max_posts": 50,
        "open_modal": False
    }
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default_config
    else:
        return default_config

def main():
    print("=" * 60)
    print("Facebook Group Scraper V3 - Detail Post + Comments")
    print("=" * 60)
    print("Tekan Ctrl+C untuk berhenti dan menyimpan hasil sementara")
    
    # Load config
    config = load_config()
    
    # Get instance number untuk multi-run
    instance_num = os.environ.get('SCRAPER_INSTANCE', '1')
    print(f"[INFO] Instance #{instance_num}")
    
    # Gunakan config atau default
    GROUP_URL = config.get('group_url', 'https://www.facebook.com/groups/894614057345113')
    COOKIES_TYPE = config.get('cookies_type', 'txt')
    COOKIES_FILE = config.get('cookies_file', 'cookies.txt')
    OUTPUT_DIR = config.get('output_dir', '.')
    MAX_POSTS = config.get('max_posts', 50)
    OPEN_MODAL_FOR_COMMENTS = config.get('open_modal', False)
    
    if OPEN_MODAL_FOR_COMMENTS:
        print("\n[INFO] Mode: Buka modal komentar untuk scrap SEMUA komentar (lebih lambat)")
    else:
        print("\n[INFO] Mode: Scrap komentar visible saja (lebih cepat)")
    
    # Setup logging
    log_file = os.path.join(OUTPUT_DIR, f"facebook_posts_v3_instance_{instance_num}_log.txt")
    
    def log_message(message):
        """Log ke file dan console"""
        print(message)
        with open(log_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")
    
    # Track waktu
    start_time = datetime.now()
    log_message(f"Scrape dimulai: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log_message(f"Group URL: {GROUP_URL}")
    log_message(f"Max Posts: {MAX_POSTS}")
    
    driver = setup_driver()
    posts = []
    
    def save_partial(data):
        # Tambahkan instance number ke filename untuk multi-run
        filename = os.path.join(OUTPUT_DIR, f"facebook_posts_v3_instance_{instance_num}_partial.csv")
        save_to_csv(data, filename, start_time, datetime.now())
        log_message(f"Partial save: {len(data)} posts")
    
    try:
        driver.get(GROUP_URL)
        time.sleep(3)
        log_message("\nLogin dengan cookies...")
        if not load_cookies(driver, COOKIES_FILE, COOKIES_TYPE):
            log_message("Login gagal!")
            return
        log_message("Login berhasil!")
        
        posts = scrape_while_scroll(driver, GROUP_URL, max_no_new=15, scroll_delay=5, 
                                    save_callback=save_partial, open_modal=OPEN_MODAL_FOR_COMMENTS)
        
        print("\n" + "=" * 60)
        print(f"HASIL: {len(posts)} post")
        print("=" * 60)
        for i, p in enumerate(posts[:10], 1):
            print(f"\n[{i}] {p['poster_name']} ({p['poster_profile_url']})")
            print(f"    Content: {p['post_content'][:100]}")
            print(f"    Images: {len(p['post_image_urls'].split(' | ')) if p['post_image_urls'] else 0}")
            print(f"    Comments ({len(p['comments'])}):")
            for c in p['comments'][:3]:
                print(f"      - {c['commenter_name']}: {c['comment_text'][:60]}")
        
        if posts:
            end_time = datetime.now()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(OUTPUT_DIR, f"facebook_posts_v3_instance_{instance_num}_{ts}.csv")
            save_to_csv(posts, filename, start_time, end_time)
            log_message(f"Scrape selesai: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            log_message(f"Total waktu: {end_time - start_time}")
            log_message(f"Total posts: {len(posts)}")
    
    except KeyboardInterrupt:
        end_time = datetime.now()
        log_message(f"\n[INTERRUPTED] Menyimpan {len(posts)} post...")
        if posts:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(OUTPUT_DIR, f"facebook_posts_v3_instance_{instance_num}_{ts}_interrupted.csv")
            save_to_csv(posts, filename, start_time, end_time)
            log_message(f"Total waktu: {end_time - start_time}")
    except Exception as e:
        end_time = datetime.now()
        log_message(f"Error: {e}")
        if posts:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(OUTPUT_DIR, f"facebook_posts_v3_instance_{instance_num}_{ts}_error.csv")
            save_to_csv(posts, filename, start_time, end_time)
    finally:
        log_message("Menutup browser...")
        try:
            time.sleep(2)
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    main()
