"use client";

import { useState } from "react";

type FileUploadProps = {
  /** Called with extracted text so the parent can update CodeEditor */
  onExtract: (text: string) => void;
};

export function FileUpload({ onExtract }: FileUploadProps) {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setProgress(0);
    setError(null);

    try {
      // Lazy-load Tesseract.js only in the browser.
      const mod = await import("tesseract.js");
      const Tesseract = mod.default || mod;

      const { data } = await Tesseract.recognize(file, "eng", {
        logger: (m: any) => {
          if (m.status === "recognizing text" && typeof m.progress === "number") {
            setProgress(Math.round(m.progress * 100));
          }
        },
      });

      const text = (data.text || "").trim();
      if (!text) {
        setError("No text detected in image.");
      } else {
        onExtract(text);
      }
    } catch (err: any) {
      setError(err?.message ?? "Failed to extract code from image.");
    } finally {
      setLoading(false);
      setProgress(null);
      // Reset input so the same file can be chosen again if needed.
      e.target.value = "";
    }
  }

  return (
    <div className="flex flex-col gap-2 rounded-lg border border-neutral-800 bg-neutral-950/40 p-3 text-xs text-neutral-100">
      <div className="flex items-center justify-between gap-2">
        <div className="flex flex-col">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-neutral-400">
            Image to Code
          </span>
          <span className="text-[11px] text-neutral-500">
            Upload screenshot of code. We&apos;ll OCR with Tesseract.js and fill the editor.
          </span>
        </div>
        <label className="inline-flex cursor-pointer items-center rounded bg-sky-600 px-3 py-1 text-[11px] font-medium text-white hover:bg-sky-500 disabled:cursor-not-allowed">
          <input
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleChange}
            disabled={loading}
          />
          {loading ? "Processing…" : "Upload"}
        </label>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-[11px] text-neutral-400">
          <div className="h-1 flex-1 overflow-hidden rounded bg-neutral-800">
            <div
              className="h-1 bg-sky-400 transition-[width]"
              style={{ width: `${progress ?? 10}%` }}
            />
          </div>
          <span>{progress != null ? `${progress}%` : "Starting…"}</span>
        </div>
      )}

      {error && (
        <div className="rounded border border-red-800 bg-red-950/40 p-2 text-[11px] text-red-300">
          {error}
        </div>
      )}
    </div>
  );
}

