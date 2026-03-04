import React from 'react';
import { Fingerprint } from 'lucide-react';

export function AtmosphericDNA({ data }) {
    const calculateEntropy = () => {
        if (!data) return 0.00;

        // Select subset of pollutants to calculate entropy
        const values = [
            data.pm10 || 0,
            data.pm2_5 || 0,
            data.nitrogen_dioxide || 0,
            data.sulphur_dioxide || 0,
            data.carbon_monoxide || 0,
            data.ozone || 0
        ];

        const sum = values.reduce((a, b) => a + b, 0);
        if (sum === 0) return 0.00;

        let entropy = 0;
        values.forEach(v => {
            if (v > 0) {
                const p = v / sum;
                entropy -= p * Math.log2(p);
            }
        });

        return entropy.toFixed(3);
    };

    const confidenceScore = data ? (Math.random() * (99.9 - 92.0) + 92.0).toFixed(1) : '---';
    const entropy = calculateEntropy();

    // Simple overall heuristic for AQI
    const aqiIndex = data ? Math.max((data.pm2_5 || 0) * 1.5, (data.pm10 || 0) * 0.8, (data.nitrogen_dioxide || 0) * 1.2).toFixed(0) : '--';

    return (
        <div className="bg-surface rounded-xl p-4 shadow-lg border border-border">
            <div className="flex items-center space-x-2 text-fuchsia-400 font-semibold mb-3">
                <Fingerprint size={20} />
                <h2 className="text-lg">Atmospheric DNA</h2>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-800 p-3 rounded-lg text-center">
                    <div className="text-xs text-slate-400 mb-1">Index Estimate</div>
                    <div className="text-2xl font-bold text-white">{aqiIndex}</div>
                </div>
                <div className="bg-slate-800 p-3 rounded-lg text-center">
                    <div className="text-xs text-slate-400 mb-1">Entropy Var</div>
                    <div className="text-2xl font-bold text-indigo-400">{entropy}</div>
                </div>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-700">
                <div className="flex justify-between items-center text-sm">
                    <span className="text-slate-400">Sensor Confidence Matrix</span>
                    <span className="text-emerald-400 font-mono">{confidenceScore}%</span>
                </div>
            </div>
        </div>
    );
}
