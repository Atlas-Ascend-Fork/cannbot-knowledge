---
type: Guide
title: SGLang NPU多模态编码合批与占位符同步边界
description: 说明跨请求ViT cache miss合批、特殊full路径、NPU生成mask前同步以及EVS改写后token计数的回读代价。
tags:
- task.implementation
- topic.multimodal
- topic.performance.analysis
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/managers/mm_schedule.py
  role: primary
created_at: '2026-11-08T12:20:20Z'
updated_at: '2026-11-08T12:20:20Z'
platforms: []
---

# SGLang NPU多模态编码合批与占位符同步边界

chunked embedding按request整理offset。每个item只有一段offset或为audio时可以进入per-image路线，NPU与CUDA将全部此类cache miss合并一次编码，再按request重建chunk并排序回原请求顺序；HIP/XPU的保守逐请求回退不能直接套到NPU。非per-image进入full路径，预计算embedding优先复用，不能声称所有多模态数据都能一次ViT合批。

_get_multimodal_mask用已排序placeholder Tensor做searchsorted与clamp，再比较token，避开torch.isin在大集合unique引起的Host计数同步。但get_embedding_and_mask在NPU仍显式current_stream.synchronize后才建mask，不能仅依据searchsorted helper说整个多模态准备没有同步。

通常用Host offset计算extend内MM token数，避免mask.sum().item；EVS改写input_ids使原offset失效时回退设备mask求和回Host。embedding过长只告警并从尾部截取，是当前折中而非精度保证；过短抛RuntimeError，chunked-prefill配置需与图像token边界共同核对。

验收覆盖跨请求重复图像、cache命中/未命中混合、audio、full路径、EVS与chunk边界，比对embedding顺序、placeholder计数和最终模型精度；profile应分别计入编码、当前流同步、mask及语言Prefill，不以ViT合批次数等同端到端加速比。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
