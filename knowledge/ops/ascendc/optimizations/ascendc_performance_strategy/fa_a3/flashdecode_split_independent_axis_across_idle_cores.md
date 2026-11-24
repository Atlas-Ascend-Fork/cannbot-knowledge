---
type: Optimization
title: 把"无依赖维"拆到空闲核（FlashDecode 式免 reduce 并行）
description: baseTasks 小于核数时，将独立维拆为 fdSplitNum 份，使任务数乘以 fdSplitNum
tags:
- task.optimization
- topic.attention
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/FA-A3/06-flashdecode-split-independent-axis-across-idle-cores.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：把"无依赖维"拆到空闲核（FlashDecode 式免 reduce 并行）

> **单一优化点：** 当一个 kernel 的**基准 task 数 < 核数**（有空闲核），且存在一个**彼此独立、无数据依赖**的可拆维度（典型：GQA/MQA 的 group——多个 query head 共享同一组 KV，但各 head 的输出行互不依赖）时，把该独立维**拆到多核**：每核处理 `独立维/splitNum` 个元素（如 `group/splitNum` 个 head）。因为拆的是**独立维**（非归约维），**无需跨核 reduce**——这是它区别于"拆 s2/KV 归约维"（需 reduce）的关键。把空闲核转成有效并行，且 `splitNum=1` 时与基线逐字节等价（prefill 等非 decode 场景不受影响）。
>
> **算子无关性：** 本策略适用于**所有**"基准并行度不足、却存在独立可拆维"的 kernel：GQA/MQA decode 的 group/head 拆分、batch 不足时的输出通道拆分、解码器多 token 的 token 维、任意"一组输出由独立计算构成"的批 GEMM/GEMV。判据只有一个：**拆的维是否需要跨核归约**——不需要即可免费并行，需要则属另一策略（带 reduce 的 split）。

本策略只改"task 切分方式 + task key 解码"：在 host 把独立维拆进 task 数，在 kernel `CreateTask` 把 task key 反解为 `(独立维索引, 其余轴)`，cube/vec 复用既有 M 轴路径（只是 `mBase` 变小）。不改数学、scale、mask、累加顺序、输出 dtype/布局；**不新增任何跨核 reduce/同步**（拆的是独立维）。

---

## 1. 优化原理

### 1.1 性能问题模式（通用）

decode/小 batch 场景下，基准 task 数 `baseTasks = B·N_kv·sQ` 很小（decode 时 `sQ=1`、batch 与 KV head 均为小值，极端下 `baseTasks=1`），远小于核数 `coreNum`，**大量核空闲**。若此时把一个本可并行的独立维（如 GQA group）塞进单核的 M 轴一次算完，则并行度被浪费：

```text
for bz in B:                                  # baseTasks = B*N_kv*sQ 很小
  for kvHead in N_kv:
    for seqPos in sQ:                         # decode sQ=1
      # group（G 个 head）整个塞进单核 M 轴：M=group
      Q = load G heads ; K,V = load ; Mmad Q@K^T(M=G) ; softmax ; Mmad P@V(M=G)
# ⇒ baseTasks 个核忙，coreNum - baseTasks 个核空转
```

空闲核无法被利用，单 task 串行算完整 group，延迟由单核决定。

典型症状：profiling 显示核利用率低（`baseTasks << coreNum`），decode 延迟高且与 `coreNum` 无关（加核也不快）。这与"拆 s2/KV 归约维"不同——后者会增加 task 数但需跨核 reduce，代价高。

### 1.2 本策略利用的机制

| 机制 | 利用方式 |
|---|---|
| 空闲核并行 | `baseTasks < coreNum` 时，把独立维拆 `splitNum` 份，task 数 `×splitNum`，用满更多核 |
| **独立维免 reduce** | GQA group 内各 head 输出行**互不依赖**（共享 KV 但输出独立）⇒ 拆到多核**无需跨核归约**；区别于拆 s2/KV（归约维，需 reduce） |
| M 轴复用 | 拆后每核 `mBase = group/splitNum`，cube/vec 复用既有 M 轴路径（仅 M 变小），无新计算结构 |
| task key 编码 | `totalTasks = sQ·splitNum`，`curTask → (seqPos, groupSplitIdx)`，独立维索引进 task key |
| 整除免尾块 | `splitNum` 选 `group` 的最大因数（在界内）⇒ 每核 head 数相等，无尾块 |

