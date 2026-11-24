---
type: Optimization
title: 2B dtype 行打包扫描的 u32 双位置打包（每 lane 承载同一行 2 个连续扫描位置，Gather/Scatter 全 B32 粒度）
description: 把 2B dtype 行打包扫描改为每 u32 lane 承载同一行相邻 2 个扫描位置，Gather/Scatter/Pack 全升 B32 粒度。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/subword-u32-pair-packed-scan.md
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
      "Pack<u16,u32,HIGHEST> 在 arch3510/CANN 9.1.0 不可用于 u32->u16 高半提取：高半不落 half-slot（hi 侧比较恒见 +0.0，奇数位更新静默丢失，行内自第一个奇位最小值起 carry 停滞）——高半提取必须用 ShiftRights<u32> + Pack<LOWEST>",
      "谓词按 slot 索引：b16 bit i 对应 half-slot i，b32 lane k 读 bit k，两种粒度不可混用",
      "Interleave<u16> 语义为 dst0[2j]=s0[j]、dst0[2j+1]=s1[j]（u32 lane k = {s0[k], s1[k]}），落位顺序必须以诊断探针反证而非假设"
    ],
    "excluded_conditions": [
      "4B dtype：单位置形态已是 B32 粒度，pair 无增益",
      "host tiling 不可表达 pair 步进而必须新增推导时，先补 tiling 侧证据再实施"
    ],
    "required_conditions": [
      "行并行 lane 打包骨架已存在并被接受（见 row-per-lane-packed-scan）",
      "sizeof(DX)==2（fp16/bf16）且扫描位置可按偶/奇成对（尾奇数位置走既有尾处理）",
      "出口写回布局可用 Interleave 类原语恢复元素交错（或已有等价已验证载体）"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "case": "fp16/bf16 T1 last-axis 子集（level2/cummin_1/3/7/11/18/20）",
      "note": "correctness 20/20；control 0.9797-1.0082（fp32 已接纳路径字节级不动得到确认）。正确性故障与修复：中断前 kernel 用 Pack<u16,u32,HIGHEST> 构造 hi 半槽，arch3510/CANN 9.1.0 实测该原语不把高半放入 half-slot 0..63（奇数位更新静默丢失 -> 行内 carry 停滞，diag：row0 first-bad=7），修复为 Pack<LOWEST>(ShiftRights<u32>(pair,16)) 后 1 个 build 周期通过全量验证。硬件语义事实：谓词按 slot 索引（b16 bit i = half-slot i，b32 lane k 读 bit k）；Interleave<u16> dst0[2j]=s0[j]/dst0[2j+1]=s1[j]。",
      "operator_class": "reduction",
      "round": 2,
      "run_id": "<run-id>",
      "speedup": "dt=2 目标 case 全部 2.2253-2.6229x、route subset 2.4849x；incremental 1.0738x、cumulative 1.2004x（预期 route 1.6x 超预期达成）",
      "status": "accepted"
    },
    {
      "comparison_sha256": "a8b138902371bfbc1e9208607da13b585b65ee13c248e30249b4c2c2c2cfa03a",
      "decision_sha256": "89e15d9ab1a36f67b5f8b878339de49199337df2f1d6c0a9be989d0588461644",
      "operator_class": "reduction",
      "performance_sha256": "b559866fc97d7e48adf17928132842d255223d1091c8b770ba496f4bc771240e",
      "round": 2,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "d283bfb645d57a7796c9326dbd4144c0074e946ce55a5c53a974eaaef7707203",
      "verify_sha256": "e6bb7bac27bdff8b3aeb69833d32a6f12afe12c61bd232fac51353fd9a7866ff"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "b16-granularity-floor",
      "per-element-heavy-op-count",
      "subword-microcode-cost"
    ],
    "pattern": "subword-u32-pair-packing",
    "structure": [
      "t1-contiguous-axis-scan",
      "pair-per-lane",
      "pack-lowest-shiftrights",
      "u32-interleave-scatter",
      "dtype-gated"
    ]
  },
  "generality": "op_class",
  "id": "SCAN-SUBWORD-U32-PAIR-PACK",
  "implementation_steps": [
    "在行并骨架上加 pair 变体核心：Gather 取 u32 pair（同行相邻 2 元素），比较/选择在 pair 域完成",
    "值分离：Pack<LOWEST>(pair) 取偶半、Pack<LOWEST>(ShiftRights<u32>(pair,16)) 取奇半；禁用 Pack<HIGHEST> 形态",
    "写回：两半结果经 Interleave<u16> 合成 u32 后单次 Scatter",
    "编译期门控 sizeof(DX)==2 实例化；4B 行并核与串行核逐字节不动",
    "probe 覆盖奇偶位置最小值交替的行（首个坏位诊断定位 hi/lo 半槽）与 NaN/inf；全量 verify + control case 字节级不动"
  ],
  "intent": "消除 2B dtype 行并扫描的 B16 粒度地板：向量 Gather/Scatter/Pack 的微码按 lane 计价与元素宽度无关，单位置形态每 step 只推进 1 个元素却按半槽付全价，per-step 微码成本翻倍且每元素 heavy-op 数不减少。",
  "mechanism": "在行并骨架上加 ComputeRowPackedPairVFRegImpl<DX>（__simd_vf__ 双位置打包核心）+ wrapper（carry 槽 + 逐行 Cast，复用行并骨架）；Process() 门控从 float 扩为 half/bfloat16_t 走 pair 核、float 单位置核字节不动；不改 host tiling（laneAlign 对 dt=2 天然满足）。Gather 取 u32 pair（=同行相邻 2 元素）在 pair 域比较/选择；loSlot/hiSlot = Pack<LOWEST>(pair) / Pack<LOWEST>(ShiftRights<u32>(pair,16))；{v1,v2} 经 Interleave<u16> 合成 u32 后单次 Scatter 落位；仅 sizeof(DX)==2 编译期实例化。",
  "name": "2B dtype 行打包扫描的 u32 双位置打包（每 lane 承载同一行 2 个连续扫描位置，Gather/Scatter 全 B32 粒度）",
  "operator_class": "reduction",
  "operator_scope": "已在行并行 lane 打包骨架（见 row-per-lane-packed-scan）上运行的 2B dtype（fp16/bf16）末轴连续前缀扫描（dimNorm == rank-1，T1 快路径）：单位置形态下 Gather/Scatter/Pack 按 u16 半槽操作，per-step 微码成本约为 4B dtype 的 2 倍",
  "principle": "把同一行的 2 个连续扫描位置打包进一个 u32 lane，Gather/Scatter/Pack 全部升到 B32 粒度，等价于每条微码处理 2 个元素——per-step 微码成本不变而每元素 heavy-op 数减半。前缀语义不受影响：pair 内两个位置同属一行，per-lane carry 仍按行封闭，LE tie-break 与 NaN sticky 在 pair 域比较中逐元素保留；出口用半槽分离 + Interleave 在写回侧恢复元素交错布局。",
  "related_anti_patterns": [],
  "risks": [
    "Pack<HIGHEST> 高半提取静默错值：精度 gate 可捕获但形态特异（奇数位更新丢失、carry 停滞在旧前缀最小值），排查时先做 hi/lo 半槽差分诊断",
    "半槽谓词索引与 lane 谓词索引混用导致掩码粒度错位",
    "奇数扫描长度/尾 pair 不满时的尾处理遗漏"
  ],
  "slug": "subword-u32-pair-packed-scan",
  "summary": "2B dtype 的行打包扫描改为 u32 pair 打包：每 lane 承载同一行的 2 个连续扫描位置（偶位置低半、奇位置高半），全部 Gather/Scatter 升到 B32 粒度且每元素 heavy-op 数减半；pair 域内完成后用 Pack<LOWEST>(pair) 与 Pack<LOWEST>(ShiftRights(pair,16)) 分离低/高半槽，再经单次 u32 Interleave 落位写回；仅 sizeof(DX)==2 编译期实例化，4B 行并核与串行核逐字节不动。",
  "verification": {
    "correctness": [
      "全量 all_cases verify 通过；hi/lo 半槽差分探针（奇偶位置交替最小值 + NaN/inf）先于全量",
      "4B 行并路径与串行路径字节级不动（control case 确认）"
    ],
    "performance": [
      "dt=2 目标 route 子集聚合达任务阈值且显著高于单位置形态；4B 与串行 control 在噪声带内",
      "incremental total_speedup 达任务阈值且无 case 低于 max_case_regression"
    ],
    "rollback_signals": [
      "任一精度失败（奇数位更新丢失/半槽掩码错位）",
      "4B 路径字节变动或 control case 回归超阈值",
      "dt=2 收益不达阈值时先核对是否仍存在 B16 粒度操作残留"
    ]
  }
}
-->

