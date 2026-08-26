---
type: Operator
title: "TopK A5 Direct Invoke 算子知识"
description: "说明 cann_bench::top_k、top_k_npu 与 launch_top_k_kernel 在 A5 上的接口语义、Launcher 参数生成、Route 选择、多 Kernel 启动图与逐节点实现。"
tags: [task.implementation, task.lookup, topic.data_movement, topic.memory, topic.precision, topic.programming_model]
status: stable
verified:
  - by: process:ops-knowledge-route-priority
    at: "2026-08-25T20:47:20Z"
  - by: process:ops-knowledge-direct53-ingest
    at: "2026-08-25T20:03:11Z"
sources:
  - resource: "https://gitcode.com/cann/ops-math/blob/c821871ee4bccb0c564a582d1b362072c356a88d/math/top_k_v2/README.md"
    role: header
  - resource: "https://gitcode.com/cann/ops-math/blob/c821871ee4bccb0c564a582d1b362072c356a88d/math/top_k_v2/op_kernel/arch35/top_k_v2.h"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-math/blob/c821871ee4bccb0c564a582d1b362072c356a88d/math/top_k_v2/op_host/arch35/top_k_v2_tiling_arch35.cpp"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-math/blob/c821871ee4bccb0c564a582d1b362072c356a88d/math/top_k_v2/op_kernel/top_k_v2_apt.cpp"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-math/blob/c821871ee4bccb0c564a582d1b362072c356a88d/math/top_k_v2/op_host/top_k_v2_def.cpp"
    role: implementation
created_at: "2026-08-24T19:33:22Z"
updated_at: "2026-08-25T20:47:20Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# TopK A5 Direct Invoke 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | `cann_bench::top_k`（Torch schema）→ `top_k_npu` → `launch_top_k_kernel`，入口类型为 Direct Invoke |
| 计算语义 | 沿归一化后的 `dim` 选择 `k` 个最大或最小值；交付接口固定返回有序值以及相对该轴的 `int64` 索引 |
| 输入输出 | 连续 ND；rank 1–8；输入 `int8/uint8/int32/int64/float16/float32/bfloat16`；`values` 同输入 dtype，`indices` 为 `int64`；输出轴长为 `k` |
| 执行类型 | AIV_VECTOR radix/merge/Sort，SIMT 小 `k`、转置、整型窄化，NDDMA/Gather/VCONV transpose；部分 Route 为多 Kernel；无可达 Cube/AIC 或 MIX_CV 节点。 |
| Kernel 路线 | 特征重要性从 P0 到 P11 依次为 R-006A/R-006B、R-001、R-003、R-002、R-011、R-008、R-010、R-007、R-009、R-004、R-005、R-012；Route ID 保持 Host selector 身份，不随阅读顺序改号。 |
| 核心资源 | GM、AIV UB/TQue/TBuf、SIMT 私有数组、16 MiB system workspace 前缀、radix 用户 workspace、512 B 对齐的转置/排序/窄化切片 |
| 来源闭包 | `direct_implementation_closed`：schema、Meta/NPU launcher、tiling、compact POD、全部可达 entry/body/helper、transpose 网络、workspace 边和构建接线均由交付源码闭合；官方固定版本只作相关 TopKV2/A5 映射 |
| 验证状态 | 已完成源码闭包检查；本次知识提取未执行编译、真机、数值或性能测试。 |

## 接口与语义

### 计算语义

令输入 shape 为 `(d0,…,dn-1)`，归一化轴 `a = dim < 0 ? dim+n : dim`，轴长 `L=da`。对每个其余坐标固定的逻辑行，返回集合中按 `largest` 指定方向排列的前 `k` 项：`largest=true` 为降序，`false` 为升序；`values[...,r,...]=x[...,indices[...,r,...],...]`，`0<=r<k`。浮点 SIMT 小 `k` 路线显式把 NaN 置于最大值方向的前端、最小值方向的后端；其余路线继承 AscendC `TopK/Sort` 的排序语义。

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| `x` | ND、连续、rank 1–8 | `int8/uint8/int32/int64/float16/float32/bfloat16` | `top_k_npu` 拒绝非连续输入；各维必须为正 |
| `k` | Host 标量 | `int64` | `1 <= k <= x.size(dim)`；不同于相关官方 TopKV2 的 Tensor `k` |
| `dim` | Host 标量 | `int64` | 支持负轴，归一化后必须在 `[0,rank)` |
| `largest` | Host 标量 | `bool` | 控制最大/最小模板实例；本接口总是有序输出 |
| `values` | 与 `x` 同 rank，轴 `dim` 改为 `k` | 与 `x` 相同 | launcher 预分配 |
| `indices` | 同 `values` | `int64` | 轴内相对索引 |

### 入口与版本

`TORCH_LIBRARY_FRAGMENT` 声明 `cann_bench::top_k`，Meta 与 `PrivateUse1` 分别绑定 `top_k_meta`、`top_k_npu`。`top_k_npu` 经 `OpCommand::RunOpApi("TopKDirect", call)` 直接进入 `launch_top_k_kernel`，不是 ACLNN，也不是官方 `TopKV2` 图接口。相关官方 9.1.0 映射在 `ascend950` 注册并含相同 arch35 radix/merge/非末轴实现族；交付源码抽取并改造了这些 body，同时增加 compact ABI、SIMT 路线、NDDMA transpose 组合和 int64 动态窄化，故这些改造只称“交付实现”。Frontmatter 将官方链接固定到任务指定 Commit；本地官方仓是未包含该对象的浅克隆，因此该 Commit 的 blob 身份未能在本地独立复核。

## Host/Launcher 执行流程

### 参数校验与前处理

`top_k_npu` 先建立 device guard，检查连续性，再调用 `top_k_meta` 校验 rank、轴、`k`、dtype并分配输出。`calc_top_k_tiling` 再拒绝空指针、非正维、无效轴/`k`、零 AIV 核或 `UB<=32768`；保留 32768 B 后得到 `usableUb`。`transposeOuter=∏i<dim di`、`transposeRows=d[dim]`、`transposeCols=∏i>dim di`。非末轴且轴长不超过 2048 时先尝试不转置融合实现，失败才进入 SIMT 转置；更长轴进入官方 NDDMA tiler。

### 参数、Workspace 与生命周期

`localMemorySize=usableUb` 同时作为 dynamic UB launch 参数和 Host 资源上限。workspace 以 `topkWorkspaceSize` 起步，先含 16 MiB system 前缀及 radix 用户区，再按 512 B 对齐追加：转置输入、转置 values、转置 indices；或排序 values/indices；或 int64 的 512 B range flag、int32 输入和 int32 values。`workspaceSize=AlignUp(finalOffset,512)`，由 `torch::empty(uint8)` 持有直到当前 stream 上全部 launch 完成。

### 启动图与失败传播

所有节点在同一 `stream` 按 launcher 调用顺序提交；交付代码未插入跨 stream event，因此 producer→consumer 可见性依赖同流顺序。Host tiling 或 transpose tiling 返回 `false` 时 `TORCH_CHECK` 阻止任何 launch；Device launch API 为 `void`，未提供逐节点返回码。

```text
top_k_npu
  -> calc_top_k_tiling
  -> [需要时] calc_transpose_tiling × 3
  -> launch_top_k_kernel
       -> R-001/R-002/R-003/R-006..R-009：单 Kernel
       -> R-004：非末轴 TopK -> SIMT strided sort
       -> R-005：非末轴 TopK -> [可选 2×transpose] -> AIV Sort -> [可选 2×reverse]
       -> R-010：flag init -> int64→int32 -> int32 TopK -> int64 fallback -> int32→int64
       -> R-011/R-012：forward transpose -> last-axis TopK -> value reverse -> index reverse
```

## Route 与参数设计

### 分核与资源计算

末轴小块从 15360 元素（int64 为 10240）起按 256 递减，要求 `TopKTmp + SingleBlockRuntimeSpace <= usableUb`。单核多 tile 仅在 `rows>=coreNum` 时尝试；优化多核要求 `k*ceil(axis/tile)<=tile`；否则使用通用多核 radix。非末轴融合在候选 `innerChunk` 中选 `peak<=usableUb` 且 active core 最大、再取 chunk 最大者。所有 SIMT kernel 以 `ceil(domain/blockDim)` 给每个 block 连续区间，线程按 `threadIdx.x` 加 `blockDim.x` 跨步。

### Route 特征与重要性

P0 为最高重要性，后续等级依次降低。该顺序只组织实现知识；`Host 顺序`字段独立保留源码中 tiling、覆盖、短路和 fallback 的真实控制流。

