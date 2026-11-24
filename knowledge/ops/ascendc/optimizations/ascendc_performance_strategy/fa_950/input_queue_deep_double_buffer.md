---
type: Optimization
title: 输入队列加深一级的 GM 搬入/向量计算重叠
description: 将输入队列深度由 2 增至 3，或对半拆分片上缓冲并增加一级深度。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A5/03-input-queue-deep-double-buffer.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：输入队列加深一级的 GM 搬入/向量计算重叠

> **单一优化点：** 向量侧消费者（vec1 读 wsS / vec2 读 wsO+wsAccO）的输入队列深度
> +1 并把每 chunk 片上缓冲一分为二，使下一 chunk 的 GM→UB 搬入在当前 chunk 的向量
> 算术执行期间就发出，用计算掩盖搬运延迟；保持整行 chunk（归约轴连续性与合并访存
> 不变），槽位轮转仍由队列抽象持有。

> **状态：未验证。** 来源：K-Search 世界模型动态生成（节点
> node_mha_submission_r6_3，rating 5.5，挂 s13 下，2026-08-25 续跑 run round 6 生成，
> 排 frontier 第一但 run 以 NO_EXECUTABLE_ACTION 退出未执行；动态节点未持久化——
> 本卡是唯一存档点）。

---

## 1. 优化原理

### 1.1 性能问题模式

本模板 vec1 的 `inputQue1_` 深度 2×32KB、vec2 同队列复用：Alloc→DataCopy→EnQue→
DeQue→算术→Free 的串行节奏下，**当前 chunk 算术运行时 MTE2 搬运管线空闲**，下一
chunk 的 DataCopy 要等 Free 归还槽位后才发出。decode/MTP 小 chunk（outerCols 小、
chunk 数多）时每次气泡占比高；prefill 大 chunk 时单次气泡小但次数多。
（动态节点原始论据："The consumer's input queue depth leaves the load pipe idle
while elementwise work runs on the current chunk."）

### 1.2 核心机制

- 队列深度 2→3（或缓冲对半分 + 深度+1），UB 预算内自平衡：inputQue1_ 现 2×32KB，
  +1 槽需 32KB——从 tmpBuf_（32KB，SoftmaxFlashV2 工作区，实际用量通常 <50%）或
  掩码辅助缓冲（colIdx/maskTmp/maskTmp2/zero/one 各 MAX_OUTER_COLS×4B=16KB×5，
  有压缩空间）挤出。
- 不改变 chunk 行数推导（vec1ChunkRows_）与整行语义，只改预取距离。
- vec2 同思路（oNewUb/oPrevUb 双满槽恰好占满深度 2，加深需挤 UB 或减 mChunk）。

## 2. 正确性红线

- UB 总预算硬约束（248KB/AIV）：加槽后所有 InitBuffer 总和不得溢出——溢出是
  编译期/初始化期硬错误，必须逐项记账。
- 预取距离改变后，队列 EnQue/DeQue 的隐式 MTE2/MTE3 同步语义不变（仍由 TQue
  管理）；禁止手改 flag。
- 与 ring 流水（S_READY/O_READY CrossCore flag）无耦合：本策略只动 AIV 内部队列，
  不动跨核信号——改动面必须守住这条边界。
- SoftmaxFlashV2 的 tmpBuf 若被压缩，需确认其工作区下界（SoftMaxFlashV2TilingFunc
  按 srcM×srcK 推算），预算不足会静默走降级路径或越界。

## 3. 泛化条件

- **适用**：chunk 数多、单 chunk 搬入时间与算术时间同量级（decode/MTP 大批量 case
  ——本轮 0.39~0.93x 未动区）；MTE2 与 VEC 利用率 profiling 呈交替空转形态。
- **不适用**：chunk 已被 01 号裁剪到很少的 causal prefill（气泡次数少）；
  UB 预算挤不出的配置（D256 大 dimAlign 场景 tmpBuf 占用高）。
- 先决 profiling 证据：PipeUtilization 里 MTE2 与 Vector 利用率之和显著 <100% 且
  互斥（可用 msprof PipeUtilization.csv 旁证）。

## 4. 实施步骤

1. 复核 UB 记账表（各 InitBuffer 字节数列清单），确定 +32KB 的来源。
2. inputQue1_ 深度 2→3；观察 TQue 深度语义下 AllocTensor 是否自然预取（AscendC
   队列深度即预取距离）。
3. 若队列加深不可行，退化为手动双缓冲对半分（TBuf + 显式事件），但成本高、
   优先走队列深度。
4. kbench 分 case 前后对比 + PipeUtilization 复测（MTE2/VEC 重叠度提升为证）。

## 5. LLM 前置问题

- 当前 inputQue1_/outputQue1_/tmpBuf_ 各占多少 UB？总预算还剩多少？
- vec1 主循环里 DataCopy 发起点与上一 chunk Free 的距离（预取是否已自然发生）？
- decode case 的 chunk 数与单 chunk 搬入/算术时长比？

## 6. 风险与回退

- UB 溢出：编译期报 InitBuffer 失败，直接回退深度。
- tmpBuf 压缩过度导致 SoftmaxFlashV2 tiling 降级（性能掉、精度可能劣化）——
  验收必须含 D256 case。
- 回退旋钮：深度改回 2 即原实现，无其它耦合。

## 7. 验收标准

- 精度：20/20 + 长序列 12/12 不变。
- 性能：decode/MTP 批量 case（case11~18）合计提升 ≥3%；prefill case ±2% 内。
- 旁证：PipeUtilization 中 MTE2 与 VEC 空闲窗口收窄。

## 检索卡（短卡）

动作：将输入队列深度由 2 增至 3，或对半拆分片上缓冲并增加一级深度。
适用：chunk 较多且单 chunk 搬入与算术耗时同量级。
限制：加槽后全部 InitBuffer 总和不得超过每个 AIV 的 248KB UB 预算。
范围：vec1 的 wsS 与 vec2 的 wsO、wsAccO 输入队列。
检索词：inputQue1_、TQue 深度、MTE2、VEC、AllocTensor、双缓冲。
机会：MTE2 与 VEC 呈交替空闲，且当前 chunk 搬入与算术串行。
代价：增加一级槽需要额外 32KB UB，须从其他缓冲中腾挪。
