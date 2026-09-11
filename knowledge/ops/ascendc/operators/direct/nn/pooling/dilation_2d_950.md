---
type: Operator
title: "Dilation2D 950 Direct Invoke 算子知识"
description: "说明 cann_bench::dilation_2_d、calc_dilation_2_d_tiling 与 launch_dilation_2_d_half 在 950 上的接口语义、Host/Launcher 参数生成、Route 选择、单 Kernel 启动图与逐节点实现。"
tags: [task.implementation, task.lookup, topic.data_movement, topic.memory, topic.precision, topic.programming_model]
status: stable
sources:
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/pooling/dilation2_d/README.md
    role: header
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/pooling/dilation2_d/op_host/dilation2_d_def.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/pooling/dilation2_d/op_host/dilation2_d_infershape.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/pooling/dilation2_d/op_host/arch35/dilation2_d_tiling.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/pooling/dilation2_d/op_kernel/arch35/dilation2_d_tiling_data.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/pooling/dilation2_d/op_kernel/arch35/dilation2_d_tiling_key.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/pooling/dilation2_d/op_kernel/arch35/dilation2_d.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/pooling/dilation2_d/op_kernel/arch35/dilation2_d_simt.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/pooling/dilation2_d/op_kernel/CMakeLists.txt
    role: implementation
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/pooling/dilation2_d/CMakeLists.txt
    role: implementation
created_at: "2026-08-25T19:30:42Z"
updated_at: "2026-09-08T14:24:40Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# Dilation2D 950 Direct Invoke 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | `cann_bench::dilation_2_d` → `dilation_2_d_npu` → `calc_dilation_2_d_tiling` → `launch_dilation_2_d_half`；入口类型为 Direct Invoke。 |
| 计算语义 | 对每个输出位置和通道，计算有效膨胀窗口内 `x + filter` 的最大值；SAME/CALCULATED 的越界输入按 `-inf` 参与加法语义。 |
| 输入输出 | `x` 为连续 4-D NHWC/NCHW，`filter` 为对应的 3-D `(fH,fW,C)`/`(C,fH,fW)`，均为 FP16；输出保持 layout 与 dtype。 |
| 执行类型 | R-001 为补充实现 `AIV_VECTOR`；R-002～R-005 为官方源码适配的 `SIMT`。全部为单 Kernel，均无 Cube/AIC 或 MIX_CV 可达节点。 |
| Kernel 路线 | P0 R-001 conditional NHWC FP16 行带 Vector；P1 R-002 active NHWC SIMT32；P2 R-004 active NCHW SIMT32；P3 R-003 conditional NHWC SIMT64；P4 R-005 conditional NCHW SIMT64。另有 D-001 dormant 整数模板分支。P 级是知识组织顺序，不是 Host selector 数值。 |
| 核心资源 | R-001 使用 GM、三条 depth=1 UB Queue 与 RegTensor；SIMT 路线直接访问 GM、使用线程寄存器，无显式 TQue/TBuf；所有路线 workspace 为 0。 |
| 来源闭包 | `direct_implementation_closed`：Direct schema/Meta/NPU glue、shape/padding、平台参数、两套 POD、Route selector、三个 entry、Vector/SIMT body、同步/tail 与构建接线均已闭合。 |
| 验证状态 | 已完成源码闭包检查；本次知识提取未执行编译、真机、数值或性能测试。 |

## 接口与语义

### 计算语义

令输入空间尺寸为 `H,W`，滤波器为 `fH,fW`，步幅为 `sH,sW`，膨胀率为 `rH,rW`，上/左 padding 为 `pT,pL`。对 NHWC：

```text
ih = oh*sH + fh*rH - pT
iw = ow*sW + fw*rW - pL
y[b,oh,ow,c] = amax_{fh,fw}(x_pad[b,ih,iw,c] + filter[fh,fw,c])
x_pad(out-of-bound) = -inf
```

NCHW 仅改变地址布局：输出为 `y[b,c,oh,ow]`，filter 为 `filter[c,fh,fw]`。有效滤波器尺寸为 `effH=fH+(fH-1)*(rH-1)`、`effW=fW+(fW-1)*(rW-1)`。SAME 使用 `oH=ceil(H/sH)`、`oW=ceil(W/sW)` 并把总 padding 的一半取整到 top/left；VALID 的 padding 为 0；CALCULATED 使用显式 `[top,bottom,left,right]` 和 `ceil_mode`。

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| `x` | NHWC `[N,H,W,C]` 或 NCHW `[N,C,H,W]`，contiguous | FP16 | rank=4；Direct 实现不隐式执行 `Contiguous`。 |
| `filter` | NHWC `(fH,fW,C)` 或 NCHW `(C,fH,fW)`，contiguous | FP16 | rank=3；dtype、device 与 `x` 相同；通道数相等；`fH,fW>0` 才能通过 tiling。 |
| `strides` | NHWC `[1,sH,sW,1]` 或 NCHW `[1,1,sH,sW]` | `int64[4]` | N/C 分量必须为 1，H/W 分量必须为正。 |
| `rates` | NHWC `[1,rH,rW,1]` 或 NCHW `[1,1,rH,rW]` | `int64[4]` | N/C 分量必须为 1，H/W 分量必须为正。 |
| `padding_mode` | 标量字符串 | String | `SAME`、`VALID`、`CALCULATED`；Direct schema 要求显式传入。 |
| `pads` | `[top,bottom,left,right]` | `int64[4]` | Direct schema 要求 4 项；CALCULATED 时非负且每项小于对应有效滤波器尺寸。 |
| `ceil_mode` | 标量 | Bool | 只改变 CALCULATED 输出尺寸公式。 |
| `data_format` | 标量字符串 | String | 只接受 `NHWC` 或 `NCHW`。 |
| `y` | `[N,oH,oW,C]` 或 `[N,C,oH,oW]`，contiguous | FP16 | 由 `torch::empty` 在 `x` 的 device/options 上分配；空输出直接返回，不启动 Kernel。 |

### 入口与版本

Direct schema 为 `cann_bench::dilation_2_d(Tensor x, Tensor filter, int[] strides, int[] rates, str padding_mode, int[] pads, bool ceil_mode, str data_format) -> Tensor`；Meta 与 PrivateUse1 实现复用 `AnalyzeDilation2D`。NPU 实现只接受 FP16、连续输入和同设备 filter，随后按值传入 POD 并在当前 NPU stream 上启动单个 Kernel。它不是 ACLNN workspace/executor 入口，也不是官方图模式 Host/Tiling 入口。

转换边界必须保持两层：

- **official-adapted SIMT**：R-002～R-005 机械保留官方 commit `26311e64257d6d54e5876cf1cc95104a3f378860` 的 POD 字段顺序、NHWC/NCHW 模板分发、32/64 位索引选择、magic division、grid-stride 遍历、地址公式和滤波循环；转换仅把框架 tiling 指针改为 Direct 按值 launch，并补充 Direct 语义要求的 NaN 传播以及越界 `-inf + filter` 的 `+inf` 边界。
- **supplemental Vector**：R-001 是转换实现额外加入的 NHWC/FP16 行带快路，官方固定 commit 中没有该 selector、POD 或 Vector body。它只能称“补充实现/补充路线”，不能称为官方 Dilation2D Vector 实现；UB 条件不成立时必须回到 official-adapted SIMT 闭包。

官方 README、OpDef、`SUPPORT_COMPUTE_UNIT` 和 Kernel CMake 共同证明 Ascend 950 支持；A2/A3 在官方支持表中明确不支持。目标版本为 CANN 9.1.0。

## Host/Launcher 执行流程

### 参数校验与前处理

1. `dilation_2_d_npu` 建立输入 device guard，检查 FP16、`x/filter` dtype 一致、二者 contiguous 且位于同一 device。
2. `AnalyzeDilation2D` 检查 rank、属性长度、layout/padding 枚举、N/C stride/rate 为 1、H/W stride/rate 为正及通道一致；所有维度再经 `CheckedI32` 收窄到非负 `int32_t`。
3. Host 以 `int64_t` 计算 `effH/effW`、`oH/oW` 和 `padTop/padLeft`；CALCULATED 额外校验四个 pad。输出尺寸再经 `CheckedI32`。
4. `torch::empty` 分配输出；`y.numel()==0` 时直接返回，因此空域没有 Device Route。
5. `calc_dilation_2_d_tiling` 先填 official-adapted SIMT POD 和默认 `route=0`，再查询 AIV 核数/UB 并尝试 supplemental Vector selector；只有完整资源谓词成立才覆盖为 `route=1`。
6. `launch_dilation_2_d_half` 先按 `route`，再按 `isNCHW` 选择三个 entry 之一，在当前 stream 上发射。

任何 shape/属性/收窄/tiling 错误都在 launch 前终止。`OpCommand::RunOpApi("Dilation2DDirect", lambda)` 包装 Direct launch，但 lambda 固定返回 0；转换实现没有把异步 Device 错误映射为该返回值。

