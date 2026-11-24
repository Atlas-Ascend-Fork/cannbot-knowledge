---
type: Optimization
title: 输出 dtype 分层去补偿：bf16 核 hi-only 平坦扫描，fp32 核逐字保留补偿路径
description: 把补偿扫描按输出 dtype 分层，低精度档核整档改为 hi-only 平坦扫描，fp32 档逐字保留补偿路径。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/outdtype-tiered-uncompensated-scan.md
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
      "分层只能落在编译期 dtype 分支（bf16 专属 hi-only 核 + fp32/fp16 逐字保留），不得引入运行期 dtype 判定",
      "hi-only 扫描必须复用既有的 hi 乒乓结构与 SHIFT_ALIGNED 合并 Add 语义，使 hi 通道逐位不变；新增原语只允许删 lo 侧算术，不得改 hi 侧数据流",
      "lo 侧的四处删除（loA/loB 全缓冲清零、lo 通道 load/store、segLo 标量读、two-sum carry 更新）必须整档一致，缺一处即产生非对称残差",
      "精度门按 dtype 逐档把关：bf16/fp16 的 mere/mare 阈值（2^-7/2^-10）与 atol/rtol 辅判据（1e-2/1e-3）必须逐 case 通过，可降档范围以实测精度为准而不是以尾数位宽推断"
    ],
    "excluded_conditions": [
      "输出为 fp32（或任何未量化输出）时不适用：fp32 mere 限 2^-13=1.2e-4 距 plain fp32 对数深度扫描误差仅约 1 个数量级，补偿不可删",
      "该 dtype 档的精度门余量小于 plain 扫描误差时不适用：本 run fp16 case 10（y=±65504，partials 游走 ~1e6 相消）即为该形态，plain-scan 误差 ~1.4e-2 rel 超 atol 1e-3",
      "按累加深度分桶但仍保留 Kahan 补偿的路线（multi-accumulator-compensated-sum-bucket-dispatch，dtype 无关）与按特殊值/有限值域触发分域的路线（dd-compensated-finite-domain-scan）都不属于本机制：本机制不引入运行期门控、不改变数值域，只做编译期 dtype 分层"
    ],
    "required_conditions": [
      "输出经 CAST_RINT 量化到低精度档，使量化噪声显著高于 plain fp32 对数深度扫描误差（本 run 论证：输出量化噪声 ~2^-9/2^-12 相对量级 vs plain fp32 Hillis-Steele 误差 ~eps*log2(n)*cond ≈ 1e-6~1e-5 相对，低 2-3 个数量级）",
      "补偿通道在扫描步里占可观份额且向量管是实测瓶颈：本 run 每 64-lane 块每步 ~22 条向量操作中 ~14 条用于 two-sum 补偿与 lo 通道（4 load + 2 store + 6 two-sum sub/add + ZeroBadLo 8 操作），另有每段/每行 2 次 lo 缓冲 Duplicate 清零（65 块/次）",
      "存在可按输出 dtype 切开的编译期分支，使被保档位能逐字保留：本 run fp32 分支与 champion 逐字相同，fp16 经 case 10 教训也回退到同一档，成功后 fp16 均值不变、fp32 均值落在噪声内",
      "存在分档验证的精度门：bf16 档在本 run 20/20；fp16 档在极端动态范围（±65504）下必须单独验证后才允许降档"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-18",
  "evidence": [
    {
      "operator": "cumulativetrapezoid",
      "operator_class": "scan-reduce",
      "precision": "20/20 PASS（1 次修复：首版 bf16+fp16 双降档为 19/20，唯一失败集 {10} fp16 y=±65504、plain-scan 误差 ~1.4e-2 rel 超 atol/rtol 1e-3；repair 1 把分层条件从『非 fp32』收紧为『仅 bf16』后 20/20）",
      "run_id": "<run-id>",
      "speedup": 1.1509,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-alu-bound",
      "two-sum-compensation-vector-overhead",
      "output-dtype-quantization-slack"
    ],
    "dtypes": [
      "bf16",
      "fp16",
      "fp32"
    ],
    "pattern": "outdtype-tiered-uncompensated-scan",
    "reduce_mode": "hillis-steele-prefix-scan",
    "structure": [
      "output-dtype-tiered-compile-time-branch",
      "hi-only-scan-step-core",
      "lo-channel-elision",
      "plain-fp32-scalar-carry",
      "fp32-compensated-path-verbatim"
    ]
  },
  "generality": "op_class",
  "id": "SCAN-DTYPE-TIERED-UNCOMPENSATED",
  "implementation_steps": [
    "在 impl 内新增 hi-only 原语 ScanHiBlockCore<SHIFT_ALIGNED>（Move + MERGING Add + Store，~4 向量操作/块/步）与 ScanHiStepFullVF / ScanHiStepPartialVF / CopyHiBlocksVF / RunScanHi，hi 乒乓结构保持不变",
    "新增 RunCarryAddFinalizeHi 把 finalize 平凡化为 out = hi + carry，并把 CarryAddFinalizeHiVF 中 carry 的 Duplicate 提升到块循环外",
    "Compute/ComputeRowBatch 按输出 dtype 分层：bf16 档跳过 loA/loB 全缓冲清零与整条 lo 通道、省略 segLo 读、carry 改为 plain fp32 标量加；fp32（以及回退后的 fp16）走 champion 原分支",
    "把分层条件写成编译期 dtype 分支且只覆盖精度已验证的档位（本 run 最终为仅 bf16），使 fp32 路径逐字保留、零回归面",
    "以分档精度门 + 6 对平衡交替 msprof 配对验收：先看各档精度是否守住，再看逐对 ratio 的方向一致性与离散（本 run <0.06%）；任一档精度下滑就单独把该档退回补偿路径而不是整机制回滚"
  ],
  "intent": "按输出 dtype 分层删减扫描补偿算术：bf16 核整档走 hi-only 平坦 Hillis-Steele（去掉 two-sum / lo 通道 / lo 缓冲清零 / ZeroBadLo），fp32 核（以及精度验证未过的 fp16 核）逐字保留全补偿路径；目标是砍掉补偿通道在 vec-alu 上的可观份额（每 64-lane 块每步 ~22 条向量操作中 ~14 条用于 two-sum 与 lo 通道，另有每段/每行 2 次 lo 缓冲清零），把省下的发射直接兑现为任务时长。",
  "mechanism": "output-dtype-tiered compensation elimination。bf16 档：新增 hi-only 原语 ScanHiBlockCore<SHIFT_ALIGNED>（Move + MERGING Add + Store，~4 向量操作/块/步，对比补偿版 ~22），并配 ScanHiStepFullVF / ScanHiStepPartialVF / CopyHiBlocksVF / RunScanHi，hi 乒乓结构不变；新增 RunCarryAddFinalizeHi 把 finalize 退化为 out = hi + carry，CarryAddFinalizeHiVF 内 carry 的 Duplicate 提升到块循环外；Compute/ComputeRowBatch 在 bf16 档跳过 loA/loB 全缓冲清零与整条 lo 通道、省略 segLo 读、carry 改为 plain fp32 标量加。fp32 档（以及修复后的 fp16 档）分支与 champion 逐字相同。分层条件是编译期 dtype 分支而非运行期判定。首版把 fp16 一起降档 -> 19/20（case 10 fp16 y=±65504，plain-scan 误差 1.4e-2 rel 超 atol 1e-3），repair 1 把分层条件从『非 fp32』收紧为『仅 bf16』后 20/20；首版与 repair 1 均一次编译通过。",
  "name": "输出 dtype 分层去补偿：bf16 核 hi-only 平坦扫描，fp32 核逐字保留补偿路径",
  "operator_class": "scan-reduce",
  "operator_scope": "输出经量化落盘、且补偿通道（two-sum + lo 通道 + 每步防御指令 + lo 缓冲清零）在向量管上占可观份额的补偿扫描类算子；本 run 为 cumulativetrapezoid（ascend950dt_9582，20 case 聚合为 3 个 dtype case，冻结基线 bf16 428.39 / fp16 85.75 / fp32 327.77us），最重 case 为 bf16 单行 N=1000002（占总时长 37%）",
  "principle": "补偿扫描的第一个杠杆不是把补偿做得更便宜，而是先问这个输出精度档是否根本不需要补偿：输出经 CAST_RINT 落到 bf16 后，量化噪声本身就是 ~2^-9 相对量级，而 plain fp32 对数深度 Hillis-Steele 扫描误差只有 ~eps*log2(n)*cond ≈ 1e-6~1e-5 相对——低 2-3 个数量级，补偿通道修掉的那点误差连最终输出的一位都影响不到。fp32 输出则完全不同：其 mere 限 2^-13=1.2e-4 只比 plain 扫描误差高约 1 个数量级，补偿不能删。因此这是一个纯按输出 dtype 分层的决策：低精度档整档走 hi-only，fp32 档逐字保留。它与按累加深度分桶的 multi-accumulator-compensated-sum-bucket-dispatch 不同——那条路线键在累加深度上、且无论 dtype 一律保留 Kahan 补偿；也与 dd-compensated-finite-domain-scan 不同——那条路线由特殊值/有限值域触发，普通路径仍带补偿。本机制不改变数值域、不引入运行期门控、不引入任何新的标量读或屏障依赖，只做编译期 dtype 分层删算术。",
  "related_anti_patterns": [
    "multi-accumulator-compensated-sum-bucket-dispatch",
    "dd-compensated-finite-domain-scan"
  ],
  "risks": [
    "『输出量化噪声淹没扫描误差』的论证必须按 dtype 的 atol/rtol 与数据动态范围逐一验证，不能只看尾数位宽：本 run 首版把 fp16 与 bf16 一起降档，case 10（fp16，y=±65504，partials 游走 ~1e6 相消）plain-scan 误差 ~1.4e-2 rel 超 atol/rtol 1e-3，精度 19/20；收紧为仅 bf16 后才 20/20 —— fp16 在极端动态范围下不可降档",
    "fp32 分支逐字保留是零回归面与收益归因的共同前提：本 run fp32 case 均值 327.7742 -> 326.7454us 落在噪声内、fp16 回退补偿档后 85.751 -> 85.8379us 不变，正是『收益来自 bf16 档被删除的补偿算术』的对照证据；任何对公共路径的顺手改动都会同时破坏这两点",
    "四处删除必须整档一致：loA/loB 全缓冲清零（每段/每行 2 次 Duplicate，65 块/次）、lo 通道 load/store、segLo 的标量读、two-sum carry 更新——漏改一处只产生非对称残差而不报错",
    "hi-only 原语必须复用原 hi 乒乓结构与 mask/UpdateMask 语义（ScanHiBlockCore<SHIFT_ALIGNED> = Move + MERGING Add + Store），一旦顺带改结构就会落入 direction_001 的坑（intra-seg 两级化因工具链标量读限制失败），把『零工具链风险』的前提丢掉",
    "收益集中在 bf16 扫描重型 case（c12 2129->1389us、c3 155->104us、c16 122->84us、c19 78->55us），bf16 短行 case 的补偿占比本就较低（c6 46->34us、c9 54->38us），这类 case 的收益空间有限"
  ],
  "slug": "outdtype-tiered-uncompensated-scan",
  "summary": "对补偿（two-sum）Hillis-Steele 前缀扫描按输出 dtype 分层去补偿：bf16 核整档走 hi-only 平坦扫描（ScanHiBlockCore ~4 向量操作/块/步，无 lo 通道、无 lo 缓冲清零、无 ZeroBadLo，carry 为 plain fp32 标量加，finalize 退化为 out = hi + carry），fp32 核逐字保留全补偿路径，fp16 因 case 10（y=±65504、partials ~1e6 相消，plain-scan 误差 1.4e-2 rel > atol 1e-3）在 1 次修复后回退补偿档。两级聚合 geomean 229.2016 -> 199.1544us = 1.1509x（12 次独立 msprof / 6 对，ratio 1.1506-1.1512，离散 <0.06%），bf16 档均值 428.39 -> 281.63us，fp16/fp32 在噪声内不变，精度 20/20 PASS。",
  "verification": {
    "correctness": [
      "最终 20/20 PASS（1 次修复）；首版 bf16+fp16 双降档为 19/20，唯一失败集 {10}（fp16 y=±65504）",
      "fp32 路径逐字未动：fp32 case 均值 327.7742 -> 326.7454us（噪声内）；fp16 回退补偿档后 85.751 -> 85.8379us（不变）",
      "bf16 全部扫描重型 case 一致下降：c12 2129->1389us、c3 155->104us、c16 122->84us、c19 78->55us、c6 46->34us、c9 54->38us",
      "首版与 repair 1 均一次编译通过（0 编译修复消耗）"
    ],
    "performance": [
      "formal 12 次独立 msprof / 6 对，顺序 A,B,B,A,A,B,B,A,B,A,A,B（3 个平衡交替块）；双 .so 独立构建（sha256 不同）、同 device_id=3、同 SoC、同 CANN 9.1.0，same_shape / provenance_clean / balanced_alternating_order / correlation_unambiguous 全部成立",
      "两级聚合 geomean 229.2016 -> 199.1544us（speedup 1.1509，improvement 13.11%），6 对 ratio 1.1506-1.1512，离散 <0.06%",
      "按 dtype 均值：bf16 428.3894 -> 281.6313us、fp16 85.751 -> 85.8379us、fp32 327.7742 -> 326.7454us",
      "冻结基线单次复测 229.7708us 与 direction_001 基线 229.806us 一致（+0.015%）；首版双降档探测 geomean 176.244us（相对基线 229.7708 为 -23.3%）确认可见收益后才进入精度修复"
    ],
    "rollback_signals": [
      "任一 dtype case 的精度跌破该档门槛（本 run 形态：fp16 case 10 plain-scan 误差 1.4e-2 rel > atol 1e-3）-> 只把该档退回补偿路径",
      "fp32 分支不再与 champion 逐字相同，或未降档 dtype 的均值走出噪声",
      "6 对配对 ratio 的离散显著大于 0.06%，或存在方向不一致的配对",
      "hi 通道出现与 lo 通道删除无关的差异（说明 hi-only 原语没有复用同一乒乓/mask 语义）"
    ]
  }
}
-->

