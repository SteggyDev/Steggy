from  flask import current_app, request, jsonify
from werkzeug.utils import secure_filename
import os
import base64
import subprocess
import zipfile

def file_info(file_ext, extracted_filename, encoded_data):
    return current_app.config["file_info"](file_ext, extracted_filename, encoded_data)

def clear_uploads():
    return current_app.config["clear_uploads"]()

def save_file(file):
    return current_app.config["save_file"](file)

def request_data():
    global file1_path, file2_path
    file1 = request.files.get('file1')
    if not file1:
        return jsonify({"error": "No file selected."})
    file1_ext = file1.filename.rsplit('.', 1)[-1].lower()
    
    if file1_ext not in current_app.config["ALLOWED_FORMATS"]:
        return jsonify({"error": f"Unsupported file format '{file1_ext}'. Allowed formats: {', '.join(current_app.config['ALLOWED_FORMATS'])}"})

    file1_path = save_file(file1)

def combine():
    request_data()
    if request.form.get("use_msg") == "on":
        message = request.form.get("message")
        if not message:
            return jsonify({"error": "No message input."})
        file2_path = os.path.join(current_app.config["UPLOAD_FOLDER"], "message.txt")
        with open(file2_path, "w") as msg_file:
            msg_file.write(message)
    else:
        file2 = request.files.get('file2')
        if not file2:
            return jsonify({"error": "No file2 selected."})
        file2_path = save_file(file2)
        
    # File combine
    with open(file1_path, 'ab') as file1:
        if request.form.get("extract_zip") == "on" and file2_path.endswith('.zip'):
            try:
                with zipfile.ZipFile(file2_path, 'r') as zip_ref:
                    for file in zip_ref.namelist():
                        file1.write(b'\n')
                        file1.write(zip_ref.read(file))
            except Exception as e:
                clear_uploads()
                return jsonify({"error": "Failed to extract zip file."})
        else:
            with open(file2_path, 'rb') as file2:
                file2_content = file2.read()
                file1.write(b'\n' + file2_content)

    with open(file1_path, 'rb') as file1:
        file1_content = file1.read()
    
    extracted_filename = file1_path.split("/")[-1]
    file_ext = file1_path.rsplit('.', 1)[-1].lower()
    clear_uploads()
    return file_info(file_ext, extracted_filename, base64.b64encode(file1_content).decode('utf-8'))

def foremost_data():
    request_data()
    try:
        os.chdir(current_app.config["UPLOAD_FOLDER"])
        command = ["foremost", file1_path.split("/")[-1]]
        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)        
        output_folder = "output"
        zip_filename = "output.zip"
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(output_folder):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), output_folder))
    except Exception as e:
        os.chdir("..")
        clear_uploads()
        return jsonify({"error": "Failed to run Foremost"})
    os.chdir("..")
    if process.returncode != 0:
        return jsonify({"error": "Failed to run Foremost"})
    try:
        extracted_filename = os.path.join(current_app.config["UPLOAD_FOLDER"], zip_filename)
        with open(extracted_filename, "rb") as f:
            encoded_data = base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        clear_uploads()
        return jsonify({"error": "Failed to get file data"})
    file_ext = extracted_filename.rsplit('.', 1)[-1].lower()
    extracted_filename = extracted_filename.split("/")[-1]
    return file_info(file_ext, extracted_filename, encoded_data)
