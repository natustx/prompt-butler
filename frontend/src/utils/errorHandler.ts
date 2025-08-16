import { ApiError } from '../services/api';

/**
 * Extracts a user-friendly error message from an error object
 * @param error - The error to extract message from
 * @param fallbackMessage - Default message if extraction fails
 * @returns User-friendly error message
 */
export function extractErrorMessage(error: unknown, fallbackMessage: string): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  return fallbackMessage;
}

/**
 * Standard error handler for API operations
 * @param error - The error to handle
 * @param operation - Description of the operation that failed
 * @param onError - Callback to set error state
 */
export function handleApiError(
  error: unknown, 
  operation: string, 
  onError: (message: string) => void
): void {
  console.error(`Failed to ${operation}:`, error);
  const errorMessage = extractErrorMessage(error, `Failed to ${operation}`);
  onError(errorMessage);
}