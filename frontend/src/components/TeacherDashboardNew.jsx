import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { toast } from 'sonner';
import {
  LogOut,
  Users,
  GraduationCap,
  Calendar,
  Search,
  Eye,
  Bell,
  Mail,
  Phone,
  MapPin,
  TrendingUp,
  UserX,
  Camera
} from 'lucide-react';
import StudentDetailModal from './StudentDetailModal';
import AttendanceGrid from './AttendanceGrid';
import PhotoViewerModal from './PhotoViewerModal';
import PhotoAvatar from './PhotoAvatar';
import NotificationBell from './NotificationBell';
import { formatClassName } from '../utils/helpers';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function TeacherDashboardNew({ user, onLogout }) {

  // Data states
  const [students, setStudents] = useState([]);
  const [stats, setStats] = useState({
    totalStudents: 0,
    avgAttendance: 0,
    todayAbsences: 0
  });
  
  // Filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [searchBy, setSearchBy] = useState('all');
  const [filterAMStatus, setFilterAMStatus] = useState('');
  const [filterPMStatus, setFilterPMStatus] = useState('');
  
  // Modal states
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [showStudentDetail, setShowStudentDetail] = useState(false);
  const [showAttendanceModal, setShowAttendanceModal] = useState(false);
  const [attendanceStudentId, setAttendanceStudentId] = useState(null);
  const [attendanceStudentName, setAttendanceStudentName] = useState('');
  
  // Photo viewer state
  const [showPhotoViewer, setShowPhotoViewer] = useState(false);
  const [currentUser, setCurrentUser] = useState(user);
  
  // Scan photo modal state
  const [showScanModal, setShowScanModal] = useState(false);
  const [selectedScan, setSelectedScan] = useState(null);

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      // Fetch students
      await fetchStudents();
    } catch (error) {
      toast.error('Failed to load dashboard data');
      console.error(error);
    }
  };

  const fetchStudents = async () => {
    try {
      const response = await axios.get(`${API}/teacher/students`);
      setStudents(response.data);
      
      // Calculate stats
      const totalStudents = response.data.length;
      const todayAbsences = response.data.filter(s => 
        s.am_status === 'red' || s.pm_status === 'red'
      ).length;
      
      setStats(prev => ({
        ...prev,
        totalStudents,
        todayAbsences
      }));
      
      // Calculate monthly attendance percentage
      if (response.data.length > 0) {
        calculateMonthlyAttendance(response.data);
      }
    } catch (error) {
      toast.error('Failed to load students');
      console.error(error);
    }
  };

  const calculateMonthlyAttendance = async (studentsList) => {
    try {
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const monthParam = `${year}-${month}`;
      
      let totalAttended = 0;
      let totalPossible = 0;
      
      for (const student of studentsList) {
        const response = await axios.get(
          `${API}/get_attendance?student_id=${student.student_id}&month=${monthParam}`
        );
        
        const gridData = response.data.grid || [];
        
        // Count attended vs possible for this student
        gridData.forEach(dayData => {
          // AM trip
          if (dayData.am_status && dayData.am_status !== 'blue') {
            totalPossible++;
            if (dayData.am_status === 'green' || dayData.am_status === 'yellow') {
              totalAttended++;
            }
          }
          // PM trip
          if (dayData.pm_status && dayData.pm_status !== 'blue') {
            totalPossible++;
            if (dayData.pm_status === 'green' || dayData.pm_status === 'yellow') {
              totalAttended++;
            }
          }
        });
      }
      
      const avgAttendance = totalPossible > 0 
        ? Math.round((totalAttended / totalPossible) * 100) 
        : 0;
      
      setStats(prev => ({
        ...prev,
        avgAttendance
      }));
    } catch (error) {
      console.error('Failed to calculate attendance:', error);
    }
  };

  const handleStudentClick = (student) => {
    setSelectedStudent(student);
    setShowStudentDetail(true);
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };


  const handleProfilePhotoClick = () => {
    setShowPhotoViewer(true);
  };

  const handleProfilePhotoUpdate = (newPhotoUrl) => {
    // newPhotoUrl already includes BACKEND_URL and cache-busting timestamp from PhotoViewerModal
    setCurrentUser(prev => ({
      ...prev,
      photo: newPhotoUrl.startsWith('http') ? newPhotoUrl : `${BACKEND_URL}${newPhotoUrl}`
    }));
  };

  const handleViewStudent = async (student) => {
    setSelectedStudent(student);
    setShowStudentDetail(true);
  };

  const handleViewAttendance = (student) => {
    setAttendanceStudentId(student.student_id);
    setAttendanceStudentName(student.name);
    setShowAttendanceModal(true);
  };

  // Status options for filters
  const statusOptions = ['gray', 'yellow', 'green', 'red', 'blue'];

  // Apply filters with dropdown-based search
  const filteredStudents = students.filter(student => {
    let matchesSearch = true;
    
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase().trim();
      
      switch (searchBy) {
        case 'all':
          matchesSearch = 
            student.name.toLowerCase().includes(term) ||
            (student.parent_name && student.parent_name.toLowerCase().includes(term)) ||
            (student.bus_number && student.bus_number.toLowerCase().includes(term)) ||
            (student.roll_number && student.roll_number.toLowerCase().includes(term));
          break;
        case 'name':
          matchesSearch = student.name.toLowerCase().includes(term);
          break;
        case 'roll':
          matchesSearch = student.roll_number && student.roll_number.toLowerCase().includes(term);
          break;
        case 'bus':
          matchesSearch = student.bus_number && student.bus_number.toLowerCase().includes(term);
          break;
        case 'parent':
          matchesSearch = student.parent_name && student.parent_name.toLowerCase().includes(term);
          break;
        default:
          matchesSearch = true;
      }
    }
    
    const matchesAM = !filterAMStatus || student.am_status === filterAMStatus;
    const matchesPM = !filterPMStatus || student.pm_status === filterPMStatus;
    
    return matchesSearch && matchesAM && matchesPM;
  });

  const getStatusClass = (status) => {
    return `status-${status}`;
  };

  const getStatusLabel = (status) => {
    const labels = {
      'gray': 'Not Scanned',
      'yellow': 'On Board',
      'green': 'Reached',
      'red': 'Missed',
      'blue': 'Holiday'
    };
    return labels[status] || status;
  };

  const handleStatusClick = (student, trip) => {
    const tripData = trip === 'AM' ? {
      photo: student.am_scan_photo,
      timestamp: student.am_scan_timestamp,
      status: student.am_status,
      trip: 'AM'
    } : {
      photo: student.pm_scan_photo,
      timestamp: student.pm_scan_timestamp,
      status: student.pm_status,
      trip: 'PM'
    };

    // Only open modal for yellow and green status (scanned)
    if (tripData.status === 'green' || tripData.status === 'yellow') {
      const today = new Date();
      setSelectedScan({
        ...tripData,
        date: today.toISOString().split('T')[0],
        day: today.getDate(),
        studentName: student.name
      });
      setShowScanModal(true);
    }
  };

  const formatScanTimestamp = (timestamp) => {
    if (!timestamp) return 'No timestamp available';
    try {
      const date = new Date(timestamp);
      const timeStr = date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
      });
      const dateStr = date.toLocaleDateString('en-US', { 
        day: '2-digit', 
        month: 'short', 
        year: 'numeric' 
      });
      return `${timeStr}, ${dateStr}`;
    } catch (e) {
      return 'Invalid timestamp';
    }
  };

  return (
    <div className="min-h-screen dashboard-bg" data-testid="teacher-dashboard">
      {/* Header with Dynamic Gradient */}
      <header className="bg-gradient-to-r from-teal-50 via-emerald-50 to-green-50 animate-gradient dashboard-panel teacher-accent-border border-b dashboard-separator shadow-md sticky top-0 z-10 transition-shadow duration-300 hover:shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4 slide-in-left">
              <div className="w-16 h-16 bg-gradient-to-br from-teacher-primary via-teal-500 to-teacher-secondary rounded-xl flex items-center justify-center shadow-lg hover:shadow-xl transition-all duration-300 hover:animate-glow group relative">
                <GraduationCap className="w-8 h-8 text-white transition-transform duration-300 group-hover:scale-110" />
                <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-teacher-primary to-teal-600 bg-clip-text text-transparent">
                  Teacher Dashboard
                </h1>
                <p className="text-sm text-gray-600 mt-1 font-medium">
                  Welcome back, <span className="text-teacher-primary">{user.name}</span>
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <NotificationBell role="teacher" />
              <Button onClick={onLogout} variant="outline" className="logout-button logout-button-teacher">
                <LogOut className="w-4 h-4" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Teacher Profile Card */}
            <Card className="p-6 dashboard-card teacher-accent-border hover:shadow-lg transition-shadow">
              <h2 className="text-xl font-semibold mb-5 text-teacher-primary">
                Teacher Profile
              </h2>
              <div className="flex items-center gap-6">
                <PhotoAvatar
                  photoUrl={currentUser.photo ? `${BACKEND_URL}${currentUser.photo}` : null}
                  userName={currentUser.name}
                  size="lg"
                  onClick={handleProfilePhotoClick}
                  gradientFrom="teacher-primary"
                  gradientTo="teacher-secondary"
                />
                <div className="flex-1 space-y-2">
                  <h3 className="text-xl font-bold text-gray-900">{user.name}</h3>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    {user.email && (
                      <div className="flex items-center gap-2">
                        <Mail className="w-4 h-4 text-teacher-primary" />
                        {user.email}
                      </div>
                    )}
                    {user.phone && (
                      <div className="flex items-center gap-2">
                        <Phone className="w-4 h-4 text-teacher-primary" />
                        {user.phone}
                      </div>
                    )}
                  </div>
                  {(user.assigned_class || user.assigned_section) && (
                    <div className="flex items-center gap-1.5 text-sm font-medium text-teacher-primary bg-teacher-light px-3 py-1.5 rounded-lg inline-flex">
                      <GraduationCap className="w-4 h-4" />
                      Class: {formatClassName(user.assigned_class)} {user.assigned_section ? `- Section ${user.assigned_section}` : ''}
                    </div>
                  )}
                </div>
              </div>
            </Card>

            {/* Summary Stats Cards */}
            <div className="grid md:grid-cols-3 gap-6">
              <Card className="p-6 dashboard-card teacher-accent-border hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 mb-2">Total Students</p>
                    <h3 className="text-4xl font-bold text-teacher-primary">{stats.totalStudents}</h3>
                  </div>
                  <div className="w-16 h-16 bg-gradient-to-br from-teacher-primary to-teacher-secondary rounded-xl flex items-center justify-center shadow-md">
                    <Users className="w-8 h-8 text-white" />
                  </div>
                </div>
              </Card>

              <Card className="p-6 dashboard-card teacher-accent-border hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 mb-2">Avg Monthly Attendance</p>
                    <h3 className="text-4xl font-bold text-teacher-primary">{stats.avgAttendance}%</h3>
                  </div>
                  <div className="w-16 h-16 bg-gradient-to-br from-teacher-primary to-teacher-secondary rounded-xl flex items-center justify-center shadow-md">
                    <TrendingUp className="w-8 h-8 text-white" />
                  </div>
                </div>
              </Card>

              <Card className="p-6 dashboard-card teacher-accent-border hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 mb-2">Today's Absences</p>
                    <h3 className="text-4xl font-bold text-status-red">{stats.todayAbsences}</h3>
                  </div>
                  <div className="w-16 h-16 bg-gradient-to-br from-red-500 to-red-600 rounded-xl flex items-center justify-center shadow-md">
                    <UserX className="w-8 h-8 text-white" />
                  </div>
                </div>
              </Card>
            </div>

            {/* Students List */}
            <Card className="p-6 dashboard-card teacher-accent-border">
              <div className="mb-6">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-5">
                  <h2 className="text-xl font-semibold text-gray-900">
                    My Students
                  </h2>
                  {/* Inline Status Legend */}
                  <div className="flex flex-wrap items-center gap-3 text-xs">
                    <div className="flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full status-gray"></div>
                      <span className="text-gray-600">Not Scanned</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full status-yellow"></div>
                      <span className="text-gray-600">On Board</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full status-green"></div>
                      <span className="text-gray-600">Reached</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full status-red"></div>
                      <span className="text-gray-600">Missed</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full status-blue"></div>
                      <span className="text-gray-600">Holiday</span>
                    </div>
                  </div>
                </div>
                
                {/* Search and Filters */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                  <select
                    value={searchBy}
                    onChange={(e) => setSearchBy(e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teacher-primary bg-white text-sm"
                  >
                    <option value="all">All Fields</option>
                    <option value="name">Name</option>
                    <option value="roll">Roll No</option>
                    <option value="bus">Bus</option>
                    <option value="parent">Parent</option>
                  </select>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input
                      type="text"
                      placeholder="Search for..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 focus:ring-teacher-primary focus:border-teacher-primary"
                    />
                  </div>

                  <select
                    value={filterAMStatus}
                    onChange={(e) => setFilterAMStatus(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-teacher-primary"
                  >
                    <option value="">All AM Status</option>
                    {statusOptions.map(status => (
                      <option key={status} value={status}>{getStatusLabel(status)}</option>
                    ))}
                  </select>

                  <select
                    value={filterPMStatus}
                    onChange={(e) => setFilterPMStatus(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-teacher-primary"
                  >
                    <option value="">All PM Status</option>
                    {statusOptions.map(status => (
                      <option key={status} value={status}>{getStatusLabel(status)}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Students Table */}
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b-2 border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Roll No</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Name</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Parent Name</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Bus No</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">AM Status</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">PM Status</th>
                      <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {filteredStudents.length === 0 ? (
                      <tr>
                        <td colSpan="7" className="px-4 py-8 text-center text-gray-500">
                          No students found
                        </td>
                      </tr>
                    ) : (
                      filteredStudents.map(student => (
                        <tr key={student.student_id} className="hover:bg-gray-50 transition-colors">
                          <td className="px-4 py-4 text-sm text-teacher-primary font-medium">
                            {student.roll_number || 'N/A'}
                          </td>
                          <td className="px-4 py-4 text-sm text-gray-600">
                            {student.name}
                          </td>
                          <td className="px-4 py-4 text-sm text-gray-600">
                            {student.parent_name || 'N/A'}
                          </td>
                          <td className="px-4 py-4 text-sm text-gray-600">
                            {student.bus_number || 'N/A'}
                          </td>
                          <td className="px-4 py-4">
                            <span 
                              className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${getStatusClass(student.am_status)} ${(student.am_status === 'yellow' || student.am_status === 'green') ? 'cursor-pointer hover:opacity-80 transition-opacity' : ''}`}
                              onClick={() => handleStatusClick(student, 'AM')}
                              title={(student.am_status === 'yellow' || student.am_status === 'green') ? 'Click to view scan photo' : ''}
                            >
                              {getStatusLabel(student.am_status)}
                            </span>
                          </td>
                          <td className="px-4 py-4">
                            <span 
                              className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${getStatusClass(student.pm_status)} ${(student.pm_status === 'yellow' || student.pm_status === 'green') ? 'cursor-pointer hover:opacity-80 transition-opacity' : ''}`}
                              onClick={() => handleStatusClick(student, 'PM')}
                              title={(student.pm_status === 'yellow' || student.pm_status === 'green') ? 'Click to view scan photo' : ''}
                            >
                              {getStatusLabel(student.pm_status)}
                            </span>
                          </td>
                          <td className="px-4 py-4">
                            <div className="flex items-center justify-center gap-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleViewStudent(student)}
                                className="text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
                                title="View Details"
                              >
                                <Eye className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleViewAttendance(student)}
                                className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                                title="View Attendance"
                              >
                                <Calendar className="w-4 h-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </Card>
      </div>

      {/* Student Detail Modal */}
      <StudentDetailModal
        student={selectedStudent}
        open={showStudentDetail}
        onClose={() => {
          setShowStudentDetail(false);
          setSelectedStudent(null);
        }}
        hideTeacherField={true}
      />

      {/* Attendance Modal */}
      <Dialog open={showAttendanceModal} onOpenChange={setShowAttendanceModal}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold flex items-center gap-2" style={{ fontFamily: 'Space Grotesk' }}>
              <Calendar className="w-6 h-6 text-blue-600" />
              Monthly Attendance - {attendanceStudentName}
            </DialogTitle>
          </DialogHeader>
          
          <div className="mt-4">
            {/* Status Legend */}
            <div className="flex flex-wrap items-center justify-center gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full status-gray"></div>
                <span className="text-xs font-medium text-gray-600">Not Scanned</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full status-yellow"></div>
                <span className="text-xs font-medium text-gray-600">On Board</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full status-green"></div>
                <span className="text-xs font-medium text-gray-600">Reached</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full status-red"></div>
                <span className="text-xs font-medium text-gray-600">Missed</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full status-blue"></div>
                <span className="text-xs font-medium text-gray-600">Holiday</span>
              </div>
            </div>
            
            {/* Attendance Grid */}
            {attendanceStudentId && (
              <AttendanceGrid studentId={attendanceStudentId} />
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Photo Viewer Modal */}
      <PhotoViewerModal
        open={showPhotoViewer}
        onClose={() => setShowPhotoViewer(false)}
        photoUrl={currentUser.photo ? `${BACKEND_URL}${currentUser.photo}` : null}
        userName={currentUser.name}
        canEdit={true}
        uploadEndpoint={`${API}/users/me/photo`}
        onPhotoUpdate={handleProfilePhotoUpdate}
      />

      {/* Scan Photo Modal */}
      <Dialog open={showScanModal} onOpenChange={setShowScanModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-emerald-700">
              <Camera className="w-5 h-5" />
              Scan Photo - {selectedScan?.trip} Trip
            </DialogTitle>
          </DialogHeader>
          
          {selectedScan && (
            <div className="space-y-4">
              <div className="bg-emerald-50 rounded-lg p-3 border border-emerald-200">
                <div className="text-sm text-emerald-900 font-medium">
                  {selectedScan.studentName}
                </div>
                <div className="text-xs text-emerald-700 mt-1">
                  {new Date(selectedScan.date).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                </div>
              </div>
              <div className="flex justify-center">
                {selectedScan.photo ? (
                  <img src={`${BACKEND_URL}${selectedScan.photo}`} alt="Scan capture" className="w-40 h-40 object-cover rounded-lg shadow-md border-2 border-gray-200" />
                ) : (
                  <div className="w-40 h-40 bg-gray-100 rounded-lg flex items-center justify-center border-2 border-gray-200">
                    <div className="text-center">
                      <Camera className="w-10 h-10 text-gray-400 mx-auto mb-2" />
                      <p className="text-xs text-gray-500">No photo available</p>
                    </div>
                  </div>
                )}
              </div>
              <div className="flex justify-center">
                <span className={`px-4 py-2 rounded-full text-sm font-medium ${getStatusClass(selectedScan.status)}`}>
                  {getStatusLabel(selectedScan.status)}
                </span>
              </div>
              <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                <div className="flex items-center gap-2 text-sm text-gray-700">
                  <Calendar className="w-4 h-4 text-gray-500" />
                  <span className="font-medium">Scan Time:</span>
                  <span>{formatScanTimestamp(selectedScan.timestamp)}</span>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

    </div>
  );
}
