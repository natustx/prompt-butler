export interface Prompt {
  name: string;
  description: string;
  system_prompt: string;
  user_prompt: string;
  tags: string[];
}

export interface PromptCreate {
  name: string;
  description?: string;
  system_prompt: string;
  user_prompt?: string;
  tags?: string[];
}

export interface PromptUpdate {
  description?: string;
  system_prompt?: string;
  user_prompt?: string;
  tags?: string[];
}

export interface ErrorResponse {
  detail: string;
}