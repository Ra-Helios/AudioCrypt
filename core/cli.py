from imgaudpro import encode_image, decode_audio
import os

# ---------------- KEY ----------------
def get_key():
    key = input("Enter 3 digit key: ").strip()
    if len(key) != 3 or not key.isdigit():
        print("Invalid key (must be 3 digits)")
        return None
    return list(key)


# ---------------- SINGLE ENCRYPT ----------------
def encrypt_single():
    img = input("Enter image path: ").strip()
    if not os.path.exists(img):
        print("File not found")
        return

    out = input("Enter output audio path (.wav): ").strip()
    key = get_key()
    if key:
        print("Encoding...")
        encode_image(img, key, out)
        print("Done\n")


# ---------------- SINGLE DECRYPT ----------------
def decrypt_single():
    aud = input("Enter audio path: ").strip()
    if not os.path.exists(aud):
        print("File not found")
        return

    out = input("Enter output image path (.png): ").strip()
    key = get_key()
    if key:
        print("Decoding...")
        decode_audio(aud, key, out)
        print("Done\n")


# ---------------- BATCH ENCRYPT ----------------
def encrypt_batch():

    in_folder = input("Enter INPUT folder of images: ").strip()
    if not os.path.isdir(in_folder):
        print("Folder not found")
        return

    out_folder = input("Enter OUTPUT folder for audio: ").strip()
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)

    key = get_key()
    if not key:
        return

    print("\nBatch Encoding...\n")

    for f in os.listdir(in_folder):
        if f.lower().endswith((".png",".jpg",".jpeg")):

            img_path = os.path.join(in_folder, f)
            name = os.path.splitext(f)[0]
            out_audio = os.path.join(out_folder, name + ".wav")

            print("Encoding:", f)
            encode_image(img_path, key, out_audio)

    print("\nBatch Done\n")


# ---------------- BATCH DECRYPT ----------------
def decrypt_batch():

    in_folder = input("Enter INPUT folder of audio: ").strip()
    if not os.path.isdir(in_folder):
        print("Folder not found")
        return

    out_folder = input("Enter OUTPUT folder for images: ").strip()
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)

    key = get_key()
    if not key:
        return

    print("\nBatch Decoding...\n")

    for f in os.listdir(in_folder):
        if f.lower().endswith(".wav"):

            aud_path = os.path.join(in_folder, f)
            name = os.path.splitext(f)[0]
            out_img = os.path.join(out_folder, name + ".png")

            print("Decoding:", f)
            decode_audio(aud_path, key, out_img)

    print("\nBatch Done\n")


# ---------------- MAIN MENU ----------------
def main():

    while True:

        print("\n===============================")
        print(" IMAGE ⇄ AUDIO CLI ")
        print("===============================")
        print("E - Encrypt")
        print("D - Decrypt")
        print("X - Exit")

        ch = input("Choice: ").upper()

        if ch == "X":
            break

        if ch not in ["E","D"]:
            print("Wrong choice")
            continue

        mode = input("S - Single | B - Batch : ").upper()

        if ch=="E" and mode=="S":
            encrypt_single()

        elif ch=="E" and mode=="B":
            encrypt_batch()

        elif ch=="D" and mode=="S":
            decrypt_single()

        elif ch=="D" and mode=="B":
            decrypt_batch()

        else:
            print("Invalid option")


if __name__ == "__main__":
    main()