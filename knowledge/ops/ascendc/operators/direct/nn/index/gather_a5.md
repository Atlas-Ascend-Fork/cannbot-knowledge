---
type: Operator
title: "Gather A5 Direct Invoke 算子知识"
description: "说明 cann_bench::gather、gather_npu 与 launch_gather 在 A5 上的接口语义、Launcher 参数生成、Route 选择、单/多 Kernel 启动图与逐节点实现。"
tags: [task.implementation, task.lookup, topic.data_movement, topic.memory, topic.precision, topic.programming_model]
status: stable
verified:
  - by: process:ops-knowledge-route-priority
    at: "2026-08-25T20:47:20Z"
  - by: process:ops-knowledge-direct53-ingest
    at: "2026-08-25T20:03:11Z"
sources:
  - resource: "https://gitcode.com/cann/ops-nn/blob/ceb4536a2bd6fc99b85aec9d0fdcc0f470376292/index/gather_elements/README.md"
    role: header
  - resource: "https://gitcode.com/cann/ops-nn/blob/ceb4536a2bd6fc99b85aec9d0fdcc0f470376292/index/gather_elements/op_host/gather_elements_def.cpp"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-nn/blob/ceb4536a2bd6fc99b85aec9d0fdcc0f470376292/index/gather_elements/op_host/arch35/gather_elements_tiling_arch35.cpp"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-nn/blob/ceb4536a2bd6fc99b85aec9d0fdcc0f470376292/index/gather_elements/op_kernel/gather_elements_apt.cpp"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-nn/blob/ceb4536a2bd6fc99b85aec9d0fdcc0f470376292/index/gather_elements/op_kernel/arch35/gather_elements.h"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-nn/blob/ceb4536a2bd6fc99b85aec9d0fdcc0f470376292/index/gather_elements/op_kernel/arch35/gather_elements_full_load.h"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-nn/blob/ceb4536a2bd6fc99b85aec9d0fdcc0f470376292/index/gather_elements/op_host/config/ascend950/gather_elements_binary.json"
    role: implementation
created_at: "2026-08-24T19:32:06Z"
updated_at: "2026-08-25T20:47:20Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# Gather A5 Direct Invoke 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | `cann_bench.gather` → `torch.ops.cann_bench.gather` → `cann_bench::gather_npu` → `calc_gather_tiling` → `launch_gather`；Direct Invoke。 |
| 计算语义 | `y.shape=index.shape`；输出坐标 `q` 上，`y[q]=x[q_0,…,index[q],…,q_(n-1)]`，`index[q]` 替换 `dim` 维坐标。 |
| 输入输出 | contiguous；等 rank 1–8；index 为 int32/int64；可启动 x dtype 为 fp16/fp32/bf16/int8/int32/int64。 |
| 执行类型 | R-006 SIMT；R-003 `NDDMA→NDDMA→AIV_VECTOR→NDDMA`；R-007 为带 512 B AIV UB 参数准备的 SIMT；R-001/R-002 AIV_VECTOR；R-005/R-004 SIMT。无可达 Cube/AIC 或 MIX_CV。 |
| Kernel 路线 | R-006 key200；R-003 key244；R-007 key301；R-001 key1210；R-002 key1320；R-005 key100；R-004 key230。 |
| 核心资源 | full-load 三个 depth=2 TQue；key244 三个 GM 临时 Tensor、NDDMA bound queue 与中间三队列；key301 512 B TBuf；其余 SIMT 直访 GM。 |
| 来源闭包 | `direct_implementation_closed`：Direct binding、selector/POD、全部可达 entry/body/helper、多 Kernel GM 边、同步及构建接线闭合；官方固定 Commit 仅作 GatherElements 相关映射。 |
| 验证状态 | 已完成源码闭包检查；本次知识提取未执行编译、真机、数值或性能测试。 |

## 接口与语义

### 计算语义

设 rank 为 `n`、规范化轴为 `a`、`q` 为 `index` 的有效坐标：

```text
y.shape = index.shape
y[q] = x[q0,...,q(a-1),index[q],q(a+1),...,q(n-1)]
```

非轴维要求 `index.size(i)<=x.size(i)`；Device 不检查 index 值，调用方必须保证 `0<=index[q]<x.size(a)`。算子只搬运 x 的位模式。

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| `x` | rank 1–8，contiguous | fp16/fp32/bf16/int8/int32/int64 | 数据源；Meta 未限制，但 launcher 仅接线这些 dtype。 |
| `index` | 与 x 同 rank，contiguous | int32/int64 | 决定输出 shape；非轴维不大于 x；值域由调用方保证。 |
| `dim` | Host 标量 | int64 | 默认 0；范围 `[-rank,rank)`，负值加 rank。 |
| `y` | `index.shape`，contiguous | 与 x 相同 | `torch::empty(index.sizes(),x.options())` 创建。 |

### 入口与版本

Python 入口只转发注册算子；Meta/PrivateUse1 分派分别绑定 `gather_meta/gather_npu`。本卡固定 CANN 9.1.0、A5/Ascend 950，不把它补写成 ACLNN。转换 README 明列 Ascend 950，CMake 将 `ascend950` 映射为 `dav-3510`。官方 Commit `ceb4536a2bd6fc99b85aec9d0fdcc0f470376292` 的 `index/gather_elements` 仅是算法与 A5 binary 配置的相关映射；Direct wrapper、补充 selector 与 key244 图均以转换交付件为事实源，不伪称官方入口。

## Host/Launcher 执行流程

### 参数校验与前处理

1. `gather_meta` 检查 rank、dim、index dtype 与非轴维，并创建 y。
2. `gather_npu` 绑定 x device，要求 x/index contiguous，规范化轴，把 shape 与元素字节数交给 `calc_gather_tiling`。
3. tiler 检查等 rank、rank 1–8、轴、`AIV coreNum>0`、`UB>32 KiB`；先 full-load，失败后合轴并选 SIMT/NDDMA。
4. selector 只为 key244 分配 `xTranspose/indexTranspose/yTranspose`。launcher 中 240–243 分支没有 selector producer，均为 dormant。
5. `OpCommand::RunOpApi("Gather",aclCall)` 用当前 NPU stream 调 `launch_gather`；未知 key/dtype 抛异常。

