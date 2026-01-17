import { useState } from 'react';
import type { ReactNode } from 'react';
import { Trash2, AlertCircle } from 'lucide-react';
import { LoadingSpinner } from './LoadingSpinner';
import { handleApiError } from '../utils/errorHandler';
import { Alert, AlertDescription } from '@/components/ui/alert';
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
  const [open, setOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const handleOpenChange = (nextOpen: boolean) => {
    if (isDeleting) {
      return;
    }
    if (!nextOpen) {
      setDeleteError(null);
    }
    setOpen(nextOpen);
  };

  const handleDelete = async () => {
    try {
      setIsDeleting(true);
      setDeleteError(null);
      await onDelete(promptName);
      setOpen(false);
    } catch (error) {
      handleApiError(error, 'delete prompt', setDeleteError);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <AlertDialog open={open} onOpenChange={handleOpenChange}>
      <AlertDialogTrigger asChild>
        {children}
      </AlertDialogTrigger>
      <AlertDialogContent className="bg-surface max-w-md">
        <AlertDialogHeader className="text-left">
          <div className="flex items-center space-x-3 mb-2">
            <div className="flex-shrink-0 w-10 h-10 bg-surface-alt border border-destructive flex items-center justify-center">
              <Trash2 className="h-5 w-5 text-destructive" />
            </div>
            <AlertDialogTitle className="text-lg font-semibold text-default">
              Delete Prompt
            </AlertDialogTitle>
          </div>
        </AlertDialogHeader>
        <AlertDialogDescription className="text-muted text-left">
          Are you sure you want to delete the prompt{' '}
          <span className="font-semibold text-default">"{promptName}"</span>?
          <span className="block text-subtle text-sm mt-2">
            This action cannot be undone.
          </span>
          
          {deleteError && (
            <Alert variant="destructive" className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {deleteError}
              </AlertDescription>
            </Alert>
          )}
        </AlertDialogDescription>
        <AlertDialogFooter className="space-x-3">
          <AlertDialogCancel
            className="text-muted hover:text-default border-strong hover:bg-surface-alt"
            disabled={isDeleting}
          >
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
