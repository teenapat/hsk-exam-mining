import { cva, type VariantProps } from "class-variance-authority";
import type { ReactNode } from "react";

import { cn } from "../../lib/utils";

const badgeVariants = cva("inline-flex rounded-full border px-2 py-0.5 text-xs font-medium", {
  variants: {
    variant: {
      default: "border-border bg-panelMuted text-text",
      success: "border-green-500/30 bg-green-500/15 text-green-300",
      warning: "border-yellow-500/30 bg-yellow-500/15 text-yellow-300",
      danger: "border-red-500/30 bg-red-500/15 text-red-300"
    }
  },
  defaultVariants: {
    variant: "default"
  }
});

export function Badge({
  className,
  variant,
  children
}: VariantProps<typeof badgeVariants> & { className?: string; children: ReactNode }) {
  return <span className={cn(badgeVariants({ variant }), className)}>{children}</span>;
}

