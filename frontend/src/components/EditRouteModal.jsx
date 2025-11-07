import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { toast } from 'sonner';
import { MapPin } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function EditRouteModal({ route, open, onClose, onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    route_name: '',
    remarks: ''
  });

  useEffect(() => {
    if (open && route) {
      setFormData({
        route_name: route.route_name || '',
        remarks: route.remarks || ''
      });
    }
  }, [open, route]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.route_name) {
      toast.error('Please enter a route name');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        route_id: route.route_id,
        route_name: formData.route_name,
        stop_ids: route.stop_ids || [],
        map_path: route.map_path || [],
        remarks: formData.remarks || null
      };

      await axios.put(`${API}/routes/${route.route_id}`, payload);
      toast.success(`Route "${formData.route_name}" updated successfully!`);
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Update route error:', error);
      toast.error(error.response?.data?.detail || 'Failed to update route');
    } finally {
      setLoading(false);
    }
  };

  if (!route) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-yellow-400 to-amber-600 rounded-full flex items-center justify-center">
              <MapPin className="w-6 h-6 text-white" />
            </div>
            <DialogTitle className="text-2xl font-bold">Edit Route</DialogTitle>
          </div>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
            <p className="text-sm text-blue-800">
              <strong>Note:</strong> To modify stops, please use the Route Details view. This form only updates route name and remarks.
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="route_name">Route Name *</Label>
            <Input
              id="route_name"
              placeholder="e.g., Route E - Downtown"
              value={formData.route_name}
              onChange={(e) => setFormData({ ...formData, route_name: e.target.value })}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="remarks">Remarks</Label>
            <textarea
              id="remarks"
              rows="3"
              placeholder="Any additional notes..."
              value={formData.remarks}
              onChange={(e) => setFormData({ ...formData, remarks: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="outline" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button 
              type="submit" 
              disabled={loading}
              className="bg-gradient-to-r from-yellow-500 to-amber-600 hover:from-yellow-600 hover:to-amber-700 text-white"
            >
              {loading ? 'Updating...' : 'Update Route'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
