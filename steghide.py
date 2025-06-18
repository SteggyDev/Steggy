import os
import base64
import subprocess
from  flask import current_app, request, jsonify

def file_info(file_ext, extracted_filename, encoded_data):
    return current_app.config["file_info"](file_ext, extracted_filename, encoded_data)

def clear_uploads():
    return current_app.config["clear_uploads"]()

def save_file(file):
    return current_app.config["save_file"](file)

def request_data():
    global file1_path, key
    file1 = request.files.get('file1')
    if not file1:
        return jsonify({"error": "No file selected."})
    file1_ext = file1.filename.rsplit('.', 1)[-1].lower()
    
    if file1_ext not in current_app.config["ALLOWED_FORMATS"]:
        return jsonify({"error": "Unsupported file format '{file1_ext}'. Allowed formats: {', '.join(current_app.config['ALLOWED_FORMATS'])}."}); 
    key = request.form.get("key") if request.form.get("use_key") == "on" else ""
    file1_path = save_file(file1)
    print(file1_path)

def hide_data():
    request_data()
    print(request.form.get("use_msg"))
    if request.form.get("use_msg") == "on":
        message = request.form.get("message")
        if not message:
            return jsonify({"error": "Error: No message input"})
        file2_path = os.path.join(current_app.config["UPLOAD_FOLDER"], "message.txt")
        with open(file2_path, "w") as msg_file:
            msg_file.write(message)
    else:
        file2 = request.files.get('file2')
        if not file2:
            return jsonify({"error": "No file selected."})
        file2_path = save_file(file2) 
    if file1_path and file2_path:
        command = ["steghide", "embed", "-ef", file2_path, "-cf", file1_path, "-p", key]
        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
        if process.returncode != 0:
            clear_uploads()
            return jsonify({"error": "Failed to do embed file with steghide"})

    with open(file1_path, "rb") as f:
        encoded_data = base64.b64encode(f.read()).decode('utf-8')

    clear_uploads()
    file_ext = file1_path.rsplit('.', 1)[-1].lower()
    extracted_filename = file1_path.split("/")[-1]
    return file_info(file_ext, extracted_filename, encoded_data)

def extract_data():
    request_data()
    try:
        os.chdir(current_app.config["UPLOAD_FOLDER"])
        command = ["steghide", "extract", "-sf", os.path.basename(file1_path), "-p", key]
        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
        print(process)
    except Exception as e:
        os.chdir("..")
        clear_uploads()
        return jsonify({"error": "Failed to extract file with steghide"})
    os.chdir("..")
    if process.returncode != 0:
        clear_uploads()
        return jsonify({"error": "Failed to extract file with steghide"})
    if "wrote extracted data to" in process.stderr:
        output_path = process.stderr.split("\"")[1]
    else:
        clear_uploads()
        return jsonify({"error": "Error: No file extracted"})

    try:
        extracted_filename = os.path.join(current_app.config["UPLOAD_FOLDER"], output_path)
        with open(extracted_filename, "rb") as f:
            encoded_data = base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        clear_uploads()
        return jsonify({"error": "Failed to get file original data"})
    file_ext = extracted_filename.rsplit('.', 1)[-1].lower()
    extracted_filename = extracted_filename.split("/")[-1]
    return file_info(file_ext, extracted_filename, encoded_data)