# 性能优化策略：2B dtype 行打包扫描的 u32 双位置打包（每 lane 承载同一行 2 个连续扫描位置，Gather/Scatter 全 B32 粒度）

单一优化点：2B dtype 的行打包扫描改为 u32 pair 打包：每 lane 承载同一行的 2 个连续扫描位置（偶位置低半、奇位置高半），全部 Gather/Scatter 升到 B32 粒度且每元素 heavy-op 数减半；pair 域内完成后用 Pack<LOWEST>(pair) 与 Pack<LOWEST>(ShiftRights(pair,16)) 分离低/高半槽，再经单次 u32 Interleave 落位写回；仅 sizeof(DX)==2 编译期实例化，4B 行并核与串行核逐字节不动。

## 1. 原理

把同一行的 2 个连续扫描位置打包进一个 u32 lane，Gather/Scatter/Pack 全部升到 B32 粒度，等价于每条微码处理 2 个元素——per-step 微码成本不变而每元素 heavy-op 数减半。前缀语义不受影响：pair 内两个位置同属一行，per-lane carry 仍按行封闭，LE tie-break 与 NaN sticky 在 pair 域比较中逐元素保留；出口用半槽分离 + Interleave 在写回侧恢复元素交错布局。

实现机制：在行并骨架上加 ComputeRowPackedPairVFRegImpl<DX>（__simd_vf__ 双位置打包核心）+ wrapper（carry 槽 + 逐行 Cast，复用行并骨架）；Process() 门控从 float 扩为 half/bfloat16_t 走 pair 核、float 单位置核字节不动；不改 host tiling（laneAlign 对 dt=2 天然满足）。Gather 取 u32 pair（=同行相邻 2 元素）在 pair 域比较/选择；loSlot/hiSlot = Pack<LOWEST>(pair) / Pack<LOWEST>(ShiftRights<u32>(pair,16))；{v1,v2} 经 Interleave<u16> 合成 u32 后单次 Scatter 落位；仅 sizeof(DX)==2 编译期实例化。

