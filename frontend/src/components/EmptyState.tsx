import { Terminal, Plus } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionText?: string;
  actionLink?: string;
}

export function EmptyState({
  title = 'NO_RECORDS_FOUND',
  description = 'Initialize database by creating your first prompt template.',
  actionText = 'CREATE_NEW',
  actionLink = '/new'
}: EmptyStateProps) {
  return (
    <div className="text-center py-12 px-6">
      {/* Terminal Icon Box */}
      <div className="mx-auto w-20 h-20 border border-border flex items-center justify-center mb-6 relative">
        <Terminal className="h-8 w-8 text-primary" />
        <div className="absolute -top-px -left-px w-2 h-2 border-t border-l border-primary" />
        <div className="absolute -top-px -right-px w-2 h-2 border-t border-r border-primary" />
        <div className="absolute -bottom-px -left-px w-2 h-2 border-b border-l border-primary" />
        <div className="absolute -bottom-px -right-px w-2 h-2 border-b border-r border-primary" />
      </div>

      {/* ASCII Art Divider */}
      <div className="text-primary text-xs tracking-widest mb-4 opacity-50">
        ════════════════════
      </div>

      <h3 className="text-sm font-semibold text-primary tracking-widest uppercase mb-2">
        {title}
      </h3>

      <p className="text-muted-foreground text-sm mb-6 max-w-md mx-auto tracking-wider">
        {description}
      </p>

      {/* Terminal Prompt Style */}
      <div className="flex items-center justify-center gap-2 text-muted-foreground text-xs mb-6">
        <span className="text-primary">$</span>
        <span className="tracking-wider">pb create --interactive</span>
        <span className="block-cursor"></span>
      </div>

      <Button asChild>
        <Link to={actionLink}>
          <Plus className="h-3 w-3" />
          <span>{actionText}</span>
        </Link>
      </Button>
    </div>
  );
}
