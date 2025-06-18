import os
import base64
import subprocess
from flask import current_app, request, jsonify

def file_info(file_ext, extracted_filename, encoded_data):
    return current_app.config["file_info"](file_ext, extracted_filename, encoded_data)

def save_file(file):
    return current_app.config["save_file"](file)

def clear_uploads():
    return current_app.config["clear_uploads"]()

def extract_metadata():
    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify({"error": "No file provided. Please upload a file."})
    
    filepath = save_file(file)
    if not isinstance(filepath, str):
        return filepath
    try:
        command = ['exiftool', filepath]
        result = subprocess.run(
            command, capture_output=True, text=True, check=True, 
            encoding='utf-8', errors='ignore'
        )
        metadata_text = result.stdout
        
        encoded_data = base64.b64encode(metadata_text.encode('utf-8')).decode('ascii')
        return file_info("txt", "metadata_result.txt", encoded_data)

    except subprocess.CalledProcessError as e:
        clear_uploads()
        return jsonify({"error": f"Error from ExifTool: {e.stderr}"})
    except Exception as e:
        clear_uploads()
        return jsonify({"error": f"An unexpected server error occurred during extraction: {e}"})


def write_metadata():
    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify({"error": "No file provided. Please upload a file."})

    original_filename = file.filename
    _, file_extension = os.path.splitext(original_filename)

    filepath = save_file(file)
    if not isinstance(filepath, str):
        return filepath

    try:
        write_action = request.form.get('write_action')
        command_args = []
        
        actions = {
            'write-tag': lambda: f"-{request.form.get('tag_name')}={request.form.get('tag_value', '')}" if request.form.get('tag_name') else None,
            'delete-one-tag': lambda: f"-{request.form.get('tag_to_delete')}=" if request.form.get('tag_to_delete') else None,
            'delete-all-tags': lambda: '-all=',
            'copy-tag': lambda: f'-\"{request.form.get("dest_tag")}<{request.form.get("source_tag")}\"' if request.form.get("source_tag") and request.form.get("dest_tag") else None
        }
        
        if write_action not in actions:
            return jsonify({"error": "Invalid write action selected."})

        arg = actions[write_action]()
        if arg is None:
            return jsonify({"error": "Missing required parameters for the selected action."})
        command_args.append(arg)
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        base_name = os.path.basename(filepath)

        new_filename = f'result{file_extension}'
        output_file_path = os.path.join(upload_folder, new_filename)

        if filepath == output_file_path:
            command = ['exiftool'] + command_args + ['-overwrite_original', filepath]
        else:
            if os.path.exists(output_file_path):
                os.remove(output_file_path)
            command = ['exiftool'] + command_args + ['-overwrite_original', '-o', output_file_path, filepath]
            
        use_shell = any('<' in s for s in command_args)
        cmd_str = ' '.join(command) if use_shell else command

        result = subprocess.run(cmd_str, capture_output=True, text=True, shell=use_shell)

        if "Warning: Tag" in result.stderr and "is not defined" in result.stderr:
            warning_message = result.stderr.strip().replace("Warning: ", "")
            clear_uploads()
            return jsonify({"error": f"Invalid Tag: {warning_message}. Please use a standard tag name."})

        if result.returncode != 0:
            clear_uploads()
            return jsonify({"error": f"ExifTool failed with an error: {result.stderr}"})
        
        new_filepath = output_file_path
        with open(new_filepath, 'rb') as f:
            encoded_data = base64.b64encode(f.read()).decode('ascii')

        file_ext = os.path.splitext(new_filename)[1].lstrip('.')
        return file_info(file_ext, new_filename, encoded_data)

    except Exception as e:
        clear_uploads()
        return jsonify({"error": f"An unexpected server error occurred during write: {e}"})