import sys
import os
import sklearn

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
sys.path.append(os.getcwd())
import numpy as np
import torch
import torch.nn as nn
from utils.img_read_save import img_save
import warnings

warnings.filterwarnings("ignore")
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
from torch.utils.data import DataLoader
from net.Film import Net
from tqdm import tqdm
from utils.Evaluator import Evaluator

# ===================== 任务配置 =====================
task_name = 'MEF'
dataset_name = 'MEFB'
# ====================================================

from utils.H5_read import H5ImageTextDataset

testloader = DataLoader(H5ImageTextDataset(os.path.join('VLFDataset_h5', dataset_name + '_test.h5')),
                        batch_size=1, shuffle=False, num_workers=0)

ckpt_path = os.path.join("models", task_name + '.pth')
save_path = os.path.join("test_output", dataset_name, "Gray")
os.makedirs(save_path, exist_ok=True)

device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = Net(hidden_dim=256, image2text_dim=32).to(device)
model = nn.DataParallel(model)

model.load_state_dict(torch.load(ckpt_path)['model'])
model.eval()


class Metrics:
    """使用 utils/Evaluator.py 统一计算所有指标，包括 VIF 和 Qabf"""
    def __init__(self):
        self.en_list = []
        self.sd_list = []
        self.sf_list = []
        self.ag_list = []
        self.vif_list = []
        self.qabf_list = []

    def process(self, fuse, src_a, src_b):
        fuse_float = fuse.astype(np.float32)
        src_a_float = src_a.astype(np.float32)
        src_b_float = src_b.astype(np.float32)

        self.en_list.append(Evaluator.EN(fuse_float))
        self.sd_list.append(Evaluator.SD(fuse_float))
        self.sf_list.append(Evaluator.SF(fuse_float))
        self.ag_list.append(Evaluator.AG(fuse_float))
        self.vif_list.append(Evaluator.VIF(fuse_float, src_a_float, src_b_float))
        self.qabf_list.append(Evaluator.Qabf(fuse_float, src_a_float, src_b_float))

    def get_result(self):
        return {
            "EN": np.mean(self.en_list),
            "SD": np.mean(self.sd_list),
            "SF": np.mean(self.sf_list),
            "AG": np.mean(self.ag_list),
            "VIF": np.mean(self.vif_list),
            "Qabf": np.mean(self.qabf_list)
        }


metrics = Metrics()

print("\n开始测试...\n")

with torch.no_grad():
    for i, (data_IR, data_VIS, text, index) in tqdm(enumerate(testloader), total=len(testloader)):
        text = text.squeeze(1).cuda()
        data_IR = torch.FloatTensor(data_IR).cuda()
        data_VIS = torch.FloatTensor(data_VIS).cuda()

        data_Fuse = model(data_IR, data_VIS, text)[0]

        data_Fuse = (data_Fuse - torch.min(data_Fuse)) / (torch.max(data_Fuse) - torch.min(data_Fuse))
        fi = np.squeeze((data_Fuse * 255).detach().cpu().numpy()).astype('uint8')

        img_save(fi, index[0], save_path)

        ir_np = np.squeeze((data_IR * 255).detach().cpu().numpy()).astype('uint8')
        vis_np = np.squeeze((data_VIS * 255).detach().cpu().numpy()).astype('uint8')
        metrics.process(fi, ir_np, vis_np)

print("\n" + "=" * 80)
print("The test result of SICE:")
print(f"                 EN      SD      SF      AG      VIF     Qabf    ")
res = metrics.get_result()
print(
    f"FILM            {res['EN']:<7.2f}{res['SD']:<7.2f}{res['SF']:<7.2f}{res['AG']:<7.2f}{res['VIF']:<7.2f}{res['Qabf']:<7.2f}")
print("=" * 80)