# 性能优化策略：输出 dtype 分层去补偿：bf16 核 hi-only 平坦扫描，fp32 核逐字保留补偿路径

对补偿（two-sum）Hillis-Steele 前缀扫描按输出 dtype 分层去补偿：bf16 核整档走 hi-only 平坦扫描（ScanHiBlockCore ~4 向量操作/块/步，无 lo 通道、无 lo 缓冲清零、无 ZeroBadLo，carry 为 plain fp32 标量加，finalize 退化为 out = hi + carry），fp32 核逐字保留全补偿路径，fp16 因 case 10（y=±65504、partials ~1e6 相消，plain-scan 误差 1.4e-2 rel > atol 1e-3）在 1 次修复后回退补偿档。两级聚合 geomean 229.2016 -> 199.1544us = 1.1509x（12 次独立 msprof / 6 对，ratio 1.1506-1.1512，离散 <0.06%），bf16 档均值 428.39 -> 281.63us，fp16/fp32 在噪声内不变，精度 20/20 PASS。

## 1. 原理

补偿扫描的第一个杠杆不是把补偿做得更便宜，而是先问这个输出精度档是否根本不需要补偿：输出经 CAST_RINT 落到 bf16 后，量化噪声本身就是 ~2^-9 相对量级，而 plain fp32 对数深度 Hillis-Steele 扫描误差只有 ~eps*log2(n)*cond ≈ 1e-6~1e-5 相对——低 2-3 个数量级，补偿通道修掉的那点误差连最终输出的一位都影响不到。fp32 输出则完全不同：其 mere 限 2^-13=1.2e-4 只比 plain 扫描误差高约 1 个数量级，补偿不能删。因此这是一个纯按输出 dtype 分层的决策：低精度档整档走 hi-only，fp32 档逐字保留。它与按累加深度分桶的 multi-accumulator-compensated-sum-bucket-dispatch 不同——那条路线键在累加深度上、且无论 dtype 一律保留 Kahan 补偿；也与 dd-compensated-finite-domain-scan 不同——那条路线由特殊值/有限值域触发，普通路径仍带补偿。本机制不改变数值域、不引入运行期门控、不引入任何新的标量读或屏障依赖，只做编译期 dtype 分层删算术。