| 重要性 | Route | Route 特征 | 适用域与实现前提 | Host 顺序、短路与 fallback |
|---:|---|---|---|---|
| P0 | R-006A/R-006B 末轴 Single Block | 整轴与一批逻辑行驻 UB；R-006B 在 int32 TopK 后追加有序化 | 末轴；whole-axis UB 账成立；R-006A 非 int32，R-006B 为 int32 | H2a：small-merge 未命中或失败后进入 common tiler；C1 首先尝试 single-block，命中即短路 C2～C4。H3 对 int32 置 output 1 得 R-006B，否则 R-006A |
| P1 | R-001 小 `k` SIMT | 每线程私有候选表，直接读写原 ND 布局，无 AIV UB | 轴长≤2048；命中三组 small-k 谓词 | H4：基础 tiling 与 H3 output selector 完成后最终覆盖为 output 5；launcher L4 在 merge key 与 dormant output 3/4 之后短路，其余 Route 不再启动 |
| P2 | R-003 非末轴融合 | `[axis,innerChunk]` 搬入、UB 内换序并融合 TopK/Sort，SIMT 直接散写 | 非末轴、轴长≤2048；`CalcNonLastTiling` 成功；无需后处理 Sort | H2b：先尝试融合；成功保留 mode 8。H3 若不需 output Sort 即为 R-003；失败转 R-012 |
| P3 | R-002 小轴 MergeSort | FP16/BF16 专用 Merge/Concat 路线，BF16 中间升 FP32 | 末轴、轴长≤1024；BF16，或 FP16 且 `4k>=axis`；merge UB/tmp 成立 | H2a：先于 common tiler尝试；成功产生 key 13002/14002，launcher L1a/L1b 最先短路；失败清理局部状态后 fallback 到 C1～C4 |
| P4 | R-011 NDDMA 转置组合 | 三段 NDDMA/Gather/VCONV 布局变换包围 last-axis TopK | 非末轴、轴长>2048；last-axis tiling 与三套 transpose tiling 均成功 | H2c：直接置 transpose 1，再调用 common last-axis tiler；任一 tiling 失败则 Host 失败，无 Device fallback |
| P5 | R-008 末轴 Multi Core Optimized | 多核生成候选并归并，候选规模受 `k*tileCount<=tile` 约束 | common tiler 中 single-block、single-core 均未命中；优化 UB/workspace 成立 | C3：位于 C1 single-block、C2 single-core 之后，命中即短路 C4；失败继续 R-009 |
| P6 | R-010 int64 动态窄化 | 全域范围证明后走 int32 快路，越界时同流执行 int64 body | 非转置、末轴、mode 1、int64，且 H4 未覆盖为 R-001 | H6：在基础 Route、output selector、small-k 覆盖与公共 slice 规划之后追加 dynamic flag；Device 内 flag=0/非0互斥选择 int32/int64，int32 retile 失败仍回 int64 single-core body |
| P7 | R-007 末轴 Single Core | 一核一行、多 tile 流式 radix，行间并行 | common tiler；`rows>=coreNum` 且 single-core UB 账成立 | C2：C1 失败后尝试；命中短路 C3/C4。int64 子域随后可在 H6 叠加为 R-010 |
| P8 | R-009 末轴 Multi Core 通用 Radix | 通用长轴 histogram/cumsum/scatter 路线，跨核同步闭合 | C1～C3 均未命中；通用多核 UB 账成立 | C4：common tiler 的最终候选；失败则 tiling 返回 false，不再有 Device fallback |
| P9 | R-004 非末轴短步排序 | mode 8 TopK 后以 SIMT insertion sort 原地补全有序输出 | 非末轴 int32、`33<=k<=64`；融合 tiling 成功 | H2b 先得到 mode 8；H3 首先识别短步域并置 output 2；不满足则按 output 选择到 R-003/R-005 |
| P10 | R-005 非末轴 Radix Sort 补全 | mode 8 TopK 后追加 AIV Sort；`inner>1` 时前后转置值与索引 | 非末轴 int32、`k>64`；融合 tiling 与 Sort UB/tmp 成立 | H2b 得 mode 8 后，H3 在 R-004 谓词不成立时置 output 1；Sort 资源闭合失败则 Host 失败 |
| P11 | R-012 SIMT 转置兼容组合 | 三段无显式 UB 的 SIMT 布局变换包围 last-axis TopK | 非末轴、轴长≤2048；融合 tiling 失败而 last-axis tiling 成功 | H2b 的 fallback：清理融合状态、置 transpose 2、重走 C1～C4；last-axis tiling 仍失败则 Host 失败 |

### Host selector 顺序

| Host 顺序 | 判断/动作 | 短路与 fallback |
|---:|---|---|
| H0 | 校验 rank、轴、`k`、dtype、AIV 核与 UB，并计算 `outer/axis/inner` | 任一失败立即返回 false，不启动 Kernel |
| H1 | 按 `dim==last`、非末轴 `axis<=2048`、非末轴 `axis>2048` 三分支选择 tiling 子树 | 三个分支互斥，分别进入 H2a/H2b/H2c |
| H2a | 末轴先判 small-merge，再进入 common last-axis tiler | merge 成功保留 R-002；否则按 C1 R-006A/B→C2 R-007→C3 R-008→C4 R-009 逐级寻找首个成立者 |
| H2b | 非末轴且 axis≤2048，先调用 `CalcNonLastTiling` | 成功得到 mode 8；失败置 transpose 2 并以 `outer*inner` 重走 C1～C4，形成 R-012 |
| H2c | 非末轴且 axis>2048，置 transpose 1 | 以 `outer*inner` 重走 C1～C4，形成 R-011；随后还需三套 transpose tiling |
| H3 | 根据 dtype、mode 与 `k` 设置初始 output selector | mode 8 int32 分到 R-004/R-005；其余保持基础 Route |
| H4 | 检查 small-k 三组谓词 | 命中时把既有 output selector 覆盖为 5，形成 R-001 |
| H5 | 按 H4 后的 selector 查询 Sort tmp，并规划 radix、transpose 或 Sort slice | tmp/UB/offset 闭合失败返回 false；small-k 不再申请被覆盖的 Sort slice |
| H6 | 检查非转置末轴 int64 mode 1，追加 dynamic flag 与三个窄化 slice，最后把总空间向 512 B 对齐 | 命中形成 R-010；否则保留 R-007；此后 selector 不再改变 |
| L1a/L1b | launcher 依次检查 FP16 key 13002、BF16 key 14002 | 各自命中后启动 R-002 并立即 return；dtype/key 不同时继续 |
| L2 | 检查 output 3 | 当前 Host 不生产；若外部构造则启动 dormant full-axis body 并 return |
| L3 | 检查 output 4 | 当前 Host 不生产；若外部构造则启动 dormant int64 short-scan body 并 return |
| L4 | 检查 output 5 | 命中后启动 R-001 并 return；未命中继续布局分支 |
| L5 | 非转置路径先启动基础 TopK，再按 output 2/1 追加后处理 | output 2 为 R-004；output 1 为 R-005 或 R-006B；无 output 时为 R-003/R-006A/R-007/R-008/R-009，R-010 在基础 launcher 内部短路 |
| L6 | transpose 路径按 value 1/2 选择 forward，随后 TopK、可选 Sort 与两路 reverse | value 1 为 R-011，value 2 为 R-012；节点间无运行时换路 |

```text
validate -> compute outer/axis/inner
  if last axis:
    if small-merge predicate and merge tiling succeeds: R-002
    else single-block -> single-core -> multi-core optimized -> multi-core generic
  else if axis<=2048:
    fused non-last succeeds -> R-003/R-004/R-005
    else R-012
  else R-011
  set preliminary output selector
  if small-k predicate: override with R-001
  close Sort/transpose slices
  if non-transpose last-axis int64 single-core: overlay R-010
```

### 模板/实现执行矩阵

