import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, CircleMarker, GeoJSON, Tooltip } from 'react-leaflet';
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
    if (aqi <= 50) return '#00B050'; // Good - Dark Green
    if (aqi <= 100) return '#92D050'; // Satisfactory - Light Green
    if (aqi <= 200) return '#FFFF00'; // Moderate - Yellow
    if (aqi <= 300) return '#FF9900'; // Poor - Orange
    if (aqi <= 400) return '#FF0000'; // Very Poor - Red
    return '#800000'; // Severe - Maroon
};

// Heatmap configuration component — dynamically scales radius on zoom
function HeatLayer({ points }) {
    const map = useMap();

    useEffect(() => {
        if (!map || !points || points.length === 0) return;

        let currentLayer = null;

        function updateHeatmap() {
            if (currentLayer) {
                map.removeLayer(currentLayer);
            }

            const zoom = map.getZoom();

            const zoomDiff = Math.max(0, zoom - 6);
            const radius = Math.floor(12 + (zoomDiff * 5));
            const blur = Math.floor(15 + (zoomDiff * 4));

            // Calculate overlap factor so colors don't vanish when we zoom in
            // Grid step is 0.02 degrees.
            const pixelsPerDegree = (256 / 360) * Math.pow(2, zoom);
            const stepPixels = pixelsPerDegree * 0.02;

            // Compute overlapping cone volume factor
            let overlapFactor = (Math.PI * radius * radius) / (2.5 * stepPixels * stepPixels);
            overlapFactor = Math.max(1.0, overlapFactor);

            // AQI 500 is the maximum possible value
            const baseMaxAQI = 500;
            const dynamicMax = baseMaxAQI * overlapFactor;

            // Deep copy coordinates because L.heatLayer mutates the array
            const heatData = points.map(p => [p[0], p[1], p[2]]);

            currentLayer = L.heatLayer(heatData, {
                radius: Math.max(8, radius),
                blur: Math.max(10, blur),
                maxZoom: 15,
                max: dynamicMax,
                minOpacity: 0.35,
                gradient: {
                    // Gradient stops placed at AQI_threshold / 500
                    // This ensures each AQI range maps to its correct color
                    0.00: '#00B050',  // Dark Green  — Good start (AQI 0)
                    0.10: '#00B050',  // Dark Green  — Good end (AQI 50)
                    0.20: '#92D050',  // Light Green — Satisfactory end (AQI 100)
                    0.40: '#FFFF00',  // Yellow      — Moderate end (AQI 200)
                    0.60: '#FF9900',  // Orange      — Poor end (AQI 300)
                    0.80: '#FF0000',  // Red         — Very Poor end (AQI 400)
                    1.00: '#800000'   // Maroon      — Severe (AQI 500)
                }
            }).addTo(map);
        }

        updateHeatmap();
        map.on('zoomend', updateHeatmap);

        return () => {
            map.off('zoomend', updateHeatmap);
            if (currentLayer) {
                map.removeLayer(currentLayer);
            }
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
    const [gridPoints, setGridPoints] = useState([]);
    const [keralaGeo, setKeralaGeo] = useState(null);

    useEffect(() => {
        fetch('/api/heatmap-grid')
            .then(res => res.json())
            .then(data => {
                if (data.points) {
                    setGridPoints(data.points);
                }
            });

        fetch('/static/data/kerala_districts.json')
            .then(res => res.json())
            .then(data => setKeralaGeo(data));
    }, [nodes]);

    const center = selectedLocation ? [selectedLocation.lat, selectedLocation.lon] : [10.8505, 76.2711];

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
                    className="map-tiles"
                />

                {/* Heatmap Layer */}
                <HeatLayer points={gridPoints} />

                {/* District Boundaries */}
                {keralaGeo && (
                    <GeoJSON
                        data={keralaGeo}
                        style={{ fillColor: 'transparent', color: '#64748b', weight: 1, opacity: 0.4 }}
                    />
                )}

                {/* Node Markers with AQI value labels */}
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
                        <Tooltip
                            permanent={true}
                            direction="top"
                            offset={[0, -5]}
                            className="aqi-tooltip"
                        >
                            <span style={{
                                color: '#1e293b',
                                fontWeight: 'bold',
                                fontSize: '11px',
                                textShadow: '0 0 3px white'
                            }}>
                                {Math.round(node.aqi)}
                            </span>
                        </Tooltip>
                        <Popup className="custom-popup">
                            <div className="p-1">
                                <strong className="text-slate-900 block border-b pb-1 mb-1">{node.name}</strong>
                                <div className="flex justify-between items-center space-x-4">
                                    <span className="text-slate-600 font-medium">AQI Value:</span>
                                    <span className="font-bold" style={{ color: getAqiColor(node.aqi) }}>{Math.round(node.aqi)}</span>
                                </div>
                                <div className="text-[10px] text-slate-600 mt-1 italic">
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