实现机制：output-dtype-tiered compensation elimination。bf16 档：新增 hi-only 原语 ScanHiBlockCore<SHIFT_ALIGNED>（Move + MERGING Add + Store，~4 向量操作/块/步，对比补偿版 ~22），并配 ScanHiStepFullVF / ScanHiStepPartialVF / CopyHiBlocksVF / RunScanHi，hi 乒乓结构不变；新增 RunCarryAddFinalizeHi 把 finalize 退化为 out = hi + carry，CarryAddFinalizeHiVF 内 carry 的 Duplicate 提升到块循环外；Compute/ComputeRowBatch 在 bf16 档跳过 loA/loB 全缓冲清零与整条 lo 通道、省略 segLo 读、carry 改为 plain fp32 标量加。fp32 档（以及修复后的 fp16 档）分支与 champion 逐字相同。分层条件是编译期 dtype 分支而非运行期判定。首版把 fp16 一起降档 -> 19/20（case 10 fp16 y=±65504，plain-scan 误差 1.4e-2 rel 超 atol 1e-3），repair 1 把分层条件从『非 fp32』收紧为『仅 bf16』后 20/20；首版与 repair 1 均一次编译通过。

## 2. 性能问题模式

- 优化目标：按输出 dtype 分层删减扫描补偿算术：bf16 核整档走 hi-only 平坦 Hillis-Steele（去掉 two-sum / lo 通道 / lo 缓冲清零 / ZeroBadLo），fp32 核（以及精度验证未过的 fp16 核）逐字保留全补偿路径；目标是砍掉补偿通道在 vec-alu 上的可观份额（每 64-lane 块每步 ~22 条向量操作中 ~14 条用于 two-sum 与 lo 通道，另有每段/每行 2 次 lo 缓冲清零），把省下的发射直接兑现为任务时长。
- 适用数据流：输出经量化落盘、且补偿通道（two-sum + lo 通道 + 每步防御指令 + lo 缓冲清零）在向量管上占可观份额的补偿扫描类算子；本 run 为 cumulativetrapezoid（ascend950dt_9582，20 case 聚合为 3 个 dtype case，冻结基线 bf16 428.39 / fp16 85.75 / fp32 327.77us），最重 case 为 bf16 单行 N=1000002（占总时长 37%）
- Feature signature：`{"bottleneck": ["vec-alu-bound", "two-sum-compensation-vector-overhead", "output-dtype-quantization-slack"], "dtypes": ["bf16", "fp16", "fp32"], "pattern": "outdtype-tiered-uncompensated-scan", "reduce_mode": "hillis-steele-prefix-scan", "structure": ["output-dtype-tiered-compile-time-branch", "hi-only-scan-step-core", "lo-channel-elision", "plain-fp32-scalar-carry", "fp32-compensated-path-verbatim"]}`