| 重要性 | Route | key/selector | dtype/shape/platform 完整命中条件 | 执行拓扑与 Kernel 节点 | 实际模板/body | 内存与同步特征 | tail/fallback |
|---:|---|---|---|---|---|---|---|
| P0 | R-006A | common/mode 0 | 整轴入 UB、非 i32 | 单 AIV radix | `RadixSortTopKSingleBlock` | 行批处理 queues + TopK tmp | batch/tail core |
| P0 | R-006B | common/mode 0/output 1 | 整轴入 UB、i32 | single-block TopK→AIV Sort | `RadixSortTopKSingleBlock`→`sort_top_k_rows_kernel<int32_t>` | TopK UB后复用设备，Sort有独立四队列+tmp | batch/tail core与Sort pad |
| P1 | R-001 | output 5 | 上表小 `k` 谓词，A5 | 单 SIMT | `small_k_top_k_kernel`→`SmallKRowsSimt<T,order,MAX_K,THREADS>` | 每线程私有 `bestValues/bestIndices`，无 workspace | block/线程双层尾保护 |
| P2 | R-003 | mode 8 | 非末轴≤2048，除 R-004/5 | 单 Hybrid AIV+SIMT store | `TopKNonLastSmallAxisNonTranspose` | UB 内 gather/transpose；V→S event 后 SIMT store | `curInnerChunk` |
| P3 | R-002 | 13002/14002 | FP16/BF16 小轴 | 单 AIV | `top_k_merge_direct_kernel`→`MergeSort::ProcessSort` | 双/单 buffer、Concat/Sort 临时区 | 行尾与 core 尾 |
| P4 | R-011 | needsTranspose 1 | 非末轴>2048 | NDDMA/Gather/VCONV→AIV TopK→两次 reverse | `launch_transpose_kernel` router | 三个 512 B 对齐 GM slices | transpose tiler tail |
| P5 | R-008 | common/mode 4 | `k*tileCount<=tile` | 单 AIV radix | `RadixSortTopKMultiCoreOptimization` | value/index candidate workspace；跨核同步 | tile/core tail |
| P6 | R-010 | dynamic flag | int64 mode 1 | 五节点 SIMT+AIV | cast kernels + int32/官方 v9.0.1 single-core body | range flag 原子 OR；同流 gating | 越界时 int64 fallback |
| P7 | R-007 | common/mode 1 | 行并行、多 tile | 单 AIV radix | `RadixSortTopKSingleCore` | tile histogram workspace | tile tail |
| P8 | R-009 | common/mode 2 | 通用长轴 | 单 AIV radix | `RadixSortTopK` | histogram、tile-topk 双区；`SyncAll` | pass/tile/core tail |
| P9 | R-004 | mode 8/output 2 | i32，33≤k≤64 | R-003→SIMT insertion sort | `SortShortStridedRowsSimt` | 原地 values/indices，同流 | 每逻辑行独立 |
| P10 | R-005 | mode 8/output 1 | i32，k>64 | R-003→AIV Sort，inner>1 时前后转置 | `sort_top_k_rows_kernel<int32_t>` | 4 队列+Sort TBuf；可有 sort workspace | 对齐 pad 不写出 |
| P11 | R-012 | needsTranspose 2 | 融合失败 | SIMT transpose→AIV TopK→两次 SIMT reverse | `transpose_axis_topk_kernel` | 同 R-011，转置无 UB | linear tail |

### 隐藏性能 Guard

| Guard | Host/Tiling 条件 | Device/资源原因 | 影响 Route | 不满足时去向 | 源码符号 |
|---|---|---|---|---|---|
| UB 保留 | `ubSize>32768` | SIMT/VF 和 AIV launch 共享资源余量 | 全部 | 失败 | `calc_top_k_tiling` |
| small merge | axis≤1024、dtype f16/bf16、tmp<usableUb | merge Sort/Concat UB | R-002 | common radix | `CalcSmallMergeTiling` |
| 非末轴融合 | axis≤2048、候选 peak≤usableUb | 全 tile、转置、值/索引/tmp 同驻 UB | R-003~5 | R-012 | `CalcNonLastTiling` |
| single-block | `TopKTmp+SingleBlockRuntimeSpace<=usableUb` | 整轴/批行驻 UB | R-006 | R-007 | `CalcLastAxisTiling` |
| optimized | `k*ceil(axis/tile)<=tile` | 候选归并不超过 tile | R-008 | R-009 | `CalcLastAxisTiling` |
| output Sort | dtype 4 B 且特定 mode；Sort UB≤usableUb | 修复需全局有序的输出 | R-004/5 | 失败或直出 | `outputSortRequired` |
| compact ABI | `sizeof(TopKDirectTiling)=64`、merge=56 | 避免大 POD 进入 scalar launch | R-002~10 | 编译期失败 | `static_assert` |
| batch scheduling | `schemMode=1` | 通用多核 radix 内含 `SyncAll` | R-008/9 | 无运行 fallback | `rtKernelLaunchWithFlagV2` |

### POD/ABI

`TopKLaunchParams` 是 Host launcher 结构，不直接作为 Device POD；其逐字段如下。ABI offset 由标准布局与 `alignas(8)` 决定，交付源码未固化各 offset，故此处不猜测。

| 结构 | 字段 | 类型/位宽 | ABI 布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| `TopKLaunchParams` | `tiling` | `TopKV2TilingDataSimd` | 首字段，内部 248 B | 混合 | tiling helpers | pack helpers | Host-only 完整 POD |
| 同上 | `blockDim` | u32 | offset 未固化 | block | route helper | TopK launch | >0 |
| 同上 | `transposeBlockDim` | u32 | offset 未固化 | block | coreNum | transpose/sort launch | >0 |
| 同上 | `localMemorySize` | u32 | offset 未固化 | byte | `ubSize-32768` | dynamic UB/AIV launch | 窄化至 u32 |
| 同上 | `tilingKey` | u64 | offset 未固化 | key | tiler | launch router | common/13002/14002 |
| 同上 | `workspaceSize` | u64 | offset 未固化 | byte | final aligned offset | Torch allocation | 512 B 对齐 |
| 同上 | `topkWorkspaceSize` | u64 | offset 未固化 | byte | route tiler | slice base | 含 16 MiB 前缀 |
| 同上 | `transposeInputOffset` | u64 | offset 未固化 | byte | workspace planner | forward transpose/TopK | transpose route active |
| 同上 | `transposeValueOffset` | u64 | offset 未固化 | byte | workspace planner | TopK/reverse | transpose route active |
| 同上 | `transposeIndexOffset` | u64 | offset 未固化 | byte | workspace planner | TopK/reverse | transpose route active |
| 同上 | `sortValueOffset` | u64 | offset 未固化 | byte | workspace planner | sort transpose graph | R-005、inner>1 |
| 同上 | `sortIndexOffset` | u64 | offset 未固化 | byte | workspace planner | sort transpose graph | R-005、inner>1 |
| 同上 | `int32FastInputOffset` | u64 | offset 未固化 | byte | workspace planner | cast/TopK | R-010 |
| 同上 | `int32FastValueOffset` | u64 | offset 未固化 | byte | workspace planner | TopK/cast output | R-010 |
| 同上 | `int32FastElementCount` | u64 | offset 未固化 | element | outer×axis | cast input | R-010 |
| 同上 | `int32RangeFlagOffset` | u64 | offset 未固化 | byte | workspace planner | range kernels/gating | R-010，512 B slice |
| 同上 | `transposeRows` | u64 | offset 未固化 | element | axis length | transpose/SIMT | >0 |
| 同上 | `transposeCols` | u64 | offset 未固化 | element | inner product | transpose/sort | >0 |
| 同上 | `transposeOuter` | u64 | offset 未固化 | row group | outer product | all row kernels | >0 |
| 同上 | `k` | u64 | offset 未固化 | element | input k | all bodies | 1..axis |
| 同上 | `sortTmpSize` | u32 | offset 未固化 | byte | Sort tmp query | AIV Sort | output radix active |
| 同上 | `needsTranspose` | u32 | offset 未固化 | enum | selector | launch graph | 0/1/2 |
| 同上 | `needsOutputSort` | u32 | offset 未固化 | enum | selector | launch graph | 0/1/2/5；3/4 不可达 |
| 同上 | `useInt64DynamicInt32` | u32 | offset 未固化 | bool | planner | official TopK router | 0/1 |
| 同上 | `transposeForward` | `TransposeLaunchParams` | 2080 B | POD | official transpose tiler | forward router | R-011 |
| 同上 | `transposeValueReverse` | 同上 | 2080 B | POD | official transpose tiler | reverse values | R-011 |
| 同上 | `transposeIndexReverse` | 同上 | 2080 B | POD | official transpose tiler | reverse indices | R-011 |
| `TopKDirectTiling` | `data[0]` | u32 | offset 0，结构 64 B | mode | `PackDirectTiling` | `top_k_direct_kernel` | mode 0/1/2/4/8 |
| 同上 | `data[1]` | u32 | offset 4 | bool | `isLargest` | template router | 0/1 |
| 同上 | `data[2..15]` | u32×14 | offsets 8..60 | 字段依 mode | `PackDirectTiling` | 重建 `TopKV2TilingDataSimd` | mode 8 与末轴布局互斥 |
| `TopKMergeDirectTiling` | `sortLoopTimes` | u64 | 结构 56 B | loop | pack | merge body | >0 |
| 同上 | `unsortedDimNum` | u64 | 顺序布局 | row | pack | merge body | >0 |
| 同上 | `oneCoreRowNum` | u64 | 顺序布局 | row/core | pack | merge body | >0 |
| 同上 | `outputLastDimValue` | i64 | 顺序布局 | element | pack | copy out | `k` |
| 同上 | `unsortedDimParallel` | u32 | 顺序布局 | core | pack | merge body | >0 |
| 同上 | `numTileDataSize` | u32 | 顺序布局 | element | pack | queues | aligned axis |
| 同上 | `mergSortAcApiNeedBufferSize` | u32 | 顺序布局 | byte | tmp query | Concat/Sort buffer | <usableUb |
| 同上 | `keyParams4` | u32 | 顺序布局 | buffer count | pack | merge Init | 1/2 |
| 同上 | `isLargest` | i32 | 顺序布局 | bool | pack | template router | 0/1 |
| 同上 | `reserved` | u32 | 末字段 | N/A | zero-init | 不读取 | 必须保持 0 |

