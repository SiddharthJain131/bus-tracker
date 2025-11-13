/**
 * Utility helper functions used across components
 */

/**
 * Get initials from a person's name
 * @param {string} name - Full name of the person
 * @returns {string} Initials (max 2 characters)
 */
export const getInitials = (name) => {
  if (!name) return '?';
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .substring(0, 2);
};

/**
 * Remove "Grade " prefix from class names
 * @param {string} className - Class name that might have "Grade " prefix
 * @returns {string} Formatted class name without "Grade " prefix
 */
export const formatClassName = (className) => {
  if (!className) return 'N/A';
  return className.replace(/^Grade\s+/i, '');
};

/**
 * Format phone number for display
 * @param {string} phone - Phone number
 * @returns {string} Formatted phone number or 'N/A'
 */
export const formatPhone = (phone) => {
  return phone || 'N/A';
};

/**
 * Get status badge color based on attendance status
 * @param {string} status - Attendance status (gray, yellow, green, blue)
 * @returns {string} Tailwind CSS classes for badge
 */
export const getStatusBadgeColor = (status) => {
  switch (status) {
    case 'gray':
      return 'bg-gray-100 text-gray-800';
    case 'yellow':
      return 'bg-yellow-100 text-yellow-800';
    case 'green':
      return 'bg-green-100 text-green-800';
    case 'blue':
      return 'bg-blue-100 text-blue-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

/**
 * Get role badge color based on user role
 * @param {string} role - User role (admin, teacher, parent)
 * @returns {string} Tailwind CSS classes for badge
 */
export const getRoleBadgeColor = (role) => {
  switch (role) {
    case 'admin':
      return 'bg-purple-100 text-purple-800';
    case 'teacher':
      return 'bg-emerald-100 text-emerald-800';
    case 'parent':
      return 'bg-blue-100 text-blue-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};