## 3. 正确性红线

- 『输出量化噪声淹没扫描误差』的论证必须按 dtype 的 atol/rtol 与数据动态范围逐一验证，不能只看尾数位宽：本 run 首版把 fp16 与 bf16 一起降档，case 10（fp16，y=±65504，partials 游走 ~1e6 相消）plain-scan 误差 ~1.4e-2 rel 超 atol/rtol 1e-3，精度 19/20；收紧为仅 bf16 后才 20/20 —— fp16 在极端动态范围下不可降档
- fp32 分支逐字保留是零回归面与收益归因的共同前提：本 run fp32 case 均值 327.7742 -> 326.7454us 落在噪声内、fp16 回退补偿档后 85.751 -> 85.8379us 不变，正是『收益来自 bf16 档被删除的补偿算术』的对照证据；任何对公共路径的顺手改动都会同时破坏这两点
- 四处删除必须整档一致：loA/loB 全缓冲清零（每段/每行 2 次 Duplicate，65 块/次）、lo 通道 load/store、segLo 的标量读、two-sum carry 更新——漏改一处只产生非对称残差而不报错
- hi-only 原语必须复用原 hi 乒乓结构与 mask/UpdateMask 语义（ScanHiBlockCore<SHIFT_ALIGNED> = Move + MERGING Add + Store），一旦顺带改结构就会落入 direction_001 的坑（intra-seg 两级化因工具链标量读限制失败），把『零工具链风险』的前提丢掉
- 收益集中在 bf16 扫描重型 case（c12 2129->1389us、c3 155->104us、c16 122->84us、c19 78->55us），bf16 短行 case 的补偿占比本就较低（c6 46->34us、c9 54->38us），这类 case 的收益空间有限

