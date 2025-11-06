import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
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
  UserX
} from 'lucide-react';
import StudentDetailModal from './StudentDetailModal';
import AttendanceGrid from './AttendanceGrid';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function TeacherDashboardNew({ user, onLogout }) {
  // Data states
  const [students, setStudents] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [stats, setStats] = useState({
    totalStudents: 0,
    avgAttendance: 0,
    todayAbsences: 0
  });
  
  // Filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [filterBus, setFilterBus] = useState('');
  const [filterAMStatus, setFilterAMStatus] = useState('');
  const [filterPMStatus, setFilterPMStatus] = useState('');
  
  // Modal states
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [showStudentDetail, setShowStudentDetail] = useState(false);
  const [showAttendanceModal, setShowAttendanceModal] = useState(false);
  const [attendanceStudentId, setAttendanceStudentId] = useState(null);

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      // Fetch students first, then notifications
      await fetchStudents();
      await fetchNotifications();
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
      
      let totalAttended = 0;
      let totalPossible = 0;
      
      for (const student of studentsList) {
        const response = await axios.get(
          `${API}/get_attendance?student_id=${student.student_id}&year=${year}&month=${month}`
        );
        
        const attendanceData = response.data.attendance || {};
        
        // Count attended vs possible for this student
        Object.values(attendanceData).forEach(dayData => {
          // AM trip
          if (dayData.AM) {
            totalPossible++;
            if (dayData.AM === 'green' || dayData.AM === 'yellow') {
              totalAttended++;
            }
          }
          // PM trip
          if (dayData.PM) {
            totalPossible++;
            if (dayData.PM === 'green' || dayData.PM === 'yellow') {
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

  const fetchNotifications = async () => {
    try {
      const response = await axios.get(`${API}/get_notifications`);
      // Enrich notifications with student names
      const enrichedNotifications = response.data.map(notification => {
        const student = students.find(s => s.student_id === notification.student_id);
        return {
          ...notification,
          student_name: student ? student.name : 'Unknown Student'
        };
      });
      setNotifications(enrichedNotifications);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  };

  const handleViewStudent = async (student) => {
    setSelectedStudent(student);
    setShowStudentDetail(true);
  };

  const handleViewAttendance = (studentId) => {
    setAttendanceStudentId(studentId);
    setShowAttendanceModal(true);
  };

  // Get unique bus numbers for filter
  const uniqueBuses = [...new Set(students.map(s => s.bus_number).filter(Boolean))];
  const statusOptions = ['gray', 'yellow', 'green', 'red', 'blue'];

  // Apply filters
  const filteredStudents = students.filter(student => {
    const matchesSearch = 
      student.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (student.parent_name && student.parent_name.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesBus = !filterBus || student.bus_number === filterBus;
    const matchesAM = !filterAMStatus || student.am_status === filterAMStatus;
    const matchesPM = !filterPMStatus || student.pm_status === filterPMStatus;
    
    return matchesSearch && matchesBus && matchesAM && matchesPM;
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-emerald-50" data-testid="teacher-dashboard">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center">
                <GraduationCap className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                  Teacher Dashboard
                </h1>
                <p className="text-sm text-gray-600">Welcome, {user.name}</p>
              </div>
            </div>
            <Button onClick={onLogout} variant="outline" className="flex items-center gap-2">
              <LogOut className="w-4 h-4" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid lg:grid-cols-4 gap-6">
          {/* Main Content - 3 columns */}
          <div className="lg:col-span-3 space-y-6">
            {/* Teacher Profile Card */}
            <Card className="p-6">
              <h2 className="text-xl font-semibold mb-4" style={{ fontFamily: 'Space Grotesk' }}>
                Teacher Profile
              </h2>
              <div className="flex items-center gap-6">
                <div className="w-20 h-20 bg-gradient-to-br from-emerald-400 to-teal-600 rounded-full flex items-center justify-center text-white text-3xl font-bold">
                  {user.photo ? (
                    <img src={user.photo} alt={user.name} className="w-full h-full rounded-full object-cover" />
                  ) : (
                    user.name.charAt(0).toUpperCase()
                  )}
                </div>
                <div className="flex-1 space-y-2">
                  <h3 className="text-2xl font-bold text-gray-900">{user.name}</h3>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    {user.email && (
                      <div className="flex items-center gap-1">
                        <Mail className="w-4 h-4" />
                        {user.email}
                      </div>
                    )}
                    {user.phone && (
                      <div className="flex items-center gap-1">
                        <Phone className="w-4 h-4" />
                        {user.phone}
                      </div>
                    )}
                  </div>
                  {(user.assigned_class || user.assigned_section) && (
                    <div className="flex items-center gap-1 text-sm font-medium text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full inline-flex">
                      <GraduationCap className="w-4 h-4" />
                      Class: {user.assigned_class || 'N/A'} {user.assigned_section ? `- Section ${user.assigned_section}` : ''}
                    </div>
                  )}
                </div>
              </div>
            </Card>

            {/* Summary Stats Cards */}
            <div className="grid md:grid-cols-3 gap-6">
              <Card className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Students</p>
                    <h3 className="text-4xl font-bold text-blue-600 mt-2">{stats.totalStudents}</h3>
                  </div>
                  <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center">
                    <Users className="w-8 h-8 text-white" />
                  </div>
                </div>
              </Card>

              <Card className="p-6 bg-gradient-to-br from-emerald-50 to-teal-50 border-emerald-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Avg Monthly Attendance</p>
                    <h3 className="text-4xl font-bold text-emerald-600 mt-2">{stats.avgAttendance}%</h3>
                  </div>
                  <div className="w-16 h-16 bg-emerald-500 rounded-full flex items-center justify-center">
                    <TrendingUp className="w-8 h-8 text-white" />
                  </div>
                </div>
              </Card>

              <Card className="p-6 bg-gradient-to-br from-red-50 to-rose-50 border-red-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Today's Absences</p>
                    <h3 className="text-4xl font-bold text-red-600 mt-2">{stats.todayAbsences}</h3>
                  </div>
                  <div className="w-16 h-16 bg-red-500 rounded-full flex items-center justify-center">
                    <UserX className="w-8 h-8 text-white" />
                  </div>
                </div>
              </Card>
            </div>

            {/* Students List */}
            <Card className="p-6">
              <div className="mb-6">
                <h2 className="text-xl font-semibold mb-4" style={{ fontFamily: 'Space Grotesk' }}>
                  My Students
                </h2>
                
                {/* Search and Filters */}
                <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                  <div className="md:col-span-2 relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input
                      type="text"
                      placeholder="Search by student or parent name..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                  
                  <select
                    value={filterBus}
                    onChange={(e) => setFilterBus(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="">All Buses</option>
                    {uniqueBuses.map(bus => (
                      <option key={bus} value={bus}>{bus}</option>
                    ))}
                  </select>

                  <select
                    value={filterAMStatus}
                    onChange={(e) => setFilterAMStatus(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="">All AM Status</option>
                    {statusOptions.map(status => (
                      <option key={status} value={status}>{getStatusLabel(status)}</option>
                    ))}
                  </select>

                  <select
                    value={filterPMStatus}
                    onChange={(e) => setFilterPMStatus(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
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
                        <td colSpan="6" className="px-4 py-8 text-center text-gray-500">
                          No students found
                        </td>
                      </tr>
                    ) : (
                      filteredStudents.map(student => (
                        <tr key={student.student_id} className="hover:bg-gray-50">
                          <td className="px-4 py-4">
                            <div className="font-medium text-gray-900">{student.name}</div>
                            <div className="text-sm text-gray-500">{student.class_name} - {student.section}</div>
                          </td>
                          <td className="px-4 py-4 text-sm text-gray-600">
                            {student.parent_name || 'N/A'}
                          </td>
                          <td className="px-4 py-4 text-sm text-gray-600">
                            {student.bus_number || 'N/A'}
                          </td>
                          <td className="px-4 py-4">
                            <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${getStatusClass(student.am_status)}`}>
                              {getStatusLabel(student.am_status)}
                            </span>
                          </td>
                          <td className="px-4 py-4">
                            <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${getStatusClass(student.pm_status)}`}>
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
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </Card>

            {/* Status Legend */}
            <Card className="p-6">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Status Legend</h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded status-gray"></div>
                  <span>Not Scanned</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded status-yellow"></div>
                  <span>On Board</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded status-green"></div>
                  <span>Reached</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded status-red"></div>
                  <span>Missed</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded status-blue"></div>
                  <span>Holiday</span>
                </div>
              </div>
            </Card>
          </div>

          {/* Notifications Sidebar - 1 column */}
          <div className="lg:col-span-1">
            <Card className="p-6 sticky top-24">
              <div className="flex items-center gap-2 mb-4">
                <Bell className="w-5 h-5 text-emerald-600" />
                <h2 className="text-lg font-semibold" style={{ fontFamily: 'Space Grotesk' }}>
                  Notifications
                </h2>
              </div>
              <div className="space-y-3 max-h-[calc(100vh-200px)] overflow-y-auto">
                {notifications.length === 0 ? (
                  <p className="text-sm text-gray-500 text-center py-8">No notifications</p>
                ) : (
                  notifications.map((notification) => (
                    <div
                      key={notification.notification_id}
                      className={`p-3 rounded-lg border text-sm ${
                        notification.type === 'mismatch'
                          ? 'bg-red-50 border-red-200'
                          : notification.type === 'update'
                          ? 'bg-blue-50 border-blue-200'
                          : notification.type === 'missed'
                          ? 'bg-orange-50 border-orange-200'
                          : 'bg-yellow-50 border-yellow-200'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        <Bell className="w-4 h-4 mt-0.5 flex-shrink-0" />
                        <div className="flex-1">
                          <p className="font-medium text-gray-900">{notification.message}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {new Date(notification.timestamp).toLocaleString()}
                          </p>
                          {notification.student_name && (
                            <p className="text-xs text-gray-600 mt-1">
                              Student: {notification.student_name}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Card>
          </div>
        </div>
      </div>

      {/* Student Detail Modal */}
      <StudentDetailModal
        student={selectedStudent}
        open={showStudentDetail}
        onClose={() => {
          setShowStudentDetail(false);
          setSelectedStudent(null);
        }}
      />
    </div>
  );
}
