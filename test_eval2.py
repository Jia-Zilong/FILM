import requests, io
BASE = "http://127.0.0.1:8000"
fused_path = r"D:\Desktop\IF-FILM-main\storage\results\fused_20260514_214319_422260.jpg"
with open(fused_path, 'rb') as f:
    fused_data = f.read()
files = {
    'image_file': ('fused.jpg', io.BytesIO(fused_data), 'image/jpeg'),
    'over_img': ('over.jpg', io.BytesIO(fused_data), 'image/jpeg'),
    'under_img': ('under.jpg', io.BytesIO(fused_data), 'image/jpeg'),
}
data = {'algo': 'IF-FILM'}
r = requests.post(BASE + '/api/evaluate', files=files, data=data)
print('Status:', r.status_code)
print('Response:', r.json())
