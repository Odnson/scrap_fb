"""
Facebook Group Scraper GUI
Support multi-run dengan konfigurasi credential dan cookies
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import subprocess
import threading
import sys

class FacebookScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Facebook Group Scraper - Multi-Run")
        self.root.geometry("800x600")
        
        # Config file path
        self.config_file = "scraper_config.json"
        
        # Load config
        self.config = self.load_config()
        
        # Create GUI
        self.create_widgets()
        
        # Running processes
        self.running_processes = []
    
    def load_config(self):
        """Load config dari file JSON"""
        default_config = {
            "group_url": "https://www.facebook.com/groups/894614057345113",
            "cookies_type": "txt",  # txt atau json
            "cookies_file": "cookies.txt",
            "output_dir": ".",
            "max_posts": 50,
            "open_modal": False
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return default_config
        else:
            return default_config
    
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
        
        # Group URL
        ttk.Label(config_frame, text="Group URL:").grid(row=0, column=0, sticky='w', pady=5)
        self.group_url_var = tk.StringVar(value=self.config.get('group_url', ''))
        ttk.Entry(config_frame, textvariable=self.group_url_var, width=60).grid(row=0, column=1, sticky='ew', pady=5)
        
        # Cookies Type
        ttk.Label(config_frame, text="Tipe Cookies:").grid(row=1, column=0, sticky='w', pady=5)
        self.cookies_type_var = tk.StringVar(value=self.config.get('cookies_type', 'txt'))
        cookies_type_combo = ttk.Combobox(config_frame, textvariable=self.cookies_type_var, values=['txt', 'json'], state='readonly')
        cookies_type_combo.grid(row=1, column=1, sticky='ew', pady=5)
        
        # Cookies File
        ttk.Label(config_frame, text="File Cookies:").grid(row=2, column=0, sticky='w', pady=5)
        cookies_file_frame = ttk.Frame(config_frame)
        cookies_file_frame.grid(row=2, column=1, sticky='ew', pady=5)
        self.cookies_file_var = tk.StringVar(value=self.config.get('cookies_file', 'cookies.txt'))
        ttk.Entry(cookies_file_frame, textvariable=self.cookies_file_var, width=40).pack(side='left')
        ttk.Button(cookies_file_frame, text="Browse", command=self.browse_cookies_file).pack(side='left', padx=5)
        
        # Output Directory
        ttk.Label(config_frame, text="Output Directory:").grid(row=3, column=0, sticky='w', pady=5)
        output_dir_frame = ttk.Frame(config_frame)
        output_dir_frame.grid(row=3, column=1, sticky='ew', pady=5)
        self.output_dir_var = tk.StringVar(value=self.config.get('output_dir', '.'))
        ttk.Entry(output_dir_frame, textvariable=self.output_dir_var, width=40).pack(side='left')
        ttk.Button(output_dir_frame, text="Browse", command=self.browse_output_dir).pack(side='left', padx=5)
        
        # Max Posts
        ttk.Label(config_frame, text="Max Posts:").grid(row=4, column=0, sticky='w', pady=5)
        self.max_posts_var = tk.StringVar(value=str(self.config.get('max_posts', 50)))
        ttk.Entry(config_frame, textvariable=self.max_posts_var, width=60).grid(row=4, column=1, sticky='ew', pady=5)
        
        # Open Modal
        self.open_modal_var = tk.BooleanVar(value=self.config.get('open_modal', False))
        ttk.Checkbutton(config_frame, text="Buka Modal Komentar (lebih lambat)", variable=self.open_modal_var).grid(row=5, column=1, sticky='w', pady=5)
        
        # Save Button
        ttk.Button(config_frame, text="Simpan Konfigurasi", command=self.save_configuration).grid(row=6, column=1, sticky='ew', pady=10)
        
        # Configure grid weights
        config_frame.columnconfigure(1, weight=1)
        
        # --- Multi-Run Tab ---
        multi_frame = ttk.Frame(multi_tab, padding="10")
        multi_frame.pack(fill='both', expand=True)
        
        # Instance count
        ttk.Label(multi_frame, text="Jumlah Instance:").grid(row=0, column=0, sticky='w', pady=5)
        self.instance_count_var = tk.StringVar(value="1")
        ttk.Entry(multi_frame, textvariable=self.instance_count_var, width=10).grid(row=0, column=1, sticky='w', pady=5)
        
        # Start Button
        ttk.Button(multi_frame, text="Start Multi-Run", command=self.start_multi_run).grid(row=1, column=0, columnspan=2, sticky='ew', pady=10)
        
        # Stop Button
        ttk.Button(multi_frame, text="Stop All", command=self.stop_all).grid(row=2, column=0, columnspan=2, sticky='ew', pady=5)
        
        # Status
        ttk.Label(multi_frame, text="Status Running Instances:").grid(row=3, column=0, sticky='w', pady=5)
        self.status_label = ttk.Label(multi_frame, text="0 instances running")
        self.status_label.grid(row=3, column=1, sticky='w', pady=5)
        
        # --- Logs Tab ---
        log_frame = ttk.Frame(log_tab, padding="10")
        log_frame.pack(fill='both', expand=True)
        
        # Log text area
        self.log_text = tk.Text(log_frame, wrap='word', height=20)
        self.log_text.pack(fill='both', expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=scrollbar.set)
    
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
    
    def save_configuration(self):
        """Simpan konfigurasi"""
        self.config = {
            "group_url": self.group_url_var.get(),
            "cookies_type": self.cookies_type_var.get(),
            "cookies_file": self.cookies_file_var.get(),
            "output_dir": self.output_dir_var.get(),
            "max_posts": int(self.max_posts_var.get()),
            "open_modal": self.open_modal_var.get()
        }
        self.save_config()
        messagebox.showinfo("Sukses", "Konfigurasi berhasil disimpan!")
    
    def start_multi_run(self):
        """Start multi-run scraper"""
        try:
            instance_count = int(self.instance_count_var.get())
        except ValueError:
            messagebox.showerror("Error", "Jumlah instance harus berupa angka!")
            return
        
        if instance_count < 1:
            messagebox.showerror("Error", "Jumlah instance minimal 1!")
            return
        
        # Update config sebelum start
        self.save_configuration()
        
        # Start instances
        for i in range(instance_count):
            try:
                # Jalankan script dengan config file
                cmd = [sys.executable, "scrape_posts_v3.py"]
                
                # Set environment untuk output file unik
                env = os.environ.copy()
                env['SCRAPER_INSTANCE'] = str(i + 1)
                
                process = subprocess.Popen(
                    cmd,
                    cwd=os.path.dirname(os.path.abspath(__file__)),
                    env=env
                )
                
                self.running_processes.append(process)
                self.log(f"Instance {i + 1} started (PID: {process.pid})")
            except Exception as e:
                self.log(f"Error starting instance {i + 1}: {e}")
        
        self.status_label.config(text=f"{len(self.running_processes)} instances running")
    
    def stop_all(self):
        """Stop semua running instances"""
        for process in self.running_processes:
            try:
                process.terminate()
                self.log(f"Stopped process (PID: {process.pid})")
            except:
                pass
        
        self.running_processes.clear()
        self.status_label.config(text="0 instances running")
    
    def log(self, message):
        """Log pesan ke text area"""
        self.log_text.insert('end', f"{message}\n")
        self.log_text.see('end')

def main():
    root = tk.Tk()
    app = FacebookScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
