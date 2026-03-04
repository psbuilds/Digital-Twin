import React from 'react';
import { Activity } from 'lucide-react';

const limits = {
    pm10: 100, // µg/m³
    pm2_5: 60,
    nitrogen_dioxide: 80,
    sulphur_dioxide: 80,
    carbon_monoxide: 4, // modified scale for UI visually
    ozone: 100
};

export function PollutantPanel({ data, loading }) {
    if (loading || !data) {
        return (
            <div className="bg-surface rounded-xl p-4 shadow-lg border border-border animate-pulse">
                <div className="h-6 w-32 bg-slate-700 rounded mb-4"></div>
                <div className="space-y-3">
                    {[1, 2, 3, 4, 5, 6].map(i => (
                        <div key={i} className="h-10 bg-slate-700 rounded"></div>
                    ))}
                </div>
            </div>
        );
    }

    const renderBar = (label, key, val, unit, standard) => {
        let value = val !== null ? val : 0;
        let safeLevel = standard;
        let width = Math.min((value / safeLevel) * 100, 100);

        // Choose color
        let colorClass = 'bg-green-500';
        if (width > 50) colorClass = 'bg-yellow-400';
        if (width > 100) colorClass = 'bg-red-500';

        return (
            <div key={key} className="flex flex-col mb-4 last:mb-0">
                <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium text-slate-300">{label}</span>
                    <span className="text-slate-200">{val !== null ? val.toFixed(1) : 'N/A'} <span className="text-xs text-slate-500">{unit}</span></span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2">
                    <div className={`h-2 rounded-full ${colorClass}`} style={{ width: `${width}%` }}></div>
                </div>
            </div>
        );
    };

    return (
        <div className="bg-surface rounded-xl p-4 shadow-lg border border-border">
            <div className="flex items-center space-x-2 text-cyan-400 font-semibold mb-3">
                <Activity size={20} />
                <h2 className="text-lg">Live Pollutant Metrics</h2>
            </div>
            <div>
                {renderBar('PM2.5', 'pm2_5', data.pm2_5, 'µg/m³', limits.pm2_5)}
                {renderBar('PM10', 'pm10', data.pm10, 'µg/m³', limits.pm10)}
                {renderBar('NO2', 'nitrogen_dioxide', data.nitrogen_dioxide, 'µg/m³', limits.nitrogen_dioxide)}
                {renderBar('SO2', 'sulphur_dioxide', data.sulphur_dioxide, 'µg/m³', limits.sulphur_dioxide)}
                {renderBar('CO', 'carbon_monoxide', data.carbon_monoxide, 'µg/m³', limits.carbon_monoxide)}
                {renderBar('O3', 'ozone', data.ozone, 'µg/m³', limits.ozone)}
            </div>
        </div>
    );
}
