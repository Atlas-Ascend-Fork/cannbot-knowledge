---
type: Operator
title: "MoeFinalizeRouting A5 Direct Invoke 算子知识"
description: "说明 cann_bench::moe_finalize_routing、moe_finalize_routing_npu 与 launch_moe_finalize_routing 在 A5 上的接口语义、Direct tiling、四级全载/切 H Route、单 Kernel 启动图及交付特化。"
tags: [task.implementation, task.lookup, topic.data_movement, topic.memory, topic.precision, topic.programming_model]
status: stable
verified:
  - by: process:ops-knowledge-route-priority
    at: "2026-08-25T20:47:20Z"
  - by: process:ops-knowledge-direct53-ingest
    at: "2026-08-25T20:03:11Z"
sources:
  - resource: "https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/moe/moe_finalize_routing_v2/docs/aclnnMoeFinalizeRoutingV2.md"
    role: header
  - resource: "https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/moe/moe_finalize_routing_v2/op_graph/moe_finalize_routing_v2_proto.h"
    role: header
  - resource: "https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/moe/moe_finalize_routing_v2/op_host/moe_finalize_routing_v2_tiling_arch35.cpp"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/moe/moe_finalize_routing_v2/op_kernel/moe_finalize_routing_v2_apt.cpp"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/moe/moe_finalize_routing_v2/op_kernel/arch35/moe_finalize_routing_v2_base.h"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/moe/moe_finalize_routing_v2/op_kernel/arch35/moe_finalize_routing_v2_row_k_h_full_load.h"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/moe/moe_finalize_routing_v2/op_kernel/arch35/moe_finalize_routing_v2_k_h_full_load.h"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/moe/moe_finalize_routing_v2/op_kernel/arch35/moe_finalize_routing_v2_h_full_load.h"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/moe/moe_finalize_routing_v2/op_kernel/arch35/moe_finalize_routing_v2_h_partial_load.h"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/moe/moe_finalize_routing_v2/op_kernel/arch35/moe_finalize_routing_v2_tiling_struct.h"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/moe/moe_finalize_routing_v2/op_host/config/ascend950/moe_finalize_routing_v2_binary.json"
    role: implementation
created_at: "2026-08-25T19:37:34Z"
updated_at: "2026-08-25T20:47:20Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# MoeFinalizeRouting A5 Direct Invoke 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | `cann_bench::moe_finalize_routing` → `moe_finalize_routing_npu` → `calc_moe_finalize_routing_tiling` → `launch_moe_finalize_routing`；入口类型为 Direct Invoke。 |
| 计算语义 | `out[i,:]=skip1[i,:]+skip2[i,:]+Σ_k scale[i,k]·(expanded[rowIdx(i,k),:]+bias[expertIdx(i,k),:])`；缺失项按 0/1 处理，drop-pad 的 `rowIdx=-1` 整项跳过。 |
| 输入输出 | `expanded` 为 drop-less `[ROW·K,H]` 或 drop-pad `[E,C,H]`；索引 `int32[ROW·K]`；可选残差 `[ROW,H]`、bias `[E,H]`、scale/expert `[ROW,K]`；输出 `[ROW,H]`。支持 FP32/FP16/BF16，BF16 允许 FP32 scale。 |
| 执行类型 | 单个 `AIV_VECTOR` Kernel；四个 body 均使用 AscendC Queue/DataCopy 与 MicroAPI RegTensor，不含 Cube/AIC 或 MIX_CV。 |
| Kernel 路线 | P0 R-004 K-H 全载+bias table cache；P1 R-003 K-H 全载；P2 R-002 ROW-K-H 全载+整表索引；P3 R-001 ROW-K-H 全载；P4 R-005 H 全载；P5 R-006 H 分片。 |
| 核心资源 | GM 输入/输出；AIV UB 中的深度 1/2 `TQue`、少量 `TBuf`、FP32 RegTensor；无调用者 workspace、无跨 Kernel 中间张量。 |
| 来源闭包 | `direct_implementation_closed`：交付件内从 PyTorch schema、校验、Direct tiler、launcher、专用 entry、四个 arch35 body/helper 到 Direct CMake 已闭合；Frontmatter 仅列固定 Commit 官方相关源码，正文明确标注 Direct 适配。 |
| 验证状态 | 已完成源码闭包检查；本次知识提取未执行编译、真机、数值或性能测试。 |

## 接口与语义

### 计算语义

令 `r∈[0,ROW)`、`j∈[0,H)`、`q∈[0,K)`，其中 `K=scales.size(1)`，缺失 `scales` 时 `K=1`。索引布局由 `drop_pad_mode` 决定：

```text
idx_pos(r,q) = q*ROW+r, mode in {0,1}  # column
             = r*K+q,   mode in {2,3}  # row

y0(r,j) = (skip1 ? skip1[r,j] : 0) + (skip2 ? skip2[r,j] : 0)
y(r,j)  = y0(r,j) + Σ valid q (scales ? scales[r,q] : 1)
                         * (expanded[rowIdx[idx_pos(r,q)],j]
                            + (bias && expertIdx ? bias[expertIdx[r,q],j] : 0))
```

`mode∈{1,3}` 的 `rowIdx=-1` 使该 `q` 的 expanded、bias 和 scale 贡献整体跳过。Direct API 不暴露官方 V2 的 `x/alpha1/alpha2/v` 与 expert-range 属性；launcher 向四个 body 的这些地址传 `nullptr`，POD 的三个 expert range 均写 `[-1,-1)`。

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| `expanded_permuted_rows` | mode 0/2：`[ROW·K,H]`；mode 1/3：`[E,C,H]`；ND contiguous | FP32/FP16/BF16 | 必选；Direct 校验 rank、连续性、`H>0`。实际 `activeNum=expanded.size(0)`；drop-pad body 将前三维展平为行。 |
| `expanded_src_to_dst_row` | `[ROW·K]`，column 或 row 排列 | INT32 | 必选、1-D contiguous；长度必须整除 `K`。Direct 未逐值检查范围；drop-pad 允许 `-1`。 |
| `skip1` | `[ROW,H]` | 同 expanded | 可选；存在时作为初始累加项。Direct 检查 shape/dtype，但未显式检查 contiguous/device。 |
| `skip2` | `[ROW,H]` | 同 expanded | 可选；存在时 `skip1` 必须存在。 |
| `bias` | `[E,H]` | 同 expanded | 可选；存在时要求 `expertIdx`；drop-pad 检查 `bias.E==expanded.E`。drop-less 的 `E` 从 bias 首维取得。 |
| `scales` | `[ROW,K]` | 同 expanded；BF16 expanded 可配 FP32 | 可选；不存在时 `K=1` 且 scale=1。Direct 在读取 `size(1)` 前未先检查 rank，调用者必须给 2-D。 |
| `expert_for_source_row` | `[ROW,K]` | INT32 | 可选；存在时检查 shape/dtype；Direct 未逐值检查 `[0,E)`。 |
| `drop_pad_mode` | 标量 | `int64` | 默认 0，只允许 0..3；0/1 为 column，2/3 为 row；1/3 允许丢弃。 |
| `out` | `[ROW,H]` | 同 expanded | 新分配输出，非原地。 |

### 入口与版本

本卡受控入口是 Direct Invoke，不是 ACLNN。`TORCH_LIBRARY_FRAGMENT` 注册公开 schema，`PrivateUse1` 落到 `moe_finalize_routing_npu`；该函数取得当前 NPU stream，并通过 `OpCommand::RunOpApi("MoeFinalizeRouting", aclCall)` 包住一次直接 kernel launch。目标为 CANN 9.1.0、A5/Ascend 950，Direct 构建把 `ascend950` 映射到 Bisheng `dav-3510`。

官方固定 Commit 中 `aclnnMoeFinalizeRoutingV2.md` 明确列出 Ascend 950PR/950DT 支持，`ascend950/moe_finalize_routing_v2_binary.json` 注册 FP32/FP16/BF16 组合，arch35 Host 与 `_apt` entry 闭合四个 body。它们是交付转换的官方相关基线；PyTorch schema、`MoeFinalizeRoutingLaunchConfig`、无 workspace 的 Direct ABI、shape 专用 entry 和 bias/index cache 都是交付适配，不伪称为官方 ACLNN 行为。

