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
                <p className="text-slate-600 text-sm animate-pulse">Running Digital Twin Simulation...</p>
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
            <div key={rule} className="flex items-center justify-between p-2 bg-slate-100/50 rounded-lg border border-slate-300/50">
                <div className="flex items-center space-x-2">
                    <div className={`p-1 rounded ${isReduction ? 'bg-emerald-500/10' : 'bg-amber-500/10'}`}>
                        <Icon size={12} className={isReduction ? "text-emerald-400" : "text-amber-400"} />
                    </div>
                    <span className="text-[10px] text-slate-700 capitalize font-medium">{rule.replace(/_/g, ' ')}</span>
                </div>
                <div className="flex items-center space-x-1">
                    {isReduction ? <TrendingDown size={12} className="text-emerald-500" /> : <TrendingUp size={12} className="text-amber-500" />}
                    <span className={`text-[10px] font-mono font-bold ${isReduction ? "text-emerald-400" : "text-amber-400"}`}>
                        {Math.abs(impact).toFixed(2)} units
                    </span>
                </div>
            </div>
        );
    };

    // Process effects to group by rule name and sum impacts across 24h simulation
    const groupedEffects = {};
    data.history.forEach(point => {
        Object.values(point.effects || {}).forEach(rules => {
            Object.entries(rules).forEach(([rule, impact]) => {
                groupedEffects[rule] = (groupedEffects[rule] || 0) + impact;
            });
        });
    });

    const notableEffects = Object.entries(groupedEffects).filter(([_, impact]) => Math.abs(impact) > 0.05);

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 h-full overflow-hidden">
            {/* Left: Chart */}
            <div className="bg-slate-50/50 rounded-xl p-4 border border-slate-200 flex flex-col">
                <div className="flex items-center justify-between mb-2">
                    <h3 className="text-xs font-bold text-blue-400 uppercase tracking-widest flex items-center">
                        <Box size={14} className="mr-2" /> 24h Twin Trajectory
                    </h3>
                    <div className="text-[10px] text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                        Simulating Physics
                    </div>
                </div>
                <div className="flex-1 min-h-[140px]">
                    <Line
                        data={chartConfig}
                        options={{
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { display: false },
                                tooltip: {
                                    backgroundColor: '#ffffff',
                                    padding: '12px',
                                    border: '1px solid #e2e8f0',
                                    borderRadius: '8px',
                                    borderColor: '#cbd5e1',
                                    borderWidth: 1
                                }
                            },
                            scales: {
                                y: { grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { color: '#64748b', font: { size: 10 } } },
                                x: { grid: { display: false }, ticks: { color: '#64748b', font: { size: 9 }, maxTicksLimit: 8 } }
                            }
                        }}
                    />
                </div>
            </div>

            {/* Right: Insights */}
            <div className="bg-slate-50/50 rounded-xl p-4 border border-slate-200 flex flex-col overflow-y-auto">
                <h3 className="text-xs font-bold text-emerald-400 uppercase tracking-widest flex items-center mb-3">
                    <Zap size={14} className="mr-2" /> Physical Impact Analysis
                </h3>
                <div className="space-y-2">
                    {notableEffects.map(([rule, impact]) => renderRuleEffect(rule, impact))}
                    {notableEffects.length === 0 && (
                        <div className="text-center py-6 opacity-40">
                            <Activity size={24} className="mx-auto mb-2" />
                            <p className="text-[10px] italic">Atmospheric equilibrium. No major rule-based movement detected.</p>
                        </div>
                    )}
                </div>
                <div className="mt-auto pt-4 border-t border-slate-200">
                    <div className="flex justify-between items-center mb-1">
                        <span className="text-[10px] text-slate-500 uppercase tracking-tighter">Atmospheric Driver</span>
                        <span className="text-[10px] text-blue-400 font-bold uppercase">{latest.dominant}</span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-[10px] text-slate-500 uppercase tracking-tighter">Current Confidence</span>
                        <span className="text-[10px] text-emerald-400 font-bold">PHYSICS-VERIFIED</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
