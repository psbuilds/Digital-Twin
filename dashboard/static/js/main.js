// Set Cesium Ion access token
Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI2NmQxMDBkNi1mZmFhLTQ3MjItOTIzZi02NDI1M2Q2MDczNDciLCJpZCI6Mzg3MjA1LCJpYXQiOjE3NzAyNjYxMTV9.xKzabHZ3YfAdm77_XObT3pOqcTAKPlHADYjwK7y0f_w';

// Global Instances
let observerEngine;
let dnaChartObserver;
let dnaChartSim;
let predictionChart;
let observerViewer;
let predictiveViewer;

// Initialize Components
document.addEventListener('DOMContentLoaded', () => {
    initViewers();
    initCharts();
    initTabs();
    initLiveData();
    initSimLogic();
    initPredictiveLogic();
});

function initViewers() {
    // Observer Viewer
    observerViewer = new Cesium.Viewer('cesiumContainerObserver', {
        animation: false,
        timeline: false,
        baseLayerPicker: false,
        infoBox: false,
        selectionIndicator: false,
        navigationHelpButton: false,
        sceneModePicker: false,
        geocoder: false,
        homeButton: false
    });

    const osmImagery = new Cesium.UrlTemplateImageryProvider({
        url: 'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png'
    });
    observerViewer.imageryLayers.addImageryProvider(osmImagery);

    // Initial position
    observerViewer.camera.setView({
        destination: Cesium.Cartesian3.fromDegrees(76.2673, 9.9312, 12000),
        orientation: {
            heading: Cesium.Math.toRadians(0),
            pitch: Cesium.Math.toRadians(-45),
            roll: 0
        }
    });

    // Initialize Pollution Engine for Observer
    observerEngine = new PollutionEngine(observerViewer);
    observerEngine.init();

    // Predictive Viewer
    predictiveViewer = new Cesium.Viewer('cesiumContainerPredictive', {
        animation: false,
        timeline: false,
        baseLayerPicker: false,
        infoBox: false,
        selectionIndicator: false,
        navigationHelpButton: false,
        sceneModePicker: false,
        geocoder: false,
        homeButton: false
    });

    predictiveViewer.imageryLayers.addImageryProvider(osmImagery);

    predictiveViewer.camera.setView({
        destination: Cesium.Cartesian3.fromDegrees(76.2673, 10.5, 300000), // Zoomed out to see Kerala
        orientation: {
            heading: Cesium.Math.toRadians(0),
            pitch: Cesium.Math.toRadians(-90),
            roll: 0
        }
    });

    // Sync views if needed (optional)
}

// Tab Logic
function initTabs() {
    const navItems = document.querySelectorAll('.nav-item');
    const tabViews = document.querySelectorAll('.tab-view');

    navItems.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.dataset.tab;

            // UI Update
            navItems.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // View Update
            tabViews.forEach(view => {
                view.classList.remove('active');
                if (view.id === `${targetTab}-view`) {
                    view.classList.add('active');
                }
            });

            console.log('Switched to tab:', targetTab);
        });
    });
}

