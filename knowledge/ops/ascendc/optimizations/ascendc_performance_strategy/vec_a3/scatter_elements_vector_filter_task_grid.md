---
type: Optimization
title: 索引散写类算子的任务网格唯一归属分派 + 向量化 filter/GatherMask 压缩 + 精确事件同步
description: 将按输出字节或行区间分核，改为把外层块×内层 tile 摊平为 task 并作 grid-stride 分派。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-scatter-elements-vector-filter-task-grid.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：索引散写类算子的任务网格唯一归属分派 + 向量化 filter/GatherMask 压缩 + 精确事件同步

单一优化点（针对「按输出区间分片导致每核重复扫描全部索引源 + 标量逐元素过滤 + 全管线 barrier 串行」三连反模式）：把并行分派从「输出 buffer 区间分片、每核过滤全量 update 找落点」改为「(外层块 × 内层 tile) 任务网格 grid-stride 分派、每条 update 条目唯一归属一个 task」；把「标量读索引→算目标→比区间」的过滤链下放到 vector pipe（branch-free 向量修正 + Compare 生成 mask + GatherMask 稳定压缩 + offset 折叠乘加），标量管线只做压缩后的纯写回（8 路展开、load/op/store 三相分离）；同步从 `PipeBarrier<PIPE_ALL>` 换成精确 HardEvent 边并让下一批 MTE2 与本批标量应用重叠。三个子变换相互依赖（压缩依赖向量 filter、软件流水依赖压缩后缓冲生命周期、tiling 依赖任务网格），作为一个统一优化点交付。

## 1. 原理

索引散写类算子（scatter/gather/稀疏更新）的每条 update 是否命中某输出段是**数据相关**的，朴素实现有两种昂贵选择：
- **按输出区间分片**：每核拥有输出的一段，但必须**扫描全部 update** 判断落点——扫描工作量被核数放大 N 倍（40 核即 40 倍），而命中率通常 <25%，即 ≥75% 是纯过滤开销，再乘 N 倍重复。
- **按 update 分片**：每核写任意位置，多核写同一 cache line 不同字节触发 write-back 竞争（部分写入丢失）。

正确做法是第三种：**按 (外层块 o, 内层 tile) 二维任务网格分派**。索引散写的地址 = oTargetBase + idx*inner + i，其中 o（外层块）与 i（内层列）**静态确定**了 update 的归属 task，只有 idx（沿 scatter 轴的索引）是数据相关的。因此把轴段（axisSegmentRows）内的输出连同「落入该段的 update 子集」整体搬进 UB 局部处理：数据相关的轴内过滤交给 vector pipe——负索引 branch-free 修正（sign = min(max(idx,-1),0); idx += sign*(-axis)）、区间测试用 `rel == clamp(rel, 0, segRows-1)` 的 Compare(EQ)（int32 Compare 只支持 EQ 时的等价技巧）、GatherMask 把命中项压缩成稠密数组。标量管线随后只处理 `validCount` 个连续命中项：预折叠的 x 偏移（rel*localStride+col）与 update 偏移（row*stride+col）也由向量乘加完成，标量循环退化为「读偏移→写值」的 LSU 流水；8 路展开的 load/op/store 三相分离让数据相关的 UB gather 不被逐 lane 串行化。UB 内单写者天然规避多核 cache line 竞争。每批 MTE2 搬运与上一批标量应用用精确事件边（S_MTE2 / MTE2_V / V_S / S_MTE3 / MTE3_MTE2）重叠。

## 2. 性能问题模式

**代码形态**（读代码即可识别，无须 profiling）：
- kernel 按**输出的字节/行区间**切分到多核，循环内有「读 index → 计算 target 偏移 → 比较 target 是否落在本核区间」的标量过滤链，命中率低时绝大多数迭代空转。
- 每批搬运后 `PipeBarrier<PIPE_ALL>`，MTE2/V/S 三管线完全串行。
- tiling 参数是常量硬编码（如固定 128KB 子块、固定批 2048 元素），与 UB 容量/shape 无关。

**profiling 特征**：
- kernel 耗时与 update 总量 × 核数成正比（而非与 update 总量成正比）；大 shape case 比理论带宽时间慢 2~4 个数量级（本例 51s vs 28ms）。
- 耗时几乎 100% 在该 kernel 自身，vector pipe 占用接近 0（全部过滤在标量管线）。

**不适用**：
- update 规模极小（如 <数千条）且输出巨大的 1-D 场景：复杂 tiling + 双 pass 的固定开销（~60us）可能高于朴素实现（~35us），此形态保留朴素路径或按规模自适应分派。
- 索引与 update 无法按 (外层, 内层) 静态划分归属的算子（如全局随机重排）；无数据相关过滤的纯连续拷贝。

## 3. 正确性红线

