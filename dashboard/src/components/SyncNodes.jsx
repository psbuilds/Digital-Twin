import React, { useState, useEffect } from 'react';
import { RefreshCcw } from 'lucide-react';

export function SyncNodes({ refreshKey, nodes = [] }) {
    const [latency, setLatency] = useState(0);
    const [trend, setTrend] = useState('Stable');
    const [trendColor, setTrendColor] = useState('text-yellow-400');

    useEffect(() => {
        // Generate simulated latency and trend when refresh key changes
        setLatency(Math.floor(Math.random() * 50) + 12);

        const trends = [
            { text: 'Improving', color: 'text-green-400' },
            { text: 'Stable', color: 'text-yellow-400' },
            { text: 'Declining', color: 'text-red-400' }
        ];

        const randomTrend = trends[Math.floor(Math.random() * trends.length)];
        setTrend(randomTrend.text);
        setTrendColor(randomTrend.color);

    }, [refreshKey]);

    return (
        <div className="bg-surface rounded-xl p-4 shadow-lg border border-border">
            <div className="flex items-center space-x-2 text-orange-400 font-semibold mb-3">
                <RefreshCcw size={20} className={latency ? "animate-spin-slow" : ""} />
                <h2 className="text-lg">Synchronizing Nodes</h2>
            </div>

            <div className="space-y-4 font-mono">
                <div className="flex justify-between border-b border-slate-300 pb-2">
                    <span className="text-slate-600">Active Sensors</span>
                    <span className="text-slate-900 font-bold">{nodes.length} / 17</span>
                </div>
                <div className="flex justify-between border-b border-slate-300 pb-2">
                    <span className="text-slate-600">Sync Latency</span>
                    <span className="text-emerald-400">{latency} ms</span>
                </div>
                <div className="flex justify-between">
                    <span className="text-slate-600">Trend Vector</span>
                    <span className={`font-bold ${trendColor}`}>{trend}</span>
                </div>
            </div>
        </div>
    );
}
