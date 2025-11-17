import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { toast } from 'sonner';
import { LogOut, Users, Calendar } from 'lucide-react';
import AttendanceGrid from './AttendanceGrid';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function TeacherDashboard({ user, onLogout }) {
  const [students, setStudents] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState(null);

  useEffect(() => {
    fetchStudents();
  }, []);

  const fetchStudents = async () => {
    try {
      const response = await axios.get(`${API}/teacher/students`);
      setStudents(response.data);
    } catch (error) {
      toast.error('Failed to load students');
    }
  };

  const getStatusClass = (status) => {
    return `status-${status}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-emerald-50" data-testid="teacher-dashboard">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center">
                <Users className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>Teacher Dashboard</h1>
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
        {selectedStudent ? (
          <div>
            <Button
              data-testid="back-to-students-button"
              onClick={() => setSelectedStudent(null)}
              variant="outline"
              className="mb-6"
            >
              ← Back to Students
            </Button>
            <Card className="p-6">
              <div className="flex items-center gap-2 mb-6">
                <Calendar className="w-5 h-5 text-emerald-600" />
                <h2 className="text-xl font-semibold" style={{ fontFamily: 'Space Grotesk' }}>
                  {selectedStudent.name} - Monthly Attendance
                </h2>
              </div>
              <AttendanceGrid studentId={selectedStudent.student_id} />
            </Card>
          </div>
        ) : (
          <div>
            <Card className="p-6 mb-6">
              <h2 className="text-xl font-semibold mb-4" style={{ fontFamily: 'Space Grotesk' }}>Today's Attendance</h2>
              <div className="space-y-2">
                {students.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No students assigned</p>
                ) : (
                  students.map((student) => (
                    <div
                      key={student.student_id}
                      data-testid={`student-row-${student.name.toLowerCase().replace(' ', '-')}`}
                      className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer"
                      onClick={() => setSelectedStudent(student)}
                    >
                      <div>
                        <p className="font-medium text-gray-900">{student.name}</p>
                        <p className="text-sm text-gray-500">Bus: {student.bus_number}</p>
                      </div>
                      <div className="flex gap-2">
                        <div className="flex items-center gap-1">
                          <span className="text-xs text-gray-600">AM:</span>
                          <div
                            data-testid={`am-status-${student.name.toLowerCase().replace(' ', '-')}`}
                            className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusClass(student.am_status)}`}
                          >
                            {student.am_status}
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          <span className="text-xs text-gray-600">PM:</span>
                          <div
                            data-testid={`pm-status-${student.name.toLowerCase().replace(' ', '-')}`}
                            className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusClass(student.pm_status)}`}
                          >
                            {student.pm_status}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
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
        )}
      </div>
    </div>
  );
}
