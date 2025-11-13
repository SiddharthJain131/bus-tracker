import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Card } from './ui/card';
import { User, Phone, Mail, MapPin, GraduationCap, Users } from 'lucide-react';
import PhotoViewerModal from './PhotoViewerModal';
import PhotoAvatar from './PhotoAvatar';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function UserDetailModal({ user, open, onClose }) {
  const [linkedStudents, setLinkedStudents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showPhotoViewer, setShowPhotoViewer] = useState(false);

  // Helper function to remove "Grade " prefix from class names
  const formatClassName = (className) => {
    if (!className) return 'N/A';
    return className.replace(/^Grade\s+/i, '');
  };

  useEffect(() => {
    if (open && user) {
      if (user.role === 'parent' || user.role === 'teacher') {
        fetchLinkedStudents();
      }
    }
  }, [open, user]);

  const fetchLinkedStudents = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/students`);
      const allStudents = response.data;
      
      const studentIds = user.student_ids || [];
      const linked = allStudents.filter(s => studentIds.includes(s.student_id));
      setLinkedStudents(linked);
    } catch (error) {
      console.error('Failed to load linked students:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  const getRoleBadgeColor = (role) => {
    switch (role) {
      case 'admin': return 'bg-purple-100 text-purple-800';
      case 'teacher': return 'bg-emerald-100 text-emerald-800';
      case 'parent': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold" style={{ fontFamily: 'Space Grotesk' }}>
            User Profile
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Profile Header */}
          <div className="flex items-center gap-6 p-6 bg-gradient-to-br from-violet-50 to-purple-50 rounded-lg">
            <PhotoAvatar
              photoUrl={user.photo_url ? `${BACKEND_URL}${user.photo_url}` : null}
              userName={user.name}
              size="xl"
              onClick={() => setShowPhotoViewer(true)}
              gradientFrom="violet-400"
              gradientTo="purple-600"
            />
            <div className="flex-1">
              <h3 className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                {user.name}
              </h3>
              <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium mt-2 ${getRoleBadgeColor(user.role)}`}>
                {user.role.toUpperCase()}
              </span>
            </div>
          </div>

          {/* User Info Grid */}
          <div className="grid md:grid-cols-2 gap-4">
            <Card className="p-4">
              <div className="flex items-center gap-3 mb-2">
                <Mail className="w-5 h-5 text-violet-600" />
                <span className="text-sm font-medium text-gray-600">Email</span>
              </div>
              <p className="text-lg font-semibold text-gray-900">{user.email}</p>
            </Card>

            <Card className="p-4">
              <div className="flex items-center gap-3 mb-2">
                <Phone className="w-5 h-5 text-violet-600" />
                <span className="text-sm font-medium text-gray-600">Phone</span>
              </div>
              <p className="text-lg font-semibold text-gray-900">{user.phone || 'N/A'}</p>
            </Card>

            {user.address && (
              <Card className="p-4 md:col-span-2">
                <div className="flex items-center gap-3 mb-2">
                  <MapPin className="w-5 h-5 text-violet-600" />
                  <span className="text-sm font-medium text-gray-600">Address</span>
                </div>
                <p className="text-lg font-semibold text-gray-900">{user.address}</p>
              </Card>
            )}

            {user.role === 'teacher' && (
              <>
                <Card className="p-4">
                  <div className="flex items-center gap-3 mb-2">
                    <GraduationCap className="w-5 h-5 text-violet-600" />
                    <span className="text-sm font-medium text-gray-600">Assigned Class</span>
                  </div>
                  <p className="text-lg font-semibold text-gray-900">
                    {formatClassName(user.assigned_class)} - {user.assigned_section || 'N/A'}
                  </p>
                </Card>
              </>
            )}
          </div>

          {/* Linked Students */}
          {(user.role === 'parent' || user.role === 'teacher') && (
            <Card className="p-4">
              <div className="flex items-center gap-3 mb-4">
                <Users className="w-5 h-5 text-violet-600" />
                <span className="text-sm font-medium text-gray-600">
                  {user.role === 'parent' ? 'Children' : 'Assigned Students'}
                </span>
              </div>
              {loading ? (
                <p className="text-sm text-gray-500">Loading...</p>
              ) : linkedStudents.length > 0 ? (
                <div className="space-y-2">
                  {linkedStudents.map(student => (
                    <div key={student.student_id} className="p-3 bg-gray-50 rounded-lg">
                      <p className="font-medium text-gray-900">{student.name}</p>
                      <p className="text-sm text-gray-600">
                        {student.class_name} - {student.section}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">No students assigned</p>
              )}
            </Card>
          )}
        </div>
      </DialogContent>

      {/* Photo Viewer Modal */}
      {showPhotoViewer && (
        <PhotoViewerModal
          open={showPhotoViewer}
          onClose={() => setShowPhotoViewer(false)}
          photoUrl={user.photo_url ? `${BACKEND_URL}${user.photo_url}` : null}
          userName={user.name}
          canEdit={false}
          uploadEndpoint={null}
          onPhotoUpdate={null}
        />
      )}
    </Dialog>
  );
}
