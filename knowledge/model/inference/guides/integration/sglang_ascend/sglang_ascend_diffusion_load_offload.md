---
type: Guide
title: SGLang Diffusion量化加载与驻留：后处理、CPU offload和释放
description: 串联checkpoint加载设备、一次性量化后处理、NPU内部格式和组件释放，区分加载峰值与推理常驻内存。
tags:
- task.implementation
- topic.diffusion
- topic.memory
- topic.precision
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/utils/quantization_utils.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/loader/component_loaders/transformer_loader.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/loader/transformer_load_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/managers/memory_managers/component_manager.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/pipelines_core/executors/pipeline_executor.py
  role: implementation
created_at: '2026-11-08T12:26:56Z'
updated_at: '2026-11-09T04:32:21Z'
platforms: []
---

# SGLang Diffusion量化加载与驻留：后处理、CPU offload和释放

## 触发顺序

process_model_weights_after_loading 遍历 native 及 SRT Linear/Embedding；quantized_only 默认 False，仅显式 True 时跳过非量化方法，quant_method=None 的模块始终跳过。调用侧负责一次性后处理安排。NPU量化启用allow_internal_format；需要process_device时逐模块暂时搬到目标设备，处理后可搬回并empty_cache。低常驻内存不代表加载期没有NPU峰值。

transformer loader只有组件计划起始在CPU且方法支持CPU加载时才把checkpoint读到CPU，否则读到设备。modelopt-fp8、comfy、auto-round、mxfp8的某些路线要求设备后处理；fp8、mxfp4、mxfp4_npu还受serialized状态影响，不应统一强制CPU。在线量化前后的tensor格式与storage owner需保持一致。

## 组件生命周期

ComponentManager支持NPU常驻与offload。释放大NPU组件storage时可抑制empty_cache以避免清空缓存开销；layerwise释放仍可触发empty_cache。源码某些ready检查显式只对CUDA，不能照搬为NPU准确性保证。执行器顺序多输出后会清理NPU缓存，影响后续分配和延迟。

按加载、量化后处理、驻留、执行、释放五阶段记录Host/NPU内存，覆盖CPU offload+量化、级联DiT切换和多输出。若格式或峰值异常先恢复无量化、关闭部分offload，再逐项启用；本次没有加载权重或测量内存，平台范围未知。
