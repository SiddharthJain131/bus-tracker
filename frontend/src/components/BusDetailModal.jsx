import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Card } from './ui/card';
import { Bus, User, Phone, MapPin, Navigation } from 'lucide-react';
import RouteMap from './RouteMap';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function BusDetailModal({ bus, open, onClose }) {
  const [busDetails, setBusDetails] = useState(null);
  const [routeData, setRouteData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && bus) {
      fetchBusDetails();
    }
  }, [open, bus]);

  const fetchBusDetails = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/buses/${bus.bus_id}`);
      setBusDetails(response.data);
      
      if (response.data.route_id) {
        const routeResponse = await axios.get(`${API}/routes/${response.data.route_id}`);
        setRouteData(routeResponse.data);
      }
    } catch (error) {
      console.error('Failed to load bus details:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!bus) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold" style={{ fontFamily: 'Space Grotesk' }}>
            Bus Details
          </DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="text-center py-8 text-gray-500">Loading...</div>
        ) : busDetails ? (
          <div className="space-y-6">
            {/* Bus Header */}
            <div className="flex items-center gap-6 p-6 bg-gradient-to-br from-orange-50 to-amber-50 rounded-lg">
              <div className="w-20 h-20 bg-gradient-to-br from-orange-400 to-amber-600 rounded-full flex items-center justify-center text-white">
                <Bus className="w-10 h-10" />
              </div>
              <div className="flex-1">
                <h3 className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                  Bus {busDetails.bus_number}
                </h3>
                <p className="text-gray-600">Capacity: {busDetails.capacity} students</p>
              </div>
            </div>

            {/* Bus Info Grid */}
            <div className="grid md:grid-cols-2 gap-4">
              <Card className="p-4">
                <div className="flex items-center gap-3 mb-2">
                  <User className="w-5 h-5 text-orange-600" />
                  <span className="text-sm font-medium text-gray-600">Driver Name</span>
                </div>
                <p className="text-lg font-semibold text-gray-900">{busDetails.driver_name}</p>
              </Card>

              <Card className="p-4">
                <div className="flex items-center gap-3 mb-2">
                  <Phone className="w-5 h-5 text-orange-600" />
                  <span className="text-sm font-medium text-gray-600">Driver Phone</span>
                </div>
                <p className="text-lg font-semibold text-gray-900">{busDetails.driver_phone}</p>
              </Card>

              {busDetails.remarks && (
                <Card className="p-4 md:col-span-2">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-sm font-medium text-gray-600">Remarks</span>
                  </div>
                  <p className="text-gray-700">{busDetails.remarks}</p>
                </Card>
              )}
            </div>

            {/* Route Flow Visualization */}
            {routeData && routeData.stops && (
              <Card className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Navigation className="w-5 h-5 text-orange-600" />
                  <h3 className="text-lg font-semibold" style={{ fontFamily: 'Space Grotesk' }}>
                    {routeData.route_name}
                  </h3>
                </div>
                
                {/* Route Flow Diagram */}
                <div className="flex items-center justify-center gap-2 mb-6 overflow-x-auto pb-4">
                  {routeData.stops.map((stop, index) => (
                    <React.Fragment key={stop.stop_id}>
                      <div className="flex flex-col items-center min-w-[140px]">
                        <div className="w-12 h-12 bg-orange-100 border-2 border-orange-500 rounded-full flex items-center justify-center">
                          <MapPin className="w-6 h-6 text-orange-600" />
                        </div>
                        <p className="text-xs font-medium text-center mt-2 text-gray-700">
                          {stop.stop_name}
                        </p>
                        <p className="text-xs text-gray-500 mb-1">Stop {stop.order_index + 1}</p>
                        {stop.morning_expected_time && stop.morning_expected_time !== 'N/A' && (
                          <div className="text-xs mt-1 space-y-0.5 text-center">
                            <div className="text-amber-600 font-semibold">
                              ☀️ {stop.morning_expected_time}
                            </div>
                            <div className="text-indigo-600 font-semibold">
                              🌙 {stop.evening_expected_time}
                            </div>
                          </div>
                        )}
                      </div>
                      {index < routeData.stops.length - 1 && (
                        <div className="w-16 h-0.5 bg-orange-300 mt-6"></div>
                      )}
                    </React.Fragment>
                  ))}
                </div>

                {/* Route Map */}
                <div className="h-96 rounded-lg overflow-hidden border-2 border-gray-200">
                  <RouteMap route={routeData} />
                </div>
              </Card>
            )}

            {!routeData && (
              <Card className="p-6 text-center text-gray-500">
                <p>No route assigned to this bus</p>
              </Card>
            )}
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
