import React from 'react';
import { keralaLocations } from '../data/keralaLocations';
import { MapPin } from 'lucide-react';

export function LocationSelector({ selectedLocation, onSelect }) {
    return (
        <div className="bg-surface rounded-xl p-4 shadow-lg border border-border">
            <div className="flex items-center space-x-2 text-blue-400 font-semibold mb-3">
                <MapPin size={20} />
                <h2 className="text-lg">Location Selection</h2>
            </div>
            <div className="flex flex-col space-y-2">
                <label htmlFor="location-select" className="text-sm text-gray-400">
                    Monitoring Hub:
                </label>
                <select
                    id="location-select"
                    className="bg-white border border-border text-slate-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 transition-colors"
                    value={selectedLocation ? selectedLocation.id : ''}
                    onChange={(e) => {
                        const loc = keralaLocations.find(l => l.id === e.target.value);
                        onSelect(loc);
                    }}
                >
                    {keralaLocations.map((loc) => (
                        <option key={loc.id} value={loc.id}>
                            {loc.name} ({loc.district})
                        </option>
                    ))}
                </select>
                <div className="text-xs text-slate-600 mt-2">
                    {selectedLocation && `Coords: [${selectedLocation.lat.toFixed(4)}, ${selectedLocation.lon.toFixed(4)}]`}
                </div>
            </div>
        </div>
    );
}