### 参数、Workspace 与生命周期

`calc_gather_tiling` 从 `PlatformAscendCManager` 读取 AIV 数与 UB 字节。key244 的 GM 边是：xT `[columns,xRows]`、iT `[columns,outputRows]`、yT `[columns,outputRows]`，字节分别为 x/index/y 的 numel×元素字节；均由 `gather_npu` 局部 Tensor 持有。它们至少存活至 `RunOpApi` 入流完成，异步回收依赖 torch_npu allocator。

Transpose tiler 会在 `TransposeLaunchParams.workspaceSize` 记录 16 MiB，但 key244 的 `TransposeCutTwoAxis` entry 不接收 workspace，launcher也不分配该 slice；真实交接介质是三份 GM Tensor。顶层 `workspaceBytes` 仅供 dormant key241，所有可达 Route 为 0。

### 启动图与失败传播

```text
key244:
N1 gather_nddma_transpose_x<X>(x -> xT)
 ->[same stream] N2 gather_nddma_transpose_x<I>(index -> iT)
 ->[same stream] N3 gather_transposed_ub<X,I>(xT,iT -> yT)
 ->[same stream] N4 gather_nddma_transpose_x<X>(yT -> y)
```

三份 transpose POD 均须 key10003/CUT_TWICE，否则启动前失败。源码未检查各 `<<<>>>` 的异步 Device 返回；跨节点可见性来自同 stream 提交顺序。单 Kernel Route 直接在相同 stream 启动。

## Route 与参数设计

### 分核与资源计算

```text
Xafter=product(x[axis:]); Iafter=product(index[axis:])
Xprefix=product(x[1:axis]); Iprefix=product(index[1:axis])  # 源码有意排除dim0与axis，空积为1
Bx=align32(Xafter*sx); Bi=align32(Iafter*si); By=align32(Iafter*sx)
load=floor(UBraw/(2*(Bx+Bi+By)))
```

full-load：`outputPrefix=product(index[:axis])`，`blockDim=min(coreNum,outputPrefix)`，`perCoreNum=ceil(outputPrefix/blockDim)`，最后核用 `tailCoreNum`。非 full-load 合并轴外连续相等维，令 `ySize=product(mergedIndex)`；小域单核，否则按 `perCoreNum=ceil(ySize/coreNum)` 均分。key244 三次 `[r,c]`、`perm=[1,0]` transpose 的 tiling UB 是 `min(UBraw,192 KiB)`，中间 gather 按 `usedCore=min(columns,coreNum)` 列循环。

### Route 选择

下表按实现复用的重要性降序排列；P0～P6 不代表 selector 判断顺序。`Host 顺序`独立保留源码中的真实先返回、后覆盖和 fallback 关系：H1 检查 full-load 并直接返回；H2 合轴后写入基础 key；H3 可把 key200 覆盖为 key230；H4 最后尝试 key244，成功时覆盖 H2/H3，失败时保留已有 key；H5 只处理不可达的 key240 准备分支。

| 重要性 | Route | 特征 | 适用域 | 实现前提 | Key/模板 | Host 顺序、短路与 fallback |
|---|---|---|---|---|---|---|
| P0 | R-006 2D axis0 direct | 2D axis0 的通用单 Kernel 主干，SIMT 直接从 GM 取 index 与 x | 非 full-load；合轴后 dim2/axis0，且后续专用覆盖均未生效 | 32 位 magic/shift 与 shape 乘积可表示；1024-thread entry 可用 | 200/`GatherDim2Direct<...,0>` | H2 先写 key200；H3 guard 真时转 R-004；H4 成功时再转 R-003，H4 失败保留 key200 或 key230。 |
| P1 | R-003 CUT_TWICE 图 | 三次 NDDMA 转置包围按列 full-load gather，以 GM 中间 Tensor 串联四节点 | 非 full-load；合轴后 dim2/axis0；`ySize>=2^24`；si∈{4,8}、sx∈{1,4,8}；index 首维为 2 幂；各维与 `ySize` 不超过 UINT32 | 三份 transpose tiling 都成功且 key10003；N3 UB guard 成功；三份 GM 临时 Tensor 已分配 | 244/3×`TransposeCutTwoAxis`+`FullLoad<2,1>` | H4 最后尝试并覆盖 H2 的 key200 或 H3 的 key230；任一 guard 失败都原样保留 H2/H3 结果。 |
| P2 | R-007 3D axis1 | 合轴后 3D 中轴 SIMT，先在 UB 准备参数再直访 GM | 非 full-load；合轴后 dim3/axis1 | 512 B TBuf 与 UB barrier 可用；2048-thread entry 可用 | 301/`GatherElementsKernel<...,3,1>` | H2 写 key301；H3/H4 仅检查 dim2/axis0，因此不覆盖；launcher 未知 key 才失败。 |
| P3 | R-001 2D 尾轴 full-load | x/index 行驻 UB，masked register gather 后连续回写 | rank2/axis1，且 full-load 公共谓词成立 | 三个 depth2 TQue 总账可驻 UB；`x[axis]<=65535`；有效 offset 可由 uint16 表示 | 1210/`FullLoad<2,1>` | H1 命中即写 key1210 并返回，不执行合轴及 H2～H5；若 H1 为假才进入后续 selector。 |
| P4 | R-002 3D 尾轴 full-load | 与 R-001 同族，增加二维 prefix 解码 | rank3/axis2，且 full-load 公共谓词成立 | 同 R-001，并要求 prefix 解码与 stride 乘积有效 | 1320/`FullLoad<3,2>` | H1 命中即写 key1320 并返回；不执行合轴及 H2～H5。 |
| P5 | R-005 1D direct | 最短 1D SIMT 直接索引路径 | 非 full-load；合轴后 dim1/axis0 | 基础分核参数有效；512-thread entry 可用 | 100/`GatherDim1Direct` | H2 写 key100；H3/H4 均不适用，不再覆盖；launcher 未知 key 才失败。 |
| P6 | R-004 大 2D grid-stride | 大 2D axis0 的 512-thread grid-stride 中间候选 | 非 full-load；合轴后 dim2/axis0；`ySize>=2^25`；si=4；index 首维为 2 幂 | UINT32 地址域与 magic/shift 有效；R-003 未成功覆盖 | 230/`GatherDim2GridStrideDirect` | H3 在 H2 key200 之后覆盖为 key230；H4 随后仍可覆盖为 R-003，H4 失败则保留 key230。 |

