---
type: Optimization
title: dtype-aware size gate 修复 SIMT direct-GM 的 fp16 mid-size 回归（机制有效，正式门禁结构性阻塞）
description: 将统一size gate改为按dtype与输入规模选择SIMT/VEC的门控，并为未知或不利区间保留回退。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/simt-direct-gm-dtype-aware-gate.md
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
      "gate 阈值必须由实测 crossover 夹定（fp16: 12.58M 回归 / 67M 改善两个数据点）",
      "kernel 保持与 round-1 逐字节一致（kernel_hash 不变），round-2 改动仅限 host gate，保持 fingerprint 契约",
      "被 gate 路由回 VEC 的 case 必须满足冻结基线 max_case_regression=0.95"
    ],
    "excluded_conditions": [
      "bf16 crossover 未实证：case 13（bf16 10.9M）在 2.2M gate 下 round-1 1.02x 薄收益、round-2 升到 1.23x；若 bf16 cast-heavy crossover 高于实测需单独提高 bf16 gate（本轮未发生，仅监测）",
      "fp16 gate 设到 >=67M 会丢失 case 5 的 SIMT 增益（gate 过高信号，非回归）",
      "形式验收要求两侧 stable 样本：run 冻结 baseline 不可变地 stable=false 时 comparison.ok 恒 false、accept/final 门禁结构性不可满足——这是验收环境边界，不是机制缺陷"
    ],
    "required_conditions": [
      "SIMT direct-GM 机制本身已验证正确（verify 20/20）且在大数据 regime 有效（10-23x）",
      "存在实测的 dtype 相关 crossover：fp16 mid-size（12.58M）SIMT 回归、fp16 大 size（67M）SIMT 2.40x；fp32/bf16 自 2.2M 起 SIMT 有收益",
      "gate 决策在 dtype 已知的位置生效（inputDtype 在 totalElements 之前解析），无 dtype-unaware 代码路径",
      "被 gate 路由回 VEC 的 case 的 VEC 基线稳定且 >= 0.95x（case 2 基线 222.24us cv 0.006，round-2 实测 1.017x）"
    ]
  },
  "classification": "lesson",
  "created": "2026-08-23",
  "evidence": [
    {
      "comparison_sha256": "c08de59f2f31d599e689e5dab10ea88be47f5a74459e9340f90f2e69238f7f9b",
      "decision_sha256": "1e3512163f8844fee9569f9644a3cd29a94572df20acf5610bf9b62d489e3dae",
      "operator_class": "fused-composite",
      "performance_sha256": "47173b759f036cf6bd78da76b8b139b4acf605d1da1e48cbb6bc48e6336d83f0",
      "round": 2,
      "run_id": "<run-id>",
      "status": "rejected",
      "strategy_sha256": "c7e8cdb3f709ea1fe9bc8804a01b822a14d869dc286c4c1c6a905b102491bc01",
      "verify_sha256": "4f173f6b691c9b7d34b6508d5ceb6ff47c0a932d5c178b42538bd9dff1f7cb09"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "scalar-bound",
      "dtype-crossover",
      "size-gate-refinement",
      "accept-gate-structural-block"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "guard": [
      "fp16-gate-bracketed-12.58m-67m",
      "kernel-hash-unchanged"
    ],
    "pattern": "simt-direct-gm-dtype-aware-gate",
    "structure": [
      "host-dtype-gate",
      "simt-direct-gm",
      "vec-fallback",
      "tensorlist-foreach"
    ]
  },
  "generality": "op_class",
  "id": "L-ELEM-SIMT-DTYPE-GATE",
  "implementation_steps": [
    "用 round-1 确认的回归（fp16 12.58M 0.7767x）与改善（fp16 67M 2.40x）夹出 fp16 gate 阈值（24M）",
    "把 host 侧单一 SIMT_MIN_ELEMENTS 拆为 dtype-aware 常量（fp16=24M、fp32/bf16=2.2M），在 inputDtype 已知后计算 useSimt",
    "重新应用已验证 SIMT kernel（逐字节相同，kernel_hash 不变），只改 host gate",
    "fingerprint-bounded clean 重采：确认 case 2 回 VEC 且 >=0.95x、case 5 留 SIMT 保持 ~2.4x、大 case 增益复现、regressed_cases=0",
    "若 case 2 仍 <0.95x 说明 gate 未生效（dtype enum 不匹配或 gate 在 dtype-unaware 路径）；若 case 5 丢增益说明 gate 过高"
  ],
  "intent": "在保留 SIMT direct-GM 大数据 regime 增益的同时，修复单一 size gate 对 fp16 mid-size multi-tensor 的回归——把 fp16 的 SIMT-vs-VEC crossover 位置（12.58M 回归、67M 改善之间）编码进 host gate。",
  "mechanism": "round-2 重新应用 round-1 已验证的 SIMT direct-GM kernel（kernel hash e8e64dc07bb37969 逐字节相同，kernel 未改动），仅 host tiling 改动：SIMT_MIN_ELEMENTS 按 dtype 分化——fp16=24,000,000、fp32/bf16=2,200,000。inputDtype 在 tiling 主流程顶部经 MapInputDtype 解析（位于 gate 决策之前，无 dtype-unaware 路径），useSimt = (totalElements >= (inputDtype==DTYPE_FP16 ? 24M : 2.2M))。case 2（fp16 12.58M）路由回 VEC，case 5（fp16 67M）保持 SIMT。",
  "name": "dtype-aware size gate 修复 SIMT direct-GM 的 fp16 mid-size 回归（机制有效，正式门禁结构性阻塞）",
  "op": "foreach_addcdiv_scalar",
  "operator_class": "fused-composite",
  "operator_scope": "SCALAR_BOUND 的 foreach/TensorList elementwise kernel 的 host size-gated dispatch：SIMT direct-GM 与 VEC 双路径之间按 dtype+总元素数选择",
  "principle": "SIMT fp16 per-element 标量计算成本近似线性于元素数，而 VEC 管线的 per-tile 标量开销随 size 超线性塌缩，因此 SIMT-vs-VEC crossover 依 dtype 不同，fp16 的 crossover 高于 fp32/bf16。用实测的两个 fp16 数据点（12.58M 回归 0.7767x、67M 改善 2.40x）把 fp16 gate 夹在 24M，可把回归模式留在 VEC 同时不过度阻塞获胜 regime。",
  "related_anti_patterns": [],
  "risks": [
    "fp16 gate 依赖 dtype enum 判断：enum 不匹配或 gate 在 dtype-unaware 代码路径计算会让 case 2 继续走 SIMT（回归信号 0.95 触发）",
    "bf16 crossover 未实证：case 13 若降到 <0.95x 需把 bf16 也纳入更高 gate",
    "run 级冻结 baseline unstable 使 accept/final 门禁结构性不可满足：即使机制验证正确、无回归，round 仍只能记录为 rejected——需换稳定基线 run 或显式 stable-gate waiver，不能在同 run 内无限重采集"
  ],
  "slug": "simt-direct-gm-dtype-aware-gate",
  "summary": "对 SIMT direct-GM 数据流，把单一 SIMT_MIN_ELEMENTS 改为 dtype-aware gate（fp16=24,000,000、fp32/bf16=2,200,000 总元素）可修复 fp16 mid-size multi-tensor 回归：case 2（fp16 12,582,912 元素）由 24M gate 路由回 VEC，speedup 0.7767x（round-1）-> 1.017x（round-2），同时全部大 case SIMT 增益按 round-1 量级保留（case 4 23.24x、case 5 2.40x、case 9 9.57x、case 20 4.11x，case 13 bf16 10.9M 升到 1.23x），comparison regressed_cases=0、improved=10、unchanged=10、total_speedup 7.5198。round-2 被 rejected 的唯一原因是结构性门禁阻塞而非机制回归：run 冻结 baseline 不可变地 stable=false 使 comparison.ok 恒 false、accept/final 门禁结构性不可满足。Lesson：机制验证正确的轮次可能因验收环境被记录为 rejected，归档时记录机制边界而不是弱化门禁。",
  "verification": {
    "correctness": [
      "rounds/002 verify 20/20 通过（kernel_hash e8e64dc07bb37969，与 build.json kernel_after 一致；fingerprint-bounded clean window）"
    ],
    "performance": [
      "case 2（fp16 12.58M）由 24M gate 路由回 VEC：speedup 1.017x（222.24->218.52us），关闭 round-1 的 0.7767x 回归",
      "大 case 增益按 round-1 量级保留：case 4（fp32 67M）23.24x、case 9（bf16 99M）9.57x、case 5（fp16 67M）2.40x、case 20（fp32 10.5M）4.11x；case 13（bf16 10.9M）升到 1.23x",
      "rounds/002/comparison.json：regressed_cases=0、improved=10、unchanged=10、total_speedup 7.5198，无一行低于 0.95x",
      "注意：comparison.json ok=false 是结构性的（冻结基线 stable=false + 当前 performance.json 因 VEC 小 case 抖动 stable=false），非机制回归"
    ],
    "rollback_signals": [
      "case 2 仍 <0.95x：fp16 gate 未生效，revert 或重推导 gate",
      "任一 SIMT-path case <0.95x（如 case 13 bf16 掉到 <0.95x 需把 bf16 也纳入 gate）",
      "case 5 丢 SIMT 增益回到 VEC 级 ~1.0x：fp16 gate 被设到 >=67M",
      "正确性失败：fp16/bf16 必须 fp32 中间计算 + 显式 cast；SIMT 写不可见需 threadfence"
    ]
  }
}
-->

