import os
import shutil
import struct
import tempfile
import uuid

from flask import Flask, jsonify, render_template, request, send_file

app = Flask(__name__)

UPLOAD_FOLDER = tempfile.mkdtemp()
OUTPUT_FOLDER = os.path.join(tempfile.gettempdir(), "audiocrypt_out")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

MAGIC_HEAD = b"MINI"

# ---- Import your modules ----
import sys

sys.path.insert(0, os.path.dirname(__file__))
from conv.imgaudpro import decode_audio, encode_image


def check_magic_header(audio_path, key):
    """Read WAV, decrypt header, check for MINI magic bytes."""
    try:
        from conv.crypt import DecryptData

        import numpy as np
        import scipy.io as sio

        _, aud_samp = sio.wavfile.read(audio_path)
        payload = aud_samp.tobytes()
        dec_payload = DecryptData(payload, key)
        magic = dec_payload[:4]
        return magic == MAGIC_HEAD, magic
    except Exception as e:
        return False, b""


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/encode", methods=["POST"])
def encode():
    key = request.form.get("key", "")
    output_path = request.form.get("output", "").strip()
    is_batch = request.form.get("batch", "false") == "true"

    if len(key) != 3 or not key.isdigit():
        return jsonify(
            {
                "success": False,
                "message": "Invalid key. Must be exactly 3 digits.",
                "logs": [],
            }
        )

    key_list = list(key)
    files = request.files.getlist("files")

    if not files or files[0].filename == "":
        return jsonify({"success": False, "message": "No files uploaded.", "logs": []})

    # Determine output directory
    if output_path and os.path.isdir(output_path):
        out_dir = output_path
    else:
        out_dir = OUTPUT_FOLDER

    logs = []
    download_links = []
    errors = []

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in [".png", ".jpg", ".jpeg"]:
            logs.append(f"⚠ Skipped (not an image): {file.filename}")
            continue

        # Save uploaded file to temp
        tmp_in = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}{ext}")
        file.save(tmp_in)

        name = os.path.splitext(file.filename)[0]
        out_audio = os.path.join(out_dir, name + ".wav")

        try:
            logs.append(f"▶ Encoding: {file.filename}")
            meta = encode_image(tmp_in, key_list, out_audio)

            logs.append(f"  ✔ Image dims    : {meta.get('image_dims', 'N/A')}")
            logs.append(f"  ✔ Payload size  : {meta.get('payload_len', 'N/A')} bytes")
            logs.append(f"  ✔ Audio samples : {meta.get('samples_count', 'N/A')}")
            logs.append(f"  ✔ Duration      : {meta.get('duration_sec', 0):.3f} sec")
            logs.append(f"  ✔ Saved to      : {out_audio}")

            # Generate a download token
            token = str(uuid.uuid4())
            token_path = os.path.join(OUTPUT_FOLDER, token + ".wav")
            shutil.copy2(out_audio, token_path)
            download_links.append({"filename": name + ".wav", "token": token})

        except Exception as e:
            errors.append(str(e))
            logs.append(f"  ✘ Error: {e}")
        finally:
            if os.path.exists(tmp_in):
                os.remove(tmp_in)

    if errors and not download_links:
        return jsonify(
            {
                "success": False,
                "message": "Encoding failed.",
                "logs": logs,
                "downloads": [],
            }
        )

    msg = f"Encoded {len(download_links)} file(s) successfully."
    if errors:
        msg += f" {len(errors)} failed."

    return jsonify(
        {"success": True, "message": msg, "logs": logs, "downloads": download_links}
    )


@app.route("/decode", methods=["POST"])
def decode():
    key = request.form.get("key", "")
    output_path = request.form.get("output", "").strip()

    if len(key) != 3 or not key.isdigit():
        return jsonify(
            {
                "success": False,
                "message": "Invalid key. Must be exactly 3 digits.",
                "logs": [],
            }
        )

    key_list = list(key)
    files = request.files.getlist("files")

    if not files or files[0].filename == "":
        return jsonify({"success": False, "message": "No files uploaded.", "logs": []})

    if output_path and os.path.isdir(output_path):
        out_dir = output_path
    else:
        out_dir = OUTPUT_FOLDER

    logs = []
    download_links = []
    errors = []

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext != ".wav":
            logs.append(f"⚠ Skipped (not a .wav): {file.filename}")
            continue

        tmp_in = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.wav")
        file.save(tmp_in)

        logs.append(f"▶ Checking magic header: {file.filename}")

        valid, found_magic = check_magic_header(tmp_in, key_list)

        if not valid:
            found_str = found_magic.hex() if found_magic else "unknown"
            logs.append(f"  ✘ Magic header mismatch!")
            logs.append(f"  ✘ Expected : MINI (4d494e49)")
            logs.append(f"  ✘ Found    : {found_str}")
            logs.append(f"  ✘ No encrypted image found in: {file.filename}")
            errors.append(f"No encrypted image found in {file.filename}")
            os.remove(tmp_in)
            continue

        logs.append(f"  ✔ Magic header OK (MINI)")

        name = os.path.splitext(file.filename)[0]
        out_img = os.path.join(out_dir, name + ".png")

        try:
            meta = decode_audio(tmp_in, key_list, out_img)

            logs.append(
                f"  ✔ Image dims    : {meta.get('width')}x{meta.get('height')}x{meta.get('channels')}"
            )
            logs.append(f"  ✔ Audio samples : {meta.get('samples_count', 'N/A')}")
            logs.append(f"  ✔ Duration      : {meta.get('duration_sec', 0):.3f} sec")
            logs.append(f"  ✔ Decryption OK : {meta.get('decryption_ok', False)}")
            logs.append(f"  ✔ Image shape   : {meta.get('image_shape', 'N/A')}")
            logs.append(f"  ✔ Saved to      : {out_img}")

            token = str(uuid.uuid4())
            token_path = os.path.join(OUTPUT_FOLDER, token + ".png")
            shutil.copy2(out_img, token_path)
            download_links.append({"filename": name + ".png", "token": token})

        except Exception as e:
            errors.append(str(e))
            logs.append(f"  ✘ Error: {e}")
        finally:
            if os.path.exists(tmp_in):
                os.remove(tmp_in)

    if not download_links and errors:
        return jsonify(
            {
                "success": False,
                "message": " | ".join(errors),
                "logs": logs,
                "downloads": [],
            }
        )

    msg = f"Decoded {len(download_links)} file(s) successfully."
    if errors:
        msg += f" {len(errors)} failed (no encrypted image found)."

    return jsonify(
        {
            "success": True if download_links else False,
            "message": msg,
            "logs": logs,
            "downloads": download_links,
        }
    )


@app.route("/download/<token>/<filename>")
def download(token, filename):
    # Validate token is uuid-like (no path traversal)
    try:
        uuid.UUID(token)
    except ValueError:
        return "Invalid token", 400

    ext = os.path.splitext(filename)[1].lower()
    token_file = os.path.join(OUTPUT_FOLDER, token + ext)
    if not os.path.exists(token_file):
        return "File not found", 404

    return send_file(token_file, as_attachment=True, download_name=filename)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
