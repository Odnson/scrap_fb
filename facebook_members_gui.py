"""
GUI untuk Facebook Group Members Scraper
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import subprocess
import threading
from datetime import datetime

class FacebookMembersGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Facebook Group Members Scraper")
        self.root.geometry("700x500")
        
        self.config_file = "members_config.json"
        self.config = self.load_config()
        self.processes = []
        
        self.create_widgets()
        self.load_configuration()
    
    def load_config(self):
        """Load config dari file JSON jika ada"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_config(self):
        """Save config ke file JSON"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)
    
    def create_widgets(self):
        """Create GUI widgets"""
        # Notebook untuk tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab 1: Konfigurasi
        config_tab = ttk.Frame(notebook)
        notebook.add(config_tab, text='Konfigurasi')
        
        # Tab 2: Multi-Run
        multi_tab = ttk.Frame(notebook)
        notebook.add(multi_tab, text='Multi-Run')
        
        # Tab 3: Logs
        log_tab = ttk.Frame(notebook)
        notebook.add(log_tab, text='Logs')
        
        # --- Konfigurasi Tab ---
        config_frame = ttk.Frame(config_tab, padding="10")
        config_frame.pack(fill='both', expand=True)
        
        # Group Members URL
        ttk.Label(config_frame, text="Group Members URL:").grid(row=0, column=0, sticky='w', pady=5)
        self.group_url_var = tk.StringVar(value=self.config.get('group_url', ''))
        ttk.Entry(config_frame, textvariable=self.group_url_var, width=60).grid(row=0, column=1, sticky='ew', pady=5)
        
        # Cookies Type
        ttk.Label(config_frame, text="Tipe Cookies:").grid(row=1, column=0, sticky='w', pady=5)
        self.cookies_type_var = tk.StringVar(value=self.config.get('cookies_type', 'json'))
        cookies_type_combo = ttk.Combobox(config_frame, textvariable=self.cookies_type_var, values=['json', 'txt'], state='readonly')
        cookies_type_combo.grid(row=1, column=1, sticky='ew', pady=5)
        
        # Cookies File
        ttk.Label(config_frame, text="File Cookies:").grid(row=2, column=0, sticky='w', pady=5)
        cookies_file_frame = ttk.Frame(config_frame)
        cookies_file_frame.grid(row=2, column=1, sticky='ew', pady=5)
        self.cookies_file_var = tk.StringVar(value=self.config.get('cookies_file', 'facebook_cookies.json'))
        ttk.Entry(cookies_file_frame, textvariable=self.cookies_file_var, width=40).pack(side='left')
        ttk.Button(cookies_file_frame, text="Browse", command=self.browse_cookies_file).pack(side='left', padx=5)
        
        # Output Directory
        ttk.Label(config_frame, text="Output Directory:").grid(row=3, column=0, sticky='w', pady=5)
        output_dir_frame = ttk.Frame(config_frame)
        output_dir_frame.grid(row=3, column=1, sticky='ew', pady=5)
        self.output_dir_var = tk.StringVar(value=self.config.get('output_dir', '.'))
        ttk.Entry(output_dir_frame, textvariable=self.output_dir_var, width=40).pack(side='left')
        ttk.Button(output_dir_frame, text="Browse", command=self.browse_output_dir).pack(side='left', padx=5)
        
        # Max Members
        ttk.Label(config_frame, text="Max Members (0 = unlimited):").grid(row=4, column=0, sticky='w', pady=5)
        self.max_members_var = tk.StringVar(value=str(self.config.get('max_members', 0)))
        ttk.Entry(config_frame, textvariable=self.max_members_var, width=20).grid(row=4, column=1, sticky='w', pady=5)
        
        # Buttons
        button_frame = ttk.Frame(config_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Simpan Konfigurasi", command=self.save_configuration).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Jalankan Scraper", command=self.run_scraper_single).pack(side='left', padx=5)
        
        # --- Multi-Run Tab ---
        multi_frame = ttk.Frame(multi_tab, padding="10")
        multi_frame.pack(fill='both', expand=True)
        
        ttk.Label(multi_frame, text="Jumlah Instance:").grid(row=0, column=0, sticky='w', pady=5)
        self.instance_count_var = tk.StringVar(value='2')
        ttk.Entry(multi_frame, textvariable=self.instance_count_var, width=10).grid(row=0, column=1, sticky='w', pady=5)
        
        ttk.Button(multi_frame, text="Jalankan Multi-Instance", command=self.run_scraper_multi).grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(multi_frame, text="Stop Semua Instance", command=self.stop_all_instances).grid(row=2, column=0, columnspan=2, pady=5)
        
        # Status
        ttk.Label(multi_frame, text="Status Running Instances:").grid(row=3, column=0, sticky='w', pady=5)
        self.status_label = ttk.Label(multi_frame, text="0 instances running")
        self.status_label.grid(row=3, column=1, sticky='w', pady=5)
        
        # --- Logs Tab ---
        log_frame = ttk.Frame(log_tab, padding="10")
        log_frame.pack(fill='both', expand=True)
        
        # Log file selector
        log_selector_frame = ttk.Frame(log_frame)
        log_selector_frame.pack(fill='x', pady=5)
        
        ttk.Label(log_selector_frame, text="Log File:").pack(side='left')
        self.log_file_var = tk.StringVar()
        ttk.Entry(log_selector_frame, textvariable=self.log_file_var, width=50).pack(side='left', padx=5)
        ttk.Button(log_selector_frame, text="Browse", command=self.browse_log_file).pack(side='left', padx=5)
        ttk.Button(log_selector_frame, text="Refresh", command=self.refresh_log).pack(side='left', padx=5)
        
        # Log text area
        self.log_text = tk.Text(log_frame, wrap='word', height=20)
        self.log_text.pack(fill='both', expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Auto-refresh checkbox
        self.auto_refresh_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(log_frame, text="Auto-refresh (5s)", variable=self.auto_refresh_var, command=self.toggle_auto_refresh).pack(pady=5)
    
    def browse_cookies_file(self):
        """Browse untuk file cookies"""
        filename = filedialog.askopenfilename(
            title="Pilih File Cookies",
            filetypes=[("Text Files", "*.txt"), ("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if filename:
            self.cookies_file_var.set(filename)
    
    def browse_output_dir(self):
        """Browse untuk output directory"""
        dirname = filedialog.askdirectory(title="Pilih Output Directory")
        if dirname:
            self.output_dir_var.set(dirname)
    
    def browse_log_file(self):
        """Browse untuk file log"""
        filename = filedialog.askopenfilename(
            title="Pilih File Log",
            filetypes=[("Log Files", "*.txt"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if filename:
            self.log_file_var.set(filename)
            self.refresh_log()
    
    def refresh_log(self):
        """Refresh log file content"""
        log_file = self.log_file_var.get()
        if not log_file or not os.path.exists(log_file):
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, "Tidak ada file log yang dipilih atau file tidak ditemukan.")
            return
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, content)
            self.log_text.see(tk.END)
        except Exception as e:
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, f"Error membaca file log: {e}")
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh log"""
        if self.auto_refresh_var.get():
            self.auto_refresh_log()
        else:
            self.root.after_cancel(self.refresh_job) if hasattr(self, 'refresh_job') else None
    
    def auto_refresh_log(self):
        """Auto-refresh log setiap 5 detik"""
        if self.auto_refresh_var.get():
            self.refresh_log()
            self.refresh_job = self.root.after(5000, self.auto_refresh_log)
    
    def save_configuration(self):
        """Simpan konfigurasi"""
        self.config = {
            "group_url": self.group_url_var.get(),
            "cookies_type": self.cookies_type_var.get(),
            "cookies_file": self.cookies_file_var.get(),
            "output_dir": self.output_dir_var.get(),
            "max_members": int(self.max_members_var.get())
        }
        self.save_config()
        messagebox.showinfo("Info", "Konfigurasi disimpan!")
    
    def load_configuration(self):
        """Load konfigurasi ke GUI"""
        if self.config:
            self.group_url_var.set(self.config.get('group_url', ''))
            self.cookies_type_var.set(self.config.get('cookies_type', 'json'))
            self.cookies_file_var.set(self.config.get('cookies_file', 'facebook_cookies.json'))
            self.output_dir_var.set(self.config.get('output_dir', '.'))
            self.max_members_var.set(str(self.config.get('max_members', 0)))
    
    def run_scraper_single(self):
        """Jalankan scraper single instance"""
        self.save_configuration()
        
        def run():
            try:
                subprocess.run(["python", "scrape_members.py"], cwd=self.output_dir_var.get())
            except Exception as e:
                messagebox.showerror("Error", f"Error menjalankan scraper: {e}")
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        messagebox.showinfo("Info", "Scraper dijalankan di background!")
    
    def run_scraper_multi(self):
        """Jalankan scraper multi-instance"""
        self.save_configuration()
        
        try:
            instance_count = int(self.instance_count_var.get())
        except:
            messagebox.showerror("Error", "Jumlah instance harus angka!")
            return
        
        for i in range(instance_count):
            env = os.environ.copy()
            env['SCRAPER_INSTANCE'] = str(i + 1)
            
            def run(env_copy):
                try:
                    subprocess.run(["python", "scrape_members.py"], cwd=self.output_dir_var.get(), env=env_copy)
                except Exception as e:
                    print(f"Error instance {env_copy.get('SCRAPER_INSTANCE')}: {e}")
            
            thread = threading.Thread(target=run, args=(env,), daemon=True)
            thread.start()
            self.processes.append(thread)
        
        self.update_status()
        messagebox.showinfo("Info", f"{instance_count} instance dijalankan di background!")
    
    def stop_all_instances(self):
        """Stop semua running instances"""
        self.processes = []
        self.update_status()
        messagebox.showinfo("Info", "Semua instance di-stop!")
    
    def update_status(self):
        """Update status label"""
        running_count = len(self.processes)
        self.status_label.config(text=f"{running_count} instances running")

if __name__ == "__main__":
    root = tk.Tk()
    app = FacebookMembersGUI(root)
    root.mainloop()
