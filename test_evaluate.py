import requests, base64, io, traceback
from PIL import Image
import numpy as np

BASE = "http://127.0.0.1:8000"
IMG_DIR = r"D:\Desktop\IF-FILM-main\storage\results"

# First, get a real fused image from the working endpoint
print("=== Step 1: Get fused image ===")
with open(IMG_DIR + "\\test_over.jpg", "rb") as f1, \
     open(IMG_DIR + "\\test_under.jpg", "rb") as f2:
    files = {"over_img": ("over.jpg", f1, "image/jpeg"), "under_img": ("under.jpg", f2, "image/jpeg")}
    r = requests.post(BASE + "/api/fuse", files=files)
    print("Fuse Status:", r.status_code)
    fused_bytes = r.content

# Now test /api/evaluate with the fused image
print()
print("=== Step 2: Test /api/evaluate ===")
with open(IMG_DIR + "\\test_over.jpg", "rb") as f1, \
     open(IMG_DIR + "\\test_under.jpg", "rb") as f2:
    over_b64 = base64.b64encode(f1.read()).decode()
    under_b64 = base64.b64encode(f2.read()).decode()

files = {"image_file": ("fused.jpg", io.BytesIO(fused_bytes), "image/jpeg")}
data = {"algo": "IF-FILM", "over_img_base64": over_b64, "under_img_base64": under_b64}
r = requests.post(BASE + "/api/evaluate", files=files, data=data)
print("Evaluate Status:", r.status_code)
if r.status_code != 200:
    print("Body:", r.text)

# Local debug: simulate what the server does
print()
print("=== Step 3: Local debug simulation ===")
try:
    pil_img = Image.open(io.BytesIO(fused_bytes)).convert('L')
    fused_gray = np.array(pil_img)
    fused_float = fused_gray.astype(np.float32)
    print("Image shape:", fused_gray.shape, "dtype:", fused_gray.dtype)
    print("Min/Max:", fused_gray.min(), fused_gray.max())

    # Test ImageMetrics.evaluate (4 base metrics)
    from mef_metrics import ImageMetrics
    result = ImageMetrics.evaluate(fused_gray)
    print("Base metrics:", result)

    # Test Evaluator.VIF
    from utils.Evaluator import Evaluator
    over_gray = np.array(Image.open(io.BytesIO(base64.b64decode(over_b64))).convert('L')).astype(np.float32)
    under_gray = np.array(Image.open(io.BytesIO(base64.b64decode(under_b64))).convert('L')).astype(np.float32)
    print("Source images shape - Over:", over_gray.shape, "Under:", under_gray.shape)

    vif = Evaluator.VIF(fused_float, over_gray, under_gray)
    print("VIF:", vif)

    qabf = Evaluator.Qabf(fused_float, over_gray, under_gray)
    print("Qabf:", qabf)

except Exception as e:
    print("Local error:", str(e))
    traceback.print_exc()
