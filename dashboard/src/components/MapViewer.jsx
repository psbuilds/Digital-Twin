import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, CircleMarker } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.heat';

// Fix leafet icon paths
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

const KERALA_BOUNDS = [
    [8.17, 74.85], // SouthWest
    [12.78, 77.42] // NorthEast
];

const getAqiColor = (aqi) => {
    if (aqi <= 50) return '#059669'; // Deep Emerald
    if (aqi <= 100) return '#f59e0b'; // Amber
    if (aqi <= 200) return '#ea580c'; // Vivid Orange
    if (aqi <= 300) return '#dc2626'; // Crimson
    if (aqi <= 400) return '#7c3aed'; // Deep Violet
    return '#4c1d95'; // Extra Deep Purple
};

const getAqiIntensity = (aqi) => {
    return Math.min(0.6, 0.2 + (aqi / 300));
};

// Heatmap configuration component
function HeatLayer({ points }) {
    const map = useMap();

    useEffect(() => {
        if (!map || !points.length) return;

        // Custom Gradient for high intensity mapping
        const heatLayer = L.heatLayer(points, {
            radius: 150, // Increased significantly for maximum state-wide coverage
            blur: 90, // Adjusted for contrasting overlapping areas
            maxZoom: 9,
            max: 1.0,
            gradient: {
                0.15: '#00e400', // Green (Good)
                0.3: '#ffff00',  // Yellow (Satisfactory)
                0.5: '#ff7e00',  // Orange (Moderate)
                0.7: '#ff0000',  // Red (Poor)
                0.9: '#8f3f97',  // Purple (Very Poor)
                1.0: '#7e0023'   // Maroon (Severe)
            }
        }).addTo(map);

        return () => {
            map.removeLayer(heatLayer);
        };
    }, [map, points]);

    return null;
}

function MapController({ center, bounds }) {
    const map = useMap();
    useEffect(() => {
        map.setMaxBounds(bounds);
        map.setView(center, map.getZoom());
    }, [center, bounds, map]);
    return null;
}

export function MapViewer({ selectedLocation, nodes = [] }) {
    const center = selectedLocation ? [selectedLocation.lat, selectedLocation.lon] : [10.8505, 76.2711];

    // Normalized so that even low values are visible and peaks handle severe AQI.
    const heatPoints = nodes.map(node => [
        node.lat,
        node.lon,
        Math.min(1.0, Math.max(0.15, node.aqi / 400))
    ]);

    return (
        <div className="h-full w-full rounded-xl overflow-hidden border border-border shadow-lg">
            <MapContainer
                center={center}
                zoom={selectedLocation ? 10 : 7}
                minZoom={6}
                maxBounds={KERALA_BOUNDS}
                maxBoundsViscosity={1.0}
                style={{ height: '100%', width: '100%' }}
                className="z-0"
            >
                <MapController center={center} bounds={KERALA_BOUNDS} />
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    // Removed grayscale filter for Light Mode
                    className="map-tiles"
                />

                {/* Real Dynamic Heatmap Layer */}
                <HeatLayer points={heatPoints} />

                {/* Node Markers */}
                {nodes.map((node, idx) => (
                    <CircleMarker
                        key={`node-${node.id || idx}`}
                        center={[node.lat, node.lon]}
                        radius={selectedLocation?.id === node.id ? 10 : 6}
                        pathOptions={{
                            fillColor: getAqiColor(node.aqi),
                            fillOpacity: 1,
                            color: '#fff',
                            weight: 2
                        }}
                    >
                        <Popup className="custom-popup">
                            <div className="p-1">
                                <strong className="text-slate-900 block border-b pb-1 mb-1">{node.name}</strong>
                                <div className="flex justify-between items-center space-x-4">
                                    <span className="text-slate-600 font-medium">AQI Value:</span>
                                    <span className="font-bold" style={{ color: getAqiColor(node.aqi) }}>{Math.round(node.aqi)}</span>
                                </div>
                                <div className="text-[10px] text-slate-400 mt-1 italic">
                                    Telemetry: {node.status || 'Active'}
                                </div>
                            </div>
                        </Popup>
                    </CircleMarker>
                ))}

                {/* Selected Location Highlight Marker (If not in nodes) */}
                {selectedLocation && !nodes.find(n => n.id === selectedLocation.id) && (
                    <Marker position={[selectedLocation.lat, selectedLocation.lon]}>
                        <Popup className="custom-popup">
                            <strong className="text-black">{selectedLocation.name}</strong>
                            <div className="text-black text-sm">{selectedLocation.district} District</div>
                        </Popup>
                    </Marker>
                )}
            </MapContainer>
        </div>
    );
}
