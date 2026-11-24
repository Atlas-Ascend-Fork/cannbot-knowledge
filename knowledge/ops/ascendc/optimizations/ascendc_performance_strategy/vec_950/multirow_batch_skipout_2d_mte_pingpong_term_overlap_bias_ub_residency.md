---
type: Optimization
title: 多行批数据流：2D 批量 skip/out MTE 拷贝 + Db0/Db1 乒乓 term 重叠 + 整 bias UB 常驻
description: 把逐行行拷贝与同步批量化：每 B 行一次 2D DataCopyPad，term/bias gather 走两个 TBuf 乒乓槽显式事件配对，可常驻数组整块预装 UB。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/multirow-batch-skipout-2d-mte-pingpong-term-overlap-bias-ub-residency.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-20T06:35:03Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "乒乓槽复用前必须 WaitFlag<V_S> 证明上一次 V 读完成（双缓冲槽复用竞争）",
      "显式事件 ID 必须避开 TPipe 队列事件池",
      "2D 拷贝 dstStride 单位为 32B datablocks，UB 行 pitch 需对齐",
      "批路径必须与原始路径结果逐位一致（本 run 全 case 覆盖验证）"
    ],
    "excluded_conditions": [
      "mte2 带宽主导且无乒乓可隐藏空间的 case（收益上限被带宽地板封顶）",
      "流量低于门控阈值的 case 保持原始路径（不进批路径）",
      "UB 装不下 B 行 skip/out staging + 双乒乓槽 + 常驻数组的组合时求解自动降批/回退"
    ],
    "required_conditions": [
      "索引读取已 UB 化后 aiv_scalar_ratio 仍高（ISSUE/SYNC 主导而非字节主导）",
      "每行行拷贝与 gather 都走队列且立即等待（每个 MTE2 延迟串行暴露）",
      "bias 或同类小数组整块可放入批 UB 预算（消除其全部 gather）",
      "host tiling 可在主循环预算外求批参数并输出门控位"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "comparison_sha256": "76b710ff68477397a7451c4417b229578941759ccc62b13e536b7535051184de",
      "decision_sha256": "bcb17b886fa8dec286418c29899bfc85c5d78fee9d16d7b2d2d6d1ea7b89c944",
      "operator_class": "fused-composite",
      "performance_sha256": "fb78e041c33fbd039072a3fcd046202137e3410c795dc8e5d0c266af05006376",
      "round": 3,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "420c4eea026c414453eb848fa207463da0790ed3cd203ba593b26a277f9a6448",
      "verify_sha256": "306b72138851eb3f2082d096678b014acd8a342aa94409c93e16986f2ee0cc85"
    },
    {
      "comparison_sha256": "255f5e1fa9c06ff967922702dd8d3576406808b7c3bb6de26ceda9d47d4ef36a",
      "decision_sha256": "79c1fac7e7b85a83f5aef9302a1400af3be129285da571e5fdc439dfd89b6a4b",
      "operator_class": "layout-transform",
      "performance_sha256": "e0d1a36f855b8e2ef10aa752666e1c83afdfe1f04d2ab3475bbfd4ecd1dedd91",
      "round": 4,
      "run_id": "<run-id>",
      "status": "rejected",
      "strategy_sha256": "2e2e95d0018e8f0a483bcd22615a57891fcda887c951ec0f5794d11f5e52e757",
      "verify_sha256": "438cca68d6e94436acfed9b2cab52d961c4692890389127e38cc5b8069e1b455"
    }
  ],
  "feature_signature": {
    "bottleneck": "scalar-pipe-issue-sync-serialization",
    "kernel_pattern": "batched-2d-datacopy-pingpong-event-pair-bias-residency",
    "precondition": "index-reads-already-ub-resident"
  },
  "generality": "op_class",
  "id": "S3-MULTIROW-BATCH-DATAFLOW",
  "implementation_steps": [
    "profiling 确认 Scalar-pipe 主导且 vec 不绑定，锁定 ISSUE/SYNC 串行化",
    "host tiling 求解批参数（B 行、槽深、biasResident）并输出门控位",
    "kernel 增加 ComputeBatch：2D 批量 skip/out 拷贝 + 乒乓槽事件配对 term gather + bias 常驻",
    "门控外 case 走原始路径零改动；污染探针证明批分支真实执行",
    "批边界 pitch/dstStride 用探针校验（交错行 artifact = pitch bug）"
  ],
  "intent": "消除 Scalar pipe 上的 ISSUE+SYNC 串行化：每个 MTE2 延迟经立即 WaitFlag 串行暴露在发射管线上。",
  "mechanism": "门控进入 ComputeBatch 路径：(1) skip1/skip2 用一次 blockCount=B 的 2D DataCopyPad（srcStride=0、UB 行 pitch 对齐），out 批同样 2D 批拷；(2) term/bias 行 gather 用 termDb0/Db1、biasDb0/Db1 两个 TBuf<VECCALC> 乒乓槽，显式 SetFlag/WaitFlag 事件配对（EVENT_ID 在 TPipe 事件池外），k+1 搬运与 k 计算重叠；(3) E x pitch 可放入批预算时整 bias 预装 UB 常驻。host 侧批参数（B、S、biasResident）由 tiling 带 UB 余量求解。",
  "name": "多行批数据流：2D 批量 skip/out MTE 拷贝 + Db0/Db1 乒乓 term 重叠 + 整 bias UB 常驻",
  "operator_class": "fused-composite",
  "operator_scope": "索引搬运已 UB 化后仍 Scalar-pipe 主导的行批 index-gather kernel：每行多次行级 MTE 拷贝 + O(K) 个 term gather，每个描述符经队列 Alloc/EnQue/DeQue/Free 且立即等待",
  "principle": "批量化把固定描述符/同步开销摊到 B 行；乒乓槽让相邻 term 的搬运与计算重叠（槽复用前必须 WaitFlag<V_S> 证明上一次 V 读完成）；常驻消掉可常驻数组的全部 gather。三者独立因果、可独立门控。",
  "related_anti_patterns": [
    "per-element-mte-descriptor-spray",
    "per-row-pipebarrier-sync"
  ],
  "risks": [
    "乒乓槽复用竞争会静默数据竞争，必须事件配对 + 探针",
    "2D 拷贝 pitch/dstStride 单位错误产生交错行错误（正确性可捕获）",
    "批路径被求解静默关闭时正确性仍过但性能不变——需污染探针",
    "mte2 主导 case 收益被带宽地板封顶，预期要按 pipe 下限折算"
  ],
  "slug": "multirow-batch-skipout-2d-mte-pingpong-term-overlap-bias-ub-residency",
  "summary": "把逐行的行拷贝/同步批量化：每 B 行一次 2D DataCopyPad（skip1/skip2/out 三个描述符摊到 B 行），term/bias gather 走两个 TBuf 乒乓槽用显式事件配对（SetFlag/WaitFlag S_MTE2/MTE2_V/V_S，事件 ID 在 TPipe 队列事件池之外），k+1 的 MTE2 与 k 的 V 计算重叠；bias 整块常驻 UB 时直接消掉一半 gather。",
  "verification": {
    "correctness": [
      "全 case verify 通过（本 run 20/20）",
      "污染探针证明批分支真实执行"
    ],
    "performance": [
      "批侧 case 显著加速且 control（门控外）零回归",
      "批热 case 若 1.0x 且精度过 → 疑似静默禁用，先跑污染探针再判"
    ],
    "rollback_signals": [
      "任何 correctness 失败立即 rollback",
      "control 回归超阈值 → 门控错分或 tiling 漂移 → reject",
      "探针出现 [1,0,1,0] 交错行 artifact → pitch/dstStride bug，先修复再测量"
    ]
  }
}
-->

