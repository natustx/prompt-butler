import { useState, useEffect, useCallback } from 'react';
import { promptApi } from '../services/api';
import { handleApiError } from '../utils/errorHandler';
import type { Prompt, PromptCreate, PromptUpdate } from '../types/prompt';

interface UsePromptState {
  prompt: Prompt | null;
  loading: boolean;
  error: string | null;
  saveError: string | null;
  refetch: () => void;
  createPrompt: (data: PromptCreate) => Promise<Prompt>;
  updatePrompt: (group: string | undefined, name: string, data: PromptUpdate) => Promise<Prompt>;
}

export function usePrompt(group?: string, name?: string): UsePromptState {
  const [prompt, setPrompt] = useState<Prompt | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
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
      const promptData = await promptApi.getPrompt(group, name);
      setPrompt(promptData);
    } catch (err) {
      handleApiError(err, 'fetch prompt', setError);
    } finally {
      setLoading(false);
    }
  }, [group, name]);

  const createPrompt = useCallback(async (data: PromptCreate): Promise<Prompt> => {
    try {
      setSaveError(null);
      const newPrompt = await promptApi.createPrompt(data);
      setPrompt(newPrompt);
      return newPrompt;
    } catch (err) {
      handleApiError(err, 'create prompt', setSaveError);
      throw err;
    }
  }, []);

  const updatePrompt = useCallback(
    async (promptGroup: string | undefined, promptName: string, data: PromptUpdate): Promise<Prompt> => {
      try {
        setSaveError(null);
        const updatedPrompt = await promptApi.updatePrompt(promptGroup, promptName, data);
        setPrompt(updatedPrompt);
        return updatedPrompt;
      } catch (err) {
        handleApiError(err, 'update prompt', setSaveError);
        throw err;
      }
    },
    []
  );

  useEffect(() => {
    fetchPrompt();
  }, [fetchPrompt]);

  return {
    prompt,
    loading,
    error,
    saveError,
    refetch: fetchPrompt,
    createPrompt,
    updatePrompt,
  };
}
