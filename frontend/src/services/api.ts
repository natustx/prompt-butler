import type {
  Prompt,
  PromptCreate,
  PromptUpdate,
  TagWithCount,
  TagRenameRequest,
  TagRenameResponse,
  GroupRenameRequest,
  GroupRenameResponse,
} from '../types/prompt';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiError extends Error {
  public status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const error = await response.json();
      // Handle different error formats from FastAPI
      if (typeof error.detail === 'string') {
        message = error.detail;
      } else if (Array.isArray(error.detail)) {
        // FastAPI validation errors
        message = error.detail.map((e: { msg?: string; message?: string }) => e.msg || e.message || 'Validation error').join(', ');
      } else if (error.detail && typeof error.detail === 'object') {
        message = JSON.stringify(error.detail);
      } else if (error.message) {
        message = error.message;
      }
    } catch {
      // Use default message if JSON parsing fails
    }
    throw new ApiError(response.status, message);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const promptApi = {
  // List all prompts
  async listPrompts(group?: string): Promise<Prompt[]> {
    const url = group
      ? `${API_BASE_URL}/api/prompts?group=${encodeURIComponent(group)}`
      : `${API_BASE_URL}/api/prompts`;
    const response = await fetch(url);
    return handleResponse<Prompt[]>(response);
  },

  // Get a specific prompt
  async getPrompt(group: string | undefined, name: string): Promise<Prompt> {
    const query = group ? `?group=${encodeURIComponent(group)}` : '';
    const response = await fetch(`${API_BASE_URL}/api/prompts/${encodeURIComponent(name)}${query}`);
    return handleResponse<Prompt>(response);
  },

  // Create a new prompt
  async createPrompt(prompt: PromptCreate): Promise<Prompt> {
    const response = await fetch(`${API_BASE_URL}/api/prompts`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(prompt),
    });
    return handleResponse<Prompt>(response);
  },

  // Update an existing prompt
  async updatePrompt(group: string | undefined, name: string, updates: PromptUpdate): Promise<Prompt> {
    const query = group ? `?group=${encodeURIComponent(group)}` : '';
    const response = await fetch(`${API_BASE_URL}/api/prompts/${encodeURIComponent(name)}${query}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    });
    return handleResponse<Prompt>(response);
  },

  // Delete a prompt
  async deletePrompt(group: string | undefined, name: string): Promise<void> {
    const query = group ? `?group=${encodeURIComponent(group)}` : '';
    const response = await fetch(`${API_BASE_URL}/api/prompts/${encodeURIComponent(name)}${query}`, {
      method: 'DELETE',
    });
    return handleResponse<void>(response);
  },

  // List all groups
  async listGroups(): Promise<string[]> {
    const response = await fetch(`${API_BASE_URL}/api/groups`);
    return handleResponse<string[]>(response);
  },

  // List all tags with counts
  async listTags(): Promise<TagWithCount[]> {
    const response = await fetch(`${API_BASE_URL}/api/tags`);
    return handleResponse<TagWithCount[]>(response);
  },

  // Rename a tag
  async renameTag(request: TagRenameRequest): Promise<TagRenameResponse> {
    const response = await fetch(`${API_BASE_URL}/api/tags/rename`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    return handleResponse<TagRenameResponse>(response);
  },

  // Rename a group
  async renameGroup(request: GroupRenameRequest): Promise<GroupRenameResponse> {
    const response = await fetch(`${API_BASE_URL}/api/groups/rename`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    return handleResponse<GroupRenameResponse>(response);
  },
};

export { ApiError };
