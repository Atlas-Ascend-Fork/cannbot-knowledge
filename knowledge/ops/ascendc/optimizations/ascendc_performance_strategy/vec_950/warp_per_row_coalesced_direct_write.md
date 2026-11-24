---
type: Optimization
title: 行稀疏输出的 warp-per-row 批处理 + 宽合并访存 + 单趟直写
description: 把每线程独占一段连续地址写输出改为按行分 warp、lane 交织宽访存、判定与写出同趟、普通 cached store。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.implementation.atomic
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/warp-per-row-coalesced-direct-write.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：行稀疏输出的 warp-per-row 批处理 + 宽合并访存 + 单趟直写

> 单一优化点：行稀疏输出（先按行判定"命中/未命中"，再决定整行拷贝还是整行初始化）这类场景，
> 不要用"每个线程独占一段连续地址 + scratch 中转 + 逐行/逐元素决策"的写法；改成 **warp-per-row 批量 + lane 交织
> 16B 合并访存 + 决策与写出同一趟 + 普通 cached store**，去掉 GM 中转与逐元素固定开销；
> 稀疏分支再按密度门控在 warp-per-slot 与 per-thread 之间切换。

---

## 1. 原理

行稀疏输出的三类成本，分别由三个手段对位：

| 成本 | 成因 | 手段 |
|---|---|---|
| 访存不合并，有效带宽掉到 ~1/8 | 映射写成"每个线程一段连续地址"（`e = tid·perThread`）：同一 warp 的 lane 相隔 `perThread` 个元素，每条 load/store 各占一个 32B 扇区 | **lane 交织 16B**：`j = lane·4`，一个 warp 一次覆盖 32×16B = 512B 连续 |
| 每元素重复的固定开销 | 每个元素都要读 kind/plan/slot、做整数除法、重算地址 | **warp-per-row（一行一个 warp）**：`warp = tid>>5` 占一行，kind/slot/src/dst 每行只读一次，分支在 warp 内一致，地址 `+= step` 递推 |
| 多 pass 与 GM 中转 | VF→GM `scratch`→MTE2→`rowBuf`→MTE3→`values`，1 份输出多走 ~2 份 GM 流量 | **单趟直写 + 减少 pass**：判定 kind 后立即写 dst，不生成 plan、不经 scratch |

**组合关系（关键）**：行级批处理决定"一个 work item 覆盖多少连续字节"，宽访问才有宽度可用；
只加宽访问而不换工作项映射时，带宽利用率上去了但每元素开销还在，收益会被吃掉；**先换工作项
映射，再谈访问宽度**。反过来，如果这一跳改由 DMA/MTE 批量搬运完成，则"宽访问"由描述符天然提供，
不需要手工 lane 交织。

**两类行共享同一循环**：命中行（src→dst 整行拷贝）与未命中行（初始化常量/插入）是同一 warp
迭代里的不同分支，地址计算与行级元数据只做一次。

**稀疏分支要门控**：当每行/每 slot 的活跃 lane 数远小于 warp 宽度时，warp 扫描的利用率极低
（1/32 量级），此时应回退 per-thread 遍历。判据示例：`活跃项数 × warp 宽度 > 扫描长度` 才用
warp-per-slot。

**缓存策略**：GB 级流式输出不要用 write-through 的流式写（`stcg` 类），它把每次写都推到下一级；
先用普通 cached store（让 L2 做写合并），实测确认后再考虑流式提示。

瓶颈类型：vec/issue（每元素指令）/ 带宽利用不足（访问不合并）/ pass 过多（GM 中转）。

## 2. 性能问题模式

- profile 症状：输出 kernel 占整算子 80%+；或"校验/初始化"段在大 D 时占该 kernel 的一半以上。
- 代码形态：`e = tid·perThread`；存在 `scratch` workspace 与二次 MTE；`plan` 先写 GM 再读回；
  每元素 `slot % nc`；输出用 `stcg`；行内循环里有除法/乘法和重复 GM load。
- 结构判据：行数 ≫ warp 数（有行可并行）、行字节 ≥ 512B（有宽度可用）、输出总字节 ≫ L2；
  命中行与 miss 行的写操作可合并到同一分支结构里。

## 3. 正确性红线

1. **16B 组不得跨行**：要求 `D·es % 16 == 0`，且组下标以 4 个元素为单位；行尾不足 16B 的余量
   单独用标量/窄向量处理。
2. **warp 内分支必须一致**：kind 的判定放在行级（每行一次），不能让同一 warp 的不同 lane 走
   不同分支后再做集合操作。
3. **稀疏不能用 warp 扫描**：活跃 lane 少时利用率 1/32，必须密度门控回退 per-thread。
4. **单趟直写的前提**是决策所需元数据在行入口一次读入（寄存器/UB 缓存），写出循环里不得再
   逐元素读 GM；否则"单趟"会变成"每元素两趟"。
