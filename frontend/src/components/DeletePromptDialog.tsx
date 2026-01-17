import { useState } from 'react';
import type { ReactNode } from 'react';
import { Trash2, AlertCircle, AlertTriangle } from 'lucide-react';
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
  children: ReactNode;
}

export function DeletePromptDialog({ promptName, onDelete, children }: DeletePromptDialogProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const handleDelete = async () => {
    try {
      setIsDeleting(true);
      setDeleteError(null);
      await onDelete(promptName);
    } catch (error) {
      handleApiError(error, 'delete prompt', setDeleteError);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        {children}
      </AlertDialogTrigger>
      <AlertDialogContent className="terminal-panel max-w-md border-destructive">
        {/* Dialog Header Bar */}
        <div className="flex items-center justify-between px-4 py-2 -mx-6 -mt-6 mb-4 border-b border-destructive bg-surface-alt">
          <div className="flex items-center gap-2 text-[10px] text-destructive tracking-widest uppercase">
            <AlertTriangle className="h-3 w-3" />
            <span>WARNING:DELETE_OPERATION</span>
          </div>
        </div>

        <AlertDialogHeader className="text-left">
          <div className="flex items-center gap-3 mb-2">
            <div className="flex-shrink-0 w-10 h-10 border border-destructive flex items-center justify-center">
              <Trash2 className="h-5 w-5 text-destructive" />
            </div>
            <AlertDialogTitle className="text-sm font-semibold text-destructive tracking-wider uppercase">
              Confirm Deletion
            </AlertDialogTitle>
          </div>
        </AlertDialogHeader>

        <AlertDialogDescription className="text-muted-foreground text-left text-sm">
          <span className="text-foreground tracking-wider">TARGET:</span>{' '}
          <span className="text-primary">"{promptName}"</span>
          <span className="block text-xs text-muted-foreground mt-3 tracking-wider">
            ⚠ THIS_ACTION_IS_IRREVERSIBLE
          </span>

          {deleteError && (
            <Alert variant="destructive" className="mt-4 border-destructive bg-transparent">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="tracking-wider">
                {deleteError}
              </AlertDescription>
            </Alert>
          )}
        </AlertDialogDescription>

        <AlertDialogFooter className="gap-2 mt-4">
          <AlertDialogCancel className="border border-border text-muted-foreground hover:text-foreground hover:border-foreground bg-transparent uppercase tracking-wider text-xs">
            [CANCEL]
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={isDeleting}
            className="border border-destructive text-destructive hover:bg-destructive hover:text-black bg-transparent uppercase tracking-wider text-xs"
          >
            {isDeleting ? (
              <div className="flex items-center gap-2">
                <LoadingSpinner size="sm" />
                <span>DELETING...</span>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Trash2 className="h-3 w-3" />
                <span>DELETE</span>
              </div>
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
