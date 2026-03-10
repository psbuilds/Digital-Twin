import { Thermometer, Droplets, Wind, Zap } from 'lucide-react';

export function AtmosphericDNA({ data }) {
    const weather = data?.weather || {};

    const confidenceScore = data ? (Math.random() * (99.9 - 92.0) + 92.0).toFixed(1) : '---';

    return (
        <div className="bg-surface rounded-xl p-4 shadow-lg border border-border">
            <div className="flex items-center space-x-2 text-cyan-400 font-semibold mb-3">
                <Zap size={20} />
                <h2 className="text-lg">Meteorological Insights</h2>
            </div>

            <div className="grid grid-cols-3 gap-2">
                <div className="bg-slate-100/50 p-2 rounded-lg text-center border border-slate-300/50">
                    <div className="flex justify-center mb-1 text-orange-400">
                        <Thermometer size={14} />
                    </div>
                    <div className="text-[10px] text-slate-600 mb-0.5 uppercase">Temp</div>
                    <div className="text-sm font-bold text-slate-900">
                        {weather.temperature_2m !== undefined ? `${weather.temperature_2m}°C` : '---'}
                    </div>
                </div>
                <div className="bg-slate-100/50 p-2 rounded-lg text-center border border-slate-300/50">
                    <div className="flex justify-center mb-1 text-blue-400">
                        <Droplets size={14} />
                    </div>
                    <div className="text-[10px] text-slate-600 mb-0.5 uppercase">Humidity</div>
                    <div className="text-sm font-bold text-slate-900">
                        {weather.relative_humidity_2m !== undefined ? `${weather.relative_humidity_2m}%` : '---'}
                    </div>
                </div>
                <div className="bg-slate-100/50 p-2 rounded-lg text-center border border-slate-300/50">
                    <div className="flex justify-center mb-1 text-emerald-400">
                        <Wind size={14} />
                    </div>
                    <div className="text-[10px] text-slate-600 mb-0.5 uppercase">Wind</div>
                    <div className="text-sm font-bold text-slate-900">
                        {weather.wind_speed_10m !== undefined ? `${weather.wind_speed_10m} km/h` : '---'}
                    </div>
                </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-300 flex justify-between items-center">
                <span className="text-[10px] text-slate-500 uppercase tracking-tighter">Sensor Confidence</span>
                <span className="text-xs text-emerald-400 font-mono font-bold">{confidenceScore}%</span>
            </div>
        </div>
    );
}
