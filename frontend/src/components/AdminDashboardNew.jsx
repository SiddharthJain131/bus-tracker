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
  Edit,
  UserPlus,
  Calendar,
  Bell,
  Mail,
  Phone,
  MapPin,
  Trash2,
  Plus,
  Camera,
  Eye
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
import PhotoAvatar from './PhotoAvatar';
import NotificationDetailModal from './NotificationDetailModal';
import BackupManagement from './BackupManagement';
import { formatClassName } from '../utils/helpers';

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
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="w-full bg-white">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Route Name</th>
              <th className="px-4 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Stops</th>
              <th className="px-4 py-4 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Remarks</th>
              <th className="px-4 py-4 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
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
                <tr key={route.route_id} className="hover:bg-gray-50 transition-colors">
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
                        className="text-admin-primary hover:text-admin-hover hover:bg-admin-light"
                        title="View Details"
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onEditRoute(route)}
                        className="text-amber-600 hover:text-amber-700 hover:bg-amber-50"
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

  const [activeTab, setActiveTab] = useState('overview');
  const [userSubTab, setUserSubTab] = useState('parents');
  const [busSubTab, setBusSubTab] = useState('buses');
  
  // Data states
  const [students, setStudents] = useState([]);
  const [users, setUsers] = useState([]);
  const [buses, setBuses] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [holidays, setHolidays] = useState([]);
  const [showAllHolidays, setShowAllHolidays] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [stats, setStats] = useState({ totalStudents: 0, totalTeachers: 0, totalBuses: 0 });
  const [searchTerm, setSearchTerm] = useState('');
  const [searchBy, setSearchBy] = useState('all');
  
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
  const [showNotificationDetail, setShowNotificationDetail] = useState(false);
  const [selectedNotification, setSelectedNotification] = useState(null);
  
  // Photo viewer state
  const [showPhotoViewer, setShowPhotoViewer] = useState(false);
  const [currentUser, setCurrentUser] = useState(user);

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      const [studentsRes, usersRes, busesRes, routesRes, holidaysRes, notificationsRes] = await Promise.all([
        axios.get(`${API}/students`),
        axios.get(`${API}/users`),
        axios.get(`${API}/buses`),
        axios.get(`${API}/routes`),
        axios.get(`${API}/admin/holidays`),
        axios.get(`${API}/get_notifications`)
      ]);

      setStudents(studentsRes.data);
      setUsers(usersRes.data);
      setBuses(busesRes.data);
      setRoutes(routesRes.data);
      setHolidays(holidaysRes.data);
      setNotifications(notificationsRes.data);

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
    // newPhotoUrl already includes BACKEND_URL and cache-busting timestamp
    setCurrentUser(prev => ({
      ...prev,
      photo: newPhotoUrl.startsWith('http') ? newPhotoUrl : `${BACKEND_URL}${newPhotoUrl}`
    }));
  };

  const handleNotificationClick = async (notification) => {
    setSelectedNotification(notification);
    setShowNotificationDetail(true);
    
    // Mark as read if unread
    if (!notification.read) {
      try {
        await axios.post(`${API}/mark_notification_read?notification_id=${notification.notification_id}`);
        // Refresh notifications
        const notificationsRes = await axios.get(`${API}/get_notifications`);
        setNotifications(notificationsRes.data);
      } catch (error) {
        console.error('Error marking notification as read:', error);
      }
    }
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
          endpoint = `${API}/buses/${deleteItem.bus_number}`;
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

  // Filter functions with dropdown-based search
  const filteredStudents = students.filter(s => {
    if (!searchTerm.trim()) return true;
    
    const term = searchTerm.toLowerCase().trim();
    
    switch (searchBy) {
      case 'all':
        return s.name.toLowerCase().includes(term) ||
          (s.parent_name && s.parent_name.toLowerCase().includes(term)) ||
          (s.class_name && s.class_name.toLowerCase().includes(term)) ||
          (s.bus_number && s.bus_number.toLowerCase().includes(term)) ||
          (s.roll_number && s.roll_number.toLowerCase().includes(term));
      case 'name':
        return s.name.toLowerCase().includes(term);
      case 'roll':
        return s.roll_number && s.roll_number.toLowerCase().includes(term);
      case 'bus':
        return s.bus_number && s.bus_number.toLowerCase().includes(term);
      case 'class':
        return s.class_name && s.class_name.toLowerCase().includes(term);
      case 'parent':
        return s.parent_name && s.parent_name.toLowerCase().includes(term);
      case 'teacher':
        return s.teacher_name && s.teacher_name.toLowerCase().includes(term);
      default:
        return true;
    }
  });

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
    <div className="min-h-screen dashboard-bg" data-testid="admin-dashboard">
      {/* Header */}
      <header className="dashboard-panel admin-accent-border border-b dashboard-separator shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-gradient-to-br from-admin-secondary to-admin-primary rounded-xl flex items-center justify-center shadow-md">
                <Users className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Admin Dashboard
                </h1>
                <p className="text-sm text-gray-600 mt-1">Welcome, {user.name}</p>
              </div>
            </div>
            <Button onClick={onLogout} variant="outline" className="flex items-center gap-2 border-gray-300 hover:border-admin-primary hover:text-admin-primary transition-colors">
              <LogOut className="w-4 h-4" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-5 mb-6 dashboard-panel shadow-md">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="students">Students</TabsTrigger>
            <TabsTrigger value="users">Users</TabsTrigger>
            <TabsTrigger value="buses">Buses & Routes</TabsTrigger>
            <TabsTrigger value="backups">Backups</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Admin Profile */}
            <Card className="p-6 dashboard-card admin-accent-border hover:shadow-lg transition-shadow">
              <h2 className="text-xl font-semibold mb-5 text-gray-900">
                Admin Profile
              </h2>
              <div className="flex items-center gap-6">
                <PhotoAvatar
                  photoUrl={currentUser.photo ? `${BACKEND_URL}${currentUser.photo}` : null}
                  userName={currentUser.name}
                  size="lg"
                  onClick={handleProfilePhotoClick}
                  gradientFrom="admin-secondary"
                  gradientTo="admin-primary"
                />
                <div className="flex-1 space-y-2">
                  <h3 className="text-2xl font-bold text-gray-900">{user.name}</h3>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    {user.email && (
                      <div className="flex items-center gap-2">
                        <Mail className="w-4 h-4 text-admin-primary" />
                        {user.email}
                      </div>
                    )}
                    {user.phone && (
                      <div className="flex items-center gap-2">
                        <Phone className="w-4 h-4 text-admin-primary" />
                        {user.phone}
                      </div>
                    )}
                  </div>
                  {user.address && (
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <MapPin className="w-4 h-4 text-admin-primary" />
                      {user.address}
                    </div>
                  )}
                </div>
              </div>
            </Card>

            {/* Quick Stats */}
            <div className="grid md:grid-cols-3 gap-6">
              <Card className="p-6 dashboard-card admin-accent-border hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 mb-2">Total Students</p>
                    <h3 className="text-4xl font-bold text-admin-primary">{stats.totalStudents}</h3>
                  </div>
                  <div className="w-16 h-16 bg-gradient-to-br from-admin-secondary to-admin-primary rounded-xl flex items-center justify-center shadow-md">
                    <GraduationCap className="w-8 h-8 text-white" />
                  </div>
                </div>
              </Card>

              <Card className="p-6 dashboard-card admin-accent-border hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 mb-2">Total Teachers</p>
                    <h3 className="text-4xl font-bold text-admin-primary">{stats.totalTeachers}</h3>
                  </div>
                  <div className="w-16 h-16 bg-gradient-to-br from-admin-secondary to-admin-primary rounded-xl flex items-center justify-center shadow-md">
                    <Users className="w-8 h-8 text-white" />
                  </div>
                </div>
              </Card>

              <Card className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 mb-2">Total Buses</p>
                    <h3 className="text-4xl font-bold text-admin-primary">{stats.totalBuses}</h3>
                  </div>
                  <div className="w-16 h-16 bg-gradient-to-br from-admin-secondary to-admin-primary rounded-xl flex items-center justify-center shadow-md">
                    <Bus className="w-8 h-8 text-white" />
                  </div>
                </div>
              </Card>
            </div>

            {/* Recent Activity / Holidays & Notifications */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm">
              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-admin-light rounded-lg flex items-center justify-center">
                    <Calendar className="w-5 h-5 text-admin-primary" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Upcoming Holidays
                  </h3>
                </div>
                <Button
                  onClick={() => setShowHolidaysManagement(true)}
                  variant="outline"
                  size="sm"
                  className="text-admin-primary hover:text-admin-hover hover:bg-admin-light border-admin-primary/30 transition-colors"
                >
                  <Edit className="w-4 h-4 mr-1" />
                  Edit Holidays
                </Button>
              </div>
              <div className="space-y-3">
                {(() => {
                  const getTodayInKolkata = () => {
                    const now = new Date();
                    const kolkataDate = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
                    kolkataDate.setHours(0, 0, 0, 0);
                    return kolkataDate;
                  };

                  const today = getTodayInKolkata();
                  const upcoming = [];
                  const past = [];

                  holidays.forEach(holiday => {
                    const holidayDate = new Date(holiday.date);
                    holidayDate.setHours(0, 0, 0, 0);
                    if (holidayDate > today) {
                      upcoming.push({ ...holiday, isPast: false });
                    } else {
                      past.push({ ...holiday, isPast: true });
                    }
                  });

                  upcoming.sort((a, b) => new Date(a.date) - new Date(b.date));
                  past.sort((a, b) => new Date(b.date) - new Date(a.date));

                  const displayedHolidays = showAllHolidays ? [...upcoming, ...past] : upcoming;

                  const formatDate = (dateStr) => {
                    const date = new Date(dateStr);
                    const month = date.toLocaleDateString('en-US', { month: 'short' });
                    const day = date.getDate();
                    return { month, day };
                  };

                  return (
                    <>
                      {past.length > 0 && (
                        <div className="mb-3">
                          <button
                            onClick={() => setShowAllHolidays(!showAllHolidays)}
                            aria-expanded={showAllHolidays}
                            className="w-full px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-600 rounded-lg text-sm font-medium transition-colors shadow-sm"
                          >
                            {showAllHolidays ? 'Show upcoming only' : 'Show all holidays'}
                          </button>
                        </div>
                      )}
                      {displayedHolidays.length === 0 ? (
                        <p className="text-sm text-gray-500 text-center py-4">No holidays scheduled</p>
                      ) : (
                        displayedHolidays.slice(0, showAllHolidays ? undefined : 5).map(holiday => {
                          const { month, day } = formatDate(holiday.date);
                          return (
                            <div
                              key={holiday.holiday_id}
                              className={`flex items-start gap-4 p-4 rounded-lg border transition-all ${
                                holiday.isPast
                                  ? 'bg-gray-50 border-gray-200 opacity-60'
                                  : 'bg-admin-light/50 border-admin-primary/20 hover:border-admin-primary/40'
                              }`}
                            >
                              <div className={`flex flex-col items-center justify-center w-16 h-16 rounded-lg flex-shrink-0 ${
                                holiday.isPast ? 'bg-gray-200 text-gray-600' : 'bg-white text-admin-primary shadow-sm border border-admin-primary/20'
                              }`}>
                                <span className="text-xs font-semibold uppercase">{month}</span>
                                <span className="text-2xl font-bold">{day}</span>
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <h3 className={`font-semibold ${holiday.isPast ? 'text-gray-600' : 'text-gray-900'}`}>
                                    {holiday.name}
                                  </h3>
                                  {holiday.isPast && (
                                    <span className="px-2 py-0.5 bg-gray-300 text-gray-600 text-xs rounded-full">
                                      Past
                                    </span>
                                  )}
                                </div>
                                {holiday.description && (
                                  <p className={`text-sm mt-1 ${holiday.isPast ? 'text-gray-500' : 'text-gray-600'}`}>
                                    {holiday.description}
                                  </p>
                                )}
                              </div>
                            </div>
                          );
                        })
                      )}
                    </>
                  );
                })()}
              </div>
            </Card>

            <Card className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm">
              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-admin-light rounded-lg flex items-center justify-center">
                    <Bell className="w-5 h-5 text-admin-primary" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Notifications
                  </h3>
                </div>
              </div>
              <div className="space-y-3">
                {notifications.length === 0 ? (
                  <p className="text-sm text-gray-500 text-center py-4">No notifications</p>
                ) : (
                  notifications.slice(0, 5).map(notification => {
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

                    return (
                      <div
                        key={notification.notification_id}
                        onClick={() => handleNotificationClick(notification)}
                        className="flex items-start gap-4 p-4 rounded-lg border border-gray-200 bg-white hover:border-admin-primary/40 hover:shadow-md transition-all cursor-pointer"
                      >
                        <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-admin-light text-admin-primary flex-shrink-0">
                          <Bell className="w-5 h-5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <h3 className="font-semibold text-gray-900 truncate">
                              {notification.title}
                            </h3>
                            {notification.timestamp && (
                              <span className="text-xs text-gray-500 whitespace-nowrap">
                                {formatTimestamp(notification.timestamp)}
                              </span>
                            )}
                          </div>
                          {notification.message && (
                            <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                              {notification.message}
                            </p>
                          )}
                          {!notification.read && (
                            <div className="mt-2">
                              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-admin-primary text-white">
                                New
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </Card>
            </div>
          </TabsContent>

          {/* Students Tab */}
          <TabsContent value="students" className="space-y-6">
            <Card className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold" style={{ fontFamily: 'Space Grotesk' }}>
                  Students Management
                </h2>
                <div className="flex gap-3">
                  <select
                    value={searchBy}
                    onChange={(e) => setSearchBy(e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-sm"
                  >
                    <option value="all">All Fields</option>
                    <option value="name">Name</option>
                    <option value="roll">Roll No</option>
                    <option value="bus">Bus</option>
                    <option value="class">Class</option>
                    <option value="parent">Parent</option>
                    <option value="teacher">Teacher</option>
                  </select>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input
                      type="text"
                      placeholder="Search for..."
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
                  <thead className="bg-muted/50 border-b-2 border-border">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-bold text-navy uppercase tracking-wider">Roll No</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-navy uppercase tracking-wider">Name</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-navy uppercase tracking-wider">Phone</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-navy uppercase tracking-wider">Parent</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-navy uppercase tracking-wider">Class</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-navy uppercase tracking-wider">Section</th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-navy uppercase tracking-wider">Bus</th>
                      <th className="px-4 py-3 text-center text-xs font-bold text-navy uppercase tracking-wider">Actions</th>
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
                        <tr key={student.student_id} className="hover:bg-muted/30">
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
                        <thead className="bg-muted/50 border-b-2 border-border">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-bold text-navy uppercase tracking-wider">Name</th>
                            <th className="px-4 py-3 text-left text-xs font-bold text-navy uppercase tracking-wider">Role</th>
                            <th className="px-4 py-3 text-left text-xs font-bold text-navy uppercase tracking-wider">Email</th>
                            <th className="px-4 py-3 text-left text-xs font-bold text-navy uppercase tracking-wider">Phone</th>
                            <th className="px-4 py-3 text-center text-xs font-bold text-navy uppercase tracking-wider">Actions</th>
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
                                <tr key={u.user_id} className="hover:bg-muted/30">
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
                      <thead className="bg-muted/50 border-b-2 border-border">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-bold text-navy uppercase tracking-wider">Bus No</th>
                          <th className="px-4 py-3 text-left text-xs font-bold text-navy uppercase tracking-wider">Driver</th>
                          <th className="px-4 py-3 text-left text-xs font-bold text-navy uppercase tracking-wider">Phone</th>
                          <th className="px-4 py-3 text-left text-xs font-bold text-navy uppercase tracking-wider">Route</th>
                          <th className="px-4 py-3 text-left text-xs font-bold text-navy uppercase tracking-wider">Capacity</th>
                          <th className="px-4 py-3 text-center text-xs font-bold text-navy uppercase tracking-wider">Actions</th>
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
                            <tr key={bus.bus_number} className="hover:bg-muted/30">
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

          {/* Backups Tab */}
          <TabsContent value="backups">
            <BackupManagement />
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
        photoUrl={currentUser.photo ? `${BACKEND_URL}${currentUser.photo}` : null}
        userName={currentUser.name}
        canEdit={true}
        uploadEndpoint={`${API}/users/me/photo`}
        onPhotoUpdate={handleProfilePhotoUpdate}
      />

      <NotificationDetailModal
        notification={selectedNotification}
        isOpen={showNotificationDetail}
        onClose={() => setShowNotificationDetail(false)}
      />
    </div>
  );
}
