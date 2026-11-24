---
type: Optimization
title: 连续流批管线：扁平化多槽 term-gather 发射窗口 + 跨批双缓冲 skip/out staging
description: 把严格配对的 2 槽乒乓升级为 S 槽扁平发射窗口（gather 先全部发射再统一等待，解除行间 slot token 串行），skip/out staging 改跨批双缓冲（批 n+1 的拷贝与批 n 的计算重叠，消除批边界全排空），MTE2 gather 队列加深让搬运延迟互相重叠。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/flattened-multislot-term-gather-window-cross-batch-skipout-double-buffer.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "槽/parity 复用前必须事件证明上一读完成（双缓冲槽复用竞争）",
      "事件 ID 与 TPipe 队列事件池隔离",
      "S 槽与双缓冲的 UB 预算必须独立于主循环 tiling 求解并带余量"
    ],
    "excluded_conditions": [
      "mte2 已饱和的 case：地板即 mte2_busy，加深发射窗口收益封顶（约 1.1x 上限量级）",
      "流量低于批门控阈值的 case 走原始路径",
      "微核噪声地板 case 不进批路径"
    ],
    "required_conditions": [
      "批数据流落地后仍 Scalar-pipe top-utilized 且 vec/mte2 均未饱和（调度墙而非带宽墙）",
      "UB 可容纳 S 槽 + 双缓冲 staging（host 带余量求解）",
      "per-case 理想地板 max(mte2_busy, vec_busy) 与实测 wall 有明显差距（存在可转换的 stall）"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "comparison_sha256": "d3bb5e318502de8540fb12320941a6316ac20df768ce9da5d188c48aaea4471e",
      "decision_sha256": "2bb5c111db5175da3c3ed3ec207e6cc8c47a06561eccba259f21a92880c3ea45",
      "operator_class": "fused-composite",
      "performance_sha256": "f2468d79fc33b80abf028c4252710aaf28a004fa01b26ad6d59f9b84ddba6e2e",
      "round": 4,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "ae542905a49b1ff86de302f4decadcb6228a7c484e173e9ef2c8e643f1ae8879",
      "verify_sha256": "a50e5cff08c43f9e6bcc7c85d2d5d8432a537c707a2090670a77d762716e4bb5"
    }
  ],
  "feature_signature": {
    "bottleneck": "unsaturated-pipes-scalar-waitflag-stall",
    "kernel_pattern": "flattened-multislot-issue-window-cross-batch-double-buffer",
    "precondition": "batch-dataflow-with-2slot-pingpong-already-in-place"
  },
  "generality": "op_class",
  "id": "S6-DEEP-BATCH-PIPELINE",
  "implementation_steps": [
    "对比 op_summary 的 mte2/vec busy 与实测 wall，确认存在调度 gap（未饱和但 Scalar 高占用）",
    "host tiling 求解槽深 S 与双缓冲批参数",
    "kernel 把乒乓等待改扁平发射窗口（发射全部 gather 后统一等待）",
    "skip/out staging 改偶/奇批双缓冲，删除批边界全排空序列",
    "污染探针证明窗口/parity 分支真实执行；采集后核对 scalar_ratio 下降"
  ],
  "intent": "消除调度墙：2 槽乒乓下 compute-k 阻塞在自己的 WaitFlag 上、行 i+1 首个 gather 等行 i 最后的 V 读释放槽 token，最多 2 个 gather 在飞、每 k 对暴露一个 gather 延迟；批边界 staging 完全串行。",
  "mechanism": "门控进入连续流批路径：(1) term gather 用 S 个扁平槽的发射窗口——先连续发射多个 gather 再统一 WaitFlag，解除逐对等待；(2) skip/out staging 双缓冲（偶/奇批交替 buffer），批 n+1 的 BatchCopyIn 与批 n 的计算重叠，去掉批边界 SKIPWAR 全排空；(3) outBat staging 深度加深。host tiling 求解 S 与双缓冲批参数。",
  "name": "连续流批管线：扁平化多槽 term-gather 发射窗口 + 跨批双缓冲 skip/out staging",
  "operator_class": "fused-composite",
  "operator_scope": "已有 2 槽乒乓批数据流（批拷贝+term 乒乓）后仍 Scalar-pipe 主导、无 pipe 饱和的行批 index-gather kernel",
  "principle": "当所有 pipe 都未饱和而 Scalar pipe 高占用（WaitFlag stall）时，墙是调度深度而非字节：加深在飞窗口把串行等待转换成重叠。理想地板趋近 max(mte2_busy, vec_busy) + prologue。",
  "related_anti_patterns": [
    "per-element-mte-descriptor-spray",
    "per-row-pipebarrier-sync"
  ],
  "risks": [
    "更深的窗口使正确性风险集中在槽/parity 复用竞争，探针必须先行",
    "mte2 主导 case 收益被带宽地板封顶，预期需按地板折算，不得按 wall 线性外推",
    "若采后 aiv_scalar_ratio 仍 >=0.85 且目标加速 <1.05，说明 scalar-stall 归因被证伪——记录边界并停止同族更深管线重试"
  ],
  "slug": "flattened-multislot-term-gather-window-cross-batch-skipout-double-buffer",
  "summary": "把严格配对的 2 槽乒乓升级为 S 槽扁平发射窗口（gather 先全部发射再统一等待，解除行间 slot token 串行），skip/out staging 改跨批双缓冲（批 n+1 的拷贝与批 n 的计算重叠，消除批边界全排空），MTE2 gather 队列加深让搬运延迟互相重叠。",
  "verification": {
    "correctness": [
      "全 case verify 通过（本 run 20/20）",
      "污染探针证明窗口/parity 分支真实执行"
    ],
    "performance": [
      "未饱和 pipe 的批 case 向 max(mte2,vec) 地板收敛；mte2 主导 case 上限封顶仍应 >1",
      "control（门控外 case）增量不超同代码漂移带"
    ],
    "rollback_signals": [
      "任何 correctness 失败立即 rollback",
      "control 回归超阈值且无噪声地板解释 → reject",
      "scalar-stall 归因证伪信号（ratio 仍高且加速 <1.05）→ 拒绝该族更深管线重试并记边界"
    ]
  }
}
-->

