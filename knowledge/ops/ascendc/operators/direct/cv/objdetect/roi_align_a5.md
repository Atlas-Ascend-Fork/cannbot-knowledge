---
type: Operator
title: "ROIAlign A5 Direct Invoke 算子知识"
description: "说明 cann_bench::roi_align、roi_align_npu 与 launch_roi_align 在 A5 上的接口语义、Host 参数生成、四路静态分发、双 Kernel 启动图与 SIMT 实现。"
tags: [task.implementation, task.lookup, topic.data_movement, topic.memory, topic.precision, topic.programming_model]
status: stable
verified:
  - by: process:ops-knowledge-route-priority
    at: "2026-08-25T20:47:20Z"
  - by: process:ops-knowledge-direct53-ingest
    at: "2026-08-25T20:03:11Z"
sources:
  - resource: https://gitcode.com/cann/ops-cv/blob/bb717d075d129fd1fc7b96b2886824a1d153ed2f/objdetect/roi_align/docs/aclnnRoiAlignV2.md
    role: header
  - resource: https://gitcode.com/cann/ops-cv/blob/bb717d075d129fd1fc7b96b2886824a1d153ed2f/objdetect/roi_align/op_graph/roi_align_proto.h
    role: header
  - resource: https://gitcode.com/cann/ops-cv/blob/bb717d075d129fd1fc7b96b2886824a1d153ed2f/objdetect/roi_align/op_host/op_api/aclnn_roi_align_v2.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-cv/blob/bb717d075d129fd1fc7b96b2886824a1d153ed2f/objdetect/roi_align/op_host/op_api/aclnn_roi_align.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-cv/blob/bb717d075d129fd1fc7b96b2886824a1d153ed2f/objdetect/roi_align/op_host/op_api/roi_align.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-cv/blob/bb717d075d129fd1fc7b96b2886824a1d153ed2f/objdetect/roi_align/op_host/CMakeLists.txt
    role: implementation
created_at: "2026-08-25T19:39:32Z"
updated_at: "2026-08-25T20:47:20Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# ROIAlign A5 Direct Invoke 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | `cann_bench::roi_align` → `roi_align_npu` → `launch_roi_align`；Direct Invoke |
| 计算语义 | 对每个 ROI 的每个 `(channel, pooled_h, pooled_w)` bin 做规则网格双线性采样，再按采样点数求平均 |
| 输入输出 | `x[B,C,H,W]`、`boxes[R,5]` 与 `y[R,C,OH,OW]`；FP16/FP32、contiguous NCHW/ND |
| 执行类型 | 四条 Route 均为 `SIMT geometry + SIMT forward` 两节点图；两个 entry 都是 `KERNEL_TYPE_AIV_ONLY` wrapper，无 Cube/AIC 或 MIX_CV |
| Kernel 路线 | 重要性顺序：P0 R-003 FP32 unaligned；P1 R-001 FP16 unaligned；P2 R-002 FP16 aligned；P3 R-004 FP32 aligned。Route ID 保持 launcher 映射；fixed/adaptive sampling 是各 Route 内部属性分支 |
| 核心资源 | boxes/features/geometry/output GM 与线程私有标量；geometry 为 `R×12×4` B 的 invocation-local GM Tensor；无 AIV UB、dynamic UB、Device workspace、atomic 或 barrier |
| 来源闭包 | `direct_implementation_closed`：交付候选闭合 Torch schema、Meta/PrivateUse1、Direct POD、四实例 router、双 Kernel body、同流 GM 边与构建；固定官方源码仅支撑接口/语义/Host 编排相关事实，不把 Direct 派生符号表述为官方实现 |
| 验证状态 | 已完成源码闭包检查；本次知识提取未执行编译、真机、数值或性能测试。 |

## 接口与语义

### 计算语义

对 `boxes[r]=(batch,x0,y0,x1,y1)`，先把四个坐标乘 `spatial_scale`。`aligned=true` 时四端点再减 `0.5`；`aligned=false` 时不偏移，并将 `roiWidth=max(x1-x0,1)`、`roiHeight=max(y1-y0,1)`。令：

```text
binH = roiHeight / OH
binW = roiWidth  / OW
gridH = sampling_ratio > 0 ? sampling_ratio : max(ceil(binH), 1)
gridW = sampling_ratio > 0 ? sampling_ratio : max(ceil(binW), 1)
stepY = binH / gridH
stepX = binW / gridW
sampleY = roiStartH + ph*binH + (iy+0.5)*stepY
sampleX = roiStartW + pw*binW + (ix+0.5)*stepX
y[r,c,ph,pw] = Σ bilinear(x[batch,c], sampleY, sampleX) / (gridH*gridW)
```

坐标小于 `-1` 或大于对应空间尺寸时该样点贡献 0；`[-1,0]` 夹到 0；末像素区域把 low/high 都夹到 `size-1`。四个邻点按 `w1*v1 + w2*v2 + w3*v3 + w4*v4` 的固定次序相加。FP16 输入先转 FP32 做几何、插值和归约，仅最终结果转回 FP16。

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| `x` | `[B,C,H,W]`，Host materialize 为 contiguous NCHW | FP16/FP32 | rank=4；Direct Host 未单独拒绝零 `B/C/H/W`，但有效 ROI 与除数要求合法正维 |
| `boxes` | `[R,5]`，contiguous ND；列为 `(batch,x0,y0,x1,y1)` | 与 `x` 相同 | rank=2 且 dim1=5；batch 列先转 FP32 再转 int32；Direct 不做越界 batch 恢复 |
| `outputHeight` | Host 标量 | int64→int32 | 必须 `>0`；写入 POD 时窄化为 int32 |
| `outputWidth` | Host 标量 | int64→int32 | 必须 `>0`；写入 POD 时窄化为 int32 |
| `spatial_scale` | Host 标量 | double→float32 | 必须 `>0`；Direct 未显式拒绝 `+Inf` |
| `sampling_ratio` | Host 标量 | int64→int32 | Host 接受 `>=-1`；`<=0` 走 adaptive，`>0` 为固定 H/W 网格 |
| `aligned` | Host 标量 | bool | 选择编译期 `ALIGNED` 实例；true 偏移 `-0.5`，false 做最小 extent 1 |
| `y` | `[R,C,OH,OW]`，contiguous NCHW | 与 `x` 相同 | 每个输出标量由唯一 SIMT lane 完整写出，不与输入别名 |