### Route 源码闭包

| 重要性 | Route | Key/selector | Host/Tiling producer | POD/参数 | Kernel entry/router 节点 | Kernel body/直接依赖 | 构建接线 |
|---:|---|---|---|---|---|---|---|
| P0 | R-006A/B | common key/mode/output enum | `CalcLastAxisTiling` 与 output-sort selector | direct POD | `top_k_direct_kernel`，R-006B 追加 Sort entry | single-block radix body及可达 post-Sort | `register_direct_launch_op` |
| P1 | R-001 | output 5 | `calc_top_k_tiling` | launch params | `small_k_top_k_kernel` | `SmallKRowsSimt` | 同上 |
| P2 | R-003 | mode 8/output 0 | `CalcNonLastTiling` | direct POD | `top_k_direct_kernel` | non-last body | 同上 |
| P3 | R-002 | 13002/14002 | `CalcSmallMergeTiling` | merge compact POD | `top_k_merge_direct_kernel` | `generateMergeTopKObject`/`MergeSort` | 同上 |
| P4 | R-011 | transpose 1 | TopK tiler + transpose tiler | three transpose POD | transpose router + TopK | NDDMA/Gather/VCONV + radix | 同上 |
| P5 | R-008 | common key/mode 4 | `CalcLastAxisTiling` | direct POD | `top_k_direct_kernel` | optimized multi-core radix body | 同上 |
| P6 | R-010 | dynamic flag | planner + runtime retile | direct POD/range flag | five launch nodes | cast SIMT + v9.0.1/int32 radix | 同上 |
| P7 | R-007 | common key/mode 1 | `CalcLastAxisTiling` | direct POD | `top_k_direct_kernel` | single-core radix body | 同上 |
| P8 | R-009 | common key/mode 2 | `CalcLastAxisTiling` | direct POD | `top_k_direct_kernel` | generic multi-core radix body | 同上 |
| P9 | R-004 | mode 8/output 2 | `CalcNonLastTiling` 与 output-sort selector | direct POD | `top_k_direct_kernel` + short-sort node | non-last body + SIMT Sort | 同上 |
| P10 | R-005 | mode 8/output 1 | `CalcNonLastTiling` 与 output-sort selector | direct POD | `top_k_direct_kernel` + transpose/Sort nodes | non-last body + AIV Sort | 同上 |
| P11 | R-012 | transpose 2 | TopK tiler | scalar dims | three SIMT transpose + TopK | AxisToLast/LastToAxis | 同上 |

## Kernel 实现

### 公共执行流程

common key 按 dtype 映射为 `1001/2001/1003/1004/3002/3003/4002`；`generateOpObject` 再严格按 mode 8、single-block、single-core、mode 4、通用多核分派。`isLargest` 是模板布尔量，`isSort=1`。交付 entry 使用 64 B/56 B compact POD 重建官方 248 B tiling 视图；workspace 传入 entry 前已去掉 16 MiB system 前缀，只有 int64 v9.0.1 路线同时保留 system 基址与 user 基址。

### Route R-006A/R-006B（P0）：末轴 Single Block Radix

#### 适用条件
##### 选择证据
| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Tiling | `op_kernel/top_k_kernel.cpp` | `CalcLastAxisTiling` | whole-axis UB 成立 | mode0/lastDimNeedCore=1 |
| Selector | 同上 | `outputSortRequired` | dtype=i32 | R-006B 追加 `sort_top_k_rows_kernel`；否则 R-006A |
#### Device 数据流
##### 函数级调用链
```text
R-006A: top_k_direct_kernel -> generateOpObject -> RadixSortTopKSingleBlock::Init -> Process
R-006B: 上述节点 -> same-stream sort_top_k_rows_kernel<int32_t>
```
##### 源码等价伪码
```text
每核按batch装入完整axis；TopK RADIX_SELECT；输出k值和int64索引；处理tail batch/core。
R-006B 再按 row 把 k 项搬入四个 depth-1 队列，以 `RADIX_SORT` 有序化后只写回有效 k 项。
```
#### 内存与数据搬运
##### 资源与搬运表
| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| input/value/index queues | row batch | batch*aligned(axis/k)*dtype bytes | T/i64 | DMA/API | API/DMA | TPipe | depth 1 |
| API tmp | UB | aligned queried max tmp | bytes | TopK | TopK | TPipe | route guard |
| R-006B Sort queues/tmp | UB | `2*Align(k*4)+2*Align(k*8)+Align(sortTmpSize)` | i32/i64/bytes | first node/Sort | Sort/copyout | second kernel TPipe | 两节点不同时占 UB |
##### 分层内存布局
```mermaid
block-beta
  columns 4
  inQ["input · batch*Align(axis)*sizeof(T)"]:1
  val["values · batch*Align(k*sizeof(T))"]:1
  idx["indices/i32 temp · batch outputs"]:1
  tmp["TopK tmp · queried"]:1
```
##### 字节账与复用顺序
```text
UB_total(R-006A) = topkTmp + SingleBlockRuntimeSpace(axis,tile,sizeof(T),8,k) <= usableUb
UB_total(R-006B) = max(上述TopK占用, 2*Align(k*4)+2*Align(k*8)+Align(sortTmpSize)) <= usableUb
workspace_total = topkWorkspaceSize（通常仅16MiB前缀）
```
| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| input/output queue | DMA/API | API/DMA | next batch | queue protocol | tail count有效 |
#### 同步、精度与尾块
##### 同步与数值边界表
| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| pipeline | TQue | DMA | TopK/copyout | UB slot | dtype原生比较，tailBatch字段 |
| R-006B kernel edge | stream order | single-block TopK | AIV Sort | output GM | i32原生比较，pad不写回 |
#### 关键实现
##### 符号证据表
| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `op_kernel/top_k_kernel.cpp` | `FillSmallMode` | batch/loop/tail |
| Kernel entry/router | 同上 | `generateOpObject`/`LaunchSortRows` | single-block 最高 radix 优先级；i32追加Sort |
| Device body/helper | 同上 | `RadixSortTopKSingleBlock`/`sort_top_k_rows_kernel` | full-axis TopK及i32有序化 |

### Route R-001（P1）：小 k SIMT 直接选择

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Tiling | `op_kernel/top_k_kernel.cpp` | `calc_top_k_tiling` | 三组 small-k 谓词 | output 5 |
| Router | 同上 | `launch_top_k_kernel` | output 5 | `LaunchSmallK` |

#### Device 数据流

##### 函数级调用链

```text
LaunchSmallK -> small_k_top_k_kernel -> SmallKRowsSimt
```

##### 源码等价伪码

```text
row <- block连续域；for row += THREADS:
  扫描 axis；维护长度 k 的有序私有数组；新值优于当前最差值时插入并右移
  写 values[(outer*k+rank)*inner+innerId] 与 int64 index
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM x | `(outer*axis+pos)*inner+innerId` | input numel | T/ND | caller | SIMT | caller | coalescing 取决于 inner |
| 私有数组 | thread-private | `MAX_K*(sizeof(T)+4)` | T+u32 | 当前线程 | 当前线程 | 单 row | 模板 MAX_K |
| GM output | `(outer*k+rank)*inner+innerId` | output numel | T/i64 | SIMT | caller | caller | 有效 rank<k |

##### 分层内存布局

N/A：该 Route 不分配 AIV UB；每线程使用编译期定长私有数组。

##### 字节账与复用顺序

```text
UB_total = 0（显式 AIV Queue/TBuf）
dynamic_ub = N/A
workspace_total = topkWorkspaceSize 基线；本 Route body 不消费用户 workspace
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| thread-private best arrays | 当前 row | 同线程输出 | 下一 row | 单线程程序序 | `k<=MAX_K` |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| row scan | SIMT 私有状态 | 同线程 | 同线程 | best list | 无 cast；显式 NaN 顺序；`local<count` |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `op_kernel/top_k_kernel.cpp` | `calc_top_k_tiling` | small-k 覆盖其它已算出的路线 |
| Kernel entry/router | 同上 | `small_k_top_k_kernel` | block 连续分区、线程跨步 |
| Device body/helper | 同上 | `SmallKRowsSimt` | 私有有序插入和 ND 地址 |

