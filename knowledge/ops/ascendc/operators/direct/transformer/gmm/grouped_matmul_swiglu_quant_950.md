---
type: Operator
title: "GroupedMatmulSwigluQuant 950 Direct Invoke 算子知识"
description: "说明 cann_bench::grouped_matmul_swiglu_quant、launch_grouped_matmul_swiglu_quant_kernel 在 950 上的接口语义、Host/Launcher 参数生成、MIX_CV Route 与融合 Kernel 实现。"
tags: [task.implementation, task.lookup, topic.data_movement, topic.memory, topic.precision, topic.programming_model]
status: stable
sources:
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul_swiglu_quant_v2/README.md
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul_swiglu_quant_v2/op_api/grouped_matmul_swiglu_quant_v2.h
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/grouped_matmul_swiglu_quant_v2_apt.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/arch35/grouped_matmul_swiglu_quant_v2_pertoken_quant.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul_swiglu_quant_v2/op_host/op_tiling/arch35/grouped_matmul_swiglu_quant_v2_basic_tiling.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/gmm/common/cgmct/kernel/kernel_gmm_swiglu_pertoken_quant.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/gmm/common/cgmct/block/block_mmad_builder.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/gmm/common/cgmct/block/block_mmad_multi_block.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/gmm/common/cgmct/block/block_scheduler_gmm_aswt_with_tail_split.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/gmm/common/cgmct/epilogue/block_epilogue_dequant_swiglu.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/gmm/common/cgmct/epilogue/block_epilogue_pertoken_quant.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul_swiglu_quant_v2/op_host/grouped_matmul_swiglu_quant_v2_def.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul_swiglu_quant_v2/CMakeLists.txt
    role: implementation
created_at: "2026-08-25T19:41:59Z"
updated_at: '2026-08-27T12:23:11Z'
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# GroupedMatmulSwigluQuant 950 Direct Invoke 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | `cann_bench::grouped_matmul_swiglu_quant`（Torch schema）→ `grouped_matmul_swiglu_quant_npu` → `calc_grouped_matmul_swiglu_quant_tiling` → `launch_grouped_matmul_swiglu_quant_kernel` |
| 计算语义 | 按累计 `group_list` 做 INT8 GroupedMatmul；INT32 结果乘 FP32 `x_scale`/`weight_scale`，沿 N 二分后做 `Swish(left) * right`，再逐 token 求 `max(abs)/127` 并量化为 INT8。 |
| 输入输出 | 连续 ND `x:[M,K]`、`weight:[E,K,N]`、`weight_scale:[E,N]`、`x_scale:[M]`；输出 `y:[M,N/2]` INT8、`y_scale:[M]` FP32。 |
| 执行类型 | 单 Kernel `MIX_CV`：每个逻辑 block 为 1 个 `AIC_CUBE` 与 2 个 `AIV_VECTOR`；无 SIMT、NDDMA 或通信节点。 |
| Kernel 路线 | P0 / R-001：固定 arch35 INT8/FP32 per-token、RowMajor A/B、ASWT tail-split、`KERNEL_TYPE_MIX_AIC_1_2`。 |
| 核心资源 | GM 输入/输出；FP32 SwiGLU workspace；AIC 的 L1/L0A/L0B/L0C；AIC→AIV 的 VECIN UB；AIV 的寄存器和双缓冲 TQue。 |
| 来源闭包 | `direct_implementation_closed`：Torch direct 入口、Host 校验/tiling、紧凑 launch ABI、MIX entry、Cube/Vector body、workspace、同步、精度、tail 与构建映射均已闭合。 |
| 验证状态 | 已完成源码闭包检查；本次知识提取未执行编译、真机、数值或性能测试。 |

## 接口与语义

### 计算语义

令 `r_-1=0`、`r_g=group_list[g]`、`M_g=r_g-r_{g-1}`，`H=N/2`。Direct 路线固定 `groupListType=0`，即累计边界。对每个非空专家：

```text
Z_g = int32_matmul(X[r_{g-1}:r_g, :], W[g, :, :])
L_g = float(Z_g[:, 0:H]) * x_scale[r_{g-1}:r_g, None] * weight_scale[g, 0:H]
R_g = float(Z_g[:, H:N]) * x_scale[r_{g-1}:r_g, None] * weight_scale[g, H:N]
S_g = (L_g / (1 + exp(-L_g))) * R_g
y_scale[row] = max(abs(S_g[row, :])) / 127
y[row, :] = cast_int8(S_g[row, :] / y_scale[row])
```

两次 MMAD 分别计算 N 的左右半部，INT8×INT8 在 INT32 累加；Vector 先转 FP32，再按 `weight_scale` 后 `x_scale` 的顺序反量化，FP32 完成 `exp/div/mul`。`S` 先物化为 workspace 中的 `[M,H]` FP32，所有分组结束并 `SyncAll` 后，逐行求绝对值最大值与 INT8 输出。

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| `x` | `[M,K]`，连续 ND/RowMajor | INT8 | rank 2；`M,K>0` 由 direct tiler收口。 |
| `weight` | `[E,K,N]`，连续 ND/RowMajor | INT8 | rank 3；K 与 X 一致；Direct 转换固定非转置。 |
| `weight_scale` | `[E,N]`，连续 ND | FP32 | 与专家数和 N 一致；每专家逐通道缩放。 |
| `x_scale` | `[M]`，连续 ND | FP32 | 逐 token 缩放。 |
| `group_list` | Host `int[]`，长度 E | int64 | 累计、非递减、末项必须为 M；`E∈[1,16]`；单组长度不超过 65535；相邻相等表示空组。 |
| `y` | `[M,N/2]`，连续 ND | INT8 | N 必须为正偶数。 |
| `y_scale` | `[M]`，连续 ND | FP32 | 每行 `max(abs(S))/127`。 |
| `workspace` | 一维 byte Tensor | uint8 | `16 MiB + M*(N/2)*4` bytes；前部作为 FP32 SwiGLU 中间结果，额外 16 MiB 保留官方 system-workspace 容量约定。 |

### 入口与版本

这是 Direct Invoke 卡，不是 ACLNN 卡。Torch PrivateUse1 实现创建输出与 workspace，在当前 NPU stream 上通过 `OpCommand::RunOpApi("GroupedMatmulSwigluQuantDirect", callable)` 提交一个 direct kernel。固定转换基于 CANN 9.1.0、ops-transformer Commit `be33d95bb755cedec3108f70805c1874d1792540` 的 `grouped_matmul_swiglu_quant_v2` arch35 per-token CGMCT specialization，目标为 950/Ascend 950、dav-3510。