```text
H1 full-load? -> key=1000+rank*100+axis*10 -> return -> 1210/1320 or launcher error
else MergeAxis -> H2 base key=rank*100+axis
-> H3 optional 230 override -> H4 optional 244 override (失败保留 H2/H3)
-> H5 dormant 240 preparation -> 244/230/100/200/301 or launcher error
```

### 模板/实现执行矩阵

| 重要性 | Route | Host 顺序 | key/selector | dtype/shape/platform 完整命中条件 | 执行拓扑与 Kernel 节点 | 实际模板/body | 内存与同步特征 | tail/fallback |
|---|---|---|---|---|---|---|---|---|
| P0 | R-006 | H2→H3/H4 | 200 | 2D axis0；后续 230/244 覆盖均未生效 | 单 SIMT | `GatherDim2Direct<...,0>` | 无UB，1024线程 | core tail；H3/H4 可覆盖。 |
| P1 | R-003 | H4 覆盖 H2/H3 | 244 | 上表全部 guard；X code1/3/4/6 | NDDMA、NDDMA、AIV_VECTOR、NDDMA | 3×`TransposeCutTwoAxis`+`gather_transposed_ub` | 三GM边、same-stream、bound queue | transpose四类tail；tiling失败保留 H2/H3 key。 |
| P2 | R-007 | H2 | 301 | 3D axis1 | 单 SIMT | `GatherElementsKernel<...,3,1>`→`GatherDim3Compute` | 512 B TBuf+UB barrier，2048线程 | core tail。 |
| P3 | R-001 | H1 return | 1210 | full-load rank2/axis1；六种X×两种I | 单 AIV_VECTOR | `FullLoad<X,I,2,1>` | 三个depth2 TQue | core/UB tail；其它 full-load key失败。 |
| P4 | R-002 | H1 return | 1320 | full-load rank3/axis2 | 单 AIV_VECTOR | `FullLoad<X,I,3,2>` | 同左，地址多一维 | 同左。 |
| P5 | R-005 | H2 | 100 | 1D axis0 | 单 SIMT | `GatherDim1Direct` | 无UB，512线程 | core tail。 |
| P6 | R-004 | H3；H4 可覆盖 | 230 | 大2D axis0、int32 index、幂次行；244未覆盖 | 单 SIMT | `GatherDim2GridStrideDirect` | 无UB，512线程 | `i<total`；H4失败保留230。 |

### 隐藏性能 Guard

| Guard | Host/Tiling 条件 | Device/资源原因 | 影响 Route | 不满足时去向 | 源码符号 |
|---|---|---|---|---|---|
| CUT_TWICE | 三 transpose key均10003 | launcher 固定 `TransposeCutTwoAxis` | R-003 | 保留230/200 | `DoSplitUB/launch_gather` |
| transpose UB cap | `min(UBraw,192KiB)` | 避免形状选择非10003 key | R-003 | 回退 | `calc_gather_tiling` |
| N3 UB | `UBraw>=2*(align32(xRows*sx)+align32(outputRows*si)+align32(outputRows*sx))` | 三个队列与offset范围 | R-003 | 230/200 | `MakeTransposedFullLoadTiling` |
| full-load UB | `load>0` | 三双队列总量≤UB | R-001/2 | 合轴 | `calc_gather_tiling` |
| offset | `x[axis]<=65535` | 1/2-byte X 用uint16 gather offset | R-001/2/3-N3 | SIMT或失败 | `isFullLoad/GatherValue` |
| grid | y≥2^25、si=4、幂次行 | 512线程grid-stride | R-004 | 200 | `calc_gather_tiling` |
| 空域 | 无完整零维guard | 除法/log2/core计算要求正量 | 全部 | 异常或无效参数 | `calc_gather_tiling` |

### POD/ABI

`GatherElementsTilingData` 全为 64 位顺序字段，`sizeof=448`、`alignof=8`：

| 结构 | 字段 | 类型/位宽 | ABI 布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| `GatherElementsTilingData` | `axis` | int64/64 | off0 | axis | selector | full-load | 模板轴限定。 |
| 同上 | `usedCore` | int64/64 | off8 | core | 分核 | 全部 | >0。 |
| 同上 | `perCoreNum` | int64/64 | off16 | element/row | ceil分核 | 循环 | tail另算。 |
| 同上 | `tailCoreNum` | int64/64 | off24 | element/row | 余数 | 末核 | 非负。 |
| 同上 | `xLoadInUbNum` | int64/64 | off32 | row | UB公式 | xQueue | SIMT inactive。 |
| 同上 | `indexLoadInUbNum` | int64/64 | off40 | row | UB/perCore上限 | index/y queue | SIMT inactive。 |
| 同上 | `xUbFactor` | int64/64 | off48 | element | `Xafter*xLoad` | full-load缓存 | 不直接分配。 |
| 同上 | `indexUbFactor` | int64/64 | off56 | element | `Iafter*iLoad` | full-load缓存 | 同上。 |
| 同上 | `xAfterAxis` | int64/64 | off64 | element/row | shape乘积 | DMA/offset | 溢出未查。 |
| 同上 | `idxAfterAxis` | int64/64 | off72 | element/row | shape乘积 | DMA/offset | 必须正。 |
| 同上 | `xStrideArr[8]` | int64[8] | off80 | element | `ComputeEightDim` | 地址 | 前补1。 |
| 同上 | `indexStrideArr[8]` | int64[8] | off144 | element | 同上 | 解码 | 前补1。 |
| 同上 | `magic[7]` | uint64[7] | off208 | ratio | reciprocal公式 | 200/230；301重算 | stride非零。 |
| 同上 | `shift[7]` | uint64[7] | off264 | bit | ceil(log2) | 同上 | stride正。 |
| 同上 | `indexShape[8]` | int64[8] | off320 | element | Host shape | body | rank表示依Route。 |
| 同上 | `xShape[8]` | int64[8] | off384 | element | Host shape | body | 同上。 |