### 参数、Workspace 与生命周期

`Dilation2DLaunchParams` 是 NPU glue 栈上对象；`tiling`、`vectorTiling`、`blockDim`、`route` 在同步完成 launch 参数封送前有效。输入、filter 和输出 Tensor 拥有 GM；Kernel 只借用其地址。stream 来自 `getCurrentNPUStream().stream(false)`。

```text
workspace_total = 0
SIMT launch  = entry<<<blockDim, nullptr, stream>>>(x, filter, y, tiling_by_value)
Vector launch= entry<<<blockDim, nullptr, stream>>>(x, filter, y, vector_tiling_by_value)
```

Direct 实现没有 Device workspace、executor buffer、多 Kernel 临时 GM 或跨节点 owner/lifetime。官方 Host/Tiling 的 system workspace 与 `SetLocalMemorySize` 不被照搬到 Direct ABI；Vector selector 改为显式读取 UB 并保留 2048 B，SIMT body 不显式分配 UB。

### 启动图与失败传播

```text
cann_bench::dilation_2_d
  -> dilation_2_d_npu / AnalyzeDilation2D / output allocation
  -> calc_dilation_2_d_tiling
     -> try supplemental Vector; otherwise keep official-adapted SIMT
  -> launch_dilation_2_d_half
     -> [exactly one]
        dilation_2_d_nhwc_vector_half
        dilation_2_d_nhwc_half
        dilation_2_d_nchw_half
  -> y GM
```

| 节点 | Host 启动函数 | entry / grid / POD | 输入→输出 | workspace / ordering / 失败 |
|---|---|---|---|---|
| K-001 | `launch_dilation_2_d_half` | `<<<params.blockDim,nullptr,current_stream>>>`；按 Route 传 `Dilation2DTilingData` 或 `Dilation2DVectorTilingData` | `x GM + filter GM → y GM` | workspace=0；单 stream；Host 失败阻断 launch；Device entry 无返回值。 |

这是单节点图，无 Kernel 间边、event 或 workspace slice。R-001 内部的 Queue/event 仅约束同一 Kernel 的 UB 阶段。

## Route 与参数设计

### 分核与资源计算

SIMT 默认分核沿用官方公式。令 `E=N*oH*oW*C`，`A=GetAivCoreNum()`：

```text
perCore = align_up(max(ceil(E/A), 1024), 32)  # 输出元素
needCoreNum = E==0 ? 0 : ceil(E/perCore)
blockDim = needCoreNum>0 ? needCoreNum : 1
threadsPerBlock = 512
thread globalIdx = blockIdx*512 + threadIdx
thread stride = blockDim*512
```

Vector 令 `P=N*oH*oW`、`K=fH*fW`、`Ca=align_up(C,16)`。候选 `tileW` 从 `min(oW,128)` 向 1 递减，首个同时满足下式者被选中：

```text
spanW = (tileW-1)*sW + (fW-1)*rW + 1
tilesPerRow = ceil(oW/tileW)
totalTiles = N*oH*tilesPerRow
requiredUb = (fH*spanW + K + tileW) * Ca * sizeof(half)
desiredCores = min(P, A)

spanW <= UINT16_MAX
totalTiles >= desiredCores
ubSize > 2048 && requiredUb <= ubSize-2048
```

命中后 `vectorCoreNum=min(totalTiles,A)`，`blockFactor=floor(totalTiles/vectorCoreNum)`，前 `blockTail=totalTiles%vectorCoreNum` 个 core 各多处理一个 tile。该搜索优先最大 `tileW`，同时禁止 tile 数少于期望使用核数。

### Route 选择

下表按合法域覆盖、selector 优先级、复用价值与兜底价值从 P0 到 P4 排列；P 级不改变 Host 判断顺序、短路或 fallback。“active”表示普通合法输入即可到达的生产兜底，“conditional”表示还需要资源或大索引条件；二者都是真实可达路线。

| 重要性 | Route / 状态 | 路线特征 | 完整触发谓词 | fallback / 终点 |
|---:|---|---|---|---|
| P0 | R-001 conditional supplemental NHWC FP16 row tile | UB 行带复用、filter 每 core 常驻、四个相邻输出共享 filterReg | Direct 前置门已保证 950/FP16/非空；再满足 `isNCHW==0 && P>0 && C>0`、`fW<=UINT16_MAX`、`K<=UINT16_MAX`、`(rW-1)*C*2<=UINT32_MAX`、`Ca<=UINT32_MAX/2`，且从宽到窄的搜索首次同时满足 `spanW<=UINT16_MAX`、`totalTiles>=min(P,A)`、`ubSize>2048`、`requiredUb<=ubSize-2048` | 任一标量 guard 失败直接保留 `route=0`；单个宽度失败继续缩窄；全失败按 layout/E 进入 R-002～R-005 |
| P1 | R-002 active official-adapted NHWC SIMT32 | NHWC GM 直访、32 位 magic division、512-thread grid-stride | `route=0 && isNCHW==0 && 0<E<=INT32_MAX`；其中 `route=0` 来自 R-001 标量 guard 或全部宽度候选未命中 | `E>INT32_MAX` 时不进入本模板而转 R-003；本路线执行后写完 y，无下游 Kernel |
| P2 | R-004 active official-adapted NCHW SIMT32 | NCHW GM 直访、W→H→C 坐标分解、32 位索引 | `route=0 && isNCHW!=0 && 0<E<=INT32_MAX`；NCHW 在 `vectorSafe` 第一项即排除 | `E>INT32_MAX` 时转 R-005；本路线执行后写完 y |
| P3 | R-003 conditional official-adapted NHWC SIMT64 | NHWC GM 直访，坐标商余数与 grid-stride 为 64 位 | `route=0 && isNCHW==0 && E>INT32_MAX` | 终点；源码没有更宽索引 Route，Host 乘法溢出也没有恢复边 |
| P4 | R-005 conditional official-adapted NCHW SIMT64 | NCHW GM 直访，W→H→C 坐标分解为 64 位 | `route=0 && isNCHW!=0 && E>INT32_MAX` | 终点；源码没有更宽索引 Route，Host 乘法溢出也没有恢复边 |

Host 真实选择顺序如下，P 级不参与这些判断：

1. 校验和输出分配后，空输出在 Host 返回；否则先写入完整 SIMT POD、`route=0` 和 SIMT `blockDim`。
2. 仅当 `vectorSafe` 的 layout/空域/窄化谓词先全部成立，才进入 `tileW` 从大到小的搜索；搜索中的 `spanW`、工作项或 UB guard 失败会继续尝试更小宽度。
3. 首个可行宽度立即短路搜索，覆盖 `route=1`、Vector POD 与 Vector `blockDim`，launcher 进入 R-001。
4. 未找到可行宽度则保持 `route=0`；launcher 先判断 `isNCHW`，NHWC 进入 `Process<half,false>`，NCHW 进入 `Process<half,true>`。
5. 各 `Process` 最后按 `E<=INT32_MAX` 选择 32 位 body，否则选择 64 位 body。

Direct 路径不消费官方图模式 `tilingKey`；它用 `route + isNCHW + E` 完成等价的三级选择。关键代码关系可压缩为：

```cpp
params->route = 0;                         // general SIMT first
if (vectorSafe && widestFeasibleTileFound) params->route = 1;
if (params->route == 1) launch(Vector, vectorTiling);
else if (params->tiling.isNCHW) launch(NCHW, tiling);
else launch(NHWC, tiling);
// Inside either SIMT entry:
E <= INT32_MAX ? asc_vf_call<...32<uint32_t>>()
               : asc_vf_call<...64<uint64_t>>();
```

```text
validate -> empty output ? Host return
-> initialize route=SIMT
-> NHWC && FP16 && vector scalar/DMA guards && widest feasible UB tile exists ? R-001
-> else isNCHW ?
     E<=INT32_MAX ? R-004 : R-005
   : E<=INT32_MAX ? R-002 : R-003
```

### 模板/实现执行矩阵

