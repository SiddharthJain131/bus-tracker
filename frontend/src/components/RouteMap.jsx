import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

export default function RouteMap({ route }) {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);

  useEffect(() => {
    if (!route) return;
    
    if (!mapInstanceRef.current && mapRef.current) {
      // Initialize map
      const centerLat = route.map_path && route.map_path.length > 0 ? route.map_path[0].lat : 37.7749;
      const centerLon = route.map_path && route.map_path.length > 0 ? route.map_path[0].lon : -122.4194;
      
      mapInstanceRef.current = L.map(mapRef.current).setView([centerLat, centerLon], 13);

      // Add tile layer
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(mapInstanceRef.current);
    }

    if (mapInstanceRef.current && route) {
      // Clear existing layers
      mapInstanceRef.current.eachLayer((layer) => {
        if (layer instanceof L.Marker || layer instanceof L.Polyline) {
          mapInstanceRef.current.removeLayer(layer);
        }
      });

      // Draw polyline
      if (route.map_path && route.map_path.length > 0) {
        const latLngs = route.map_path.map((point) => [point.lat, point.lon]);
        const polyline = L.polyline(latLngs, {
          color: '#3b82f6',
          weight: 4,
          opacity: 0.7,
        }).addTo(mapInstanceRef.current);

        // Fit map to polyline bounds
        mapInstanceRef.current.fitBounds(polyline.getBounds(), { padding: [50, 50] });
      }

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
        });
      }
    }
  }, [route]);

  return <div ref={mapRef} style={{ width: '100%', height: '100%' }} data-testid="route-leaflet-map" />;
}
