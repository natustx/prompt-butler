export interface Prompt {
  name: string;
  description: string;
  system_prompt: string;
  user_prompt: string;
  tags: string[];
  group: string;
}

export interface PromptCreate {
  name: string;
  description?: string;
  system_prompt: string;
  user_prompt?: string;
  tags?: string[];
  group?: string;
}

export interface PromptUpdate {
  description?: string;
  system_prompt?: string;
  user_prompt?: string;
  tags?: string[];
  group?: string;
}

export interface GroupCount {
  group: string;
  count: number;
}

export interface TagCount {
  tag: string;
  count: number;
}

export interface ErrorResponse {
  detail: string;
}