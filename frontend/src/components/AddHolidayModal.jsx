import React from 'react';
import axios from 'axios';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Calendar } from 'lucide-react';
import { API_ENDPOINTS } from '../config/api';
import { useModalForm } from '../hooks/useModalForm';

const initialFormData = {
  name: '',
  date: '',
  description: ''
};

export default function AddHolidayModal({ open, onClose, onSuccess }) {
  const {
    formData,
    loading,
    updateField,
    handleSubmit,
    handleClose,
  } = useModalForm(
    initialFormData,
    async (data) => {
      const response = await axios.post(API_ENDPOINTS.holidays.create(), data);
      return response.data;
    },
    () => {
      if (onSuccess) onSuccess();
    },
    onClose
  );

  const onSubmit = (e) => {
    handleSubmit(e, ['name', 'date']); // Validate required fields
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Space Grotesk' }}>
            <Calendar className="w-5 h-5 text-blue-600" />
            Add New Holiday
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={onSubmit} className="space-y-4">
          {/* Holiday Title */}
          <div className="space-y-2">
            <Label htmlFor="name">
              Holiday Title <span className="text-red-500">*</span>
            </Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => updateField('name', e.target.value)}
              placeholder="e.g., Independence Day"
              required
            />
          </div>

          {/* Date */}
          <div className="space-y-2">
            <Label htmlFor="date">
              Date <span className="text-red-500">*</span>
            </Label>
            <Input
              id="date"
              type="date"
              value={formData.date}
              onChange={(e) => updateField('date', e.target.value)}
              required
            />
          </div>

          {/* Description (Optional) */}
          <div className="space-y-2">
            <Label htmlFor="description">
              Description <span className="text-gray-400 text-sm">(optional)</span>
            </Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => updateField('description', e.target.value)}
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
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {loading ? 'Adding...' : 'Add Holiday'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
