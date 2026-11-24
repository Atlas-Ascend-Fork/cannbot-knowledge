---
type: Optimization
title: Softmax 行统计量标量归约改为向量化归约与广播
description: 将softmax行统计量的逐行标量归约改为向量化归约与广播。
tags:
- task.optimization
- topic.attention
- topic.implementation.synchronization
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/01-softmax-scalar-to-vector.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-23T06:46:32Z'
platforms:
- a3
---

# 性能优化策略：Softmax 行统计量标量归约改为向量化归约与广播

> **单一优化点：** 将 attention backward 中 Vec 阶段处理函数对 softmax_max/sum 分桶统计量的逐行标量 merge（`GetValue` 逐桶比较/累加）以及后续逐行标量广播操作（`Adds`/`Sub` 逐行调用），整体替换为 V pipe 向量化路径，消除大量 S pipe 操作和 S_V/V_S 同步开销。

本策略适用于 attention backward kernel 中，softmax stat 以 `[B, S, N, B_DIM]` 格式存储（末维 B_DIM 通常 4 或 8），Vec 阶段需要得到每行全局 max/sum 并将其广播到整行的场景。

> **输入格式分支（决定 Phase B 是否需要 merge）：** B_DIM 维的语义有两种，对应两条处理路径：
> - **路径 A — 分桶格式**：每行 B_DIM 个值**互不相同**（forward 按 head_dim 分 B_DIM 段统计的局部 max/sum），必须先 merge 多桶得到全局值，再广播。
> - **路径 B — 广播格式**：每行 B_DIM 个值**完全相同**（forward 已算出全局 max/sum 并复制 B_DIM 份），**无需 merge**，可直接复用 `statTile`（gmax 侧）/`gsumTile`（gsum 侧）作为广播源。
>
> 两种语义由 forward 阶段 stat 的产出方式决定，实施前必须确认（见第 6 节问题 8）。Phase A（对 dS 行内求和）与输入格式无关，两条路径下均需执行。
>
> **输入 buffer 约定**：`statTile` 指 gmax 侧输入统计量、`gsumTile` 指 gsum 侧输入统计量，形状均为 `[numRows, B_DIM]`；路径 A 下每行 B_DIM 个值为分桶局部值，路径 B 下为等值全局量。若 forward 把两侧统计量放在同一 UB tile 的不同段，则 `statTile`/`gsumTile` 分别是该 tile 的两个段视图，下文调用按各自视图替换。

---

## 1. 原理

### 问题：逐行标量路径

`Vec1Process` 类的 Vec 阶段处理中三个阶段均可能存在标量瓶颈：

```text
// Phase A：sfmg 行归约（BlockReduceSum + 标量累加）
for r in [0, numRows):
    BlockReduceSum(tmp, tileUb[r*C], C)      // V pipe，产生 B_DIM 个部分和
    V_S sync
    for i in 0..B_DIM: sfmg += GetValue(tmp[i])  // S pipe，B_DIM*2 次 GetValue/行
    S_V sync
    Adds(tileUb[r*rowStride], srcTile[r*rowStride], -sfmg, actualCols)  // 逐行向量

// Phase B：gmax/gsum merge（标量逐桶比较/累加）
for r in [0, numRows):
    gmax = GetValue(statTile[r*B_DIM])               // S pipe
    for bIdx in 1..B_DIM: if statTile[r*B_DIM+bIdx] > gmax: gmax = GetValue(...)
    for bIdx in 0..B_DIM: gsum += ...                // B_DIM 次 GetValue/行
    Muls/Adds/Exp/Muls(tileUb[r*actualCols], ..., actualCols)  // 逐行小粒度向量
```

每批 `numRows` 行共产生 O(numRows × B_DIM) 次 GetValue/SetValue，加上 O(numRows) 次 S_V/V_S 同步，scalar pipe 占比可过半。

### 解法：全 V pipe 向量化

所有标量路径统一替换为向量 API 组合：