`GatherElementsLaunchTiling` 的字段依次是 `data`、三份 `transposeNddma*`、三份 dormant `transpose*`、三份 dormant `vconv*`、dormant `v2`、`key:uint64`、`blockDim/transposeBlockDim/xRows/outputRows/columns/columnShift/outputRowsShift:uint32`、`workspaceBytes:uint64`。同一 header 供 Host/Device 使用；源码无顶层 `static_assert(sizeof/offsetof)`，故不写未经编译确认的绝对 offset。可达 consumer：`key/blockDim` 全路线；三份 NDDMA POD 与 `xRows/outputRows/columns` 仅 R-003；`columnShift/outputRowsShift` 在 R-003 写入但不读取；`workspaceBytes=0`。

每个 `TransposeLaunchParams` 含 `blockDim:int64`、`tilingKey:uint64`、`workspaceSize/dataSize:size_t` 与 `alignas(8) data[2048]`。其 payload 是 `TransposeOpTilingData`：19个 int64 标量及 input/output/perm/base/expanded/inUb main/input-tail/output-tail/both-tail 数组；`FillTilingData` 逐字段生产，`TransposeCutTwoAxis` 消费。

### Route 源码闭包

| 重要性 | Route | Host 顺序 | Key/selector | Host/Tiling producer | POD/参数 | Kernel entry/router 节点 | Kernel body/直接依赖 | 构建接线 |
|---|---|---|---|---|---|---|---|---|
| P0 | R-006 | H2→H3/H4 | 200 | `calc_gather_tiling` | Gather POD | generated `_200` | `GatherDim2Direct` | `gather/CMakeLists.txt` |
| P1 | R-003 | H4 覆盖 H2/H3 | 244 | `calc_gather_tiling/calc_transpose_tiling/TransposeNddmaTiling` | Launch POD+3×Transpose POD | 3×`gather_nddma_transpose_x`+`gather_transposed_ub` | `TransposeCutTwoAxis/ComputeDim1Vf` | 同上；Host tiler由plugin同TU include |
| P2 | R-007 | H2 | 301 | `calc_gather_tiling` | Gather POD | generated `_301` | `GatherElementsKernel/GatherDim3Compute` | 同上 |
| P3 | R-001 | H1 return | 1210 | 同上 | 同上 | generated `_1210` | `gather_elements_full_load.h` | 同上 |
| P4 | R-002 | H1 return | 1320 | 同上 | 同上 | generated `_1320` | `gather_elements_full_load.h` | 同上 |
| P5 | R-005 | H2 | 100 | 同上 | 同上 | generated `_100` | `GatherDim1Direct` | 同上 |
| P6 | R-004 | H3；H4 可覆盖 | 230 | 同上 | 同上 | generated `_230` | `GatherDim2GridStrideDirect` | 同上 |

## Kernel 实现

### 公共执行流程

torch dtype code 1/3/4/5/6/15 分别分派 int8/int32/int64/half/float/bfloat16，index code 3/4 分派 int32/int64。key244 先走专用多 Kernel router，其余 key 进入生成的 `launch_X_I`。Kernel 标注 AIV_ONLY，但 `asc_vf_call` 内线程算法按 SIMT 族记录；无通信、Cube 或 MIX_CV。

### P0 · Route R-006：2D axis0 直接 SIMT

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host/Router | `gather_kernel.cpp` | `calc_gather_tiling/BODY_200` | merged rank2/axis0且未被244/230覆盖 | 1024-thread direct |

#### Device 数据流

##### 函数级调用链

`launch_X_I -> gather_X_I_200 -> asc_vf_call<GatherDim2Direct<X,I,0>>(1024)`

##### 源码等价伪码

```text
for i in 本核区间 stride1024:
 row=UintDiv(i,magic[6],shift[6]); col=i-row*indexStride[6]
 y[i]=x[index[i]*xStride[6]+col]
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM x/index/y | 伪码公式 | 单元素 | X/I/X | caller/thread | thread/caller | caller | 无UB |

##### 分层内存布局

N/A：线程直接 GM→GM。

##### 字节账与复用顺序

`UB_total=0; dynamic_ub=N/A; workspace_total=0`。无复用子区。

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| 坐标解码 | `Simt::UintDiv` | Host magic/shift | 地址计算 | x offset | core tail；无cast/atomic。 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `gather_kernel.cpp` | `ComputeEightDim/calc_gather_tiling` | stride/magic/key200。 |
| Kernel entry/router | 同上 | `BODY_200` | 1024线程。 |
| Device body/helper | 同上 | `GatherDim2Direct<...,0>` | 2D地址/tail。 |

### P1 · Route R-003：CUT_TWICE NDDMA 四节点

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | `gather_kernel.cpp` | `calc_gather_tiling` | 大2D axis0、dtype/幂次/uint32 guard | 三次transpose tiling |
| Tiling | `transpose_tiling_arch35.cpp` | `DoSplitUB` | `outCutIndex>FindOutIndex(inCutIndex)` | key10003 |
| Router | `gather_kernel.cpp` | `launch_gather` | key244且三份10003 | N1→N2→N3→N4 |

#### Device 数据流

##### 函数级调用链

```text
N1 TransposeCutTwoAxis<X>(x->xT) -> N2 TransposeCutTwoAxis<I>(index->iT)
 -> N3 gather_transposed_ub<X,I>(xT,iT->yT) -> N4 TransposeCutTwoAxis<X>(yT->y)
