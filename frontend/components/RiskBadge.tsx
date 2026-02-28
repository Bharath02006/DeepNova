"use client";

type RiskLevel = "Low" | "Medium" | "High" | "Critical" | string;

type RiskBadgeProps = {
  level: RiskLevel | null | undefined;
};

export function RiskBadge({ level }: RiskBadgeProps) {
  const normalized = (level || "Unknown").toString();

  const palette: Record<string, { bg: string; border: string; text: string }> = {
    Low: {
      bg: "bg-emerald-900/30",
      border: "border-emerald-500/70",
      text: "text-emerald-200",
    },
    Medium: {
      bg: "bg-amber-900/30",
      border: "border-amber-400/80",
      text: "text-amber-200",
    },
    High: {
      bg: "bg-orange-900/40",
      border: "border-orange-500/80",
      text: "text-orange-100",
    },
    Critical: {
      bg: "bg-red-950/60",
      border: "border-red-500/90",
      text: "text-red-100",
    },
    Unknown: {
      bg: "bg-neutral-900/60",
      border: "border-neutral-600",
      text: "text-neutral-200",
    },
  };

  const colors = palette[normalized as keyof typeof palette] ?? palette.Unknown;

  return (
    <span
      className={[
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium",
        colors.bg,
        colors.border,
        colors.text,
      ].join(" ")}
    >
      <span
        className={[
          "h-1.5 w-1.5 rounded-full",
          normalized === "Low"
            ? "bg-emerald-400"
            : normalized === "Medium"
            ? "bg-amber-300"
            : normalized === "High"
            ? "bg-orange-400"
            : normalized === "Critical"
            ? "bg-red-500"
            : "bg-neutral-400",
        ].join(" ")}
      />
      <span>{normalized}</span>
    </span>
  );
}