## 2. 性能问题模式

- 优化目标：消除 2B dtype 行并扫描的 B16 粒度地板：向量 Gather/Scatter/Pack 的微码按 lane 计价与元素宽度无关，单位置形态每 step 只推进 1 个元素却按半槽付全价，per-step 微码成本翻倍且每元素 heavy-op 数不减少。
- 适用数据流：已在行并行 lane 打包骨架（见 row-per-lane-packed-scan）上运行的 2B dtype（fp16/bf16）末轴连续前缀扫描（dimNorm == rank-1，T1 快路径）：单位置形态下 Gather/Scatter/Pack 按 u16 半槽操作，per-step 微码成本约为 4B dtype 的 2 倍
- Feature signature：`{"bottleneck": ["b16-granularity-floor", "per-element-heavy-op-count", "subword-microcode-cost"], "pattern": "subword-u32-pair-packing", "structure": ["t1-contiguous-axis-scan", "pair-per-lane", "pack-lowest-shiftrights", "u32-interleave-scatter", "dtype-gated"]}`

## 3. 正确性红线

- Pack<HIGHEST> 高半提取静默错值：精度 gate 可捕获但形态特异（奇数位更新丢失、carry 停滞在旧前缀最小值），排查时先做 hi/lo 半槽差分诊断
- 半槽谓词索引与 lane 谓词索引混用导致掩码粒度错位
- 奇数扫描长度/尾 pair 不满时的尾处理遗漏

资源与硬件约束：

