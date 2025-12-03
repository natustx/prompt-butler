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
      variant="secondary" 
      className={cn(
        "inline-flex items-center gap-1 bg-surface-alt text-muted",
        className
      )}
    >
      <span className="truncate">{tag}</span>
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          className="flex-shrink-0 p-0.5 hover:bg-muted-foreground/20 rounded-full transition-colors ml-1"
          aria-label={`Remove tag: ${tag}`}
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </Badge>
  );
}