### Route R-003（P2）：非末轴融合 TopK/Sort

#### 适用条件
##### 选择证据
| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Tiling | `op_kernel/top_k_kernel.cpp` | `CalcNonLastTiling` | axis≤2048、bestChunk peak≤UB | mode 8 |
| Router | 同上 | `generateOpObject` | mode 8/keyParams0 | radix-select 或 merge |

#### Device 数据流
##### 函数级调用链
```text
top_k_direct_kernel -> TopKNonLastSmallAxisNonTranspose::Process
 -> LoadTile -> TransposeToTopKMajor -> RunTopK/RunMergeSort -> StoreTile(SIMT)
```
##### 源码等价伪码
```text
tileId覆盖outer*ceil(inner/chunk)；加载[axis,chunk]；UB内转为[chunk,axis]；
逐chunk行 TopK/Sort；V_S event；SIMT 按[outer,k,inner]散写。
```

#### 内存与数据搬运
##### 资源与搬运表
| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| inputTile | `outer*axis*inner+innerStart` | `axis*inputRowBytes` | `[axis,chunk]` | LoadTile | transpose | TPipe | 32 B rows |
| sortInput | UB | `chunk*axisRowBytes` | `[chunk,alignedAxis]` | transpose | TopK/Sort | TPipe | aligned |
| value/index | UB | `chunk*(valueRowBytes+indexRowBytes)` | `[chunk,k]` | TopK/Sort | SIMT store | TPipe | row aligned |
| tmp | UB | aligned queried tmp | bytes | API | API | TPipe | no alias |

##### 分层内存布局
```mermaid
block-beta
  columns 4
  input["inputTile · axis*inputRowBytes"]:1
  trans["sortInput · chunk*axisRowBytes"]:1
  out["value+index · chunk*(valueRow+indexRow)"]:1
  tmp["TopK/Sort tmp · aligned tmpUbSize"]:1
```
##### 字节账与复用顺序
```text
UB_total = axis*inputRowBytes + bf16_cast(optional) + chunk*(axisRowBytes+valueRowBytes+indexRowBytes) + Align(tmp)
UB_total <= usableUb；workspace_total = 16 MiB
```
| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| value/index UB | TopK/Sort | Store SIMT | 下一 tile | V_S SetFlag/WaitFlag 前后 | store 完成后覆盖 |

#### 同步、精度与尾块
##### 同步与数值边界表
| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Vector→SIMT | `HardEvent::V_S` | TopK/Sort | Store helper | value/index UB | `curInnerChunk` 防越界；BF16 merge 升 FP32 |

#### 关键实现
##### 符号证据表
| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `op_kernel/top_k_kernel.cpp` | `CalcNonLastTiling` | chunk/UB/core 搜索 |
| Kernel entry/router | 同上 | `generateOpObject` | keyParams0 选择 merge/radix |
| Device body/helper | 同上 | `TopKNonLastSmallAxisNonTranspose` | UB 转置、API、SIMT store |

### Route R-002（P3）：小轴 MergeSort

#### 适用条件
##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Tiling | `op_kernel/top_k_kernel.cpp` | `CalcSmallMergeTiling` | axis≤1024、f16/bf16、UB/tmp 成立 | 13002/14002 |
| Router | 同上 | `launch_top_k_kernel` | key+dtype 双检 | merge entry |

#### Device 数据流
##### 函数级调用链
```text
top_k_merge_direct_kernel -> generateMergeTopKObject -> MergeSort::Init -> ProcessSort
  -> CopyDataIn -> VbsMergeSort/Bf16 -> CopyValue2Gm
```
##### 源码等价伪码
```text
按 core/loop 取 rowsPerCore 行；GM->双缓冲 input；BF16 先转 FP32；
对 alignedAxis 做 Merge Sort，截取前 k 值/索引；UB->GM。
```

#### 内存与数据搬运
##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| input/output queues | row tile | `bufferNum*align(realNum)*sizeof(dtype)` | T | DMA | merge/copyout | TPipe | `bufferNum=2` |
| merge TBuf | UB | queried concat tmp + aligned intermediates | ConvertT | Sort helper | Sort helper | TPipe | BF16 用 FP32 |
| user workspace | system 后 | histogram+tile metadata | byte | body | body | Torch workspace | 32 B internal |

##### 分层内存布局
```mermaid
block-beta
  columns 4
  inQ["inQueue · depth=keyParams4 · aligned rows"]:1
  cast["cast/value temp · BF16 uses FP32"]:1
  merge["Concat/Sort tmp · queried bytes"]:1
  outQ["value/index queues · depth=keyParams4"]:1
```
##### 字节账与复用顺序
```text
UB_total = Σ MergeSort::InitBuffers + MergeSortInitBuffer 分配
UB_total <= usableUb；workspace_total = 16 MiB + histogram + 2*aligned(tileTopk)
```
| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| double-buffer queues | CopyIn | Sort/CopyOut | 下一行批 | Que EnQue/DeQue/FreeTensor | depth 与循环一致 |

#### 同步、精度与尾块
##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| merge | Queue + Sort | CopyIn | Sort/CopyOut | UB slots | BF16→FP32→BF16；只写 k |

#### 关键实现
##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `op_kernel/top_k_kernel.cpp` | `CalcSmallMergeTiling` | core、tile、tmp、workspace |
| Kernel entry/router | 同上 | `top_k_merge_direct_kernel<T,ConvertT>` | compact POD 重建 |
| Device body/helper | 同上 | `MergeSort`/`KernelVbsMergeSort` | 队列、BF16 cast、Merge Sort |

### Route R-011（P4）：官方 NDDMA 转置组合

#### 适用条件
##### 选择证据
| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Tiling | `op_kernel/top_k_kernel.cpp` | `calc_top_k_tiling` | 非末轴axis>2048 | transpose 1 |
| Host | `op_plugin/top_k_plugin.cpp` | `calc_transpose_tiling` | 三个 `[outer,row,col]` POD | launch graph |
#### Device 数据流
##### 函数级调用链
```text
launch_transpose_kernel(forward) -> NDDMA/Gather/VCONV router
 -> LaunchOfficialTopK(last axis)
 -> launch_transpose_kernel(values reverse)
 -> launch_transpose_kernel(indices reverse)
```
##### 源码等价伪码
```text
[outer,axis,inner] --perm(0,2,1)--> [outer,inner,axis]
 -> 每行TopK得[outer,inner,k]
 -> values/indices分别perm回[outer,k,inner]。
transpose tilingKey决定NO_CUT/CUT_ONCE/CUT_TWICE/N_LAST/BIG_DIM/GATHER/VCONV阶段。
```
#### 内存与数据搬运
##### 资源与搬运表
| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| transposed input | offset | outer*axis*inner*sizeof(T) | `[outer,inner,axis]` | forward | TopK | workspace | 512 B |
| transposed values | offset | outer*inner*k*sizeof(T) | `[outer,inner,k]` | TopK | reverse | workspace | 512 B |
| transposed indices | offset | outer*inner*k*8 | `[outer,inner,k]` | TopK | reverse | workspace | 512 B |
| transpose UB | per tiling | `vecQue` 1×ubSize or 2×ubSize/2；Gather双队列+index；VCONV双队列 | bytes | NDDMA/gather | copyout | TPipe | stage-specific |
##### 分层内存布局
```mermaid
block-beta
  columns 4
  fwd["forward slice · full input"]:1
  topk["TopK user/system workspace"]:1
  val["transposed values · outer*inner*k*sizeof(T)"]:1
  idx["transposed indices · outer*inner*k*8"]:1
```
##### 字节账与复用顺序
```text
workspace_total = Align(topkWorkspace,512)+Align(inputBytes,512)+Align(valueBytes,512)+indexBytes
transpose UB_total = tilingData.ubSize（NDDMA）或各 router 对应的等价分配
```
| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| forward slice | transpose | TopK | graph end | same stream | TopK完成前不覆盖 |
| value/index slices | TopK | two reverse nodes | graph end | same stream | slices不别名 |
#### 同步、精度与尾块
##### 同步与数值边界表
| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| graph | stream order | each node | next node | GM slices | byte-preserving transpose；NDDMA tiler描述各tail |
#### 关键实现
##### 符号证据表
| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `op_plugin/top_k_plugin.cpp` | `TransposeNddmaTiling`/`calc_transpose_tiling` | CUT阶段、block、POD |
| Kernel entry/router | `op_kernel/top_k_kernel.cpp` | `launch_by_type` | Gather/VCONV/NDDMA router |
| Device body/helper | 同上 | `TransposeCutOneAxis/TwoAxis/NLast/...` | NDDMA地址、tail与阶段 |

