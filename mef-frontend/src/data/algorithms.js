// mef-frontend/src/data/algorithms.js
// Static algorithm information for info cards

export const algorithms = {
  ai: {
    name: 'IF-FILM',
    fullName: 'IF-FILM (深度学习)',
    principle:
      '利用视觉语言模型（ChatGPT + BLIP2）生成的文本语义信息引导图像融合。'
      + '通过跨注意力机制（Cross-Attention）将文本特征与图像特征对齐，'
      + '在 YCbCr 颜色空间中仅对 Y（亮度）通道进行神经网络融合，Cb/Cr 通道采用 0.5 加权平均。',
    citation: {
      title: 'Image Fusion via Vision-Language Model',
      venue: 'ICML 2024',
      year: 2024,
      link: 'https://arxiv.org/abs/2402.02235',
    },
  },
  ffmef: {
    name: 'FFMEF',
    fullName: 'FFMEF (深度学习)',
    principle:
      '基于全卷积神经网络的无参考多曝光图像融合方法。'
      + '采用 U-Net 风格编码器提取多尺度特征，通过空间交叉注意力进行特征加权，'
      + '利用核预测网络（KPN）进行多尺度融合，无需参考图像即可生成高质量融合结果。',
    citation: {
      title: 'FFMEF: Unsupervised Multi-Exposure Image Fusion via Deep Learning',
      venue: 'CVPR Workshop 2023',
      year: 2023,
      link: 'https://openaccess.thecvf.com/content/CVPR2023W/...',
    },
  },
  avg: {
    name: '加权平均',
    fullName: '加权平均 (传统)',
    principle:
      '最简单的图像融合方法：对两张输入图像以相等权重（0.5/0.5）逐像素加权求和。'
      + '计算速度快，无学习参数，但容易丢失高对比度区域的细节信息。',
    citation: null,
  },
  mertens: {
    name: 'Mertens 融合',
    fullName: 'Mertens 融合 (传统)',
    principle:
      '基于曝光融合的经典算法（Mertens et al., 2009）。'
      + '通过评估每张输入图像的对比度、饱和度和良好曝光度三个质量度量，'
      + '构建权重图并进行拉普拉斯金字塔融合，生成高动态范围效果的图像。',
    citation: {
      title: 'Exposure Fusion: A Simple and Practical Alternative to High Dynamic Range Photography',
      venue: 'Computer Graphics Forum, 2009',
      year: 2009,
      link: 'https://doi.org/10.1111/j.1467-8659.2009.01389.x',
    },
  },
  max: {
    name: '最大值',
    fullName: '最大值保留 (传统)',
    principle:
      '逐像素取两张输入图像中的较大值作为输出。'
      + '保留最亮区域的细节，适用于保留高光信息的场景，'
      + '但可能引入不自然的过渡和噪声放大。',
    citation: null,
  },
}
