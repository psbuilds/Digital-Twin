import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

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

function MapController({ center, bounds }) {
    const map = useMap();
    useEffect(() => {
        map.setMaxBounds(bounds);
        map.setView(center, map.getZoom());
    }, [center, bounds, map]);
    return null;
}

export function MapViewer({ selectedLocation }) {
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
                {selectedLocation && (
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
