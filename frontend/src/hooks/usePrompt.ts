import { useState, useEffect, useCallback } from 'react';
import { promptApi } from '../services/api';
import { handleApiError } from '../utils/errorHandler';
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
      handleApiError(err, 'fetch prompt', setError);
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
      handleApiError(err, 'create prompt', setSaveError);
      throw err;
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
      handleApiError(err, 'update prompt', setSaveError);
      throw err;
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