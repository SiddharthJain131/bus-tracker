import React, { useState, useRef } from 'react';
import { User, Mail, Phone, Camera } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const getInitials = (name) => {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .substring(0, 2);
};

export default function UserProfileHeader({ user, onPhotoUpdate }) {
  const [isHovered, setIsHovered] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);

  const handlePhotoClick = () => {
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
      const response = await axios.put(`${BACKEND_URL}/api/users/me/photo`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        withCredentials: true,
      });

      toast.success('Photo updated successfully!');
      
      // Notify parent component to refresh user data
      if (onPhotoUpdate) {
        onPhotoUpdate(response.data.photo_url);
      } else {
        // Force page reload to show new photo
        window.location.reload();
      }
    } catch (error) {
      console.error('Photo upload error:', error);
      toast.error(error.response?.data?.detail || 'Failed to update photo');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="flex items-center gap-4 bg-white p-4 rounded-lg border border-gray-200" data-testid="user-profile-header">
      {/* Avatar */}
      <div 
        className="relative w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xl font-bold overflow-hidden transition-all duration-300 hover:scale-110 hover:shadow-xl hover:ring-4 hover:ring-blue-300 cursor-pointer"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={handlePhotoClick}
      >
        {user.photo ? (
          <img src={user.photo} alt={user.name} className="w-full h-full rounded-full object-cover transition-transform duration-300 hover:scale-110" />
        ) : (
          getInitials(user.name)
        )}
        
        {/* Edit overlay */}
        {isHovered && !isUploading && (
          <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center rounded-full">
            <Camera className="w-6 h-6 text-white" />
          </div>
        )}
        
        {/* Uploading overlay */}
        {isUploading && (
          <div className="absolute inset-0 bg-black bg-opacity-70 flex items-center justify-center rounded-full">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
          </div>
        )}
        
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          className="hidden"
        />
      </div>
      
      {/* Info */}
      <div className="flex-1">
        <h2 className="text-xl font-semibold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>{user.name}</h2>
        <div className="flex flex-wrap gap-4 mt-1 text-sm text-gray-600">
          {user.email && (
            <div className="flex items-center gap-1">
              <Mail className="w-4 h-4" />
              <span>{user.email}</span>
            </div>
          )}
          {user.phone && (
            <div className="flex items-center gap-1">
              <Phone className="w-4 h-4" />
              <span>{user.phone}</span>
            </div>
          )}
        </div>
        {user.assigned_class && (
          <div className="mt-1 text-sm text-gray-500">
            Class: {user.assigned_class} {user.assigned_section && `- Section ${user.assigned_section}`}
          </div>
        )}
      </div>
    </div>
  );
}
