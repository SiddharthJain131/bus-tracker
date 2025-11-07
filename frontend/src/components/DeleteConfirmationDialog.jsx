import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Button } from './ui/button';
import { AlertTriangle } from 'lucide-react';

export default function DeleteConfirmationDialog({ 
  open, 
  onClose, 
  onConfirm, 
  title = "Are you sure?",
  description,
  itemName,
  itemType = "item",
  isDeleting = false
}) {
  const defaultDescription = `This will permanently delete ${itemName || `this ${itemType}`}. This action cannot be undone.`;
  
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-red-600" />
            </div>
            <div>
              <DialogTitle className="text-xl font-bold text-gray-900">
                {title}
              </DialogTitle>
            </div>
          </div>
          <DialogDescription className="text-gray-600 pt-4">
            {description || defaultDescription}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isDeleting}
            className="w-full sm:w-auto"
          >
            Cancel
          </Button>
          <Button
            onClick={onConfirm}
            disabled={isDeleting}
            className="w-full sm:w-auto bg-red-600 hover:bg-red-700 text-white"
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
