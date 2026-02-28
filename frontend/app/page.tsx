"use client";

import React, { useState } from "react";
import { analyze, autofix, chat } from "../lib/api";
import { CodeEditor } from "../components/CodeEditor";
import { Charts } from "../components/Charts";
import { DiffViewer } from "../components/DiffViewer";
import { FileUpload } from "../components/FileUpload";
import { MicButton } from "../components/MicButton";
import { RiskBadge } from "../components/RiskBadge";

type AnalysisResult = {
  big_o: string;
  cyclomatic_complexity: number;
  maintainability: number;
  security_summary: string;
  ai_summary: string;
  risk_level: string;
  risk_score: number;
  complexity_trend: string;
};

type AutofixResult = {
  fixed_code: string;
  diff_summary: string[];
  changes: { title: string; description: string }[];
} | null;

type ChatMessage = {
  role: string;
  content: string;
};

type TabId = "analyze" | "compare" | "autofix" | "chat";

export default function Home() {
  const [code, setCode] = useState("");
  const [activeTab, setActiveTab] = useState<TabId>("analyze");

  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<{ error: string; message: string } | null>(
    null,
  );

  const [autofixResult, setAutofixResult] = useState<AutofixResult>(null);
  const [autofixing, setAutofixing] = useState(false);

  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatSending, setChatSending] = useState(false);

  const canAnalyze = code.trim().length > 0 && !analyzing;
  const tabsDisabled = !!analysisError;
  const canAutofix = !tabsDisabled && code.trim().length > 0 && !autofixing;
  const canChat = !tabsDisabled && chatInput.trim().length > 0 && !chatSending;

  async function handleAnalyze() {
    if (!canAnalyze) return;
    setAnalyzing(true);
    try {
      const data: any = await analyze(code);

      if (data && typeof data === "object" && data.error) {
        setAnalysis(null);
        setAnalysisError({
          error: String(data.error ?? "SyntaxError"),
          message: String(data.message ?? "Invalid syntax."),
        });
        setActiveTab("analyze");
      } else {
        setAnalysis(data as AnalysisResult);
        setAnalysisError(null);
      }
    } catch (err) {
      console.error(err);
      alert("Analysis failed. Is the backend running on http://localhost:8000?");
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleAutofix() {
    if (!canAutofix) return;
    setAutofixing(true);
    try {
      const res = await autofix(code);
      setAutofixResult(res);
    } catch (err) {
      console.error(err);
      alert("Autofix failed. Check backend.");
    } finally {
      setAutofixing(false);
    }
  }

  async function handleSendChat() {
    if (!canChat) return;
    setChatSending(true);
    try {
      const res = await chat(code || null, chatInput.trim());
      setChatMessages(res.messages);
      setChatInput("");
    } catch (err) {
      console.error(err);
      alert("Chat failed. Check backend.");
    } finally {
      setChatSending(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-50">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-6">
        {/* Top header + file upload */}
        <header className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
              AI Code Intelligence Suite
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Single-screen dashboard for complexity, risk, autofix and AI chat — tuned for
              hackathon demos.
            </p>
          </div>

          <div className="flex flex-col items-stretch gap-2 sm:flex-row sm:items-center">
            <FileUpload onExtract={setCode} />
            <div className="hidden h-full w-px bg-slate-800 sm:block" />
            <div className="sm:self-stretch">
              <MicButton codeContext={code} />
            </div>
          </div>
        </header>

        {/* Main two-column layout */}
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
          {/* Left: editor */}
          <section className="flex flex-col gap-3">
            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
              <CodeEditor
                value={code}
                onChange={setCode}
                language="auto"
                isAnalyzing={analyzing}
                riskLevel={analysis?.risk_level ?? null}
              />
            </div>
          </section>

          {/* Right: tabs */}
          <section className="flex flex-col gap-3 rounded-xl border border-slate-800 bg-slate-950/60 p-3">
            <div className="mb-2 flex gap-2 border-b border-slate-800 pb-1 text-xs font-medium text-slate-400">
              {(["analyze", "compare", "autofix", "chat"] as TabId[]).map((tab) => (
                <button
                  key={tab}
                  type="button"
                  onClick={() => {
                    if (analysisError && tab !== "analyze") return;
                    setActiveTab(tab);
                  }}
                  disabled={analysisError != null && tab !== "analyze"}
                  className={`rounded-t px-3 py-1 transition-colors ${
                    activeTab === tab
                      ? "border-b-2 border-b-sky-400 bg-slate-900 text-sky-200"
                      : analysisError && tab !== "analyze"
                      ? "cursor-not-allowed text-slate-700"
                      : "text-slate-500 hover:text-slate-200"
                  }`}
                >
                  {tab === "analyze"
                    ? "Analyze"
                    : tab === "compare"
                    ? "Compare"
                    : tab === "autofix"
                    ? "Autofix"
                    : "Chat"}
                </button>
              ))}
            </div>

            <div className="min-h-[260px] text-sm">
              {activeTab === "analyze" && (
                <div className="flex flex-col gap-3">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                        Static &amp; AI analysis
                      </h2>
                      <p className="text-xs text-slate-500">
                        Run the backend analyzer on the current code.
                      </p>
                    </div>
                    <button
                      type="button"
                      disabled={!canAnalyze}
                      onClick={handleAnalyze}
                      className="rounded-full bg-sky-600 px-3 py-1 text-xs font-semibold text-slate-50 shadow-sm shadow-sky-500/30 disabled:cursor-not-allowed disabled:bg-slate-700"
                    >
                      {analyzing ? "Analyzing…" : "Analyze"}
                    </button>
                  </div>

                  {analysisError ? (
                    <div className="rounded border border-red-800 bg-red-950/40 p-3 text-xs text-red-200">
                      <div className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-red-300">
                        {analysisError.error}
                      </div>
                      <div>{analysisError.message}</div>
                      <p className="mt-2 text-[11px] text-red-300/80">
                        Fix the syntax error above before running complexity, security, autofix or
                        chat features.
                      </p>
                    </div>
                  ) : analysis ? (
                    <>
                      <div className="grid gap-2 md:grid-cols-2">
                        <div className="rounded border border-slate-800 bg-slate-950/60 p-2">
                          <div className="text-[11px] uppercase tracking-wide text-slate-500">
                            Big O
                          </div>
                          <div className="mt-1 text-sm font-medium text-slate-100">
                            {analysis.big_o}
                          </div>
                        </div>
                        <div className="rounded border border-slate-800 bg-slate-950/60 p-2">
                          <div className="text-[11px] uppercase tracking-wide text-slate-500">
                            Cyclomatic complexity
                          </div>
                          <div className="mt-1 text-sm font-medium text-slate-100">
                            {analysis.cyclomatic_complexity}
                          </div>
                        </div>
                        <div className="rounded border border-slate-800 bg-slate-950/60 p-2">
                          <div className="text-[11px] uppercase tracking-wide text-slate-500">
                            Maintainability
                          </div>
                          <div className="mt-1 text-sm font-medium text-slate-100">
                            {analysis.maintainability.toFixed(1)} / 100
                          </div>
                        </div>
                        <div className="rounded border border-slate-800 bg-slate-950/60 p-2">
                          <div className="text-[11px] uppercase tracking-wide text-slate-500">
                            Risk
                          </div>
                          <div className="mt-1 flex items-center gap-2 text-sm">
                            <RiskBadge level={analysis.risk_level} />
                            <span className="text-xs text-slate-400">
                              score {analysis.risk_score}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="rounded border border-slate-800 bg-slate-950/60 p-2">
                        <div className="mb-1 text-[11px] uppercase tracking-wide text-slate-500">
                          AI summary
                        </div>
                        <p className="text-xs leading-relaxed text-slate-100 whitespace-pre-wrap">
                          {analysis.ai_summary}
                        </p>
                        <p className="mt-2 text-[11px] text-slate-500">
                          Security: {analysis.security_summary}
                        </p>
                      </div>

                      <Charts analysis={analysis} metricsComparison={null} />
                    </>
                  ) : (
                    <p className="text-xs text-slate-500">
                      Paste some code on the left and click <strong>Analyze</strong> to see
                      results.
                    </p>
                  )}
                </div>
              )}

              {activeTab === "compare" && (
                <div className="flex flex-col gap-3">
                  <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                    Compare versions
                  </h2>
                  <p className="text-xs text-slate-500">
                    Use the current code as version A and paste the updated version inside the
                    diff panel.
                  </p>
                  <DiffViewer originalCode={code} />
                </div>
              )}

              {activeTab === "autofix" && (
                <div className="flex flex-col gap-3">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                        AI Autofix
                      </h2>
                      <p className="text-xs text-slate-500">
                        Generate a minimally improved version of the current code.
                      </p>
                    </div>
                    <button
                      type="button"
                      disabled={!canAutofix}
                      onClick={handleAutofix}
                      className="rounded-full bg-emerald-600 px-3 py-1 text-xs font-semibold text-slate-50 shadow-sm shadow-emerald-500/30 disabled:cursor-not-allowed disabled:bg-slate-700"
                    >
                      {autofixing ? "Autofixing…" : "Run Autofix"}
                    </button>
                  </div>

                  {autofixResult ? (
                    <>
                      <div className="rounded border border-slate-800 bg-slate-950/60 p-2">
                        <div className="mb-1 text-[11px] uppercase tracking-wide text-slate-500">
                          Improved code (read-only)
                        </div>
                        <pre className="max-h-72 overflow-auto rounded bg-slate-950 p-3 text-xs text-slate-100">
                          {autofixResult.fixed_code}
                        </pre>
                      </div>

                      <div className="rounded border border-slate-800 bg-slate-950/60 p-2 text-xs text-slate-200">
                        {autofixResult.diff_summary.length > 0 && (
                          <div className="mb-2">
                            <div className="text-[11px] uppercase tracking-wide text-slate-500">
                              Diff summary
                            </div>
                            <ul className="mt-1 list-disc space-y-1 pl-4">
                              {autofixResult.diff_summary.map((item, idx) => (
                                <li key={idx}>{item}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {autofixResult.changes.length > 0 && (
                          <div>
                            <div className="text-[11px] uppercase tracking-wide text-slate-500">
                              Changes
                            </div>
                            <ul className="mt-1 space-y-1">
                              {autofixResult.changes.map((c, idx) => (
                                <li
                                  key={idx}
                                  className="rounded border border-slate-800 bg-slate-950/70 px-2 py-1"
                                >
                                  <div className="font-semibold text-slate-100">
                                    {c.title}
                                  </div>
                                  <div className="text-[11px] text-slate-400">
                                    {c.description}
                                  </div>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </>
                  ) : (
                    <p className="text-xs text-slate-500">
                      Click <strong>Run Autofix</strong> to see a suggested improved version.
                    </p>
                  )}
                </div>
              )}

              {activeTab === "chat" && (
                <div className="flex h-full flex-col gap-3">
                  <div>
                    <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                      Chat with code
                    </h2>
                    <p className="text-xs text-slate-500">
                      Ask questions about the current snippet. The backend sees your code as
                      context.
                    </p>
                  </div>

                  <div className="flex-1 space-y-2 rounded border border-slate-800 bg-slate-950/60 p-2">
                    <div className="max-h-64 space-y-2 overflow-auto pr-1 text-xs">
                      {chatMessages.length === 0 ? (
                        <p className="text-slate-500">
                          No messages yet. Ask something like{" "}
                          <span className="italic">"Where are the main risks here?"</span>.
                        </p>
                      ) : (
                        chatMessages.map((m, idx) => (
                          <div
                            key={idx}
                            className={`flex ${
                              m.role === "assistant" ? "justify-start" : "justify-end"
                            }`}
                          >
                            <div
                              className={`max-w-[80%] rounded px-2 py-1 ${
                                m.role === "assistant"
                                  ? "bg-slate-800 text-slate-100"
                                  : "bg-sky-600 text-slate-50"
                              }`}
                            >
                              <div className="text-[10px] font-semibold uppercase tracking-wide text-slate-300/80">
                                {m.role === "assistant" ? "AI" : "You"}
                              </div>
                              <div className="mt-0.5 whitespace-pre-wrap text-xs">
                                {m.content}
                              </div>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                  <form
                    className="flex items-center gap-2 text-xs"
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleSendChat();
                    }}
                  >
                    <input
                      type="text"
                      className="flex-1 rounded border border-slate-800 bg-slate-950 px-2 py-2 text-xs text-slate-100 outline-none focus:border-sky-500"
                      placeholder="Ask the AI about this code..."
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                    />
                    <button
                      type="submit"
                      disabled={!canChat}
                      className="rounded bg-sky-600 px-3 py-2 text-xs font-semibold text-slate-50 disabled:cursor-not-allowed disabled:bg-slate-700"
                    >
                      {chatSending ? "Sending…" : "Send"}
                    </button>
                  </form>
                </div>
              )}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}