```text
// Phase A：BlockReduceSum + WholeReduceSum + Brcb
// ⚠️ 前提：桶宽 = blockElement（FP32=8），即 B_DIM = C/8；且 C ≤ 64（mask 上限）。
//    BlockReduceSum 每 repeat 固定把 8 个 datablock 各自求和 → 固定出 8 个部分和，
//    故此单次形式仅在 B_DIM=8、C=64 时成立（repeatTime=numRows，每 repeat 恰好一行）。
BlockReduceSum(rowSumUb, tileUb, numRows, C, 1, 1, B_DIM)
// 参数对应 (dst, src, repeatTime=numRows, mask=C, dstRepStride=1, srcBlkStride=1, srcRepStride=B_DIM)
// 无 reducedNum 参数；mask=C 必须 ≤64，srcRepStride=B_DIM=C/8(datablock)

WholeReduceSum(sfmgUb, rowSumUb, B_DIM, numRows, 1, 1, 1)
// [numRows, B_DIM] → [numRows, 1] 每行全局 sum，7 个参数，无 ReduceOrder
// srcRepStride=1 隐含 B_DIM=8（1 datablock）；B_DIM≠8 时应为 B_DIM/8

Brcb(sfmgBcast, sfmgUb, (numRows+7)/8, {1, B_DIM})
// [numRows, 1] → [numRows, B_DIM] 广播，供 src1BlkStride=0 使用
// {1, B_DIM} = {dstBlkStride=1, dstRepStride=B_DIM(单位 datablock)}，仅 B_DIM=8 数值成立

// Phase B：WholeReduceMax + Brcb（gmax）
WholeReduceMax(gmaxUb, statTile, B_DIM, numRows, 1, 1, 1, ReduceOrder::ORDER_ONLY_VALUE)
// 8 个参数，最后必传 ORDER_ONLY_VALUE
Brcb(gmaxBcast, gmaxUb, (numRows+7)/8, {1, B_DIM})

// 批量行广播减：BinaryRepeatParams src1BlkStride=0
BinaryRepeatParams rp = {.src1BlkStride=0, .src0RepStride=alignedCols/8, .src1RepStride=1, ...}
Sub(pUb, pUb, gmaxBcast, min(actualCols,64), numRows, rp)   // 1 次调用处理全部行
```

**向量化成立的前提**：搬入时使用 `DataCopyPad rightPadding` 将每行补齐到 B_DIM 个 FP32（32B）对齐，使后续批量向量操作的行基址全部满足 V pipe 32B 对齐约束：

```cpp
DataCopyPad(tileUb, srcGm,
    {numRows, actualCols*sizeof(T), (rowLen - actualCols)*sizeof(T), 0, 0},
    {true, 0, (uint8_t)(alignedCols - actualCols), 0})
// alignedCols = (actualCols+B_DIM-1)/B_DIM*B_DIM，rightPadding 单位为元素数，FP32 最大 7
```

### 三个子手段的关系

| 子手段                                     | 目的                                                    | 是否必备                                                                                |
| ------------------------------------------ | ------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| BlockReduceSum + WholeReduceSum/Max + Brcb | 将桶 merge 归约从 S pipe 转为 V pipe                    | 必备：是消除标量 GetValue 的直接手段                                                    |
| DataCopyPad rightPadding                   | 使 UB 行基址满足 V pipe 32B 对齐                        | 必备：`actualCols % B_DIM != 0` 时不对齐会触发 vec error，向量化无法执行              |
| BinaryRepeatParams src1BlkStride=0         | 将逐行广播减从 O(numRows) 次小向量调用变为 1 次批量调用 | 必备：Brcb 展开的 B_DIM 等值 datablock 正是为此参数准备的，缺少则归约结果无法被批量消费 |

### Phase B 的两条路径（取决于输入 stat 格式）

Phase B 处理的是**输入统计量（gmax 侧 `statTile`、gsum 侧 `gsumTile`）**，是否需要 merge 取决于 stat 的 B_DIM 维语义：

