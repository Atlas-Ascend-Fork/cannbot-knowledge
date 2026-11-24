---
type: Optimization
title: 增大 cube/vector 计算基本块
description: 把单级分块 kernel 的 baseM/baseN/baseK 三者同步放大（baseK 覆盖整个 dim 使 kTiles=1），host 派生量同步调整。
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/01-increase-base-block-size.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：增大 cube/vector 计算基本块

> **单一优化点：** 在不改变任何计算语义、不引入新的分块层级、不改动跨核任务划分的前提下，把一个"单级分块" AscendC 矩阵类 kernel 的基本块——cube 输出 tile 的 `baseM`、`baseN` **与 reduce 轴步进 `baseK`**——**三者同步放大**（翻倍或按容量公式取更大值），并同步调整 host 端对齐量、tiling 派生量、kernel 端 L1/L0/UB buffer 尺寸与循环步长。`baseK` 应放大到覆盖整个 `dim`（使 `kTiles = ceil(dim/baseK) = 1`），让单次 `Mmad` 完成整个 reduce 轴，消除多次 load/Mmad 迭代与 L0C 累加同步。不新增缓冲、不删同步、不改数据流。

> **术语统一（baseMNK）与算子常量映射：** 本策略用 `baseM`/`baseN`/`baseK` 三个统一术语描述基本块的三个维度（M=矩阵乘法输出行、N=矩阵乘法输出列、K=reduce 轴步进），**三者必须作为一个整体同步放大，禁止只改其中一维**。不同算子的 kernel 常量命名可能不同，应用前必须先建立映射：
>
> | 策略术语 | 含义 | 常见算子常量名 |
> |---|---|---|
> | `baseM` | cube 输出 tile 的 M 维（Q 行块） | `BLOCK_M` / `blockM` / `mBase` |
> | `baseN` | cube 输出 tile 的 N 维（KV 列块） | `BLOCK_N` / `blockN` / `nBase` |
> | `baseK` | reduce 轴单次步进（覆盖 dim） | `BASE_K` / `Kstep` / `kBase` |
>
> **⚠️ 高危陷阱（见 KP-031）：** 若只放大 `baseK`（或算子里对应的 K 维常量，如 `BASE_K`）而 `baseM`/`baseN` 不变，本策略**不成立**——把 K 维放大到超过 `dim` 不会减少循环次数（`kTiles` 已为 1），只会浪费 L0A/L0B 容量并可能引发精度问题，对端到端性能零贡献。历史上 codegen 曾因此把策略退化为"只改 BASE_K"，连续多轮零收益。**提交 diff 前必须自检：baseM、baseN、baseK 三个维度的常量是否都被修改；若仅 K 维变化，立即回退重做。**

> **已验证锚点：** 在一组 attention-like 前向 shape（fp16/bf16，序列长明显大于初始块行数，KV 被多个 Q 行重复访问）上，盲实现编译通过、精度 PASS，相对较小基本块基线有接近整数倍的端到端加速。该收益的硬件来源是 L0A/L0B/L0C/matrix unit 利用率提升、外层循环（KV 列循环）与 launch/同步次数成比例下降。本策略**只对"基本块即主要分块粒度"的单级实现有效**；若实现已有两级分块（外层常驻块 + 内层 micro tile），基本块只是内层 micro tile，放大收益会边际递减，应改用"两级 L1 复用"类策略。

本策略只做"放大基本块"一件事。多缓冲软流水、两级分块、删除冗余同步、改 matmul helper、改 softmax 公式、改输出布局或 dtype 都**不属于**本策略，必须作为独立实验。

---

## 1. 优化原理

### 1.1 性能问题模式

低效基线用一个固定较小基本块（记 `baseM = baseN = B0`，通常等于矩阵单元硬件粒度的若干倍）作为**唯一**分块粒度：

```text
for qBlock in qSeq step baseM:        # baseM 既是加载块也是 matmul M
  load Q[baseM, dim] once
  for kvBlock in kvSeq step baseN:    # baseN 既是 KV 加载块也是 matmul N
    load K[baseN, dim], compute S[baseM, baseN]  # 一次完整 cube tile
    softmax on S[baseM, baseN]                     # vector 一次处理整块
    load P[baseM, baseN], compute O += P @ V[baseN, dim]
```

这里 `baseM/baseN` 同时是「cube tile 大小」「加载块大小」「vector softmax/输出块大小」「外层循环步长」。当 `kvSeq` 较大时，KV 列循环被切成很多次 `kvSeq / baseN`；每次都要走完整的 cube→vector→cube 串行 + workspace 往返 + 跨核队列同步。`baseM/baseN` 偏小导致：

