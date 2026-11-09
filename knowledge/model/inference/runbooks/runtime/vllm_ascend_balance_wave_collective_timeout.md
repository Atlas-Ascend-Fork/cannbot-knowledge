---
type: Runbook
title: vLLM Ascend Balance：波次边界 sample_tokens 超时与 gather 缺席
description: 在 DP balance 开启后以逐 rank 的 EngineCore 调用序列排查 sample_tokens 超时，区分 collective
  参与缺失和 worker 计算问题。
tags:
- task.debugging
- topic.model_serving
- topic.data_movement
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_balance_schedule.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/balance_schedule_refactor.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_engine_core.py
  role: implementation
created_at: '2026-10-29T11:00:26Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
      parallelism:
        all_of:
        - dp
updated_at: '2026-10-29T11:00:26Z'
---

# vLLM Ascend Balance：波次边界 sample_tokens 超时与 gather 缺席


## 触发与证据强度

多 DP 服务启用 balance 后，短请求先结束或连续 wave 切换时偶发停顿，随后出现 RPC call to sample_tokens timed out。固定设计/实现记载一种 EngineCore collective 失配机制，不表示所有同名超时都由 balance 导致；无整卡硬件范围证据，draft。本次没有故障复现。

## 先收集进程级证据

保存版本对、有效 scheduler/EngineCore 类、DP组成员、每 rank 本地 unfinished、engines_running、wave、dummy batch、schedule 与 balance_gather 的进入/退出序号。核对各 rank 最近一次完成的 input/future 等待和 worker shm 收发；只看有请求的 rank 日志会遗漏关键缺席者。

当前必要调用点是 BalanceDPEngineCoreProc._has_global_unfinished_reqs 中 super 返回后，再注入 dp_group、gather。源码存在并不证明运行进程选择了该类；检查中央 patch_engine_core 的 Dyntra/balance 优先级和 spawn 子进程入口是否真正生效。

## 两条判别分支

若 busy rank 在 gather 等待、drained rank 只运行 dummy batch，检查是否把 gather 放进了 schedule。若某 rank 在 _process_input_queue/future，另一 rank 提前 gather，检查是否把 gather 移到 _process_engine_step、位于 wave/idle 协调之前。

阻塞 EngineCore 无法继续排空 worker shared-memory 通道，sample_tokens 回复积压后超时；因此该报错本身不足以定位 Attention kernel。相反，若全 rank gather 序号完整且调用点正确，应继续采集 worker/设备与通信栈，不将本卡假设当结论。[逐 rank collective 参与规则](collective_participation_per_rank_consistency.md)是通用诊断依据。

## 处置与验证

恢复固定版本的同步调用点和一致进程组；先解决[调度副本兼容缺口](vllm_ascend_balance_scheduler_version_drift.md)，再运行无本地请求、连续 wave、全部 idle 后重入及不同完成次序。临时关闭 balance 需新进程核对有效类；扩大 RPC timeout 只能改变报错时间，不能使缺席 rank 参与 collective。

通过信号为每个 active iteration 的 gather 全组配对、全 idle 一致跳过、所有 wave 继续返回且输出正确；还须与关闭策略的队列等待和时延比较。这里给出探针与判据，未宣称修复或性能通过。