官方入口接收动态 TensorList `weight/weightScale`、Device `groupList` 和更多量化属性；Direct 入口只接受已连续化的单个 `[E,K,N]`、`[E,N]` Tensor，并把 Host `group_list` 压成四个 uint64。它不执行 TransData、TensorList descriptor 解析、ACLNN executor 构造或通用 tiling-key 分发。官方 README 对 950 公开接口描述的是 MX FP8/FP4 合同；本卡的 INT8/FP32 路线是固定源码内部 per-token body 的 Direct 转换，不应外推为 950 ACLNN 的公开 INT8 支持声明。

## Host/Launcher 执行流程

### 参数校验与前处理

`grouped_matmul_swiglu_quant_meta` 检查 X/weight/scale 的 rank、INT8/FP32 dtype、K/E/N/M 对应关系、N 为正偶数以及 `group_list.size()==E`，并创建 `y:[M,N/2]`、`y_scale:[M]`。NPU 实现再要求四个输入 Tensor 连续；不存在隐式 contiguous 或 TransData。

`calc_grouped_matmul_swiglu_quant_tiling` 拒绝 `M<=0`、`K<=0`、`N<=0/奇数`、空 group、`E>16`，逐项验证累计边界，计算每组差值并把四个 16-bit group size 装入一个 uint64；最后一项不等于 M 或单组大于 65535 均失败。随后查询 AIC/UB/L1/L0C，计算 Cube tiling、`rowLen=N/2`、`ubAvail`、blockDim 和 workspace。

### 参数、Workspace 与生命周期

Host `GMMSQLaunchParams` 按值捕获进 `RunOpApi` callable；launcher 把其中实际 Device 消费的字段重打包为 `meta/dims/tile` 三个 uint64，并连同 7 个 GM pointer 与 4 个 group pack 启动 Kernel，最终 Device launch ABI 为 112 bytes。`TCubeTiling` 不直接穿过 raw launch aggregate ABI，而是在 Device 由三个 scalar pack 重建。

workspace Tensor 的 Host 分配长度是：

```text
H = N / 2
user_fp32 = M * H * sizeof(float)
workspace_total = 16 * 1024 * 1024 + user_fp32
```

当前 direct body 将 workspace 基址直接作为 `[M,H]` FP32 中间区，偏移 `[0,user_fp32)`；代码没有把指针加 16 MiB，因而额外 system-workspace 容量位于未显式切片的剩余区。workspace 的 Host Tensor 活到 callable 完成提交；Device 期间的存活依赖当前 stream 与框架 allocator 的异步生命周期，转换源码未显式 `recordStream`。

### 启动图与失败传播

```text
cann_bench::grouped_matmul_swiglu_quant
  -> grouped_matmul_swiglu_quant_npu / meta validation
    -> calc_grouped_matmul_swiglu_quant_tiling / pack group sizes
      -> allocate y, y_scale, workspace
        -> RunOpApi callable on current stream
          -> launch_grouped_matmul_swiglu_quant_kernel
            -> schemMode=1, blockDim=aicNum
              -> grouped_matmul_swiglu_quant_direct_kernel [MIX_AIC_1_2]
                -> AIC: two INT8 MMAD halves -> L0C -> VECIN
                -> AIV: FP32 dequant + SwiGLU -> GM workspace
                -> SyncAll
                -> AIV: workspace -> per-token quant -> y/y_scale
```

Meta、连续性或 tiling 失败由 `TORCH_CHECK` 在 launch 前终止。平台对象为空、AIC 数为零、UB/L1/L0C 不足也使 tiler 返回 false。launcher 设置 `ACL_RT_LAUNCH_KERNEL_ATTR_SCHEM_MODE=1`；callable 对 launch 本身固定返回 0，未单独检查异步 Kernel launch 状态。空专家在 Device 跳过，但只要最终累计值 M 正确，其余专家继续执行。

## Route 与参数设计

### 分核与资源计算

Host 从原始 M/K/N 推导：

```text
baseM = align_up(min(M,128),16)
baseN = align_up(min(N,256),32)
baseK = align_up(min(K,128),32)
baseA = baseM * baseK bytes
baseB = baseN * baseK bytes
scaleReserve = baseN * sizeof(float)
```

L1 先扣 `scaleReserve`，再由 `GetDepthA1B1Host` 选择 A1/B1 depth；`stepKa=depthA1/2`、`stepKb=depthB1/2`，分别裁到 `ceil(K/baseK)`，并调整为整倍数关系，最终 `depthA1=2*stepKa`、`depthB1=2*stepKb`。`dbL0A=dbL0B=2`；若 `2*baseM*baseN*sizeof(int32)<=L0C_size`，`dbL0C=2`，否则为 1。`usedCoreNum=blockDim=aicNum`。

Vector 行量化使用 `rowLen=N/2`、`alignedRowLen=align_up(rowLen,16)`，`ubAvail=(UB_size-1024)/(alignedRowLen*14)`。实际每次最多处理 `min(ubAvail,255,rows_per_vector_core)` 行；`vectorCoreNum=blockDim*2` 与 MIX 1:2 对应。

### Route 选择

本卡只有一个 Host 可达 Route，重要性为 P0；Route 选择表、执行矩阵、源码闭包与 Kernel 展开均按 `P0 / R-001` 的同一顺序展示。

| 顺序 | Route | Key/模板 | 精确选择条件与优先级 | 不适用去向 |
|---:|---|---|---|---|
| 1 | P0 / R-001 INT8 per-token MIX_CV | 特征：无 runtime tiling key；固定 `RowMajor/RowMajor` CGMCT 与单 Kernel MIX 1:2 实例 | 适用域：950、INT8 X/W、FP32 scales、N 正偶数、累计 group list、`1<=E<=16`、单组 `<=65535`；实现前提：连续 ND、Host 校验通过且 UB/L1/L0C 可构造 tiling；优先级 P0，唯一可达 Route | Host 返回失败；无下一 Route 或 Device fallback |

```text
if schema/shape/dtype/contiguous/group-list invalid: fail before launch
else if AIC/UB/L1/L0C or tiling capacity invalid: fail before launch
else: P0 / R-001 fixed arch35 per-token MIX_AIC_1_2
```

### 模板/实现执行矩阵

