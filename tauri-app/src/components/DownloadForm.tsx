import { useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { ClipboardPaste, FolderOpen, FolderInput, Download, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ProgressCard } from "@/components/ProgressCard";
import type { MediaType, MediaFormat, ProgressState } from "@/lib/types";

interface DownloadFormProps {
  outputDir: string;
  onOutputDirChange: (dir: string) => void;
  progress: ProgressState;
  onDownloadStart: (meta: { url: string; format: string; quality: string }) => void;
  onCancel: () => void;
  onError: (msg: string) => void;
}

// Cascade definitions
const FORMAT_OPTIONS: Record<MediaType, MediaFormat[]> = {
  Audio: ["MP3", "M4A", "WAV"],
  Video: ["MP4", "WEBM", "MKV"],
};

const QUALITY_OPTIONS: Record<MediaFormat, string[]> = {
  MP3: ["128 kbps", "192 kbps", "256 kbps", "320 kbps"],
  M4A: ["128 kbps", "192 kbps", "256 kbps", "320 kbps"],
  WAV: ["Lossless"],
  MP4: ["360p", "480p", "720p", "1080p", "1440p", "2160p (4K)", "Best"],
  WEBM: ["360p", "480p", "720p", "1080p", "1440p", "2160p (4K)", "Best"],
  MKV: ["360p", "480p", "720p", "1080p", "1440p", "2160p (4K)", "Best"],
};

const DEFAULT_QUALITY: Record<MediaFormat, string> = {
  MP3: "192 kbps",
  M4A: "192 kbps",
  WAV: "Lossless",
  MP4: "720p",
  WEBM: "720p",
  MKV: "720p",
};

function qualityToArg(format: MediaFormat, quality: string): string {
  // For audio: extract the number (e.g. "192 kbps" → "192")
  if (["MP3", "M4A"].includes(format)) {
    return quality.split(" ")[0];
  }
  return quality;
}

export function DownloadForm({
  outputDir,
  onOutputDirChange,
  progress,
  onDownloadStart,
  onCancel,
  onError,
}: DownloadFormProps) {
  const [url, setUrl] = useState("");
  const [mediaType, setMediaType] = useState<MediaType>("Audio");
  const [format, setFormat] = useState<MediaFormat>("MP3");
  const [quality, setQuality] = useState("192 kbps");

  const isDownloading =
    progress.status === "downloading" || progress.status === "processing";

  function handleMediaTypeChange(val: string) {
    const t = val as MediaType;
    setMediaType(t);
    const firstFmt = FORMAT_OPTIONS[t][0];
    setFormat(firstFmt);
    setQuality(DEFAULT_QUALITY[firstFmt]);
  }

  function handleFormatChange(val: string) {
    const f = val as MediaFormat;
    setFormat(f);
    setQuality(DEFAULT_QUALITY[f]);
  }

  async function handlePaste() {
    try {
      const text = await navigator.clipboard.readText();
      setUrl(text.trim());
    } catch {
      // Clipboard API not available
    }
  }

  async function handleSelectDir() {
    try {
      const selected = await invoke<string | null>("select_directory");
      if (selected) onOutputDirChange(selected);
    } catch (e) {
      console.error("select_directory failed:", e);
    }
  }

  async function handleOpenDir() {
    try {
      await invoke("open_folder", { path: outputDir });
    } catch (e) {
      console.error("open_folder failed:", e);
    }
  }

  async function handleDownload() {
    if (!url || isDownloading) return;
    onDownloadStart({ url, format, quality: qualityToArg(format, quality) });
    try {
      await invoke("start_download", {
        payload: {
          url,
          format: format.toLowerCase(),
          quality: qualityToArg(format, quality),
          output_dir: outputDir,
        },
      });
    } catch (e) {
      onError(String(e));
    }
  }

  async function handleCancel() {
    try {
      await invoke("cancel_download");
      onCancel();
    } catch (e) {
      console.error("cancel_download failed:", e);
    }
  }

  const dirName = outputDir.split(/[\\/]/).pop() ?? outputDir;

  return (
    <div className="flex flex-col gap-5">
      {/* URL input */}
      <div className="space-y-2">
        <label className="text-xs font-semibold uppercase tracking-widest text-[oklch(0.5_0.008_285)]">
          Video URL
        </label>
        <div className="flex gap-2">
          <Input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Paste a YouTube link…"
            onKeyDown={(e) => e.key === "Enter" && handleDownload()}
            className="flex-1"
          />
          <Button
            variant="secondary"
            size="md"
            onClick={handlePaste}
            title="Paste from clipboard"
          >
            <ClipboardPaste className="h-4 w-4" />
            <span className="hidden sm:inline">Paste</span>
          </Button>
        </div>
      </div>

      {/* Type / Format / Quality */}
      <div className="space-y-2">
        <label className="text-xs font-semibold uppercase tracking-widest text-[oklch(0.5_0.008_285)]">
          Format
        </label>
        <div className="grid grid-cols-3 gap-3">
          <div className="space-y-1.5">
            <span className="text-xs text-[oklch(0.45_0.008_285)]">Type</span>
            <Select value={mediaType} onValueChange={handleMediaTypeChange}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Audio">Audio</SelectItem>
                <SelectItem value="Video">Video</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <span className="text-xs text-[oklch(0.45_0.008_285)]">Format</span>
            <Select value={format} onValueChange={handleFormatChange}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {FORMAT_OPTIONS[mediaType].map((f) => (
                  <SelectItem key={f} value={f}>
                    {f}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <span className="text-xs text-[oklch(0.45_0.008_285)]">Quality</span>
            <Select value={quality} onValueChange={setQuality}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {QUALITY_OPTIONS[format].map((q) => (
                  <SelectItem key={q} value={q}>
                    {q}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Save location */}
      <div className="space-y-2">
        <label className="text-xs font-semibold uppercase tracking-widest text-[oklch(0.5_0.008_285)]">
          Save Location
        </label>
        <div className="flex items-center gap-2 rounded-lg border border-[oklch(0.22_0.006_285)] bg-[oklch(0.12_0.006_285)] px-3 py-2">
          <FolderOpen className="h-4 w-4 text-[oklch(0.45_0.008_285)] shrink-0" />
          <span className="flex-1 truncate text-sm text-[oklch(0.65_0.008_285)]" title={outputDir}>
            {dirName}
          </span>
          <Button variant="ghost" size="sm" onClick={handleSelectDir}>
            <FolderInput className="h-3.5 w-3.5" />
            Change
          </Button>
          <Button variant="ghost" size="sm" onClick={handleOpenDir}>
            <FolderOpen className="h-3.5 w-3.5" />
            Open
          </Button>
        </div>
      </div>

      {/* Progress */}
      <ProgressCard progress={progress} />

      {/* Action buttons */}
      <div className="flex gap-3 pt-1">
        <Button
          variant="primary"
          size="lg"
          className="flex-1"
          onClick={handleDownload}
          disabled={!url.trim() || isDownloading}
        >
          <Download className="h-4 w-4" />
          {isDownloading ? "Downloading…" : "Download"}
        </Button>
        {isDownloading && (
          <Button variant="danger" size="lg" onClick={handleCancel}>
            <X className="h-4 w-4" />
            Cancel
          </Button>
        )}
      </div>
    </div>
  );
}
