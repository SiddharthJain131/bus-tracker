import React, { useState, useEffect, useRef } from 'react';
import { Bell, X, Check, AlertCircle, MoreVertical, Trash2, CheckCircle } from 'lucide-react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import NotificationDetailModal from './NotificationDetailModal';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const NotificationBell = ({ role = 'parent' }) => {
  const [notifications, setNotifications] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [showDetail, setShowDetail] = useState(false);
  const [selectedNotification, setSelectedNotification] = useState(null);
  const [openMenuId, setOpenMenuId] = useState(null);
  const dropdownRef = useRef(null);

  const unreadCount = notifications.filter(n => !n.read).length;

  // Fetch notifications
  const fetchNotifications = async () => {
    try {
      const res = await fetch(`${API}/get_notifications`, {
        credentials: 'include'
      });
      if (res.ok) {
        const data = await res.json();
        setNotifications(data);
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  };

  useEffect(() => {
    fetchNotifications();
    // Poll for new notifications every 30 seconds
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const markAsRead = async (notificationId, e) => {
    if (e) e.stopPropagation();
    try {
      const res = await fetch(`${API}/mark_notification_read/${notificationId}`, {
        method: 'PUT',
        credentials: 'include'
      });
      if (res.ok) {
        // REMOVED: Success toast - silent icon state change is sufficient
        setNotifications(prev =>
          prev.map(n => n.notification_id === notificationId ? { ...n, read: true } : n)
        );
        setOpenMenuId(null);
      } else {
        // KEEP: Error toast for failed operations
        toast.error('Failed to mark as read');
      }
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
      // KEEP: Error toast for network failures
      toast.error('Failed to mark as read');
    }
  };

  const deleteNotification = async (notificationId, e) => {
    if (e) e.stopPropagation();
    try {
      const res = await fetch(`${API}/notifications/${notificationId}`, {
        method: 'DELETE',
        credentials: 'include'
      });
      if (res.ok) {
        // REMOVED: Success toast - silent removal is sufficient
        setNotifications(prev => prev.filter(n => n.notification_id !== notificationId));
        setOpenMenuId(null);
      }
    } catch (error) {
      console.error('Failed to delete notification:', error);
      // KEEP: Error toast for network failures
      toast.error('Failed to delete notification');
    }
  };

  const handleNotificationClick = (notification) => {
    setSelectedNotification(notification);
    setShowDetail(true);
    setIsOpen(false);
    if (!notification.read) {
      markAsRead(notification.notification_id);
    }
  };

  const getRoleColor = () => {
    switch (role) {
      case 'admin':
        return 'text-admin-primary';
      case 'teacher':
        return 'text-teacher-primary';
      case 'parent':
        return 'text-parent-primary';
      default:
        return 'text-blue-600';
    }
  };

  const getRoleBgColor = () => {
    switch (role) {
      case 'admin':
        return 'bg-admin-primary';
      case 'teacher':
        return 'bg-teacher-primary';
      case 'parent':
        return 'bg-parent-primary';
      default:
        return 'bg-blue-600';
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`relative p-2 rounded-lg hover:bg-gray-100 transition-colors ${
          unreadCount > 0 ? 'animate-shake-pulse' : ''
        }`}
        aria-label="Notifications"
      >
        <Bell className={`w-6 h-6 ${unreadCount > 0 ? getRoleColor() : 'text-gray-600'}`} />
        {unreadCount > 0 && (
          <span className={`absolute -top-1 -right-1 ${getRoleBgColor()} text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center`}>
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 max-h-[600px] overflow-hidden rounded-lg shadow-modern-xl border border-gray-200 bg-white z-50 animate-fade-in">
          {/* Header */}
          <div className={`px-4 py-3 border-b border-gray-200 flex items-center justify-between ${getRoleBgColor()} bg-opacity-10`}>
            <h3 className="font-semibold text-gray-900 flex items-center gap-2">
              <Bell className="w-5 h-5" />
              Notifications
              {unreadCount > 0 && (
                <span className={`${getRoleBgColor()} text-white text-xs font-bold rounded-full px-2 py-0.5`}>
                  {unreadCount} new
                </span>
              )}
            </h3>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1 hover:bg-gray-200 rounded transition-colors"
            >
              <X className="w-4 h-4 text-gray-500" />
            </button>
          </div>

          {/* Notifications List */}
          <div className="overflow-y-auto max-h-[500px]">
            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-500">
                <Bell className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p className="font-medium">No notifications</p>
                <p className="text-sm mt-1">You're all caught up!</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {notifications.map((notification) => (
                  <div
                    key={notification.notification_id}
                    className={`px-4 py-3 transition-colors hover:bg-gray-50 relative ${
                      !notification.read ? 'bg-blue-50/50' : ''
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`mt-1 p-2 rounded-full ${
                        notification.type === 'alert' ? 'bg-red-100' : 'bg-yellow-100'
                      }`}>
                        <AlertCircle className={`w-4 h-4 ${
                          notification.type === 'alert' ? 'text-red-600' : 'text-yellow-600'
                        }`} />
                      </div>
                      <div 
                        className="flex-1 min-w-0 cursor-pointer"
                        onClick={() => handleNotificationClick(notification)}
                      >
                        <p className={`text-sm font-medium text-gray-900 ${
                          !notification.read ? 'font-semibold' : ''
                        }`}>
                          {notification.title || 'Notification'}
                        </p>
                        <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                          {notification.message}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                          {new Date(notification.timestamp).toLocaleString()}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        {!notification.read && (
                          <div className={`w-2 h-2 ${getRoleBgColor()} rounded-full`}></div>
                        )}
                        <div className="relative">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setOpenMenuId(openMenuId === notification.notification_id ? null : notification.notification_id);
                            }}
                            className="p-1 hover:bg-gray-200 rounded transition-colors"
                          >
                            <MoreVertical className="w-4 h-4 text-gray-500" />
                          </button>
                          {openMenuId === notification.notification_id && (
                            <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-50 overflow-hidden">
                              {!notification.read && (
                                <button
                                  onClick={(e) => markAsRead(notification.notification_id, e)}
                                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2 transition-colors"
                                >
                                  <CheckCircle className="w-4 h-4 text-green-600" />
                                  <span>Mark as Read</span>
                                </button>
                              )}
                              <button
                                onClick={(e) => deleteNotification(notification.notification_id, e)}
                                className="w-full px-4 py-2 text-left text-sm hover:bg-red-50 flex items-center gap-2 text-red-600 transition-colors"
                              >
                                <Trash2 className="w-4 h-4" />
                                <span>Delete</span>
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Notification Detail Modal */}
      {showDetail && selectedNotification && (
        <NotificationDetailModal
          notification={selectedNotification}
          isOpen={showDetail}
          onClose={() => {
            setShowDetail(false);
            setSelectedNotification(null);
          }}
        />
      )}
    </div>
  );
};

export default NotificationBell;
