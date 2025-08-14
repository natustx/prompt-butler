import { X } from 'lucide-react';

interface TagPillProps {
  tag: string;
  onRemove?: () => void;
  className?: string;
}

export function TagPill({ tag, onRemove, className = '' }: TagPillProps) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 text-sm rounded-full ${className}`}
    >
      <span className="truncate">{tag}</span>
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          className="flex-shrink-0 p-0.5 hover:bg-blue-200 dark:hover:bg-blue-800/50 rounded-full transition-colors"
          aria-label={`Remove tag: ${tag}`}
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </span>
  );
}