# 性能优化策略：dtype-aware size gate 修复 SIMT direct-GM 的 fp16 mid-size 回归（机制有效，正式门禁结构性阻塞）

单一优化点：对 SIMT direct-GM 数据流，把单一 SIMT_MIN_ELEMENTS 改为 dtype-aware gate（fp16=24,000,000、fp32/bf16=2,200,000 总元素）可修复 fp16 mid-size multi-tensor 回归：case 2（fp16 12,582,912 元素）由 24M gate 路由回 VEC，speedup 0.7767x（round-1）-> 1.017x（round-2），同时全部大 case SIMT 增益按 round-1 量级保留（case 4 23.24x、case 5 2.40x、case 9 9.57x、case 20 4.11x，case 13 bf16 10.9M 升到 1.23x），comparison regressed_cases=0、improved=10、unchanged=10、total_speedup 7.5198。round-2 被 rejected 的唯一原因是结构性门禁阻塞而非机制回归：run 冻结 baseline 不可变地 stable=false 使 comparison.ok 恒 false、accept/final 门禁结构性不可满足。Lesson：机制验证正确的轮次可能因验收环境被记录为 rejected，归档时记录机制边界而不是弱化门禁。

## 1. 原理

SIMT fp16 per-element 标量计算成本近似线性于元素数，而 VEC 管线的 per-tile 标量开销随 size 超线性塌缩，因此 SIMT-vs-VEC crossover 依 dtype 不同，fp16 的 crossover 高于 fp32/bf16。用实测的两个 fp16 数据点（12.58M 回归 0.7767x、67M 改善 2.40x）把 fp16 gate 夹在 24M，可把回归模式留在 VEC 同时不过度阻塞获胜 regime。

