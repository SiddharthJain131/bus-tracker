import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function EditStudentModal({ student, onClose, onSave }) {
  const [formData, setFormData] = useState({
    name: student.name || '',
    phone: student.phone || '',
    class_name: student.class_name || '',
    section: student.section || '',
    parent_id: student.parent_id || '',
    teacher_id: student.teacher_id || '',
    bus_id: student.bus_id || '',
    stop_id: student.stop_id || '',
    emergency_contact: student.emergency_contact || '',
    remarks: student.remarks || '',
  });
  const [loading, setLoading] = useState(false);
  const [users, setUsers] = useState([]);
  const [buses, setBuses] = useState([]);

  useEffect(() => {
    fetchUsers();
    fetchBuses();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to load users:', error);
    }
  };

  const fetchBuses = async () => {
    try {
      const response = await axios.get(`${API}/buses`);
      setBuses(response.data);
    } catch (error) {
      console.error('Failed to load buses:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.put(`${API}/students/${student.student_id}`, formData);
      toast.success('Student updated successfully');
      onSave();
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update student');
    } finally {
      setLoading(false);
    }
  };

  const parents = users.filter((u) => u.role === 'parent');
  const teachers = users.filter((u) => u.role === 'teacher');

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
            Edit Student
          </h2>
          <Button onClick={onClose} variant="ghost" size="sm" className="rounded-full">
            <X className="w-5 h-5" />
          </Button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">Name *</label>
              <Input
                data-testid="edit-student-name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">Phone</label>
              <Input
                data-testid="edit-student-phone"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              />
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">Class</label>
              <Input
                data-testid="edit-student-class"
                placeholder="e.g., 5"
                value={formData.class_name}
                onChange={(e) => setFormData({ ...formData, class_name: e.target.value })}
              />
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">Section</label>
              <Input
                data-testid="edit-student-section"
                placeholder="e.g., A"
                value={formData.section}
                onChange={(e) => setFormData({ ...formData, section: e.target.value })}
              />
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">Parent</label>
              <select
                data-testid="edit-student-parent"
                value={formData.parent_id}
                onChange={(e) => setFormData({ ...formData, parent_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select Parent</option>
                {parents.map((parent) => (
                  <option key={parent.user_id} value={parent.user_id}>
                    {parent.name} ({parent.email})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">Teacher</label>
              <select
                data-testid="edit-student-teacher"
                value={formData.teacher_id}
                onChange={(e) => setFormData({ ...formData, teacher_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select Teacher</option>
                {teachers.map((teacher) => (
                  <option key={teacher.user_id} value={teacher.user_id}>
                    {teacher.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">Bus</label>
              <select
                data-testid="edit-student-bus"
                value={formData.bus_id}
                onChange={(e) => setFormData({ ...formData, bus_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select Bus</option>
                {buses.map((bus) => (
                  <option key={bus.bus_id} value={bus.bus_id}>
                    {bus.bus_number} - {bus.driver_name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">Emergency Contact</label>
              <Input
                data-testid="edit-student-emergency"
                value={formData.emergency_contact}
                onChange={(e) => setFormData({ ...formData, emergency_contact: e.target.value })}
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">Remarks</label>
            <textarea
              data-testid="edit-student-remarks"
              value={formData.remarks}
              onChange={(e) => setFormData({ ...formData, remarks: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows="3"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button data-testid="save-student-button" type="submit" disabled={loading}>
              {loading ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
