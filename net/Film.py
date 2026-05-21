import torch
import torch.nn as nn
from net.restormer import TransformerBlock as Restormer
import torch.nn.functional as F


class CrossImageAttention(nn.Module):
    """Cross-image feature exchange: imageA queries imageB and vice versa."""
    def __init__(self, dim, num_heads, ffn_expansion_factor=2, bias=False):
        super().__init__()
        ffn_ch = int(dim * ffn_expansion_factor)
        # Attention params for Q from source A, K/V from source B
        self.qkv_a = nn.Conv2d(dim, dim * 3, kernel_size=1, bias=bias)
        self.qkv_a_dwconv = nn.Conv2d(dim * 3, dim * 3, kernel_size=3, stride=1, padding=1,
                                       groups=dim * 3, bias=bias)
        self.qkv_b = nn.Conv2d(dim, dim * 3, kernel_size=1, bias=bias)
        self.qkv_b_dwconv = nn.Conv2d(dim * 3, dim * 3, kernel_size=3, stride=1, padding=1,
                                       groups=dim * 3, bias=bias)
        self.proj_a = nn.Conv2d(dim, dim, kernel_size=1, bias=bias)
        self.proj_b = nn.Conv2d(dim, dim, kernel_size=1, bias=bias)

        self.num_heads = num_heads
        self.temperature = nn.Parameter(torch.ones(num_heads, 1, 1))

        # Lightweight gating FFN after attention
        self.ffn_in = nn.Conv2d(dim, ffn_ch * 2, kernel_size=1, bias=bias)
        self.ffn_dw = nn.Conv2d(ffn_ch * 2, ffn_ch * 2,
                                 kernel_size=3, stride=1, padding=1,
                                 groups=ffn_ch * 2, bias=bias)
        self.ffn_out = nn.Conv2d(ffn_ch, dim, kernel_size=1, bias=bias)

    def _attn(self, q, k, v):
        b, _, h, w = q.shape
        q = q.reshape(b, self.num_heads, -1, h * w).transpose(-1, -2)  # [B, H, HW, C/H]
        k = k.reshape(b, self.num_heads, -1, h * w).transpose(-1, -2)
        v = v.reshape(b, self.num_heads, -1, h * w).transpose(-1, -2)

        q = F.normalize(q, dim=-1)
        k = F.normalize(k, dim=-1)

        attn = (q @ k.transpose(-2, -1)) * self.temperature
        attn = attn.softmax(dim=-1)
        out = (attn @ v).transpose(-1, -2).reshape(b, -1, h, w)
        return out

    def forward(self, feat_a, feat_b):
        """Cross-image attention: feat_a attends to feat_b, feat_b attends to feat_a."""
        b, _, h, w = feat_a.shape

        # A queries B
        qkv_a = self.qkv_a_dwconv(self.qkv_a(feat_a))
        q_a, k_a, v_a = torch.chunk(qkv_a, 3, dim=1)

        qkv_b = self.qkv_b_dwconv(self.qkv_b(feat_b))
        q_b, k_b, v_b = torch.chunk(qkv_b, 3, dim=1)

        # Cross: A's Q with B's K,V  |  B's Q with A's K,V
        out_a = self._attn(q_a, k_b, v_b)
        out_b = self._attn(q_b, k_a, v_a)

        out_a = self.proj_a(out_a)
        out_b = self.proj_b(out_b)

        # Residual + gating FFN
        out_a = feat_a + self._gdfn(out_a)
        out_b = feat_b + self._gdfn(out_b)

        return out_a, out_b

    def _gdfn(self, x):
        """Gated-Dconv Feed-Forward Network."""
        x = self.ffn_dw(self.ffn_in(x))
        x1, x2 = torch.chunk(x, 2, dim=1)
        x = x1 * F.gelu(x2)
        return self.ffn_out(x)