### 入口与版本

交付注册 `roi_align(Tensor x, Tensor boxes, int outputHeight, int outputWidth, float spatial_scale, int sampling_ratio, bool aligned) -> Tensor y`，并绑定 Meta 与 `PrivateUse1`，不是 ACLNN 两段式接口。目标是 CANN 9.1.0、A5/Ascend 950。

固定官方提交中的 `aclnnRoiAlignV2` 是最接近的公开语义边界：同样接收 `[K,5] boxes`、FP16/FP32、`aligned` 与平均池化；但其文档明确标记 Ascend 950PR/950DT 不支持，且该提交的 forward `objdetect/roi_align` 没有 `op_host/arch35` 或 `op_kernel/arch35`。因此：

- **官方接口/实现相关来源**：Frontmatter 中的 V1/V2 文档、Op API、L0 launcher 与 OpProto，只证明参数布局、输出 shape、contiguous/格式转换、`aligned` 语义和 launcher 编排；不证明 A5 ACLNN 可用或 Direct body 来源。
- **交付 Direct 适配/补充**：Torch 注册、`ROIAlignTilingData`、A5 核数计算、四个模板实例、geometry GM、SIMT 插值、精确舍入 helper 与 direct CMake 均来自转换交付候选；按约束不把本地交付路径或不可达 artifact URL写入 `sources`。

## Host/Launcher 执行流程

### 参数校验与前处理

`roi_align_npu` 按顺序执行：设备 guard 绑定 `x.device()`；检查 `x.dim()==4`；检查 `boxes.dim()==2 && boxes.size(1)==5`；检查两输入 dtype 相同且为 FP16/FP32；检查 `OH/OW>0`、`spatialScale>0`、`samplingRatio>=-1`。之后分别执行 `x.contiguous()`、`boxes.contiguous()`，分配 `output[R,C,OH,OW]` 和 `geometry[R,12]`（INT32）。

Host 未检查 `boxes.device()==x.device()`、batch 列整数性/范围、四坐标有序性、`samplingRatio` 上限、int64→int32 窄化范围及乘法溢出；这些属于调用前约束。任一 `TORCH_CHECK` 失败都会在分配/launch 前终止。

### 参数、Workspace 与生命周期

设 `O=R*C*OH*OW`。`calc_roi_align_tiling` 把 shape/属性写入 POD，并查询 `GetCoreNumAiv()`：

```text
maxAiv = max(GetCoreNumAiv(), 1)
perCore0 = ceil(O / maxAiv)
perCore1 = max(perCore0, 1024)
perCore  = align_up(perCore1, 32)
blockDim = O==0 ? 1 : max(ceil(O / perCore), 1)
```

两个 Kernel 共享同一 POD。K-001 geometry 固定 `blockDim=1`；K-002 forward 使用上式 `blockDim`。无 opaque Device workspace；唯一跨节点中间量是 Torch 持有的 `geometry` GM Tensor，容量 `48R` B，从 K-001 写入前有效，至少保持到 K-002 同流提交完成。输入连续副本、output 与 geometry 的存储均由当前调用的 Tensor/allocator 管理。

### 启动图与失败传播

```text
roi_align_npu
  -> calc_roi_align_tiling(shape, attrs)
  -> dtypeTag × aligned router
  -> K-001 roi_align_geometry_entry<T,ALIGNED><<<1,current_stream>>>
       boxes[R,5] -> geometry[R,12] uint32 words
  -> same-current-stream ordering
  -> K-002 roi_align_entry<T,ALIGNED><<<blockDim,current_stream>>>
       features + geometry -> output[R,C,OH,OW]
```

| 节点/边 | entry/body | grid/lane | 输入→输出 | ordering、owner/lifetime | 失败传播 |
|---|---|---|---|---|---|
| K-001 geometry | `roi_align_geometry_entry<T,ALIGNED>` → `BuildROIGeometry` | 1 AIV block × 512 SIMT lane | boxes→geometry | 当前 stream；geometry Tensor 属于本次调用 | launcher 为 `void`，无逐节点返回码 |
| E-001 | geometry GM，offset `48*r`、extent `48R` B、word layout | N/A | K-001→K-002 | 同 stream 提交保证 producer 先于 consumer；不得在 K-002 完成前复用 | 无显式 event/错误短路 |
| K-002 forward | `roi_align_entry<T,ALIGNED>` → `ROIAlignForward` → `EvaluateOutput` | `blockDim` AIV blocks，每块 512 lanes | features+geometry→output | 当前 stream；每 lane 唯一 output owner | 同上 |

`OpCommand::RunOpApi` 只包装 direct-launch lambda 以接入框架 stream/error 机制；lambda 内只调用 `launch_roi_align`。代码没有 ACLNN ROIAlign、ATen compute、CPU 或外部算子 fallback。

## Route 与参数设计

### 分核与资源计算

K-001 以 `roiIndex=threadIdx.x; roiIndex<R; roiIndex+=512` 分配 ROI。K-002 先按 AIV block 切连续输出区间：

