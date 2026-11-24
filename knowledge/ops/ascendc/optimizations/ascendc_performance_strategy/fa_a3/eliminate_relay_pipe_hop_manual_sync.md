---
type: Optimization
title: 消除"中转专用"管线 hop（plain TBuf + 手工跨管线同步替代 TQue 桥）
description: 将纯拷贝中转管线改为 plain TBuf，并在生产者写与消费者读之间显式同步。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/04-eliminate-relay-pipe-hop-manual-sync.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：消除"中转专用"管线 hop（plain TBuf + 手工跨管线同步替代 TQue 桥）

> **单一优化点：** 当一条数据通路形如 `GM→(管线A)→UB→(中转管线B)→UB→(管线C)→GM`，而**中转管线 B 不做任何计算/变换**（仅因 TQue 自动同步的拓扑约束而存在，用于把数据从 A 的输出缓冲桥接到 C 的输入缓冲）时，把中转段删除：用一个 **plain `TBuf`** 同时承载 A 的写与 C 的读，并在 A→C 之间用**显式 `SetWaitFlag<HardEvent::A_C>`** 手工同步。删掉中转 `DataCopy`(UB→UB) 及其同步，把 3 hop、2 同步/元素降到 2 hop、批量同步。
>
> **与策略 03 的区别：** 03 是"**批量** gather/scatter"（攒 N 行再搬），其收益来自批量化；03 的实现恰好用了 plain TBuf + 手工同步，但那是手段。本策略是"**删中转 hop**"，收益来自少一跳搬运与同步，**与是否批量无关**——即使不批量、逐元素中转，只要中转 hop 是"纯桥"，都能用本策略删掉。两者正交，可独立或叠加。
>
> **算子/管线无关性：** 适用于 AscendC 任意"GM→UB→(纯桥)→UB→GM"中转通路（Vector、Cube 管线组合均可），只要中转段无变换且 A→C 存在可用 `HardEvent`。不限于任何具体算子。

本策略只删"纯桥中转 hop"。不改变数据值/语义、不改 tiling、不改跨核同步、不引入批量（批量属 03）或软流水。

---

## 1. 优化原理

### 1.1 性能问题模式（通用）

AscendC 里把数据从 GM 经 UB 中转再回 GM，常写成"双 TQue 桥"：

```text
inputQue(VECIN):  DataCopy GM→UB (MTE2); EnQue 自动插 MTE2→V
bridgeQue(VECOUT): DataCopy UB→UB (V 复制); EnQue 自动插 V→MTE3
                  DataCopy UB→GM (MTE3)
```

TQue 的 `EnQue/DeQue` 只为其**所在管线位置的自然前驱→本管线**插同步（buffer-guide §3.4：TQue 不处理同轮内跨管线二次依赖）。因此 `GM→UB(MTE2)` 要到 `UB→GM(MTE3)`，靠单 TQue 拼不出 MTE2→MTE3，被迫引入一个 **V 复制桥**（VECIN 自动 MTE2→V，VECOUT 自动 V→MTE3），多一跳 UB→UB 与多一类同步。

若这个 V 段**不做任何变换**（不是 cast/transpose/compute，只是把字节从 A 缓冲搬到 C 缓冲以满足同步拓扑），它就是"纯桥 hop"——纯开销。

### 1.2 本策略利用的硬件机制

| 机制 | 利用方式 |
|---|---|
| plain `TBuf` | 不带自动同步的裸 buffer，可被任意管线读写，不被 TQue 拓扑约束 |
| 显式 `HardEvent` 同步 | `SetWaitFlag<HardEvent::A_C>` 直接同步任意两个管线（如 `MTE2_MTE3`/`MTE3_MTE2`），无需中间 hop |
| 单/双缓冲复用 | 单缓冲跨轮靠 WAR(`C_A`) + RAW(`A_C`)；双缓冲可去 WAR（非本策略） |

核心改动：

```text
# 基线（纯桥）
DataCopy ubA, gm, len            # MTE2
<TQue 自动 MTE2→V>
DataCopy ubC, ubA, len           # V 复制（纯桥，无变换）
<TQue 自动 V→MTE3>
DataCopy gm, ubC, len            # MTE3

# 改写（删桥）
buf = tbuf.Get<T>()              # plain TBuf，A 与 C 共用
SetWaitFlag<MTE3_MTE2>()         # WAR：上一轮 MTE3 读完，MTE2 才许覆写（单缓冲）
DataCopy buf, gm, len            # MTE2
SetWaitFlag<MTE2_MTE3>()         # RAW：MTE2 写完，MTE3 才许读
DataCopy gm, buf, len            # MTE3
```

---

## 2. 适用条件与泛化边界

必须**同时**满足：

