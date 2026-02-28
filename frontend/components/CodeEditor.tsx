"use client";

import { useCallback } from "react";
import { Loader } from "./UI/Loader";
import { RiskBadge } from "./RiskBadge";

type CodeEditorProps = {
  value: string;
  onChange: (val: string) => void;
  language?: string;
  isAnalyzing?: boolean;
  riskLevel?: string | null;
};

export function CodeEditor({
  value,
  onChange,
  language = "auto",
  isAnalyzing = false,
  riskLevel = null,
}: CodeEditorProps) {
  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      onChange(e.target.value);
    },
    [onChange],
  );

  return (
    <div className="relative flex h-full flex-col rounded-lg border border-neutral-800 bg-neutral-950/60">
      <div className="flex items-center justify-between gap-2 border-b border-neutral-800 px-3 py-2 text-[11px] text-neutral-400">
        <div className="flex items-center gap-2">
          <span className="font-semibold uppercase tracking-wide text-neutral-300">
            Code
          </span>
          <span className="rounded bg-neutral-900 px-1.5 py-0.5 font-mono text-[10px] text-neutral-400">
            {language}
          </span>
        </div>
        <div className="flex items-center gap-3">
          {riskLevel && <RiskBadge level={riskLevel} />}
          {isAnalyzing && <Loader small label="Analyzing…" />}
        </div>
      </div>
      <textarea
        className="min-h-[260px] flex-1 resize-none bg-transparent p-3 font-mono text-xs text-neutral-100 outline-none"
        spellCheck={false}
        value={value}
        onChange={handleChange}
        placeholder="// Paste or type code here to analyze..."
      />
    </div>
  );
}