## Host/Launcher 执行流程

### 参数校验与前处理

`ValidateAndGetShape` 按以下顺序执行：检查 mode 0..3；expanded dtype；row-index 为 1-D INT32；两个必选输入 contiguous；按 mode 检查 expanded rank 2/3；从 scale 的第二维或默认 1 得到 K，并以 `ROW=rowIdx.numel()/K`、`H=expanded.size(-1)`、`E/C` 推导逻辑维；检查 `ROW,H>0`；检查两个 skip；约束 `skip2=>skip1`；检查 bias/expert 依赖；检查 scale dtype；检查 expert shape。

Meta 与 NPU 实现共用上述函数。NPU 路径以 expanded device 建 guard，分配 `[ROW,H]` 输出，把 optional Tensor 转为 `nullptr` 或 GM 地址，构造 Direct tiling，再取得 current stream。源码未检查所有可选输入与 expanded 的 device/contiguous 一致性，也未检查索引值和 expert 值范围；这些是调用者边界。

### 参数、Workspace 与生命周期

`calc_moe_finalize_routing_tiling` 从 `PlatformAscendCManager` 取得 AIV core 数和 UB 字节；core 数非正时保守置 1。`hAligned=ceil_align(H*sizeof(T),32)/sizeof(T)`，`rowPerCore=ceil(ROW/coreNum)`，`blockDim=min(ceil(ROW/rowPerCore),coreNum)`，尾核行数为 `ROW-(blockDim-1)*rowPerCore`。

调用者 workspace 为 `0`。`launch_moe_finalize_routing` 将 `MoeFinalizeRoutingV2RegbaseTilingData` 按值传入 kernel；body 的 workspace、`x/a1/a2/v` 均为 `nullptr`。输入 Tensor 与输出 Tensor 由调用框架持有到 stream 工作完成；源码内没有临时 GM 或跨节点 owner。

### 启动图与失败传播

| 节点 | Host 启动 | entry/grid | POD/参数 | 输入→输出 | workspace/GM slice | ordering 与失败 |
|---|---|---|---|---|---|---|
| K1 唯一节点 | `launch_moe_finalize_routing` 中专用 entry 或 `LAUNCH_MOE_KERNEL_SET` | `moe_finalize_*<<<config.blockDim,nullptr,stream>>>` | `MoeFinalizeRoutingV2RegbaseTilingData` 按值；dtype/mode/Route 编译期模板化 | 七路 Direct 输入 → `out[ROW,H]` | workspace N/A；全部直接 GM | 单 stream 单节点，无跨节点 event；launcher 返回 `void`。 |

```text
moe_finalize_routing_npu
  -> calc_moe_finalize_routing_tiling
     -> ROWKH ? KH ? H-full ? H-partial
  -> launch_moe_finalize_routing
     -> exact-shape/static-mask/cache entry, if guarded
        OR generic dtype×scale-dtype×mode×Route entry
     -> RunOfficialMoeFinalizeRouting（T/S/mode/route 与 Direct 特化参数）
        -> one arch35 class::Init -> Process
        -> out[ROW,H]
```

校验失败由 `TORCH_CHECK` 在 launch 前抛出。Direct `aclCall` 在调用 `void` launcher 后固定返回 0，源码未同步检查单次 kernel launch 错误；这部分错误传播属于 runtime/framework 边界。

## Route 与参数设计

### 分核与资源计算

记 `A_b(x)=ceil_align(x,32)`（字节）、`t=sizeof(T)∈{2,4}`、`s=sizeof(S)∈{2,4}`、`Q_T(n,S)=ceil_align(n,32/t)*s`（body 按 T 的元素对齐数为 S queue 分配的实际字节）、`RF=rowFactor`、`HA=hAligned`。四级选择保持官方优先级：先判断完整 expanded/bias 是否能全载，再判断每个 row 的 K×H，再判断每个 K tile 的 H，最后切 H。

- ROW-K-H 全载：`expandedBytes=A_b((dropLess?ROW*K:E*C)*H*t)`，`biasBytes=hasBias?A_b(E*H*t):0`；加上双缓冲的 skip/scale/FP32-y 行 tile 后不超过 UB。
- K-H 全载：选择式预算为 `2*(K*HA*t + bias?K*HA*t + scale?A_b(K*s) + K==1 的 index 项 + skip 行 + A_b(H*4))`。Direct body 对所有 K 批量索引，`RowsHSizeForKHFullLoad` 的两个 `A_b(RF*K*4)` 覆盖其实际 int32 队列。
- H 全载：先在 `UB/2` 中二分最大 `kFactor`；Direct Host 实际预算 `kFactor*(1+hasBias)*HA*t + A_b(kFactor*t) + RowsHSize(RF,false)`，再回算 `kLoop/tailKFactor/RF`。其中 scale queue 的 Device 实分配是 `Q_T(kFactor,S)`，混合 BF16+FP32 时必须额外审计二者差额。
- H 分片：`actualInputNum=8-!x1-!x2-!bias-!x-3*!constExpert`；Direct 的 `x/constExpert` 恒缺失。`hFactor=floor((UB/2)/(t*(actualInputNum+1+(T!=FP32))))`，随后用 `hLoop=ceil(H/hFactor)` 重均分。

### Route 选择

**特征/重要性（知识组织顺序）**

| 重要性 | Route | 关键特征 | 复用价值 |
|---:|---|---|---|
| P0 | R-004 K-H+bias table cache | K×H 全载基础上常驻完整 bias table，覆盖 fixed-HK、static-mask 与混合 scale 特化 | 把重复 expert bias 行搬运改为核内 UB 复用，是最值得优先迁移的专用机制 |
| P1 | R-003 K-H 全载 | 主体 KH 路径，具备 static/fixed/all-input/generic 多级 entry 与批量索引 | 承接 cache 未命中并保留广泛 shape/dtype/mode 兼容，是专用路径的稳定底座 |
| P2 | R-002 ROW-K-H+整表索引 | 全载 expanded/bias，并把完整 routing/expert 索引表搬入 UB | 对受 guard 约束的 ROWKH 路径消除热循环 scalar GM 索引读取 |
| P3 | R-001 ROW-K-H 全载 | 最大数据域常驻 UB 的通用 route0 body | 提供 ROWKH 基线与 R-002 未命中时的语义兜底 |
| P4 | R-005 H 全载 | 不能常驻 K×H 时，以 K tile 保持完整 H 向量 | 保留向量整行计算，并承接前两级 Host selector 未命中 |
| P5 | R-006 H 分片 | 最小 H tile、逐片 gather 与累加 | 资源压力最高时的最终正确性兜底 |

**真实 Host/Launcher 选择顺序**

`H1/H2/H3/H4` 分别表示 Host tiler 的 ROWKH、KH、H-full、H-partial 层级；launcher 的 `L1` 为 KH static-mask 树，`L2` 为 ROWKH batch-id 树，`L3` 为 KH all-input 树，`L4` 为通用 dtype/mode/route 树。每个专用 entry 启动后立即返回，只有未命中才继续后继层。

| 重要性 | Route | Host 顺序 | Key/模板 | 精确选择条件与短路语义 | fallback |
|---:|---|---|---|---|---|
| P0 | R-004 K-H+bias table cache | H2：H1 ROWKH 为假后进入 KH；L1 的 mask29 cache 或 L3 all-input cache guard | route 1；`cacheBiasTable=true` | `IsKHFullLoad()` 成立，且固定 dtype/mode/H/K/optional/E 上界命中；entry 启动后立即 `return` | 同一 guard 的 E 上界未满足时走 R-003 transient-bias；其余未命中继续 KH 子树 |
| P1 | R-003 K-H 全载 | H2：H1 ROWKH 为假；L1 static-mask、L3 all-input non-cache、L4 generic | route 1；generic/all-input/fixed-HK/static-mask | `IsKHFullLoad()` 成立；launcher 按 static mask、all-input、generic 逐级短路 | KH Host 判定失败才进入 H3；KH 子树专用 entry 未命中由 R-003 generic 收口 |
| P2 | R-002 ROW-K-H+整表索引 | H1：最先判断 ROWKH；L2 的两个 batch-id guard | route 0；`batchRoutingIndices=true` | `IsRowKHFullLoad()` 成立、mode0、K=4，并命中对应 dtype/H/optional pattern；启动后立即 `return` | guard 未命中保留 route0，走 R-001 |
| P3 | R-001 ROW-K-H 全载 | H1：最先判断 ROWKH；L4 route0 generic | route 0；`RowKHFullLoad<T,S,mode>` | `IsRowKHFullLoad()` 成立且 R-002 未短路 | Host 的 ROWKH 判定失败才进入 H2 KH |
| P4 | R-005 H 全载 | H3：H1 ROWKH、H2 KH 均为假 | route 2；`HFullLoad<T,S,mode>` | `IsHFullLoad()` 成立，generic launcher 按 dtype/mode 选择 route2 entry | 判定失败进入 H4 R-006 |
| P5 | R-006 H 分片 | H4：前三层 Host 判定均为假 | route 3；`HPartialLoad<T,S,mode>` | 最终 fallback，generic launcher 按 dtype/mode 选择 route3 entry | 无下一 Route；非法输入应由 Host 拒绝 |

