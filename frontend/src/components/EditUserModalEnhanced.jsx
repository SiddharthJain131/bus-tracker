import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { toast } from 'sonner';
import { AlertCircle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function EditUserModalEnhanced({ user, currentUser, open, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    email: '',
    assigned_class: '',
    assigned_section: '',
    address: '',
    photo: ''  // Base64 encoded photo
  });
  const [saving, setSaving] = useState(false);
  const [currentPhoto, setCurrentPhoto] = useState(null); // Store original photo for display

  // Check if editing another admin
  const isEditingOtherAdmin = user && user.role === 'admin' && user.user_id !== currentUser.user_id;

  useEffect(() => {
    if (open && user) {
      setFormData({
        name: user.name || '',
        phone: user.phone || '',
        email: user.email || '',
        assigned_class: user.assigned_class || '',
        assigned_section: user.assigned_section || '',
        address: user.address || '',
        photo: ''  // Empty by default, will be filled if user uploads new photo
      });
      // Store current photo for display
      setCurrentPhoto(user.photo || null);
    }
  }, [open, user]);

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  // Handle photo file selection and convert to Base64
  const handlePhotoChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Image size should be less than 5MB');
      return;
    }

    try {
      // Convert to Base64
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64String = reader.result; // Includes data:image/xxx;base64,
        setFormData({ ...formData, photo: base64String });
      };
      reader.onerror = () => {
        toast.error('Failed to read image file');
      };
      reader.readAsDataURL(file);
    } catch (error) {
      console.error('Error converting image to Base64:', error);
      toast.error('Failed to process image');
    }
  };

  const handleSave = async () => {
    if (isEditingOtherAdmin) {
      toast.error('Cannot edit another admin');
      return;
    }

    setSaving(true);
    try {
      // Prepare update data - only send photo if a new one was uploaded
      const updateData = { ...formData };
      if (!formData.photo) {
        delete updateData.photo; // Don't send empty photo field
      }

      await axios.put(`${API}/users/${user.user_id}`, updateData);
      // REMOVED: Success toast - modal close is sufficient feedback
      onSuccess();
      onClose();
    } catch (error) {
      toast.error('Failed to update user');
      console.error('Update error:', error);
    } finally {
      setSaving(false);
    }
  };

  if (!user) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold" style={{ fontFamily: 'Space Grotesk' }}>
            Edit User - {user.name}
          </DialogTitle>
        </DialogHeader>

        {isEditingOtherAdmin && (
          <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
            <AlertCircle className="w-5 h-5" />
            <p className="text-sm font-medium">Cannot edit another admin's account</p>
          </div>
        )}

        <div className="space-y-6">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <Label>Name *</Label>
              <Input
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                placeholder="Full name"
                disabled={isEditingOtherAdmin}
              />
            </div>

            <div>
              <Label>Phone</Label>
              <Input
                value={formData.phone}
                onChange={(e) => handleChange('phone', e.target.value)}
                placeholder="Phone number"
                disabled={isEditingOtherAdmin}
              />
            </div>

            <div>
              <Label>Email *</Label>
              <Input
                value={formData.email}
                onChange={(e) => handleChange('email', e.target.value)}
                placeholder="Email address"
                type="email"
                disabled={isEditingOtherAdmin}
              />
            </div>

            {user.role === 'teacher' && (
              <>
                <div>
                  <Label>Assigned Class</Label>
                  <Input
                    value={formData.assigned_class}
                    onChange={(e) => handleChange('assigned_class', e.target.value)}
                    placeholder="e.g., 5"
                    disabled={isEditingOtherAdmin}
                  />
                </div>

                <div>
                  <Label>Assigned Section</Label>
                  <Input
                    value={formData.assigned_section}
                    onChange={(e) => handleChange('assigned_section', e.target.value)}
                    placeholder="e.g., A, B, C"
                    disabled={isEditingOtherAdmin}
                  />
                </div>
              </>
            )}
          </div>

          <div>
            <Label>Address</Label>
            <textarea
              value={formData.address}
              onChange={(e) => handleChange('address', e.target.value)}
              placeholder="Full address"
              rows={3}
              disabled={isEditingOtherAdmin}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
          </div>

          {/* Photo Section */}
          <div className="border-t pt-4">
            <Label>Photo (optional)</Label>
            <div className="mt-2">
              {/* Show current photo or new photo preview */}
              {(formData.photo || currentPhoto) && (
                <div className="mb-3 flex items-center gap-3">
                  <img 
                    src={formData.photo || currentPhoto} 
                    alt="User" 
                    className="w-20 h-20 rounded-full object-cover border-2 border-gray-300"
                  />
                  <span className="text-sm text-gray-600">
                    {formData.photo ? 'New photo selected' : 'Current photo'}
                  </span>
                </div>
              )}
              <Input
                type="file"
                accept="image/*"
                onChange={handlePhotoChange}
                className="cursor-pointer"
                disabled={isEditingOtherAdmin}
              />
              <p className="text-xs text-gray-500 mt-1">Max size: 5MB. Leave empty to keep current photo.</p>
              {formData.photo && (
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, photo: '' })}
                  className="text-sm text-red-600 hover:text-red-700 mt-2"
                  disabled={isEditingOtherAdmin}
                >
                  Remove New Photo
                </button>
              )}
            </div>
          </div>

          <div className="flex gap-3 justify-end">
            <Button variant="outline" onClick={onClose} disabled={saving}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={saving || isEditingOtherAdmin}>
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
