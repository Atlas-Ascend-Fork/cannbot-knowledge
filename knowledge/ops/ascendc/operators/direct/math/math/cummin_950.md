---
type: Operator
title: "Cummin 950 Direct Invoke 算子知识"
description: "说明 cann_bench::cummin 在 950 上的接口语义、Direct Launcher 参数生成、Route 选择、单/多 Kernel 启动图与逐节点实现。"
tags: [task.implementation, task.lookup, topic.data_movement, topic.memory, topic.precision, topic.programming_model]
status: stable
sources:
  - resource: https://gitcode.com/cann/ops-math/blob/c821871ee4bccb0c564a582d1b362072c356a88d/math/cummin/README.md
    role: header
  - resource: https://gitcode.com/cann/ops-math/blob/c821871ee4bccb0c564a582d1b362072c356a88d/math/cummin/op_host/cummin_def.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-math/blob/c821871ee4bccb0c564a582d1b362072c356a88d/math/cummin/op_host/arch35/cummin_tiling.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-math/blob/c821871ee4bccb0c564a582d1b362072c356a88d/math/cummin/op_kernel/arch35/cummin.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-math/blob/c821871ee4bccb0c564a582d1b362072c356a88d/math/cummin/CMakeLists.txt
    role: implementation
created_at: "2026-08-24T19:31:28Z"
updated_at: '2026-08-27T12:23:11Z'
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# Cummin 950 Direct Invoke 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | `cann_bench::cummin(Tensor input, int dim)`；`PrivateUse1` 实现 `cummin_npu`；按 dtype 调用 `launch_cummin_{float16,float32,bfloat16,int32}` |
| 计算语义 | 把连续 ND 输入按 `dim` 展平为 `[M,R,N]`，对每个 `(m,n)` 沿 `r` 做 inclusive cumulative minimum，同时输出产生当前前缀最小值的位置 |
| 输入输出 | `input/values` 同 shape、连续 ND，dtype 为 `float16/float32/bfloat16/int32`；`indices` 同 shape、`int64`；`dim∈[-rank,rank-1]`，`rank>=1` |
| 执行类型 | R-005 为 AIV wrapper 内 `asc_vf_call` 的 SIMT；R-002/R-003/R-007 为 AIV_VECTOR；R-006 为三个 AIV wrapper + 三个 SIMT 节点；R-001 为 AIV_VECTOR；R-004 为 AIV wrapper 内 `asc_vf_call` 的 SIMT；无可达 Cube/AIC 或 MIX_CV 节点。 |
| Kernel 路线 | R-005 warp-row SIMT；R-002 N 全载、R 分片；R-003 N 分片；R-007 NaN-aware 寄存器扫描；R-006 segmented-row 三 Kernel SIMT；R-001 RN 全载；R-004 lane-SIMT |
| 核心资源 | AIV Route 使用 GM、`TQue`/LocalTensor、MicroAPI RegTensor 与硬事件；SIMT Route 使用 GM、线程/warp 寄存器与 shuffle；R-006 以输出 GM 作为节点间交接；workspace 为 0 |
| 来源闭包 | `direct_implementation_closed`：转换交付件已闭合 `cann_bench::cummin`→PrivateUse1→`calc_cummin_tiling`→四个 dtype launcher→所有可达单/多 Kernel entry→AIV/MicroAPI 或 SIMT body；官方固定 Commit 仅提供 Cummin/950 相关映射和基线来源，本文 Direct 扩展 Route 事实均明确归于转换交付件 |

## 接口与语义

### 计算语义

令标准化后的 `dim=(dim+rank)%rank`，`M=∏dims[0:dim]`、`R=dims[dim]`、`N=∏dims[dim+1:rank]`。连续地址为 `p(m,r,n)=m*R*N+r*N+n`。对每个固定 `(m,n)`：

```text
values[p(m,r,n)]  = input[p(m,k,n)]，其中 k 是 [0,r] 上按实现比较规则选出的前缀最小位置
indices[p(m,r,n)] = k
```

所有 Route 在相等值时都保留右侧/当前位置，即同值最小项取最新索引。R-005、R-007 和 R-006 用显式 NaN 状态使 NaN 保持优先且同样取最新 NaN；R-002/R-003/R-001 的普通模板未启用 `NAN_AWARE`，R-004 的基础 SIMT 也仅使用标量 `<`，其 NaN 行为不能外推为 R-007 的粘滞语义。

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| `input` | rank>=1，连续 ND | `float16/float32/bfloat16/int32` | Direct 实现显式拒绝非连续输入和其它 dtype |
| `dim` | 标量属性 | `int64` | `-rank <= dim < rank`；负值按模归一化 |
| `values` | 与 `input` 相同 | 与 `input` 相同 | `empty_like(input)` 分配，写入 inclusive prefix minimum |
| `indices` | 与 `input` 相同 | `int64` | `empty(...dtype=torch::kInt64)` 分配；Vector 路线在 UB 内先形成 `int32` 索引再 cast 为 `int64` |

### 入口与版本

转换交付件通过 `TORCH_LIBRARY_FRAGMENT(cann_bench)` 声明 `cummin`，Meta 实现只负责 rank/dim 校验和输出元数据，`TORCH_LIBRARY_IMPL(cann_bench, PrivateUse1)` 绑定 `cummin_npu`。`cummin_npu` 取得当前 NPU stream，生成 `CumminLaunchConfig`，再按输入 dtype 精确分发到四个 `launch_cummin_*` 符号；它不是 ACLNN 两段式入口。官方固定 Commit 的 `math/cummin` 只作为同名算子、950 与基线 Tiling/Kernel 的相关映射；转换交付件新增的 key、SIMT warp/segment body、三 Kernel 图和 Direct ABI 不归因于官方公开接口。

## Host/Launcher 执行流程

### 参数校验与前处理

调用顺序为：Meta 检查 `rank>=1` 与 dim 范围→PrivateUse1 检查 contiguous 与四种 dtype→安装输入 device guard→按输入 shape 分配 `values` 和 `int64 indices`→取得当前 stream→`calc_cummin_tiling(input.sizes().data(), rank, dim, input.element_size(), 8)`。Tiling 再校验 rank/dim，归一化 dim、合轴成 `M/R/N`，从 `PlatformAscendCManager` 查询 AIV core 数和 UB 字节；查询结果非正时抛异常。没有 Contiguous/ViewCopy 隐式修复，非连续输入直接失败。

### 参数、Workspace 与生命周期

设输入元素字节 `d∈{2,4}`、索引字节 `a=8`、硬件 UB 为 `UB_hw`、AIV 核数为 `C`：

```text
P = ceil(32 / d)
A = ceil_align(N, P)
U = floor(((UB_hw - 4096) / (1 + a/d)) / 32) * 32  # config.localMemorySize，字节
```

`input/values/indices` 由 PyTorch Tensor 拥有，lambda 捕获其地址、config 与 stream，并在 `OpCommand::RunOpApi("CumminDirect", acl_call)` 中提交。所有 Kernel 都直接读写这三个 GM 地址；独立 workspace 大小为 0。R-006 的 `values/indices` 在三节点之间兼作中间存储并持续存活到调用返回。`config.localMemorySize` 被 producer 填写，但 `<<<config.blockDim, nullptr, stream>>>` 启动表达式未显式消费该字段，这是 Direct launcher 的源码可见边界。

### 启动图与失败传播