class restormer_cablock(nn.Module):
    """Dual-branch feature extraction with cross-image attention."""
    def __init__(
            self,
            input_channel=1,
            restormer_dim=32,
            restormer_head=8,
            ffn_expansion_factor=4,
            bias=False,
            LayerNorm_type='WithBias',
    ):
        super().__init__()
        # Branch A
        self.convA1 = nn.Conv2d(input_channel, restormer_dim, kernel_size=3, stride=1, padding=1, bias=bias)
        self.preluA1 = nn.PReLU()
        self.restormerA1 = Restormer(restormer_dim, restormer_head, ffn_expansion_factor, bias, LayerNorm_type)
        # Branch B
        self.convB1 = nn.Conv2d(input_channel, restormer_dim, kernel_size=3, stride=1, padding=1, bias=bias)
        self.preluB1 = nn.PReLU()
        self.restormerB1 = Restormer(restormer_dim, restormer_head, ffn_expansion_factor, bias, LayerNorm_type)

        # Cross-image attention: A <-> B
        self.cross_attn = CrossImageAttention(restormer_dim, restormer_head, bias=bias)

        # Fusion conv: combine original + cross-attended
        self.convA3 = nn.Conv2d(2 * restormer_dim, restormer_dim, kernel_size=1, bias=bias)
        self.preluA3 = nn.PReLU()
        self.convB3 = nn.Conv2d(2 * restormer_dim, restormer_dim, kernel_size=1, bias=bias)
        self.preluB3 = nn.PReLU()

    def forward(self, imageA, imageB):
        if len(imageA.shape) == 3:
            imageA = imageA.cuda().unsqueeze(0).permute(0, 3, 1, 2)
            imageB = imageB.cuda().unsqueeze(0).permute(0, 3, 1, 2)
        _, _, H, W = imageA.shape

        # Stage 1: independent feature extraction
        feat_a = self.restormerA1(self.preluA1(self.convA1(imageA)))
        feat_b = self.restormerB1(self.preluB1(self.convB1(imageB)))

        # Stage 2: cross-image attention
        cross_a, cross_b = self.cross_attn(feat_a, feat_b)

        # Stage 3: fuse original + cross-attended features
        feat_a = F.interpolate(feat_a, [H, W], mode='nearest')
        feat_b = F.interpolate(feat_b, [H, W], mode='nearest')
        cross_a = F.interpolate(cross_a, [H, W], mode='nearest')
        cross_b = F.interpolate(cross_b, [H, W], mode='nearest')

        out_a = self.preluA3(self.convA3(torch.cat((feat_a, cross_a), dim=1)))
        out_b = self.preluB3(self.convB3(torch.cat((feat_b, cross_b), dim=1)))

        return out_a, out_b


class Net(nn.Module):
    """FILM network with Cross-Image Attention (no text dependency)."""
    def __init__(
            self,
            mid_channel=32,
            decoder_num_heads=8,
            ffn_factor=4,
            bias=False,
            LayerNorm_type='WithBias',
            out_channel=1,
            pooling='avg',
            normalization='l1'
    ):
        super().__init__()
        self.restormerca1 = restormer_cablock(restormer_dim=mid_channel, restormer_head=decoder_num_heads,
                                              ffn_expansion_factor=ffn_factor, bias=bias,
                                              LayerNorm_type=LayerNorm_type)
        self.restormerca2 = restormer_cablock(input_channel=mid_channel, restormer_dim=mid_channel,
                                              restormer_head=decoder_num_heads, ffn_expansion_factor=ffn_factor,
                                              bias=bias, LayerNorm_type=LayerNorm_type)
        self.restormerca3 = restormer_cablock(input_channel=mid_channel, restormer_dim=mid_channel,
                                              restormer_head=decoder_num_heads, ffn_expansion_factor=ffn_factor,
                                              bias=bias, LayerNorm_type=LayerNorm_type)
        self.restormer1 = Restormer(2 * mid_channel, decoder_num_heads, ffn_factor, bias, LayerNorm_type)
        self.restormer2 = Restormer(mid_channel, decoder_num_heads, ffn_factor, bias, LayerNorm_type)
        self.restormer3 = Restormer(mid_channel, decoder_num_heads, ffn_factor, bias, LayerNorm_type)
        self.conv1 = nn.Conv2d(2 * mid_channel, mid_channel, kernel_size=1, bias=bias)
        self.conv2 = nn.Conv2d(mid_channel, out_channel, kernel_size=1, bias=bias)
        self.sigmoid = nn.Sigmoid()

    def forward(self, imageA, imageB):
        feature_a, feature_b = self.restormerca1(imageA, imageB)
        feature_a, feature_b = self.restormerca2(feature_a, feature_b)
        feature_a, feature_b = self.restormerca3(feature_a, feature_b)
        fusion_feature = torch.cat((feature_a, feature_b), dim=1)
        fusion_feature = self.restormer1(fusion_feature)
        fusion_feature = self.conv1(fusion_feature)
        fusion_feature = self.restormer2(fusion_feature)
        fusion_feature = self.restormer3(fusion_feature)
        fusion_feature = self.conv2(fusion_feature)
        fusion_feature = self.sigmoid(fusion_feature)
        return fusion_feature
