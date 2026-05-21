from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request, BackgroundTasks
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from mef_engine import MEFFusionEngine
import uvicorn
import sys
import traceback
from mef_metrics import ImageMetrics
import os
from datetime import datetime
from pathlib import Path
from PIL import Image
import io
import numpy as np
import sqlite3
import cv2
from contextlib import asynccontextmanager

# ================== 输入验证 ==================
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/bmp", "image/webp"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
BASE_DIR = Path(__file__).resolve().parent
SAVE_DIR = BASE_DIR / "storage" / "results"
DB_PATH = BASE_DIR / "mef_history.db"


def validate_image(file: UploadFile, field_name: str = "image"):
    """验证上传文件的类型和大小"""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} 不支持的文件类型: {file.content_type}，仅支持 {', '.join(sorted(ALLOWED_CONTENT_TYPES))}"
        )


def validate_image_payload(data: bytes, field_name: str = "image"):
    try:
        with Image.open(io.BytesIO(data)) as img:
            size = img.size
            img.verify()
        return size
    except Exception as e:
        print(f"[DEBUG] validate_image_payload FAILED: {field_name}, error={type(e).__name__}: {e}")
        raise HTTPException(status_code=400, detail=f"{field_name} is not a valid image file")


def validate_same_size(size_a, size_b):
    if size_a != size_b:
        raise HTTPException(
            status_code=400,
            detail=(
                "Input images must have the same dimensions: "
                f"{size_a[0]}x{size_a[1]} vs {size_b[0]}x{size_b[1]}"
            )
        )


async def read_and_validate(file: UploadFile, field_name: str = "image", strict_content_type: bool = True):
    """读取文件并验证大小"""
    if strict_content_type:
        validate_image(file, field_name)
    data = await file.read()
    print(f"[DEBUG] {field_name}: content_type={file.content_type}, size={len(data)} bytes")
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} 文件过大 ({len(data) / 1024 / 1024:.1f}MB)，最大支持 {MAX_FILE_SIZE / 1024 / 1024:.0f}MB"
        )
    return data, validate_image_payload(data, field_name)
# ==============================================

film_engine = None
ffmef_engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global film_engine, ffmef_engine
    film_engine = MEFFusionEngine()
    print("FILM MEF 引擎加载完毕！")

    # Load FFMEF model
    try:
        import torch
        FFMEF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "compare_methods", "FFMEF")
        MODEL_DIR = os.path.join(FFMEF_DIR, "model")
        if MODEL_DIR not in sys.path:
            sys.path.insert(0, MODEL_DIR)
        from FFMEF import FFMEF

        # Use CPU for FFMEF to save VRAM (FILM already on GPU)
        device = torch.device("cpu")
        ckpt_path = os.path.join(FFMEF_DIR, "ckp", "mef.pth")
        model = FFMEF(channels=4)
        checkpoint = torch.load(ckpt_path, map_location=device, weights_only=False)
        net = checkpoint['model']
        net = {key.replace("module.", ""): val for key, val in net.items()}
        model.load_state_dict(net, strict=False)
        model.to(device)
        model.eval()

        ffmef_engine = {"model": model, "device": device}
        print("FFMEF 引擎加载完毕！(CPU 模式，节省显存)")
    except Exception as e:
        print(f"[WARN] FFMEF 引擎加载失败: {e}")
        ffmef_engine = None

    # Clear unused GPU memory
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            print(f"GPU 显存已清理，当前使用: {torch.cuda.memory_allocated()/1024**2:.0f}MB / {torch.cuda.get_device_properties(0).total_mem/1024**2:.0f}MB")
    except Exception:
        pass

    yield
    print("正在关闭服务...")


app = FastAPI(title="多曝光图像融合系统 API", lifespan=lifespan)

# Starlette 0.44.0: use module-level constants (not class attributes)
import starlette.formparsers
starlette.formparsers.MAX_PART_SIZE = 50 * 1024 * 1024  # 50MB for form fields
starlette.formparsers.MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB for files

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

