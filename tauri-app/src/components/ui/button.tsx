import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full text-sm font-semibold transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500/50 disabled:pointer-events-none disabled:opacity-40 cursor-pointer",
  {
    variants: {
      variant: {
        primary:
          "bg-red-600 text-white hover:bg-red-700 active:scale-[0.97] shadow-lg shadow-red-900/30",
        secondary:
          "bg-[oklch(0.2_0.006_285)] text-white hover:bg-[oklch(0.26_0.006_285)] active:scale-[0.97] border border-[oklch(0.28_0.006_285)]",
        ghost:
          "text-[oklch(0.62_0.01_285)] hover:bg-[oklch(0.18_0.006_285)] hover:text-white",
        danger:
          "bg-[oklch(0.18_0.006_285)] text-red-400 hover:bg-red-900/30 border border-[oklch(0.28_0.006_285)]",
      },
      size: {
        sm: "h-8 px-3 text-xs",
        md: "h-10 px-5",
        lg: "h-12 px-8 text-base",
        icon: "h-8 w-8 rounded-md",
      },
    },
    defaultVariants: {
      variant: "secondary",
      size: "md",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
