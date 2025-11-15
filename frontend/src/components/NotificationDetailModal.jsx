import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Bell, X } from 'lucide-react';
import { Button } from './ui/button';

const NotificationDetailModal = ({ notification, isOpen, onClose }) => {
  if (!notification) return null;

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', { 
      month: 'long', 
      day: 'numeric', 
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true 
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5 text-purple-600" />
            {notification.title}
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          {notification.timestamp && (
            <p className="text-sm text-gray-500">
              {formatTimestamp(notification.timestamp)}
            </p>
          )}
          {notification.message && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-gray-700 whitespace-pre-wrap">{notification.message}</p>
            </div>
          )}
          <div className="flex items-center gap-2">
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
              notification.read 
                ? 'bg-gray-100 text-gray-600' 
                : 'bg-purple-100 text-purple-700'
            }`}>
              {notification.read ? 'Read' : 'Unread'}
            </span>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
              {notification.type}
            </span>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default NotificationDetailModal;