- matrix unit 单次 `Mmad` 的 m/n 维度小，L0C 填充率低，cube 单元空转比例高；
- 外层循环迭代多，每次迭代的 launch/同步/fixpipe/queue acquire-release 开销被放大；
- 同一个 Q 块被重复读写、softmax 状态在多个小 KV 块间频繁 online 合并，归并开销随 `kvSeq/baseN` 线性增长。
- `baseK < dim` 时 reduce 轴被切成 `kTiles = ceil(dim/baseK)` 段，每个 (m,n) tile 要 `kTiles` 次 L0A/L0B load + `Mmad` + L0C 累加，串行开销与 L0C 累加同步随 `kTiles` 线性增长（如 `dim=128, baseK=64` 时翻倍）；放大 `baseK` 到 `dim` 使 `kTiles=1`，单次 `Mmad` 完成 reduce 即可消除该开销。

### 1.2 本策略利用的硬件机制

| 机制 | 利用方式 |
|---|---|
| L0A/L0B/L0C | 放大 matmul tile 的 m/n，使单次 `Mmad` 更接近 L0 容量上限，提升 matrix unit 填充率与吞吐 |
| cube 单元 | 更大的 baseM 让一次 cube launch 完成更多行，降低 cube 空转与 K 维循环外的常数开销 |
| 数据搬运 | KV 列循环次数减半（baseN 翻倍），GM→L1 的 KV tile 发射次数、地址计算、MTE2 等待次数同比下降 |
| 同步/launch | 外层 KV 循环次数减半，AIC↔AIV 队列 acquire/release、跨核 flag、launch 常数开销同步减半 |
| vector 单元 | vector 单次处理更大的 baseM 行块，reduce/cast 写回的条带数下降，vector 流水填充更饱满 |

核心是把"基本块"在硬件容量允许范围内整体放大，所有派生量按同一比例缩放：

```text
new_baseM, new_baseN = scale_up(old_baseM, old_baseN, hw_limits)
assert new_baseM % C0 == 0 and new_baseN % C0 == 0
# host: qSeqLenAlign  = AlignUp(qSeqLen, new_baseM)
#       kvSeqLenAlign = AlignUp(kvSeqLen, new_baseN)
#       tailValid     = kvSeqLen % new_baseN
#       (q/kv stride 不随块大小变化)
# kernel: 所有 L1/L0/UB buffer 与循环步长用新 baseM/baseN 重新派生
```

注意：放大基本块**不减少**每个 tile 的 GM→L1 总搬运字节数（K/V 仍要被搬一遍），它减少的是**次数**（launch/同步开销）和提升的是**单次 cube 的填充率**。若瓶颈纯粹在 GM 带宽且 cube 已饱和，收益会消失。

---

## 2. 适用条件与泛化边界

### 2.1 必须满足

| 条件 | 要求 |
|---|---|
| 单级分块 | 当前实现里"加载块 == matmul tile == softmax tile == 输出 tile == 外层循环步长"是同一个量。**这是本策略的前提**。若已存在"外层大块常驻 + 内层 micro tile"，则基本块已是内层 micro，放大它收益递减，应改用两级 L1 复用策略 |
| 容量有余量 | 放大后的 L1/L0/UB 峰值占用仍小于目标硬件各级容量上限（见 §3 公式） |
| 对齐可满足 | 新 baseM、new baseN 都是 `C0`（half/bf16=16）的整数倍；`baseM * baseN` 在 vector 侧仍满足 32B 对齐 |
| seq 可整除或可处理尾块 | `qSeqLen`、`kvSeqLen` 不是新块的整数倍时，实现已具备正确的尾块处理：KV 尾块基于 `min` + `AlignUp` + 有效列数 `tailValid` 屏蔽；Q 尾块基于输出 clamp **且** padding 行清零/屏蔽（见 §4.1，放大 baseM 后 Q 尾块 padding 行污染会放大，不能仅靠输出 clamp）；否则必须先补尾块处理 |
| 基线稳定 | 放大前 build、精度、性能可重复 |
| dtype/hw 一致 | 放大前后同一 dtype、同一硬件（L0A/L0B/L0C/UB/L1 容量相同） |

### 2.2 优先适用（收益最大）

- 序列长明显大于初始块行数，外层 KV 循环迭代数大（`kvSeq / baseN` 大）。
- 初始 `baseM/baseN` 偏小，matrix unit 单次 `Mmad` 的 m/n 远低于 L0 容量下限。
- profiling 显示 cube 单元利用率低、launch/同步/queue 等待占比高、KV tile 发射次数多。
- Q 块被同一 head 内多次重复访问，放大 Q 块（baseM）能摊薄 Q 的 GM→L1 搬运。

