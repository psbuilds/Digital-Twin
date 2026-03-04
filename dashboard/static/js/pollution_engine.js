class PollutionEngine {
    constructor(viewer) {
        this.viewer = viewer;
        this.particles = [];
        this.layers = {
            'PM25': true,
            'PM10': true,
            'NO2': true
        };

        // Strict Kerala Bounds
        this.config = {
            count: 300,
            bounds: {
                minLon: 76.10, maxLon: 76.50, // Tight around Kochi
                minLat: 9.80, maxLat: 10.20,
                minAlt: 20, maxAlt: 300
            },
            motion: {
                windSpeed: 0.00001,
                oscAmp: 100
            }
        };

        this.stations = [
            { name: 'Vytilla', lon: 76.3213, lat: 9.9673 },
            { name: 'Eloor', lon: 76.2995, lat: 10.0754 },
            { name: 'MG Road', lon: 76.2825, lat: 9.9723 }
        ];
    }

    init() {
        this.createParticles();
        this.renderClusters();
        this.animate();
    }

    updateStations(newStations) {
        // Clear existing markers
        const markers = this.viewer.entities.values.filter(e => e.ellipse || e.point || e.label);
        markers.forEach(m => this.viewer.entities.remove(m));

        this.stations = newStations.map(s => ({
            id: s.id,
            name: s.name,
            lon: s.lon,
            lat: s.lat,
            aqi: s.aqi,
            color: s.color || '#facc15'
        }));

        this.renderClusters();

        // Refresh particles to be around new stations
        this.particles.forEach(p => this.viewer.entities.remove(p));
        this.particles = [];
        this.createParticles();
    }

    renderClusters() {
        this.stations.forEach(station => {
            const color = Cesium.Color.fromCssColorString(station.color);

            // Pulse circle
            this.viewer.entities.add({
                id: `pulse_${station.id}`,
                position: Cesium.Cartesian3.fromDegrees(station.lon, station.lat, 0),
                ellipse: {
                    semiMinorAxis: 150.0,
                    semiMajorAxis: 150.0,
                    material: color.withAlpha(0.2),
                    outline: true,
                    outlineColor: color,
                    heightReference: Cesium.HeightReference.CLAMP_TO_GROUND
                }
            });

            // Station Marker
            const marker = this.viewer.entities.add({
                id: station.id,
                position: Cesium.Cartesian3.fromDegrees(station.lon, station.lat, 50),
                point: {
                    pixelSize: 14,
                    color: color,
                    outlineColor: Cesium.Color.WHITE,
                    outlineWidth: 3
                },
                label: {
                    text: `${station.name}\nAQI: ${station.aqi || '--'}`,
                    font: 'bold 12px Outfit, sans-serif',
                    fillColor: Cesium.Color.WHITE,
                    outlineColor: Cesium.Color.BLACK,
                    outlineWidth: 2,
                    showBackground: true,
                    backgroundColor: new Cesium.Color(0, 0, 0, 0.7),
                    style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                    verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
                    pixelOffset: new Cesium.Cartesian2(0, -20)
                }
            });

            // Make markers interactive
            marker.description = `Air Quality Monitoring Station: ${station.name}`;
        });

        // Add Click Listener to Viewer for Node Selection
        if (!this.handler) {
            this.handler = new Cesium.ScreenSpaceEventHandler(this.viewer.scene.canvas);
            this.handler.setInputAction((movement) => {
                const pickedObject = this.viewer.scene.pick(movement.position);
                if (Cesium.defined(pickedObject) && pickedObject.id) {
                    const id = pickedObject.id.id || pickedObject.id;
                    if (this.stations.find(s => s.id === id)) {
                        console.log('Selected Node:', id);
                        selectedNodeId = id;
                        if (typeof updateObserverUI === 'function') updateObserverUI();
                    }
                }
            }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
        }
    }

    createParticles() {
        const types = Object.keys(this.layers);
        if (this.stations.length === 0) return;

        for (let i = 0; i < this.config.count; i++) {
            const type = types[Math.floor(Math.random() * types.length)];
            const station = this.stations[Math.floor(Math.random() * this.stations.length)];

            // Spread around stations
            const lon = station.lon + (Math.random() - 0.5) * 0.1;
            const lat = station.lat + (Math.random() - 0.5) * 0.1;
            const alt = this.config.bounds.minAlt + Math.random() * this.config.bounds.maxAlt;

            const intensity = Math.random();
            const color = Cesium.Color.fromCssColorString(station.color).withAlpha(0.6);

            const entity = this.viewer.entities.add({
                position: Cesium.Cartesian3.fromDegrees(lon, lat, alt),
                point: {
                    pixelSize: 3 + intensity * 5,
                    color: color,
                    disableDepthTestDistance: Number.POSITIVE_INFINITY
                },
                properties: {
                    baseLon: lon,
                    baseLat: lat,
                    baseAlt: alt,
                    type: type,
                    intensity: intensity,
                    phase: Math.random() * Math.PI * 2
                }
            });

            this.particles.push(entity);
        }
    }

    getColor(intensity) {
        if (intensity < 0.3) return Cesium.Color.fromCssColorString('#0ea5e9').withAlpha(0.5);
        if (intensity < 0.7) return Cesium.Color.fromCssColorString('#facc15').withAlpha(0.6);
        return Cesium.Color.fromCssColorString('#ef4444').withAlpha(0.7);
    }

    animate() {
        if (this.animationBound) return;
        this.animationBound = true;
        const startTime = Date.now();

        this.viewer.scene.preUpdate.addEventListener(() => {
            const time = (Date.now() - startTime) * 0.001;

            this.particles.forEach(p => {
                const props = p.properties;
                const phase = props.phase.getValue();

                const lonOffset = Math.sin(time * 0.15 + phase) * 0.008;
                const latOffset = Math.cos(time * 0.25 + phase) * 0.008;
                const altOffset = Math.sin(time * 0.8 + phase) * 15;

                const newLon = props.baseLon.getValue() + lonOffset;
                const newLat = props.baseLat.getValue() + latOffset;
                const newAlt = props.baseAlt.getValue() + altOffset;

                p.position = new Cesium.ConstantPositionProperty(Cesium.Cartesian3.fromDegrees(newLon, newLat, newAlt));
            });
        });
    }
}
