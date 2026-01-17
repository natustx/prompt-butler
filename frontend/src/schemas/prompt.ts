import { z } from 'zod';

// Keep these in sync with backend/models.py.
const NAME_REGEX = /^[a-zA-Z0-9_-]+$/;
const GROUP_REGEX = /^[a-zA-Z0-9_-]*$/;
const NAME_MESSAGE =
  'Name must contain only letters, numbers, underscores, and hyphens (no spaces)';
const GROUP_MESSAGE = 'Group must contain only letters, numbers, underscores, and hyphens';
const PROMPT_MAX_LENGTH = 50000;
const PROMPT_MAX_MESSAGE = 'Prompt must be at most 50000 characters';

// Base schema for common fields
const basePromptSchema = {
  description: z.string().optional(),
  system_prompt: z.string().min(1, 'System prompt is required').max(PROMPT_MAX_LENGTH, PROMPT_MAX_MESSAGE),
  user_prompt: z.string().max(PROMPT_MAX_LENGTH, PROMPT_MAX_MESSAGE).optional(),
  tags: z.array(z.string()).optional(),
  group: z.string().regex(GROUP_REGEX, GROUP_MESSAGE).optional(),
};

// Schema for creating new prompts
export const promptCreateSchema = z.object({
  name: z
    .string()
    .min(1, 'Name is required')
    .regex(NAME_REGEX, NAME_MESSAGE),
  ...basePromptSchema,
});

// Schema for updating existing prompts  
export const promptUpdateSchema = z.object({
  ...basePromptSchema,
});

// Form schema that includes all fields for react-hook-form
export const promptFormSchema = z.object({
  name: z
    .string()
    .min(1, 'Name is required')
    .regex(NAME_REGEX, NAME_MESSAGE),
  description: z.string(),
  system_prompt: z.string().min(1, 'System prompt is required').max(PROMPT_MAX_LENGTH, PROMPT_MAX_MESSAGE),
  user_prompt: z.string().max(PROMPT_MAX_LENGTH, PROMPT_MAX_MESSAGE),
  tags: z.array(z.string()),
  group: z.string().regex(GROUP_REGEX, GROUP_MESSAGE),
});

// Type inference from schemas
export type PromptCreateInput = z.infer<typeof promptCreateSchema>;
export type PromptUpdateInput = z.infer<typeof promptUpdateSchema>;
export type PromptFormInput = z.infer<typeof promptFormSchema>;