实现机制：round-2 重新应用 round-1 已验证的 SIMT direct-GM kernel（kernel hash e8e64dc07bb37969 逐字节相同，kernel 未改动），仅 host tiling 改动：SIMT_MIN_ELEMENTS 按 dtype 分化——fp16=24,000,000、fp32/bf16=2,200,000。inputDtype 在 tiling 主流程顶部经 MapInputDtype 解析（位于 gate 决策之前，无 dtype-unaware 路径），useSimt = (totalElements >= (inputDtype==DTYPE_FP16 ? 24M : 2.2M))。case 2（fp16 12.58M）路由回 VEC，case 5（fp16 67M）保持 SIMT。

## 2. 性能问题模式

- 优化目标：在保留 SIMT direct-GM 大数据 regime 增益的同时，修复单一 size gate 对 fp16 mid-size multi-tensor 的回归——把 fp16 的 SIMT-vs-VEC crossover 位置（12.58M 回归、67M 改善之间）编码进 host gate。
- 适用数据流：SCALAR_BOUND 的 foreach/TensorList elementwise kernel 的 host size-gated dispatch：SIMT direct-GM 与 VEC 双路径之间按 dtype+总元素数选择
- Feature signature：`{"bottleneck": ["scalar-bound", "dtype-crossover", "size-gate-refinement", "accept-gate-structural-block"], "dtypes": ["fp16", "bf16", "fp32"], "guard": ["fp16-gate-bracketed-12.58m-67m", "kernel-hash-unchanged"], "pattern": "simt-direct-gm-dtype-aware-gate", "structure": ["host-dtype-gate", "simt-direct-gm", "vec-fallback", "tensorlist-foreach"]}`

