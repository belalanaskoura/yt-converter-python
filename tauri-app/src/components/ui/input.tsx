import * as React from "react";
import { cn } from "@/lib/utils";

const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, type, ...props }, ref) => {
  return (
    <input
      type={type}
      className={cn(
        "flex h-10 w-full rounded-lg border border-[oklch(0.25_0.006_285)] bg-[oklch(0.14_0.006_285)] px-3 py-2 text-sm text-white placeholder:text-[oklch(0.45_0.008_285)] focus:outline-none focus:ring-2 focus:ring-red-600/50 focus:border-red-600/60 transition-all duration-150 disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      ref={ref}
      {...props}
    />
  );
});
Input.displayName = "Input";

export { Input };