| Route | key/selector | dtype/shape/platform 完整命中条件 | 执行族与 kernel 节点 | 实际模板/body | 内存与同步特征 | tail/fallback |
|---|---|---|---|---|---|---|
| P0 / R-001 | fixed direct specialization | 表中合法域，950/dav-3510 | 单 Kernel：AIC_CUBE ↔ 两个 AIV_VECTOR；末段仍为同 Kernel AIV | `KernelGmmSwiGluPertokenQuant<MatmulShape,BlockMmadBuilder<int8_t,RowMajor,int8_t,RowMajor,int32_t,RowMajorAlign,float,RowMajor,Shape<_0,_0,_0>,Shape<_0,_0,_0>,GroupedMatmulAswtWithTailSplitScheduler,MatmulMultiBlock<>,TileCopy<DAV3510,CopyInAndCopyOutSplitMWithParams>>,BlockEpilogueDequantSwiglu<Shape<_0,_0,_0>,float,int32_t,float,float,true>,BlockEpiloguePertokenQuant<float,int8_t>,GroupedMatmulAswtWithTailSplitScheduler,float,float>` | AIC/AIV flags 4/20 与 6/22；FP32 workspace；最终 `SyncAll`；量化 TQue 双缓冲 | M/N/K tile tail、末专家 tail split、空组 skip；不满足无 fallback |

### 隐藏性能 Guard

| Guard | Host/Tiling 条件 | Device/资源原因 | 影响 Route | 不满足时去向 | 源码符号 |
|---|---|---|---|---|---|
| Cube base | `M,K,N>0`，base tile 可放入 L1/L0C | 固定 int8 Cube tile 与 FP32 L0C | P0 / R-001 | Host fail | `FillCubeTiling` |
| L1 scale reservation | `L1 > baseN*4` 且剩余 `>=baseA+baseB` | B scale 与 A1/B1 共用 L1 预算 | P0 / R-001 | Host fail | `FillCubeTiling` |
| L0C double buffer | `2*baseM*baseN*4<=L0C_size` | 两阶段 INT32 accumulator | P0 / R-001 | 降为 `dbL0C=1` | `FillCubeTiling` |
| AIV UB 行批 | `ubAvail=(UB-1024)/(align16(H)*14)` | 输入 FP32、INT8 输出、scale 与双缓冲总预算 | P0 / R-001 | `ubAvail==0` 时 Device 行循环不可成立；Host 仅检查 `UB>1024` | `DoOpTilingPertoken` 对应式、`CalParams` |
| dequant 固定 UB | 950 UB 至少覆盖 199680 bytes | 两块 INT32/FP32 VECIN、SwiGLU VECOUT与三个 scale buffer使用固定地址 | P0 / R-001 | 转换 Host没有显式容量 fallback | `BlockEpilogueDequantSwiglu::Init` |
| compact ABI 宽度 | M/N/K 进 16 bit，baseM/深度/step 进 8 bit | raw launch 只传 3 个 uint64 metadata | P0 / R-001 | 转换源码没有溢出 fallback | `launch_grouped_matmul_swiglu_quant_kernel`, `RebuildCubeTiling` |
| B L2 hint | 单专家 `M_g<=baseM`、`N%256==0`、`baseN%256==0`，且 `K<=256 || K>=4096` | 一次性 B 流关闭 L2；中等 K 保留 cache 供 tail 分片复用 | P0 / R-001 每专家 | normal cache | `UpdateGlobalBuffer` |
| scale L2 hint | `M_g<=baseM && N%256==0 && baseN%256==0` | 一次性 weight_scale 读取 | P0 / R-001 每专家 | normal cache | `SetX2ScaleL2CacheHint` |
| schedule mode | 恒设 `schemMode=1` | MIX 1:2 的配对 AIC/AIV flag 协议要求批调度 | P0 / R-001 | 无替代 launch | `launch_grouped_matmul_swiglu_quant_kernel` |

### POD/ABI

| 结构 | 字段 | 类型/位宽 | ABI 布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| `GMMSQLaunchParams` | `blockDim` | int64/64 | offset 0 | AIC blocks | `FillCubeTiling=aicNum` | launch grid | >0 |
| 同上 | `groupNum` | uint32/32 | offset 8 | groups | `groupList.size()` | `meta[7:0]` | 1..16 |
| 同上 | `rowLen` | uint32/32 | offset 12 | elements/row | `N/2` | `meta[23:8]`、quant epilogue | Device pack 16 bit |
| 同上 | `ubAvail` | uint32/32 | offset 16 | rows/batch | UB formula | `meta[39:24]`、quant epilogue | Device pack 16 bit |
| 同上 | `groupListType` | uint8/8 | offset 20 | enum | 固定 0 | inactive；Device 构造时写 0 | 仅 cumsum |
| 同上 | `dequantDtype` | uint8/8 | offset 21 | enum | 固定 0 | inactive；模板已固定 float | 不参与 launch |
| 同上 | `quantDtype` | uint8/8 | offset 22 | enum | 固定 2 | inactive；模板已固定 int8 | 不参与 launch |
| 同上 | `reserved` | uint8/8 | offset 23 | reserved | 零初始化 | 不读取 | 必须保持 0 |
| 同上 | `workspaceSize` | size_t/64 | offset 24 | bytes | workspace 公式 | Host allocator | 不传 Device |
| 同上 | `groupSizePacks[4]` | uint64×4 | offset 32..63 | 4×uint16/group | `groupSize << 16*(g%4)` | `GetPackedGroupSize` | 每组 0..65535 |
| 同上 | `cubeTiling[256]` | byte[256], align 8 | offset 64；LP64 推导 `sizeof=320,alignof=8` | POD bytes | `memcpy(TCubeTiling)` | launcher 读取并重打包 | `sizeof(TCubeTiling)<=256` |
| Device args | `x,weight,weightScale,xScale,y,yScale,workspace` | GM pointer×7 | args 0..55 | addresses | launcher | entry/CGMCT | 各 Tensor 生命周期覆盖 stream work |
| Device args | `groupSizePack0..3` | uint64×4 | args 56..87 | group sizes | launch params | `GetPackedGroupSize` | E<=16 |
| Device args | `meta` | uint64 | args 88..95 | packed fields | launcher | entry/Rebuild | group 8b、row 16b、UB 16b、dbL0C 8b、cores 8b |
| Device args | `dims` | uint64 | args 96..103 | packed elements | launcher | `RebuildCubeTiling` | M/N/K 16b、baseM 8b |
| Device args | `tile` | uint64 | args 104..111 | packed tile/stages | launcher | `RebuildCubeTiling` | baseN/baseK 16b；depth/step 8b |
| rebuilt `TCubeTiling` | `M,N,Ka,Kb` | int32 | SDK ABI；本转换不透传结构 | elements | `RebuildCubeTiling(dims)` | Matmul/scheduler | 来自 16-bit pack |
| 同上 | `baseM,baseN,baseK` | int32 | SDK ABI | elements | `RebuildCubeTiling(dims,tile)` | scheduler/Matmul | 16/32/32 对齐 |
| 同上 | `depthA1,depthB1,stepKa,stepKb` | int32 | SDK ABI | stages/K tiles | `RebuildCubeTiling(tile)` | Matmul pipeline | 8-bit pack |
| 同上 | `dbL0A,dbL0B,dbL0C` | int32 | SDK ABI | stages | 2、2、`meta` | L0 pipeline | dbL0C 1/2 |
| 同上 | `usedCoreNum` | int32 | SDK ABI | AIC cores | `meta[55:48]` | scheduler/Matmul | 8-bit pack |

