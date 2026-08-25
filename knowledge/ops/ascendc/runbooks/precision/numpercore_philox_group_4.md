---
type: "Runbook"
title: "多核 numPerCore 须对齐 Philox group 4"
description: "bit-exact 复现原生随机算子时，host 自算的多核 numPerCore 必须向上对齐到 Philox group size 4，否则跨核元素落入不同 counter group，从某元素起全线偏移。"
tags: ["task.debugging", "topic.precision", "topic.compute.random_sampling", "topic.tiling"]
status: draft
sources: []
created_at: "2026-08-18T05:33:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: []
aliases: ["StatelessRandomUniformV2"]
---

# 多核 numPerCore 须对齐 Philox group 4

## 现象

在 Uint32ToFloat、exponential 路径、Philox counter 按 group 推进三项 kernel 修复完成之后，自定义输出从"全 0% 匹配"变为"前 3 个元素跨不同 shape 保持一致，但从第 4 个元素起随 shape 出现偏移"。`compare_exponential.py`（seed=42，4 个 shape）对每个 shape 均报 `Exact match: False`、`Exact match elements: 0.00%`，但跨 shape 比较可见 custom 的前 3 个元素一致、第 4 个起不同。这是一个典型的多核 tiling 边界问题：`128 元素 / 56 核` 时 host 算出 `numPerCore = ceil(128/56) = 3`，element 3 被分配到 core 1（落入不同的 Philox counter group），而原生对齐到 4，element 3 留在 core 0 的同一 group 内。

## 适用场景

- **工程形态**：ops-direct-invoke Kernel 直调 + `.so` dispatch；host 侧自算多核切分（不经 TilingKey/CompileInfo）。
- **API 路径**：`op_extension/*_torch.cpp` 内 `aclrtGetDeviceInfo(ACL_DEV_ATTR_VECTOR_CORE_NUM)` 取核数后自算 `numPerCore`/`blockNum`/`tailNumLastCore`；对标 native V2 tiling 的 `blockTilingSize_`。
- **验证过的平台与 CANN 版本**：arch35 / CANN 9.1.0 / AIV vector core（trace 内观察到 56 与 43 两种核数，分别来自推理上下文与独立测试上下文）；trace 未明示芯片型号，`platforms: []`（未定位），推断同 arch 可迁移但未验证。
- **适用粒度**：`operator_family`（任何 host 自算多核切分、kernel 内按 numPerCore 做 `blockOffSet = numPerCore * blockIdx` 起点跳过的随机数 kernel）。
- **路线优先级**：`recommended_fastpath`（host 自算 tiling 时 numPerCore 对齐到 group size 是 bit-exact 的必要条件）。
- **不适用或未验证场景**：经 CompileInfo/TilingKey 由框架算 tiling 的算子仓流程（框架已保证对齐）；非 Philox group=4 的 PRNG 不适用此对齐值。

## 根因

Philox4x32-10 按 4 元素 group 推进 counter。多核切分时，每核起点 `blockOffSet = numPerCore * blockIdx`，kernel 进核先 `Skip(ceil(blockOffSet/4))` 跳到本核起始 group。若 `numPerCore` 不是 4 的倍数（如 3），则：

- core 0 处理 element 0,1,2（group 0 的前 3 个），counter group 0；
- core 1 起点为 `blockOffSet = 3`，`Skip(ceil(3/4)) = Skip(1)` 跳到 group 1，处理 element 3、4、5 等后续元素；

而原生对齐到 4：core 0 处理 element 0,1,2,3（group 0 全 4 个），core 1 起点为 4，`Skip(1)` 跳到 group 1。结果：自定义的 element 3 来自 group 1，原生的 element 3 来自 group 0——从 element 3 起全线偏移，且随 shape（核数）变化而变化，表现为"前 3 一致、第 4 起偏移"。

机制推导（不跳步）：`128 / 56 = 2.2857 → ceil = 3`。3 不是 4 的倍数。`blockOffSet(core1) = 3`，`ceil(3/4) = 1`，故 core1 从 group 1 开始；native `blockTilingSize` 对齐到 4 时 `blockOffSet(core1) = 4`，`ceil(4/4) = 1`，core1 也从 group 1 开始，但 core0 占满了 group 0 的 4 个元素。差异在 element 3 的归属。

