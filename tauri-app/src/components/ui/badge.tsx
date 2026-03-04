import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "bg-[oklch(0.2_0.006_285)] text-[oklch(0.7_0.01_285)] border border-[oklch(0.28_0.006_285)]",
        red: "bg-red-900/30 text-red-400 border border-red-900/50",
        green: "bg-green-900/30 text-green-400 border border-green-900/50",
        audio: "bg-blue-900/30 text-blue-400 border border-blue-900/50",
        video: "bg-purple-900/30 text-purple-400 border border-purple-900/50",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