`GMMSQLaunchParams` 的数字布局按声明和 LP64 对齐规则推导；固定转换源码没有单独的 `offsetof` 静态断言。本次提取未编译验证这些推导值。

### Route 源码闭包

| Route | Key/selector | Host/Tiling producer | POD/参数 | Kernel entry/router | Kernel body/直接依赖 | 构建接线 |
|---|---|---|---|---|---|---|
| P0 / R-001 | fixed arch35 per-token | `grouped_matmul_swiglu_quant_plugin.cpp::grouped_matmul_swiglu_quant_npu`；`grouped_matmul_swiglu_quant_kernel.cpp::FillCubeTiling/calc_*` | `GMMSQLaunchParams` → 7 pointers + 4 packs + `meta/dims/tile` | `grouped_matmul_swiglu_quant_direct_kernel` → `RunOfficialPertokenRoute` | `KernelGmmSwiGluPertokenQuant`；`BlockMmadBuilder/MatmulMultiBlock`；ASWT scheduler；dequant-SwiGLU 与 per-token quant epilogues | conversion operator CMake；官方 `gmm/grouped_matmul_swiglu_quant_v2/CMakeLists.txt` 为对应算子构建映射 |

## Kernel 实现

### 公共执行流程

只有 P0 / R-001。entry 声明 `KERNEL_TYPE_MIX_AIC_1_2`，保存 overflow control SPR 60、临时设为 0，重建 `TCubeTiling` 并实例化固定 CGMCT 模板。AIC 与 AIV 共享同一个参数对象和 tiling，但通过 `ASCEND_IS_AIC/AIV` 分支执行不同 body。

每专家由 ASWT 在 `[M_g,H]` tile 域分配工作。AIC 对同一 X tile 先计算 W 左半部、再计算右半部，结果通过 Matmul `TPosition::VECIN`/`CopyInAndCopyOutSplitMWithParams` 落到两块 AIC→AIV UB。两个 AIV sub-block 各处理 M tile 的一半，反量化并做 SwiGLU，写 FP32 workspace。最后一次 AIC/AIV 握手完成后 `SyncAll`，AIV 按全局行域重新分核，从 workspace 做逐 token 量化；AIC 不执行这一尾段。

### Route R-001：P0 INT8 per-token MIX_CV

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct Host | `op_plugin/grouped_matmul_swiglu_quant_plugin.cpp` | `grouped_matmul_swiglu_quant_meta/npu` | rank、dtype、shape、N even、continuous | 进入 tiler或抛错 |
| Tiling | `op_kernel/grouped_matmul_swiglu_quant_kernel.cpp` | `calc_grouped_matmul_swiglu_quant_tiling` | cumsum、E<=16、group size<=65535、末项=M、资源合法 | 固定 params 或 false |
| Launcher | 同上 | `launch_grouped_matmul_swiglu_quant_kernel` | 无 key；`schemMode=1`、grid=aicNum | 单 MIX kernel |
| Router | 同上 | `RunOfficialPertokenRoute` | compile-time INT8/FP32、RowMajor A/B、DAV3510 | 固定 `QGmmKernel` |
| Device | `cgmct/kernel/kernel_gmm_swiglu_pertoken_quant.h` | `operator()/ProcessSingleGroup` | 非空专家、ASWT tile 可达 | Cube↔Vector；结束后 quant |

#### Device 数据流

##### 函数级调用链

```text
grouped_matmul_swiglu_quant_direct_kernel
  -> RebuildCubeTiling
  -> RunOfficialPertokenRoute
    -> KernelGmmSwiGluPertokenQuant::operator()
      -> UpdateGroupParams / ProcessSingleGroup
        -> BlockSchedulerGmmAswtWithTailSplit::GetTileIdx/GetBlockShape
        -> AIC: BlockMmad::operator() [left] -> l0cOutUbFirst
        -> AIC: BlockMmad::operator() [right] -> l0cOutUbSecond
        -> CrossCore flags
        -> AIV: BlockEpilogueDequantSwiglu::operator() -> workspace FP32
      -> End -> SyncAll
      -> AIV: BlockEpiloguePertokenQuant::operator() -> y/y_scale
```

##### 源码等价伪码

