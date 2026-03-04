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
                const url = `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${lat}&longitude=${lon}&current=pm10,pm2_5,nitrogen_dioxide,sulphur_dioxide,carbon_monoxide,ozone`;
                const response = await fetch(url);

                if (!response.ok) {
                    throw new Error('Failed to fetch air quality data');
                }

                const result = await response.json();
                if (isMounted) {
                    setData(result.current);
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
