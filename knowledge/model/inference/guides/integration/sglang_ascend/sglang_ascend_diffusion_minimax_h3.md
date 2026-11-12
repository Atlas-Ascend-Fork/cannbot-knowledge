---
type: Guide
title: SGLang Diffusion MiniMax-H3：NPU全循环、packed attention与VAE门控
description: 说明全去噪循环NPU入口、与LASER的真实token边界配合及VAE SiluAndMul，避免从导入推导完整模型验证。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/pipelines_core/stages/model_specific_stages/minimax_h3/stages/denoising.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/models/vaes/minimax_h3_video_vae/base_module.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/pipelines_core/stages/model_specific_stages/minimax_h3/keyframe_encoding.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/test/unit/test_minimax_h3_denoise_loop.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/pipelines_core/stages/denoising.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/pipelines_core/stages/model_specific_stages/minimax_h3/denoise_loop.py
  role: implementation
created_at: '2026-11-08T12:27:30Z'
updated_at: '2026-11-09T04:32:43Z'
platforms: []
---

# SGLang Diffusion MiniMax-H3：NPU全循环、packed attention与VAE门控

## 推理适配

MiniMax-H3全去噪循环的device guard允许NPU，并与packed真实token/填充边界、共享cache和编译路径配合；源码的编译对象是DiT/transformer模块或其子模块，denoise_loop仍由Python逐步调用模型；逐步模型执行与完整去噪循环的端到端验证属于不同层次，不能据此声称整个循环已捕获或编译。LASER的H3特殊varlen分支只处理used段，padding输出置零，BF16范围缩放需要保持QK与V两组补偿。

VAE gated SiLU在NPU通过SiluAndMul实现，CUDA的特殊舍入kernel不是NPU分支；门控输入最后维切分及输出dtype要与VAE残差一致。keyframe encoding中的NPU探测或设备分配本身不建立完整编码器兼容矩阵。

## 接入与验收

先eager逐步对齐真实token位置、噪声/时间步、cache更新与输出序列，再启用DiT/transformer编译，并对完整去噪循环做端到端验证，检查多输出与keyframe条件。验证VAE门控、超范围BF16、padding与长视频质量；同时记录编译首轮、稳态与内存。出现差异先分离全循环和attention优化定位，本次未运行上游代码或模型，不声明完整Device闭包。
