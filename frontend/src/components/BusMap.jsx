import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icon
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

export default function BusMap({ location, route, showRoute }) {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markerRef = useRef(null);
  const routeLayersRef = useRef([]);

  const createBusIcon = (isStale = false) => {
    return L.divIcon({
      className: 'custom-bus-marker',
      html: `
        <div style="
          width: 40px;
          height: 40px;
          background: linear-gradient(135deg, ${isStale ? '#9ca3af 0%, #6b7280 100%' : '#3b82f6 0%, #8b5cf6 100%'});
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 4px 6px rgba(0,0,0,0.2);
          border: 3px solid white;
          position: relative;
        ">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M8 6v6"/>
            <path d="M15 6v6"/>
            <path d="M2 12h19.6"/>
            <path d="M18 18h3s.5-1.7.8-2.8c.1-.4.2-.8.2-1.2 0-.4-.1-.8-.2-1.2l-1.4-5C20.1 6.8 19.1 6 18 6H4a2 2 0 0 0-2 2v10h3"/>
            <circle cx="7" cy="18" r="2"/>
            <circle cx="16" cy="18" r="2"/>
          </svg>
          ${isStale ? `
            <div style="
              position: absolute;
              top: -8px;
              right: -8px;
              width: 20px;
              height: 20px;
              background: #ef4444;
              border-radius: 50%;
              display: flex;
              align-items: center;
              justify-content: center;
              border: 2px solid white;
              box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            ">
              <span style="color: white; font-size: 14px; font-weight: bold;">?</span>
            </div>
          ` : ''}
        </div>
      `,
      iconSize: [40, 40],
      iconAnchor: [20, 20],
    });
  };

  useEffect(() => {
    if (!mapInstanceRef.current && mapRef.current) {
      // Initialize map
      mapInstanceRef.current = L.map(mapRef.current).setView([37.7749, -122.4194], 13);

      // Add tile layer
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(mapInstanceRef.current);

      // Create initial bus marker with normal icon
      const busIcon = createBusIcon(false);
      markerRef.current = L.marker([37.7749, -122.4194], { icon: busIcon }).addTo(mapInstanceRef.current);
      markerRef.current.bindPopup('<b>School Bus</b><br>Live Location');
    }
  }, []);

  useEffect(() => {
    if (location && markerRef.current && mapInstanceRef.current) {
      // Check if location is stale or missing
      const isStale = location.is_stale === true || location.is_missing === true;
      const hasValidLocation = location.lat !== null && location.lon !== null && 
                               typeof location.lat === 'number' && typeof location.lon === 'number';
      
      // Update marker icon based on stale status
      const busIcon = createBusIcon(isStale);
      markerRef.current.setIcon(busIcon);
      
      // Update popup text
      let popupText = '<b>School Bus</b><br>';
      if (!hasValidLocation) {
        popupText += 'GPS Unavailable';
      } else if (isStale) {
        popupText += 'Location Uncertain<br><span style="color: #ef4444; font-size: 11px;">Last updated: >60s ago</span>';
      } else {
        popupText += 'Live Location';
      }
      markerRef.current.bindPopup(popupText);
      
      // Update marker position only if location is valid
      if (hasValidLocation) {
        const newLatLng = [location.lat, location.lon];
        markerRef.current.setLatLng(newLatLng);
        
        // If route is not shown, center on bus location
        if (!showRoute) {
          mapInstanceRef.current.setView(newLatLng, 15, { animate: true });
        }
      }
      // If location is invalid, keep marker at last known position or default
    }
  }, [location, showRoute]);

  // Handle route display
  useEffect(() => {
    if (!mapInstanceRef.current) return;

    // Clear existing route layers
    routeLayersRef.current.forEach(layer => {
      mapInstanceRef.current.removeLayer(layer);
    });
    routeLayersRef.current = [];

    if (showRoute && route) {
      // Draw polyline
      if (route.map_path && route.map_path.length > 0) {
        const latLngs = route.map_path.map((point) => [point.lat, point.lon]);
        const polyline = L.polyline(latLngs, {
          color: '#3b82f6',
          weight: 4,
          opacity: 0.7,
        }).addTo(mapInstanceRef.current);
        routeLayersRef.current.push(polyline);

        // Add stop markers
        if (route.stops && route.stops.length > 0) {
          route.stops.forEach((stop, index) => {
            const markerIcon = L.divIcon({
              className: 'custom-stop-marker',
              html: `
                <div style="
                  width: 32px;
                  height: 32px;
                  background: white;
                  border: 3px solid #3b82f6;
                  border-radius: 50%;
                  display: flex;
                  align-items: center;
                  justify-content: center;
                  font-weight: bold;
                  color: #3b82f6;
                  box-shadow: 0 2px 6px rgba(0,0,0,0.2);
                ">
                  ${index + 1}
                </div>
              `,
              iconSize: [32, 32],
              iconAnchor: [16, 16],
            });

            const marker = L.marker([stop.lat, stop.lon], { icon: markerIcon }).addTo(mapInstanceRef.current);
            const timesHtml = stop.morning_expected_time && stop.morning_expected_time !== 'N/A' 
              ? `<br><span style="color: #d97706; font-weight: 600;">☀️ ${stop.morning_expected_time}</span><br><span style="color: #4f46e5; font-weight: 600;">🌙 ${stop.evening_expected_time}</span>`
              : '';
            marker.bindPopup(`<b>${stop.stop_name}</b><br>Stop ${index + 1}${timesHtml}`);
            routeLayersRef.current.push(marker);
          });
        }

        // Fit bounds to include both route and bus location
        const bounds = polyline.getBounds();
        
        // Only extend bounds with bus location if coordinates are valid
        if (location && location.lat !== null && location.lon !== null && 
            typeof location.lat === 'number' && typeof location.lon === 'number') {
          bounds.extend([location.lat, location.lon]);
        }
        
        mapInstanceRef.current.fitBounds(bounds, { padding: [50, 50] });
      }
    } else if (location && mapInstanceRef.current) {
      // When route is hidden, center on bus location only if coordinates are valid
      const hasValidLocation = location.lat !== null && location.lon !== null && 
                               typeof location.lat === 'number' && typeof location.lon === 'number';
      
      if (hasValidLocation) {
        mapInstanceRef.current.setView([location.lat, location.lon], 15, { animate: true });
      }
      // If location is invalid, keep map at current view (don't attempt to center on invalid coords)
    }
  }, [showRoute, route, location]);

  return <div ref={mapRef} style={{ width: '100%', height: '100%' }} data-testid="leaflet-map" />;
}
