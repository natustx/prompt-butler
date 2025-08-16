import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Edit, Trash2, AlertCircle } from 'lucide-react';
import { usePrompts } from '../hooks/usePrompts';
import { EmptyState } from '../components/EmptyState';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { DeleteConfirmModal } from '../components/DeleteConfirmModal';
import { TagPill } from '../components/TagPill';

export function PromptList() {
  const { prompts, loading, error, refetch, deletePrompt } = usePrompts();
  const [deleteModal, setDeleteModal] = useState<{ isOpen: boolean; promptName: string }>({
    isOpen: false,
    promptName: '',
  });

  const handleDeleteClick = (promptName: string) => {
    setDeleteModal({ isOpen: true, promptName });
  };

  const handleDeleteConfirm = async () => {
    try {
      await deletePrompt(deleteModal.promptName);
      setDeleteModal({ isOpen: false, promptName: '' });
    } catch (error) {
      console.error('Failed to delete prompt:', error);
      throw error;
    }
  };

  const handleDeleteCancel = () => {
    setDeleteModal({ isOpen: false, promptName: '' });
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-primary">Prompts</h1>
        <div className="bg-primary shadow rounded-lg p-8 flex items-center justify-center">
          <div className="flex items-center space-x-3">
            <LoadingSpinner size="md" />
            <span className="text-secondary">Loading prompts...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-primary">Prompts</h1>
        <div className="bg-primary shadow rounded-lg p-6">
          <div className="flex items-center space-x-3 text-red-600">
            <AlertCircle className="h-5 w-5" />
            <span>Error loading prompts: {error}</span>
          </div>
          <button
            onClick={refetch}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (prompts.length === 0) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-primary">Prompts</h1>
        <div className="bg-primary shadow rounded-lg">
          <EmptyState />
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-primary">Prompts</h1>
        
        <div className="bg-primary shadow rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-secondary">
              <thead className="bg-tertiary">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                    Tags
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-secondary uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-secondary">
                {prompts.map((prompt) => (
                  <tr key={prompt.name} className="hover:bg-tertiary transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-primary">
                        {prompt.name}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-secondary max-w-md">
                        {prompt.description || 'No description'}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1">
                        {prompt.tags && prompt.tags.length > 0 ? (
                          prompt.tags.map((tag) => (
                            <TagPill key={tag} tag={tag} className="inline-flex items-center gap-1 px-2 py-1 bg-tertiary text-secondary text-xs rounded-full" />
                          ))
                        ) : (
                          <span className="text-xs text-tertiary">No tags</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end space-x-2">
                        <Link
                          to={`/edit/${encodeURIComponent(prompt.name)}`}
                          className="p-2 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md transition-colors"
                          title="Edit prompt"
                        >
                          <Edit className="h-4 w-4" />
                        </Link>
                        <button
                          onClick={() => handleDeleteClick(prompt.name)}
                          className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md transition-colors"
                          title="Delete prompt"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <DeleteConfirmModal
        isOpen={deleteModal.isOpen}
        onClose={handleDeleteCancel}
        onConfirm={handleDeleteConfirm}
        itemName={deleteModal.promptName}
        itemType="prompt"
      />
    </>
  );
}