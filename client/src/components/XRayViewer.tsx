import React, { useState } from 'react';
import { ZoomIn, Layers, Eye, EyeOff } from 'lucide-react';
import { DetectionResult } from '../services/api';

interface XRayViewerProps {
    result: DetectionResult;
}

const XRayViewer: React.FC<XRayViewerProps> = ({ result }) => {
    const [showHeatmap, setShowHeatmap] = useState(true);
    const [showBoxes, setShowBoxes] = useState(true);

    const API_ROOT = 'http://127.0.0.1:5001';

    return (
        <div className="viewer-grid fade-in">
            {/* Original Image Panel */}
            <div className="viewer-panel">
                <div className="panel-header">
                    <span>ORIGINAL X-RAY</span>
                    <span style={{ opacity: 0.5 }}>PRE-PROCESSED (LOG)</span>
                </div>
                <div className="image-container">
                    <img
                        src={`${API_ROOT}${result.processed_url}`}
                        alt="Original"
                        className="xray-image"
                    />
                </div>
            </div>

            {/* AI Annotated Panel */}
            <div className="viewer-panel" style={{ borderColor: result.detection.confidence_score > 0.9 ? 'rgba(16, 185, 129, 0.3)' : 'var(--border-color)' }}>
                <div className="panel-header">
                    <span style={{ color: 'var(--accent-primary)' }}>AI ANNOTATION & GRAD-CAM</span>
                    <span className={`severity-pill severity-${result.detection.severity_grade.toLowerCase()}`}>
                        {result.detection.severity_grade} RISK
                    </span>
                </div>
                <div className="image-container">
                    {/* Base Processed Image */}
                    <img
                        src={`${API_ROOT}${result.processed_url}`}
                        alt="AI Annotated"
                        className="xray-image"
                    />

                    {/* Heatmap Overlay */}
                    {showHeatmap && (
                        <img
                            src={`${API_ROOT}${result.heatmap_url}`}
                            alt="Grad-CAM"
                            className="xray-image"
                            style={{ position: 'absolute', top: 0, left: 0, opacity: 0.5, mixBlendMode: 'screen' }}
                        />
                    )}

                    {/* Bounding Box */}
                    {showBoxes && (
                        <div
                            className="bounding-box"
                            style={{
                                left: `${(result.detection.bounding_box.x / 800) * 100}%`, // Normalized mock coords
                                top: `${(result.detection.bounding_box.y / 800) * 100}%`,
                                width: `${(result.detection.bounding_box.width / 800) * 100}%`,
                                height: `${(result.detection.bounding_box.height / 800) * 100}%`
                            }}
                        >
                            <div style={{
                                position: 'absolute',
                                top: -24,
                                left: 0,
                                background: 'var(--accent-danger)',
                                fontSize: '0.7rem',
                                padding: '2px 6px',
                                color: 'white',
                                fontWeight: 700
                            }}>
                                FRACTURE: {Math.round(result.detection.confidence_score * 100)}%
                            </div>
                        </div>
                    )}
                </div>

                {/* Controls Overlay */}
                <div className="controls-overlay">
                    <button className="btn" onClick={() => setShowHeatmap(!showHeatmap)}>
                        {showHeatmap ? <Eye size={16} /> : <EyeOff size={16} />}
                        HEATMAP
                    </button>
                    <button className="btn" onClick={() => setShowBoxes(!showBoxes)}>
                        {showBoxes ? <Eye size={16} /> : <EyeOff size={16} />}
                        BOXES
                    </button>
                    <div style={{ width: 1, height: 20, background: 'rgba(255,255,255,0.2)' }}></div>
                    <button className="btn">
                        <ZoomIn size={16} /> ZOOM
                    </button>
                </div>
            </div>
        </div>
    );
};

export default XRayViewer;