```text
devicePerCore = ceil(O / GetBlockNum())
begin = devicePerCore * blockIdx
count = min(devicePerCore, O-begin), begin>=O 时为 0
for local = threadIdx.x; local<count; local+=512:
    outIndex = begin+local
```

Host 的 `perCore` 只用于求 `blockDim`；Device 再以实际 `GetBlockNum()` 均分，所以两者不应混为一个 ABI 字段。`O<=UINT32_MAX` 时 entry 为 `OW/OH/C` 生成 magic/shift，并用 `Simt::UintDiv` 解码 `(r,c,ph,pw)`；更大输出退回 uint64 `%`/`/`。两个节点都直接 GM→线程私有标量→GM，不申请 UB。

### Route 选择

下表按实现知识的重要性 P0→P3 排列，不代表 Host 判断顺序。`Host 顺序`字段保留 `dtypeTag` 外层分发与 `aligned` 内层分发的真实短路关系。

| 重要性 | Route | 路线特征 | 适用域与实现前提 | Host 顺序、短路与 fallback |
|---:|---|---|---|---|
| P0 | R-003 FP32 unaligned | `<float,false>` 双 SIMT 节点；FP32 GM 与内部算术同精度，无末端降精度 | FP32、`aligned=false`、Host shape/属性校验通过；A5 | H0：`dtypeTag!=FLOAT16` 进入 else；H1：`aligned` 判断为 false 才命中。true 先命中 R-004；无 Device fallback |
| P1 | R-001 FP16 unaligned | `<half,false>` 双 SIMT 节点；输入升 FP32、输出末端降 FP16；extent 最小为1 | FP16、`aligned=false`、Host shape/属性校验通过；A5 | H0：`dtypeTag==FLOAT16`；H1：先检查 `aligned`，false 的 else 命中。true 先命中 R-002；无 Device fallback |
| P2 | R-002 FP16 aligned | `<half,true>` 双 SIMT 节点；FP16 I/O、FP32中间、端点减0.5 | FP16、`aligned=true`、Host shape/属性校验通过；A5 | H0：`dtypeTag==FLOAT16`；H1：`aligned` 的首分支直接命中；false 到 R-001；无 Device fallback |
| P3 | R-004 FP32 aligned | `<float,true>` 双 SIMT 节点；FP32全程、端点减0.5 | FP32、`aligned=true`、Host shape/属性校验通过；A5 | H0：`dtypeTag!=FLOAT16` 进入 else；H1：`aligned` 的首分支命中；false 到 R-003；无 Device fallback |

```text
dtypeTag = (features.dtype == Half) ? FLOAT16 : FLOAT32
if dtypeTag == FP16:
    if aligned: R-002 else: R-001
else:
    if aligned: R-004 else: R-003
# samplingRatio 不参与 Host Route 分发；进入 K-001 后：
if samplingRatio > 0: fixed grid
else: adaptive grid
```

### 模板/实现执行矩阵

| 重要性 | Route | key/selector | dtype/shape/platform 完整命中条件 | 执行拓扑与 Kernel 节点 | 实际模板/body | 内存与同步特征 | tail/fallback |
|---:|---|---|---|---|---|---|---|
| P0 | R-003 | float/false | FP32、unaligned、Host shape/attr 校验通过、A5 | geometry→forward SIMT | `BuildROIGeometry<float,false>`；`ROIAlignForward<float,false>` | geometry 48R B；同流；无末端降精度 | width/height clamp≥1；grid-stride tail |
| P1 | R-001 | half/false | FP16、unaligned、Host shape/attr 校验通过、A5 | geometry→forward SIMT | `BuildROIGeometry<half,false>`；`ROIAlignForward<half,false>` | geometry 48R B；同流；FP32 intermediate | width/height clamp≥1；grid-stride tail |
| P2 | R-002 | half/true | FP16、aligned、其余同上 | 同上 | `<half,true>` 两 body | 同上 | 端点减0.5，不做 extent clamp |
| P3 | R-004 | float/true | FP32、aligned、其余同上 | 同上 | `<float,true>` 两 body | geometry同上；无末端降精度 | 端点减0.5；grid-stride tail |

### 隐藏性能 Guard

| Guard | Host/Tiling 条件 | Device/资源原因 | 影响 Route | 不满足时去向 | 源码符号 |
|---|---|---|---|---|---|
| AIV core floor | `maxCoreNum=max(GetCoreNumAiv(),1)` | 防止平台查询异常造成除零 | 全部 | 退为1 core | Direct `calc_roi_align_tiling` |
| 每核最小工作 | `perCore=max(ceil(O/maxAiv),1024)` | 限制小任务启动过多 AIV block | 全部 | 用更多每核输出换较少 block | 同上 |
| 32元素对齐 | `perCore=align_up(perCore,32)` | 保持官方同族调度粒度；只影响 block 数，不分配 UB tile | 全部 | 无其它 Route | 同上 |
| 32位 flat decode | `O<=0xffffffff` | `Simt::UintDiv` 的 divisor/index 为 uint32 | 全部 | 大 O 用 uint64 `/`、`%` | `roi_align_entry` |
| fixed/adaptive | `samplingRatio>0` | fixed 可直接复用属性；非正值需由 ROI/bin 尺寸计算 H/W grid | 全部 | `<=0` 到 adaptive | `BuildROIGeometry` |
| 空输出 | Host 未禁止 `R==0`；`O==0` 时 `blockDim=1` | K-001/K-002 循环均无迭代 | 全部 | 返回空 output | `calc_roi_align_tiling`、两个 body |

### POD/ABI