| 重要性 | Route | key/selector | dtype/shape/platform 完整命中条件 | 执行拓扑与 Kernel 节点 | 实际模板/body | 内存与同步特征 | tail/fallback |
|---:|---|---|---|---|---|---|---|
| P0 | R-001 supplemental Vector | `route=1` | 950、FP16、NHWC、完整 vectorSafe+tile 搜索谓词 | 单 K-001 | `dilation_2_d_nhwc_vector_half` → `NsDilation2DVector::Process` → `Dilation2DVectorKernel` | 三条 depth=1 Queue；边界 tile `Duplicate(-inf)` 后 `V_MTE2`；MicroAPI RegTensor | 宽度尾为 `actualW`；通道尾用 mask；不安全即 fallback SIMT |
| P1 | R-002 | `route=0,false,uint32` | 950、FP16、NHWC、`E<=INT32_MAX`、非 R-001 | 单 K-001 | `Process<half,false>` → `OpDilation2DSimtKernelNHWC32<half,uint32_t>` | GM 直访；512 threads；magic division；无显式 UB/atomic/barrier | grid-stride 保护 `globalIdx<E` |
| P2 | R-004 | `route=0,true,uint32` | 950、FP16、NCHW、`E<=INT32_MAX` | 单 K-001 | `Process<half,true>` → `OpDilation2DSimtKernelNCHW32<half,uint32_t>` | GM 直访；W→H→C 坐标分解 | 同上 |
| P3 | R-003 | `route=0,false,uint64` | 950、FP16、NHWC、`E>INT32_MAX`、非 R-001 | 单 K-001 | `Process<half,false>` → `OpDilation2DSimtKernelNHWC64<half,uint64_t>` | GM 直访；坐标商/余数和 globalIdx 为 64 位 | 同上 |
| P4 | R-005 | `route=0,true,uint64` | 950、FP16、NCHW、`E>INT32_MAX` | 单 K-001 | `Process<half,true>` → `OpDilation2DSimtKernelNCHW64<half,uint64_t>` | GM 直访；64 位 W→H→C 坐标分解 | 同上 |

### Selector、性能与安全 Guard

| Guard | Host/Tiling 条件 | Device/资源原因 | 影响 Route | 不满足时去向 | 源码符号 |
|---|---|---|---|---|---|
| Vector layout/空域 | `isNCHW==0 && P>0 && C>0` | 行带地址公式以 NHWC 连续 C 为基础；tile/core 除法要求非空 | R-001 | SIMT；空输出在插件返回 | `calc_dilation_2_d_tiling::vectorSafe` |
| DMA 窄字段 | `fW<=65535 && K<=65535 && spanW<=65535` | `filterH/filterW/outputW` 与 `DataCopyPad.blockCount` 在 body 内收窄为 `uint16_t` | R-001 | SIMT | 同上；`CopyFilter/CopyInputTile/ComputeTile` |
| 32 位参数 | `(rW-1)*C*2<=UINT32_MAX && Ca<=UINT32_MAX/2` | 搬运长度和 MicroAPI 地址步长使用 `uint32_t` | R-001 | SIMT | `vectorSafe`；`ComputeTile` |
| UB 上界 | `requiredUb<=ubSize-2048` 且 `ubSize>2048` | 三条 Queue 的真实容量之和为 requiredUb；保留 2048 B 给 pipe/固定开销 | R-001 | SIMT | `calc_dilation_2_d_tiling`；`Dilation2DVectorKernel::Init` |
| 并行度 | `totalTiles>=min(P,A)` | 防止过宽 tile 使可用工作项少于期望核数 | R-001 | 继续减小 width；最终 SIMT | 宽度搜索 |
| aligned C | `Ca=align_up(C,16)` | 16 个 half 即 32 B；决定连续 `DataCopy` 或 ragged `DataCopyPad` | R-001 | 两者均在同 Route 内；无失败 | `CopyFilter/CopyInputTile/CopyOutputTile` |
| SIMT 索引宽度 | `E<=INT32_MAX` | 允许 magic divider 与 globalIdx 使用 `uint32_t` | P1 R-002 / P2 R-004 | P3 R-003 / P4 R-005 | `NsDilation2D::Process` |
| layout 模板 | launcher 的 `isNCHW` | 两种 GM/filter 线性地址与坐标分解顺序不同 | R-002～R-005 | 对应 layout entry | `launch_dilation_2_d_half`；`Process<T,IsNCHW>` |
| SIMT 线程数 | 固定 `THREAD_NUM=512` | `asc_vf_call` 的 block 线程布局；每线程 grid-stride | R-002～R-005 | 无其它线程配置 | `NsDilation2D::THREAD_NUM` |

### Route 穷尽性与 dormant 分支

- **D-001 dormant：整数 SIMT 模板分支。** `ComputeMaxVal<T,IsNCHW>` 保留 `std::is_integral_v<T>` 的饱和加法代码，但 Meta/NPU dtype gate、官方 OpDef 与三个 Direct entry 都只允许或实例化 FP16；因此 selector 不可能把合法输入送到整数 body。重新启用至少需要扩展接口 dtype 合同与 Host dtype gate、增加匹配的 Direct entry 和 launcher dtype selector、核对整型 `lowest`/饱和顺序，并为 layout×索引位宽建立对应实例。未完成这些 producer/consumer 接线前，它不能提升为 Route。
- **NHWC Vector 的内部条件不另拆 Route。** `interior/boundary` 只切换 input UB 的构造方式，`C==Ca/C!=Ca` 只切换连续 DMA 与 `DataCopyPad`，四列主循环/1～3 列尾循环只处理 tile 内尾部；它们共享同一 Host selector、Vector POD、entry、分核和输出 owner。
- **不存在 NCHW Vector、Cube/AIC 或多 Kernel dormant Route。** 当前源码没有对应 selector、POD、entry 或 body，不能把“尚未实现”伪装成 dormant 生产路线。官方图模式 Host/Tiling 属于来源链而非本 Direct 调用模式的备用 Route。

整数分支的阻断关系可落成下面的审查式伪码：

```text
interface contract + meta/npu gates: dtype must be FP16
launcher: launch *_half only
entry: Process<half, IsNCHW>
=> if constexpr(is_integral_v<half>) is false
=> saturating integer body is compile-time unreachable
```

### POD/ABI

两个 tiling 结构均按值传入 Kernel。以下 offset/size 按标准布局与 8 B 自然对齐从字段声明推导；转换实现未提供 `static_assert`，复用时应增加 ABI 锁定。`Dilation2DTilingData` 预计 `sizeof=80, alignof=8`；`Dilation2DVectorTilingData` 预计 `sizeof=88, alignof=8`；`Dilation2DLaunchParams` 预计 `sizeof=176, alignof=8`。

| 结构 | 字段 | 类型/位宽 | ABI 布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| `Dilation2DTilingData` | `needCoreNum` | int32/32 | off 0；4～7 padding | core | `ceil(E/perCore)` | body 不读；用于产生 `blockDim` | `E=0` 时 0 |
| 同上 | `totalElements` | int64/64 | off 8 | 输出元素 | `N*oH*oW*C` | `Process` 分索引位宽；SIMT loop 上界 | 非空 launch 时 >0 |
| 同上 | `N` | int32/32 | off 16 | batch | `n` | SIMT 参数/坐标上界 | 非负 |
| 同上 | `H` | int32/32 | off 20 | 元素 | `h` | `ComputeMaxVal` 边界/地址 | 非负 |
| 同上 | `W` | int32/32 | off 24 | 元素 | `w` | 同上 | 非负 |
| 同上 | `C` | int32/32 | off 28 | 元素 | `c` | 坐标分解和 GM/filter 地址 | 非负 |
| 同上 | `oH` | int32/32 | off 32 | 元素 | padding 公式 | 坐标分解 | 非负 |
| 同上 | `oW` | int32/32 | off 36 | 元素 | padding 公式 | 坐标分解 | 非负 |
| 同上 | `filterH` | int32/32 | off 40 | 元素 | filter shape | `fh` loop | >0 |
| 同上 | `filterW` | int32/32 | off 44 | 元素 | filter shape | `fw` loop | >0 |
| 同上 | `strideH` | int32/32 | off 48 | 输入元素 | strides H | `ih` 公式 | >0 |
| 同上 | `strideW` | int32/32 | off 52 | 输入元素 | strides W | `iw` 公式 | >0 |
| 同上 | `rateH` | int32/32 | off 56 | 输入元素 | rates H | `ih` 公式 | >0 |
| 同上 | `rateW` | int32/32 | off 60 | 输入元素 | rates W | `iw` 公式 | >0 |
| 同上 | `padTop` | int32/32 | off 64 | 输入元素 | SAME/VALID/CALCULATED | `ih` 公式 | 非负 |
| 同上 | `padLeft` | int32/32 | off 68 | 输入元素 | 同上 | `iw` 公式 | 非负 |
| 同上 | `isNCHW` | int32/32 | off 72；76～79 tail padding | flag | `data_format==NCHW` | Host launcher 选 entry；Device body不读 | 0/1 |
| `Dilation2DVectorTilingData` | `totalTiles` | int64/64 | off 0 | tile | `N*oH*tilesPerRow` | body 不读；Host 产 core 数 | >0 |
| 同上 | `blockFactor` | int64/64 | off 8 | tile/core | `totalTiles/vectorCoreNum` | `Process` 的 count | >0 |
| 同上 | `blockTail` | int32/32 | off 16 | core count | `totalTiles%vectorCoreNum` | former/tail core 分支 | `[0,blockDim)` |
| 同上 | `H` | int32/32 | off 20 | 元素 | `h` | tile 边界/GM 地址 | 非负 |
| 同上 | `W` | int32/32 | off 24 | 元素 | `w` | tile 边界/GM 地址 | 非负 |
| 同上 | `C` | int32/32 | off 28 | 元素 | `c` | DMA 长度、mask、地址 | >0 |
| 同上 | `oH` | int32/32 | off 32 | 元素 | `outH` | work→`b,oh` 分解 | >0 |
| 同上 | `oW` | int32/32 | off 36 | 元素 | `outW` | tile 尾、输出地址 | >0 |
| 同上 | `filterH` | int32/32 | off 40 | 元素 | filter shape | Queue 容量、fh loop | >0 |
| 同上 | `filterW` | int32/32 | off 44 | 元素 | filter shape | Queue 容量、fw loop | >0 |
| 同上 | `strideH` | int32/32 | off 48 | 输入元素 | strides H | `firstH` | >0 |
| 同上 | `strideW` | int32/32 | off 52 | 输入元素 | strides W | `spanW`、x offset | >0 |
| 同上 | `rateH` | int32/32 | off 56 | 输入元素 | rates H | sampled row offset | >0 |
| 同上 | `rateW` | int32/32 | off 60 | 输入元素 | rates W | `spanW`、x offset | >0 |
| 同上 | `padTop` | int32/32 | off 64 | 输入元素 | padding 公式 | `firstH` | 非负 |
| 同上 | `padLeft` | int32/32 | off 68 | 输入元素 | padding 公式 | `firstW` | 非负 |
| 同上 | `alignedC` | int32/32 | off 72 | 元素 | `align_up(C,16)` | UB stride/容量 | 16 对齐且 `>=C` |
| 同上 | `tileW` | int32/32 | off 76 | 输出点 | 宽度搜索首个可行值 | tile 起点/尾、输出 Queue | 1～128 |
| 同上 | `maxSpanW` | int32/32 | off 80 | 输入列 | 选中 tile 的 `spanW` | input Queue stride/容量 | 1～65535 |
| 同上 | `tilesPerRow` | int32/32 | off 84 | tile/输出行 | `ceil(oW/tileW)` | work→行/tile 分解 | >0 |
| `Dilation2DLaunchParams` | `tiling` | struct/640 | off 0 | POD | SIMT producer | SIMT entry | 始终填充 |
| 同上 | `vectorTiling` | struct/704 | off 80 | POD | Vector producer | Vector entry | SIMT 时字段为零且不读 |
| 同上 | `blockDim` | uint32/32 | off 168 | core | 当前 Route 的 core 公式 | `<<<blockDim>>>` | 非空调用 >0 |
| 同上 | `route` | uint32/32 | off 172 | selector | 默认 0；Vector 命中写 1 | launcher router | 0/1 |