```text
rowKH = IsRowKHFullLoad()
kh    = !rowKH && IsKHFullLoad()
hfull = !rowKH && !kh && IsHFullLoad()

if rowKH: R-002 guarded shapes, else R-001
elif kh:  R-004 cache guards, else R-003 static/fixed/generic
elif hfull: R-005
else:       R-006
```

### 模板/实现执行矩阵

| 重要性 | Route | key/selector | dtype/shape/platform 完整命中条件 | 执行拓扑与 Kernel 节点 | 实际模板/body | 内存与同步特征 | tail/fallback |
|---:|---|---|---|---|---|---|---|
| P0 | R-004 | `route=1,cache=true` | 固定 cache guard | 单 AIV | `MoeFinalizeRoutingV2KHFullLoad<T,S,mode>`，`cacheBiasTable=true` | E×HA bias depth1 常驻，移除 transient bias queue；其余同 KH | odd H 每 expert 独立 DMA 到 HA stride；E 超限回 R-003 |
| P1 | R-003 | `route=1,cache=false` | KH UB 式成立；含固定 H/K、mask、all-input 与 generic entry | 单 AIV | `MoeFinalizeRoutingV2KHFullLoad<T,S,mode>`，`cacheBiasTable=false` | row/K index、gather/bias/skip/scale/y 全为 depth2；K≤4 可 16 rows batch | `validK` 压缩 drop-pad；固定 guard 失败仍 generic |
| P2 | R-002 | `route=0,batchRoutingIndices=true` | mode0 K4 固定 shape/optional pattern | 单 AIV | `MoeFinalizeRoutingV2RowKHFullLoad<T,S,mode>`，固定 H/K 与 static mask | R-001 加两个完整 `ROW*K` int32 depth1 queue | 同 R-001；guard 失败回 R-001 |
| P3 | R-001 | `route=0` | A5；ROWKH UB 式成立；除 R-002 guard | 单 AIV | `MoeFinalizeRoutingV2RowKHFullLoad<T,S,mode>` 基线实例 | expanded/bias depth1 全载；行 tile depth2 | 尾核+尾 row tile；索引无效跳过 |
| P4 | R-005 | `route=2` | H-full UB 式成立 | 单 AIV | `MoeFinalizeRoutingV2HFullLoad<T,S,mode>` | K tile 的 expanded/bias + row tile skip/y；均 depth2 | K 尾 tile、row 尾 tile、无效 index |
| P5 | R-006 | `route=3` | 兜底 | 单 AIV | `MoeFinalizeRoutingV2HPartialLoad<T,S,mode>` | H tile 的 expanded/bias/skip/y depth2；scale scalar GM | H tail、row tail、无效 index |

### 隐藏性能 Guard

| Guard | Host/Tiling 条件 | Device/资源原因 | 影响 Route | 不满足时去向 | 源码符号 |
|---|---|---|---|---|---|
| bias cache E 上界 | launcher 的七个 `E<=8/16/32` guard | 必须保证 `A_b(E*HA*t)` 与其余 queue 总和落入 A5 UB | R-004 | R-003 transient bias | `launch_moe_finalize_routing` |
| odd H cache stride | `H!=HA` | compact `E*H` 会使 expert>0 本地起点失去 32B 对齐 | R-004 | 每 expert 单独拷入 `expert*HA` | `KHFullLoad::Process` |
| K≤4 批量 16 row | `k<=4 && RF>=16` | expanded/bias queue 容量固定为 `16*K*HA`，分 batch 搬运与计算 | R-003 | 逐 row gather | `KHFullLoad::ProcessYWithInputK4` |
| optional static mask | 固定 mask 11/23/28/29 或五可选全有 | 编译期删除 pointer-presence 与计算分支 | R-002/R-003/R-004 | generic entry | `RunOfficialMoeFinalizeRouting` 实例 |
| drop-less 无 sentinel | mode 0/2 | Direct 公共契约保证索引非负有效，专用 KH 删除 `-1` 判断和 scale compact | R-003/R-004 | mode1/3 保留 `validK` 压缩 | `IsValidExpandedRowIdx` |
| index UB batching | Direct KH 对所有 K；ROWKH 仅在专用 guard | 避免 H/K 热循环的 scalar GM 索引读 | R-002/R-003/R-004 | ROWKH 普通路径 scalar GM | `ProcessWithId`、`LoadRoutingIndices` |
| 32B 行对齐 | `HA=A_b(H*t)/t` | gather/bias tile 使用 HA stride，DMA 有效长度仍为 H | R-003/R-004 | 无 fallback，tiler统一生成 | `OfficialArch35Tiler::Run` |
| Host Route 顺序 | ROWKH→KH→H→partial | Host 先取最大可全载域并短路，知识重要性顺序不改变该 selector | 全部 | 下一层 Host Route | `OfficialArch35Tiler::Run` |
| dtype/scale dtype | FP32→S=FP32；FP16→S=FP16；BF16→S=BF16/FP32 | MicroAPI load/cast/broadcast 模板必须与 GM 类型一致 | 全部 | Host dtype 检查失败 | `ToDtypeCode`、launcher dtype tree |
| mixed-scale 对齐账 | T=BF16、S=FP32 时比较 Host 的 `A_b(n*s)`（H-full局部甚至为 `A_b(n*t)`）与 body 的 `Q_T(n,S)` | Queue 用 `RoundUp<T>(n)*sizeof(S)`，可比 Host 项多 32B/slot | R-001/R-003/R-005 | 固定交付无独立 fallback；复用时按实际 Queue 重验 UB | `RowsHSize*`、`HFullLoad::Init`、`KHFullLoad::InitQueBuffers` |

### POD/ABI

官方 POD 由 28 个连续 `int64_t` 组成。在 LP64 ABI 下推导 `sizeof=224, alignof=8`；每个字段 offset 按 8 字节递增。固定源码没有 `static_assert(sizeof/offsetof)`，Direct 复用应补静态断言。`MoeFinalizeRoutingLaunchConfig` 是 Host-only 包装：POD 后接 `blockDim:int64@224`、`route:int32@232`、`inputDtype:int32@236`、`scaleDtype:int32@240`、`dropPadMode:int32@244`，推导 `sizeof=248,alignof=8`；Device 只收到前 224 字节 POD。

