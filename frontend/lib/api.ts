const BASE_URL = "http://localhost:8000";

type FetchOptions = {
  signal?: AbortSignal;
};

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Request failed (${res.status}): ${text || res.statusText}`);
  }
  return (await res.json()) as T;
}

export async function analyze(code: string, options: FetchOptions = {}) {
  const res = await fetch(`${BASE_URL}/code/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    // Treat all dashboard analysis as Python so the backend
    // can run syntax validation with ast.parse.
    body: JSON.stringify({ code, language: "python" }),
    signal: options.signal,
  });

  return handleResponse<{
    big_o: string;
    cyclomatic_complexity: number;
    maintainability: number;
    security_summary: string;
    ai_summary: string;
    risk_level: string;
    risk_score: number;
    complexity_trend: string;
  }>(res);
}

export async function compare(codeA: string, codeB: string, options: FetchOptions = {}) {
  const res = await fetch(`${BASE_URL}/compare`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      original_code: codeA,
      modified_code: codeB,
    }),
    signal: options.signal,
  });

  return handleResponse(res);
}

export async function chat(code: string | null, query: string, options: FetchOptions = {}) {
  const messages = [
    {
      role: "user",
      content: query,
    },
  ];

  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      messages,
      context_snippet: code ?? undefined,
    }),
    signal: options.signal,
  });

  return handleResponse<{
    messages: { role: string; content: string }[];
  }>(res);
}

export async function autofix(code: string, options: FetchOptions = {}) {
  const res = await fetch(`${BASE_URL}/autofix`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ code }),
    signal: options.signal,
  });

  return handleResponse<{
    fixed_code: string;
    diff_summary: string[];
    changes: { title: string; description: string }[];
  }>(res);
}

export async function analyzeStructure(files: string[], options: FetchOptions = {}) {
  // This assumes a backend endpoint will be added that accepts
  // a list of file paths and returns the structure analysis JSON.
  const res = await fetch(`${BASE_URL}/structure/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ files }),
    signal: options.signal,
  });

  return handleResponse<{
    total_files: number;
    language_breakdown: Record<string, number>;
    risky_modules: {
      file_path: string;
      language: string;
      reasons: string[];
    }[];
    summary: string;
  }>(res);
}