### 2.3 不适用或需先重构

- 实现已有两级分块（外层常驻块 + 内层 micro tile）：基本块是内层 micro，放大它只是改内层 tile，外层复用范围不变，收益边际递减，应改用"放大外层常驻块 / 两级 L1 复用"策略。
- 放大后 L1/UB/L0 任一超限，且无法通过"减少 L1 内并发的 buffer 数"或"给 vector 块加行切分"收回：必须先重构，不能硬放大。
- 跨核任务划分依赖块大小整数关系（如核数 = 总块数），放大后总块数变化导致核分配不均且未重新调度。
- 当前实现存在已知正确性 bug（坐标系错误、状态未重置、尾块未处理）：必须先修，否则放大会放大 bug。
- 收益期望来自改变 softmax 公式、scale、mask 或 dtype：不属于本策略。
- 目标硬件 L0A/L0B/L0C 容量极小，放大小块即超限。

---

## 3. 基本块选择规则

本策略的核心：**让应用者能独立根据硬件各级容量推导出目标块大小**，而非照抄某个数字。

### 3.1 硬件容量约束（通用，按目标硬件手册代入具体值）

设 `E = sizeof(elem)`（half/bf16 取 2），`F = sizeof(float)=4`，`C0 = 32/E`（half/bf16=16），`Kdim` 为 matmul 的 K 方向单次步进（通常 = `AlignUp(dim, C0)` 的一个分段），`RING` 为 workspace 往返 slot 数，`depthA/depthB` 为 L0A/L0B 队列深度。

```text
# —— cube 侧 L0 容量上限 ——
L0A 需求 = depthA * baseM * baseK * E       <= L0A 容量
L0B 需求 = depthB * baseK * baseN * E       <= L0B 容量
L0C 需求 = baseM * max(baseN, dim) * F     <= L0C 容量   # 累加器是 m×n(不含 reduce 维 baseK): MM1 输出 baseM×baseN, MM2 输出 baseM×dim

# —— cube 侧 L1 容量上限（同时驻留的 cube buffer 峰值）——
L1 峰值 = baseM * dimAlign * E       # Q 工作块（单缓冲）
        + baseN * dimAlign * E       # K/V 当前工作块（单缓冲，KV 复用同一 buffer）
        + baseM * baseN   * E        # P 工作块（MM2 左矩阵，单缓冲）
        <= L1 容量

# —— vector 侧 UB 容量上限 ——
UB 输入块 = max(baseM * baseN * F,   vec2 行切分块)
UB 输出块 = max(baseM * baseN * E,   vec2 行切分块,  baseM * dimAlign * F)
UB 其它  = softmax tmp + softmax state(max/sum/exp，各 baseM * F)
         + softmax default(max/sum)
         + brcb( AlignUp(baseM, BRCB) * BRCB * F )
         + mask( baseN * F )
UB 总计 = UB输入块 + UB输出块 + UB其它   <= UB 容量
```

> 推导流程：先固定 `baseM`（受 Q 行块、L0A、L1 Q 块、UB state 行数约束），再在每个 `baseM` 下用 L0B/L1 K-V 块/UB mask 约束选最大可行 `baseN`。两者都必须是 `C0` 的整数倍。建议 `baseM == baseN`（本算子 Q 块与 KV 块用同一常量），简化推导且通常更优。
>
> `baseK` 选择：优先放大到 `baseK = AlignUp(dim, C0)`（覆盖整个 reduce 轴，`kTiles=1`），用上面 L0A/L0B 的 K 维容量公式验证不超限。若 `depthA*baseM*baseK` 或 `depthB*baseK*baseN` 超限，优先缩 `baseK`（接受 `kTiles>1`）而非缩 `baseM/baseN`，但 `kTiles>1` 会重新引入多次 load/Mmad 迭代与 L0C 累加同步（见 §1.1、§4.1 dim 尾块），需在容量与 reduce 串行开销间权衡。

### 3.2 选择函数（泛化伪代码）

```text
PickBlockSize(old_base, C0, hw):
    # 1. 候选必须是 C0 的整数倍，且 >= old_base（只放大不缩小）
    cand = smallest C0-multiple > old_base
    # 2. 在 L0A/L0B/L0C/L1/UB 全部容量公式满足的前提下，取最大候选
    while L0A_ok(cand) and L0B_ok(cand) and L0C_ok(cand) \
          and L1_ok(cand) and UB_ok(cand):
        cand += C0            # 沿 C0 粒度继续放大
    return cand - C0          # 上一个满足的就是目标
```

