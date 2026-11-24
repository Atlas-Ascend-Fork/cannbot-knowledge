---
type: Optimization
title: SIMT direct-GM 大数据机制与单一 size gate 过宽的负向边界
description: 将过宽的单一总元素 size gate 改为按 dtype 分化，并验证回退边界。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/simt-direct-gm-size-gate-regression.md
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
      "SIMT fp16 为 per-element 标量计算，成本近似线性于元素数；gate 阈值必须由 dtype 实测 crossover 界定（12.58M 回归、67M 2.40x 改善两个数据点夹出 fp16 gate）",
      "AssignDataToEachCore 退化（blockCount < needCoreNum）不可达：SIMT gate 要求 >=2.2M 元素，blockCount 远大于 needCoreNum",
      "SIMT 写 GM 依赖框架刷新可见性；若后续读/verify 不可见需加 threadfence/核间同步或回退"
    ],
    "excluded_conditions": [
      "fp16 mid-size multi-tensor foreach（如 12.58M 总元素、3 tensor/list）在单一 2.2M gate 下走 SIMT 会确认回归（实测 0.7767x）——必须留在 VEC 管线",
      "不得把单一 size gate 外推为通用规则：fp16 与 fp32/bf16 的 crossover 不同（fp16 需更高 gate；fp32/bf16 自 2.2M 起 SIMT 即有收益）",
      "形式验收要求两侧 stable 样本：当 run 的冻结 baseline/performance.json 不可变地 stable=false 时，确定性 compare gate 对本 run 任意一轮恒返回 rejected——这是验收环境边界，与机制边界正交"
    ],
    "required_conditions": [
      "设备 ascend950/A5（examples_a5、arch35 SIMT 路径可用，三个 dtype __simt_entry 符号编译成功）",
      "瓶颈被完整 msprof 证实为 SCALAR_BOUND（aiv_scalar_ratio ~100%、VEC/MTE2/MTE3 idle ~99%），如 case 4/9",
      "SIMT 路径用 fp32 中间计算 + __half2float/__bfloat162float/__float2half/__float2bfloat16 显式 cast（lesson simt-lowprecision-scalar-cast-intrinsic），且 SIMT 写 GM 对后续 MTE 读可见（lesson simt-write-to-mte-read-visibility）",
      "size gate 必须按 dtype/pattern 区分——本卡证明单一 2.2M 总元素 gate 对 fp16 mid-size multi-tensor 过宽"
    ]
  },
  "classification": "negative_boundary",
  "created": "2026-08-23",
  "evidence": [
    {
      "comparison_sha256": "e7de0e6c58ec320ac5c0f329cb64ac29ce82c7ef3e233690503d7c0f83fdeadf",
      "decision_sha256": "637949bcb21418b61482f3952697073618aeada3e42bc345ce7a35c38bbc39d5",
      "operator_class": "fused-composite",
      "performance_sha256": "4462171dd3e3b1023cb7fe02fdd91714379fd375f9cc0957b2d9441ec5a64390",
      "round": 1,
      "run_id": "<run-id>",
      "status": "rejected",
      "strategy_sha256": "9f37e9667890428db4a8436c8cde10fc8a70140bcfdb1076912d63d8b1e8ba78",
      "verify_sha256": "c6c4b4ec51107ac3a78869197bd686dae52acf867f57bc54f4574a62c8305730"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "scalar-bound",
      "per-tile-sync",
      "dtype-crossover",
      "size-gate-overbroad"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "simt-direct-gm-single-size-gate",
    "structure": [
      "simt-direct-gm",
      "size-gated-dispatch",
      "vec-fallback",
      "tensorlist-foreach"
    ]
  },
  "generality": "op_class",
  "id": "ELEM-SIMT-DIRECT-GM-GATE-BOUND",
  "implementation_steps": [
    "用完整 msprof 确认 SCALAR_BOUND（aiv_scalar_ratio ~100%）与引擎 idle，定位 per-tile 标量/地址/同步开销",
    "从 arch35 参考迁移 SIMT direct-GM kernel（线程按 GetThreadIdx/GetThreadNum 跨 GM 步进、fp32 中间计算、dtype 显式 cast），host 侧按 32B block 粒度 AssignDataToEachCore 平衡切分 per-core 张量区间",
    "host tiling 加 size-gated dispatch：totalElements >= SIMT_MIN_ELEMENTS 走 SIMT，否则保留 VEC 路径",
    "对全量 20 case 做 fingerprint-bounded clean 重采，逐 case 核对 speedup 与 regressed_cases",
    "出现任一 case < 0.95x 时按 dtype/pattern 收紧或分化 gate，或回退"
  ],
  "intent": "在保留 VEC 管线应对小/中数据 regime 的同时，用 SIMT direct-GM 消除大数据 regime 的 SCALAR_BOUND per-tile 标量/地址/同步开销；单一 2.2M 总元素 size gate 被实测证明无法覆盖 dtype 相关的 crossover。",
  "mechanism": "从 mainline-cann arch35 参考迁移 ForeachAddcdivScalarSimtKernel（__simt_vf__，按 Simt::GetThreadIdx/GetThreadNum 跨 GM 步进，fp32 中间计算 + dtype 显式 cast）与 Process per-core 张量区间循环；host tiling 按 totalElements >= SIMT_MIN_ELEMENTS(2,200,000) 派发 SIMT 否则保留 VEC。32B block 粒度元素平衡切分 AssignDataToEachCore；scalar 作为 Float attr 经 TilingData 传递（op_def 无 GM scalar 张量）；TensorList 基址经 ListTensorDesc::GetDataPtr(tensorIdx) 解析。kernel hash e8e64dc07bb37969（rounds/001 指纹）。",
  "name": "SIMT direct-GM 大数据机制与单一 size gate 过宽的负向边界",
  "op": "foreach_addcdiv_scalar",
  "operator_class": "fused-composite",
  "operator_scope": "SCALAR_BOUND 的 foreach/TensorList elementwise kernel（fp32/fp16/bf16 逐元素 x/scalar 复合算术，GE DYNAMIC_INPUT TensorList，host size-gated dispatch 在 SIMT direct-GM 与 VEC 双路径间按总元素数选择）",
  "principle": "SCALAR_BOUND 根因是 per-tile 的 SplitRowsToSegments、64-bit 地址运算、4x ListTensorDesc::GetDataPtr + SetGlobalBuffer 和串行 TQue EnQue/DeQue（msprof aiv_scalar_ratio 100%、VEC/MTE2/MTE3 idle ~99%）；SIMT direct-GM 移除全部这些开销。但 SIMT fp16 是 per-element 标量计算（3x __half2float + fp32 div/mul/add + 1x __float2half），成本近似线性于元素数；VEC 管线的 per-tile 标量开销随 size 超线性塌缩（fp16 case 2 的 VEC 12.58M 仍 ~453 GB/s、case 5 的 VEC 67M 塌缩到 ~81 GB/s），因此 SIMT-vs-VEC 的 crossover 依 dtype 不同——单一 2.2M gate 对 fp16 mid-size 过宽（回归）而对 fp32/bf16 正确（有收益）。",
  "related_anti_patterns": [],
  "risks": [
    "单一 size gate 对 fp16 mid-size multi-tensor 过宽会确认回归（本卡实证 0.7767x）——必须按 dtype 分化阈值",
    "SIMT 写 GM 可见性依赖框架刷新；不可见时需 threadfence/核间同步（lesson simt-write-to-mte-read-visibility）",
    "SIMT 标量上下文低精度转换必须用显式 intrinsic（lesson simt-lowprecision-scalar-cast-intrinsic），static_cast 实测产生 0",
    "大 case 增益若未出现（如 SIMT 直访 GM 成为带宽受限），SCALAR_BOUND 假设被证伪，需回退"
  ],
  "slug": "simt-direct-gm-size-gate-regression",
  "summary": "A5 SIMT direct-GM 数据流（SIMT 线程按 Simt::GetThreadIdx/GetThreadNum 直接跨 GM 步进，消除 per-tile 标量/地址/TQue-sync 开销）在大数据 regime 实测 10-23x 有效（case 4 23.24x、case 9 9.60x、case 5 2.40x、case 20 4.46x，均 stable 复现），但单一 SIMT_MIN_ELEMENTS=2,200,000 总元素 size gate 过宽：fp16 mid-size multi-tensor（case 2，12,582,912 总元素、3 tensor/list）在 SIMT 路径被确认回归 0.7767x（两轮独立测量 0.7786x/0.7767x，5 个重采样本 273.2-307.3us 高于紧致基线簇 219.3-223.4us cv 0.006）。负向边界：单一 size gate 不按 dtype 区分时对 fp16 mid-size 张量列表不安全；fp16 的 SIMT-vs-VEC crossover 位置高于 fp32/bf16（fp32 3.0M 起 SIMT 即 1.95x-23.24x、bf16 10.9M 平/16.8M 起 2.32x，而 fp16 12.58M 回归）。",
  "verification": {
    "correctness": [
      "rounds/001 verify 20/20 通过（kernel_hash e8e64dc07bb37969，与 build.json kernel_after 一致；fingerprint-bounded clean window）；fp32/fp16/bf16 均在 MERE/MARE 阈值内"
    ],
    "performance": [
      "大 case 稳定大幅改善且复现：case 4（fp32 67M）23.24x、case 9（bf16 99M）9.60x、case 5（fp16 67M）2.40x、case 20（fp32 10.5M）4.46x（case 4/5/9/20 cv 0.0006-0.0028）",
      "case 2（fp16 12.58M，SIMT 路径）确认回归 0.7767x（222.24->286.13us；首轮 0.7786x、clean 重采 0.7767x，5 样本 273.2-307.3us 23-38% 高于基线簇 219.3-223.4us cv 0.006）",
      "rounds/001/comparison.json：total_speedup 7.4203、improved 9、regressed 2（case 2 0.7767x 与 case 8 0.9173x，后者判为 VEC 未改码环境抖动）；注意 comparison.json ok=false 为结构性（冻结基线 stable=false），非本机制证据"
    ],
    "rollback_signals": [
      "任一 case 低于 0.95x 冻结基线（尤其小 case 若 gate 过松进入 SIMT 路径）",
      "fp16 mid-size multi-tensor 在 SIMT 路径回归（本卡实证 0.7767x）——应提高 fp16 gate 或按 dtype 分化",
      "正确性失败：fp16/bf16 必须 fp32 中间计算 + 显式 cast；SIMT 写不可见需 threadfence"
    ]
  }
}
-->