资源与硬件约束：

- 分层只能落在编译期 dtype 分支（bf16 专属 hi-only 核 + fp32/fp16 逐字保留），不得引入运行期 dtype 判定
- hi-only 扫描必须复用既有的 hi 乒乓结构与 SHIFT_ALIGNED 合并 Add 语义，使 hi 通道逐位不变；新增原语只允许删 lo 侧算术，不得改 hi 侧数据流
- lo 侧的四处删除（loA/loB 全缓冲清零、lo 通道 load/store、segLo 标量读、two-sum carry 更新）必须整档一致，缺一处即产生非对称残差
- 精度门按 dtype 逐档把关：bf16/fp16 的 mere/mare 阈值（2^-7/2^-10）与 atol/rtol 辅判据（1e-2/1e-3）必须逐 case 通过，可降档范围以实测精度为准而不是以尾数位宽推断

## 4. 泛化条件

- 策略作用域：op_class：scan-reduce

适用：

- 输出经 CAST_RINT 量化到低精度档，使量化噪声显著高于 plain fp32 对数深度扫描误差（本 run 论证：输出量化噪声 ~2^-9/2^-12 相对量级 vs plain fp32 Hillis-Steele 误差 ~eps*log2(n)*cond ≈ 1e-6~1e-5 相对，低 2-3 个数量级）
- 补偿通道在扫描步里占可观份额且向量管是实测瓶颈：本 run 每 64-lane 块每步 ~22 条向量操作中 ~14 条用于 two-sum 补偿与 lo 通道（4 load + 2 store + 6 two-sum sub/add + ZeroBadLo 8 操作），另有每段/每行 2 次 lo 缓冲 Duplicate 清零（65 块/次）
- 存在可按输出 dtype 切开的编译期分支，使被保档位能逐字保留：本 run fp32 分支与 champion 逐字相同，fp16 经 case 10 教训也回退到同一档，成功后 fp16 均值不变、fp32 均值落在噪声内
- 存在分档验证的精度门：bf16 档在本 run 20/20；fp16 档在极端动态范围（±65504）下必须单独验证后才允许降档

