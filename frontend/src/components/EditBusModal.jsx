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
import { Bus as BusIcon } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function EditBusModal({ bus, open, onClose, onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [routes, setRoutes] = useState([]);
  const [formData, setFormData] = useState({
    bus_number: '',
    driver_name: '',
    driver_phone: '',
    route_id: '',
    capacity: '',
    remarks: ''
  });

  useEffect(() => {
    if (open && bus) {
      setFormData({
        bus_number: bus.bus_number || '',
        driver_name: bus.driver_name || '',
        driver_phone: bus.driver_phone || '',
        route_id: bus.route_id || '',
        capacity: bus.capacity || '',
        remarks: bus.remarks || ''
      });
      fetchRoutes();
    }
  }, [open, bus]);

  const fetchRoutes = async () => {
    try {
      const response = await axios.get(`${API}/routes`);
      setRoutes(response.data);
    } catch (error) {
      console.error('Failed to fetch routes:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.bus_number || !formData.driver_name || !formData.driver_phone || !formData.capacity) {
      toast.error('Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        bus_number: bus.bus_number,
        ...formData,
        capacity: parseInt(formData.capacity),
        route_id: formData.route_id || null
      };

      await axios.put(`${API}/buses/${bus.bus_number}`, payload);
      // REMOVED: Success toast - modal close is sufficient feedback
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Update bus error:', error);
      toast.error(error.response?.data?.detail || 'Failed to update bus');
    } finally {
      setLoading(false);
    }
  };

  if (!bus) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-yellow-400 to-orange-600 rounded-full flex items-center justify-center">
              <BusIcon className="w-6 h-6 text-white" />
            </div>
            <DialogTitle className="text-2xl font-bold">Edit Bus</DialogTitle>
          </div>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          <div className="space-y-2">
            <Label htmlFor="bus_number">Bus Number *</Label>
            <Input
              id="bus_number"
              placeholder="e.g., BUS-005"
              value={formData.bus_number}
              onChange={(e) => setFormData({ ...formData, bus_number: e.target.value })}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="driver_name">Driver Name *</Label>
            <Input
              id="driver_name"
              placeholder="Enter driver's full name"
              value={formData.driver_name}
              onChange={(e) => setFormData({ ...formData, driver_name: e.target.value })}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="driver_phone">Driver Phone *</Label>
            <Input
              id="driver_phone"
              type="tel"
              placeholder="+1-555-0123"
              value={formData.driver_phone}
              onChange={(e) => setFormData({ ...formData, driver_phone: e.target.value })}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="route_id">Assigned Route</Label>
            <select
              id="route_id"
              value={formData.route_id}
              onChange={(e) => setFormData({ ...formData, route_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500"
            >
              <option value="">No route assigned</option>
              {routes.map(route => (
                <option key={route.route_id} value={route.route_id}>
                  {route.route_name}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="capacity">Capacity (Students) *</Label>
            <Input
              id="capacity"
              type="number"
              min="1"
              placeholder="e.g., 40"
              value={formData.capacity}
              onChange={(e) => setFormData({ ...formData, capacity: e.target.value })}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="remarks">Remarks</Label>
            <textarea
              id="remarks"
              rows="2"
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
              className="bg-gradient-to-r from-yellow-500 to-orange-600 hover:from-yellow-600 hover:to-orange-700 text-white"
            >
              {loading ? 'Updating...' : 'Update Bus'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