`ROIAlignTilingData` 的 `sizeof=64, alignof=8`；`ROIAlignLaunchTiling` 的 `sizeof=72, alignof=8`。offset 为字节，均按标准 C++ ABI 顺序布局。

| 结构 | 字段 | 类型/位宽 | ABI 布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| ROIAlignTilingData | `batch` | int32/32 | off 0 | element-axis | `features.size(0)` 窄化 | 当前 body不读 | 调用约束用于 batch index |
| 同上 | `channels` | int32/32 | off 4 | element-axis | `features.size(1)` | feature stride、flat decode | 必须正且适合 uint32 divisor |
| 同上 | `height` | int32/32 | off 8 | element-axis | `features.size(2)` | feature stride、boundary | 有效调用需正 |
| 同上 | `width` | int32/32 | off 12 | element-axis | `features.size(3)` | feature stride、boundary | 有效调用需正 |
| 同上 | `numRois` | int32/32 | off 16 | ROI | `rois.size(0)` | K-001 loop | 可为0 |
| 同上 | `pooledHeight` | int32/32 | off 20 | element-axis | `outputHeight` | bin除数、flat decode | Host保证>0，窄化未审计 |
| 同上 | `pooledWidth` | int32/32 | off 24 | element-axis | `outputWidth` | bin除数、flat decode | 同上 |
| 同上 | `samplingRatio` | int32/32 | off 28 | samples/axis | `samplingRatio` | fixed/adaptive selector | Host仅保证>=-1 |
| 同上 | `groupWidth` | int32/32 | off 32 | output/group | 固定1 | 当前 body不读 | inactive 保留字段 |
| 同上 | `tilesPerChannel` | int32/32 | off 36 | tile/channel | 固定1 | 当前 body不读 | inactive 保留字段 |
| 同上 | `spatialScale` | float/32 | off 40 | scale | `static_cast<float>(spatialScale)` | K-001 坐标缩放 | Host只检查>0 |
| 同上 | padding | 4 B | off 44 | byte | ABI 自动填充 | 不读 | 对齐后续 uint64 |
| 同上 | `totalOutputElements` | uint64/64 | off 48 | output element | `R*C*OH*OW` | 32/64 decode selector | 中间乘法从 uint64 R 开始 |
| 同上 | `totalWorkItems` | uint64/64 | off 56 | output element | 等于上一字段 | block分段/count | 当前实现一 work item=一 output |
| ROIAlignLaunchTiling | `data` | struct/512 | off 0 | POD | `calc_roi_align_tiling` | 两 entry 按值接收 | 结构必须字节一致 |
| 同上 | `blockDim` | uint32/32 | off 64 | AIV block | Host core公式 | K-002 launch grid | 至少1 |
| 同上 | tail padding | 4 B | off 68 | byte | ABI 自动填充 | 不读 | struct总长72 |

geometry 不是 POD，而是跨节点 GM 协议：每 ROI 12 个 uint32 word。`0=batch`、`1=gridH`、`2=gridW`、`4=startW bits`、`5=startH bits`、`6=binH bits`、`7=binW bits`、`8=stepY bits`、`9=stepX bits`；word 3/10/11 未写也不读。这个稀疏布局不得压缩，否则 K-002 offset ABI 会改变。

### Route 源码闭包

| 重要性 | Route | Key/selector | Host/Tiling producer | POD/参数 | Kernel entry/router 节点 | Kernel body/直接依赖 | 构建接线 |
|---:|---|---|---|---|---|---|---|
| P0 | R-003 | float/false | Direct `roi_align_npu`、`calc_roi_align_tiling` | `ROIAlignLaunchTiling` | `launch_roi_align`→两个 `<float,false>` entry | `BuildROIGeometry`、`ROIAlignForward`、bilinear/rounding helpers，T=float | Direct `register_direct_launch_op` |
| P1 | R-001 | half/false | 同上 | 同上 | 两个 `<half,false>` entry | 同上，T=half、ALIGNED=false | 同上 |
| P2 | R-002 | half/true | 同上 | 同上 | 两个 `<half,true>` entry | 同上，T=half、ALIGNED=true | 同上 |
| P3 | R-004 | float/true | 同上 | 同上 | 两个 `<float,true>` entry | 同上，T=float、ALIGNED=true | 同上 |

这里的 Direct 文件/符号是交付闭包身份，不是 Frontmatter 官方来源；固定官方 `roi_align` 文件仅提供相关接口与编排对照。

## Kernel 实现

### 公共执行流程

下列逐 Route 章节按重要性 P0→P3 排列，R-ID 保持不变；这不是 Host 判断顺序，真实 dtype→aligned 嵌套短路见“Route 选择”。所有 Route 都先在一个 512-lane AIV-only SIMT 节点中把每 ROI 重复使用的端点、bin、grid 与 step 写入 geometry，再在第二节点中让一个 lane 独占一个输出标量。K-002 每个 output 只读一次 geometry，但循环读取 `4*gridH*gridW` 个 feature 标量。两节点均无 UB/shared memory；同步只来自同 stream 的 Kernel 顺序。

### P0 / Route R-003：FP32 unaligned

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | Direct plugin | `roi_align_npu` | Float、`aligned=false` | `dtypeTag=FLOAT32` |
| Router | Direct kernel | `launch_roi_align` | dtypeTag else && !aligned | 两个 `<float,false>` entry |

#### Device 数据流

##### 函数级调用链

```text
launch_roi_align
  -> roi_align_geometry_entry<float,false><<<1>>>
    -> BuildROIGeometry<float,false>(512 lanes) -> geometry GM
  -> same stream
  -> roi_align_entry<float,false><<<blockDim>>>
    -> GetUintDivMagicAndShift(W/H/C)
    -> ROIAlignForward<float,false>(512 lanes)
      -> EvaluateOutput -> BuildBilinearPoint -> SampleBilinear
      -> AccumulateSample -> FoldAccumulator -> CorrectedDivByPositiveInt
      -> FP32 output GM
```