不适用：

- 输出为 fp32（或任何未量化输出）时不适用：fp32 mere 限 2^-13=1.2e-4 距 plain fp32 对数深度扫描误差仅约 1 个数量级，补偿不可删
- 该 dtype 档的精度门余量小于 plain 扫描误差时不适用：本 run fp16 case 10（y=±65504，partials 游走 ~1e6 相消）即为该形态，plain-scan 误差 ~1.4e-2 rel 超 atol 1e-3
- 按累加深度分桶但仍保留 Kahan 补偿的路线（multi-accumulator-compensated-sum-bucket-dispatch，dtype 无关）与按特殊值/有限值域触发分域的路线（dd-compensated-finite-domain-scan）都不属于本机制：本机制不引入运行期门控、不改变数值域，只做编译期 dtype 分层

## 5. 实施步骤

1. 在 impl 内新增 hi-only 原语 ScanHiBlockCore<SHIFT_ALIGNED>（Move + MERGING Add + Store，~4 向量操作/块/步）与 ScanHiStepFullVF / ScanHiStepPartialVF / CopyHiBlocksVF / RunScanHi，hi 乒乓结构保持不变
2. 新增 RunCarryAddFinalizeHi 把 finalize 平凡化为 out = hi + carry，并把 CarryAddFinalizeHiVF 中 carry 的 Duplicate 提升到块循环外
3. Compute/ComputeRowBatch 按输出 dtype 分层：bf16 档跳过 loA/loB 全缓冲清零与整条 lo 通道、省略 segLo 读、carry 改为 plain fp32 标量加；fp32（以及回退后的 fp16）走 champion 原分支
4. 把分层条件写成编译期 dtype 分支且只覆盖精度已验证的档位（本 run 最终为仅 bf16），使 fp32 路径逐字保留、零回归面
5. 以分档精度门 + 6 对平衡交替 msprof 配对验收：先看各档精度是否守住，再看逐对 ratio 的方向一致性与离散（本 run <0.06%）；任一档精度下滑就单独把该档退回补偿路径而不是整机制回滚

## 6. LLM 前置问题

