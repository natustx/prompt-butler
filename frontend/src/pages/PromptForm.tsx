import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Save, AlertCircle } from 'lucide-react';
import { usePrompt } from '../hooks/usePrompt';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { TagInput } from '../components/TagInput';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
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
        <h1 className="text-2xl font-bold text-primary">
          {isEditing ? 'Edit Prompt' : 'New Prompt'}
        </h1>
        <div className="bg-primary shadow rounded-lg overflow-hidden">
          <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-secondary">
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
          <div className="px-6 py-4 bg-tertiary border-t border-secondary flex justify-end space-x-3">
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
        <h1 className="text-2xl font-bold text-primary">
          {isEditing ? 'Edit Prompt' : 'New Prompt'}
        </h1>
        <div className="bg-primary shadow rounded-lg p-6">
          <Alert variant="destructive" className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Error loading prompt: {error}
            </AlertDescription>
          </Alert>
          <button
            onClick={handleCancel}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-primary">
          {isEditing ? `Edit "${decodedName}"` : 'New Prompt'}
        </h1>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="bg-primary shadow rounded-lg overflow-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-secondary">
          {/* Left Side - Basic Info */}
          <div className="p-6 space-y-6">
            <div>
              <Label htmlFor="name" className="block text-sm font-medium text-primary mb-2">
                Name *
              </Label>
              <Input
                type="text"
                id="name"
                {...register('name')}
                disabled={isEditing || isSubmitting}
                className={`w-full bg-primary text-primary ${
                  errors.name ? 'border-red-300' : 'border-secondary'
                } disabled:bg-gray-100 disabled:cursor-not-allowed`}
                placeholder="Enter prompt name"
              />
              {errors.name && (
                <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
              )}
              {isEditing && (
                <p className="mt-1 text-sm text-tertiary">Name cannot be changed when editing</p>
              )}
            </div>

            <div>
              <Label htmlFor="description" className="block text-sm font-medium text-primary mb-2">
                Description
              </Label>
              <Textarea
                id="description"
                {...register('description')}
                disabled={isSubmitting}
                rows={4}
                className="w-full bg-primary text-primary border-secondary resize-vertical"
                placeholder="Describe what this prompt does..."
              />
            </div>

            <div>
              <Label className="block text-sm font-medium text-primary mb-2">
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
                    placeholder="Add tags and press Enter..."
                    className="w-full px-3 py-2 border border-secondary rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-primary text-primary"
                    tagClassName="inline-flex items-center gap-1 px-2 py-1 bg-secondary text-secondary text-sm rounded-full"
                    disabled={isSubmitting}
                  />
                )}
              />
            </div>

            {(saveError || submitError) && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  {saveError || submitError}
                </AlertDescription>
              </Alert>
            )}
          </div>

          {/* Right Side - Prompt Content */}
          <div className="p-6 space-y-6">
            <div>
              <Label htmlFor="system_prompt" className="block text-sm font-medium text-primary mb-2">
                System Prompt *
              </Label>
              <Textarea
                id="system_prompt"
                {...register('system_prompt')}
                disabled={isSubmitting}
                rows={8}
                className={`w-full bg-primary text-primary font-mono text-sm resize-vertical ${
                  errors.system_prompt ? 'border-red-300' : 'border-secondary'
                }`}
                placeholder="You are a helpful assistant..."
              />
              {errors.system_prompt && (
                <p className="mt-1 text-sm text-red-600">{errors.system_prompt.message}</p>
              )}
            </div>

            <div>
              <Label htmlFor="user_prompt" className="block text-sm font-medium text-primary mb-2">
                User Prompt
              </Label>
              <Textarea
                id="user_prompt"
                {...register('user_prompt')}
                disabled={isSubmitting}
                rows={6}
                className="w-full bg-primary text-primary border-secondary font-mono text-sm resize-vertical"
                placeholder="Enter user prompt template..."
              />
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="px-6 py-4 bg-tertiary border-t border-secondary flex items-center justify-end space-x-3">
          <button
            type="button"
            onClick={handleCancel}
            disabled={isSubmitting}
            className="px-4 py-2 text-secondary hover:text-primary border border-secondary hover:bg-primary rounded-md transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting || !isDirty}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors disabled:opacity-50 flex items-center space-x-2"
          >
            {isSubmitting ? (
              <>
                <LoadingSpinner size="sm" />
                <span>Saving...</span>
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                <span>{isEditing ? 'Update' : 'Create'}</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}