```text
cann_bench::cummin / PrivateUse1
  -> cummin_npu
    -> calc_cummin_tiling
    -> launch_cummin_<dtype>(x, y, argmin, config, stream)
      -> R-005: one AIV wrapper / SIMT warp-row entry
      -> R-002: one AIV vector ComputeR entry
      -> R-003: one AIV vector ComputeN entry
      -> R-007: one AIV vector NaN-aware entry
      -> R-006:
           cummin_k6_scan_<dtype>(blockDim, stream)
        -> y/argmin GM edge, same-stream ordering
           cummin_k6_summary_<dtype>(min(M,blockDim), stream)
        -> y/argmin GM edge, same-stream ordering
           cummin_k6_apply_<dtype>(blockDim, stream)
      -> R-001: one AIV vector ComputeM entry
      -> R-004: one AIV wrapper / SIMT lane entry; router default shares this body
```

单 Kernel 节点均传同一 `CumminRegbaseTilingData` 值对象，无 workspace slice。R-006 节点 1 生成每个 1024 元素 segment 的局部前缀；节点 2 只在各 segment 尾位置原位写跨 segment 前缀摘要；节点 3 读取前一 segment 尾摘要并原位修正后续 segment。三个 launch 使用同一 stream，代码依赖 stream 提交顺序形成 GM 可见性。launcher 与各 `launch_cummin_*` 返回 `void`，`acl_call` 无条件返回 0；源码未提供逐 launch 返回码检查或中途 cleanup 分支。

## Route 与参数设计

### 分核与资源计算

基础 selector 先计算 `q=(U/d-A)/(A*R)`。若 `q>=1`，按 M 切片：`computeM=q`、`splitM=ceil(mRowsPerCore/computeM)`、`ReservedM=mRowsPerCore%computeM`。否则设 `L=ceil_align(N*d,32)`、`ubLines=(U-L)/L`：`ubLines>=2` 时按 R 切片，`computeR=(U-L)/L`；否则按 N 切片，`computeN=floor_align(U/2,256)/d`。`mRowsPerCore=floor(M/C)`，`reservedRows=M%C`。有剩余行时，`A*d<=256` 令剩余处理核数 `Cr=reservedRows`，否则 `Cr=floor(C/reservedRows)*reservedRows`；每行分到 `G=Cr/reservedRows` 个核，并以 former/tail 长度切 N。基础 `blockDim` 为 `mRowsPerCore>0 ? C : Cr`。后续特殊 selector 可把 key 和 blockDim 覆盖为 SIMT/NaN 路线。

### Route 选择

#### Route 特征与重要性

P0 为最高重要性，后续等级依次降低。该顺序只组织实现知识，不改变 Host selector 的真实控制流。

| 重要性 | Route | 路线特征 | 适用域 | 实现前提 |
|---:|---|---|---|---|
| P0 | R-005 | 一个 warp 连续扫描一行，以 shuffle 在 32 元素 chunk 内传播前缀状态 | `N==1` 且行数足以支撑 warp-row 分核的连续行 | R-007 短路未命中；`M>=256`；SIMT warp/shuffle 可用 |
| P1 | R-002 | 完整 N 驻留 UB，沿 R 分批并跨批保留 value/index carry | RN 无法全载，但 UB 仍可容纳 carry 和至少两行 N | 基础 Route 判定为 N 全载；后续特殊 override 全部未命中 |
| P2 | R-003 | 以 256B 向量粒度切 N，每个 N 片内顺序扫描 R | 单行 N 也无法按 R 分批所需的层级驻留 | 基础 Route 判定 `ubLines<2`；`computeN>0`；特殊 override 全部未命中 |
| P3 | R-007 | 在 R 分批扫描中显式传播 NaN mask，保持 sticky NaN 状态 | 大 N、短 R 的连续 `[M,R,N]` 前缀扫描 | `N>=4096 && R<=32`；`generalProcessInfo` 必须已按 R/N 分片语义生成 |
| P4 | R-006 | 将少量超长行切为 segment，用 scan→summary→apply 三节点合并 carry | `N==1`、行数较少且 R 足够长 | R-007/R-005 短路未命中；`R>=8192`；三节点同 stream 有序提交 |
| P5 | R-001 | 在 UB 中一次容纳一批 M 行的 R×alignedN，逐行完成 R 扫描 | RN 工作集可全载的小 R/N 域 | `q>=1`；`computeM>0`；特殊 override 全部未命中 |
| P6 | R-004 | 一个 SIMT lane 处理一个 `(m,n)` 并串行扫描 R；同时承担 launcher 未知 key fallback | 大 M、小 N、中等 R 的 lane 并行域 | 预选条件 `N<128 && M>12800 && R<12800`；特殊 override 未命中；或 router 落入 `default` |

#### Host selector 顺序与短路

Route 重要性不改变 Host 的真实判定次序。下表按重要性排列，`Host 顺序` 则完整记录各 Route 在 selector 中的生成、覆盖、短路和 fallback 位置。

| 重要性 | Route | Key/模板 | Host 顺序 | 未命中或 fallback 去向 |
|---:|---|---|---|---|
| P0 | R-005 warp-row SIMT | key 5，`RunWarpRowScan<X>` | ④ `if (N>=4096 && R<=32)` 未命中后进入第一个 `else if`；`N==1 && M>=256` 命中后覆盖 R-004 预选或 R-001/002/003 基础 Route，并短路 R-006 | 条件 false 时继续⑤ R-006 |
| P1 | R-002 N 全载、R 分片 | key 1，`ComputeR` | ① RN 不可全载后执行 `DoUBSlice`，`ubLines>=2` 生成基础 key 1；② R-004 可覆盖；③–⑤ R-007/R-005/R-006 可覆盖 | ②–⑤ 全部未命中时保留 key 1；`ubLines<2` 则基础 Route 为 R-003 |
| P2 | R-003 N 分片 | key 2，`ComputeN` | ① RN 不可全载后执行 `DoUBSlice`，`ubLines<2` 生成基础 key 2；② R-004 可覆盖；③–⑤ R-007/R-005/R-006 可覆盖 | ②–⑤ 全部未命中时保留 key 2；无更低基础 Route |
| P3 | R-007 NaN-aware 寄存器扫描 | key 8，`Cummin<X,int64_t,true>` | ③ R-004 预选之后执行独立 `if`；`N>=4096 && R<=32` 命中后覆盖当前 Route，并使后续 `else if` 链短路 | 条件 false 时进入④ R-005 |
| P4 | R-006 segmented-row SIMT | key 6，三节点 `RunSegment*` | ⑤ 仅在 R-007 与 R-005 均未命中时进入第二个 `else if`；`N==1 && R>=8192` 命中后覆盖 R-004 预选或基础 Route | 条件 false 时保留 R-004 预选或 R-001/002/003 基础 Route |
| P5 | R-001 RN 全载 | key 0，`ComputeM` | ① `q>=1` 生成基础 key 0；② R-004 可覆盖；③–⑤ R-007/R-005/R-006 可覆盖 | `q<1` 时进入 R-002/R-003 基础分支；②–⑤ 全部未命中时才保留 key 0 |
| P6 | R-004 lane-SIMT | key 3，`SimtCompute<X,int64_t>` | ② 基础 Route 生成后执行预选 `if (N<128 && M>12800 && R<12800)`；③–⑤ 任一特殊 Route 命中都会覆盖它；launcher `switch default` 也进入 R-004 body | ③–⑤ 全部未命中时保留 key 3；预选 false 时保留基础 Route |

```text
baseKey = (q >= 1) ? 0 : ((ubLines >= 2) ? 1 : 2)
key = (N < 128 && M > 12800 && R < 12800) ? 3 : baseKey
if (N >= 4096 && R <= 32) key = 8
else if (N == 1 && M >= 256) key = 5
else if (N == 1 && R >= 8192) key = 6
```

