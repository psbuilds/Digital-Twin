import React, { useState } from 'react';
import { Wind, Clock } from 'lucide-react';

export function SimulationPanel() {
    const [hourStart, setHourStart] = useState(0);
    const [windSpeed, setWindSpeed] = useState(12);

    return (
        <div className="bg-surface rounded-xl p-4 shadow-lg border border-border h-full flex flex-col">
            <div className="flex items-center space-x-2 text-indigo-400 font-semibold mb-4">
                <Wind size={20} />
                <h2 className="text-lg">AQI Dispersion Simulation</h2>
            </div>

            <div className="flex-1 bg-slate-50 rounded-lg border border-slate-300 p-4 mb-4 relative overflow-hidden flex items-center justify-center">
                {/* Mock Heatmap visualization container */}
                <div className="text-center opacity-50 z-10">
                    <Wind size={48} className="mx-auto text-indigo-500 animate-pulse mb-3" />
                    <p className="text-sm font-mono text-slate-700">Dispersion active layer</p>
                    <p className="text-xs text-slate-500">Overlay applied to Kerala Topology</p>
                </div>

                {/* CSS Heatmap simulation effect */}
                <div
                    className="absolute rounded-full blur-[80px] bg-red-600/30"
                    style={{
                        width: '200px', height: '100px',
                        transform: `translateX(${hourStart * 5}px) scale(${1 + (windSpeed / 50)})`,
                        transition: 'all 0.5s ease'
                    }}
                />
            </div>

            <div className="space-y-4">
                <div>
                    <label className="flex justify-between text-sm text-slate-600 mb-1">
                        <span className="flex items-center"><Clock size={14} className="mr-1" /> Time Horizon (+{hourStart}h)</span>
                        <span>24h Max</span>
                    </label>
                    <input
                        type="range" min="0" max="24" step="1"
                        value={hourStart} onChange={(e) => setHourStart(Number(e.target.value))}
                        className="w-full h-1 bg-slate-200 rounded-lg appearance-none cursor-pointer"
                    />
                </div>

                <div>
                    <label className="flex justify-between text-sm text-slate-600 mb-1">
                        <span>Wind Speed (km/h)</span>
                        <span>{windSpeed}</span>
                    </label>
                    <input
                        type="range" min="0" max="50" step="1"
                        value={windSpeed} onChange={(e) => setWindSpeed(Number(e.target.value))}
                        className="w-full h-1 bg-slate-200 rounded-lg appearance-none cursor-pointer"
                    />
                </div>
            </div>
        </div>
    );
}