##### 源码等价伪码

```text
# K-001
for r = lane; r<R; r+=512:
  batch = int(boxes[5r])
  endpoints = boxes[5r+1:5r+5] * spatialScale
  roiW/H = max(end-start, 1)
  binW/H = roiW/H / OW/OH
  gridW/H = ratio>0 ? ratio : max(ceil(binW/H),1)
  geometry[12r + {0,1,2,4..9}] = batch, grid, start, bin, step
# K-002
for local = lane; local<count; local+=512:
  outIndex=begin+local; decode -> (r,c,ph,pw)
  acc[0..7]=0
  for iy,ix in grid:
    sample = ordered_fp32_bilinear(features, geometry, ph,pw,iy,ix)
    acc[(iy*gridW+ix)&7] += sample
  output[outIndex] = (acc0+...+acc7)/(gridH*gridW)
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| boxes GM | `5r` | `20R` B | FP32/ND | caller | K-001 | Tensor | 5 scalar loads |
| geometry GM | `12r` | `48R` B | uint32 words | K-001 | K-002 | Tensor | 同 ABI |
| features/output GM | NCHW flat | `4BCHW`/`4O` B | FP32 | caller/K-002 | K-002/caller | Tensor | 唯一输出写 |
| thread registers | endpoints、weights、4 values、8 accumulators、index magic | 固定标量 | FP32/u32/u64 | 当前 lane | 当前 lane | 单 output iteration | 无跨 lane 共享 |

##### 分层内存布局

N/A：无 AIV UB/dynamic UB。

##### 字节账与复用顺序

```text
UB_total=0; dynamic_ub=N/A; workspace_total=0; inter_kernel_GM=48R B
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| geometry ROI slice | K-001 | K-002 | 调用后 | 同 stream | K-002完成前有效 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| 输入/输出 | FP32 GM scalar | caller/K-002 | interpolation/caller | values | 无 dtype cast |
| K-001→K-002 | current stream ordering | geometry store | K-002 geometry load | 48R B GM | 无显式 event/barrier |
| 乘法 | `__fmaf_rn(a,b,0)` | FP32 operands | geometry/weight/product | 单次 RN rounding | build禁用 contraction以保持加减边界 |
| 归约 | 8个有序 accumulator | sample values | 固定 lane0..7 fold | FP32 sum | sample编号 `&7`，不跨线程 |
| 除法 | power-of-two scale / native quotient+FMA residual / exact fallback | rawSum、正整数count | output store | IEEE RN ties-to-even | subnormal/大除数有 fallback |
| tail | loop bounds | R/O/count | lane return | output/geometry | `r<R`、`local<count`、`count==0 return` |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Router | Direct kernel | `launch_roi_align` | FP32/false映射 |
| Geometry | Direct kernel | `BuildROIGeometry<float,false>` | FP32 unaligned geometry |
| Forward | Direct kernel | `ROIAlignForward<float,false>` | FP32最终store |

### P1 / Route R-001：FP16 unaligned

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | Direct plugin | `roi_align_npu` | dtype相等且为 Half、`aligned=false` | `dtypeTag=FLOAT16` |
| Router | Direct kernel | `launch_roi_align` | `dtypeTag==FLOAT16 && !aligned` | 两个 `<half,false>` entry |
| Geometry | Direct kernel | `BuildROIGeometry<half,false>` | `samplingRatio>0` 或 `<=0` | fixed/adaptive grid |

#### Device 数据流

##### 函数级调用链

```text
launch_roi_align
  -> roi_align_geometry_entry<half,false><<<1>>>
    -> BuildROIGeometry<half,false>(512 lanes) -> geometry GM
  -> same stream
  -> roi_align_entry<half,false><<<blockDim>>>
    -> GetUintDivMagicAndShift(W/H/C)
    -> ROIAlignForward<half,false>(512 lanes)
      -> EvaluateOutput -> BuildBilinearPoint -> SampleBilinear
      -> AccumulateSample -> FoldAccumulator -> CorrectedDivByPositiveInt
      -> cast half -> output GM
```

##### 源码等价伪码

