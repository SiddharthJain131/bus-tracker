import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function EditStudentModalEnhanced({ student, open, onClose, onSuccess, adminName }) {
  const [formData, setFormData] = useState({
    name: '',
    roll_number: '',
    phone: '',
    class_section: '',  // Combined field for display
    class_name: '',
    section: '',
    parent_id: '',
    parent_search: '',  // For searchable parent input
    bus_number: '',
    stop_id: '',
    emergency_contact: '',
    remarks: ''
  });
  const [saving, setSaving] = useState(false);
  const [parents, setParents] = useState([]);
  const [buses, setBuses] = useState([]);
  const [stops, setStops] = useState([]);
  const [loadingStops, setLoadingStops] = useState(false);
  const [classSectionSuggestions, setClassSectionSuggestions] = useState([]);

  useEffect(() => {
    if (open && student) {
      // Combine class and section for display
      const classNum = student.class_name ? student.class_name.replace(/Grade|Class/gi, '').trim() : '';
      const combinedClassSection = classNum && student.section ? `${classNum}${student.section}` : '';
      
      setFormData({
        name: student.name || '',
        roll_number: student.roll_number || '',
        phone: student.phone || '',
        class_section: combinedClassSection,
        class_name: student.class_name || '',
        section: student.section || '',
        parent_id: student.parent_id || '',
        parent_search: '',  // Will be set after fetching parent details
        bus_number: student.bus_number || '',
        stop_id: student.stop_id || '',
        emergency_contact: student.emergency_contact || '',
        remarks: student.remarks || ''
      });
      fetchDropdownData();
      // Fetch stops if bus is already selected
      if (student.bus_number) {
        fetchStopsForBus(student.bus_number);
      }
    }
  }, [open, student]);

  // Fetch stops when bus changes
  useEffect(() => {
    if (formData.bus_number && open) {
      fetchStopsForBus(formData.bus_number);
    } else {
      setStops([]);
    }
  }, [formData.bus_number, open]);

  const fetchDropdownData = async () => {
    try {
      const [usersRes, busesRes, classSectionsRes] = await Promise.all([
        axios.get(`${API}/users`),
        axios.get(`${API}/buses`),
        axios.get(`${API}/students/class-sections`)
      ]);
      
      const parentsList = usersRes.data.filter(u => u.role === 'parent');
      setParents(parentsList);
      setBuses(busesRes.data);
      setClassSectionSuggestions(classSectionsRes.data || []);
      
      // Set parent search field with current parent's name and email
      if (student && student.parent_id) {
        const currentParent = parentsList.find(p => p.user_id === student.parent_id);
        if (currentParent) {
          setFormData(prev => ({
            ...prev,
            parent_search: `${currentParent.name} (${currentParent.email})`
          }));
        }
      }
    } catch (error) {
      console.error('Failed to load dropdown data:', error);
    }
  };

  const fetchStopsForBus = async (busId) => {
    setLoadingStops(true);
    try {
      const response = await axios.get(`${API}/buses/${busId}/stops`);
      setStops(response.data);
      if (response.data.length === 0) {
        toast.info('No stops available for this bus route');
      }
    } catch (error) {
      console.error('Failed to load stops:', error);
      toast.error('Failed to load stops for selected bus');
      setStops([]);
    } finally {
      setLoadingStops(false);
    }
  };

  // Parse class-section input (e.g., "5A", "5-A", "Class 5 A", "Grade 5 A")
  const parseClassSection = (input) => {
    if (!input) return { class_name: '', section: '' };
    
    // Remove common prefixes
    const cleaned = input.replace(/^(class|grade)\s*/i, '').trim();
    
    // Match patterns like "5A", "5-A", "5 A"
    const match = cleaned.match(/^(\d+)\s*[-\s]*([A-Za-z])$/i);
    
    if (match) {
      return {
        class_name: match[1],  // Just the number
        section: match[2].toUpperCase()
      };
    }
    
    return { class_name: '', section: '' };
  };

  const handleChange = (field, value) => {
    setFormData(prev => {
      // If bus changes, reset stop selection
      if (field === 'bus_number') {
        return { ...prev, [field]: value, stop_id: '' };
      }
      
      // If class-section changes, parse it
      if (field === 'class_section') {
        const parsed = parseClassSection(value);
        return {
          ...prev,
          class_section: value,
          class_name: parsed.class_name,
          section: parsed.section
        };
      }
      
      // If parent search changes, find matching parent
      if (field === 'parent_search') {
        // Try to find parent by matching the search string
        const matchedParent = parents.find(p => 
          `${p.name} (${p.email})` === value || 
          p.name.toLowerCase().includes(value.toLowerCase()) ||
          p.email.toLowerCase().includes(value.toLowerCase())
        );
        return {
          ...prev,
          parent_search: value,
          parent_id: matchedParent ? matchedParent.user_id : prev.parent_id
        };
      }
      
      return { ...prev, [field]: value };
    });
  };

  const handleSave = async () => {
    // Validation
    if (!formData.name || !formData.roll_number || !formData.class_name || 
        !formData.section || !formData.bus_number || !formData.stop_id) {
      toast.error('Please fill in all required fields (including Stop)');
      return;
    }

    setSaving(true);
    try {
      // Track changed fields
      const changedFields = [];
      Object.keys(formData).forEach(key => {
        if (formData[key] !== (student[key] || '')) {
          changedFields.push(`${key}: ${student[key] || 'N/A'} → ${formData[key] || 'N/A'}`);
        }
      });

      const response = await axios.put(`${API}/students/${student.student_id}`, formData);
      
      // Check for capacity warning
      if (response.data?.capacity_warning) {
        toast.warning(response.data.capacity_warning, { duration: 6000 });
      }
      
      toast.success('Student updated successfully! Email notification sent to parent.');
      onSuccess();
      onClose();
    } catch (error) {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Failed to update student');
      }
      console.error('Update error:', error);
    } finally {
      setSaving(false);
    }
  };

  if (!student) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold" style={{ fontFamily: 'Space Grotesk' }}>
            Edit Student - {student.name}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <Label>Name *</Label>
              <Input
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                placeholder="Student name"
              />
            </div>

            <div>
              <Label>Roll Number *</Label>
              <Input
                value={formData.roll_number}
                onChange={(e) => handleChange('roll_number', e.target.value)}
                placeholder="Roll number"
              />
            </div>

            <div>
              <Label>Phone</Label>
              <Input
                value={formData.phone}
                onChange={(e) => handleChange('phone', e.target.value)}
                placeholder="Phone number"
              />
            </div>

            <div className="md:col-span-2">
              <Label>Class and Section *</Label>
              <Input
                value={formData.class_section}
                onChange={(e) => handleChange('class_section', e.target.value)}
                placeholder="Enter Class and Section (e.g., 5A)"
                list="edit-class-section-suggestions"
              />
              <datalist id="edit-class-section-suggestions">
                {classSectionSuggestions.map((suggestion, idx) => (
                  <option key={idx} value={suggestion} />
                ))}
              </datalist>
              {formData.class_section && formData.class_name && formData.section && (
                <p className="text-xs text-green-600 mt-1">
                  ✓ Parsed as: Class {formData.class_name}, Section {formData.section}
                </p>
              )}
              {formData.class_section && (!formData.class_name || !formData.section) && (
                <p className="text-xs text-amber-600 mt-1">
                  ⚠️ Please use format like "5A" or "5-A"
                </p>
              )}
            </div>

            <div className="md:col-span-2">
              <Label>Parent *</Label>
              <Input
                value={formData.parent_search}
                onChange={(e) => handleChange('parent_search', e.target.value)}
                placeholder="Search parent by name or email"
                list="parent-suggestions"
              />
              <datalist id="parent-suggestions">
                {parents.map(p => (
                  <option key={p.user_id} value={`${p.name} (${p.email})`} />
                ))}
              </datalist>
              {formData.parent_id && (
                <p className="text-xs text-green-600 mt-1">
                  ✓ Parent selected: {parents.find(p => p.user_id === formData.parent_id)?.name}
                </p>
              )}
            </div>

            <div>
              <Label>Bus *</Label>
              <select
                value={formData.bus_number}
                onChange={(e) => handleChange('bus_number', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select Bus</option>
                {buses.map(b => (
                  <option key={b.bus_number} value={b.bus_number}>Bus {b.bus_number}</option>
                ))}
              </select>
            </div>

            <div>
              <Label>Stop *</Label>
              <select
                value={formData.stop_id}
                onChange={(e) => handleChange('stop_id', e.target.value)}
                disabled={!formData.bus_number || loadingStops}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              >
                <option value="">
                  {!formData.bus_number 
                    ? "Select bus first" 
                    : loadingStops 
                    ? "Loading stops..." 
                    : "Select stop"}
                </option>
                {stops.map(s => (
                  <option key={s.stop_id} value={s.stop_id}>{s.stop_name}</option>
                ))}
              </select>
              {formData.bus_number && stops.length === 0 && !loadingStops && (
                <p className="text-xs text-amber-600 mt-1">
                  ⚠️ Selected bus has no route stops configured
                </p>
              )}
            </div>

            <div>
              <Label>Emergency Contact</Label>
              <Input
                value={formData.emergency_contact}
                onChange={(e) => handleChange('emergency_contact', e.target.value)}
                placeholder="Emergency phone"
              />
            </div>
          </div>

          <div>
            <Label>Remarks</Label>
            <textarea
              value={formData.remarks}
              onChange={(e) => handleChange('remarks', e.target.value)}
              placeholder="Additional notes"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex gap-3 justify-end">
            <Button variant="outline" onClick={onClose} disabled={saving}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
