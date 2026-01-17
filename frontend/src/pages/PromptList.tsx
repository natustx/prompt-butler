import { Link } from 'react-router-dom';
import { Edit, Trash2, AlertCircle, Database } from 'lucide-react';
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
        <div className="flex items-center gap-3">
          <Database className="h-5 w-5 text-primary" />
          <h1 className="text-lg font-semibold text-primary tracking-wider uppercase">
            Prompt Database
          </h1>
        </div>
        <div className="terminal-panel p-8 flex items-center justify-center">
          <div className="flex items-center gap-3">
            <LoadingSpinner size="md" />
            <span className="text-muted-foreground tracking-wider">
              LOADING_RECORDS<span className="block-cursor"></span>
            </span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <Database className="h-5 w-5 text-primary" />
          <h1 className="text-lg font-semibold text-primary tracking-wider uppercase">
            Prompt Database
          </h1>
        </div>
        <div className="terminal-panel p-6">
          <div className="flex items-center gap-3 text-destructive">
            <AlertCircle className="h-5 w-5" />
            <span className="tracking-wider">ERROR: {error}</span>
          </div>
          <Button onClick={refetch} className="mt-4">
            [RETRY]
          </Button>
        </div>
      </div>
    );
  }

  if (prompts.length === 0) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <Database className="h-5 w-5 text-primary" />
          <h1 className="text-lg font-semibold text-primary tracking-wider uppercase">
            Prompt Database
          </h1>
        </div>
        <div className="terminal-panel">
          <EmptyState />
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Database className="h-5 w-5 text-primary" />
            <h1 className="text-lg font-semibold text-primary tracking-wider uppercase">
              Prompt Database
            </h1>
            <span className="text-muted-foreground text-sm">
              [{prompts.length} RECORDS]
            </span>
          </div>
        </div>

        {/* Terminal Table */}
        <div className="terminal-panel overflow-hidden">
          {/* Table Header Decoration */}
          <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-surface-alt">
            <div className="flex items-center gap-2 text-[10px] text-muted-foreground tracking-widest">
              <span className="text-primary">■</span>
              <span>TABLE:PROMPTS</span>
            </div>
            <div className="flex items-center gap-2 text-[10px] text-muted-foreground tracking-widest">
              <span>SORT:NAME</span>
              <span className="text-primary">▼</span>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full terminal-table">
              <thead>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-primary uppercase tracking-widest border-b border-primary">
                    Name
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-primary uppercase tracking-widest border-b border-primary">
                    Description
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-primary uppercase tracking-widest border-b border-primary">
                    Tags
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-primary uppercase tracking-widest border-b border-primary">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {prompts.map((prompt, index) => (
                  <tr
                    key={prompt.name}
                    className="group hover:bg-surface-alt transition-colors border-b border-border last:border-b-0"
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className="text-primary text-xs opacity-50">
                          {String(index + 1).padStart(2, '0')}
                        </span>
                        <span className="text-sm font-medium text-foreground group-hover:text-primary transition-colors">
                          {prompt.name}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-sm text-muted-foreground max-w-md truncate">
                        {prompt.description || '—'}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {prompt.tags && prompt.tags.length > 0 ? (
                          prompt.tags.map((tag) => (
                            <TagPill key={tag} tag={tag} />
                          ))
                        ) : (
                          <span className="text-xs text-muted-foreground">—</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          asChild
                          className="h-8 w-8 text-muted-foreground hover:text-primary hover:border-primary"
                        >
                          <Link
                            to={`/edit/${encodeURIComponent(prompt.name)}`}
                            title="Edit prompt"
                          >
                            <Edit className="h-3.5 w-3.5" />
                          </Link>
                        </Button>
                        <DeletePromptDialog
                          promptName={prompt.name}
                          onDelete={deletePrompt}
                        >
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-muted-foreground hover:text-destructive hover:border-destructive"
                            title="Delete prompt"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </DeletePromptDialog>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Table Footer */}
          <div className="flex items-center justify-between px-4 py-2 border-t border-border bg-surface-alt">
            <div className="text-[10px] text-muted-foreground tracking-widest">
              <span className="text-accent">RECORDS:</span> {prompts.length}
            </div>
            <div className="text-[10px] text-muted-foreground tracking-widest">
              <span className="text-primary">●</span> END_OF_TABLE
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
