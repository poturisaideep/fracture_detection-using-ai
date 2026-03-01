import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from services.preprocessing import PreprocessingPipeline
from services.ai_engine import AIEngine
from database.db_utils import save_patient_and_scan, get_all_patients, get_patient_history

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'storage/uploads'
PROCESSED_FOLDER = 'storage/processed'
HEATMAP_FOLDER = 'storage/heatmaps'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(HEATMAP_FOLDER, exist_ok=True)

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({"status": "online", "system": "X-Ray Fracture Detector"}), 200

@app.route('/api/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # 1. Save Original
    file_uuid = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    original_filename = f"{file_uuid}_original{ext}"
    original_path = os.path.join(UPLOAD_FOLDER, original_filename)
    file.save(original_path)

    try:
        # 2. Preprocessing
        processed_filename = f"{file_uuid}_processed.jpg"
        processed_path = os.path.join(PROCESSED_FOLDER, processed_filename)
        PreprocessingPipeline.process_image(original_path, processed_path)

        # 3. AI Inference (Mock)
        detection_result = AIEngine.run_inference(processed_path)

        # 4. Explainable AI (Grad-CAM Mock)
        heatmap_filename = f"{file_uuid}_heatmap.jpg"
        heatmap_path = os.path.join(HEATMAP_FOLDER, heatmap_filename)
        AIEngine.generate_heatmap(processed_path, heatmap_path)

        # 5. Build Response
        response = {
            "scan_id": file_uuid,
            "original_url": f"/storage/uploads/{original_filename}",
            "processed_url": f"/storage/processed/{processed_filename}",
            "heatmap_url": f"/storage/heatmaps/{heatmap_filename}",
            "detection": detection_result,
            "report": {
                "summary": f"Fracture detected with {detection_result['confidence_score']*100}% confidence.",
                "severity": detection_result['severity_grade'],
                "timestamp": "2026-02-26T00:25:00Z" # Mock timestamp
            }
        }

        # 6. Save to Database
        patient_id = request.form.get('patientId', 'ANONYMOUS')
        patient_name = request.form.get('patientName', 'Unknown Patient')
        save_patient_and_scan(patient_id, patient_name, response)
        
        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to serve storage files
@app.route('/storage/<path:filename>')
def serve_storage(filename):
    return send_from_directory('storage', filename)

@app.route('/api/patients', methods=['GET'])
def list_patients():
    patients = get_all_patients()
    return jsonify(patients), 200

@app.route('/api/patients/<int:db_id>/history', methods=['GET'])
def patient_history(db_id):
    history = get_patient_history(db_id)
    return jsonify(history), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
