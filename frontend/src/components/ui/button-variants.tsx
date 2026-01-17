import { cva } from "class-variance-authority"

export const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none uppercase tracking-wider",
  {
    variants: {
      variant: {
        default:
          "bg-transparent border border-primary text-primary hover:bg-primary hover:text-primary-foreground hover:shadow-[0_0_10px_rgba(0,255,0,0.3),0_0_20px_rgba(0,255,0,0.2)] focus-visible:ring-2 focus-visible:ring-primary/50",
        destructive:
          "bg-transparent border border-destructive text-destructive hover:bg-destructive hover:text-black hover:shadow-[0_0_10px_rgba(255,107,107,0.3),0_0_20px_rgba(255,107,107,0.2)] focus-visible:ring-2 focus-visible:ring-destructive/50",
        outline:
          "border border-border bg-transparent text-muted-foreground hover:border-primary hover:text-primary focus-visible:ring-2 focus-visible:ring-primary/50",
        secondary:
          "bg-transparent border border-accent text-accent hover:bg-accent hover:text-accent-foreground hover:shadow-[0_0_10px_rgba(255,176,0,0.3),0_0_20px_rgba(255,176,0,0.2)] focus-visible:ring-2 focus-visible:ring-accent/50",
        ghost:
          "border border-transparent text-muted-foreground hover:border-border hover:text-foreground",
        link: "text-primary underline-offset-4 hover:underline border-none",
      },
      size: {
        default: "h-9 px-4 py-2 has-[>svg]:px-3",
        sm: "h-8 gap-1.5 px-3 has-[>svg]:px-2.5 text-xs",
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
