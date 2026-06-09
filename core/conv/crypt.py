# crypt.py
import hashlib as hab


def KeyGen(tres_dig):  # Key generation from 3-digit combo
    combo = "".join(tres_dig)
    key = combo.encode("utf-8")
    for k in range(100):  # Key streatching, 100 iterations
        key = hab.sha256(key).digest()
    return key


def EncryptData(Bit_8_data, tres_dig):
    cih_key = KeyGen(tres_dig)
    ken_len = len(cih_key)
    enc_data = bytearray()
    for i, byte in enumerate(Bit_8_data):
        enc_data.append(byte ^ cih_key[i % ken_len])
    return bytes(enc_data)


def DecryptData(Bit_8_data, tres_dig):
    cih_key = KeyGen(tres_dig)
    ken_len = len(cih_key)
    dec_data = bytearray()
    for i, byte in enumerate(Bit_8_data):
        dec_data.append(byte ^ cih_key[i % ken_len])
    return bytes(dec_data)