function initCharts() {
    const radarConfig = (id) => ({
        type: 'radar',
        data: {
            labels: ['Dispersion', 'Sea Breeze', 'Urban Heat', 'Traffic', 'Industrial', 'Humidity'],
            datasets: [{
                data: [45, 65, 30, 80, 55, 40],
                backgroundColor: 'rgba(14, 165, 233, 0.4)',
                borderColor: '#0ea5e9',
                borderWidth: 2,
                pointBackgroundColor: '#0ea5e9',
                pointRadius: 3
            }]
        },
        options: {
            scales: {
                r: {
                    angleLines: { color: '#e2e8f0' },
                    grid: { color: '#f1f5f9' },
                    pointLabels: { font: { family: 'Outfit', size: 10, weight: '700' }, color: '#64748b' },
                    ticks: { display: false },
                    suggestedMin: 0,
                    suggestedMax: 100
                }
            },
            plugins: { legend: { display: false } },
            maintainAspectRatio: false
        }
    });

    dnaChartObserver = new Chart(document.getElementById('dnaRadarObserver').getContext('2d'), radarConfig());
    dnaChartSim = new Chart(document.getElementById('dnaRadarSim').getContext('2d'), radarConfig());

    // Prediction Trend Chart
    predictionChart = new Chart(document.getElementById('predictionChart').getContext('2d'), {
        type: 'line',
        data: {
            labels: ['Now', '+1h', '+6h', '+24h', '+1w'],
            datasets: [{
                label: 'PM2.5 Trend',
                data: [30, 32, 35, 28, 40],
                borderColor: '#a855f7',
                backgroundColor: 'rgba(168, 85, 247, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: false, grid: { color: '#f1f5f9' } },
                x: { grid: { display: false } }
            },
            maintainAspectRatio: false
        }
    });
}

// Live Data Fetching
let allNodes = [];
let selectedNodeId = null;

async function initLiveData() {
    const refreshBtn = document.getElementById('refreshBtn');

    const fetchData = async () => {
        const aqiEl = document.getElementById('main-aqi-value');
        const syncEl = document.getElementById('sync-time');
        const nodeLabel = document.getElementById('node-label');
        const nodeName = document.getElementById('current-node-name');

        if (aqiEl && aqiEl.innerText === '--') aqiEl.innerText = '...';

        try {
            console.log('Fetching live data from Open-Meteo batch endpoint...');
            const endpoint = '/api/open-meteo-aqi';
            const response = await fetch(endpoint);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            console.log(`Fetched ${data.nodes ? data.nodes.length : 0} nodes successfully.`);

            allNodes = data.nodes || [];
            if (allNodes.length > 0) {
                // Populate Dropdown
                const select = document.getElementById('locationSelect');
                if (select) {
                    const currentVal = select.value;
                    select.innerHTML = '<option value="">Switch Location...</option>';
                    allNodes.forEach(node => {
                        const opt = document.createElement('option');
                        opt.value = node.id;
                        opt.text = node.name;
                        select.appendChild(opt);
                    });
                    if (currentVal && allNodes.find(n => n.id === currentVal)) {
                        select.value = currentVal;
                    }
                }

                if (!selectedNodeId || !allNodes.find(n => n.id === selectedNodeId)) {
                    selectedNodeId = allNodes[0].id;
                }

                try {
                    updateObserverUI();
                } catch (uiErr) {
                    console.error('updateObserverUI failed:', uiErr);
                }

                // Update map markers
                if (observerEngine) {
                    observerEngine.updateStations(allNodes);
                }

                const now = new Date();
                if (syncEl) syncEl.innerText = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            } else {
                console.error('No nodes returned from API');
                if (aqiEl) aqiEl.innerText = 'OFF';
                if (nodeLabel) nodeLabel.innerText = "Data Offline";
                if (nodeName) nodeName.innerText = "No Nodes";
            }
        } catch (err) {
            console.error('Failed to fetch live data:', err);
            if (aqiEl) aqiEl.innerText = 'ERR';
            if (nodeLabel) nodeLabel.innerText = "Sync Error";
            if (nodeName) nodeName.innerText = "Connection Lost";
        }
    };

    fetchData();
    refreshBtn.addEventListener('click', fetchData);

    // Auto-refresh every 5 minutes
    setInterval(fetchData, 300000);

    // Location selector listener
    const select = document.getElementById('locationSelect');
    if (select) {
        select.addEventListener('change', (e) => {
            if (e.target.value) {
                selectedNodeId = e.target.value;
                updateObserverUI();

                // Zoom to location on map
                const node = allNodes.find(n => n.id === selectedNodeId);
                if (node && observerViewer) {
                    observerViewer.camera.flyTo({
                        destination: Cesium.Cartesian3.fromDegrees(node.lon, node.lat, 5000),
                        duration: 1.5
                    });
                }
            }
        });
    }
}

function updateObserverUI() {
    if (allNodes.length === 0) return;

    // Find selected node
    const primary = allNodes.find(n => n.id === selectedNodeId) || allNodes[0];

    document.getElementById('current-node-name').innerText = primary.name;
    document.getElementById('node-label').innerText = primary.name;
    const aqiEl = document.getElementById('main-aqi-value');
    aqiEl.innerText = primary.aqi || 'N/A';
    if (primary.color) {
        aqiEl.style.color = primary.color;
    }

    document.getElementById('humidity-val').innerText = primary.metrics.humidity;
    document.getElementById('wind-val').innerText = primary.metrics.wind;

    // Update reasoning
    if (primary.reasoning) {
        const reasoningEl = document.querySelector('.model-reasoning p');
        if (reasoningEl) reasoningEl.innerText = `"${primary.reasoning}"`;
    }

    // Update pollutant bars
    const polls = primary.pollutants;
    const barsContainer = document.querySelector('.pollutant-bars');
    if (barsContainer) {
        barsContainer.innerHTML = '';
        Object.entries(polls).forEach(([key, val]) => {
            if (val === null) return;
            // Scale normalization for display
            let maxVal = 150;
            if (key === 'pm10') maxVal = 250;
            if (key === 'co') maxVal = 5;
            if (key === 'no2') maxVal = 100;

            const width = Math.min(100, (val / maxVal) * 100);
            const row = document.createElement('div');
            row.className = 'pollutant-row';
            row.innerHTML = `
                <label>${key.toUpperCase()}</label>
                <div class="bar-container">
                    <div class="bar" style="width: ${width}%; background: ${primary.color || '#0ea5e9'};"></div>
                </div>
                <span class="val">${val.toFixed(1)}</span>
            `;
            barsContainer.appendChild(row);
        });
    }

    // Update Radar Chart data (keep semi-random but biased by AQI)
    const factor = (primary.aqi || 50) / 200;
    dnaChartObserver.data.datasets[0].data = dnaChartObserver.data.datasets[0].data.map(v =>
        Math.max(10, Math.min(100, 40 + factor * 60 + (Math.random() - 0.5) * 10))
    );
    dnaChartObserver.update();

    // Zoom camera to station if updated manually
    if (observerViewer && primary.lat) {
        // Only zoom if this was triggered by a user click, or just keep it centered
    }
}

// Simulation Logic
function initSimLogic() {
    const sliders = ['traffic-sim', 'industry-sim', 'forest-sim'];
    const updateSim = () => {
        const traffic = parseInt(document.getElementById('traffic-sim').value);
        const industry = parseInt(document.getElementById('industry-sim').value);
        const forest = parseInt(document.getElementById('forest-sim').value);

        // Simulation impact formula
        const aqiDelta = Math.round(((traffic - 100) * 0.4) + ((industry - 100) * 0.3) - ((forest - 100) * 0.5));

        const deltaEl = document.getElementById('aqi-delta');
        deltaEl.innerText = (aqiDelta >= 0 ? '+' : '') + aqiDelta + ' %';
        deltaEl.style.color = aqiDelta > 10 ? '#ef4444' : (aqiDelta < -10 ? '#10b981' : '#0ea5e9');

        const healthSavings = (aqiDelta * -150).toLocaleString();
        document.getElementById('health-delta').innerText = '$' + healthSavings;

        // Update Sim Radar Chart
        dnaChartSim.data.datasets[0].data[3] = Math.min(100, traffic * 0.6); // Traffic
        dnaChartSim.data.datasets[0].data[4] = Math.min(100, industry * 0.5); // Industry
        dnaChartSim.data.datasets[0].data[0] = Math.max(10, 80 - (aqiDelta * 0.5)); // Dispersion
        dnaChartSim.update();
    };

    sliders.forEach(id => {
        document.getElementById(id).addEventListener('input', updateSim);
    });

    updateSim();
}

// Predictive Tab Logic
async function initPredictiveLogic() {
    const cards = document.querySelectorAll('.p-card');

    const updatePredictiveView = async (horizon = 24) => {
        try {
            // 1. Fetch horizon predictions for cards (if not already loaded)
            const predRes = await fetch('/api/predictions?pollutant=pm2p5');
            const preds = await predRes.json();

            // Update UI cards
            if (preds[1]) document.getElementById('pred-1h').innerText = preds[1].toFixed(1);
            if (preds[6]) document.getElementById('pred-6h').innerText = preds[6].toFixed(1);
            if (preds[24]) document.getElementById('pred-24h').innerText = preds[24].toFixed(1);
            if (preds[168]) document.getElementById('pred-168h').innerText = preds[168].toFixed(1);

            // Update Trend Chart
            predictionChart.data.datasets[0].data = [
                parseFloat(document.getElementById('main-aqi-value').innerText) || 30,
                preds[1], preds[6], preds[24], preds[168]
            ];
            predictionChart.update();

            // 2. Fetch Heatmap Data for the SELECTED horizon
            const heatRes = await fetch(`/api/heatmap?pollutant=pm2p5&horizon=${horizon}`);
            const districtData = await heatRes.json();

            renderHeatmap(districtData);

        } catch (err) {
            console.error('Failed to update predictive logic:', err);
        }
    };

    // Card click events
    cards.forEach(card => {
        card.addEventListener('click', () => {
            cards.forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            const h = card.dataset.horizon;
            updatePredictiveView(h);
        });
    });

    // Initial Load
    updatePredictiveView(24);
}

async function renderHeatmap(districtData) {
    predictiveViewer.entities.removeAll();

    try {
        const dataSource = await Cesium.GeoJsonDataSource.load('/static/data/kerala_districts.json', {
            stroke: Cesium.Color.BLACK,
            fill: Cesium.Color.GRAY.withAlpha(0.2),
            strokeWidth: 2
        });

        await predictiveViewer.dataSources.add(dataSource);

        const entities = dataSource.entities.values;
        for (let i = 0; i < entities.length; i++) {
            const entity = entities[i];
            const name = entity.properties.DISTRICT.getValue();
            const val = districtData[name] || 25; // Default if not found

            // Color scale matching the standard Indian AQI categories
            let color;
            if (val <= 50) color = Cesium.Color.fromCssColorString('#00B050'); // Good
            else if (val <= 100) color = Cesium.Color.fromCssColorString('#92D050'); // Satisfactory
            else if (val <= 200) color = Cesium.Color.fromCssColorString('#FFFF00'); // Moderate
            else if (val <= 300) color = Cesium.Color.fromCssColorString('#FF9900'); // Poor
            else if (val <= 400) color = Cesium.Color.fromCssColorString('#FF0000'); // Very Poor
            else color = Cesium.Color.fromCssColorString('#C00000'); // Severe

            entity.polygon.material = color.withAlpha(0.85);
            entity.polygon.outline = true;
            entity.polygon.outlineColor = Cesium.Color.BLACK;

            // Add Label at center
            const center = Cesium.BoundingSphere.fromPoints(entity.polygon.hierarchy.getValue().positions).center;
            predictiveViewer.entities.add({
                position: center,
                label: {
                    text: `${name}\n${val.toFixed(0)}`,
                    font: 'bold 10pt Outfit',
                    fillColor: Cesium.Color.WHITE,
                    outlineColor: Cesium.Color.BLACK,
                    outlineWidth: 2,
                    style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                    verticalOrigin: Cesium.VerticalOrigin.CENTER,
                    distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 1000000)
                }
            });
        }

        // Optional: zoom to Kerala
        predictiveViewer.zoomTo(dataSource);

    } catch (err) {
        console.error('Error rendering GeoJSON heatmap:', err);
    }
}
