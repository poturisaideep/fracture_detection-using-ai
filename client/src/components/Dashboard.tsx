import React, { useState, useRef, useEffect } from 'react';
import { Upload, FileText, History, ZoomIn, Layers, Download, CheckCircle, Activity, Users } from 'lucide-react';
import { uploadXRay, DetectionResult, getSystemStatus } from '../services/api';
import XRayViewer from './XRayViewer';
import PatientSidebar from './PatientSidebar';
import PatientEntryModal from './PatientEntryModal';
import PatientList from './PatientList';
import { DetectionResult as APIDetectionResult, ScanRecord } from '../services/api';

// Map database record to frontend result type
const mapScanToResult = (scan: ScanRecord): APIDetectionResult => ({
    scan_id: scan.scan_uuid,
    original_url: scan.original_path,
    processed_url: scan.processed_path,
    heatmap_url: scan.heatmap_path,
    patient_id: scan.patient_str_id,
    patient_name: scan.patient_name,
    detection: {
        confidence_score: scan.confidence_score,
        body_part: scan.body_part,
        severity_grade: scan.severity_grade as any,
        bounding_box: { x: 0, y: 0, width: 0, height: 0 } // Mock for now
    },
    report: {
        summary: scan.summary,
        severity: scan.severity_grade,
        timestamp: scan.timestamp
    }
});

const Dashboard: React.FC = () => {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<APIDetectionResult | null>(null);
    const [systemOnline, setSystemOnline] = useState(false);
    const [currentView, setCurrentView] = useState<'dashboard' | 'patients'>('dashboard');
    const [isPatientModalOpen, setIsPatientModalOpen] = useState(false);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        const checkConnection = async () => {
            try {
                const data = await getSystemStatus();
                if (data.status === 'online') {
                    setSystemOnline(true);
                    console.log("Connected to AI Backend");
                }
            } catch (error) {
                console.error("Backend unreachable", error);
                setSystemOnline(false);
            }
        };
        checkConnection();
    }, []);

    const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;
        setSelectedFile(file);
        setIsPatientModalOpen(true);
    };

    const handlePatientSubmit = async (patientId: string, patientName: string) => {
        if (!selectedFile) return;

        setIsPatientModalOpen(false);
        setLoading(true);
        try {
            const data = await uploadXRay(selectedFile, patientId, patientName);
            const enhancedData = {
                ...data,
                patient_id: patientId,
                patient_name: patientName
            };
            setResult(enhancedData);
            setCurrentView('dashboard');
        } catch (error) {
            console.error("Upload failed", error);
            alert("Failed to process X-ray. Is the backend running?");
        } finally {
            setLoading(false);
            setSelectedFile(null);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    return (
        <div className="dashboard-container">
            <header className="header">
                <div className="logo" style={{ fontSize: '1.2rem', letterSpacing: 'normal', textTransform: 'none' }}>
                    X-ray Detection Model using AI
                </div>
                <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem' }}>
                        <div style={{ width: 8, height: 8, borderRadius: '50%', background: systemOnline ? '#10b981' : '#ef4444' }}></div>
                        {systemOnline ? 'AI INFRASTRUCTURE ONLINE' : 'OFFLINE'}
                    </div>
                    <button
                        className="btn btn-primary"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={loading}
                    >
                        {loading ? <Activity className="animate-spin" size={16} /> : <Upload size={16} />}
                        {loading ? 'ANALYZING...' : 'UPLOAD SCAN'}
                    </button>
                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileSelect}
                        style={{ display: 'none' }}
                        accept="image/*"
                    />
                </div>
            </header>

            <nav style={{ gridArea: 'nav', background: 'var(--panel-bg)', borderRight: '1px solid var(--border-color)', padding: '24px 12px' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <button
                        className="btn"
                        style={{
                            justifyContent: 'flex-start',
                            background: currentView === 'dashboard' ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
                            color: currentView === 'dashboard' ? 'var(--accent-primary)' : 'inherit'
                        }}
                        onClick={() => setCurrentView('dashboard')}
                    >
                        <Layers size={18} /> DASHBOARD
                    </button>
                    <button
                        className="btn"
                        style={{
                            justifyContent: 'flex-start',
                            background: currentView === 'patients' ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
                            color: currentView === 'patients' ? 'var(--accent-primary)' : 'inherit'
                        }}
                        onClick={() => setCurrentView('patients')}
                    >
                        <Users size={18} /> PATIENT LIST
                    </button>
                </div>
            </nav>

            <main className="main-content">
                {currentView === 'patients' ? (
                    <PatientList
                        onBack={() => setCurrentView('dashboard')}
                        onViewScan={(scan) => {
                            setResult(mapScanToResult(scan));
                            setCurrentView('dashboard');
                        }}
                    />
                ) : result ? (
                    <XRayViewer result={result} />
                ) : (
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', opacity: 0.5 }}>
                        <Upload size={64} strokeWidth={1} style={{ marginBottom: '24px' }} />
                        <h2 style={{ fontWeight: 400 }}>No Active Scan Selected</h2>
                        <p>Upload a high-resolution DICOM or JPEG to begin AI analysis</p>
                    </div>
                )}
            </main>

            <PatientEntryModal
                isOpen={isPatientModalOpen}
                onClose={() => setIsPatientModalOpen(false)}
                onSubmit={handlePatientSubmit}
            />

            <aside className="sidebar">
                <PatientSidebar result={result} />
            </aside>
        </div>
    );
};

export default Dashboard;
