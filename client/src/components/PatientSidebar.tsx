import React from 'react';
import { User, Calendar, FileType, Activity, Download, CheckCircle } from 'lucide-react';
import { DetectionResult } from '../services/api';

interface PatientSidebarProps {
    result: DetectionResult | null;
}

const PatientSidebar: React.FC<PatientSidebarProps> = ({ result }) => {
    return (
        <div className="fade-in">
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '32px' }}>
                <div style={{ width: 48, height: 48, borderRadius: '50%', background: 'rgba(59, 130, 246, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <User size={24} color="var(--accent-primary)" />
                </div>
                <div>
                    <h3 style={{ fontSize: '1rem' }}>{result ? result.patient_id : 'NO ACTIVE PATIENT'}</h3>
                    <p style={{ fontSize: '0.8rem', opacity: 0.6 }}>{result ? result.patient_name : 'PLEASE UPLOAD A SCAN'}</p>
                </div>
            </div>

            <div className="card">
                <h4 style={{ fontSize: '0.8rem', opacity: 0.6, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Activity size={14} /> CURRENT STUDY
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                        <span style={{ opacity: 0.6 }}>Modality</span>
                        <span>CR (X-RAY)</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                        <span style={{ opacity: 0.6 }}>View</span>
                        <span>AP / LATERAL</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                        <span style={{ opacity: 0.6 }}>Status</span>
                        <span style={{ color: 'var(--accent-secondary)' }}>AI ANALYZED</span>
                    </div>
                </div>
            </div>

            {result && (
                <div className="card" style={{ borderLeft: '4px solid var(--accent-primary)' }}>
                    <h4 style={{ fontSize: '0.8rem', opacity: 0.6, marginBottom: '12px' }}>AI PRELIMINARY REPORT</h4>
                    <p style={{ fontSize: '0.9rem', marginBottom: '16px', lineHeight: '1.4' }}>
                        {result.report.summary} Severity graded as <strong>{result.report.severity}</strong>.
                        Radiologist confirmation required for clinical sign-off.
                    </p>
                    <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
                        <Download size={16} /> EXPORT REPORT
                    </button>
                </div>
            )}

            <div style={{ marginTop: '32px' }}>
                <h4 style={{ fontSize: '0.8rem', opacity: 0.6, marginBottom: '16px' }}>PRIOR STUDIES</h4>
                {[1, 2].map(i => (
                    <div key={i} style={{ padding: '12px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem' }}>
                        <div>
                            <div style={{ fontWeight: 600 }}>Chest X-Ray</div>
                            <div style={{ opacity: 0.5 }}>Oct 12, 2025</div>
                        </div>
                        <CheckCircle size={14} color="var(--accent-secondary)" />
                    </div>
                ))}
            </div>
        </div>
    );
};

export default PatientSidebar;