```

##### 源码等价伪码

```text
N1/N2: [rows,columns]转为[columns,rows]
N3: for column=core; column<columns; column+=usedCore:
      DMA xT[column,:],iT[column,:]; masked MicroAPI gather整列；DMA yT[column,:]
N4: [columns,outputRows]转回[outputRows,columns]
CUT_TWICE各节点把循环域分为main/input-tail/output-tail/both-tail，MultiCopy GM->UB，DataCopyPad UB->GM
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| xT/iT/yT GM | mixed-radix/`column*rows` | x/index/y原字节数 | 转置2D | N1/N2/N3 | N3/N3/N4 | torch Tensor | same-stream边 |
| NDDMA bound queue | 0 | `td.ubSize`，depth1 | 当前T | MultiCopy | DataCopyPad | 节点TPipe | 每tile复用 |
| N3 x/i/y queue | 0 | `align32(xRows*sx)`/`align32(outputRows*si)`/`align32(outputRows*sx)`，depth1 | X/I/X | DMA/compute | compute/DMA | N3 TPipe | 每列复用 |

##### 分层内存布局

```mermaid
block-beta
  columns 4
  nd["N1/N2/N4各自boundQ depth1 · td.ubSize"]:1
  xq["N3 xQ depth1 · align32(xRows*sx)"]:1
  iq["N3 iQ depth1 · align32(outputRows*si)"]:1
  yq["N3 yQ depth1 · align32(outputRows*sx)"]:1
```

##### 字节账与复用顺序

```text
N1/N2/N4 UB_total(each)=td.ubSize<=min(UBraw,192KiB)
N3 UB_total=align32(xRows*sx)+align32(outputRows*si)+align32(outputRows*sx); selector要求2*N3_UB<=UBraw
dynamic_ub=N/A
workspace_total(GM临时)=numel(x)*sx+numel(index)*si+numel(y)*sx
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| boundQ/N3 queues | MultiCopy/DMA/compute | DataCopyPad/compute/DMA | 下一tile/列 | EnQue→DeQue→Free | 消费后覆盖。 |
| xT/iT/yT | 前序Kernel | 后序Kernel | Route后回收 | same-stream | allocator感知stream。 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| 跨节点 | current stream | N1/N2/N3 | N3/N4 | GM临时 | 位模式；无cast。 |
| NDDMA内 | boundQ+loop mode | MultiCopy | DataCopyPad | UB tile | main/input/output/both-tail，blockLen/stride为byte。 |
| N3 | TQue+mask | row DMA | gather/copy | UB row | 最后repeat裁到outputRows。 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `gather_kernel.cpp`、`transpose_tiling_arch35.cpp` | `calc_gather_tiling/DoSplitUB/FillTilingData` | 244、三transpose、四类tail POD。 |
| Kernel entry/router | `gather_kernel.cpp` | `launch_gather` key244 | 四节点顺序。 |
| Device body/helper | `transpose_cut_two_axis.h`、`gather_kernel.cpp` | `TransposeCutTwoAxis/gather_transposed_ub` | 5D MultiCopy与逐列gather。 |

### P2 · Route R-007：3D axis1 SIMT

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host/Router | `gather_kernel.cpp` | `calc_gather_tiling/BODY_301` | merged rank3/axis1 | `GatherElementsKernel<...,3,1>` |

#### Device 数据流

##### 函数级调用链

```text
gather_X_I_301 -> GatherElementsKernel<X,I,uint32,3,1>::Init/Process
 -> GetUintDivMagicAndShift -> DataSyncBarrier<UB> -> asc_vf_call<GatherDim3Compute>(2048)
```

##### 源码等价伪码

```text
for i in 本核区间 stride2048:
 d0=UintDiv(i,m5,s5); rem=i-d0*iStride5; d1=UintDiv(rem,m6,s6); d2=rem-d1*iStride6
 y[i]=x[d0*xStride5+index[i]*xStride6+d2]
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| `magicAndShiftBuf` | 0 | 512 B | uint32 local | Init/Process | 参数准备 | TPipe | Kernel期；DIM3实际用成员寄存器 |
| GM x/index/y | 伪码公式 | 单元素 | X/I/X | caller/thread | thread/caller | caller | 无GM staging |

##### 分层内存布局

```mermaid
block-beta
  columns 1
  ms["magicAndShiftBuf · VECCALC TBuf · 512 B"]:1
```

##### 字节账与复用顺序

`UB_total=512 B; dynamic_ub=N/A; workspace_total=0`。buffer 在 Kernel 结束后释放；当前 DIM3 SIMT 用 `m_/shift_`，不读取其数组视图。

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| 参数/线程 | UB DSB+per-core interval | AIV准备/thread | SIMT call | local/y | 最后核tail；无cast/atomic。 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `gather_kernel.cpp` | `calc_gather_tiling` | key301/分核。 |
| Kernel entry/router | 同上 | `BODY_301` | `<3,1>`。 |
| Device body/helper | `gather_elements.h` | `Init/Process/GatherDim3Compute` | 512B、barrier、2048线程。 |

### P3 · Route R-001：2D 尾轴 full-load

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | `op_kernel/gather_kernel.cpp` | `calc_gather_tiling` | full-load 且 rank2/axis1 | key1210 |
| Router/Entry | 同上 | `DEFINE_LAUNCH/BODY_1210` | `t.key==1210` | `FullLoad<X,I,2,1>` |

