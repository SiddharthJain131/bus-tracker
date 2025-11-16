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

  const handleCellClick = (day, trip) => {
    const tripData = trip === 'AM' ? {
      photo: day.am_scan_photo,
      timestamp: day.am_scan_timestamp,
      status: day.am_status,
      trip: 'AM'
    } : {
      photo: day.pm_scan_photo,
      timestamp: day.pm_scan_timestamp,
      status: day.pm_status,
      trip: 'PM'
    };

    // Open modal for both yellow and green status
    if (tripData.status === 'green' || tripData.status === 'yellow') {
      setSelectedScan({
        ...tripData,
        date: day.date,
        day: day.day
      });
      setShowScanModal(true);
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'No timestamp available';
    try {
      const date = new Date(timestamp);
      const timeStr = date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
      });
      const dateStr = date.toLocaleDateString('en-US', { 
        day: '2-digit', 
        month: 'short', 
        year: 'numeric' 
      });
      return `${timeStr}, ${dateStr}`;
    } catch (e) {
      return 'Invalid timestamp';
    }
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
              {/* AM Status Cell */}
              <div
                data-testid={`am-status-day-${day.day}`}
                className={`text-xs py-1 px-2 rounded text-center font-medium ${getStatusClass(day.am_status)} ${
                  (day.am_status === 'green' || day.am_status === 'yellow') ? 'cursor-pointer hover:opacity-80 transition-opacity' : ''
                }`}
                title={day.am_confidence ? `Confidence: ${(day.am_confidence * 100).toFixed(0)}%` : ''}
                onClick={() => handleCellClick(day, 'AM')}
              >
                AM
              </div>
              {/* PM Status Cell */}
              <div
                data-testid={`pm-status-day-${day.day}`}
                className={`text-xs py-1 px-2 rounded text-center font-medium ${getStatusClass(day.pm_status)} ${
                  (day.pm_status === 'green' || day.pm_status === 'yellow') ? 'cursor-pointer hover:opacity-80 transition-opacity' : ''
                }`}
                title={day.pm_confidence ? `Confidence: ${(day.pm_confidence * 100).toFixed(0)}%` : ''}
                onClick={() => handleCellClick(day, 'PM')}
              >
                PM
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Scan Details Modal */}
      <Dialog open={showScanModal} onOpenChange={setShowScanModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold flex items-center gap-2" style={{ fontFamily: 'Space Grotesk' }}>
              <Calendar className="w-5 h-5 text-blue-600" />
              {selectedScan?.trip === 'AM' ? 'Arrival Scan' : 'Departure Scan'}
            </DialogTitle>
          </DialogHeader>
          
          {selectedScan && (
            <div className="space-y-4">
              {/* Photo Section */}
              <div className="flex justify-center">
                {selectedScan.photo ? (
                  <img 
                    src={`${BACKEND_URL}${selectedScan.photo}`}
                    alt="Scan capture" 
                    className="w-40 h-40 object-cover rounded-lg shadow-md border-2 border-gray-200"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.nextSibling.style.display = 'flex';
                    }}
                  />
                ) : (
                  <div className="w-40 h-40 bg-gray-100 rounded-lg flex items-center justify-center border-2 border-gray-200">
                    <div className="text-center text-gray-500 text-sm">
                      <Calendar className="w-8 h-8 mx-auto mb-2 opacity-50" />
                      <p>No photo available</p>
                    </div>
                  </div>
                )}
                {/* Fallback div for image load error */}
                <div style={{ display: 'none' }} className="w-40 h-40 bg-gray-100 rounded-lg flex items-center justify-center border-2 border-gray-200">
                  <div className="text-center text-gray-500 text-sm">
                    <Calendar className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>Photo not found</p>
                  </div>
                </div>
              </div>

              {/* Timestamp Section */}
              <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                <div className="flex items-center gap-2 justify-center text-blue-900">
                  <Clock className="w-5 h-5 text-blue-600" />
                  <div className="text-center">
                    <p className="text-xs text-blue-600 font-medium mb-1">Scan Time</p>
                    <p className="font-semibold">{formatTimestamp(selectedScan.timestamp)}</p>
                  </div>
                </div>
              </div>

              {/* Additional Info */}
              {!selectedScan.photo && !selectedScan.timestamp && (
                <div className="text-center text-gray-500 text-sm p-4 bg-gray-50 rounded-lg">
                  No scan data available for this session.
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
