---
type: Guide
title: SGLang Ascend V4 RoPE：预热表、前向memo与图内生命周期
description: 说明interleaved RoPE表的dtype/device键、buffer注册、position逐轮gather和禁止图内临时构表的约束。
tags:
- task.implementation
- topic.attention
- topic.graph_execution
- topic.precision
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/dsv4/dsv4_rope.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_dsv4_backend.py
  role: implementation
created_at: '2026-11-08T12:07:58Z'
updated_at: '2026-11-08T12:07:58Z'
platforms: []
aliases:
- Dsv4NpuRoPE
- prime_rope_cos_sin
---

# SGLang Ascend V4 RoPE：预热表、前向memo与图内生命周期

## 初始化与表布局

`Dsv4NpuRoPE`按freqs_cis对象身份共享实例，先将complex频率的real/imag物化成连续视图，避免每步对strided view索引。cos/sin扩成[c0,c0,c1,c1,...]和[s0,s0,s1,s1,...]，YARN mscale应已在freqs_cis预计算阶段乘入，此处不再重复缩放。

有rotary owner时按dtype注册persistent=False buffer，model.to()可以迁移；无owner时以(dtype,device)缓存。ensure_tables还检查shape/dtype/device，旧表不满足时允许初始化重建；decode allow_build=False，缺表直接报错，不能在捕获图中repeat_interleave创建新存储。

## 每轮位置与精度

只缓存整张表，position-gathered cos/sin是前向局部张量。跨轮保留gather结果会在MTP positions改变时复用旧角度。prime_rope_cos_sin只在当前ForwardBatch建立memo，以freqs身份、dtype、inverse区分，并要求positions为同一对象才命中。inverse使用sin取负，不能重用正向sin。

BF16调用从预先BF16表gather，其他dtype可从FP32表gather再cast；同一元素一次舍入等价，但不能任意把整个RoPE运算降低为BF16 PyTorch乘法。源码选择custom inplace_partial_rotary_mul，注释指出内核FP32累积与普通BF16乘法的差异可能影响argmax。partial_slice只覆盖NoPE之后的RoPE段，Q/K各自shape需对应。

## 验证与代价

初始化后核对表长度、dtype、device和buffer迁移；连续两轮只改变positions，确认输出跟随新位置；测试不同freqs、inverse、空输入及图capture/replay。memo减少重复gather，但增加每前向缓存引用，不能跨ForwardBatch无限延长寿命。本次未做数值/性能试验，也不推断所有NPU型号支持custom op。
