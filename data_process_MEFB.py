import os
from utils.img_read_save import image_read_cv2
import h5py
import numpy as np
from tqdm import tqdm
import cv2

# ===================== 配置 =====================
img_text_path = 'VLFDataset'
h5_path = "VLFDataset_h5"
os.makedirs(h5_path, exist_ok=True)

task_name = 'MEF'
dataset_name = 'MEFB'
dataset_mode = 'train'
size = 'small'

h5_file_path = os.path.join(h5_path, dataset_name + '_' + dataset_mode + '.h5')
small_size_0 = (384, 288)
small_size_1 = (288, 384)

# ===================== 自动读取图片，不需要txt！=====================
img_dir = os.path.join(img_text_path, 'Image', task_name, dataset_name, 'OVER')
sample_names = [os.path.splitext(f)[0] for f in os.listdir(img_dir) if f.endswith('.png')]
# ===================================================================

with h5py.File(h5_file_path, 'w') as h5_file:
    imageA = h5_file.create_group('imageA')
    imageB = h5_file.create_group('imageB')
    text = h5_file.create_group('text')

    for sample_name in tqdm(sample_names):
        try:
            if dataset_mode == 'train' and size == 'small':
                img_A = image_read_cv2(os.path.join(img_text_path, 'Image', task_name, dataset_name, 'OVER', sample_name + '.png'), mode='GRAY')
                h, w = img_A.shape
                if h < w:
                    img_A = cv2.resize(img_A, small_size_0)[None, ...] / 255.0
                    img_B = cv2.resize(image_read_cv2(os.path.join(img_text_path, 'Image', task_name, dataset_name, 'UNDER', sample_name + '.png'), mode='GRAY'), small_size_0)[None, ...] / 255.0
                else:
                    img_A = cv2.resize(img_A, small_size_1).T[None, ...] / 255.0
                    img_B = cv2.resize(image_read_cv2(os.path.join(img_text_path, 'Image', task_name, dataset_name, 'UNDER', sample_name + '.png'), mode='GRAY'), small_size_1).T[None, ...] / 255.0
            else:
                img_A = image_read_cv2(os.path.join(img_text_path, 'Image', task_name, dataset_name, 'OVER', sample_name + '.png'), mode='GRAY')[None, ...] / 255.0
                img_B = image_read_cv2(os.path.join(img_text_path, 'Image', task_name, dataset_name, 'UNDER', sample_name + '.png'), mode='GRAY')[None, ...] / 255.0

            text_feature = np.load(os.path.join(img_text_path, 'TextFeature', task_name, dataset_name, sample_name + '.npy'))
            imageA.create_dataset(sample_name, data=img_A)
            imageB.create_dataset(sample_name, data=img_B)
            text.create_dataset(sample_name, data=text_feature)
        except Exception as e:
            print(f"跳过 {sample_name}，原因：{e}")
            continue