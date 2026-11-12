---
type: Guide
title: SGLang Diffusion通用kernel：NPU延迟分派与RoPE回退
description: 区分import时绑定与动态平台键，说明NPU scale-shift、rotary_mul门槛和Torch高精度norm回退。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/diffusion/common/fallback_npu.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/diffusion/common/platform.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/diffusion/common/fallback_torch.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/diffusion/modulate/scale_shift_triton.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/diffusion/rope/rotary_triton.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/diffusion/ext/hunyuan3d_rasterizer/__init__.py
  role: implementation
created_at: '2026-11-08T12:26:53Z'
updated_at: '2026-11-09T04:32:21Z'
platforms: []
---

# SGLang Diffusion通用kernel：NPU延迟分派与RoPE回退

## 平台分派

platform_key不缓存，避免平台插件尚未冻结时记住错误结果；但select_impl会在模块import时选定实现，不能假设修改环境变量会重绑定已导入函数。lazy_fallback首次调用才导入选中模块；平台映射未列出的设备默认取Triton，并不保证该Triton在任意硬件可运行。

## NPU具体实现

scale_shift使用x*(1+scale)+shift的Torch表达式，源码说明NPU Triton版本存在问题；不能给该fallback标为融合kernel。RoPE只在非interleaved、满足cos/x维度条件、head<1000且dim<896时用npu_rotary_mul；半宽cos/sin先扩展。其他情况固定用Torch偶奇通道配对（x[...,::2] 与 x[...,1::2]）并交错写回，即使 interleaved=False 且未命中 npu_rotary_mul 也不会自动改成前后半布局；interleaved全宽cos按偶数项压缩，需保持原布局语义。

Torch norm 的 RMSNorm 分支仅在 bias 存在（即使与输入同 dtype）或非空 weight.dtype!=x.dtype 时显式提升 FP32，防止仿射前提前舍入；无 bias 且 weight 同 dtype 时直接 F.rms_norm。LayerNorm 分支直接调用 F.layer_norm，没有上述统一提升步骤。结果最后回输入dtype；提供out时copy_写回。RMS回退是推理路径，不支持任意dropout/x1组合；residual_in_fp32是独立选项。排障时核对实际函数所属模块、输入stride/dtype、广播方式与out别名，再比较参考输出；本次未运行kernel或编译，不声称完整Device闭包。

## 补充调用与验证边界

Hunyuan3D rasterize对pos.device.type==npu选择CPU，JIT只加载C++源、不加载CUDA文件，将pos/tri/clamp_depth复制到Host，结果再复制回原设备；不是NPU原生光栅化kernel。输入pos若有batch只取pos[0]，输出涉及完整D2H/H2D与Host计算成本。扩展对象为全局单例缓存，混用先后CPU/CUDA初始化还须核对，不能仅据函数名推断任意设备批次兼容。本次未编译该扩展。
