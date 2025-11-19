import React, { useState } from 'react';
import axios from 'axios';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { toast } from 'sonner';
import { UserPlus } from 'lucide-react';
import { CLASS_OPTIONS, SECTION_OPTIONS } from '../constants/options';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AddUserModal({ open, onClose, onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [selectedRole, setSelectedRole] = useState('parent');
  
  const [userData, setUserData] = useState({
    name: '',
    email: '',
    password: '',
    phone: '',
    photo: '',  // Base64 encoded photo
    address: '',
    assigned_class: '',
    assigned_section: ''
  });

  const resetForm = () => {
    setUserData({
      name: '',
      email: '',
      password: '',
      phone: '',
      photo: '',  // Base64 encoded photo
      address: '',
      assigned_class: '',
      assigned_section: ''
    });
    setSelectedRole('parent');
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
        setUserData({ ...userData, photo: base64String });
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

  const handleSubmit = async () => {
    // Validation
    if (!userData.name || !userData.email || !userData.password) {
      toast.error('Please fill in all required fields');
      return;
    }

    if (selectedRole === 'teacher' && (!userData.assigned_class || !userData.assigned_section)) {
      toast.error('Please select class and section for teacher');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        ...userData,
        role: selectedRole
      };

      const response = await axios.post(`${API}/users`, payload);

      // Check email status and show appropriate message
      if (response.data.email_sent === false && response.data.email_warning) {
        toast.warning(response.data.email_warning);
      } else if (response.data.email_sent === true) {
        toast.success(`User created successfully! Welcome email sent to ${userData.email}`);
      } else {
        toast.success('User created successfully!');
      }

      onSuccess();
      onClose();
      resetForm();
    } catch (error) {
      console.error('Failed to create user:', error);
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Failed to create user');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold flex items-center gap-2" style={{ fontFamily: 'Space Grotesk' }}>
            <UserPlus className="w-6 h-6 text-violet-600" />
            Add New User
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Role Selection */}
          <div>
            <Label>User Role *</Label>
            <Select value={selectedRole} onValueChange={setSelectedRole}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="parent">Parent</SelectItem>
                <SelectItem value="teacher">Teacher</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Common Fields */}
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Name *</Label>
                <Input
                  value={userData.name}
                  onChange={(e) => setUserData({ ...userData, name: e.target.value })}
                  placeholder="Enter name"
                />
              </div>
              
              <div>
                <Label>Phone *</Label>
                <Input
                  value={userData.phone}
                  onChange={(e) => setUserData({ ...userData, phone: e.target.value })}
                  placeholder="Phone number"
                />
              </div>
            </div>

            <div>
              <Label>Email *</Label>
              <Input
                type="email"
                value={userData.email}
                onChange={(e) => setUserData({ ...userData, email: e.target.value })}
                placeholder="email@example.com"
              />
            </div>

            <div>
              <Label>Password *</Label>
              <Input
                type="password"
                value={userData.password}
                onChange={(e) => setUserData({ ...userData, password: e.target.value })}
                placeholder="Enter password"
              />
            </div>
          </div>

          {/* Role-Specific Fields */}
          {selectedRole === 'parent' && (
            <div className="space-y-4 border-t pt-4">
              <h4 className="font-semibold text-gray-900">Parent Information</h4>
              
              <div>
                <Label>Address</Label>
                <Input
                  value={userData.address}
                  onChange={(e) => setUserData({ ...userData, address: e.target.value })}
                  placeholder="Home address"
                />
              </div>
              
              <div>
                <Label>Photo (optional)</Label>
                <Input
                  type="file"
                  accept="image/*"
                  onChange={handlePhotoChange}
                  className="cursor-pointer"
                />
                <p className="text-xs text-gray-500 mt-1">Max size: 5MB. Supported: JPG, PNG, WebP</p>
                {userData.photo && (
                  <div className="mt-3 flex items-center gap-3">
                    <img 
                      src={userData.photo} 
                      alt="Preview" 
                      className="w-16 h-16 rounded-full object-cover border-2 border-gray-300"
                    />
                    <button
                      type="button"
                      onClick={() => setUserData({ ...userData, photo: '' })}
                      className="text-sm text-red-600 hover:text-red-700"
                    >
                      Remove Photo
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {selectedRole === 'teacher' && (
            <div className="space-y-4 border-t pt-4">
              <h4 className="font-semibold text-gray-900">Teacher Assignment</h4>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Assigned Class *</Label>
                  <Select
                    value={userData.assigned_class}
                    onValueChange={(value) => setUserData({ ...userData, assigned_class: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select class" />
                    </SelectTrigger>
                    <SelectContent>
                      {CLASS_OPTIONS.map(option => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label>Assigned Section *</Label>
                  <Select
                    value={userData.assigned_section}
                    onValueChange={(value) => setUserData({ ...userData, assigned_section: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select section" />
                    </SelectTrigger>
                    <SelectContent>
                      {SECTION_OPTIONS.map(option => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div>
                <Label>Photo (optional)</Label>
                <Input
                  type="file"
                  accept="image/*"
                  onChange={handlePhotoChange}
                  className="cursor-pointer"
                />
                <p className="text-xs text-gray-500 mt-1">Max size: 5MB. Supported: JPG, PNG, WebP</p>
                {userData.photo && (
                  <div className="mt-3 flex items-center gap-3">
                    <img 
                      src={userData.photo} 
                      alt="Preview" 
                      className="w-16 h-16 rounded-full object-cover border-2 border-gray-300"
                    />
                    <button
                      type="button"
                      onClick={() => setUserData({ ...userData, photo: '' })}
                      className="text-sm text-red-600 hover:text-red-700"
                    >
                      Remove Photo
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {selectedRole === 'admin' && (
            <div className="space-y-4 border-t pt-4">
              <h4 className="font-semibold text-gray-900">Admin Information</h4>
              
              <div>
                <Label>Photo (optional)</Label>
                <Input
                  type="file"
                  accept="image/*"
                  onChange={handlePhotoChange}
                  className="cursor-pointer"
                />
                <p className="text-xs text-gray-500 mt-1">Max size: 5MB. Supported: JPG, PNG, WebP</p>
                {userData.photo && (
                  <div className="mt-3 flex items-center gap-3">
                    <img 
                      src={userData.photo} 
                      alt="Preview" 
                      className="w-16 h-16 rounded-full object-cover border-2 border-gray-300"
                    />
                    <button
                      type="button"
                      onClick={() => setUserData({ ...userData, photo: '' })}
                      className="text-sm text-red-600 hover:text-red-700"
                    >
                      Remove Photo
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <Button variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button 
              onClick={handleSubmit} 
              disabled={loading}
              className="bg-violet-600 hover:bg-violet-700"
            >
              {loading ? 'Creating...' : `Create ${selectedRole.charAt(0).toUpperCase() + selectedRole.slice(1)}`}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
