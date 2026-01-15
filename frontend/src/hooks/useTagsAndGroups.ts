import { useState, useEffect, useCallback } from 'react';
import { promptApi } from '../services/api';
import type { TagWithCount } from '../types/prompt';

interface UseTagsAndGroupsState {
  tags: TagWithCount[];
  groups: string[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useTagsAndGroups(): UseTagsAndGroupsState {
  const [tags, setTags] = useState<TagWithCount[]>([]);
  const [groups, setGroups] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [tagsData, groupsData] = await Promise.all([promptApi.listTags(), promptApi.listGroups()]);

      setTags(tagsData);
      setGroups(groupsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tags and groups');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    tags,
    groups,
    loading,
    error,
    refetch: fetchData,
  };
}
