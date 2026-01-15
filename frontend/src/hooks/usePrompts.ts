import { useState, useEffect, useCallback } from 'react';
import { promptApi } from '../services/api';
import { handleApiError, extractErrorMessage } from '../utils/errorHandler';
import type { Prompt } from '../types/prompt';

interface UsePromptsState {
  prompts: Prompt[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
  deletePrompt: (group: string, name: string) => Promise<void>;
}

export function usePrompts(): UsePromptsState {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPrompts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const prompts = await promptApi.listPrompts();
      setPrompts(prompts);
    } catch (err) {
      handleApiError(err, 'fetch prompts', setError);
    } finally {
      setLoading(false);
    }
  }, []);

  const deletePrompt = useCallback(async (group: string, name: string) => {
    try {
      await promptApi.deletePrompt(group, name);
      setPrompts((prevPrompts) => prevPrompts.filter((p) => !(p.group === group && p.name === name)));
    } catch (err) {
      const errorMessage = extractErrorMessage(err, 'Failed to delete prompt');
      console.error('Failed to delete prompt:', err);
      throw new Error(errorMessage);
    }
  }, []);

  useEffect(() => {
    fetchPrompts();
  }, [fetchPrompts]);

  return {
    prompts,
    loading,
    error,
    refetch: fetchPrompts,
    deletePrompt,
  };
}
