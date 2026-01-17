import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Save, AlertCircle, FileEdit, FilePlus } from 'lucide-react';
import { usePrompt } from '../hooks/usePrompt';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { TagInput } from '../components/TagInput';
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
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const isEditing = Boolean(name);
  const decodedName = name ? decodeURIComponent(name) : undefined;

  const { prompt, loading, error, saveError, createPrompt, updatePrompt } = usePrompt(decodedName);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const form = useForm<PromptFormInput>({
    resolver: zodResolver(promptFormSchema),
    defaultValues: {
      name: '',
      description: '',
      system_prompt: '',
      user_prompt: '',
      tags: [],
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
        await updatePrompt(decodedName, updateData);
      } else {
        const createData: PromptCreate = {
          name: data.name,
          description: data.description.trim() || undefined,
          system_prompt: data.system_prompt,
          user_prompt: data.user_prompt.trim() || undefined,
          tags: data.tags.length > 0 ? data.tags : undefined,
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
        <div className="flex items-center gap-3">
          <FileEdit className="h-5 w-5 text-primary" />
          <h1 className="text-lg font-semibold text-primary tracking-wider uppercase">
            {isEditing ? 'Edit Prompt' : 'New Prompt'}
          </h1>
        </div>
        <div className="terminal-panel overflow-hidden">
          <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-border">
            <div className="p-6 space-y-6">
              <div className="space-y-2">
                <Skeleton className="h-4 w-16 bg-surface-alt" />
                <Skeleton className="h-10 w-full bg-surface-alt" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-4 w-20 bg-surface-alt" />
                <Skeleton className="h-24 w-full bg-surface-alt" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-4 w-12 bg-surface-alt" />
                <Skeleton className="h-10 w-full bg-surface-alt" />
              </div>
            </div>
            <div className="p-6 space-y-6">
              <div className="space-y-2">
                <Skeleton className="h-4 w-24 bg-surface-alt" />
                <Skeleton className="h-32 w-full bg-surface-alt" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-4 w-20 bg-surface-alt" />
                <Skeleton className="h-24 w-full bg-surface-alt" />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <FileEdit className="h-5 w-5 text-primary" />
          <h1 className="text-lg font-semibold text-primary tracking-wider uppercase">
            {isEditing ? 'Edit Prompt' : 'New Prompt'}
          </h1>
        </div>
        <div className="terminal-panel p-6">
          <Alert variant="destructive" className="mb-4 border-destructive bg-transparent">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="tracking-wider">
              ERROR: {error}
            </AlertDescription>
          </Alert>
          <Button variant="outline" onClick={handleCancel}>
            [GO_BACK]
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {isEditing ? (
            <FileEdit className="h-5 w-5 text-primary" />
          ) : (
            <FilePlus className="h-5 w-5 text-primary" />
          )}
          <h1 className="text-lg font-semibold text-primary tracking-wider uppercase">
            {isEditing ? `Edit: ${decodedName}` : 'New Prompt'}
          </h1>
        </div>
        <div className="text-[10px] text-muted-foreground tracking-widest">
          <span className="text-accent">MODE:</span> {isEditing ? 'EDIT' : 'CREATE'}
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="terminal-panel overflow-hidden">
        {/* Form Header */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-surface-alt">
          <div className="flex items-center gap-2 text-[10px] text-muted-foreground tracking-widest">
            <span className="text-primary">■</span>
            <span>FORM:PROMPT_EDITOR</span>
          </div>
          <div className="flex items-center gap-2 text-[10px] text-muted-foreground tracking-widest">
            <span className={isDirty ? 'text-accent' : 'text-muted-foreground'}>
              {isDirty ? 'MODIFIED' : 'UNCHANGED'}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-border">
          {/* Left Side - Metadata */}
          <div className="p-6 space-y-6">
            <div className="text-[10px] text-muted-foreground tracking-widest mb-4 pb-2 border-b border-border">
              <span className="text-accent">SECTION:</span> METADATA
            </div>

            {/* Name Field */}
            <div>
              <Label htmlFor="name" className="block text-xs font-medium text-primary uppercase tracking-widest mb-2">
                Name <span className="text-destructive">*</span>
              </Label>
              <Input
                type="text"
                id="name"
                {...register('name')}
                disabled={isEditing || isSubmitting}
                className={`w-full bg-page text-foreground terminal-input ${
                  errors.name ? 'border-destructive' : ''
                } disabled:opacity-50 disabled:cursor-not-allowed`}
                placeholder="prompt_name"
              />
              {errors.name && (
                <p className="mt-1 text-xs text-destructive tracking-wider">{errors.name.message}</p>
              )}
              {isEditing && (
                <p className="mt-1 text-[10px] text-muted-foreground tracking-wider">
                  NAME_FIELD_LOCKED_IN_EDIT_MODE
                </p>
              )}
            </div>

            {/* Description Field */}
            <div>
              <Label htmlFor="description" className="block text-xs font-medium text-primary uppercase tracking-widest mb-2">
                Description
              </Label>
              <Textarea
                id="description"
                {...register('description')}
                disabled={isSubmitting}
                rows={4}
                className="w-full bg-page text-foreground terminal-textarea resize-vertical"
                placeholder="Describe the prompt purpose..."
              />
            </div>

            {/* Tags Field */}
            <div>
              <Label className="block text-xs font-medium text-primary uppercase tracking-widest mb-2">
                Tags
              </Label>
              <Controller
                name="tags"
                control={control}
                render={({ field }) => (
                  <TagInput
                    {...field}
                    tags={field.value}
                    onChange={field.onChange}
                    placeholder="Add tags..."
                    className="w-full px-3 py-2 bg-page text-foreground terminal-input"
                    tagClassName="tag-pill"
                    disabled={isSubmitting}
                  />
                )}
              />
            </div>

            {/* Error Alert */}
            {(saveError || submitError) && (
              <Alert variant="destructive" className="border-destructive bg-transparent">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription className="tracking-wider">
                  {saveError || submitError}
                </AlertDescription>
              </Alert>
            )}
          </div>

          {/* Right Side - Prompt Content */}
          <div className="p-6 space-y-6">
            <div className="text-[10px] text-muted-foreground tracking-widest mb-4 pb-2 border-b border-border">
              <span className="text-accent">SECTION:</span> PROMPT_CONTENT
            </div>

            {/* System Prompt */}
            <div>
              <Label htmlFor="system_prompt" className="block text-xs font-medium text-primary uppercase tracking-widest mb-2">
                System Prompt <span className="text-destructive">*</span>
              </Label>
              <Textarea
                id="system_prompt"
                {...register('system_prompt')}
                disabled={isSubmitting}
                rows={8}
                className={`w-full bg-page text-foreground terminal-textarea resize-vertical text-sm ${
                  errors.system_prompt ? 'border-destructive' : ''
                }`}
                placeholder="You are a helpful assistant..."
              />
              {errors.system_prompt && (
                <p className="mt-1 text-xs text-destructive tracking-wider">{errors.system_prompt.message}</p>
              )}
            </div>

            {/* User Prompt */}
            <div>
              <Label htmlFor="user_prompt" className="block text-xs font-medium text-primary uppercase tracking-widest mb-2">
                User Prompt
              </Label>
              <Textarea
                id="user_prompt"
                {...register('user_prompt')}
                disabled={isSubmitting}
                rows={6}
                className="w-full bg-page text-foreground terminal-textarea resize-vertical text-sm"
                placeholder="Enter user prompt template..."
              />
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="px-4 py-3 bg-surface-alt border-t border-border flex items-center justify-between">
          <div className="text-[10px] text-muted-foreground tracking-widest">
            <span className="text-primary">●</span> READY_TO_SAVE
          </div>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={isSubmitting}
            >
              [CANCEL]
            </Button>
            <Button type="submit" disabled={isSubmitting || !isDirty}>
              {isSubmitting ? (
                <>
                  <LoadingSpinner size="sm" />
                  <span>SAVING...</span>
                </>
              ) : (
                <>
                  <Save className="h-3 w-3" />
                  <span>{isEditing ? 'UPDATE' : 'CREATE'}</span>
                </>
              )}
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