5. **唯一写者**：一行只由一个 warp（或一个核）写；去掉 scratch 后命中行与 miss 行仍不能跨 warp
   覆盖同一行，否则竞态丢数据。
6. **流式写不要 write-through**：大输出先按普通 cached store 验证，再决定是否加流式提示。
7. **不要为了省同步删掉跨 block 依赖**：存在全局归约（如 argmin/winner）时，必要的跨 block 同步
   与 workspace 语义不能省，否则是语义错误而不是优化。
8. **归约优先下沉到 UB 聚合 + 块内 merge**：先做块内聚合再扇出；直接对每次查询打 GM 原子在
   稀疏/冲突场景会显著变慢。

## 4. 泛化条件

- **适用**：行结构明显（B 行 × D 列）、输出为"每行命中拷贝 / 未命中初始化"的行稀疏类；
  行字节 ≥ 256~512B；`D·es` 可被 16 整除或可做尾部处理；行数远大于 warp 数。
- **不适用 / 收益低**：
  - 行字节很小（< 64B）：warp 只有少数 lane 有活，warp-per-row 退化 → 用 per-thread 或跨行打包；
  - 行数小于 warp 数：warp-per-row 空转 → 一行多 warp 或按元素并行；
  - 命中率极低（几乎全初始化）：写放大成为主因 → 改用整块初始化型路径（少一次读）；
  - 稀疏 slot 校验：必须密度门控，否则 warp 扫描是负优化。
- **可叠加**：单趟融合、普通 cached store、行内 unroll×2/×4（提高 MLP）、跨行批量。
- **不叠加**：GM 原子/世代号类全局归约替换（在稀疏与冲突场景多为负结果）。

## 5. 实施步骤

1. **确认瓶颈在输出段**：按 kernel 拆分计时（winner vs output）或按段拆 pipe 占比；
   输出占比 < 50% 时不要先动它。
2. **选 work item 粒度**：行字节 ≥ 512B 且行数 ≫ warp 数 → 一行一个 warp；
   否则 per-thread 或"一行多 warp"；把行数上限与大 B 的分段（grid-stride）一起定好。
3. **决策行级化**：warp 入口用 `warp`（及 grid-stride 步长）读一次 kind/slot/src/dst；
   去掉循环内除法与重复 GM load；行基址用 `base += step` 递推。
4. **宽访问**：`j = lane·4`，每 lane 16B；行内循环展开 ×2/×4 发独立 16B load/store 提高 MLP；
   行尾余量单独处理。
5. **单趟直写**：判 kind 后立即写 dst；命中行与 miss 行在同一循环的不同分支；不生成 plan、
   不经 scratch。
6. **缓存策略**：默认普通 store；大输出避免 write-through；必要时再对比流式提示。
7. **密度门控**：统计活跃项数与扫描长度，按 `活跃项数 × warp 宽度 > 扫描长度` 选 warp-per-slot，
   否则 per-thread。
8. **归约侧**：先把归约下沉为 UB 聚合 + 块内 merge，再考虑跨核扇出；保留必要的跨 block 同步。

## 6. LLM 前置问题

- 输出段占整算子的比例是多少（按 kernel / 按段拆分）？
- 行字节 `D·es` 多大、能否被 16 整除？行数 B 与 warp 数的比值是多少？
- 当前线程↔地址映射是"per-thread 连续段"还是"lane 交织"？行内是否重复读 plan/kind/slot、是否有除法？
- 是否存在 scratch / plan 的 GM 往返？输出是否使用了 write-through 的流式写？
- 命中与未命中的比例？命中行与 miss 行是否由同一个 warp / 同一个核写？
- 校验或归约是否存在稀疏场景？活跃量与扫描长度的比值是否触发密度门控？
- 归约是否依赖跨 block 同步？现在是 GM 原子还是 UB 聚合 + 块内 merge？

## 检索卡（短卡）

动作：把每线程独占一段连续地址写输出改为按行分 warp、lane 交织宽访存、判定与写出同趟、普通 cached store。
适用：行结构明显、输出为按行命中拷贝或整行初始化、行字节可被宽向量整除、行数远大于 warp 数。
限制：16B 组不得跨行；warp 内分支须一致；稀疏时活跃 lane 少须密度门控回退 per-thread；大输出避免 write-through。
范围：行稀疏输出的写回环节（按行命中或未命中的整行拷贝与初始化）。
检索词：warp-per-row、lane 交织、uint4、合并访存、密度门控、cached store、unroll。
机会：线程映射为每线程一段连续地址，同 warp lane 跨扇区，输出通路有效带宽只有合并访问的零头。
代价：需行级元数据一次读入与分支一致化，稀疏行会空转。
