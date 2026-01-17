import * as React from "react"

import { cn } from "@/lib/utils"

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "flex field-sizing-content min-h-16 w-full border bg-transparent px-3 py-2 text-base transition-all outline-none md:text-sm",
        "border-border bg-page text-foreground",
        "placeholder:text-muted-foreground/70",
        "focus-visible:border-primary focus-visible:shadow-[0_0_0_1px_rgba(0,255,0,0.1),inset_0_0_10px_rgba(0,255,0,0.1)]",
        "hover:border-primary/50",
        "disabled:cursor-not-allowed disabled:opacity-50",
        "aria-invalid:border-destructive aria-invalid:shadow-[0_0_0_1px_rgba(255,107,107,0.2)]",
        "caret-primary",
        className
      )}
      {...props}
    />
  )
}

export { Textarea }