### 模板/实现执行矩阵

| 重要性 | Route | key/selector | dtype/shape/platform 完整命中条件 | 执行拓扑与 Kernel 节点 | 实际模板/body | 内存与同步特征 | tail/fallback |
|---:|---|---|---|---|---|---|---|
| P0 | R-005 | 5 | `N==1,M>=256`（在 key8 后） | 单 AIV wrapper→至多 64 warps/core | `RunWarpRowScan`→`WarpRowScan/WarpScanChunk` | GM+warp shuffle+carry 寄存器 | 32 元素 full chunk + masked tail |
| P1 | R-002 | 1 | 特殊条件均 false，`q<1,ubLines>=2` | 单 AIV Kernel | `ComputeR(generalProcessInfo)` + reserved-row R/N body | 同上，跨 R 分片保留 `tmpX/tmpArgmin` carry | `reservedR` 尾批 |
| P2 | R-003 | 2 | 特殊条件均 false，`q<1,ubLines<2` | 单 AIV Kernel | `ComputeN(generalProcessInfo)` + reserved-row R/N body | 同上，每个 N 片逐 R 扫描 | `reservedN` 与 MicroAPI mask |
| P3 | R-007 | 8 | `N>=4096,R<=32` | 单 AIV Kernel | `Cummin<X,int64_t,true>::ComputeR` + reserved-row body | R-002 资源图 + NaN mask 寄存器 | 依赖 `generalProcessInfo` 已有效生成 |
| P4 | R-006 | 6 | `N==1,M<256,R>=8192` | 三 AIV wrapper/SIMT Kernel | `SegmentScan`→`SegmentSummaryScan`→`SegmentApplyCarry` | y/indices 原位 GM 边，同 stream | 1024 segment、32-lane chunk、尾 segment |
| P5 | R-001 | 0 | 特殊条件均 false，`q>=1` | 单 AIV Kernel | `Cummin<X,int64_t,false>::ComputeM` + reserved-row R/N body | 四个 depth-1 TQue，MicroAPI，硬事件 | splitM 尾批；剩余 M 行再分 N |
| P6 | R-004 | 3/default | 特殊 override false，SIMT 谓词 true | 单 AIV wrapper→2048-thread SIMT | `SimtCompute<X,int64_t>` | 无 AIV UB 分配；GM+线程寄存器 | block 内 grid-stride `(m,n)` lane；unknown key 也进入此 body |

### 隐藏性能 Guard

| Guard | Host/Tiling 条件 | Device/资源原因 | 影响 Route | 不满足时去向 | 源码符号 |
|---|---|---|---|---|---|
| warp row | `N==1,M>=256` | 每个 warp 连续扫描一行，行数足以铺开 row 任务 | R-005 | R-006/基础 | `HostTiling::Run`、`RunWarpRowScan` |
| N 全载 | `(U-ceil_align(N*d,32))/ceil_align(N*d,32)>=2` | 一行 carry 外至少可装两行 R 数据 | R-002 | R-003 | `HostTiling::DoUBSlice` |
| vReg 对齐 | `computeN=floor_align(U/2,256)/d` | 两行 value/索引预算并使 tile 为 256B 向量粒度 | R-003 | 无进一步 fallback | `DoUBSliceForN` |
| NaN-aware override | `N>=4096 && R<=32` | 大 N、短 R 使用 MicroAPI lane 并显式维护 prior/current NaN mask | R-007 | R-005 等 | `HostTiling::Run`、`DoCompare<NAN_AWARE>` |
| segmented row | `N==1,M<256,R>=8192` | 少量超长连续行切成 1024 元素 segment，跨 Kernel 合并 carry | R-006 | 基础/SIMT | `HostTiling::Run`、`SEGMENT_SIZE` |
| UB 预留与索引折算 | `U=floor(((UB_hw-4096)/(1+8/d))/32)*32` | 同时为 value 与 int64 索引结果留空间并保持 32B 粒度 | R-002/003/007/001 | selector 计算其它分片 | `HostTiling::Run` |
| RN 全载 | `(U/d-A)/(A*R)>=1` | 至少容纳一批 M 行的 R×alignedN value 区和 carry | R-001 | R-002/003 | `HostTiling::Run/DoUBSliceForM` |
| unknown key | launcher `switch default` | 未识别 key 不报错而启动 key3 body | R-004 body | 无显式失败 | `LAUNCH_BY_KEY` |

### POD/ABI

`#pragma pack(push,8)` 且全部标量为 `int64_t`，因此 `sizeof(CumminSplitInfo)=72`、`alignof=8`，`sizeof(CumminRegbaseTilingData)=328`、`alignof=8`。下表 offset 均为相对外层结构起点的字节；`general/former/tail` 三个嵌套对象的字段 producer 均为同名 `DoUBSlice*`，未命中时保持 config 值初始化的 0。

