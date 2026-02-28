"use client";

import { useEffect, useRef, useState } from "react";
import { chat } from "../lib/api";

type MicButtonProps = {
  /** Optional current code snippet to pass as context to /chat */
  codeContext?: string | null;
};

type RecognitionType = SpeechRecognition | webkitSpeechRecognition;

declare global {
  // Web Speech API types (minimal)
  // eslint-disable-next-line no-var
  var webkitSpeechRecognition: {
    new (): webkitSpeechRecognition;
  } | undefined;

  interface SpeechRecognition extends EventTarget {
    lang: string;
    continuous: boolean;
    interimResults: boolean;
    start: () => void;
    stop: () => void;
    abort: () => void;
    onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null;
    onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => any) | null;
    onaudioend: ((this: SpeechRecognition, ev: Event) => any) | null;
  }

  interface SpeechRecognitionResult {
    isFinal: boolean;
    [index: number]: SpeechRecognitionAlternative;
    length: number;
  }

  interface SpeechRecognitionAlternative {
    transcript: string;
    confidence: number;
  }

  interface SpeechRecognitionEvent extends Event {
    results: SpeechRecognitionResultList;
  }

  interface SpeechRecognitionResultList {
    [index: number]: SpeechRecognitionResult;
    length: number;
  }
}

export function MicButton({ codeContext = null }: MicButtonProps) {
  const [supported, setSupported] = useState(true);
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const recognitionRef = useRef<RecognitionType | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const SpeechRecognitionCtor =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognitionCtor) {
      setSupported(false);
      return;
    }

    const recognition: RecognitionType = new SpeechRecognitionCtor();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalText = "";
      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i];
        const alt = result[0];
        finalText += alt.transcript;
      }
      setTranscript(finalText.trim());
    };

    recognition.onerror = (ev: SpeechRecognitionErrorEvent) => {
      setError(ev.error || "Speech recognition error");
      setListening(false);
    };

    recognition.onaudioend = () => {
      setListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.abort();
      recognitionRef.current = null;
    };
  }, []);

  async function handleToggle() {
    if (!supported || !recognitionRef.current) return;
    setError(null);

    if (!listening) {
      setTranscript("");
      setResponse(null);
      setListening(true);
      try {
        recognitionRef.current.start();
      } catch (e: any) {
        setError(e?.message ?? "Unable to start microphone.");
        setListening(false);
      }
    } else {
      recognitionRef.current.stop();
      setListening(false);
    }
  }

  async function handleSend() {
    if (!transcript.trim() || sending) return;
    setSending(true);
    setError(null);

    try {
      const res = await chat(codeContext ?? null, transcript.trim());
      const last = res.messages[res.messages.length - 1];
      setResponse(last?.content ?? "(no response)");
    } catch (e: any) {
      setError(e?.message ?? "Failed to send to chat.");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex flex-col gap-2 rounded-lg border border-neutral-800 bg-neutral-950/40 p-3 text-xs text-neutral-100">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleToggle}
            disabled={!supported}
            className={`flex h-8 w-8 items-center justify-center rounded-full border text-sm transition-colors ${
              listening
                ? "border-red-500 bg-red-600 text-white"
                : "border-neutral-600 bg-neutral-900 text-neutral-200"
            } disabled:cursor-not-allowed disabled:opacity-50`}
            title={supported ? "Hold to speak" : "Speech recognition not supported"}
          >
            🎙
          </button>
          <div className="flex flex-col">
            <span className="text-[11px] font-semibold uppercase tracking-wide text-neutral-400">
              Voice Chat
            </span>
            <span className="text-[11px] text-neutral-500">
              {supported
                ? listening
                  ? "Listening…"
                  : "Tap the mic and speak your question."
                : "Web Speech API not supported in this browser."}
            </span>
          </div>
        </div>
        <button
          type="button"
          onClick={handleSend}
          disabled={!transcript.trim() || sending}
          className="rounded bg-sky-600 px-3 py-1 text-[11px] font-medium text-white disabled:cursor-not-allowed disabled:bg-neutral-700"
        >
          {sending ? "Sending…" : "Ask AI"}
        </button>
      </div>

      {transcript && (
        <div className="rounded border border-neutral-800 bg-black/40 p-2">
          <div className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-neutral-400">
            You said
          </div>
          <div className="text-[11px] text-neutral-100">{transcript}</div>
        </div>
      )}

      {response && (
        <div className="rounded border border-sky-800 bg-sky-950/40 p-2">
          <div className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-sky-300">
            AI response
          </div>
          <div className="whitespace-pre-wrap text-[11px] text-neutral-50">
            {response}
          </div>
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

