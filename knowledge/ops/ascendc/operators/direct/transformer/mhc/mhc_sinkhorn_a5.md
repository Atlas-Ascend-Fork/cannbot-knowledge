---
type: Operator
title: "MhcSinkhorn A5 Direct Invoke 算子知识"
description: "说明 mhc_sinkhorn 在 A5 上的接口语义、Direct Launcher 参数生成、Route 选择、单 Kernel 启动图与逐节点实现。"
tags: [task.implementation, task.lookup, topic.data_movement, topic.memory, topic.precision, topic.programming_model]
status: stable
verified:
  - by: process:ops-knowledge-route-priority
    at: "2026-08-25T20:47:20Z"
  - by: process:ops-knowledge-direct53-ingest
    at: "2026-08-25T20:03:11Z"
sources:
  - resource: https://gitcode.com/cann/ops-transformer/blob/22bc210c35313f6d79d7fe7a546edc49387df8da/mhc/mhc_sinkhorn/README.md
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/22bc210c35313f6d79d7fe7a546edc49387df8da/mhc/mhc_sinkhorn/op_host/mhc_sinkhorn_def.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/22bc210c35313f6d79d7fe7a546edc49387df8da/mhc/mhc_sinkhorn/op_host/mhc_sinkhorn_tiling.h
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/22bc210c35313f6d79d7fe7a546edc49387df8da/mhc/mhc_sinkhorn/op_host/mhc_sinkhorn_tiling.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/22bc210c35313f6d79d7fe7a546edc49387df8da/mhc/mhc_sinkhorn_common/op_host/arch35/mhc_sinkhorn_base_tiling.h
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/22bc210c35313f6d79d7fe7a546edc49387df8da/mhc/mhc_sinkhorn_common/op_host/arch35/mhc_sinkhorn_base_tiling.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/22bc210c35313f6d79d7fe7a546edc49387df8da/mhc/mhc_sinkhorn/op_kernel/mhc_sinkhorn_apt.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/22bc210c35313f6d79d7fe7a546edc49387df8da/mhc/mhc_sinkhorn/op_kernel/arch35/mhc_sinkhorn_struct.h
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/22bc210c35313f6d79d7fe7a546edc49387df8da/mhc/mhc_sinkhorn/op_kernel/arch35/mhc_sinkhorn_tiling_key.h
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/22bc210c35313f6d79d7fe7a546edc49387df8da/mhc/mhc_sinkhorn/op_kernel/arch35/mhc_sinkhorn.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/22bc210c35313f6d79d7fe7a546edc49387df8da/mhc/mhc_sinkhorn/op_host/CMakeLists.txt
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/22bc210c35313f6d79d7fe7a546edc49387df8da/mhc/mhc_sinkhorn/op_host/config/ascend950/mhc_sinkhorn_binary.json
    role: implementation
created_at: "2026-08-25T19:32:39Z"
updated_at: "2026-08-25T20:47:20Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# MhcSinkhorn A5 Direct Invoke 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | `torch.ops.cann_bench.mhc_sinkhorn(comb, iter_step=20, eps=1e-6)`；NPU 实现符号 `mhc_sinkhorn_npu`，Direct Invoke。 |
| 计算语义 | 对每个方阵先做稳定 row-softmax 与带 `eps` 的列归一化，再交替做带 `eps` 的行/列归一化。 |
| 输入输出 | `comb/output: [B,n,n]`、ND、FP32；输出与输入同 shape/dtype。 |
| 执行类型 | P0 R-002、P1 R-003、P2 R-001 为单节点 `AIV_VECTOR`；P3 R-004 为单节点 `SIMT`。所有可达节点均无 Cube/AIC 或 MIX_CV。 |
| Kernel 路线 | P0 R-002 matrix-lane 转置 UB；P1 R-003 官方 arch35 body 直调适配；P2 R-001 寄存器分组；P3 R-004 通用 SIMT fallback。 |
| 核心资源 | GM 输入/输出；AIV Route 使用 TQue/TBuf/RegTensor；SIMT Route 使用 32 KiB dynamic UB；无外部 workspace。 |
| 来源闭包 | `direct_implementation_closed`：Direct schema/selector、迭代裁剪、launch 参数、四条 entry/body、UB/dynamic-UB、同步和构建接线均闭合；官方适配边界映射到固定 Commit。 |
| 验证状态 | 已完成源码闭包检查；本次知识提取未执行编译、真机、数值或性能测试。 |

## 接口与语义

### 计算语义

令输入第 `b` 个矩阵为 `X`，`K` 为该 Route 的实际迭代数。实现顺序是：

```text
s[r,c] = exp(X[r,c] - max_j X[r,j]) / sum_j exp(X[r,j] - max_j X[r,j])
v[r,c] = s[r,c] + eps
v[r,c] = v[r,c] / (sum_i v[i,c] + eps)
for k = 1 .. K-1:
    v[r,c] = v[r,c] / (sum_j v[r,j] + eps)
    v[r,c] = v[r,c] / (sum_i v[i,c] + eps)
y = v
```

R-003 的官方 body 在 `CalcSoftmax` 中先保存 `s`，同时累计 `s+eps`；`CalcColNorm<true>` 再把分子变为 `s+eps` 并给列和再加一次 `eps`，与上式一致。所有计算和累加均为 FP32，没有升/降精度 cast。

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| `comb` | `[B,n,n]` / ND | FP32 | 必须 rank=3 且末两维相等；Device 地址公式要求连续存储，wrapper 未主动 contiguous 化。 |
| `iter_step` | 标量 | int64 Host 参数 | 默认 20，wrapper 检查 `[1,40]`；部分宽度使用 `effective_iters` 裁剪。 |
| `eps` | 标量 | double Host、float Device | 默认 `1e-6`，wrapper 只检查 `eps >= 0`，launch 前窄化为 FP32。 |
| `output` | `[B,n,n]` / 与 `empty_like(comb)` 一致 | FP32 | 只返回最终矩阵；无 `norm_out`、`sum_out` 可见输出。 |

### 入口与版本

本卡只描述 CANN 9.1.0、Ascend 950（A5）的 Direct Invoke 交付入口，不补造成官方 ACLNN。官方固定源码公开支持 Ascend 950PR/950DT，并把 `MhcSinkhorn` 注册到 `ascend950`；A2/A3 明确不支持。Direct 实现保留了官方 `MhcSinkhornSimd<float,false>` body，并以按值 tiling 参数与直接 launch 替换框架 tiling 指针；映射记录确认官方 `arch35/mhc_sinkhorn.h` 的完整 namespace body 与交付中的对应区段逐字一致。其余 register、element 和 SIMT 路线是交付层 supplemental 实现，不属于官方固定 Commit。

## Host/Launcher 执行流程

### 参数校验与前处理

