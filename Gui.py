"""
YouTube to MP3/MP4 Converter GUI
Requires: pip install yt-dlp customtkinter
"""

import customtkinter as ctk
import yt_dlp
import threading
from pathlib import Path
from tkinter import filedialog, messagebox


class YouTubeConverterGUI:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("YouTube Converter")
        self.window.geometry("500x480")
        self.window.resizable(False, False)
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.output_dir = Path("downloads")
        self.output_dir.mkdir(exist_ok=True)
        self.downloading = False
        self.cancel_download = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Title
        title = ctk.CTkLabel(
            main_frame, 
            text="YouTube Converter",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(0, 15))
        
        # URL Input
        ctk.CTkLabel(main_frame, text="URL:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 3))
        self.url_entry = ctk.CTkEntry(main_frame, placeholder_text="https://youtube.com/watch?v=...")
        self.url_entry.pack(fill="x", pady=(0, 12))
        
        # Format and Quality in one row
        options_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        options_frame.pack(fill="x", pady=(0, 12))
        
        # Format Selection (Left)
        format_container = ctk.CTkFrame(options_frame, fg_color="transparent")
        format_container.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        ctk.CTkLabel(format_container, text="Format:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 3))
        
        self.format_var = ctk.StringVar(value="MP3")
        format_buttons = ctk.CTkFrame(format_container, fg_color="transparent")
        format_buttons.pack(fill="x")
        
        ctk.CTkRadioButton(
            format_buttons, 
            text="MP3", 
            variable=self.format_var, 
            value="MP3",
            command=self.update_quality_options
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkRadioButton(
            format_buttons, 
            text="MP4", 
            variable=self.format_var, 
            value="MP4",
            command=self.update_quality_options
        ).pack(side="left")
        
        # Quality Selection (Right)
        quality_container = ctk.CTkFrame(options_frame, fg_color="transparent")
        quality_container.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        ctk.CTkLabel(quality_container, text="Quality:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 3))
        
        self.quality_var = ctk.StringVar(value="192 kbps")
        self.quality_menu = ctk.CTkOptionMenu(
            quality_container,
            variable=self.quality_var,
            values=["128 kbps", "192 kbps", "256 kbps", "320 kbps"],
            width=140
        )
        self.quality_menu.pack(fill="x")
        
        # Output Directory
        ctk.CTkLabel(main_frame, text="Save to:", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 3))
        
        dir_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        dir_frame.pack(fill="x", pady=(0, 12))
        
        self.dir_label = ctk.CTkLabel(
            dir_frame, 
            text=str(self.output_dir.absolute()),
            font=ctk.CTkFont(size=10),
            anchor="w"
        )
        self.dir_label.pack(side="left", fill="x", expand=True)
        
        ctk.CTkButton(
            dir_frame,
            text="Browse",
            width=80,
            height=28,
            command=self.select_directory
        ).pack(side="right", padx=(8, 0))
        
        # Progress
        self.progress_bar = ctk.CTkProgressBar(main_frame)
        self.progress_bar.pack(fill="x", pady=(0, 8))
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Ready",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.pack(pady=(0, 12))
        
        # Download and Stop Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        self.download_btn = ctk.CTkButton(
            button_frame,
            text="Download",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=38,
            command=self.start_download
        )
        self.download_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.stop_btn = ctk.CTkButton(
            button_frame,
            text="Stop",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=38,
            width=100,
            fg_color="red",
            hover_color="darkred",
            command=self.stop_download,
            state="disabled"
        )
        self.stop_btn.pack(side="right")
        
    def update_quality_options(self):
        if self.format_var.get() == "MP3":
            self.quality_menu.configure(values=["128 kbps", "192 kbps", "256 kbps", "320 kbps"])
            self.quality_var.set("192 kbps")
        else:
            self.quality_menu.configure(values=["360p", "480p", "720p", "1080p", "Best"])
            self.quality_var.set("720p")
    
    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir = Path(directory)
            self.dir_label.configure(text=str(self.output_dir.absolute()))
    
    def progress_hook(self, d):
        if self.cancel_download:
            raise Exception("Download cancelled by user")
            
        if d['status'] == 'downloading':
            try:
                percent = d.get('_percent_str', '0%').strip().replace('%', '')
                self.progress_bar.set(float(percent) / 100)
                self.status_label.configure(text=f"Downloading: {d.get('_percent_str', '0%')}")
            except:
                pass
        elif d['status'] == 'finished':
            self.progress_bar.set(1)
            self.status_label.configure(text="Processing...")
    
    def download_video(self):
        url = self.url_entry.get().strip()
        
        if not url:
            self.window.after(0, lambda: messagebox.showerror("Error", "Please enter a YouTube URL"))
            self.downloading = False
            self.window.after(0, lambda: self.download_btn.configure(state="normal", text="Download"))
            self.window.after(0, lambda: self.stop_btn.configure(state="disabled"))
            return
        
        format_type = self.format_var.get()
        quality = self.quality_var.get()
        
        try:
            if format_type == "MP3":
                quality_value = quality.split()[0]
                
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': quality_value,
                    }],
                    'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
                    'progress_hooks': [self.progress_hook],
                }
            else:
                quality_map = {
                    '360p': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
                    '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
                    '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
                    '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
                    'Best': 'bestvideo+bestaudio/best'
                }
                
                ydl_opts = {
                    'format': quality_map.get(quality, quality_map['720p']),
                    'merge_output_format': 'mp4',
                    'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
                    'progress_hooks': [self.progress_hook],
                }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                if not self.cancel_download:
                    self.window.after(0, lambda: self.progress_bar.set(1))
                    self.window.after(0, lambda: self.status_label.configure(text=f"✓ Download complete!"))
                    self.window.after(0, lambda: messagebox.showinfo("Success", f"Downloaded successfully!\n\nSaved to: {self.output_dir}"))
                
        except Exception as e:
            if self.cancel_download:
                self.window.after(0, lambda: self.progress_bar.set(0))
                self.window.after(0, lambda: self.status_label.configure(text="Download cancelled"))
                self.window.after(0, lambda: messagebox.showinfo("Cancelled", "Download stopped by user"))
            else:
                self.window.after(0, lambda: messagebox.showerror("Error", f"Download failed:\n{str(e)}"))
                self.window.after(0, lambda: self.progress_bar.set(0))
                self.window.after(0, lambda: self.status_label.configure(text="Download failed"))
        
        finally:
            self.downloading = False
            self.cancel_download = False
            self.window.after(0, lambda: self.download_btn.configure(state="normal", text="Download"))
            self.window.after(0, lambda: self.stop_btn.configure(state="disabled"))
    
    def start_download(self):
        if self.downloading:
            return
        
        self.downloading = True
        self.cancel_download = False
        self.download_btn.configure(state="disabled", text="Downloading...")
        self.stop_btn.configure(state="normal")
        self.progress_bar.set(0)
        
        # Run download in separate thread
        thread = threading.Thread(target=self.download_video, daemon=True)
        thread.start()
    
    def stop_download(self):
        if self.downloading:
            self.cancel_download = True
            self.status_label.configure(text="Stopping download...")
            self.stop_btn.configure(state="disabled")
    
    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    app = YouTubeConverterGUI()
    app.run()