import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Save, AlertCircle } from 'lucide-react';
import { usePrompt } from '../hooks/usePrompt';
import { useTagsAndGroups } from '../hooks/useTagsAndGroups';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { TagAutocomplete } from '../components/TagAutocomplete';
import { GroupSelect } from '../components/GroupSelect';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { handleApiError } from '../utils/errorHandler';
import { promptFormSchema, type PromptFormInput } from '../schemas/prompt';
import type { PromptCreate, PromptUpdate } from '../types/prompt';

export function PromptForm() {
  const { group, name } = useParams<{ group?: string; name?: string }>();
  const navigate = useNavigate();
  const isEditing = Boolean(name);
  const decodedGroup = group ? decodeURIComponent(group) : '';
  const decodedName = name ? decodeURIComponent(name) : undefined;

  const { prompt, loading, error, saveError, createPrompt, updatePrompt } = usePrompt(decodedGroup, decodedName);
  const { tags: availableTags, groups: availableGroups } = useTagsAndGroups();
  const [submitError, setSubmitError] = useState<string | null>(null);

  const form = useForm<PromptFormInput>({
    resolver: zodResolver(promptFormSchema),
    defaultValues: {
      name: '',
      description: '',
      system_prompt: '',
      user_prompt: '',
      tags: [],
      group: '',
    },
  });

  const { control, register, handleSubmit, formState, reset } = form;
  const { errors, isDirty, isSubmitting } = formState;

  useEffect(() => {
    if (isEditing && prompt) {
      reset({
        name: prompt.name,
        description: prompt.description || '',
        system_prompt: prompt.system_prompt,
        user_prompt: prompt.user_prompt || '',
        tags: prompt.tags || [],
        group: prompt.group || '',
      });
    }
  }, [prompt, isEditing, reset]);

  const onSubmit = async (data: PromptFormInput) => {
    try {
      setSubmitError(null);

      if (isEditing && decodedName) {
        const updateData: PromptUpdate = {
          description: data.description.trim() || undefined,
          system_prompt: data.system_prompt,
          user_prompt: data.user_prompt.trim() || undefined,
          tags: data.tags.length > 0 ? data.tags : undefined,
        };
        await updatePrompt(decodedGroup || undefined, decodedName, updateData);
      } else {
        const createData: PromptCreate = {
          name: data.name,
          description: data.description.trim() || undefined,
          system_prompt: data.system_prompt,
          user_prompt: data.user_prompt.trim() || undefined,
          tags: data.tags.length > 0 ? data.tags : undefined,
          group: data.group.trim() || undefined,
        };
        await createPrompt(createData);
      }

      navigate('/');
    } catch (error) {
      handleApiError(error, 'save prompt', setSubmitError);
    }
  };

  const handleCancel = () => {
    navigate('/');
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-[var(--terminal-green)] crt-glow tracking-wider">
          &gt; {isEditing ? 'EDIT_PROMPT' : 'NEW_PROMPT'}
        </h1>
        <div className="bg-[var(--terminal-dark)] border border-[var(--terminal-border)] overflow-hidden">
          <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-[var(--terminal-border)]">
            {/* Left Side Skeleton */}
            <div className="p-6 space-y-6">
              <div className="space-y-2">
                <Skeleton className="h-4 w-16" />
                <Skeleton className="h-10 w-full" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-24 w-full" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-4 w-12" />
                <Skeleton className="h-10 w-full" />
              </div>
            </div>
            {/* Right Side Skeleton */}
            <div className="p-6 space-y-6">
              <div className="space-y-2">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-32 w-full" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-24 w-full" />
              </div>
            </div>
          </div>
          <div className="px-6 py-4 bg-[var(--terminal-gray)] border-t border-[var(--terminal-border)] flex justify-end space-x-3">
            <Skeleton className="h-10 w-16" />
            <Skeleton className="h-10 w-20" />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-[var(--terminal-green)] crt-glow tracking-wider">
          &gt; {isEditing ? 'EDIT_PROMPT' : 'NEW_PROMPT'}
        </h1>
        <div className="bg-[var(--terminal-dark)] border border-[var(--terminal-red)]/50 p-6">
          <Alert variant="destructive" className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>ERROR: {error}</AlertDescription>
          </Alert>
          <Button variant="secondary" onClick={handleCancel}>
            GO_BACK
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[var(--terminal-green)] crt-glow tracking-wider">
          &gt; {isEditing ? `EDIT: ${decodedGroup || 'ungrouped'}/${decodedName}` : 'NEW_PROMPT'}
        </h1>
      </div>

      <form
        onSubmit={handleSubmit(onSubmit)}
        className="bg-[var(--terminal-dark)] border border-[var(--terminal-border)] overflow-hidden"
      >
        <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-[var(--terminal-border)]">
          {/* Left Side - Basic Info */}
          <div className="p-6 space-y-6">
            <div>
              <Label htmlFor="group" className="block text-sm font-medium mb-2">
                GROUP
              </Label>
              <Controller
                name="group"
                control={control}
                render={({ field }) => (
                  <GroupSelect
                    value={field.value}
                    onChange={field.onChange}
                    availableGroups={availableGroups}
                    placeholder="select_or_enter_group..."
                    className={`w-full ${errors.group ? 'border-[var(--terminal-red)]' : ''}`}
                    disabled={isEditing || isSubmitting}
                  />
                )}
              />
              {errors.group && <p className="mt-1 text-sm text-[var(--terminal-red)]">{errors.group.message}</p>}
              {isEditing && (
                <p className="mt-1 text-sm text-[var(--terminal-text-dim)]">// group is immutable during edit</p>
              )}
            </div>

            <div>
              <Label htmlFor="name" className="block text-sm font-medium mb-2">
                NAME *
              </Label>
              <Input
                type="text"
                id="name"
                {...register('name')}
                disabled={isEditing || isSubmitting}
                className={`w-full ${errors.name ? 'border-[var(--terminal-red)]' : ''} disabled:opacity-50 disabled:cursor-not-allowed`}
                placeholder="enter_prompt_name"
              />
              {errors.name && <p className="mt-1 text-sm text-[var(--terminal-red)]">{errors.name.message}</p>}
              {isEditing && (
                <p className="mt-1 text-sm text-[var(--terminal-text-dim)]">// name is immutable during edit</p>
              )}
            </div>

            <div>
              <Label htmlFor="description" className="block text-sm font-medium mb-2">
                DESCRIPTION
              </Label>
              <Textarea
                id="description"
                {...register('description')}
                disabled={isSubmitting}
                rows={4}
                className="w-full resize-vertical"
                placeholder="describe_this_prompt..."
              />
            </div>

            <div>
              <Label className="block text-sm font-medium mb-2">TAGS</Label>
              <Controller
                name="tags"
                control={control}
                render={({ field }) => (
                  <TagAutocomplete
                    tags={field.value}
                    onChange={field.onChange}
                    availableTags={availableTags}
                    placeholder="add_tags_press_enter..."
                    className="w-full px-3 py-2 border border-[var(--terminal-border)] bg-[var(--terminal-dark)] text-[var(--terminal-text)] focus:border-[var(--terminal-green)] focus:shadow-[0_0_10px_var(--terminal-green-glow)] transition-all"
                    tagClassName="inline-flex items-center gap-1 px-2 py-1 bg-[var(--terminal-green)]/10 text-[var(--terminal-green)] text-sm border border-[var(--terminal-green-dim)]"
                    disabled={isSubmitting}
                  />
                )}
              />
            </div>

            {(saveError || submitError) && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>ERROR: {saveError || submitError}</AlertDescription>
              </Alert>
            )}
          </div>

          {/* Right Side - Prompt Content */}
          <div className="p-6 space-y-6">
            <div>
              <Label htmlFor="system_prompt" className="block text-sm font-medium mb-2">
                SYSTEM_PROMPT *
              </Label>
              <Textarea
                id="system_prompt"
                {...register('system_prompt')}
                disabled={isSubmitting}
                rows={8}
                className={`w-full font-mono text-sm resize-vertical ${errors.system_prompt ? 'border-[var(--terminal-red)]' : ''}`}
                placeholder="you_are_a_helpful_assistant..."
              />
              {errors.system_prompt && (
                <p className="mt-1 text-sm text-[var(--terminal-red)]">{errors.system_prompt.message}</p>
              )}
            </div>

            <div>
              <Label htmlFor="user_prompt" className="block text-sm font-medium mb-2">
                USER_PROMPT
              </Label>
              <Textarea
                id="user_prompt"
                {...register('user_prompt')}
                disabled={isSubmitting}
                rows={6}
                className="w-full font-mono text-sm resize-vertical"
                placeholder="enter_user_prompt_template..."
              />
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="px-6 py-4 bg-[var(--terminal-gray)] border-t border-[var(--terminal-border)] flex items-center justify-end space-x-3">
          <Button type="button" variant="outline" onClick={handleCancel} disabled={isSubmitting}>
            CANCEL
          </Button>
          <Button type="submit" disabled={isSubmitting || !isDirty}>
            {isSubmitting ? (
              <>
                <LoadingSpinner size="sm" />
                <span>SAVING...</span>
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                <span>{isEditing ? 'UPDATE' : 'CREATE'}</span>
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
