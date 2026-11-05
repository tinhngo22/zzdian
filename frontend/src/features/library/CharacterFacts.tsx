import type { ReactNode } from "react";

export interface Fact {
  label: string;
  value: ReactNode;
}

/** Label/value rows; rows without a value are dropped. */
export function FactList({ facts, compact = false }: { facts: Fact[]; compact?: boolean }) {
  const shown = facts.filter((f) => f.value);
  if (shown.length === 0) {
    return <p className="text-sm text-stone-500">No dictionary data available.</p>;
  }
  return (
    <dl
      className={`grid flex-1 gap-y-3 ${compact ? "grid-cols-[5rem_1fr] gap-x-3" : "grid-cols-[6rem_1fr] gap-x-4"}`}
    >
      {shown.map((f) => (
        <div key={f.label} className="contents">
          <dt className="text-sm font-medium text-stone-500">{f.label}</dt>
          <dd className="text-stone-900">{f.value}</dd>
        </div>
      ))}
    </dl>
  );
}

const GLYPH_SIZES = {
  lg: "size-32 text-7xl max-md:size-24 max-md:text-6xl",
  md: "size-20 text-5xl",
};

export function BigGlyph({ glyph, size = "lg" }: { glyph: string; size?: keyof typeof GLYPH_SIZES }) {
  return (
    <span
      lang="zh-Hans"
      className={`flex shrink-0 items-center justify-center rounded-2xl border border-stone-200 bg-stone-50 font-cjk text-stone-900 ${GLYPH_SIZES[size]}`}
    >
      {glyph}
    </span>
  );
}

export function joinReadings(pinyin: string[] | null | undefined): string | null {
  const readings = pinyin?.filter(Boolean) ?? [];
  return readings.length ? readings.join(", ") : null;
}
