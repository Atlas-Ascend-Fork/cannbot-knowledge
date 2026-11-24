---
type: Optimization
title: 分裂-融合类逐元素算子的扁平跨核切分与 kernel 内非对齐半行读取
description: 将两半输入的搬运与逐元素融合置于 kernel 内，并按扁平空间跨核切分。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/flat-parallel-inkernel-split-read.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：分裂-融合类逐元素算子的扁平跨核切分与 kernel 内非对齐半行读取

单一优化点：对于"把一个连续输入沿某轴劈成两半、逐元素融合输出（如门控/激活乘）"的带宽型算子，把搬运与并行统一做到 kernel 内——按扁平 tile 序号跨核切分（消除单轴尺寸为 1 时的单核坍缩），并在 kernel 内对非对齐的半行做对齐取整读取（消除 host 侧预暂存拷贝兜底）。

## 1. 原理

这类算子本质是带宽型：读两份等长输入半区、写一份输出，计算极轻。性能由"用了几个核"与"是否多了一次整张 GM 往返拷贝"决定。

- **并行维度**：若把工作按"劈裂轴的外层行数"来分核，则当劈裂发生在最前轴时，外层行数为 1，所有 tile 落到单核。正确做法是把二维 tile 网格（行块 × 列块）摊平成一维 tile 序号，按序号区间分给各核——这样即使外层行数为 1，列块仍能把所有核喂满。
- **搬运兜底**：当每个半行的长度不是搬运对齐宽度的整数倍时，朴素实现常在 host 侧把两半各自 `连续化`（对非首轴劈裂，这等于一次整张 GM 拷贝），再跑一个简单的一维 kernel。正确做法是在 kernel 内对每个半行做"对齐取整读取"：按对齐宽度把每行读取长度向上取整，使每行在片上缓存里紧凑排列；多读出的尾部必须是同一输入分配内的可读空间（或宿主保证 32B 填充），计算后丢弃，回写时只写真实长度。行间源间隔（srcStride）必须从取整后读取长度的末尾起算。

两子变换耦合：非对齐半行若不进 kernel 内读取，则仍走 host 拷贝；而 kernel 内读取要真正吃饱多核，又依赖扁平跨核切分。故作为一个统一优化点交付。

## 2. 性能问题模式

命中本策略的 kernel 通常同时具备两个反模式（用代码阅读即可识别，无须 profiling）：

- **反模式 A（单轴并行坍缩）**：分核数 = min(可用核数, ceil(外层行数 / 每块行数))。当劈裂轴在最前、外层行数为 1 时，分核数退化到 1。现象：同一算子在该 shape 下比"形状相近但劈裂轴在末尾"的 case 慢数倍，且核利用率极低。
- **反模式 B（host 预暂存兜底）**：host 侧有形如 `if (半行长度对齐) 走 kernel 内跨步读; else 两半 = 输入.切片().连续化()` 的分支。对非首轴劈裂，`.连续化()` 触发整张 GM 拷贝。现象：半行非对齐的 case 比对齐 case 慢很多；首轴劈裂的 case 即便落入此分支也不慢（切片本就连续，`.连续化()` 是空操作）——这一"首轴不劣化、非首轴劣化"的非对称是关键判据。

## 3. 正确性红线

- **回写只写真实长度**：每行计算覆盖对齐取整后的长度（含尾部无效填充），但向输出 GM 回写时每行只写真实元素数；严禁按取整长度整块回写，否则会覆盖下一行输出。
- **行间源间隔从取整末尾起算**：跨步读取的行间间隔 = (行元素步幅 − 取整后列长) × sizeof(dtype)，而非 (行元素步襟 − 真实列长)。取整后列长必为对齐宽度的整数倍，保证每行源片段与片上目的布局都对齐。
- **片上缓冲按取整后列长开**：输入/输出队列与（低精度需要的）高精度镜像缓冲，都要按"每块行数 × 取整后列长"开，否则尾部 tile 越界。
- **尾块与尾行**：列尾块真实列长 < 取整列长时，只有在输入分配末尾仍有多读空间（宿主保证 32B 填充）时才可按取整读取；否则最后一个列块/最后一行必须用 DataCopyPad 按真实长度读取或回退逐行，禁止越过张量分配末尾。行尾块行数 < 每块行数时按真实行数。
- **极小半行（半行元素数 < 对齐宽度元素数）**：取整会越过本行边界，本策略不覆盖；此类 shape 应回退原兜底路径（在 host 侧判明并路由），不得强行走跨步取整。
- **dtype 精度**：低精度走"升精度计算再降回"路径时，取整读取对升精度缓冲同样按取整列长开；舍入模式与原实现保持一致。
- **输入连续性**：kernel 内跨步读要求输入在内存上连续（C 序）；非连续输入回退原兜底路径。

## 4. 泛化条件

适用：
- 逐元素/门控/激活类带宽型算子，输入为单个连续张量，沿某轴劈成两半后逐元素融合。
- host 侧存在"对齐走 kernel 内读、非对齐走 host 连续化兜底"的分支，且劈裂轴可任意（含最前轴）。
- 有可用核数 > 1 的 vector 核。

