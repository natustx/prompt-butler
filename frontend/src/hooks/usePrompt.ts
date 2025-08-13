import { useState, useEffect, useCallback } from 'react';
import { promptApi, ApiError } from '../services/api';
import type { Prompt, PromptCreate, PromptUpdate } from '../types/prompt';

interface UsePromptState {
  prompt: Prompt | null;
  loading: boolean;
  error: string | null;
  saving: boolean;
  saveError: string | null;
  refetch: () => void;
  createPrompt: (data: PromptCreate) => Promise<Prompt>;
  updatePrompt: (name: string, data: PromptUpdate) => Promise<Prompt>;
}

export function usePrompt(name?: string): UsePromptState {
  const [prompt, setPrompt] = useState<Prompt | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const fetchPrompt = useCallback(async () => {
    if (!name) {
      setPrompt(null);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const promptData = await promptApi.getPrompt(name);
      setPrompt(promptData);
    } catch (err) {
      console.error('Failed to fetch prompt:', err);
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to load prompt');
      }
    } finally {
      setLoading(false);
    }
  }, [name]);

  const createPrompt = useCallback(async (data: PromptCreate): Promise<Prompt> => {
    try {
      setSaving(true);
      setSaveError(null);
      const newPrompt = await promptApi.createPrompt(data);
      setPrompt(newPrompt);
      return newPrompt;
    } catch (err) {
      console.error('Failed to create prompt:', err);
      const errorMessage = err instanceof ApiError ? err.message : 'Failed to create prompt';
      setSaveError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setSaving(false);
    }
  }, []);

  const updatePrompt = useCallback(async (promptName: string, data: PromptUpdate): Promise<Prompt> => {
    try {
      setSaving(true);
      setSaveError(null);
      const updatedPrompt = await promptApi.updatePrompt(promptName, data);
      setPrompt(updatedPrompt);
      return updatedPrompt;
    } catch (err) {
      console.error('Failed to update prompt:', err);
      const errorMessage = err instanceof ApiError ? err.message : 'Failed to update prompt';
      setSaveError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setSaving(false);
    }
  }, []);

  useEffect(() => {
    fetchPrompt();
  }, [fetchPrompt]);

  return {
    prompt,
    loading,
    error,
    saving,
    saveError,
    refetch: fetchPrompt,
    createPrompt,
    updatePrompt,
  };
}