| 结构 | 字段 | 类型/位宽 | ABI 布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| `MoeFinalizeRoutingV2RegbaseTilingData` | `row` | int64/64 | off 0 | row | `ROW` | 分核、column index stride | `>0` |
| 同上 | `e` | int64/64 | off 8 | expert | drop-pad expanded dim0；否则 bias dim0/0 | full-load、bias cache | 无 bias 的 drop-less 可为0 |
| 同上 | `c` | int64/64 | off 16 | row/expert | drop-pad expanded dim1，否则0 | ROWKH expanded extent | drop-less inactive |
| 同上 | `h` | int64/64 | off 24 | element | expanded last dim | 所有地址/vector长度 | `>0` |
| 同上 | `hAligned` | int64/64 | off 32 | element | `A_b(H*t)/t` | KH UB stride | `>=H` |
| 同上 | `k` | int64/64 | off 40 | expert/token | scales dim1或1 | index/scale/K loop | `>0` |
| 同上 | `rowOfFormerBlock` | int64/64 | off 48 | row/core | `ceil(ROW/coreNum)` | block GM base | 正数 |
| 同上 | `rowOfTailBlock` | int64/64 | off 56 | row | 尾核公式 | 尾核 loop | 正数 |
| 同上 | `rowLoopOfFormerBlock` | int64/64 | off 64 | loop | `ceil(rowFormer/RF)` | outer loop | 正数 |
| 同上 | `rowLoopOfTailBlock` | int64/64 | off 72 | loop | `ceil(rowTail/RF)` | 尾核 outer loop | 正数 |
| 同上 | `rowFactor` | int64/64 | off 80 | row/tile | UB 搜索后重均分；cache entry可固定 | Queue容量、row tile | `>=1` |
| 同上 | `constExpertRangeFactor` | int64/64 | off 88 | expert/tile | `min(-1,RF)` 的 Direct 结果 | Direct body不读 | Direct inactive |
| 同上 | `tailRowFactorOfFormerBlock` | int64/64 | off 96 | row | former尾 tile公式 | `rowInnerLoop` | `1..RF` |
| 同上 | `tailRowFactorOfTailBlock` | int64/64 | off 104 | row | tail-core尾 tile公式 | `rowInnerLoop` | `1..RF` |
| 同上 | `hLoop` | int64/64 | off 112 | loop | full=1；partial=`ceil(H/hFactor)` | R-006 H loop | 正数 |
| 同上 | `hFactor` | int64/64 | off 120 | element/tile | full=H；partial UB公式 | H tile/Queue | 正数 |
| 同上 | `tailHFactor` | int64/64 | off 128 | element | `H-(hLoop-1)*hFactor` | R-006 tail | 正数 |
| 同上 | `kLoop` | int64/64 | off 136 | loop | KH/ROWKH=K；H-full=`ceil(K/kFactor)` | R-005 K loop | 正数 |
| 同上 | `kFactor` | int64/64 | off 144 | K/tile | KH/ROWKH=1；H-full UB二分 | expanded/bias Queue | 正数 |
| 同上 | `tailKFactor` | int64/64 | off 152 | K | `K-(kLoop-1)*kFactor` | R-005 tail | 正数 |
| 同上 | `activeNum` | int64/64 | off 160 | expanded row | `expanded.size(0)` | drop-less范围保护 | drop-pad不读 |
| 同上 | `zeroExpertStart` | int64/64 | off 168 | expert id | -1 | expert-range branch | Direct inactive |
| 同上 | `zeroExpertEnd` | int64/64 | off 176 | expert id | -1 | 同上 | Direct inactive |
| 同上 | `copyExpertStart` | int64/64 | off 184 | expert id | -1 | copy-expert branch | Direct inactive |
| 同上 | `copyExpertEnd` | int64/64 | off 192 | expert id | -1 | 同上 | Direct inactive |
| 同上 | `constantExpertStart` | int64/64 | off 200 | expert id | -1 | constant-expert branch | Direct inactive |
| 同上 | `constantExpertEnd` | int64/64 | off 208 | expert id | -1 | 同上 | Direct inactive |
| 同上 | `constExpertRangeNum` | int64/64 | off 216 | expert count | -1 | Direct body不读 | Direct inactive |

### Route 源码闭包

| 重要性 | Route | Key/selector | Host/Tiling producer | POD/参数 | Kernel entry/router 节点 | Kernel body/直接依赖 | 构建接线 |
|---:|---|---|---|---|---|---|---|
| P0 | R-004 | route1+cache | Direct `IsKHFullLoad/DoOpTilingKHFullLoad` + launcher E guard | POD；部分 entry 重写 RF | cache entry | Direct 扩展 `KHFullLoad<cacheBiasTable=true>` + base | Direct `register_direct_launch_op`；官方 ascend950 binary 作平台映射 |
| P1 | R-003 | route1 | Direct `IsKHFullLoad/DoOpTilingKHFullLoad` | POD+可选 fixed H/K/RF | generic/all/fixed/mask entry | Direct 扩展 `KHFullLoad<cache=false>` + base | 同上 |
| P2 | R-002 | route0+batch ids | Direct `OfficialArch35Tiler::IsRowKHFullLoad/DoOpTilingRowKHFullLoad` + launcher shape guard | POD+固定 H/K/mask | `*_rowkh_batch_ids` entry | Direct 扩展 `RowKHFullLoad<batchRoutingIndices=true>` | 同上 |
| P3 | R-001 | route0 | Direct `OfficialArch35Tiler::IsRowKHFullLoad/DoOpTilingRowKHFullLoad` | 官方 arch35 POD | generic `moe_finalize_*_rowkh` | `RowKHFullLoad` + base helper | 同上 |
| P4 | R-005 | route2 | Direct `IsHFullLoad/DoOpTilingHFullLoad` | POD | generic `*_h` | 官方 byte-identical `HFullLoad` + base | 同上 |
| P5 | R-006 | route3 | Direct `DoOpTilingSplitH` | POD | generic `*_partial` | 官方 byte-identical `HPartialLoad` + base | 同上 |

## Kernel 实现

### 公共执行流程

每个 block 处理连续 row 域；末 block 使用 `rowOfTailBlock`。body 先把 `skip1/skip2` 升到 FP32 yLocal，随后按 k 顺序 gather expanded row、可选 bias 与 scale，并以 FP32 RegTensor 执行 `(expanded+bias)*scale+y`。FP16/BF16 输入经 `DIST_UNPACK_B16 + Cast<float>` 升精度；每个 row 的 K 累加保持原次序；最终以 `NO_SAT + CAST_RINT` trait 或 AscendC `Cast` 的 `CAST_RINT` 模式降回 T。MicroAPI 通过 `UpdateMask<float>` 屏蔽 H 尾 lane，Queue 的 `EnQue/DeQue/FreeTensor` 管理 MTE→V→MTE 生命周期。

### Route R-004：K-H 全载与 bias table cache

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Tiler | Direct adapter | route1 | KH基础Route成立 | launcher cache guard |
| Launcher | Direct adapter | dtype/mode/H/K/E/optional完整谓词 | 七类固定 cache entry | cache body |
| Body | Direct KH extension | `cacheBiasTable=true` | 编译期移除 transient bias | persistent bias table |

#### Device 数据流

##### 函数级调用链

```text
KHFullLoad::Process
  -> DMA whole bias table once (compact if H==HA, per-row padded otherwise)
  -> per row tile: ProcessWithId/skip/scales
  -> ProcessYWithCachedBias
     -> gather only expanded rows
     -> direct VF with biasTableLocal[expert*HA]
  -> cast/copy; free table at kernel end
```

##### 源码等价伪码

```text
for expert: DMA bias[expert,0:H] -> biasTable[expert*HA]
for each row tile:
  load IDs/skip/scale as R-003
  for row:
    gather valid expanded rows only
    for q in valid order:
      e = expertIdxLocal[row,q]
      y += scale[row,q] * (expandedLocal[q*HA] + biasTable[e*HA])
cast/copy output
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| bias table | `expert*HA` | `A_b(E*HA*t)` | T padded rows | initial DMA | all row/K | depth1 kernel lifetime | H!=HA逐 expert DMA |
| expanded queue | validK*HA | 同 R-003 Xcap | T | gather | VF | row | depth2 |
| transient bias | N/A | 0 | N/A | N/A | N/A | 未分配 | 被 persistent table 替代 |
| ids/skip/scale/y | 同 R-003 | 同 R-003 | 同上 | 同上 | 同上 | row tile | 同上 |

##### 分层内存布局

```mermaid
block-beta
  columns 4
  table["biasTable · depth=1 · A_b(E·HA·t)"]:1
  ids["IDs · depth=2"]:1
  x["expanded · depth=2 · 2·Xcap"]:1
  rest["skip/scale/y · depth=2"]:1
```

##### 字节账与复用顺序

```text
UB_R004 = UB_R003 - 2*transientBiasXcap + A_b(E*HA*t)
          （RF可由固定 cache entry整体重算）