### Route R-008（P5）：末轴 Multi Core Optimized

#### 适用条件
##### 选择证据
| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Tiling | `op_kernel/top_k_kernel.cpp` | `CalcLastAxisTiling` | optimized UB且候选数≤tile | mode4 |
#### Device 数据流
##### 函数级调用链
```text
top_k_direct_kernel -> RadixSortTopKMultiCoreOptimization::Init -> Process
```
##### 源码等价伪码
```text
多个核并行处理一行的tile，写(value,index)候选workspace；同步后归并k项。
```
#### 内存与数据搬运
##### 资源与搬运表
| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| candidate workspace | aligned value then index | `Align(sizeof(T)*factor*k)+Align(4*factor*k)` | T/i32 | tile cores | reducer | workspace | 32 B |
| UB | per tile | `MultiCoreOptimRuntimeSpace+tmp` | mixed | body | body | TPipe | aligned |
##### 分层内存布局
```mermaid
block-beta
  columns 4
  in["tile input"]:1
  idx["tile index"]:1
  cand["k value/index candidates"]:1
  tmp["TopK tmp"]:1
```
##### 字节账与复用顺序
```text
UB_total = topkTmp + MultiCoreOptimRuntimeSpace(tile,sizeof(T),8,k) <= usableUb
workspace_total = 16MiB + aligned candidate values + indices
```
| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| candidate slices | tile cores | reducer | next logical row | kernel global sync | batch scheduling |
#### 同步、精度与尾块
##### 同步与数值边界表
| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| inter-core | `SyncAll`/batch schedule | tile cores | reducer | workspace | tile/core tail guard |
#### 关键实现
##### 符号证据表
| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `op_kernel/top_k_kernel.cpp` | `FillMultiCoreMode(...,true)` | parallel/tile/core |
| Kernel entry/router | 同上 | `generateOpObject` | mode4 |
| Device body/helper | 同上 | `RadixSortTopKMultiCoreOptimization` | 候选workspace与归并 |

### Route R-010（P6）：int64 动态 int32 窄化

#### 适用条件
##### 选择证据
| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Tiling | `op_kernel/top_k_kernel.cpp` | workspace planner | int64、末轴、mode1 | dynamic flag |
| Router | 同上 | `LaunchOfficialTopK` | dynamic flag | five-node graph |
#### Device 数据流
##### 函数级调用链
```text
range_init -> cast_input(atomic_or flag) -> int32 retiled TopK or int32 v9.0.1 body
 -> int64 v9.0.1 fallback(flag!=0 only) -> cast_output(flag==0 only)
```
##### 源码等价伪码
```text
flag=0；并行窄化全部输入，任一往返不等则atomic_or(1)；
flag==0执行int32 TopK并扩回int64；flag!=0跳过int32输出、执行int64 TopK。
```
#### 内存与数据搬运
##### 资源与搬运表
| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| range flag | aligned offset | 512 B | u32 scalar | init/cast | gating | workspace | atomic OR |
| int32 input | aligned offset | input elements*4 | i32 | cast | int32 TopK | workspace | 512 B start |
| int32 values | aligned offset | rows*k*4 | i32 | int32 TopK | cast output | workspace | 512 B start |
| user workspace | after 16 MiB | radix formula | mixed | TopK | TopK | workspace | shared by mutually exclusive bodies |
##### 分层内存布局
N/A：SIMT cast 无显式 AIV UB；TopK 节点分别采用 R-007 的 UB 布局。
##### 字节账与复用顺序
```text
workspace_total = Align(TopKBase + 512flag + 4*inputCount + 4*rows*k,512)
dynamic_ub = 0 for cast；TopK localMemorySize=usableUb
```
| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| user radix workspace | int32 body或int64 fallback | 同一 body | graph end | flag使两body互斥、same stream | flag可见 |
#### 同步、精度与尾块
##### 同步与数值边界表
| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| range | atomic OR + stream order | cast threads | TopK gating | flag | 往返相等才走i32；block/thread tail |
| output | flag gate | int32 TopK/int64 fallback | cast output | values | 无损 i32→i64 |
#### 关键实现
##### 符号证据表
| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `op_kernel/top_k_kernel.cpp` | planner/`CalcLastAxisTiling` | slices与运行时retile |
| Kernel entry/router | `op_kernel/top_k_cast_kernel.cpp` | three cast launchers | 1/blocks/blocks launch |
| Device body/helper | 两个 kernel 文件 | `CastInputVf`/v9.0.1 body | 原子范围证明与互斥fallback |

### Route R-007（P7）：末轴 Single Core 多 Tile

#### 适用条件
##### 选择证据
| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Tiling | `op_kernel/top_k_kernel.cpp` | `FillSingleCoreMode` | rows≥cores、single-core UB | mode1 |
#### Device 数据流
##### 函数级调用链
```text
top_k_direct_kernel -> RadixSortTopKSingleCore::Init -> per-tile radix -> candidate TopK -> CopyOut
```
##### 源码等价伪码
```text
一核负责一行；每tile做radix直方图/选择，保存tile候选；再从tile候选中取全局k并排序。
```
#### 内存与数据搬运
##### 资源与搬运表
| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| histogram workspace | row/tile | `tileCount*256*parallel*4` | i32 bins | tile radix | reduction | workspace | user region |
| UB queues/TBuf | per tile | `SingleCoreRuntimeSpace + tmp` | mixed | body | body | TPipe | aligned |
##### 分层内存布局
```mermaid
block-beta
  columns 4
  inQ["tile input"]:1
  hist["3*256-bin + tile cumsum"]:1
  cand["tile values/index"]:1
  tmp["TopK/Sort tmp"]:1
```
##### 字节账与复用顺序
```text
UB_total = topkTmp + SingleCoreRuntimeSpace(axis,tile,sizeof(T),8,k,true) <= usableUb
workspace_total = 16MiB + tileCount*256*parallel*4
```
| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| tile UB | CopyIn/radix | candidate reduction | next tile | body pipe/order | candidate已写workspace/UB |
#### 同步、精度与尾块
##### 同步与数值边界表
| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| tile loop | pipe + program order | tile radix | final TopK | candidates | tailTileNum |
#### 关键实现
##### 符号证据表
| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `op_kernel/top_k_kernel.cpp` | `FillSingleCoreMode` | tileCount/numTile/tail |
| Kernel entry/router | 同上 | `generateOpObject` | mode1 |
| Device body/helper | 同上 | `RadixSortTopKSingleCore` | per-tile+final reduction |

### Route R-009（P8）：末轴 Multi Core 通用 Radix

#### 适用条件
##### 选择证据
| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Tiling | `op_kernel/top_k_kernel.cpp` | `CalcLastAxisTiling` | generic UB 成立 | mode2 |
#### Device 数据流
##### 函数级调用链
```text
top_k_direct_kernel -> RadixSortTopK::Init -> ProcessTopK
  -> per-pass histogram -> global cumsum -> scatter/candidate -> final TopK
```
##### 源码等价伪码
```text
每个radix pass按tile产生256-bin histogram；跨核前缀和；按bin散射；
围绕k所在bin收缩候选，最后TopK并写出。
```
#### 内存与数据搬运
##### 资源与搬运表
| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| hist workspace | per row/core/tile | `256*4*parallel` | i32 | histogram | cumsum | workspace | fixed bins |
| tile metadata | after hist | `2*Align(tileCount*4*parallel)` | i32 | passes | reducer | workspace | 32 B |
| UB | per tile | `MultiCoreRuntimeSpace+tmp` | mixed | body | body | TPipe | aligned |
##### 分层内存布局
```mermaid
block-beta
  columns 4
  in["input/copy/twiddle"]:1
  hist["256-bin hist+cumsum"]:1
  idx["source/output indices"]:1
  tmp["TopK/Sort tmp"]:1
```
##### 字节账与复用顺序
```text
UB_total = topkTmp + MultiCoreRuntimeSpace(axis,tile,cores,sizeof(T),8,k) <= usableUb
workspace_total = 16MiB + hist + 2*aligned(tile metadata)
```
| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| hist/tile metadata | current pass | cumsum/scatter | next pass | `SyncAll` | schemMode=1 |
#### 同步、精度与尾块
##### 同步与数值边界表
| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| radix passes | `SyncAll` | hist/scatter cores | next phase | GM workspace | NumPass=1/2/4/8；tail tile有效长度 |
#### 关键实现
##### 符号证据表
| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `op_kernel/top_k_kernel.cpp` | `FillMultiCoreMode(...,false)` | generic route |
| Kernel entry/router | 同上 | `LaunchTypedTopK` | dtype/unsigned/NumPass |
| Device body/helper | 同上 | `RadixSortTopK` | histogram/cumsum/scatter |