`mhc_sinkhorn_npu` 的顺序为：设备 guard → meta 校验与 `empty_like` 分配 → 读取 `B,n` 与 GM 指针/当前 NPU stream → 按 Host if/else 顺序计算 Route → 计算 `effective_iters` → 仅 R-003 生成官方 tiling → 在 `OpCommand::RunOpApi("MhcSinkhorn", lambda)` 内直接启动一个自定义 Kernel。任何 `TORCH_CHECK` 失败都发生在 launch 前；lambda 固定返回 0，未建立 Device launch 错误的细粒度传播协议。

### 参数、Workspace 与生命周期

- `effective_iters`：`n=2 -> min(iter_step,8)`，`n=3 -> min(iter_step,7)`，`n in {6,8} -> min(iter_step,5)`，`n in {12,16} -> min(iter_step,3)`；`n=4` 与通用 Route 保留请求值。
- R-003 的 `calc_mhc_sinkhorn_official_tiling(B,n,effective_iters,float(eps))` 从 A5 platform manager 读取 AIV core 数与 UB 字节，产生 `MhcSinkhornTilingData` 和 `block_dim`。
- R-001/R-002/R-004 的 launch 参数均由 wrapper/launcher 直接按值传入，不使用 tiling GM。
- `workspace_total=0`。R-003 为兼容官方 `Init` 参数，把 `output` 同时传为不可达的辅助输出，把 `input` 传为未解引用的 tiling 占位；`OUT_FLAG=false` 编译期裁掉辅助 GM 写出。
- 输入、输出和 stream 由调用者/框架持有到当前 stream 上 Kernel 完成；所有 Route 恰好一次 launch，无跨 Kernel 中间对象。

### 启动图与失败传播

```text
mhc_sinkhorn_npu
  -> validate + allocate output + select Route
     # Host selector order: R-001 -> R-002 -> R-003 -> R-004 fallback
  -> RunOpApi("MhcSinkhorn", lambda)
       -> exactly one of:
          R-001 register entry       [AIV_VECTOR]
          R-002 element entry        [AIV_VECTOR]
          R-003 official entry       [AIV_VECTOR]
          R-004 generic SIMT entry   [SIMT]
  -> output
```

| 节点 | Host launcher | entry/grid | 参数 | 输入/输出 | workspace/ordering/lifetime | 失败传播 |
|---|---|---|---|---|---|---|
| P0 R-002（Host 2） | `launch_mhc_sinkhorn_element_fast` | `mhc_sinkhorn_element_n*<<<blockDim,0,stream>>>` | `B,N,K,eps,groups,blockDim` | `comb -> output` | 单 stream；无 workspace；Queue 生命周期限单 Kernel | wrapper lambda 不检查异步 launch 状态 |
| P1 R-003（Host 3） | `launch_mhc_sinkhorn_official` | `mhc_sinkhorn_official_entry<<<usedCoreNum,0,stream>>>` | `comb,output,tilingData` | `comb -> output` | 同上；辅助指针仅作不可达占位 | 同上 |
| P2 R-001（Host 1） | `launch_mhc_sinkhorn_register_fast` | `mhc_sinkhorn_register_n2/n3<<<blockDim,0,stream>>>` | `B,N,K,eps,groupsPerCore` | `comb -> output` | 同上 | 同上 |
| P3 R-004（Host 4 fallback） | `launch_mhc_sinkhorn_generic` | `mhc_sinkhorn_generic_simt_entry<<<ceil(B/32),32768,stream>>>` | `B,n,iter_step,eps,stride` | `comb -> output` | 32 KiB dynamic UB，线程私有切片；无跨节点边 | 同上 |

## Route 与参数设计

### 分核与资源计算

- P0 R-002：`tile=64`（`N=2,3,6`）或 48（`N=4,12,16`），`groups=ceil(B/tile)`，`blockDim=min(groups,64)`；按 `baseGroups=floor(groups/blockDim)` 与前 `extraGroups=groups%blockDim` 个核多领一组的方式均分。
- P1 R-003：`tNormCore=ceil(B/C)`、`usedCoreNum=ceil(B/tNormCore)`。Host 分别按 forward/backward 内存估算式求 `tUbFactor`，取较小者；每核循环 `ceil(tNormCore/tUbFactor)`，最后一核和每核最后一轮分别由 tail 字段收口。
- P2 R-001：`groups=ceil(B/8)`，`blockDim=min(groups,64)`，`groupsPerCore=ceil(groups/blockDim)`；一个 register group 覆盖 8 个矩阵，当前入口只让该 Route 处理 `B<=1`。
- P3 R-004：`blocks=ceil(B/32)`，每 block 固定 32 个 SIMT thread，线程 `matrix_idx=blockIdx*32+threadIdx`，步长 `blocks*32`。

### Route 选择

| 重要性 | Route | Route 特征 | 适用域 | 实现前提 | Host 顺序、短路与 fallback |
|---:|---|---|---|---|---|
| P0 | R-002 element-fast | `MhcSinkhornElementFast<N>`；一条 vector lane 负责一个矩阵，`normBuffer_` 使用 `[row,col,matrix_lane]` | `((n==2 || n==3) && B>1) || n in {4,6,12,16}` | FP32 连续方阵、`B>0`、A5；48/64-matrix tile 的 UB 容量成立 | Host 第 2 项；仅在 R-001 false 后检查，false 后继续 R-003 |
| P1 | R-003 official-adapted | 官方 `MhcSinkhornSimd<float,false>`；data-block gather/reduce 与 depth-2 Queue | `n==8` | 官方 POD、A5 UB/AIV core 信息、`OUT_FLAG=false` 与 direct entry ABI 一致 | Host 第 3 项；仅在 R-001/R-002 false 后检查，false 后进入 R-004 |
| P2 | R-001 register-fast | `MhcSinkhornRegisterFast<2/3>`；一个 register group 覆盖 8 个矩阵 | `(n==2 || n==3) && B<=1` | FP32 连续方阵、`B>=1`、A5；mask/reduce/norm TBuf 容量成立 | Host 第 1 项；true 时短路其余 selector，false 后继续 R-002 |
| P3 | R-004 generic-SIMT | 32-thread VF；每线程独占一个 256-FP32 dynamic-UB slice | 前三条 Host 条件均为 false | FP32 连续方阵、`B>0`、`n*n<=256` | Host 第 4 项 final fallback；命中后无更后 Route |

```text
if ((n == 2 || n == 3) && B <= 1) R-001
else if ((n == 2 || n == 3) || n == 4 || n == 6 || n == 12 || n == 16) R-002
else if (n == 8) R-003
else R-004
```

### 模板/实现执行矩阵

