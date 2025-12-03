import { Link } from 'react-router-dom';
import { Edit, Trash2, AlertCircle } from 'lucide-react';
import { usePrompts } from '../hooks/usePrompts';
import { EmptyState } from '../components/EmptyState';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { TagPill } from '../components/TagPill';
import { DeletePromptDialog } from '../components/DeletePromptDialog';
import { Button } from '@/components/ui/button';

export function PromptList() {
  const { prompts, loading, error, refetch, deletePrompt } = usePrompts();

  if (loading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-default">Prompts</h1>
        <div className="bg-surface shadow rounded-lg p-8 flex items-center justify-center">
          <div className="flex items-center space-x-3">
            <LoadingSpinner size="md" />
            <span className="text-muted">Loading prompts...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-default">Prompts</h1>
        <div className="bg-surface shadow rounded-lg p-6">
          <div className="flex items-center space-x-3 text-red-600">
            <AlertCircle className="h-5 w-5" />
            <span>Error loading prompts: {error}</span>
          </div>
          <Button onClick={refetch} className="mt-4">
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (prompts.length === 0) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-default">Prompts</h1>
        <div className="bg-surface shadow rounded-lg">
          <EmptyState />
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-default">Prompts</h1>
        
        <div className="bg-surface shadow rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-strong">
              <thead className="bg-surface-alt">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    Tags
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-muted uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-strong">
                {prompts.map((prompt) => (
                  <tr key={prompt.name} className="hover:bg-surface-alt transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-default">
                        {prompt.name}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-muted max-w-md">
                        {prompt.description || 'No description'}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1">
                        {prompt.tags && prompt.tags.length > 0 ? (
                          prompt.tags.map((tag) => (
                            <TagPill key={tag} tag={tag} />
                          ))
                        ) : (
                          <span className="text-xs text-subtle">No tags</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end space-x-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          asChild
                          className="text-blue-600 hover:text-blue-800 hover:bg-blue-50"
                        >
                          <Link
                            to={`/edit/${encodeURIComponent(prompt.name)}`}
                            title="Edit prompt"
                          >
                            <Edit className="h-4 w-4" />
                          </Link>
                        </Button>
                        <DeletePromptDialog
                          promptName={prompt.name}
                          onDelete={deletePrompt}
                        >
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-red-600 hover:text-red-800 hover:bg-red-50"
                            title="Delete prompt"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </DeletePromptDialog>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
}