| 结构 | 字段 | 类型/位宽 | ABI 布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| `CumminRegbaseTilingData` | `M` | int64/64 | off 0 | 行组 | shape 前轴乘积 | 全部 body | 乘法溢出未检查 |
| 同上 | `R` | int64/64 | off 8 | 元素/扫描轴 | `dims[dim]` | 全部 body | 需为正才可安全循环/取模 |
| 同上 | `N` | int64/64 | off 16 | 元素/内层跨度 | shape 后轴乘积 | 全部 body | 乘法溢出未检查 |
| 同上 | `mRowsPerCore` | int64/64 | off 24 | M 行/核 | `M/C` | AIV 主段循环 | SIMT body 不读 |
| 同上 | `formerCore` | int64/64 | off 32 | 核 | `N%G` | `Init` 剩余行映射 | `reservedRows==0` 时 inactive |
| 同上 | `tailCore` | int64/64 | off 40 | 核 | `Cr-formerCore` | 仅分类/记录；地址分支由 former 条件决定 | 同上 |
| 同上 | `formerCoreComputeLength` | int64/64 | off 48 | N 元素 | `N/G+1` | `Init` | 同上 |
| 同上 | `tailCoreComputeLength` | int64/64 | off 56 | N 元素 | `N/G` | `Init` | 同上 |
| 同上 | `coreNum` | int64/64 | off 64 | 核 | `Cr` | `Init/ComputeReservedM` | 仅有剩余行时赋值 |
| 同上 | `perGroupCoreNum` | int64/64 | off 72 | 核/剩余行 | `Cr/reservedRows` | `Init` 除法/取模 | 必须非零 |
| 同上 | `reservedRows` | int64/64 | off 80 | M 行 | `M%C` | `ComputeReservedM` guard | 0 表示无剩余段 |
| 同上 | `splitM` | int64/64 | off 88 | 批 | `ceil(mRowsPerCore/computeM)` | R-001 `ComputeM` | 其它主 Route inactive |
| 同上 | `computeM` | int64/64 | off 96 | M 行/批 | `q` | R-001 `ComputeM` | 必须非零 |
| 同上 | `ReservedM` | int64/64 | off 104 | M 行 | `mRowsPerCore%computeM` | R-001 尾批 | 0 表示无尾批 |
| `generalProcessInfo` | `isNFullyLoad` | int64/64 | off 112 | bool(0/1) | `DoUBSlice` | Route key 与 reserved body | key0 时未生产 |
| 同上 | `splitR` | int64/64 | off 120 | 批 | `ceil(R/computeR)` | `ComputeR` | N 分片时 inactive |
| 同上 | `reservedR` | int64/64 | off 128 | R 行 | `R%computeR` | `ComputeR` 尾批 | 同上 |
| 同上 | `computeR` | int64/64 | off 136 | R 行/批 | `(U-L)/L` | `ComputeR` | 必须非零 |
| 同上 | `splitN` | int64/64 | off 144 | 批 | `ceil(length/computeN)` | `ComputeN` | R 分片时 inactive |
| 同上 | `reservedN` | int64/64 | off 152 | N 元素 | `length%computeN` | `ComputeN` 尾片 | 同上 |
| 同上 | `computeN` | int64/64 | off 160 | N 元素/片 | `floor_align(U/2,256)/d` | `ComputeN` | 必须非零 |
| 同上 | `computeLength` | int64/64 | off 168 | N 元素 | N 或 computeN | `CopyIn/Out` | 按 `isNFullyLoad` 解释 |
| 同上 | `allocLength` | int64/64 | off 176 | N 元素 | 32B 对齐 N 或 computeN | `InitBuffers/DoCompare` | 按 dtype 对齐 |
| `formerCoreProcessInfo` | `isNFullyLoad` | int64/64 | off 184 | bool | former `DoUBSlice` | reserved body | 无剩余行时 inactive |
| 同上 | `splitR` | int64/64 | off 192 | 批 | former `DoUBSliceForR` | `ComputeR` | 按路线 inactive |
| 同上 | `reservedR` | int64/64 | off 200 | R 行 | 同上 | `ComputeR` | 同上 |
| 同上 | `computeR` | int64/64 | off 208 | R 行/批 | 同上 | `ComputeR` | 必须非零 |
| 同上 | `splitN` | int64/64 | off 216 | 批 | former `DoUBSliceForN` | `ComputeN` | 按路线 inactive |
| 同上 | `reservedN` | int64/64 | off 224 | N 元素 | 同上 | `ComputeN` | 同上 |
| 同上 | `computeN` | int64/64 | off 232 | N 元素/片 | 同上 | `ComputeN` | 必须非零 |
| 同上 | `computeLength` | int64/64 | off 240 | N 元素 | former 长度或 computeN | Copy methods | 必须匹配 GM stride |
| 同上 | `allocLength` | int64/64 | off 248 | N 元素 | 对齐后的 former 长度 | buffer/compare | 需满足 UB |
| `tailCoreProcessInfo` | `isNFullyLoad` | int64/64 | off 256 | bool | tail `DoUBSlice` | reserved body | 无剩余行时 inactive |
| 同上 | `splitR` | int64/64 | off 264 | 批 | tail `DoUBSliceForR` | `ComputeR` | 按路线 inactive |
| 同上 | `reservedR` | int64/64 | off 272 | R 行 | 同上 | `ComputeR` | 同上 |
| 同上 | `computeR` | int64/64 | off 280 | R 行/批 | 同上 | `ComputeR` | 必须非零 |
| 同上 | `splitN` | int64/64 | off 288 | 批 | tail `DoUBSliceForN` | `ComputeN` | 按路线 inactive |
| 同上 | `reservedN` | int64/64 | off 296 | N 元素 | 同上 | `ComputeN` | 同上 |
| 同上 | `computeN` | int64/64 | off 304 | N 元素/片 | 同上 | `ComputeN` | 必须非零 |
| 同上 | `computeLength` | int64/64 | off 312 | N 元素 | tail 长度或 computeN | Copy methods | 必须匹配 GM stride |
| 同上 | `allocLength` | int64/64 | off 320 | N 元素 | 对齐后的 tail 长度 | buffer/compare | 需满足 UB |

`CumminLaunchConfig` 在 Host C++ ABI 中顺序为 328B tiling、`uint32 blockDim`、随后 8B 对齐的 `uint64 tilingKey/localMemorySize`；按常规 8B 对齐推导 `sizeof=352`、`alignof=8`、offset 分别为 0/328/336/344。该结构不跨 Device 序列化，Kernel 只按值接收其中的 328B tiling POD。

### Route 源码闭包

| 重要性 | Route | Key/selector | Host/Tiling producer | POD/参数 | Kernel entry/router 节点 | Kernel body/直接依赖 | 构建接线 |
|---:|---|---|---|---|---|---|---|
| P0 | R-005 | 5 | `HostTiling::Run` | M/R、blockDim | `cummin_k5_*` | `RunWarpRowScan/WarpRowScan/WarpScanChunk` | `cummin/CMakeLists.txt`→`register_direct_launch_op` |
| P1 | R-002 | 1 | `HostTiling::Run/DoUBSliceForR` | general + former/tail info | `cummin_k1_*` | `ComputeR/ComputeReservedM/DoCompare` | 同上 |
| P2 | R-003 | 2 | `HostTiling::Run/DoUBSliceForN` | general + former/tail info | `cummin_k2_*` | `ComputeN/ComputeReservedM/DoCompare` | 同上 |
| P3 | R-007 | 8 | `HostTiling::Run` | general + former/tail info | `cummin_k8_*` | `Cummin<X,int64,true>::ComputeR/DoCompare` | 同上 |
| P4 | R-006 | 6 | `HostTiling::Run/launch_segmented_*` | M/R、两种 blockDim | `cummin_k6_scan/summary/apply_*` | 三个 `RunSegment*` 与 SIMT body | 同上 |
| P5 | R-001 | 0 | 转换件 `cummin_kernel.cpp::HostTiling::Run` | `CumminRegbaseTilingData` | `cummin_k0_*` | `cummin.h::ComputeM/ComputeReservedM/DoCompare` | 同上 |
| P6 | R-004 | 3/default | `HostTiling::Run` | M/R/N、blockDim | `cummin_k3_*` | `InitForSimT/SimtCompute` | 同上 |

## Kernel 实现

### 公共执行流程

下列逐 Route 章节严格按 P0→P6 排列，R-ID 保持不变；该章节顺序不是 Host selector 顺序。四个 dtype launcher 共用 `LAUNCH_BY_KEY`，只改变 entry 后缀与模板 `X`。所有 entry 标注 `KERNEL_TYPE_AIV_ONLY`；Vector Route 由 AIV 直接执行 DMA、硬事件和 MicroAPI，SIMT Route 则从 AIV wrapper 通过 `asc_vf_call` 启动 SIMT 线程函数。基础 AIV Route 先处理每核的 `mRowsPerCore` 连续主段，再 `TPipe::Reset`，把 `reservedRows` 的每一行沿 N 分给一组核处理。索引在 Vector UB 中用 `int32` 计算，输出前在同一 argmin buffer 内 cast 为 `int64`；SIMT Route 直接写 `int64` GM。所有地址都基于 `[M,R,N]` 连续布局，无 workspace 或跨核 Atomic。

### Route P0 · R-005：warp-row SIMT

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Launcher | 转换件 `cummin_kernel.cpp` | `HostTiling::Run` | `N==1 && M>=256` | key5，blockDim=C |
| Router | 同文件 | `LAUNCH_BY_KEY` | `switch` 的 `WARP_ROW_SIMT` 分支 | `cummin_k5_*` |

#### Device 数据流

##### 函数级调用链

```text
cummin_k5_X -> RunWarpRowScan<X>
  -> asc_vf_call<WarpRowScan<X>>(warpsPerCore*32)
    -> WarpScanChunk<full/tail,carry>
```

##### 源码等价伪码