- 目标实现是否满足：输出经 CAST_RINT 量化到低精度档，使量化噪声显著高于 plain fp32 对数深度扫描误差（本 run 论证：输出量化噪声 ~2^-9/2^-12 相对量级 vs plain fp32 Hillis-Steele 误差 ~1e-6~1e-5 相对，低 2-3 个数量级）？
- 目标实现是否满足：补偿通道在扫描步里占可观份额且向量管是实测瓶颈（本 run 每 64-lane 块每步 ~22 条向量操作中 ~14 条用于 two-sum 补偿与 lo 通道）？
- 目标实现是否满足：存在可按输出 dtype 切开的编译期分支，使被保档位能逐字保留？
- 目标实现是否满足：存在分档验证的精度门，且待降档的 dtype 在极端动态范围下已单独验证？
- 是否命中排除条件：输出为 fp32（或任何未量化输出）时不适用？
- 是否命中排除条件：该 dtype 档的精度门余量小于 plain 扫描误差时不适用（如本 run fp16 case 10）？
- 是否命中排除条件：按累加深度分桶仍保留 Kahan 补偿、或按特殊值/有限值域触发分域的路线不属于本机制？

## 7. 验收标准

正确性：

- 最终 20/20 PASS（1 次修复）；首版 bf16+fp16 双降档为 19/20，唯一失败集 {10}（fp16 y=±65504）
- fp32 路径逐字未动：fp32 case 均值 327.7742 -> 326.7454us（噪声内）；fp16 回退补偿档后 85.751 -> 85.8379us（不变）
- bf16 全部扫描重型 case 一致下降：c12 2129->1389us、c3 155->104us、c16 122->84us、c19 78->55us、c6 46->34us、c9 54->38us
- 首版与 repair 1 均一次编译通过（0 编译修复消耗）

性能：

- formal 12 次独立 msprof / 6 对，顺序 A,B,B,A,A,B,B,A,B,A,A,B（3 个平衡交替块）；双 .so 独立构建（sha256 不同）、同 device_id=3、同 SoC、同 CANN 9.1.0，same_shape / provenance_clean / balanced_alternating_order / correlation_unambiguous 全部成立
- 两级聚合 geomean 229.2016 -> 199.1544us（speedup 1.1509，improvement 13.11%），6 对 ratio 1.1506-1.1512，离散 <0.06%
- 按 dtype 均值：bf16 428.3894 -> 281.6313us、fp16 85.751 -> 85.8379us、fp32 327.7742 -> 326.7454us
- 冻结基线单次复测 229.7708us 与 direction_001 基线 229.806us 一致（+0.015%）；首版双降档探测 geomean 176.244us（相对基线 229.7708 为 -23.3%）确认可见收益后才进入精度修复

回滚信号：

- 任一 dtype case 的精度跌破该档门槛（本 run 形态：fp16 case 10 plain-scan 误差 1.4e-2 rel > atol 1e-3）-> 只把该档退回补偿路径
- fp32 分支不再与 champion 逐字相同，或未降档 dtype 的均值走出噪声
- 6 对配对 ratio 的离散显著大于 0.06%，或存在方向不一致的配对
- hi 通道出现与 lo 通道删除无关的差异（说明 hi-only 原语没有复用同一乒乓/mask 语义）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：multi-accumulator-compensated-sum-bucket-dispatch, dd-compensated-finite-domain-scan

- loop_20260917_024611（round=01, status=accepted, speedup=1.1509, precision=20/20 PASS（1 次修复：首版 bf16+fp16 双降档为 19/20，唯一失败集 {10} fp16 y=±65504、plain-scan 误差 ~1.4e-2 rel 超 atol/rtol 1e-3；repair 1 把分层条件从『非 fp32』收紧为『仅 bf16』后 20/20））

## 检索卡（短卡）

动作：把补偿扫描按输出 dtype 分层，低精度档核整档改为 hi-only 平坦扫描，fp32 档逐字保留补偿路径
适用：输出经 CAST_RINT 量化到低精度档且量化噪声低 2-3 个数量级；补偿占每步约 22 条向量操作中约 14 条
限制：分层须落编译期 dtype 分支；四处删除（清零、load/store、segLo 读、carry 更新）须整档一致；fp16 极端动态范围不可降档
范围：输出经量化落盘的补偿扫描类算子分档核
检索词：ScanHiBlockCore、CAST_RINT、ZeroBadLo、two-sum、RunCarryAddFinalizeHi、hi-only
机会：每 64-lane 块每步约 22 条向量操作中约 14 条用于 two-sum 与 lo 通道，另有每行 2 次 lo 缓冲清零
代价：收益集中在扫描重型 case，短行 case 的补偿占比本就低，收益空间有限
