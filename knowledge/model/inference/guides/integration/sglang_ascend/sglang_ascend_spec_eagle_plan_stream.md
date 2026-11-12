---
type: Guide
title: SGLang Ascend Eagle批次计划：padding后元数据与draft完成栅栏
description: 说明关闭图时的post-pad重规划、plan stream后mRoPE/verify缓冲刷新和V4 C128接受后清理边界。
tags:
- task.implementation
- topic.speculative_decoding
- topic.graph_execution
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/eagle_worker_common.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_dsv4_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/eagle_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/model_executor/forward_batch_info.py
  role: implementation
created_at: '2026-11-08T12:08:02Z'
updated_at: '2026-11-09T04:32:54Z'
platforms: []
aliases:
- prepare_for_draft
- eagle_prepare_for_verify
- SGLANG_ENABLE_OVERLAP_PLAN_STREAM
---

# SGLang Ascend Eagle批次计划：padding后元数据与draft完成栅栏

## 元数据应在哪个阶段建立

draft decode/extend准备会决定请求槽、写窗口和ForwardBatch。NPU关闭图时，prepare_mlp_sync_batch还会改变padding形状；过早mark_forward_metadata_ready会让页表行数与最终batch不符。因此该路径保留未ready标记，让forward_extend在post-pad重新初始化。图load_batch已完成计划时才可复用ready元数据。

多层Eagle每个de-tied runner有自己的attention backend；只准备第一个runner不能声称后续层都ready。非图verify也需在post-pad按实际runner建立元数据，避免pre-pad长度固化。

## Overlap计划流与draft依赖

plan stream只可提前准备不依赖draft结果的数据。主流等待plan stream后，NPU mRoPE模型必须按真实draft positions重新计算mrope positions；update_verify_buffers_to_fill_after_draft 在普通 Ascend backend 中为空实现，不刷新 custom_mask；V4 backend 只在具备缓冲时刷新 C4/C128 压缩位置。这些压缩位置需要最后一次更新，不能用提前计划时尚未产生的draft输出。

plan stream分配的input_ids/out_cache_loc会record_stream到实际forward流，避免allocator在计算前回收。grammar_tree 必须在 target verify 发射前取得；grammar 词表掩码则在 target forward 返回后、采样前构建，不能混淆两个阶段。这个准备流开关与普通scheduler overlap不是同一能力。

## 接受与缓存

target verify之后根据接受结果整理token/长度与缓存；需要C128 cleanup的V4 pool不直接使用跳过该清理的通用post-verify graph。不能只看到post-verify图已捕获就将所有pool强制接入。

建议在关闭图、DP padding、mRoPE、开启计划流和V4跨128边界场景记录计划/最终shape、ready标志与cache位置，比较关闭计划流的输出和后续状态。本次没有运行竞态或压力测试；保留stream同步会有代价，但不能以省同步为由忽略真实依赖。

## 调用依赖补充

ForwardBatch只有在ready且replan_equivalent=True时才比较计划batch/token shape与最终padding shape，发现变化后重规划；不具备等价重规划能力的多步包装保留skip行为并依靠backend防御检查。已弃用skip_attn_backend_init=True仍映射为ready标志并warn-once，不能把它当作被忽略的空参数，否则会意外重建多步草稿元数据。
