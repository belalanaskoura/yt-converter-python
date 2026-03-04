export type MediaType = "Audio" | "Video";

export type AudioFormat = "MP3" | "M4A" | "WAV";
export type VideoFormat = "MP4" | "WEBM" | "MKV";
export type MediaFormat = AudioFormat | VideoFormat;

export type DownloadStatus =
  | "idle"
  | "downloading"
  | "processing"
  | "complete"
  | "error"
  | "cancelled";

export interface ProgressState {
  percent: number | null;
  speed: string;
  status: DownloadStatus;
  errorMessage?: string;
  completedTitle?: string;
  completedFilepath?: string;
}

export interface HistoryEntry {
  id?: number;
  title: string;
  url: string;
  filepath: string;
  format: string;
  quality: string;
  downloaded_at: string;
  file_size: number;
  thumbnail?: string;
}
