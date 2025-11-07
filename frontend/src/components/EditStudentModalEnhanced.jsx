import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { toast } from 'sonner';
import { CLASS_OPTIONS, SECTION_OPTIONS } from '../constants/options';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function EditStudentModalEnhanced({ student, open, onClose, onSuccess, adminName }) {
  const [formData, setFormData] = useState({
    name: '',
    roll_number: '',
    phone: '',
    class_name: '',
    section: '',
    parent_id: '',
    teacher_id: '',
    bus_id: '',
    stop_id: '',
    emergency_contact: '',
    remarks: ''
  });
  const [saving, setSaving] = useState(false);
  const [parents, setParents] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [buses, setBuses] = useState([]);

  useEffect(() => {
    if (open && student) {
      setFormData({
        name: student.name || '',
        roll_number: student.roll_number || '',
        phone: student.phone || '',
        class_name: student.class_name || '',
        section: student.section || '',
        parent_id: student.parent_id || '',
        teacher_id: student.teacher_id || '',
        bus_id: student.bus_id || '',
        stop_id: student.stop_id || '',
        emergency_contact: student.emergency_contact || '',
        remarks: student.remarks || ''
      });
      fetchDropdownData();
    }
  }, [open, student]);

  const fetchDropdownData = async () => {
    try {
      const [usersRes, busesRes] = await Promise.all([
        axios.get(`${API}/users`),
        axios.get(`${API}/buses`)
      ]);
      
      setParents(usersRes.data.filter(u => u.role === 'parent'));
      setTeachers(usersRes.data.filter(u => u.role === 'teacher'));
      setBuses(busesRes.data);
    } catch (error) {
      console.error('Failed to load dropdown data:', error);
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // Track changed fields
      const changedFields = [];
      Object.keys(formData).forEach(key => {
        if (formData[key] !== (student[key] || '')) {
          changedFields.push(`${key}: ${student[key] || 'N/A'} → ${formData[key] || 'N/A'}`);
        }
      });

      await axios.put(`${API}/students/${student.student_id}`, formData);
      
      toast.success('Student updated successfully! Email notification sent to parent.');
      onSuccess();
      onClose();
    } catch (error) {
      toast.error('Failed to update student');
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
              <Label>Roll Number</Label>
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

            <div>
              <Label>Class</Label>
              <Select
                value={formData.class_name}
                onValueChange={(value) => handleChange('class_name', value)}
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
              <Label>Section</Label>
              <Select
                value={formData.section}
                onValueChange={(value) => handleChange('section', value)}
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

            <div>
              <Label>Parent</Label>
              <select
                value={formData.parent_id}
                onChange={(e) => handleChange('parent_id', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select Parent</option>
                {parents.map(p => (
                  <option key={p.user_id} value={p.user_id}>{p.name} ({p.email})</option>
                ))}
              </select>
            </div>

            <div>
              <Label>Teacher</Label>
              <select
                value={formData.teacher_id}
                onChange={(e) => handleChange('teacher_id', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select Teacher</option>
                {teachers.map(t => (
                  <option key={t.user_id} value={t.user_id}>{t.name} ({t.email})</option>
                ))}
              </select>
            </div>

            <div>
              <Label>Bus</Label>
              <select
                value={formData.bus_id}
                onChange={(e) => handleChange('bus_id', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select Bus</option>
                {buses.map(b => (
                  <option key={b.bus_id} value={b.bus_id}>Bus {b.bus_number}</option>
                ))}
              </select>
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