save_dir = SAVE_DIR
os.makedirs(save_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(save_dir)), name="static")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            algo TEXT,
            img_url TEXT,
            time TEXT,
            en REAL,
            sd REAL,
            sf REAL,
            ag REAL,
            vif REAL,
            qabf REAL
        )
    ''')
    conn.commit()
    conn.close()


init_db()
print("[DB] SQLite 数据库初始化完成！")


@app.post("/api/fuse")
async def fuse_images(
        over_img: UploadFile = File(...),
        under_img: UploadFile = File(...)
):
    try:
        if film_engine is None:
            raise HTTPException(status_code=503, detail="FILM Fusion engine is not ready")

        over_bytes, over_size = await read_and_validate(over_img, "over image")
        under_bytes, under_size = await read_and_validate(under_img, "under image")
        validate_same_size(over_size, under_size)

        fused_bytes = film_engine.fuse(over_bytes, under_bytes)

        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        save_filename = f"fused_{timestamp}.jpg"
        save_path = save_dir / save_filename

        with open(save_path, "wb") as f:
            f.write(fused_bytes)

        print(f"[SAVE] 融合图像已保存至 {save_path}")
        return Response(content=fused_bytes, media_type="image/jpeg")

    except HTTPException:
        raise
    except Exception as e:
        print("[ERROR] FILM 推理逻辑发生错误：")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/fuse-multi", summary="多图融合 (2-10张)")
async def fuse_multi_images(
        files: list[UploadFile] = File(...),
        algo_type: str = Form("ai"),
        quality: int = Form(95),
        max_dim: int = Form(1024),
):
    try:
        if len(files) < 2:
            raise HTTPException(status_code=400, detail="至少需要 2 张图片")
        if len(files) > 10:
            raise HTTPException(status_code=400, detail="最多支持 10 张图片")

        # Validate all files
        data_list = []
        sizes = []
        for i, f in enumerate(files):
            validate_image(f, f"image_{i}")
            data = await f.read()
            if len(data) > MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail=f"image_{i} 文件过大")
            data_list.append(data)
            sizes.append(validate_image_payload(data, f"image_{i}"))

        # Check all same size
        if not all(s == sizes[0] for s in sizes):
            raise HTTPException(status_code=400, detail="所有输入图像必须尺寸一致")

        if film_engine is None:
            raise HTTPException(status_code=503, detail="FILM Fusion engine is not ready")

        if algo_type in ("avg", "max", "mertens"):
            # Traditional: pairwise with opencv
            result = cv2.imdecode(np.frombuffer(data_list[0], np.uint8), cv2.IMREAD_COLOR)
            for i in range(1, len(data_list)):
                img = cv2.imdecode(np.frombuffer(data_list[i], np.uint8), cv2.IMREAD_COLOR)
                if algo_type == "avg":
                    result = cv2.addWeighted(result, 0.5, img, 0.5, 0)
                elif algo_type == "max":
                    result = cv2.max(result, img)
                elif algo_type == "mertens":
                    result = cv2.addWeighted(result, 0.5, img, 0.5, 0)
            _, buffer = cv2.imencode('.jpg', result, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
            return Response(content=buffer.tobytes(), media_type="image/jpeg")

        # AI/FFMEF: use engine's pairwise fusion
        fused_bytes = film_engine.fuse_multi(data_list, quality=quality, max_dim=max_dim)

        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        save_filename = f"fused_multi_{timestamp}.jpg"
        save_path = save_dir / save_filename

        with open(save_path, "wb") as f:
            f.write(fused_bytes)

        print(f"[SAVE] 多图融合已保存至 {save_path}")
        return Response(content=fused_bytes, media_type="image/jpeg")

    except HTTPException:
        raise
    except Exception as e:
        print("[ERROR] 多图融合发生错误：")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/fuse/ffmef", summary="FFMEF 深度学习融合 (CVPRW 2023)")
async def fuse_ffmef(
        over_img: UploadFile = File(...),
        under_img: UploadFile = File(...)
):
    try:
        if ffmef_engine is None:
            raise HTTPException(status_code=503, detail="FFMEF engine is not ready")

        over_bytes, over_size = await read_and_validate(over_img, "over image")
        under_bytes, under_size = await read_and_validate(under_img, "under image")
        validate_same_size(over_size, under_size)

        import torch

        model = ffmef_engine["model"]
        device = ffmef_engine["device"]

        # Decode images
        img1 = cv2.imdecode(np.frombuffer(over_bytes, np.uint8), cv2.IMREAD_COLOR)
        img2 = cv2.imdecode(np.frombuffer(under_bytes, np.uint8), cv2.IMREAD_COLOR)

        if img1 is None or img2 is None:
            raise HTTPException(status_code=400, detail="无法解码图像，请检查文件是否损坏")

        # Convert to YCbCr, extract Y channel
        y1 = cv2.cvtColor(img1, cv2.COLOR_BGR2YCrCb)[:, :, 0]
        y2 = cv2.cvtColor(img2, cv2.COLOR_BGR2YCrCb)[:, :, 0]

        # Normalize Y to [0, 1] as float32 tensors
        y1_tensor = torch.from_numpy(y1.astype(np.float32) / 255.0).unsqueeze(0).unsqueeze(0).to(device)
        y2_tensor = torch.from_numpy(y2.astype(np.float32) / 255.0).unsqueeze(0).unsqueeze(0).to(device)

        with torch.no_grad():
            fused_y = model(img0_RGB=None, img0_Y=y1_tensor, img1_RGB=None, img1_Y=y2_tensor)
            fused_y = fused_y.clamp(0, 1)

        # Convert fused Y [0,1] to [0,255] uint8
        fused_y_np = (fused_y.squeeze(0).squeeze(0).cpu().numpy() * 255.0).astype(np.uint8)

        # Merge with averaged Cb/Cr
        cb1 = cv2.cvtColor(img1, cv2.COLOR_BGR2YCrCb)[:, :, 1]
        cr1 = cv2.cvtColor(img1, cv2.COLOR_BGR2YCrCb)[:, :, 2]
        cb2 = cv2.cvtColor(img2, cv2.COLOR_BGR2YCrCb)[:, :, 1]
        cr2 = cv2.cvtColor(img2, cv2.COLOR_BGR2YCrCb)[:, :, 2]
        cb_fused = ((cb1.astype(np.float32) + cb2.astype(np.float32)) / 2).astype(np.uint8)
        cr_fused = ((cr1.astype(np.float32) + cr2.astype(np.float32)) / 2).astype(np.uint8)

        fused_ycrcb = cv2.merge([fused_y_np, cb_fused, cr_fused])
        fused_rgb = cv2.cvtColor(fused_ycrcb, cv2.COLOR_YCrCb2RGB)

        _, buffer = cv2.imencode('.jpg', cv2.cvtColor(fused_rgb, cv2.COLOR_RGB2BGR))
        return Response(content=buffer.tobytes(), media_type="image/jpeg")

    except HTTPException:
        raise
    except Exception as e:
        print("[ERROR] FFMEF 推理逻辑发生错误：")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/fuse/traditional", summary="传统算法集合 (包含平均、最大值、Mertens)")
async def fuse_traditional(
        over_img: UploadFile = File(...),
        under_img: UploadFile = File(...),
        algo_type: str = Form("avg")
):
    try:
        over_bytes, over_size = await read_and_validate(over_img, "over image")
        under_bytes, under_size = await read_and_validate(under_img, "under image")
        validate_same_size(over_size, under_size)

        img1 = cv2.imdecode(np.frombuffer(over_bytes, np.uint8), cv2.IMREAD_COLOR)
        img2 = cv2.imdecode(np.frombuffer(under_bytes, np.uint8), cv2.IMREAD_COLOR)

        if img1 is None or img2 is None:
            raise HTTPException(status_code=400, detail="无法解码图像，请检查文件是否损坏")

        if algo_type == "avg":
            fused = cv2.addWeighted(img1, 0.5, img2, 0.5, 0)
        elif algo_type == "max":
            fused = cv2.max(img1, img2)
        elif algo_type == "mertens":
            merge_mertens = cv2.createMergeMertens()
            fused_float = merge_mertens.process([img1, img2])
            fused = np.clip(fused_float * 255, 0, 255).astype(np.uint8)
        else:
            raise HTTPException(status_code=400, detail=f"未知的算法类型: {algo_type}，可选: avg, max, mertens")

        _, buffer = cv2.imencode('.jpg', fused)
        return Response(content=buffer.tobytes(), media_type="image/jpeg")

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] 传统算法 ({algo_type}) 发生错误：")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/evaluate", summary="计算评价指标并存档到数据库")
async def evaluate_image(
        request: Request,
        background_tasks: BackgroundTasks,
        image_file: UploadFile = File(...),
        algo: str = Form("AI"),
        over_img: UploadFile = File(None),
        under_img: UploadFile = File(None),
        metrics: str = Form(None),  # NEW: comma-separated metric names
):
    try:
        from utils.Evaluator import Evaluator

        img_bytes, _ = await read_and_validate(image_file, "evaluation image", strict_content_type=False)
        pil_img = Image.open(io.BytesIO(img_bytes)).convert('L')
        fused_gray = np.array(pil_img)
        fused_float = fused_gray.astype(np.float32)

        # Parse selected metrics
        if metrics:
            selected = [m.strip().upper() for m in metrics.split(',')]
        else:
            selected = ['EN', 'SD', 'SF', 'AG', 'VIF', 'Qabf']  # default: all

        # Fast metrics: only compute selected ones that are EN/SD/SF/AG
        fast_selected = [m for m in selected if m in ('EN', 'SD', 'SF', 'AG')]
        slow_selected = [m for m in selected if m in ('VIF', 'Qabf')]

        if fast_selected:
            full_result = ImageMetrics.evaluate(fused_gray)
            metrics_result = {k: v for k, v in full_result.items() if k in fast_selected}
        else:
            metrics_result = {}

        # Pad uncomputed fast metrics with None
        for m in fast_selected:
            if m not in metrics_result:
                metrics_result[m] = None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"eval_{timestamp}.jpg"
        save_path = save_dir / filename

        with open(save_path, "wb") as f:
            f.write(img_bytes)

        img_url = str(request.url_for("static", path=filename))
        curr_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Save initial record
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO history (algo, img_url, time, en, sd, sf, ag, vif, qabf) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (algo, img_url, curr_time,
                   metrics_result.get('EN', 0) or 0.0,
                   metrics_result.get('SD', 0) or 0.0,
                   metrics_result.get('SF', 0) or 0.0,
                   metrics_result.get('AG', 0) or 0.0,
                   0.0, 0.0))
        record_id = c.lastrowid
        conn.commit()
        conn.close()

        # Build response: only include selected metrics
        result_data = {}
        for m in selected:
            if m in metrics_result and metrics_result[m] is not None:
                result_data[m] = metrics_result[m]
            else:
                result_data[m] = None

        result = {"code": 200, "message": "指标计算与存档成功", "data": result_data}

        # Background task: compute VIF/Qabf if selected and source images provided
        if slow_selected and over_img and under_img:
            over_data = await over_img.read()
            under_data = await under_img.read()

            def _compute_vif_qabf():
                try:
                    over_gray = np.array(Image.open(io.BytesIO(over_data)).convert('L')).astype(np.float32)
                    under_gray = np.array(Image.open(io.BytesIO(under_data)).convert('L')).astype(np.float32)
                    if 'VIF' in slow_selected:
                        vif_val = round(float(Evaluator.VIF(fused_float, over_gray, under_gray)), 4)
                    else:
                        vif_val = 0.0
                    if 'Qabf' in slow_selected:
                        qabf_val = round(float(Evaluator.Qabf(fused_float, over_gray, under_gray)), 4)
                    else:
                        qabf_val = 0.0
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("UPDATE history SET vif = ?, qabf = ? WHERE id = ?", (vif_val, qabf_val, record_id))
                    conn.commit()
                    conn.close()
                    print(f"[VIF/Qabf] id={record_id}: VIF={vif_val}, Qabf={qabf_val}")
                except Exception as e:
                    print(f"[VIF/Qabf ERROR] id={record_id}: {e}")
                    traceback.print_exc()

            background_tasks.add_task(_compute_vif_qabf)

        return result

    except HTTPException:
        raise
    except Exception as e:
        print("[ERROR] 指标计算发生错误：")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/fuse/compare", summary="多算法并行对比融合")
async def fuse_compare(
        files: list[UploadFile] = File(...),
        quality: int = Form(95),
        max_dim: int = Form(1024),
):
    """Run all 5 algorithms on the same input images and return comparison results."""
    try:
        if len(files) < 2:
            raise HTTPException(status_code=400, detail="至少需要 2 张图片")
        if len(files) > 10:
            raise HTTPException(status_code=400, detail="最多支持 10 张图片")

        # Validate all files
        data_list = []
        sizes = []
        for i, f in enumerate(files):
            validate_image(f, f"image_{i}")
            data = await f.read()
            if len(data) > MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail=f"image_{i} 文件过大")
            data_list.append(data)
            sizes.append(validate_image_payload(data, f"image_{i}"))

        if not all(s == sizes[0] for s in sizes):
            raise HTTPException(status_code=400, detail="所有输入图像必须尺寸一致")

        n_images = len(data_list)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        results = []

        # ---------- helpers ----------
        def _run_algo(name: str, fuse_fn):
            """Run a single algorithm, compute metrics, save result, record entry."""
            try:
                fused_bytes = fuse_fn()
                save_filename = f"fused_compare_{name}_{timestamp}.jpg"
                save_path = save_dir / save_filename
                with open(save_path, "wb") as sf:
                    sf.write(fused_bytes)
                print(f"[SAVE] {name} 对比结果已保存至 {save_path}")

                # Compute fast metrics on grayscale
                fused_arr = cv2.imdecode(np.frombuffer(fused_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
                metrics = ImageMetrics.evaluate(fused_arr)

                entry = {
                    "algo": name,
                    "image_url": f"/static/{save_filename}",
                    "en": metrics["EN"],
                    "sd": metrics["SD"],
                    "sf": metrics["SF"],
                    "ag": metrics["AG"],
                }
                results.append(entry)
            except Exception as e:
                print(f"[ERROR] {name} 算法发生错误：")
                traceback.print_exc()
                results.append({"algo": name, "error": str(e)})

        def _traditional_avg():
            result = cv2.imdecode(np.frombuffer(data_list[0], np.uint8), cv2.IMREAD_COLOR)
            for i in range(1, n_images):
                img = cv2.imdecode(np.frombuffer(data_list[i], np.uint8), cv2.IMREAD_COLOR)
                result = cv2.addWeighted(result, 0.5, img, 0.5, 0)
            _, buf = cv2.imencode('.jpg', result, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
            return buf.tobytes()

        def _traditional_max():
            imgs = [cv2.imdecode(np.frombuffer(d, np.uint8), cv2.IMREAD_COLOR) for d in data_list]
            result = np.maximum.reduce(imgs)
            _, buf = cv2.imencode('.jpg', result, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
            return buf.tobytes()

        def _traditional_mertens():
            imgs = [cv2.imdecode(np.frombuffer(d, np.uint8), cv2.IMREAD_COLOR) for d in data_list]
            merge_mertens = cv2.createMergeMertens()
            fused_float = merge_mertens.process(imgs)
            fused = np.clip(fused_float * 255, 0, 255).astype(np.uint8)
            _, buf = cv2.imencode('.jpg', fused, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
            return buf.tobytes()

        def _ai_fuse():
            if film_engine is None:
                raise RuntimeError("FILM Fusion engine is not ready")
            return film_engine.fuse_multi(data_list, quality=quality, max_dim=max_dim)

        def _ffmef_fuse():
            if ffmef_engine is None:
                raise RuntimeError("FFMEF engine is not ready")
            if n_images == 2:
                # Single 2-image FFMEF fusion
                fused_bgr = _ffmef_two(data_list[0], data_list[1])
                _, buf = cv2.imencode('.jpg', fused_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
                return buf.tobytes()
            else:
                # Pairwise iteration (FFMEF is 2-input only)
                current = data_list[0]
                for i in range(1, n_images):
                    current = _ffmef_two(current, data_list[i])
                    print(f"[ffmef] Pairwise step {i}/{n_images - 1} done")
                # current is a BGR numpy array from _ffmef_two
                _, buf = cv2.imencode('.jpg', current, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
                return buf.tobytes()

        def _ffmef_two(over_bytes, under_bytes):
            """FFMEF fusion for a single pair of images. Returns BGR numpy array."""
            import torch
            model = ffmef_engine["model"]
            device = ffmef_engine["device"]

            img1 = cv2.imdecode(np.frombuffer(over_bytes, np.uint8), cv2.IMREAD_COLOR)
            img2 = cv2.imdecode(np.frombuffer(under_bytes, np.uint8), cv2.IMREAD_COLOR)
            if img1 is None or img2 is None:
                raise RuntimeError("FFMEF image decode failed")

            y1 = cv2.cvtColor(img1, cv2.COLOR_BGR2YCrCb)[:, :, 0]
            y2 = cv2.cvtColor(img2, cv2.COLOR_BGR2YCrCb)[:, :, 0]

            y1_t = torch.from_numpy(y1.astype(np.float32) / 255.0).unsqueeze(0).unsqueeze(0).to(device)
            y2_t = torch.from_numpy(y2.astype(np.float32) / 255.0).unsqueeze(0).unsqueeze(0).to(device)

            with torch.no_grad():
                fused_y = model(img0_RGB=None, img0_Y=y1_t, img1_RGB=None, img1_Y=y2_t)
                fused_y = fused_y.clamp(0, 1)

            fused_y_np = (fused_y.squeeze(0).squeeze(0).cpu().numpy() * 255.0).astype(np.uint8)

            cb1 = cv2.cvtColor(img1, cv2.COLOR_BGR2YCrCb)[:, :, 1]
            cr1 = cv2.cvtColor(img1, cv2.COLOR_BGR2YCrCb)[:, :, 2]
            cb2 = cv2.cvtColor(img2, cv2.COLOR_BGR2YCrCb)[:, :, 1]
            cr2 = cv2.cvtColor(img2, cv2.COLOR_BGR2YCrCb)[:, :, 2]
            cb_f = ((cb1.astype(np.float32) + cb2.astype(np.float32)) / 2).astype(np.uint8)
            cr_f = ((cr1.astype(np.float32) + cr2.astype(np.float32)) / 2).astype(np.uint8)

            fused_ycrcb = cv2.merge([fused_y_np, cb_f, cr_f])
            fused_rgb = cv2.cvtColor(fused_ycrcb, cv2.COLOR_YCrCb2BGR)
            return fused_rgb

        # ---------- run all 5 algorithms ----------
        _run_algo("ai", _ai_fuse)
        _run_algo("ffmef", _ffmef_fuse)
        _run_algo("avg", _traditional_avg)
        _run_algo("max", _traditional_max)
        _run_algo("mertens", _traditional_mertens)

        return {"results": results}

    except HTTPException:
        raise
    except Exception as e:
        print("[ERROR] 多算法对比发生错误：")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history", summary="获取历史处理记录")
async def get_history():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, algo, img_url, time, en, sd, sf, ag, vif, qabf FROM history ORDER BY id DESC LIMIT 20")
        rows = c.fetchall()
        conn.close()

        history_list = []
        for row in rows:
            history_list.append({
                "id": row[0],
                "algo": row[1],
                "fused": row[2],
                "time": row[3],
                "metrics": {"EN": row[4], "SD": row[5], "SF": row[6], "AG": row[7], "VIF": row[8], "Qabf": row[9]}
            })
        return {"code": 200, "data": history_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=False)