```text
warp maps to row = coreId + warpId*coreCount; rowStride=coreCount*warpsPerCore
for each 32-element chunk:
  each lane loads one r; pack NaN into sign bit of int32 state for floating X
  Sklansky-like shfl_up deltas 1,2,4,8,16 combine left prefix into right
  combine previous chunk carry; store X and masked int64 index
  broadcast last active lane as next carry
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM row | `row*R+chunk+lane` | one row | X/int64 | input | warp | Tensor | N=1 contiguous |
| warp registers | lane-local | value/state + carry | C/int32 | load/shuffle | store/next chunk | warp | BF16 C=float；其余 C=X |

##### 分层内存布局

N/A：无 AIV UB/shared allocation，32-lane warp 寄存器和 shuffle 构成前缀网络。

##### 字节账与复用顺序

```text
UB_total=N/A; dynamic_ub=N/A; workspace_total=0
threadsPerBlock=min(ceil(M/C),64)*32
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| carry registers | chunk last active lane | next chunk | next row | warp shuffle/program order | 同一 warp 串行处理 chunks |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| warp prefix | `WarpShflUpSync/ShflSync` | left lane | right lane/next chunk | warp registers | full chunk 模板消除边界分支；tail 用 active guard |
| state | sign-bit NaN flag | load | combine/store | index state | float族 NaN sticky；输出掩掉 flag；ties 留右侧 |
| BF16 | cast to float | GM load | compare/store | value register | BF16 路线用 FP32 比较后降回 BF16 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | 转换件 `cummin_kernel.cpp` | `Run` | key5、C blocks |
| Kernel entry/router | 同上 | `cummin_k5_*` | dtype wrapper |
| Device body/helper | 转换件 `cummin_parallel_scan.h` | `RunWarpRowScan/WarpRowScan/WarpScanChunk` | warp 映射、shuffle、carry、tail |

### Route P1 · R-002：N 全载、R 分片

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Launcher | 转换件 `cummin_kernel.cpp` | `Run/DoUBSlice` | `q<1 && ubLines>=2` 且无特殊 override | key1 |
| Router | 同文件 | `LAUNCH_BY_KEY` | `switch` 的 `N_FULLY_LOAD` 分支 | `cummin_k1_*` |

#### Device 数据流

##### 函数级调用链

```text
cummin_k1_X -> Init -> ComputeR(generalProcessInfo)
  -> InitBuffers -> per M row/per R batch: CopyIn -> DoCompare -> CopyOut
  -> ComputeReservedM -> ComputeR or ComputeN
```

##### 源码等价伪码

```text
for local m row:
  for rBatch in [0,splitR):
    rows = tail ? reservedR : computeR
    DMA rows x N
    if first batch: initialize carry from r=0 and argmin=0
    scan rows, duplicate index uses rBatch*computeR + local_r
    output this R batch; retain tmpX/tmpArgmin carry for next batch
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM slice | `i*R*N+j*computeR*N` | `rows*N` | `[Rpart,N]` | x | y/argmin | Tensor | stride 0 主段 |
| carry queues | UB | `B*d + ceil_align(B,256/d)*4` | X/int32 | first/previous batch | next batch | TPipe | B=`allocLength` |
| y/argmin queues | UB | `B*Q*d + B*Q*8` | X/int32→int64 | CopyIn/compare | CopyOut | TPipe | Q=`computeR` |

##### 分层内存布局

```mermaid
block-beta
  columns 4
  xCarry["xTmp · B*d"]:1
  iCarry["iTmp · ceil_align(B,256/d)*4"]:1
  yTile["y · B*computeR*d"]:1
  iTile["idx · B*computeR*8"]:1
```

##### 字节账与复用顺序

```text
B=allocLength; Q=computeR
UB_total=B*d+ceil_align(B,256/d)*4+B*Q*d+B*Q*8
dynamic_ub=N/A; workspace_total=0
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| tmp carry | first/previous R batch | next `DoCompare` | 下一 M 行初始化 | VEC 顺序 | batch 顺序不可交换 |
| argminQue | compare | Cast+DMA | 下一 batch | 硬事件 | int32→int64 原位转换完成 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| R batch load | DataCopyPad+events | GM | compare | yTile | `reservedR` 改 rows |
| compare | MicroAPI strict LT | carry/current | output/carry | prefix state | ties 取当前；普通模板不启用 NaN-aware |
| store | Cast+DataCopyPad | int32 indices | int64 GM | output tile | valid N only |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | 转换件 `cummin_kernel.cpp` | `DoUBSliceForR` | computeR/splitR/reservedR |
| Kernel entry/router | 同上 | `cummin_k1_*` | key1→body |
| Device body/helper | 转换件 `cummin.h` | `ComputeR/DoCompare` | 跨批 carry 与有效 N 输出 |

### Route P2 · R-003：N 分片

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Launcher | 转换件 `cummin_kernel.cpp` | `Run/DoUBSliceForN` | `q<1 && ubLines<2` 且无特殊 override | key2 |
| Router | 同文件 | `LAUNCH_BY_KEY` | `switch` 的 `N_NOT_FULLY_LOAD` 分支 | `cummin_k2_*` |

#### Device 数据流

##### 函数级调用链

```text
cummin_k2_X -> Init -> ComputeN
  -> InitBuffers -> per M row/per N tile/per r: CopyIn -> DoCompare -> CopyOut
  -> ComputeReservedM -> ComputeR or ComputeN
```

##### 源码等价伪码

```text
for local m, for N tile:
  length = tail ? reservedN : computeN
  r=0: load into carry, zero indices, immediately output
  for r=1..R-1:
    load one current N tile; compare with carry; output updated carry/index
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM tile | `i*R*N+j*computeN+k*N` | `length` | contiguous N slice | x | y/i | Tensor | final tile guarded by length |
| x/i carry | UB | `B*d + ceil_align(B,256/d)*4` | X/int32 | r=0/previous r | next r | TPipe | B=computeN |
| current/output | UB | `B*d + B*8` | X/int32→int64 | current r | output | TPipe | Q=1 |

##### 分层内存布局

```mermaid
block-beta
  columns 4
  xCarry["xTmp · B*d"]:1
  iCarry["iTmp · ceil_align(B,256/d)*4"]:1
  current["y · B*d"]:1
  indices["idx · B*8"]:1
```

##### 字节账与复用顺序

```text
B=computeN; Q=1
UB_total=B*d+ceil_align(B,256/d)*4+B*d+B*8
dynamic_ub=N/A; workspace_total=0
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| xTmp/iTmp | r=0或 compare | 下一 r | 下一 N tile | VEC 顺序 | 当前 tile 的全部 R 完成 |
| yTensor | CopyIn current | DoCompare | 下一 r | MTE2_V | carry 已写回 xTmp |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| N tile | `UpdateMask` | length | MicroAPI | 尾 lane | `reservedN` 改 repeat/mask |
| prefix | strict LT+Select | carry/current | stores | values/index | ties 取当前，原 dtype |
| output | events+Pad copy | UB | GM | valid length | 不写 padded lane |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | 转换件 `cummin_kernel.cpp` | `DoUBSliceForN` | 256B 对齐 computeN |
| Kernel entry/router | 同上 | `cummin_k2_*` | key2→body |
| Device body/helper | 转换件 `cummin.h` | `ComputeN/DoCompare` | N-tail、逐 R carry |

### Route P3 · R-007：NaN-aware 寄存器扫描

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Launcher | 转换件 `cummin_kernel.cpp` | `HostTiling::Run` | `N>=4096 && R<=32`，最高 override | key8，blockDim=C |
| Router | 同文件 | `LAUNCH_BY_KEY` | `switch` 的 `NAN_AWARE_REG` 分支 | `cummin_k8_*` |

#### Device 数据流

##### 函数级调用链

```text
cummin_k8_X -> Cummin<X,int64,true>::Init
  -> ComputeR(generalProcessInfo) -> DoCompare<NAN_AWARE>
  -> ComputeReservedM
```

