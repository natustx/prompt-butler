import { useState, useEffect, useCallback } from 'react';
import { promptApi, ApiError } from '../services/api';
import type { Prompt } from '../types/prompt';

interface UsePromptsState {
  prompts: Prompt[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
  deletePrompt: (name: string) => Promise<void>;
}

export function usePrompts(): UsePromptsState {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPrompts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const promptNames = await promptApi.listPrompts();
      
      if (promptNames.length === 0) {
        setPrompts([]);
        return;
      }
      
      const promptDetails = await Promise.all(
        promptNames.map(name => promptApi.getPrompt(name))
      );
      
      setPrompts(promptDetails);
    } catch (err) {
      console.error('Failed to fetch prompts:', err);
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to load prompts');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const deletePrompt = useCallback(async (name: string) => {
    try {
      await promptApi.deletePrompt(name);
      setPrompts(prevPrompts => prevPrompts.filter(p => p.name !== name));
    } catch (err) {
      console.error('Failed to delete prompt:', err);
      if (err instanceof ApiError) {
        throw new Error(err.message);
      } else {
        throw new Error('Failed to delete prompt');
      }
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