# 性能优化策略：SIMT direct-GM 大数据机制与单一 size gate 过宽的负向边界

单一优化点：A5 SIMT direct-GM 数据流（SIMT 线程按 Simt::GetThreadIdx/GetThreadNum 直接跨 GM 步进，消除 per-tile 标量/地址/TQue-sync 开销）在大数据 regime 实测 10-23x 有效（case 4 23.24x、case 9 9.60x、case 5 2.40x、case 20 4.46x，均 stable 复现），但单一 SIMT_MIN_ELEMENTS=2,200,000 总元素 size gate 过宽：fp16 mid-size multi-tensor（case 2，12,582,912 总元素、3 tensor/list）在 SIMT 路径被确认回归 0.7767x（两轮独立测量 0.7786x/0.7767x，5 个重采样本 273.2-307.3us 高于紧致基线簇 219.3-223.4us cv 0.006）。负向边界：单一 size gate 不按 dtype 区分时对 fp16 mid-size 张量列表不安全；fp16 的 SIMT-vs-VEC crossover 位置高于 fp32/bf16（fp32 3.0M 起 SIMT 即 1.95x-23.24x、bf16 10.9M 平/16.8M 起 2.32x，而 fp16 12.58M 回归）。

## 1. 原理

SCALAR_BOUND 根因是 per-tile 的 SplitRowsToSegments、64-bit 地址运算、4x ListTensorDesc::GetDataPtr + SetGlobalBuffer 和串行 TQue EnQue/DeQue（msprof aiv_scalar_ratio 100%、VEC/MTE2/MTE3 idle ~99%）；SIMT direct-GM 移除全部这些开销。但 SIMT fp16 是 per-element 标量计算（3x __half2float + fp32 div/mul/add + 1x __float2half），成本近似线性于元素数；VEC 管线的 per-tile 标量开销随 size 超线性塌缩（fp16 case 2 的 VEC 12.58M 仍 ~453 GB/s、case 5 的 VEC 67M 塌缩到 ~81 GB/s），因此 SIMT-vs-VEC 的 crossover 依 dtype 不同——单一 2.2M gate 对 fp16 mid-size 过宽（回归）而对 fp32/bf16 正确（有收益）。

