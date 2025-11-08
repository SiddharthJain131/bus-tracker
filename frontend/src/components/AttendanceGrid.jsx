import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { ChevronLeft, ChevronRight, Calendar, Clock } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AttendanceGrid({ studentId }) {
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [gridData, setGridData] = useState([]);
  const [summary, setSummary] = useState('');
  const [showScanModal, setShowScanModal] = useState(false);
  const [selectedScan, setSelectedScan] = useState(null);

  useEffect(() => {
    fetchAttendance();
  }, [studentId, currentMonth]);

  const fetchAttendance = async () => {
    try {
      const month = `${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, '0')}`;
      const response = await axios.get(`${API}/get_attendance?student_id=${studentId}&month=${month}`);
      setGridData(response.data.grid);
      setSummary(response.data.summary);
    } catch (error) {
      console.error('Failed to load attendance:', error);
    }
  };

  const previousMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1));
  };

  const nextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1));
  };

  const getStatusClass = (status) => {
    return `status-${status}`;
  };

  const monthName = currentMonth.toLocaleString('default', { month: 'long', year: 'numeric' });

  return (
    <div data-testid="attendance-grid">
      {/* Month selector */}
      <div className="flex justify-between items-center mb-6">
        <Button
          data-testid="previous-month-button"
          onClick={previousMonth}
          variant="outline"
          size="sm"
        >
          <ChevronLeft className="w-4 h-4" />
        </Button>
        <div className="text-center">
          <h3 className="font-semibold text-lg">{monthName}</h3>
          <p className="text-sm text-gray-600">{summary}</p>
        </div>
        <Button
          data-testid="next-month-button"
          onClick={nextMonth}
          variant="outline"
          size="sm"
        >
          <ChevronRight className="w-4 h-4" />
        </Button>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-7 gap-2">
        {gridData.map((day) => (
          <div
            key={day.date}
            data-testid={`attendance-day-${day.day}`}
            className="border border-gray-200 rounded-lg p-2 bg-white hover:shadow-md transition-shadow"
          >
            <div className="text-center font-semibold text-sm text-gray-700 mb-2">{day.day}</div>
            <div className="space-y-1">
              <div
                data-testid={`am-status-day-${day.day}`}
                className={`text-xs py-1 px-2 rounded text-center font-medium ${getStatusClass(day.am_status)}`}
                title={day.am_confidence ? `Confidence: ${(day.am_confidence * 100).toFixed(0)}%` : ''}
              >
                AM
              </div>
              <div
                data-testid={`pm-status-day-${day.day}`}
                className={`text-xs py-1 px-2 rounded text-center font-medium ${getStatusClass(day.pm_status)}`}
                title={day.pm_confidence ? `Confidence: ${(day.pm_confidence * 100).toFixed(0)}%` : ''}
              >
                PM
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