##### 源码等价伪码

```text
same R-batched flow as R-002
cmp = prior < current
priorNan = prior != prior; currentNan = current != current
retainPrior = (priorNan OR cmp) AND NOT(currentNan)
Select(retainPrior ? prior : current); update value/index carry
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM/UB queues | 同 R-002 | `B*d+align(B)*4+B*Q*d+B*Q*8` | X/int32→int64 | Copy/compare | output | Tensor/TPipe | B=general allocLength，Q=computeR |
| mask registers | per vReg | cmp/priorNan/currentNan/notNan/retain | bit mask | Compare/Mask ops | Select | VEC scope | int32 路线 NaN compare恒 false |

##### 分层内存布局

```mermaid
block-beta
  columns 4
  xCarry["xTmp · B*d"]:1
  iCarry["iTmp · ceil_align(B,256/d)*4"]:1
  yTile["y · B*computeR*d"]:1
  iTile["idx · B*computeR*8"]:1
```

##### 字节账与复用顺序

```text
UB_total=B*d+ceil_align(B,256/d)*4+B*computeR*d+B*computeR*8
dynamic_ub=N/A; workspace_total=0
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| carry queues | prior R batch | next batch | next M row | VEC order | generalProcessInfo 有效 |
| mask regs | current vReg | Select | next vReg | VEC scope | tail mask 同步更新 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| DMA | 同 R-002 硬事件 | GM/UB | VEC/MTE3 | queues | N/tail mask |
| NaN | `Compare NE(x,x)`+Mask ops | values | Select | prefix state | current NaN 胜出；prior NaN 对非 NaN 保持；同为 NaN 取当前 |
| dtype | MicroAPI X | load | store | value | 无升精度；int32 不产生 NaN |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | 转换件 `cummin_kernel.cpp` | `Run` | key8 override、C blocks |
| Kernel entry/router | 同上 | `cummin_k8_*` | `NAN_AWARE=true` |
| Device body/helper | 转换件 `cummin.h` | `ComputeR/DoCompare<true>` | NaN mask 网络、R carry |
### Route P4 · R-006：segmented-row 三 Kernel SIMT

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Launcher | 转换件 `cummin_kernel.cpp` | `HostTiling::Run` | key8/key5 未命中，`N==1 && R>=8192`，等价含 `M<256` | key6，blockDim=C |
| Router | 同文件 | `launch_segmented_*` | `switch` 的 `SEGMENTED_ROW_SIMT` 分支 | scan→summary→apply |

#### Device 数据流

##### 函数级调用链

```text
cummin_k6_scan_X -> RunSegmentScan -> SegmentScan
  -> same-stream y/indices GM edge
cummin_k6_summary_X -> RunSegmentSummaryScan -> SegmentSummaryScan
  -> same-stream y/indices GM edge
cummin_k6_apply_X -> RunSegmentApplyCarry -> SegmentApplyCarry
```

##### 源码等价伪码

```text
node1: each warp owns (row,segment); scan 1024-element segment in 32-lane chunks and write local prefixes
node2: each warp owns row; scan segment-end summaries in chunks of 32 and overwrite each segment endpoint with global segment prefix
node3: each thread grid-strides over M*R; for segment>0 combine value/index with previous segment endpoint carry
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| node1 y/i | `row*R+r` | M*R | X/int64 | SegmentScan | node2/node3 | output Tensor | segment-local prefix |
| segment endpoint | `row*R+min((s+1)*1024,R)-1` | ceil(R/1024) per row | X/int64 | node1→node2 | node3 carry | output Tensor | node2 原位覆盖 |
| node3 carry edge | `rowBase+segment*1024-1` | one pair per element | X/int64 | node2 | node3 | output Tensor | same stream |
| SIMT registers | per lane/thread | values/state/carry | C/int32 | each node | same node | invocation | no UB/shared/workspace |

##### 分层内存布局

```text
output GM y      : [segment-local prefixes] -> [segment endpoints carry-corrected] -> [all prefixes corrected]
output GM indices: same three-phase lifetime
UB/shared        : N/A
```

##### 字节账与复用顺序

```text
UB_total=N/A; dynamic_ub=N/A; workspace_total=0
node1 threads=min(ceil(M*ceil(R/1024)/C),64)*32
node2 threads=min(ceil(M/min(M,C)),64)*32
node3 threads=2048
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| y/i 全输出 | node1 | node2/node3 | node2 endpoint、node3 elements | 同 stream launch 顺序 | 不得把三节点放到无依赖 stream |
| segment endpoint | node2 | node3 | node3不改前一 endpoint之外的读取顺序 | node2 完成可见 | endpoint 必须先汇总 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| node edge | same stream | prior Kernel GM stores | next Kernel loads | y/indices | 无 event/workspace |
| intra-warp | shuffle | lane | lane/carry | registers | 32-lane tail active guard |
| segment | 1024 constant | node1 | node2/node3 | row partition | 最后一 segment 取 min(end,R) |
| state | packed NaN | loads | combines | int32 state | BF16 以 FP32 比较；float族 NaN sticky；ties 取右 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | 转换件 `cummin_kernel.cpp` | `Run/launch_segmented_*` | key6、三次同 stream launch、两种 blockDim |
| Kernel entry/router | 同上 | `cummin_k6_scan/summary/apply_*` | 三个 AIV-only wrapper |
| Device body/helper | 转换件 `cummin_parallel_scan.h` | 三个 `RunSegment*`/SIMT body | segment/summary/apply 地址、shuffle、carry |

### Route P5 · R-001：RN 全载

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Launcher | 转换件 `csrc/ops/cummin/op_kernel/cummin_kernel.cpp` | `HostTiling::Run` | `q>=1`，且后续 key3/8/5/6 均不命中 | key 0 |
| Router | 同文件 | `LAUNCH_BY_KEY` | `switch` 的 `RN_FULLY_LOAD` 分支 | `cummin_k0_<dtype>` |

#### Device 数据流

##### 函数级调用链

```text
cummin_k0_X(x,y,argmin,td)
  -> Cummin<X,int64,false>::Init
  -> ComputeM -> InitBuffers -> CopyIn -> DoCompare -> CopyOut
  -> ComputeReservedM -> TPipe::Reset -> ComputeR or ComputeN
```

##### 源码等价伪码

```text
for mBatch in [0, splitM):
  rows = tail ? ReservedM : computeM
  DMA rows*R blocks of N values into yTensor[rows,R,alignedN]
  for each local m row:
    tmpX = r=0 values; tmpArgmin = 0
    for r=1..R-1: mask-wise choose prior iff prior < current, else current/r
  DMA valid N values and casted int64 indices back
reset pipe; if reservedRows and this block belongs to Cr: scan its N slice via R- or N-sliced body
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM x/y/i | `blockId*mRowsPerCore*R*N + batch*computeM*R*N` | `rows*R*N` | X/X/int64, `[rows,R,N]` | Host Tensor/Kernel | CopyIn/CopyOut | Tensor | N 有效，UB stride 为 alignedN |
| `xTmpQue` | UB allocator | `B*d` | X | first R row | DoCompare carry | TPipe，整个批 | depth 1 |
| `argminTmpQue` | UB allocator | `ceil_align(B,256/d)*4` | int32 | zero/compare | DoCompare carry | TPipe | depth 1 |
| `yQue` | UB allocator | `B*Q*d` | X | CopyIn | compare/CopyOut | TPipe | `B=A,Q=computeM*R` |
| `argminQue` | UB allocator | `B*Q*8` | int32 source + int64 cast dst | compare/Cast | CopyOut | TPipe | 同一物理区后半写 int32、全区写 int64 |

##### 分层内存布局

```mermaid
block-beta
  columns 4
  xCarry["xTmpQue · depth=1 · B*d"]:1
  iCarry["argminTmpQue · depth=1 · ceil_align(B,256/d)*4"]:1
  values["yQue · depth=1 · B*Q*d"]:1
  indices["argminQue · depth=1 · B*Q*8"]:1
