import { useEffect, useState, useCallback, useRef } from "react";
import { listen } from "@tauri-apps/api/event";
import { invoke } from "@tauri-apps/api/core";
import { downloadDir } from "@tauri-apps/api/path";
import Database from "@tauri-apps/plugin-sql";
import { Sidebar } from "@/components/Sidebar";
import { DownloadForm } from "@/components/DownloadForm";
import type { ProgressState, HistoryEntry } from "@/lib/types";

const DB_NAME = "sqlite:downloads.db";

const INIT_SQL = `
  CREATE TABLE IF NOT EXISTS downloads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    url TEXT,
    filepath TEXT,
    format TEXT,
    quality TEXT,
    downloaded_at TEXT,
    file_size INTEGER DEFAULT 0
  );
`;

export default function App() {
  const [db, setDb] = useState<Database | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [outputDir, setOutputDir] = useState("");
  const [progress, setProgress] = useState<ProgressState>({
    status: "idle",
    percent: null,
    speed: "",
  });
  // Tracks metadata of the in-flight download so history can record format/quality/url
  const pendingMeta = useRef<{ url: string; format: string; quality: string } | null>(null);

  // ── Resolve OS download directory ─────────────────────────────────────────

  useEffect(() => {
    downloadDir().then(setOutputDir).catch(() => {/* keep fallback */});
  }, []);

  // ── Database setup ────────────────────────────────────────────────────────

  useEffect(() => {
    let mounted = true;
    Database.load(DB_NAME)
      .then(async (d) => {
        if (!mounted) return;
        await d.execute(INIT_SQL);
        // Migration: add thumbnail column for existing DBs (no-op if already present)
        await d.execute("ALTER TABLE downloads ADD COLUMN thumbnail TEXT DEFAULT ''").catch(() => {});
        setDb(d);
        const rows = await d.select<HistoryEntry[]>(
          "SELECT * FROM downloads ORDER BY downloaded_at DESC LIMIT 100"
        );
        setHistory(rows);
      })
      .catch(console.error);
    return () => {
      mounted = false;
    };
  }, []);

  const addHistoryEntryRef = useRef<((entry: Omit<HistoryEntry, "id">) => Promise<void>) | null>(null);

  const addHistoryEntry = useCallback(
    async (entry: Omit<HistoryEntry, "id">) => {
      if (!db) return;
      await db.execute(
        "INSERT INTO downloads (title, url, filepath, format, quality, downloaded_at, file_size, thumbnail) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
          entry.title,
          entry.url,
          entry.filepath,
          entry.format,
          entry.quality,
          entry.downloaded_at,
          entry.file_size,
          entry.thumbnail ?? "",
        ]
      );
      const rows = await db.select<HistoryEntry[]>(
        "SELECT * FROM downloads ORDER BY downloaded_at DESC LIMIT 100"
      );
      setHistory(rows);
    },
    [db]
  );

  const deleteEntry = useCallback(
    async (id: number) => {
      if (!db) return;
      await db.execute("DELETE FROM downloads WHERE id = ?", [id]);
      setHistory((prev) => prev.filter((e) => e.id !== id));
    },
    [db]
  );

  const clearHistory = useCallback(
    async () => {
      if (!db) return;
      await db.execute("DELETE FROM downloads");
      setHistory([]);
    },
    [db]
  );

  // Keep ref in sync so Tauri listeners always call the latest version
  useEffect(() => {
    addHistoryEntryRef.current = addHistoryEntry;
  }, [addHistoryEntry]);

  // ── Tauri event listeners ─────────────────────────────────────────────────

  useEffect(() => {
    let active = true;
    let unlisteners: Array<() => void> = [];

    Promise.all([
      listen<{ percent: number | null; speed: string }>("download://progress", (e) => {
        setProgress((prev) => ({
          ...prev,
          status: "downloading",
          percent: e.payload.percent,
          speed: e.payload.speed,
        }));
      }),
      listen("download://processing", () => {
        setProgress((prev) => ({ ...prev, status: "processing", percent: 100 }));
      }),
      listen<{ filepath: string; title: string; thumbnail: string }>("download://complete", (e) => {
        setProgress({
          status: "complete",
          percent: 100,
          speed: "",
          completedTitle: e.payload.title,
          completedFilepath: e.payload.filepath,
        });
        const folder = e.payload.filepath
          .replace(/\\/g, "/")
          .split("/")
          .slice(0, -1)
          .join("/")
          .replace(/\//g, "\\");
        invoke("open_folder", { path: folder }).catch(console.error);
        addHistoryEntryRef.current?.({
          title: e.payload.title,
          url: pendingMeta.current?.url ?? "",
          filepath: e.payload.filepath,
          format: pendingMeta.current?.format ?? "",
          quality: pendingMeta.current?.quality ?? "",
          downloaded_at: new Date().toISOString(),
          file_size: 0,
          thumbnail: e.payload.thumbnail ?? "",
        });
        pendingMeta.current = null;
      }),
      listen<{ message: string }>("download://error", (e) => {
        setProgress({
          status: "error",
          percent: null,
          speed: "",
          errorMessage: e.payload.message,
        });
      }),
      listen("download://cancelled", () => {
        setProgress({ status: "cancelled", percent: null, speed: "" });
      }),
    ]).then((fns) => {
      if (!active) {
        fns.forEach((u) => u());
      } else {
        unlisteners = fns;
      }
    });

    return () => {
      active = false;
      unlisteners.forEach((u) => u());
    };
  }, []);

  // ── Handlers ──────────────────────────────────────────────────────────────

  function handleDownloadStart(meta: { url: string; format: string; quality: string }) {
    pendingMeta.current = meta;
    setProgress({ status: "downloading", percent: 0, speed: "" });
  }

  function handleCancel() {
    setProgress({ status: "cancelled", percent: null, speed: "" });
  }

  function handleError(msg: string) {
    setProgress({ status: "error", percent: null, speed: "", errorMessage: msg });
  }

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="flex h-screen overflow-hidden bg-[oklch(0.09_0.005_285)]">
      <Sidebar history={history} onDeleteEntry={deleteEntry} onClearAll={clearHistory} />

      <main className="flex flex-1 flex-col overflow-y-auto">
        <div className="flex-1 px-8 py-8 max-w-2xl w-full mx-auto">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-white">Download</h1>
            <p className="text-sm text-[oklch(0.5_0.008_285)] mt-1">
              Paste a YouTube URL and choose your format
            </p>
          </div>

          <DownloadForm
            outputDir={outputDir}
            onOutputDirChange={setOutputDir}
            progress={progress}
            onDownloadStart={handleDownloadStart}
            onCancel={handleCancel}
            onError={handleError}
          />
        </div>
      </main>
    </div>
  );
}