实现机制：从 mainline-cann arch35 参考迁移 ForeachAddcdivScalarSimtKernel（__simt_vf__，按 Simt::GetThreadIdx/GetThreadNum 跨 GM 步进，fp32 中间计算 + dtype 显式 cast）与 Process per-core 张量区间循环；host tiling 按 totalElements >= SIMT_MIN_ELEMENTS(2,200,000) 派发 SIMT 否则保留 VEC。32B block 粒度元素平衡切分 AssignDataToEachCore；scalar 作为 Float attr 经 TilingData 传递（op_def 无 GM scalar 张量）；TensorList 基址经 ListTensorDesc::GetDataPtr(tensorIdx) 解析。kernel hash e8e64dc07bb37969（rounds/001 指纹）。

## 2. 性能问题模式

- 优化目标：在保留 VEC 管线应对小/中数据 regime 的同时，用 SIMT direct-GM 消除大数据 regime 的 SCALAR_BOUND per-tile 标量/地址/同步开销；单一 2.2M 总元素 size gate 被实测证明无法覆盖 dtype 相关的 crossover。
- 适用数据流：SCALAR_BOUND 的 foreach/TensorList elementwise kernel（fp32/fp16/bf16 逐元素 x/scalar 复合算术，GE DYNAMIC_INPUT TensorList，host size-gated dispatch 在 SIMT direct-GM 与 VEC 双路径间按总元素数选择）
- Feature signature：`{"bottleneck": ["scalar-bound", "per-tile-sync", "dtype-crossover", "size-gate-overbroad"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "simt-direct-gm-single-size-gate", "structure": ["simt-direct-gm", "size-gated-dispatch", "vec-fallback", "tensorlist-foreach"]}`

