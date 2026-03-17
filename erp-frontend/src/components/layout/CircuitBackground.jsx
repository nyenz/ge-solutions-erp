// PATH: erp-frontend/src/components/layout/CircuitBackground.jsx
import React, { useState, useEffect, useRef } from 'react';
import { LAYER_1, LAYER_2, LAYER_3, ENDPOINTS, TURNS, CHIPS } from './circuitData';
import styles from './CircuitBackground.module.css';

/**
 * GE SOLUTIONS - CIRCUIT BACKGROUND ENGINE
 * This file contains the logic only. All coordinates are in circuitData.js.
 * Features: Zero-crash masking, literal hardware restoration, and 1-1 hover glow.
 */
const CircuitBackground = () => {
    const [mouse, setMouse] = useState({ x: -9999, y: -9999 });
    const svgRef = useRef(null);

    useEffect(() => {
        const handleMove = (e) => {
            const svg = svgRef.current;
            if (!svg) return;
            const pt = svg.createSVGPoint();
            pt.x = e.clientX; pt.y = e.clientY;
            // Map mouse pixels to SVG coordinates (1440x900 system)
            const ctm = svg.getScreenCTM();
            if (!ctm) return;
            const svgP = pt.matrixTransform(ctm.inverse());
            setMouse({ x: svgP.x, y: svgP.y });
        };

        const handleLeave = () => setMouse({ x: -9999, y: -9999 });

        window.addEventListener('mousemove', handleMove);
        svgRef.current?.addEventListener('mouseleave', handleLeave);

        return () => {
            window.removeEventListener('mousemove', handleMove);
        };
    }, []);

    const renderPaths = (paths, layerClass, radii) => (
        paths.map((item, i) => {
            const id = `${layerClass}-${i}`;
            return (
                <g key={id} className={`${styles[layerClass]} ${item.pulse ? styles[item.pulse] : ''}`}>
                    <path className={styles.lineBase} d={item.d} />
                    <path className={styles.lineGlow} d={item.d} mask={`url(#m-${id})`} />
                    
                    <defs>
                        <radialGradient id={`g-${id}`} cx={mouse.x} cy={mouse.y} r={radii} gradientUnits="userSpaceOnUse">
                            <stop offset="0%" stopColor="white" stopOpacity="1" />
                            <stop offset="70%" stopColor="white" stopOpacity="0.8" />
                            <stop offset="100%" stopColor="white" stopOpacity="0" />
                        </radialGradient>
                        <mask id={`m-${id}`}>
                            <rect x="0" y="0" width="1440" height="900" fill={`url(#g-${id})`} />
                        </mask>
                    </defs>
                </g>
            );
        })
    );

    return (
        <div className={styles.wrapper}>
            {/* Literal Particle Restoration */}
            {Array.from({ length: 20 }, (_, i) => (
                <div key={i} className={`${styles.particle} ${styles[`p${i + 1}`]}`} />
            ))}

            <svg ref={svgRef} className={styles.bgSvg} viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice">
                <defs>
                    <filter id="glowL1" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
                    <filter id="glowL2" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="3.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
                    <filter id="glowL3" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
                    <filter id="glowSoft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="1.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
                </defs>

                {/* THE TRACE LAYERS */}
                {renderPaths(LAYER_1, 'L1', 40)}
                {renderPaths(LAYER_2, 'L2', 55)}
                {renderPaths(LAYER_3, 'L3', 70)}

                {/* ORANGE ENDPOINT BOXES */}
                <g filter="url(#glowSoft)">
                    {ENDPOINTS.map((e, i) => (
                        <rect key={`e-${i}`} x={e.x} y={e.y} width="6" height="6" fill="none" stroke="#EE8C3A" strokeWidth="0.8" opacity="0.6" rx="1"/>
                    ))}
                    {TURNS.map((t, i) => (
                        <rect key={`t-${i}`} x={t.x} y={t.y} width="4" height="4" fill="#EE8C3A" opacity="0.4" rx="0.5"/>
                    ))}
                </g>

                {/* HARDWARE CHIP BODIES */}
                <g opacity="0.35" fill="#1a2a2e" stroke="#4a6a7a" strokeWidth="0.7">
                    {CHIPS.map((c, i) => (
                        <rect key={`c-${i}`} x={c.x} y={c.y} width={c.w} height={c.h} rx="2" />
                    ))}
                </g>

                {/* SYSTEM ANNOTATIONS */}
                <g fill="#4a5c60" fontFamily="monospace" fontSize="7" opacity="0.4">
                    <text x="76" y="26">SYS.0</text><text x="1350" y="26">SYS.1</text>
                    <text x="76" y="878">SYS.2</text><text x="1350" y="878">SYS.3</text>
                </g>
            </svg>
        </div>
    );
};

export default CircuitBackground;