经验起点：若初始 `baseM=baseN` 约为一个 `C0` 的若干倍且容量公式留有 ≥2x 余量，目标值通常是初始值的整数倍（常见为 2 倍）。但**必须由 §3.1 公式验证**，不能凭"翻倍"直接写死。

### 3.3 seq 整除性检查

选定 `new_baseN` 后必须确认：

- 若 `kvSeqLen % new_baseN == 0`：无 KV 尾块，`tailValid=0`，正常路径。
- 否则：`tailValid = kvSeqLen % new_baseN`，且实现**必须**已具备尾块屏蔽（见 §4.1）。放大块后单个尾块的最大无效行数从「旧块 − 1」增长到「新块 − 1」，尾块占块的比例同步增大，更要确认尾块路径仍正确。

`qSeqLen` 不需要整除 `new_baseM`（Q 尾块通过输出 clamp + padding 行清零/屏蔽处理，见 §4.1），但 `qSeqLenAlign` 必须用新 `new_baseM` 重新对齐。**注意：Q 尾块不能仅靠输出 clamp，必须同时保证 padding 行不污染有效行（见 §4.1 Q 尾块 padding 污染判据）。**

---

## 4. 正确性红线

### 4.1 尾块

- **KV 尾块**：`kvRows = min(baseN, kvSeqLen - rowStart)`；`kvRowsAlign = AlignUp(kvRows, C0)`；L0B/K 的 `dstNzC0Stride` 用 `kvRowsAlign`（尾块）或 `baseN`（满块），二者要保持 NZ 布局一致。matmul 的 `n` 维用 `kvRowsAlign`。vector 侧 softmax 的 `oriSrcK` / mask 必须用**有效列数** `tailValid`（最后一个 KV 块）屏蔽 padding 列，不能假设满块。
- **Q 尾块**：`validRows = min(baseM, qSeqLen - rowBase)`；Q 加载用 `validRows` 行但 L1 Q buffer 的 NZ 布局 `dstNzC0Stride` 仍取**满块** `baseM`（保证 L0A 寻址一致）；输出写回必须 clamp 到 `[0, qSeqLen)`，不写 padding 行。
  - **放大 baseM 后必须重新校验 Q 尾块 —— padding 行污染会被放大。** Q 尾块时 `validRows < baseM`，但 L1 Q buffer 的 NZ 布局仍按满块 `baseM` 排布（`dstNzC0Stride = baseM`，保证后续把 Q 搬进 L0A 的 `LoadData` 按同一 `srcStride = baseM/C0` 寻址一致）。若 Q 块加载逻辑只写 `validRows` 行而**未清零、未屏蔽** `[validRows, baseM)` 的 padding 行，这些 padding 行是 L1 残留的未初始化数据，随后会被 L0A 加载步骤当作有效矩阵行加载进 L0A、参与 `Mmad`，污染 L0C 与最终输出。**`baseM` 越大，padding 行数（`baseM - validRows`）越多，残留未初始化数据越多，污染越严重**——这正是放大块后必须重新验证 Q 尾块的根因。注意本污染**与 host 侧把 Q 维 pad 到 `baseM` 倍数填 0 无关**：只要 kernel 侧 Q 尾块加载只搬 `validRows` 行、L1 NZ 布局仍取满块 `baseM`，padding 行就会暴露；host padding 只解决 GM 对齐，不解决 L1 padding 行未初始化问题。
  - **判据：padding 行污染是否扩散到有效行。** 关键取决于 `Mmad` 的 m 维是否包含 padding 行、且其结果列对应有效输出行：
    - 若 `Mmad` 的 **m 维 = `baseM`（满块，含 padding 行）**，padding 行的乘积会被累加进 L0C。虽然 `Mmad` 的 m 维每行结果各自独立（A 的第 m 行 × B → C 的第 m 行），但 padding 行未初始化数据可能通过以下路径扩散到有效行：(1) padding 行产生的极大/NaN 的 S 值经 softmax 生成异常 P，若后续 `Mmad` 的 m 维跨行累加、或 softmax state 按行合并时 padding 行的异常 state 被有效行读取；(2) padding 行的 L0C 残留被下一轮 `Mmad` 复用（`cmatrixInitVal=false`）累加进有效行；(3) `LoadData3D` 的 `l1W/stride` 按 `baseM` 跨越未初始化 padding 行时寻址泄漏。**只要 padding 行污染经任一路径扩散到有效行，就必须源头清零，输出侧 clamp 无法补救。**
    - 若实现能保证 padding 行污染**严格只停留在 padding 行**（m 维完全行独立、softmax 与输出累加严格按行隔离、且输出已 clamp 不读 padding 行），则可接受 —— 但这种"行隔离"前提在放大 baseM 后极易被打破，**必须用 Q 尾块精度回归验证，不能假设**。
  - **泛化修复要求（任选其一或组合，按"源头清零优先"）：**
    - **[推荐，源头清零]** Q 块加载步骤写完 `validRows` 行后，显式清零/初始化 L1 Q buffer 的 `[validRows, baseM)` padding 行（写入全 0，使 padding 行参与 `Mmad` 的乘积为 0，不污染任何有效行的累加）：
      ```text
      copy Q[0 : validRows] rows from GM -> L1 Q buffer   # 只搬有效行
      zero-fill L1 Q buffer[validRows : baseM, 0 : dim]   # 必须显式清零 padding 行
      # 现在 L0A 加载满 baseM 行，padding 行=0，乘积=0，L0C 不被污染
      ```
    - **[屏蔽加载]** 令 padding 行不进入 L0A：L0A 加载步骤只搬 `validRowsAlign = AlignUp(validRows, C0)` 行，但必须保证 L0A/L0C 的 m 维寻址与 NZ 布局仍与 `dstNzC0Stride=baseM` 一致（否则行错位）。此法改动 L0A 加载参数，易引入寻址 bug，**仅在无法源头清零时使用**。
    - **[输出侧屏蔽，有条件]** 若 padding 行污染**严格只到 padding 行且未扩散**（见上文判据），可在 softmax state 与输出写回侧严格按 `validRows` 行处理、屏蔽 padding 行影响。**注意：此法只在"污染未扩散到有效行"时可接受；一旦污染经 `Mmad` 扩散到有效行（最常见情况），输出侧 clamp 救不回来，必须回到源头清零。**
