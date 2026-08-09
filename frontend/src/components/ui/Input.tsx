import { forwardRef, type InputHTMLAttributes, type TextareaHTMLAttributes } from "react";
import { cn } from "@/utils/ui";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, hint, error, id, ...rest }, ref) => {
    const inputId = id ?? rest.name;
    return (
      <label className="block">
        {label && (
          <span className="mb-1 block text-xs font-medium text-ink-muted">{label}</span>
        )}
        <input
          ref={ref}
          id={inputId}
          className={cn(
            "w-full rounded-md border border-border bg-bg-panel px-3 py-2 text-sm text-ink placeholder:text-ink-subtle focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent/40 disabled:opacity-60",
            error && "border-red-500/60 focus:border-red-500 focus:ring-red-500/30",
            className,
          )}
          {...rest}
        />
        {(hint || error) && (
          <span className={cn("mt-1 block text-xs", error ? "text-red-400" : "text-ink-subtle")}>
            {error ?? hint}
          </span>
        )}
      </label>
    );
  },
);
Input.displayName = "Input";

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  hint?: string;
  error?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, hint, error, id, ...rest }, ref) => {
    const inputId = id ?? rest.name;
    return (
      <label className="block">
        {label && (
          <span className="mb-1 block text-xs font-medium text-ink-muted">{label}</span>
        )}
        <textarea
          ref={ref}
          id={inputId}
          className={cn(
            "w-full resize-none rounded-md border border-border bg-bg-panel px-3 py-2 text-sm text-ink placeholder:text-ink-subtle focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent/40 disabled:opacity-60",
            error && "border-red-500/60",
            className,
          )}
          {...rest}
        />
        {(hint || error) && (
          <span className={cn("mt-1 block text-xs", error ? "text-red-400" : "text-ink-subtle")}>
            {error ?? hint}
          </span>
        )}
      </label>
    );
  },
);
Textarea.displayName = "Textarea";
