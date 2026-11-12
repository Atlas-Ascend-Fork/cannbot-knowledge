---
type: Guide
title: SGLang 昇腾 EPLB 的统计窗口、分层迁移与恢复闭环
description: 补齐 NPU 权重迁移上层的 EPLB 触发、统计新鲜度、算法选择、分 chunk yield 和缺失专家恢复。
tags:
- task.implementation
- topic.mixture_of_experts
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/eplb/eplb_manager.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/eplb/expert_location.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/eplb/eplb_algorithms/__init__.py
  role: supporting
created_at: '2026-11-08T12:22:44Z'
updated_at: '2026-11-08T12:22:44Z'
platforms: []
---

# SGLang 昇腾 EPLB 的统计窗口、分层迁移与恢复闭环

## 统计到迁移的闭环

NPU 专用 staging/migration 由公共 EPLBManager 的 updater 调用链触发；manager 没有 NPU 关键词，单靠关键词清单会遗漏其统计与调度前提。初始化要求 rebalance_num_iterations 不小于 recorder_buffer_size，避免 ring buffer 包含过旧数据，并在尚未 recording 时启动统计。on_forward_pass_end 驱动 generator，每设定轮数进入 rebalance。

manager 读取 logical_count 和窗口 average_utilization；utilization 高于 min_rebalancing_utilization_threshold 时跳过，未知 utilization 则继续。不要把“阈值越低越积极”当结论，实际比较方向是大于阈值时不迁移。

## 算法与分 chunk 行为

ExpertLocationMetadata 把二维 counts 扩为带窗口维的 Tensor，再传模型 expert/group/node/replica 拓扑。auto 算法在 num_groups 存在且可被 num_nodes 整除时选 deepseek_hierarchical，否则 deepseek；源码未提供通用最优性能证明。physical expert 数需与 EP 布局匹配。

按层排序并切 chunk，多 chunk 时在每个更新前 yield，分摊到后续 forward 边界；只有未分 chunk 时的日志计时同步设备，因此不能直接拿两类日志 time 比较迁移成本。elastic post-scale 的映射由 rank0 计算并广播，阶段未提交时跳过；这些公共协议不等于 NPU 已支持任意 elastic 拓扑，仍受 NPU TP=EP=WORLD 限制。

## 恢复与验证

updater 返回缺失专家后，优先用模型 generate_weight_name_filter 定向恢复，否则全量重载；有 DRAM backup 先从 backup，否则磁盘。lp 分派更新后重新初始化求解器。检查统计是否排除 padding、窗口新鲜度、chunk 边界、mapping/权重一致性及缺失恢复，再评估负载改善是否抵消迁移成本。禁用 rebalance 并重载稳定 placement 可回退；本次未执行 EPLB 或报告收益。

## 相关机制

- [SGLang 昇腾 EPLB 的地址稳定迁移与 staging 流水](../../optimizations/sglang_ascend/sglang_ascend_moe_eplb_weight_migration.md)
- [SGLang 昇腾 TopK 的物理专家映射与 padding 统计](../../concepts/sglang_ascend/sglang_ascend_moe_topk_placement_padding.md)