## 判别方法

- **触发**：kernel 侧三项 bit-exact 修复（Uint32ToFloat IEEE754、exponential `1-u`+Log+Muls、counter per-group+Skip）均落地后，`compare_exponential.py` 仍报全 shape `Exact match: False`、`Exact match elements: 0.00%`，但跨 shape 的 custom 首 8 元素呈现"前 3 一致、第 4 起随 shape 分叉"；host 侧 `numPerCore` 由 `ceil(totalElements/numCores)` 算出且未对齐到 4。
- **探针**：打印 host 算出的 `numPerCore`，检查 `numPerCore % 4 != 0`；并把 4 个 shape 的 custom 首 8 元素并排比较，确认分叉点恰落在 `numPerCore`（首个非对齐核的起点）处。等价的可执行检查：`python scripts/compare_exponential.py`（seed=42，shape=128/1024/4096/129280）观察 `Exact match` 与首 8 元素。
- **原始观测**：4 shape（128/1024/4096/129280）全部 `Exact match: False`、`Exact match elements: 0.00%`，`max_abs_diff` 约 6.4~11.1；跨 shape custom 首 8 元素前 3 个一致、第 4 个起分叉（来源平台：未定位；证据等级：tool_observed）。
- **解释**：`numPerCore` 未对齐到 Philox group size 4，使第 1 个非对齐核的 `blockOffSet` 落在 group 中部，`Skip(ceil(blockOffSet/4))` 把该核起点推到下一个 group，element `numPerCore` 被错误归到下一 group——从该元素起全线偏移，并随 shape（核数）变化而变化。对齐到 4 即让每核起点都落在 group 边界，counter group 不跨核错位。

## 验证信号

- kernel 三项修复后、host `numPerCore` 未对齐时：4 shape（128/1024/4096/129280）全部 `Exact match: False`、`Exact match elements: 0.00%`、`max_abs_diff` 约 6.4~11.1，custom 首 8 元素跨 shape 前 3 一致、第 4 起分叉（来源平台：未定位；证据等级：tool_observed）
- host `numPerCore` 向上对齐到 4（`(numPerCore+3)&~3u`）后：4 shape 全部 `Exact match: True`、`max_abs_diff: 0.0`、`Exact match elements: 100.00%`（来源平台：未定位；证据等级：tool_observed）

注：这是完整修复集里唯一有"前后隔离信号"的根因——前 3 一致/第 4 起偏移是对齐前特有现象，对齐后立刻 100% match。

## 设计决策

- 为何对齐值是 4 而非 256：Philox 的 group size 是 4（`RESULT_ELEMENT_CNT`），counter 推进的最小语义单位是 4 元素；256 是 UB 块大小（搬运单位），与 counter group 无关。对齐到 256 也能保证 4 的倍数，但 256 会让小 shape（如 128）单核装不下且 tail 处理复杂；对齐到 4 既满足 counter 语义又保留小 shape 灵活性。
- 为何从 `blocksPerCore` 改为 `numPerCore`：v0 用 256 元素块作切分单位，`td.numPerCore = blocksPerCore` 语义不一致（kernel 把 `numPerCore` 当元素数用）；统一为元素计数并按 4 对齐后，host 与 kernel 的 `blockOffSet` 单位才一致。

## 预防

host 自算多核切分、kernel 内按 `blockOffSet = numPerCore * blockIdx` 起点 `Skip(ceil(blockOffSet/groupSize))` 的随机数 kernel，`numPerCore` 一律向上对齐到 PRNG group size（Philox=4）。算式：`numPerCore = (numPerCore + (GROUP-1)) & ~(GROUP-1);`。

## 失效边界

- arch35 / CANN 9.1.0 / AIV 设备验证 100% match；芯片型号未明示，未验证，推断可迁移到同 arch AscendC 设备。
- 若经框架 TilingKey/CompileInfo 算 tiling，对齐由框架保证，此 host 侧对齐不适用。
- group size 非 4 的 PRNG 需改为对应 group size 对齐。

