import type { HTMLAttributes } from "react";

export function Card({ className = "", ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded-xl border border-stone-200 bg-white shadow-sm ${className}`}
      {...rest}
    />
  );
}