UB_R004 <= platform UB 由 launcher 的 shape/E guard 与固定RF共同保证
workspace_total=0; dynamic_ub=N/A
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| biasTable | initial MTE | all VF | 不覆盖 | MTE2→S event后，kernel末Free | `expert<E`且E guard成立 |
| expanded queue | gather | 当前 row/K | next row | Queue Free | 不与 table alias |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| table→scalar/V | `HardEvent::MTE2_S` + Queue | initial DMA | expert address/VF | bias table | odd H用HA stride |
| per-K VF | direct specialized helper | expanded/table/scale | y store | yLocal | 与 R-003 相同K顺序、FP32 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | Direct adapter | cache guard + FixedRowFactor | E上界、RF重算 |
| Kernel entry/router | Direct adapter | `*_cache_bias` | cache模板实例 |
| Device body/helper | Direct KH extension、official base | `ProcessYWithCachedBias`、`VFProcessExpandXBiasScaleOptimized` | 整表常驻且直接寻址 |

### Route R-003：K-H 全载

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct tiler | Direct kernel adapter | `IsKHFullLoad` | ROWKH失败且 KH UB式成立 | route1 |
| Launcher | Direct adapter | shape/mask/all-input/generic tree | R-004 cache guard优先，否则 non-cache entry | KH body |
| Body | Direct KH extension | `KHFullLoad` 且 `cacheBiasTable=false` | K1、K≤4/RF≥16、普通三分支 | 对应 inner pipeline |

#### Device 数据流

##### 函数级调用链

```text
KHFullLoad::Process
  -> ProcessInputWithX (skip/scales row tile)
  -> ProcessWithId (rowIdx/expertIdx row tile into UB)
  -> y=skip1+skip2
  -> K==1 ? ProcessYWithInputK1
     : K<=4 && RF>=16 ? LoadBatchAsync/ComputeBatch
     : ProcessYWithInput
  -> ProcessExpandedXBiasAndScale
  -> ProcessExpandXBiasScaleOptimized -> cast -> CopyOut
```

##### 源码等价伪码

```text
for block rowTile:
  DMA skip/scales; DMA rowIdx and expertIdx tile
  yFP32 = skip1+skip2
  for row batch (RF rows, optionally chunks of 16):
    validK=0
    for q:
      idx = rowIdxLocal; if dropPad && idx==-1: continue
      DMA expanded[idx,0:H] -> expandedLocal[validK*HA]
      DMA bias[e,0:H] -> biasLocal[validK*HA]
      if dropPad: compact scale[q] to scale[validK]
      validK++
    vector loop q=0..validK-1: y += scale*(expanded+bias)
  cast/copy output
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| rowIdx queue | column:`q*ceil_align(RF,8)+r`；row:`r*K+q` | depth2 ×（column:`K*A_b(RF*4)`；row:`A_b(RF*K*4)`） | INT32 | tile DMA | scalar gather | row tile | 每 K 段/整块 32B |
| expertIdx queue | `r*K+q` | depth2 × `A_b(RF*K*4)` | INT32 | tile DMA | bias gather | row tile | 32B |
| expanded queue | validK*HA | depth2 × `Xcap` | T | gather DMA | VF | row/batch | `Xcap=RF*HA*t` for K1；`16*K*HA*t` for K≤4 batch；否则 `K*HA*t` |
| bias queue | 同 expanded | depth2 × `Xcap` | T | gather DMA | VF | row/batch | cache=false |
| skip/scale/y | row tile | skip:`A_b(RF*H*t)` each；scale:`Q_T(RF*K,S)`；y:`A_b(RF*H*4)`，均 depth2 | T/S/FP32 | DMA/Vector | Vector/CopyOut | row tile | scale queue 以 T 元素粒度对齐 |

##### 分层内存布局

```mermaid
block-beta
  columns 4
  ids["rowIdx+expertIdx · depth=2 · 4·A_b(RF·K·4)"]:1
  xb["expanded+bias · depth=2 · 4·Xcap"]:1
  skips["skip1+skip2 · depth=2 · 2·ΣA_b(RF·H·t)"]:1
  sy["scale+y · depth=2 · 2·(A_b(RF·K·s)+A_b(RF·H·4))"]:1
```

##### 字节账与复用顺序

```text
UB_R003 = 2*(rowIdxBytes + hasBias*expertIdxBytes
             + Xcap + hasBias*Xcap
             + hasX1*A_b(RF*H*t) + hasX2*A_b(RF*H*t)
             + hasScale*Q_T(RF*K,S) + A_b(RF*H*4))
UB_R003 <= platform UB
workspace_total=0; dynamic_ub=N/A
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| index queues | ProcessWithId | row/K gather | next row tile | FreeTensor after y | consumer已结束 |
| expanded/bias queues | LoadBatchAsync/gather | ComputeBatch/VF | next row/batch | EnQue→DeQue→Free | `validK<=K`、Xcap成立 |
| yLocal | skip init/K accumulation | next K load/CopyOut | next row tile | LocalMemBar + yQue | K顺序不变 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| id/scale scalar→V | `HardEvent::S_V` | scalar compact/read | MicroAPI | scale LocalTensor | drop-pad validK压缩 |
| gather→V | Queue | MTE | VF | expanded/bias | HA分配，H有效 |
| K accumulation | LocalMemBar | VEC_STORE | VEC_LOAD | yLocal | FP32、K原顺序 |
| cast/out | CAST_RINT + Queue | VF | MTE | output | row/H tail |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | official tiling；Direct adapter | `RowsHSizeForKHFullLoad/DoOpTilingKHFullLoad` | RF与UB上界 |
| Kernel entry/router | Direct adapter | generic/all/fixed/mask KH entry | compile-time optional/mode/H/K |
| Device body/helper | official KH baseline、Direct KH extension、base | `ProcessWithId`、三种 `ProcessYWithInput`、`VFProcessExpandXBiasScaleOptimized` | index batching、gather、FP32融合 |

### Route R-002：ROW-K-H 全载与整表索引

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Tiler | Direct kernel adapter | route0 | ROWKH UB成立 | launcher guard |
| Launcher | Direct kernel adapter | `launch_moe_finalize_routing` | mode0,K4 且 F32/H64/all-input，或 F16/H32/mask29 | 两个 batch-id entry |
| Body | Direct rowkh extension | `batchRoutingIndices=true` | 编译期 true | `LoadRoutingIndices` |

#### Device 数据流

##### 函数级调用链

```text
R-001 chain
  + LoadRoutingIndices
      -> DMA rowIdx[ROW*K] once
      -> DMA expertIdx[ROW*K] once when present
  -> K loop reads LocalTensor<int32_t>, not scalar GM
```

##### 源码等价伪码

```text
load whole expanded and bias as R-001
rowIdxLocal = DMA(ROW*K); expertIdxLocal = DMA(ROW*K)
for every row/K: idx,e = local[index_offset]; vector accumulate as R-001
free both index tables only after all row tiles
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| R-001 buffers | 同 R-001 | 同 R-001 | 同 R-001 | 同上 | 同上 | 同上 | 同上 |
| rowIdxLocal | logical index | `A_b(ROW*K*4)` | INT32 | one DMA | all K loops | depth1 kernel lifetime | 32B |
| expertIdxLocal | `r*K+q` | `A_b(ROW*K*4)` | INT32 | one DMA | bias lookup | depth1 kernel lifetime | 32B |

##### 分层内存布局

```mermaid
block-beta
  columns 4
  base["R-001 UB"]:2
  rid["rowIdx · depth=1 · A_b(ROW·K·4)"]:1
  eid["expertIdx · depth=1 · A_b(ROW·K·4)"]:1
```

##### 字节账与复用顺序

```text
UB_R002 = UB_R001 + A_b(ROW*K*4) + hasExpertIdx*A_b(ROW*K*4)
workspace_total = 0; dynamic_ub = N/A
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| 两个 index table | `LoadRoutingIndices` | 所有 row/K | 不覆盖 | depth1持有至最终 Free | 仅专用小 shape guard可达 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| index DMA | EnQue/DeQue | MTE | scalar GetValue | 两整表 | 与 R-001 相同有效域 |
| Vector | 同 R-001 | 同 R-001 | 同 R-001 | yLocal | 精度顺序不变 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | Direct adapter | route0 + fixed guard | 限定两个专用形状 |
| Kernel entry/router | Direct adapter | `*_rowkh_batch_ids` | 固定H/K/mask |
| Device body/helper | Direct rowkh extension | `LoadRoutingIndices` | 一次搬入索引并跨循环复用 |