<!-- cannbot:related:start -->
## 相关

- [PhiloxRandom](../../apis/simd_api/adv_api/random_functions/philox_random.md)（`exemplifies`）：“PhiloxRandom”处理基于Philox随机数生成算法，给定随机数种子，生成若干的随机数。 Philox随机数生成的核心算法是一个基于记数的伪随机数生成算法，输入为一个128bit的记数器C，两个32bit的key（k0和k1），输出为4个32bit的整数。；“多核 numPerCore 须对齐 Philox group 4”明确bit-exact 复现原生随机算子时，host 自算的多核 numPerCore 必须向上对齐到 Philox group size 4，否则跨核元素落入不同 counter group，从某元素起全线偏移。。实质衔接：这些卡直接定位 PhiloxRandom 的轮数、counter/offset、每核 group=4 对齐以及 uint32 到浮点分布变换，能够执行性地解释随机序列不一致。
- [随机函数](../../apis/simd_api/adv_api/random_functions/random_functions.md)（`exemplifies`）：Philox 每个 counter 生成 4 个值，运行卡说明多核 numPerCore 必须按该 group=4 对齐才能保持 counter 分区连续。
- [philox offset 推进量须固定 12 而非元素数](philox_offset_12.md)（`related`）：多核 numPerCore 须对齐 Philox group 4 与《philox offset 推进量须固定 12 而非元素数》的实质衔接是：Philox 每核切分须保持 group4；round 数、counter 槽、offset 推进和 PhiloxRandom API共同定义可复现随机序列。
- [核间负载均衡](../../guides/operator_practice/simd_operator_optimization/tiling_strategy/inter_core_load_balance.md)（`related`）：核间负载均衡 与《多核 numPerCore 须对齐 Philox group 4》的实质衔接是：核间负载均衡通过调整拖尾核与 block 数减少尾部空闲，并与核间同步、DoubleBuffer/异步 Iterate 和具体 Matmul/Philox 分块约束共同决定并行度。
- [Philox offset 须放 counter[2:3] 而非 [0:1]](philox_offset_counter_2_3_0_1.md)（`same_topic`）：多核 numPerCore 须对齐 Philox group 4 与《Philox offset 须放 counter[2:3] 而非 [0:1]》的实质衔接是：Philox 每核切分须保持 group4；round 数、counter 槽、offset 推进和 PhiloxRandom API共同定义可复现随机序列。
- [PhiloxRandom 默认 7 rounds 与原生 10 不匹配](philoxrandom_7_rounds_10.md)（`same_topic`）：PhiloxRandom 默认 7 rounds 与原生 10 不匹配 与《多核 numPerCore 须对齐 Philox group 4》的实质衔接是：Philox 与原生逐元素对齐同时依赖显式 10 rounds、counter[2:3]、offset=12、group4 切分及 uint 到 uniform/exponential 转换，所选卡组成同一 RNG 序列契约。
- [SIMT 切分未 coalesce 致 block 边界错位](simt_coalesce_block.md)（`same_topic`）：两卡都定位多核切分边界改变全局元素到 Philox counter group 的映射：本卡先合并连续维再切 block，目标卡要求 numPerCore 对齐 4 元素 counter group。
- [Uint32ToFloat 须用 IEEE754 位操作而非位移乘法](uint32tofloat_ieee754.md)（`same_topic`）：Uint32ToFloat 须用 IEEE754 位操作而非位移乘法 与《多核 numPerCore 须对齐 Philox group 4》的实质衔接是：bit-exact 随机链必须与 Philox 原生实现一致：counter/round/offset 先生成 uint32，再按 IEEE754 尾数位重解释；通用 Cast 不能替代该位级契约。
- [exponential_ 0% 匹配须改 -log(1-u) 路径](exponential_0_log_1_u.md)（`same_topic`）：每核元素分组需按 Philox 每 counter 产出 4 个值。
<!-- cannbot:related:end -->
