---
type: Optimization
title: dtype 条件化 L2 cache hint（写旁路 + fp32 读常驻）
description: 把输出写改为 CACHE_MODE_DISABLE 写旁路，并只在 fp32 实例把输入读流标为 PERSISTENT，fp16/bf16 保持 NORMAL。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/l2-cache-hint-dtype-conditional.md
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
      "cache hint 只在 kernel Init() 的 GM buffer 设置处（四个 SetGlobalBuffer 调用之后）生效，不改 tiling、队列结构、同步结构与数值路径",
      "PERSISTENT 读标记必须由编译期 dtype 门控约束（if constexpr(IsSameType<dataType,float>)），fp16/bf16 输入一律保持 CACHE_MODE_NORMAL",
      "输出写旁路 SetL2CacheHint<WRITE>(CACHE_MODE_DISABLE) 对所有 dtype 生效",
      "hint 属 L2 状态侧优化，收益随读集大小与跨 launch 复用情况变化，须以 ABBA 配对实测验收，不可按 dtype 无关的普适收益外推"
    ],
    "excluded_conditions": [
      "fp16/bf16 输入不得标 PERSISTENT——约 100.7MB 的近驻留读集会被打穿，有效读带宽 4.56->2.87 TB/s",
      "输入读集规模未知、或跨 launch 不存在输入复用的部署场景下 PERSISTENT 不适用",
      "在未验证 DISABLE 位在 MTE3 写通道上等价于 no-allocate 的后端版本上不适用"
    ],
    "required_conditions": [
      "后端提供 GlobalTensor::SetL2CacheHint(CacheMode)（CANN 9.1.0 / arch3510，经 L2CacheAlter 用地址 bit60-62 编码 NORMAL/PERSISTENT/DISABLE）",
      "内核此前未使用任何 cache hint（默认 CACHE_MODE_NORMAL，写分配）",
      "算子为 aiv_mte2 主导（基线 profiling：fp32 87.81us 中 mte2 93.1%/81.7us；fp16 29.58us 中 mte2 74.6%/22.06us；bf16 29.51us 与 fp16 同构；geomean 42.481us）",
      "输入读集规模与 L2 容量的相对关系已知（每 case 约 16.8M 元素 x 3 输入 + 1 输出：fp32 读 201MB / 写 67MB；fp16/bf16 读 100.7MB / 写 33.6MB，fp16/bf16 有效读带宽约 4.58 TB/s 介于 L2 命中与 DRAM 之间）",
      "存在同 shape 的 ABBA 配对度量路径（本 run 2 对）"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-14",
  "evidence": [
    {
      "operator": "InputLayerAdd",
      "operator_class": "elementwise",
      "pairs": 2,
      "precision": "20/20 PASS（round_01 与 round_02 两侧均 20/20，0 修复轮）",
      "run_id": "<run-id>",
      "speedup": 1.0738,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "aiv-mte2-dominated",
      "write-allocate-evicting-input-residency",
      "l2-cache-hint-unused"
    ],
    "dtypes": [
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "l2-cache-hint-dtype-conditional",
    "structure": [
      "init-time-cache-hint",
      "output-write-bypass",
      "dtype-conditional-input-persistent",
      "tiling-queue-sync-untouched"
    ]
  },
  "generality": "op_class",
  "id": "ELEM-L2-CACHE-HINT-DTYPE-CONDITIONAL",
  "implementation_steps": [
    "在 kernel Init() 的四个 SetGlobalBuffer 调用之后，对输出 yGM_ 调 SetL2CacheHint<WRITE>(CACHE_MODE_DISABLE)，使 MTE3 写不分配 L2（对所有 dtype 生效）",
    "对 fp32 kernel 实例，在 if constexpr(IsSameType<dataType,float>) 下把三路输入 xGM_/t1GM_/t2GM_ 标 SetL2CacheHint<READ>(CACHE_MODE_PERSISTENT)",
    "fp16/bf16 输入保持默认 CACHE_MODE_NORMAL，不做任何 PERSISTENT 标记（round_01 已证会打穿约 100.7MB 读集，4.56->2.87 TB/s）",
    "不改 tiling、队列结构、同步结构与数值路径，精度护栏不受影响",
    "跑 20/20 精度与同 shape 的 ABBA 配对（外层 msprof device Task Duration），并按 dtype 分别核对 fp32 与 fp16/bf16 的收益归属"
  ],
  "intent": "压低 aiv_mte2 的有效读时延/带宽占比：把输出的 MTE3 写标记为不分配 L2，避免写分配挤出近驻留的输入行；并只在 fp32 侧把输入读流标记为 PERSISTENT。",
  "mechanism": "在 kernel Init() 内按 dtype 条件化设置 GlobalTensor 的 L2 cache hint。输出 yGM_ 统一 SetL2CacheHint<WRITE>(CACHE_MODE_DISABLE)（MTE3 写旁路、不分配 L2）；fp32 实例再由 if constexpr(IsSameType<dataType,float>) 额外把三路输入标 SetL2CacheHint<READ>(CACHE_MODE_PERSISTENT)；fp16/bf16 输入保持 NORMAL。底层为 arch3510 GlobalTensor::SetL2CacheHint(CacheMode)（kernel_tensor.h:263），经 L2CacheAlter 以地址 bit60-62 编码 CACHE_MODE_NORMAL(0b000)/PERSISTENT(0b010)/DISABLE(0b100)（kernel_utils_macros.h:251）。tiling/队列/同步/数值路径零改动，精度护栏不受影响。",
  "name": "dtype 条件化 L2 cache hint（写旁路 + fp32 读常驻）",
  "operator_class": "elementwise",
  "operator_scope": "aiv_mte2 主导、输入存在跨 launch 复用、且能在 kernel Init 的 GM buffer 设置处按 dtype 条件化打 cache hint 的算子；读集规模与 L2 容量的相对关系需已实测",
  "principle": "L2 容量有限且默认 CACHE_MODE_NORMAL 的写分配会把输出行填入 L2，挤出近驻留的输入行。fp16/bf16 的输入读集约 100.7MB/launch、有效读带宽约 4.58 TB/s（介于 L2 命中与 DRAM 流之间），其驻留率对写挤占敏感——输出写旁路后输入命中率上升，mte3 自身同时下降。但 PERSISTENT 读标记并非普适：读集远大于 L2 时（fp16/bf16 约 100.7MB）PERSISTENT 反而把缓存打穿，有效读带宽从 4.56 掉到 2.87 TB/s；只有流式读集（fp32 201MB）下 PERSISTENT 才以更低的替换扰动收敛到 mte2 下降。故 hint 必须按 dtype 条件化，不可全局统一。",
  "related_anti_patterns": [],
  "risks": [
    "fp16/bf16 输入不能标 PERSISTENT：约 100.7MB 的近驻留读集会被打穿，有效读带宽 4.56->2.87 TB/s；round_01 的合并策略（输入不分 dtype 的 PERSISTENT + 写旁路）因此整体回退 18.4% geomean",
    "正式结论只基于 2 对 ABBA（不是 4 对）；7.4% 的 geomean 收益几乎全部由 fp32 一侧承担（fp32 -17.7%，fp16/bf16 约 -1%），fp16/bf16 侧只有约 1% 的边际变化，不应按“全 dtype 普适”外推",
    "单做写旁路不足以过门：round_02 仅写旁路 screened 只降 2.0%，收益主要来自 dtype 条件化的 PERSISTENT 组合（round_03 dtype 条件化 screened 降 6.6%）",
    "收益依赖 L2 状态：性能循环对同一批张量重复 launch（time_call 3x20 次），跨迭代存在输入复用；部署场景若无这种复用，PERSISTENT 侧收益会缩水",
    "DISABLE 位在 MTE3 写通道上是否真等价于 no-allocate、PERSISTENT 标记跨 launch 的保持语义，在数据中列为未知，须以实测闭环"
  ],
  "slug": "l2-cache-hint-dtype-conditional",
  "summary": "在 kernel Init() 的 GM buffer 设置处按 dtype 条件化打 L2 cache hint：输出 yGM_ 统一 SetL2CacheHint<WRITE>(CACHE_MODE_DISABLE)（MTE3 写不分配 L2，避免挤出近驻留输入流），fp32 实例再对三路输入标 CACHE_MODE_PERSISTENT，fp16/bf16 输入保持 NORMAL。候选 geomean 39.241us vs 基线 42.137us（1.0738x，7.4%，formal ABBA 2 对；fp32 -17.7%、fp16/bf16 约 -1%）。机制经三轮隔离：写旁路使 fp32 mte3 22.5->13.4us，fp32 输入 PERSISTENT 使 mte2 77.6->66.6us；fp16/bf16 输入若标 PERSISTENT 会使有效读带宽 4.56->2.87 TB/s（round_01 整体回退 18.4%）。精度 20/20。",
  "verification": {
    "correctness": [
      "20/20 PASS，0 修复轮（round_01 与 round_02 两侧均 20/20）",
      "改动仅涉及 cache hint，tiling / 队列结构 / 同步结构与数值路径零改动，精度护栏不受影响"
    ],
    "performance": [
      "候选 geomean 39.241us vs 基线 42.137us（speedup 1.0738x，7.4%，formal ABBA 2 对）：fp32 -17.7%、fp16/bf16 约 -1%",
      "机制三轮隔离：输出写旁路（CACHE_MODE_DISABLE）使 fp32 mte3 22.5->13.4us 并带动部分 mte2；fp32 输入 PERSISTENT 使 mte2 77.6->66.6us；fp16/bf16 输入必须保持 NORMAL",
      "同 run 对照：round_01 合并策略（不分 dtype 的 PERSISTENT + 写旁路）screened 即回退（geomean +18.4% 回归）；round_02 仅写旁路 screened 只降 2.0%；round_03 dtype 条件化 screened 降 6.6% 后进入 formal ABBA 并采纳",
      "另两条被证伪的对照：tile 放大到 UB 满块 task 不变（0.9980）、同步批化使 scalar_ratio 0.538->0.478 但 task 不变（0.9939）——确认约束在 aiv_mte2 而非 tile 几何或同步次数"
    ],
    "rollback_signals": [
      "全局 PERSISTENT（不分 dtype）导致 fp16/bf16 有效读带宽从 4.56 掉到 2.87 TB/s 并整体回退（round_01 +18.4% 的前车）",
      "ABBA 配对下 mte2 相关 case 均值变化 <1%（噪声级）或出现 >2% 回归时按 rollback signal 回滚并归档",
      "输出写 DISABLE 在 MTE3 通道上被实测证明不等价于 no-allocate",
      "fp32 侧收益消失或反转（机制的主贡献项失效）"
    ]
  }
}
-->

# 性能优化策略：dtype 条件化 L2 cache hint（写旁路 + fp32 读常驻）

在 kernel Init() 的 GM buffer 设置处按 dtype 条件化打 L2 cache hint：输出统一写旁路（CACHE_MODE_DISABLE），仅 fp32 输入标 PERSISTENT，fp16/bf16 输入保持 NORMAL。候选 geomean 39.241us vs 基线 42.137us（1.0738x，7.4%，formal ABBA 2 对）。

## 1. 原理

L2 容量有限且默认 CACHE_MODE_NORMAL 的写分配会把输出行填入 L2，挤出近驻留的输入行。fp16/bf16 的输入读集约 100.7MB/launch、有效读带宽约 4.58 TB/s（介于 L2 命中与 DRAM 流之间），其驻留率对写挤占敏感——输出写旁路后输入命中率上升，mte3 自身同时下降。但 PERSISTENT 读标记并非普适：读集远大于 L2 时（fp16/bf16 约 100.7MB）PERSISTENT 反而把缓存打穿，有效读带宽从 4.56 掉到 2.87 TB/s；只有流式读集（fp32 201MB）下 PERSISTENT 才以更低的替换扰动收敛到 mte2 下降。故 hint 必须按 dtype 条件化，不可全局统一。

实现机制：在 kernel Init() 内按 dtype 条件化设置 GlobalTensor 的 L2 cache hint。输出 yGM_ 统一 SetL2CacheHint<WRITE>(CACHE_MODE_DISABLE)（MTE3 写旁路、不分配 L2）；fp32 实例再由 if constexpr(IsSameType<dataType,float>) 额外把三路输入标 SetL2CacheHint<READ>(CACHE_MODE_PERSISTENT)；fp16/bf16 输入保持 NORMAL。底层为 arch3510 GlobalTensor::SetL2CacheHint(CacheMode)（kernel_tensor.h:263），经 L2CacheAlter 以地址 bit60-62 编码 CACHE_MODE_NORMAL(0b000)/PERSISTENT(0b010)/DISABLE(0b100)（kernel_utils_macros.h:251）。tiling/队列/同步/数值路径零改动，精度护栏不受影响。

## 2. 性能问题模式

- 优化目标：压低 aiv_mte2 的有效读时延/带宽占比：把输出的 MTE3 写标记为不分配 L2，避免写分配挤出近驻留的输入行；并只在 fp32 侧把输入读流标记为 PERSISTENT
- 适用数据流：aiv_mte2 主导、输入存在跨 launch 复用、且能在 kernel Init 的 GM buffer 设置处按 dtype 条件化打 cache hint 的算子；读集规模与 L2 容量的相对关系需已实测
- Feature signature：`{"bottleneck": ["aiv-mte2-dominated", "write-allocate-evicting-input-residency", "l2-cache-hint-unused"], "dtypes": ["fp16", "bf16", "fp32"], "pattern": "l2-cache-hint-dtype-conditional", "structure": ["init-time-cache-hint", "output-write-bypass", "dtype-conditional-input-persistent", "tiling-queue-sync-untouched"]}`

## 3. 正确性红线

- fp16/bf16 输入不能标 PERSISTENT：约 100.7MB 的近驻留读集会被打穿，有效读带宽 4.56->2.87 TB/s；round_01 的合并策略（输入不分 dtype 的 PERSISTENT + 写旁路）因此整体回退 18.4% geomean
- 正式结论只基于 2 对 ABBA（不是 4 对）；7.4% 的 geomean 收益几乎全部由 fp32 一侧承担（fp32 -17.7%，fp16/bf16 约 -1%），fp16/bf16 侧只有约 1% 的边际变化，不应按“全 dtype 普适”外推
- 单做写旁路不足以过门：round_02 仅写旁路 screened 只降 2.0%，收益主要来自 dtype 条件化的 PERSISTENT 组合（round_03 dtype 条件化 screened 降 6.6%）
- 收益依赖 L2 状态：性能循环对同一批张量重复 launch（time_call 3x20 次），跨迭代存在输入复用；部署场景若无这种复用，PERSISTENT 侧收益会缩水
- DISABLE 位在 MTE3 写通道上是否真等价于 no-allocate、PERSISTENT 标记跨 launch 的保持语义，在数据中列为未知，须以实测闭环

资源与硬件约束：

- cache hint 只在 kernel Init() 的 GM buffer 设置处（四个 SetGlobalBuffer 调用之后）生效，不改 tiling、队列结构、同步结构与数值路径
- PERSISTENT 读标记必须由编译期 dtype 门控约束（if constexpr(IsSameType<dataType,float>)），fp16/bf16 输入一律保持 CACHE_MODE_NORMAL
- 输出写旁路 SetL2CacheHint<WRITE>(CACHE_MODE_DISABLE) 对所有 dtype 生效
- hint 属 L2 状态侧优化，收益随读集大小与跨 launch 复用情况变化，须以 ABBA 配对实测验收，不可按 dtype 无关的普适收益外推

## 4. 泛化条件

- 策略作用域：op_class：elementwise

适用：

- 后端提供 GlobalTensor::SetL2CacheHint(CacheMode)（CANN 9.1.0 / arch3510，经 L2CacheAlter 用地址 bit60-62 编码 NORMAL/PERSISTENT/DISABLE）
- 内核此前未使用任何 cache hint（默认 CACHE_MODE_NORMAL，写分配）
- 算子为 aiv_mte2 主导（基线 profiling：fp32 87.81us 中 mte2 93.1%/81.7us；fp16 29.58us 中 mte2 74.6%/22.06us；bf16 29.51us 与 fp16 同构；geomean 42.481us）
- 输入读集规模与 L2 容量的相对关系已知（每 case 约 16.8M 元素 x 3 输入 + 1 输出：fp32 读 201MB / 写 67MB；fp16/bf16 读 100.7MB / 写 33.6MB，fp16/bf16 有效读带宽约 4.58 TB/s 介于 L2 命中与 DRAM 之间）
- 存在同 shape 的 ABBA 配对度量路径（本 run 2 对）

不适用：

- fp16/bf16 输入不得标 PERSISTENT——约 100.7MB 的近驻留读集会被打穿，有效读带宽 4.56->2.87 TB/s
- 输入读集规模未知、或跨 launch 不存在输入复用的部署场景下 PERSISTENT 不适用
- 在未验证 DISABLE 位在 MTE3 写通道上等价于 no-allocate 的后端版本上不适用

## 5. 实施步骤

1. 在 kernel Init() 的四个 SetGlobalBuffer 调用之后，对输出 yGM_ 调 SetL2CacheHint<WRITE>(CACHE_MODE_DISABLE)，使 MTE3 写不分配 L2（对所有 dtype 生效）
2. 对 fp32 kernel 实例，在 if constexpr(IsSameType<dataType,float>) 下把三路输入 xGM_/t1GM_/t2GM_ 标 SetL2CacheHint<READ>(CACHE_MODE_PERSISTENT)
3. fp16/bf16 输入保持默认 CACHE_MODE_NORMAL，不做任何 PERSISTENT 标记（round_01 已证会打穿约 100.7MB 读集，4.56->2.87 TB/s）
4. 不改 tiling、队列结构、同步结构与数值路径，精度护栏不受影响
5. 跑 20/20 精度与同 shape 的 ABBA 配对（外层 msprof device Task Duration），并按 dtype 分别核对 fp32 与 fp16/bf16 的收益归属

## 6. LLM 前置问题

- 目标实现是否满足：后端提供 GlobalTensor::SetL2CacheHint(CacheMode)（CANN 9.1.0 / arch3510，经 L2CacheAlter 用地址 bit60-62 编码 NORMAL/PERSISTENT/DISABLE）？
- 目标实现是否满足：内核此前未使用任何 cache hint（默认 CACHE_MODE_NORMAL，写分配）？
- 目标实现是否满足：算子为 aiv_mte2 主导（基线 fp32 mte2 93.1%、fp16 74.6%、bf16 同构）？
- 目标实现是否满足：输入读集规模与 L2 容量的相对关系已知（fp32 读 201MB；fp16/bf16 读 100.7MB、有效读带宽约 4.58 TB/s）？
- 目标实现是否满足：存在同 shape 的 ABBA 配对度量路径？
- 是否命中排除条件：fp16/bf16 输入不得标 PERSISTENT——约 100.7MB 的近驻留读集会被打穿？
- 是否命中排除条件：输入读集规模未知、或跨 launch 不存在输入复用的部署场景下 PERSISTENT 不适用？
- 是否命中排除条件：在未验证 DISABLE 位在 MTE3 写通道上等价于 no-allocate 的后端版本上不适用？

## 7. 验收标准

正确性：

- 20/20 PASS，0 修复轮（round_01 与 round_02 两侧均 20/20）
- 改动仅涉及 cache hint，tiling / 队列结构 / 同步结构与数值路径零改动，精度护栏不受影响

性能：

- 候选 geomean 39.241us vs 基线 42.137us（speedup 1.0738x，7.4%，formal ABBA 2 对）：fp32 -17.7%、fp16/bf16 约 -1%
- 机制三轮隔离：输出写旁路（CACHE_MODE_DISABLE）使 fp32 mte3 22.5->13.4us 并带动部分 mte2；fp32 输入 PERSISTENT 使 mte2 77.6->66.6us；fp16/bf16 输入必须保持 NORMAL
- 同 run 对照：round_01 合并策略（不分 dtype 的 PERSISTENT + 写旁路）screened 即回退（geomean +18.4% 回归）；round_02 仅写旁路 screened 只降 2.0%；round_03 dtype 条件化 screened 降 6.6% 后进入 formal ABBA 并采纳
- 另两条被证伪的对照：tile 放大到 UB 满块 task 不变（0.9980）、同步批化使 scalar_ratio 0.538->0.478 但 task 不变（0.9939）——确认约束在 aiv_mte2 而非 tile 几何或同步次数

回滚信号：

- 全局 PERSISTENT（不分 dtype）导致 fp16/bf16 有效读带宽从 4.56 掉到 2.87 TB/s 并整体回退（round_01 +18.4% 的前车）
- ABBA 配对下 mte2 相关 case 均值变化 <1%（噪声级）或出现 >2% 回归时按 rollback signal 回滚并归档
- 输出写 DISABLE 在 MTE3 通道上被实测证明不等价于 no-allocate
- fp32 侧收益消失或反转（机制的主贡献项失效）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- loop_20260913_070917（operator=InputLayerAdd, status=accepted, speedup=1.0738, precision=20/20 PASS, formal ABBA 2 对, geomean 42.137->39.241us）

## 检索卡（短卡）

动作：把输出写改为 CACHE_MODE_DISABLE 写旁路，并只在 fp32 实例把输入读流标为 PERSISTENT，fp16/bf16 保持 NORMAL。
适用：内核未用过 cache hint、aiv_mte2 主导、后端提供 SetL2CacheHint。
限制：fp16/bf16 输入不得标 PERSISTENT（约 100.7MB 读集被打穿，4.56->2.87 TB/s）；须 ABBA 实测。
范围：elementwise 的 Init GM buffer 设置处。
检索词：SetL2CacheHint、CACHE_MODE_DISABLE、CACHE_MODE_PERSISTENT、L2CacheAlter、MTE3
机会：默认写分配把输出行填入 L2、挤出近驻留输入行，有效读带宽介于 L2 与 DRAM 之间。
代价：收益随读集大小与跨 launch 复用变化；单做写旁路不足以过门。
