import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Calendar } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function EditHolidayModal({ holiday, open, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    name: '',
    date: '',
    description: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (holiday) {
      setFormData({
        name: holiday.name || '',
        date: holiday.date || '',
        description: holiday.description || ''
      });
    }
  }, [holiday]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name || !formData.date) {
      toast.error('Please fill in all required fields');
      return;
    }

    setIsSubmitting(true);
    try {
      await axios.put(`${API}/admin/holidays/${holiday.holiday_id}`, formData);
      // REMOVED: Success toast - modal close is sufficient feedback
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Error updating holiday:', error);
      toast.error(error.response?.data?.detail || 'Failed to update holiday');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setFormData({ name: '', date: '', description: '' });
    onClose();
  };

  if (!holiday) return null;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Space Grotesk' }}>
            <Calendar className="w-5 h-5 text-blue-600" />
            Edit Holiday
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Holiday Title */}
          <div className="space-y-2">
            <Label htmlFor="edit-name">
              Holiday Title <span className="text-red-500">*</span>
            </Label>
            <Input
              id="edit-name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Independence Day"
              required
            />
          </div>

          {/* Date */}
          <div className="space-y-2">
            <Label htmlFor="edit-date">
              Date <span className="text-red-500">*</span>
            </Label>
            <Input
              id="edit-date"
              type="date"
              value={formData.date}
              onChange={(e) => setFormData({ ...formData, date: e.target.value })}
              required
            />
          </div>

          {/* Description (Optional) */}
          <div className="space-y-2">
            <Label htmlFor="edit-description">
              Description <span className="text-gray-400 text-sm">(optional)</span>
            </Label>
            <Textarea
              id="edit-description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="e.g., National holiday celebrating independence"
              rows={3}
              className="resize-none"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-2 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {isSubmitting ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