## 3. 正确性红线

- 单一 size gate 对 fp16 mid-size multi-tensor 过宽会确认回归（本卡实证 0.7767x）——必须按 dtype 分化阈值
- SIMT 写 GM 可见性依赖框架刷新；不可见时需 threadfence/核间同步（lesson simt-write-to-mte-read-visibility）
- SIMT 标量上下文低精度转换必须用显式 intrinsic（lesson simt-lowprecision-scalar-cast-intrinsic），static_cast 实测产生 0
- 大 case 增益若未出现（如 SIMT 直访 GM 成为带宽受限），SCALAR_BOUND 假设被证伪，需回退

资源与硬件约束：

- SIMT fp16 为 per-element 标量计算，成本近似线性于元素数；gate 阈值必须由 dtype 实测 crossover 界定（12.58M 回归、67M 2.40x 改善两个数据点夹出 fp16 gate）
- AssignDataToEachCore 退化（blockCount < needCoreNum）不可达：SIMT gate 要求 >=2.2M 元素，blockCount 远大于 needCoreNum
- SIMT 写 GM 依赖框架刷新可见性；若后续读/verify 不可见需加 threadfence/核间同步或回退

## 4. 泛化条件

- 策略作用域：op_class：fused-composite

适用：

- 设备 ascend950/A5（examples_a5、arch35 SIMT 路径可用，三个 dtype __simt_entry 符号编译成功）
- 瓶颈被完整 msprof 证实为 SCALAR_BOUND（aiv_scalar_ratio ~100%、VEC/MTE2/MTE3 idle ~99%），如 case 4/9
- SIMT 路径用 fp32 中间计算 + __half2float/__bfloat162float/__float2half/__float2bfloat16 显式 cast（lesson simt-lowprecision-scalar-cast-intrinsic），且 SIMT 写 GM 对后续 MTE 读可见（lesson simt-write-to-mte-read-visibility）
- size gate 必须按 dtype/pattern 区分——本卡证明单一 2.2M 总元素 gate 对 fp16 mid-size multi-tensor 过宽

不适用：

- fp16 mid-size multi-tensor foreach（如 12.58M 总元素、3 tensor/list）在单一 2.2M gate 下走 SIMT 会确认回归（实测 0.7767x）——必须留在 VEC 管线
- 不得把单一 size gate 外推为通用规则：fp16 与 fp32/bf16 的 crossover 不同（fp16 需更高 gate；fp32/bf16 自 2.2M 起 SIMT 即有收益）
- 形式验收要求两侧 stable 样本：当 run 的冻结 baseline/performance.json 不可变地 stable=false 时，确定性 compare gate 对本 run 任意一轮恒返回 rejected——这是验收环境边界，与机制边界正交

## 5. 实施步骤

