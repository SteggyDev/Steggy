from flask import Flask, jsonify
from routes import bp  # Import the Blueprint
from werkzeug.utils import secure_filename
import os
import base64
import mimetypes
import shutil

app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = 'uploads'
app.config["ALLOWED_FORMATS"] = {"jpg", "jpeg", "bmp", "wav", "au", "gif"}
UPLOAD_FOLDER = app.config["UPLOAD_FOLDER"]

def allowed_file_size(file):
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB limit
    file.seek(0, os.SEEK_END)  # Move the cursor to the end of the file
    file_size = file.tell()  # Get the current position of the cursor, which is the size of the file
    file.seek(0, os.SEEK_SET)  # Reset the cursor to the beginning of the file
    return file_size <= MAX_FILE_SIZE

def save_file(file):
    if file and file.filename:
        if not allowed_file_size(file):
            return jsonify("File size exceeds the allowed limit.")
        path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        try:
            file.save(path)
            return path
        except Exception as e:
            return jsonify(f"Error saving file {file.filename}")
    return None

def clear_uploads():
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # Removes directories and their contents
        except Exception as e:
            print(f"Error removing {file_path}: {e}")

def file_info(file_ext, extracted_filename, encoded_data):
    mime_type, _ = mimetypes.guess_type(extracted_filename)
    response_data = {
        "filename": extracted_filename,
        "file_ext": file_ext,
        "mime_type": mime_type or "application/octet-stream",
        "encoded_data": encoded_data  # Base64 encoded data
    }
    if mime_type:
        if mime_type.startswith("image/"):
            response_data["display"] = f"data:{mime_type};base64,{encoded_data}"
            response_data["preview_type"] = "image"
        elif mime_type == "text/plain":
            response_data["display"] = base64.b64decode(encoded_data).decode('utf-8')
            response_data["preview_type"] = "text"
        elif mime_type.startswith("audio/"):
            response_data["display"] = f"data:{mime_type};base64,{encoded_data}"
            response_data["preview_type"] = "audio"
        else:
            response_data["preview_type"] = "download"
    else:
        response_data["preview_type"] = "download"
    clear_uploads()
    return jsonify(response_data)


os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["clear_uploads"] = clear_uploads  # Add function to app config
app.config["save_file"] = save_file  # Add function to app config
app.config["file_info"] = file_info  # Add function to app config

app.register_blueprint(bp)  # Register Blueprint


if __name__ == '__main__':
    app.run(debug=True)
    clear_uploads()