## 3. 正确性红线

- fp16 gate 依赖 dtype enum 判断：enum 不匹配或 gate 在 dtype-unaware 代码路径计算会让 case 2 继续走 SIMT（回归信号 0.95 触发）
- bf16 crossover 未实证：case 13 若降到 <0.95x 需把 bf16 也纳入更高 gate
- run 级冻结 baseline unstable 使 accept/final 门禁结构性不可满足：即使机制验证正确、无回归，round 仍只能记录为 rejected——需换稳定基线 run 或显式 stable-gate waiver，不能在同 run 内无限重采集

资源与硬件约束：

- gate 阈值必须由实测 crossover 夹定（fp16: 12.58M 回归 / 67M 改善两个数据点）
- kernel 保持与 round-1 逐字节一致（kernel_hash 不变），round-2 改动仅限 host gate，保持 fingerprint 契约
- 被 gate 路由回 VEC 的 case 必须满足冻结基线 max_case_regression=0.95

## 4. 泛化条件

- 策略作用域：op_class：fused-composite

适用：

- SIMT direct-GM 机制本身已验证正确（verify 20/20）且在大数据 regime 有效（10-23x）
- 存在实测的 dtype 相关 crossover：fp16 mid-size（12.58M）SIMT 回归、fp16 大 size（67M）SIMT 2.40x；fp32/bf16 自 2.2M 起 SIMT 有收益
- gate 决策在 dtype 已知的位置生效（inputDtype 在 totalElements 之前解析），无 dtype-unaware 代码路径
- 被 gate 路由回 VEC 的 case 的 VEC 基线稳定且 >= 0.95x（case 2 基线 222.24us cv 0.006，round-2 实测 1.017x）

不适用：

- bf16 crossover 未实证：case 13（bf16 10.9M）在 2.2M gate 下 round-1 1.02x 薄收益、round-2 升到 1.23x；若 bf16 cast-heavy crossover 高于实测需单独提高 bf16 gate（本轮未发生，仅监测）
- fp16 gate 设到 >=67M 会丢失 case 5 的 SIMT 增益（gate 过高信号，非回归）
- 形式验收要求两侧 stable 样本：run 冻结 baseline 不可变地 stable=false 时 comparison.ok 恒 false、accept/final 门禁结构性不可满足——这是验收环境边界，不是机制缺陷

## 5. 实施步骤

