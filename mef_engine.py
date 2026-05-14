import torch
import torchvision.transforms as transforms
from PIL import Image
import io
import os
from collections import OrderedDict

# 从原工程导入相关模块
from net.Film import Net
from torch.utils.data import DataLoader
from utils.H5_read import H5ImageTextDataset


class MEFFusionEngine:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"正在初始化 MEF 引擎，使用设备: {self.device}")

        # 1. 实例化模型 (从 net.Film 导入)
        self.model = Net(hidden_dim=256, image2text_dim=32)

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

        # 3. 【终极修复】提前提取文本特征张量
        print("正在从数据集提取固定 Text Prompt Tensor...")
        dataset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "VLFDataset_h5", "MEFB_test.h5")
        testloader = DataLoader(H5ImageTextDataset(dataset_path), batch_size=1, shuffle=False)

        # 只需要取第一条数据的 text 即可，因为 MEF 任务的文本提示是一样的
        self.text_tensor = None
        for _, _, text, _ in testloader:
            self.text_tensor = text.squeeze(1).to(self.device)
            break
        if self.text_tensor is None:
            raise RuntimeError(f"No text prompt tensor found in {dataset_path}")

        self.transform = transforms.ToTensor()
        print("MEF 引擎完全就绪！")

    def fuse(self, over_bytes: bytes, under_bytes: bytes) -> bytes:
        # 1. 读取并直接转换为 YCbCr 格式
        img_over_rgb = Image.open(io.BytesIO(over_bytes)).convert('RGB')
        img_under_rgb = Image.open(io.BytesIO(under_bytes)).convert('RGB')

        img_over_ycbcr = img_over_rgb.convert('YCbCr')
        img_under_ycbcr = img_under_rgb.convert('YCbCr')

        # 2. 分离出 Y (亮度), Cb (蓝差), Cr (红差) 通道
        y_over, cb_over, cr_over = img_over_ycbcr.split()
        y_under, cb_under, cr_under = img_under_ycbcr.split()

        # 3. 只有 Y 通道（单通道）送入神经网络！
        tensor_over = self.transform(y_over).unsqueeze(0).to(self.device)
        tensor_under = self.transform(y_under).unsqueeze(0).to(self.device)

        with torch.no_grad():
            fused_y_tensor = self.model(tensor_over, tensor_under, self.text_tensor)[0]

        # 后处理：归一化并转回单通道 PIL 图像
        min_val = torch.min(fused_y_tensor)
        max_val = torch.max(fused_y_tensor)
        fused_y_tensor = (fused_y_tensor - min_val) / torch.clamp(max_val - min_val, min=1e-8)
        fused_y_tensor = fused_y_tensor.squeeze(0).cpu()
        fused_y_img = transforms.ToPILImage()(fused_y_tensor)

        # 4. 色度通道融合：采用最经典的加权平均策略 (alpha=0.5)
        fused_cb = Image.blend(cb_over, cb_under, alpha=0.5)
        fused_cr = Image.blend(cr_over, cr_under, alpha=0.5)

        # 5. 将深度学习处理的 Y，与传统处理的 Cb, Cr 重新合并
        fused_ycbcr = Image.merge('YCbCr', (fused_y_img, fused_cb, fused_cr))

        # 6. 转回前端需要的 RGB 图像
        fused_rgb = fused_ycbcr.convert('RGB')

        output_buffer = io.BytesIO()
        fused_rgb.save(output_buffer, format="JPEG")
        return output_buffer.getvalue()