### Route 源码闭包

| 重要性 | Route | Key/selector | Host/Tiling producer | POD/参数 | Kernel entry/router 节点 | Kernel body/直接依赖 | 构建接线 |
|---:|---|---|---|---|---|---|---|
| P0 | R-001 supplemental Vector | `route=1` | 转换层 `AnalyzeDilation2D`、`calc_dilation_2_d_tiling` | `Dilation2DVectorTilingData` | `launch_dilation_2_d_half` → `dilation_2_d_nhwc_vector_half` | `NsDilation2DVector::Process`、`Dilation2DVectorKernel::{Init,Process,CopyFilter,CopyInputTile,ComputeTile,CopyOutputTile}` | Direct `register_direct_launch_op`；官方固定仓无此 Route |
| P1 | R-002 | `route=0,false,uint32` | 同上；SIMT 参数公式映射官方 `Dilation2DTilingFunc/FillTilingData` | `Dilation2DTilingData` | router → `dilation_2_d_nhwc_half` | `Process<half,false>`、`OpDilation2DSimtKernelNHWC32`、`ComputeMaxVal` | Direct 单 Kernel target；官方 `add_kernel_sources(...ascend950)` |
| P2 | R-004 | `route=0,true,uint32` | 同 R-002 | 同上 | router → `dilation_2_d_nchw_half` | `Process<half,true>`、`OpDilation2DSimtKernelNCHW32`、`ComputeMaxVal` | 同上 |
| P3 | R-003 | `route=0,false,uint64` | 同 R-002 | 同上 | 同 R-002 | `Process<half,false>`、`OpDilation2DSimtKernelNHWC64`、`ComputeMaxVal` | 同上 |
| P4 | R-005 | `route=0,true,uint64` | 同 R-002 | 同上 | 同 R-004 | `Process<half,true>`、`OpDilation2DSimtKernelNCHW64`、`ComputeMaxVal` | 同上 |

## Kernel 实现

### 公共执行流程

所有 Route 只启动 K-001。launcher 按值传 POD，entry 标记 `KERNEL_TYPE_AIV_ONLY`。R-001 构造 `TPipe` 后执行 Queue/RegTensor 管线；R-002～R-005 调用 `asc_vf_call` 进入 512-thread SIMT body。它们共享同一数学地址定义与输出有效域，但不共享内存组织：Vector 把行带物化到 UB 并复用，SIMT 每线程直接从 GM 遍历完整 filter。

### Route R-001（P0）：supplemental NHWC FP16 行带 Vector

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct Host | `dilation_2d_kernel.cpp` | `calc_dilation_2_d_tiling` | 完整 `vectorSafe` 标量 guard，再从 `min(oW,128)` 向下搜索 `span/tiles/requiredUb` | 首个可行 width 写 `route=1`；否则保持 SIMT |
| Launcher | 同上 | `launch_dilation_2_d_half` | `params->route==1` | `dilation_2_d_nhwc_vector_half` |
| Entry/body | `dilation_2_d_vector.h` | `NsDilation2DVector::Process` | NHWC、FP16、Vector POD；`blockDim=vectorCoreNum` | `Dilation2DVectorKernel` |

#### Device 数据流

##### 函数级调用链

```text
launch_dilation_2_d_half
  -> dilation_2_d_nhwc_vector_half
    -> NsDilation2DVector::Process
      -> Dilation2DVectorKernel::Init
         -> InitBuffer(xQueue/filterQueue/yQueue) -> CopyFilter
      -> Process
         -> CopyInputTile -> ComputeTile -> CopyOutputTile
```

##### 源码等价伪码

```text
core range:
  count = blockFactor + (blockIdx < blockTail)
  begin = blockIdx*blockFactor + min(blockIdx, blockTail)
copy whole filter once to filterQueue
for work in [begin, begin+count):
  decode work -> (b, oh, tileIndex); owStart=tileIndex*tileW
  actualW=min(tileW, oW-owStart)
  spanW=(actualW-1)*sW+(fW-1)*rW+1
  if sampled rectangle is interior:
    copy each sampled input row once into [fH,maxSpanW,alignedC]
  else:
    fill full input UB with -inf; V_MTE2 wait; overlay only valid rows/columns
  for outCol in groups of 4, then scalar-width tail:
    for channel register repeat with UpdateMask(C-tail):
      result[0..3] = -inf
      for fh,fw:
        load filterReg once
        load four x registers at adjacent output offsets
        result[i] = IEEE_Max(result[i], x[i] + filterReg)
      masked store results to yLocal
  copy only actualW*C from yLocal to output GM
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| x GM | `((b*H+ih)*W+iw)*C` | 有效 sampled row/columns | FP16 NHWC | caller | `CopyInputTile` | input Tensor | 连续 C；每个行带只搬一次重叠输入 |
| filter GM | `(fh*fW+fw)*C` | `K*C` | FP16 `(fH,fW,C)` | caller | `CopyFilter` | filter Tensor | 每 core 只搬一次 |
| `xQueue_` | `(fh*maxSpanW+col)*Ca+c` | `fH*maxSpanW*Ca` 元素，depth=1 | FP16 padded NHWC strip | `CopyInputTile` | `ComputeTile` | 每 tile alloc→enqueue→dequeue→free | `Ca` 为 32B 对齐；边界先填 `-inf` |
| `filterQueue_` | `(fh*fW+fw)*Ca+c` | `K*Ca` 元素，depth=1 | FP16 | `CopyFilter` | 所有 tile 的 `ComputeTile` | 每 core Init 时 alloc；Process 末 free | 跨 core 内全部 tile 复用 |
| `yQueue_` | `outCol*Ca+c` | `tileW*Ca` 元素，depth=1 | FP16 | `ComputeTile` | `CopyOutputTile` | 每 tile alloc→enqueue→dequeue→free | GM 只写 `actualW*C` |
| RegTensor | channel chunk `r*VECTOR_REG_WIDTH/2` | filter、4×x、4×result 寄存器 | FP16 | MicroAPI load/Add/Max | masked store | 当前 `(outCol group,r)` | 四输出共享 filterReg；通道尾 mask |
| y GM | `firstPoint*C` | `actualW*C` | FP16 NHWC | `CopyOutputTile` | caller | output Tensor | `C==Ca` 连续 DMA，否则 ragged copy |

##### 分层内存布局

```mermaid
block-beta
  columns 3
  xq["xQueue · depth=1 · fH*maxSpanW*Ca*2 B"]:1
  fq["filterQueue · depth=1 · fH*fW*Ca*2 B"]:1
  yq["yQueue · depth=1 · tileW*Ca*2 B"]:1