# 性能优化策略：连续流批管线：扁平化多槽 term-gather 发射窗口 + 跨批双缓冲 skip/out staging

单一优化点：把严格配对的 2 槽乒乓升级为 S 槽扁平发射窗口（gather 先全部发射再统一等待，解除行间 slot token 串行），skip/out staging 改跨批双缓冲（批 n+1 的拷贝与批 n 的计算重叠，消除批边界全排空），MTE2 gather 队列加深让搬运延迟互相重叠。

## 1. 原理

当所有 pipe 都未饱和而 Scalar pipe 高占用（WaitFlag stall）时，墙是调度深度而非字节：加深在飞窗口把串行等待转换成重叠。理想地板趋近 max(mte2_busy, vec_busy) + prologue。

实现机制：门控进入连续流批路径：(1) term gather 用 S 个扁平槽的发射窗口——先连续发射多个 gather 再统一 WaitFlag，解除逐对等待；(2) skip/out staging 双缓冲（偶/奇批交替 buffer），批 n+1 的 BatchCopyIn 与批 n 的计算重叠，去掉批边界 SKIPWAR 全排空；(3) outBat staging 深度加深。host tiling 求解 S 与双缓冲批参数。

## 2. 性能问题模式

- 优化目标：消除调度墙：2 槽乒乓下 compute-k 阻塞在自己的 WaitFlag 上、行 i+1 首个 gather 等行 i 最后的 V 读释放槽 token，最多 2 个 gather 在飞、每 k 对暴露一个 gather 延迟；批边界 staging 完全串行。
- 适用数据流：已有 2 槽乒乓批数据流（批拷贝+term 乒乓）后仍 Scalar-pipe 主导、无 pipe 饱和的行批 index-gather kernel
- Feature signature：`{"bottleneck": "unsaturated-pipes-scalar-waitflag-stall", "kernel_pattern": "flattened-multislot-issue-window-cross-batch-double-buffer", "precondition": "batch-dataflow-with-2slot-pingpong-already-in-place"}`

