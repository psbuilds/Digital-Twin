import React, { useState, useEffect } from 'react';
import { Box, Activity, Wind, CloudRain, Zap, TrendingDown, TrendingUp } from 'lucide-react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

export function TwinInsights({ location }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchInsights = async () => {
            if (!location) return;
            setLoading(true);
            try {
                const response = await fetch(`/api/dt-insights?lat=${location.lat}&lon=${location.lon}`);
                const result = await response.json();
                setData(result);
            } catch (err) {
                console.error("Failed to fetch DT insights:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchInsights();
    }, [location]);

    if (loading || !data) {
        return (
            <div className="bg-surface rounded-xl p-6 h-full flex flex-col items-center justify-center space-y-4 border border-border">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                <p className="text-slate-400 text-sm animate-pulse">Running Digital Twin Simulation...</p>
            </div>
        );
    }

    const chartConfig = {
        labels: data.history.map(h => h.time),
        datasets: [
            {
                label: 'Twin Simulated AQI',
                data: data.history.map(h => h.aqi),
                borderColor: 'rgb(14, 165, 233)',
                backgroundColor: 'rgba(14, 165, 233, 0.1)',
                fill: true,
                tension: 0.4,
            }
        ]
    };

    const latest = data.history[data.history.length - 1];

    const renderRuleEffect = (rule, impact) => {
        const isReduction = impact > 0;
        const Icon = rule.includes('wind') ? Wind : rule.includes('rain') ? CloudRain : Activity;

        return (
            <div key={rule} className="flex items-center justify-between p-2 bg-slate-800/50 rounded-lg border border-slate-700/50">
                <div className="flex items-center space-x-2">
                    <Icon size={14} className={isReduction ? "text-emerald-400" : "text-amber-400"} />
                    <span className="text-[10px] text-slate-300 capitalize">{rule.replace(/_/g, ' ')}</span>
                </div>
                <div className="flex items-center space-x-1">
                    {isReduction ? <TrendingDown size={12} className="text-emerald-500" /> : <TrendingUp size={12} className="text-amber-500" />}
                    <span className={`text-[10px] font-mono ${isReduction ? "text-emerald-400" : "text-amber-400"}`}>
                        {impact.toFixed(2)} pts
                    </span>
                </div>
            </div>
        );
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 h-full overflow-hidden">
            {/* Left: Chart */}
            <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-800 flex flex-col">
                <div className="flex items-center justify-between mb-2">
                    <h3 className="text-xs font-bold text-blue-400 uppercase tracking-widest flex items-center">
                        <Box size={14} className="mr-2" /> 24h Twin Trajectory
                    </h3>
                </div>
                <div className="flex-1 min-h-[140px]">
                    <Line
                        data={chartConfig}
                        options={{
                            maintainAspectRatio: false,
                            plugins: { legend: { display: false } },
                            scales: {
                                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b', font: { size: 10 } } },
                                x: { grid: { display: false }, ticks: { color: '#64748b', font: { size: 9 }, maxTicksLimit: 8 } }
                            }
                        }}
                    />
                </div>
            </div>

            {/* Right: Insights */}
            <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-800 flex flex-col overflow-y-auto">
                <h3 className="text-xs font-bold text-emerald-400 uppercase tracking-widest flex items-center mb-3">
                    <Zap size={14} className="mr-2" /> Physic-Rule Attribution
                </h3>
                <div className="space-y-2">
                    {Object.entries(latest.effects).map(([pollutant, rules]) => (
                        Object.entries(rules).map(([rule, impact]) => renderRuleEffect(rule, impact))
                    ))}
                    {Object.keys(latest.effects).length === 0 && (
                        <p className="text-[10px] text-slate-500 italic">Static conditions detected. No major rule-based deviations.</p>
                    )}
                </div>
                <div className="mt-auto pt-4 border-t border-slate-800">
                    <div className="flex justify-between items-center text-[10px]">
                        <span className="text-slate-500">Dominant Cause</span>
                        <span className="text-blue-400 font-bold uppercase">{latest.dominant}</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
