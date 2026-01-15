import * as React from "react"

import { cn } from "@/lib/utils"

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "border-[var(--terminal-border)] placeholder:text-[var(--terminal-text-dim)] focus-visible:border-[var(--terminal-green)] focus-visible:shadow-[0_0_10px_var(--terminal-green-glow)] aria-invalid:border-[var(--terminal-red)] aria-invalid:shadow-[0_0_10px_rgba(255,51,51,0.2)] bg-[var(--terminal-dark)] text-[var(--terminal-text)] flex field-sizing-content min-h-16 w-full border px-3 py-2 text-base transition-all outline-none disabled:cursor-not-allowed disabled:opacity-50 md:text-sm selection:bg-[var(--terminal-green)] selection:text-[var(--terminal-black)]",
        className
      )}
      {...props}
    />
  )
}

export { Textarea }
