import { FileText, Plus } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionText?: string;
  actionLink?: string;
}

export function EmptyState({
  title = 'NO_PROMPTS_FOUND',
  description = '// initialize your first prompt template',
  actionText = 'CREATE_NEW',
  actionLink = '/new'
}: EmptyStateProps) {
  return (
    <div className="text-center py-12">
      <div className="mx-auto w-24 h-24 bg-[var(--terminal-gray)] border border-[var(--terminal-border)] flex items-center justify-center mb-6">
        <FileText className="h-12 w-12 text-[var(--terminal-green-dim)]" />
      </div>

      <h3 className="text-lg font-semibold text-[var(--terminal-green)] crt-glow mb-2 tracking-wider">
        {title}
      </h3>

      <p className="text-[var(--terminal-text-dim)] mb-8 max-w-md mx-auto">
        {description}
      </p>

      <Button asChild>
        <Link to={actionLink}>
          <Plus className="h-4 w-4 mr-2" />
          {actionText}
        </Link>
      </Button>
    </div>
  );
}