- **dim 尾块**：若 `dim % baseK != 0`，K 维最后一段必须单独处理（`kAligned = AlignUp(dim % baseK, C0)`），`cmatrixInitVal` 对第一段为真、对剩余段为假。

### 4.2 对齐

- `baseM`、`baseN` 必须是 `C0`（half/bf16=16）整数倍。
- 所有 `Mmad` 的 m/n/k、所有 `LoadData` 的 `repeatTimes`/`srcStride` 派生（`mActAlign/C0` 等）都要用新块重新计算；不能残留旧块常量。
- workspace slot 写回 stride（`dstStride`）由 `baseN`（S/P slot）或 `dimAlign`（O slot）决定，放大块后必须同步。

### 4.3 容量上限

- 放大后必须重算 §3.1 全部公式，任一超限即不可行；优先通过"单缓冲 L1（Q/KV/P 各一个 buffer）"而非"双缓冲"来留容量。
- vector 侧若 `baseM*baseN*F` 超 UB，不能直接放大；需先给 vector 加行切分（按 `vecChunkRows` 分批进 UB），但加行切分本身可能引入新的坐标系 bug，须作为本策略内的一步同步完成并测试。

### 4.4 host / kernel 派生量必须同步

这是本策略**最容易出错的红线**：块大小常量被 host 和 kernel 共享，放大后两者必须用**同一个新值**派生以下量，否则 host 分配的 workspace 与 kernel 期望不符：

| 量 | host 侧 | kernel 侧 | 放大后必须同值 |
|---|---|---|---|
| baseM/baseN | tiling.blockM/blockN 字段 | `constexpr` 块常量 + 所有 `MmadParams.m/.n`、`InitBuffer` 尺寸、循环步长 | 是 |
| qSeqLenAlign | `AlignUp(qSeqLen, baseM)` | `CeilDiv(qSeqLenAlign, baseM)` 算 seqBlocks | 是 |
| kvSeqLenAlign | `AlignUp(kvSeqLen, baseN)` | （若用于切分） | 是 |
| tailValid | `kvSeqLen % baseN` | 读 tiling.tailValid 决定尾块 | 是 |
| workspace per-core size | `RING*(baseM*baseN*F + baseM*baseN*E + baseM*dimAlign*F + baseM*3*F + baseM*dimAlign*F)` | kernel 用同公式设 GM buffer 上界 | 是 |
| queue slot size | `baseM*baseN`（S/P）、`baseM*dimAlign`（O） | queue Init 传入同值 | 是 |

**host 改了块常量但忘记重新编译 kernel（或 kernel 用了独立的旧常量）会导致 workspace 越界写、跨核 flag 错位、运行时设备执行超时。** 放大块后必须整体重新编译，不能增量替换。

### 4.5 不改的项（保持语义）

