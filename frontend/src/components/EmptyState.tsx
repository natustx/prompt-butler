import { FileText, Plus } from 'lucide-react';
import { Link } from 'react-router-dom';

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
      
      <Link
        to={actionLink}
        className="inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-md font-medium transition-colors"
      >
        <Plus className="h-5 w-5" />
        <span>{actionText}</span>
      </Link>
    </div>
  );
}