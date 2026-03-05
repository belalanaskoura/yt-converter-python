import { invoke } from "@tauri-apps/api/core";
import { motion, AnimatePresence } from "framer-motion";
import { Music2, Video, FolderOpen, Clock, Download, Trash2 } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatRelativeTime } from "@/lib/utils";
import type { HistoryEntry } from "@/lib/types";
import logoImage from "@/assets/logo.png";

const AUDIO_FORMATS = ["MP3", "M4A", "WAV"];

interface SidebarProps {
  history: HistoryEntry[];
  onDeleteEntry: (id: number) => void;
  onClearAll: () => void;
}

function HistoryItem({ entry, index, onDelete }: { entry: HistoryEntry; index: number; onDelete: (id: number) => void }) {
  const isAudio = AUDIO_FORMATS.includes(entry.format.toUpperCase());

  async function handleOpenFolder() {
    const dir = entry.filepath.split(/[\\/]/).slice(0, -1).join("/");
    if (dir) {
      try {
        await invoke("open_folder", { path: dir });
      } catch (e) {
        console.error("open_folder failed:", e);
      }
    }
  }

  async function handleOpenFile() {
    if (entry.filepath) {
      try {
        await invoke("open_file", { path: entry.filepath });
      } catch (e) {
        console.error("open_file failed:", e);
      }
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.04, duration: 0.2, ease: "easeOut" }}
      className="group px-3 py-3 rounded-lg hover:bg-[oklch(0.16_0.006_285)] transition-colors cursor-default"
    >
      <div className="flex items-start gap-2.5">
        {entry.thumbnail ? (
          <img
            src={entry.thumbnail}
            alt=""
            className="mt-0.5 h-10 w-16 shrink-0 rounded-md object-cover bg-[oklch(0.18_0.006_285)]"
          />
        ) : (
          <div className="mt-0.5 p-1.5 rounded-md bg-[oklch(0.18_0.006_285)] shrink-0">
            {isAudio ? (
              <Music2 className="h-3.5 w-3.5 text-blue-400" />
            ) : (
              <Video className="h-3.5 w-3.5 text-purple-400" />
            )}
          </div>
        )}
        <div className="flex-1 min-w-0">
          <p
            className="text-sm text-white font-medium leading-tight truncate"
            title={entry.title}
          >
            {entry.title || "Unknown"}
          </p>
          <div className="flex items-center gap-2 mt-1.5 flex-wrap">
            <Badge variant={isAudio ? "audio" : "video"}>
              {entry.format.toUpperCase()}
            </Badge>
            {entry.quality && (
              <span className="text-xs text-[oklch(0.45_0.008_285)]">
                {entry.quality}
              </span>
            )}
            <div className="flex items-center gap-1 text-xs text-[oklch(0.4_0.008_285)] ml-auto">
              <Clock className="h-3 w-3" />
              {formatRelativeTime(entry.downloaded_at)}
            </div>
          </div>
        </div>
        {/* Delete button — always visible */}
        <button
          className="shrink-0 mt-0.5 text-[oklch(0.45_0.008_285)] hover:text-red-400 transition-colors"
          onClick={() => entry.id != null && onDelete(entry.id)}
          title="Remove from history"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Action buttons — revealed on hover */}
      <div className="mt-2 flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
        <Button
          variant="ghost"
          size="sm"
          className="h-6 px-2 text-xs"
          onClick={handleOpenFile}
          title="Open file"
        >
          <Download className="h-3 w-3" />
          Open
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 px-2 text-xs"
          onClick={handleOpenFolder}
          title="Show in folder"
        >
          <FolderOpen className="h-3 w-3" />
          Folder
        </Button>
      </div>
    </motion.div>
  );
}

export function Sidebar({ history, onDeleteEntry, onClearAll }: SidebarProps) {
  return (
    <aside className="flex flex-col h-full w-72 shrink-0 border-r border-[oklch(0.18_0.006_285)] bg-[oklch(0.105_0.006_285)]">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-4 py-5">
        <img src={logoImage} alt="FetchIt" className="h-8 w-8 rounded-lg" />
        <div>
          <p className="text-sm font-bold text-white leading-none">FetchIt</p>
          <p className="text-xs text-[oklch(0.45_0.008_285)] mt-0.5">YouTube Downloader</p>
        </div>
      </div>

      <Separator />

      {/* History header */}
      <div className="flex items-center justify-between px-4 py-3">
        <span className="text-xs font-semibold uppercase tracking-widest text-[oklch(0.45_0.008_285)]">
          Downloads
          {history.length > 0 && (
            <span className="ml-2 text-[oklch(0.4_0.008_285)] tabular-nums font-normal normal-case tracking-normal">
              {history.length}
            </span>
          )}
        </span>
        {history.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 px-2 text-xs text-red-400 hover:text-red-300"
            onClick={onClearAll}
            title="Clear all history"
          >
            <Trash2 className="h-3 w-3" />
            Clear all
          </Button>
        )}
      </div>

      {/* History list */}
      <ScrollArea className="flex-1 px-2">
        <AnimatePresence initial={false}>
          {history.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center py-16 text-center"
            >
              <div className="p-3 rounded-xl bg-[oklch(0.14_0.006_285)] mb-3">
                <Download className="h-6 w-6 text-[oklch(0.35_0.006_285)]" />
              </div>
              <p className="text-sm text-[oklch(0.45_0.008_285)]">No downloads yet</p>
              <p className="text-xs text-[oklch(0.35_0.008_285)] mt-1">
                Your history will appear here
              </p>
            </motion.div>
          ) : (
            <div className="space-y-0.5 pb-4">
              {history.map((entry, i) => (
                <HistoryItem key={entry.id ?? i} entry={entry} index={i} onDelete={onDeleteEntry} />
              ))}
            </div>
          )}
        </AnimatePresence>
      </ScrollArea>
    </aside>
  );
}
