import { cva, type VariantProps } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";

import { cn } from "../../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-xl px-3 py-2 text-sm font-medium transition focus-visible:outline-none",
  {
    variants: {
      variant: {
        default: "bg-primary text-white hover:bg-blue-500",
        ghost: "bg-transparent text-textMuted hover:bg-panelMuted hover:text-text",
        outline: "border border-border bg-panel text-text hover:bg-panelMuted"
      }
    },
    defaultVariants: {
      variant: "default"
    }
  }
);

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & VariantProps<typeof buttonVariants>;

export function Button({ className, variant, ...props }: ButtonProps) {
  return <button className={cn(buttonVariants({ variant }), className)} {...props} />;
}