```text
# K-001
for r = lane; r<R; r+=512:
  batch = int(float(boxes[5r]))
  endpoints = float(boxes[5r+1:5r+5]) * spatialScale
  roiW/H = max(end-start, 1)
  binW/H = roiW/H / OW/OH
  gridW/H = ratio>0 ? ratio : max(ceil(binW/H),1)
  geometry[12r + {0,1,2,4..9}] = batch, grid, start, bin, step
# K-002
for local = lane; local<count; local+=512:
  outIndex=begin+local; decode -> (r,c,ph,pw)
  acc[0..7]=0
  for iy,ix in grid:
    sample = ordered_fp32_bilinear(features, geometry, ph,pw,iy,ix)
    acc[(iy*gridW+ix)&7] += sample
  output[outIndex] = half((acc0+...+acc7)/(gridH*gridW))
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| boxes GM | `5*r` | `5R` | half/ND | caller | K-001 lane | contiguous Tensor | 每 ROI 读5元素 |
| geometry GM | `12*r` | `12R=48R B` | uint32 word ABI | K-001 | K-002 | invocation-local Tensor | word 3/10/11 hole |
| features GM | `batch*C*HW+c*HW+pointOffset` | `B*C*H*W` | half/NCHW | caller | K-002 | input Tensor | 每样点4个不规则读 |
| thread registers | endpoints、weights、4 values、8 accumulators、index magic | 固定标量 | FP32/u32/u64 | 当前 lane | 当前 lane | 单 output iteration | 无跨 lane 共享 |
| output GM | `outIndex` | `O` | half/NCHW | K-002 lane | caller | output Tensor | 唯一写 |

##### 分层内存布局

N/A：两个 SIMT 节点均不分配 AIV UB 或 dynamic UB；实际路径为 GM→线程私有标量→GM，中间 geometry 位于 GM。

##### 字节账与复用顺序

```text
UB_total(K-001)=0; UB_total(K-002)=0
dynamic_ub=N/A
workspace_total=0
inter_kernel_GM=alignof(uint32) naturally aligned, 48R bytes
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| geometry `[12r,12r+12)` | K-001 ROI owner lane | 所有属于 ROI r 的 K-002 lanes | 调用结束后 allocator 回收 | 同 stream K-001→K-002 | K-002 完成前 Tensor storage 不回收 |
| `Accumulator8` | 当前 sample | `FoldAccumulator` | 下一 output iteration | 单线程程序序 | 每 lane独占 output |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| K-001→K-002 | current stream ordering | geometry store | K-002 geometry load | 48R B GM | 无显式 event/barrier |
| 乘法 | `__fmaf_rn(a,b,0)` | FP32 operands | geometry/weight/product | 单次 RN rounding | build禁用 contraction以保持加减边界 |
| 归约 | 8个有序 accumulator | sample values | 固定 lane0..7 fold | FP32 sum | sample编号 `&7`，不跨线程 |
| 除法 | power-of-two scale / native quotient+FMA residual / exact fallback | rawSum、正整数count | final cast | IEEE RN ties-to-even | subnormal/大除数有 fallback |
| tail | loop bounds | R/O/count | lane return | output/geometry | `r<R`、`local<count`、`count==0 return` |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host producer | Direct plugin/kernel | `roi_align_npu`、`calc_roi_align_tiling` | 校验、contiguous、POD、core公式 |
| Kernel router | Direct kernel | `launch_roi_align` | FP16/unaligned映射、双节点顺序 |
| Device body | Direct kernel | `BuildROIGeometry<half,false>`、`ROIAlignForward<half,false>` | geometry hoist、输出独占SIMT |
| Helper | Direct kernel | `BuildBilinearPoint`、`SampleBilinear`、`CorrectedDivByPositiveInt` | boundary、四点插值、舍入 |

### P2 / Route R-002：FP16 aligned

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | Direct plugin | `roi_align_npu` | Half、`aligned=true` | `dtypeTag=FLOAT16` |
| Router | Direct kernel | `launch_roi_align` | FP16 && aligned | 两个 `<half,true>` entry |

#### Device 数据流

##### 函数级调用链

```text
geometry_entry<half,true> -> BuildROIGeometry<half,true> -> same-stream geometry
roi_align_entry<half,true> -> ROIAlignForward<half,true> -> EvaluateOutput -> output
```

##### 源码等价伪码

```text
同 R-001，但 K-001 在缩放四端点后各减0.5，不执行 roiW/roiH 的 min-1 clamp；
其余 grid、双线性、8路归约、除法与 half cast 完全相同。
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| boxes/geometry/features/output | 同 R-001 | `5R/12R/BCHW/O` | half、uint32 | K-001/K-002 | K-002/caller | Tensor | 仅几何公式不同 |
| thread registers | 同 R-001，加常量0.5 | 固定标量 | FP32 | lane | lane | 单迭代 | 无共享 |

##### 分层内存布局

N/A：同 R-001，GM→线程标量→GM。

##### 字节账与复用顺序

```text
UB_total=0; dynamic_ub=N/A; workspace_total=0; inter_kernel_GM=48R B
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| geometry ROI slice | K-001 | K-002 | 调用后 | 同 stream | 同 R-001 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| alignment | compile-time `if constexpr(ALIGNED)` | scaled endpoints | bin geometry | geometry words | FP32减0.5；不做 extent clamp |
| 其余 | 同 R-001 | 同 R-001 | 同 R-001 | 同 R-001 | 同 R-001 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Router | Direct kernel | `launch_roi_align` | true映射 `<half,true>` |
| Body | Direct kernel | `BuildROIGeometry<half,true>` | 四端点-0.5、无min-1 |
| Forward | Direct kernel | `ROIAlignForward<half,true>` | 与R-001相同输出协议 |

### P3 / Route R-004：FP32 aligned

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | Direct plugin | `roi_align_npu` | Float、`aligned=true` | `dtypeTag=FLOAT32` |
| Router | Direct kernel | `launch_roi_align` | dtypeTag else && aligned | 两个 `<float,true>` entry |

#### Device 数据流

##### 函数级调用链

```text
geometry_entry<float,true> -> BuildROIGeometry<float,true> -> geometry
roi_align_entry<float,true> -> ROIAlignForward<float,true> -> EvaluateOutput -> FP32 output
```

##### 源码等价伪码

```text
同 R-003，但四端点缩放后减0.5，roiW/roiH 不做min-1；
其余 boundary、sample loop、8路归约和 corrected division 不变。
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| boxes/geometry/features/output | 同 R-003 | `20R/48R/4BCHW/4O` B | FP32/uint32 | K-001/K-002 | K-002/caller | Tensor | 仅 aligned geometry不同 |
| registers | 同 R-003 | 固定标量 | FP32/index | lane | lane | 单迭代 | 无共享 |

##### 分层内存布局

N/A：无 AIV UB/dynamic UB。

##### 字节账与复用顺序

```text
UB_total=0; dynamic_ub=N/A; workspace_total=0; inter_kernel_GM=48R B
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| geometry ROI slice | K-001 | K-002 | 调用后 | 同 stream | 同前 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| alignment | compile-time true | scaled endpoints | bin geometry | geometry | FP32减0.5，无min-1 |
| 其余 | 同 R-003 | 同上 | 同上 | 同上 | 同 R-003 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Router | Direct kernel | `launch_roi_align` | FP32/true映射 |
| Geometry | Direct kernel | `BuildROIGeometry<float,true>` | aligned geometry |
| Forward | Direct kernel | `ROIAlignForward<float,true>` | FP32输出 |