- **路径 A（分桶输入）**：每行 B_DIM 个值**互不相同**，须先 `WholeReduceMax/Sum` 归约成全局值，再 `Brcb` 广播（即上文给出的 Phase B 解法）。
- **路径 B（广播输入）**：每行 B_DIM 个值**完全相同**（全局值已复制 B_DIM 份），已等价于 Brcb 的输出。此时 `WholeReduceMax` 对相同值归约是恒等、`Brcb` 又复原输入，整套 merge+broadcast 是冗余的——**可直接复用 `statTile` 作为 `src1BlkStride=0` 的广播源**，省去 `WholeReduceMax/Sum ×2` + `Brcb ×2` + `gmaxUb/gmaxBcast/gsumUb/gsumBcast` 四块 UB（具体调用见第 5 节步骤 5b）。

> 注意：Phase A 处理的是动态数据 `tileUb`（dS 行内求和），与输入格式无关，两条路径下均需执行。

---

## 2. 性能问题模式

寻找以下模式：

1. profiling 显示 `aiv_scalar_ratio > 50%`，对应代码中存在 `for r: GetValue(statTile[r*B_DIM+bIdx])` 形式的双层循环。
2. softmax stat 以分桶格式存储（末尾维度为 B_DIM，通常 4 或 8），backward 需要在 Vec 阶段 merge 多桶。
3. 逐行归约结果以标量形式传递给后续向量操作（`Adds(tileUb[r*rowStride], ..., -scalar_r, actualCols)`），每行一次 API 调用。
4. 测试中 `actualCols % B_DIM != 0` 的 shape 触发 vec error（行基址非 32B 对齐），`actualCols % B_DIM == 0` 的 shape 正常。

不应实施的情况：

- B_DIM = 1（无桶 merge，原始统计量即全局值）。
- `(alignedCols - actualCols) * sizeof(T) > 32`（rightPadding 超出 DataCopyPad 限制，需改变行步长设计）。
- merge 语义非简单 max 或 sum（WholeReduceMax/Sum 无法表达）。
- Phase A 用 `BlockReduceSum` 时 `B_DIM ≠ C/blockElement`（桶宽非 blockElement 对齐，如 C=128 但 B_DIM=8 即桶宽 16），该 API 无法直接表达桶求和，需换归约方案（如 `B_DIM=1` 直接 `WholeReduceSum([numRows,C]→[numRows,1])`）。

---

## 3. 正确性红线

**API 参数数量（最易踩坑）：**

- `WholeReduceMax`：**8 个参数**，末参 `ReduceOrder order` 有默认值 `ORDER_VALUE_INDEX`；**本场景需显式传 `ORDER_ONLY_VALUE`**（只返回最值，dst 仅需一半空间；否则会同时写 value+index）。
- `WholeReduceSum`：**7 个参数**，无 `ReduceOrder` 参数，禁止多传。

**WholeReduceMax/Sum 约束：**

- mask 上限：FP32 `mask∈[1,64]`、FP16/BF16 `mask∈[1,128]`，即 **`B_DIM ≤ 64`（FP32）**；超限非法。
- src 起始地址需 32B 对齐。dst 对齐按类型区分：`WholeReduceMax` dst 需 8B（float）/4B（half）；`WholeReduceSum` dst 需 4B（float）/2B（half）。
- `srcRepStride=1` 隐含 `B_DIM=8`（FP32，1 datablock）；`B_DIM≠8` 时须为 `B_DIM/8`。

**BlockReduceSum 约束：**

- 参数顺序 `(dst, src, repeatTime, mask, dstRepStride, srcBlkStride, srcRepStride)`，**无 `reducedNum` 参数**（策略代码中的 `B_DIM` 实为第 7 参 `srcRepStride`）。
- 每 repeat 固定输出 blockElement 个（FP32=8）部分和（每 datablock 8 float 求和成 1）；**mask 上限 64（FP32）**。
- 故适用前提：**桶宽 = blockElement（FP32=8），即 `B_DIM = C/8`**；`C>64` 须分段（见步骤 3 降级路径）。`B_DIM≠C/8` 时此 API 无法直接表达，需换归约。
- dst 起始地址需 32B 对齐（float）；`dstRepStride` 单位为 32B（1 repeat 归约后长度）。

