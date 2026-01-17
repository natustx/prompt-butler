import { cn } from '@/lib/utils';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function LoadingSpinner({ size = 'md', className = '' }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4 border',
    md: 'h-6 w-6 border-2',
    lg: 'h-8 w-8 border-2',
  };

  return (
    <div
      className={cn(
        'animate-spin border-muted-foreground/30 border-t-primary',
        sizeClasses[size],
        className
      )}
      style={{
        boxShadow: '0 0 10px rgba(0, 255, 0, 0.2)',
      }}
    >
      <span className="sr-only">Loading...</span>
    </div>
  );
}