```

##### 字节账与复用顺序

```text
B=A; Q=computeM*R
UB_total = B*d + ceil_align(B,256/d)*4 + B*Q*d + B*Q*8
dynamic_ub = N/A
workspace_total = 0
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| argminQue 后半→全区 | `DoCompare` int32 | `Cast` | 下一批 CopyOut 后 | `V_MTE3/MTE3_V` | castOffset=`B*Q`，cast 完成后才 DMA |
| tmp carry | 每个 m 行初始化 | 后续 R compare | 下一 m 行 | VEC 顺序 | 一行 R 扫描结束 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| GM→UB | `MTE3_MTE2`,`MTE2_V` | 前次输出/DMA | MicroAPI | yTensor | `DataCopyPad` 仅有效 N 字节 |
| compare | MicroAPI mask | yTensor/carry | stores | value/index lanes | X 原精度比较；最后 vReg 用 `UpdateMask` |
| UB→GM | `V_MTE3`,`MTE3_MTE2`,`MTE3_V` | compare/cast | DMA/下批 | y/argmin buffer | 只提交 `rows*R*N` 有效元素 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | 转换件 `cummin_kernel.cpp` | `HostTiling::Run/DoUBSliceForM` | key0、computeM/splitM |
| Kernel entry/router | 同上 | `cummin_k0_*`/`LAUNCH_BY_KEY` | dtype entry 与单 Kernel launch |
| Device body/helper | 转换件 `cummin.h` | `ComputeM/DoCompare/ComputeReservedM` | 批循环、MicroAPI、尾 M 行 |

### Route P6 · R-004：lane-SIMT

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Launcher | 转换件 `cummin_kernel.cpp` | `HostTiling::Run` | `N<128,M>12800,R<12800`，且后续 8/5/6 未覆盖 | key3，blockDim=`min(M,C)` |
| Router | 同文件 | `LAUNCH_BY_KEY` | `default`（包括 key3） | `cummin_k3_*` |

#### Device 数据流

##### 函数级调用链

```text
cummin_k3_X -> InitForSimT -> asc_vf_call<SimtCompute<X,int64>>(2048 threads)
```

##### 源码等价伪码

```text
each AIV block owns floor/ceil M rows and rebases GM
thread logical lane b = threadIdx.x; stride=2048
while lane index maps inside local count:
  (m,n) from b; scan r=0..R-1 serially
  retain prior only when prior < current; otherwise write current/r
  b += 2048
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM lane | `(b/N)*R*N+(b%N)` from block-rebased base | R strided elements | X/int64 | input | SIMT thread | Tensor | stride N |
| thread registers | per thread | minVal/minIdx/counters | X/int64 | thread loads | thread stores | SIMT invocation | no shared/dynamic UB |

##### 分层内存布局

N/A：该 Route 未调用 `InitBuffer`，实际替代路径为每线程寄存器状态直接读写 GM。

##### 字节账与复用顺序

```text
UB_total=N/A; dynamic_ub=N/A; workspace_total=0
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| thread min state | 当前 r | 下一 r | 下一 lane | 单线程程序顺序 | 每个 (m,n) 仅由一个线程处理 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| lane scan | N/A，单线程顺序 | load | store | 独占 GM lane | 无 barrier/atomic；count guard |
| compare | scalar `<` | min/current | select | X/int64 | 原 dtype；NaN 无显式 sticky state |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | 转换件 `cummin_kernel.cpp` | `Run` | key3 与 blockDim |
| Kernel entry/router | 同上 | `cummin_k3_*` | default→SIMT body |
| Device body/helper | 转换件 `cummin.h` | `InitForSimT/SimtCompute` | 2048 线程与 lane 地址 |


## 算子特定优化

### Trick T-001：按 UB 可容纳层级在 M/R/N 三轴间切换

#### 触发与源码依据

