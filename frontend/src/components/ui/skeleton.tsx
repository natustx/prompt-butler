import { cn } from "@/lib/utils"

function Skeleton({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="skeleton"
      className={cn("bg-[var(--terminal-gray)] animate-pulse border border-[var(--terminal-border)]", className)}
      {...props}
    />
  )
}

export { Skeleton }
