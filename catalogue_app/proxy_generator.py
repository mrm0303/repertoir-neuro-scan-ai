import os
import subprocess
import threading
import time
import re
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.ttk import Progressbar

def get_video_duration(input_path):
    """Obtient la durée en secondes via ffprobe."""
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries",
               "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", input_path]
        res = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
        return float(res.strip())
    except:
        return 1.0

def time_to_sec(time_str):
    """Convertit '00:01:23.45' en secondes."""
    parts = time_str.split(':')
    if len(parts) == 3:
        h, m, s = parts
        return float(h)*3600 + float(m)*60 + float(s)
    return 0.0

class ProxyWindow(tk.Toplevel):
    def __init__(self, master, files):
        super().__init__(master)
        self.title("Générateur de Proxies")
        self.geometry("500x250")
        self.files = files
        self.cancel_event = threading.Event()
        self.is_running = True
        
        self.lbl_file = ttk.Label(self, text="Préparation...", font=("TkDefaultFont", 10, "bold"))
        self.lbl_file.pack(pady=(20, 5), padx=20, anchor="w")
        
        self.lbl_status = ttk.Label(self, text="0 / 0", foreground="#888")
        self.lbl_status.pack(pady=0, padx=20, anchor="w")
        
        self.pb = Progressbar(self, orient="horizontal", mode="determinate", length=460)
        self.pb.pack(pady=15, padx=20, fill="x")
        
        self.btn_cancel = ttk.Button(self, text="Annuler", command=self.cancel)
        self.btn_cancel.pack(pady=10)
        
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # Start thread
        threading.Thread(target=self.worker, daemon=True).start()
        
    def cancel(self):
        self.cancel_event.set()
        self.is_running = False
        self.destroy()
        
    def worker(self):
        total_files = len(self.files)
        success_count = 0
        
        for i, path in enumerate(self.files):
            if self.cancel_event.is_set():
                break
                
            if not os.path.exists(path):
                continue
                
            filename = os.path.basename(path)
            self.after(0, lambda f=filename, i=i, t=total_files: [
                self.lbl_file.config(text=f"Encodage : {f}"),
                self.lbl_status.config(text=f"Fichier {i+1} sur {t}"),
                self.pb.config(value=0)
            ])
            
            # Ensure "Proxies" folder exists next to original file
            proxy_dir = os.path.join(os.path.dirname(path), "Proxies")
            if not os.path.exists(proxy_dir):
                try:
                    os.makedirs(proxy_dir)
                except:
                    # Fallback to Desktop if read-only
                    proxy_dir = os.path.expanduser("~/Desktop/Proxies_Repertoire")
                    if not os.path.exists(proxy_dir):
                        os.makedirs(proxy_dir)
            
            base, ext = os.path.splitext(filename)
            output_path = os.path.join(proxy_dir, f"{base}_Proxy.mp4")
            
            # Skip if exists
            if os.path.exists(output_path):
                success_count += 1
                continue
                
            duration = get_video_duration(path)
            
            cmd = [
                "ffmpeg", "-y", "-i", path,
                "-vf", "scale=-2:1080",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                "-c:a", "aac", "-b:a", "128k",
                output_path
            ]
            
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            # Parse FFmpeg output to update progress bar
            while True:
                line = proc.stdout.readline()
                if not line and proc.poll() is not None:
                    break
                if self.cancel_event.is_set():
                    proc.terminate()
                    break
                    
                match = re.search(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})", line)
                if match:
                    sec = time_to_sec(match.group(1))
                    pct = min((sec / duration) * 100, 100) if duration > 0 else 0
                    self.after(0, lambda p=pct: self.pb.config(value=p))
            
            if proc.returncode == 0:
                success_count += 1
                
        if not self.cancel_event.is_set():
            self.after(0, lambda: messagebox.showinfo("Terminé", f"{success_count} proxie(s) généré(s) avec succès !"))
            self.after(0, self.destroy)
