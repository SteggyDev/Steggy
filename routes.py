from steghide import hide_data, extract_data
from foremost import combine, foremost_data
from pdffitz import embedpdf, extractpdf
from stegoveritas import stegoveritas_extract
from exiftool import extract_metadata, write_metadata
from audiospec import create_audio_with_spectrogram, display_audio_spectrogram
from flask import Blueprint, render_template, request, send_from_directory, redirect, url_for, jsonify
import os
import shutil
import base64
import tempfile

bp = Blueprint('main', __name__)

STATIC_AUDIO_DIR = "upload/"
os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)

@bp.route('/')
def dashboard():
    return render_template('index.html')

@bp.route("/decode", methods=["POST"])
def decode_audio_to_image():
    if "file" not in request.files:
        return jsonify({"error": "Missing file"}), 400

    file = request.files["file"]
    temp_path = os.path.join(tempfile.gettempdir(), file.filename)
    file.save(temp_path)

    image_path = display_audio_spectrogram(temp_path)

    return jsonify({
        "image": "/" + image_path
    })

@bp.route('/upload', methods=['POST'])
def upload_file():
    print("Upload file")
    action = request.form.get("action")
    if action == "Embed":
        return hide_data()
    elif action == "Extract":
        return extract_data()
    elif action == "Combine":
        return combine()
    elif action == "Foremost":
        return foremost_data()
    elif action == "EmbedPDF":
        return embedpdf()
    elif action == "PDFExtract":
        return extractpdf()
    elif action == "StegoVeritas":
        return stegoveritas_extract()
    elif action == "Extract Metadata":
        return extract_metadata()
    elif action == "Write Metadata":
        return write_metadata()
    elif action == "AudioSpectrogramWrite":
        return handle_audio_spectrogram_write()
    elif action == "AudioSpectrogramRead":
        return handle_audio_spectrogram_read()
    else:
        return "Error: Invalid action"
    
def handle_audio_spectrogram_write():
    try:
        text = request.form["text"]
        base_width = int(request.form.get("base_width", 512))
        height = int(request.form.get("height", 256))
        max_font_size = int(request.form.get("max_font_size", 80))
        margin = int(request.form.get("margin", 10))
        letter_spacing = int(request.form.get("letter_spacing", 5))

        audio_path, image_path = create_audio_with_spectrogram(
            text, base_width, height, max_font_size, margin, letter_spacing
        )

        # Save and encode for frontend
        new_audio_path = os.path.join(STATIC_AUDIO_DIR, "generated_audio.wav")
        new_img_path = os.path.join(STATIC_AUDIO_DIR, "generated_spectrogram.png")
        os.replace(audio_path, new_audio_path)
        os.replace(image_path, new_img_path)

        with open(new_audio_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode("utf-8")
        with open(new_img_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")

        return jsonify({
            "audio": f"data:audio/wav;base64,{audio_b64}",
            "image": f"data:image/png;base64,{img_b64}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def handle_audio_spectrogram_read():
    try:
        audio_file = request.files.get("file")
        if not audio_file:
            return jsonify({"error": "No audio file uploaded"}), 400

        filename = audio_file.filename
        filepath = os.path.join(STATIC_AUDIO_DIR, filename)
        audio_file.save(filepath)

        spectrogram_path = display_audio_spectrogram(filepath)
        new_img_path = os.path.join(STATIC_AUDIO_DIR, "decoded_spectrogram.png")
        os.replace(spectrogram_path, new_img_path)

        with open(new_img_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")

        return jsonify({
            "image": f"data:image/png;base64,{img_b64}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500