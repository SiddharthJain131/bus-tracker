/**
 * API Configuration
 * Central configuration for all API endpoints
 */

// Get backend URL from environment variable with fallback for development
export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Base API URL with /api prefix (required for Kubernetes ingress routing)
export const API_BASE_URL = `${BACKEND_URL}/api`;

/**
 * API endpoint builders
 * These functions help construct consistent API endpoints
 */
export const API_ENDPOINTS = {
  // Authentication
  auth: {
    login: () => `${API_BASE_URL}/auth/login`,
    logout: () => `${API_BASE_URL}/auth/logout`,
    me: () => `${API_BASE_URL}/auth/me`,
  },
  
  // Students
  students: {
    list: () => `${API_BASE_URL}/students`,
    detail: (id) => `${API_BASE_URL}/students/${id}`,
    create: () => `${API_BASE_URL}/students`,
    update: (id) => `${API_BASE_URL}/students/${id}`,
    delete: (id) => `${API_BASE_URL}/students/${id}`,
    classSections: () => `${API_BASE_URL}/students/class-sections`,
    embedding: (id) => `${API_BASE_URL}/students/${id}/embedding`,
    photo: (id) => `${API_BASE_URL}/students/${id}/photo`,
  },
  
  // Users
  users: {
    list: () => `${API_BASE_URL}/users`,
    detail: (id) => `${API_BASE_URL}/users/${id}`,
    create: () => `${API_BASE_URL}/users`,
    update: (id) => `${API_BASE_URL}/users/${id}`,
    delete: (id) => `${API_BASE_URL}/users/${id}`,
  },
  
  // Parents
  parents: {
    unlinked: () => `${API_BASE_URL}/parents/unlinked`,
    all: () => `${API_BASE_URL}/parents/all`,
  },
  
  // Buses
  buses: {
    list: () => `${API_BASE_URL}/buses`,
    detail: (id) => `${API_BASE_URL}/buses/${id}`,
    create: () => `${API_BASE_URL}/buses`,
    update: (id) => `${API_BASE_URL}/buses/${id}`,
    delete: (id) => `${API_BASE_URL}/buses/${id}`,
    stops: (id) => `${API_BASE_URL}/buses/${id}/stops`,
    location: (id) => `${API_BASE_URL}/get_bus_location?bus_number=${id}`,
  },
  
  // Routes
  routes: {
    list: () => `${API_BASE_URL}/routes`,
    detail: (id) => `${API_BASE_URL}/routes/${id}`,
    create: () => `${API_BASE_URL}/routes`,
    update: (id) => `${API_BASE_URL}/routes/${id}`,
    delete: (id) => `${API_BASE_URL}/routes/${id}`,
  },
  
  // Stops
  stops: {
    list: () => `${API_BASE_URL}/stops`,
    detail: (id) => `${API_BASE_URL}/stops/${id}`,
    create: () => `${API_BASE_URL}/stops`,
    update: (id) => `${API_BASE_URL}/stops/${id}`,
    delete: (id) => `${API_BASE_URL}/stops/${id}`,
  },
  
  // Holidays
  holidays: {
    list: () => `${API_BASE_URL}/admin/holidays`,
    create: () => `${API_BASE_URL}/admin/holidays`,
    update: (id) => `${API_BASE_URL}/admin/holidays/${id}`,
    delete: (id) => `${API_BASE_URL}/admin/holidays/${id}`,
  },
  
  // Attendance
  attendance: {
    get: (studentId, month, year) => 
      `${API_BASE_URL}/get_attendance?student_id=${studentId}&month=${month}&year=${year}`,
  },
  
  // Notifications
  notifications: {
    list: () => `${API_BASE_URL}/get_notifications`,
    markRead: (id) => `${API_BASE_URL}/mark_notification_read/${id}`,
  },
  
  // Photos
  photos: {
    upload: (type) => `${API_BASE_URL}/upload_photo?type=${type}`,
    base: () => `${API_BASE_URL}/photos`,
  },
  
  // Device/Scan Events
  device: {
    register: () => `${API_BASE_URL}/device/register`,
    list: () => `${API_BASE_URL}/device/list`,
  },
  
  scan: {
    event: () => `${API_BASE_URL}/scan_event`,
    updateLocation: () => `${API_BASE_URL}/update_location`,
  },
  
  // Teacher specific
  teacher: {
    students: () => `${API_BASE_URL}/teacher/students`,
  },
};

// For backward compatibility - export the base API URL as API
export const API = API_BASE_URL;