## 3. 正确性红线

- 更深的窗口使正确性风险集中在槽/parity 复用竞争，探针必须先行
- mte2 主导 case 收益被带宽地板封顶，预期需按地板折算，不得按 wall 线性外推
- 若采后 aiv_scalar_ratio 仍 >=0.85 且目标加速 <1.05，说明 scalar-stall 归因被证伪——记录边界并停止同族更深管线重试

资源与硬件约束：

- 槽/parity 复用前必须事件证明上一读完成（双缓冲槽复用竞争）
- 事件 ID 与 TPipe 队列事件池隔离
- S 槽与双缓冲的 UB 预算必须独立于主循环 tiling 求解并带余量

## 4. 泛化条件

- 策略作用域：op_class：fused-composite

适用：

- 批数据流落地后仍 Scalar-pipe top-utilized 且 vec/mte2 均未饱和（调度墙而非带宽墙）
- UB 可容纳 S 槽 + 双缓冲 staging（host 带余量求解）
- per-case 理想地板 max(mte2_busy, vec_busy) 与实测 wall 有明显差距（存在可转换的 stall）

不适用：

- mte2 已饱和的 case：地板即 mte2_busy，加深发射窗口收益封顶（约 1.1x 上限量级）
- 流量低于批门控阈值的 case 走原始路径
- 微核噪声地板 case 不进批路径

## 5. 实施步骤

1. 对比 op_summary 的 mte2/vec busy 与实测 wall，确认存在调度 gap（未饱和但 Scalar 高占用）
2. host tiling 求解槽深 S 与双缓冲批参数
3. kernel 把乒乓等待改扁平发射窗口（发射全部 gather 后统一等待）
4. skip/out staging 改偶/奇批双缓冲，删除批边界全排空序列
5. 污染探针证明窗口/parity 分支真实执行；采集后核对 scalar_ratio 下降

## 6. LLM 前置问题

- 目标实现是否满足：批数据流落地后仍 Scalar-pipe top-utilized 且 vec/mte2 均未饱和（调度墙而非带宽墙）？
- 目标实现是否满足：UB 可容纳 S 槽 + 双缓冲 staging（host 带余量求解）？
- 目标实现是否满足：per-case 理想地板 max(mte2_busy, vec_busy) 与实测 wall 有明显差距（存在可转换的 stall）？
- 是否命中排除条件：mte2 已饱和的 case：地板即 mte2_busy，加深发射窗口收益封顶（约 1.1x 上限量级）？

## 7. 验收标准

正确性：

- 全 case verify 通过（本 run 20/20）
- 污染探针证明窗口/parity 分支真实执行

性能：

- 未饱和 pipe 的批 case 向 max(mte2,vec) 地板收敛；mte2 主导 case 上限封顶仍应 >1
- control（门控外 case）增量不超同代码漂移带

回滚信号：

- 任何 correctness 失败立即 rollback
- control 回归超阈值且无噪声地板解释 → reject
- scalar-stall 归因证伪信号（ratio 仍高且加速 <1.05）→ 拒绝该族更深管线重试并记边界

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：per-element-mte-descriptor-spray, per-row-pipebarrier-sync

- moe_finalize_routing-20260902_124740-ebd397（round=4, status=accepted）

## 检索卡（短卡）

动作：把严格配对的 2 槽乒乓改为 S 槽扁平发射窗口，skip/out staging 改跨批偶/奇双缓冲
适用：批数据流落地后仍 Scalar-pipe top-utilized 且 vec/mte2 均未饱和，UB 可容纳 S 槽与双缓冲
限制：槽/parity 复用前须事件证明上一读完成；事件 ID 与 TPipe 队列事件池隔离；mte2 饱和 case 收益被地板封顶（约 1.1x）
范围：fused-composite 的行批 index-gather 批数据流
检索词：扁平发射窗口、WaitFlag、SKIPWAR、偶/奇批双缓冲、outBat staging
机会：2 槽乒乓下最多 2 个 gather 在飞、每 k 对暴露一个 gather 延迟
代价：更深窗口把正确性风险集中在槽/parity 复用竞争，探针必须先行
