import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Calendar, Search, Edit, Trash2, Plus } from 'lucide-react';
import AddHolidayModal from './AddHolidayModal';
import EditHolidayModal from './EditHolidayModal';
import DeleteConfirmationDialog from './DeleteConfirmationDialog';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL ? `${process.env.REACT_APP_BACKEND_URL}/api` : 'http://localhost:8001/api';

export default function HolidaysManagementModal({ open, onClose, onSuccess }) {
  const [holidays, setHolidays] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  
  // Modal states
  const [showAddHoliday, setShowAddHoliday] = useState(false);
  const [showEditHoliday, setShowEditHoliday] = useState(false);
  const [editHoliday, setEditHoliday] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteItem, setDeleteItem] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (open) {
      fetchHolidays();
    }
  }, [open]);

  const fetchHolidays = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/admin/holidays`);
      setHolidays(response.data);
    } catch (error) {
      console.error('Error fetching holidays:', error);
      toast.error('Failed to load holidays');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = (holiday) => {
    setDeleteItem({ ...holiday, type: 'holiday' });
    setShowDeleteConfirm(true);
  };

  const confirmDelete = async () => {
    if (!deleteItem) return;
    
    setIsDeleting(true);
    try {
      await axios.delete(`${API}/admin/holidays/${deleteItem.holiday_id}`);
      toast.success(`Holiday "${deleteItem.name}" deleted successfully`);
      fetchHolidays();
      if (onSuccess) onSuccess();
      setShowDeleteConfirm(false);
      setDeleteItem(null);
    } catch (error) {
      console.error('Delete error:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete holiday');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleAddSuccess = () => {
    fetchHolidays();
    if (onSuccess) onSuccess();
  };

  const handleEditSuccess = () => {
    fetchHolidays();
    if (onSuccess) onSuccess();
  };

  const filteredHolidays = holidays
    .filter(holiday => 
      holiday.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      holiday.date.includes(searchTerm) ||
      (holiday.description && holiday.description.toLowerCase().includes(searchTerm.toLowerCase()))
    )
    .sort((a, b) => {
      // Sort by date - upcoming first (descending order)
      const dateA = new Date(a.date);
      const dateB = new Date(b.date);
      return dateB - dateA;
    });

  return (
    <>
      <Dialog open={open} onOpenChange={onClose}>
        <DialogContent className="sm:max-w-[900px] max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Space Grotesk' }}>
              <Calendar className="w-5 h-5 text-blue-600" />
              Manage Holidays
            </DialogTitle>
          </DialogHeader>

          <div className="flex-1 overflow-y-auto">
            {/* Search Bar and Add Button */}
            <div className="flex justify-between items-center gap-4 mb-6">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search holidays..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Button
                onClick={() => setShowAddHoliday(true)}
                className="bg-blue-600 hover:bg-blue-700 flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Add Holiday
              </Button>
            </div>

            {/* Holidays Table */}
            {loading ? (
              <div className="text-center py-8 text-gray-500">Loading holidays...</div>
            ) : (
              <div className="overflow-x-auto border rounded-lg">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr className="border-b">
                      <th className="text-left p-3 font-semibold text-gray-700">Date</th>
                      <th className="text-left p-3 font-semibold text-gray-700">Title</th>
                      <th className="text-left p-3 font-semibold text-gray-700">Description</th>
                      <th className="text-left p-3 font-semibold text-gray-700">Status</th>
                      <th className="text-right p-3 font-semibold text-gray-700">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredHolidays.length === 0 ? (
                      <tr>
                        <td colSpan="5" className="text-center py-8 text-gray-500">
                          {searchTerm ? 'No holidays found matching your search.' : 'No holidays found. Click "Add Holiday" to create one.'}
                        </td>
                      </tr>
                    ) : (
                      filteredHolidays.map(holiday => {
                        const holidayDate = new Date(holiday.date);
                        const today = new Date();
                        today.setHours(0, 0, 0, 0);
                        const isPast = holidayDate < today;
                        const isUpcoming = holidayDate >= today;
                        
                        return (
                          <tr 
                            key={holiday.holiday_id} 
                            className={`border-b hover:bg-gray-50 ${isPast ? 'opacity-50' : ''}`}
                          >
                            <td className="p-3">
                              <span className={`font-medium ${isPast ? 'text-gray-400' : 'text-gray-900'}`}>
                                {new Date(holiday.date).toLocaleDateString('en-US', {
                                  year: 'numeric',
                                  month: 'short',
                                  day: 'numeric'
                                })}
                              </span>
                            </td>
                            <td className="p-3">
                              <span className={`font-medium ${isPast ? 'text-gray-400' : 'text-gray-900'}`}>
                                {holiday.name}
                              </span>
                            </td>
                            <td className="p-3">
                              <span className={`text-sm ${isPast ? 'text-gray-400' : 'text-gray-600'}`}>
                                {holiday.description || '-'}
                              </span>
                            </td>
                            <td className="p-3">
                              {isUpcoming && (
                                <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                                  🌟 Upcoming
                                </span>
                              )}
                              {isPast && (
                                <span className="inline-flex items-center px-2 py-1 bg-gray-100 text-gray-500 rounded-full text-xs font-medium">
                                  Past
                                </span>
                              )}
                            </td>
                            <td className="p-3">
                              <div className="flex justify-end gap-2">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => {
                                    setEditHoliday(holiday);
                                    setShowEditHoliday(true);
                                  }}
                                  className="text-blue-600 hover:text-blue-800 hover:bg-blue-50"
                                >
                                  <Edit className="w-4 h-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleDelete(holiday)}
                                  className="text-red-600 hover:text-red-800 hover:bg-red-50"
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
            )}
          </div>

          {/* Close Button */}
          <div className="flex justify-end pt-4 border-t">
            <Button
              onClick={onClose}
              variant="outline"
            >
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Child Modals */}
      <AddHolidayModal
        open={showAddHoliday}
        onClose={() => setShowAddHoliday(false)}
        onSuccess={handleAddSuccess}
      />

      <EditHolidayModal
        holiday={editHoliday}
        open={showEditHoliday}
        onClose={() => {
          setShowEditHoliday(false);
          setEditHoliday(null);
        }}
        onSuccess={handleEditSuccess}
      />

      <DeleteConfirmationDialog
        open={showDeleteConfirm}
        onClose={() => {
          setShowDeleteConfirm(false);
          setDeleteItem(null);
        }}
        onConfirm={confirmDelete}
        title="Delete Holiday"
        itemName={deleteItem?.name}
        itemType="holiday"
        isDeleting={isDeleting}
      />
    </>
  );
}
