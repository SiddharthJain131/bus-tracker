import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X } from 'lucide-react';
import { Button } from './ui/button';
import RouteMap from './RouteMap';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function RouteVisualizationModal({ routeId, open, onClose }) {
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (open && routeId) {
      fetchRoute();
    }
  }, [routeId, open]);

  const fetchRoute = async () => {
    try {
      const response = await axios.get(`${API}/routes/${routeId}`);
      setRoute(response.data);
    } catch (error) {
      console.error('Failed to load route:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" data-testid="route-modal">
        <div className="bg-white rounded-lg p-6">
          <div className="spinner mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading route...</p>
        </div>
      </div>
    );
  }

  if (!route) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" data-testid="route-modal" onClick={onClose}>
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-auto" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk' }}>
            {route.route_name}
          </h2>
          <Button
            data-testid="close-route-modal"
            onClick={onClose}
            variant="ghost"
            size="sm"
            className="rounded-full"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Flowchart */}
          {route.stops && route.stops.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-4">Route Stops</h3>
              <div className="flex items-center justify-center gap-2 overflow-x-auto pb-4" data-testid="route-flowchart">
                {route.stops.map((stop, index) => (
                  <React.Fragment key={stop.stop_id}>
                    <div className="flex flex-col items-center">
                      <div className="w-12 h-12 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold text-lg mb-2">
                        {index + 1}
                      </div>
                      <div className="text-center min-w-[120px]">
                        <div className="font-medium text-gray-900">{stop.stop_name}</div>
                        <div className="text-xs text-gray-500 mt-1">
                          {stop.lat.toFixed(4)}, {stop.lon.toFixed(4)}
                        </div>
                      </div>
                    </div>
                    {index < route.stops.length - 1 && (
                      <div className="flex items-center pb-8">
                        <div className="h-1 w-16 bg-blue-300"></div>
                        <div className="text-blue-500 text-xl">→</div>
                      </div>
                    )}
                  </React.Fragment>
                ))}
              </div>
            </div>
          )}

          {/* Map */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Route Map</h3>
            <div className="h-96 rounded-lg overflow-hidden border border-gray-200" data-testid="route-map-container">
              <RouteMap route={route} />
            </div>
          </div>

          {route.remarks && (
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-gray-700">
                <strong>Remarks:</strong> {route.remarks}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