- Pack<u16,u32,HIGHEST> 在 arch3510/CANN 9.1.0 不可用于 u32->u16 高半提取：高半不落 half-slot（hi 侧比较恒见 +0.0，奇数位更新静默丢失，行内自第一个奇位最小值起 carry 停滞）——高半提取必须用 ShiftRights<u32> + Pack<LOWEST>
- 谓词按 slot 索引：b16 bit i 对应 half-slot i，b32 lane k 读 bit k，两种粒度不可混用
- Interleave<u16> 语义为 dst0[2j]=s0[j]、dst0[2j+1]=s1[j]（u32 lane k = {s0[k], s1[k]}），落位顺序必须以诊断探针反证而非假设

## 4. 泛化条件

- 策略作用域：op_class：reduction

适用：

- 行并行 lane 打包骨架已存在并被接受（见 row-per-lane-packed-scan）
- sizeof(DX)==2（fp16/bf16）且扫描位置可按偶/奇成对（尾奇数位置走既有尾处理）
- 出口写回布局可用 Interleave 类原语恢复元素交错（或已有等价已验证载体）

不适用：

- 4B dtype：单位置形态已是 B32 粒度，pair 无增益
- host tiling 不可表达 pair 步进而必须新增推导时，先补 tiling 侧证据再实施

## 5. 实施步骤

1. 在行并骨架上加 pair 变体核心：Gather 取 u32 pair（同行相邻 2 元素），比较/选择在 pair 域完成
2. 值分离：Pack<LOWEST>(pair) 取偶半、Pack<LOWEST>(ShiftRights<u32>(pair,16)) 取奇半；禁用 Pack<HIGHEST> 形态
3. 写回：两半结果经 Interleave<u16> 合成 u32 后单次 Scatter
4. 编译期门控 sizeof(DX)==2 实例化；4B 行并核与串行核逐字节不动
5. probe 覆盖奇偶位置最小值交替的行（首个坏位诊断定位 hi/lo 半槽）与 NaN/inf；全量 verify + control case 字节级不动

## 6. LLM 前置问题

- 目标实现是否满足：行并行 lane 打包骨架已存在并被接受（见 row-per-lane-packed-scan）？
- 目标实现是否满足：sizeof(DX)==2（fp16/bf16）且扫描位置可按偶/奇成对（尾奇数位置走既有尾处理）？
- 目标实现是否满足：出口写回布局可用 Interleave 类原语恢复元素交错（或已有等价已验证载体）？
- 是否命中排除条件：4B dtype：单位置形态已是 B32 粒度，pair 无增益？

## 7. 验收标准

正确性：

- 全量 all_cases verify 通过；hi/lo 半槽差分探针（奇偶位置交替最小值 + NaN/inf）先于全量
- 4B 行并路径与串行路径字节级不动（control case 确认）

性能：

- dt=2 目标 route 子集聚合达任务阈值且显著高于单位置形态；4B 与串行 control 在噪声带内
- incremental total_speedup 达任务阈值且无 case 低于 max_case_regression

回滚信号：

- 任一精度失败（奇数位更新丢失/半槽掩码错位）
- 4B 路径字节变动或 control case 回归超阈值
- dt=2 收益不达阈值时先核对是否仍存在 B16 粒度操作残留

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- cummin-20260831_113913-196633（round=2, status=accepted, case=fp16/bf16 T1 last-axis 子集（level2/cummin_1/3/7/11/18/20）, speedup=dt=2 目标 case 全部 2.2253-2.6229x、route subset 2.4849x；incremental 1.0738x、cumulative 1.2004x（预期 route 1.6x 超预期达成））
- cummin-20260831_113913-196633（round=2, status=accepted）

## 检索卡（短卡）

动作：把 2B dtype 行打包扫描改为每 u32 lane 承载同一行相邻 2 个扫描位置，Gather/Scatter/Pack 全升 B32 粒度。
适用：行并行 lane 打包骨架已 accepted；sizeof(DX)==2 且扫描位置可按偶/奇成对。
限制：Pack<u16,u32,HIGHEST> 不能取 u32->u16 高半（奇数位更新静默丢失、carry 停滞）；谓词按 slot 索引不可混用。
范围：2B dtype（fp16/bf16）末轴连续前缀扫描 T1 快路径
检索词：Pack<LOWEST>、ShiftRights、Interleave<u16>、u32 pair、Scatter、B16 粒度地板
机会：Gather/Scatter/Pack 微码按 lane 计价，单位置每 step 只推进 1 元素
代价：尾 pair 不满与奇数扫描长度须走既有尾处理
