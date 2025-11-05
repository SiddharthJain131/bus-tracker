import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { toast } from 'sonner';
import { LogOut, UserPlus, Users, Calendar, Search, Trash2, Bus } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminDashboard({ user, onLogout }) {
  const [activeTab, setActiveTab] = useState('students');
  const [students, setStudents] = useState([]);
  const [users, setUsers] = useState([]);
  const [holidays, setHolidays] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddStudent, setShowAddStudent] = useState(false);
  const [showAddHoliday, setShowAddHoliday] = useState(false);
  const [newStudent, setNewStudent] = useState({
    name: '',
    parent_id: '',
    bus_id: '',
  });
  const [newHoliday, setNewHoliday] = useState({
    date: '',
    name: '',
  });

  useEffect(() => {
    fetchStudents();
    fetchUsers();
    fetchHolidays();
  }, []);

  const fetchStudents = async () => {
    try {
      const response = await axios.get(`${API}/admin/students`);
      setStudents(response.data);
    } catch (error) {
      toast.error('Failed to load students');
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/users`);
      setUsers(response.data);
    } catch (error) {
      toast.error('Failed to load users');
    }
  };

  const fetchHolidays = async () => {
    try {
      const response = await axios.get(`${API}/admin/holidays`);
      setHolidays(response.data);
    } catch (error) {
      toast.error('Failed to load holidays');
    }
  };

  const handleAddStudent = async () => {
    try {
      await axios.post(`${API}/admin/students`, newStudent);
      toast.success('Student added successfully');
      setShowAddStudent(false);
      setNewStudent({ name: '', parent_id: '', bus_id: '' });
      fetchStudents();
    } catch (error) {
      toast.error('Failed to add student');
    }
  };

  const handleDeleteStudent = async (studentId) => {
    if (!window.confirm('Are you sure you want to delete this student?')) return;
    try {
      await axios.delete(`${API}/admin/students/${studentId}`);
      toast.success('Student deleted');
      fetchStudents();
    } catch (error) {
      toast.error('Failed to delete student');
    }
  };

  const handleAddHoliday = async () => {
    try {
      await axios.post(`${API}/admin/holidays`, newHoliday);
      toast.success('Holiday added successfully');
      setShowAddHoliday(false);
      setNewHoliday({ date: '', name: '' });
      fetchHolidays();
    } catch (error) {
      toast.error('Failed to add holiday');
    }
  };

  const handleDeleteHoliday = async (holidayId) => {
    if (!window.confirm('Are you sure you want to delete this holiday?')) return;
    try {
      await axios.delete(`${API}/admin/holidays/${holidayId}`);
      toast.success('Holiday deleted');
      fetchHolidays();
    } catch (error) {
      toast.error('Failed to delete holiday');
    }
  };

  const filteredStudents = students.filter((s) =>
    s.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredUsers = users.filter((u) =>
    u.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-violet-50" data-testid="admin-dashboard">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-violet-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Users className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>Admin Dashboard</h1>
                <p className="text-sm text-gray-600">Welcome, {user.name}</p>
              </div>
            </div>
            <Button
              data-testid="logout-button"
              onClick={onLogout}
              variant="outline"
              className="flex items-center gap-2"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tabs */}
        <Card className="p-2 mb-6">
          <div className="flex gap-2">
            <Button
              data-testid="students-tab"
              onClick={() => setActiveTab('students')}
              variant={activeTab === 'students' ? 'default' : 'ghost'}
              className="flex-1"
            >
              <UserPlus className="w-4 h-4 mr-2" />
              Students
            </Button>
            <Button
              data-testid="users-tab"
              onClick={() => setActiveTab('users')}
              variant={activeTab === 'users' ? 'default' : 'ghost'}
              className="flex-1"
            >
              <Users className="w-4 h-4 mr-2" />
              Users
            </Button>
            <Button
              data-testid="holidays-tab"
              onClick={() => setActiveTab('holidays')}
              variant={activeTab === 'holidays' ? 'default' : 'ghost'}
              className="flex-1"
            >
              <Calendar className="w-4 h-4 mr-2" />
              Holidays
            </Button>
            <Button
              data-testid="demo-tab"
              onClick={() => setActiveTab('demo')}
              variant={activeTab === 'demo' ? 'default' : 'ghost'}
              className="flex-1"
            >
              <Bus className="w-4 h-4 mr-2" />
              Demo
            </Button>
          </div>
        </Card>

        {/* Search */}
        {(activeTab === 'students' || activeTab === 'users') && (
          <Card className="p-4 mb-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <Input
                data-testid="search-input"
                type="text"
                placeholder={`Search ${activeTab}...`}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </Card>
        )}

        {/* Students Tab */}
        {activeTab === 'students' && (
          <div>
            <Card className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold" style={{ fontFamily: 'Space Grotesk' }}>Students</h2>
                <Button
                  data-testid="add-student-button"
                  onClick={() => setShowAddStudent(!showAddStudent)}
                  className="flex items-center gap-2"
                >
                  <UserPlus className="w-4 h-4" />
                  Add Student
                </Button>
              </div>

              {showAddStudent && (
                <Card className="p-4 mb-6 bg-gray-50">
                  <h3 className="font-semibold mb-4">Add New Student</h3>
                  <div className="grid md:grid-cols-3 gap-4">
                    <Input
                      data-testid="new-student-name"
                      placeholder="Student Name"
                      value={newStudent.name}
                      onChange={(e) => setNewStudent({ ...newStudent, name: e.target.value })}
                    />
                    <Input
                      data-testid="new-student-parent-id"
                      placeholder="Parent ID"
                      value={newStudent.parent_id}
                      onChange={(e) => setNewStudent({ ...newStudent, parent_id: e.target.value })}
                    />
                    <Input
                      data-testid="new-student-bus-id"
                      placeholder="Bus ID"
                      value={newStudent.bus_id}
                      onChange={(e) => setNewStudent({ ...newStudent, bus_id: e.target.value })}
                    />
                  </div>
                  <div className="flex gap-2 mt-4">
                    <Button data-testid="save-student-button" onClick={handleAddStudent}>Save</Button>
                    <Button variant="outline" onClick={() => setShowAddStudent(false)}>Cancel</Button>
                  </div>
                </Card>
              )}

              <div className="space-y-2" data-testid="students-list">
                {filteredStudents.map((student) => (
                  <div
                    key={student.student_id}
                    className="flex justify-between items-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100"
                  >
                    <div>
                      <p className="font-medium text-gray-900">{student.name}</p>
                      <p className="text-sm text-gray-500">Bus: {student.bus_id} | Parent: {student.parent_id}</p>
                    </div>
                    <Button
                      data-testid={`delete-student-${student.name.toLowerCase().replace(' ', '-')}`}
                      onClick={() => handleDeleteStudent(student.student_id)}
                      variant="ghost"
                      size="sm"
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        )}

        {/* Users Tab */}
        {activeTab === 'users' && (
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-6" style={{ fontFamily: 'Space Grotesk' }}>Users</h2>
            <div className="space-y-2" data-testid="users-list">
              {filteredUsers.map((u) => (
                <div key={u.user_id} className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-medium text-gray-900">{u.name}</p>
                      <p className="text-sm text-gray-500">{u.email}</p>
                    </div>
                    <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                      {u.role}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Holidays Tab */}
        {activeTab === 'holidays' && (
          <Card className="p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold" style={{ fontFamily: 'Space Grotesk' }}>Holidays</h2>
              <Button
                data-testid="add-holiday-button"
                onClick={() => setShowAddHoliday(!showAddHoliday)}
                className="flex items-center gap-2"
              >
                <Calendar className="w-4 h-4" />
                Add Holiday
              </Button>
            </div>

            {showAddHoliday && (
              <Card className="p-4 mb-6 bg-gray-50">
                <h3 className="font-semibold mb-4">Add New Holiday</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  <Input
                    data-testid="new-holiday-date"
                    type="date"
                    value={newHoliday.date}
                    onChange={(e) => setNewHoliday({ ...newHoliday, date: e.target.value })}
                  />
                  <Input
                    data-testid="new-holiday-name"
                    placeholder="Holiday Name"
                    value={newHoliday.name}
                    onChange={(e) => setNewHoliday({ ...newHoliday, name: e.target.value })}
                  />
                </div>
                <div className="flex gap-2 mt-4">
                  <Button data-testid="save-holiday-button" onClick={handleAddHoliday}>Save</Button>
                  <Button variant="outline" onClick={() => setShowAddHoliday(false)}>Cancel</Button>
                </div>
              </Card>
            )}

            <div className="space-y-2" data-testid="holidays-list">
              {holidays.map((holiday) => (
                <div
                  key={holiday.holiday_id}
                  className="flex justify-between items-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100"
                >
                  <div>
                    <p className="font-medium text-gray-900">{holiday.name}</p>
                    <p className="text-sm text-gray-500">{holiday.date}</p>
                  </div>
                  <Button
                    data-testid={`delete-holiday-${holiday.name.toLowerCase().replace(' ', '-')}`}
                    onClick={() => handleDeleteHoliday(holiday.holiday_id)}
                    variant="ghost"
                    size="sm"
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Demo Tab */}
        {activeTab === 'demo' && (
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4" style={{ fontFamily: 'Space Grotesk' }}>Demo Simulation</h2>
            <p className="text-gray-600 mb-6">Simulate RFID scans and bus movements for testing</p>
            <DemoControls />
          </Card>
        )}
      </div>
    </div>
  );
}

function DemoControls() {
  const [busId, setBusId] = useState('BUS-001');
  const [simulating, setSimulating] = useState(false);

  const simulateScan = async () => {
    try {
      const response = await axios.post(`${API}/demo/simulate_scan`);
      toast.success(`Scan simulated: ${response.data.student_name} (Verified: ${response.data.verified})`);
    } catch (error) {
      toast.error('Failed to simulate scan');
    }
  };

  const simulateBusMovement = async () => {
    try {
      await axios.post(`${API}/demo/simulate_bus_movement?bus_id=${busId}`);
      toast.success('Bus location updated');
    } catch (error) {
      toast.error('Failed to simulate bus movement');
    }
  };

  const startContinuousSimulation = () => {
    setSimulating(true);
    const interval = setInterval(() => {
      simulateScan();
      simulateBusMovement();
    }, 5000);

    setTimeout(() => {
      clearInterval(interval);
      setSimulating(false);
      toast.info('Simulation stopped');
    }, 30000); // Run for 30 seconds
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="text-sm font-medium text-gray-700 mb-2 block">Bus ID</label>
        <Input
          data-testid="demo-bus-id"
          value={busId}
          onChange={(e) => setBusId(e.target.value)}
          placeholder="BUS-001"
        />
      </div>
      <div className="flex flex-wrap gap-3">
        <Button data-testid="simulate-scan-button" onClick={simulateScan}>
          Simulate Single Scan
        </Button>
        <Button data-testid="simulate-bus-button" onClick={simulateBusMovement} variant="outline">
          Simulate Bus Movement
        </Button>
        <Button
          data-testid="start-continuous-button"
          onClick={startContinuousSimulation}
          disabled={simulating}
          className="bg-gradient-to-r from-violet-600 to-purple-600"
        >
          {simulating ? 'Simulating...' : 'Start Continuous (30s)'}
        </Button>
      </div>
    </div>
  );
}
