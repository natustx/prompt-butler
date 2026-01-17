import { useState, useEffect, useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Edit, Trash2, AlertCircle, Database } from 'lucide-react';
import { usePrompts } from '../hooks/usePrompts';
import { EmptyState } from '../components/EmptyState';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { TagPill } from '../components/TagPill';
import { DeletePromptDialog } from '../components/DeletePromptDialog';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { groupApi } from '../services/api';
import type { GroupCount } from '../types/prompt';

export function PromptList() {
  const { prompts, loading, error, refetch, deletePrompt } = usePrompts();
  const [searchParams, setSearchParams] = useSearchParams();
  const [groups, setGroups] = useState<GroupCount[]>([]);
  const [deletingPrompts, setDeletingPrompts] = useState<Set<string>>(() => new Set());

  const selectedGroup = searchParams.get('group') ?? '';

  // Load groups for filter
  useEffect(() => {
    groupApi.listGroups().then(setGroups).catch(console.error);
  }, [prompts]);

  // Filter prompts by selected group
  const filteredPrompts = useMemo(() => {
    if (!selectedGroup) return prompts;
    if (selectedGroup === '(root)') return prompts.filter(p => !p.group);
    return prompts.filter(p => p.group === selectedGroup);
  }, [prompts, selectedGroup]);

  const handleGroupFilter = (group: string) => {
    if (group) {
      setSearchParams({ group });
    } else {
      setSearchParams({});
    }
  };

  const handleDeletePrompt = async (promptName: string) => {
    setDeletingPrompts((prev) => {
      const next = new Set(prev);
      next.add(promptName);
      return next;
    });

    try {
      await deletePrompt(promptName);
    } finally {
      setDeletingPrompts((prev) => {
        const next = new Set(prev);
        next.delete(promptName);
        return next;
      });
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <Database className="h-5 w-5 text-primary" />
          <h1 className="text-lg font-semibold text-primary tracking-wider uppercase">
            Prompt Database
          </h1>
        </div>
        <Card className="p-8 flex items-center justify-center">
          <div className="flex items-center gap-3">
            <LoadingSpinner size="md" />
            <span className="text-muted-foreground tracking-wider">
              LOADING_RECORDS<span className="block-cursor"></span>
            </span>
          </div>
        </Card>
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
        <Card className="p-6">
          <div className="flex items-center gap-3 text-destructive">
            <AlertCircle className="h-5 w-5" />
            <span className="tracking-wider">ERROR: {error}</span>
          </div>
          <Button onClick={refetch} className="mt-4">
            [RETRY]
          </Button>
        </Card>
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
        <Card>
          <EmptyState />
        </Card>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Database className="h-5 w-5 text-primary" />
            <h1 className="text-lg font-semibold text-primary tracking-wider uppercase">
              Prompt Database
            </h1>
            <span className="text-muted-foreground text-sm">
              [{filteredPrompts.length} RECORDS]
            </span>
          </div>
          <div className="flex items-center gap-2">
            <label htmlFor="group-filter" className="text-[10px] text-muted-foreground tracking-widest">
              FILTER:GROUP
            </label>
            <select
              id="group-filter"
              value={selectedGroup}
              onChange={(e) => handleGroupFilter(e.target.value)}
              className="terminal-input h-8 px-3 text-xs uppercase tracking-widest bg-page text-foreground border border-border focus-visible:border-primary"
            >
              <option value="">All groups</option>
              {groups.map((g) => (
                <option key={g.group || '(root)'} value={g.group || '(root)'}>
                  {g.group || '(root)'} ({g.count})
                </option>
              ))}
            </select>
          </div>
        </div>

        <Card className="overflow-hidden">
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
                    Group
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
                {filteredPrompts.map((prompt, index) => {
                  const isDeleting = deletingPrompts.has(prompt.name);
                  return (
                    <tr key={prompt.name} className="group hover:bg-surface-alt transition-colors border-b border-border last:border-b-0">
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
                        <div className="text-sm text-muted-foreground">
                          {prompt.group || '(root)'}
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
                            onDelete={handleDeletePrompt}
                          >
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-muted-foreground hover:text-destructive hover:border-destructive"
                              title="Delete prompt"
                              disabled={isDeleting}
                            >
                              {isDeleting ? <LoadingSpinner size="sm" /> : <Trash2 className="h-3.5 w-3.5" />}
                            </Button>
                          </DeletePromptDialog>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between px-4 py-2 border-t border-border bg-surface-alt">
            <div className="text-[10px] text-muted-foreground tracking-widest">
              <span className="text-accent">RECORDS:</span> {filteredPrompts.length}
            </div>
            <div className="text-[10px] text-muted-foreground tracking-widest">
              <span className="text-primary">●</span> END_OF_TABLE
            </div>
          </div>
        </Card>
      </div>
    </>
  );
}
