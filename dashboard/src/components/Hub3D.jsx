import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Box, Grid } from '@react-three/drei';
import { Box as BoxIcon } from 'lucide-react';

function KeralaTerrain() {
    return (
        <Grid args={[10, 10]} cellColor="rgba(45, 212, 191, 0.5)" sectionColor="rgba(45, 212, 191, 1)" fadeDistance={20} fadeStrength={1} />
    );
}

function PollutionSpike({ position, height, color }) {
    const meshRef = useRef();

    // Slight pulsation animation
    useFrame((state) => {
        if (meshRef.current) {
            meshRef.current.scale.y = 1 + Math.sin(state.clock.elapsedTime * 2 + position[0]) * 0.05;
        }
    });

    return (
        <Box ref={meshRef} args={[0.3, height, 0.3]} position={[position[0], height / 2, position[2]]}>
            <meshStandardMaterial color={color} transparent opacity={0.8} />
        </Box>
    );
}

export function Hub3D({ data }) {
    // Generate pseudo-3D data to demonstrate Kerala terrain spikes
    // Based on current data point (simulating 10 points)
    const aqiBase = data ? Math.max((data.pm2p5 || 0), (data.pm10 || 0)) : 40;

    const nodes = useMemo(() => {
        return Array.from({ length: 8 }).map((_, i) => {
            // Create a grid layout or random scattered points within 10x10
            const x = (Math.random() - 0.5) * 8;
            const z = (Math.random() - 0.5) * 8;
            const variation = (Math.random() - 0.5) * 40;

            const localAqi = Math.max(10, aqiBase + variation);
            const height = localAqi / 30; // Scale down for visual

            let color = 'green';
            if (localAqi > 50) color = 'yellow';
            if (localAqi > 100) color = 'orange';
            if (localAqi > 150) color = 'red';

            return { id: i, position: [x, height, z], height, color };
        });
    }, [data, aqiBase]);

    return (
        <div className="bg-surface rounded-xl p-4 shadow-lg border border-border h-full flex flex-col">
            <div className="flex items-center space-x-2 text-purple-400 font-semibold mb-4">
                <BoxIcon size={20} />
                <h2 className="text-lg">3D Hub Realtime</h2>
            </div>

            <div className="flex-1 bg-black rounded-lg overflow-hidden relative cursor-move">
                <Canvas camera={{ position: [0, 4, 8], fov: 50 }}>
                    <ambientLight intensity={0.5} />
                    <directionalLight position={[10, 10, 5]} intensity={1} />
                    <KeralaTerrain />
                    {nodes.map(node => (
                        <PollutionSpike key={node.id} position={node.position} height={node.height} color={node.color} />
                    ))}
                    <OrbitControls
                        enableZoom={true}
                        maxPolarAngle={Math.PI / 2 - 0.05} // Prevent going under ground
                        autoRotate
                        autoRotateSpeed={0.5}
                    />
                </Canvas>

                <div className="absolute top-2 left-2 flex space-x-2 px-2 py-1 bg-black/50 rounded-md text-xs font-mono">
                    <span className="text-green-500">{'<50'}</span>
                    <span className="text-yellow-500">{'50-100'}</span>
                    <span className="text-orange-500">{'100-150'}</span>
                    <span className="text-red-500">{'>150'}</span>
                </div>
            </div>
        </div>
    );
}
