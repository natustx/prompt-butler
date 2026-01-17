import * as React from "react"

import { cn } from "@/lib/utils"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "flex h-9 w-full min-w-0 border bg-transparent px-3 py-1 text-base transition-all outline-none md:text-sm",
        "border-border bg-page text-foreground",
        "placeholder:text-muted-foreground/70",
        "selection:bg-primary selection:text-primary-foreground",
        "file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground",
        "focus-visible:border-primary focus-visible:shadow-[0_0_0_1px_rgba(0,255,0,0.1),inset_0_0_10px_rgba(0,255,0,0.1)]",
        "hover:border-primary/50",
        "disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50",
        "aria-invalid:border-destructive aria-invalid:shadow-[0_0_0_1px_rgba(255,107,107,0.2)]",
        "caret-primary",
        className
      )}
      {...props}
    />
  )
}

export { Input }