核心改动——独立维从"单核 M 轴"改为"多核 task 拆分"：

```text
# 基线：group 整个进单核 M 轴
for task in baseTasks(=B*N_kv*sQ):
    M = group ; <cube+vec 算整个 group>          # coreNum-baseTasks 核空闲

# 改写后：group 拆 splitNum 份到多核
for task in baseTasks * splitNum:
    seqPos, groupSplitIdx = decode(task)
    qHeadBase = kvHead*group + groupSplitIdx*mBase
    M = mBase(=group/splitNum) ; <cube+vec 算 mBase 个 head>   # 无跨核 reduce
# splitNum=1 ⇒ mBase=group、totalTasks=sQ，与基线逐字节等价
```

---

## 2. 适用条件与泛化边界

必须**同时**满足：

| 条件 | 要求 |
|---|---|
| 并行度不足 | `baseTasks < coreNum`（有空闲核）；否则无空闲可拆 |
| 存在独立可拆维 | 存在一个**彼此独立、无数据依赖**的维（GQA group/head、输出通道、token 等）；其元素拆到不同核后**无需跨核归约** |
| 拆后单核工作量足够 | 每核 `mBase = dim/splitNum ≥ MIN_PER_CORE`（如 32，保证 cube `M≥C0` 量级、mmad 有效）；否则拆太碎致 M 欠载 |
| M 轴可承载拆后大小 | `mBase ≤ BLOCK_M`；拆后 Q/L0C 等 buffer 按新 `mBase` 仍放得下（通常更小，更宽松） |
| 寻址可反解 | task key 能唯一反解 `(独立维索引, 其余轴)`；输出写回偏移按独立维索引导出 |
| 基线稳定 | 修改前 build/精度/性能可重复 |

优先适用：

- decode / 小 batch（`baseTasks` 远小于 `coreNum`，空闲核多，收益大）。
- 独立维较大（接近 `coreNum/baseTasks`，可拆多份）。
- 拆后 `mBase` 仍 ≥ cube 有效阈值（不致 M 欠载）。

不适用或需先重构：

- **无可拆独立维**：所有维都是归约维或彼此依赖（如 MHA `group=1`、纯序列依赖）。此时要并行只能拆归约维（带 reduce，属另一策略）。
- `baseTasks ≥ coreNum`（核已用满）：无空闲可拆，`splitNum=1`。
- 拆后 `mBase < MIN_PER_CORE`（M 严重欠载，cube 浪费）：不拆或减少 `splitNum`。
- 拆的维**实际有数据依赖**（误判为独立）：拆后缺 reduce → 结果错误（陷阱 2）。

> **关键判据——拆的是否归约维：** 把 s2/KV（归约维）拆到多核，各核算部分和，**必须**跨核 reduce（FlashAttention 的 s2-split/FlashDecode-KV-split）。把 group/head（独立维）拆到多核，各核输出互不重叠，**免 reduce**。本策略专攻后者——"免 reduce 的免费并行"。

---

## 3. splitNum 的选择

### 3.1 选择函数

```text
splitNum = 1                                  # 默认不拆（逐字节等价基线）
if (sQ == 1                                    # decode（M=group 可拆；非 decode 拆会与 seq 维冲突）
    && baseTasks < coreNum                      # 有空闲核
    && dim >= MIN_PER_CORE * 2):                # 独立维足够大（每核至少 MIN_PER_CORE，且能拆≥2）
    maxByCore  = coreNum / max(1, baseTasks)    # 每个 base task 可摊到的核数上限
    maxByDim   = dim / MIN_PER_CORE             # 最多拆几份（每份 ≥ MIN_PER_CORE）
    want       = min(maxByCore, maxByDim)
    # 选 ≤ want 的、能整除 dim 的最大因数（免尾块）
    for s in want .. 2:
        if dim % s == 0: splitNum = s; break
mBase = dim / splitNum                        # 每核处理的独立维元素数
```

