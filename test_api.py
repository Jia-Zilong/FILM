import requests, base64, io
from PIL import Image

BASE = "http://127.0.0.1:8000"
IMG_DIR = r"D:\Desktop\IF-FILM-main\storage\results"

# Test 1: /api/fuse endpoint
print("=== Test 1: POST /api/fuse ===")
with open(IMG_DIR + "\\test_over.jpg", "rb") as f1, \
     open(IMG_DIR + "\\test_under.jpg", "rb") as f2:
    files = {"over_img": ("over.jpg", f1, "image/jpeg"), "under_img": ("under.jpg", f2, "image/jpeg")}
    r = requests.post(BASE + "/api/fuse", files=files)
    print("Status:", r.status_code)
    if r.status_code == 200:
        ct = r.headers.get("content-type")
        print("Response size:", len(r.content), "bytes, content-type:", ct)
    else:
        print("Body:", r.text)

# Test 2: /api/fuse/traditional endpoint
print()
print("=== Test 2: POST /api/fuse/traditional ===")
with open(IMG_DIR + "\\test_over.jpg", "rb") as f1, \
     open(IMG_DIR + "\\test_under.jpg", "rb") as f2:
    files = {"over_img": ("over.jpg", f1, "image/jpeg"), "under_img": ("under.jpg", f2, "image/jpeg")}
    data = {"algo_type": "avg"}
    r = requests.post(BASE + "/api/fuse/traditional", files=files, data=data)
    print("Status:", r.status_code)
    if r.status_code == 200:
        print("Response size:", len(r.content), "bytes")
    else:
        print("Body:", r.text)

# Test 3: /api/evaluate endpoint
print()
print("=== Test 3: POST /api/evaluate ===")
img = Image.new("RGB", (100, 100), color=(128, 128, 128))
buf = io.BytesIO()
img.save(buf, format="JPEG")
buf.seek(0)

with open(IMG_DIR + "\\test_over.jpg", "rb") as f1, \
     open(IMG_DIR + "\\test_under.jpg", "rb") as f2:
    over_b64 = base64.b64encode(f1.read()).decode()
    under_b64 = base64.b64encode(f2.read()).decode()

files = {"image_file": ("res.jpg", buf, "image/jpeg")}
data = {"algo": "IF-FILM", "over_img_base64": over_b64, "under_img_base64": under_b64}
r = requests.post(BASE + "/api/evaluate", files=files, data=data)
print("Status:", r.status_code)
print("Body:", r.text)
