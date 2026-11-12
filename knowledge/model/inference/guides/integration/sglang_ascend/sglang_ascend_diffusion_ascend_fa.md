---
type: Guide
title: SGLang Diffusion Ascend FA：变长边界、Ring LSE与MXFP8门槛
description: 从BSND/TND布局、空段与LSE规范到950 MXFP8自注意力、正交旋转和head分块，区分普通与量化路线。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/layers/attention/backends/ascend_fa.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/test/unit/test_mxfp8_attention_selection.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/layers/attention/selector.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/server_args/server_args.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/sglang-diffusion/environment_variables.mdx
  role: constraint
created_at: '2026-11-08T12:26:52Z'
updated_at: '2026-11-09T04:31:18Z'
platforms: []
---

# SGLang Diffusion Ascend FA：变长边界、Ring LSE与MXFP8门槛

## 接入与张量契约

普通forward将[B,S,H,D]转BNSD调用FIA，再恢复BSND；LSE为[B,H,S]。packed入口接收TND的Q/K/V与1D int32/int64累计边界，要求首项0、末项等于总token、非递减、Q/K段数一致；K/V的token和head匹配且Q/K维度相同。每段Q/K必须同时空或同时非空，否则NotImplementedError；双空段从实际边界中移除，全空返回empty_like(Q)及[H,Tq] FP32 LSE。可传 cu_seqlens_host 复用已有 Host 边界；只有未提供副本时才调用 cu_seqlens.tolist()，且边界位于设备上时产生设备到 Host 复制及同步成本。Ring chunk 调用显式传入 Host 边界。

packed FIA的actual_seq_lengths传累计终点而非逐段长度；返回[T,H,1] LSE整理为[H,T]。同shape非连续QKV可stack再unbind合并连续化，异shape分别contiguous。Ring chunk明确使用普通BF16变长FIA及LSE，即使量化开关存在也不走MXFP8。

## MXFP8实际选择

需同时满足NPU、量化config为MXFP8Config/ModelSlimConfig、SGLANG_DIFFUSION_ENABLE_MXFP8_ATTENTION开关、soc_version>=260、dynamic_mx_quant/FIA v2及E4M3/E8M0 dtype存在。缺条件保留普通FA；提示要求torch2.10、torch_npu>=2.10.post4、CANN>=9.1.1，这是该特性的依赖，不替代通用安装矩阵。

量化只用于非因果self-attention、相同Q/K/V序列与MHA head、总token可被64整除；cross attention和请求LSE不支持。源输入固定BF16。Q/K沿末维量化mode6，V沿token轴mode8，E4M3 payload配E8M0 scales后调用TND FIA v2并还原dtype。源码支持按head分块降低峰值，但会增加调用和拼接。

## 精度与回退

默认按head_dim以seed42生成CPU FP32 QR正交矩阵，在线旋转Q/K；已标记离线旋转的checkpoint避免重复。正交变换保留实数点积，不保证量化舍入无损。先普通FA固定seed对比，再逐项启用MXFP8、head分块；覆盖空段、非连续输入和Ring LSE合并。本次未运行数值或性能检查；950门槛只约束MXFP8局部分支，不据此扩张整卡平台。

## 补充调用与验证边界

选择优先级是显式函数参数→全局强制→组件角色→组件→ServerArgs→层默认；仅都未选中且非cross时，MXFP8能力探测才自动选FA，不能覆盖用户或模型默认。全局CLI对DiT严格；辅助组件可回退，显式组件覆盖仍严格，稀疏cross回到dense。MiniMax-H3使用LASER且未覆盖text_encoder时自动将其encoder设torch_sdpa，LASER只约束transformer。CLI对mxfp4_npu的“预量化”文字与online类/文档冲突，按具体加载路线核对。

## 文档开关补充

文档默认MXFP8 FA head chunk为4，设0关闭head拆分；该开关默认关闭，unsupported调用保留普通attention。SGLANG_DIFFUSION_PLATFORM_OVERRIDE可选npu/插件，但不安装相应运行时。

## 配套知识

[双源文档与选择策略](../../deployment/sglang_ascend/sglang_ascend_doc_diffusion_attention_versions.md)。
