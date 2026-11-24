---
type: Optimization
title: 收尾段代数化死工作消除（只喂养单调比较通路的偏置加法整段删除）
description: 删掉只喂养单调比较通路的偏置加法及其装载，连带其后随屏障与目标段 UB 写读往返一并消除。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/cv-A5/40-epilogue-algebraic-dead-work-elision.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：收尾段代数化死工作消除（只喂养单调比较通路的偏置加法整段删除）

> **来源：A5 自由探索实测（matmul_bias_argmax，2026-09-14，107 裸机）**
> direction_key: `aiv-consume-lane-op-volume::argmax-shift-invariance-bias-add-elimination::vector-tile-consume-loop`
> 证据：<AOA_ROOT>/campaigns/matmul-bias-argmax-a5-107-20260912-opencode/framework/aoa_out/matmul_bias_argmax_custom/loop_<run-id>/explore/direction_004/
> 实测：1.1715 x（geomean 36.6103→31.2519us，23/25 条目 -8~-23%；fp32 AIC-bound 与 REDLINE-tie 条目按预测持平），精度 22/22 **bit-exact**，REDLINE-tie 首下标逐位不变。

## 原理

当某个中间量**只**喂养单调比较通路（典型：argmax/argmin/max 归约）时，对它的「加偏置 / 加常数」不改变比较结果（平移不变性），该项的装载与逐行加法是**死工作**，可整段删除。

收益是三重叠加的：删掉一条向量指令的同时，其后随的 `PipeBarrier` 与目标段的 UB 写读往返也一并消失——实测收益（-14.64%）显著超出「消费段指令数 4→3」的线性模型预测（-4~-5%），差额就来自屏障与 UB 往返。

## 性能问题模式（哪些 profiling 信号说明该用）

- 消费/收尾段是 top1 流水，且其指令构成里存在「装载偏置 → 加法 → 比较/归约」的固定小链（每行重复）。
- 该偏置的消费者只有一个，且该消费者是单调的（比较、max/min、argmax/argmin）。
- 消费段的收益模型按「指令数线性」预测时总是偏低——说明屏障与 UB 往返也在同一条链上（本条正好把它们一起删掉）。
- 与其它消费段策略（双 lane 拆分、屏障塌缩、批量化）叠加后仍有一段固定开销未消。

## 正确性红线（什么情况下禁止用 / 必须回退）

1. **代数等价性必须证明**：只有「平移 + 单调比较」这一对才成立；加法必须保序（浮点加法在有限范围内保序，但**NaN/Inf 与溢出**会破坏保序——须确认该通路不产生 NaN/Inf，或在证明里排除这些取值域）。
2. **精度暴露面不得增大**：变换后输出与基线的关系必须可证（实测 22/22 bit-exact，REDLINE-tie 首下标逐位不变）。
3. **tie-break 语义逐位保持**：argmax 的首下标/末下标语义是守门 case（有 tie 的 REDLINE 条目必须单列验证）。
4. **只在「单消费者」时删**：若同一偏置还喂养输出累加或其它消费者，禁止跨用途删除；删除前把消费者集合列全。
5. **顺序改变时的兜底**：删除会改变该段的中间值（少一步单调舍入），若下游对中间值有依赖（例如把中间值也写出去），本条不适用。

## 泛化条件（dtype / shape / pipeline / 算子类型）

- dtype：与 dtype 无关；但浮点取值域（NaN/Inf/溢出）须逐 dtype 复核。
- shape：消费段每行都执行该链的形态收益最大（行数多、行宽小）；AIC-bound 的 case 无收益（实测持平）。
- 流水线：`aiv_vec` / `aiv_scalar` 的消费段；对任何「偏置只喂养单调归约」的融合算子适用。
- 与 05/26 号卡（收尾段批量化/多行合批）互补：那两张卡降低该链的**发射次数**，本条**直接删掉链上的一项**；叠加时先删项再批量化。
- 与 11/16 号卡（双 lane 数据面拆分）互补：拆 lane 后每条 lane 上的死工作同样值得删。

## 实施步骤（从证据里的真实 diff 抽象成通用步骤）

1. 列出消费段的逐行指令链与每个中间量的消费者集合。
2. 判定待删项是否只喂养单调通路；给出平移不变性 + 保序性论证（含取值域，排除 NaN/Inf/溢出）。
3. 删除该加法及其装载；同步删除其后随的屏障与去往目标段的 UB 写读往返。
4. 复核下游消费者未受影响（尤其是写出去的量）。
5. 全量精度用例通过（含 tie/REDLINE 条目），核对逐位一致。
6. 配对测量并做收益分解：指令数减少 + 屏障消失 + UB 往返消失三项分别的贡献。

## LLM 前置问题（应用前必须自问）

1. 该中间量的消费者有哪些？是否只喂养单调比较？
2. 平移不变性与浮点保序在什么取值域成立？NaN/Inf/溢出会不会出现？
3. tie-break（首/末下标）语义会不会被影响？守门 case 是哪条？
4. 删掉这条指令后，哪些屏障和 UB 往返可以一并删？
5. 收益模型是按指令数线性算的吗？是否低估（屏障/往返）？
6. 该段是不是 top1 流水？不是的话收益预期应下调。

## 验收标准（编译 / 精度 / 性能判据，含噪声底口径与回退阈值）

- **构建**：编译通过；删除后的中间量无残留引用（编译期 + 运行期各一处）。
- **精度**：全量用例通过（实测 22/22）且**输出与基线逐位一致**（bit-exact 是硬判据，含 tie 条目）。
- **性能**：配对 geomean 超噪声底（实测 1.1715x）；收益集中在消费段主导的条目（实测 -8~-23%）。
- **零劣化判据**：AIC-bound 与 tie 条目按预测持平（实测），不得出现稳定回退。
- **归因**：给出三重叠加的分解证据（指令数、屏障、UB 往返）。
- **回退**：等价性无法证明、取值域含 NaN/Inf、或 tie 语义受影响时，恢复原加法链。

## 检索卡（短卡）

动作：删掉只喂养单调比较通路的偏置加法及其装载，连带其后随屏障与目标段 UB 写读往返一并消除。
适用：中间量只喂养单调比较通路（argmax/argmin/max 归约）、且为单消费者的消费/收尾段。
限制：须给出平移不变性加保序论证（排除 NaN/Inf/溢出取值域）；输出逐位一致、tie-break 首下标逐位不变；只在单消费者时删。
范围：融合算子消费/收尾段的逐行指令链（代数等价化简）。
检索词：移位不变性、死工作消除、偏置加法、单调归约、argmax、PipeBarrier、UB 往返、bit-exact、tie-break。
机会：消费段存在「装载偏置→加法→比较」固定小链且每行重复；按指令数线性预测收益总偏低（屏障与 UB 往返同链）。
