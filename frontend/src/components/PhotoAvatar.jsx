import React, { useState } from 'react';
import { Eye } from 'lucide-react';
import { getInitials } from '../utils/helpers';

/**
 * Reusable PhotoAvatar component with eye icon hover effect
 * @param {string} photoUrl - URL of the photo to display
 * @param {string} userName - Name of the user for fallback initials
 * @param {string} size - Size variant: 'sm', 'md', 'lg', 'xl'
 * @param {function} onClick - Click handler for photo
 * @param {string} gradientFrom - Starting color of gradient (default: 'blue-400')
 * @param {string} gradientTo - Ending color of gradient (default: 'indigo-600')
 * @param {string} className - Additional CSS classes
 */
export default function PhotoAvatar({
  photoUrl,
  userName,
  size = 'md',
  onClick,
  gradientFrom = 'blue-400',
  gradientTo = 'indigo-600',
  className = ''
}) {
  const [isHovering, setIsHovering] = useState(false);

  // Size mappings
  const sizeClasses = {
    sm: 'w-12 h-12 text-lg',     // 48px - UserProfileHeader compact
    md: 'w-16 h-16 text-xl',     // 64px - UserProfileHeader
    lg: 'w-20 h-20 text-3xl',    // 80px - Dashboard headers
    xl: 'w-24 h-24 text-3xl'     // 96px - Detail modals
  };

  const eyeSizeClasses = {
    sm: 'w-5 h-5',
    md: 'w-6 h-6',
    lg: 'w-7 h-7',
    xl: 'w-8 h-8'
  };

  // Gradient color mappings (Tailwind safe list - all possible gradients hardcoded)
  const gradientClasses = {
    'blue-400-indigo-600': 'bg-gradient-to-br from-blue-400 to-indigo-600',
    'violet-400-purple-600': 'bg-gradient-to-br from-violet-400 to-purple-600',
    'emerald-400-teal-600': 'bg-gradient-to-br from-emerald-400 to-teal-600',
    'blue-500-purple-600': 'bg-gradient-to-br from-blue-500 to-purple-600',
  };

  const gradientKey = `${gradientFrom}-${gradientTo}`;
  const gradientClass = gradientClasses[gradientKey] || 'bg-gradient-to-br from-blue-400 to-indigo-600';

  return (
    <div
      className={`relative ${gradientClass} rounded-full flex items-center justify-center text-white font-bold overflow-hidden ${onClick ? 'cursor-pointer' : ''} ${sizeClasses[size]} ${className}`}
      onClick={onClick}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      {photoUrl ? (
        <img
          src={photoUrl}
          alt={userName}
          className="w-full h-full object-cover"
          onError={(e) => {
            e.target.style.display = 'none';
            e.target.parentElement.textContent = getInitials(userName);
          }}
        />
      ) : (
        getInitials(userName)
      )}

      {/* Eye icon overlay on hover */}
      {isHovering && onClick && (
        <div className="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center rounded-full">
          <Eye className={`text-white ${eyeSizeClasses[size]}`} />
        </div>
      )}
    </div>
  );
}