### Route R-001：ROW-K-H 全载

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct tiler | `op_kernel/moe_finalize_routing_kernel.cpp` | `IsRowKHFullLoad` | full expanded + optional full bias + double-buffer row tile `<=UB` | route0 |
| Launcher | 同上 | `launch_moe_finalize_routing` | route0 且不命中 R-002 | generic entry |
| Router/body | official arch35 rowkh header | `RowKHFullLoad<T,S,mode>` | dtype/mode 编译期 | `Init→Process` |

#### Device 数据流

##### 函数级调用链

```text
entry -> RunOfficialMoeFinalizeRouting -> RowKHFullLoad::Init/Process
  -> LoadExpandedX (whole table)
  -> LoadBiasAndAllocOptionalTensors (whole bias)
  -> for row tile: ProcessInputWithX
     -> ProcessX1AndX2
     -> for row, K: scalar row/expert index -> ProcessExpandXBiasScale
     -> CastYOutput -> CopyOut
```

##### 源码等价伪码

```text
expandedLocal = DMA(all valid expanded rows)
if bias: biasLocal = DMA(E*H)
for block rowTile:
  DMA skip1/skip2/scales
  yFP32 = fp32(skip1) + fp32(skip2)
  for r in tile:
    for q in 0..K-1:
      idx = rowIdx[column_or_row_offset]
      if idx==-1 or (dropLess && idx>=activeNum): continue
      e = expertIdx[r,q] if present
      yFP32[r] += scale[r,q] * (fp32(expandedLocal[idx]) + fp32(biasLocal[e]))
  cast_rint(yFP32) -> output GM
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| expanded GM/UB | idx*H | `dropLess?ROW*K*H:E*C*H` | T/flat rows | caller/DMA | K loop | depth1，整个 kernel | 32B 总 extent |
| bias GM/UB | expert*H | `E*H` | T `[E,H]` | caller/DMA | K loop | depth1，整个 kernel | 32B 总 extent |
| skip1/skip2 | blockRow*H | 每路 `RF*H` | T | DMA | init y | depth2，每 row tile | 32B queue |
| scales | blockRow*K | depth2 × `Q_T(RF*K,S)` | S | DMA | K loop | 每 row tile | T 与 S 相同时等于 `A_b(RF*K*s)` |
| yQue | blockRow*H | `RF*H` | FP32→T | Vector | DMA out | depth2，每 row tile | H tail mask |

##### 分层内存布局

```mermaid
block-beta
  columns 4
  exp["expanded · depth=1 · A_b(expCount·H·t)"]:1
  bias["bias · depth=1 · hasBias·A_b(E·H·t)"]:1
  skips["skip1+skip2 · depth=2 each · 2·ΣA_b(RF·H·t)"]:1
  sy["scales+y · depth=2 · 2·(A_b(RF·K·s)+A_b(RF·H·4))"]:1
```

##### 字节账与复用顺序

```text
UB_R001 = A_b(expCount*H*t) + hasBias*A_b(E*H*t)
         + 2*(hasX1*A_b(RF*H*t) + hasX2*A_b(RF*H*t)
              + hasScale*Q_T(RF*K,S) + A_b(RF*H*4))
UB_R001 <= platform UB
dynamic_ub = N/A
workspace_total = 0
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| expanded/bias depth1 | initial DMA | 所有 row/K | kernel结束 | persistent DeQue 后最终 Free | Route UB 式成立 |
| skip/scale/y slot | tile DMA/Vector | init/K/CopyOut | 下一 row tile | Queue FreeTensor | 当前 CopyOut 完成 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| GM→UB | TQue EnQue/DeQue | DataCopyPad | Vector | persistent/table与行 tile | 有效长度 H，分配按32B |
| K 累加 | `LocalMemBar<VEC_STORE,VEC_LOAD>` | 前一个 K store | 下一个 K load | 原地 yLocal | FP32；逐 K 顺序 |
| UB→GM | yQue | Vector/cast | CopyOut | 输出 tile | FP16/BF16 CAST_RINT；尾 row/H |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | official arch35 tiling；Direct kernel adapter | `IsRowKHFullLoad/DoOpTilingRowKHFullLoad` | 优先级、UB公式、rowFactor |
| Kernel entry/router | official `_apt.cpp`；Direct adapter | route0实例 | T/S/mode到body |
| Device body/helper | official rowkh/base headers | `LoadExpandedX/ProcessInnerLoopBody/ProcessExpandXBiasScale` | 全表常驻、索引、FP32累加 |

### Route R-005：H 全载

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Tiler | official arch35 tiling；Direct adapter | `IsHFullLoad/DoOpTilingHFullLoad` | 前两级失败且单H/K tile预算成立 | route2 |
| Launcher | Direct adapter | generic set route2 | dtype/mode entry |
| Body | official H-full | `HFullLoad<T,S,mode>` | `kLoop/kFactor` | H full body |

#### Device 数据流

##### 函数级调用链

```text
HFullLoad::Process -> row tile skip init
  -> for row -> for K tile
     -> scalar row/expert index
     -> gather curKFactor full-H expanded/bias and scales
     -> ProcessExpandXBiasScaleOptimized(validK,H)
  -> CastYOutput -> CopyOut
```

##### 源码等价伪码

```text
for row tile, row, kTile:
  compact valid q into expandedLocal[validK*HA], biasLocal[validK*HA] and scalesLocal
  VF loops validK and full H, accumulating into yFP32[row]
cast/copy row tile
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| expanded/bias | validK*HA | 每路 depth2 × `kFactor*HA*t` | T | gather | VF | K tile | HA stride |
| scales | K tile | depth2 × `Q_T(kFactor,S)` | S | DMA | VF broadcast | K tile | T 与 S 相同时等于 `A_b(kFactor*s)` |
| skip/y | row tile | skip each depth2 × `A_b(RF*H*t)`；y depth2 × `A_b(RF*H*4)` | T/FP32 | DMA/VF | init/out | row tile | tail mask |

##### 分层内存布局

```mermaid
block-beta
  columns 4
  xb["expanded+bias · depth=2 · 2·kFactor·HA·t each"]:2
  skip["skip queues · depth=2"]:1
  sy["scale+y · depth=2"]:1
```

##### 字节账与复用顺序

```text
UB_R005 = 2*(kFactor*HA*t + hasBias*kFactor*HA*t + hasScale*Q_T(kFactor,S)
             + hasX1*A_b(RF*H*t) + hasX2*A_b(RF*H*t) + A_b(RF*H*4))
workspace_total=0; dynamic_ub=N/A
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| expanded/bias K tile | CopyExpanedXAndBiasScales | VF | next K tile | Queue FreeTensor | validK≤curKFactor |
| yLocal | skip init/K tiles | CopyOut | next row tile | LocalMemBar/Queue | K tile顺序固定 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| scalar scale→V | S_V event | scale compact | VF | scale local | tailKFactor |
| K累加 | LocalMemBar | y store | next K | yLocal | FP32 |
| output | CAST_RINT | FP32 y | DMA | output | tail row/H |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | official arch35 tiling | `DoOpTilingHFullLoad` | kFactor二分与RF |
| Kernel entry/router | official `_apt.cpp`、Direct generic set | H-full实例 | dtype/mode映射 |
| Device body/helper | official H-full/base | `ProcessKLoopBody`、`CopyInnerLoopBody`、`VFProcessExpandXBiasScaleOptimized` | K tile、FP32累加 |

### Route R-006：H 分片

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Tiler | official arch35 tiling；Direct adapter | `DoOpTilingSplitH` | 三个 full-load guard均失败 | route3 |
| Launcher | Direct adapter | generic set else | partial entry |
| Body | official H-partial | `HPartialLoad<T,S,mode>` | hLoop/hFactor | H切片body |

#### Device 数据流

##### 函数级调用链

```text
HPartialLoad::Process
  -> for row -> for H tile
     -> Copy skip tile -> yFP32
     -> for K: scalar index/scale -> gather expanded/bias H tile
        -> ProcessExpandXBiasScale
     -> cast/copy H tile
```

##### 源码等价伪码

