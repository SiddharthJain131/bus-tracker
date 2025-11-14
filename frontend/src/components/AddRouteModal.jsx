import React, { useState } from 'react';
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
import { MapPin, Plus, Trash2 } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AddRouteModal({ open, onClose, onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    route_name: '',
    remarks: ''
  });
  const [stops, setStops] = useState([{
    stop_name: '',
    lat: '',
    lon: '',
    order_index: 0,
    morning_expected_time: '',
    evening_expected_time: ''
  }]);

  const handleAddStop = () => {
    setStops([...stops, {
      stop_name: '',
      lat: '',
      lon: '',
      order_index: stops.length,
      morning_expected_time: '',
      evening_expected_time: ''
    }]);
  };

  const handleRemoveStop = (index) => {
    const newStops = stops.filter((_, i) => i !== index);
    // Re-index
    newStops.forEach((stop, i) => stop.order_index = i);
    setStops(newStops);
  };

  const handleStopChange = (index, field, value) => {
    const newStops = [...stops];
    newStops[index][field] = value;
    setStops(newStops);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.route_name) {
      toast.error('Please enter a route name');
      return;
    }

    if (stops.length === 0) {
      toast.error('Please add at least one stop');
      return;
    }

    // Validate stops
    for (let i = 0; i < stops.length; i++) {
      if (!stops[i].stop_name || !stops[i].lat || !stops[i].lon) {
        toast.error(`Please fill in all fields for stop ${i + 1}`);
        return;
      }
    }

    setLoading(true);
    try {
      // First create stops
      const createdStops = [];
      for (const stop of stops) {
        const stopResponse = await axios.post(`${API}/stops`, {
          stop_name: stop.stop_name,
          lat: parseFloat(stop.lat),
          lon: parseFloat(stop.lon),
          order_index: stop.order_index
        });
        createdStops.push(stopResponse.data);
      }

      // Create route with stop IDs
      const map_path = createdStops.map(s => ({ lat: s.lat, lon: s.lon }));
      const stop_ids = createdStops.map(s => s.stop_id);

      await axios.post(`${API}/routes`, {
        route_name: formData.route_name,
        stop_ids,
        map_path,
        remarks: formData.remarks || null
      });

      toast.success(`Route "${formData.route_name}" created successfully with ${stops.length} stops!`);
      onSuccess();
      handleClose();
    } catch (error) {
      console.error('Create route error:', error);
      toast.error(error.response?.data?.detail || 'Failed to create route');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({
      route_name: '',
      remarks: ''
    });
    setStops([{
      stop_name: '',
      lat: '',
      lon: '',
      order_index: 0
    }]);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-indigo-600 rounded-full flex items-center justify-center">
              <MapPin className="w-6 h-6 text-white" />
            </div>
            <DialogTitle className="text-2xl font-bold">Add New Route</DialogTitle>
          </div>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
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
              rows="2"
              placeholder="Any additional notes..."
              value={formData.remarks}
              onChange={(e) => setFormData({ ...formData, remarks: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500"
            />
          </div>

          <div className="border-t pt-4">
            <div className="flex justify-between items-center mb-3">
              <Label className="text-lg font-semibold">Stops ({stops.length})</Label>
              <Button
                type="button"
                onClick={handleAddStop}
                size="sm"
                className="bg-blue-500 hover:bg-blue-600 text-white"
              >
                <Plus className="w-4 h-4 mr-1" />
                Add Stop
              </Button>
            </div>

            <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2">
              {stops.map((stop, index) => (
                <div key={index} className="border rounded-lg p-3 bg-gray-50">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-semibold text-sm text-gray-700">Stop {index + 1}</span>
                    {stops.length > 1 && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemoveStop(index)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Input
                      placeholder="Stop name"
                      value={stop.stop_name}
                      onChange={(e) => handleStopChange(index, 'stop_name', e.target.value)}
                      required
                    />
                    <div className="grid grid-cols-2 gap-2">
                      <Input
                        type="number"
                        step="any"
                        placeholder="Latitude"
                        value={stop.lat}
                        onChange={(e) => handleStopChange(index, 'lat', e.target.value)}
                        required
                      />
                      <Input
                        type="number"
                        step="any"
                        placeholder="Longitude"
                        value={stop.lon}
                        onChange={(e) => handleStopChange(index, 'lon', e.target.value)}
                        required
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="text-xs text-gray-600 block mb-1">Morning Expected Time</label>
                        <Input
                          type="time"
                          placeholder="HH:MM"
                          value={stop.morning_expected_time || ''}
                          onChange={(e) => handleStopChange(index, 'morning_expected_time', e.target.value)}
                          className="text-sm"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-gray-600 block mb-1">Evening Expected Time</label>
                        <Input
                          type="time"
                          placeholder="HH:MM"
                          value={stop.evening_expected_time || ''}
                          onChange={(e) => handleStopChange(index, 'evening_expected_time', e.target.value)}
                          className="text-sm"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t">
            <Button type="button" variant="outline" onClick={handleClose} disabled={loading}>
              Cancel
            </Button>
            <Button 
              type="submit" 
              disabled={loading}
              className="bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white"
            >
              {loading ? 'Creating...' : 'Create Route'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
