/**
 * Modern Theme Constants
 * Centralized theme configuration for consistent styling across the application
 */

export const THEME_COLORS = {
  // Primary Colors
  navy: '#1F2A44',
  accentBlue: '#3E8EF7',
  
  // Secondary Colors
  softCyan: '#5ED1E3',
  lime: '#C4F000',
  
  // Grayscale
  charcoal: '#111318',
  mediumGray: '#2E323D',
  lightGray: '#F3F4F6',
  white: '#FFFFFF',
  
  // Status Colors
  statusGreen: '#22C55E',
  statusYellow: '#EAB308',
  statusRed: '#EF4444',
  statusBlue: '#3E8EF7',
  statusGray: '#6B7280',
};

export const THEME_RADIUS = {
  sm: '0.5rem',
  md: '0.75rem',
  lg: '1rem',
  xl: '1.25rem',
};

export const THEME_SHADOWS = {
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -1px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -2px rgb(0 0 0 / 0.1)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
};

export const THEME_TYPOGRAPHY = {
  fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", sans-serif',
  
  sizes: {
    xs: '0.75rem',
    sm: '0.875rem',
    base: '1rem',
    lg: '1.125rem',
    xl: '1.25rem',
    '2xl': '1.5rem',
    '3xl': '1.875rem',
    '4xl': '2.25rem',
  },
  
  weights: {
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
};

export const STATUS_STYLES = {
  green: {
    bg: 'bg-green-100 dark:bg-green-900/20',
    text: 'text-green-800 dark:text-green-300',
    border: 'border-green-200 dark:border-green-800',
    badge: 'bg-green-500',
  },
  yellow: {
    bg: 'bg-yellow-100 dark:bg-yellow-900/20',
    text: 'text-yellow-800 dark:text-yellow-300',
    border: 'border-yellow-200 dark:border-yellow-800',
    badge: 'bg-yellow-500',
  },
  red: {
    bg: 'bg-red-100 dark:bg-red-900/20',
    text: 'text-red-800 dark:text-red-300',
    border: 'border-red-200 dark:border-red-800',
    badge: 'bg-red-500',
  },
  blue: {
    bg: 'bg-blue-100 dark:bg-blue-900/20',
    text: 'text-blue-800 dark:text-blue-300',
    border: 'border-blue-200 dark:border-blue-800',
    badge: 'bg-blue-500',
  },
  gray: {
    bg: 'bg-gray-100 dark:bg-gray-800',
    text: 'text-gray-800 dark:text-gray-300',
    border: 'border-gray-200 dark:border-gray-700',
    badge: 'bg-gray-500',
  },
};

export const BUTTON_VARIANTS = {
  primary: 'bg-primary hover:bg-primary/90 text-primary-foreground shadow-modern hover:shadow-modern-md',
  secondary: 'bg-secondary hover:bg-secondary/80 text-secondary-foreground',
  accent: 'bg-accent-blue hover:bg-accent-blue/90 text-white shadow-modern hover:shadow-modern-md',
  outline: 'border-2 border-input bg-background hover:bg-accent hover:text-accent-foreground',
  ghost: 'hover:bg-accent hover:text-accent-foreground',
  destructive: 'bg-destructive hover:bg-destructive/90 text-destructive-foreground shadow-modern',
};

export const CARD_VARIANTS = {
  default: 'bg-card text-card-foreground shadow-modern rounded-xl border',
  elevated: 'bg-card text-card-foreground shadow-modern-lg rounded-xl border',
  glass: 'bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl border border-white/20 dark:border-white/10 rounded-xl shadow-modern-lg',
};
