import React, { useState, useEffect } from 'react';
import { Bell } from 'lucide-react';
import { Button } from './ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from './ui/popover';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function NotificationDropdown({ 
  notifications, 
  onNotificationClick, 
  onRefresh,
  themeColor = 'teacher' // 'teacher', 'parent', or 'admin'
}) {
  const [open, setOpen] = useState(false);
  const [shake, setShake] = useState(false);
  
  const unreadCount = notifications.filter(n => !n.read).length;
  
  // Shake animation when new unread notifications arrive
  useEffect(() => {
    if (unreadCount > 0) {
      setShake(true);
      const timer = setTimeout(() => setShake(false), 1000);
      return () => clearTimeout(timer);
    }
  }, [unreadCount]);
  
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };
  
  const getThemeColors = () => {
    switch (themeColor) {
      case 'teacher':
        return {
          bgLight: 'bg-teacher-light',
          textPrimary: 'text-teacher-primary',
          borderHover: 'hover:border-teacher-primary/40',
          badgeBg: 'bg-teacher-primary',
        };
      case 'parent':
        return {
          bgLight: 'bg-parent-light',
          textPrimary: 'text-parent-primary',
          borderHover: 'hover:border-parent-primary/40',
          badgeBg: 'bg-parent-primary',
        };
      case 'admin':
        return {
          bgLight: 'bg-admin-light',
          textPrimary: 'text-admin-primary',
          borderHover: 'hover:border-admin-primary/40',
          badgeBg: 'bg-admin-primary',
        };
      default:
        return {
          bgLight: 'bg-gray-100',
          textPrimary: 'text-gray-900',
          borderHover: 'hover:border-gray-400',
          badgeBg: 'bg-gray-900',
        };
    }
  };
  
  const colors = getThemeColors();
  
  const handleNotificationClick = (notification) => {
    setOpen(false);
    onNotificationClick(notification);
  };
  
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button 
          variant="outline" 
          size="icon"
          className={`relative ${shake ? 'animate-shake' : ''}`}
        >
          <Bell className={`h-5 w-5 ${colors.textPrimary}`} />
          {unreadCount > 0 && (
            <Badge 
              className={`absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 ${colors.badgeBg} text-white text-xs`}
            >
              {unreadCount > 9 ? '9+' : unreadCount}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent 
        className="w-96 p-0" 
        align="end"
        sideOffset={8}
      >
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="font-semibold text-lg">Notifications</h3>
          {unreadCount > 0 && (
            <Badge variant="secondary" className="text-xs">
              {unreadCount} new
            </Badge>
          )}
        </div>
        <ScrollArea className="h-[400px]">
          <div className="p-2">
            {notifications.length === 0 ? (
              <div className="text-center py-8 text-gray-500 text-sm">
                No notifications
              </div>
            ) : (
              <div className="space-y-1">
                {notifications.map((notification) => (
                  <div
                    key={notification.notification_id}
                    onClick={() => handleNotificationClick(notification)}
                    className={`flex items-start gap-3 p-3 rounded-lg border border-gray-200 bg-white ${colors.borderHover} hover:shadow-md transition-all cursor-pointer`}
                  >
                    <div className={`flex items-center justify-center w-10 h-10 rounded-lg ${colors.bgLight} ${colors.textPrimary} flex-shrink-0`}>
                      <Bell className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <h4 className="font-semibold text-gray-900 text-sm truncate">
                          {notification.title}
                        </h4>
                        {notification.timestamp && (
                          <span className="text-xs text-gray-500 whitespace-nowrap">
                            {formatTimestamp(notification.timestamp)}
                          </span>
                        )}
                      </div>
                      {notification.message && (
                        <p className="text-sm text-gray-600 line-clamp-2">
                          {notification.message}
                        </p>
                      )}
                      {!notification.read && (
                        <div className="mt-2">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${colors.badgeBg} text-white`}>
                            New
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </ScrollArea>
      </PopoverContent>
    </Popover>
  );
}
