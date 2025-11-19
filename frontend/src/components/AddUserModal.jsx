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
    photo: '',
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
      photo: '',
      address: '',
      assigned_class: '',
      assigned_section: ''
    });
    setSelectedRole('parent');
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

      await axios.post(`${API}/users`, payload);

      // REMOVED: Success toast - modal close is sufficient feedback
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
                <Label>Photo URL (optional)</Label>
                <Input
                  value={userData.photo}
                  onChange={(e) => setUserData({ ...userData, photo: e.target.value })}
                  placeholder="https://example.com/photo.jpg"
                />
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
                <Label>Photo URL (optional)</Label>
                <Input
                  value={userData.photo}
                  onChange={(e) => setUserData({ ...userData, photo: e.target.value })}
                  placeholder="https://example.com/photo.jpg"
                />
              </div>
            </div>
          )}

          {selectedRole === 'admin' && (
            <div className="space-y-4 border-t pt-4">
              <h4 className="font-semibold text-gray-900">Admin Information</h4>
              
              <div>
                <Label>Photo URL (optional)</Label>
                <Input
                  value={userData.photo}
                  onChange={(e) => setUserData({ ...userData, photo: e.target.value })}
                  placeholder="https://example.com/photo.jpg"
                />
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
