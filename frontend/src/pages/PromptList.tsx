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
        <h1 className="text-2xl font-bold text-[var(--terminal-green)] crt-glow tracking-wider">&gt; PROMPTS</h1>
        <div className="bg-[var(--terminal-dark)] border border-[var(--terminal-border)] p-8 flex items-center justify-center">
          <div className="flex items-center space-x-3">
            <LoadingSpinner size="md" />
            <span className="text-[var(--terminal-text-dim)]">Loading prompts...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-[var(--terminal-green)] crt-glow tracking-wider">&gt; PROMPTS</h1>
        <div className="bg-[var(--terminal-dark)] border border-[var(--terminal-red)]/50 p-6">
          <div className="flex items-center space-x-3 text-[var(--terminal-red)]">
            <AlertCircle className="h-5 w-5" />
            <span>ERROR: {error}</span>
          </div>
          <Button onClick={refetch} className="mt-4">
            RETRY
          </Button>
        </div>
      </div>
    );
  }

  if (prompts.length === 0) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-[var(--terminal-green)] crt-glow tracking-wider">&gt; PROMPTS</h1>
        <div className="bg-[var(--terminal-dark)] border border-[var(--terminal-border)]">
          <EmptyState />
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-[var(--terminal-green)] crt-glow tracking-wider">&gt; PROMPTS</h1>

        <div className="bg-[var(--terminal-dark)] border border-[var(--terminal-border)] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-[var(--terminal-gray)] border-b border-[var(--terminal-border)]">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-[var(--terminal-green)] uppercase tracking-wider">
                    GROUP
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-[var(--terminal-green)] uppercase tracking-wider">
                    NAME
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-[var(--terminal-green)] uppercase tracking-wider">
                    DESCRIPTION
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-[var(--terminal-green)] uppercase tracking-wider">
                    TAGS
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-[var(--terminal-green)] uppercase tracking-wider">
                    ACTIONS
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--terminal-border)]">
                {prompts.map((prompt) => (
                  <tr key={`${prompt.group}/${prompt.name}`} className="hover:bg-[var(--terminal-gray)] transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-[var(--terminal-text-dim)]">{prompt.group}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-[var(--terminal-text)]">{prompt.name}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-[var(--terminal-text-dim)] max-w-md">{prompt.description || '—'}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1">
                        {prompt.tags && prompt.tags.length > 0 ? (
                          prompt.tags.map((tag) => <TagPill key={tag} tag={tag} />)
                        ) : (
                          <span className="text-xs text-[var(--terminal-text-dim)]">—</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end space-x-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          asChild
                          className="text-[var(--terminal-amber)] hover:text-[var(--terminal-amber)] hover:bg-[var(--terminal-amber)]/10"
                        >
                          <Link
                            to={`/edit/${encodeURIComponent(prompt.group)}/${encodeURIComponent(prompt.name)}`}
                            title="Edit prompt"
                          >
                            <Edit className="h-4 w-4" />
                          </Link>
                        </Button>
                        <DeletePromptDialog promptGroup={prompt.group} promptName={prompt.name} onDelete={deletePrompt}>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-[var(--terminal-red)] hover:text-[var(--terminal-red)] hover:bg-[var(--terminal-red)]/10"
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
