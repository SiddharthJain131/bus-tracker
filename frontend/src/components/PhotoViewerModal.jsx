import React, { useRef, useState } from 'react';
import { Dialog, DialogContent } from './ui/dialog';
import { Button } from './ui/button';
import { X, Edit2, Upload } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { getInitials } from '../utils/helpers';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function PhotoViewerModal({ 
  open, 
  onClose, 
  photoUrl, 
  userName, 
  canEdit = false,
  onPhotoUpdate,
  uploadEndpoint
}) {
  const [isUploading, setIsUploading] = useState(false);
  const [currentPhotoUrl, setCurrentPhotoUrl] = useState(photoUrl);
  const fileInputRef = useRef(null);

  // Update photo when prop changes
  React.useEffect(() => {
    setCurrentPhotoUrl(photoUrl);
  }, [photoUrl]);

  const handleEditClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Image size should be less than 5MB');
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.put(uploadEndpoint, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        withCredentials: true,
      });

      toast.success('Photo updated successfully!');
      
      // Update local state with new photo
      const newPhotoUrl = response.data.photo_url;
      setCurrentPhotoUrl(newPhotoUrl);
      
      // Notify parent component to refresh
      if (onPhotoUpdate) {
        onPhotoUpdate(newPhotoUrl);
      }
    } catch (error) {
      console.error('Photo upload error:', error);
      toast.error(error.response?.data?.detail || 'Failed to update photo');
    } finally {
      setIsUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const getInitials = (name) => {
    if (!name) return '?';
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .substring(0, 2);
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl p-0 overflow-hidden bg-black/95">
        {/* Close button */}
        <Button
          variant="ghost"
          size="icon"
          onClick={onClose}
          className="absolute top-4 right-4 z-50 text-white hover:bg-white/20 rounded-full"
        >
          <X className="w-6 h-6" />
        </Button>

        {/* Photo viewer */}
        <div className="relative w-full h-[80vh] flex items-center justify-center p-8">
          {currentPhotoUrl ? (
            <img
              src={currentPhotoUrl}
              alt={userName}
              className="max-w-full max-h-full object-contain rounded-lg"
            />
          ) : (
            <div className="w-64 h-64 bg-gradient-to-br from-blue-400 to-indigo-600 rounded-full flex items-center justify-center text-white text-8xl font-bold">
              {getInitials(userName)}
            </div>
          )}

          {/* Edit button overlay */}
          {canEdit && (
            <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 flex gap-3">
              <Button
                onClick={handleEditClick}
                disabled={isUploading}
                className="bg-blue-600 hover:bg-blue-700 text-white shadow-lg"
              >
                {isUploading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Uploading...
                  </>
                ) : (
                  <>
                    <Edit2 className="w-4 h-4 mr-2" />
                    Edit Photo
                  </>
                )}
              </Button>
            </div>
          )}

          {/* Hidden file input */}
          {canEdit && (
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="hidden"
            />
          )}
        </div>

        {/* User name */}
        <div className="absolute top-4 left-4 text-white text-lg font-semibold">
          {userName}
        </div>
      </DialogContent>
    </Dialog>
  );
}
