---
type: Guide
title: SGLang Diffusion NPU激活与Norm：融合、缓存和TP归约
description: 说明SwiGLU/GEGLU、FP32 LayerNorm缓存、残差调制与跨TP RMSNorm不可省略的归约。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/layers/layernorm.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/layers/activation.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/layers/elementwise.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/layers/custom_op.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/rmsnorm_without_weight.py
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/rmsnorm_split.py
  role: constraint
created_at: '2026-11-08T12:26:54Z'
updated_at: '2026-11-09T04:32:54Z'
platforms: []
---

# SGLang Diffusion NPU激活与Norm：融合、缓存和TP归约

## 调用与精度

CustomOp初始化时固定forward分派，out-of-tree实现优先；没有专门NPU函数时forward_npu回到native。SiluAndMul用npu_swiglu，GEGLU用npu_geglu的approximate=0/1和activate_left=True，输入最后一维拆为等宽两半。MulAdd的NPU路径调用fused_scale_shift并传scale_constant，不宜直接套用native的按帧广播假设。

RMSNorm用npu_rms_norm或npu_add_rms_norm，残差融合路径返回更新残差；deterministic开关可强制native。无weight版本直接使用外部 fused_rmsnorm_without_weight；与本知识库固定 kernel 快照配套时，输入须为连续三维 `[B,L,C]` 且 C 为正的2次幂，kernel按连续地址和 tl.arange(0,C) 读取，没有自动native回退。不能套用 forward_native 的一般前导维度或非连续输入支持，见[无权重RMSNorm接口](../../../apis/sgl_kernel_npu/sgl_rmsnorm_without_weight.md)。FP32LayerNorm依赖attentions，缺包走native；缓存FP32权重/bias的key包含data_ptr、_version、device和dtype，grad模式跳过缓存，不能用对象身份代替版本检查。

## 调制和并行

gated residual仅支持约定gate形态；norm后scale/shift满足标量/hidden/完整shape约束才融合，否则Torch广播。TP RMSNorm先以FP32计算local variance，经TP组AVG，再rsqrt与本地weight相乘并转回输入dtype；各rank通道分片必须等宽，局部均方的AVG才等于全局均方；单rank本地RMS不等价于全局head归一化。与固定kernel快照配套的NPU局部统计要求连续 `[B,L,C]`、局部 C 为正的2次幂；转成FP32不会补齐布局或通道约束，见[TP RMSNorm统计接口](../../../apis/sgl_kernel_npu/sgl_tp_rmsnorm_statistics.md)。QK norm+RoPE中的某些fused guard属于CUDA，不能从共同helper推导NPU全部融合。

适配时固定输出dtype与残差精度，覆盖缓存权重原地更新、非连续输入和TP>1；检查allreduce组/分母及数值。融合减少调用但增加布局、缓存与版本依赖，回退保留native。这里只静态核对，没有比较性能或数值误差。
