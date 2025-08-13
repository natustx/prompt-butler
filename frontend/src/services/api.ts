import { Prompt, PromptCreate, PromptUpdate } from '../types/prompt';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const error = await response.json();
      message = error.detail || message;
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
  async listPrompts(): Promise<string[]> {
    const response = await fetch(`${API_BASE_URL}/api/prompts/`);
    return handleResponse<string[]>(response);
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

export { ApiError };