**Brcb 约束：**

- src ≠ dst（**原地调用不被支持，行为未定义**）。
- src/dst 起始地址均需 32B 对齐。
- 每次迭代固定把 src 的 8 个元素广播到 8 个 datablock（64 float），广播粒度天然对应 **FP32 B_DIM=8**；**src 元素数须 ≥ 8×repeatTime**，即 sfmgUb/gmaxUb 容量 ≥ `(numRows+7)/8 × 8`。
- `repeatTime = (numRows + 7) / 8`，使用实际行数；`{1, B_DIM}` 中 `dstRepStride=B_DIM` 单位为 datablock，仅 `B_DIM=8` 时数值正确。
- 迁移前核对芯片支持度：Brcb 在 Atlas 200I/500 A2 推理产品、Atlas 训练系列产品**不支持**。

**rightPadding 约束（DataCopyPad）：**

- `blockLen` 单位为**字节**（须 `×sizeof(T)`），而 `leftPadding`/`rightPadding` 单位为**元素数**——二者混用是最易踩坑点。
- `leftPadding`、`rightPadding` 所占**字节数均 ≤ 32**（FP32 各最多 7 元素），非仅 right。
- padding 填 0；64 位 dtype 的 `paddingValue` 只能设 0。
- 若 padding 列参与后续 reduce 写回 GM，需用 mask 屏蔽。

**mask 与 alignedCols 区分：**

- 批量向量操作（Muls/Exp）的 `count = numRows * alignedCols`。
- `Sub`/`Adds` 中 mask 必须使用 `min(actualCols, 64)`（有效列），不得用 `alignedCols`（会将 padding 写入结果）。
- mask 上限 64（FP32）的根因：`BinaryRepeatParams.blockNumber` 固定为 8（1 repeat = 8 datablock = 64 float）。

**src1BlkStride=0 前置条件：**

- `sfmgBcast`/`gmaxBcast` 必须由 Brcb 展开（或路径 B 下输入 `statTile` 本身即为广播等值），保证 datablock 内 B_DIM 个元素等值；直接传未展开的标量 buffer 会读取未初始化元素。

---

## 4. 泛化条件

| 维度            | 检查项                                                                                                                                                                                      |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| B_DIM           | Brcb`{repStride=1, blockLen=B_DIM}`；B_DIM=8 对应 FP32；B_DIM != 8 时需调整 Brcb 参数                                                                                                     |
| actualCols      | `alignedCols = (actualCols+B_DIM-1)/B_DIM*B_DIM`（FP32）；`actualCols > 64` 时 Sub 需分两段（mask=64 + mask=actualCols-64）                                                             |
| alignedCols / 8 | 必须 ≤ 255（BinaryRepeatParams RepStride 上限）；`actualCols ≤ 128` 时恒满足                                                                                                            |
| numRows         | `repeatTimes = numRows ≤ 255`；需在目标算子的 tiling 策略中确认每批行数上限                                                                                                              |
| dtype           | 以上均针对 FP32（blockElement=8，32B=8 float）；FP16/BF16 需调整对齐单位（16 元素）和 Brcb blockLen                                                                                         |
| UB 容量         | rowSumUb ≥ numRows×B_DIM×sizeof(T)；gmaxUb ≥ numRows×sizeof(T)（32B 对齐）；gmaxBcast ≥ numRows×B_DIM×sizeof(T)（32B 对齐）；tile 从 actualCols 扩展到 alignedCols 的额外占用需核算 |

### 参数与 B_DIM 的换算公式（消除 B_DIM=8 硬编码）

上表与正文代码默认 FP32 + B_DIM=8，以下给出与 B_DIM / dtype 无关的换算，落地时据实代入：

