import { z } from 'zod';

// Base schema for common fields
const basePromptSchema = {
  description: z.string().optional(),
  system_prompt: z.string().min(1, 'System prompt is required'),
  user_prompt: z.string().optional(),
  tags: z.array(z.string()).optional(),
  group: z.string().optional(),
};

// Schema for creating new prompts
export const promptCreateSchema = z.object({
  name: z
    .string()
    .min(1, 'Name is required')
    .regex(/^[a-zA-Z0-9_-]+$/, 'Name must contain only letters, numbers, underscores, and hyphens (no spaces)'),
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
    .regex(/^[a-zA-Z0-9_-]+$/, 'Name must contain only letters, numbers, underscores, and hyphens (no spaces)'),
  description: z.string(),
  system_prompt: z.string().min(1, 'System prompt is required'),
  user_prompt: z.string(),
  tags: z.array(z.string()),
  group: z.string().min(1, 'Group is required'),
});

// Type inference from schemas
export type PromptCreateInput = z.infer<typeof promptCreateSchema>;
export type PromptUpdateInput = z.infer<typeof promptUpdateSchema>;
export type PromptFormInput = z.infer<typeof promptFormSchema>;