- 适用 Route：R-002、R-003、R-001
- 触发条件：先判断 `q>=1`，不成立再以 `ubLines>=2` 区分 R 全载和 N 分片；转换 Direct Tiling 保留这一基线机制。
- Golden 来源：[`math/cummin/op_host/arch35/cummin_tiling.cpp:217-228`](https://gitcode.com/cann/ops-math/blob/c821871ee4bccb0c564a582d1b362072c356a88d/math/cummin/op_host/arch35/cummin_tiling.cpp#L217-L228)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
ubSize_ = (compileInfo_->ubSize - RESERVED_UB) / (1 + argminDSize_ / dSize_) / BLOCK_SIZE * BLOCK_SIZE;
tilingData_.mRowsPerCore = M / compileInfo_->coreNum;
if (Ops::Base::FloorDiv(ubSize_ / dSize_ - alignedN_, alignedN_ * R) >= 1) {
    tilingKey_ = 0;
    DoUBSliceForM(tilingData_.mRowsPerCore);
} else {
    DoUBSlice(tilingData_.generalProcessInfo, N);
    tilingKey_ = 2 - tilingData_.generalProcessInfo.isNFullyLoad;
}
```

#### 机制与设计原因

selector 先用 `(1+argminDSize/dSize)` 把 value 与索引共同计入可用 UB，再按 32B 对齐。RN 可装时一次搬入多 M 行，复用同一 carry 做 R 扫描；RN 不可装但能容纳至少两行时保持完整 N、沿 R 分批并跨批保留 carry；再不足时固定两行预算并沿 N 切片。它直接改变 DMA 粒度、循环嵌套和 UB 形状，而不是仅改变模板名字。

#### 迁移边界

- 适用：连续 `[M,R,N]` prefix scan，结果与索引同时驻留 UB。
- 前提：950 AIV、32B DMA 粒度、256B vReg 粒度、`computeM/computeR/computeN` 均为正。
- 失效：资源谓词变化时必须重算 Route 和全部 split/POD，不能只复用 key。

#### 错误做法

固定仓未提供可验证反例；但源码明确要求 value/index 联合预算，迁移时不得只按 value 字节估算 UB。

## 模板与实现对比

| 对比维度 | R-005 | R-002 | R-003 | R-007 | R-006 | R-001 | R-004 |
|---|---|---|---|---|---|---|---|
| 命中条件/优先级 | N=1且M>=256 | ubLines>=2 | ubLines<2 | 大N、短R优先覆盖 | N=1、少行、超长R | q>=1 后保留 | 大 M、小 N；特殊 Route 未覆盖 |
| 模板与 dtype | warp，BF16→FP32 | AIV X/int64 | 同 R-002 | AIV NAN_AWARE | 3×SIMT，BF16→FP32 | AIV X/int64 | 2048-thread |
| 循环与分核 | warp→row→chunk | 行→R批 | 行→N片→R | 同 R-002 | segment→summary→apply | M批→行→R | thread→(m,n)→R |
| Queue/TBuf/寄存器 | warp regs | 4 TQue+Reg | 同 R-002，Q=1 | 4 TQue+NaN masks | warp/thread regs | 4 TQue+Reg | thread regs |
| 内存总占用与复用 | 无 UB | B,Q=computeR | B=computeN,Q=1 | 同 R-002 | 输出 GM 原位交接 | B,Q=computeM*R | 无 UB |
| 搬运/计算 API | shuffle | Pad DMA+MicroAPI | 同 R-002 | MicroAPI Mask ops | shuffle+3 launches | Pad DMA+MicroAPI | scalar GM |
| 同步、精度与 tail | active lane | R tail | N tail | 硬事件+NaN mask | stream+segment tail | 硬事件/vReg mask | count guard |
| fallback/失败边界 | 条件不满足继续 | 资源不足→N | 无下一基础 Route | general info 必须有效 | 三节点不可重排 | 资源不足→R/N | unknown key也进入此 body |

## 平台差异

| 项目 | A2 | A3 | 950 |
|---|---|---|---|
| 支持状态 | 非本卡目标；未闭合 Direct Route | 非本卡目标；未闭合 Direct Route | 本卡目标，`platforms:["950"]`；相关官方映射含 Ascend 950 配置 |
| Host/Launcher | Direct 构建脚本含可选架构名，但本卡不扩展结论 | 同左 | `NPU_ARCH=ascend950` 映射 `--npu-arch=dav-3510`；运行时查询 AIV core/UB |
| Kernel/资源 | 未提取平台资源上限 | 未提取平台资源上限 | 全部可达 entry 为 AIV-only；Vector 与 SIMT/multi-Kernel Route 如上 |

## 限制与失败边界

- Direct 入口只接受 rank>=1、连续 ND、四种输入 dtype 和 int64 indices；不提供 ACLNN 的非连续输入修复、其它 dtype 或 int32 indices 变体。
- shape 乘积、`alignedN*R`、M/R/N 地址乘法和多处向 `uint16_t/uint32_t` 的 DMA 参数窄化没有显式溢出检查；零长度维度还可能使 compute/split/取模除数为 0。
- `Init` 在读取 `perGroupCoreNum` 的取模/除法前没有以 `reservedRows` 保护；当 Host 未生成剩余行分组字段时，源码缺少非零证明。
- R-007 覆盖 key8 后直接消费 `generalProcessInfo`，但该字段只在基础 selector 的 `q<1` 分支生成；源码未给出 `N>=4096,R<=32` 必然推出 `q<1` 的显式 guard。
- `config.localMemorySize` 被计算但 launch 未显式使用；实际可用 Local Memory 与 Host 预算一致性在固定 Direct 源码外不可见。
- `switch default` 把未知 key 当作 R-004，而不是报错；四个 launcher 为 void 且 `acl_call` 固定返回 0，逐 Kernel launch 失败传播不可见。
- SIMT 与 Vector Route 的 NaN 行为差异仅按源码记录，不作跨 Route 数值等价外推。

## 源码索引

### 链路索引

| 链路阶段 | 文件 | 关键符号 | 支撑内容 |
|---|---|---|---|
| 入口声明/约束 | 官方映射 `math/cummin/README.md` | Cummin 语义/950 | 同名算子语义和平台相关性 |
| 入口实现 | 转换交付件 `csrc/ops/cummin/op_plugin/cummin_plugin.cpp` | `cummin_meta/cummin_npu` | Direct schema、PrivateUse1、dtype launcher |
| Host/Tiling/Launcher | 转换交付件 `csrc/ops/cummin/op_kernel/cummin_kernel.cpp` | `HostTiling/calc_cummin_tiling/LAUNCH_BY_KEY` | Route producer、POD、blockDim、launch graph |
| Kernel entry/body | 转换交付件 `csrc/ops/cummin/op_kernel/cummin.h` | `Cummin/SimtCompute/DoCompare` | 基础 AIV 与 lane-SIMT |
| Kernel entry/body | 转换交付件 `csrc/ops/cummin/op_kernel/cummin_parallel_scan.h` | `RunWarpRowScan/RunSegment*` | warp 与三 Kernel SIMT body |
| 构建接线 | 转换交付件 `csrc/ops/cummin/CMakeLists.txt` | `register_direct_launch_op` | kernel/plugin 注册 |
| 构建接线 | 官方映射 `math/cummin/CMakeLists.txt` | `SUPPORT_COMPUTE_UNIT` | 固定 Commit 的 950 相关映射 |

官方 Frontmatter `sources` 锁定固定 Commit 的相关映射；上表中标为“转换交付件”的 Direct 文件是本卡实际技术事实源，不等同于官方公开源码，也不据此扩张官方接口声明。

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | 328B tiling POD 和四字段 LaunchConfig | pack=8、字段顺序/位宽、inactive 字段有效性 | `cummin_struct.h/cummin_launch.h` |
| 调用顺序 | schema→tiling→dtype launcher→key router | R-006 scan→summary→apply 顺序 | `cummin_plugin.cpp/cummin_kernel.cpp` |
| workspace/内存 | workspace=0；R-006 复用输出 GM | UB 四区字节公式、index 原位 cast、owner/lifetime | `InitBuffers/launch_segmented_*` |
| 同步 | AIV 硬事件；R-006 同 stream | 不得提前覆盖 carry 或跨 stream 无依赖启动 | `InsertSync/launch_segmented_*` |
| 精度与尾块 | strict-LT 决定 latest tie；warp packed NaN；vReg/segment tail | BF16 warp 的 FP32 compute、NaN Route 差异不可抹平 | `DoCompare/CombinePrefixPacked` |
| 失败边界 | rank/dim/dtype/contiguous/platform query | unknown-key default、void launch、零除与窄化边界 | `cummin_npu/calc_cummin_tiling/LAUNCH_BY_KEY` |

<!-- cannbot:related:start -->
## 相关

- [cummin 非末维 batch-inner 跨步扫描 banned](../../../../runbooks/performance/cummin_batch_inner_banned.md)（`related`）：把连续 ND 输入按 `dim` 展平为 `［M,R,N］`，对每个 `(m,n)` 沿 `r` 做 inclusive cumulative minimum，同时输出产生当前前缀最小值的位置。客观失败：batch-inner 相对 transpose 参照路线在大 dimSize case 退化 37-78×，整体评分相对 transpose 路线下降；仅 Case 14（dimSize 极小）约为 transpose 的 2×（唯一受益）。随即回退到 transpose 路线。性能卡针对同一 Cummin 前缀扫描任务给出必须排除的非末维替代路线，可用于审查搬运与 Tiling 改写是否引入实测退化。
- [半精度索引错位—拆分双 int32 掩码](../../../../runbooks/precision/b16_value_mask_must_split_for_two_int32_index_registers.md)（`related`）：索引在 Vector UB 中用 `int32` 计算，输出前在同一 argmin buffer 内 cast 为 `int64`；SIMT Route 直接写 `int64` GM。一个 256B 的 fp16/bf16 寄存器有 128 个 value lane，而一个 int32 寄存器只有 64 个 index lane，单个 int32 RegTensor 与单个未拆分 MaskReg 无法覆盖同一批 128 个逻辑元素。算子卡的低精度 value 与 int32 工作索引形成二比一 lane 宽度；精度卡给出双寄存器和双 mask 的具体实现与验证合同。
- [跨批首行漏比较—续批从 row 0 扫描](../../../../runbooks/precision/prefix_scan_continuation_batch_must_compare_first_row.md)（`related`）：RN 不可装但能容纳至少两行时保持完整 N、沿 R 分批并跨批保留 carry。续批沿用“row 0 是初始 carry”的首批约定，先用前批 carry 覆盖当前 `yTensor［0］` 再只扫描 `rows - 1` 行，导致续批首个真实输入永远未与 carry 比较。算子卡的 R 分批 carry 路线正是该错误的触发结构；精度卡给出的首批与续批不同起点可直接约束 Device 循环，并以跨批首行用例验证修复。
<!-- cannbot:related:end -->