# 性能优化策略：多行批数据流：2D 批量 skip/out MTE 拷贝 + Db0/Db1 乒乓 term 重叠 + 整 bias UB 常驻

单一优化点：把逐行的行拷贝/同步批量化：每 B 行一次 2D DataCopyPad（skip1/skip2/out 三个描述符摊到 B 行），term/bias gather 走两个 TBuf 乒乓槽用显式事件配对（SetFlag/WaitFlag S_MTE2/MTE2_V/V_S，事件 ID 在 TPipe 队列事件池之外），k+1 的 MTE2 与 k 的 V 计算重叠；bias 整块常驻 UB 时直接消掉一半 gather。

## 1. 原理

批量化把固定描述符/同步开销摊到 B 行；乒乓槽让相邻 term 的搬运与计算重叠（槽复用前必须 WaitFlag<V_S> 证明上一次 V 读完成）；常驻消掉可常驻数组的全部 gather。三者独立因果、可独立门控。

实现机制：门控进入 ComputeBatch 路径：(1) skip1/skip2 用一次 blockCount=B 的 2D DataCopyPad（srcStride=0、UB 行 pitch 对齐），out 批同样 2D 批拷；(2) term/bias 行 gather 用 termDb0/Db1、biasDb0/Db1 两个 TBuf<VECCALC> 乒乓槽，显式 SetFlag/WaitFlag 事件配对（EVENT_ID 在 TPipe 事件池外），k+1 搬运与 k 计算重叠；(3) E x pitch 可放入批预算时整 bias 预装 UB 常驻。host 侧批参数（B、S、biasResident）由 tiling 带 UB 余量求解。

## 2. 性能问题模式

