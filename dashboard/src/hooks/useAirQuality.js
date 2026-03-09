import { useState, useEffect } from 'react';

export function useAirQuality(lat, lon, refreshInterval = 60000) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        let isMounted = true;

        const fetchData = async () => {
            if (isMounted) {
                setLoading(true);
                setError(null);
            }

            try {
                const aqUrl = `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${lat}&longitude=${lon}&current=pm10,pm2_5,nitrogen_dioxide,sulphur_dioxide,carbon_monoxide,ozone`;
                const weatherUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m`;

                const [aqRes, weatherRes] = await Promise.all([
                    fetch(aqUrl),
                    fetch(weatherUrl)
                ]);

                if (!aqRes.ok || !weatherRes.ok) {
                    throw new Error('Failed to fetch data');
                }

                const aqResult = await aqRes.json();
                const weatherResult = await weatherRes.json();

                if (isMounted) {
                    // Map Open-Meteo fields to required keys
                    const current = aqResult.current;
                    setData({
                        pm2p5: current.pm2_5,
                        pm10: current.pm10,
                        co: current.carbon_monoxide !== null ? current.carbon_monoxide / 1000 : null, // Convert µg/m³ to mg/m³
                        no2: current.nitrogen_dioxide,
                        go3: current.ozone,
                        so2: current.sulphur_dioxide,
                        weather: weatherResult.current
                    });
                    setLoading(false);
                    setError(null);
                }
            } catch (err) {
                if (isMounted) {
                    setError(err.message);
                    setLoading(false);
                }
            }
        };

        fetchData();

        const intervalId = setInterval(fetchData, refreshInterval);

        return () => {
            isMounted = false;
            clearInterval(intervalId);
        };
    }, [lat, lon, refreshInterval]);

    return { data, loading, error };
}
