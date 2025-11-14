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
import { MapPin, Plus, Trash2, MoveUp, MoveDown } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function EditRouteModal({ route, open, onClose, onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    route_name: '',
    remarks: ''
  });
  const [stops, setStops] = useState([]);
  const [originalStops, setOriginalStops] = useState([]);

  useEffect(() => {
    if (open && route) {
      setFormData({
        route_name: route.route_name || '',
        remarks: route.remarks || ''
      });
      
      // Fetch stops for this route
      fetchRouteStops();
    }
  }, [open, route]);

  const fetchRouteStops = async () => {
    if (!route?.route_id) return;
    
    try {
      const response = await axios.get(`${API}/routes/${route.route_id}`);
      const routeData = response.data;
      
      if (routeData.stops && routeData.stops.length > 0) {
        const sortedStops = routeData.stops.sort((a, b) => a.order_index - b.order_index);
        setStops(sortedStops.map(s => ({
          stop_id: s.stop_id || null,
          stop_name: s.stop_name,
          lat: s.lat.toString(),
          lon: s.lon.toString(),
          order_index: s.order_index,
          isNew: false
        })));
        setOriginalStops(JSON.parse(JSON.stringify(sortedStops.map(s => s.stop_id))));
      } else {
        setStops([]);
        setOriginalStops([]);
      }
    } catch (error) {
      console.error('Failed to fetch route stops:', error);
      toast.error('Failed to load route stops');
    }
  };

  const handleAddStop = () => {
    setStops([...stops, {
      stop_id: null,
      stop_name: '',
      lat: '',
      lon: '',
      order_index: stops.length,
      isNew: true
    }]);
  };

  const handleRemoveStop = (index) => {
    if (stops.length === 1) {
      toast.error('Route must have at least one stop');
      return;
    }
    
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

  const handleMoveStop = (index, direction) => {
    if (direction === 'up' && index === 0) return;
    if (direction === 'down' && index === stops.length - 1) return;
    
    const newStops = [...stops];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    
    // Swap stops
    [newStops[index], newStops[targetIndex]] = [newStops[targetIndex], newStops[index]];
    
    // Re-index
    newStops.forEach((stop, i) => stop.order_index = i);
    setStops(newStops);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.route_name) {
      toast.error('Please enter a route name');
      return;
    }

    if (stops.length === 0) {
      toast.error('Route must have at least one stop');
      return;
    }

    // Validate stops
    for (let i = 0; i < stops.length; i++) {
      if (!stops[i].stop_name || !stops[i].lat || !stops[i].lon) {
        toast.error(`Please fill in all fields for stop ${i + 1}`);
        return;
      }
      
      // Validate coordinates
      const lat = parseFloat(stops[i].lat);
      const lon = parseFloat(stops[i].lon);
      if (isNaN(lat) || isNaN(lon)) {
        toast.error(`Invalid coordinates for stop ${i + 1}`);
        return;
      }
    }

    setLoading(true);
    try {
      // Determine which stops are new, modified, or deleted
      const stopsToDelete = originalStops.filter(id => 
        !stops.find(s => s.stop_id === id)
      );
      
      // Create or update stops
      const processedStops = [];
      for (const stop of stops) {
        if (stop.isNew || !stop.stop_id) {
          // Create new stop
          const stopResponse = await axios.post(`${API}/stops`, {
            stop_name: stop.stop_name,
            lat: parseFloat(stop.lat),
            lon: parseFloat(stop.lon),
            order_index: stop.order_index
          });
          processedStops.push(stopResponse.data);
        } else {
          // Update existing stop
          const stopResponse = await axios.put(`${API}/stops/${stop.stop_id}`, {
            stop_id: stop.stop_id,
            stop_name: stop.stop_name,
            lat: parseFloat(stop.lat),
            lon: parseFloat(stop.lon),
            order_index: stop.order_index
          });
          processedStops.push(stopResponse.data);
        }
      }

      // Delete removed stops (if they're not used elsewhere)
      for (const stopId of stopsToDelete) {
        try {
          // Check if stop is used by students
          const studentsResponse = await axios.get(`${API}/students?stop_id=${stopId}`);
          const students = studentsResponse.data;
          
          if (students.length > 0) {
            // Move students to the first stop of the route
            const firstStopId = processedStops[0].stop_id;
            for (const student of students) {
              await axios.put(`${API}/students/${student.student_id}`, {
                ...student,
                stop_id: firstStopId
              });
            }
            toast.info(`Moved ${students.length} student(s) from deleted stop to first stop`);
          }
          
          // Now delete the stop
          await axios.delete(`${API}/stops/${stopId}`);
        } catch (error) {
          console.error(`Failed to handle stop deletion: ${stopId}`, error);
          // Continue with route update even if stop deletion fails
        }
      }

      // Update route with new stop IDs
      const map_path = processedStops.map(s => ({ lat: s.lat, lon: s.lon }));
      const stop_ids = processedStops.map(s => s.stop_id);

      await axios.put(`${API}/routes/${route.route_id}`, {
        route_id: route.route_id,
        route_name: formData.route_name,
        stop_ids,
        map_path,
        remarks: formData.remarks || null
      });

      toast.success(`Route "${formData.route_name}" updated successfully!`);
      onSuccess();
      handleClose();
    } catch (error) {
      console.error('Update route error:', error);
      toast.error(error.response?.data?.detail || 'Failed to update route');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setStops([]);
    setOriginalStops([]);
    onClose();
  };

  if (!route) return null;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-yellow-400 to-amber-600 rounded-full flex items-center justify-center">
              <MapPin className="w-6 h-6 text-white" />
            </div>
            <DialogTitle className="text-2xl font-bold">Edit Route</DialogTitle>
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
                className="bg-yellow-500 hover:bg-yellow-600 text-white"
              >
                <Plus className="w-4 h-4 mr-1" />
                Add Stop
              </Button>
            </div>

            {stops.length === 0 ? (
              <div className="text-center py-8 text-gray-500 border rounded-lg bg-gray-50">
                No stops yet. Click "Add Stop" to begin.
              </div>
            ) : (
              <div className="space-y-3 max-h-[350px] overflow-y-auto pr-2">
                {stops.map((stop, index) => (
                  <div key={index} className="border rounded-lg p-3 bg-gray-50">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-semibold text-sm text-gray-700">Stop {index + 1}</span>
                      <div className="flex items-center gap-1">
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => handleMoveStop(index, 'up')}
                          disabled={index === 0}
                          className="text-gray-600 hover:text-gray-700 hover:bg-gray-100 p-1 h-7 w-7"
                          title="Move up"
                        >
                          <MoveUp className="w-4 h-4" />
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => handleMoveStop(index, 'down')}
                          disabled={index === stops.length - 1}
                          className="text-gray-600 hover:text-gray-700 hover:bg-gray-100 p-1 h-7 w-7"
                          title="Move down"
                        >
                          <MoveDown className="w-4 h-4" />
                        </Button>
                        {stops.length > 1 && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemoveStop(index)}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50 p-1 h-7 w-7"
                            title="Remove stop"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
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
            )}
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t">
            <Button type="button" variant="outline" onClick={handleClose} disabled={loading}>
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
