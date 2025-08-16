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
  title = 'No prompts found',
  description = 'Get started by creating your first prompt template.',
  actionText = 'Create New Prompt',
  actionLink = '/new'
}: EmptyStateProps) {
  return (
    <div className="text-center py-12">
      <div className="mx-auto w-24 h-24 bg-tertiary rounded-full flex items-center justify-center mb-6">
        <FileText className="h-12 w-12 text-tertiary" />
      </div>
      
      <h3 className="text-lg font-semibold text-primary mb-2">
        {title}
      </h3>
      
      <p className="text-tertiary mb-8 max-w-md mx-auto">
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