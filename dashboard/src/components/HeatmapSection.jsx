import React, { useState, useEffect } from 'react';
import { Layout, Terminal, RefreshCw, BarChart3, Map as MapIcon } from 'lucide-react';

export const HeatmapSection = () => {
    const [mlOutput, setMlOutput] = useState('Loading output...');
    const [loading, setLoading] = useState(false);
    const [timestamp, setTimestamp] = useState(Date.now());

    useEffect(() => {
        fetchMlOutput();
    }, []);

    const fetchMlOutput = async () => {
        setLoading(true);
        try {
            const response = await fetch('/api/ml-results');
            const data = await response.json();
            setMlOutput(data.output || 'No output found.');
        } catch (error) {
            setMlOutput('Error fetching ML output: ' + error.message);
        } finally {
            setLoading(false);
            setTimestamp(Date.now());
        }
    };

    return (
        <div className="bg-surface border border-slate-800 rounded-xl overflow-hidden h-full flex flex-col">
            <div className="flex items-center justify-between px-4 py-3 bg-slate-900/50 border-b border-slate-800">
                <div className="flex items-center space-x-2 text-slate-300">
                    <MapIcon size={18} className="text-emerald-400" />
                    <span className="font-semibold text-sm">Kerala Statewide AQI Analysis</span>
                </div>
                <button
                    onClick={fetchMlOutput}
                    className="p-1.5 hover:bg-slate-800 rounded-lg transition-colors text-slate-400"
                    disabled={loading}
                >
                    <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                </button>
            </div>

            <div className="flex-1 overflow-auto p-4 flex flex-col space-y-6">

                {/* Visualizations Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {/* Actual Heatmap */}
                    <div className="flex flex-col space-y-2">
                        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-1 flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                            Target: Actual Sensor Values
                        </h3>
                        <div className="aspect-[3/4] bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-center p-2 shadow-2xl overflow-hidden">
                            <img
                                src={`/static/images/aqi_heatmap_actual.png?t=${timestamp}`}
                                alt="Actual AQI"
                                className="h-full w-full object-contain"
                            />
                        </div>
                    </div>

                    {/* Predicted Heatmap */}
                    <div className="flex flex-col space-y-2">
                        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-1 flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                            XGBoost: Spatial Prediction
                        </h3>
                        <div className="aspect-[3/4] bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-center p-2 shadow-2xl overflow-hidden">
                            <img
                                src={`/static/images/aqi_heatmap_predicted.png?t=${timestamp}`}
                                alt="Predicted AQI"
                                className="h-full w-full object-contain"
                            />
                        </div>
                    </div>
                </div>

                {/* Bottom Row: Graph and Logs */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                    {/* Static Prediction Graph */}
                    <div className="lg:col-span-1 flex flex-col space-y-2">
                        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-1 flex items-center gap-2">
                            <BarChart3 size={14} className="text-blue-400" />
                            24h Mean Statewide Forecast
                        </h3>
                        <div className="flex-1 bg-slate-950 rounded-lg border border-slate-800 p-2 min-h-[250px] flex items-center justify-center">
                            <img
                                src={`/static/images/aqi_hourly_forecast.png?t=${timestamp}`}
                                alt="Hourly Forecast"
                                className="max-h-full max-w-full object-contain"
                            />
                        </div>
                    </div>

                    {/* Execution Logs */}
                    <div className="lg:col-span-2 flex flex-col space-y-2">
                        <div className="flex items-center space-x-2 px-1 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                            <Terminal size={12} className="text-emerald-400" />
                            <span>ML Pipeline Execution Log</span>
                        </div>
                        <div className="bg-black/80 rounded-lg border border-slate-800 p-4 font-mono text-[10px] leading-relaxed text-emerald-400/80 shadow-2xl h-[250px] overflow-y-auto">
                            <pre className="whitespace-pre-wrap">{mlOutput}</pre>
                        </div>
                    </div>
                </div>
            </div>

            <div className="px-4 py-2 bg-slate-900/30 border-t border-slate-800/50 flex items-center justify-between">
                <span className="text-[10px] text-slate-500">
                    Source: <code className="text-slate-400">ml_prediction_digital_twin.py</code>
                </span>
                <span className="text-[10px] text-blue-400/80 font-medium">
                    Statewide Deep Ensemble Prediction
                </span>
            </div>
        </div>
    );
};
