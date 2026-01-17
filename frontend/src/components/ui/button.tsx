import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none border border-[var(--terminal-green-dim)] focus-visible:border-[var(--terminal-green)] focus-visible:shadow-[0_0_10px_var(--terminal-green-glow)] aria-invalid:border-[var(--terminal-red)]",
  {
    variants: {
      variant: {
        default:
          "bg-[var(--terminal-gray)] text-[var(--terminal-green)] hover:bg-[var(--terminal-green)]/10 hover:text-[var(--terminal-green)] hover:shadow-[0_0_10px_var(--terminal-green-glow)]",
        destructive:
          "bg-[var(--terminal-gray)] text-[var(--terminal-red)] border-[var(--terminal-red)]/50 hover:border-[var(--terminal-red)] hover:shadow-[0_0_10px_rgba(255,51,51,0.2)]",
        outline:
          "bg-transparent text-[var(--terminal-text)] hover:bg-[var(--terminal-green)]/10 hover:text-[var(--terminal-green)]",
        secondary:
          "bg-[var(--terminal-dark)] text-[var(--terminal-amber)] border-[var(--terminal-amber-dim)] hover:bg-[var(--terminal-amber)]/10 hover:shadow-[0_0_10px_var(--terminal-amber-glow)]",
        ghost:
          "border-transparent hover:bg-[var(--terminal-green)]/10 hover:text-[var(--terminal-green)] hover:border-[var(--terminal-green-dim)]",
        link: "text-[var(--terminal-green)] underline-offset-4 hover:underline border-transparent",
      },
      size: {
        default: "h-9 px-4 py-2 has-[>svg]:px-3",
        sm: "h-8 gap-1.5 px-3 has-[>svg]:px-2.5",
        lg: "h-10 px-6 has-[>svg]:px-4",
        icon: "size-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot : "button"

  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export { Button, buttonVariants }
