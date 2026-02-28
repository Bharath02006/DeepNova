"use client";

import { useState } from "react";
import { compare } from "../lib/api";

type MetricsComparison = {
  A: {
    big_o: string;
    cyclomatic_complexity: number;
    maintainability: number;
    risk_score: number;
    risk_level: string;
  };
  B: {
    big_o: string;
    cyclomatic_complexity: number;
    maintainability: number;
    risk_score: number;
    risk_level: string;
  };
  delta: {
    cyclomatic_complexity: number;
    risk_score: number;
  };
};

type CompareResponse = {
  diff: {
    added: string[];
    removed: string[];
    changed: string[];
  };
  risk_score: number | null;
  summary: string | null;
  metrics_comparison?: MetricsComparison;
};

type DiffViewerProps = {
  originalCode: string;
};

export function DiffViewer({ originalCode }: DiffViewerProps) {
  const [modifiedCode, setModifiedCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CompareResponse | null>(null);

  const canCompare = !!originalCode && !!modifiedCode && !loading;

  async function handleCompare() {
    if (!canCompare) return;
    setLoading(true);
    setError(null);

    try {
      const res = await compare(originalCode, modifiedCode);
      setResult(res as CompareResponse);
    } catch (err: any) {
      setError(err?.message ?? "Failed to compare code.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-neutral-800 bg-neutral-950/40 p-3">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-neutral-400">
          Diff &amp; Metrics
        </h3>
        <button
          type="button"
          onClick={handleCompare}
          disabled={!canCompare}
          className="rounded bg-sky-600 px-3 py-1 text-xs font-medium text-white disabled:cursor-not-allowed disabled:bg-neutral-700"
        >
          {loading ? "Comparing..." : "Compare"}
        </button>
      </div>

      <label className="flex flex-col gap-1 text-xs text-neutral-300">
        <span className="text-neutral-400">Second version (paste here)</span>
        <textarea
          className="min-h-[120px] rounded border border-neutral-700 bg-black/40 p-2 font-mono text-xs text-neutral-100 outline-none focus:border-sky-500"
          placeholder="Paste the updated version of your code..."
          value={modifiedCode}
          onChange={(e) => setModifiedCode(e.target.value)}
        />
      </label>

      {error && (
        <div className="rounded border border-red-800 bg-red-950/40 p-2 text-xs text-red-300">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-1 grid gap-3 md:grid-cols-2">
          <div className="space-y-2 text-xs">
            <div className="rounded border border-neutral-800 bg-black/40 p-2">
              <div className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-neutral-400">
                Summary
              </div>
              <div className="text-neutral-200">
                {result.summary || "No summary from backend."}
              </div>
              {typeof result.risk_score === "number" && (
                <div className="mt-2 text-neutral-400">
                  Basic diff risk score:{" "}
                  <span className="font-mono">{result.risk_score}</span>
                </div>
              )}
            </div>

            <div className="rounded border border-neutral-800 bg-black/40 p-2">
              <div className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-neutral-400">
                Line Changes
              </div>
              <div className="space-y-1">
                <div>
                  <span className="text-emerald-400">+ Added</span>{" "}
                  <span className="text-neutral-500">
                    ({result.diff.added.length})
                  </span>
                </div>
                <div>
                  <span className="text-red-400">- Removed</span>{" "}
                  <span className="text-neutral-500">
                    ({result.diff.removed.length})
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="rounded border border-neutral-800 bg-black/40 p-2 text-xs">
            <div className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-neutral-400">
              Metrics Comparison
            </div>
            {result.metrics_comparison ? (
              <MetricsTable metrics={result.metrics_comparison} />
            ) : (
              <div className="text-neutral-500">
                Metrics comparison not available yet.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

type MetricsTableProps = {
  metrics: MetricsComparison;
};

function MetricsTable({ metrics }: MetricsTableProps) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-[11px] text-neutral-500">
        <span>Metric</span>
        <span className="flex gap-4">
          <span>A</span>
          <span>B</span>
        </span>
      </div>
      {[
        {
          label: "Cyclomatic",
          a: metrics.A.cyclomatic_complexity,
          b: metrics.B.cyclomatic_complexity,
        },
        {
          label: "Risk score",
          a: metrics.A.risk_score,
          b: metrics.B.risk_score,
        },
      ].map((row) => (
        <div
          key={row.label}
          className="flex items-center justify-between rounded border border-neutral-800 bg-neutral-950/40 px-2 py-1"
        >
          <span className="text-neutral-300">{row.label}</span>
          <span className="flex gap-4 font-mono text-[11px]">
            <span className="text-sky-300">{row.a}</span>
            <span className="text-amber-300">{row.b}</span>
          </span>
        </div>
      ))}
    </div>
  );
}

