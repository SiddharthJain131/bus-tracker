import React, { useState } from 'react';
import { User, Mail, Phone } from 'lucide-react';
import PhotoViewerModal from './PhotoViewerModal';
import PhotoAvatar from './PhotoAvatar';
import { formatClassName } from '../utils/helpers';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

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
        <PhotoAvatar
          photoUrl={user.photo}
          userName={user.name}
          size="md"
          onClick={handlePhotoClick}
          gradientFrom="blue-500"
          gradientTo="purple-600"
        />
        
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
              Class: {formatClassName(user.assigned_class)} {user.assigned_section && `- Section ${user.assigned_section}`}
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
