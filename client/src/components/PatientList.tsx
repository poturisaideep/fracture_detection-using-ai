import React, { useState, useEffect } from 'react';
import { Users, ChevronRight, Calendar, Activity, ArrowLeft, Search, Clock } from 'lucide-react';
import { getPatients, getPatientHistory, Patient, ScanRecord } from '../services/api';

interface PatientListProps {
    onBack: () => void;
    onViewScan: (scan: any) => void;
}

const PatientList: React.FC<PatientListProps> = ({ onBack, onViewScan }) => {
    const [patients, setPatients] = useState<Patient[]>([]);
    const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
    const [history, setHistory] = useState<ScanRecord[]>([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchPatients();
    }, []);

    const fetchPatients = async () => {
        setLoading(true);
        try {
            const data = await getPatients();
            setPatients(data);
        } catch (err) {
            console.error("Failed to fetch patients", err);
        } finally {
            setLoading(false);
        }
    };

    const handlePatientClick = async (patient: Patient) => {
        setSelectedPatient(patient);
        setLoading(true);
        try {
            const data = await getPatientHistory(patient.id);
            setHistory(data);
        } catch (err) {
            console.error("Failed to fetch history", err);
        } finally {
            setLoading(false);
        }
    };

    const filteredPatients = patients.filter(p =>
        p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.patient_id.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (selectedPatient) {
        return (
            <div className="patient-history-container" style={{ padding: '24px', flex: 1, overflowY: 'auto' }}>
                <button onClick={() => setSelectedPatient(null)} className="btn" style={{ marginBottom: '24px' }}>
                    <ArrowLeft size={16} /> BACK TO PATIENTS
                </button>

                <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '40px' }}>
                    <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(59, 130, 246, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent-primary)' }}>
                        <Users size={32} />
                    </div>
                    <div>
                        <h1 style={{ margin: 0, fontSize: '1.5rem' }}>{selectedPatient.name}</h1>
                        <p style={{ margin: 0, color: 'var(--text-muted)' }}>Patient ID: {selectedPatient.patient_id}</p>
                    </div>
                </div>

                <h3 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', letterSpacing: '0.1em', marginBottom: '16px' }}>SCAN HISTORY</h3>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {history.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '40px', background: 'var(--panel-bg)', borderRadius: '12px', opacity: 0.5 }}>
                            No scans found for this patient.
                        </div>
                    ) : (
                        history.map((scan) => (
                            <div
                                key={scan.id}
                                className="history-card"
                                onClick={() => onViewScan(scan)}
                                style={{
                                    background: 'var(--panel-bg)',
                                    border: '1px solid var(--border-color)',
                                    borderRadius: '12px',
                                    padding: '16px',
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    cursor: 'pointer',
                                    transition: 'transform 0.2s'
                                }}
                            >
                                <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
                                    <div style={{ width: '80px', height: '80px', borderRadius: '8px', overflow: 'hidden', background: '#000' }}>
                                        <img src={`http://127.0.0.1:5001${scan.processed_path}`} alt="X-Ray" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                                    </div>
                                    <div>
                                        <div style={{ display: 'flex', gap: '8px', marginBottom: '4px' }}>
                                            <span style={{ fontSize: '0.7rem', color: 'var(--accent-primary)', background: 'rgba(59, 130, 246, 0.1)', padding: '2px 8px', borderRadius: '4px' }}>
                                                {scan.body_part.toUpperCase()}
                                            </span>
                                            <span style={{ fontSize: '0.7rem', color: scan.severity_grade === 'Normal' ? '#10b981' : '#ef4444', background: scan.severity_grade === 'Normal' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', padding: '2px 8px', borderRadius: '4px' }}>
                                                {scan.severity_grade.toUpperCase()}
                                            </span>
                                        </div>
                                        <div style={{ fontSize: '0.9rem', marginBottom: '4px' }}>{scan.summary}</div>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                            <Clock size={12} /> {new Date(scan.timestamp).toLocaleString()}
                                        </div>
                                    </div>
                                </div>
                                <ChevronRight size={20} style={{ opacity: 0.3 }} />
                            </div>
                        ))
                    )}
                </div>
            </div>
        );
    }

    return (
        <div style={{ padding: '24px', flex: 1, overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
                <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Patient Directory</h1>
                <div style={{ position: 'relative', width: '300px' }}>
                    <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', opacity: 0.5 }} />
                    <input
                        type="text"
                        placeholder="Search by name or ID..."
                        className="input-field"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        style={{ paddingLeft: '36px' }}
                    />
                </div>
            </div>

            {loading && patients.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px' }}>Loading patients...</div>
            ) : (
                <div className="patient-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
                    {filteredPatients.map((patient) => (
                        <div
                            key={patient.id}
                            onClick={() => handlePatientClick(patient)}
                            style={{
                                background: 'var(--panel-bg)',
                                border: '1px solid var(--border-color)',
                                borderRadius: '12px',
                                padding: '20px',
                                cursor: 'pointer',
                                transition: 'all 0.2s',
                            }}
                            className="patient-card"
                        >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                                <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(59, 130, 246, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent-primary)' }}>
                                    <Users size={24} />
                                </div>
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                    <Calendar size={12} /> {new Date(patient.created_at).toLocaleDateString()}
                                </div>
                            </div>
                            <h3 style={{ margin: '0 0 4px 0', fontSize: '1.1rem' }}>{patient.name}</h3>
                            <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.85rem' }}>ID: {patient.patient_id}</p>
                        </div>
                    ))}
                </div>
            )}

            {filteredPatients.length === 0 && !loading && (
                <div style={{ textAlign: 'center', padding: '60px', opacity: 0.5 }}>
                    <Users size={48} style={{ marginBottom: '16px', strokeWidth: 1 }} />
                    <p>No patients found matching your search.</p>
                </div>
            )}
        </div>
    );
};

export default PatientList;
