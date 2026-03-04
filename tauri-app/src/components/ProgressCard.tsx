import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, XCircle, Loader2, Zap } from "lucide-react";
import type { ProgressState } from "@/lib/types";

interface ProgressCardProps {
  progress: ProgressState;
}

const statusConfig = {
  idle: null,
  downloading: {
    icon: <Zap className="h-4 w-4 text-red-400 animate-pulse" />,
    label: "Downloading",
    color: "text-white",
  },
  processing: {
    icon: <Loader2 className="h-4 w-4 text-yellow-400 animate-spin" />,
    label: "Processing",
    color: "text-yellow-300",
  },
  complete: {
    icon: <CheckCircle2 className="h-4 w-4 text-green-400" />,
    label: "Download complete",
    color: "text-green-400",
  },
  error: {
    icon: <XCircle className="h-4 w-4 text-red-400" />,
    label: "Download failed",
    color: "text-red-400",
  },
  cancelled: {
    icon: <XCircle className="h-4 w-4 text-[oklch(0.5_0.008_285)]" />,
    label: "Cancelled",
    color: "text-[oklch(0.5_0.008_285)]",
  },
} as const;

export function ProgressCard({ progress }: ProgressCardProps) {
  const { status, percent, speed, errorMessage, completedTitle } = progress;
  const config = status !== "idle" ? statusConfig[status] : null;

  const displayPercent =
    status === "processing" || status === "complete"
      ? 100
      : (percent ?? 0);

  const barColor =
    status === "complete"
      ? "bg-green-500"
      : status === "error"
      ? "bg-red-700"
      : status === "cancelled"
      ? "bg-[oklch(0.35_0.006_285)]"
      : "bg-red-600";

  return (
    <AnimatePresence>
      {status !== "idle" && (
        <motion.div
          key="progress-card"
          initial={{ opacity: 0, y: 16, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 8, scale: 0.98 }}
          transition={{ duration: 0.25, ease: "easeOut" }}
          className="rounded-xl border border-[oklch(0.22_0.006_285)] bg-[oklch(0.12_0.006_285)] p-4 space-y-3"
        >
          {/* Header row */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {config?.icon}
              <span className={`text-sm font-medium ${config?.color}`}>
                {status === "error"
                  ? errorMessage ?? "An error occurred"
                  : status === "complete" && completedTitle
                  ? completedTitle
                  : config?.label}
              </span>
            </div>
            {status === "downloading" && (
              <div className="flex items-center gap-3">
                {speed && (
                  <span className="text-xs text-[oklch(0.5_0.008_285)] font-mono">
                    {speed}
                  </span>
                )}
                {percent !== null && (
                  <span className="text-xs font-semibold text-white tabular-nums">
                    {Math.round(percent)}%
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Progress bar */}
          <div className="h-1.5 rounded-full bg-[oklch(0.2_0.006_285)] overflow-hidden">
            <motion.div
              className={`h-full rounded-full ${barColor}`}
              initial={{ width: 0 }}
              animate={{ width: `${displayPercent}%` }}
              transition={{ ease: "easeOut", duration: 0.3 }}
            />
          </div>

          {/* Indeterminate shimmer during processing */}
          {status === "processing" && (
            <motion.div
              className="text-xs text-center text-[oklch(0.5_0.008_285)]"
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ repeat: Infinity, duration: 1.5 }}
            >
              Converting to final format…
            </motion.div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
