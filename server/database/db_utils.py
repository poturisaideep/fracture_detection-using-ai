import sqlite3
import os

DB_PATH = 'storage/xray_detector.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def save_patient_and_scan(patient_id, name, scan_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Get or Create Patient
    cursor.execute('SELECT id FROM patients WHERE patient_id = ?', (patient_id,))
    row = cursor.fetchone()
    
    if row:
        patient_db_id = row['id']
    else:
        cursor.execute('INSERT INTO patients (patient_id, name) VALUES (?, ?)', (patient_id, name))
        patient_db_id = cursor.lastrowid
    
    # 2. Save Scan
    cursor.execute('''
        INSERT INTO scans (
            patient_db_id, scan_uuid, original_path, processed_path, heatmap_path,
            confidence_score, body_part, severity_grade, summary
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        patient_db_id, 
        scan_data['scan_id'],
        scan_data['original_url'],
        scan_data['processed_url'],
        scan_data['heatmap_url'],
        scan_data['detection']['confidence_score'],
        scan_data['detection']['body_part'],
        scan_data['detection']['severity_grade'],
        scan_data['report']['summary']
    ))
    
    conn.commit()
    conn.close()

def get_all_patients():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM patients ORDER BY created_at DESC')
    rows = cursor.fetchall()
    patients = [dict(row) for row in rows]
    conn.close()
    return patients

def get_patient_history(patient_db_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*, p.name as patient_name, p.patient_id as patient_str_id
        FROM scans s
        JOIN patients p ON s.patient_db_id = p.id
        WHERE s.patient_db_id = ? 
        ORDER BY s.timestamp DESC
    ''', (patient_db_id,))
    rows = cursor.fetchall()
    scans = [dict(row) for row in rows]
    conn.close()
    return scans