```text
for row assigned to block:
  for hTile in 0..hLoop-1:
    yFP32 = skip1/skip2 slice
    for q:
      idx=scalar rowIdx; if invalid continue
      DMA expanded[idx,h0:h0+len] and bias[e,h0:h0+len]
      yFP32 += scale*(expanded+bias)
    cast/copy only len tail-aware elements
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| expanded/bias H tile | `idx*H+hIdx*hFactor` | 每路 depth2 × `A_b(hFactor*t)` | T | DMA | VF | K iteration | 32B |
| skip H tile | `globalRow*H+h0` | 每路 depth2 × `A_b(hFactor*t)` | T | DMA | init y | H tile | 32B |
| y H tile | output同offset | depth2 × `A_b(hFactor*4)` | FP32→T | VF | DMA | H tile | tailHFactor |
| scale | scalar GM | 1 element | S | GetValue | VF | K iteration | 无 UB queue |

##### 分层内存布局

```mermaid
block-beta
  columns 4
  exp["expanded · depth=2 · 2·A_b(hFactor·t)"]:1
  bias["bias · depth=2 · 2·A_b(hFactor·t)"]:1
  skip["skip1+skip2 · depth=2 each"]:1
  y["y · depth=2 · 2·A_b(hFactor·4)"]:1
```

##### 字节账与复用顺序

```text
UB_R006 = 2*((1+hasBias+hasX1+hasX2)*A_b(hFactor*t) + A_b(hFactor*4))
UB_R006 <= platform UB
workspace_total=0; dynamic_ub=N/A
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| expanded/bias queue | current K DMA | current K VF | next K | FreeTensor | current VF完成 |
| skip/y queue | H tile init/VF | K loop/CopyOut | next H tile | EnQue/DeQue/Free | tail长度正确 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| GM→UB | Queue | DMA | VF | H tile | `tailHFactor` |
| K累加 | unaligned MicroAPI + LocalMemBar | previous y | next K | yLocal | FP32、mask hFactor |
| output | CAST_RINT/CopyOut | VF | GM | output slice | exact tail length |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | official arch35 tiling | `DoOpTilingSplitH` | hFactor/hLoop/tail |
| Kernel entry/router | official `_apt.cpp`、Direct generic set | partial实例 | dtype/mode映射 |
| Device body/helper | official H-partial/base | `Process/ProcessInnerLoopBody/ProcessExpandXBiasScale` | H切片、scalar scale、tail |

## 算子特定优化

### Trick T-001：按 UB 可承载范围逐级全载

#### 触发与源码依据

