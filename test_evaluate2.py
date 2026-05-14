import requests, base64, io, json
from PIL import Image

BASE = "http://127.0.0.1:8000"
IMG_DIR = r"D:\Desktop\IF-FILM-main\storage\results"

# Get a real fused image
with open(IMG_DIR + "\\test_over.jpg", "rb") as f1, \
     open(IMG_DIR + "\\test_under.jpg", "rb") as f2:
    files = {"over_img": ("over.jpg", f1, "image/jpeg"), "under_img": ("under.jpg", f2, "image/jpeg")}
    r = requests.post(BASE + "/api/fuse", files=files)
    fused_bytes = r.content

# Test /api/evaluate with detailed headers inspection
print("=== Testing /api/evaluate ===")
with open(IMG_DIR + "\\test_over.jpg", "rb") as f1, \
     open(IMG_DIR + "\\test_under.jpg", "rb") as f2:
    over_b64 = base64.b64encode(f1.read()).decode()
    under_b64 = base64.b64encode(f2.read()).decode()

# Use Session to see exact request/response
session = requests.Session()
files = {"image_file": ("fused.jpg", io.BytesIO(fused_bytes), "image/jpeg")}
data = {"algo": "IF-FILM", "over_img_base64": over_b64, "under_img_base64": under_b64}

# Prepare and inspect the request
req = requests.Request("POST", BASE + "/api/evaluate", files=files, data=data)
prepared = session.prepare_request(req)
print("Request headers:", dict(prepared.headers))
print("Content-Type:", prepared.headers.get("Content-Type"))

resp = session.send(prepared)
print("\nResponse Status:", resp.status_code)
print("Response Headers:", dict(resp.headers))
print("Response Body:", resp.text[:500] if len(resp.text) > 500 else resp.text)

# Test without base64 source images (only 4 base metrics)
print()
print("=== Testing /api/evaluate WITHOUT base64 sources ===")
files2 = {"image_file": ("fused.jpg", io.BytesIO(fused_bytes), "image/jpeg")}
data2 = {"algo": "IF-FILM"}
r2 = requests.post(BASE + "/api/evaluate", files=files2, data=data2)
print("Status:", r2.status_code)
print("Body:", r2.text)