#### Device 数据流

##### 函数级调用链

```text
launch_gather -> launch_X_I -> gather_X_I_1210
 -> FullLoad<2,1>::Init -> Process -> CopyInIdx/CopyInX -> ComputeDim1Vf/GatherValue -> CopyOut
```

##### 源码等价伪码

```text
for UB批 in 本核prefix行:
  DMA有效index行与对应x行到双缓冲队列
  for row,repeat: mask尾lane; load/deinterleave index; DataCopyGather(xLocal,indexReg); store yLocal
  DMA仅有效rows*Iafter到y
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM x/index/y | prefix stride | 有效行×axis后长度 | X/I/X row-major | caller/DMA | DMA/caller | caller | tail精确 |
| xQueue/indexQueue/yQueue | aligned row slice | `Bx*xLoad`/`Bi*iLoad`/`By*iLoad`，各depth2 | X/I/X | DMA/compute | compute/DMA | TPipe | EnQue→DeQue→Free |

##### 分层内存布局

```mermaid
block-beta
  columns 3
  xQ["xQueue depth2 · 2*Bx*xLoad"]:1
  iQ["indexQueue depth2 · 2*Bi*iLoad"]:1
  yQ["yQueue depth2 · 2*By*iLoad"]:1
```

##### 字节账与复用顺序

```text
UB_total=2*(Bx*xLoad+Bi*iLoad+By*iLoad)<=UBraw; dynamic_ub=N/A; workspace_total=0
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| 三queue slot | DMA/Compute | Compute/CopyOut | 下一UB批 | EnQue/DeQue/FreeTensor | 消费后才覆盖。 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| 搬运/计算 | TQue+MicroAPI mask | DMA/index load | DeQue/gather | queue/lane | 位模式搬运；末核与末repeat裁尾；不查index值。 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `op_kernel/gather_kernel.cpp` | `calc_gather_tiling` | UB、分核、1210。 |
| Kernel entry/router | 同上 | `BODY_1210` | key→模板。 |
| Device body/helper | `op_kernel/gather_elements_full_load.h` | `Init/Process/ComputeDim1Vf/GatherValue` | 双队列、masked gather、tail。 |

### P4 · Route R-002：3D 尾轴 full-load

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | `op_kernel/gather_kernel.cpp` | `calc_gather_tiling` | full-load 且 rank3/axis2 | key1320 |
| Router/Entry | 同上 | `DEFINE_LAUNCH/BODY_1320` | `t.key==1320` | `FullLoad<X,I,3,2>` |

#### Device 数据流

##### 函数级调用链

```text
launch_X_I -> gather_X_I_1320 -> FullLoad<3,2>::Init/Process
 -> 二维prefix解码 -> CopyIn -> ComputeDim1Vf -> CopyOut
```

##### 源码等价伪码

```text
prefix=core*perCore+loop*iLoad; (d0,d1)=divmod(prefix,indexShape[1])
xOffset=d0*xStride[5]+d1*xStride[6]
成批载入有效prefix行，沿最后轴masked gather，跳过超出index前缀域的x坐标，写有效y行
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM与三queue | `d0*xStride[5]+d1*xStride[6]` | 同R-001 | X/I/X | DMA/compute | compute/DMA | caller/TPipe | 32B、depth2、逐批复用 |

##### 分层内存布局

```mermaid
block-beta
  columns 3
  xQ["xQueue depth2 · 2*Bx*xLoad"]:1
  iQ["indexQueue depth2 · 2*Bi*iLoad"]:1
  yQ["yQueue depth2 · 2*By*iLoad"]:1
```

##### 字节账与复用顺序

```text
UB_total=2*(Bx*xLoad+Bi*iLoad+By*iLoad)<=UBraw; dynamic_ub=N/A; workspace_total=0
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| 三queue slot | DMA/Compute | Compute/CopyOut | 下一prefix批 | queue生命周期 | 同R-001。 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| prefix/gather | div/mod+TQue+mask | POD/DMA | 地址/compute | GM/UB/lane | 二维prefix guard、末核/末批/末repeat裁尾。 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `op_kernel/gather_kernel.cpp` | `calc_gather_tiling` | 1320与原shape。 |
| Kernel entry/router | 同上 | `BODY_1320` | `FullLoad<3,2>`。 |
| Device body/helper | `gather_elements_full_load.h` | `Process` 3D axis2 | prefix地址、队列、tail。 |

### P5 · Route R-005：1D 直接 SIMT

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host/Router | `gather_kernel.cpp` | `MergeAxis/calc_gather_tiling/BODY_100` | merged rank1/axis0 | 512-thread direct |

#### Device 数据流

##### 函数级调用链

`launch_X_I -> gather_X_I_100 -> asc_vf_call<GatherDim1Direct>(512)`

##### 源码等价伪码

```text
begin=block*perCore; end=begin+(last?tailCore:perCore)
for i=thread+begin; i<end; i+=512: y[i]=x[index[i]]
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM x/index/y | `index[i]`/`i`/`i` | 单元素 | X/I/X | caller/thread | thread/caller | caller | 无UB |

##### 分层内存布局

N/A：线程直接 GM→GM。

##### 字节账与复用顺序

`UB_total=0; dynamic_ub=N/A; workspace_total=0`。无复用子区；输出 i 唯一归属。

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| SIMT interval | per-core range | thread | N/A | y[i] | 最后核tail；无cast/barrier。 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `gather_kernel.cpp` | `calc_gather_tiling` | 分核/key100。 |
| Kernel entry/router | 同上 | `BODY_100` | 512线程。 |
| Device body/helper | 同上 | `GatherDim1Direct` | 1D gather/tail。 |

### P6 · Route R-004：大 2D grid-stride SIMT

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host/Router | `gather_kernel.cpp` | `calc_gather_tiling/BODY_230` | 230 guard且244未覆盖 | 512-thread grid-stride |

#### Device 数据流

##### 函数级调用链

`launch_X_i32 -> gather_X_i32_230 -> asc_vf_call<GatherDim2GridStrideDirect>(512)`

##### 源码等价伪码

```text
for i=block*512+thread; i<total; i+=usedCore*512:
 row=UintDiv(i,magic,shift); col=i-row*columns; y[i]=x[index[i]*columns+col]
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM x/index/y | 伪码公式 | 单元素/迭代 | X/int32/X | caller/thread | thread/caller | caller | 无UB |

