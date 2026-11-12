---
type: Guide
title: SGLang Ascend V4缓存窗口：分配后挂钩与verify实时bundle
description: 区分预留容量与本轮投机写区间，说明C4无NonZero压紧、C128页表展开、CPU镜像和PD状态索引适配。
tags:
- task.implementation
- topic.attention
- topic.kv_cache
- topic.speculative_decoding
- topic.data_movement
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/dsv4/dsv4_common_hooks.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/dsv4/dsv4_allocator.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_dsv4_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/allocation.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/static_kv_storage.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/managers/schedule_batch.py
  role: implementation
created_at: '2026-11-08T12:07:57Z'
updated_at: '2026-11-09T04:31:18Z'
platforms: []
aliases:
- maybe_build_dsv4_verify_bundle
- DSV4OutCacheLoc
---

# SGLang Ascend V4缓存窗口：分配后挂钩与verify实时bundle

## 分配后状态写入

通用分配器将DSV4OutCacheLoc暂存到batch；extend/decode挂钩把flat C128 loc按每请求[floor(prefix/128),floor(seq/128))切片，写入request sidecar。decode输入是已经增长token_per_req后的长度，必须先减回旧长度得到新增区间。host request镜像用于此路径，不能为了取得req id读取在飞device tensor造成D2H同步。

PD per-request预分配没有ScheduleBatch，因此由dsv4_unwrap_prealloc/write_dsv4_prealloc_tables走同一侧表协议；只拆出full loc而不写sidecar会留下C128不可寻址状态。非DSV4路径bundle为None，挂钩无操作。

## Verify不能复用整块reserve

Spec-v2提前预留的容量可大于本轮draft实际区间。`maybe_build_dsv4_verify_bundle`以实时live前缀及固定或ragged verify长度，重建当前写窗口，而非复用旧reserve bundle。C128按压缩位置查sidecar page再加页内offset；full/SWA来自本轮flattened写loc。状态ring不参与这些KV槽分配。

C4选择full slot%4==3并除4，用cumsum计算稳定压紧目的位置，invalid写到最终丢弃的trash槽，固定输出上界为min(T,T//4+bs)。这避免布尔索引降低为NonZeroV2所引起的主机同步；尾部0是消费者约定padding，不能照搬到“state location0无效”的错误判断。

## PD状态索引与边界

C128 KV是独立page payload；950 C4 compress state按请求bank和本地ring size生成逻辑token对应行，允许两端ring8/16不同。pre-950 explicit C4 state已跟随共享SWA payload，不能再重复发送950专用行。这里只说明索引适配，完整传输所有权由PD链路负责。

建议验证live与reserve不同、跨4/128边界、ragged请求长度不等、空压缩区间及请求slot换号；逐请求对照loc和位置，不以总flat长度相等代替顺序正确。此路径某些eager ragged准备允许CPU回读，compact graph应走静态元数据buffer；本次未跑同步/传输测试。

## 调用依赖补充

实际通用allocation路径在extend/decode写req_to_token后调用DSV4挂钩，decode传入的是旧CPU长度+token_per_req；StaticKVStorage向独立C128 allocator传request ids和对应request表，并将返回bundle保存在batch.out_cache_loc_dsv4，普通out_cache_loc仍拆为full槽。bundle字段全是各自池的token slot id，构造页表时才除各池page_size，不能把C128 page id直接当token loc。ScheduleBatch携带bundle跨阶段，forward init和轻量视图需继续传递。

NPU DSV4进入Triton last_loc路线时使用safe变体：kernel内保持int32结果，发射后再提升类型，规避混合int32→int64 store误编译。DCP 会把 allocator.page_size 扩为配置 page_size×dcp_size，应读取实际 allocator.page_size，不能沿用未扩大的物理页值；保持物理页大小的说明属于 KV sharding 分支，该分支只扩大索引空间。
