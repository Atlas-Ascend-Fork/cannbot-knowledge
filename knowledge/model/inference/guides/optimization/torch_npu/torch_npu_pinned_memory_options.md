---
type: Guide
title: TorchNPU pinned memory：扩展段、注册与缓存阈值
description: 区分 Host pinned memory 与 Device 分配器，说明后台 Event、host register 和两个大块阈值的版本及互斥。
tags:
- task.optimization
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/PYTORCH_NPU_ALLOC_CONF.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/PYTORCH_NPU_ALLOC_CONF.md
  role: constraint
created_at: '2026-11-09T06:08:21Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# TorchNPU pinned memory：扩展段、注册与缓存阈值

## 固定版本与范围

依据 TorchNPU 固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`，按中英文配置页列出的A2/A3及950DT限定；不扩展950PR；逐项版本门槛独立核对，不回推至 26.0/PyTorch2.8 发布基线。本文仅静态审阅，没有 NPU 实验。

## 分别选择 Host 内存策略

|选项|机制与门槛|
|--|--|
|pinned_use_background_threads|默认False，后台线程查询/处理Events以减少主线程阻塞；TorchNPU≥26.0且PyTorch≥2.8。|
|pin_memory_expandable_segments|默认False，Host pinned池扩展段按20MB固定物理粒度申请；要求TorchNPU≥7.3、HDK≥25.5、CANN商用≥8.5。开启后相关块计数统计不参与、显示0，不能据零值认定没有占用。|
|pinned_mem_register|默认False，True将Host pinned内存注册为Device可访问地址；要求TorchNPU≥26.0、HDK≥26.0.RC1、CANN商用≥8.5；与pin_memory_expandable_segments不支持同配。|

这些选项在 PYTORCH_NPU_ALLOC_CONF 或适用版本的 PYTORCH_ALLOC_CONF 中配置，不是设备 expandable_segments 的同义名，不能把设备页大小配置直接套到Host池。

## 大块舍入和缓存是两个阈值

pinned_max_round_threshold_mb、pinned_max_cached_size_mb 都为正整数MB，要求TorchNPU≥26.2和PyTorch≥2.13，仅默认非expandable pinned路径生效；与Host扩展段同配会告警且忽略两个阈值，进程仍可启动。

未设舍入阈值时，可缓存请求通常向上取到2的幂；设阈值后，大于它的请求按精确大小，例如129MB可避免取整至256MB。缓存阈值则控制释放后进free list还是立即归还OS；大于缓存阈值的块本来就不缓存，也不做上述舍入。默认不设缓存阈值表示释放块都可缓存，不表示所有Host内存立即归还。

分别检查Host内存峰值、H2D吞吐、分配频率与主线程阻塞；减少缓存可能降低常驻量但增加分配开销。本文没有申请Host内存或验证搬运性能。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/PYTORCH_NPU_ALLOC_CONF.md)（primary）

- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/PYTORCH_NPU_ALLOC_CONF.md)（constraint）
