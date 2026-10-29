---
type: Runbook
title: 推理 warmup 静默长耗时易误判卡死 + 同质 minibatch 冗余前向可 dummy 缓存跳过
description: 推理 warmup 静默长耗时易误判卡死 + 同质 minibatch 冗余前向可 dummy 缓存跳过。在昇腾上拉起大模型推理，正式服务前会先跑一次 warmup（用 dummy 输入跑一遍真实 prefill 前向，触发算子编译 / cache 分配 / 图捕获）。这一步有两个反复出现的坑： 看似卡死：warmup 阶段全程无日志输出，长 input/output seq 下前向本身就要跑很久，控制台长时间静止，很容易被误判成进程挂死 → 被 kill 重来，白白浪费一轮启动。 冗余耗时：warmup 为了覆盖不同并行档位，常在多个同质 prefill minibatch 上把完整前向重复跑多遍，其中大部分前向是重复计算，纯属浪费。
tags:
- task.debugging
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/10
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/6
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-22T10:43:19Z'
platforms:
- agnostic
---

# 推理 warmup 静默长耗时易误判卡死 + 同质 minibatch 冗余前向可 dummy 缓存跳过

## 信号（现象）

在昇腾上拉起大模型推理，正式服务前会先跑一次 **warmup**（用 dummy 输入跑一遍真实 prefill 前向，触发算子编译 / cache 分配 / 图捕获）。这一步有两个反复出现的坑：

- **看似卡死**：warmup 阶段全程无日志输出，长 input/output seq 下前向本身就要跑很久，控制台长时间静止，很容易被误判成进程挂死 → 被 kill 重来，白白浪费一轮启动。
- **冗余耗时**：warmup 为了覆盖不同并行档位，常在**多个同质 prefill minibatch** 上把完整前向重复跑多遍，其中大部分前向是重复计算，纯属浪费。

## 触发条件

- 任何有独立 warmup 阶段的昇腾推理路径（观测于 MLA/DSA 系大模型 prefill）。
- 长序列（大 input_max_len / output）放大 warmup 单次前向耗时，「看似卡死」更明显。
- warmup 用多个**结构同质**的 minibatch（形状/配置一致，仅为触发编译）时才有冗余前向可省。

## 根因

- **静默**：长序列可能增加 warmup 前向耗时，具体关系取决于模型、阶段和执行路径，来源没有给出线性计时证据，而该阶段未打任何进度日志 → 没有可观测信号区分「在算」与「卡住」。这不是性能 bug，是可观测性缺失。
- **冗余**：若多个 warmup minibatch 只为触发同一套算子编译/图捕获，它们的前向输出对后续无实际依赖，重复跑等价前向对 warmup 目的无增益。

## 修法 / 手段

1. **给 warmup 打日志**：在 warmup 入口、每个 minibatch 前后打印进度（第几个/共几个、耗时），把「静默长耗时」变成「可见的进行中」，避免误 kill。运行时优化 agent 遇到「拉起后长时间无输出、疑似 hang」时，**先确认是否在 warmup 阶段**，别急着判死。
2. **warmup dummy 缓存复用**：warmup 若在多个同质 minibatch 上跑完整前向，只让**首个 minibatch 真跑一遍并缓存其输出**，后续 warmup cycle 入口直接返回该缓存（"warm up dummy"）、跳过重复前向，即可压掉 warmup 里的冗余计算耗时。仅适用于 minibatch 同质、输出对后续无真实依赖的 warmup 场景，不可用于真实推理请求。

## 风险 / 边界

- dummy 缓存仅在 warmup（非真实请求）且 minibatch 同质时成立；一旦 warmup 需覆盖**不同形状/不同并行档**的 minibatch（各自会触发不同算子编译），不能跨档复用缓存，否则漏编译某档、真实请求时再补编译反而更慢。
- 打日志只解决「误判」，不缩短 warmup 本身；真要缩短长序列 warmup，考虑减小 warmup 的 dummy 序列长度到「够触发所有算子编译」的下限。

## 相关经验

- 「拉起后长时间无输出、疑似 hang」的通用辨别（区分 warmup / 环境驱动初始化 / 真故障）见 [bringup-error-root-cause-env-driver-platform](../runtime/bringup_error_root_cause_env_driver_platform.md)。
- warmup 之后进入 decode 稳态期还能进一步跳 guard 复评省 host 开销，见 [aclgraph-decode-steady-state-skip-guard-reinplace](../../optimizations/rules/aclgraph_decode_steady_state_skip_guard_reinplace.md)（二者都以「warm-up 已把该编译的都编译完」为前提）。

## Evidence

- `仓自报`（@244e12f）：warmup 在增补日志前全程无输出、长 seq 下易被误判卡死；dummy 缓存复用把多同质 minibatch 的重复前向压到只跑首个。二者均为该仓 warmup 路径行为，无独立 before→after 计时数字。
- 溯源下探：[cann-recipes-infer-issue-10-requirement-warmup](https://gitcode.com/cann/cann-recipes-infer/issues/10)、[cann-recipes-infer-pr-6-feat-add-warm-up-dummy](https://gitcode.com/cann/cann-recipes-infer/merge_requests/6)