| Route | key/selector | dtype/shape/platform 完整命中条件 | 执行拓扑与 Kernel 节点 | 实际模板/body | 内存与同步特征 | tail/fallback |
|---|---|---|---|---|---|---|
| P0 R-002 element-fast | `N=2,3,4,6,12,16` | FP32、A5；N=2/3 还需 `B>1` | 单 AIV Kernel | `MhcSinkhornElementFast<N>::Process/Compute` | `[row,col,matrix_lane]` norm TBuf；每元素跨矩阵向量化 | `UpdateMask(B_tail)`；无更宽模板 fallback |
| P1 R-003 official-adapted | direct `OUT_FLAG=false` | FP32、A5、`n=8` | 单 AIV Kernel | 官方 `MhcSinkhornSimd<float,false>` | depth-2 Queue/TBuf；MTE3→V event 与 MicroAPI local barrier | former/tail core、tail loop、mask；Host tiling 失败无备用 Route |
| P2 R-001 register-fast | `N=2/3` | FP32、`[B,N,N]`、A5，`B<=1` | 单 AIV Kernel | `MhcSinkhornRegisterFast<N>::Process/Compute` | depth-1 in/out Queue；mask/reduce/norm TBuf；VEC store→load barrier | lane mask 保护不足 8 个矩阵；`B=0` 是未保护失败边界 |
| P3 R-004 generic-SIMT | default | FP32、A5、方阵、前三条未命中 | 单 Vector entry 内 32-thread SIMT body | `mhc_sinkhorn_generic_simt_vf` | 32 KiB dynamic UB；每线程独占 256 FP32 | `matrix_idx<B` 步进；`n*n>256` 会越过线程切片 |

### 隐藏性能 Guard

| Guard | Host/Tiling 条件 | Device/资源原因 | 影响 Route | 不满足时去向 | 源码符号 |
|---|---|---|---|---|---|
| element tile | `tile=64` for `n=2,3,6`，否则 48 | norm TBuf 固定 `N*N*64*4`，in/out Queue 随 tile 增长 | R-002 | 固定模板，无运行时备用 |
| 64 AIV core cap | `blockDim=min(groups,64)` | launcher 显式限制并行核数 | R-002/R-001 | 每核顺序处理更多 group |
| official width | `n==8` | 官方固定源码只接受 `n in {4,6,8}`，但 direct selector 仅保留 n=8 | R-003 | R-004 仅在 `n!=8` 时可达 |
| official UB | forward/backward `occupy<=available`，否则按 one-piece 估算并向下 8 对齐 | depth-2 Queue 与 32B/256B 向量粒度 | R-003 | 重新减小 `tUbFactor`；极小 UB 的零因子未显式报错 |
| register tiny-batch | `B<=1 && n in {2,3}` | 8 矩阵/register 的布局在 tiny batch 上仍以 mask 收口 | R-001 | R-002 |
| SIMT thread slice | `n*n<=256`（Device 必要条件，Host 未校验） | 每线程只分配 256 FP32 | R-004 | 无 fallback；越界 |
| 非空 batch | `B>=1`（launch 必要条件，Host 未校验） | `groups=0` 会令 R-001/R-002 的 `blockDim=0`，并参与除法 | 全部 | 无安全 fallback |
| iteration cap | N 相关上限 8/7/5/3 | 交付 selector 减少归一化轮数，属于可见数值策略 | R-001/R-002/R-003 | n=4/通用 Route 用原始值 |

### POD/ABI

`MhcSinkhornTilingData` 在 Direct R-003 中按值传递。固定字段顺序给出 `sizeof=88`、`alignof=8`；`eps` 后有 4B padding。补充 Route 不使用 POD，而是传独立标量 Kernel 参数。

| 结构 | 字段 | 类型/位宽 | ABI 布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| P0 R-002 独立参数 | `total_groups` | int64/64 | 非 POD | tile-group | `ceil(B/tile)` | balanced group split | `B>0` |
| P0 R-002 独立参数 | `block_dim` | int64/64 | 非 POD | core | `min(total_groups,64)` | balanced group split | `>0` |
| P1 `MhcSinkhornTilingData` | `eps` | float/32 | offset 0 | 数值 | `config.tiling.eps=eps` | softmax/row/col denominator | double→float 已在 wrapper 窄化 |
| 同上 | `num_iters` | int64/64 | offset 8 | 次 | `=effective_iters` | `iterCnt_` 与 `Process` 循环 | Direct 请求范围 1..40，可能被 cap |
| 同上 | `out_flag` | int64/64 | offset 16 | bool-like | 固定 0 | 模板在 entry 已固化为 `false` | Device 不运行时读取分支 |
| 同上 | `n` | int64/64 | offset 24 | 元素/边长 | `=n` | `nAlign_`、`nnSize_` 与行列循环 | R-003 恒为 8 |
| 同上 | `usedCoreNum` | int64/64 | offset 32 | core | split result | 空闲核保护、尾核判断 | 同时作为 `block_dim` |
| 同上 | `tNormCoreLoop` | int64/64 | offset 40 | tile-loop/core | split result | normal core 的 `loop_` | 正整数 |
| 同上 | `tUbFactor` | int64/64 | offset 48 | matrix/tile | split result | Queue 容量与 loop stride | 资源上界关键字段 |
| 同上 | `tUbFactorTail` | int64/64 | offset 56 | matrix | `tNormCore-(loops-1)*factor` | normal core 尾轮 `handleNum` | `1..factor` |
| 同上 | `tTailCoreLoop` | int64/64 | offset 64 | tile-loop | tail split | 最后一核 `loop_` | 尾核 active |
| 同上 | `tUbTailTail` | int64/64 | offset 72 | matrix | tail core 余数 | 最后一核尾轮 | 尾核 active |
| 同上 | `tNormCore` | int64/64 | offset 80 | matrix/core | `ceil(B/C)` | 每核 GM base 与 telemetry stride | R-003 active |
| P2 R-001 独立参数 | `groups_per_core` | int64/64 | 非 POD | group/core | `ceil(ceil(B/8)/blockDim)` | `Process` 的 group 区间 | `blockDim>0` 才定义 |
| P3 R-004 独立参数 | `matrix_stride` | int64/64 | 非 POD | matrix | `ceil(B/32)*32` | SIMT grid-stride loop | `B>0` 时正数 |

### Route 源码闭包

| Route | Key/selector | Host/Tiling producer | POD/参数 | Kernel entry/router 节点 | Kernel body/直接依赖 | 构建接线 |
|---|---|---|---|---|---|---|
| P0 R-002 | element predicate | 交付层 `mhc_sinkhorn_npu` / `launch_mhc_sinkhorn_element_fast` | 独立 scalar 参数 | `mhc_sinkhorn_element_n*` | `MhcSinkhornElementFast<N>`（supplemental） | direct-launch 单算子 target |
| P1 R-003 | `n=8,OUT_FLAG=false` | `mhc_sinkhorn_tiling.cpp` + common base；direct helper 等价复现 | `MhcSinkhornTilingData` | 官方 `mhc_sinkhorn<TEMPLATE_MODE=0>` 适配为 direct entry | 官方 `MhcSinkhornSimd<float,false>` 完整 body | `op_host/CMakeLists.txt` + ascend950 binary config |
| P2 R-001 | `n=2/3,B<=1` | 交付层 `mhc_sinkhorn_npu` / `launch_mhc_sinkhorn_register_fast` | 独立 scalar 参数 | `mhc_sinkhorn_register_n2/n3` | `MhcSinkhornRegisterFast<N>`（supplemental） | direct-launch 单算子 target |
| P3 R-004 | default | 交付层 `launch_mhc_sinkhorn_generic` | 独立 scalar 参数 | `mhc_sinkhorn_generic_simt_entry` | `mhc_sinkhorn_generic_simt_vf`（supplemental） | direct-launch 单算子 target |

