# imgaudpro.py
import struct
from .crypt import DecryptData, EncryptData

import numpy as np
import scipy.io as sio
from PIL import Image as ImG

# Constant Sample Rate
samp_rate = 96000  # in Hz
magic_head = b"MINI"  # Dev's Choice 4 Bytes
head_size = 32  # in Integer
head_ver = 1  # in Integer
head_chan = 3  # in Integer , Since RGB = 3 channels in an Img


# Encoding Func.
def encode_image(image_path, tres_key, audio_path):
    status_meta = {}

    # Load image
    img = ImG.open(image_path)
    img = img.convert("RGB")
    img_arr = np.array(img, dtype=np.uint8)
    hgt, wdt, chn = img_arr.shape
    status_meta["image_dims"] = f"{hgt}x{wdt}x{chn}"

    flt_arr = img_arr.flatten()
    flt_bytes = flt_arr.tobytes()
    exp_len = hgt * wdt * chn
    status_meta["flatten_ok"] = len(flt_bytes) == exp_len

    header = (
        magic_head  # 4 Bytes
        + bytes([head_ver])  # 1 Byte
        + struct.pack(">H", wdt)  # 2 Bytes
        + struct.pack(">H", hgt)  # 2 Bytes
        + bytes([head_chan])  # 1 Byte
        + struct.pack(">I", samp_rate)  # 4 Bytes
    )
    rem = head_size - len(header)
    header += b"\x00" * rem  # Padding to make header size 32 bytes
    status_meta["header_len"] = len(header)
    status_meta["header_start"] = header[:8].hex()

    payload = header + flt_bytes
    status_meta["payload_len"] = len(payload)
    status_meta["payload_ok"] = len(payload) == 32 + hgt * wdt * chn

    enc_payload = EncryptData(payload, tres_key)
    status_meta["encrypt_ok"] = len(enc_payload) == len(payload)

    if len(enc_payload) % 2 == 1:
        enc_payload += b"\x00"

    aud_samp = np.frombuffer(enc_payload, dtype=np.int16)
    status_meta["samples_count"] = len(aud_samp)
    status_meta["samples_dtype"] = str(aud_samp.dtype)
    status_meta["samples_range"] = f"[{aud_samp.min()}, {aud_samp.max()}]"

    duration = len(aud_samp) / samp_rate
    status_meta["duration_sec"] = duration

    # WAV write
    sio.wavfile.write(audio_path, samp_rate, aud_samp)
    status_meta["wav_saved"] = True

    # Core metadata
    status_meta["width"] = wdt
    status_meta["height"] = hgt

    return status_meta


# Decoding Func.
def decode_audio(audio_path, tres_key, image_path):
    status_meta = {}
    read_samp_rate, aud_samp = sio.wavfile.read(audio_path)
    if read_samp_rate != samp_rate:
        status_meta["samples_ok"] = False
    else:
        status_meta["samples_ok"] = True
    status_meta["samples_count"] = len(aud_samp)
    status_meta["samples_dtype"] = str(aud_samp.dtype)
    status_meta["samples_range"] = f"[{aud_samp.min()}, {aud_samp.max()}]"
    status_meta["duration_sec"] = len(aud_samp) / read_samp_rate
    payload = aud_samp.tobytes()
    if len(payload) % 2 == 0:
        status_meta["payload_ok"] = True
    else:
        status_meta["payload_ok"] = False
    status_meta["payload_len"] = len(payload)
    dec_payload = DecryptData(payload, tres_key)
    if len(dec_payload) == len(payload):
        status_meta["decryption_ok"] = True
    else:
        status_meta["decryption_ok"] = False
    header = dec_payload[:head_size]
    magic = header[:4]
    if magic == magic_head:
        status_meta["header_ok"] = True
    else:
        status_meta["header_ok"] = False
    wdt = struct.unpack(">H", header[5:7])[0]
    hgt = struct.unpack(">H", header[7:9])[0]
    chn = header[9]
    status_meta["width"] = wdt
    status_meta["height"] = hgt
    status_meta["channels"] = chn
    exp_img_len = wdt * chn * hgt
    flt_pxl = np.frombuffer(
        dec_payload[head_size : head_size + exp_img_len], dtype=np.uint8
    )
    if len(flt_pxl) == hgt * wdt * chn:
        status_meta["flatten_ok"] = True
    else:
        status_meta["flatten_ok"] = False
    img_3d_arr = flt_pxl.reshape(hgt, wdt, chn)
    expected_shape = (hgt, wdt, chn)
    status_meta["image_shape"] = str(img_3d_arr.shape)
    status_meta["image_shape_ok"] = img_3d_arr.shape == expected_shape
    img_out = ImG.fromarray(img_3d_arr, mode="RGB")
    img_out.save(image_path)
    status_meta["image_saved"] = True
    return status_meta
