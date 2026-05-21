import torch
import torchvision.transforms as transforms
from PIL import Image
import io
import os
from typing import List
from collections import OrderedDict

from net.Film import Net


class MEFFusionEngine:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"正在初始化 MEF 引擎，使用设备: {self.device}")

        # 1. 实例化模型 (无文本依赖)
        self.model = Net(mid_channel=32)

        # 2. 加载并清洗权重 (去除 module. 前缀)
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "MEF.pth")
        checkpoint = torch.load(model_path, map_location=self.device)

        state_dict = checkpoint['model'] if 'model' in checkpoint else (
            checkpoint['state_dict'] if 'state_dict' in checkpoint else checkpoint
        )

        new_state_dict = OrderedDict()
        for k, v in state_dict.items():
            name = k[7:] if k.startswith('module.') else k
            new_state_dict[name] = v

        self.model.load_state_dict(new_state_dict)
        self.model.eval()
        self.model.to(self.device)

        self.transform = transforms.ToTensor()
        print("MEF 引擎完全就绪！")

    def fuse(self, over_bytes: bytes, under_bytes: bytes, quality: int = 95, max_dim: int = 1024) -> bytes:
        # 1. 读取并直接转换为 YCbCr 格式
        img_over_rgb = Image.open(io.BytesIO(over_bytes)).convert('RGB')
        img_under_rgb = Image.open(io.BytesIO(under_bytes)).convert('RGB')

        # 2. 自动缩放超大图片，防止 GPU 显存溢出
        w, h = img_over_rgb.size
        if w > max_dim or h > max_dim:
            scale = max_dim / max(w, h)
            new_w, new_h = int(w * scale), int(h * scale)
            new_w = new_w if new_w % 2 == 0 else new_w - 1
            new_h = new_h if new_h % 2 == 0 else new_h - 1
            img_over_rgb = img_over_rgb.resize((new_w, new_h), Image.LANCZOS)
            img_under_rgb = img_under_rgb.resize((new_w, new_h), Image.LANCZOS)

        img_over_ycbcr = img_over_rgb.convert('YCbCr')
        img_under_ycbcr = img_under_rgb.convert('YCbCr')

        # 3. 分离 Y / Cb / Cr
        y_over, cb_over, cr_over = img_over_ycbcr.split()
        y_under, cb_under, cr_under = img_under_ycbcr.split()

        # 4. 只有 Y 通道送入神经网络
        tensor_over = self.transform(y_over).unsqueeze(0).to(self.device)
        tensor_under = self.transform(y_under).unsqueeze(0).to(self.device)

        with torch.no_grad():
            fused_y_tensor = self.model(tensor_over, tensor_under)[0]

        # 后处理：clamp 到 [0, 1]（网络输出已是 sigmoid）
        fused_y_tensor = torch.clamp(fused_y_tensor, 0, 1)
        fused_y_tensor = fused_y_tensor.squeeze(0).cpu()
        fused_y_img = transforms.ToPILImage()(fused_y_tensor)

        # 5. 色度通道 0.5 加权平均
        fused_cb = Image.blend(cb_over, cb_under, alpha=0.5)
        fused_cr = Image.blend(cr_over, cr_under, alpha=0.5)

        # 6. 合并 YCbCr → RGB
        fused_ycbcr = Image.merge('YCbCr', (fused_y_img, fused_cb, fused_cr))
        fused_rgb = fused_ycbcr.convert('RGB')

        output_buffer = io.BytesIO()
        fused_rgb.save(output_buffer, format="JPEG", quality=quality)
        return output_buffer.getvalue()

    def fuse_multi(self, image_bytes_list: List[bytes], quality: int = 95, max_dim: int = 1024) -> bytes:
        """Pairwise iterative fusion for N>2 images."""
        if len(image_bytes_list) < 2:
            raise ValueError("At least 2 images required for fusion")
        if len(image_bytes_list) == 2:
            return self.fuse(image_bytes_list[0], image_bytes_list[1], quality=quality, max_dim=max_dim)

        current = image_bytes_list[0]
        for i in range(1, len(image_bytes_list)):
            current = self.fuse(current, image_bytes_list[i], quality=quality, max_dim=max_dim)
            print(f"[fuse_multi] Pairwise step {i}/{len(image_bytes_list) - 1} done")

        return current