- **整除优先**：`splitNum` 取 `dim` 的因数 ⇒ 每核 `mBase` 相等，无尾块（陷阱 1）。
- **下限 `MIN_PER_CORE`**：保证拆后 cube `M` 仍在有效区间（如取 `C0` 量级或其 2 倍，mmad 不欠载）。
- **上限 `maxByCore`**：不超过空闲核能摊到的份数，避免过度拆分使单核工作量过小。

---

## 4. task 编码与寻址

### 4.1 task key 反解

把独立维拆分编进 task key，`CreateTask` 反解：

```text
# 编码（host）: totalTasks = sQ * splitNum
# 反解（kernel CreateTask）:
seqPos        = curTask / splitNum              # decode sQ=1 ⇒ 恒 0
groupSplitIdx = curTask - seqPos * splitNum     # 独立维（group）拆分索引
qHeadBase     = kvHead * group + groupSplitIdx * mBase   # 本 task 首 head
groupRows     = mBase                                     # M 维 = mBase 个 head
```

`splitNum=1` 时 `groupSplitIdx=0`、`mBase=group`、`qHeadBase=kvHead*group`，与基线一致。

### 4.2 输出写回寻址

行 `i` → `y[bz, seqPos, qHeadBase + i, :]`。各核写**互不重叠**的 head 区间（`groupSplitIdx` 不同 ⇒ `qHeadBase` 不同），故**无写冲突、无需归约**：

```text
core 0: qHeadBase = kvHead*group + 0*mBase      # head [0, mBase)
core 1: qHeadBase = kvHead*group + 1*mBase      # head [mBase, 2*mBase)
...                                              # 区间互不重叠 ⇒ 免 reduce
```

### 4.3 与既有 M 轴路径的关系

cube/vec **不改**：拆后 `M=mBase`（更小），既有 M 轴 tiling/Q 载入/softmax/写回路径天然兼容（只是处理更少行）。若既有实现已把该独立维折叠进 M 轴（如 GQA group 维打包进 cube M 轴的策略），拆分只是缩小 M、平移首元素偏移。

---

## 5. 实施步骤

### 5.1 修改位置（通用）

| 位置 | 修改 |
|---|---|
| Host tiling | 计算 `splitNum`（§3.1）；`mBase = dim/splitNum`；`totalTasks = sQ*splitNum`；新增 `splitNum` 字段传 kernel |
| Kernel `CreateTask` | 反解 `curTask → (seqPos, groupSplitIdx)`（§4.1）；`qHeadBase += groupSplitIdx*mBase`；`groupRows = mBase` |
| Kernel task 游标推进处 | `totalTasks = sQ*splitNum`（task 总数） |
| Cube / Vec | **不改**（复用 M 轴路径，M 变小） |
| 数学/scale/mask/累加顺序/输出/跨核同步 | **不改**；**不新增 reduce** |

### 5.2 通用 host 改写

```text
# 基线（独立维进单核 M）
mBaseSize = dim                                  # M = 整个独立维
totalTasks  = sQ                                   # task 数 = baseTasks

# 改写后（独立维拆多核）
splitNum = SelectFdSplit(sQ, baseTasks, coreNum, dim, MIN_PER_CORE)  # §3.1
mBaseSize  = dim / splitNum
totalTasks   = sQ * splitNum                     # task 数 ×splitNum
tiling.set_splitNum(splitNum)
```

### 5.3 通用 kernel 反解改写

```text
# 基线
seqPos = curTask; qHeadBase = kvHead*group; groupRows = group

# 改写后
splitNum   = tilingData_->splitNum
seqPos       = curTask / splitNum
groupSplitIdx= curTask - seqPos * splitNum
qHeadBase    = kvHead*group + groupSplitIdx*mBaseSize
groupRows    = mBaseSize
```

---

## 6. 正确性红线

### 6.1 整除与尾块