## Kernel 实现

### 公共执行流程

四条 Route 都是单 Kernel：从连续 GM 输入读取一个或一组矩阵，在 Kernel 内完成 stable softmax、首次列归一化与其余交替归一化，再一次性写回同布局 GM 输出。P0 R-002、P1 R-003、P2 R-001 使用 `KERNEL_TYPE_AIV_ONLY` 和 AscendC MicroAPI；P3 R-004 由 `__vector__` entry 调用 32-thread SIMT VF。没有 Kernel 间 workspace 边、atomic 或跨核归约。

### Route R-002（P0）：supplemental element-fast AIV

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct Host | 交付层 wrapper | `mhc_sinkhorn_npu` | `((n=2/3)&&B>1) || n in {4,6,12,16}`；Host 第 2 项 | R-001 false 后检查；true 时短路，false 时检查 R-003 |
| Launcher | 交付层 Kernel 单元 | `launch_mhc_sinkhorn_element_fast` | 逐 `n` if-chain | `mhc_sinkhorn_element_nN` |
| Device | 同上 | `RunMhcSinkhornElementFast<N>` | `N` 编译期常量 | `MhcSinkhornElementFast<N>::Process` |

#### Device 数据流

##### 函数级调用链

```text
launch_mhc_sinkhorn_element_fast
  -> mhc_sinkhorn_element_n2/n3/n4/n6/n12/n16
    -> RunMhcSinkhornElementFast<N>
      -> Process -> CopyIn -> Compute -> CopyOut
```

##### 源码等价伪码

```text
tile = 64 if N in {2,3,6} else 48
balanced-partition ceil(B/tile) groups among min(groups,64) cores
for each owned group:
  DMA packed matrices into inputQue
  gatherIndex[lane] = lane*N*N; validMask = first handleNum lanes
  for row, col: gather the same element across matrices
  stable row softmax and write norm[(row*N+col)*64 + lane]
  add eps; first column normalize
  repeat K-1 row/column normalizations in-place in transposed normBuffer
  scatter each [row,col,lane] back to packed outputLocal
  DMA valid bytes to GM
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM input/output | `matrixOffset*N²` | `handleNum*N²*4` B | FP32 packed | caller/Compute | CopyIn/caller | stream | 单段 DMA |
| in/out Queue | Queue-owned | 各 `tile*N²*4` B | FP32 packed | CopyIn/Compute | Compute/CopyOut | depth 1 | tail 用实际字节数 |
| `normBuffer_` | `(row*N+col)*64 + lane` | `N²*64*4` B | FP32 batch-last | softmax/normalization | normalization/scatter | 当前 group | 同址原地覆盖 |
| RegTensor | register scope | 固定仓不公开物理字节 | FP32/int32/mask | gather/reduce | arithmetic/scatter | 单 vector scope | 每 lane 对应一个矩阵 |

##### 分层内存布局

```mermaid
block-beta
  columns 3
  inQ["inputQue depth=1 · tile*N²*4B"]:1
  norm["normBuffer · N²*64*4B · batch-last"]:1
  outQ["outputQue depth=1 · tile*N²*4B"]:1
```

##### 字节账与复用顺序

```text
UB_total = 2*tile*N²*4 + N²*64*4
         = 768*N² B when tile=64
         = 640*N² B when tile=48
N=2/3/4/6/12/16 => 3,072/6,912/10,240/27,648/92,160/163,840 B
UB_total <= A5 编译目标的可用 UB（launcher 无运行时 UB guard）
dynamic_ub = N/A
workspace_total = 0
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| `normBuffer_[element,lane]` | softmax/row/col stage | 下一 stage | 当前 stage 的 divide 结果 | stage 间 `LocalMemBar` | `handleNum<=64` 且 validMask 正确 |
| in/out Queue | DMA/Compute | Compute/DMA | 下一 group | Queue 生命周期 | depth=1 串行 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Queue handoff | EnQue/DeQue | DMA/Compute | Compute/DMA | packed tile | 实际字节 tail |
| batch-last materialize | `LocalMemBar<VEC_STORE,VEC_LOAD>` | element stores | row/col loads | norm TBuf | FP32；`UpdateMask(handleNum)` |
| normalization | FP32 `Add/Div/Max/Exp` | current RegTensor | store to norm | active lanes | K 采用宽度 cap，N=4 无 cap |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host producer | 交付层 wrapper/Kernel 单元 | `mhc_sinkhorn_npu`、`launch_mhc_sinkhorn_element_fast` | Route、tile、grid、K |
| Kernel entry | 交付层 Kernel 单元 | `mhc_sinkhorn_element_n*` | 六个 Host 可达实例 |
| Device body | 交付层 Kernel 单元 | `MhcSinkhornElementFast<N>::Process/Compute` | batch-last gather/scatter 与融合迭代 |

### Route R-003（P1）：official-adapted n=8 AIV

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct Host | 交付层 wrapper | `mhc_sinkhorn_npu` | `n==8`，`K=min(iter_step,5)`；Host 第 3 项 | R-001/R-002 false 后检查；true 时短路，false 时进入 R-004 |
| Official Tiling | `mhc/mhc_sinkhorn/op_host/mhc_sinkhorn_tiling.cpp` | `CheckInputShape/GetTilingKey` | 官方允许 `n in {4,6,8}`；`out_flag=0 -> key 0` | `TEMPLATE_MODE=0` |
| Router | `mhc/mhc_sinkhorn/op_kernel/mhc_sinkhorn_apt.cpp` | `mhc_sinkhorn<0>` | `TEMPLATE_MODE==0` | `MhcSinkhornSimd<float,false>` |
| Direct entry | 交付适配层 | `mhc_sinkhorn_official_entry` | 按值 tiling、`OUT_FLAG=false` | 同一官方 body |

#### Device 数据流

##### 函数级调用链

```text
calc_mhc_sinkhorn_official_tiling -> launch_mhc_sinkhorn_official
  -> mhc_sinkhorn_official_entry
    -> MhcSinkhornSimd<float,false>::Init
    -> Process
      -> CopyIn -> CalcSoftmax -> CalcColNorm<true>
      -> (CalcRowNorm -> CalcColNorm<false>)*(K-1)
      -> ScatterOutFromNorm -> CopyOut
```

##### 源码等价伪码

```text
coreBase = core*tNormCore*64
loop/tail = normal fields; last core switches to tail-core fields
build n=8 full data-block mask
for loopIdx:
  handleNum = last loop ? tail : tUbFactor
  DMA handleNum*64 FP32 to inputQue
  vector groups of 8 matrices:
    gather rows -> reduce-max -> subtract -> exp -> reduce-sum -> divide
    save transposed norm; accumulate softmax+eps column sums
    first col divide: (softmax+eps)/(colSum+eps)
    for iter=1..K-1: row divide by sum+eps; col divide by sum+eps
  scatter transposed norm to packed outputQue
  DMA valid bytes to GM
```