不适用：
- 半行元素数 < 对齐宽度元素数（极小末维，如末维仅 1–2 个元素的低精度 case）。
- 输入本身非连续且无法廉价连续化。
- cube/矩阵类算子（其瓶颈与切分模型不同）。
- 计算重度型算子（本策略针对带宽与并行，非计算）。

## 5. 实施步骤

1. **诊断**：阅读 host 侧派发与 kernel 切分。确认是否存在反模式 A（分核数绑死外层行数）与反模式 B（非对齐半行走 host 连续化）。用一组"同算子、劈裂轴分别为最前轴与末轴、半行分别对齐与非对齐"的 case 交叉验证（首轴非对齐应明显劣化，首轴对齐不劣化）。
2. **扁平跨核切分（修反模式 A）**：把二维 tile 网格摊平。计算 `列块数=ceil(半行长度/列块长)`、`行块数=ceil(外层行数/每块行数)`、`总 tile 数=行块数×列块数`；`分核数=min(可用核数, 总tile数)`；`每核 tile 数=ceil(总tile数/分核数)`。kernel 内每个核遍历自己的 tile 序号区间，由 `行块=序号/列块数, 列块=序号%列块数` 反算行起点与列起点，再走原有的"按 (行起点, 行数, 列起点, 列长) 取一片"的跨步读。本步只改分布，不改读机制，精度不变。
3. **kernel 内非对齐读取（修反模式 B）**：
   - host 侧放宽门控为"输入连续 且 半行元素数 ≥ 对齐宽度元素数"即走 kernel 内读；否则回退原兜底。
   - kernel 内对每片真实列长 `colsInTile` 取 `colsRounded = 向上取整到对齐宽度元素数`。读取参数：行数=该片行数，每行字节数=`colsRounded×sizeof(dtype)`（必对齐），行间源间隔（字节）=`(行元素步幅−colsRounded)×sizeof(dtype)`，目的行间间隔=0（紧凑）。计算覆盖`行数×colsRounded`个元素。
   - 回写：当真实列长已对齐 且 该片是单列块（colsInTile==半行长度）时，沿用原紧凑多行回写；否则逐行回写，每行只写真实列长字节到输出对应行位置。
4. **缓冲与边界**：按 `每块行数×colsRounded`（取每片取整列长的上界）开片上缓冲；低精度镜像缓冲同口径。处理列尾块（末 tile 用 DataCopyPad/逐行回退）、行尾块、空 tile（核的起始序号≥总 tile 数则直接返回）。
5. **逐案验证**：在覆盖"首轴/末轴 × 对齐/非对齐 × 各 dtype"的 case 集上验证精度全过，再测性能。

伪代码（泛化，无具体符号）：
```text
for each flat tile index owned by this core (a contiguous subrange of the global tile list):
    map the index to a row chunk and a column chunk, then to an absolute row start and a column start
    rows in this tile = min(rows per tile, remaining rows from the row start)
    real cols in this tile = min(cols per tile, remaining half row length from the column start)
    rounded cols = real cols rounded up to the alignment width
    strided read the first half and the second half, each as rows-in-this-tile rows of rounded-cols elements,
        with the inter-row source gap measured from the end of the rounded length
    elementwise fuse the two halves over rows-in-this-tile times rounded-cols (padded tail ignored)
    write back per row only the real cols elements to the matching output row positions
```

## 6. LLM 前置问题

在动手改前，确认：
- 目标算子的劈裂轴是否可任意（含最前轴）？host 侧是否存在"非对齐半行→连续化兜底"分支？
- 现有分核数是否绑定外层行数？是否存在外层行数为 1 的 case？
- 搬运对齐宽度元素数是多少（= 对齐字节数 / sizeof(dtype)）？是否存在半行元素数小于该值的极小末维 case？
- 低精度路径是否升精度计算？镜像缓冲是否按取整列长开？
- 回写是否保证每行只写真实长度、不覆盖下一行？

## 7. 验收标准

- 精度：在覆盖"首轴/末轴 × 对齐/非对齐 × 各 dtype"的 case 集上与参考实现逐元素误差不超阈（含尾块、特殊值）。
- 性能：非对齐半行 case 与首轴劈裂 case 的延迟向"对齐末轴 case"看齐；整体均值显著下降，超过计时噪声；单核坍缩 case 核利用率明显上升。
- 鲁棒性：极小末维（半行元素数 < 对齐宽度元素数）与非连续输入回退原路径，不崩溃、精度不退。

## 检索卡（短卡）

动作：将两半输入的搬运与逐元素融合置于 kernel 内，并按扁平空间跨核切分。
适用：单个连续输入沿某轴分成两半后逐元素融合的带宽型算子。
限制：计算可覆盖对齐后的 padding，但每行写回输出 GM 只写真实有效长度；多读不得越过输入分配末尾。
范围：读取两个等长输入半区并写一个输出的轻计算路径。
检索词：带宽型算子、扁平跨核切分、非对齐半行、host 连续化。
机会：分核数绑死外层行数，且非对齐半行经 host 连续化。
