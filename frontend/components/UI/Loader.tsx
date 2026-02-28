"use client";

type LoaderProps = {
  label?: string;
  small?: boolean;
};

export function Loader({ label = "Thinking…", small = false }: LoaderProps) {
  const size = small ? "h-3 w-3" : "h-4 w-4";

  return (
    <div className="inline-flex items-center gap-2 text-[11px] text-neutral-400">
      <span
        className={`${size} animate-spin rounded-full border-2 border-sky-500 border-t-transparent`}
      />
      <span>{label}</span>
    </div>
  );
}

