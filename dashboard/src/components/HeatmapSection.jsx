import React, { useState, useEffect } from 'react';
import { Layout, Terminal, RefreshCw } from 'lucide-react';

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
                    <Layout size={18} className="text-blue-400" />
                    <span className="font-semibold text-sm">Spatial AQI Heatmap</span>
                </div>
                <button
                    onClick={fetchMlOutput}
                    className="p-1.5 hover:bg-slate-800 rounded-lg transition-colors text-slate-400"
                    disabled={loading}
                >
                    <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                </button>
            </div>

            <div className="flex-1 overflow-auto p-4 flex flex-col lg:flex-row gap-6">
                {/* Image Display */}
                <div className="flex-[1.5] flex flex-col space-y-2 min-h-[600px] lg:h-full">
                    <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wider px-1">Heatmap Visualization</h3>
                    <div className="flex-1 bg-slate-900/50 rounded-lg border border-slate-800 flex items-center justify-center p-2 shadow-inner group relative overflow-auto">
                        <img
                            src={`/static/images/aqi_heatmap_kerala.png?t=${timestamp}`}
                            alt="AQI Heatmap"
                            className="max-h-full max-w-full object-contain shadow-2xl rounded"
                        />
                        <div className="absolute bottom-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                            <span className="text-[10px] text-slate-300 bg-slate-800/80 px-2 py-1 rounded backdrop-blur-sm">
                                Full Spatial AQI (Kerala State)
                            </span>
                        </div>
                    </div>
                </div>

                {/* Terminal Output */}
                <div className="flex-1 flex flex-col space-y-2 min-h-[300px] lg:h-full">
                    <div className="flex items-center space-x-2 px-1 text-xs font-medium text-slate-500 uppercase tracking-wider">
                        <Terminal size={12} />
                        <span>Execution Pipeline Logs</span>
                    </div>
                    <div className="flex-1 bg-black/80 rounded-lg border border-slate-800 p-4 font-mono text-[11px] leading-relaxed text-emerald-400/90 shadow-2xl overflow-y-auto w-full">
                        <pre className="whitespace-pre-wrap">
                            {mlOutput}
                        </pre>
                    </div>
                </div>
            </div>

            <div className="px-4 py-2 bg-slate-900/30 border-t border-slate-800/50 flex items-center justify-between">
                <span className="text-[10px] text-slate-500 italic">
                    Pipeline Source: ml_prediction_digital_twin.py
                </span>
                <span className="text-[10px] text-blue-400 font-medium">
                    XGBoost Multi-Horizon Core
                </span>
            </div>
        </div>
    );
};
