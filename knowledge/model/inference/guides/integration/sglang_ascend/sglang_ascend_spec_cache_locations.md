---
type: Guide
title: SGLang Ascend投机写地址：固定窗口与cache_loc_update回退
description: 说明NPU草稿/验证写窗口从request表取址、int32输出和位置填充，区分GPU融合地址翻译与NPU端点tensor路线。
tags:
- task.implementation
- topic.speculative_decoding
- topic.kv_cache
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/ops/speculative/cache_locs.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/eagle_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/dsv4/dsv4_common_hooks.py
  role: implementation
created_at: '2026-11-08T12:08:04Z'
updated_at: '2026-11-08T12:08:04Z'
platforms: []
aliases:
- cache_loc_update
- assign_extend_cache_locs_func
---

# SGLang Ascend投机写地址：固定窗口与cache_loc_update回退

## 地址窗口

投机阶段写地址对应每请求[start_offset,end_offset)的token位置，flat输出为请求优先的bs*draft_width行。NPU assign_extend_cache_locs_func分配int32 out_cache_loc并调用torch.ops.npu.cache_loc_update，将request ids、req_to_token、start/end传入，不能用CUDA分支int64或自定义stride假设替代。

GPU可融合固定draft宽、位置输出、anchor拷贝及virtual→physical写翻译；NPU/CPU回到end_offset tensor路径，full_v2p必须None。若请求positions_out，显式写start_offset[:,None]+arange(width)；anchor_out首列copy anchor，再调用共用窗口函数。存在GPU融合入口不等于NPU也执行该融合。

## 接入顺序与所有权

先确保窗口容量已经由allocator预留并写入request表，再按实时prefix读取本轮地址；reserve容量不代表每步全部写入。多步draft需把整块窗口转换为各step的地址列，不能每step重复使用同一个前缀切片。full/SWA/C128等不同空间由各pool/runner映射处理，函数本身不分配页、不维护引用计数。

检查start/end差与draft宽、输出dtype、request行宽和空batch行为。建议用非连续物理页、请求重排、跨页、部分接受和多step生成与逐项Python索引对照，并检查下一轮写窗口。此处不展开cache_loc_update底层Device实现，未运行内核或性能测试，芯片范围未知。
