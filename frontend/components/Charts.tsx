"use client";

type AnalysisSummary = {
  big_o: string;
  cyclomatic_complexity: number;
  maintainability: number;
  security_summary: string;
  ai_summary: string;
  risk_level: string;
  risk_score: number;
  complexity_trend: string;
};

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

type ChartsProps = {
  analysis: AnalysisSummary | null;
  metricsComparison: MetricsComparison | null;
};

export function Charts({ analysis, metricsComparison }: ChartsProps) {
  if (!analysis && !metricsComparison) {
    return (
      <div className="text-sm text-neutral-500">
        Run an analysis or comparison to see charts.
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <div className="rounded-lg border border-neutral-800 bg-neutral-950/40 p-3">
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-400">
          Complexity Trend
        </h3>
        <LineChart complexityTrend={analysis?.complexity_trend ?? "stable"} />
      </div>

      <div className="rounded-lg border border-neutral-800 bg-neutral-950/40 p-3">
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-400">
          Risk Level
        </h3>
        <PieChart riskLevel={analysis?.risk_level ?? "Low"} />
      </div>

      <div className="rounded-lg border border-neutral-800 bg-neutral-950/40 p-3">
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-400">
          Metrics Comparison
        </h3>
        <BarChart metrics={metricsComparison} />
      </div>
    </div>
  );
}

type LineChartProps = {
  complexityTrend: string;
};

function LineChart({ complexityTrend }: LineChartProps) {
  const trendMap: Record<string, number> = {
    stable: 1,
    slightly_increasing: 2,
    increasing: 3,
  };

  const value = trendMap[complexityTrend] ?? 1;

  return (
    <div className="flex h-24 items-end gap-1">
      {[0, 1, 2].map((i) => {
        const height =
          i === 2 ? value : i === 1 ? Math.max(1, value - 1) : 1;
        return (
          <div
            key={i}
            className="flex-1 rounded-t bg-sky-500/70"
            style={{ height: `${height * 20}px` }}
          />
        );
      })}
      <div className="ml-2 text-xs text-neutral-400">
        <div className="font-mono">{complexityTrend}</div>
      </div>
    </div>
  );
}

type PieChartProps = {
  riskLevel: string;
};

function PieChart({ riskLevel }: PieChartProps) {
  const levels = ["Low", "Medium", "High", "Critical"] as const;

  return (
    <div className="flex items-center gap-3">
      <div className="relative h-16 w-16 rounded-full border border-neutral-700 bg-neutral-900">
        {levels.map((lvl) => {
          const active = lvl === riskLevel;
          return (
            <div
              key={lvl}
              className={`absolute inset-1 rounded-full border-2 transition-opacity ${
                active
                  ? "border-emerald-400 opacity-100"
                  : "border-neutral-700 opacity-10"
              }`}
            />
          );
        })}
      </div>
      <div className="text-xs text-neutral-300">
        <div className="font-semibold">{riskLevel || "Unknown"}</div>
        <div className="mt-1 text-neutral-500">
          Based on backend risk scoring.
        </div>
      </div>
    </div>
  );
}

type BarChartProps = {
  metrics: MetricsComparison | null;
};

function BarChart({ metrics }: BarChartProps) {
  if (!metrics) {
    return (
      <div className="text-xs text-neutral-500">
        Compare two versions to see metric bars.
      </div>
    );
  }

  const rows: {
    label: string;
    a: number;
    b: number;
  }[] = [
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
  ];

  const max = Math.max(
    1,
    ...rows.flatMap((r) => [r.a, r.b]),
  );

  return (
    <div className="flex flex-col gap-2 text-xs">
      {rows.map((row) => (
        <div key={row.label}>
          <div className="mb-1 flex justify-between text-neutral-400">
            <span>{row.label}</span>
          </div>
          <div className="mb-1 flex gap-1">
            <div className="w-4 text-right text-[10px] text-neutral-500">A</div>
            <div className="flex-1 rounded bg-sky-500/70">
              <div
                className="h-3 rounded bg-sky-400"
                style={{ width: `${(row.a / max) * 100 || 4}%` }}
              />
            </div>
            <div className="w-6 text-[10px] text-neutral-400 text-right">
              {row.a}
            </div>
          </div>
          <div className="flex gap-1">
            <div className="w-4 text-right text-[10px] text-neutral-500">B</div>
            <div className="flex-1 rounded bg-amber-500/70">
              <div
                className="h-3 rounded bg-amber-400"
                style={{ width: `${(row.b / max) * 100 || 4}%` }}
              />
            </div>
            <div className="w-6 text-[10px] text-neutral-400 text-right">
              {row.b}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

