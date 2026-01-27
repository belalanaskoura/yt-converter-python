
import yt_dlp
import os
import sys
from pathlib import Path


class YouTubeConverter:
    def __init__(self, output_dir="downloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def download_mp3(self, url, quality="192"):
        """
        Download YouTube video as MP3
        quality: '128', '192', '256', '320' (kbps)
        """
        quality_map = {
            '128': '128',
            '192': '192',
            '256': '256',
            '320': '320'
        }
        
        if quality not in quality_map:
            print(f"Invalid quality. Using 192 kbps. Available: {list(quality_map.keys())}")
            quality = '192'
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality_map[quality],
            }],
            'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print(f"\nDownloading MP3 ({quality} kbps)...")
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                mp3_filename = filename.rsplit('.', 1)[0] + '.mp3'
                print(f"\n✓ Download complete: {mp3_filename}")
                return mp3_filename
        except Exception as e:
            print(f"✗ Error downloading MP3: {e}")
            return None
    
    def download_mp4(self, url, quality="720"):
        """
        Download YouTube video as MP4
        quality: '360', '480', '720', '1080', 'best'
        """
        quality_map = {
            '360': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
            '480': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
            '720': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            '1080': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            'best': 'bestvideo+bestaudio/best'
        }
        
        if quality not in quality_map:
            print(f"Invalid quality. Using 720p. Available: {list(quality_map.keys())}")
            quality = '720'
        
        ydl_opts = {
            'format': quality_map[quality],
            'merge_output_format': 'mp4',
            'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print(f"\nDownloading MP4 ({quality}p)...")
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                print(f"\n✓ Download complete: {filename}")
                return filename
        except Exception as e:
            print(f"✗ Error downloading MP4: {e}")
            return None


def main():
    print("=" * 60)
    print("YouTube to MP3/MP4 Converter")
    print("=" * 60)
    
    converter = YouTubeConverter()
    
    # Get URL
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("\nEnter YouTube URL: ").strip()
    
    if not url:
        print("✗ No URL provided")
        return
    
    # Get format
    print("\nSelect format:")
    print("1. MP3 (audio only)")
    print("2. MP4 (video)")
    
    format_choice = input("Choice (1 or 2): ").strip()
    
    if format_choice == '1':
        print("\nMP3 Quality options:")
        print("1. 128 kbps (smallest)")
        print("2. 192 kbps (good)")
        print("3. 256 kbps (very good)")
        print("4. 320 kbps (best)")
        
        quality_choice = input("Choice (1-4, default 2): ").strip() or '2'
        quality_map = {'1': '128', '2': '192', '3': '256', '4': '320'}
        quality = quality_map.get(quality_choice, '192')
        
        converter.download_mp3(url, quality)
        
    elif format_choice == '2':
        print("\nMP4 Quality options:")
        print("1. 360p")
        print("2. 480p")
        print("3. 720p (HD)")
        print("4. 1080p (Full HD)")
        print("5. Best available")
        
        quality_choice = input("Choice (1-5, default 3): ").strip() or '3'
        quality_map = {'1': '360', '2': '480', '3': '720', '4': '1080', '5': 'best'}
        quality = quality_map.get(quality_choice, '720')
        
        converter.download_mp4(url, quality)
        
    else:
        print("✗ Invalid choice")
        return
    
    print(f"\nFiles saved to: {converter.output_dir.absolute()}")


if __name__ == "__main__":
    main()