import { useState, useEffect, FormEvent } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Save, AlertCircle } from 'lucide-react';
import { usePrompt } from '../hooks/usePrompt';
import { LoadingSpinner } from '../components/LoadingSpinner';
import type { PromptCreate, PromptUpdate } from '../types/prompt';

interface FormData {
  name: string;
  description: string;
  system_prompt: string;
  user_prompt: string;
}

interface FormErrors {
  name?: string;
  system_prompt?: string;
}

export function PromptForm() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const isEditing = Boolean(name);
  const decodedName = name ? decodeURIComponent(name) : undefined;
  
  const { prompt, loading, error, saving, saveError, createPrompt, updatePrompt } = usePrompt(decodedName);
  
  const [formData, setFormData] = useState<FormData>({
    name: '',
    description: '',
    system_prompt: '',
    user_prompt: '',
  });
  
  const [errors, setErrors] = useState<FormErrors>({});
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    if (isEditing && prompt) {
      setFormData({
        name: prompt.name,
        description: prompt.description || '',
        system_prompt: prompt.system_prompt,
        user_prompt: prompt.user_prompt || '',
      });
      setHasChanges(false);
    }
  }, [prompt, isEditing]);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    } else if (!/^[a-zA-Z0-9_-]+$/.test(formData.name)) {
      newErrors.name = 'Name must contain only letters, numbers, underscores, and hyphens (no spaces)';
    }

    if (!formData.system_prompt.trim()) {
      newErrors.system_prompt = 'System prompt is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field: keyof FormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setHasChanges(true);
    
    if (errors[field as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      if (isEditing && decodedName) {
        const updateData: PromptUpdate = {
          description: formData.description || undefined,
          system_prompt: formData.system_prompt,
          user_prompt: formData.user_prompt || undefined,
        };
        await updatePrompt(decodedName, updateData);
      } else {
        const createData: PromptCreate = {
          name: formData.name,
          description: formData.description.trim() || undefined,
          system_prompt: formData.system_prompt,
          user_prompt: formData.user_prompt.trim() || undefined,
        };
        await createPrompt(createData);
      }
      
      navigate('/');
    } catch (error) {
      console.error('Failed to save prompt:', error);
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
        <div className="bg-primary shadow rounded-lg p-8 flex items-center justify-center">
          <div className="flex items-center space-x-3">
            <LoadingSpinner size="md" />
            <span className="text-secondary">Loading prompt...</span>
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
          <div className="flex items-center space-x-3 text-red-600">
            <AlertCircle className="h-5 w-5" />
            <span>Error loading prompt: {error}</span>
          </div>
          <button
            onClick={handleCancel}
            className="mt-4 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
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

      <form onSubmit={handleSubmit} className="bg-primary shadow rounded-lg overflow-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-secondary">
          {/* Left Side - Basic Info */}
          <div className="p-6 space-y-6">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-primary mb-2">
                Name *
              </label>
              <input
                type="text"
                id="name"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                disabled={isEditing || saving}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-primary text-primary ${
                  errors.name ? 'border-red-300' : 'border-secondary'
                } disabled:bg-gray-100 disabled:cursor-not-allowed`}
                placeholder="Enter prompt name"
              />
              {errors.name && (
                <p className="mt-1 text-sm text-red-600">{errors.name}</p>
              )}
              {isEditing && (
                <p className="mt-1 text-sm text-tertiary">Name cannot be changed when editing</p>
              )}
            </div>

            <div>
              <label htmlFor="description" className="block text-sm font-medium text-primary mb-2">
                Description
              </label>
              <textarea
                id="description"
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                disabled={saving}
                rows={4}
                className="w-full px-3 py-2 border border-secondary rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-primary text-primary resize-vertical"
                placeholder="Describe what this prompt does..."
              />
            </div>

            {saveError && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="h-5 w-5 text-red-600" />
                  <span className="text-red-600 text-sm">{saveError}</span>
                </div>
              </div>
            )}
          </div>

          {/* Right Side - Prompt Content */}
          <div className="p-6 space-y-6">
            <div>
              <label htmlFor="system_prompt" className="block text-sm font-medium text-primary mb-2">
                System Prompt *
              </label>
              <textarea
                id="system_prompt"
                value={formData.system_prompt}
                onChange={(e) => handleInputChange('system_prompt', e.target.value)}
                disabled={saving}
                rows={8}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-primary text-primary font-mono text-sm resize-vertical ${
                  errors.system_prompt ? 'border-red-300' : 'border-secondary'
                }`}
                placeholder="You are a helpful assistant..."
              />
              {errors.system_prompt && (
                <p className="mt-1 text-sm text-red-600">{errors.system_prompt}</p>
              )}
            </div>

            <div>
              <label htmlFor="user_prompt" className="block text-sm font-medium text-primary mb-2">
                User Prompt
              </label>
              <textarea
                id="user_prompt"
                value={formData.user_prompt}
                onChange={(e) => handleInputChange('user_prompt', e.target.value)}
                disabled={saving}
                rows={6}
                className="w-full px-3 py-2 border border-secondary rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-primary text-primary font-mono text-sm resize-vertical"
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
            disabled={saving}
            className="px-4 py-2 text-secondary hover:text-primary border border-secondary hover:bg-primary rounded-md transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving || !hasChanges}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors disabled:opacity-50 flex items-center space-x-2"
          >
            {saving ? (
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