```text
# 伪码；保持源码阶段顺序
rebuild mmTiling(meta,dims,tile)
for g in [0,E):
  M_g = unpack_u16(groupPack[g/4], g%4)
  update X/W/scale/workspace base offsets
  if M_g == 0: continue
  scheduler.update([M_g,H,K])
  if g == E-1: scheduler.update_tail_tile()
  for tile in scheduler:
    if AIC:
      if not first tile: wait flags 6 and 22 from two AIV
      C0 = mmad_int8(X_tile, W_left_tile)   # int32 L0C -> first VECIN UB
      C1 = mmad_int8(X_tile, W_right_tile)  # int32 L0C -> second VECIN UB
      set flags 4 and 20
    if AIV:
      wait flag 4 for paired AIC
      load weight_scale halves and x_scale rows GM->UB
      S_tile = swish(float(C0)*wscale0*xscale) * (float(C1)*wscale1*xscale)
      copy S_tile UB->workspace GM
      set flags 6 and 22
AIC waits final AIV completion
SyncAll()
if AIV:
  partition M rows across blockDim*2 vector cores
  for row batch:
    workspace GM -> double-buffered UB
    scale = reduce_max(abs(row))/127
    y = cast_int8(row/scale)
    UB -> y GM and y_scale GM
restore overflow SPR
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM X | `rowStart_g*K + tile_m*K` | `[M,K]` | INT8 RowMajor | caller | AIC MTE2/Matmul | input Tensor；全 Kernel | K tail 由 Matmul tiling |
| GM W | `g*K*N + tile_n`；右半再 `+H` | `[E,K,N]` | INT8 RowMajor | caller | AIC MTE2/Matmul | input Tensor；全 Kernel | baseK 32、baseN 32 对齐 |
| GM scales | X：`rowStart_g+tile_m`；W：`g*N+tile_n` 与 `+H` | X `[M]`、W `[E,N]` | FP32 ND | caller | AIV MTE2 | inputs；dequant阶段 | W scale tile `singleN*4` bytes |
| L1 A1 | Matmul内部 | `depthA1*baseM*baseK` bytes | INT8 | GM X | L0A | Matmul pipeline | depth=2*stepKa |
| L1 B1 | Matmul内部 | `depthB1*baseN*baseK` bytes | INT8 | GM W | L0B | Matmul pipeline | depth=2*stepKb；另预留 `baseN*4` |
| L0A | Matmul内部 | `2*baseM*baseK` bytes | INT8 | L1 A1 | MMAD | AIC tile | double buffer |
| L0B | Matmul内部 | `2*baseN*baseK` bytes | INT8 | L1 B1 | MMAD | AIC tile | double buffer |
| L0C | Matmul内部 | `dbL0C*baseM*baseN*4` bytes | INT32 RowMajorAlign | MMAD | CopyCo1ToOut | AIC tile | dbL0C 1/2 |
| VECIN first/second | fixed offsets 0、`16384*4` | 各 `64*256*4=65536` bytes | INT32；随后同地址解释 FP32 | AIC CopyCo1ToOut | 两个 AIV | 单 tile；flag 保护 | 两块共 128 KiB；dequant原地复用 |
| AIV SwiGLU VECOUT | offset 128 KiB | `64*256*4=65536` bytes | FP32 | Vector registers | MTE3 | 单 tile | 后接 3 个 256×FP32 scale buffer |
| scale UB | 192 KiB 后顺排 | `3*256*4=3072` bytes | FP32 | GM scales | Vector dequant | 单 tile | left/right W scale + X scale |
| GM workspace S | `(rowStart_g*H)+tileOffset` | `M*H*4` bytes | FP32 RowMajor | AIV SwiGLU | AIV per-token quant | workspace Tensor；两阶段之间 | 有效前缀；无专家间重叠 |
| quant inQueue | 每 core GM base 按 head/tail 行划分 | `2*multiRow*align8(H)*4` bytes | FP32 | workspace GM | Vector registers | quant loop | TQue depth 2；Host 的 `align16(H)*14` 是保守行预算 |
| quant outQueue | 同一行域 | `2*multiRow*align32(H)` bytes | INT8 | Vector registers | y GM | quant loop | TQue depth 2 |
| quant scaleQueue | 每批行 | `2*align8(multiRow)*4` bytes | FP32 | ReduceMax | y_scale GM | quant loop | TQue depth 2 |
| 寄存器 | 每 VF repeat | vector register width | FP32/INT16/FP16/INT8 | UB load | UB store | 单 repeat | mask 保护 H tail |

##### 分层内存布局

```mermaid
flowchart LR
  X["GM X INT8"] --> A1["L1 A1"] --> A0["L0A"]
  W["GM W left/right INT8"] --> B1["L1 B1"] --> B0["L0B"]
  A0 --> MM["AIC MMAD ×2\nINT32 accumulate"]
  B0 --> MM
  MM --> C0["L0C"] --> V0["VECIN UB\nleft/right INT32"]
  XS["GM x_scale FP32"] --> VS["AIV scale UB"]
  WS["GM weight_scale FP32"] --> VS
  V0 --> DV["AIV FP32 dequant\nSwish(left)*right"]
  VS --> DV
  DV --> TMP["GM workspace S[M,H] FP32"]
  TMP --> QUB["AIV double-buffer TQue"]
  QUB --> REG["Reg reduce max / divide / cast"]
  REG --> Y["GM y INT8"]
  REG --> YS["GM y_scale FP32"]
```

##### 字节账、交接边与复用顺序

```text
H = N/2
workspace_total = 16 MiB + M*H*4
L1 = depthA1*baseM*baseK + depthB1*baseN*baseK + baseN*4
L0 = 2*baseM*baseK + 2*baseN*baseK + dbL0C*baseM*baseN*4
dequant_UB = 2*(64*256*4) + (64*256*4) + 3*(256*4) = 199680 bytes
quant_UB = 2*multiRow*align8(H)*4 + 2*multiRow*align32(H) + 2*align8(multiRow)*4
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| AIC→AIV first half | first MMAD | VECIN offset 0，`singleM*singleN*4` logical | INT32 RowMajorAlign | AIV dequant left | flags 4/20；AIV wait 4 | MIX shared local buffer；一 tile | 下次 AIC 覆盖前等 flags 6/22 |
| AIC→AIV second half | second MMAD | VECIN offset 65536，等量 | INT32 RowMajorAlign | AIV dequant right | 同上 | 同上 | `singleM/2<=64`、`singleN<=256` |
| dequant→SwiGLU | AIV dequant | 同两块 UB 原地转 FP32 | FP32 | AIV SwiGLU | MTE2_V hard event | AIV tile | scale copy 完成且 mask 有效 |
| SwiGLU→workspace | AIV MTE3 | `(row*H+col)*4` | FP32 RowMajor | final quant | per tile V_MTE3；全局 `SyncAll` | workspace Tensor | 每 tile disjoint；全生产完成后读取 |
| workspace→quant queues | final AIV | head/tail core 连续行片 | FP32 | ReduceMax/quant | TQue EnQue/DeQue | quant phase | `blockIdx<coreNum`；tail batch单独处理 |
| dequant UB→quant UB 复用 | dequant epilogue | 同一物理 UB 空间 | phase-dependent | quant TPipe queues | AIC final wait + `SyncAll` | 单 Kernel | 所有 workspace 写完才重新 InitBuffer |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| AIC→2×AIV | `CrossCoreSetFlag<SYNC_AIC_AIV_MODES,PIPE_FIX>(4/20)` | 两次 MMAD+CopyCo1ToOut | AIV `CrossCoreWaitFlag<SYNC_AIC_AIV_MODES,PIPE_V>(4)` | 两块 VECIN UB | INT32 accumulator；M/N/K tail由 Matmul |
| 2×AIV→AIC | AIV逻辑 flag 6/22 | 两个 AIV epilogue | AIC `CrossCoreWaitFlag<SYNC_AIC_AIV_MODES,PIPE_FIX>(6/22)` 或 `End` | 防止 UB 提前覆盖 | AIV 以 subBlockIdx 二分 M；空半块直接返回 |
| GM scale→Vector | `MTE2_V` hard event | MTE2 | dequant VF | scale UB | INT32→FP32 `CAST_RINT`，再乘 FP32 scales |
| Vector→GM workspace | `V_MTE3`、随后 `MTE3_V/V_MTE2` | SwiGLU VF | MTE3/下一搬运 | FP32 S tile | `exp/div/mul` 均 FP32；N tail mask |
| 两大阶段 | AIC final `WaitForVector` + `SyncAll` | 全部 SwiGLU tiles | per-token quant | workspace 完整可见与 UB phase reuse | 空专家不写；总体 M 由 pack 累加 |
| per-token quant | TQue depth 2 + VF masks | workspace MTE2 | ReduceMax/Div/Cast/MTE3 | 行批 | `scale=maxabs/127`；F32→I16 RINT→FP16 ROUND→I8 TRUNC，NO_SAT；H tail padding/mask |
| kernel 范围 | SPR 60 save/set(0)/restore | entry | 全 body/return | float overflow behavior | 没有单独的零行 `scale=0` 分支；固定源码行为保留 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `op_kernel/grouped_matmul_swiglu_quant_kernel.cpp` | `FillCubeTiling`, `calc_grouped_matmul_swiglu_quant_tiling` | tile/depth/UB/workspace/group pack |
| Kernel entry/router | 同上 | `grouped_matmul_swiglu_quant_direct_kernel`, `RunOfficialPertokenRoute` | MIX 1:2 与唯一模板实例 |
| Cube body | `gmm/common/cgmct/block/block_mmad_builder.h`、`block_mmad_multi_block.h` | `BlockMmadBuilder`, `MatmulMultiBlock<>` | GM→L1/L0→INT32 L0C→VECIN |
| MIX orchestration | `gmm/common/cgmct/kernel/kernel_gmm_swiglu_pertoken_quant.h` | `ProcessSingleGroup`, `NotifyVector/Cube`, `End` | 两半 MMAD、flags、workspace阶段、SyncAll |
| Vector epilogues | `gmm/common/cgmct/epilogue/block_epilogue_dequant_swiglu.h`、`block_epilogue_pertoken_quant.h` | `VFDoPertokenDequantAndSwiglu`, `ComputeScaleVF/ComputeYVF` | FP32 dequant/SwiGLU 与逐行 INT8 quant |
| Scheduler | `gmm/common/cgmct/block/block_scheduler_gmm_aswt_with_tail_split.h` | `UpdateNextProblem`, `UpdateTailTile`, `GetTileIdx` | ASWT window、轮转专家起始 core、最后专家 tail split |

