---
type: Guide
title: SGLang Diffusion MOVA：NPU布局、复数精度与平台判断缺陷
description: 说明channels_last_3d规避、complex64频率缓存和三段torchair编译，同时保留漏调用平台判定的静态缺陷。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/models/dits/mova_video_dit.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/pipelines_core/stages/model_specific_stages/mova.py
  role: implementation
created_at: '2026-11-08T12:27:28Z'
updated_at: '2026-11-08T12:27:28Z'
platforms: []
---

# SGLang Diffusion MOVA：NPU布局、复数精度与平台判断缺陷

## 数据布局与频率

MOVA patchify意图为NPU避开不支持的channels_last_3d，选择连续布局。固定版本条件写成if current_platform.is_npu，遗漏()；Python绑定方法通常为truthy，因而该分支可误作用于其他平台。这是静态语义推断，本次没有复现，不能把它写成正确的独立平台选择配方。

MOVA stage在NPU将频率缓存转complex64，规避torch.cat不支持complex128；先准备全局频率再按SP切分，局部位置必须与token分片一致。编译时视觉/音频相关三个DiT分别使用torchair参数，不能共享错误目标的compiled callable。

## 验收与回退

核对平台条件、patchify前后stride、复数dtype与SP频率范围，再比较eager/compiled及TP/SP配置。固定布局可改变内存峰值和copy成本，complex64还需长位置质量验收。出错先eager和已核对连续布局，保留原输出基线；本次未运行模型、编译或数值测试。
