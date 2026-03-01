import React, { useState } from 'react';
import { User, Hash, X } from 'lucide-react';

interface PatientEntryModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (patientId: string, patientName: string) => void;
}

const PatientEntryModal: React.FC<PatientEntryModalProps> = ({ isOpen, onClose, onSubmit }) => {
    const [id, setId] = useState('');
    const [name, setName] = useState('');

    if (!isOpen) return null;

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (id.trim() && name.trim()) {
            onSubmit(id, name);
            setId('');
            setName('');
        }
    };

    return (
        <div className="modal-overlay">
            <div className="modal-content" style={{ maxWidth: '400px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                    <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Patient Information</h2>
                    <button onClick={onClose} className="btn-icon">
                        <X size={20} />
                    </button>
                </div>

                <form onSubmit={handleSubmit}>
                    <div style={{ marginBottom: '20px' }}>
                        <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                            PATIENT ID
                        </label>
                        <div style={{ position: 'relative' }}>
                            <Hash size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', opacity: 0.5 }} />
                            <input
                                type="text"
                                value={id}
                                onChange={(e) => setId(e.target.value)}
                                className="input-field"
                                placeholder="E.g. P10293"
                                required
                                autoFocus
                                style={{ paddingLeft: '36px' }}
                            />
                        </div>
                    </div>

                    <div style={{ marginBottom: '32px' }}>
                        <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                            PATIENT FULL NAME
                        </label>
                        <div style={{ position: 'relative' }}>
                            <User size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', opacity: 0.5 }} />
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                className="input-field"
                                placeholder="E.g. John Doe"
                                required
                                style={{ paddingLeft: '36px' }}
                            />
                        </div>
                    </div>

                    <button type="submit" className="btn btn-primary" style={{ width: '100%', height: '48px' }}>
                        CONFIRM & PROCEED TO UPLOAD
                    </button>
                </form>
            </div>
        </div>
    );
};

export default PatientEntryModal;
