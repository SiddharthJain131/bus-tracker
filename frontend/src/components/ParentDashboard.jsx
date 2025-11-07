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
                  <div className="h-96 rounded-lg overflow-hidden" data-testid="bus-map-container">
                    <BusMap location={busLocation} />
                  </div>
                </Card>

                {/* Attendance Grid */}
                <Card className="p-6 card-hover">
                  <div className="flex items-center gap-2 mb-4">
                    <Calendar className="w-5 h-5 text-blue-600" />
                    <h2 className="text-xl font-semibold" style={{ fontFamily: 'Space Grotesk' }}>Attendance</h2>
                  </div>
                  <AttendanceGrid studentId={selectedStudent.student_id} />
                </Card>
              </div>

              {/* Right column - Notifications */}
              <div>
                <Card className="p-6 card-hover">
                  <div className="flex items-center gap-2 mb-4">
                    <Bell className="w-5 h-5 text-blue-600" />
                    <h2 className="text-xl font-semibold" style={{ fontFamily: 'Space Grotesk' }}>Notifications</h2>
                  </div>
                  <div className="space-y-3 max-h-96 overflow-y-auto" data-testid="notifications-container">
                    {notifications.length === 0 ? (
                      <p className="text-sm text-gray-500 text-center py-8">No notifications</p>
                    ) : (
                      notifications.map((notification) => (
                        <div
                          key={notification.notification_id}
                          data-testid={`notification-${notification.type}`}
                          className={`p-3 rounded-lg border ${
                            notification.type === 'mismatch'
                              ? 'bg-red-50 border-red-200'
                              : notification.type === 'update'
                              ? 'bg-blue-50 border-blue-200'
                              : 'bg-yellow-50 border-yellow-200'
                          }`}
                        >
                          <p className="text-sm font-medium text-gray-900">{notification.message}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {new Date(notification.timestamp).toLocaleString()}
                          </p>
                        </div>
                      ))
                    )}
                  </div>
                </Card>

                {/* Status Legend */}
                <Card className="p-6 mt-6">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">Status Legend</h3>
                  <div className="space-y-2 text-xs">
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
                      <span>Reached School</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded status-red"></div>
                      <span>Missed Boarding</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded status-blue"></div>
                      <span>Holiday</span>
                    </div>
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
