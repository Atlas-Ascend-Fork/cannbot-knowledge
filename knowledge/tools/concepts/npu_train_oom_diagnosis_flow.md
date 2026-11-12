---
type: Concept
title: NPU 训练 OOM 诊断流程：来源分类、静态估算与内存快照分析
description: 按报错关键字判定 OOM 来源（WorkspaceAllocator/HCCL/NPUCachingAllocator），先做静态内存估算判断配置是否超限（峰值≈参数+梯度+优化器状态+激活+临时缓冲 ≤ 显存×0.95）；临时内存 OOM 走条件化排查分支（记录实际可用显存/allocated/reserved/申请失败大小/其他进程与通信缓冲占用，证据支持时再做 set_per_process_memory_fraction 水线 A/B），CachingAllocator OOM 采集 memory snapshot 做六维分析（语义分类/峰值/时间线/碎片化/Top 大块），泄漏判断须控制 shape/负载、区分 allocated 与 reserved 并检查预热后持续增长。
tags: [task.debugging, topic.memory, topic.model_architecture]
status: stable
sources:
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/model/model-train-oom-analysis/SKILL.md
    role: primary
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/model/model-train-oom-analysis/references/memory-estimation-templates.md
    role: supporting
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/model/model-train-oom-analysis/references/mosaic-analysis-guide.md
    role: supporting
created_at: "2026-11-05T02:10:00Z"
updated_at: "2026-11-10T02:45:00Z"
platforms: [a2, a3, "950"]
aliases: [OOM, memory snapshot, set_per_process_memory_fraction, NPUCachingAllocator, memory fragmentation]
---

# NPU 训练 OOM 诊断流程：来源分类、静态估算与内存快照分析

诊断 PyTorch on NPU 大模型训练中的 NPU OOM（Out of Memory）问题：日志分类 → 静态估算 → snapshot 深度分析 → 优化建议。来源技能以 torchtitan-npu 为示例载体；内存估算公式、snapshot 分析维度与决策矩阵框架无关，可映射到其他训练框架。

## 来源分类（按报错关键字）

| OOM 来源 | 特征关键字 | 后续步骤 |
| --- | --- | --- |
| NPUWorkspaceAllocator | `workspace allocator`、`workspace memory` | 走条件化排查分支（原「调内存水线」） |
| HCCL 通信 | `HCCL`、`hccl`、`communication` | 走条件化排查分支（原「调内存水线」） |
| NPUCachingAllocator | `CachingAllocator`、`torch.OutOfMemoryError`、`NPU out of memory` | 先静态估算，再按需 snapshot |
| 无法判断 | 不含上述关键字 | 先静态估算 |

**发生时机**是排查线索而非判定：OOM 在 step 0-2 更可能是配置问题（估算 + 调配置），但也可能是初始化期通信缓冲或临时张量放大；OOM 在 step N 较大更倾向疑似内存泄漏（snapshot 对比 + 代码审查），仍需结合 snapshot 证据确认。

## 静态估算（采集 snapshot 前必做）

收集模型参数（dim/n_layers/n_heads/vocab_size/MoE 配置等）与训练参数（batch_size/seq_len/各并行度/激活重计算策略/优化器类型），按模板估算：

```
训练峰值内存 ≈ 参数内存 + 梯度内存 + 优化器状态 + 激活内存 + 临时缓冲
估算总内存 ≤ NPU 总显存 × 0.95（预留 5% 安全余量）
```

估算超限 = 配置本身超限，无需 snapshot，直接按优化矩阵调整（参数量、batch/seq、激活重计算、优化器分片/卸载等）。配置超限是最常见的 OOM 根因。

## 临时内存 OOM：条件化排查分支

Workspace/HCCL OOM 且静态估算表明模型放得下时，**不能直接断定根因是 PTA 缓存分配器占用过多**——静态估算无法排除估算遗漏、其他进程占用、通信缓冲需求或运行峰值变化。按条件化分支排查：先记录实际可用显存、allocated/reserved、申请失败的大小、其他进程与通信缓冲占用；证据支持「需要给分配器之外的内存留空间」时，再做水线 A/B——用 `torch.npu.set_per_process_memory_fraction(ratio)` 限制 PTA 显存上限（各框架配置项名不同，torchtitan-npu 为 `torch_npu_memory_ratio`）：首次尝试 0.9，仍 OOM 降到 0.85。**失败与回退条件**：降低水线后 CachingAllocator 本身 OOM，说明限制过紧或模型需求过高，回到估算与配置优化；水线调整前后 allocated/reserved 与失败申请大小无变化，说明根因不在分配器占用，回到占用记录逐项排查。

## CachingAllocator OOM：memory snapshot 六维分析

估算接近上限或估算合理仍 OOM 时，用 `torch.npu.memory._record_memory_history()` + `_dump_snapshot()` 采集快照（多数训练框架已封装开关；OOM 发生时也会自动转储）。分析维度：

1. **分配概览**：Reserved / Allocated / Active / 碎片化率 / 设备利用率；
2. **语义分类**：按激活、梯度、优化器状态、参数、通信缓冲、注意力层、MoE 层等类别给出大小与占比；
3. **峰值分析**：定位峰值时刻、各类别占比与 Top 调用栈；
4. **时间线**：alloc/free 事件序列，识别训练阶段，检测潜在泄漏；
5. **碎片化**：空闲块分布、最大空闲块、小块占比与等级评估；
6. **Top-N 大块**：最大内存块的大小、类别与完整调用栈。

**分析判断矩阵**：激活 >40% → 启用 activation checkpoint；优化器状态 >40% → 卸载/分片；梯度 >30% → 增大 TP/PP；通信缓冲 >20% → 调整并行策略与 HCCL 配置；碎片化率 >20% → `torch.npu.empty_cache()` 与分配策略；其他/未知 >20% → 用 Mosaic 深度分析定位来源。

**泄漏检测**（快照增长是排查线索，不能单凭快照数确认）：传 3+ 个不同 step 的 snapshot 分析增长趋势，且须控制 shape/负载一致、区分 allocated 与 reserved 口径、并检查预热期之后的持续增长与对象释放情况。某类别在预热后仍持续单调增长 = 泄漏证据充分，进入代码审查；增长后稳定 = warmup 正常增长；未增长仍 OOM = 内存本身不足，回到估算。**双快照差异对比**可量化两个场景（如开/关激活重计算）的各类别内存变化。

快照基于 pickle 反序列化，只分析自己训练产出的可信 `.pickle`，不加载来历不明的快照。

## 失效边界

- 来源技能的分析脚本与框架配置项是 torchtitan-npu 的具体实现；估算公式、六维分析与判断矩阵阈值可直接复用，框架接入点需映射；
- 判断矩阵阈值为分析指引而非硬性标准，联合结论以多维度交叉为准；
- 精度类内存问题（如 dtype 升格导致激活翻倍）会体现在语义分类中，根因排查另见精度诊断知识。