| 参数 | FP32 B_DIM=8（代码示例值） | 通用公式 |
|---|---|---|
| `blockElement`（每 datablock 元素数） | 8 | 32B / sizeof(T)（FP16/BF16=16） |
| `WholeReduce` `srcRepStride` | 1 | `B_DIM / blockElement`（单位 datablock） |
| `WholeReduce` mask（= B_DIM） | 8 | ≤ 64（FP32）/ ≤128（FP16）；即 `B_DIM ≤ blockElement×8` |
| `Brcb` 适用性 | 可用 | 仅 `B_DIM = blockElement`（FP32=8）可用；否则须换广播方案 |
| `Brcb` `dstRepStride`（`{1, B_DIM}` 第 2 值） | 8 | 仅 `B_DIM=8` 数值成立（单位 datablock） |
| BlockReduceSum 桶宽前提 | C=8×B_DIM | 桶宽须 = blockElement，即 `B_DIM = C / blockElement` |

---

## 5. 实施步骤

1. **定位标量热点**：统计 Vec 阶段处理中三个阶段各有多少 GetValue/SetValue，记录总次数。
2. **数据搬入改 rightPadding**（先做，后续所有向量操作的前提）：

   - 计算 `alignedCols = (actualCols + B_DIM - 1) / B_DIM * B_DIM`。
   - 修改 `DataCopyPad` 的 `DataCopyPadExtParams` 第 3 个成员为 `alignedCols - actualCols`。
   - 将后续所有 `tileUb[r * actualCols]` 的行步长改为 `alignedCols`。
2.5 **判定输入 stat 格式（决定 Phase B 走路径 A 还是 B）**：

   - 检查 forward 产出 stat 的语义：每行 B_DIM 个值**互不相同**（分桶 → 路径 A）还是**完全相同**（广播 → 路径 B）。
   - 路径 A → 执行步骤 4/5 的 `WholeReduceMax/Sum + Brcb`。
   - 路径 B → 跳过步骤 4/5，改执行步骤 5b 的直接复用。
3. **Phase A sfmg 向量化**：

   **理想路径（单次批量调用，严格前提）**：

   - 前提：**桶宽 = blockElement（FP32=8），即 `B_DIM = C/8`**，且 **`C ≤ 64`**（mask 上限）。BlockReduceSum 每 repeat 固定输出 8 个部分和（每 datablock 8 float 求和成 1），故此单次形式仅在 `B_DIM=8、C=64` 时成立。
   - `BlockReduceSum(rowSumUb, tileUb, numRows, C, 1, 1, B_DIM)`：参数为 `(dst, src, repeatTime=numRows, mask=C, dstRepStride=1, srcBlkStride=1, srcRepStride=B_DIM)`；**无 `reducedNum` 参数**，`B_DIM` 实为第 7 参 `srcRepStride`（单位 datablock = C/8）。
     > ⚠️ 若 `C > 64` 或 `B_DIM ≠ C/8`，此单次形式**不成立**，必须改用降级路径或换归约方案。
   - `WholeReduceSum<T>(sfmgUb, rowSumUb, B_DIM, numRows, 1, 1, 1)` （7 参数）；`srcRepStride=1` 隐含 `B_DIM=8`（1 datablock），`B_DIM≠8` 时应改为 `B_DIM/8`。
   - `Brcb(sfmgBcast, sfmgUb, (numRows+7)/8, {1, B_DIM})` 展开为等值 datablock；`{1, B_DIM}` 仅 `B_DIM=8` 时 `dstRepStride` 数值正确。

   **安全降级路径（C > 64 时使用，纯 V-pipe，与理想路径等价）**：

   当 `C > 64`（理想路径 mask 超 64 上限）时，把每行 C 个元素拆成多段、每段长 ≤ 64 分别 `BlockReduceSum`，段输出连续拼接即得每行 `C/8` 个部分和。仍要求**桶宽 = blockElement（FP32=8）**，即 `B_DIM = C/8`。

   ```cpp
   // 段式 BlockReduceSum（C > 64 时用）：每行拆 NSEG 段，段长 SEG ≤ 64
   //   每段 1 个 repeat、mask=SEG，输出 SEG/8 个部分和（FP32）；拼接得 C/8 = B_DIM 个
   constexpr uint32_t SEG = 64;          // 段长，须 ≤ mask 上限 64
   const uint32_t NSEG = C / SEG;        // 段数（要求 C 为 SEG 的倍数，否则尾段单独处理）
   const uint32_t SEG_OUT = SEG / 8;     // 每段输出部分和数
   for (uint32_t r = 0; r < numRows; ++r) {
       for (uint32_t s = 0; s < NSEG; ++s) {
           // (dst, src, repeatTime=1, mask=SEG, dstRepStride=1, srcBlkStride=1, srcRepStride=SEG_OUT)
           BlockReduceSum(rowSumUb[r * (C/8) + s * SEG_OUT],
                          tileUb[r * C + s * SEG],
                          1, SEG, 1, 1, SEG_OUT);
       }
   }
   // 各段输出连续拼接即为 [numRows, C/8]；后续 WholeReduceSum/Brcb 输入为 [numRows, B_DIM=C/8]
   ```

   > ⚠️ 此路径仅在**桶宽 = 8（FP32）、`B_DIM = C/8`** 时与理想路径等价。若实际算子 `B_DIM ≠ C/8`（桶宽非 8 元素对齐，如 C=128 但 B_DIM=8 即桶宽 16），BlockReduceSum 无法直接表达"每 16 元素求和"，需改用其他归约（`B_DIM=1` 时可直接 `WholeReduceSum([numRows,C]→[numRows,1])`），不计为策略偏差。全程纯 V-pipe，满足主目标（消除 GetValue/SetValue）。