### Route R-004（P9）：非末轴 i32 短步有序化

#### 适用条件
##### 选择证据
| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Tiling | `op_kernel/top_k_kernel.cpp` | `calc_top_k_tiling` | mode8、i32、33≤k≤64 | output 2 |

#### Device 数据流
##### 函数级调用链
```text
R-003 producer -> same-stream sort_short_strided_top_k_kernel -> SortShortStridedRowsSimt
```
##### 源码等价伪码
```text
每线程取一个(outer,inner)逻辑行；对 k 个 strided value/index 做原地插入排序。
```
#### 内存与数据搬运
##### 资源与搬运表
| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| values/indices GM | `outer*k*inner+rank*inner+innerId` | output | i32/i64 | R-003 | SIMT sort | caller | 原地 |
##### 分层内存布局
N/A：后处理节点使用寄存器标量并原地更新 GM。
##### 字节账与复用顺序
```text
UB_total = R-003 UB；post-sort显式UB=0；workspace_total=16 MiB
```
| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| output GM row | R-003 | post-sort | caller | same stream | 每线程唯一 row |
#### 同步、精度与尾块
##### 同步与数值边界表
| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| kernel edge | stream order | R-003 | post-sort | output GM | i32 比较；row<count |
#### 关键实现
##### 符号证据表
| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `op_kernel/top_k_kernel.cpp` | output sort selector | 33..64 |
| Kernel entry/router | 同上 | `LaunchShortStridedSort` | order 模板 |
| Device body/helper | 同上 | `SortShortStridedRowsSimt` | strided 原地插入 |

### Route R-005（P10）：非末轴 i32 Radix Sort 补全

#### 适用条件
##### 选择证据
| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Tiling | `op_kernel/top_k_kernel.cpp` | output sort selector | mode8、i32、k>64 | output 1 |
#### Device 数据流
##### 函数级调用链
```text
R-003 -> [inner>1: values/index AxisToLast] -> sort_top_k_rows_kernel
      -> [inner>1: values/index LastToAxis]
```
##### 源码等价伪码
```text
把[outer,k,inner]重排成[outer,inner,k]；每核跨步处理 row；
DataCopyPad值/索引到UB；AscendC::Sort RADIX_SORT；只复制k项；反向重排。
```
#### 内存与数据搬运
##### 资源与搬运表
| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| sort slices | 512 B aligned offsets | outer*inner*k*(4+8) | row-major k | transpose | Sort/reverse | workspace | values/indices 独立 |
| Sort queues | UB | `2*Align(k*4)+2*Align(k*8)` | i32/i64 | DMA/Sort | Sort/DMA | TPipe | depth 1 |
| Sort tmp | UB | Align(sortTmpSize) | bytes | Sort | Sort | TPipe | queried |
##### 分层内存布局
```mermaid
block-beta
  columns 5
  vin["valueIn · Align(k*4)"]:1
  iin["indexIn · Align(k*8)"]:1
  vout["valueOut · Align(k*4)"]:1
  iout["indexOut · Align(k*8)"]:1
  tmp["Sort tmp · Align(tmpSize)"]:1
```
##### 字节账与复用顺序
```text
UB_total = 2*Align(k*4)+2*Align(k*8)+Align(sortTmpSize) <= usableUb
workspace_total = Align(16MiB + 2 output-sized sort slices,512)
```
| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| queue slot | DataCopyPad/Sort | Sort/DataCopyPad | next row | EnQue/DeQue/FreeTensor | depth 1 sequential row loop |
#### 同步、精度与尾块
##### 同步与数值边界表
| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| graph edges | stream order | transpose/Sort | next node | workspace slices | padding lanes不复制到GM |
#### 关键实现
##### 符号证据表
| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `op_kernel/top_k_kernel.cpp` | `GetOutputSortTmpSize` | Sort tmp/UB guard |
| Kernel entry/router | 同上 | `LaunchSortRows` | inner==1 快路与转置图 |
| Device body/helper | 同上 | `sort_top_k_rows_kernel` | 五段 UB、radix Sort |

### Route R-012（P11）：SIMT 转置兼容组合

#### 适用条件
##### 选择证据
| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Tiling | `op_kernel/top_k_kernel.cpp` | fused fallback | axis≤2048且融合失败 | transpose 2 |
#### Device 数据流
##### 函数级调用链
```text
AxisToLastSimt -> LaunchOfficialTopK -> LastToAxisSimt(values) -> LastToAxisSimt(indices)
```
##### 源码等价伪码
```text
每block取连续linear区间，2048线程跨步；按除模映射布局；同流完成TopK与两路逆映射。
```
#### 内存与数据搬运
##### 资源与搬运表
| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| 三个 transpose slices | 同 R-011 | 同 R-011 | GM | SIMT/TopK | next node | workspace | 512 B starts |
##### 分层内存布局
N/A：转置节点不分配 AIV UB；GM workspace 布局与 R-011 相同。
##### 字节账与复用顺序
```text
UB_total(transpose)=0；workspace_total与R-011同式；TopK UB按R-006~9
```
| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| GM slices | preceding node | next node | graph end | same stream | linear count tail guard |
#### 同步、精度与尾块
##### 同步与数值边界表
| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| transpose | stream order | SIMT node | TopK/reverse | GM slices | bitwise move；`local<count` |
#### 关键实现
##### 符号证据表
| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `op_kernel/top_k_kernel.cpp` | fallback selector | needsTranspose=2 |
| Kernel entry/router | 同上 | `transpose_axis_topk_kernel` | direction template |
| Device body/helper | 同上 | `AxisToLastSimt/LastToAxisSimt` | ND线性地址映射 |

## 算子特定优化

### Trick T-001（共享 Route）：Compact POD 保留官方 body 而缩小直调参数

#### 触发与源码依据

- 适用 Route：R-002~R-010
- 触发条件：direct-launch entry；mode 8 与末轴模式使用互斥字段布局
- Golden 来源：交付实现 `op_kernel/top_k_launch.h` 与 `op_kernel/top_k_kernel.cpp`（SHA-256 已列于 Frontmatter）

**交付源码（连续逐字摘录）**：

```cpp
struct TopKDirectTiling {
    uint32_t data[16];
};

static_assert(sizeof(TopKDirectTiling) == 64, "TopK direct tiling ABI changed");
```

#### 机制与设计原因

Host 保留完整 tiling 计算，只把当前 body 真正消费的字段压入 64 B；Device entry 重建 `TopKV2TilingDataSimd` 后继续进入相关官方模板。这减少 scalar kernel 参数载荷，同时用 mode 区分两套互斥布局，避免传输 inactive 字段。

#### 迁移边界

- 适用：需要直接 launch 复用大 POD 官方 body 的实现。
- 前提：producer/consumer 对每个 slot、位宽和 inactive 条件完全一致。
- 失效：新增 Device consumer 时必须扩展 pack/unpack 或放弃 compact ABI。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓未提供可验证反例；但 `static_assert` 明确阻止结构大小静默变化。

### Trick T-003（关联 P2、P9、P10）：非末轴小轴在 UB 内融合布局变换

#### 触发与源码依据

- 适用 Route：R-003~R-005
- 触发条件：axis≤2048 且至少一个 innerChunk 候选满足完整 peak UB 账
- Golden 来源：交付实现 `op_kernel/top_k_kernel.cpp` 中 `CalcNonLastTiling` 与 `TopKNonLastSmallAxisNonTranspose`

**交付源码（连续逐字摘录）**：

```cpp
this->pipe_->InitBuffer(this->inputTileBuf_, this->axisLen_ * this->inputRowBytes_);
this->pipe_->InitBuffer(this->sortInputBuf_, this->innerChunk_ * axisRowBytes_);
this->pipe_->InitBuffer(topkValueBuf_, this->innerChunk_ * valueRowBytes_);
this->pipe_->InitBuffer(topkIndexBuf_, this->innerChunk_ * indexRowBytes_);
this->pipe_->InitBuffer(this->tmpBuf_, ROUND_UP_AGLIN(this->tmpUbSize_));
```

#### 机制与设计原因