- 不改 scale、mask 语义、online softmax 合并公式、累加顺序、输出 dtype、输出布局、ND↔NZ 寻址契约。
- 不改跨核任务划分算法（仍按总块数线性切分）；总块数因 `baseM` 变化而变化，但核分配逻辑不变。
- 不删任何 `acquire/release`、跨核 flag、`PipeBarrier`、`SetFlag/WaitFlag`；同步保护范围不变。
- 不改 `RING`（workspace slot 数）与 prelaunch 深度；它们与块大小正交。

---

## 5. 实施步骤

应用者只看本文档 + 慢实现，按以下顺序操作。

### 5.1 定位所有"基本块"定义点

在慢实现中搜索被 baseM/baseN 参数化的**所有**位置（这是本策略工作量集中处）：

1. **块大小常量**：通常是 tiling 头文件里的 `constexpr`，既是 host 也被 kernel 包含。
2. **host 派生量**：`qSeqLenAlign`、`kvSeqLenAlign`、`tailValid`、`usedCoreNum`、所有 workspace size、tiling struct 的 blockM/blockN 字段。
3. **kernel 顶层循环**：`seqBlocks = CeilDiv(qSeqLenAlign, baseM)`、`kvLoops = CeilDiv(kvSeqLen, baseN)`、blockIdx 解码。
4. **kernel cube buffer**：L1 的 Q/KV/P buffer `InitBuffer` 尺寸、L0A/L0B/L0C 队列 `InitBuffer` 尺寸、所有 `MmadParams.m/.n`、`FixpipeParams.mSize/.nSize/.srcStride/.dstStride`、`LoadData` 的 `repeatTimes/srcStride`。
5. **kernel vector buffer**：UB input/output queue `InitBuffer` 尺寸、mask buffer（baseN）、brcb buffer（AlignUp(baseM, BRCB)）、softmax state 行数（baseM）、subBlockRows（baseM/subBlockNum）。
6. **workspace queue slot size**：S/P queue 传 `baseM*baseN`，O queue 传 `baseM*dimAlign`。
7. **Q 尾块 padding 行处理**（放大 baseM 后的高危点）：Q 块加载写 `validRows` 行后，是否清零/屏蔽 L1 Q buffer 的 `[validRows, baseM)` padding 行？把 Q 搬进 L0A 的加载步骤 m 维是否取满块 `baseM`（含 padding 行）？padding 行污染是否扩散到有效行（见 §4.1 判据）。

### 5.2 改块大小（baseMNK 三者同改）

按 §3 公式选定 `new_baseM`、`new_baseN`（建议相等）与 `new_baseK`（优先 `AlignUp(dim, C0)`），**三者一起**替换 §5.1 定位的块常量。

**强制自检（提交 diff 前必做，任一未勾选不得提交）：**

- [ ] `baseM` 对应的 kernel 常量（如 `BLOCK_M`）已改为新值
- [ ] `baseN` 对应的 kernel 常量（如 `BLOCK_N`）已改为新值
- [ ] `baseK` 对应的 kernel 常量（如 `BASE_K`）已改为新值（且 `new_baseK ≤ AlignUp(dim, C0)`，超过 `dim` 无收益）
- [ ] host 侧 `blockM`/`blockN`/tiling 字段同步更新
- [ ] `ASCENDC_DESIGN.md` 和 `CODE_MAP.md` 中所有涉及 `baseM`/`baseN`/`baseK`、UB 总字节、L0C 容量、workspace per-core size、totalBlocks 的公式/数字已按新块同步；旧公式/旧数字未更新不得提交

仅改 K 维（`baseK`/`BASE_K`）而 M/N 不变 = KP-031 的典型退化，本策略视为未完成。

### 5.3 同步 host 派生量

- `qSeqLenAlign = AlignUp(qSeqLen, new_baseM)`
- `kvSeqLenAlign = AlignUp(kvSeqLen, new_baseN)`
- `tailValid = kvSeqLen % new_baseN`（若整除则为 0）
- workspace per-core 与 total 用新块重算（公式见 §4.4 表）。
- tiling struct 的 `blockM/blockN` 字段写新值（host 写、kernel 读，二者一致）。
- **不改** q/kv stride、smScale、输出 shape。

### 5.4 同步 kernel buffer 与循环步长

- 所有 `InitBuffer` 尺寸按新块重算（L1/L0/UB）。
- 所有 `MmadParams.m = new_baseM`、`.n` 用 `kvRowsAlign` 或 `new_baseN`/`baseK`。
- 所有 `Fixpipe` 的 `srcStride = AlignUp(new_baseM, C0)`、`dstStride` 用 `new_baseN`（S/P）或 `dimAlign`（O）。
- 顶层 `seqBlocks`、`kvLoops` 用新块重算（循环次数自动下降）。
- vector 的 `subBlockRows = new_baseM / subBlockNum`、softmax `srcShape.srcM/srcK` 用新块。

