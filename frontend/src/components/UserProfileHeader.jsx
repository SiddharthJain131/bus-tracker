import React, { useState, useEffect } from 'react';
import { Mail, Phone, Heart } from 'lucide-react';
import PhotoViewerModal from './PhotoViewerModal';
import PhotoAvatar from './PhotoAvatar';
import { formatClassName } from '../utils/helpers';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Greeting messages that rotate
const greetings = [
  "Welcome back",
  "Good to see you",
  "Hope you're having a great day",
  "Hello there",
  "Great to have you here"
];

export default function UserProfileHeader({ user, onPhotoUpdate, role = 'parent' }) {
  const [showPhotoViewer, setShowPhotoViewer] = useState(false);
  const [greeting, setGreeting] = useState(greetings[0]);

  useEffect(() => {
    // Set a random greeting on mount
    const randomGreeting = greetings[Math.floor(Math.random() * greetings.length)];
    setGreeting(randomGreeting);
  }, []);

  const handlePhotoClick = () => {
    setShowPhotoViewer(true);
  };

  const handlePhotoUpdateInternal = (newPhotoUrl) => {
    if (onPhotoUpdate) {
      onPhotoUpdate(newPhotoUrl);
    }
  };

  // Role-based styling
  const roleStyles = {
    parent: {
      bgGradient: 'bg-gradient-to-r from-parent-light/50 to-orange-50/50',
      accentColor: 'text-parent-primary',
      iconColor: 'text-parent-primary',
      borderColor: 'border-parent-primary/20',
      gradientFrom: 'parent-primary',
      gradientTo: 'parent-secondary'
    },
    teacher: {
      bgGradient: 'bg-gradient-to-r from-teacher-light/50 to-teal-50/50',
      accentColor: 'text-teacher-primary',
      iconColor: 'text-teacher-primary',
      borderColor: 'border-teacher-primary/20',
      gradientFrom: 'teacher-primary',
      gradientTo: 'teacher-secondary'
    },
    admin: {
      bgGradient: 'bg-gradient-to-r from-admin-light/50 to-blue-50/50',
      accentColor: 'text-admin-primary',
      iconColor: 'text-admin-primary',
      borderColor: 'border-admin-primary/20',
      gradientFrom: 'admin-primary',
      gradientTo: 'admin-secondary'
    }
  };

  const currentRole = roleStyles[role] || roleStyles.parent;

  return (
    <>
      <div 
        className={`flex items-center gap-4 ${currentRole.bgGradient} p-6 rounded-xl border-2 ${currentRole.borderColor} shadow-sm hover:shadow-md transition-all duration-300 fade-in dashboard-card-enhanced`} 
        data-testid="user-profile-header"
      >
        {/* Avatar with slide-in animation */}
        <div className="slide-in-left">
          <PhotoAvatar
            photoUrl={user.photo ? `${BACKEND_URL}${user.photo}` : null}
            userName={user.name}
            size="lg"
            onClick={handlePhotoClick}
            gradientFrom={currentRole.gradientFrom}
            gradientTo={currentRole.gradientTo}
          />
        </div>
        
        {/* Info with fade-in */}
        <div className="flex-1 fade-in" style={{ animationDelay: '0.1s' }}>
          {/* Greeting line */}
          <p className={`text-sm font-medium ${currentRole.accentColor} mb-1 flex items-center gap-2`}>
            {greeting}, <Heart className="w-3 h-3 fill-current" />
          </p>
          
          <h2 className="text-2xl font-bold text-gray-900 mb-2" style={{ fontFamily: 'Space Grotesk' }}>
            {user.name}
          </h2>
          
          <div className="flex flex-wrap gap-4 text-sm text-gray-600">
            {user.email && (
              <div className={`flex items-center gap-2 hover:${currentRole.accentColor} transition-colors`}>
                <Mail className={`w-4 h-4 ${currentRole.iconColor}`} />
                <span>{user.email}</span>
              </div>
            )}
            {user.phone && (
              <div className={`flex items-center gap-2 hover:${currentRole.accentColor} transition-colors`}>
                <Phone className={`w-4 h-4 ${currentRole.iconColor}`} />
                <span>{user.phone}</span>
              </div>
            )}
          </div>
          
          {user.assigned_class && (
            <div className="mt-2 text-sm text-gray-500">
              Class: {formatClassName(user.assigned_class)} {user.assigned_section && `- Section ${user.assigned_section}`}
            </div>
          )}
        </div>
      </div>

      {/* Photo Viewer Modal */}
      <PhotoViewerModal
        open={showPhotoViewer}
        onClose={() => setShowPhotoViewer(false)}
        photoUrl={user.photo ? `${BACKEND_URL}${user.photo}` : null}
        userName={user.name}
        canEdit={true}
        uploadEndpoint={`${BACKEND_URL}/api/users/me/photo`}
        onPhotoUpdate={handlePhotoUpdateInternal}
      />
    </>
  );
}
