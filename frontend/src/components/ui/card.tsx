import type { ReactNode } from "react";

import { cn } from "../../lib/utils";

export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return (
    <section className={cn("rounded-2xl border border-border bg-panel p-5 shadow-glow", className)}>
      {children}
    </section>
  );
}

export function CardTitle({ children, className }: { children: ReactNode; className?: string }) {
  return <h3 className={cn("text-sm font-medium text-textMuted", className)}>{children}</h3>;
}

export function CardValue({ children, className }: { children: ReactNode; className?: string }) {
  return <p className={cn("mt-2 text-3xl font-semibold text-text", className)}>{children}</p>;
}

