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
        self.window.title("YouTube Downloader")
        self.window.geometry("520x500")
        self.window.resizable(False, False)
        
        # YouTube color scheme
        ctk.set_appearance_mode("dark")
        
        self.output_dir = Path("downloads")
        self.output_dir.mkdir(exist_ok=True)
        self.downloading = False
        self.cancel_download = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Header with YouTube red accent
        header = ctk.CTkFrame(self.window, fg_color="#282828", corner_radius=0)
        header.pack(fill="x")
        
        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(pady=18)
        
        # YouTube-style logo/title
        title_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        title_frame.pack()
        
        ctk.CTkLabel(
            title_frame,
            text="▶",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#FF0000"
        ).pack(side="left", padx=(0, 8))
        
        ctk.CTkLabel(
            title_frame,
            text="YouTube Downloader",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#FFFFFF"
        ).pack(side="left")
        
        # Main content area
        content = ctk.CTkFrame(self.window, fg_color="#181818")
        content.pack(fill="both", expand=True, padx=0, pady=0)
        
        inner_content = ctk.CTkFrame(content, fg_color="transparent")
        inner_content.pack(fill="both", expand=True, padx=24, pady=24)
        
        # URL Input with YouTube styling
        ctk.CTkLabel(
            inner_content,
            text="Video URL",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#AAAAAA",
            anchor="w"
        ).pack(anchor="w", pady=(0, 6))
        
        self.url_entry = ctk.CTkEntry(
            inner_content,
            placeholder_text="Paste YouTube link here...",
            height=40,
            border_width=1,
            border_color="#303030",
            fg_color="#212121",
            text_color="#FFFFFF",
            placeholder_text_color="#717171"
        )
        self.url_entry.pack(fill="x", pady=(0, 20))
        
        # Format and Quality row
        options_row = ctk.CTkFrame(inner_content, fg_color="transparent")
        options_row.pack(fill="x", pady=(0, 20))
        
        # Format section
        format_section = ctk.CTkFrame(options_row, fg_color="transparent")
        format_section.pack(side="left", fill="both", expand=True, padx=(0, 8))
        
        ctk.CTkLabel(
            format_section,
            text="Format",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#AAAAAA",
            anchor="w"
        ).pack(anchor="w", pady=(0, 6))
        
        format_frame = ctk.CTkFrame(format_section, fg_color="#212121", border_width=1, border_color="#303030")
        format_frame.pack(fill="x")
        
        self.format_var = ctk.StringVar(value="MP3")
        
        mp3_btn = ctk.CTkRadioButton(
            format_frame,
            text="Audio (MP3)",
            variable=self.format_var,
            value="MP3",
            command=self.update_quality_options,
            fg_color="#FF0000",
            hover_color="#CC0000",
            text_color="#FFFFFF",
            border_color="#505050"
        )
        mp3_btn.pack(side="left", padx=12, pady=10)
        
        mp4_btn = ctk.CTkRadioButton(
            format_frame,
            text="Video (MP4)",
            variable=self.format_var,
            value="MP4",
            command=self.update_quality_options,
            fg_color="#FF0000",
            hover_color="#CC0000",
            text_color="#FFFFFF",
            border_color="#505050"
        )
        mp4_btn.pack(side="left", padx=12, pady=10)
        
        # Quality section
        quality_section = ctk.CTkFrame(options_row, fg_color="transparent")
        quality_section.pack(side="right", fill="both", expand=True, padx=(8, 0))
        
        ctk.CTkLabel(
            quality_section,
            text="Quality",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#AAAAAA",
            anchor="w"
        ).pack(anchor="w", pady=(0, 6))
        
        self.quality_var = ctk.StringVar(value="192 kbps")
        self.quality_menu = ctk.CTkOptionMenu(
            quality_section,
            variable=self.quality_var,
            values=["128 kbps", "192 kbps", "256 kbps", "320 kbps"],
            fg_color="#212121",
            button_color="#303030",
            button_hover_color="#404040",
            dropdown_fg_color="#212121",
            dropdown_hover_color="#303030",
            text_color="#FFFFFF"
        )
        self.quality_menu.pack(fill="x")
        
        # Save location
        ctk.CTkLabel(
            inner_content,
            text="Save Location",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#AAAAAA",
            anchor="w"
        ).pack(anchor="w", pady=(0, 6))
        
        location_frame = ctk.CTkFrame(inner_content, fg_color="#212121", border_width=1, border_color="#303030")
        location_frame.pack(fill="x", pady=(0, 20))
        
        location_inner = ctk.CTkFrame(location_frame, fg_color="transparent")
        location_inner.pack(fill="x", padx=12, pady=10)
        
        self.dir_label = ctk.CTkLabel(
            location_inner,
            text=f"📁 {self.output_dir.name}",
            font=ctk.CTkFont(size=12),
            text_color="#AAAAAA",
            anchor="w"
        )
        self.dir_label.pack(side="left", fill="x", expand=True)
        
        browse_btn = ctk.CTkButton(
            location_inner,
            text="Change",
            width=70,
            height=28,
            fg_color="#303030",
            hover_color="#404040",
            text_color="#FFFFFF",
            command=self.select_directory,
            corner_radius=4
        )
        browse_btn.pack(side="right")
        
        # Progress section
        self.progress_bar = ctk.CTkProgressBar(
            inner_content,
            progress_color="#FF0000",
            fg_color="#303030"
        )
        self.progress_bar.pack(fill="x", pady=(0, 8))
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(
            inner_content,
            text="Ready to download",
            font=ctk.CTkFont(size=12),
            text_color="#AAAAAA"
        )
        self.status_label.pack(pady=(0, 20))
        
        # Action buttons
        button_container = ctk.CTkFrame(inner_content, fg_color="transparent")
        button_container.pack()
        
        self.download_btn = ctk.CTkButton(
            button_container,
            text="Download",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
            width=200,
            fg_color="#FF0000",
            hover_color="#CC0000",
            text_color="#FFFFFF",
            command=self.start_download,
            corner_radius=22
        )
        self.download_btn.pack(side="left", padx=(0, 10))
        
        self.stop_btn = ctk.CTkButton(
            button_container,
            text="Cancel",
            font=ctk.CTkFont(size=14),
            height=44,
            width=100,
            fg_color="#303030",
            hover_color="#404040",
            text_color="#FFFFFF",
            command=self.stop_download,
            state="disabled",
            corner_radius=22
        )
        self.stop_btn.pack(side="left")
        
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
            self.dir_label.configure(text=f"📁 {self.output_dir.name}")
    
    def progress_hook(self, d):
        if self.cancel_download:
            raise Exception("Download cancelled by user")
            
        if d['status'] == 'downloading':
            try:
                percent = d.get('_percent_str', '0%').strip().replace('%', '')
                self.progress_bar.set(float(percent) / 100)
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                self.status_label.configure(text=f"Downloading... {d.get('_percent_str', '0%')} • {speed} • ETA: {eta}")
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
                    self.window.after(0, lambda: self.status_label.configure(text="✓ Download complete!"))
                    self.window.after(0, lambda: messagebox.showinfo("Success", f"Download complete!\n\nSaved to: {self.output_dir}"))
                
        except Exception as e:
            if self.cancel_download:
                self.window.after(0, lambda: self.progress_bar.set(0))
                self.window.after(0, lambda: self.status_label.configure(text="Download cancelled"))
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
        
        thread = threading.Thread(target=self.download_video, daemon=True)
        thread.start()
    
    def stop_download(self):
        if self.downloading:
            self.cancel_download = True
            self.status_label.configure(text="Cancelling...")
            self.stop_btn.configure(state="disabled")
    
    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    app = YouTubeConverterGUI()
    app.run()