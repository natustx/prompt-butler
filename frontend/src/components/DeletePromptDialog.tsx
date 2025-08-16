import { useState } from 'react';
import type { ReactNode } from 'react';
import { Trash2 } from 'lucide-react';
import { LoadingSpinner } from './LoadingSpinner';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';

interface DeletePromptDialogProps {
  promptName: string;
  onDelete: (promptName: string) => Promise<void>;
  children: ReactNode; // The trigger element
}

export function DeletePromptDialog({ promptName, onDelete, children }: DeletePromptDialogProps) {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    try {
      setIsDeleting(true);
      await onDelete(promptName);
    } catch (error) {
      console.error('Failed to delete prompt:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        {children}
      </AlertDialogTrigger>
      <AlertDialogContent className="bg-primary max-w-md">
        <AlertDialogHeader className="text-left">
          <div className="flex items-center space-x-3 mb-2">
            <div className="flex-shrink-0 w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
              <Trash2 className="h-5 w-5 text-red-600" />
            </div>
            <AlertDialogTitle className="text-lg font-semibold text-primary">
              Delete Prompt
            </AlertDialogTitle>
          </div>
        </AlertDialogHeader>
        <AlertDialogDescription className="text-secondary text-left">
          Are you sure you want to delete the prompt{' '}
          <span className="font-semibold text-primary">"{promptName}"</span>?
          <span className="block text-tertiary text-sm mt-2">
            This action cannot be undone.
          </span>
        </AlertDialogDescription>
        <AlertDialogFooter className="space-x-3">
          <AlertDialogCancel className="text-secondary hover:text-primary border-secondary hover:bg-tertiary">
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={isDeleting}
            className="bg-red-600 hover:bg-red-700 text-white"
          >
            {isDeleting ? (
              <div className="flex items-center space-x-2">
                <LoadingSpinner size="sm" />
                <span>Deleting...</span>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <Trash2 className="h-4 w-4" />
                <span>Delete</span>
              </div>
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}