以 `[axis,innerChunk]` 搬入，UB 内转成 API 友好的 `[innerChunk,axis]`，完成 TopK/Sort 后由 SIMT 直接散写 `[outer,k,inner]`。这避免全输入 forward transpose 和两份完整输出 reverse transpose；Host 的 peak 公式把输入 tile、转置后行、输出值/索引、BF16 cast 与 API tmp 全部计入。

#### 迁移边界

- 适用：非末轴较短、inner 可分块且 UB 可容纳完整融合工作集。
- 前提：V→S event、地址公式和 `curInnerChunk` tail 保持一致。
- 失效：无候选满足 UB 时必须进入 R-012；axis>2048 进入 R-011。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓给出的真实 fallback 是转置组合；不能在 peak 超限时强行增大 chunk。

### Trick T-002（关联 P6）：int64 运行时范围证明与互斥 fallback

#### 触发与源码依据

- 适用 Route：R-010
- 触发条件：末轴 int64 single-core，且未被 small-k 路线覆盖
- Golden 来源：交付实现 `op_kernel/top_k_cast_kernel.cpp` 与 `LaunchInt64DynamicInt32Typed`（SHA-256 已列于 Frontmatter）

**交付源码（连续逐字摘录）**：

```cpp
int64_t value = input[index];
int32_t narrowed = static_cast<int32_t>(value);
output[index] = narrowed;
if (static_cast<int64_t>(narrowed) != value) asc_atomic_or(rangeFlag, 1U);
```

#### 机制与设计原因

先用并行往返转换为整张输入构造一个单调 range flag；全部值可精确表示时，重算真正的 int32 tiling并执行四 pass radix，否则同流的 int64 fallback 才生效。两个 TopK body 由同一 flag 互斥，用户 workspace 可安全复用，正确性不依赖抽样。

#### 迁移边界

- 适用：较宽整数可由运行时证明无损窄化的选择/排序。
- 前提：range flag 初始化、atomic、body gating 和 cast-back 全部同流有序。
- 失效：任一输入越界时必须完整执行原 dtype 路线。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

仅检查局部 tile 或无原子地写 flag 会漏掉其它线程发现的越界；源码以全域遍历和 `atomic_or` 避免该错误。

## 模板与实现对比

| 重要性 | Route | selector 与主要模板 | 循环/分核 | 内存、同步与精度 | fallback/失败边界 |
|---:|---|---|---|---|---|
| P0 | R-006A/R-006B | mode 0；`RadixSortTopKSingleBlock`，int32 可追加 AIV Sort | row batch/core | whole-axis UB、Queue；R-006B 以 stream 连接第二节点 | UB 不成立到 R-007 |
| P1 | R-001 | output 5；SIMT 私有有序表 | row/block/thread | 无显式 UB；私有数组；原 dtype 比较 | H4 覆盖既有基础 Route；无 Device fallback |
| P2 | R-003 | mode 8；non-last TopK/merge | outer×innerTile | 六类 UB 区；V→S event；BF16 merge 升 FP32 | 融合失败到 R-012 |
| P3 | R-002 | key 13002/14002；MergeSort/Concat | row/core | 多 Queue/TBuf；BF16 升 FP32 | merge tiling 失败回 common radix |
| P4 | R-011 | transpose 1；NDDMA/Gather/VCONV + last-axis TopK | transform/core + TopK | 三个 GM slice；同流交接；byte-preserving transpose | 任一 tiling 失败则 Host 失败 |
| P5 | R-008 | mode 4；`RadixSortTopKMultiCoreOptimization` | tile/core | 候选 workspace；跨核同步 | 资源或候选约束不成立到 R-009 |
| P6 | R-010 | dynamic flag；cast + int32/int64 single-core | 五节点 | atomic range flag；两种 body 互斥复用 workspace | 窄化越界或 retile 失败走 int64 body |
| P7 | R-007 | mode 1；`RadixSortTopKSingleCore` | row/core/tile | tile histogram workspace；Queue | UB 不成立继续 R-008；int64 可叠加 R-010 |
| P8 | R-009 | mode 2；`RadixSortTopK` | pass/tile/core | histogram 与 tile metadata；`SyncAll` | common tiler 终点，失败即 Host 失败 |
| P9 | R-004 | mode 8/output 2；SIMT insertion sort | logical row/thread | values/indices 原地；同流 | 谓词不成立按 H3 保留 R-003 或转 R-005 |
| P10 | R-005 | mode 8/output 1；AIV radix Sort | row/core；inner>1 增加布局变换 | 四 Queue+Sort TBuf；可有两个 output slice | Sort tmp/UB 不闭合则 Host 失败 |
| P11 | R-012 | transpose 2；SIMT transform + last-axis TopK | linear/block/thread + TopK | 三个 GM slice；transpose 无显式 UB；同流 | last-axis tiling 失败则 Host 失败 |

## 平台差异

| 项目 | A2 | A3 | A5 |
|---|---|---|---|
| 支持状态 | 本直调交付未声明 | 本直调交付未声明 | 任务指定目标平台；本地相关官方 9.1.0 README/OpDef 声明 Ascend 950 支持 |
| Host/Launcher | 固定仓不可见 | 固定仓不可见 | `PlatformAscendCManager` 查询 AIV core/UB；direct launcher |
| Kernel/资源 | 固定仓不可见 | 固定仓不可见 | arch35 AIV/SIMT/NDDMA，32 KiB 保留，16 MiB system workspace |

## 限制与失败边界

- 直调接口不支持官方 TopKV2 的 `int16/uint16/uint32/uint64`，也不支持 `sorted=false`、Tensor `k` 或 `indices_dtype=int32`；不得用官方接口能力扩大本卡语义。
- 输入必须连续、rank 1–8、各维正、`1<=k<=axis`；shape 乘积写入 u64，源码没有显式乘法溢出检查；`localMemorySize` 窄化为 u32。
- output enum 3（full-axis direct）与 4（int64 short scan）只有 router/body，当前 selector 不生产，属于 dormant，不是 Host 可达 Route。
- `launch_top_k_kernel` 与各 Device launcher 为 `void`，提交后的逐节点错误传播在固定交付源码中不可见。
- 相关官方映射只支撑 A5 平台与 body/key 关联；compact ABI、SIMT 快路、动态窄化及多 Kernel 组合均为交付实现，不伪称官方。任务指定 Commit 的对象不在本地浅克隆中，故固定 Commit blob 身份是保留缺口。
- 本次知识提取未执行编译、真机、数值或性能测试。

## 源码索引

### 链路索引

| 链路阶段 | 文件 | 关键符号 | 支撑内容 |
|---|---|---|---|
| 入口声明/约束 | `csrc/ops/top_k/op_plugin/top_k_plugin.cpp` | schema、`top_k_meta` | 交付接口与约束；Frontmatter SHA-256 |
| 入口实现 | `csrc/ops/top_k/op_plugin/top_k_plugin.cpp` | `top_k_npu` | tiling、workspace、stream、direct call；Frontmatter SHA-256 |
| Host/Tiling/Launcher | `csrc/ops/top_k/op_kernel/top_k_kernel.cpp` | `calc_top_k_tiling` | Route/资源/workspace；Frontmatter SHA-256 |
| Kernel entry/body | `csrc/ops/top_k/op_kernel/top_k_kernel.cpp` | `launch_top_k_kernel` 及全部 helper | AIV/SIMT/NDDMA、多 Kernel 图；Frontmatter SHA-256 |
| 构建接线 | `csrc/ops/top_k/CMakeLists.txt` | `register_direct_launch_op` | 两个 kernel TU 与 plugin TU |
| 官方平台映射 | `math/top_k_v2/op_host/top_k_v2_def.cpp` | `AddConfig("ascend950")` | 相关官方 TopKV2 A5 注册 |
| 官方 body 映射 | `math/top_k_v2/op_kernel/top_k_v2_apt.cpp` | `generateOpObject`/`top_k_v2` | key、mode、模板族 |

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | compact pack/unpack | 64/56 B、slot位宽、mode互斥布局 | `PackDirectTiling`/`PackMergeDirectTiling` |
| 调用顺序 | 同流多节点图 | producer→consumer顺序、NDDMA三套POD | `launch_top_k_kernel` |
| workspace/内存 | 16MiB前缀+512B切片 | offset、extent、owner/lifetime | `calc_top_k_tiling` |
| 同步 | Queue/V_S/SyncAll/atomic/stream | batch scheduling、flag可见性 | `rtKernelLaunchWithFlagV2`、各body |
| 精度与尾块 | BF16升FP32、int64有证据窄化 | cast顺序、NaN比较、有效count | merge/SmallK/cast helpers |
| 失败边界 | tiler false阻止launch | dormant router不当作Route，void launch不伪造返回 | Host/router |