```

##### 字节账与复用顺序

```text
xQueue_bytes      = fH*maxSpanW*Ca*2
filterQueue_bytes = fH*fW*Ca*2
yQueue_bytes      = tileW*Ca*2
UB_total          = (fH*maxSpanW + fH*fW + tileW)*Ca*2 = requiredUb
UB_total <= platform_ub_size - 2048
dynamic_ub = N/A
workspace_total = 0
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| `filterQueue_` | `CopyFilter` | 每次 `ComputeTile` | Kernel 结束前不覆盖 | EnQue→单次 DeQue；所有 work 完成后 FreeTensor | 每 core 独占 Queue |
| `xQueue_` | 当前 tile 的 `CopyInputTile` | 当前 `ComputeTile` | 下一 tile `AllocTensor` | DeQue 后 Compute；Compute 后 FreeTensor | 不在 FreeTensor 前启动下一次覆盖 |
| `yQueue_` | 当前 tile `ComputeTile` | 当前 `CopyOutputTile` | 下一 tile | EnQue→DeQue→CopyOut→FreeTensor | CopyOut 完成后释放 |
| `xQueue_` 边界全区 | `Duplicate(-inf)` | 后续有效区域 DMA 与 Compute | 有效 DMA 覆盖子区；下一 tile覆盖全区 | `SetFlag/WaitFlag<V_MTE2>` | Vector fill 完成后 MTE2 才能覆盖 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| filter copy | TQue EnQue/DeQue | MTE2 | `ComputeTile` | filter UB | FP16 原值；`Ca>C` lane 被 mask，不写输出 |
| boundary init | `Duplicate` + `V_MTE2` event | Vector fill | valid-region DMA | x UB | 先完整写 `-inf`，再覆盖有效输入，保留 padding 语义 |
| tile compute | `UpdateMask<half>`、RegTensor Add/Max | x/filter registers | result store | 当前 channel chunk | FP16 加法与 dav-3510 IEEE Max；最后 repeat 只覆盖 C 有效 lane |
| width tail | `groupedWidth=actualW&~3` | 4-output loop | scalar-width loop | 最后 0～3 个输出点 | 不访问 tileW 外部 |
| output | Queue + `DataCopy`/`DataCopyPad` | yLocal | GM output | `actualW*C` | 不回写 Ca padding 或 tileW 尾 |

##### Fallback 与失效边界

R-001 只在 Host 完整证明标量窄化、工作项数量和三 Queue UB 总量安全后才会发射；候选宽度从大到小失败时继续缩窄，全部失败或平台 UB 查询返回 0 时保持 `route=0`。进入 Device 后没有二次 Route 判断；POD、Queue 容量或 ABI 若与 Host 推导不一致，只能视为实现错误，不能期待 Kernel 内回退。NCHW 永不进入本路线。

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `dilation_2d_kernel.cpp` | `calc_dilation_2_d_tiling` | supplemental selector、宽度搜索、UB 账与 core 划分 |
| Kernel entry/router | 同上 | `launch_dilation_2_d_half`、`dilation_2_d_nhwc_vector_half` | route=1 到唯一 Vector body |
| Device body/helper | `dilation_2_d_vector.h` | `Dilation2DVectorKernel` 全部方法 | 行带搬运、filter 复用、四输出 RegTensor、event、mask 与 tail |

### Route R-002（P1）：official-adapted NHWC SIMT32

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct Host | `dilation_2d_kernel.cpp` | `calc_dilation_2_d_tiling` | R-001 未接受，默认 `route=0` | SIMT launcher |
| Launcher | 同上 | `launch_dilation_2_d_half` | `route!=1 && isNCHW==0` | `dilation_2_d_nhwc_half` |
| SIMT router | `dilation_2_d_simt.h` | `Process<half,false>` | `totalElements<=INT32_MAX` | `OpDilation2DSimtKernelNHWC32<half,uint32_t>` |

#### Device 数据流

##### 函数级调用链

```text
launch_dilation_2_d_half -> dilation_2_d_nhwc_half
  -> Process<half,false> -> asc_vf_call<NHWC32>(dim3(512), ...)
    -> grid-stride loop -> ComputeMaxVal<half,false> -> y[globalIdx]
```

##### 源码等价伪码

```text
for globalIdx=blockIdx*512+threadIdx; globalIdx<E; globalIdx+=gridDim*512:
  c,ow,oh,b = chained UintDiv/remainders by C,oW,oH
  maxVal=-inf
  for fh in [0,fH), fw in [0,fW):
    ih=oh*sH+fh*rH-pT; iw=ow*sW+fw*rW-pL
    fIdx=(fh*fW+fw)*C+c
    val = in_bounds ? x[((b*H+ih)*W+iw)*C+c] + filter[fIdx] : -inf+filter[fIdx]
    if isnan(val): return NaN
    maxVal=max(maxVal,val)
  y[globalIdx]=maxVal
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| x GM | `((b*H+ih)*W+iw)*C+c` | 单元素/有效 filter 点 | FP16 NHWC | caller | thread | input Tensor | 无 UB staging |
| filter GM | `(fh*fW+fw)*C+c` | 单元素/filter 点 | FP16 | caller | thread | filter Tensor | 每输出线程重复读取 |
| thread registers | 坐标、magic 商余数、`maxVal` | 固定仓不提供字节数 | scalar | SIMT thread | 同一 thread | 一个 globalIdx 迭代 | 下一 globalIdx 覆盖 |
| y GM | `globalIdx` | 1 元素/迭代 | FP16 NHWC | thread | caller | output Tensor | 每 globalIdx 唯一 writer |

##### 分层内存布局

N/A：该 SIMT body 不声明 AIV `TQue/TBuf`、dynamic UB 或 shared memory；实际替代路径是线程寄存器加 GM 直读直写。

##### 字节账与复用顺序

```text
explicit_UB_total = 0
dynamic_ub = N/A
workspace_total = 0
register_bytes = 固定官方/转换源码未给出；生命周期为单线程当前 globalIdx
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| thread scalar/register state | 当前 globalIdx | 当前 filter reduction | 下一 globalIdx | 单线程程序顺序 | 每个输出由唯一 thread 迭代写入 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| coordinate | `Simt::UintDiv` | magic/shift + globalIdx | 地址计算 | NHWC 坐标 | uint32 quotient/remainder，地址乘法用 int64 |
| reduction | 线程本地程序顺序 | GM loads/add | `maxVal` | 单输出元素 | FP16；NaN 立即返回；越界按 `-inf+filter` 只检测 NaN |
| output | unique writer | current thread | 无等待 | `y[globalIdx]` | `globalIdx<E` 是尾保护；无 atomic/barrier |

##### Fallback 与失效边界

R-002 是 `route=0` 的普通 NHWC 兜底。`E>INT32_MAX` 时 `Process<half,false>` 在调用 body 前改选 R-003；一旦进入 NHWC32 body 就没有中途 fallback。`C/oW/oH` 必须为正，空输出已由 Host 返回，否则 magic division 的除数域不成立。

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | 官方 `op_host/arch35/dilation2_d_tiling.cpp`；Direct `dilation_2d_kernel.cpp` | `FillTilingData`；`calc_dilation_2_d_tiling` | official-adapted POD/core 公式；Vector fallback 边界 |
| Kernel entry/router | 官方 `op_kernel/arch35/dilation2_d.cpp`；Direct entry | `dilation2_d<NHWC>`；`dilation_2_d_nhwc_half` | `IsNCHW=false` 编译期 body |
| Device body/helper | 官方/适配 `dilation2_d_simt.h` | `Process<half,false>`、`NHWC32`、`ComputeMaxVal` | 32 位坐标分解、64 位 GM 地址、NaN 适配 |

### Route R-004（P2）：official-adapted NCHW SIMT32

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct Host | `dilation_2d_kernel.cpp` | calc | `isNCHW!=0` 使 Vector selector 为 false | SIMT |
| Launcher | 同上 | launcher | `route!=1 && isNCHW!=0` | NCHW entry |
| SIMT router | `dilation_2_d_simt.h` | `Process<half,true>` | `E<=INT32_MAX` | `NCHW32<half,uint32_t>` |

#### Device 数据流

##### 函数级调用链

```text
launch -> dilation_2_d_nchw_half -> Process<half,true>
  -> asc_vf_call<NCHW32>(dim3(512), ...) -> ComputeMaxVal<half,true> -> y
```

##### 源码等价伪码