### 5.5 编译并验证容量

- 整体重编译（host + kernel），确认无残留旧块常量。
- 若编译期 `InitBuffer` 超过硬件上限，构建会报错；回到 §3 公式缩小候选。
- 若 UB 超限，先尝试给 vector 加 `vecChunkRows` 行切分（不改变全局行坐标系），再验证。

### 5.6 校验并修复 Q 尾块 padding 污染（放大 baseM 后必须做）

放大 `baseM` 后 padding 行数从「旧块 − 1」增长到「新块 − 1」，Q 尾块 padding 行污染被放大。按以下顺序确认：

1. **定位 padding 行来源**：Q 尾块 `validRows = min(baseM, qSeqLen - rowBase)`。检查 Q 块加载逻辑：写 `validRows` 行后，L1 Q buffer 的 `[validRows, baseM)` 行是否被清零/屏蔽？（注意：host 侧把 Q 维 pad 到 `baseM` 倍数填 0 **不解决**此问题——kernel 侧 Q 块加载仍只搬 `validRows` 行，L1 padding 行仍是未初始化残留。）
2. **确认 padding 行是否进入 L0A**：检查把 Q 搬进 L0A 的加载步骤：m 维是否取满块 `baseM`（含 padding 行）、`srcStride` 是否按 `baseM` 寻址？若是，padding 行必进 L0A。
3. **按判据选修复**（见 §4.1）：
   - 若 padding 行污染会扩散到有效行（`Mmad` m 维含 padding 行、padding 行结果列对应有效输出行，或 softmax state 跨行合并）→ **源头清零**：Q 块加载写完 `validRows` 行后显式清零 `[validRows, baseM)` padding 行（写全 0），使 padding 行参与 `Mmad` 的乘积为 0。
   - 若能严格证明 padding 行污染只停留在 padding 行且输出已 clamp → 可暂用输出侧屏蔽，但**必须用 Q 尾块回归验证**。
4. **强制回归**：用一批 `qSeqLen < new_baseM` 的 Q 尾块 shape 测精度（含"略大于 `new_baseM` 整数倍但小于 `2*new_baseM`"的高危 shape），PASS 才算此步完成。

---

## 6. LLM 前置问题

应用者实施前必须能回答：

| 问题 | 必填内容 |
|---|---|
| 当前是否单级分块 | 加载块/matmul tile/softmax tile/输出块/外层步长是否同一个量？是否已有外层常驻块 + 内层 micro？（决定本策略是否适用） |
| **kernel 变量名映射** | **列出 kernel 中对应 `baseM`/`baseN`/`baseK` 的实际常量名（如 `BLOCK_M`/`BLOCK_N`/`BASE_K`），三者都必须定位到。任一项无法定位 → 不实施（避免退化为只改 K 维，见 KP-031）** |
| 硬件各级容量 | L0A/L0B/L0C/UB/L1 的字节上限（代入 §3.1 公式） |
| 当前块大小与 dtype | baseM/baseN、`C0`、`baseK`、elem/float 字节数 |
| 目标块选择 | 由 §3 公式推导出的 new_baseM/new_baseN，以及为何该值满足全部容量约束 |
| seq 整除性 | `kvSeqLen % new_baseN`、`qSeqLen % new_baseM`，尾块如何处理 |
| host/kernel 同步点 | 列出所有 baseM/baseN 参数化的量，确认 host 与 kernel 用同一新值 |
| 尾块路径 | KV 尾块（tailValid 屏蔽）、Q 尾块（padding 行污染判据 + 修复）、dim 尾块（K 维余段）是否都已正确实现 |
| Q 尾块 padding 清零 | Q 尾块 `validRows < baseM` 时，L1 Q buffer 的 `[validRows, baseM)` padding 行是否被显式清零/屏蔽？padding 行污染是否会经 `Mmad` 扩散到有效行（m 维是否含 padding 行、softmax state 是否按行隔离）？放大 baseM 后是否已用 Q 尾块 shape 回归验证？ |
| 设计文档同步 | `ASCENDC_DESIGN.md` 和 `CODE_MAP.md` 中所有容量/公式/数字是否已随新块同步更新？ |
| workspace | per-core 与 total 字节数（新块下重算），是否在 HBM 预算内 |

任一项无法回答，不实施本策略。

---

## 7. 验收标准

最小验证：

