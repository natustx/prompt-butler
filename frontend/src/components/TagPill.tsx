import { X } from 'lucide-react';

interface TagPillProps {
  tag: string;
  onRemove?: () => void;
  className?: string;
}

export function TagPill({ tag, onRemove, className = '' }: TagPillProps) {
  return (
    <span className={className}>
      <span className="truncate">{tag}</span>
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          className="flex-shrink-0 p-0.5 hover:bg-tertiary rounded-full transition-colors"
          aria-label={`Remove tag: ${tag}`}
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </span>
  );
}