```text
for globalIdx=blockIdx*512+threadIdx; globalIdx<E; globalIdx+=gridDim*512:
  afterW=UintDiv(globalIdx,mW,sW); ow=globalIdx-afterW*oW
  afterH=UintDiv(afterW,mH,sH);    oh=afterW-afterH*oH
  afterC=UintDiv(afterH,mC2,sC2);  c=afterH-afterC*C; b=afterC
  maxVal=-inf
  for fh,fw:
    ih=oh*sH+fh*rH-pT; iw=ow*sW+fw*rW-pL
    fIdx=(c*fH+fh)*fW+fw
    val = in_bounds ? x[((b*C+c)*H+ih)*W+iw]+filter[fIdx]
                    : -inf+filter[fIdx]
    if isnan(val): return NaN
    maxVal=max(maxVal,val)
  y[globalIdx]=maxVal
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| x GM | `((b*C+c)*H+ih)*W+iw` | 每个有效 filter 点 1 元素 | FP16 NCHW | caller | 当前 SIMT thread | input Tensor | GM 直访；无 UB staging |
| filter GM | `(c*fH+fh)*fW+fw` | 每个 filter 点 1 元素 | FP16 CHW | caller | 当前 SIMT thread | filter Tensor | 越界 input 点仍读取，用于 `-inf+filter` |
| y GM | `globalIdx` | 每次迭代 1 元素 | FP16 NCHW | 当前 thread | caller | output Tensor | 每个 `globalIdx` 唯一 writer |
| registers | uint32 magic/坐标/商余数，int64 `ih/iw/xIdx/fIdx`，half reduction | 源码未声明字节数 | scalar | 当前 thread | 当前 thread | 一个 `globalIdx` 迭代 | 下一次 grid-stride 迭代覆盖 |

##### 分层内存布局

N/A：无显式 UB/dynamic UB/shared memory；实际路径为 GM+线程寄存器。

##### 字节账与复用顺序

```text
explicit_UB_total=0; dynamic_ub=N/A; workspace_total=0
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| thread state | 当前 output | reduction | 下一 output | 程序顺序 | unique writer |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| coordinate | 三次 `Simt::UintDiv` | `Process` 生成的 uint32 magic/shift | 地址计算 | W→H→C 商余数 | 商余数为 uint32；GM 地址表达式显式提升为 int64 |
| reduction | 单线程程序顺序 | GM load 与 half add | `maxVal` | 一个 NCHW 输出 | 初值 `-inf`；有效/越界都先执行加法语义；任一 NaN 立即返回 |
| output/tail | unique writer + grid-stride | 当前 thread | 无跨线程等待 | `y[globalIdx]` | `globalIdx<E` 保护最后一个不满 512-thread 的逻辑尾；无 barrier/atomic |

##### Fallback 与失效边界

R-004 是所有非空 NCHW 普通索引域的兜底，Vector selector 不参与。`E>INT32_MAX` 时同一 entry 的 `Process<half,true>` 改选 R-005；进入 NCHW32 body 后无中途 fallback。`C/oH/oW` 的正值前提由非空输出与 Host shape gate 共同建立。

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | 官方 tiling + Direct calc | layout parse / calc | NCHW 与 E |
| Kernel entry/router | 官方 template + Direct NCHW entry | `Process<half,true>` | 编译期 NCHW |
| Device body/helper | `dilation2_d_simt.h` | `NCHW32`、`ComputeMaxVal<half,true>` | W→H→C 坐标与 NCHW 地址 |

### Route R-003（P3）：official-adapted NHWC SIMT64

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct Host/launcher | `dilation_2d_kernel.cpp` | calc + launcher | R-001 未命中，`isNCHW==0` | NHWC SIMT entry |
| SIMT router | `dilation_2_d_simt.h` | `Process<half,false>` | `totalElements>INT32_MAX` | `OpDilation2DSimtKernelNHWC64<half,uint64_t>` |

#### Device 数据流

##### 函数级调用链

```text
launch -> dilation_2_d_nhwc_half -> Process<half,false>
  -> asc_vf_call<NHWC64>(dim3(512), ...) -> ComputeMaxVal<half,false> -> y
```

##### 源码等价伪码

```text
for u64 globalIdx=blockIdx*512+threadIdx; globalIdx<E; globalIdx+=u64(gridDim)*512:
  afterC=UintDiv(globalIdx,mC,sC);   c=globalIdx-afterC*C
  afterW=UintDiv(afterC,mOW,sOW);    ow=afterC-afterW*oW
  afterH=UintDiv(afterW,mOH,sOH);    oh=afterW-afterH*oH; b=afterH
  half maxVal=-inf
  for fh in [0,fH), fw in [0,fW):
    ih=oh*sH+fh*rH-pT; iw=ow*sW+fw*rW-pL
    fIdx=(fh*fW+fw)*C+c
    val = in_bounds ? x[((b*H+ih)*W+iw)*C+c]+filter[fIdx]
                    : -inf+filter[fIdx]
    if isnan(val): return NaN
    maxVal=max(maxVal,val)
  y[globalIdx]=maxVal
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| x GM | `((b*H+ih)*W+iw)*C+c` | 每个有效 filter 点 1 元素 | FP16 NHWC | caller | 当前 thread | input Tensor | int64 地址；无 UB staging |
| filter GM | `(fh*fW+fw)*C+c` | 每个 filter 点 1 元素 | FP16 HWC | caller | 当前 thread | filter Tensor | input 越界时仍读取 |
| y GM | `globalIdx` | 每次迭代 1 元素 | FP16 NHWC | 当前 thread | caller | output Tensor | uint64 线性索引；unique writer |
| thread registers | uint64 magic/坐标/商余数与 grid-stride，int64 地址，half reduction | 源码未声明字节数 | scalar | 当前 thread | 当前 thread | 当前 `globalIdx` | 下一迭代覆盖 |

##### 分层内存布局

N/A：无显式 AIV UB/dynamic UB/shared memory；GM 直访与线程寄存器替代。

##### 字节账与复用顺序

```text
explicit_UB_total=0; dynamic_ub=N/A; workspace_total=0
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| thread state | 当前 globalIdx | 当前 reduction | 下一 globalIdx | 程序顺序 | unique output writer |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| coordinate | `GetUintDivMagicAndShift<uint64_t>` + 三次 `UintDiv` | `Process<half,false>` | 地址计算 | C→W→H 商余数 | `globalIdx/gridStride/magic/quotient` 全为 uint64；轴坐标收窄 int32 前均小于对应 int32 轴长 |
| reduction | 单线程程序顺序 | GM loads 与 half add | half `maxVal` | 一个 NHWC 输出 | 初值 `-inf`；有效值或 `-inf+filter` 出现 NaN 即返回；否则按源码遍历顺序 Max |
| output/tail | unique writer + `globalIdx<E` | 当前 thread | 无等待 | y GM | 64 位 loop guard 覆盖 grid-stride 尾；无 barrier/atomic |

##### Fallback 与失效边界

R-003 是 NHWC 的最终大索引路线，没有更宽模板或 Device 恢复边。它只扩大线性索引、magic 与商余数；`b/oh/ow/c` 和各 shape 轴仍是 int32，GM 地址仍是有符号 int64。Host 的 `E=N*oH*oW*C` 未做 checked multiply；若该乘法溢出，64 位 Route 本身不能补救。

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | 官方 tiling + Direct calc | `FillTilingData`、`calc_dilation_2_d_tiling` | E 与 blockDim |
| Kernel entry/router | 官方 entry + Direct NHWC entry | `Process<half,false>` | layout 固化 |
| Device body/helper | `dilation2_d_simt.h` | `NHWC64<half,uint64_t>` | 64 位 magic division 与 grid-stride |

### Route R-005（P4）：official-adapted NCHW SIMT64

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct Host/launcher | `dilation_2d_kernel.cpp` | calc + launcher | `isNCHW!=0`，`route=0` | NCHW entry |
| SIMT router | `dilation_2_d_simt.h` | `Process<half,true>` | `E>INT32_MAX` | `NCHW64<half,uint64_t>` |

#### Device 数据流

##### 函数级调用链

```text
launch -> dilation_2_d_nchw_half -> Process<half,true>
  -> asc_vf_call<NCHW64>(dim3(512), ...) -> ComputeMaxVal<half,true> -> y
```

##### 源码等价伪码