`splitNum` 必须整除 `dim`（§3.1 选因数）。若不整除，末核 `mBase` 与其它核不等，须显式处理尾核（`mBase = dim - groupSplitIdx*step`），否则 head 映射错位（陷阱 1）。优先整除以避免该分支。

### 6.2 拆的必须是独立维（免 reduce 的前提）

拆的维元素间**无数据依赖**：GQA group 各 head 输出独立（共享 KV 但不互相读输出）。若误拆有依赖的维（如某变体 head 间共享归约因子、或拆了归约维 s2/KV），各核算部分结果**必须**跨核 reduce——本策略**不提供** reduce，会得到错误结果（陷阱 2）。实施前必须证明"拆后各核输出互不依赖、写回区间互不重叠"。

### 6.3 head 映射一致性

`qHeadBase = kvHead*group + groupSplitIdx*mBase`，行 `i` → `kvHead*group + groupSplitIdx*mBase + i`，须与参考实现的 head 交错布局一致（`head = kvHead*group + groupId`）。`N_kv>1` 时不可漏 `kvHead*group`（陷阱 3）。

### 6.4 decode 门控（避免与 seq 维冲突）

门控 `sQ==1`（decode）。非 decode（prefill，`sQ>1`）时 `seqPos = curTask/splitNum` 会与序列维 task 编码冲突，且 prefill `baseTasks` 通常已 ≥ coreNum（无空闲核）——故仅 decode 启用，`splitNum=1` 时其它 case 逐字节等价、不受影响。

### 6.5 数值正确性

不改 scale、mask、累加顺序、输出 dtype/布局。`splitNum=1` 时逐位等价；`splitNum>1` 时各核算互不重叠的 head 区间，结果与单核算整个 group 在浮点容差内一致（无跨核累加，无归约顺序变化）。

---

## 7. 已知陷阱

### 陷阱 1：splitNum 不整除 dim，末核 head 映射错位

问题：`splitNum` 非 `dim` 因数，各核 `mBase` 不等却按统一 `mBase` 寻址。
症状：head 区间重叠或漏算，部分 head 重复/缺失，mismatch。
修复：`splitNum` 取 `dim` 因数（§3.1）；不能整除则显式尾核 `mBase = dim - groupSplitIdx*step`。

### 陷阱 2：误拆有依赖的维，缺跨核 reduce

问题：把实际有数据依赖的维（head 间共享状态，或归约维 s2/KV）当独立维拆，未加 reduce。
症状：各核部分结果未归约，输出错误（如 attention 拆 s2 后 rowmax/rowsum 未合并）。
修复：拆前证明维独立性（§6.2）；拆归约维须配套跨核 reduce（属另一策略，非本策略）。

### 陷阱 3：N_kv>1 时 head 映射漏 kvHead

问题：`qHeadBase = groupSplitIdx*mBase`（漏 `kvHead*group`）。
症状：`N_kv>1` 的 GQA case 全错；`N_kv=1` 巧合正确。
修复：`qHeadBase = kvHead*group + groupSplitIdx*mBase`（§6.3）。

### 陷阱 4：拆太碎致 M 欠载（拆了反而慢）

问题：`splitNum` 过大，`mBase < C0` 量级，cube M 被 pad，算力浪费抵消并行收益。
症状：decode 用核更多但整体耗时未降甚至上升；profiling 显示 `aic_mac` 利用率下降。
修复：`mBase ≥ MIN_PER_CORE`（§3.1）；`splitNum` 上限受 `maxByDim` 约束。

### 陷阱 5：误把"未提速"当策略失效

问题：拆分用满更多核，但整体耗时降幅有限（剩余 gap 是 per-tile 固定开销：每核 K/V 重载 + 跨核 flag + softmax 建状态，非并行度问题）。
诊断：看核利用率是否上升、单 task 工作量是否下降。利用率上升即并行生效；剩余 gap 需叠加削减 per-tile 固定开销的策略（如策略 02/03 的操作数复用、策略 05 的 tile 放大）。

---

## 8. LLM 实施前必须回答的问题

