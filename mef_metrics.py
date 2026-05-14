import numpy as np


class ImageMetrics:
    """
    图像融合客观评价指标计算工具类
    所有指标计算基于单通道（灰度）图像
    """

    @staticmethod
    def EN(img):
        """信息熵 (Entropy): 衡量图像包含的信息量大小"""
        hist = np.histogram(img, bins=256, range=(0, 255))[0]
        hist = hist / hist.sum()
        hist = hist[hist > 0]
        return -np.sum(hist * np.log2(hist))

    @staticmethod
    def SD(img):
        """标准差 (Standard Deviation): 衡量图像像素对比度和分布的离散程度"""
        return float(np.std(img))

    @staticmethod
    def SF(img):
        """空间频率 (Spatial Frequency): 反映图像灰度变化率，值越大边缘细节越丰富"""
        gx = np.diff(img, axis=1)
        gy = np.diff(img, axis=0)
        return float(np.sqrt(np.mean(gx ** 2) + np.mean(gy ** 2)))

    @staticmethod
    def AG(img):
        """平均梯度 (Average Gradient): 反映图像微小细节反差和纹理变化特征"""
        gx = np.abs(np.diff(img, axis=1))
        gy = np.abs(np.diff(img, axis=0))
        min_h = min(gx.shape[0], gy.shape[0])
        min_w = min(gx.shape[1], gy.shape[1])
        gx = gx[:min_h, :min_w]
        gy = gy[:min_h, :min_w]
        return float(np.mean((gx + gy) / 2))

    @classmethod
    def evaluate(cls, img_array):
        """
        统一评估接口
        :param img_array: numpy 数组格式的灰度图像 (uint8)
        :return: 包含各项指标的字典
        """
        img_float = img_array.astype(np.float32)
        return {
            "EN": round(cls.EN(img_float), 4),
            "SD": round(cls.SD(img_float), 4),
            "SF": round(cls.SF(img_float), 4),
            "AG": round(cls.AG(img_float), 4)
        }
