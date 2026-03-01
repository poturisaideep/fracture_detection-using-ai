-- HIPAA-Compliant PostgreSQL Schema for X-Ray Fracture Detection System

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Define Roles for RBAC
CREATE TYPE user_role AS ENUM ('Radiologist', 'Admin', 'Technician');
CREATE TYPE fracture_severity AS ENUM ('Low', 'Moderate', 'Critical');

-- Users Table
-- Stores authorized personnel with role-based access
CREATE TABLE IF NOT EXISTS Users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role user_role NOT NULL,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Patients Table
-- HIPAA Compliance: PII fields are stored as encrypted text
CREATE TABLE IF NOT EXISTS Patients (
    patient_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    encrypted_name TEXT NOT NULL,          -- Encrypted Application-side
    encrypted_dob TEXT NOT NULL,           -- Encrypted Application-side
    encrypted_ssn TEXT,                  -- Encrypted Application-side
    gender VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Scans Table
-- Stores metadata for X-ray images and modality details
CREATE TABLE IF NOT EXISTS Scans (
    scan_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES Patients(patient_id) ON DELETE CASCADE,
    uploaded_by UUID REFERENCES Users(user_id),
    image_path TEXT NOT NULL,              -- Path to encrypted storage (S3/Local)
    modality VARCHAR(50) DEFAULT 'X-RAY',
    study_date TIMESTAMP WITH TIME ZONE NOT NULL,
    upload_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    dicom_metadata JSONB,                -- Store non-sensitive DICOM tags
    is_archived BOOLEAN DEFAULT FALSE
);

-- Detections Table
-- AI Prediction logs with audit trail
CREATE TABLE IF NOT EXISTS Detections (
    detection_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID REFERENCES Scans(scan_id) ON DELETE CASCADE,
    confidence_score FLOAT NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    bounding_box JSONB NOT NULL,           -- Format: {"x": 0, "y": 0, "w": 0, "h": 0}
    severity_grade fracture_severity NOT NULL,
    heatmap_path TEXT,                   -- Path to Grad-CAM heatmap overlay
    radiologist_id UUID REFERENCES Users(user_id), -- Assigned radiologist
    radiologist_override BOOLEAN DEFAULT FALSE,
    override_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    audit_trail JSONB DEFAULT '[]'::jsonb  -- Array of change logs: [{"user_id": UUID, "action": "string", "timestamp": "ISO8601"}]
);

-- Audit Logs Table (Global Trail)
CREATE TABLE IF NOT EXISTS GlobalAuditLogs (
    log_id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES Users(user_id),
    action TEXT NOT NULL,
    table_name VARCHAR(50),
    record_id UUID,
    old_values JSONB,
    new_values JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45)
);

-- Indexes for performance
CREATE INDEX idx_scans_patient ON Scans(patient_id);
CREATE INDEX idx_detections_scan ON Detections(scan_id);
CREATE INDEX idx_patients_created ON Patients(created_at);