## 算子特定优化

### Trick T-001：直接消费五列 boxes，避免 V1 重建 ROI

#### 触发与源码依据

- 适用 Route：R-001～R-004。
- 触发条件：调用接口已提供 `[R,5]` 的 `(batch,x0,y0,x1,y1)` 且 dtype 与 features 相同。
- Golden 来源：[`objdetect/roi_align/op_host/op_api/aclnn_roi_align_v2.cpp:191-192`](https://gitcode.com/cann/ops-cv/blob/bb717d075d129fd1fc7b96b2886824a1d153ed2f/objdetect/roi_align/op_host/op_api/aclnn_roi_align_v2.cpp)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
auto boxesContiguous = l0op::Contiguous(boxes, uniqueExecutor.get());
CHECK_RET(boxesContiguous != nullptr, ACLNN_ERR_INNER_NULLPTR);
```

#### 机制与设计原因

官方 V2 Host 把连续化后的五列 `boxes` 直接交给 ROIAlign 核心；相对地，官方 V1 Host 会对独立 `batchIndices` 执行 Reshape、Cast，再与四列 rois 做 ConcatD。Direct 入口本来就采用 V2 形态，K-001 直接从 `boxes[5r:5r+5]` 读取，因而不物化 reshape/cast/concat 中间 Tensor；这减少 Host executor 节点与 GM 中间量。Direct 仍必须先 `contiguous()`，因为 Device 使用固定 `5*r+k` 地址公式。

#### 迁移边界

- 适用：上游能稳定提供 `[R,5]`、batch 列与坐标同 dtype 的 ROIAlign 接口。
- 前提：batch 值是可精确转为 int32 的合法整数；boxes contiguous 或在 launch 前显式物化。
- 失效：若 ABI 是四列 rois + 独立 INT batchIndices，必须保留转换/拼接，或重写 Device 为双输入；不能按五列越界读取。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

把非连续 boxes 的 `data_ptr` 直接交给固定 `5*r+k` Device 地址公式会忽略 stride；固定官方 V2 源码明确先做 `Contiguous`。固定仓未提供 Direct A5 body 的可验证反例。

### Trick T-002：两节点 geometry hoist 与输出标量独占

#### 触发与源码依据

- 适用 Route：R-001～R-004。
- 触发条件：同一 ROI 的几何量被 `C*OH*OW` 个输出复用，且两个 Kernel 在同一 stream 顺序提交。
- Golden 来源：[`objdetect/roi_align/op_host/op_api/roi_align.cpp:83-84`](https://gitcode.com/cann/ops-cv/blob/bb717d075d129fd1fc7b96b2886824a1d153ed2f/objdetect/roi_align/op_host/op_api/roi_align.cpp)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
auto ret = ADD_TO_LAUNCHER_LIST_AICORE(ROIAlign, OP_INPUT(self, boxes), OP_OUTPUT(out),
    OP_ATTR(spatialScale, outputHeight, outputWidth, samplingRatio, roiEndMode, mode));
```

#### 机制与设计原因

官方 L0 只锁定 ROI 数决定输出第0维以及核心 launcher 的参数语义；固定提交没有 forward A5 Kernel。交付 Direct 补充把 ROI-only 的 scaled endpoints、bin、grid、step 先物化为 `48R` B geometry，使 K-002 不再对每个 `(c,ph,pw)` 重算这些值；随后一 lane 独占一个输出，局部完成所有 sample 累加并只写一次 output，消除 atomic、跨 lane reduction 和中间 partial output。代价是一个小 Kernel 与一次 geometry GM 交接。

#### 迁移边界

- 适用：`C*OH*OW` 足以摊薄 geometry Kernel 与 `48R` B 中间量，且 ROI 几何与 channel 无关。
- 前提：geometry word ABI、同流可见性及 Tensor lifetime 全部保持；每 output 的采样循环可由单 lane承载。
- 失效：跨 stream 启动必须增加 event；若几何依赖 channel/output value，则不能按 ROI 缓存；极小工作量可能不值得多一次 launch。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

只按 Host 书写顺序假设跨流可见，或提前释放 geometry，都会使 K-002 读取未完成/失效数据。固定仓没有 forward A5 body，未提供同机制的可验证官方反例。

## 模板与实现对比

| 对比维度 | P0 R-003 FP32 false | P1 R-001 FP16 false | P2 R-002 FP16 true | P3 R-004 FP32 true | 设计选择依据 |
|---|---|---|---|---|---|
| 命中条件/优先级 | Float、false | Half、false | Half、true | Float、true | 重要性与Host嵌套顺序分离；真实短路见Route表 |
| 模板与 dtype | `<float,false>` | `<half,false>` | `<half,true>` | `<float,true>` | dtype决定GM load/store与末端cast；bool消除几何运行时分支 |
| 循环与分核 | 双Kernel、512 lanes | 同左 | 同左 | 同左 | geometry按ROI；forward按output |
| Queue/TBuf/寄存器/dynamic UB | 仅线程寄存器 | 同左 | 同左 | 同左 | 无UB/shared/atomic |
| 内存总占用与复用 | geometry 48R B；FP32 I/O | geometry 48R B；FP16 I/O | 同左 | geometry 48R B；FP32 I/O | ROI-only geometry跨输出复用 |
| 搬运/SIMT API | GM scalar、`asc_vf_call` | 同左 | 同左 | 同左 | 不规则四邻点读适合输出独占SIMT |
| 同步、精度与 tail | FP32全程；min-1 | 同流；FP32中间→half；min-1 | 同流；FP32中间→half；-0.5 | FP32全程；-0.5 | 8路有序归约、corrected divide、grid-stride bounds |
| fallback/失败边界 | dtype else由Host封闭为Float | 无外部fallback | 同左 | dtype else由Host封闭为Float | 大O仅切换u64 flat decode，不切Route |

## 平台差异

| 项目 | A2 | A3 | A5 |
|---|---|---|---|
| 支持状态 | 固定官方 ACLNN V2 文档支持；本卡不覆盖 Direct | 固定官方 ACLNN V2 文档支持；本卡不覆盖 Direct | 固定官方 ACLNN V2 文档明确不支持；本卡仅覆盖交付 Direct A5 实现 |
| Host/Launcher | 官方 executor + TransData + L0 launcher | 同左 | Torch PrivateUse1 + Direct POD + 两次当前流 launch |
| Kernel/资源 | 固定来源未纳入本卡的官方 body | 同左 | AIV-only SIMT geometry→forward；geometry 48R B；无UB/workspace |

官方“不支持 A5”与 Direct A5 交付不冲突：前者限定公开 ACLNN/API，后者是独立注册的 Direct Invoke 入口。不得据此把 `aclnnRoiAlignV2` 宣称为 950 支持。

## 限制与失败边界

- Direct Host 仅检查 rank/boxes列数/dtype/属性下界；batch index、ROI 坐标、同设备、正 `B/C/H/W`、有限 `spatialScale` 与 int32 窄化范围由调用方保证。
- `sampling_ratio=-1` 是 Direct 补充；固定官方 V2 只接受 `>=0`。Direct 中 `-1` 与 `0` 都走 `<=0` adaptive branch。
- geometry 的 word 3/10/11 是未写空洞；consumer也不读。复用实现必须保持12-word stride，或同时原子地修改 producer/consumer ABI。
- `gridHeight*gridWidth` 在 int32 中相乘后转 uint32；超大自适应网格可能溢出。目标任务范围把 sampling ratio 限在 `[-1,16]`，但 Host 未编码上限。
- output 总量从 `uint64_t(R)*C*OH*OW` 计算；shape/属性先窄化 int32，超范围调用可能在到达该乘法前改变语义。
- K-001/K-002 launcher 返回 `void`，无逐节点错误码和 consumer 抑制；依赖框架异步错误机制。
- 无 CPU、ACLNN、ATen compute 或外部算子 fallback；不合法 dtype 在 Host 已失败，大 output 仅回退到 uint64 解码。
- 固定官方提交没有 forward A5 Host/Tiling/Kernel body，Direct 的512-lane选择、精确算术和geometry协议是交付补充，不可宣称为官方实现。
- 本次知识提取未执行编译、真机、数值或性能测试。

## 源码索引

### 链路索引

| 链路阶段 | 文件 | 关键符号 | 支撑内容 |
|---|---|---|---|
| 入口声明/约束 | `objdetect/roi_align/docs/aclnnRoiAlignV2.md` | `aclnnRoiAlignV2GetWorkspaceSize` | 官方V2 `[K,5] boxes`、dtype/shape/aligned语义与950不支持边界 |
| 入口声明/约束 | `objdetect/roi_align/op_graph/roi_align_proto.h` | `REG_OP(ROIAlign)` | ROI五列语义、属性与dtype |
| 官方Host实现 | `objdetect/roi_align/op_host/op_api/aclnn_roi_align_v2.cpp` | `CheckParams`、`aclnnRoiAlignV2GetWorkspaceSize` | V2校验、Contiguous、aligned映射、executor链 |
| 相关旧版实现 | `objdetect/roi_align/op_host/op_api/aclnn_roi_align.cpp` | `aclnnRoiAlignGetWorkspaceSize` | V1 Reshape/Cast/ConcatD 对照 |
| L0 launcher | `objdetect/roi_align/op_host/op_api/roi_align.cpp` | `ROIAlignV2`、`ADD_TO_LAUNCHER_LIST_AICORE` | 输出shape与核心属性顺序 |
| 构建接线 | `objdetect/roi_align/op_host/CMakeLists.txt` | `add_modules_sources` | 官方 ACLNN Host module接线；非Direct构建 |

每行文件均存在于 Frontmatter `sources`。Direct 交付文件按约束不写本机路径，也不伪造公开 blob URL。

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | 64 B POD、72 B launch struct、12-word geometry | 字段顺序/位宽/offset；geometry稀疏word位置 | Direct `ROIAlignTilingData`、`GeometryWord` |
| 调用顺序 | geometry→forward 两节点 | 同一 stream；K-001必须先于K-002 | Direct `launch_roi_align` |
| workspace/内存 | Device workspace=0；geometry=48R B | geometry owner/lifetime、12-word stride | Direct `roi_align_npu`、`BuildROIGeometry` |
| 同步 | 无barrier/atomic/event；每output唯一owner | 跨节点必须同流或补event | Direct `ROIAlignForward` |
| 精度与尾块 | FP32 intermediate、显式RN、8路fold、corrected integer division | 操作次序、末端cast、bounds guard | Direct arithmetic helpers、`EvaluateOutput` |
| 失败边界 | Host校验失败不launch；Device无外部fallback | 不得把dtype else开放给非FP32；不得忽略窄化/非法batch | Direct `roi_align_npu`、`launch_roi_align` |
