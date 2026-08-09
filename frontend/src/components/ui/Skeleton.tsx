import { cn } from "@/utils/ui";

interface SkeletonProps {
  className?: string;
  // Use a small width/height to control shape when the consumer wants
  // a precise placeholder (e.g. a 100x100 thumbnail).
  width?: number | string;
  height?: number | string;
  rounded?: boolean;
}

// Skeleton — shimmer placeholder used while async content loads.
//
// Why hand-rolled: a single CSS animation is ~10 lines, no extra deps,
// and avoids pulling in tailwindcss-animate or a UI kit. The pulse uses
// the existing ink-subtle colour so it disappears naturally in both
// panels and cards.

const style = (width?: number | string, height?: number | string): React.CSSProperties => {
  const out: React.CSSProperties = {};
  if (width !== undefined) out.width = typeof width === "number" ? `${width}px` : width;
  if (height !== undefined)
    out.height = typeof height === "number" ? `${height}px` : height;
  return out;
};

export const Skeleton = ({ className, width, height, rounded }: SkeletonProps) => (
  <span
    aria-hidden
    style={style(width, height)}
    className={cn(
      "block animate-pulse bg-bg-hover",
      rounded ? "rounded-full" : "rounded-md",
      className,
    )}
  />
);

export const SkeletonText = ({ lines = 3 }: { lines?: number }) => (
  <div className="space-y-2" aria-hidden>
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton
        key={i}
        height={12}
        className={i === lines - 1 ? "w-2/3" : "w-full"}
      />
    ))}
  </div>
);
