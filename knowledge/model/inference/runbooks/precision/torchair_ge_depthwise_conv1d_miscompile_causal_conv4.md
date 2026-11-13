---
{
  "type": "Runbook",
  "title": "TorchAir/GE depthwise Conv1D 错译致整模 GE 偏差：layer0 probe 判别（Conv1D 转换 relL2=1.077 而同图 MatMul/shift 形式逐位正确）",
  "description": "StartLux（Qwen3.5 结构）整模 GE 输出严重偏离 CPU/NPU eager。最小真实权重 layer0 probe 判别：in_proj_qkv MatMul 逐位正确（relL2=0），GE Conv1D（C=6144, groups=C, kernel=4, padding=3）relL2=1.077/maxabs=20.25 且 contiguous 输入同错（排除布局），4-tap shift 形式逐位正确。",
  "tags": [
    "task.debugging",
    "topic.precision"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# TorchAir/GE depthwise Conv1D 错译致整模 GE 偏差：layer0 probe 判别（Conv1D 转换 relL2=1.077 而同图 MatMul/shift 形式逐位正确）

## 适用场景

StartLux（Qwen3.5 结构）整模 GE 输出严重偏离 CPU/NPU eager。最小真实权重 layer0 probe 判别：in_proj_qkv MatMul 逐位正确（relL2=0），GE Conv1D（C=6144, groups=C, kernel=4, padding=3）relL2=1.077/maxabs=20.25 且 contiguous 输入同错（排除布局），4-tap shift 形式逐位正确。

适用于 TorchAir/torch_npu 导出 GE 图后整模输出与 CPU/NPU eager 出现严重数值偏差（cos 为负/relL2≈1 量级）的精度排查，尤其是含 depthwise 短卷积（groups=C、kernel=4、padding=3）的 GDN/线性注意力模型（StartLux/Qwen3.5 结构）。

## 触发与观测

整模 GE scores 严重偏离 CPU/NPU eager；逐层 trace 显示 embed 逐位正确、layer0 首个偏差（relL2 2.287）、beta/g/g_cumsum/decay 逐位正确——偏差恰从 conv 阶段进入。

### 结论与证据边界

TorchAir/GE 对 depthwise Conv1D（C=6144, groups=C, kernel=4, padding=3）的转换在真实权重 layer0 上错译：GE conv 相对 NPU eager relL2=1.077、maxabs=20.25（conv_silu 路径 1.363），而同一 probe 中 in_proj_qkv MatMul 逐位正确（relL2=0、maxabs=0）、4-tap shift_silu 形式逐位正确（relL2=0）；contiguous 输入 conv_contig 同样 relL2=1.077，排除非连续布局根因，是 Conv1D 转换本身错误；layer-trace 显示 embed 逐位正确、layer0 首个偏差（relL2 2.287）、beta/g/g_cumsum/decay 逐位正确，偏差恰从 conv 阶段进入。

## 探针与操作

最小真实权重 layer0 QKVConvProbe（debug_qkv_conv.py）：用真实 in_proj_qkv 权重与真实 ln0*pad hidden state [1,256,1024] BF16，分别对 qkv 投影、原 Conv1d、Conv1d+SiLU、4-tap shift+SiLU、conv_contig 做小图 GE vs NPU eager 对照。

## 机制与判别

见上方结论原文与下方机制片段；判别性证据与边界适用讨论见“适用与失效边界”节。

### 补充机制片段

```
eager qkv (1, 6144, 256) 31.875
eager conv (1, 6144, 259) 20.25
eager conv_silu (1, 6144, 256) 9.9375
eager shift_silu (1, 6144, 256) 9.9375
runtime status: success
      output        relL2       maxabs
         qkv    0.000e+00    0.000e+00
        conv    1.077e+00    2.026e+01
   conv_silu    1.363e+00    1.005e+01
  shift_silu    0.000e+00    0.000e+00
eager shift_silu vs conv_silu: relL2 0.000e+00 maxabs 0.000e+00
```

## 验证信号

probe 输出 relL2/maxabs 表（qkv=0、conv=1.077、conv_contig=1.077、shift_silu=0、eager shift vs conv_silu=0）。

## 适用与失效边界

适用：TorchAir/GE 对该 depthwise Conv1D 配置（contiguous 与 transposed 输入同错，排除布局）的转换错译判别。局限：本卡止于错译定位；GE Conv1D 转换器本身的修复未在本轨迹内完成。
