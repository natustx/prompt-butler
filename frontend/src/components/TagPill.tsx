import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TagPillProps {
  tag: string;
  onRemove?: () => void;
  className?: string;
}

export function TagPill({ tag, onRemove, className = '' }: TagPillProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5",
        "bg-transparent border border-accent text-accent",
        "text-xs font-medium lowercase tracking-wider",
        "transition-all hover:bg-accent/10",
        className
      )}
    >
      <span className="truncate">{tag}</span>
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          className="flex-shrink-0 p-0.5 hover:bg-accent/20 transition-colors ml-0.5"
          aria-label={`Remove tag: ${tag}`}
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </span>
  );
}