#### 内存与数据搬运

##### 资源与搬运表

令 `F=tUbFactor`、`A=ceil_align(F*n²,8)`、`nAlign=ceil_align(n,8)=8`。

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM input/output | `core*tNormCore*n² + loopIdx*F*n²` | `handleNum*n²*4` B | FP32 packed | caller/CopyOut | CopyIn/caller | stream | tail 只搬有效字节 |
| `inputQue_` | Queue | `2*A*4` B | FP32 packed | CopyIn | CalcSoftmax | depth 2 | 32B 对齐 |
| `outputQue_` | Queue | `2*A*4` B | FP32 packed | Scatter | CopyOut | depth 2 | 32B 对齐 |
| `normOutQue_` | Queue | `2*F*n*nAlign*4` B | FP32 vectorized | softmax/norm | next norm/scatter | depth 2 | 原地归一化 |
| `sumColQue_` | Queue | `2*F*nAlign*4` B | FP32 | softmax/row | col norm | depth 2 | 轮间复用 |
| `sumRowQue_` | Queue | `2*8*4=64` B | FP32 | row norm | Process cleanup | depth 2 | `OUT_FLAG=false` 固定最小区 |
| mask/mid/sum TBuf | 独立 | `64+256+256` B | uint32/FP32 | Process/reduce | MicroAPI | Kernel | reduce store/load scratch |

##### 分层内存布局

```mermaid
block-beta
  columns 6
  inQ["inputQ depth=2 · 2*A*4B"]:1
  outQ["outputQ depth=2 · 2*A*4B"]:1
  norm["normQ depth=2 · 2*F*n*8*4B"]:1
  col["sumColQ depth=2 · 2*F*8*4B"]:1
  row["sumRowQ depth=2 · 64B"]:1
  fixed["mask+mid+sum · 576B"]:1
```

##### 字节账与复用顺序

```text
UB_total = 2*A*4 + 2*A*4 + 2*F*n*8*4 + 2*F*8*4 + 64 + 64 + 256 + 256
         = 16*A + 64*F*(n+1) + 640 bytes; n=8
Host forward_available = (UB_bytes - 64 - 3*256) / 2
Host 同时计算 forward/backward F，选择较小 tUbFactor
UB_total <= UB_bytes 是该 Host 选择与 A5 编译资源成立的必要条件
dynamic_ub = N/A
workspace_total = 0
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| `normOutQue_` | softmax/row/col | 下一阶段/scatter | 下一归一化阶段原地写回 | Queue + MTE3→V event + local barrier | `OUT_FLAG=false` 不发生辅助 GM 抽取 |
| `midBuffer_/sumBuffer_` | reduce store | broadcast reload | 下一 reduce | `LocalMemBar` | reload 后覆盖 |
| Queue slot | producer | DeQue consumer | `FreeTensor` 后 | depth-2 Queue protocol | Host F 满足 UB 预算 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| reduce | VEC load/store local barrier | ReduceMax/ReduceSum | broadcast reload | mid/sum TBuf | stable max-shift FP32 |
| potential MTE3→V | `SetFlag/WaitFlag<HardEvent::MTE3_V>` | 编译期可选辅助 GM store | 后续 Vector norm | norm/sum Queue | Direct 为 false，仍保留 event 序列 |
| vector tail | mask TBuf + `UpdateMask` | Host handleNum/n mask | all MicroAPI ops | inactive matrices/lanes | n=8 全 32-bit row mask；matrix tail 动态 |
| core/tile tail | last-core/last-loop fields | Host tiling | Process branch | GM extent | 只写 `handleNum*n²` |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `mhc/mhc_sinkhorn/op_host/mhc_sinkhorn_tiling.cpp`、common base tiling | `SplitByCoreNum/SetTilingData/BaseSplitCores` | core、F、tail、POD、blockDim |
| Kernel entry/router | `mhc/mhc_sinkhorn/op_kernel/mhc_sinkhorn_apt.cpp` | `mhc_sinkhorn<0>` | key 0 → `float,false` |
| Device body/helper | `mhc/mhc_sinkhorn/op_kernel/arch35/mhc_sinkhorn.h` | `MhcSinkhornSimd<float,false>` 全部方法 | Queue、MicroAPI、event、tail 与计算顺序 |

### Route R-001（P2）：supplemental register-fast AIV

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct Host | 交付层 wrapper | `mhc_sinkhorn_npu` | `(n==2 || n==3) && B<=1`；Host 第 1 项 | true 时短路到 register launcher；false 时检查 R-002 |
| Launcher | 交付层 Kernel 单元 | `launch_mhc_sinkhorn_register_fast` | `n==2` / `n==3` | entry `<2>` / `<3>` |
| Device | 同上 | `RunMhcSinkhornRegisterFast<N>` | `N` 编译期常量 | `MhcSinkhornRegisterFast<N>::Process` |

#### Device 数据流

##### 函数级调用链

```text
launch_mhc_sinkhorn_register_fast
  -> mhc_sinkhorn_register_n2/n3
    -> RunMhcSinkhornRegisterFast<N>
      -> Process -> CopyIn -> Compute -> CopyOut
```

##### 源码等价伪码

```text
group = core * groupsPerCore; each group owns up to 8 matrices
for matrixOffset in this core's range step 128:
  DMA contiguous handleNum*N*N FP32 GM -> inputQue
  for each 8-matrix register group:
    gather each row of each matrix; validMask clips B tail
    stable row softmax; save rows to normBuffer as [row, register-lane]
    add eps; accumulate and apply first column normalization
    repeat K-1 times: row sum+eps divide; column sum+eps divide
    scatter register lanes to packed outputLocal
  DMA valid packed bytes outputQue -> GM
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM input/output | `matrixOffset*N*N` | `handleNum*N*N*4` B | FP32 packed `[matrix,row,col]` | caller/Compute | CopyIn/caller | stream 生命周期 | 一次连续 DataCopyPad |
| `inputQue_` | Queue-owned | `128*N*N*4` B | FP32 packed | CopyIn | Compute | depth 1，Compute 后 Free | tail 只搬有效字节 |
| `outputQue_` | Queue-owned | `128*N*N*4` B | FP32 packed | Compute | CopyOut | depth 1，CopyOut 后 Free | 同上 |
| `maskBuffer_` | TBuf | 64 B | uint32 mask | Process | Compute | Kernel 全程 | N=2/3 row mask |
| `reduceBuffer_` | TBuf | `N*64*4` B | FP32 reduction scratch | Reduce | broadcast reload | Kernel 全程 | store→load barrier 后复用 |
| `normBuffer_` | TBuf | `128*N*8*4` B | FP32 `[group,row,lane]` | softmax/normalization | 后续 normalization/scatter | 当前 tile | 原地覆盖每轮结果 |