```text
for u64 globalIdx=blockIdx*512+threadIdx; globalIdx<E; globalIdx+=u64(gridDim)*512:
  afterW=UintDiv(globalIdx,mW,sW);   ow=globalIdx-afterW*oW
  afterH=UintDiv(afterW,mH,sH);      oh=afterW-afterH*oH
  afterC=UintDiv(afterH,mC2,sC2);    c=afterH-afterC*C; b=afterC
  half maxVal=-inf
  for fh in [0,fH), fw in [0,fW):
    ih=oh*sH+fh*rH-pT; iw=ow*sW+fw*rW-pL
    fIdx=(c*fH+fh)*fW+fw
    val = in_bounds ? x[((b*C+c)*H+ih)*W+iw]+filter[fIdx]
                    : -inf+filter[fIdx]
    if isnan(val): return NaN
    maxVal=max(maxVal,val)
  y[globalIdx]=maxVal
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| x GM | `((b*C+c)*H+ih)*W+iw` | 每个有效 filter 点 1 元素 | FP16 NCHW | caller | 当前 thread | input Tensor | int64 地址；无 UB staging |
| filter GM | `(c*fH+fh)*fW+fw` | 每个 filter 点 1 元素 | FP16 CHW | caller | 当前 thread | filter Tensor | input 越界时仍读取 |
| y GM | `globalIdx` | 每次迭代 1 元素 | FP16 NCHW | 当前 thread | caller | output Tensor | uint64 线性索引；unique writer |
| registers | uint64 magic/商余数/grid-stride，int64 地址，half reduction | 源码未声明字节数 | scalar | 当前 thread | 当前 thread | 当前 `globalIdx` | 下一迭代覆盖 |

##### 分层内存布局

N/A：无显式 UB/dynamic UB/shared memory；实际路径为 GM+线程寄存器。

##### 字节账与复用顺序

```text
explicit_UB_total=0; dynamic_ub=N/A; workspace_total=0
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| thread state | 当前 output | reduction | 下一 output | 程序顺序 | unique writer |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| coordinate | `GetUintDivMagicAndShift<uint64_t>` + 三次 `UintDiv` | `Process<half,true>` | 地址计算 | W→H→C 商余数 | 64 位索引域；坐标收窄 int32 后用于 int64 GM 地址表达式 |
| reduction | 单线程程序顺序 | GM loads 与 half add | half `maxVal` | 一个 NCHW 输出 | 初值 `-inf`；有效值/越界加法的 NaN 立即返回；否则按 fh→fw 顺序 Max |
| output/tail | unique writer + `globalIdx<E` | 当前 thread | 无等待 | y GM | 64 位 grid-stride 尾保护；无 barrier/atomic |

##### Fallback 与失效边界

R-005 是 NCHW 的最终大索引路线，没有更宽模板或 Device 恢复边。64 位只覆盖输出线性索引与除法链，POD 轴值仍为 int32、GM 地址仍为 int64；Host `totalElements` 溢出或错误 POD 不会在 Kernel 内被检测。

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | 官方 tiling + Direct calc | `FillTilingData` / calc | 大 E 和 blockDim |
| Kernel entry/router | 官方 template + Direct NCHW entry | `Process<half,true>` | NCHW specialization |
| Device body/helper | `dilation2_d_simt.h` | `NCHW64<half,uint64_t>` | 64 位坐标分解和 NCHW 地址 |

## 算子特定优化

### Trick T-001：用 layout 模板在编译期消除地址分支

#### 触发与源码依据

- 适用 Route：P1 R-002、P2 R-004、P3 R-003、P4 R-005。
- 触发条件：Host/launcher 已把 NHWC/NCHW 映射到 `schMode` 或 Direct 的独立 entry。
- 官方固定来源：[`op_kernel/arch35/dilation2_d.cpp:29-34`](https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/pooling/dilation2_d/op_kernel/arch35/dilation2_d.cpp)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
if constexpr (schMode == DILATION2D_MODE_NHWC) {
    NsDilation2D::Process<DTYPE_X, false>(x, filter, y, &tilingData);
} else if constexpr (schMode == DILATION2D_MODE_NCHW) {
    NsDilation2D::Process<DTYPE_X, true>(x, filter, y, &tilingData);
}
```

#### 机制与设计原因

`schMode` 由 Host layout 选择产生，模板布尔值一路传给 `Process` 与 `ComputeMaxVal`。因此坐标分解、x/filter 地址公式都由 `if constexpr` 固化，SIMT 内层 `fh×fw` 循环无需每个 filter 点再判断 layout。Direct 转换把同一边界实现为两个独立 entry，仍保持编译期 specialization。

#### 迁移边界

- 适用：同一数学语义具有少量、稳定 layout 地址公式的 SIMT 算子。
- 前提：Host 必须准确校验 layout，并让每个 entry/POD 与模板值一一对应。
- 失效：加入新 layout 时必须新增模板实例和 launcher 分支；不能把未知 layout 静默落入 NHWC。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓提供的失败边界是 Host 对非 NHWC/NCHW 直接返回失败；不得把非法字符串当作默认 NHWC。

### Trick T-002：按输出规模切换 32/64 位 magic division

#### 触发与源码依据

- 适用 Route：P1 R-002 / P2 R-004 使用 32 位；P3 R-003 / P4 R-005 使用 64 位。
- 触发条件：`totalElements <= INT32_MAX` 选 32 位，否则选 64 位；layout 再决定除数链 C/oW/oH 或 oW/oH/C。
- 官方固定来源：[`op_kernel/arch35/dilation2_d_simt.h:241-263`](https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/pooling/dilation2_d/op_kernel/arch35/dilation2_d_simt.h)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
if (tilingData->totalElements <= static_cast<int64_t>(INT32_MAX)) {
    uint32_t mW = 0, sW = 0, mH = 0, sH = 0, mC2 = 0, sC2 = 0;
    GetUintDivMagicAndShift(mW, sW, static_cast<uint32_t>(oW));
    GetUintDivMagicAndShift(mH, sH, static_cast<uint32_t>(oH));
    GetUintDivMagicAndShift(mC2, sC2, static_cast<uint32_t>(C));
    asc_vf_call<OpDilation2DSimtKernelNCHW32<T, uint32_t>>(
        dim3(THREAD_NUM), static_cast<uint32_t>(tilingData->totalElements), tilingData->N, tilingData->H,
        tilingData->W, C, oH, oW, tilingData->filterH, tilingData->filterW, tilingData->strideH,
        tilingData->strideW, tilingData->rateH, tilingData->rateW, tilingData->padTop, tilingData->padLeft, mW,
        sW, mH, sH, mC2, sC2, x_gm, filter_gm, y_gm);
} else {
    uint64_t mW = 0, sW = 0, mH = 0, sH = 0, mC2 = 0, sC2 = 0;
    GetUintDivMagicAndShift(mW, sW, static_cast<uint64_t>(oW));
    GetUintDivMagicAndShift(mH, sH, static_cast<uint64_t>(oH));
    GetUintDivMagicAndShift(mC2, sC2, static_cast<uint64_t>(C));
    asc_vf_call<OpDilation2DSimtKernelNCHW64<T, uint64_t>>(
        dim3(THREAD_NUM), static_cast<uint64_t>(tilingData->totalElements), tilingData->N, tilingData->H,
        tilingData->W, C, oH, oW, tilingData->filterH, tilingData->filterW, tilingData->strideH,
        tilingData->strideW, tilingData->rateH, tilingData->rateW, tilingData->padTop, tilingData->padLeft, mW,
        sW, mH, sH, mC2, sC2, x_gm, filter_gm, y_gm);
}
```

#### 机制与设计原因

每线程需要把线性输出索引分解成四维坐标。Host/POD 提供 `C,oH,oW`，`Process` 只在每 block 建立对应位宽的 magic/shift，SIMT 线程使用 `Simt::UintDiv` 链式求商余数；普通规模避免全程 64 位坐标计算，大规模仍由 64 位路线保证索引域。GM 地址在两条路线中都用 `int64_t`，所以 32 位优化只缩窄坐标分解，不缩窄最终线性地址。

#### 迁移边界

- 适用：输出可线性化、各轴长为正、每线程独立映射输出元素的 SIMT Kernel。
- 前提：阈值必须覆盖所有中间 quotient；除数 C/oH/oW 不能为 0；空域必须先返回。
- 失效：输出元素超过阈值必须进入 uint64 模板；不能仅把 globalIdx 扩成 64 位而保留 32 位 magic 参数。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓以明确的 64 位模板作为反例边界：大输出继续调用 32 位 kernel 会使 globalIdx 或商余数截断。

R-001 的“输入行带只搬一次、filter 每 core 只搬一次、四个相邻输出共享 filterReg”同样是高杠杆机制，但它属于 **supplemental Vector 转换实现**，官方固定 commit 没有可引用的对应源码，因此不登记为官方 Trick。其完整触发条件、UB 账、同步和迁移失败去向已在 R-001 闭合。

## 模板与实现对比

