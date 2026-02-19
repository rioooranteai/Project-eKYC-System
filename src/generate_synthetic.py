import json
import os
import random
import time

import requests
from PIL import Image, ImageDraw, ImageFont
from faker import Faker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(BASE_DIR, "Data", "Template", "Template-KTP.png")
FIELDS_PATH = os.path.join(BASE_DIR, "Data", "Template", "fields.json")
GENERATED_DIR = os.path.join(BASE_DIR, "Data", "Generated E-ktp")
OUTPUT_DIR = os.path.join(GENERATED_DIR, "images")
LABEL_DIR = os.path.join(GENERATED_DIR, "labels")
FACE_CACHE_DIR = os.path.join(BASE_DIR, "Data", "Face Cache")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LABEL_DIR, exist_ok=True)
os.makedirs(FACE_CACHE_DIR, exist_ok=True)

fake = Faker("id_ID")

FONT_PATHS = {
    "arial": [
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
    "arial_bold": [
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "ocr_a": [
        os.path.join(BASE_DIR, "Data", "Fonts", "OCRA.ttf"),
        os.path.join(BASE_DIR, "Data", "Fonts", "OCRAExt.ttf"),
        "C:/Windows/Fonts/OCRAEXT.TTF",
        "/usr/share/fonts/truetype/ocr-a/OCRA.ttf",
    ],
}


def get_font(font_key: str, size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_PATHS.get(font_key, []):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    try:
        return ImageFont.truetype("arialbd.ttf", size)
    except Exception:
        return ImageFont.load_default()


FIELD_STYLE = {
    "Provinsi": {"font": "arial_bold", "center": True},
    "Kabupaten/Kota": {"font": "arial_bold", "center": True},
    "NIK": {"font": "ocr_a", "center": False},
    "Nama": {"font": "arial_bold", "center": False},
    "Tempat Tanggal Lahir": {"font": "arial_bold", "center": False},
    "Jenis Kelamin": {"font": "arial_bold", "center": False},
    "Alamat": {"font": "arial_bold", "center": False},
    "RT/RW": {"font": "arial_bold", "center": False},
    "Kelurahan/Desa": {"font": "arial_bold", "center": False},
    "Kecamatan": {"font": "arial_bold", "center": False},
    "Agama": {"font": "arial_bold", "center": False},
    "Status Perkawinan": {"font": "arial_bold", "center": False},
    "Pekerjaan": {"font": "arial_bold", "center": False},
    "Kewarganegaraan": {"font": "arial_bold", "center": False},
    "Berlaku Hingga": {"font": "arial_bold", "center": False},
    "Gol. Darah": {"font": "arial_bold", "center": False},
    "Kota Dibuat": {"font": "arial_bold", "center": True},
    "Tanggal KTP Dikeluarkan": {"font": "arial_bold", "center": True},
}

PROVINSI_LIST = [
    "JAWA BARAT", "JAWA TENGAH", "JAWA TIMUR", "DKI JAKARTA",
    "SUMATERA UTARA", "SULAWESI SELATAN", "KALIMANTAN TIMUR",
    "BALI", "DI YOGYAKARTA", "BANTEN"
]
AGAMA_LIST = ["ISLAM", "KRISTEN", "KATOLIK", "HINDU", "BUDHA", "KONGHUCU"]
STATUS_LIST = ["BELUM KAWIN", "KAWIN", "CERAI HIDUP", "CERAI MATI"]
PEKERJAAN_LIST = [
    "PELAJAR/MAHASISWA", "KARYAWAN SWASTA", "PEGAWAI NEGERI SIPIL",
    "WIRASWASTA", "PETANI", "NELAYAN", "BURUH", "DOKTER",
    "GURU/DOSEN", "TIDAK BEKERJA", "PENSIUNAN"
]
GOLDAR_LIST = ["A", "B", "AB", "O"]


def clean_city(name: str) -> str:
    prefixes = [
        "Kota Administrasi ", "Kabupaten ", "Kota ", "Kab. ", "Kab ",
    ]
    result = name.strip()
    for prefix in prefixes:
        if result.lower().startswith(prefix.lower()):
            result = result[len(prefix):]
            break
    return result.upper()


def generate_nik():
    kode_wilayah = f"{random.randint(11, 99)}{random.randint(1, 99):02d}{random.randint(1, 99):02d}"
    tgl_str = f"{random.randint(1, 28):02d}{random.randint(1, 12):02d}{random.randint(60, 99):02d}"
    urut = f"{random.randint(1, 9999):04d}"
    return kode_wilayah + tgl_str + urut


def generate_ktp_data():
    tgl_lahir = fake.date_of_birth(minimum_age=17, maximum_age=80)
    provinsi = random.choice(PROVINSI_LIST)
    kabupaten_kota = fake.city().upper()
    prefix_lokasi = random.choice(["KOTA", "KABUPATEN"])
    tgl_ktp = fake.date_between(start_date="-5y", end_date="today")
    return {
        "Provinsi": f"PROVINSI {provinsi}",
        "Kabupaten/Kota": f"{prefix_lokasi} {kabupaten_kota}",
        "NIK": generate_nik(),
        "Nama": fake.name().upper(),
        "Tempat Tanggal Lahir": f"{clean_city(fake.city())}, {tgl_lahir.strftime('%d-%m-%Y')}",
        "Jenis Kelamin": random.choice(["LAKI-LAKI", "PEREMPUAN"]),
        "Alamat": fake.street_address().upper()[:26],
        "RT/RW": f"{random.randint(1, 20):03d}/{random.randint(1, 20):03d}",
        "Kelurahan/Desa": clean_city(fake.city()),
        "Kecamatan": clean_city(fake.city()),
        "Agama": random.choice(AGAMA_LIST),
        "Status Perkawinan": random.choice(STATUS_LIST),
        "Pekerjaan": random.choice(PEKERJAAN_LIST),
        "Kewarganegaraan": "WNI",
        "Berlaku Hingga": "SEUMUR HIDUP",
        "Gol. Darah": random.choice(GOLDAR_LIST),
        "Kota Dibuat": clean_city(kabupaten_kota),
        "Tanggal KTP Dikeluarkan": tgl_ktp.strftime('%d-%m-%Y'),
    }


def download_faces(n: int):
    """
    Download n gambar wajah dari thispersondoesnotexist.com ke folder cache.
    Setiap request diberi jeda supaya tidak diblokir.
    """
    print(f"Mengunduh {n} gambar wajah ke cache...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    downloaded = 0
    attempts = 0
    max_attempts = n * 3  # toleransi retry jika gagal

    while downloaded < n and attempts < max_attempts:
        attempts += 1
        try:
            response = requests.get(
                "https://thispersondoesnotexist.com",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                face_path = os.path.join(FACE_CACHE_DIR, f"face_{downloaded + 1:04d}.jpg")
                with open(face_path, "wb") as f:
                    f.write(response.content)
                downloaded += 1

                if downloaded % 10 == 0:
                    print(f"  {downloaded}/{n} wajah diunduh")

                # Jeda antar request agar tidak diblokir (1-2 detik)
                time.sleep(random.uniform(1.0, 2.0))
            else:
                print(f"  Gagal (status {response.status_code}), mencoba lagi...")
                time.sleep(2)

        except requests.RequestException as e:
            print(f"  Error: {e}, mencoba lagi...")
            time.sleep(3)

    print(f"Selesai mengunduh. Total tersimpan: {downloaded} wajah di {FACE_CACHE_DIR}")
    return downloaded


def get_cached_faces() -> list:
    """Ambil daftar path semua wajah yang sudah ada di cache."""
    files = [
        os.path.join(FACE_CACHE_DIR, f)
        for f in os.listdir(FACE_CACHE_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]
    return files


def paste_face(img: Image.Image, face_box: list) -> tuple:
    """
    Tempel gambar wajah acak dari cache ke area foto di KTP.
    Mengembalikan (img, face_path) supaya file bisa dihapus setelah render selesai.
    """
    cached = get_cached_faces()
    if not cached:
        print("  Peringatan: tidak ada wajah di cache, area foto dibiarkan kosong.")
        return img, None

    x1, y1, x2, y2 = face_box
    box_w = x2 - x1
    box_h = y2 - y1

    face_path = random.choice(cached)
    face_img  = Image.open(face_path).convert("RGB")
    face_img  = face_img.resize((box_w, box_h), Image.LANCZOS)

    img.paste(face_img, (x1, y1))

    face_img.close()  # tutup file dari memory PIL

    return img, face_path


def load_fields():
    with open(FIELDS_PATH, "r") as f:
        return json.load(f)


def draw_text_in_box(draw, text, box, font_key, img_w, img_h, center=False):
    """
    Render teks di dalam bounding box.
    Jika center=True, teks akan ditempatkan di tengah horizontal dan vertikal box.
    Mengembalikan tuple (cx, cy, nw, nh) dalam format YOLO normalized.
    """
    x1, y1, x2, y2 = box
    box_w = x2 - x1
    box_h = y2 - y1

    font_size = max(8, int(box_h * 0.90))
    font = get_font(font_key, font_size)

    if center:
        bbox_text = font.getbbox(text)
        text_w = bbox_text[2] - bbox_text[0]
        text_h = bbox_text[3] - bbox_text[1]
        x_pos = x1 + (box_w - text_w) / 2
        y_pos = y1 + (box_h - text_h) / 2
    else:
        x_pos = x1 + 2
        y_pos = y1 + (box_h - font_size) / 2

    draw.text((x_pos, y_pos), text, fill="black", font=font)

    cx = (x1 + x2) / 2 / img_w
    cy = (y1 + y2) / 2 / img_h
    nw = box_w / img_w
    nh = box_h / img_h
    return cx, cy, nw, nh


def render_ktp(data: dict, fields: dict, output_path: str):
    img  = Image.open(TEMPLATE_PATH).convert("RGB")
    img_w, img_h = img.size

    used_face_path = None

    if "Foto" in fields:
        img, used_face_path = paste_face(img, fields["Foto"])

    draw = ImageDraw.Draw(img)
    yolo_labels = []
    field_keys  = list(fields.keys())

    for field, value in data.items():
        if field not in fields:
            continue

        style    = FIELD_STYLE.get(field, {"font": "arial_bold", "center": False})
        font_key = style["font"]
        center   = style["center"]
        box      = fields[field]

        cx, cy, nw, nh = draw_text_in_box(
            draw, value, box, font_key, img_w, img_h, center=center
        )

        class_id = field_keys.index(field)
        yolo_labels.append(f"{class_id} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")

    img.save(output_path)
    img.close()  # tutup template dari memory

    # Hapus file wajah dari disk setelah render selesai
    if used_face_path and os.path.exists(used_face_path):
        os.remove(used_face_path)

    return yolo_labels


# --- GENERATE BATCH ---

def generate_batch(n: int = 100):
    print(f"Template  : {TEMPLATE_PATH}")
    print(f"Output    : {OUTPUT_DIR}")
    print(f"Jumlah    : {n} gambar\n")

    if not os.path.exists(FIELDS_PATH):
        print("ERROR: fields.json belum ada.")
        print("Jalankan dulu: python src/find_coordinate.py")
        return

    fields = load_fields()
    print(f"Field terdeteksi: {list(fields.keys())}\n")

    # Cek cache wajah, download jika kurang
    cached = get_cached_faces()
    if len(cached) < n:
        kurang = n - len(cached)
        print(f"Cache wajah kurang {kurang}, akan diunduh terlebih dahulu.")
        download_faces(kurang)
    else:
        print(f"Cache wajah tersedia: {len(cached)} gambar, skip download.")

    print()

    for i in range(n):
        data = generate_ktp_data()
        filename = f"ktp_{i + 1:04d}"
        img_path = os.path.join(OUTPUT_DIR, f"{filename}.png")
        label_path = os.path.join(LABEL_DIR, f"{filename}.txt")

        labels = render_ktp(data, fields, img_path)

        with open(label_path, "w") as f:
            f.write("\n".join(labels))

        if (i + 1) % 10 == 0:
            print(f"  {i + 1}/{n} gambar selesai")

    print(f"\nSelesai. {n} gambar tersimpan di Data/Generated E-ktp/")
    save_classes(fields)


def save_classes(fields: dict):
    os.makedirs(GENERATED_DIR, exist_ok=True)
    classes_path = os.path.join(GENERATED_DIR, "classes.txt")
    with open(classes_path, "w") as f:
        for field in fields.keys():
            f.write(field + "\n")
    print(f"classes.txt tersimpan: {classes_path}")


if __name__ == "__main__":
    generate_batch(n=150)
