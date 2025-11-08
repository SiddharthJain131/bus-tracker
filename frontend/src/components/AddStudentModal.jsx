import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { toast } from 'sonner';
import { UserPlus, ArrowRight, ArrowLeft, CheckCircle } from 'lucide-react';
import { CLASS_OPTIONS, SECTION_OPTIONS } from '../constants/options';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AddStudentModal({ open, onClose, onSuccess }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  
  // Dropdown data
  const [buses, setBuses] = useState([]);
  const [stops, setStops] = useState([]);
  const [loadingStops, setLoadingStops] = useState(false);
  
  // Step 1: Student basic info
  const [studentData, setStudentData] = useState({
    name: '',
    roll_number: '',
    class_name: '',
    section: '',
    bus_id: '',
    stop_id: '',
    phone: '',
    emergency_contact: '',
    remarks: ''
  });
  
  // Step 2: Parent info
  const [parentData, setParentData] = useState({
    name: '',
    phone: '',
    email: '',
    photo: '',
    address: ''
  });

  useEffect(() => {
    if (open) {
      fetchDropdownData();
      resetForm();
    }
  }, [open]);

  // Fetch stops when bus is selected
  useEffect(() => {
    if (studentData.bus_id) {
      fetchStopsForBus(studentData.bus_id);
    } else {
      setStops([]);
      setStudentData(prev => ({ ...prev, stop_id: '' }));
    }
  }, [studentData.bus_id]);

  const fetchDropdownData = async () => {
    try {
      const busesRes = await axios.get(`${API}/buses`);
      setBuses(busesRes.data);
    } catch (error) {
      console.error('Failed to load dropdown data:', error);
      toast.error('Failed to load form data');
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

  const resetForm = () => {
    setStep(1);
    setStudentData({
      name: '',
      roll_number: '',
      class_name: '',
      section: '',
      bus_id: '',
      stop_id: '',
      phone: '',
      emergency_contact: '',
      remarks: ''
    });
    setParentData({
      name: '',
      phone: '',
      email: '',
      photo: '',
      address: ''
    });
    setStops([]);
  };

  const handleNext = () => {
    // Validate Step 1
    if (step === 1) {
      if (!studentData.name || !studentData.roll_number || !studentData.class_name || 
          !studentData.section || !studentData.bus_id || !studentData.stop_id) {
        toast.error('Please fill in all required fields (including Stop)');
        return;
      }
    }
    
    setStep(step + 1);
  };

  const handleBack = () => {
    setStep(step - 1);
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      // Step 1: Create parent account
      const parentResponse = await axios.post(`${API}/users`, {
        email: parentData.email,
        password: 'parent123', // Default password
        role: 'parent',
        name: parentData.name,
        phone: parentData.phone,
        photo: parentData.photo,
        address: parentData.address
      });

      // Step 2: Create student with parent_id and teacher_id
      const studentPayload = {
        ...studentData,
        parent_id: parentResponse.data.user_id,
        teacher_id: assignedTeacher ? assignedTeacher.user_id : null
      };

      await axios.post(`${API}/students`, studentPayload);

      toast.success('Student and Parent created successfully!');
      onSuccess();
      onClose();
      resetForm();
    } catch (error) {
      console.error('Failed to create student:', error);
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Failed to create student');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold flex items-center gap-2" style={{ fontFamily: 'Space Grotesk' }}>
            <UserPlus className="w-6 h-6 text-violet-600" />
            Add New Student
          </DialogTitle>
        </DialogHeader>

        {/* Step Indicator */}
        <div className="flex items-center justify-center gap-4 mb-6">
          {[1, 2, 3].map((stepNum) => (
            <div key={stepNum} className="flex items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                step >= stepNum 
                  ? 'bg-violet-600 text-white' 
                  : 'bg-gray-200 text-gray-500'
              }`}>
                {stepNum}
              </div>
              {stepNum < 3 && (
                <div className={`w-12 h-1 mx-2 ${
                  step > stepNum ? 'bg-violet-600' : 'bg-gray-200'
                }`}></div>
              )}
            </div>
          ))}
        </div>

        {/* Step 1: Student Basic Info */}
        {step === 1 && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Student Information</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Name *</Label>
                <Input
                  value={studentData.name}
                  onChange={(e) => setStudentData({ ...studentData, name: e.target.value })}
                  placeholder="Enter student name"
                />
              </div>
              
              <div>
                <Label>Roll Number *</Label>
                <Input
                  value={studentData.roll_number}
                  onChange={(e) => setStudentData({ ...studentData, roll_number: e.target.value })}
                  placeholder="Enter roll number"
                />
              </div>
              
              <div>
                <Label>Class *</Label>
                <Select
                  value={studentData.class_name}
                  onValueChange={(value) => setStudentData({ ...studentData, class_name: value })}
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
                <Label>Section *</Label>
                <Select
                  value={studentData.section}
                  onValueChange={(value) => setStudentData({ ...studentData, section: value })}
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
                <Label>Bus *</Label>
                <Select
                  value={studentData.bus_id}
                  onValueChange={(value) => setStudentData({ ...studentData, bus_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select bus" />
                  </SelectTrigger>
                  <SelectContent>
                    {buses.map(bus => (
                      <SelectItem key={bus.bus_id} value={bus.bus_id}>
                        {bus.bus_number}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label>Stop</Label>
                <Select
                  value={studentData.stop_id}
                  onValueChange={(value) => setStudentData({ ...studentData, stop_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select stop" />
                  </SelectTrigger>
                  <SelectContent>
                    {stops.map(stop => (
                      <SelectItem key={stop.stop_id} value={stop.stop_id}>
                        {stop.stop_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label>Phone</Label>
                <Input
                  value={studentData.phone}
                  onChange={(e) => setStudentData({ ...studentData, phone: e.target.value })}
                  placeholder="Student phone"
                />
              </div>
              
              <div>
                <Label>Emergency Contact</Label>
                <Input
                  value={studentData.emergency_contact}
                  onChange={(e) => setStudentData({ ...studentData, emergency_contact: e.target.value })}
                  placeholder="Emergency contact number"
                />
              </div>
            </div>
            
            <div>
              <Label>Remarks</Label>
              <Input
                value={studentData.remarks}
                onChange={(e) => setStudentData({ ...studentData, remarks: e.target.value })}
                placeholder="Any additional notes"
              />
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <Button variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button onClick={handleNext} className="bg-violet-600 hover:bg-violet-700">
                Next <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        )}

        {/* Step 2: Parent Information */}
        {step === 2 && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Parent Information</h3>
            <p className="text-sm text-gray-600">A parent account will be created for this student</p>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Parent Name *</Label>
                <Input
                  value={parentData.name}
                  onChange={(e) => setParentData({ ...parentData, name: e.target.value })}
                  placeholder="Enter parent name"
                />
              </div>
              
              <div>
                <Label>Phone *</Label>
                <Input
                  value={parentData.phone}
                  onChange={(e) => setParentData({ ...parentData, phone: e.target.value })}
                  placeholder="Parent phone number"
                />
              </div>
              
              <div className="col-span-2">
                <Label>Email *</Label>
                <Input
                  type="email"
                  value={parentData.email}
                  onChange={(e) => setParentData({ ...parentData, email: e.target.value })}
                  placeholder="parent@example.com"
                />
                <p className="text-xs text-gray-500 mt-1">Default password will be: parent123</p>
              </div>
              
              <div className="col-span-2">
                <Label>Address</Label>
                <Input
                  value={parentData.address}
                  onChange={(e) => setParentData({ ...parentData, address: e.target.value })}
                  placeholder="Home address"
                />
              </div>
              
              <div className="col-span-2">
                <Label>Photo URL (optional)</Label>
                <Input
                  value={parentData.photo}
                  onChange={(e) => setParentData({ ...parentData, photo: e.target.value })}
                  placeholder="https://example.com/photo.jpg"
                />
              </div>
            </div>

            <div className="flex justify-between gap-3 pt-4">
              <Button variant="outline" onClick={handleBack}>
                <ArrowLeft className="w-4 h-4 mr-2" /> Back
              </Button>
              <div className="flex gap-3">
                <Button variant="outline" onClick={onClose}>
                  Cancel
                </Button>
                <Button onClick={handleNext} className="bg-violet-600 hover:bg-violet-700">
                  Next <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Teacher Assignment */}
        {step === 3 && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Teacher Assignment</h3>
            
            <div className="bg-gradient-to-br from-violet-50 to-purple-50 p-6 rounded-lg">
              <h4 className="font-semibold text-gray-900 mb-3">Assigned Class Teacher</h4>
              
              {assignedTeacher ? (
                <div className="bg-white p-4 rounded-lg border-2 border-violet-200">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-violet-100 rounded-full flex items-center justify-center">
                      <UserPlus className="w-6 h-6 text-violet-600" />
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900">{assignedTeacher.name}</p>
                      <p className="text-sm text-gray-600">{assignedTeacher.email}</p>
                      <p className="text-sm text-gray-600">
                        {studentData.class_name} - {studentData.section}
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
                  <p className="text-sm text-yellow-800">
                    ⚠️ No teacher assigned to {studentData.class_name} - {studentData.section} yet.
                  </p>
                  <p className="text-xs text-yellow-700 mt-1">
                    Student will be created without a teacher. You can assign a teacher later.
                  </p>
                </div>
              )}
            </div>

            <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
              <h4 className="font-semibold text-blue-900 mb-2">Summary</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Student: {studentData.name} (Roll #{studentData.roll_number})</li>
                <li>• Class: {studentData.class_name} - {studentData.section}</li>
                <li>• Parent: {parentData.name} ({parentData.email})</li>
                <li>• Teacher: {assignedTeacher ? assignedTeacher.name : 'Not assigned'}</li>
              </ul>
            </div>

            <div className="flex justify-between gap-3 pt-4">
              <Button variant="outline" onClick={handleBack}>
                <ArrowLeft className="w-4 h-4 mr-2" /> Back
              </Button>
              <div className="flex gap-3">
                <Button variant="outline" onClick={onClose}>
                  Cancel
                </Button>
                <Button 
                  onClick={handleSubmit} 
                  disabled={loading}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {loading ? 'Creating...' : (
                    <>
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Create Student & Parent
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