- 优化目标：消除 Scalar pipe 上的 ISSUE+SYNC 串行化：每个 MTE2 延迟经立即 WaitFlag 串行暴露在发射管线上。
- 适用数据流：索引搬运已 UB 化后仍 Scalar-pipe 主导的行批 index-gather kernel：每行多次行级 MTE 拷贝 + O(K) 个 term gather，每个描述符经队列 Alloc/EnQue/DeQue/Free 且立即等待
- Feature signature：`{"bottleneck": "scalar-pipe-issue-sync-serialization", "kernel_pattern": "batched-2d-datacopy-pingpong-event-pair-bias-residency", "precondition": "index-reads-already-ub-resident"}`

## 3. 正确性红线

- 乒乓槽复用竞争会静默数据竞争，必须事件配对 + 探针
- 2D 拷贝 pitch/dstStride 单位错误产生交错行错误（正确性可捕获）
- 批路径被求解静默关闭时正确性仍过但性能不变——需污染探针
- mte2 主导 case 收益被带宽地板封顶，预期要按 pipe 下限折算

资源与硬件约束：

- 乒乓槽复用前必须 WaitFlag<V_S> 证明上一次 V 读完成（双缓冲槽复用竞争）
- 显式事件 ID 必须避开 TPipe 队列事件池
- 2D 拷贝 dstStride 单位为 32B datablocks，UB 行 pitch 需对齐
- 批路径必须与原始路径结果逐位一致（本 run 全 case 覆盖验证）

## 4. 泛化条件

- 策略作用域：op_class：fused-composite

适用：

- 索引读取已 UB 化后 aiv_scalar_ratio 仍高（ISSUE/SYNC 主导而非字节主导）
- 每行行拷贝与 gather 都走队列且立即等待（每个 MTE2 延迟串行暴露）
- bias 或同类小数组整块可放入批 UB 预算（消除其全部 gather）
- host tiling 可在主循环预算外求批参数并输出门控位

不适用：

- mte2 带宽主导且无乒乓可隐藏空间的 case（收益上限被带宽地板封顶）
- 流量低于门控阈值的 case 保持原始路径（不进批路径）
- UB 装不下 B 行 skip/out staging + 双乒乓槽 + 常驻数组的组合时求解自动降批/回退

## 5. 实施步骤

1. profiling 确认 Scalar-pipe 主导且 vec 不绑定，锁定 ISSUE/SYNC 串行化
2. host tiling 求解批参数（B 行、槽深、biasResident）并输出门控位
3. kernel 增加 ComputeBatch：2D 批量 skip/out 拷贝 + 乒乓槽事件配对 term gather + bias 常驻
4. 门控外 case 走原始路径零改动；污染探针证明批分支真实执行
5. 批边界 pitch/dstStride 用探针校验（交错行 artifact = pitch bug）

## 6. LLM 前置问题

- 目标实现是否满足：索引读取已 UB 化后 aiv_scalar_ratio 仍高（ISSUE/SYNC 主导而非字节主导）？
- 目标实现是否满足：每行行拷贝与 gather 都走队列且立即等待（每个 MTE2 延迟串行暴露）？
- 目标实现是否满足：bias 或同类小数组整块可放入批 UB 预算（消除其全部 gather）？
- 是否命中排除条件：mte2 带宽主导且无乒乓可隐藏空间的 case（收益上限被带宽地板封顶）？

## 7. 验收标准

正确性：

- 全 case verify 通过（本 run 20/20）
- 污染探针证明批分支真实执行

性能：

- 批侧 case 显著加速且 control（门控外）零回归
- 批热 case 若 1.0x 且精度过 → 疑似静默禁用，先跑污染探针再判

回滚信号：

- 任何 correctness 失败立即 rollback
- control 回归超阈值 → 门控错分或 tiling 漂移 → reject
- 探针出现 [1,0,1,0] 交错行 artifact → pitch/dstStride bug，先修复再测量

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：per-element-mte-descriptor-spray, per-row-pipebarrier-sync

- moe_finalize_routing-20260902_124740-ebd397（round=3, status=accepted）
- moe_re_routing-20260903_134013-4b9448（round=4, status=rejected）

## 检索卡（短卡）

动作：把逐行行拷贝与同步批量化：每 B 行一次 2D DataCopyPad，term/bias gather 走两个 TBuf 乒乓槽显式事件配对，可常驻数组整块预装 UB。
适用：索引读取已 UB 化后 aiv_scalar_ratio 仍高、每行行拷贝与 gather 都走队列且立即等待。
限制：乒乓槽复用前必须 WaitFlag<V_S>；事件 ID 须避开 TPipe 事件池；dstStride 为 32B datablocks。
范围：行批 index-gather kernel 的行拷贝与 term gather。
检索词：DataCopyPad、TBuf<VECCALC>、SetFlag/WaitFlag、S_MTE2、MTE2_V、V_S、dstStride
机会：每个 MTE2 延迟经立即 WaitFlag 串行暴露在发射管线上。
代价：mte2 带宽主导 case 收益被带宽地板封顶。
