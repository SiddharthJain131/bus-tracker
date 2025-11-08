import React from 'react';
import { Card } from './ui/card';
import { User, GraduationCap, Bus, Phone, AlertCircle } from 'lucide-react';

const getInitials = (name) => {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .substring(0, 2);
};

export default function StudentCard({ student, compact = false }) {

  if (compact) {
    return (
      <Card className="p-4 hover:shadow-md transition-shadow" data-testid={`student-card-${student.student_id}`}>
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white font-bold">
            {student.photo ? (
              <img src={student.photo} alt={student.name} className="w-full h-full rounded-full object-cover" />
            ) : (
              getInitials(student.name)
            )}
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900">{student.name}</h3>
            <p className="text-sm text-gray-600">
              {student.class_name} {student.section && `- ${student.section}`}
            </p>
          </div>
        </div>
        <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-1 text-gray-600">
            <GraduationCap className="w-3 h-3" />
            <span>{student.teacher_name || 'N/A'}</span>
          </div>
          <div className="flex items-center gap-1 text-gray-600">
            <Bus className="w-3 h-3" />
            <span>{student.bus_number || 'N/A'}</span>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <>
      <Card className="p-6 card-hover" data-testid={`student-detail-card-${student.student_id}`}>
        <div className="flex items-start gap-4">
          {/* Avatar */}
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white text-2xl font-bold flex-shrink-0">
            {student.photo ? (
              <img src={student.photo} alt={student.name} className="w-full h-full rounded-full object-cover" />
            ) : (
              getInitials(student.name)
            )}
          </div>

          {/* Info */}
          <div className="flex-1">
            <h3 className="text-2xl font-bold text-gray-900 mb-1" style={{ fontFamily: 'Space Grotesk' }}>
              {student.name}
            </h3>
            
            <div className="grid md:grid-cols-2 gap-3 mt-4">
              {/* 1. Class & Section */}
              <div className="flex items-center gap-2 text-gray-700">
                <GraduationCap className="w-5 h-5 text-blue-600" />
                <div>
                  <div className="text-xs text-gray-500">Class & Section</div>
                  <div className="font-medium">{student.class_name || 'N/A'} - {student.section || 'N/A'}</div>
                </div>
              </div>

              {/* 2. Teacher */}
              <div className="flex items-center gap-2 text-gray-700">
                <User className="w-5 h-5 text-blue-600" />
                <div>
                  <div className="text-xs text-gray-500">Teacher</div>
                  <div className="font-medium">{student.teacher_name || 'N/A'}</div>
                </div>
              </div>

              {/* 3. Phone */}
              <div className="flex items-center gap-2 text-gray-700">
                <Phone className="w-5 h-5 text-blue-600" />
                <div>
                  <div className="text-xs text-gray-500">Phone</div>
                  <div className="font-medium">{student.phone || 'N/A'}</div>
                </div>
              </div>

              {/* 4. Emergency Contact */}
              <div className="flex items-center gap-2 text-gray-700">
                <AlertCircle className="w-5 h-5 text-red-600" />
                <div>
                  <div className="text-xs text-gray-500 font-semibold">Emergency Contact</div>
                  <div className="font-medium">{student.emergency_contact || 'N/A'}</div>
                </div>
              </div>

              {/* 5. Bus */}
              <div className="flex items-center gap-2 text-gray-700">
                <Bus className="w-5 h-5 text-blue-600" />
                <div>
                  <div className="text-xs text-gray-500">Bus</div>
                  <div className="font-medium">{student.bus_number || 'N/A'}</div>
                </div>
              </div>

              {/* 6. Stop */}
              <div className="flex items-center gap-2 text-gray-700">
                <MapPin className="w-5 h-5 text-blue-600" />
                <div>
                  <div className="text-xs text-gray-500">Stop</div>
                  <div className="font-medium">{student.stop_name || 'N/A'}</div>
                </div>
              </div>
            </div>

            {student.remarks && (
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-900">
                  <strong>Note:</strong> {student.remarks}
                </p>
              </div>
            )}
          </div>
        </div>
      </Card>
    </>
  );
}
