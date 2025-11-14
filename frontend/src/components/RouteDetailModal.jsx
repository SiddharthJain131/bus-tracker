import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Card } from './ui/card';
import { Navigation, MapPin, Bus } from 'lucide-react';
import RouteMap from './RouteMap';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function RouteDetailModal({ route, open, onClose }) {
  const [routeDetails, setRouteDetails] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && route) {
      fetchRouteDetails();
    }
  }, [open, route]);

  const fetchRouteDetails = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/routes/${route.route_id}`);
      setRouteDetails(response.data);
    } catch (error) {
      console.error('Failed to load route details:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!route) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold" style={{ fontFamily: 'Space Grotesk' }}>
            Route Details
          </DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="text-center py-8 text-gray-500">Loading...</div>
        ) : routeDetails ? (
          <div className="space-y-6">
            {/* Route Header */}
            <div className="flex items-center gap-6 p-6 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-400 to-indigo-600 rounded-full flex items-center justify-center text-white">
                <Navigation className="w-10 h-10" />
              </div>
              <div className="flex-1">
                <h3 className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
                  {routeDetails.route_name}
                </h3>
                <p className="text-gray-600">
                  {routeDetails.stops?.length || 0} stops
                </p>
              </div>
            </div>

            {/* Route Info */}
            {routeDetails.remarks && (
              <Card className="p-4">
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-sm font-medium text-gray-600">Remarks</span>
                </div>
                <p className="text-gray-700">{routeDetails.remarks}</p>
              </Card>
            )}

            {/* Stops List */}
            {routeDetails.stops && routeDetails.stops.length > 0 && (
              <Card className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <MapPin className="w-5 h-5 text-blue-600" />
                  <h3 className="text-lg font-semibold" style={{ fontFamily: 'Space Grotesk' }}>
                    Route Stops
                  </h3>
                </div>
                
                {/* Route Flow Diagram */}
                <div className="flex items-center justify-center gap-2 mb-6 overflow-x-auto pb-4">
                  {routeDetails.stops.map((stop, index) => (
                    <React.Fragment key={stop.stop_id}>
                      <div className="flex flex-col items-center min-w-[140px]">
                        <div className="w-12 h-12 bg-blue-100 border-2 border-blue-500 rounded-full flex items-center justify-center">
                          <MapPin className="w-6 h-6 text-blue-600" />
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
                      {index < routeDetails.stops.length - 1 && (
                        <div className="w-16 h-0.5 bg-blue-300 mt-6"></div>
                      )}
                    </React.Fragment>
                  ))}
                </div>

                {/* Route Map */}
                <div className="h-96 rounded-lg overflow-hidden border-2 border-gray-200">
                  <RouteMap route={routeDetails} />
                </div>
              </Card>
            )}

            {(!routeDetails.stops || routeDetails.stops.length === 0) && (
              <Card className="p-6 text-center text-gray-500">
                <p>No stops configured for this route</p>
              </Card>
            )}

            {/* Associated Bus */}
            {routeDetails.bus_number && (
              <Card className="p-4">
                <div className="flex items-center gap-3 mb-2">
                  <Bus className="w-5 h-5 text-blue-600" />
                  <span className="text-sm font-medium text-gray-600">Assigned Bus</span>
                </div>
                <p className="text-lg font-semibold text-gray-900">{routeDetails.bus_number}</p>
              </Card>
            )}
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
