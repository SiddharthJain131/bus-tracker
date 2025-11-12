import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { User, Phone, GraduationCap, Users, Bus, MapPin, Eye } from 'lucide-react';
import RouteVisualizationModal from './RouteVisualizationModal';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function StudentDetailModal({ student, open, onClose, hideTeacherField = false }) {
  const [studentDetails, setStudentDetails] = useState(null);
  const [showRouteModal, setShowRouteModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [tempClosed, setTempClosed] = useState(false);

  // Helper function to remove "Grade " prefix from class names
  const formatClassName = (className) => {
    if (!className) return 'N/A';
    return className.replace(/^Grade\s+/i, '');
  };

  useEffect(() => {
    if (open && student) {
      fetchStudentDetails();
      setTempClosed(false);
    }
  }, [open, student]);

  const fetchStudentDetails = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/students/${student.student_id}`);
      setStudentDetails(response.data);
    } catch (error) {
      console.error('Failed to load student details:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!student) return null;

  return (
    <>
      <Dialog open={open && !tempClosed} onOpenChange={onClose}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold" style={{ fontFamily: 'Space Grotesk' }}>
              Student Profile
            </DialogTitle>
          </DialogHeader>

          {loading ? (
            <div className="text-center py-8 text-gray-500">Loading...</div>
          ) : studentDetails ? (
            <div className="space-y-6">
              {/* Profile Header */}
              <div className="flex items-center gap-6 p-6 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg">
                <div className="w-24 h-24 bg-gradient-to-br from-blue-400 to-indigo-600 rounded-full flex items-center justify-center text-white text-3xl font-bold overflow-hidden transition-all duration-300 hover:scale-110 hover:shadow-xl hover:ring-4 hover:ring-indigo-300 cursor-pointer">
                  {studentDetails.photo_url ? (
                    <img 
                      src={`${BACKEND_URL}${studentDetails.photo_url}`} 
                      alt={studentDetails.name} 
                      className="w-full h-full object-cover transition-transform duration-300 hover:scale-110" 
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.parentElement.textContent = studentDetails.name.charAt(0).toUpperCase();
                      }}
                    />
                  ) : (
                    studentDetails.name.charAt(0).toUpperCase()
                  )}
                </div>
                <div className="flex-1">
                  <h3 className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                    {studentDetails.name}
                  </h3>
                  <p className="text-gray-600">
                    Roll No: <span className="font-semibold text-emerald-700">{studentDetails.roll_number || studentDetails.student_id}</span>
                  </p>
                </div>
              </div>

              {/* Student Info Grid */}
              <div className="grid md:grid-cols-2 gap-4">
                <Card className="p-4">
                  <div className="flex items-center gap-3 mb-2">
                    <GraduationCap className="w-5 h-5 text-blue-600" />
                    <span className="text-sm font-medium text-gray-600">Class & Section</span>
                  </div>
                  <p className="text-lg font-semibold text-gray-900">
                    {formatClassName(studentDetails.class_name)} - {studentDetails.section || 'N/A'}
                  </p>
                </Card>

                <Card className="p-4">
                  <div className="flex items-center gap-3 mb-2">
                    <Phone className="w-5 h-5 text-blue-600" />
                    <span className="text-sm font-medium text-gray-600">Phone</span>
                  </div>
                  <p className="text-lg font-semibold text-gray-900">
                    {studentDetails.phone || 'N/A'}
                  </p>
                </Card>

                {!hideTeacherField && (
                  <Card className="p-4">
                    <div className="flex items-center gap-3 mb-2">
                      <Users className="w-5 h-5 text-blue-600" />
                      <span className="text-sm font-medium text-gray-600">Teacher</span>
                    </div>
                    <p className="text-lg font-semibold text-gray-900">
                      {studentDetails.teacher_name || 'Not Assigned'}
                    </p>
                  </Card>
                )}

                <Card className="p-4">
                  <div className="flex items-center gap-3 mb-2">
                    <Bus className="w-5 h-5 text-blue-600" />
                    <span className="text-sm font-medium text-gray-600">Bus Number</span>
                  </div>
                  <p className="text-lg font-semibold text-gray-900">
                    {studentDetails.bus_number || 'N/A'}
                  </p>
                </Card>

                <Card className="p-4">
                  <div className="flex items-center gap-3 mb-2">
                    <Bus className="w-5 h-5 text-blue-600" />
                    <span className="text-sm font-medium text-gray-600">Stop</span>
                  </div>
                  <p className="text-lg font-semibold text-gray-900">
                    {studentDetails.stop_name || 'N/A'}
                  </p>
                </Card>
              </div>

              {/* Parent Info */}
              <Card className="p-4 bg-gradient-to-br from-green-50 to-emerald-50">
                <div className="flex items-center gap-3 mb-3">
                  <User className="w-5 h-5 text-green-600" />
                  <span className="text-sm font-medium text-gray-600">Parent Information</span>
                </div>
                <div className="space-y-2">
                  <p className="text-lg font-semibold text-gray-900">{studentDetails.parent_name}</p>
                  <p className="text-sm text-gray-600">{studentDetails.parent_email}</p>
                  {studentDetails.emergency_contact && (
                    <p className="text-sm text-gray-600">Emergency: {studentDetails.emergency_contact}</p>
                  )}
                </div>
              </Card>

              {/* Additional Info */}
              {studentDetails.remarks && (
                <Card className="p-4">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-sm font-medium text-gray-600">Remarks</span>
                  </div>
                  <p className="text-gray-700">{studentDetails.remarks}</p>
                </Card>
              )}

              {/* View Route Button */}
              {studentDetails.route_id && (
                <Button
                  onClick={() => {
                    setShowRouteModal(true);
                    setTempClosed(true);
                  }}
                  className="w-full flex items-center justify-center gap-2"
                >
                  <MapPin className="w-4 h-4" />
                  View Route on Map
                </Button>
              )}
            </div>
          ) : null}
        </DialogContent>
      </Dialog>

      {/* Route Visualization Modal */}
      {showRouteModal && studentDetails?.route_id && (
        <RouteVisualizationModal
          routeId={studentDetails.route_id}
          open={showRouteModal}
          onClose={() => {
            setShowRouteModal(false);
            setTempClosed(false);
          }}
        />
      )}
    </>
  );
}