```bash
cmake --build <kernel-build-dir>           # 整体重编译，确认无容量越界
ASCENDC_SKIP_BUILD=1 bash <eval-script> <op> basic   # 精度
```

建议验证：

- **基准 shape**：序列长明显大于初始块行数（放大块前外层 KV 循环迭代数大）。
- **精度**：与放大前基线同精度阈值（如 REL ~1e-3，mismatch 0%）；数值结果应**逐位等价**或仅舍入差异，因为放大块不改任何计算公式。
- **性能**：相对较小基本块基线应有可观加速（接近整数倍量级）；若持平或倒退，用 profiling 检查：cube 利用率是否提升、KV tile 发射次数是否减半。若 cube 已饱和（放大前后利用率接近），说明本算子非容量受限，收益不会出现。
- **设计文档一致性**：diff 中所有块相关常量、派生量、容量数字在 `ASCENDC_DESIGN.md` 和 `CODE_MAP.md` 中一致；源码与文档不一致不得进入评估。
- **边界 shape**：
  - `kvSeqLen` 非 `new_baseN` 倍数（触发 KV 尾块）；
  - `qSeqLen` 非 `new_baseM` 倍数（触发 Q 尾块输出 clamp）；
  - `dim` 非 `baseK` 倍数（触发 K 维尾段）；
  - 小序列（`seq < new_base`，单块即尾块）；
  - 多 batch/head、不同 `groupNum`（确认总块数变化后核分配仍均衡）；
  - fp16 与 bf16 两种 dtype。
- **Q 尾块 padding 污染回归（必须通过，否则策略不算成功）**：放大 `baseM` 后 padding 行数从「旧块 − 1」增长到「新块 − 1」，污染被放大。**必须**对一批 `qSeqLen < new_baseM` 的 Q 尾块 shape 做精度回归（覆盖满块到尾块的全部过渡：含尾块的 `qSeqLen` 恰好略大于 `new_baseM` 的倍数、`qSeqLen` 恰为某倍数 + 余数、以及 `qSeqLen` 远小于 `new_baseM` 的单块即尾块）。**特别注意 `qSeqLen` 略大于 `new_baseM` 的整数倍但小于 `2*new_baseM` 这种"最后一块是 Q 尾块"的高危 shape**——它既有满块又有 Q 尾块，padding 污染最容易在此暴露。
- **KV 尾块回归（必须通过）**：同理对 `kvSeqLen < new_baseN` 的 KV 尾块 shape 回归（含 `kvSeqLen` 略大于 `new_baseN` 整数倍的过渡 shape），验证 `tailValid` 屏蔽仍正确。
- **仅测无尾块主 case（如 `qSeqLen`、`kvSeqLen` 均为 `new_base` 的整数倍）不充分**——它走满块路径，不触发 padding 清零/屏蔽逻辑，无法暴露放大 baseM 后的 Q 尾块/KV 尾块污染。策略验收**必须**包含 Q 尾块 + KV 尾块 shape，二者精度 PASS 才算成功。
- **重复运行**高风险 case（Q 尾块 + KV 尾块 + 多 head），排查是否有非确定性错误（通常是 host/kernel 块常量不同步、尾块坐标系错误，或 Q 尾块 padding 行未清零导致 `Mmad` 污染有效行）。

性能结论必须写清楚基线：

```text
本策略收益相对"较小基本块"基线；
后续若叠加多缓冲/两级分块策略，必须相对本策略放大后的结果评估增量，
不能回到较小基本块基线作为下一轮的增量基线。
```

回退条件：放大后 build 失败（容量超限）、精度失败且无法定位到单一尾块/对齐/host-kernel 不同步问题、或性能持平且 profiling 证明 cube 利用率未提升（说明非容量受限，本策略无效，应改用搬运复用类策略）。

## 检索卡（短卡）

动作：把单级分块 kernel 的 baseM/baseN/baseK 三者同步放大（baseK 覆盖整个 dim 使 kTiles=1），host 派生量同步调整。
适用：单级分块（加载块==matmul tile==外层步长同一量）；放大后 L1/L0/UB 有余量；新块为 C0 整数倍且尾块完备。
限制：禁只放大 baseK（KP-031）；host/kernel 派生量须同一新值否则越界；Q 尾块 padding 行须源头清零，clamp 救不回。
范围：单级分块的 attention-like 矩阵乘 kernel。
检索词：baseM、baseN、baseK、kTiles、Mmad、L0A、L0B、L0C、C0。
机会：baseM/baseN 偏小致 Mmad 填充率低、外层迭代多，launch/同步开销线性放大。
代价：不减 GM→L1 总字节只减次数；瓶颈纯在 GM 带宽且 cube 饱和时收益消失。