| 问题 | 必填内容 |
|---|---|
| 并行度 | `baseTasks = B*N_kv*sQ` vs `coreNum`？是否有空闲核 |
| 独立维 | 哪个维可拆？其元素是否**无数据依赖**（免 reduce）？给出独立性证明 |
| 归约维区分 | 目标维是独立维（免 reduce）还是归约维（需 reduce）？后者不属本策略 |
| 拆分参数 | `splitNum`（整除 dim）、`mBase`、`MIN_PER_CORE`、`maxByCore/maxByDim` |
| M 有效性 | 拆后 `mBase ≥ MIN_PER_CORE`？cube M 是否欠载（陷阱 4） |
| task 编码 | `curTask → (seqPos, groupSplitIdx)` 反解式；`splitNum=1` 是否逐字节等价 |
| 寻址 | `qHeadBase`/写回偏移含 `kvHead*group + groupSplitIdx*mBase`（陷阱 3） |
| 门控 | 是否仅 `sQ==1`(decode) 启用？非 decode 是否不受影响 |
| 基线可重复 | 修改前 build/精度/性能基线值 |

任一项无法回答，不实施本策略。

---

## 9. 禁止事项与回退条件

禁止：

- 拆有数据依赖的维却不加跨核 reduce（陷阱 2）。
- `splitNum` 不整除 `dim` 且无尾核处理（陷阱 1）。
- `N_kv>1` 时 head 映射漏 `kvHead*group`（陷阱 3）。
- 拆到 `mBase < MIN_PER_CORE`（M 欠载，陷阱 4）。
- 非 decode（`sQ>1`）启用拆分（与 seq 维 task 编码冲突）。
- 改变数学/scale/mask/累加顺序/输出 dtype，或新增跨核 reduce（本策略是免 reduce 的）。

回退或缩小策略的条件：

- `baseTasks ≥ coreNum`（无空闲核）→ `splitNum=1`，不拆。
- 独立维不可证独立 / 实为归约维 → 改用带 reduce 的 split 策略。
- 拆后 `mBase < MIN_PER_CORE`（M 欠载）→ 减小 `splitNum` 或不拆。
- 精度失败且定位到 陷阱 1/2/3 单一原因 → 修该原因后重试。

---

## 10. 验收标准

最小验证：

```bash
bash <build> --soc=<soc> --op=<op>            # 编译算子
bash <build> --soc=<soc> --op=<op> --wheel    # 编译 pta
source <set_env>
pytest <op>/test/test_<op>.py                 # 精度
pytest <op>/test/test_<op>_perf.py            # 性能（生成 profiling）
```

精度：与基线一致（沿用算子既有 `atol/rtol`）。**必须覆盖**：`splitNum>1`（拆分路径，如小 batch decode）、`splitNum=1`（逐字节等价回退，非 decode 场景）、`N_kv>1`（head 映射，陷阱 3）、不同 `coreNum`。

性能（**必须覆盖 decode 拆分与回退两类，且无劣化**）：

- decode（`splitNum>1`）：整体 `Task Duration` 下降，核利用率上升、单 task 工作量下降。
- 回退 case（`splitNum=1`）：不劣化（逐字节等价）。

性能结论必须写清基线、拆分维与归因：

```text
本策略收益相对"group 进单核 M 轴、空闲核空转"基线；判据是拆独立维用满空闲核、且免跨核 reduce。
剩余 gap 多为 per-tile 固定开销（每核 K/V 重载 + 跨核 flag + softmax 建状态），非并行度问题——
需叠加削减 per-tile 开销的策略（02/03/05），不能把"剩余 gap"误判为本策略失效（陷阱 5）。
splitNum=1 路径逐字节等价是硬指标（非 decode 场景不受影响）。
```

## 检索卡（短卡）

动作：baseTasks 小于核数时，将独立维拆为 fdSplitNum 份，使任务数乘以 fdSplitNum
适用：baseTasks 小于 coreNum，存在空闲核
限制：fdSplitNum 必须整除 dim
范围：decode／小 batch kernel 的任务切分
检索词：baseTasks、coreNum、fdSplitNum、dim、mBase
机会：基准任务数 B·N_kv·sQ 很小，核并行度不足