1. 用完整 msprof 确认 SCALAR_BOUND（aiv_scalar_ratio ~100%）与引擎 idle，定位 per-tile 标量/地址/同步开销
2. 从 arch35 参考迁移 SIMT direct-GM kernel（线程按 GetThreadIdx/GetThreadNum 跨 GM 步进、fp32 中间计算、dtype 显式 cast），host 侧按 32B block 粒度 AssignDataToEachCore 平衡切分 per-core 张量区间
3. host tiling 加 size-gated dispatch：totalElements >= SIMT_MIN_ELEMENTS 走 SIMT，否则保留 VEC 路径
4. 对全量 20 case 做 fingerprint-bounded clean 重采，逐 case 核对 speedup 与 regressed_cases
5. 出现任一 case < 0.95x 时按 dtype/pattern 收紧或分化 gate，或回退

## 6. LLM 前置问题

- 目标实现是否满足：设备 ascend950/A5（examples_a5、arch35 SIMT 路径可用，三个 dtype __simt_entry 符号编译成功）？
- 目标实现是否满足：瓶颈被完整 msprof 证实为 SCALAR_BOUND（aiv_scalar_ratio ~100%、VEC/MTE2/MTE3 idle ~99%），如 case 4/9？
- 目标实现是否满足：SIMT 路径用 fp32 中间计算 + __half2float/__bfloat162float/__float2half/__float2bfloat16 显式 cast（lesson simt-lowprecision-scalar-cast-intrinsic），且 SIMT 写 GM 对后续 MTE 读可见（lesson simt-write-to-mte-read-visibility）？
- 是否命中排除条件：fp16 mid-size multi-tensor foreach（如 12.58M 总元素、3 tensor/list）在单一 2.2M gate 下走 SIMT 会确认回归（实测 0.7767x）——必须留在 VEC 管线？

## 7. 验收标准

正确性：

- rounds/001 verify 20/20 通过（kernel_hash e8e64dc07bb37969，与 build.json kernel_after 一致；fingerprint-bounded clean window）；fp32/fp16/bf16 均在 MERE/MARE 阈值内

性能：

- 大 case 稳定大幅改善且复现：case 4（fp32 67M）23.24x、case 9（bf16 99M）9.60x、case 5（fp16 67M）2.40x、case 20（fp32 10.5M）4.46x（case 4/5/9/20 cv 0.0006-0.0028）
- case 2（fp16 12.58M，SIMT 路径）确认回归 0.7767x（222.24->286.13us；首轮 0.7786x、clean 重采 0.7767x，5 样本 273.2-307.3us 23-38% 高于基线簇 219.3-223.4us cv 0.006）
- rounds/001/comparison.json：total_speedup 7.4203、improved 9、regressed 2（case 2 0.7767x 与 case 8 0.9173x，后者判为 VEC 未改码环境抖动）；注意 comparison.json ok=false 为结构性（冻结基线 stable=false），非本机制证据

回滚信号：

- 任一 case 低于 0.95x 冻结基线（尤其小 case 若 gate 过松进入 SIMT 路径）
- fp16 mid-size multi-tensor 在 SIMT 路径回归（本卡实证 0.7767x）——应提高 fp16 gate 或按 dtype 分化
- 正确性失败：fp16/bf16 必须 fp32 中间计算 + 显式 cast；SIMT 写不可见需 threadfence

## 8. 分类与证据

- Classification：`negative_boundary`
- Generality：`op_class`
- Related anti-patterns：无

- foreach_addcdiv_scalar-20260823_153850-4ed096（round=1, status=rejected）

## 检索卡（短卡）

动作：将过宽的单一总元素 size gate 改为按 dtype 分化，并验证回退边界。
适用：ascend950/A5、arch35 SIMT 路径且目标 dtype 有 __simt_entry，并经完整分析确认瓶颈。
限制：门控必须按 dtype 分化并验证回退边界；须确认相关开销主导且其他引擎空闲。
范围：elementwise-arithmetic 的 SIMT 路由、dtype 与 size
检索词：SIMT direct-GM、size gate、SCALAR_BOUND、SplitRowsToSegments、TQue EnQue/DeQue
机会：每 tile 的切分、64 位寻址、描述符绑定及串行队列操作形成标量瓶颈。
代价：不同 dtype 的 SIMT/VEC 交叉区间不同；fp16 标量成本近似随元素数线性增长。
