---
type: Guide
title: SGLang 昇腾 compressed-tensors 的可用 scheme 与限制
description: 按 Dense、动态 INT8/INT4 MoE、WNA16 和 MXFP4 分支解释配置选择，避免沿用 GPU scheme。
tags:
- task.implementation
- topic.compute.quantization
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/compressed_tensors/compressed_tensors.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/compressed_tensors/schemes/compressed_tensors_w8a8_int8.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/compressed_tensors/schemes/compressed_tensors_w8a8_int8_moe.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/compressed_tensors/schemes/compressed_tensors_w4a8_int8_moe.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/compressed_tensors/schemes/compressed_tensors_wNa16_moe.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/quantization/compressed_tensors/schemes/compressed_tensors_w4a8_mxfp4_moe.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/quantization/moe_methods.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:35:32Z'
platforms: []
---

# SGLang 昇腾 compressed-tensors 的可用 scheme 与限制

## scheme 选择与拒绝条件

compressed-tensors 依据目标层、weight/input quant 参数及 ignore 配置选 scheme。NPU 的 MXFP4 MoE 必须在普通整数 INT4 检测前识别，并跳过 GPU Mxfp4MoEMethod；同一 MoE 的 gate/up/down 配置组必须一致，正常scheme选择路径中ignored层回退全精度；Dense若配置linear_fp8_config，则在get_linear_scheme和ignore判断前直接选择Fp8LinearMethod，属于允许的混合量化分支，不能套用该回退结论。

Dense W8A8 的 NPU 类只实现动态输入量化；静态输入量化因缺少所需 quant_bias 明确抛 NotImplementedError。INT8 MoE 则要求 channelwise 权重量化和 dynamic per-token 激活，不接受静态 input scale。

NPU W4A8 INT8 MoE 的当前类固定 group_size=0、tp_size=1，支持 activation_use_clip 与对应补偿参数，不能套用 ModelSlim 的任意 per-group 能力。无input quant的整数INT4 expert还须为静态权重、CHANNEL或GROUP strategy且symmetric=True，才可在此NPU分支选择W4A16/WNA16，使用 INT32 packed 权重、group scales/offsets 和 BF16 激活。

MXFP4 MoE 以 `_packed` 名称加载 uint8 payload，w13 `[E,2I,H/2]`、w2 `[E,H,I/2]`，scale 为每 32 值一个 E8M0 byte；加载后改名为 kernel 所需参数并进行 NZ/scale 转换，A8 为 MXFP8。

## 适配检查

先核对配置被分到的实际 scheme，检查拒绝条件而非只看 quant_method 字符串。分别验证 input scale 的动态性、packed 参数是否完整加载、offset 和 bias 是否存在，再比较逐层输出与 logits。恢复全精度或改导出配置需要重新加载。源码分支不构成所有芯片/导出工具版本的兼容承诺，本卡保持 draft。