| 条件 | 要求 |
|---|---|
| 通路形态 | 多段 UB 中转 `GM→UB→…→UB→GM`，存在一个中间管线段 |
| 纯桥判定 | 该中间段**不做计算/变换**（不是 cast/transpose/reshape/elementwise），仅搬字节 |
| 同步拓扑 | 该中间段仅因 TQue 自动同步覆盖不到 A→C 而存在（非数据依赖必需） |
| HardEvent 可用 | A→C 与 C→A 的 `HardEvent` 在目标平台存在（如 `MTE2_MTE3`/`MTE3_MTE2`/`V_MTE3`/`MTE3_V`/`MTE2_V`/`V_MTE2` 等） |
| 布局兼容 | A 写入与 C 读取的 UB 布局一致（无需 reshape）；否则中间段不是纯桥，不能删 |
| 基线稳定 | 修改前 build/精度/性能可重复 |

优先适用：

- profiling 显示某 UB→UB `DataCopy`（常落在 V 管线）占比高，且该搬运无变换。
- 通路是"读 GM→（中转）→写 GM"的纯 relay（gather/scatter/搬运中转）。
- 中转 hop 是为修同步 bug（如 VECIN 不覆盖 V→MTE3 的 NaN bug）而引入的桥。

不适用或需先重构：

- 中间段**真做变换**（cast、transpose、elementwise、reduce）——那是真实工作，保留；可另评估能否用一条指令合并，但非本策略。
- A→C 无可用 `HardEvent` 对（平台/管线不支持直接同步）——仍需中间 hop。
- 数据需在中转段 reshape/改布局——非纯桥。
- 收益来自批量（用 03）、软流水、double buffer——非本策略。

---

## 3. 实施要点

### 3.1 判定"纯桥"

逐段问：该 `DataCopy`/指令是否改变数据的**值或布局**？
- 仅 `DataCopy(UB_dst, UB_src, n)` 等拷贝、无计算 → 纯桥候选。
- 含 `Cast`/`Transpose`/`Adds`/`Mul` 等 → 真变换，**不可删**。
- 纯桥删除后，A 的输出布局须与 C 的输入布局一致（同 dtype、同排布、同 stride）。

### 3.2 plain TBuf 替换 TQue

- 把中转链路上的 VECIN/VECOUT `TQue` 换成一个（或复用一个）plain `TBuf<TPosition::VECCALC>`。
- A 的写与 C 的读指向同一 `TBuf`（或同 `TBuf` 内不同槽位，按布局）。
- 删去所有 `AllocTensor/EnQue/DeQue/FreeTensor`（plain TBuf 用 `Get<T>()` 直接取，无队列语义）。

### 3.3 手工跨管线同步

- RAW（先写后读）：A 写完 → C 读，`SetWaitFlag<HardEvent::A_C>`（如 `MTE2_MTE3`）。
- WAR（同 buffer 跨轮覆写）：C 读完 → 下一轮 A 写，`SetWaitFlag<HardEvent::C_A>`（如 `MTE3_MTE2`）。
- 单缓冲跨轮复用：每轮首 WAR、A 后 RAW（同 05 §6.1）。
- 双缓冲：可去 WAR，两槽交替；但非本策略范围。
- 同步事件类型必须与真实管线对一致（误用如把 S 当 V 是常见错误）。

### 3.4 与 TQue 并存

- 未被本策略影响的其它 TQue（真正的计算流水）保留其自动同步。
- 只在"纯桥"链路上换 plain TBuf + 手工同步；不要全局去 TQue 化。

---

## 4. 数据与缓存布局

- plain `TBuf` 容量 = 实际承载的数据量（A 写入量 = C 读取量）；按 §3.1 布局兼容性确认。
- 删除中转 buffer（原中转 TQue/桥 buffer）后，其容量可回收或转作他用（见策略 05）。
- 单缓冲复用须保证 WAR/RAW；同一通路有多段独立数据流时可各开一个 plain TBuf，同步独立。

---

## 5. 正确性红线

### 5.1 同步正确性（核心）

- **必须**在 A 写与 C 读之间插入 RAW（`A_C`）；单缓冲跨轮还要 WAR（`C_A`）。
- 首轮无"上一轮 C"，但须保证 C 不读到未初始化数据（首轮 A 先于 C 自然成立）。
- 事件类型匹配真实管线对；`HardEvent` 须为平台支持的合法枚举。
- 漏加/倒置 ⇒ 读未完成或被覆写数据 ⇒ NaN/错值（§6 陷阱 1）。

### 5.2 纯桥判定不可放宽

- 只有**确认中间段无变换**才能删。若误删含变换的 hop，数值错误（§6 陷阱 2）。
- A 输出布局须与 C 输入布局一致；不一致则需保留中转段（其负责 reshape）。

### 5.3 TQue 同步剥离范围

- 只剥离"纯桥"链路的自动同步；不要误删其它 TQue 的同步。
- plain TBuf 不提供任何自动同步——所有跨管线依赖必须手工补全。

### 5.4 数值正确性

