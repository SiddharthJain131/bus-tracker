import React, { useState } from 'react';
import { User, Mail, Phone } from 'lucide-react';
import PhotoViewerModal from './PhotoViewerModal';

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
  const [showPhotoViewer, setShowPhotoViewer] = useState(false);

  const handlePhotoClick = () => {
    setShowPhotoViewer(true);
  };

  const handlePhotoUpdateInternal = (newPhotoUrl) => {
    if (onPhotoUpdate) {
      onPhotoUpdate(newPhotoUrl);
    }
  };

  return (
    <>
      <div className="flex items-center gap-4 bg-white p-4 rounded-lg border border-gray-200" data-testid="user-profile-header">
        {/* Avatar */}
        <div 
          className="relative w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xl font-bold overflow-hidden cursor-pointer"
          onClick={handlePhotoClick}
        >
          {user.photo ? (
            <img src={user.photo} alt={user.name} className="w-full h-full rounded-full object-cover" />
          ) : (
            getInitials(user.name)
          )}
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

      {/* Photo Viewer Modal */}
      <PhotoViewerModal
        open={showPhotoViewer}
        onClose={() => setShowPhotoViewer(false)}
        photoUrl={user.photo}
        userName={user.name}
        canEdit={true}
        uploadEndpoint={`${BACKEND_URL}/api/users/me/photo`}
        onPhotoUpdate={handlePhotoUpdateInternal}
      />
    </>
  );
}
