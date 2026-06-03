import torch
import torchvision.transforms as transforms
from PIL import Image
import io
import os
from typing import List
from collections import OrderedDict

from net.Film import Net
from torch.utils.data import DataLoader
from utils.H5_read import H5ImageTextDataset


class MEFFusionEngine:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"正在初始化 MEF 引擎，使用设备: {self.device}")

        self.model = Net(hidden_dim=256, image2text_dim=32)

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

        print("正在从数据集提取固定 Text Prompt Tensor...")
        dataset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "VLFDataset_h5", "MEFB_test.h5")
        testloader = DataLoader(H5ImageTextDataset(dataset_path), batch_size=1, shuffle=False)

        self.text_tensor = None
        for _, _, text, _ in testloader:
            self.text_tensor = text.squeeze(1).to(self.device)
            break
        if self.text_tensor is None:
            raise RuntimeError(f"No text prompt tensor found in {dataset_path}")

        self.transform = transforms.ToTensor()
        print("MEF 引擎完全就绪！")

    def fuse(self, over_bytes: bytes, under_bytes: bytes, quality: int = 95, max_dim: int = 1024) -> bytes:
        img_over_rgb = Image.open(io.BytesIO(over_bytes)).convert('RGB')
        img_under_rgb = Image.open(io.BytesIO(under_bytes)).convert('RGB')

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

        y_over, cb_over, cr_over = img_over_ycbcr.split()
        y_under, cb_under, cr_under = img_under_ycbcr.split()

        tensor_over = self.transform(y_over).unsqueeze(0).to(self.device)
        tensor_under = self.transform(y_under).unsqueeze(0).to(self.device)

        with torch.no_grad():
            fused_y_tensor = self.model(tensor_over, tensor_under, self.text_tensor)[0]

        min_val = torch.min(fused_y_tensor)
        max_val = torch.max(fused_y_tensor)
        fused_y_tensor = (fused_y_tensor - min_val) / torch.clamp(max_val - min_val, min=1e-8)
        fused_y_tensor = fused_y_tensor.squeeze(0).cpu()
        fused_y_img = transforms.ToPILImage()(fused_y_tensor)

        fused_cb = Image.blend(cb_over, cb_under, alpha=0.5)
        fused_cr = Image.blend(cr_over, cr_under, alpha=0.5)

        fused_ycbcr = Image.merge('YCbCr', (fused_y_img, fused_cb, fused_cr))
        fused_rgb = fused_ycbcr.convert('RGB')

        output_buffer = io.BytesIO()
        fused_rgb.save(output_buffer, format="JPEG", quality=quality)
        return output_buffer.getvalue()

    def fuse_multi(self, image_bytes_list: List[bytes], quality: int = 95, max_dim: int = 1024) -> bytes:
        if len(image_bytes_list) < 2:
            raise ValueError("At least 2 images required for fusion")
        if len(image_bytes_list) == 2:
            return self.fuse(image_bytes_list[0], image_bytes_list[1], quality=quality, max_dim=max_dim)

        pil_images = [Image.open(io.BytesIO(b)).convert('RGB') for b in image_bytes_list]
        base_w, base_h = pil_images[0].size
        if base_w > max_dim or base_h > max_dim:
            scale = max_dim / max(base_w, base_h)
            base_w, base_h = int(base_w * scale), int(base_h * scale)
        base_w = base_w if base_w % 2 == 0 else base_w - 1
        base_h = base_h if base_h % 2 == 0 else base_h - 1
        aligned = [img.resize((base_w, base_h), Image.LANCZOS) for img in pil_images]

        ycbcr_list = [img.convert('YCbCr') for img in aligned]
        y_channels = [ycbcr.split()[0] for ycbcr in ycbcr_list]
        cb_channels = [ycbcr.split()[1] for ycbcr in ycbcr_list]
        cr_channels = [ycbcr.split()[2] for ycbcr in ycbcr_list]

        # Y 通道：tensor 级别逐对神经网络融合，无中间 JPEG 编解码
        current_y = self.transform(y_channels[0]).unsqueeze(0).to(self.device)
        for i in range(1, len(y_channels)):
            next_y = self.transform(y_channels[i]).unsqueeze(0).to(self.device)
            with torch.no_grad():
                current_y = self.model(current_y, next_y, self.text_tensor)
            print(f"[fuse_multi] Y channel step {i}/{len(y_channels) - 1} done")

        min_val = torch.min(current_y)
        max_val = torch.max(current_y)
        current_y = (current_y - min_val) / torch.clamp(max_val - min_val, min=1e-8)
        fused_y_img = transforms.ToPILImage()(current_y.squeeze(0).cpu())

        # Cb/Cr 通道：等权平均
        fused_cb = cb_channels[0]
        for i in range(1, len(cb_channels)):
            fused_cb = Image.blend(fused_cb, cb_channels[i], alpha=1.0 / (i + 1))
        fused_cr = cr_channels[0]
        for i in range(1, len(cr_channels)):
            fused_cr = Image.blend(fused_cr, cr_channels[i], alpha=1.0 / (i + 1))

        fused_ycbcr = Image.merge('YCbCr', (fused_y_img, fused_cb, fused_cr))
        fused_rgb = fused_ycbcr.convert('RGB')

        output_buffer = io.BytesIO()
        fused_rgb.save(output_buffer, format="JPEG", quality=quality)
        return output_buffer.getvalue()
