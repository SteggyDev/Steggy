from  flask import current_app, request, jsonify
from werkzeug.utils import secure_filename
import os
import base64
import subprocess
import zipfile
import pymupdf

def file_info(file_ext, extracted_filename, encoded_data):
    return current_app.config["file_info"](file_ext, extracted_filename, encoded_data)

def clear_uploads():
    return current_app.config["clear_uploads"]()

def save_file(file):
    return current_app.config["save_file"](file)

def request_data():
    global file1_path, file2_path, key
    file1 = request.files.get('file1')
    if not file1:
        return jsonify({"error": "No file selected"})
    file1_ext = file1.filename.rsplit('.', 1)[-1].lower()    
    key = request.form.get("key") if request.form.get("use_key") == "on" else ""
    file1_path = save_file(file1)

def embedpdf():
    request_data()
    if request.form.get("use_msg") == "on":
        message = request.form.get("message")
        if not message:
            return jsonify({"error": "No message input"})
        file2_path = os.path.join(current_app.config["UPLOAD_FOLDER"], "message.txt")
        with open(file2_path, "w") as msg_file:
            msg_file.write(message)
    else:
        file2 = request.files.get('file2')
        if not file2:
            return jsonify({"error": "No file 2 selected"})
        file2_path = save_file(file2)

    doc = pymupdf.open(file1_path)
    with open(file2_path, "rb") as f:
        file_data = f.read()
    doc.embfile_add(file2_path, file_data)

    # Encrypt the PDF with a password
    pdf_output = os.path.join(current_app.config["UPLOAD_FOLDER"], "output.pdf")
    if request.form.get("use_key") == "on":
        doc.save(pdf_output, encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw=key, user_pw=key)
    else:
        doc.save(pdf_output)
    doc.close()        

    with open(pdf_output, "rb") as f:
        file_data = f.read()
    extracted_filename = pdf_output.split("/")[-1]
    file_ext = pdf_output.rsplit('.', 1)[-1].lower()
    clear_uploads()
    return file_info(file_ext, extracted_filename, base64.b64encode(file_data).decode('utf-8'))

def extractpdf():
    request_data()
    unlocked_pdf = "unlocked.pdf"
    doc = pymupdf.open(file1_path)
    if request.form.get("use_key") == "on":
        if not doc.authenticate(owner_pw=key):
            doc.close()
            clear_uploads()
            return jsonify({"error": "Incorrect password"})
    doc.save(os.path.join(current_app.config["UPLOAD_FOLDER"], unlocked_pdf))
    doc.close()
    try:
        os.chdir(current_app.config["UPLOAD_FOLDER"])
        command = ["pdfextract", unlocked_pdf]
        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)        
        # Zip the output folder
        output_folder = unlocked_pdf.split(".")[0] + ".dump"
        zip_filename = "output.zip"
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(output_folder):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), output_folder))
    except:
        os.chdir("..")
        clear_uploads()
        return jsonify({"error": "Failed to run pdfextract"})
    os.chdir("..")
    try:
        extracted_filename = os.path.join(current_app.config["UPLOAD_FOLDER"], zip_filename)
        with open(extracted_filename, "rb") as f:
            encoded_data = base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        clear_uploads()
        return jsonify({"error": "Failed to get file data"})
    file_ext = file1_path.rsplit('.', 1)[-1].lower()
    extracted_filename = extracted_filename.split("/")[-1]
    clear_uploads()
    return file_info(file_ext, extracted_filename, encoded_data)