- 不改变数据值、布局、dtype、有效行/列语义。
- 仅改变搬运与同步编排。

---

## 6. 已知陷阱

### 陷阱 1：手工同步漏加或事件类型错用

问题：删 TQue 桥后忘加 RAW/WAR，或事件类型用错（如 `MTE2_V` 守卫 MTE3 读）。
症状：读到未完成/被覆写数据，NaN/错值，常与轮次/批数相关。
修复：§3.3/§5.1，按真实管线对插 RAW（`A_C`）+ 单缓冲 WAR（`C_A`）。

### 陷阱 2：误删含变换的中转段

问题：把含 cast/transpose/elementwise 的中转当纯桥删除。
症状：数值错误（缺变换）。
修复：§3.1 逐段判定；含变换段保留。

### 陷阱 3：布局不兼容强删

问题：A 输出布局与 C 输入布局不同（如 NZ vs ZZ、不同 stride），强删中转导致 C 读错。
症状：数据错位/错值。
修复：确认布局一致；不一致保留中转段。

### 陷阱 4：HardEvent 不可用

问题：目标平台不支持 A→C 的 `HardEvent`，仍强删桥。
症状：编译失败或同步无效。
修复：确认 `HardEvent` 枚举可用；不可用则保留中间 hop。

### 陷阱 5：误把本策略当批量

问题：期望删桥带来"批量"收益，混淆 03。
澄清：本策略不批量，收益是少一跳搬运+同步；批量请用 03。两者可叠加（03 的累加器路径本就用了本策略删 V 桥）。

---

## 7. LLM 实施前必须回答的问题

| 问题 | 必填内容 |
|---|---|
| 通路形态 | 哪条 GM→UB→…→UB→GM 链路，几个 hop，哪些 TQue |
| 纯桥判定 | 中间段是否无变换（逐段确认）；A 输出与 C 输入布局是否一致 |
| 同步拓扑 | 中间段是否仅因 TQue 覆盖不到 A→C 而存在 |
| HardEvent | A→C、C→A 的合法事件；平台是否支持 |
| 同步落点 | RAW(`A_C`)、单缓冲 WAR(`C_A`) 的位置 |
| buffer | plain TBuf 容量；中转 buffer 删除后容量去向 |
| 瓶颈定位 | profiling 是否显示中转搬运（常 V 管线）占比高 |
| 基线可重复 | 修改前 build/精度/性能基线值 |

任一项无法回答，不实施本策略。

---

## 8. 禁止事项与回退条件

禁止：

- 删除含计算/变换的中转段（陷阱 2）。
- 漏加/错用 RAW/WAR 同步（陷阱 1）。
- 在布局不兼容时强删中转（陷阱 3）。
- 在 `HardEvent` 不可用时强删（陷阱 4）。
- 全局去 TQue 化（只对纯桥链路换 plain TBuf）。
- 改变数据值/布局/dtype。

回退或缩小策略的条件：

- 中间段实际含变换或布局不兼容 → 保留中转。
- A→C 无可用 `HardEvent` → 保留中间 hop。
- 精度失败且无法定位到同步（陷阱 1）/误删变换（陷阱 2）/布局（陷阱 3）单一原因。
- profiling 显示中转搬运**未下降**——说明该 hop 非瓶颈或非纯桥，重新归因。

---

## 9. 验收标准

最小验证：

```bash
bash <build> --soc=<soc> --op=<op> && bash <build> --soc=<soc> --op=<op> --wheel
source <set_env> && pytest <op>/test/test_<op>_*.py
```

精度：与基线一致。

性能（profiling 归因）：

- 中转搬运所在管线时间下降（同步数下降是直接贡献之一）。
- 对应 `DataCopy` 指令数下降（少一跳/元素）。
- 整体不劣化；该链路在关键路径时整体下降。
- 常与 03 叠加：03 的累加器路径用本策略删中转桥，两者收益相对"各自前序状态"评估。

边界：单缓冲跨轮（WAR+RAW）、多段独立 TBuf、不同管线对（MTE2/V/MTE3/S 组合）、不同 dtype。

性能结论须写清：

```text
本策略收益相对"含纯桥中转 hop"基线；判据是中转搬运管线时间 + 同步数下降。
与 03 正交：03 批量、本策略删 hop，可叠加。未单独隔离测量时，按机制归因。
```

## 检索卡（短卡）

动作：将纯拷贝中转管线改为 plain TBuf，并在生产者写与消费者读之间显式同步。
适用：GM 与 UB 多段中转中存在只拷贝、不计算且不改变值或布局的中间段。
限制：A写与C读之间必须插入RAW(A_C)同步；单缓冲跨轮复用还必须有WAR同步。
范围：GM→UB→UB→GM 的纯桥接数据通路
检索词：plain TBuf、TQue、HardEvent、RAW、UB 中转、DataCopy
机会：通路含仅执行 UB 间 DataCopy 的中转管线段。