- **稳定压缩保序**：GatherMask 压缩必须稳定（保源序），重复索引的「后写覆盖」（update 模式）与 reduce 的结合顺序才与参考实现的行主序迭代一致。
- **压缩后重索引去重探测**：reduce 模式下同一 8 路组内若出现重复目标偏移，load/op/store 三相分离会丢失组内累计（store 覆盖先前的 store）；必须先做组内重索引探针，检出重复退回逐 lane 串行路径。
- **pad lane 投毒**：DataCopyPad 会把对齐尾 lane 填成首元素值（看似合法索引），向量过滤前必须把这些 lane 预填 INT32_MIN（每段一次 + 每批 gap lane），否则假命中写出越界。
- **负索引语义**：branch-free 修正必须与参考实现一致（idx<0 → idx += axisSize）；int64 索引 GatherMask 不支持，先 Cast 到 int32（值域须保证 < 2^31）。
- **UB 内处理含初值**：reduce 语义要求输出初值（include_self）参与，任务段的输出必须先从 GM 搬入（含克隆初值）再 RMW，最后一次性搬出；段内每 target 只有一个写者核，段间无重叠。
- **低精度 opmath**：half/bf16 的 reduce 在 fp32 shadow buffer 上做（与宿主框架 opmath 累加一致），最后一次性 cast 回；逐元素低精度 cast 会因舍入顺序差 1~2 ulp。
- **事件边方向**：MTE3→MTE2（写回完成才能复用 UB）、S→V（标量投毒完成才能向量过滤）、V→S（压缩完成才能标量应用）；方向接反即竞态。

## 4. 泛化条件

- **适用**：一切「按索引散写/散读到输出」的 index-driven 算子（scatter 系 / gather 系 / 稀疏乘 / one-hot / embedding 更新），输出可按 (非索引轴) 静态划分任务、索引轴数据相关过滤的形态；多核重复扫描或标量过滤占主导的任何实现。
- **不适用**：见 §2「不适用」。

## 5. 实施步骤

1. 把输出按 (外层块 o × 内层 tile) 摊平成 task 序号，`for (task = blockIdx; task < totalTasks; task += blockNum)` grid-stride；每个 task 处理一个轴段（axisSegmentRows）× innerTile 列。
2. host 侧 tiling 求解器：按 UB 字节预算（含 x 段/索引/update/压缩 scratch/mask/row-col 伴随向量全部缓冲）二分求 axisSegmentRows（x 段占 ~70% 预算）与 updateBatchRows；可用「标量同步次数估计 >3x 改善才应用」精化。
3. kernel 内每 task：搬入 x 段 → 每批搬入 update/index →（i64 索引先 Cast i32）→ 投毒 pad lane → 向量 filter 链 + GatherMask 压缩（rel/row/col/update 四路同 mask）→ 压缩后标量应用（8 路展开三相分离 + reduce 去重探针）→ 段结束搬出。
4. 全管线 barrier 全部替换为方向精确的 HardEvent；`canOverlap` 条件（apply 不再读 raw staging）满足时下一批 MTE2 提前发射。
5. 全量精度对照（重复索引、负索引、非对齐 shape、各 dtype）+ 全量性能回归。

## 6. LLM 前置问题

- update 条目的归属是否可以按 (非索引轴) 静态划分？索引轴数据相关的部分交给哪段管线？
- 现实现是否存在「每核扫描全量 update」或「标量逐元素过滤」？命中率多少？
- reduce 模式的重复索引语义（include_self / 后写覆盖）如何在压缩+三相分离下保持？
- pad lane 投毒、i64→i32 Cast、fp32 shadow 各在哪个位置做？
- 超小 update 规模是否需要保留朴素路径（按规模自适应分派）？

## 7. 验收标准

- build + 精度全过（重复索引/负索引/非对齐 shape/各 dtype：GatherMask 稳定压缩保源序，update 后写覆盖与 reduce 结合顺序与参考行主序一致；reduce 重复目标偏移检出后回退逐 lane 串行；pad lane 投毒后无假命中；half/bf16 在 fp32 shadow 上累加后一次性 cast 回）。
- 性能验收：目标瓶颈场景（原实现耗时与 update 总量 × 核数成正比，大 shape 比理论带宽时间慢 2~4 个数量级，如 51s vs 28ms）延迟显著下降至带宽量级；耗时不再随核数放大，vector pipe 占用脱离接近 0 的状态。
- 超小 update 规模（<数千条且输出巨大，朴素 ~35us vs 本策略固定开销 ~60us）按规模自适应回退朴素路径，且无精度/性能退化。

## 检索卡（短卡）

动作：将按输出字节或行区间分核，改为把外层块×内层 tile 摊平为 task 并作 grid-stride 分派。
适用：输出可沿非索引轴静态划分任务。
限制：使用 GatherMask 压缩时必须稳定并保持源顺序。
范围：scatter、gather、稀疏乘、one-hot、embedding 更新。
检索词：索引散写、scatter、gather、稀疏更新、task 网格、grid-stride、GatherMask
机会：每核拥有一段输出，却重复扫描全部 update 判断落点。