1. 用 round-1 确认的回归（fp16 12.58M 0.7767x）与改善（fp16 67M 2.40x）夹出 fp16 gate 阈值（24M）
2. 把 host 侧单一 SIMT_MIN_ELEMENTS 拆为 dtype-aware 常量（fp16=24M、fp32/bf16=2.2M），在 inputDtype 已知后计算 useSimt
3. 重新应用已验证 SIMT kernel（逐字节相同，kernel_hash 不变），只改 host gate
4. fingerprint-bounded clean 重采：确认 case 2 回 VEC 且 >=0.95x、case 5 留 SIMT 保持 ~2.4x、大 case 增益复现、regressed_cases=0
5. 若 case 2 仍 <0.95x 说明 gate 未生效（dtype enum 不匹配或 gate 在 dtype-unaware 路径）；若 case 5 丢增益说明 gate 过高

## 6. LLM 前置问题

- 目标实现是否满足：SIMT direct-GM 机制本身已验证正确（verify 20/20）且在大数据 regime 有效（10-23x）？
- 目标实现是否满足：存在实测的 dtype 相关 crossover：fp16 mid-size（12.58M）SIMT 回归、fp16 大 size（67M）SIMT 2.40x；fp32/bf16 自 2.2M 起 SIMT 有收益？
- 目标实现是否满足：gate 决策在 dtype 已知的位置生效（inputDtype 在 totalElements 之前解析），无 dtype-unaware 代码路径？
- 是否命中排除条件：bf16 crossover 未实证：case 13（bf16 10.9M）在 2.2M gate 下 round-1 1.02x 薄收益、round-2 升到 1.23x；若 bf16 cast-heavy crossover 高于实测需单独提高 bf16 gate（本轮未发生，仅监测）？

## 7. 验收标准

正确性：

- rounds/002 verify 20/20 通过（kernel_hash e8e64dc07bb37969，与 build.json kernel_after 一致；fingerprint-bounded clean window）

性能：

- case 2（fp16 12.58M）由 24M gate 路由回 VEC：speedup 1.017x（222.24->218.52us），关闭 round-1 的 0.7767x 回归
- 大 case 增益按 round-1 量级保留：case 4（fp32 67M）23.24x、case 9（bf16 99M）9.57x、case 5（fp16 67M）2.40x、case 20（fp32 10.5M）4.11x；case 13（bf16 10.9M）升到 1.23x
- rounds/002/comparison.json：regressed_cases=0、improved=10、unchanged=10、total_speedup 7.5198，无一行低于 0.95x
- 注意：comparison.json ok=false 是结构性的（冻结基线 stable=false + 当前 performance.json 因 VEC 小 case 抖动 stable=false），非机制回归

回滚信号：

- case 2 仍 <0.95x：fp16 gate 未生效，revert 或重推导 gate
- 任一 SIMT-path case <0.95x（如 case 13 bf16 掉到 <0.95x 需把 bf16 也纳入 gate）
- case 5 丢 SIMT 增益回到 VEC 级 ~1.0x：fp16 gate 被设到 >=67M
- 正确性失败：fp16/bf16 必须 fp32 中间计算 + 显式 cast；SIMT 写不可见需 threadfence

## 8. 分类与证据

- Classification：`lesson`
- Generality：`op_class`
- Related anti-patterns：无

- foreach_addcdiv_scalar-20260823_153850-4ed096（round=2, status=rejected）

## 检索卡（短卡）

动作：将统一size gate改为按dtype与输入规模选择SIMT/VEC的门控，并为未知或不利区间保留回退。
适用：SIMT direct-GM已在目标dtype验证正确，且需按dtype与规模选择SIMT或VEC。
限制：各dtype须分别定阈值；dtype枚举与host判断必须一致，未知区间回退且保持输出语义。
范围：目标dtype的SIMT direct-GM与VEC选择路径。
检索词：SIMT direct-GM、dtype-aware gate、SIMT/VEC crossover、per-element、per-tile。
机会：单一size gate与不同dtype的SIMT/VEC交叉区间不匹配。
代价：需要分别测量各dtype候选规模下的两条路径。
