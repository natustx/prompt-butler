import { X } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface TagPillProps {
  tag: string;
  onRemove?: () => void;
  className?: string;
}

export function TagPill({ tag, onRemove, className = '' }: TagPillProps) {
  return (
    <Badge
      variant="default"
      className={cn(
        "inline-flex items-center gap-1",
        className
      )}
    >
      <span className="truncate">{tag}</span>
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          className="flex-shrink-0 p-0.5 hover:bg-[var(--terminal-green)]/20 transition-colors ml-1"
          aria-label={`Remove tag: ${tag}`}
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </Badge>
  );
}