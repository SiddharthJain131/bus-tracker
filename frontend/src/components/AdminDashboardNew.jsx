import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { toast } from 'sonner';
import {
  LogOut,
  Users,
  GraduationCap,
  Bus,
  Search,
  Eye,
  Edit,
  UserPlus,
  Calendar,
  Bell,
  Mail,
  Phone,
  MapPin,
  Trash2,
  Plus,
  Camera
} from 'lucide-react';
import StudentDetailModal from './StudentDetailModal';
import UserDetailModal from './UserDetailModal';
import BusDetailModal from './BusDetailModal';
import RouteDetailModal from './RouteDetailModal';
import EditStudentModalEnhanced from './EditStudentModalEnhanced';
import EditUserModalEnhanced from './EditUserModalEnhanced';
import AddStudentModal from './AddStudentModal';
import AddUserModal from './AddUserModal';
import AddBusModal from './AddBusModal';
import AddRouteModal from './AddRouteModal';
import EditBusModal from './EditBusModal';
import EditRouteModal from './EditRouteModal';
import HolidaysManagementModal from './HolidaysManagementModal';
import AddHolidayModal from './AddHolidayModal';
import EditHolidayModal from './EditHolidayModal';
import DeleteConfirmationDialog from './DeleteConfirmationDialog';
import PhotoViewerModal from './PhotoViewerModal';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Routes Table Component
function RoutesTable({ searchTerm, onViewRoute, onEditRoute, onDeleteRoute, onAddRoute }) {
  const [routes, setRoutes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRoutes();
  }, []);

  const fetchRoutes = async () => {
    try {
      const response = await axios.get(`${API}/routes`);
      setRoutes(response.data);
    } catch (error) {
      console.error('Failed to fetch routes:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredRoutes = routes.filter(r =>
    r.route_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b-2 border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Route Name</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Stops</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Remarks</th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan="4" className="px-4 py-8 text-center text-gray-500">
                  Loading routes...
                </td>
              </tr>
            ) : filteredRoutes.length === 0 ? (
              <tr>
                <td colSpan="4" className="px-4 py-8 text-center text-gray-500">
                  No routes found
                </td>
              </tr>
            ) : (
              filteredRoutes.map(route => (
                <tr key={route.route_id} className="hover:bg-gray-50">
                  <td className="px-4 py-4">
                    <div className="font-medium text-gray-900">{route.route_name}</div>
                  </td>
                  <td className="px-4 py-4 text-sm text-gray-600">
                    {route.stop_ids?.length || 0} stops
                  </td>
                  <td className="px-4 py-4 text-sm text-gray-600">
                    {route.remarks || 'N/A'}
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex items-center justify-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onViewRoute(route)}
                        className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                        title="View Details"
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onEditRoute(route)}
                        className="text-yellow-600 hover:text-yellow-700 hover:bg-yellow-50"
                        title="Edit Route"
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDeleteRoute(route)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        title="Delete Route"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}

export default function AdminDashboardNew({ user, onLogout }) {
  // Helper function to remove "Grade " prefix from class names
  const formatClassName = (className) => {
    if (!className) return 'N/A';
    return className.replace(/^Grade\s+/i, '');
  };

  const [activeTab, setActiveTab] = useState('overview');
  const [userSubTab, setUserSubTab] = useState('parents');
  const [busSubTab, setBusSubTab] = useState('buses');
  
  // Data states
  const [students, setStudents] = useState([]);
  const [users, setUsers] = useState([]);
  const [buses, setBuses] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [holidays, setHolidays] = useState([]);
  const [stats, setStats] = useState({ totalStudents: 0, totalTeachers: 0, totalBuses: 0 });
  const [searchTerm, setSearchTerm] = useState('');
  
  // Modal states
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedBus, setSelectedBus] = useState(null);
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [editStudent, setEditStudent] = useState(null);
  const [editUser, setEditUser] = useState(null);
  const [editBus, setEditBus] = useState(null);
  const [editRoute, setEditRoute] = useState(null);
  const [deleteItem, setDeleteItem] = useState(null);
  
  // Modal visibility
  const [showStudentDetail, setShowStudentDetail] = useState(false);
  const [showUserDetail, setShowUserDetail] = useState(false);
  const [showBusDetail, setShowBusDetail] = useState(false);
  const [showRouteDetail, setShowRouteDetail] = useState(false);
  const [showEditStudent, setShowEditStudent] = useState(false);
  const [showEditUser, setShowEditUser] = useState(false);
  const [showEditBus, setShowEditBus] = useState(false);
  const [showEditRoute, setShowEditRoute] = useState(false);
  const [showAddStudent, setShowAddStudent] = useState(false);
  const [showAddUser, setShowAddUser] = useState(false);
  const [showAddBus, setShowAddBus] = useState(false);
  const [showAddRoute, setShowAddRoute] = useState(false);
  const [showHolidaysManagement, setShowHolidaysManagement] = useState(false);
  const [showAddHoliday, setShowAddHoliday] = useState(false);
  const [showEditHoliday, setShowEditHoliday] = useState(false);
  const [editHoliday, setEditHoliday] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  
  // Photo viewer state
  const [showPhotoViewer, setShowPhotoViewer] = useState(false);
  const [isHoveringPhoto, setIsHoveringPhoto] = useState(false);
  const [currentUser, setCurrentUser] = useState(user);

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      const [studentsRes, usersRes, busesRes, routesRes, holidaysRes] = await Promise.all([
        axios.get(`${API}/students`),
        axios.get(`${API}/users`),
        axios.get(`${API}/buses`),
        axios.get(`${API}/routes`),
        axios.get(`${API}/admin/holidays`)
      ]);

      setStudents(studentsRes.data);
      setUsers(usersRes.data);
      setBuses(busesRes.data);
      setRoutes(routesRes.data);
      setHolidays(holidaysRes.data);

      // Calculate stats
      const teachers = usersRes.data.filter(u => u.role === 'teacher');
      setStats({
        totalStudents: studentsRes.data.length,
        totalTeachers: teachers.length,
        totalBuses: busesRes.data.length
      });
    } catch (error) {
      toast.error('Failed to load data');
      console.error(error);
    }
  };

  const handleViewStudent = (student) => {
    setSelectedStudent(student);
    setShowStudentDetail(true);
  };

  const handleEditStudent = (student) => {
    setEditStudent(student);
    setShowEditStudent(true);
  };

  const handleViewUser = (user) => {
    setSelectedUser(user);
    setShowUserDetail(true);
  };

  const handleEditUser = (user) => {
    setEditUser(user);
    setShowEditUser(true);
  };

  const handleViewBus = (bus) => {
    setSelectedBus(bus);
    setShowBusDetail(true);
  };

  const handleEditBus = (bus) => {
    setEditBus(bus);
    setShowEditBus(true);
  };

  const handleEditRoute = (route) => {
    setEditRoute(route);
    setShowEditRoute(true);
  };

  const handleDelete = (item, type) => {
    setDeleteItem({ ...item, type });
    setShowDeleteConfirm(true);
  };


  const handleProfilePhotoClick = () => {
    setShowPhotoViewer(true);
  };

  const handleProfilePhotoUpdate = (newPhotoUrl) => {
    // Update current user photo
    setCurrentUser(prev => ({
      ...prev,
      photo: `${BACKEND_URL}${newPhotoUrl}`
    }));
  };

  const confirmDelete = async () => {
    if (!deleteItem) return;
    
    setIsDeleting(true);
    try {
      let endpoint = '';
      let successMessage = '';
      
      switch (deleteItem.type) {
        case 'student':
          endpoint = `${API}/students/${deleteItem.student_id}`;
          successMessage = `Student ${deleteItem.name} deleted successfully`;
          break;
        case 'user':
          endpoint = `${API}/users/${deleteItem.user_id}`;
          successMessage = `User ${deleteItem.name} deleted successfully`;
          break;
        case 'bus':
          endpoint = `${API}/buses/${deleteItem.bus_id}`;
          successMessage = `Bus ${deleteItem.bus_number} deleted successfully`;
          break;
        case 'route':
          endpoint = `${API}/routes/${deleteItem.route_id}`;
          successMessage = `Route ${deleteItem.route_name} deleted successfully`;
          break;
        default:
          throw new Error('Invalid delete type');
      }
      
      await axios.delete(endpoint);
      toast.success(successMessage);
      fetchAllData();
      setShowDeleteConfirm(false);
      setDeleteItem(null);
    } catch (error) {
      console.error('Delete error:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete item');
    } finally {
      setIsDeleting(false);
    }
  };

  // Filter functions
  const filteredStudents = students.filter(s =>
    s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (s.parent_name && s.parent_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (s.class_name && s.class_name.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const filteredUsers = users.filter(u =>
    u.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const parentUsers = filteredUsers.filter(u => u.role === 'parent');
  const teacherUsers = filteredUsers.filter(u => u.role === 'teacher');
  const adminUsers = filteredUsers.filter(u => u.role === 'admin');

  const filteredBuses = buses.filter(b =>
    b.bus_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    b.driver_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-violet-50" data-testid="admin-dashboard">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-violet-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Users className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                  Admin Dashboard
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
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4 mb-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="students">Students</TabsTrigger>
            <TabsTrigger value="users">Users</TabsTrigger>
            <TabsTrigger value="buses">Buses & Routes</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Admin Profile */}
            <Card className="p-6">
              <h2 className="text-xl font-semibold mb-4" style={{ fontFamily: 'Space Grotesk' }}>
                Admin Profile
              </h2>
              <div className="flex items-center gap-6">
                <div 
                  className="relative w-20 h-20 bg-gradient-to-br from-violet-400 to-purple-600 rounded-full flex items-center justify-center text-white text-3xl font-bold overflow-hidden cursor-pointer"
                  onClick={handleProfilePhotoClick}
                >
                  {currentUser.photo ? (
                    <img src={currentUser.photo} alt={currentUser.name} className="w-full h-full rounded-full object-cover" />
                  ) : (
                    currentUser.name.charAt(0).toUpperCase()
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
                  {user.address && (
                    <div className="flex items-center gap-1 text-sm text-gray-600">
                      <MapPin className="w-4 h-4" />
                      {user.address}
                    </div>
                  )}
                </div>
              </div>
            </Card>

            {/* Quick Stats */}
            <div className="grid md:grid-cols-3 gap-6">
              <Card className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Students</p>
                    <h3 className="text-4xl font-bold text-blue-600 mt-2">{stats.totalStudents}</h3>
                  </div>
                  <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center">
                    <GraduationCap className="w-8 h-8 text-white" />
                  </div>
                </div>
              </Card>

              <Card className="p-6 bg-gradient-to-br from-emerald-50 to-teal-50 border-emerald-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Teachers</p>
                    <h3 className="text-4xl font-bold text-emerald-600 mt-2">{stats.totalTeachers}</h3>
                  </div>
                  <div className="w-16 h-16 bg-emerald-500 rounded-full flex items-center justify-center">
                    <Users className="w-8 h-8 text-white" />
                  </div>
                </div>
              </Card>

              <Card className="p-6 bg-gradient-to-br from-orange-50 to-amber-50 border-orange-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Buses</p>
                    <h3 className="text-4xl font-bold text-orange-600 mt-2">{stats.totalBuses}</h3>
                  </div>
                  <div className="w-16 h-16 bg-orange-500 rounded-full flex items-center justify-center">
                    <Bus className="w-8 h-8 text-white" />
                  </div>
                </div>
              </Card>
            </div>

            {/* Recent Activity / Holidays */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-violet-600" />
                  <h3 className="text-lg font-semibold" style={{ fontFamily: 'Space Grotesk' }}>
                    Upcoming Holidays
                  </h3>
                </div>
                <Button
                  onClick={() => setShowHolidaysManagement(true)}
                  variant="outline"
                  size="sm"
                  className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 border-blue-200"
                >
                  <Edit className="w-4 h-4 mr-1" />
                  Edit Holidays
                </Button>
              </div>
              <div className="space-y-2">
                {holidays.length === 0 ? (
                  <p className="text-sm text-gray-500 text-center py-4">No holidays scheduled</p>
                ) : (
                  holidays.slice(0, 5).map(holiday => (
                    <div key={holiday.holiday_id} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium text-gray-900">{holiday.name}</p>
                        <p className="text-sm text-gray-600">{new Date(holiday.date).toLocaleDateString()}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Card>
          </TabsContent>

          {/* Students Tab */}
          <TabsContent value="students" className="space-y-6">
            <Card className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold" style={{ fontFamily: 'Space Grotesk' }}>
                  Students Management
                </h2>
                <div className="flex gap-3">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input
                      type="text"
                      placeholder="Search students..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 w-64"
                    />
                  </div>
                  <Button
                    onClick={() => setShowAddStudent(true)}
                    className="bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white"
                  >
                    <UserPlus className="w-4 h-4 mr-2" />
                    Add Student
                  </Button>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b-2 border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Roll No</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Name</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Phone</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Parent</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Class</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Section</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Bus</th>
                      <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {filteredStudents.length === 0 ? (
                      <tr>
                        <td colSpan="8" className="px-4 py-8 text-center text-gray-500">
                          No students found
                        </td>
                      </tr>
                    ) : (
                      filteredStudents.map(student => (
                        <tr key={student.student_id} className="hover:bg-gray-50">
                          <td className="px-4 py-4">
                            <div className="font-medium text-gray-900">{student.roll_number || 'N/A'}</div>
                          </td>
                          <td className="px-4 py-4">
                            <div className="font-medium text-gray-900">{student.name}</div>
                          </td>
                          <td className="px-4 py-4 text-sm text-gray-600">{student.phone || 'N/A'}</td>
                          <td className="px-4 py-4 text-sm text-gray-600">{student.parent_name || 'N/A'}</td>
                          <td className="px-4 py-4 text-sm text-gray-600">{formatClassName(student.class_name)}</td>
                          <td className="px-4 py-4 text-sm text-gray-600">{student.section || 'N/A'}</td>
                          <td className="px-4 py-4 text-sm text-gray-600">{student.bus_number || 'N/A'}</td>
                          <td className="px-4 py-4">
                            <div className="flex items-center justify-center gap-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleViewStudent(student)}
                                className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                                title="View Details"
                              >
                                <Eye className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleEditStudent(student)}
                                className="text-yellow-600 hover:text-yellow-700 hover:bg-yellow-50"
                                title="Edit Student"
                              >
                                <Edit className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDelete(student, 'student')}
                                className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                title="Delete Student"
                              >
                                <Trash2 className="w-4 h-4" />
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
          </TabsContent>

          {/* Users Tab */}
          <TabsContent value="users" className="space-y-6">
            <Card className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold" style={{ fontFamily: 'Space Grotesk' }}>
                  Users Management
                </h2>
                <div className="flex gap-3">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input
                      type="text"
                      placeholder="Search users..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 w-64"
                    />
                  </div>
                  <Button
                    onClick={() => setShowAddUser(true)}
                    className="bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white"
                  >
                    <UserPlus className="w-4 h-4 mr-2" />
                    Add User
                  </Button>
                </div>
              </div>

              <Tabs value={userSubTab} onValueChange={setUserSubTab}>
                <TabsList className="grid w-full grid-cols-3 mb-6">
                  <TabsTrigger value="parents">Parents ({parentUsers.length})</TabsTrigger>
                  <TabsTrigger value="teachers">Teachers ({teacherUsers.length})</TabsTrigger>
                  <TabsTrigger value="admins">Admins ({adminUsers.length})</TabsTrigger>
                </TabsList>

                {['parents', 'teachers', 'admins'].map(role => (
                  <TabsContent key={role} value={role}>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gray-50 border-b-2 border-gray-200">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Name</th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Role</th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Email</th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Phone</th>
                            <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                          {(role === 'parents' ? parentUsers : role === 'teachers' ? teacherUsers : adminUsers).length === 0 ? (
                            <tr>
                              <td colSpan="5" className="px-4 py-8 text-center text-gray-500">
                                No {role} found
                              </td>
                            </tr>
                          ) : (
                            (role === 'parents' ? parentUsers : role === 'teachers' ? teacherUsers : adminUsers).map(u => {
                              const isElevated = user.is_elevated_admin || false;
                              const canEditAdmin = u.role !== 'admin' || u.user_id === user.user_id || isElevated;
                              const canDeleteAdmin = u.role !== 'admin' || (u.user_id !== user.user_id && isElevated);
                              
                              return (
                                <tr key={u.user_id} className="hover:bg-gray-50">
                                  <td className="px-4 py-4">
                                    <div className="flex items-center gap-2">
                                      <span className="font-medium text-gray-900">{u.name}</span>
                                      {u.is_elevated_admin && (
                                        <span 
                                          className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gradient-to-r from-amber-100 to-yellow-100 text-amber-800 border border-amber-300"
                                          title="Elevated Admin - Can manage other admins"
                                        >
                                          ⭐ Elevated
                                        </span>
                                      )}
                                    </div>
                                  </td>
                                  <td className="px-4 py-4">
                                    <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                                      u.role === 'admin' ? 'bg-purple-100 text-purple-800' :
                                      u.role === 'teacher' ? 'bg-emerald-100 text-emerald-800' :
                                      'bg-blue-100 text-blue-800'
                                    }`}>
                                      {u.role}
                                    </span>
                                  </td>
                                  <td className="px-4 py-4 text-sm text-gray-600">{u.email}</td>
                                  <td className="px-4 py-4 text-sm text-gray-600">{u.phone || 'N/A'}</td>
                                  <td className="px-4 py-4">
                                    <div className="flex items-center justify-center gap-2">
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => handleViewUser(u)}
                                        className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                                        title="View Details"
                                      >
                                        <Eye className="w-4 h-4" />
                                      </Button>
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => handleEditUser(u)}
                                        className={canEditAdmin ? "text-yellow-600 hover:text-yellow-700 hover:bg-yellow-50" : "text-gray-400 cursor-not-allowed"}
                                        disabled={!canEditAdmin}
                                        title={canEditAdmin ? "Edit User" : "Only elevated admins can edit other admins"}
                                      >
                                        <Edit className="w-4 h-4" />
                                      </Button>
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => handleDelete(u, 'user')}
                                        className={canDeleteAdmin ? "text-red-600 hover:text-red-700 hover:bg-red-50" : "text-gray-400 cursor-not-allowed"}
                                        disabled={!canDeleteAdmin}
                                        title={
                                          u.user_id === user.user_id ? 'Cannot delete yourself' :
                                          !canDeleteAdmin ? 'Only elevated admins can delete other admins' :
                                          'Delete User'
                                        }
                                      >
                                        <Trash2 className="w-4 h-4" />
                                      </Button>
                                    </div>
                                  </td>
                                </tr>
                              );
                            })
                          )}
                        </tbody>
                      </table>
                    </div>
                  </TabsContent>
                ))}
              </Tabs>
            </Card>
          </TabsContent>

          {/* Buses & Routes Tab */}
          <TabsContent value="buses" className="space-y-6">
            <Card className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold" style={{ fontFamily: 'Space Grotesk' }}>
                  Buses & Routes Management
                </h2>
                <div className="flex gap-3">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input
                      type="text"
                      placeholder="Search..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 w-64"
                    />
                  </div>
                  <Button
                    onClick={() => setShowAddBus(true)}
                    className="bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700 text-white"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Add Bus
                  </Button>
                  <Button
                    onClick={() => setShowAddRoute(true)}
                    className="bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Add Route
                  </Button>
                </div>
              </div>

              <Tabs value={busSubTab} onValueChange={setBusSubTab}>
                <TabsList className="grid w-full grid-cols-2 mb-6">
                  <TabsTrigger value="buses">Buses ({buses.length})</TabsTrigger>
                  <TabsTrigger value="routes">Routes</TabsTrigger>
                </TabsList>

                <TabsContent value="buses">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50 border-b-2 border-gray-200">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Bus No</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Driver</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Phone</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Route</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Capacity</th>
                          <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {filteredBuses.length === 0 ? (
                          <tr>
                            <td colSpan="6" className="px-4 py-8 text-center text-gray-500">
                              No buses found
                            </td>
                          </tr>
                        ) : (
                          filteredBuses.map(bus => (
                            <tr key={bus.bus_id} className="hover:bg-gray-50">
                              <td className="px-4 py-4">
                                <div className="font-medium text-gray-900">{bus.bus_number}</div>
                              </td>
                              <td className="px-4 py-4 text-sm text-gray-600">{bus.driver_name}</td>
                              <td className="px-4 py-4 text-sm text-gray-600">{bus.driver_phone}</td>
                              <td className="px-4 py-4 text-sm text-gray-600">{bus.route_name || 'N/A'}</td>
                              <td className="px-4 py-4 text-sm text-gray-600">{bus.capacity} students</td>
                              <td className="px-4 py-4">
                                <div className="flex items-center justify-center gap-2">
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleViewBus(bus)}
                                    className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                                    title="View Details"
                                  >
                                    <Eye className="w-4 h-4" />
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleEditBus(bus)}
                                    className="text-yellow-600 hover:text-yellow-700 hover:bg-yellow-50"
                                    title="Edit Bus"
                                  >
                                    <Edit className="w-4 h-4" />
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleDelete(bus, 'bus')}
                                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                    title="Delete Bus"
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </Button>
                                </div>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </TabsContent>

                <TabsContent value="routes">
                  <RoutesTable 
                    searchTerm={searchTerm}
                    onViewRoute={(route) => {
                      setSelectedRoute(route);
                      setShowRouteDetail(true);
                    }}
                    onEditRoute={handleEditRoute}
                    onDeleteRoute={(route) => handleDelete(route, 'route')}
                    onAddRoute={() => setShowAddRoute(true)}
                  />
                </TabsContent>
              </Tabs>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Modals */}
      <StudentDetailModal
        student={selectedStudent}
        open={showStudentDetail}
        onClose={() => {
          setShowStudentDetail(false);
          setSelectedStudent(null);
        }}
        userRole={currentUser.role}
      />

      <UserDetailModal
        user={selectedUser}
        open={showUserDetail}
        onClose={() => {
          setShowUserDetail(false);
          setSelectedUser(null);
        }}
      />

      <BusDetailModal
        bus={selectedBus}
        open={showBusDetail}
        onClose={() => {
          setShowBusDetail(false);
          setSelectedBus(null);
        }}
      />

      <RouteDetailModal
        route={selectedRoute}
        open={showRouteDetail}
        onClose={() => {
          setShowRouteDetail(false);
          setSelectedRoute(null);
        }}
      />

      <EditStudentModalEnhanced
        student={editStudent}
        open={showEditStudent}
        onClose={() => {
          setShowEditStudent(false);
          setEditStudent(null);
        }}
        onSuccess={fetchAllData}
        adminName={user.name}
      />

      <EditUserModalEnhanced
        user={editUser}
        currentUser={user}
        open={showEditUser}
        onClose={() => {
          setShowEditUser(false);
          setEditUser(null);
        }}
        onSuccess={fetchAllData}
      />

      <AddStudentModal
        open={showAddStudent}
        onClose={() => setShowAddStudent(false)}
        onSuccess={fetchAllData}
      />

      <AddUserModal
        open={showAddUser}
        onClose={() => setShowAddUser(false)}
        onSuccess={fetchAllData}
      />

      <AddBusModal
        open={showAddBus}
        onClose={() => setShowAddBus(false)}
        onSuccess={fetchAllData}
      />

      <AddRouteModal
        open={showAddRoute}
        onClose={() => setShowAddRoute(false)}
        onSuccess={fetchAllData}
      />

      <EditBusModal
        bus={editBus}
        open={showEditBus}
        onClose={() => {
          setShowEditBus(false);
          setEditBus(null);
        }}
        onSuccess={fetchAllData}
      />

      <EditRouteModal
        route={editRoute}
        open={showEditRoute}
        onClose={() => {
          setShowEditRoute(false);
          setEditRoute(null);
        }}
        onSuccess={fetchAllData}
      />

      <AddHolidayModal
        open={showAddHoliday}
        onClose={() => setShowAddHoliday(false)}
        onSuccess={fetchAllData}
      />

      <EditHolidayModal
        holiday={editHoliday}
        open={showEditHoliday}
        onClose={() => {
          setShowEditHoliday(false);
          setEditHoliday(null);
        }}
        onSuccess={fetchAllData}
      />

      <HolidaysManagementModal
        open={showHolidaysManagement}
        onClose={() => setShowHolidaysManagement(false)}
        onSuccess={fetchAllData}
      />

      <DeleteConfirmationDialog
        open={showDeleteConfirm}
        onClose={() => {
          setShowDeleteConfirm(false);
          setDeleteItem(null);
        }}
        onConfirm={confirmDelete}
        title="Delete Confirmation"
        itemName={deleteItem?.name || deleteItem?.bus_number || deleteItem?.route_name}
        itemType={deleteItem?.type}
        isDeleting={isDeleting}
      />

      <PhotoViewerModal
        open={showPhotoViewer}
        onClose={() => setShowPhotoViewer(false)}
        photoUrl={currentUser.photo}
        userName={currentUser.name}
        canEdit={true}
        uploadEndpoint={`${API}/users/me/photo`}
        onPhotoUpdate={handleProfilePhotoUpdate}
      />
    </div>
  );
}
