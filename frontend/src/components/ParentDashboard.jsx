import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { toast } from 'sonner';
import { LogOut, Bus, Bell, Calendar, MapPin, Eye, EyeOff } from 'lucide-react';
import BusMap from './BusMap';
import AttendanceGrid from './AttendanceGrid';
import UserProfileHeader from './UserProfileHeader';
import StudentCard from './StudentCard';
import NotificationDetailModal from './NotificationDetailModal';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ParentDashboard({ user, onLogout }) {
  const [students, setStudents] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [selectedStudentDetails, setSelectedStudentDetails] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [busLocation, setBusLocation] = useState(null);
  const [showRoute, setShowRoute] = useState(false);
  const [route, setRoute] = useState(null);
  const [showNotificationDetail, setShowNotificationDetail] = useState(false);
  const [selectedNotification, setSelectedNotification] = useState(null);

  useEffect(() => {
    fetchStudents();
    fetchNotifications();
  }, []);

  useEffect(() => {
    if (selectedStudent) {
      fetchStudentDetails(selectedStudent.student_id);
      const interval = setInterval(() => {
        fetchBusLocation(selectedStudent.bus_id);
      }, 10000);

      fetchBusLocation(selectedStudent.bus_id);
      
      return () => clearInterval(interval);
    }
  }, [selectedStudent]);

  useEffect(() => {
    // Fetch route data when student details are loaded and route_id exists
    if (selectedStudentDetails && selectedStudentDetails.route_id) {
      fetchRoute(selectedStudentDetails.route_id);
    } else {
      setRoute(null);
      setShowRoute(false);
    }
  }, [selectedStudentDetails]);

  const fetchStudents = async () => {
    try {
      const response = await axios.get(`${API}/students`);
      setStudents(response.data);
      if (response.data.length > 0) {
        setSelectedStudent(response.data[0]);
      }
    } catch (error) {
      toast.error('Failed to load students');
    }
  };

  const fetchStudentDetails = async (studentId) => {
    try {
      const response = await axios.get(`${API}/students/${studentId}`);
      setSelectedStudentDetails(response.data);
    } catch (error) {
      console.error('Failed to load student details:', error);
    }
  };

  const fetchNotifications = async () => {
    try {
      const response = await axios.get(`${API}/get_notifications`);
      setNotifications(response.data);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  };

  const fetchBusLocation = async (busId) => {
    try {
      const response = await axios.get(`${API}/get_bus_location?bus_id=${busId}`);
      setBusLocation(response.data);
    } catch (error) {
      console.error('Failed to load bus location:', error);
    }
  };

  const fetchRoute = async (routeId) => {
    try {
      const response = await axios.get(`${API}/routes/${routeId}`);
      setRoute(response.data);
    } catch (error) {
      console.error('Failed to load route:', error);
      setRoute(null);
    }
  };

  const toggleRoute = () => {
    setShowRoute(!showRoute);
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50" data-testid="parent-dashboard">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Bus className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>Parent Dashboard</h1>
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

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* User Profile */}
        <UserProfileHeader user={user} />

        {/* Student Cards - Multiple Children */}
        {students.length > 1 ? (
          <div>
            <h2 className="text-xl font-semibold mb-4" style={{ fontFamily: 'Space Grotesk' }}>My Children</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
              {students.map((student) => (
                <div
                  key={student.student_id}
                  onClick={() => setSelectedStudent(student)}
                  className={`cursor-pointer ${selectedStudent?.student_id === student.student_id ? 'ring-2 ring-blue-500 rounded-lg' : ''}`}
                >
                  <StudentCard student={student} compact={true} />
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {selectedStudent && selectedStudentDetails && (
          <div className="space-y-6">
            {/* Student Details */}
            <StudentCard student={selectedStudentDetails} />

            <div className="grid lg:grid-cols-3 gap-6">
              {/* Left column - Map and Attendance */}
              <div className="lg:col-span-2 space-y-6">
                {/* Live Bus Map */}
                <Card className="p-6 card-hover">
                  <div className="flex items-center gap-2 mb-4">
                    <MapPin className="w-5 h-5 text-blue-600" />
                    <h2 className="text-xl font-semibold" style={{ fontFamily: 'Space Grotesk' }}>Live Bus Location</h2>
                    {busLocation && (
                      <span className="ml-auto text-xs text-gray-500">
                        Updated: {new Date(busLocation.timestamp).toLocaleTimeString()}
                      </span>
                    )}
                  </div>
                  <div className="h-96 rounded-lg overflow-hidden relative" data-testid="bus-map-container">
                    <BusMap location={busLocation} route={route} showRoute={showRoute} />
                    
                    {/* Toggle Route Button */}
                    {route && (
                      <button
                        onClick={toggleRoute}
                        data-testid="toggle-route-button"
                        className={`absolute top-4 right-4 z-[1000] flex items-center gap-2 px-4 py-2 rounded-lg shadow-lg transition-all ${
                          showRoute
                            ? 'bg-blue-600 text-white hover:bg-blue-700'
                            : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
                        }`}
                      >
                        {showRoute ? (
                          <>
                            <EyeOff className="w-4 h-4" />
                            <span className="text-sm font-medium">Hide Route</span>
                          </>
                        ) : (
                          <>
                            <Eye className="w-4 h-4" />
                            <span className="text-sm font-medium">Show Route</span>
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </Card>

                {/* Attendance Grid */}
                <Card className="p-6 card-hover">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-5 h-5 text-blue-600" />
                      <h2 className="text-xl font-semibold" style={{ fontFamily: 'Space Grotesk' }}>Attendance</h2>
                    </div>
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
                  <AttendanceGrid studentId={selectedStudent.student_id} />
                </Card>
              </div>

              {/* Right column - Notifications */}
              <div>
                <Card className="p-6 card-hover">
                  <div className="flex items-center gap-2 mb-4">
                    <Bell className="w-5 h-5 text-violet-600" />
                    <h2 className="text-xl font-semibold" style={{ fontFamily: 'Space Grotesk' }}>Notifications</h2>
                  </div>
                  <div className="space-y-3 max-h-96 overflow-y-auto" data-testid="notifications-container">
                    {notifications.length === 0 ? (
                      <p className="text-sm text-gray-500 text-center py-8">No notifications</p>
                    ) : (
                      notifications.slice(0, 5).map((notification) => (
                        <div
                          key={notification.notification_id}
                          data-testid={`notification-${notification.type}`}
                          onClick={() => handleNotificationClick(notification)}
                          className="flex items-start gap-4 p-4 rounded-lg border bg-gradient-to-r from-purple-50 to-pink-50 border-purple-200 shadow-sm hover:shadow-md transition-all cursor-pointer"
                        >
                          <div className="flex items-center justify-center w-10 h-10 rounded-full bg-white text-purple-600 shadow-sm flex-shrink-0">
                            <Bell className="w-5 h-5" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between gap-2">
                              <h3 className="font-semibold text-gray-800 truncate">
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
                                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-purple-600 text-white">
                                  New
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </Card>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
