---
type: Guide
title: SGLang Diffusion LASER：短序列回退与H3 BF16缩放
description: 说明attentions依赖、BNSD填充、变长与双段padding限制，以及MiniMax-H3范围保护与普通FP16转换的差异。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/layers/attention/backends/laser_attn.py
  role: primary
created_at: '2026-11-08T12:26:52Z'
updated_at: '2026-11-09T04:32:54Z'
platforms: []
---

# SGLang Diffusion LASER：短序列回退与H3 BF16缩放

## 触发与布局

LASER要求attentions扩展，head_dim支持32/64/96/128。Q序列小于2048或Q/KV长度不等时回退SDPA；长序列从BSND转置为BNSD（无需补齐时可仍是非连续视图，连续性取决于输入及后续转换），序列补齐256、head_dim补齐128后调用torch.ops.attentions.la。补齐KV尾部时以pre_tokens约束真实范围，最后截回原shape。稀疏后端的warmup也复用该路径。

## 变长与数值边界

varlen普通分段路径按请求独立调用；但累计边界长度为3、起点为0、终点为总token数时，会先命中单真实段加padding分支，代码不检查模型身份。调用方必须保证 `[0,used,padded]` 代表一个真实段加padding：该分支仅计算首段并把尾段置零，两个真实请求的 `[0,L1,L1+L2]` 也会命中，第二请求不会得到计算，不能当通用双请求支持。此分支为BF16动态范围将Q/K/V除256后转FP16，softmax_scale乘65536补偿QK，输出乘256恢复V量级；普通dense路径只是转FP16，不能宣称都有同一范围保护。输出延迟分配以降低峰值。

## 验收

先验证扩展版本和shape，覆盖2047/2048、非256整除、head_dim补齐与H3空padding，比较SDPA输出及极大BF16值。回退会改变kernel和延迟，LASER与稀疏组合仍需模型质量测试；本次仅来源核对，未获得性能或全芯片支持证据。
