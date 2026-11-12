---
type: Guide
title: SGLang Diffusion在线MXFP4：加载期双层量化与实验边界
description: 说明mxfp4_npu区别于ROCm mxfp4，950硬件门槛、NZ后处理和CPU offload下的加载峰值。
tags:
- task.implementation
- topic.diffusion
- topic.precision
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/layers/quantization/mxfp4_npu.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/sglang-diffusion/quantization.mdx
  role: implementation
created_at: '2026-11-08T12:26:55Z'
updated_at: '2026-11-08T12:34:39Z'
platforms:
- '950'
---

# SGLang Diffusion在线MXFP4：加载期双层量化与实验边界

## 选择和硬件

mxfp4_npu供Ascend在线量化，mxfp4名称保留ROCm/aiter。加载FP16/BF16原权重，通过npu_dynamic_dual_level_mx_quant生成packed权重和双层scale；文档明确950PR/DT或更新，A2/A3没有相应dynamic dual-level和matmul算子。在线权重量化是experimental，离线校准可能得到不同数值，不应互换结果。

## 生命周期

post-load将weight移至NPU、转NZ格式29并排好L0 scale，即使常驻策略是CPU offload也会产生一次设备量化与峰值。前向展平activation，动态量化后调用双层matmul；此处weight传法与离线MXFP8的显式转置不同，不能统一修改。恢复输出原shape；FP16/BF16输入保留其dtype，其他输入转BF16并以BF16输出。

文档已明确在线加载原浮点权重，部分源码/CLI注释仍称只支持预量化，属于版本内描述冲突，应按具体类与实际加载器核对。先保留未量化权重基线，记录加载峰值、每层scale和输出质量，再比较执行延迟；失败恢复浮点或已验收离线模型。本次未运行量化、加载或性能测试。
