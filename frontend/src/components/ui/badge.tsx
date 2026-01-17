import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center justify-center border px-2 py-0.5 text-xs font-medium w-fit whitespace-nowrap shrink-0 [&>svg]:size-3 gap-1 [&>svg]:pointer-events-none focus-visible:border-[var(--terminal-green)] focus-visible:shadow-[0_0_10px_var(--terminal-green-glow)] transition-all overflow-hidden",
  {
    variants: {
      variant: {
        default:
          "border-[var(--terminal-green-dim)] bg-[var(--terminal-green)]/10 text-[var(--terminal-green)] [a&]:hover:bg-[var(--terminal-green)]/20",
        secondary:
          "border-[var(--terminal-amber-dim)] bg-[var(--terminal-amber)]/10 text-[var(--terminal-amber)] [a&]:hover:bg-[var(--terminal-amber)]/20",
        destructive:
          "border-[var(--terminal-red)]/50 bg-[var(--terminal-red)]/10 text-[var(--terminal-red)] [a&]:hover:bg-[var(--terminal-red)]/20",
        outline:
          "border-[var(--terminal-border)] text-[var(--terminal-text)] [a&]:hover:bg-[var(--terminal-green)]/10 [a&]:hover:text-[var(--terminal-green)] [a&]:hover:border-[var(--terminal-green-dim)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({
  className,
  variant,
  asChild = false,
  ...props
}: React.ComponentProps<"span"> &
  VariantProps<typeof badgeVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot : "span"

  return (
    <Comp
      data-slot="badge"
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    />
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export { Badge, badgeVariants }
