import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { RadioGroup, RadioGroupItem } from './ui/radio-group';
import { toast } from 'sonner';
import { UserPlus, ArrowRight, ArrowLeft, CheckCircle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AddStudentModal({ open, onClose, onSuccess }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  
  // Dropdown data
  const [buses, setBuses] = useState([]);
  const [stops, setStops] = useState([]);
  const [loadingStops, setLoadingStops] = useState(false);
  const [classSectionSuggestions, setClassSectionSuggestions] = useState([]);
  const [allParents, setAllParents] = useState([]);  // Changed from unlinkedParents to allParents
  
  // Step 1: Student basic info
  const [studentData, setStudentData] = useState({
    name: '',
    roll_number: '',
    class_section: '',  // Combined field
    class_name: '',
    section: '',
    bus_id: '',
    stop_id: '',
    phone: '',
    emergency_contact: '',
    remarks: ''
  });
  
  // Step 2: Parent selection mode and data
  const [parentMode, setParentMode] = useState('create'); // 'create' or 'select'
  const [selectedParentId, setSelectedParentId] = useState('');
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
      const [busesRes, classSectionsRes, parentsRes] = await Promise.all([
        axios.get(`${API}/buses`),
        axios.get(`${API}/students/class-sections`),
        axios.get(`${API}/parents/all`)  // Changed to fetch ALL parents
      ]);
      setBuses(busesRes.data);
      setClassSectionSuggestions(classSectionsRes.data || []);
      setAllParents(parentsRes.data || []);  // Changed state variable
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
      class_section: '',
      class_name: '',
      section: '',
      bus_id: '',
      stop_id: '',
      phone: '',
      emergency_contact: '',
      remarks: ''
    });
    setParentMode('create');
    setSelectedParentId('');
    setParentData({
      name: '',
      phone: '',
      email: '',
      photo: '',
      address: ''
    });
    setStops([]);
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

  const handleClassSectionChange = (value) => {
    setStudentData(prev => {
      const parsed = parseClassSection(value);
      return {
        ...prev,
        class_section: value,
        class_name: parsed.class_name,
        section: parsed.section
      };
    });
  };

  const handleNext = () => {
    // Validate Step 1
    if (step === 1) {
      if (!studentData.name || !studentData.roll_number || !studentData.class_name || 
          !studentData.section || !studentData.bus_id || !studentData.stop_id) {
        toast.error('Please fill in all required fields (Name, Roll Number, Class-Section, Bus, Stop)');
        return;
      }
    }
    
    setStep(step + 1);
  };

  const handleBack = () => {
    setStep(step - 1);
  };

  const handleSubmit = async () => {
    // Final validation based on parent mode
    if (parentMode === 'create') {
      if (!parentData.name || !parentData.phone || !parentData.email) {
        toast.error('Please fill in all required parent fields');
        return;
      }
    } else if (parentMode === 'select') {
      if (!selectedParentId) {
        toast.error('Please select a parent from the list');
        return;
      }
    }

    setLoading(true);
    try {
      let parentId;
      
      if (parentMode === 'create') {
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
        parentId = parentResponse.data.user_id;
      } else {
        // Use selected existing parent
        parentId = selectedParentId;
      }

      // Step 2: Create student with parent_id (teacher_id removed from UI)
      const studentPayload = {
        name: studentData.name,
        roll_number: studentData.roll_number,
        class_name: studentData.class_name,
        section: studentData.section,
        bus_id: studentData.bus_id,
        stop_id: studentData.stop_id,
        phone: studentData.phone,
        emergency_contact: studentData.emergency_contact,
        remarks: studentData.remarks,
        parent_id: parentId,
        teacher_id: null  // No longer assigned via UI
      };

      const studentResponse = await axios.post(`${API}/students`, studentPayload);

      // Check for capacity warning
      if (studentResponse.data?.capacity_warning) {
        toast.warning(studentResponse.data.capacity_warning, { duration: 6000 });
      }

      toast.success(parentMode === 'create' ? 'Student and Parent created successfully!' : 'Student created successfully!');
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
          {[1, 2].map((stepNum) => (
            <div key={stepNum} className="flex items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                step >= stepNum 
                  ? 'bg-violet-600 text-white' 
                  : 'bg-gray-200 text-gray-500'
              }`}>
                {stepNum}
              </div>
              {stepNum < 2 && (
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
              
              <div className="col-span-2">
                <Label>Class and Section *</Label>
                <Input
                  value={studentData.class_section}
                  onChange={(e) => handleClassSectionChange(e.target.value)}
                  placeholder="Enter Class and Section (e.g., 5A)"
                  list="class-section-suggestions"
                />
                <datalist id="class-section-suggestions">
                  {classSectionSuggestions.map((suggestion, idx) => (
                    <option key={idx} value={suggestion} />
                  ))}
                </datalist>
                {studentData.class_section && studentData.class_name && studentData.section && (
                  <p className="text-xs text-green-600 mt-1">
                    ✓ Parsed as: Class {studentData.class_name}, Section {studentData.section}
                  </p>
                )}
                {studentData.class_section && (!studentData.class_name || !studentData.section) && (
                  <p className="text-xs text-amber-600 mt-1">
                    ⚠️ Please use format like "5A" or "5-A"
                  </p>
                )}
              </div>
              
              <div>
                <Label>Bus *</Label>
                <Select
                  value={studentData.bus_id}
                  onValueChange={(value) => {
                    setStudentData({ ...studentData, bus_id: value, stop_id: '' });
                  }}
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
                <Label>Stop *</Label>
                <Select
                  value={studentData.stop_id}
                  onValueChange={(value) => setStudentData({ ...studentData, stop_id: value })}
                  disabled={!studentData.bus_id || loadingStops}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={
                      !studentData.bus_id 
                        ? "Select bus first" 
                        : loadingStops 
                        ? "Loading stops..." 
                        : "Select stop"
                    } />
                  </SelectTrigger>
                  <SelectContent>
                    {stops.length > 0 ? (
                      stops.map(stop => (
                        <SelectItem key={stop.stop_id} value={stop.stop_id}>
                          {stop.stop_name}
                        </SelectItem>
                      ))
                    ) : (
                      <SelectItem value="no-stops" disabled>
                        No stops available
                      </SelectItem>
                    )}
                  </SelectContent>
                </Select>
                {studentData.bus_id && stops.length === 0 && !loadingStops && (
                  <p className="text-xs text-amber-600 mt-1">
                    ⚠️ Selected bus has no route stops configured
                  </p>
                )}
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
            
            {/* Radio buttons for parent selection mode */}
            <div className="bg-gray-50 border border-gray-200 p-4 rounded-lg">
              <Label className="mb-3 block">Parent Selection</Label>
              <RadioGroup value={parentMode} onValueChange={setParentMode} className="space-y-3">
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="create" id="create" />
                  <Label htmlFor="create" className="cursor-pointer font-normal">
                    Create New Parent Account
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="select" id="select" />
                  <Label htmlFor="select" className="cursor-pointer font-normal">
                    Select Existing Parent
                  </Label>
                </div>
              </RadioGroup>
            </div>

            {/* Create New Parent Form */}
            {parentMode === 'create' && (
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
            )}

            {/* Select Existing Parent */}
            {parentMode === 'select' && (
              <div>
                <Label>Select Parent *</Label>
                {allParents.length > 0 ? (
                  <Select value={selectedParentId} onValueChange={setSelectedParentId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a parent" />
                    </SelectTrigger>
                    <SelectContent>
                      {allParents.map(parent => (
                        <SelectItem key={parent.user_id} value={parent.user_id}>
                          {parent.name} ({parent.email})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <div className="text-sm text-amber-600 bg-amber-50 border border-amber-200 p-3 rounded">
                    ⚠️ No parent accounts available. Please create a new parent account.
                  </div>
                )}
              </div>
            )}

            {/* Summary Preview */}
            <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg mt-4">
              <h4 className="font-semibold text-blue-900 mb-2">Summary</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Student: {studentData.name} (Roll #{studentData.roll_number})</li>
                <li>• Class: {studentData.class_name}{studentData.section}</li>
                <li>• Bus: {buses.find(b => b.bus_id === studentData.bus_id)?.bus_number || 'N/A'}</li>
                <li>• Stop: {stops.find(s => s.stop_id === studentData.stop_id)?.stop_name || 'N/A'}</li>
                <li>• Parent: {
                  parentMode === 'create' 
                    ? `${parentData.name || 'Not entered'} (${parentData.email || 'Not entered'})` 
                    : unlinkedParents.find(p => p.user_id === selectedParentId)?.name || 'Not selected'
                }</li>
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
                      {parentMode === 'create' ? 'Create Student & Parent' : 'Create Student'}
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
