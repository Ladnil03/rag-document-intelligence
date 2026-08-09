// Centralised, theme-aware className helpers. The point is to avoid scattering
// long Tailwind class strings across components. Each helper returns the final
// class string the consumer spreads onto the element.

import type { ReactNode } from "react";

export const cn = (...parts: Array<string | false | null | undefined>): string =>
  parts.filter(Boolean).join(" ");

export type ClassValue = string | false | null | undefined;

export const Spinner = ({ className }: { className?: ClassValue }) => (
  <span
    aria-hidden
    className={cn(
      "inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent",
      className,
    )}
  />
);

export const formatBytes = (bytes: number | null | undefined): string => {
  if (!bytes && bytes !== 0) return "—";
  const units = ["B", "KB", "MB", "GB"];
  let value = bytes;
  let i = 0;
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024;
    i += 1;
  }
  return `${value.toFixed(value < 10 && i > 0 ? 1 : 0)} ${units[i]}`;
};

export const formatDate = (iso: string): string =>
  new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });

export const formatRelative = (iso: string): string => {
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.round(diff / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  if (days < 7) return `${days}d ago`;
  return formatDate(iso);
};

export type { ReactNode };
