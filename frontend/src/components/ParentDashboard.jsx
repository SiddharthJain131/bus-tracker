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
import NotificationBell from './NotificationBell';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ParentDashboard({ user, onLogout }) {
  const [students, setStudents] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [selectedStudentDetails, setSelectedStudentDetails] = useState(null);
  const [busLocation, setBusLocation] = useState(null);
  const [showRoute, setShowRoute] = useState(false);
  const [route, setRoute] = useState(null);

  useEffect(() => {
    fetchStudents();
    fetchNotifications();
  }, []);

  useEffect(() => {
    if (selectedStudent) {
      fetchStudentDetails(selectedStudent.student_id);
      const interval = setInterval(() => {
        fetchBusLocation(selectedStudent.bus_number);
      }, 10000);

      fetchBusLocation(selectedStudent.bus_number);
      
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

  const fetchBusLocation = async (busNumber) => {
    try {
      const response = await axios.get(`${API}/get_bus_location?bus_number=${busNumber}`);
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
    <div className="min-h-screen dashboard-bg" data-testid="parent-dashboard">
      {/* Header with Dynamic Gradient */}
      <header className="bg-gradient-to-r from-amber-50 via-orange-50 to-yellow-50 animate-gradient dashboard-panel parent-accent-border border-b dashboard-separator shadow-md sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4 slide-in-left">
              <div className="w-16 h-16 bg-gradient-to-br from-parent-primary via-parent-secondary to-orange-400 rounded-xl flex items-center justify-center shadow-lg hover:shadow-xl transition-all duration-300 hover:animate-glow">
                <Bus className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-parent-primary to-orange-600 bg-clip-text text-transparent">
                  Parent Dashboard
                </h1>
                <p className="text-sm text-gray-600 mt-1 font-medium">
                  Welcome back, <span className="text-parent-primary">{user.name}</span>
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <NotificationBell role="parent" />
              <Button
                data-testid="logout-button"
                onClick={onLogout}
                variant="outline"
                className="logout-button logout-button-parent"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* User Profile */}
        <UserProfileHeader user={user} role="parent" />

        {/* Student Cards - Multiple Children */}
        {students.length > 1 ? (
          <div>
            <h2 className="text-xl font-semibold mb-5 text-gray-900">My Children</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5 mb-6">
              {students.map((student) => (
                <div
                  key={student.student_id}
                  onClick={() => setSelectedStudent(student)}
                  className={`cursor-pointer transition-all ${selectedStudent?.student_id === student.student_id ? 'ring-2 ring-parent-primary rounded-xl' : ''}`}
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

            <div className="space-y-6">
                {/* Live Bus Map */}
                <Card className="p-6 dashboard-card-enhanced parent-accent-border hover-lift">
                  <div className="flex items-center gap-3 mb-5 pb-4 border-b border-gray-100">
                    <div className="w-12 h-12 bg-gradient-to-br from-parent-primary to-parent-secondary rounded-xl flex items-center justify-center shadow-sm">
                      <MapPin className="w-6 h-6 text-white" />
                    </div>
                    <h2 className="text-xl font-semibold text-parent-primary">Live Bus Location</h2>
                    {busLocation && (
                      <span className="ml-auto text-xs text-gray-500">
                        Updated: {new Date(busLocation.timestamp).toLocaleTimeString()}
                      </span>
                    )}
                  </div>
                  <div className="h-96 rounded-xl overflow-hidden relative border border-gray-200" data-testid="bus-map-container">
                    <BusMap location={busLocation} route={route} showRoute={showRoute} />
                    
                    {/* Toggle Route Button */}
                    {route && (
                      <button
                        onClick={toggleRoute}
                        data-testid="toggle-route-button"
                        className={`absolute top-4 right-4 z-[1000] flex items-center gap-2 px-4 py-2 rounded-xl shadow-md transition-all font-medium ${
                          showRoute
                            ? 'bg-parent-primary text-white hover:bg-parent-hover'
                            : 'bg-white text-gray-900 hover:bg-gray-50 border-2 border-gray-300'
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
                <Card className="p-6 dashboard-card-enhanced parent-accent-border hover-lift">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-5 pb-4 border-b border-gray-100">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-gradient-to-br from-parent-primary to-parent-secondary rounded-xl flex items-center justify-center shadow-sm">
                        <Calendar className="w-6 h-6 text-white" />
                      </div>
                      <h2 className="text-xl font-semibold text-parent-primary">Attendance Calendar</h2>
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
          </div>
        )}
      </div>

      {/* Notification Detail Modal */}
      {showNotificationDetail && selectedNotification && (
        <NotificationDetailModal
          notification={selectedNotification}
          onClose={() => {
            setShowNotificationDetail(false);
            setSelectedNotification(null);
          }}
        />
      )}
    </div>
  );
}
