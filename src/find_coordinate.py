import json
import os

import cv2

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(BASE_DIR, "Data", "Template", "Template-KTP.png")
OUTPUT_JSON = os.path.join(BASE_DIR, "Data", "Template", "fields.json")

boxes = {}
drawing = False
start_x = start_y = 0
current_box = None
img_display = None
img_original = None

FIELD_LIST = [
    "Provinsi",
    "Kabupaten/Kota",
    "NIK",
    "Nama",
    "Tempat Tanggal Lahir",
    "Jenis Kelamin",
    "Alamat",
    "RT/RW",
    "Kelurahan/Desa",
    "Kecamatan",
    "Agama",
    "Status Perkawinan",
    "Pekerjaan",
    "Kewarganegaraan",
    "Berlaku Hingga",
    "Gol. Darah",
    "Foto",
    "Kota Dibuat",
    "Tanggal KTP Dikeluarkan"
]

current_field_idx = 0

COLOR_DONE = (0, 200, 0)
COLOR_CURRENT = (0, 100, 255)
COLOR_TEXT = (255, 255, 255)

def get_current_field():
    if current_field_idx < len(FIELD_LIST):
        return FIELD_LIST[current_field_idx]
    return None


def redraw():
    global img_display
    img_display = img_original.copy()
    h, w = img_display.shape[:2]

    for field, (x1, y1, x2, y2) in boxes.items():
        cv2.rectangle(img_display, (x1, y1), (x2, y2), COLOR_DONE, 2)
        cv2.putText(img_display, field, (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, COLOR_DONE, 1)

    if current_box:
        x1, y1, x2, y2 = current_box
        cv2.rectangle(img_display, (x1, y1), (x2, y2), COLOR_CURRENT, 2)

    field = get_current_field()
    if field:
        info = f"Field ({current_field_idx + 1}/{len(FIELD_LIST)}): {field}  |  Drag untuk buat box  |  [z] undo  |  [s] simpan  |  [q] keluar"
    else:
        info = "Semua field selesai!  |  [s] simpan  |  [q] keluar"

    cv2.rectangle(img_display, (0, h - 30), (w, h), (30, 30, 30), -1)
    cv2.putText(img_display, info, (8, h - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, COLOR_TEXT, 1)

    cv2.imshow("KTP Field Mapper", img_display)


def mouse_callback(event, x, y, flags, param):
    global drawing, start_x, start_y, current_box

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        start_x, start_y = x, y
        current_box = None

    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        current_box = (min(start_x, x), min(start_y, y),
                       max(start_x, x), max(start_y, y))
        redraw()

    elif event == cv2.EVENT_LBUTTONUP and drawing:
        drawing = False
        field = get_current_field()
        if field and abs(x - start_x) > 5 and abs(y - start_y) > 5:
            x1, y1 = min(start_x, x), min(start_y, y)
            x2, y2 = max(start_x, x), max(start_y, y)
            boxes[field] = (x1, y1, x2, y2)
            print(f"✅  {field}: ({x1}, {y1}, {x2}, {y2})")
            current_box = None
            next_field()
        redraw()


def next_field():
    global current_field_idx
    current_field_idx += 1
    field = get_current_field()
    if field:
        print(f"\n➡️  Sekarang gambar box untuk: [{field}]")
    else:
        print("\n🎉 Semua field selesai! Tekan [s] untuk simpan.")


def save_json():
    data = {field: list(bbox) for field, bbox in boxes.items()}
    with open(OUTPUT_JSON, "w") as f:
        json.dump(data, f, indent=4)
    print(f"\n💾 Disimpan ke: {OUTPUT_JSON}")
    print(json.dumps(data, indent=4))


# ─── MAIN ───────────────────────────────────────────────
def main():
    global img_original, img_display, current_field_idx

    if not os.path.exists(TEMPLATE_PATH):
        print(f"File tidak ditemukan: {TEMPLATE_PATH}")
        print("Pastikan Template-KTP.png ada di folder Data/Template/")
        return

    img_original = cv2.imread(TEMPLATE_PATH)
    print(f"Template loaded: {img_original.shape[1]}x{img_original.shape[0]} px")
    print(f"\nMulai gambar box untuk: [{FIELD_LIST[0]}]")
    print("─" * 60)
    print("CARA PAKAI:")
    print("  • Drag mouse untuk buat bounding box per field")
    print("  • [z] = undo field terakhir")
    print("  • [s] = simpan ke fields.json")
    print("  • [q] = keluar")
    print("─" * 60)

    cv2.namedWindow("KTP Field Mapper", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("KTP Field Mapper", 1000, 700)
    cv2.setMouseCallback("KTP Field Mapper", mouse_callback)

    redraw()

    while True:
        key = cv2.waitKey(20) & 0xFF

        if key == ord('q'):
            break

        elif key == ord('s'):
            save_json()

        elif key == ord('z'):  # undo
            if boxes:
                last = list(boxes.keys())[-1]
                del boxes[last]
                current_field_idx = max(0, current_field_idx - 1)
                print(f"Undo field: {last}")
                redraw()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
