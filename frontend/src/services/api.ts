import type { GroupCount, Prompt, PromptCreate, PromptUpdate, TagCount } from '../types/prompt';

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
  async listPrompts(): Promise<Prompt[]> {
    const response = await fetch(`${API_BASE_URL}/api/prompts/`);
    return handleResponse<Prompt[]>(response);
  },

  // Get a specific prompt
  async getPrompt(name: string): Promise<Prompt> {
    const response = await fetch(`${API_BASE_URL}/api/prompts/${encodeURIComponent(name)}`);
    return handleResponse<Prompt>(response);
  },

  // Create a new prompt
  async createPrompt(prompt: PromptCreate): Promise<Prompt> {
    const response = await fetch(`${API_BASE_URL}/api/prompts/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(prompt),
    });
    return handleResponse<Prompt>(response);
  },

  // Update an existing prompt
  async updatePrompt(name: string, updates: PromptUpdate): Promise<Prompt> {
    const response = await fetch(`${API_BASE_URL}/api/prompts/${encodeURIComponent(name)}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    });
    return handleResponse<Prompt>(response);
  },

  // Delete a prompt
  async deletePrompt(name: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/prompts/${encodeURIComponent(name)}`, {
      method: 'DELETE',
    });
    return handleResponse<void>(response);
  },
};

export const groupApi = {
  // List all groups with counts
  async listGroups(): Promise<GroupCount[]> {
    const response = await fetch(`${API_BASE_URL}/api/groups/`);
    return handleResponse<GroupCount[]>(response);
  },

  // Rename a group
  async renameGroup(oldGroup: string, newGroup: string): Promise<{ updated_count: number }> {
    const response = await fetch(`${API_BASE_URL}/api/groups/rename`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ old_group: oldGroup, new_group: newGroup }),
    });
    return handleResponse<{ updated_count: number }>(response);
  },
};

export const tagApi = {
  // List all tags with counts
  async listTags(): Promise<TagCount[]> {
    const response = await fetch(`${API_BASE_URL}/api/tags/`);
    return handleResponse<TagCount[]>(response);
  },
};

export { ApiError };