##### 分层内存布局

```mermaid
block-beta
  columns 5
  inQ["inputQue depth=1 · 128*N²*4B"]:1
  outQ["outputQue depth=1 · 128*N²*4B"]:1
  mask["mask · 64B"]:1
  reduce["reduce · N*64*4B"]:1
  norm["norm · 128*N*8*4B"]:1
```

##### 字节账与复用顺序

```text
UB_total = 2*(128*N²*4) + 64 + N*64*4 + 128*N*8*4
         = 1024*N² + 4352*N + 64 bytes
         = 12,864 B (N=2) or 22,336 B (N=3)
UB_total <= A5 编译目标的可用 UB（launcher 无运行时 UB guard）
dynamic_ub = N/A
workspace_total = 0
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| `normBuffer_` | softmax/当前归一化 | 下一行/列归一化与 scatter | 下一轮同元素写回 | `LocalMemBar<VEC_STORE,VEC_LOAD>` | 每轮全部 store 对后续 load 可见 |
| `reduceBuffer_` | Reduce result store | `DIST_E2B_B32` reload | 下一行 reduce | local memory barrier | reload 完成后才能覆盖 |
| in/out Queue | CopyIn/Compute | Compute/CopyOut | 下一 tile | `EnQue/DeQue/FreeTensor` | depth=1 严格串行 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| DMA→compute | Queue | CopyIn `EnQue` | Compute `DeQue` | input tile | 有效搬运长度为 `handleNum*N²*4` |
| reduce broadcast | `LocalMemBar` | reduce store | scalar broadcast reload | `reduceBuffer_` | FP32 max/sum/div |
| norm iteration | `LocalMemBar` | norm store | 下一 normalization load | `normBuffer_` | `validMask=rowMask & freshMask` 屏蔽不足 8 矩阵 |
| compute→DMA | Queue | output `EnQue` | CopyOut `DeQue` | output tile | 只写有效矩阵 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host producer | 交付层 wrapper/Kernel 单元 | `mhc_sinkhorn_npu`、`launch_mhc_sinkhorn_register_fast` | 选择、cap、blockDim/groupsPerCore |
| Kernel entry | 交付层 Kernel 单元 | `mhc_sinkhorn_register_n2/n3` | `N` 到 AIV body 的编译期映射 |
| Device body | 交付层 Kernel 单元 | `MhcSinkhornRegisterFast<N>::Process/Compute` | gather、reduce、norm TBuf 原地迭代、scatter |

### Route R-004（P3）：supplemental generic SIMT

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct Host | 交付层 wrapper | `mhc_sinkhorn_npu` | R-001/R-002/R-003 全部 false；Host 第 4 项 | final fallback，直接进入 generic launcher |
| Launcher | 交付层 Kernel 单元 | `launch_mhc_sinkhorn_generic` | `blocks=ceil(B/32)` | generic entry，32 KiB dynamic UB |
| SIMT entry | 同上 | `mhc_sinkhorn_generic_simt_entry` | 固定 `dim3(32)` | `mhc_sinkhorn_generic_simt_vf` |

#### Device 数据流

##### 函数级调用链

```text
launch_mhc_sinkhorn_generic
  -> mhc_sinkhorn_generic_simt_entry
    -> LocalMemAllocator<UB>::Alloc<float>(32*256)
    -> asc_vf_call<mhc_sinkhorn_generic_simt_vf>(dim3(32), ...)
```

##### 源码等价伪码

```text
thread = blockIdx*32 + threadIdx
values = dynamicUB + threadIdx*256
for matrix=thread; matrix<B; matrix+=blocks*32:
  scalar copy n² GM -> values
  stable row softmax; store softmax+eps
  first column divide by colSum+eps
  repeat requested_iter-1 row/column divide by sum+eps
  scalar copy n² values -> GM
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM input/output | `matrix_idx*n²` | `n²*4` B/thread/iteration | FP32 packed | caller/thread | thread/caller | stream | scalar loop，无 DMA Queue |
| dynamic UB | `threadIdx*256` floats | 256 FP32/thread，32 threads | FP32 packed matrix | thread load/normalization | same thread/store | 单 entry/block | 线程私有；要求 `n²<=256` |
| registers | thread local | 固定仓不可见 | FP32 scalars | scalar loops | scalar loops | 单线程 | 无共享/atomic |

##### 分层内存布局

```text
dynamic UB 32 KiB per block
  thread 0:  [0,256) FP32
  thread 1:  [256,512) FP32
  ...
  thread 31: [7936,8192) FP32
```

##### 字节账与复用顺序

```text
dynamic_ub = 32 threads * 256 FP32/thread * 4 B = 32,768 B
workspace_total = 0
AIV TQue/TBuf = N/A；实际替代路径为线程私有 dynamic UB
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| thread-private `values[0:n²]` | input load/每轮 divide | 后续行列循环/output store | 下一矩阵 | 单线程程序顺序 | `n²<=256`，线程间无别名 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| thread ownership | grid-stride index | launcher | SIMT body | one matrix | `matrix_idx<B` 收口 |
| normalization | 单线程程序顺序 | scalar store | next scalar load | thread slice | FP32，NaN row-max 显式传播 |
| cross-thread | N/A | 每线程独占矩阵 | N/A | 无共享数据 | 无 barrier/atomic 必要 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host producer | 交付层 wrapper/Kernel 单元 | `mhc_sinkhorn_npu`、`launch_mhc_sinkhorn_generic` | default Route、grid、stride、dynamic UB |
| Kernel entry | 交付层 Kernel 单元 | `mhc_sinkhorn_generic_simt_entry` | UB allocator 与 32-thread VF 调用 |
| Device body | 交付层 Kernel 单元 | `mhc_sinkhorn_generic_simt_vf` | thread→matrix、scalar stable softmax、完整请求迭代 |

## 算子特定优化

### Trick T-001：data-block gather 上的稳定 row-softmax

#### 触发与源码依据

- 适用 Route：R-003（R-001 沿用同类稳定归约思想）。
- 触发条件：官方 direct Route `n=8`，每个 vector loop 处理最多 `blockCnt` 个矩阵。
- Golden 来源：[`mhc_sinkhorn.h:212-234`](https://gitcode.com/cann/ops-transformer/blob/22bc210c35313f6d79d7fe7a546edc49387df8da/mhc/mhc_sinkhorn/op_kernel/arch35/mhc_sinkhorn.h)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
for (uint16_t nIdx = 0; nIdx < static_cast<uint16_t>(tilingData_.n); nIdx++) {
    auto inputOfset = inputAddr + (i * blockCnt * nnSize_) + nIdx * tilingData_.n;
    MicroAPI::DataCopyGather(inputReg, inputOfset, (MicroAPI::RegTensor<uint32_t> &)(rowIndexReg),
                             maskRegCalc);
    MicroAPI::ReduceMaxWithDataBlock(midReg, inputReg, maskRegCalc);
    MicroAPI::LocalMemBar<AscendC::MicroAPI::MemType::VEC_LOAD, AscendC::MicroAPI::MemType::VEC_STORE>();
    MicroAPI::DataCopy(midResAddr, midReg, maskReg);
    MicroAPI::LocalMemBar<AscendC::MicroAPI::MemType::VEC_STORE, AscendC::MicroAPI::MemType::VEC_LOAD>();
    MicroAPI::DataCopy<float, MicroAPI::LoadDist::DIST_E2B_B32>(midReg, midResAddr);
    MicroAPI::Sub(inputReg, inputReg, midReg, maskRegCalc);
    MicroAPI::Exp(inputReg, inputReg, maskRegCalc);
```

