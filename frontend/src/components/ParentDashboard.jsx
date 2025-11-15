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
      fetchBusLocation(selectedStudent.bus_id);
      fetchRoute(selectedStudent.route_id);
    }
  }, [selectedStudent]);

  const fetchStudents = async () => {
    try {
      const response = await axios.get(`${API}/students`);
      setStudents(response.data);
      if (response.data.length > 0 && !selectedStudent) {
        const firstStudent = response.data[0];
        setSelectedStudent(firstStudent);
        await fetchStudentDetails(firstStudent.student_id);
      }
    } catch (error) {
      console.error('Failed to load students:', error);
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

  const handleStudentSelect = async (student) => {
    setSelectedStudent(student);
    await fetchStudentDetails(student.student_id);
  };

  const fetchNotifications = async () => {
    try {
      const response = await axios.get(`${API}/get_notifications`);
      setNotifications(response.data);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  };

  const handleNotificationClick = async (notification) => {
    setSelectedNotification(notification);
    setShowNotificationDetail(true);
    
    if (!notification.read) {
      try {
        await axios.post(`${API}/mark_notification_read?notification_id=${notification.notification_id}`);
        await fetchNotifications();
      } catch (error) {
        console.error('Error marking notification as read:', error);
      }
    }
  };

  const fetchBusLocation = async (busId) => {
    if (!busId) return;
    try {
      const response = await axios.get(`${API}/get_bus_location`, {
        params: { bus_id: busId }
      });
      setBusLocation(response.data);
    } catch (error) {
      console.error('Failed to load bus location:', error);
    }
  };

  const fetchRoute = async (routeId) => {
    if (!routeId) return;
    try {
      const response = await axios.get(`${API}/routes/${routeId}`);
      setRoute(response.data);
    } catch (error) {
      console.error('Failed to load route:', error);
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
                <GraduationCap className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent" style={{ fontFamily: 'Space Grotesk' }}>
                  Parent Dashboard
                </h1>
                <p className="text-sm text-gray-600">Track your child's journey</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <UserProfileHeader user={user} />
              <Button
                onClick={onLogout}
                variant="outline"
                className="flex items-center gap-2 hover:bg-red-50 hover:text-red-600 hover:border-red-200"
              >
                <LogOut className="w-4 h-4" />
                <span>Logout</span>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left column - Children */}
          <div>
            <Card className="p-6 card-hover">
              <div className="flex items-center gap-2 mb-4">
                <Users className="w-5 h-5 text-blue-600" />
                <h2 className="text-xl font-semibold" style={{ fontFamily: 'Space Grotesk' }}>My Children</h2>
              </div>
              <div className="space-y-3">
                {students.map((student) => (
                  <StudentCard
                    key={student.student_id}
                    student={student}
                    isSelected={selectedStudent?.student_id === student.student_id}
                    onClick={() => handleStudentSelect(student)}
                    view="compact"
                  />
                ))}
              </div>
            </Card>
          </div>

          {/* Middle column - Student Details */}
          <div className="lg:col-span-2 space-y-6">
            {selectedStudent && selectedStudentDetails && (
              <>
                {/* Student Info Card */}
                <StudentCard
                  student={{
                    ...selectedStudent,
                    ...selectedStudentDetails
                  }}
                  view="full"
                />

                {/* Attendance Grid */}
                <Card className="p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <Calendar className="w-5 h-5 text-purple-600" />
                    <h2 className="text-xl font-semibold" style={{ fontFamily: 'Space Grotesk' }}>Attendance</h2>
                  </div>
                  <AttendanceGrid studentId={selectedStudent.student_id} />
                </Card>

                {/* Bus Location */}
                {busLocation && route && (
                  <Card className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">
                        <Bus className="w-5 h-5 text-green-600" />
                        <h2 className="text-xl font-semibold" style={{ fontFamily: 'Space Grotesk' }}>Bus Location</h2>
                      </div>
                      <Button
                        onClick={() => setShowRoute(!showRoute)}
                        variant="outline"
                        size="sm"
                        className="flex items-center gap-2"
                      >
                        {showRoute ? (
                          <>
                            <EyeOff className="w-4 h-4" />
                            Hide Route
                          </>
                        ) : (
                          <>
                            <Eye className="w-4 h-4" />
                            Show Route
                          </>
                        )}
                      </Button>
                    </div>
                    <div className="h-96 rounded-lg overflow-hidden">
                      <BusMap
                        busLocation={busLocation}
                        route={showRoute ? route : null}
                      />
                    </div>
                  </Card>
                )}
              </>
            )}
          </div>

          {/* Right column - Notifications */}
          <div className="lg:col-start-3 lg:row-start-2">
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
                      onClick={() => handleNotificationClick(notification)}
                      data-testid={`notification-${notification.type}`}
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
      </main>

      <NotificationDetailModal
        notification={selectedNotification}
        isOpen={showNotificationDetail}
        onClose={() => setShowNotificationDetail(false)}
      />
    </div>
  );
}

const GraduationCap = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222" />
  </svg>
);

const Users = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
  </svg>
);