- 适用 Route：R-001 至 R-006。
- 触发条件：按 ROW-K-H、K-H、H 的完整 UB 公式依次判断；第一次成立即停止，三者都失败才切 H。
- Golden 来源：[`op_host/moe_finalize_routing_v2_tiling_arch35.cpp:968-985`](https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/moe/moe_finalize_routing_v2/op_host/moe_finalize_routing_v2_tiling_arch35.cpp#L968-L985)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
rowKHFullLoad_ = IsRowKHFullLoad();
if (rowKHFullLoad_) {
    return true;
}

kHFullLoad_ = IsKHFullLoad();
if (kHFullLoad_) {
    return true;
}
hFullLoad_ = IsHFullLoad();

return true;
```

#### 机制与设计原因

Route 优先级把最大的可复用域优先留在 UB：R-001 整张 expanded/bias 只搬一次，R-003 每 row gather K×H，R-005 进一步切 K，R-006 才切 H。Direct tiler保留相同判断顺序与字节公式，只把框架 Host 上下文改成纯值 ABI。

#### 迁移边界

- 适用：存在多个“全载粒度”的 gather+逐项融合算子。
- 前提：每一级必须用实际 Queue depth、dtype bytes、alignment 和可选项计算 UB。
- 失效：上一级总量超过 UB 时必须下降一级，不能仅缩小 `blockDim`。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓未提供可验证反例；从选择式可证明，跳过 UB guard 强行全载会使 `InitBuffer` 总量失去上界。

### Trick T-002：在 FP32 yLocal 中按 K 原序融合

#### 触发与源码依据

- 适用 Route：全部 Route。
- 触发条件：`T` 为 FP16/BF16 时 load 先升 FP32；每个有效 K 依次执行 bias、scale、累加，最终一次降精度。
- Golden 来源：[`op_kernel/arch35/moe_finalize_routing_v2_base.h:274-311`](https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/moe/moe_finalize_routing_v2/op_kernel/arch35/moe_finalize_routing_v2_base.h#L274-L311)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
for (uint16_t k = 0; k < validK; k++) {
    srcLocalAddr = yOriginAddr;
    yLocalAddr = yOriginAddr;
    DataCopyUnAlignPre<float>(uSrc, srcLocalAddr);
    if constexpr (hasScale) {
        LoadInputDataWithBrc<S>(scaleReg, scalesLocalAddr, pregMain, k);
    }
    for (uint16_t i = 0; i < loopCount; i++) {
        LoadInputDataUnalign<float>(src, srcLocalAddr, uSrc, pregMain, VL_FP32);
        LoadInputData<T>(expandedX, expandedXLocalAddr, pregMain, k * processLenAlign + i * VL_FP32);
        if constexpr (hasBias) {
            LoadInputData<T>(bias, biasLocalAddr, pregMain, k * processLenAlign + i * VL_FP32);
            Add(expandedX, expandedX, bias, pregMain);
        }
        if constexpr (hasScale) {
            Mul(expandedX, expandedX, scaleReg, pregMain);
        }
        Add(y, src, expandedX, pregMain);
```

#### 机制与设计原因

`yLocal` 物理存储为 FP32，低精度 expanded/bias/scale 在寄存器加载时升精度；K 维不做树形重排，因此 Direct 的 fixed-H/K、index batching 和 bias cache 都保持相同累加顺序。`LocalMemBar<VEC_STORE,VEC_LOAD>` 防止下一 K 过早读取原地 y。

#### 迁移边界

- 适用：低精度输入、较小 K 的逐行 gather-and-accumulate。
- 前提：UB 必须按 FP32 y 的 4 字节计账；降精度只发生在输出阶段。
- 失效：改变 K 顺序或每 K 都降回 T 会改变数值语义与误差。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓未提供可验证反例；源码明确要求 y 在全部 K 完成前保持 FP32。

### Trick T-003：Direct 批量索引与整表 bias cache

#### 触发与源码依据

- 适用 Route：R-002、R-003、R-004。
- 触发条件：R-003 对每个 row tile 批量搬入 row/expert index；R-002 对两个固定小 workload 搬入整表；R-004 仅在固定 H/K/E guard 内缓存完整 bias。
- Golden 来源：[`op_kernel/arch35/moe_finalize_routing_v2_k_h_full_load.h:430-454`](https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/moe/moe_finalize_routing_v2/op_kernel/arch35/moe_finalize_routing_v2_k_h_full_load.h#L430-L454)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
for (int64_t kIdx = 0; kIdx < tilingData->k; kIdx += 1) {
    SetExpandedRowIdxOffset(rowOuterIdx, rowInnerIdx, kIdx);
    int64_t expandedRowIdxGmValue = expandedRowIdxGm.GetValue(expandedRowIdxOffset);
    if (!IsValidExpandedRowIdx(expandedRowIdxGmValue)) {
        continue;
    }
    int64_t expertIdx = GetExpertIdxValue(rowInnerIdx, rowOuterIdx, kIdx);
    if (!LoadExpandedXForK(rowOuterIdx, rowInnerIdx, expertIdx, expandedRowIdxGmValue, offset)) {
        continue;
    }

    if (hasBiasAndExpertIdx) {
        int64_t biasGmOffset = expertIdxGm.GetValue(expertIdxOffset) * tilingData->h;
        CopyIn(biasGm[biasGmOffset], biasLocal[offset + validK * tilingData->hAligned], 1, tilingData->h);
    }
```

#### 机制与设计原因

上段官方基线在 K 热循环中 scalar 读取索引并逐 expert 搬 bias。Direct 适配把索引先批量搬到 UB；cache Route 再把 `E×HA` bias table 搬一次并由 VF 直接选行，从而消除重复 GM 索引读和重复 bias 行 DMA。odd H 必须以 `expert*HA` padding，否则第 2 行起点不满足 32B 对齐。该机制不改变 expanded gather、K 次序或 FP32 累加。

#### 迁移边界

- 适用：索引被 H 维反复复用，且索引 tile/完整 bias table 可证明放入 UB。
- 前提：cache guard 同时约束 `E,H,dtype,RF`；expert 值必须在 `[0,E)`；column index 的每 K 段需单独对齐。
- 失效：E 超过 guard 时回 R-003 transient bias；ROWKH 非专用 shape 回 R-001 scalar index。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定交付演进给出一个明确边界：仅把 GM bias 变成本地 table 后仍逐次复制到 transient K×H buffer，会把 GM 流量换成同量 UB-to-UB 流量；最终 R-004 直接把 `biasTableLocal[expert*HA]` 交给 VF。

## 模板与实现对比

| 对比维度 | P0/P1 R-004/R-003 KH | P2/P3 R-002/R-001 ROWKH | P4 R-005 H-full | P5 R-006 H-partial | 设计选择依据 |
|---|---|---|---|---|---|
| Host 命中层级 | H2：H1 ROWKH 为假后判断 K×H 可入 UB | H1：最先判断完整表可入 UB | H3：前两层为假后判断 H 可入 UB | H4：前三层为假 | 本表按知识重要性排列；Host 仍按 H1→H2→H3→H4 短路 |
| 模板与 dtype | `KHFullLoad<T,S,mode>` 加 Direct bool/mask | `RowKHFullLoad<T,S,mode>` 加 Direct bool/mask | `HFullLoad<T,S,mode>` | `HPartialLoad<T,S,mode>` | T三类；BF16 S两类 |
| 循环与分核 | block→rowTile→row/batch→K→H | block→rowTile→row→K | block→rowTile→row→Ktile→K→H | block→row→Htile→K→H | UB承载域决定循环层次 |
| Queue/TBuf/寄存器 | 全部行/K tile depth2；R004 bias depth1 | expanded/bias depth1；R002 index depth1 | K/H tile depth2 | H tile depth2 | FP32 RegTensor公共 |
| 内存总占用与复用 | 中等，按row复用；R004按kernel复用 bias table | 最大 persistent expanded/bias table | K tile | 最小H tile | 均受Host UB式限制 |
| 搬运/Vector API | gather DMA+批量ID；R004直接寻址 bias cache | 全表DMA+scalar/local索引 | Ktile gather | Htile gather | Vector公式相同 |
| 同步、精度与 tail | 加 S_V/MTE2_S；validK/drop-pad | Queue/FP32/K原序；row tail | K tail | H tail | CAST_RINT统一 |
| fallback/失败边界 | R-004→R-003；KH Host失败→H3 | R-002→R-001；ROWKH Host失败→H2 | →H4 R-006 | 无 | 非法输入不应进入Device |

## 平台差异

| 项目 | A2 | A3 | A5 |
|---|---|---|---|
| 支持状态 | 官方 V2 文档支持；本卡 Direct 交付未覆盖 | 官方 V2 文档支持；本卡 Direct 交付未覆盖 | 官方文档、ascend950 binary、arch35 与 Direct `dav-3510` 接线闭合 |
| Host/Launcher | 固定交付不可见 | 固定交付不可见 | 自包含 Direct tiler+PyTorch launcher |
| Kernel/资源 | 本卡不推导 | 本卡不推导 | arch35 AIV/MicroAPI；A5 UB/core 数运行时查询 |

## 限制与失败边界

- Direct 只覆盖公开的七输入 schema；官方 V2 的 `x/alpha1/alpha2/v` 与三类 expert range 不可从该 Direct 入口设置。
- optional tensor 除 shape/dtype 外未统一检查 contiguous、device；`scales` 在读 `size(1)` 前未检查 rank；调用者需保证 2-D、同 device、可按连续地址访问。
- Direct 未逐值检查 row index、expert index；drop-less 专用 KH Route 会在编译期移除 sentinel/上界判断，必须满足公开有效域。
- 所有 UB 公式使用 `int64_t`，POD 也是 int64；Device 部分 DMA 参数窄化为 `uint16_t/uint32_t`，Direct Host 未对极大维度逐项验证这些 API 上限。
- BF16 expanded 配 FP32 scale 时，Host scale 项与 Device `RoundUp<T>(n)*sizeof(S)` 的对齐口径不完全一致；本卡的 Route 字节账采用 Device 实分配，复用实现必须据此重新验证 UB，不能只照抄 Host 选择式。
- `calc_moe_finalize_routing_tiling` 假设 UB 至少能容纳一个最小 tile；若输入超出公开支持范围导致搜索下界为0/除数异常，源码没有独立 fallback。
- launcher 返回 `void`，`aclCall` 固定返回0；异步 launch 错误不在该源码闭包内同步传播。
- Frontmatter 只收录固定 Commit 官方相关文件；Direct 适配事实来自受控 final candidate，未将本机路径或不可达交付 URL写入卡片。
- 本次知识提取未执行编译、真机、数值或性能测试，不声明实测收益。

## 源码索引

### 链路索引

| 链路阶段 | 文件 | 关键符号 | 支撑内容 |
|---|---|---|---|
| 入口声明/约束 | `docs/aclnnMoeFinalizeRoutingV2.md` | 产品支持与公式 | A5支持、dtype/shape语义（官方相关） |
| 入口声明/约束 | `op_graph/moe_finalize_routing_v2_proto.h` | `REG_OP(MoeFinalizeRoutingV2)` | 输入、属性、scale A5差异 |
| Host/Tiling/Launcher | `op_host/moe_finalize_routing_v2_tiling_arch35.cpp` | `MoeFinalizeRoutingV2Regbase` | 四级selector、POD、UB公式 |
| Kernel entry/body | `op_kernel/moe_finalize_routing_v2_apt.cpp` | `moe_finalize_routing_v2` | key到四body的官方映射 |
| Kernel entry/body | `op_kernel/arch35/moe_finalize_routing_v2_base.h` | `VFProcess*`、`CopyIn/CopyOut` | FP32计算、cast、DMA helper |
| Kernel entry/body | `op_kernel/arch35/moe_finalize_routing_v2_row_k_h_full_load.h` | `MoeFinalizeRoutingV2RowKHFullLoad` | ROWKH基线 |
| Kernel entry/body | `op_kernel/arch35/moe_finalize_routing_v2_k_h_full_load.h` | `MoeFinalizeRoutingV2KHFullLoad` | KH基线 |
| Kernel entry/body | `op_kernel/arch35/moe_finalize_routing_v2_h_full_load.h` | `MoeFinalizeRoutingV2HFullLoad` | H-full body |
| Kernel entry/body | `op_kernel/arch35/moe_finalize_routing_v2_h_partial_load.h` | `MoeFinalizeRoutingV2HPartialLoad` | H-partial body |
| POD/ABI | `op_kernel/arch35/moe_finalize_routing_v2_tiling_struct.h` | `MoeFinalizeRoutingV2RegbaseTilingData` | 28字段 ABI |
| 构建接线 | `op_host/config/ascend950/moe_finalize_routing_v2_binary.json` | `MoeFinalizeRoutingV2` entries | A5 dtype/optional 注册 |

每行文件都存在于 Frontmatter `sources`。Direct adapter、plugin 与 Direct CMake 只以符号说明交付适配闭包，不伪造官方 URL。

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | 28×int64 POD、Direct wrapper按值传递 | 字段顺序、224B POD、T/S/mode模板一致 | `MoeFinalizeRoutingV2RegbaseTilingData` |
| 调用顺序 | 校验→tiling→单次同stream launch | 专用 guard必须在generic前；只启动一个entry | `moe_finalize_routing_npu`、`launch_moe_finalize_routing` |
| workspace/内存 | workspace=0；UB按实际depth计账 | cache table不与transient queue同时计漏；odd H按HA stride | 四个 `InitBuffer` 网络 |
| 同步 | Queue、S_V、MTE2_S、LocalMemBar | y原地K累加前必须保证V store→load | base/KH body |
| 精度与尾块 | FP32累加、K原序、CAST_RINT、mask/tail | 不可每K降精度或重排K；drop-pad要压缩validK/scale | `VFProcessExpandXBiasScaleOptimized` |
| 失败边界 | Host拒绝dtype/rank/shape依赖 | Direct未检查的device/contiguous/index/API窄化由调用者补齐 | `ValidateAndGetShape`、Direct tiler |