##### 分层内存布局

N/A：线程直接访问 GM。

##### 字节账与复用顺序

`UB_total=0; dynamic_ub=N/A; workspace_total=0`。无复用子区；每个 i 唯一写 y[i]。

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| SIMT loop | grid stride | thread | 自身下一i | y[i] | `i<total`；无barrier/atomic/cast。 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `gather_kernel.cpp` | `calc_gather_tiling` | 230 guard/magic。 |
| Kernel entry/router | 同上 | `BODY_230` | 512线程。 |
| Device body/helper | 同上 | `GatherDim2GridStrideDirect` | 地址与tail。 |

## 算子特定优化

### Trick T-001：UB full-load 后做 masked register gather

#### 触发与源码依据

- 适用 Route：R-001、R-002。
- 触发条件：完整 full-load guard 且 key1210/1320。
- Golden 来源：[`index/gather_elements/op_kernel/arch35/gather_elements_full_load.h:74-76`](https://gitcode.com/cann/ops-nn/blob/ceb4536a2bd6fc99b85aec9d0fdcc0f470376292/index/gather_elements/op_kernel/arch35/gather_elements_full_load.h#L74-L76)

**官方相关映射源码（固定 Commit；Direct 路线选择以转换交付件为准）**：

```cpp
pipe_.InitBuffer(xQueue_, BUFFER_NUM, ops::CeilAlign(xAfterAxis_ * sizeof(X_T), static_cast<uint64_t>(blockSize)) * tilingData_->xLoadInUbNum);
pipe_.InitBuffer(indexQueue_, BUFFER_NUM, ops::CeilAlign(idxAfterAxis_ * sizeof(INDEX_T), static_cast<uint64_t>(blockSize)) * tilingData_->indexLoadInUbNum);
pipe_.InitBuffer(yQueue_, BUFFER_NUM, ops::CeilAlign(idxAfterAxis_ * sizeof(X_T), static_cast<uint64_t>(blockSize)) * tilingData_->indexLoadInUbNum);
```

#### 机制与设计原因

Host 以 `UB/(2*(Bx+Bi+By))` 决定驻留行数，Device 成批驻留 x/index/y 行；`oneRepeatSize=GetVecLen()/sizeof(I)`（64位X时按8字节），末repeat由 `UpdateMask` 裁尾，`DataCopyGather` 从驻留 x 行取值，减少逐输出随机 GM 读取。

#### 迁移边界

- 适用：轴后数据可成批入 UB 且同一 x 行被多个 index lane 复用。
- 前提：双缓冲字节账、x轴≤65535、index合法、offset位宽匹配。
- 失效：guard 不成立走 SIMT/NDDMA；不能只缩输出 mask 绕过 offset 上限。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

Host 若生成非1210/1320的 full-load key，Direct router 会抛 `Unexpected GatherElements tiling key`；不得假定其它模板已接线。

### Trick T-002：大 2D axis0 先转置再按列 full-load

#### 触发与源码依据

- 适用 Route：R-003。
- 触发条件：R-003 的完整规模、dtype、uint32、三次CUT_TWICE与UB guard。
- Golden 来源：[`index/gather_elements/op_kernel/arch35/gather_elements_full_load.h:144-163`](https://gitcode.com/cann/ops-nn/blob/ceb4536a2bd6fc99b85aec9d0fdcc0f470376292/index/gather_elements/op_kernel/arch35/gather_elements_full_load.h#L144-L163)

**官方相关映射源码（固定 Commit；四节点组合是转换交付件事实）**：

```cpp
MicroAPI::DataCopyGather(RegY, xPtr, RegGatherIndex, maskRegInput);
MicroAPI::DataCopy(yPtrOffset, RegY, maskRegInput);
```

#### 机制与设计原因

三个 CUT_TWICE transpose 把 axis0 的跨行访问改为连续列，N3 一次载入整列 x/index 后在 UB 内 gather，再转回输出布局。源码可证明它把随机 GM gather 改为连续 NDDMA 搬运加 UB gather；未给出性能结论。

#### 迁移边界

- 适用：大2D axis0且三个 transpose 都选10003。
- 前提：X字节1/4/8、I字节4/8、三GM临时量、same-stream顺序。
- 失效：任一tiling或N3 UB guard失败，保留230/200；half/bf16不进入。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

不可把 transpose 的 16 MiB workspace metadata 当作已分配 workspace；真实边是三个 Tensor。也不可把转换新增 key244 伪称固定官方 Commit 的公开入口。

## 模板与实现对比

| 重要性 | Route | Host 顺序 | 模板与 dtype | 循环与分核 | Queue/TBuf/GM 临时区 | 搬运与执行 API | 同步、精度与 tail | fallback/失败边界 |
|---|---|---|---|---|---|---|---|---|
| P0 | R-006 | H2→H3/H4 | `GatherDim2Direct`；六X×两I | 1024-thread 本核区间 | 无 UB 临时区 | SIMT GM 直访 | 位模式；core tail | H3/H4 可覆盖；其它 base key 失败。 |
| P1 | R-003 | H4 覆盖 H2/H3 | `TransposeCutTwoAxis`+full-load；X code1/3/4/6，I两类 | 三次 mixed-radix 转置+逐列 gather | boundQ、N3 三Q、三份 GM 临时 Tensor | MultiCopy/DataCopyPad+MicroAPI | same-stream、queue、四类 tail | 失败保留 key230/key200。 |
| P2 | R-007 | H2 | `GatherElementsKernel<...,3,1>`；六X×两I | 2048-thread 本核区间 | 512 B TBuf | SIMT GM 直访 | UB DSB；core tail | 其它 base key 失败。 |
| P3 | R-001 | H1 return | `FullLoad<2,1>`；六X×两I | prefix/UB 批 | 三个 depth2 TQue；`2*(Bx+Bi+By)` | DMA+MicroAPI gather | queue/mask/core tail | 其它 full-load key 失败。 |
| P4 | R-002 | H1 return | `FullLoad<3,2>`；六X×两I | 二维 prefix/UB 批 | 同 R-001 | DMA+MicroAPI gather | queue/mask/core tail | 其它 full-load key 失败。 |
| P5 | R-005 | H2 | `GatherDim1Direct`；六X×两I | 512-thread 本核区间 | 无 UB 临时区 | SIMT GM 直访 | 位模式；core tail | 其它 base key 失败。 |
| P6 | R-004 | H3；H4 可覆盖 | `GatherDim2GridStrideDirect`；六X、int32 I | 512-thread grid-stride | 无 UB 临时区 | SIMT GM 直访 | 位模式；loop guard | H4 成功转 R-003，失败保留 key230。 |

## 平台差异

| 项目 | A2 | A3 | A5 |
|---|---|---|---|
| 支持状态 | 本卡不覆盖；转换README虽列910B/910_93，不作本卡结论。 | 本卡不覆盖。 | 转换README/CMake明确 `ascend950/dav-3510`；官方相关映射含ascend950 binary config。 |
| Host/Launcher | 未提取 | 未提取 | Platform manager读取AIV/UB；当前NPU stream直调。 |
| Kernel/资源 | 未提取 | 未提取 | AIV_VECTOR、SIMT、NDDMA与四节点图；`--npu-arch=dav-3510 -xasc`。 |

## 限制与失败边界

- Meta 不限制 x dtype，launcher 只接线 fp16/fp32/bf16/int8/int32/int64。
- tiler 可生成更多 full-load/generic key，但 router 只接线1210/1320/100/200/230/301；其它 key 失败。
- 240–243 有 launcher/body 无 selector producer，为 dormant。
- 不检查 index 值域；负值或越界值会形成越界 GM 地址。
- 零维 guard 不完整；除法、log2、usedCore 依赖正量。
- shape 连乘未查 int64 溢出；`MergeAxis` 用 `int` 保存合并乘积；key244仅检查自身uint32字段。
- `blockLen` 收窄uint32、full-load `rows` 收窄uint16，Host未逐处证明乘积位宽。
- key244 的 fp32 以 int32 模板搬运等宽位模式；不得在该图加入算术。
- 临时 Tensor 异步回收无显式 event/recordStream，安全性属于 torch_npu allocator 边界。
- 固定官方 Commit 只作 GatherElements 相关映射，Direct wrapper/selector/key244 来自转换交付件。
- 本次知识提取未执行编译、真机、数值或性能测试。

## 源码索引

### 链路索引

| 链路阶段 | 文件 | 关键符号 | 支撑内容 |
|---|---|---|---|
| 入口声明/约束 | `cann_bench/__init__.py` | `gather` | Python入口。 |
| 入口实现 | `csrc/ops/gather/op_plugin/gather_plugin.cpp` | `gather_meta/gather_npu` | 校验、输出、临时量、stream。 |
| Host/Tiling/Launcher | `csrc/ops/gather/op_kernel/gather_kernel.cpp` | `calc_gather_tiling/launch_gather` | selector、七Route、graph。 |
| Host/Tiling/Launcher | `csrc/ops/gather/op_host/transpose_direct_tiling.cpp` | `calc_transpose_tiling` | Direct context/POD序列化。 |
| Host/Tiling/Launcher | `csrc/ops/gather/op_host/transpose_tiling_arch35.cpp` | `TransposeNddmaTiling` | CUT_TWICE/分核/tail。 |
| POD/ABI | `csrc/ops/gather/op_kernel/gather_elements_tilingdata.h` | POD structs | 共享ABI。 |
| Kernel entry/body | `csrc/ops/gather/op_kernel/gather_elements.h` | `GatherElementsKernel` | R-007。 |
| Kernel entry/body | `csrc/ops/gather/op_kernel/gather_elements_full_load.h` | `FullLoadKernel` | R-001/2与N3。 |
| Kernel entry/body | `csrc/ops/gather/op_kernel/transpose_nddma/arch35/transpose_cut_two_axis.h` | `TransposeCutTwoAxis` | R-003 NDDMA。 |
| 构建接线 | `csrc/ops/gather/CMakeLists.txt` | `register_direct_launch_op` | kernel/plugin注册。 |
| 平台相关映射 | `index/gather_elements/op_host/config/ascend950/gather_elements_binary.json` | A5 config | 官方固定Commit相关映射，不证明Direct wrapper。 |

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | Gather POD 448B；Launch POD同头共享 | 字段顺序/位宽、payload 8B对齐与2048B上限 | `gather_elements_tilingdata.h` |
| 调用顺序 | key244 N1→N2→N3→N4 | same-stream；N3等待两输入，N4等待N3 | `launch_gather` |
| workspace/内存 | 三双Q；key244三GM temp | depth计入；16MiB metadata非实际workspace | `InitBuffer/gather_npu` |
| 同步 | TQue、boundQ、same-stream、R-007 DSB | 不省略handoff或跨Kernel顺序 | `Process*/launch_gather` |
| 精度与尾块 | 位模式、mask、core/UB/NDDMA四类tail | index解包、有效mask、四分区 | `GatherValue/GetIntervalInfoForCutTwice` |
| 失败边界 | 仅七key可达且接线 | 不把dormant 240–243或官方完整key视为Direct可达 | `calc_gather_tiling/DEFINE_LAUNCH` |