| 对比维度 | P0 R-001 supplemental Vector | P1 R-002 NHWC SIMT32 | P2 R-004 NCHW SIMT32 | P3 R-003 NHWC SIMT64 | P4 R-005 NCHW SIMT64 | 设计选择依据 |
|---|---|---|---|---|---|---|
| 命中条件/优先级 | NHWC+FP16+scalar/DMA/UB/并行度全部可行 | Vector 未命中、NHWC、普通索引域 | NCHW、普通索引域 | Vector 未命中、NHWC、超 32 位索引域 | NCHW、超 32 位索引域 | P 级只组织知识；Host 仍先尝试 Vector，再按 layout 与 E 分支 |
| 模板与 dtype | `Dilation2DVectorKernel`，half | `Process<half,false>`，uint32 | `Process<half,true>`，uint32 | `Process<half,false>`，uint64 | `Process<half,true>`，uint64 | Direct 只接受 FP16；layout 与索引位宽均编译期固化 |
| 循环与分核 | core 分连续 row-tile；tile 内 fh/fw/channel repeat/4-output | 512-thread grid-stride；每线程完整 fh/fw | 同 P1，坐标顺序 W→H→C | 同 P1，grid-stride/坐标改 64 位 | 同 P2，grid-stride/坐标改 64 位 | layout 决定地址；E 决定索引位宽 |
| Queue/TBuf/寄存器/dynamic UB | 3×depth1 Queue + 9 个主要 RegTensor；无 dynamic UB | 无显式 Queue/TBuf/dynamic UB；scalar registers | 同 P1 | 同 P1，uint64 坐标寄存器 | 同 P2，uint64 坐标寄存器 | UB 可容纳行带才选择 Vector |
| 内存总占用与复用 | requiredUb；input strip 重叠复用、filter core 内复用 | explicit UB=0；每输出重复 GM filter/input | 同 P1，NCHW 地址 | 同 P1，64 位索引 | 同 P2，64 位索引 | 资源谓词失败保持 SIMT 闭包 |
| 搬运/Vector/SIMT API | DataCopy/DataCopyPad/Duplicate + MicroAPI Add/Max | `asc_vf_call`、UintDiv、GM scalar load/store | 同 P1 | 同 P1 的 64 位实例 | 同 P2 的 64 位实例 | 两执行族不合并 Route |
| 同步、精度与 tail | Queue；边界 V_MTE2；FP16 IEEE Max；W/C tail | 无 barrier；FP16 + NaN adaptation；globalIdx tail | 同 P1 | 同 P1，uint64 tail 比较 | 同 P2，uint64 tail 比较 | padding/NaN 语义必须一致 |
| fallback/失败边界 | 任一 guard 不成立 → SIMT | `E>INT32_MAX` → P3 R-003 | `E>INT32_MAX` → P4 R-005 | 终点 | 终点 | supplemental 不得成为唯一闭包 |

## 平台差异

| 项目 | A2 | A3 | 950 |
|---|---|---|---|
| 支持状态 | 官方 README 明确不支持 | 官方 README 明确不支持 | 官方 README、OpDef、`SUPPORT_COMPUTE_UNIT=ascend950` 与 Kernel CMake 支持 |
| Host/Launcher | 不发布本卡实现 | 不发布本卡实现 | Direct Host 查询 AIV core/UB；SIMT official-adapted + supplemental Vector |
| Kernel/资源 | N/A | N/A | dav-3510；SIMT 512 threads；Vector 使用 UB/MicroAPI；无 Cube/AIC |

## 限制与失败边界

- Direct Invoke 只接受连续 FP16；不执行 `Contiguous`，不支持官方 README 之外的 dtype，也不提供 ACLNN executor/workspace 语义。
- `CheckedI32` 禁止负维或超过 `INT32_MAX` 的单轴，但输出尺寸中间式、`totalElements=N*oH*oW*C`、`totalPoints=N*oH*oW` 与 `candidateTiles=rows*tilesPerRow` 没有统一的 checked arithmetic；复用时必须为有符号加乘和收窄补齐溢出检查。
- Vector 的 Host guard 覆盖主要 `uint16_t/uint32_t` 窄化与 UB 总量，但源码没有 `static_assert` 锁定两个 POD 的 size/offset；跨编译单元复用应显式锁定 ABI。
- Vector 的 `requiredUb` 只计三条 Queue，并额外保留 2048 B；若平台 `TPipe` 固定开销契约变化，必须重新审计 reserve，不能只沿用常量。
- official-adapted SIMT 的 NaN 行为不是官方原 body 的逐字复制：转换实现为有效 `x+filter` 的 NaN 和越界 `-inf + +inf` 增加传播；迁回官方图模式时不能假设该差异已经存在。
- supplemental Vector 只覆盖 NHWC；NCHW 或任一资源 guard 失败都依赖 SIMT fallback。官方固定 commit 不证明该 Vector 路线的性能或跨版本兼容性。
- 单 stream 保证本次 K-001 的发射顺序；无跨 Kernel 同步。launch wrapper 固定返回 0，异步 Device 错误不在该返回值中闭合。
- 本次知识提取未执行编译、真机、数值或性能测试；不提供性能百分比结论。

## 源码索引

### 链路索引

| 链路阶段 | 文件 | 关键符号 | 支撑内容 |
|---|---|---|---|
| 入口声明/约束 | `pooling/dilation2_d/README.md` | 产品表、公式、参数/约束 | 950 支持、FP16、layout、padding 语义 |
| 入口实现 | `pooling/dilation2_d/op_host/dilation2_d_def.cpp` | `ops::Dilation2D` | 输入输出 dtype/format、属性、ascend950 注册 |
| shape | `pooling/dilation2_d/op_host/dilation2_d_infershape.cpp` | `InferShapeDilation2D` | shape/layout/stride/rate/padding 公式与错误边界 |
| Host/Tiling | `pooling/dilation2_d/op_host/arch35/dilation2_d_tiling.cpp` | `Dilation2DTilingFunc`、`FillTilingData` | 平台查询、core 公式、POD producer、key 与 workspace |
| POD | `pooling/dilation2_d/op_kernel/arch35/dilation2_d_tiling_data.h` | `Dilation2DTilingData` | official-adapted fallback ABI 字段顺序 |
| key | `pooling/dilation2_d/op_kernel/arch35/dilation2_d_tiling_key.h` | `DILATION2D_MODE_*` | NHWC/NCHW 模板域 |
| Kernel entry | `pooling/dilation2_d/op_kernel/arch35/dilation2_d.cpp` | `dilation2_d<schMode>` | layout 编译期分发 |
| Kernel body | `pooling/dilation2_d/op_kernel/arch35/dilation2_d_simt.h` | `Process`、四个 SIMT kernel、`ComputeMaxVal` | 线程映射、索引、地址、reduction、tail |
| 构建接线 | `pooling/dilation2_d/op_kernel/CMakeLists.txt` | `add_kernel_sources` | ascend950 Kernel 编译接线 |
| 构建接线 | `pooling/dilation2_d/CMakeLists.txt` | `SUPPORT_COMPUTE_UNIT` | ascend950/arch35 Host 接线 |

每行文件均对应 Frontmatter `sources` 中同一固定 commit 的官方 HTTP(S) blob URL。Direct 转换符号只用于说明实现闭包，不伪造成可达官方交付 URL。

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | official-adapted SIMT 可复用 `Dilation2DTilingData` 字段顺序；Vector POD 必须独立 | 不能把 Vector 字段插入官方 POD；需锁定 size/offset/按值 ABI | 官方 `Dilation2DTilingData`；Direct 两 POD |
| 调用顺序 | validate→shape/padding→empty return→tiling→single launch | 空域不得进入 magic division；Route 必须在 launch 前冻结 | `AnalyzeDilation2D`、calc、launcher |
| workspace/内存 | workspace=0；Vector UB 为三 Queue 精确和；SIMT GM 直访 | reserve、depth、Ca、actualW 与有效 extent 不得混淆 | Vector `Init`；SIMT `Process` |
| 同步 | Vector 边界 fill 后 V_MTE2；Queue 生命周期串联；SIMT unique writer | 有效 DMA 不得早于 `-inf` fill；Queue 不得提前复用 | `CopyInputTile`、`Process` |
| 精度与尾块 | FP16 add/max；Vector C/W mask；SIMT globalIdx guard；转换层 NaN propagation | 不能退回 comparison-only max 或忽略 `-inf + +inf` | `ComputeTile`、`ComputeMaxVal` |
| 失败边界 | supplemental Vector 任一 guard 失败回 SIMT；32 位超限回 64 位 | 不能把 supplemental 路线称官方或删除 general SIMT fallback | `vectorSafe`、`Process` |

<!-- cannbot:related:start -->
## 相关

- [Isnan](../../../../apis/simt_api/math_functions/float_math_functions/isnan.md)（`related`）：isnan API 的功能是“判断浮点数是否为nan。”；Dilation2D 950 的 SIMT 规则明确“if isnan(val): return NaN”。算子实现直接调用该判定保持 NaN 传播。
- [VECTOR_REG_WIDTH 只能在 Device 作用域求值](../../../../runbooks/compilation/vector_reg_width_only_in_device_context.md)（`related`）：“RegTensor ｜ channel chunk `r*VECTOR_REG_WIDTH/2`”；“CANN 9.0.1 dav-3510 的 Reg 常量在 device/VF 函数上下文内可见”。Dilation2D Vector 路线以 VECTOR_REG_WIDTH 划分通道，Runbook 给出避免把该常量移到全局作用域的编译边界。
<!-- cannbot:related:end -->
