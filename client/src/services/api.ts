import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:5001/api';

export interface DetectionResult {
    scan_id: string;
    original_url: string;
    processed_url: string;
    heatmap_url: string;
    patient_id?: string;
    patient_name?: string;
    detection: {
        confidence_score: number;
        body_part: string;
        bounding_box: {
            x: number;
            y: number;
            width: number;
            height: number;
        };
        severity_grade: 'Low' | 'Moderate' | 'Critical';
    };
    report: {
        summary: string;
        severity: string;
        timestamp: string;
    };
}

export interface Patient {
    id: number;
    patient_id: string;
    name: string;
    created_at: string;
}

export interface ScanRecord {
    id: number;
    scan_uuid: string;
    original_path: string;
    processed_path: string;
    heatmap_path: string;
    confidence_score: number;
    body_part: string;
    severity_grade: string;
    summary: string;
    timestamp: string;
    patient_name: string;
    patient_str_id: string;
}

export const uploadXRay = async (file: File, patientId: string, patientName: string): Promise<DetectionResult> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('patientId', patientId);
    formData.append('patientName', patientName);

    const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });

    return response.data;
};

export const getPatients = async (): Promise<Patient[]> => {
    const response = await axios.get(`${API_BASE_URL}/patients`);
    return response.data;
};

export const getPatientHistory = async (dbId: number): Promise<ScanRecord[]> => {
    const response = await axios.get(`${API_BASE_URL}/patients/${dbId}/history`);
    return response.data;
};

export const getSystemStatus = async () => {
    const response = await axios.get(`${API_BASE_URL}/status`);
    return response.data;
};
