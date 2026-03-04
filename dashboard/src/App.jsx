import React, { useState, useEffect } from 'react';
import { MapViewer } from './components/MapViewer';
import { LocationSelector } from './components/LocationSelector';
import { PollutantPanel } from './components/PollutantPanel';
import { AtmosphericDNA } from './components/AtmosphericDNA';
import { SyncNodes } from './components/SyncNodes';
import { PredictivePanel } from './components/PredictivePanel';
import { Hub3D } from './components/Hub3D';
import { HeatmapSection } from './components/HeatmapSection';
import { useAirQuality } from './hooks/useAirQuality';
import { keralaLocations } from './data/keralaLocations';
import { Cloud, Radio } from 'lucide-react';

function App() {
    const [selectedLocation, setSelectedLocation] = useState(keralaLocations.find(l => l.id === 'koch'));
    const { data, loading, error } = useAirQuality(selectedLocation.lat, selectedLocation.lon);

    // Track refresh cycles for components that need triggering
    const [refreshKey, setRefreshKey] = useState(0);

    // Poll intervals
    useEffect(() => {
        const interval = setInterval(() => {
            setRefreshKey(prev => prev + 1);
        }, 60000);
        return () => clearInterval(interval);
    }, []);

    const [activeTab, setActiveTab] = useState('predictive');

    const renderTab = () => {
        switch (activeTab) {
            case 'predictive': return <PredictivePanel data={data} />;
            case '3dhub': return <Hub3D data={data} />;
            case 'heatmap': return <HeatmapSection />;
            default: return <PredictivePanel data={data} />;
        }
    };

    return (
        <div className="min-h-screen bg-background border-t-4 border-blue-500 font-sans p-6 text-slate-200">

            {/* Top Navigation / Header */}
            <header className="flex justify-between items-center bg-surface p-4 rounded-xl shadow-lg border border-border mb-6">
                <div className="flex items-center space-x-3">
                    <div className="p-2 bg-blue-500/20 text-blue-400 rounded-lg">
                        <Cloud size={28} />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
                            Digital Twin Kerala AQI
                        </h1>
                        <p className="text-xs text-slate-400 flex items-center mt-1">
                            <Radio size={12} className="mr-1 text-emerald-400 animate-pulse" />
                            Telemetry Online • Data Live Synchronizing
                        </p>
                    </div>
                </div>

                <div className="flex space-x-2">
                    {['predictive', '3dhub', 'heatmap'].map(tab => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${activeTab === tab
                                ? 'bg-blue-600 shadow-[0_0_15px_rgba(37,99,235,0.4)] text-white'
                                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                                }`}
                        >
                            {tab.charAt(0).toUpperCase() + tab.slice(1).replace('hub', ' Hub')}
                        </button>
                    ))}
                </div>
            </header>

            {/* Main Content Area */}
            {activeTab === 'heatmap' ? (
                <div className="h-[calc(100vh-160px)]">
                    <HeatmapSection />
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

                    {/* Left Column (3) - Metrics & Selectors */}
                    <div className="lg:col-span-3 space-y-6 flex flex-col h-full">
                        <LocationSelector
                            selectedLocation={selectedLocation}
                            onSelect={setSelectedLocation}
                        />
                        <AtmosphericDNA data={data} />
                        <SyncNodes refreshKey={refreshKey} />
                    </div>

                    {/* Center Column (6) - Primary Display Hub (Map & Advanced Features) */}
                    <div className="lg:col-span-6 flex flex-col space-y-6 border border-slate-800/50 rounded-2xl bg-slate-900/10 p-2 shadow-inner h-[800px]">
                        {/* Map Viewer Container */}
                        <div className="flex-1 rounded-xl overflow-hidden shadow-2xl relative order-1">
                            <MapViewer selectedLocation={selectedLocation} />
                            {error && (
                                <div className="absolute top-4 right-4 bg-red-500/90 text-white px-4 py-2 rounded shadow-lg z-[1000] text-sm">
                                    Live link disrupted. Falling back.
                                </div>
                            )}
                            {loading && (
                                <div className="absolute top-4 left-4 bg-blue-500/90 text-white px-4 py-2 rounded shadow-lg z-[1000] flex items-center text-sm">
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                    Updating telemetry...
                                </div>
                            )}
                        </div>

                        {/* Advanced Tab Panels Container */}
                        <div className="h-64 mt-6">
                            {renderTab()}
                        </div>
                    </div>

                    {/* Right Column (3) - Raw Pollutant Indicators */}
                    <div className="lg:col-span-3">
                        <PollutantPanel data={data} loading={loading} />
                    </div>

                </div>
            )}
        </div>
    );
}

export default App;