4. **Phase B gmax 向量化**（路径 A — 分桶输入，需 merge）：

   - `WholeReduceMax<T>(gmaxUb, statTile, B_DIM, numRows, 1, 1, 1, ReduceOrder::ORDER_ONLY_VALUE)` （8 参数）。
   - `Brcb(gmaxBcast, gmaxUb, (numRows+7)/8, {1, B_DIM})`。
5. **Phase B gsum 向量化**（路径 A — 分桶输入，需 merge；与 sfmg 路径相同，用对应的统计量 buffer 作为 src）：

   - `WholeReduceSum<T>(gsumUb, gsumTile, B_DIM, numRows, 1, 1, 1)` （7 参数）。
   - `Brcb(gsumBcast, gsumUb, (numRows+7)/8, {1, B_DIM})`；对 gsumBcast 做 `Maxs(..., 1e-37f)` + `Reciprocal` 后用于批量 RowMuls。
5b. **路径 B（广播输入）替代**：若步骤 2.5 判定为广播格式，则**跳过步骤 4 和 5 的 merge + Brcb**，直接复用输入 `statTile`/`gsumTile` 作为 `src1BlkStride=0` 的广播源：

   - gmax：`Sub(dstTile, dstTile, statTile, min(actualCols,64), numRows, {src1BlkStride=0, src0RepStride=alignedCols/8, src1RepStride=1, dstRepStride=alignedCols/8})`；`actualCols > 64` 时同样分两段。
   - gsum：先对 `gsumTile` 做 `Maxs(..,1e-37f)` + `Reciprocal` 求倒数（仍需 UB buffer 存倒数，但无需 WholeReduceSum+Brcb），再以同样 `src1BlkStride=0` 的 rp 做 `Muls(dstTile, dstTile, gsumTileRecip, min(actualCols,64), numRows, rp)`。
   - 省去 `WholeReduceMax/Sum ×2` + `Brcb ×2` + `gmaxUb/gmaxBcast/gsumUb/gsumBcast` 四块 UB。
   - 前提：`statTile`/`gsumTile` 每行 B_DIM 个等值、与 `dstTile` UB 区域不重叠、32B 对齐。
