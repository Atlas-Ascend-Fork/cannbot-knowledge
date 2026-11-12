---
type: Guide
title: SGLang Diffusion离线MXFP4：双层scale契约与当前源码缺陷
description: 保留packed权重和smooth scale流程，并明确未定义属性及无mul_scale访问使固定版本不能直接当运行配方。
tags:
- task.implementation
- topic.diffusion
- topic.precision
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/layers/quantization/modelslim_mxfp4_scheme.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/sglang-diffusion/quantization.mdx
  role: implementation
created_at: '2026-11-08T12:26:55Z'
updated_at: '2026-11-09T04:32:21Z'
platforms: []
---

# SGLang Diffusion离线MXFP4：双层scale契约与当前源码缺陷

## 预期数据契约

ModelSlim区分单层与DUALSCALE；weight按uint8[out,in/2]分配，weight_scale为uint8[out,in/32]，双层FP32 scale为[out,in/512,1]，post-load后packed FP4权重转NZ格式29，L1 reshape为[out,in/64,2]，L0转置。smooth mul_scale为FP32[in]，有效时必须在activation动态量化之前应用。

双层分支调用 npu_dynamic_dual_level_mx_quant 与 npu_dual_level_quant_matmul；固定文档限定这两个接口要求 Ascend 950PR/DT 或更新硬件，不支持 A2/A3。修复下述元数据/属性问题也不能解除此硬件限制。双层前向将activation与weight的L0/L1 scale按npu_dual_level_quant_matmul约定传入，bias转FP32并恢复输出shape；FP16/BF16输入保留其dtype，其他输入先转BF16且original_dtype重设为BF16，因此原FP32输入不会恢复FP32；单层复用SRT方案。文档称FP8 container而本文件分配uint8，不能以注释替代实际checkpoint加载契约。

## 固定版本的具体缺陷

构造函数定义dual_scale_key后却读取self.is_dual_scale_key，本类未定义该属性，双层初始化可触发AttributeError。has_mul_scale还要求旧.div.mul_scale与新.mul_scale两个键同时存在；前向双层分支在检查是否使用之前直接读取layer.mul_scale，无该参数可再次AttributeError。这些是静态控制流推断，本次没有执行报错复现。

因此本卡保留实现reference，不能当作该版本已可用的离线MXFP4部署教程。接入前先确认上述硬件和接口可用性，再修复并验证元数据键、缺smooth项、两层scale尺寸、NZ格式及数值，再比较离线校准基线；临时采用已验收浮点或其他量化路径，不能通过伪造参数掩盖加载失败。

## 配套知识

[ModelSlim分派](sglang_ascend_diffusion_modelslim.md)；[在线MXFP4边界](sglang_ascend_diffusion_mxfp4_online.md)。