#### 机制与设计原因

`rowIndexReg` 把多个矩阵的相同行 gather 到一个寄存器，`maskRegCalc` 同时编码合法矩阵与 N=8 data-block lane。先做 `ReduceMaxWithDataBlock`、广播最大值再 `Exp`，避免直接指数的溢出风险；同一寄存器随后做 reduce-sum 和 divide，避免把每一行的 exp 中间量往返 GM。

#### 迁移边界

- 适用：多个小方阵、每行能映射到固定 data block 的 FP32 stable softmax。
- 前提：A5 MicroAPI、正确 gather index、mask、store→load barrier 和 per-row data-block layout。
- 失效：任意宽度无法构造官方 mask/layout 时，必须改用重新证明的 element/register Route 或 SIMT。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓未提供可验证反例；源码明确要求在 reduce 写 UB 后以 local barrier 保证广播读取可见。

### Trick T-002：forward/backward 双内存估算取更小 tile

#### 触发与源码依据

- 适用 Route：R-003。
- 触发条件：所有官方 Host tiling；`BaseSplitCores` 同时估算两套共享实现的 UB 上界。
- Golden 来源：[`mhc_sinkhorn_base_tiling.cpp:34-46`](https://gitcode.com/cann/ops-transformer/blob/22bc210c35313f6d79d7fe7a546edc49387df8da/mhc/mhc_sinkhorn_common/op_host/arch35/mhc_sinkhorn_base_tiling.cpp)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
MhcSinkhornSplitCoreInfo MhcSinkhornBaseTiling::BaseSplitCores(int64_t tSize, int64_t nSize, int64_t xDtypeSize,
                                                               int64_t outFlag)
{
    MhcSinkhornSplitCoreInfo forwardInfo;
    MhcSinkhornSplitCoreInfo backwardInfo;
    auto ascendcPlatform = platform_ascendc::PlatformAscendC(context_->GetPlatformInfo());
    int64_t totalCoreNum = ascendcPlatform.GetCoreNumAiv();
    uint64_t ubSize;
    ascendcPlatform.GetCoreMemSize(platform_ascendc::CoreMemType::UB, ubSize);

    BackwardSplitCore(ubSize, totalCoreNum, tSize, nSize, xDtypeSize, backwardInfo);
    ForwardSplitCore(ubSize, totalCoreNum, tSize, nSize, xDtypeSize, outFlag, forwardInfo);
    return forwardInfo.tUbFactor <= backwardInfo.tUbFactor ? forwardInfo : backwardInfo;
}
```

#### 机制与设计原因

Host 不仅按当前 forward Queue 估算 tile，还计算共享 backward 资源式并选 `tUbFactor` 较小者。这样生成的同一 POD 可满足更保守的 UB 约束；代价是可能减少每轮矩阵数。Direct helper 保留该选择，而不是硬编码 A5 tile。

#### 迁移边界

- 适用：forward/backward 共用 ABI 或需要统一安全 tile 的小矩阵算子。
- 前提：两套 `occupySize` 都以真实 depth、对齐和 dtype 字节数计账。
- 失效：buffer 拓扑变化时必须同步更新两套估算式；不能继承旧公式。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓未提供可验证反例；只用逻辑有效元素数、不乘 double buffer 会破坏该上界。

### Trick T-003：`OUT_FLAG` 模板裁剪辅助轨迹输出

#### 触发与源码依据

- 适用 Route：R-003。
- 触发条件：Direct selector 固定 `OUT_FLAG=false`，对应官方 `TEMPLATE_MODE=0`。
- Golden 来源：[`mhc_sinkhorn_apt.cpp:31-40`](https://gitcode.com/cann/ops-transformer/blob/22bc210c35313f6d79d7fe7a546edc49387df8da/mhc/mhc_sinkhorn/op_kernel/mhc_sinkhorn_apt.cpp)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
if constexpr (TEMPLATE_MODE == 0) {
    GET_TILING_DATA_WITH_STRUCT(MhcSinkhornTilingData, tilingData, tiling);
    MhcSinkhornSimd<float, false> op(pipe, tilingData);
    op.Init(h_res, y, norm_out, sum_out, tiling);
    op.Process();
} else if constexpr (TEMPLATE_MODE == 1) {
    GET_TILING_DATA_WITH_STRUCT(MhcSinkhornTilingData, tilingData, tiling);
    MhcSinkhornSimd<float, true> op(pipe, tilingData);
    op.Init(h_res, y, norm_out, sum_out, tiling);
    op.Process();
}
```

#### 机制与设计原因

`if constexpr` 把是否输出每轮 `norm_out/sum_out` 提升到模板期。Direct 只需要最终 `y`，固定选择 `float,false` 后，辅助 GM copy 分支被消除，`sumRowQue_` 也缩为一个 32B block 的 depth-2 Queue；这减少不需要的 GM 物化和 UB 容量。

#### 迁移边界

- 适用：调用方只消费最终迭代结果。
- 前提：Host key、模板实参、POD `out_flag` 和输出契约一致。
- 失效：需要中间轨迹时必须使用 `OUT_FLAG=true`，恢复辅助输出 shape、GM owner 与更大 `sumRowQue_`。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓未提供可验证反例；不能在 `false` body 上宣称 `norm_out/sum_out` 已被生产。

## 模板与实现对比

| 对比维度 | P0 R-002 element-fast | P1 R-003 official-adapted | P2 R-001 register-fast | P3 R-004 generic-SIMT | 设计选择依据 |
|---|---|---|---|---|---|
| 适用域 | n=2/3 且 B>1，或 n=4/6/12/16 | n=8 | n=2/3，B<=1 | 前三条 Host 条件均为 false | 重要性顺序与 Host 顺序相互独立 |
| Host 顺序/短路 | 第 2；R-001 false 后检查，false→R-003 | 第 3；前两条 false 后检查，false→R-004 | 第 1；true 时短路，false→R-002 | 第 4 final fallback | 必须保持 wrapper 的 if/else 语义 |
| 模板与 dtype | `<2/3/4/6/12/16>`, FP32 | `<float,false>` | `<2/3>`, FP32 | scalar FP32 | 全程无 cast |
| 循环与分核 | 48/64 matrix/group，均衡 group | Host F/core/tail | 8 matrix/group，最多 64 core | 32 thread/block，grid-stride | 按 batch/width 分工 |
| Queue/TBuf/寄存器/dynamic UB | in/out + norm | 5 Queue + 3 TBuf + RegTensor | in/out + mask/reduce/norm | 32 KiB dynamic UB | 各 Route 的局部布局不同 |
| 内存总占用与复用 | `640N²` 或 `768N²` | `16A+64F(n+1)+640` | `1024N²+4352N+64` | 32768 B/block | 由真实分配计账 |
| 搬运/Vector/SIMT API | DMA + element gather/scatter | DMA + data-block reduce | DMA + gather/reduce/scatter | scalar GM/UB loops | 小矩阵向量化方式不同 |
| 同步、精度与 tail | local barrier + lane mask | Queue/event/barrier + core/tile mask | local barrier + lane mask | thread-private，无 barrier | 均为 FP32 |
| fallback/失败边界 | B=0 未保护 | tiling 失败无备用 | B=0 未保护 | n²>256 越界 | wrapper 未补全这些 guard |

## 平台差异

| 项目 | A2 | A3 | A5 |
|---|---|---|---|
| 支持状态 | 官方 README 明确不支持 | 官方 README 明确不支持 | 官方支持 Ascend 950PR/950DT；本卡 Direct 目标为 950/A5 |
| Host/Launcher | N/A | N/A | 官方 OpDef 注册 `ascend950`；Direct 使用当前 A5 stream 与 platform manager |
| Kernel/资源 | N/A | N/A | `arch35` AIV MicroAPI body；supplemental AIV/SIMT；最多 64 AIV core 的两条补充 launcher |

## 限制与失败边界

- Direct wrapper 仅校验 rank=3、内维相等、FP32、`iter_step in [1,40]` 和 `eps>=0`；未校验 contiguous，但所有 Device 地址均按连续 `[B,n,n]` 解释。
- `B=0` 未被拒绝：R-001/R-002 可产生 `blockDim=0` 并进入除零表达式；调用者必须保证 `B>=1`。
- R-004 每线程只有 256 FP32，故必须满足 `n*n<=256`；wrapper 未验证这一必要条件。前三条未命中的 `n>16` 会造成线程 UB 越界。
- R-003 只复用官方 `OUT_FLAG=false` body，只有最终 `y`；辅助输出指针虽与 `output` 别名，但编译期分支不可达。
- 宽度相关 iteration cap 会改变请求的迭代次数；这是 Direct 交付的显式数值/调度策略，不是官方 Host/Tiling 语义。R-004 传原始 `iter_step`。
- `eps` 从 double 窄化为 float；NaN 会因 `eps>=0` 比较失败而被 Host 拒绝，`+inf` 可通过并在 FP32 计算中传播。
- lambda 固定返回 0，源码未提供同步 launch 错误回传；输出有效性仍依赖 stream 上 Kernel 成功完成。
- supplemental register/element/SIMT 路线没有对应官方 blob；本卡仅把它们作为 final candidate 的交付层实现陈述，不将其来源标为官方。
- 本次知识提取未执行编译、真机、数值或性能测试。

## 源码索引

### 链路索引

| 链路阶段 | 文件 | 关键符号 | 支撑内容 |
|---|---|---|---|
| 公开平台/语义 | `mhc/mhc_sinkhorn/README.md` | 产品支持表、公式 | A5 支持，A2/A3 不支持，算子语义 |
| 官方注册 | `mhc/mhc_sinkhorn/op_host/mhc_sinkhorn_def.cpp` | `ops::MhcSinkhorn` | FP32/ND、attrs、ascend950 注册 |
| Tiling 声明 | `mhc/mhc_sinkhorn/op_host/mhc_sinkhorn_tiling.h` | `MhcSinkhornTiling` | Host 状态与 POD producer |
| Tiling 实现 | `mhc/mhc_sinkhorn/op_host/mhc_sinkhorn_tiling.cpp` | `GetShapeAttrsInfo/CheckInputShape/SetTilingData/GetTilingKey/PostTiling` | 校验、key、POD、blockDim |
| 公共 Tiling 声明 | `mhc/mhc_sinkhorn_common/op_host/arch35/mhc_sinkhorn_base_tiling.h` | `MhcSinkhornBaseTiling` | split/occupancy 接口 |
| 公共 Tiling 实现 | `mhc/mhc_sinkhorn_common/op_host/arch35/mhc_sinkhorn_base_tiling.cpp` | `BaseSplitCores/ForwardSplitCore/BackwardSplitCore` | UB 公式、F/core/tail |
| POD | `mhc/mhc_sinkhorn/op_kernel/arch35/mhc_sinkhorn_struct.h` | `MhcSinkhornTilingData` | 字段顺序与类型 |
| 模板 key | `mhc/mhc_sinkhorn/op_kernel/arch35/mhc_sinkhorn_tiling_key.h` | `MhcSinkhorn` template args | AIV-only key 0/1 |
| 官方 entry | `mhc/mhc_sinkhorn/op_kernel/mhc_sinkhorn_apt.cpp` | `mhc_sinkhorn<TEMPLATE_MODE>` | key→`OUT_FLAG` body |
| 官方 body | `mhc/mhc_sinkhorn/op_kernel/arch35/mhc_sinkhorn.h` | `MhcSinkhornSimd` | 完整 Vector pipeline、UB、同步、tail |
| 构建接线 | `mhc/mhc_sinkhorn/op_host/CMakeLists.txt` | ascend950 compile branch | A5 编译选项与 common tiling 接线 |
| binary config | `mhc/mhc_sinkhorn/op_host/config/ascend950/mhc_sinkhorn_binary.json` | `MhcSinkhorn` op list | ascend950 binary 接口与 attrs |

每行只写一个文件，并确保该文件存在于 Frontmatter `sources`。

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | R-003 可复用 88B `MhcSinkhornTilingData` | 字段顺序、4B padding、int64 位宽、按值传递 | `MhcSinkhornTilingData`、`SetTilingData` |
| 调用顺序 | stable softmax→first col→(row→col)×(K-1) | 首次 `ADDS_EPS=true` 与后续 false 的顺序 | `MhcSinkhornSimd::Process` |
| workspace/内存 | 单 Kernel、workspace=0；真实 Queue/TBuf 公式 | depth、32B 对齐、F/tile 与线程 256-FP32 slice | `Init`、各 supplemental 构造函数/entry |
| 同步 | Queue + local barrier；官方保留 MTE3→V event | reduce store/reload 和 norm stage 之间不能去掉可见性 | `CalcSoftmax/CalcRowNorm/Process` |
| 精度与尾块 | FP32 max-shift、FP32 sum/div；mask/tail/core 收口 | iteration cap、eps 加入位置、有效搬运字节 | `CalcSoftmax/CalcColNorm/Process` |
| 失败边界 | Host 先校验再 launch；generic 是最终 fallback | 必须补 `B>=1`、contiguous、`n²<=256` 才能扩大安全域 | `mhc_sinkhorn_npu`、各 launcher |
