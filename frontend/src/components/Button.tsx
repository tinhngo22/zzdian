import type { ButtonHTMLAttributes, Ref } from "react";
import { Spinner } from "./Spinner";

type Variant = "primary" | "secondary" | "danger" | "ghost" | "dangerGhost";
type Size = "sm" | "md";

const VARIANTS: Record<Variant, string> = {
  primary: "bg-red-700 text-white hover:bg-red-800 disabled:bg-red-700/60",
  secondary:
    "border border-stone-300 bg-white text-stone-800 hover:bg-stone-50 disabled:text-stone-400",
  danger: "bg-rose-600 text-white hover:bg-rose-700 disabled:bg-rose-600/60",
  ghost: "text-stone-700 hover:bg-stone-100 disabled:text-stone-400",
  dangerGhost: "text-rose-700 hover:bg-rose-50 disabled:text-rose-300",
};

const SIZES: Record<Size, string> = {
  sm: "h-8 px-3 text-sm",
  md: "h-10 px-4 text-sm",
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  /** Shows a spinner and disables the button (prevents double submits). */
  pending?: boolean;
  ref?: Ref<HTMLButtonElement>;
}

export function Button({
  variant = "primary",
  size = "md",
  pending = false,
  disabled,
  className = "",
  children,
  type = "button",
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled || pending}
      aria-busy={pending || undefined}
      className={`inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-700 disabled:cursor-not-allowed ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...rest}
    >
      {pending && <Spinner />}
      {children}
    </button>
  );
}