## 算子特定优化

### Trick T-001：两次 Cube MMAD 与 Vector epilogue 在单个 MIX Kernel 内交接

#### 触发与源码依据

- 适用 Route：P0 / R-001。
- 触发条件：固定 `KERNEL_TYPE_MIX_AIC_1_2`、RowMajor INT8 per-token specialization，当前 tile 非空。
- Golden 来源：[`gmm/common/cgmct/kernel/kernel_gmm_swiglu_pertoken_quant.h:301`](https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/gmm/common/cgmct/kernel/kernel_gmm_swiglu_pertoken_quant.h#L301-L316)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
            if ASCEND_IS_AIC {
                if (isVecSetSyncCom_) {
                    WaitForVector();
                }
                AscendC::Std::tuple<int32_t, int32_t, int32_t> mmSingleShape{Get<M_VALUES>(singleShape),
                                                                             Get<N_VALUES>(singleShape), k};
                // left block
                mmadOp_(aGlobal_[Get<INDEX_A_OFFSET>(blockOffset_)], bGlobal_[Get<INDEX_B_OFFSET>(blockOffset_)],
                        l0cOutUbFirst_, mmSingleShape, transA, transB);
                // right block
                int64_t bRightOffset = Get<INDEX_B_OFFSET>(blockOffset_);
                ComputeOffset(bRightOffset, n, k);
                mmadOp_(aGlobal_[Get<INDEX_A_OFFSET>(blockOffset_)], bGlobal_[bRightOffset], l0cOutUbSecond_,
                        mmSingleShape, transA, transB);
                NotifyVector();
            }
```

#### 机制与设计原因

当前实例把 Matmul C 类型设为 `TPosition::VECIN` 的 INT32，而非先写 GM。AIC 对左右 N 半区各做一次 MMAD；配对的两个 AIV 在同一 launch 内直接消费共享 local buffer，完成 FP32 dequant 与 SwiGLU。flags 4/20 和 6/22形成生产、消费、再覆盖闭环，消除了 INT32 `[M,N]` 中间 GM 物化。

#### 迁移边界

- 适用：AIC 产生两个等宽门控分支、AIV 紧接非线性 epilogue 的 arch35 MIX 路线。
- 前提：N 为偶数，AIC:AIV=1:2，`schemMode=1`，两块 VECIN 容量覆盖每个 tile，模板 C 类型/布局与 AIV 读取一致。
- 失效：AIC-only launch、比例不同、N 不可二分、C 输出到 GM 或 flags 编号/轮次改变时必须重建交接协议。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

只保留 `NotifyVector` 而删除 AIC 对 flags 6/22 的等待会允许下一 tile 覆盖仍被两个 AIV 消费的 UB；只启动 AIC 或关闭 schedule mode 1 会使配对等待无法闭合。

### Trick T-002：FP32 SwiGLU workspace 与全局逐 token 量化分阶段复用 AIV

#### 触发与源码依据

- 适用 Route：P0 / R-001。
- 触发条件：`dequantDtype=float`、最终输出 INT8、所有专家 SwiGLU tile 已写 workspace。
- Golden 来源：[`gmm/common/cgmct/epilogue/block_epilogue_pertoken_quant.h:197`](https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/gmm/common/cgmct/epilogue/block_epilogue_pertoken_quant.h#L197-L205)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
    uint32_t rowNum = realM;
    uint32_t vectorCoreNum = uint32_t(GetBlockNum() * GetTaskRation());
    headCoreNum_ = rowNum % vectorCoreNum;
    rowPerHeadCore_ = (rowNum + vectorCoreNum - 1U) / vectorCoreNum;
    rowPerTailCore_ = rowNum / vectorCoreNum;
    coreNum_ = vectorCoreNum < rowNum ? vectorCoreNum : rowNum;
    coreNum_ = coreNum_ > 1 ? coreNum_ : 1;
    multiRowNumHeadCore_ = min(params_->ubAvail, min(COMPARE_INT, rowPerHeadCore_));
    multiRowNumTailCore_ = min(params_->ubAvail, min(COMPARE_INT, rowPerTailCore_));
```

#### 机制与设计原因

SwiGLU 后先写 `[M,H]` FP32 workspace，使逐行 `ReduceMax(abs)` 能在完整行上计算统一 scale。`SyncAll` 把 tile 级 MIX 阶段和全局行量化阶段隔开；随后同一批 AIV 按 `blockDim*2` 划分 head/tail 行，`ubAvail` 与 255 上限约束每批行数，三个 depth-2 TQue 覆盖 GM copy、VF 与 copy-out。

#### 迁移边界

- 适用：非线性结果需要按完整行生成单 scale 的 per-token quant。
- 前提：workspace 至少 `M*H*4` bytes，阶段间存在全局可见性，行域连续，UB 公式与实际 TQue dtype/对齐一致。
- 失效：per-tile scale、不同输出量化格式或跨 Kernel 实现必须重新定义 workspace 边与 stream/event ordering。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

在某个 SwiGLU tile 写完后立即对该 tile独立求 scale 会改变逐 token 全行量化语义；删除 `SyncAll` 会让 quant 读取尚未完成的 workspace 行。

### Trick T-003：仅最后专家启用 ASWT tail tile 再拆分

#### 触发与源码依据

- 适用 Route：P0 / R-001。
- 触发条件：`groupIdx+1==groupNum`；剩余空闲 core 足以使 `remainTile>1`。
- Golden 来源：[`gmm/common/cgmct/block/block_scheduler_gmm_aswt_with_tail_split.h:151`](https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/gmm/common/cgmct/block/block_scheduler_gmm_aswt_with_tail_split.h#L151-L176)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
        int64_t remainTile = (AscendC::GetBlockNum() - endBlockIdx_ - 1) / GetTailTileCnt() + 1;
        if (remainTile <= 1) {
            return;
        }

        // Initialize the minimum tile sizes.
        int64_t mMin = AscendC::BLOCK_CUBE;
        int64_t nMin = AscendC::BLOCK_CUBE;

        // Adjust the minimum tile sizes based on the A/B transpose layout.
        if constexpr (TransA_) {
            mMin = INNER_AXIS_MIN_SPLIT_VAL;
        }
        if constexpr (!TransB_) {
            nMin = INNER_AXIS_MIN_SPLIT_VAL;
        }
        int64_t mTile = Min(CeilDiv(mBaseTail_, mMin), remainTile);
        int64_t nTile = Min(CeilDiv(nBaseTail_, nMin), remainTile);
        while (mTile * nTile > remainTile) {
            if (mTile >= nTile) {
                mTile -= 1;
            } else {
                nTile -= 1;
            }
        }
        UpdateTailTile(mTile, nTile);
```

#### 机制与设计原因

ASWT 在多个专家间轮转起始 core；提前拆某一专家尾块会破坏后续专家复用的 rotating window。Direct body只在最后专家调用官方 `UpdateTailTile()`，此时已无后继专家，可把末轮 M/N tail 拆给原本空闲 core；`GetBlockShape` 仍按实际剩余 M/N 截断，并把 split offset纳入 X/W/workspace 地址。

#### 迁移边界

- 适用：最后一个非后继复用阶段的 ASWT grouped Matmul。
- 前提：scheduler 的 `endBlockIdx_`、tail count、M/N 最小切分对齐与 `GetBlockShape` 同步更新。
- 失效：后面仍有共享同一 rotating window 的专家、transpose 改变 inner-axis 最小切分，或输出 offset未包含 split offset时不能直接复用。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

对每个专家无条件调用 tail split 会占用后续专家预期的 core window；只扩大 `endBlockIdx_` 而不更新 tile 到 split offset 的映射会产生覆盖或漏算。

## 模板与实现对比

| 对比维度 | P0 / R-001 INT8 per-token MIX_CV | 设计选择依据 |
|---|---|---|
| 命中条件/优先级 | P0；唯一 Direct route；Host 合法域通过即命中 | Direct 接口固定该 dtype/layout/量化合同，不保留官方多 dtype/key router |
| 执行族/节点图 | 单 Kernel AIC_CUBE↔2×AIV_VECTOR，随后同 Kernel AIV quant | `KERNEL_TYPE_MIX_AIC_1_2` 与交叉核 flags |
| M/N/K、tile 与 scheduler | baseM<=128、baseN<=256、baseK<=128；ASWT + last-group tail split | arch35 basic tiling 与 CGMCT specialization |
| workspace/L1/L0/UB | FP32 `[M,N/2]` workspace；A1/B1 depth；L0 double buffer；dequant/quant UB phase reuse | SwiGLU tile与全行 scale 的语义边界 |
| AIC/AIV 或 kernel 交接 | VECIN 两块 INT32 local buffer，flags 4/20、6/22 | 避免 INT32 GM 中间结果且防止覆盖 |
| 同步、精度与 tail | schedule mode 1、hard events、SyncAll；INT32→FP32→INT8；M/N/K/VF tail | 固定官方 body 顺序 |
| fallback/失败边界 | Host fail，无第二 Route或 Device fallback | Direct ABI只为该 specialization构造 |

## 平台差异

| 项目 | A2 | A3 | 950 |
|---|---|---|---|
| 支持状态 | 官方公开算子有 INT8 A8W8 描述；本 Direct 转换未构建/验证 | 官方公开算子有 INT8 A8W8 描述；本 Direct 转换未构建/验证 | 本卡 Direct 目标为 Ascend 950/dav-3510；官方 README 的 950 公开合同仅列 MX FP8/FP4，故不得把本路线声明为 ACLNN INT8 支持 |
| Host/Launcher | 固定仓未提供本 Direct launcher | 固定仓未提供本 Direct launcher | compact 112-byte ABI、schemMode=1、blockDim=aicNum |
| Kernel/资源 | 本卡不外推 | 本卡不外推 | DAV3510 TileCopy、MIX_AIC_1_2、arch35 tiling、950 UB/L1/L0C 查询 |

## 限制与失败边界

- Direct 语义固定 INT8 X/W、FP32 scales、RowMajor non-transpose、cumsum group list、INT8 per-token output；官方其它 dtype、NZ/ZN、transpose、MX、bias、smoothScale、稀疏 group list与确定性 router均不在本卡 Route。
- `E<=16`、每组 token 数 `<=65535`；N 必须正偶数。compact ABI 还把 M/N/K压为 16 bit，baseM/depth/step压为 8 bit，但 Host没有显式检查这些 pack 上界；超出时会截断，不能复用。
- Host仅检查输入连续性，没有完成通用 device一致性、所有整数乘法溢出、固定 199680-byte dequant UB 容量与 `ubAvail>0` 检查；这些是调用方边界。
- workspace 有效 FP32中间区从基址开始；额外 16 MiB未在 direct body中显式偏移或消费，不得按官方 `GetUserWorkspace` 假设重排。
- AIC/AIV flag ID、1:2比例与 schemMode 1是 correctness协议，不是可独立调整的性能参数。
- `scale=max(abs)/127` 对全零行没有单独分支；浮点除零/转换行为按固定 Kernel与 overflow控制执行，本卡不补造数值结果。
- launcher callable固定返回 0，不独立传播异步 launch错误；workspace没有显式 `recordStream`，生命周期依赖框架当前 stream allocator规则。
- 官方 950公开文档与此 Direct INT8内部路线边界不同；禁止用本卡代替 ACLNN产品/数据类型支持表。
- 固定源码中的 `TCubeTiling` 真实 `sizeof/alignof/offsetof` 属 CANN SDK ABI边界；本卡只闭合 direct重建字段。本次知识提取未执行编译、真机、数值或性能测试。

## 源码索引

### 链路索引

| 链路阶段 | 文件 | 关键符号 | 支撑内容 |
|---|---|---|---|
| 公开语义/平台边界 | `gmm/grouped_matmul_swiglu_quant_v2/README.md` | A8W8公式、产品支持与 dtype约束 | 语义及 Direct/ACLNN边界 |
| 官方入口声明 | `gmm/grouped_matmul_swiglu_quant_v2/op_api/grouped_matmul_swiglu_quant_v2.h` | `GroupedMatmulSwigluQuantV2` | TensorList、属性与 executor合同 |
| Kernel router | `gmm/grouped_matmul_swiglu_quant_v2/op_kernel/grouped_matmul_swiglu_quant_v2_apt.cpp` | `GmmSwigluAswtPertoken` branch | FP32 xScale命中 per-token RowMajor route |
| 当前官方实例 | `gmm/grouped_matmul_swiglu_quant_v2/op_kernel/arch35/grouped_matmul_swiglu_quant_v2_pertoken_quant.h` | `GmmSwigluAswtPertokenKernel` | 完整 template/type traits/参数顺序 |
| Host/Tiling | `gmm/grouped_matmul_swiglu_quant_v2/op_host/op_tiling/arch35/grouped_matmul_swiglu_quant_v2_basic_tiling.cpp` | `DoLibApiTiling`, `DoOpTilingPertoken`, `GetWorkspaceSize`, `PostTiling` | baseM clamp、UB、workspace、schedule mode |
| MIX orchestration | `gmm/common/cgmct/kernel/kernel_gmm_swiglu_pertoken_quant.h` | `KernelGmmSwiGluPertokenQuant` | 分组、两半 MMAD、flags、SyncAll |
| Cube specialization | `gmm/common/cgmct/block/block_mmad_builder.h` | `BlockMmadBuilder` | GM type/layout、VECIN C、Matmul策略 |
| Cube body | `gmm/common/cgmct/block/block_mmad_multi_block.h` | `BlockMmad` 的 `MatmulMultiBlock<>` specialization | Matmul初始化、GM输入、L0C到VECIN输出 |
| Scheduler | `gmm/common/cgmct/block/block_scheduler_gmm_aswt_with_tail_split.h` | `BlockSchedulerGmmAswtWithTailSplit` | ASWT与 tail split |
| Vector epilogue 1 | `gmm/common/cgmct/epilogue/block_epilogue_dequant_swiglu.h` | `BlockEpilogueDequantSwiglu` | scale搬运、FP32 dequant/SwiGLU、workspace写 |
| Vector epilogue 2 | `gmm/common/cgmct/epilogue/block_epilogue_pertoken_quant.h` | `BlockEpiloguePertokenQuant` | 行分核、UB双缓冲、reduce/quant/tail |
| 平台接线 | `gmm/grouped_matmul_swiglu_quant_v2/op_host/grouped_matmul_swiglu_quant_v2_def.cpp` | `AICore().AddConfig` 的 `ascend950` 注册 | 950 OpDef与 apt文件接线 |
| 构建接线 | `gmm/grouped_matmul_swiglu_quant_v2/CMakeLists.txt` | operator subdirectory wiring | 官方同算子构建边界 |

每个 Frontmatter URL 都是 ops-transformer 固定 40 位 Commit 的真实文件 blob；Direct conversion文件名仅用于说明转换闭包，不作为外部 source URL。

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | 7 pointers + 4 group packs + 3 metadata scalars | pack位宽、字段顺序、112-byte Device ABI、TCubeTiling重建一致 | `GMMSQLaunchParams`, `RebuildCubeTiling` |
| 调用顺序 | Host tiling→单 MIX launch→tile级 AIC/AIV→SyncAll→全局 quant | 不能让 quant早于所有 workspace写；不能丢失 overflow SPR restore | entry, `KernelGmmSwiGluPertokenQuant::operator()` |
| workspace/内存 | `[0,M*H*4)` FP32中间区；L1/L0/UB公式可复用 | workspace基址、dtype/layout、owner、tile不重叠、阶段复用顺序 | `GetWorkspaceSize`对应式、两个 epilogue Params |
| 同步 | flags 4/20 与 6/22、hard events、SyncAll | MIX 1:2、PIPE方向、等待/通知轮次、schemMode 1 | `Notify/Wait`, launcher schedule attr |
| 精度与尾块 | INT32累加→FP32 scales/SwiGLU→row max/127→INT8；ASWT/VF masks | 左右半顺序、scale广播、cast/round链、N偶数、last-group tail split | `VFDoDequant`, `VFDoSwiglu`, `ComputeScaleVF/YVF` |
| 失败边界 | Host校验失败即不 launch；空组skip | 不得增加隐式 fallback或把 pack截断静默当合法 | `calc_grouped_matmul_swiglu_quant_tiling`, `UpdateGroupParams` |

<!-- cannbot:related:start -->
## 相关

- [grouped_matmul_swiglu_quant 950 ACLNN 算子知识](../../../aclnn/transformer/gmm/grouped_matmul_swiglu_quant_950.md)（`same_topic`）：按累计 `group_list` 做 INT8 GroupedMatmul；INT32 结果乘 FP32 `x_scale`/`weight_scale`，沿 N 二分后做 `Swish(left) * right`，再逐 token 求 `max(abs)/127` 并量化为 INT8。；每组矩阵乘宽度 N，设备端按 FP32 per-token scale 或 64 元素 MX group 的 E8M0 scale 恢复为中间浮点，按源码的后半/前半实参计算 `S=SwiGLU(C［:,N/2:N］,C［:,0:N/2］,beta=1)`。。两端实现同一 950 GroupedMatmul 后接 SwiGLU 与动态量化的核心链，分别记录 Direct Invoke 固定 INT8 per-token 路线与 ACLNN V2 的 per-token、MX 和 WeightNZ 路线，联合阅读可完成前端与量化 route 选型。
<!-- cannbot:related:end -->
