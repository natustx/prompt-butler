import * as React from "react"

import { cn } from "@/lib/utils"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "file:text-[var(--terminal-green)] placeholder:text-[var(--terminal-text-dim)] selection:bg-[var(--terminal-green)] selection:text-[var(--terminal-black)] flex h-9 w-full min-w-0 border border-[var(--terminal-border)] bg-[var(--terminal-dark)] px-3 py-1 text-base text-[var(--terminal-text)] transition-all outline-none file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
        "focus-visible:border-[var(--terminal-green)] focus-visible:shadow-[0_0_10px_var(--terminal-green-glow)]",
        "aria-invalid:border-[var(--terminal-red)] aria-invalid:shadow-[0_0_10px_rgba(255,51,51,0.2)]",
        className
      )}
      {...props}
    />
  )
}

export { Input }