6. **批量行广播减替换逐行 Adds/Sub**：

   - 构造 `BinaryRepeatParams {src1BlkStride=0, src0RepStride=alignedCols/8, src1RepStride=1, dstRepStride=alignedCols/8}`。
   - `Sub(dstTile, dstTile, gmaxBcast, min(actualCols,64), numRows, rp)`；`actualCols > 64` 时加第二段 `Sub(dstTile[64], dstTile[64], gmaxBcast, actualCols-64, numRows, rp)`。
   - Phase A 中 dS - sfmg 的广播减同理处理。
7. **删除所有标量路径**：移除 `GetValue`/`SetValue` 调用及遗留的 `S_V`/`V_S` 同步 event。
8. **先验证基础用例**（整块 shape，`actualCols % B_DIM == 0`），再验证尾块 shape（`actualCols % B_DIM != 0`）。

---

## 6. LLM 前置问题

实施前必须回答：

1. 统计量最后一维桶数 B_DIM 是多少？Phase A 若用 `BlockReduceSum`，是否满足 `B_DIM = C/blockElement`（FP32 即 `B_DIM = C/8`，桶宽=blockElement）？每行有效桶数是否固定？
2. `actualCols` 是否可能不是 B_DIM 的倍数？`alignedCols - actualCols` 是否 ≤ B_DIM-1（即满足 rightPadding ≤ 32B 限制）？
3. `WholeReduceMax` 和 `WholeReduceSum` 参数数量是否已区分（8 vs 7）？
4. Brcb 的 src 和 dst 是否分配在不重叠的 UB 区域？`gmaxBcast`/`sfmgBcast` 是否 32B 对齐？
5. `Sub`/`Adds` 中 mask 是否使用 `actualCols`（而非 `alignedCols`）？`actualCols > 64` 时是否分两段？
6. 写回 GM 的 DataCopy 路径是否仍使用 `actualCols`（非 `alignedCols`）作为列数？
7. 删除标量路径后，是否还有遗留的 S_V/V_S 同步 event 未清理？
8. 输入 stat 的 B_DIM 个值是**互不相同的分桶局部值**（路径 A，需 merge），还是**完全相同的广播全局值**（路径 B，可直接复用 `statTile`）？此判定决定 Phase B 走哪条路径。

---

## 7. 验收标准

正确性：

- 全量精度测试通过，覆盖整块行（`numRows` 取最大分块值）和尾块行（numRows 取余数值）。
- **所有 `actualCols % B_DIM != 0` 的 shape 由失败转为通过**（验证 rightPadding 生效）。
- 多次重复运行无随机 NaN 或 mismatch。
- **Phase A 可接受实现声明**：若 `C>64` 而采用多段 `BlockReduceSum`（每段 mask≤64）拼接得到 `[numRows, B_DIM]` 部分和（纯 V-pipe，不含 GetValue/SetValue），属于等价可接受实现，不视为策略偏差。
- **路径 B（广播输入）验收**：若按步骤 2.5 判定走路径 B，需额外验证——输入 `statTile`/`gsumTile` 每行 B_DIM 个值确实等值（若误判会把分桶值当全局值，结果错误）；`statTile`/`gsumTile` 与 `dstTile` UB 区域不重叠且 32B 对齐；跳过 `WholeReduceMax`/`Brcb` 后数值结果与路径 A 完全一致。

性能：

- `aiv_scalar_ratio` 从 >50% 降至 <30%。
- AIV 总耗时和 task duration 显著下降。
- `aiv_mte2_ratio` 和 `aiv_vec_ratio` 对应上升（标量时间转为搬运/计算时间）。

## 检索卡（短卡）

动作：将softmax行统计量的逐行标量归约改为向量化归约与广播。
限制：先改搬入为rightPadding；WholeReduceMax为8参数API，末参ReduceOrder有默认值。
范围：attention backward的Vec1Process行统计路径。
检索词：softmax_max/sum、BlockReduceSum、GetValue、SetValue、Brcb。
机会：aiv_scalar_ratio超过50%，且存在逐行GetValue双层循环。
