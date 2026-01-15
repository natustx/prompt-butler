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

export interface ErrorResponse {
  detail: string;
}

export interface TagWithCount {
  name: string;
  count: number;
}

export interface TagRenameRequest {
  old_tag: string;
  new_tag: string;
}

export interface TagRenameResponse {
  old_tag: string;
  new_tag: string;
  updated_count: number;
}

export interface GroupRenameRequest {
  old_name: string;
  new_name: string;
}

export interface GroupRenameResponse {
  old_name: string;
  new_name: string;
  moved_count: number;
}