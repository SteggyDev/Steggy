import os
import shutil
import subprocess
import base64
from werkzeug.utils import secure_filename
from flask import current_app, request, jsonify, send_from_directory
from flask import send_file

def file_info(file_ext, extracted_filename, encoded_data):
    return current_app.config["file_info"](file_ext, extracted_filename, encoded_data)

def clear_uploads():
    return current_app.config["clear_uploads"]()

def save_file(file):
    return current_app.config["save_file"](file)

def request_data():
    global file1
    file1 = request.files.get('file1')
    if not file1:
        return jsonify({"error": "No file selected."})
    file1_ext = file1.filename.rsplit('.', 1)[-1].lower()
    if file1_ext not in current_app.config["ALLOWED_FORMATS"]:
        return jsonify({"error": f"Unsupported file format '{file1_ext}'. Allowed formats: {', '.join(current_app.config['ALLOWED_FORMATS'])}."}); 

def stegoveritas_extract():
    request_data()
    UPLOAD_FOLDER = current_app.config["UPLOAD_FOLDER"]
    filename = secure_filename(file1.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    results_folder_path = os.path.join(UPLOAD_FOLDER, 'results')
    zip_path_base = os.path.join(UPLOAD_FOLDER, 'results')
    file1.save(file_path)
    
    try : 
        subprocess.run(['stegoveritas', filename], check=True, capture_output=True, text=True, cwd = UPLOAD_FOLDER)
        shutil.make_archive(base_name=zip_path_base, format='zip', root_dir=results_folder_path)

        try:
            zip_filename = "results.zip"
            extracted_filename = os.path.join(current_app.config["UPLOAD_FOLDER"], zip_filename)
            with open(extracted_filename, "rb") as f:
                encoded_data = base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            clear_uploads()
            return jsonify({"error": "Failed to get file data"})
        file_ext = file_path.rsplit('.', 1)[-1].lower()
        extracted_filename = extracted_filename.split("/")[-1]
        clear_uploads()
        return file_info(file_ext, extracted_filename, encoded_data)
        
    except subprocess.CalledProcessError as e:
        error_output = e.stderr if hasattr(e, 'stderr') else str(e)
        return jsonify({'error': f'Stegoveritas Failed: {error_output}'})

