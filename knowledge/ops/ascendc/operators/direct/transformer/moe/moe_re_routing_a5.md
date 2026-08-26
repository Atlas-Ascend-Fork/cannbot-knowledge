---
type: Operator
title: "MoeReRouting A5 Direct Invoke 算子知识"
description: "说明 moe_re_routing_npu、calc_moe_re_routing_tiling 与 launch_moe_re_routing 在 A5 上的接口语义、Launcher 参数生成、Route 选择、单 Kernel 启动图与逐 Route 实现。"
tags: [task.implementation, task.lookup, topic.data_movement, topic.memory, topic.precision]
status: stable
verified:
  - by: process:ops-knowledge-route-priority
    at: "2026-08-25T20:47:20Z"
  - by: process:ops-knowledge-direct53-ingest
    at: "2026-08-25T20:03:11Z"
sources:
  - resource: "https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_re_routing/README.md"
    role: header
  - resource: "https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_re_routing/op_host/moe_re_routing_def.cpp"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_re_routing/op_host/moe_re_routing_tiling.h"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_re_routing/op_host/moe_re_routing_tiling_base.cpp"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_re_routing/op_host/moe_re_routing_re_tiling.h"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_re_routing/op_host/moe_re_routing_re_tiling.cpp"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_re_routing/op_host/moe_re_routing_r_tiling.h"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_re_routing/op_host/moe_re_routing_r_tiling.cpp"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_re_routing/op_kernel/moe_re_routing_apt.cpp"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_re_routing/op_kernel/arch35/moe_re_routing_re_regbase.h"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_re_routing/op_kernel/arch35/moe_re_routing_r_regbase.h"
    role: implementation
  - resource: "https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_re_routing/op_host/config/ascend950/moe_re_routing_binary.json"
    role: implementation
created_at: "2026-08-25T19:38:59Z"
updated_at: "2026-08-25T20:47:20Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# MoeReRouting A5 Direct Invoke 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | `cann_bench::moe_re_routing_npu` → `calc_moe_re_routing_tiling` → `launch_moe_re_routing` → 36 个显式 global entry 之一；Direct Invoke。 |
| 计算语义 | 将 rank-major、rank 内 expert-major 的 token 段转成 expert-major、expert 内 rank-major；scale 同步重排，生成 gather index 与逐 expert token 总数。 |
| 输入输出 | `tokens[A,H]` fp16/bf16/int8；`counts[N,E]` int32/int64；可选 `scales[A]` fp32；输出 `[A,H]`、`[A]` fp32、`[A]` int32、`[E]` 与 counts 同 dtype。 |
| 执行类型 | R-001/R-002/R-003 均为单 Kernel `AIV_VECTOR` 数据搬运；entry 对 `g_coreType==AIC` 直接返回，无可达 Cube/AIC 或 MIX_CV。 |
| Kernel 路线 | 重要性降序为 P0 R-002 Device 派生 fast-RE、P1 R-003 官方 R、P2 R-001 官方 RE；Host 仍按 R-001→R-002→R-003 短路。每条 Route 各有 3×2×2 个 dtype/index/scale 实例。 |
| 核心资源 | GM、`TQueBind<VECIN,VECOUT,1>` depth=2、index `TQue<VECOUT,1>` depth=2；无 workspace、dynamic UB、NDDMA buffer 或通信 window。 |
| 来源闭包 | `direct_implementation_closed`：官方 A5 语义、POD、R/RE tiling 与 body 已闭合；Direct wrapper、显式 launcher、无-scale 清零及 fast-RE 为转换交付的 Device 派生补充，固定官方仓无对应文件，边界已显式隔离。 |
| 验证状态 | 已完成源码闭包检查；本次知识提取未执行编译、真机、数值或性能测试。 |

## 接口与语义

### 计算语义

令 `C[r,e]=expert_token_num_per_rank[r,e]`。输入 token 按 `(rank,expert)` 词典序分段，输出按 `(expert,rank)` 词典序分段。单元 `(r,e)` 的 token 数、源首 token 与目标首 token 为：

```text
count(r,e) = C[r,e]
S(r,e) = sum_{r'<r,e'} C[r',e'] + sum_{e'<e} C[r,e']
D(r,e) = sum_{e'<e,r'} C[r',e'] + sum_{r'<r} C[r',e]
permute_tokens[D(r,e):D(r,e)+C[r,e]] = tokens[S(r,e):S(r,e)+C[r,e]]
expert_token_num[e] = sum_r C[r,e]
```

有 scale 时对同一 token 区间做完全相同的置换。Direct 入口固定 `idx_type=0`，所以 `permute_token_idx[D+k]=S+k`，是从输出位置回到输入位置的 gather index。固定官方 body 同时实现 `idx_type=1` 的 scatter 方向，但 Direct wrapper 拒绝该属性。无 scale 时仍返回 `[A]` fp32 占位输出，交付派生 entry 在 Device 上将其置零；官方 kernel 不写这个可选输出。

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| `tokens` | `[A,H]`，ND；调用方保证 contiguous | fp16/bf16/int8 | Direct 接受正维；官方约束 `0<H<16384`。位模式搬运，不做数值计算。 |
| `expert_token_num_per_rank` | `[N,E]`，ND；调用方保证 contiguous | int32/int64 | `N,E>0`；调用方须保证元素非负且 `sum(C)=A`，Direct Host 不读取/校验 tensor 值。 |
| `per_token_scales` | 可选 `[A]`，ND；调用方保证 contiguous | fp32 | 存在时与 token 同置换；Direct 子集不接官方 2D/3D 或 fp8 scale。 |
| `expert_token_num_type` | Host 标量 | int64 | Direct 仅允许 1（count 模式），默认 1。 |
| `idx_type` | Host 标量 | int64 | Direct 仅允许 0（gather index），默认 0。 |
| `permute_tokens` | `[A,H]` | 同 `tokens` | expert-major 输出。 |
| `permute_per_token_scales` | `[A]` | fp32 | 有 scale 时置换输出；无 scale 时为 Device 清零占位。 |
| `permute_token_idx` | `[A]` | int32 | Direct 为 gather index；`A` 必须能由 int32 index 表达。 |
| `expert_token_num` | `[E]` | 同 counts | 每列求和。 |

### 入口与版本

本卡固定转换交付的 CANN 9.1.0、A5/Ascend 950 Direct Invoke，不补写成 ACLNN。官方 README 明列 Ascend 950PR/950DT，`MoeReRouting` OpDef 为 `ascend950` 接入 `moe_re_routing_apt`，binary config 列出 A5 dtype 组合。转换交付只覆盖 fp16/bf16/int8 token、int32/int64 counts、可选 fp32 scale；官方额外的 FP8/HIFLOAT8/FP4、`idx_type=1`、多维 scale 不属于此 Direct ABI。

官方固定提交没有 `calc_moe_re_routing_tiling`、`launch_moe_re_routing`、Torch 注册、fast-RE 或无-scale 清零实现。它们是 final candidate/source mapping 记录的 Device 派生补充路线；官方 `MoeReRoutingReRegbase`、`MoeReRoutingRRegbase` 的算法主体与 POD 字段顺序则被转换交付保留。

## Host/Launcher 执行流程

### 参数校验与前处理

1. `moe_re_routing_meta` 检查两个必选输入均为 2D 且各维为正；token dtype 为 fp16/bf16/int8，counts dtype 为 int32/int64；属性固定为 `expert_token_num_type=1, idx_type=0`。
2. scale 存在时要求 shape 为 `[A]`、dtype fp32。随后用输入 options 创建四个输出；没有 Host tensor-value 计算。
3. `moe_re_routing_npu` 要求输入同 device，映射 token/index dtype code，调用 `calc_moe_re_routing_tiling(A,H,N,E,sizeof(TIndex),hasScale,idxType)`。
4. tiler 从 `PlatformAscendCManager` 读取 AIV 数 `P` 与 UB 字节 `U`，按优先级选择 RE、fast-RE 或 R，并填 Direct POD。
5. wrapper 取得当前 NPU stream；`launch_moe_re_routing` 先按 Route，再按 token dtype、counts dtype、scale presence 分派一个显式 global entry。

Direct wrapper 没有复现官方全部检查：未验证 `sum(C)=A`、counts 非负、`H<16384`、int32 输出 index 上界，也没有显式 default 错误分支处理越界 dtype code；这些条件由 wrapper 已有 dtype 检查与调用方契约共同保证。

### 参数、Workspace 与生命周期

所有输入输出由调用方/框架分配，Direct launcher不申请 workspace，`workspace_total=0`。`MoeReRoutingLaunchParams` 是调用栈上的同步 Host 参数；global launch 按值复制其中选中 POD。stream 为当前 NPU stream；单 Kernel launch 后输出生命周期由 Torch allocator/stream 语义管理。

令 `I=sizeof(TIndex)`：index queue 预留 `Ridx=2*256*I` 字节。R 与 fast-RE 使用 `q=align((U-Ridx)/2-32,32)`；官方 RE 使用 `q=align((U-Ridx)/2,32)`。Direct tiler把 `q` 写作 `ubFactor`。`-32` 为 R/fast 路径对向上对齐保留的 gap；这里的 `align` 与源码一致是向上对齐。

### 启动图与失败传播

```text
moe_re_routing_npu
  -> calc_moe_re_routing_tiling
  -> launch_moe_re_routing(current stream)
     -> exactly one AIV global entry
        -> [hasScale=false: disjoint GM zero-fill of scale placeholder + PIPE_ALL barrier]
        -> RouteClass::Init
        -> RouteClass::Process
  -> four output tensors
```

三条 Route 都是单 Kernel，无跨 Kernel edge、event 或 workspace。entry 的 `g_coreType==AIC` guard 排除 Cube 核。Host launcher不读取异步 Device 返回；显式 entry 选择依赖 wrapper 已校验的枚举。无-scale 的每核清零区间为 `[blockIdx*ceil(A/blockDim), min(A,...))`，区间互斥；`PipeBarrier<PIPE_ALL>` 是该 AIV 核内流水屏障，不应解释为跨核 barrier。

## Route 与参数设计

### 分核与资源计算

```text
P = AIV core count, U = UB bytes, I = sizeof(count dtype)
reserve = 2*256*I

RE / fast-RE:
  br0 = ceil(N/P)
  blockNumR = ceil(N/br0); blockFactorR = ceil(N/blockNumR)
  blockNumE0 = min(P/max(blockNumR,1), E)
  blockFactorE = ceil(E/blockNumE0); blockNumE = ceil(E/blockFactorE)
  blockDim = blockNumR*blockNumE
  ubFactor = align((U-reserve)/2 - (fast-RE ? 32 : 0), 32)

R:
  blockFactor0 = ceil(N/P)
  blockNum = ceil(N/blockFactor0); blockFactor = ceil(N/blockNum)
  blockDim = blockNum
  ubFactor = align((U-reserve)/2-32,32)
```

Direct Meta 要求 `A,N,E>0`，所以 tiler 中 `A==0` 的 `blockNum=1` 分支不可达。Device 内部对最后 rank/expert block、最后 UB loop 与 index 的 256-entry loop分别裁尾。

### Route 选择

下表按重要性降序排列；`Host 顺序`独立记录 launcher 的真实判断次序，因此 P0 不代表先执行。

| 重要性 | Host 顺序 | Route | 主要特征 | Key/模板 | 精确选择条件、短路与 fallback |
|---|---:|---|---|---|---|
| P0 | 2 | R-002 Device 派生 fast-RE | rank×expert 矩形分核，块内递增维护 S/D，复用 R 的合并搬运 | `useReRoute=2`；`MoeReRoutingFastReRegbase<T,I,float,S>` | 仅在 Host 顺序1失败后判断 `N*2<=P && E!=1`；失败落到 R-003。 |
| P1 | 3 | R-003 官方 R | rank-only 分核，逐 expert 扫描 counts，full-load/overload 自适应 | `useReRoute=0`；`MoeReRoutingRRegbase<T,I,float,S>` | 前两个分支均失败后的最终 fallback，即 `E==1`，或 `N>=5 && 2N>P`。 |
| P2 | 1 | R-001 官方 RE | 官方 rank×expert 矩形分核，每个 cell 独立求 S/D | `useReRoute=1`；`MoeReRoutingReRegbase<T,I,float,S>` | 首先判断 `N<5 && E!=1`；命中即短路，未命中继续 R-002。 |

```text
if N < 5 && E != 1: R-001
else if 2*N <= AIV_core_num && E != 1: R-002   # Device 派生
else: R-003
then token_type(fp16/bf16/int8) × index_type(i32/i64) × has_scale(false/true)
```

### 模板/实现执行矩阵

| 重要性 | Host 顺序 | Route | key/selector | dtype/shape/platform 完整命中条件 | 执行拓扑与 Kernel 节点 | 实际模板/body | 内存与同步特征 | tail/fallback |
|---|---:|---|---|---|---|---|---|---|
| P0 | 2 | R-002 派生 fast-RE | `useReRoute=2` | A5；R-001 未中；`2N<=P,E>1`；T∈fp16/bf16/int8，I∈i32/i64，S∈{false,true} | 单 AIV | 派生 `FastRe::Process` + 官方 R 搬运 helper | 同 RE POD，采用 R 的合并 token+scale搬运；核内增量 offset | 同 R 的 UB/tail；条件失败转 R-003。 |
| P1 | 3 | R-003 官方 R | `useReRoute=0` | A5；`E=1` 或 `N>=5,2N>P`；同 dtype 矩阵 | 单 AIV | `MoeReRoutingRRegbase<T,I,float,S>::Process` | 按 rank 分核；每 expert 扫 counts 求 offset | 末 rank/core、UB loop、256 index tail；最终 fallback。 |
| P2 | 1 | R-001 官方 RE | `useReRoute=1` | A5；`N<5,E>1`；同 dtype 矩阵 | 单 AIV | `MoeReRoutingReRegbase<T,I,float,S>::Process` | rank×expert 矩形分核；bound queue+index queue；无 workspace | 末 rank/expert block、UB loop、256 index tail；零 count 跳过。 |

### 隐藏性能 Guard

| Guard | Host/Tiling 条件 | Device/资源原因 | 影响 Route | 不满足时去向 | 源码符号 |
|---|---|---|---|---|---|
| fast-RE cell 并行 | R-001 未中且 `2N<=P,E!=1` | 至少可暴露两倍 rank cell；这是交付派生 guard | R-002 | R-003 | 派生 `calc_moe_re_routing_tiling`，官方固定仓无对应符号。 |
| R 最终 fallback | R-001、R-002 均未命中 | 保留单 expert 与较大 rank 的完整实现 | R-003 | 无下一 Route | 派生 `calc_moe_re_routing_tiling` 的 `else`。 |
| RE Host 首选 | `N<5 && E!=1` | 小 rank 时增加 expert 维并行度 | R-001 | R-002/R-003 | 官方 `MoeReRoutingReTiling::IsCapable`；Direct tiler等价首分支。 |
| UB 双缓冲 | `reserve=2*256*I; q≈(U-reserve)/2` | queueBind 与 index queue 均 depth=2 | 全部 | Direct 无显式失败；要求 `U>reserve` | 官方 `SplitUb`、各 `Init`。 |
| full/overload | R/fast：`ubFactor >= align(H*sizeof(T),32)+[S?align(4,32):0]`；RE 每 token/scale各自比较 | 决定批量 token 搬运或逐 token/分段搬运 | 全部 body 内子路 | 自动走 overload | `ProcessTokenScale`。 |
| int8 压缩 | `tokenSizeOrigin>0` | FP4 2:1 物理存储地址 | 官方扩展 | Direct 永远为0 | `CalTokenOffset`；Direct POD producer写0。 |
| index 分块 | `rows>256` | index queue 固定 256 项 | 全部 | 继续下一 loop，末 loop裁尾 | `CopyOutIndex`。 |
| 空域/契约 | Direct 要求正维，但不读 counts | 防止除零/OOB | 全部 | Host 异常或未定义越界 | `moe_re_routing_meta` 派生边界；官方 `CheckParam`。 |

### POD/ABI

所有字段都是顺序 `int64_t`，故标准布局可直接推出 `alignof=8`；RE POD `sizeof=96`，R POD `sizeof=72`，Launch POD `sizeof=184`。官方 tiling macro定义与 Direct POD字段顺序相同，但 Direct 使用普通 C++ struct 按值传 kernel。

| 结构 | 字段 | 类型/位宽 | ABI 布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| `MoeReRoutingLaunchParams` | `blockDim` | int64/64 | off0 | core | tiler=`blockNum` | launch `<<<blockDim>>>` | >0。 |
| 同上 | `useReRoute` | int64/64 | off8 | enum | 0/1/2 selector | launcher Route 分支 | 2 为官方缺失的派生值。 |
| 同上 | `re` | struct/96B | off16 | POD | R-001/2 producer | RE/fast entry | R-003 inactive。 |
| 同上 | `r` | struct/72B | off112 | POD | R-003 producer | R entry | R-001/2 inactive。 |
| `MoeReRoutingReTilingData` | `tokenSize` | int64/64 | off0 | element/token | `H` | token地址/DMA | Direct不压缩。 |
| 同上 | `scaleSize` | int64/64 | off8 | element/token | `hasScale?1:0` | scale DMA | false时编译期不读GM。 |
| 同上 | `rankNum` | int64/64 | off16 | rank | `N` | offset/循环 | >0。 |
| 同上 | `expertNum` | int64/64 | off24 | expert | `E` | offset/循环 | >0。 |
| 同上 | `coreNum` | int64/64 | off32 | core | `blockNumR*blockNumE` | expert总数步长、清零分片 | 等于blockDim。 |
| 同上 | `blockNumR` | int64/64 | off40 | block | RE分核公式 | `blockIdx%blockNumR` | >0。 |
| 同上 | `blockFactorR` | int64/64 | off48 | rank/block | `ceil(N/blockNumR)` | rank区间 | 末块裁尾。 |
| 同上 | `blockNumE` | int64/64 | off56 | block | RE分核公式 | `blockIdx/blockNumR` | >0。 |
| 同上 | `blockFactorE` | int64/64 | off64 | expert/block | `ceil(E/blockNumE)` | expert区间 | 末块裁尾。 |
| 同上 | `ubFactor` | int64/64 | off72 | byte budget | UB公式 | queue容量/分段因子 | fast-RE额外减32。 |
| 同上 | `idxType` | int64/64 | off80 | enum | Direct固定0 | `CopyOutIndex` | 官方允许1。 |
| 同上 | `tokenSizeOrigin` | int64/64 | off88 | logical element | Direct固定0 | FP4地址 | Direct inactive。 |
| `MoeReRoutingRTilingData` | `tokenSize` | int64/64 | off0 | element/token | `H` | R/fast token DMA | >0。 |
| 同上 | `scaleSize` | int64/64 | off8 | element/token | 0/1 | scale DMA | S=false inactive。 |
| 同上 | `rankNum` | int64/64 | off16 | rank | `N` | rank/offset循环 | >0。 |
| 同上 | `expertNum` | int64/64 | off24 | expert | `E` | expert/offset循环 | >0。 |
| 同上 | `coreNum` | int64/64 | off32 | core | R=`blockNum` | rank映射/总数步长/清零 | 等于blockDim。 |
| 同上 | `blockFactor` | int64/64 | off40 | rank/core | R公式 | Direct R body实际上按`rank%coreNum`循环；保留ABI但不直接读 | 不得删除。 |
| 同上 | `ubFactor` | int64/64 | off48 | byte budget | R UB公式 | full/overload与queue | >0。 |
| 同上 | `idxType` | int64/64 | off56 | enum | 0 | index方向 | Direct固定。 |
| 同上 | `tokenSizeOrigin` | int64/64 | off64 | logical element | 0 | FP4地址 | Direct inactive。 |

### Route 源码闭包

| 重要性 | Host 顺序 | Route | Key/selector | Host/Tiling producer | POD/参数 | Kernel entry/router 节点 | Kernel body/直接依赖 | 构建接线 |
|---|---:|---|---|---|---|---|---|---|
| P0 | 2 | R-002 fast-RE | `useReRoute=2` | Direct派生 tiler | RE POD | Direct 12个 `moe_re_routing_fast_re_*` | 派生 `FastRe::Process`；数据搬运映射官方 R body | Direct-only，官方固定仓无 fast-RE target。 |
| P1 | 3 | R-003 官方 R | `useReRoute=0` | Direct派生 tiler；公式映射官方 `MoeReRoutingRTiling` | 官方 `MoeReRoutingRTilingData` 顺序 | Direct 12个 `moe_re_routing_r_*`；官方 router key 210000/210100 | 官方 `arch35/moe_re_routing_r_regbase.h` | 官方 OpDef `ascend950`+binary config；Direct CMake为交付派生。 |
| P2 | 1 | R-001 官方 RE | `useReRoute=1` | Direct派生 tiler；公式映射官方 `MoeReRoutingReTiling` | 官方 `MoeReRoutingReTilingData` 顺序 | Direct 12个 `moe_re_routing_re_*`；官方 router key 200000/200100 | 官方 `arch35/moe_re_routing_re_regbase.h` | 官方 OpDef `ascend950`+binary config；Direct CMake为交付派生。 |

## Kernel 实现

### 公共执行流程

每个 global entry 先排除 AIC，构造 `TPipe` 与对应 `RouteClass<T,TIndex,float,hasScale>`。无 scale 时先按核分片 `InitOutput<float>(...,0)`，再执行 `Init→Process`。`Init` 绑定七个 GM tensor（scale 仅编译期存在时绑定），建立一个 VECIN/VECOUT bound queue 与一个 index output queue。

公共搬运不做 token 算术：`DataCopyPad` 把 token/scale GM 段搬到 bound queue，同一 LocalTensor 随后由 VECOUT 侧取出写目标 GM。`CopyOutIndex` 用 `CreateVecIndex(head,subRows)` 生成连续 int32 index；`CalcExpertTokenNum` 在标量寄存器累加每列 counts，再用 `Duplicate` 写一个 LocalTensor 并搬出。同步来自 TQue 的 `Alloc→EnQue→DeQue→Free` 生命周期；无 atomic、跨核 barrier 或 workspace。

### Route R-002（P0）：Device 派生矩形 fast-RE

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Direct tiler | Device 派生文件（官方缺失） | `calc_moe_re_routing_tiling` | R-001未中且 `2N<=P,E!=1` | `useReRoute=2`。 |
| Router | Device 派生文件（官方缺失） | `launch_moe_re_routing` | route2+dtype矩阵 | `moe_re_routing_fast_re_*`。 |
| Body | Device 派生文件（官方缺失） | `MoeReRoutingFastReRegbase::Process` | RE矩形POD | 增量src/dst offset；搬运helper映射官方R。 |

#### Device 数据流

##### 函数级调用链

```text
launch -> fast_re_entry -> [!S zero] -> FastRe::Init -> FastRe::Process
 -> rectangular (rank,expert) loop with incremental offsets
 -> official-R-derived ProcessTokenScale/Copy*/CopyOutIndex
 -> CalcExpertTokenNum
```

##### 源码等价伪码

```text
计算本核矩形 [rStart,rEnd)×[eStart,eEnd)
for r in rank block:
  src = 所有前rank总数 + 当前rank中eStart之前总数
  dst = eStart之前所有expert总数
  for e in expert block:
    dst += 当前expert中前rank总数
    c=C[r,e]; if c!=0: 合并搬运token+scale并写index
    src += c
    dst += 当前expert从本rank到末rank总数
最后按blockIdx步长写expert总数
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM与两queue | 同R-001的S/D/c | 同R-003的合并 token+scale slice | T/I/fp32 | 派生offset+官方搬运helper | output | caller/TPipe | depth2、32B、逐cell复用。 |

##### 分层内存布局

```mermaid
block-beta
  columns 2
  dataQ["queBind · depth=2 · 2*q bytes"]:1
  idxQ["idxOutQue · depth=2 · 2*qi bytes"]:1
```

##### 字节账与复用顺序

```text
q=align(align((U-2*256*I)/2-32,32),32/sizeof(T)); qi=align(256*I,32/I)
UB_total=2*q+2*qi<=U（依32B gap与平台UB对齐）; dynamic_ub=N/A; workspace_total=0
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| bound/index slots | fast-RE搬入/index生成 | 搬出 | 下一tile/cell | Queue生命周期 | 矩形cell间无UB存活数据。 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| cell relay | TQueBind | GM→UB | UB→GM | slot | 位模式；R风格full/overload；r/e/UB/index均裁尾。 |
| offset | 标量增量 | counts扫描 | 下一cell地址 | S/D | 不改变数学顺序；非法counts会OOB。 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | 官方无对应文件 | 派生 `calc_moe_re_routing_tiling` | fast-RE专用guard与32B gap。 |
| Kernel entry/router | 官方无对应文件 | 派生 `moe_re_routing_fast_re_*` | 12实例。 |
| Device body/helper | 官方最近映射 `op_kernel/arch35/moe_re_routing_r_regbase.h` | `ProcessTokenScale/Copy*/CopyOutIndex` | 搬运部分来源；矩形`Process`为派生，不伪称官方。 |

### Route R-003（P1）：官方 rank-only R

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| 官方 Host | `op_host/moe_re_routing_r_tiling.h` | `MoeReRoutingRTiling::IsCapable` | Regbase；priority 11000，在RE priority10000失败后命中 | R。 |
| Direct tiler | Device 派生文件（官方缺失） | `calc_moe_re_routing_tiling` | 两个前置分支均失败 | `useReRoute=0`。 |
| Body | `op_kernel/arch35/moe_re_routing_r_regbase.h` | `MoeReRoutingRRegbase::Process` | R POD | rank-only循环。 |

#### Device 数据流

##### 函数级调用链

```text
launch -> r_entry -> [!S zero] -> R::Init -> R::Process
 -> per-rank source prefix scan
 -> per-expert destination prefix scan
 -> ProcessTokenScale -> (UbFullLoad | UbOverLoad)
 -> CopyIn/CopyOutIndex/CopyOut -> CalcExpertTokenNum
```

##### 源码等价伪码

```text
for r=blockIdx; r<N; r+=blockDim:
  src=sum_{r'<r,e} C[r',e]; dst=0
  for e in [0,E):
    c=C[r,e]; dst += sum_{r'<r} C[r',e]
    搬运c个token/scale并写index
    src += c; dst += sum_{r'>=r} C[r',e]
for e=blockIdx; e<E; e+=blockDim: expert_out[e]=sum_r C[r,e]
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM token+scale | S/D公式 | c rows | T/fp32 | caller/R offset | Copy helpers/caller | caller | full-load可在同一bound slot拼接token与scale。 |
| GM index/count | D及`r*E+e` | c / N×E | int32/I | helper/caller | caller/body | caller | 256 index tail；标量counts扫描。 |
| `queBind_`/`idxOutQue_` | 物理slot | q/qi，均depth2 | T/reinterpret fp32；I/int32 | helper | helper | TPipe | 32B对齐、Free后复用。 |

##### 分层内存布局

```mermaid
block-beta
  columns 2
  dataQ["queBind · depth=2 · 2*q bytes"]:1
  idxQ["idxOutQue · depth=2 · 2*qi bytes"]:1
```

##### 字节账与复用顺序

```text
q=align(align((U-2*256*I)/2-32,32),32/sizeof(T)); qi=align(256*I,32/I)
UB_total=2*q+2*qi<=U（依32B gap与平台UB对齐）; dynamic_ub=N/A; workspace_total=0
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| bound queue slot | `CopyIn`或分段CopyIn | `CopyOut` | 下一tile/expert | EnQue→DeQue→Free | hasScale拼接偏移按32B对齐。 |
| index queue slot | `CreateVecIndex`/`Duplicate` | GM copy | 下一块 | Queue生命周期 | `subRows<=256`。 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| full-load | TQueBind | token与可选scale拼接 | token/scale分别搬出 | 同一slot子区 | 每批`floor(ubFactor/tokSclSize)` token；末批取余。 |
| overload | TQueBind | 单token的token/scale分段 | 对应GM段 | slot | 末子段取`size%ubFactor`。 |
| index/sum | TQue+标量 | index序列/列和 | GM | slot/output | int32 index与I累加不升精度。 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `op_host/moe_re_routing_r_tiling.cpp` | `SplitCore/SplitUb/PostTiling` | rank分核、32B gap、R POD。 |
| Kernel entry/router | `op_kernel/moe_re_routing_apt.cpp` | keys 210000/210100 | 官方 key→R实例；Direct显式化。 |
| Device body/helper | `op_kernel/arch35/moe_re_routing_r_regbase.h` | `Process/UbFullLoad/UbOverLoad/Copy*` | rank循环、offset、拼接搬运与tail。 |

### Route R-001（P2）：官方 rank×expert RE

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| 官方 Host | `op_host/moe_re_routing_re_tiling.h` | `MoeReRoutingReTiling::IsCapable` | Regbase 且 `rankNums_<5 && expertNum_!=1` | RE；失败尝试优先级11000 R。 |
| Direct tiler | Device 派生文件（官方缺失） | `calc_moe_re_routing_tiling` | 同一首分支 | `useReRoute=1`。 |
| Router | Device 派生文件（官方缺失） | `launch_moe_re_routing` | route+dtype矩阵 | 一个 `moe_re_routing_re_*` entry。 |
| Body | `op_kernel/arch35/moe_re_routing_re_regbase.h` | `MoeReRoutingReRegbase::Process` | RE POD | rank×expert cell搬运。 |

#### Device 数据流

##### 函数级调用链

```text
launch_moe_re_routing -> moe_re_routing_re_<T>_<I>_<S>
 -> [!S: ZeroUnusedScaleOutput]
 -> MoeReRoutingReRegbase::Init
 -> Process -> PrepareParams
    -> CalSrcOffSet -> CalDstOffSet
    -> ProcessTokenScale(token,false) -> CopyIn -> CopyOutIndex -> CopyOut
    -> [S] ProcessTokenScale(scale,true) -> CopyIn -> CopyOut
    -> CalcExpertTokenNum
```

##### 源码等价伪码

```text
(rb,eb)=divmod(blockIdx,blockNumR); 裁剪本核rank/expert尾块
for r in rank_block:
  src=S(r,expert_block_start)
  for e in expert_block:
    c=C[r,e]; if c==0: continue
    dst=D(r,e)
    分块 copy tokens[src:src+c] -> tokens_out[dst:dst+c]
    生成 idx_out[dst:dst+c]=src..src+c-1
    if hasScale: 分块 copy scale 同区间
    src += c
for e=blockIdx; e<E; e+=blockDim: expert_out[e]=sum_r C[r,e]
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM token in/out | `S*H` / `D*H` | `c*H` elements | T/ND rows | caller/CopyIn | CopyIn/caller | caller | `DataCopyPad`, tail按字节。 |
| GM scale in/out | `S` / `D` | `c` fp32 | fp32/[A] | caller/CopyIn | CopyIn/caller | caller | S=true only。 |
| GM index | `D` | `c` int32 | int32/[A] | `CreateVecIndex` | caller | caller | 256项分块。 |
| GM counts/out | `[r,e]` / `[e]` | N×E / E | TIndex/ND | caller/Calc | offset与sum/caller | caller | 标量GetValue；每e单写者。 |
| `queBind_` | 物理slot | `q=align(ubFactor,32/sizeof(T))` bytes/slot | T或reinterpret fp32 | CopyIn | CopyOut | TPipe/Process | depth2、VECIN/VECOUT绑定复用。 |
| `idxOutQue_` | 物理slot | `qi=align(256*I,32/I)` bytes/slot | I或int32 | index/sum helper | GM copy | TPipe/Process | depth2。 |

##### 分层内存布局

```mermaid
block-beta
  columns 2
  dataQ["queBind VECIN↔VECOUT · depth=2 · 2*q bytes"]:1
  idxQ["idxOutQue VECOUT · depth=2 · 2*qi bytes"]:1
```

##### 字节账与复用顺序

```text
q=align(ubFactor,32/sizeof(T)); qi=align(256*sizeof(I),32/sizeof(I))
UB_total=2*q+2*qi; ubFactor=align((U-2*256*sizeof(I))/2,32)
dynamic_ub=N/A; workspace_total=0
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| bound queue slot | `CopyIn` | `CopyOut` | 下一 tile/scale | EnQue→DeQue→FreeTensor | Free 后才复用；token与scale串行。 |
| index queue slot | `CreateVecIndex`/`Duplicate` | `DataCopyPad` | 下一256项或expert | EnQue→DeQue→FreeTensor | 单消费者。 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| token/scale relay | TQueBind | `DataCopyPad` GM→UB | DeQue后 UB→GM | bound slot | 位模式不cast；full-load按token批，overload按单token子段；末loop取余。 |
| index | TQue+`CreateVecIndex` | int32连续序列 | GM copy | index slot | 每次≤256；`A`超int32会窄化。 |
| expert sum | 标量TIndex+TQue | `sum_r C`/`Duplicate` | GM copy | 单expert | 以I dtype累加，溢出语义未额外保护。 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `op_host/moe_re_routing_re_tiling.cpp` | `SplitCore/SplitUb/PostTiling` | 矩形分核、UB、RE POD。 |
| Kernel entry/router | `op_kernel/moe_re_routing_apt.cpp` | keys 200000/200100 | 官方 key→RE实例；Direct改为显式entry。 |
| Device body/helper | `op_kernel/arch35/moe_re_routing_re_regbase.h` | `PrepareParams/Process/ProcessTokenScale/Copy*` | cell offset、搬运、index、sum与tail。 |

## 算子特定优化

### Trick T-001：小 rank 使用 rank×expert 二维分核

#### 触发与源码依据

- 适用 Route：R-001。
- 触发条件：A5 Regbase 且 `rankNums_ < 5 && expertNum_ != 1`；优先级10000先于 R 的11000。
- Golden 来源：[`op_host/moe_re_routing_re_tiling.h:32-36`](https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_re_routing/op_host/moe_re_routing_re_tiling.h)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
return (Ops::Transformer::OpTiling::IsRegbaseSocVersion(context_)) &&
       (rankNums_ < MIN_RANK_NUM && expertNum_ != 1);
```

#### 机制与设计原因

R 只按 rank 分核，`N<5` 时最多暴露少量 block；RE 在不改变 cell 语义的前提下把 block映射成 `(rank block,expert block)`，`blockDim=blockNumR*blockNumE`。每核只搬其矩形 cell，并独立按 S/D 公式求偏移，从源码可证明增加了可并行 cell 数；本卡不声称实测收益。

#### 迁移边界

- 适用：counts矩阵驱动的二维分段转置，第一维过小而第二维大于1。
- 前提：A5 Regbase、每个输出 cell互不重叠、可从counts确定S/D。
- 失效：`N>=5` 或 `E==1` 时官方选择 R；Direct 可能先尝试派生 fast-RE。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓未提供可验证反例；但若不同核会写重叠 D 区间，就不能迁移该二维分核。

### Trick T-002：VECIN/VECOUT bound queue 原位转发

#### 触发与源码依据

- 适用 Route：R-001/R-003；R-002复用同一机制但其Direct body为派生。
- 触发条件：所有 token/scale搬运，且计算仅改变地址、不改变数据位模式。
- Golden 来源：[`op_kernel/arch35/moe_re_routing_r_regbase.h:90-93`](https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_re_routing/op_kernel/arch35/moe_re_routing_r_regbase.h)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
this->pipe_->InitBuffer(queBind_, DOUBLE_BUFFER,
                        Ops::Base::CeilAlign(tilingData_->ubFactor,
                        static_cast<int64_t>(BLOCK_SIZE / sizeof(T))));
```

#### 机制与设计原因

`TQueBind<VECIN,VECOUT,1>` 让 CopyIn 与 CopyOut共享同一物理 LocalTensor；中间没有 Cast/Vector算术。hasScale 的 R/fast full-load还把 scale放在 token 字节区之后的32B对齐子区，一次 queue slot同时承载两类数据，避免额外scale queue与中间物化。depth=2允许搬入/搬出流水交叠，安全性由EnQue/DeQue/Free控制。

#### 迁移边界

- 适用：纯重排、输入输出dtype/位模式一致的 GM→UB→GM relay。
- 前提：输出不依赖修改后的UB数据；拼接子区容量计入`tokSclSize`且32B对齐。
- 失效：需要数值变换、独立并行消费或双输出不同生命周期时，应拆queue/TBuf并重做字节账。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓未提供可验证反例；不得在`FreeTensor`前覆盖bound slot，亦不得用逻辑有效字节替代depth=2的实际分配。

### Trick T-003：UB可容纳时合并多 token 与可选 scale 搬运

#### 触发与源码依据

- 适用 Route：R-003；R-002派生复用。
- 触发条件：`ubFactor >= align(H*sizeof(T),32)+[hasScale?align(scaleSize*sizeof(float),32):0]`。
- Golden 来源：[`op_kernel/arch35/moe_re_routing_r_regbase.h:200-212`](https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_re_routing/op_kernel/arch35/moe_re_routing_r_regbase.h)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
if (tilingData_->ubFactor < tokSclSize) {
    CopyOutIndex(currTokenNum, tokensSrc_, tokensDst_);
    UbOverLoad(currTokenNum);
} else {
    UbFullLoad(currTokenNum, tokSclSize);
}
```

#### 机制与设计原因

可容纳时 `tokSclFactor=floor(ubFactor/tokSclSize)`，一次 DMA relay 多个连续 token，并在同批生成index；不足时才逐 token、再按UB factor切H/scale。它减少可证明的DMA调用与queue周转次数，同时保留末批与末子段精确长度。

#### 迁移边界

- 适用：按连续token段重排且token行定长。
- 前提：`tokSclSize`按真实字节与所有可选payload对齐计账，factor非零。
- 失效：单行超过UB时必须走overload；不能仍按整行批量搬运。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

官方源码给出的真实错误边界是 `ubFactor<tokSclSize`：继续计算整行batch factor会得到0并导致除零，必须切换`UbOverLoad`。

## 模板与实现对比

| 对比维度 | P0 R-002 派生 fast-RE | P1 R-003 官方 R | P2 R-001 官方 RE | 设计选择依据 |
|---|---|---|---|---|
| 命中条件/优先级 | Host顺序2；R-001未中且`2N<=P,E>1` | Host顺序3；前两分支未中 | Host顺序1；`N<5,E>1`即短路 | 重要性排序不改变Host短路。 |
| 模板与 dtype | `FastRe<T,I,float,S>` 12实例 | `R<T,I,float,S>` 12实例 | `Re<T,I,float,S>` 12实例 | T∈3、I∈2、S∈2。 |
| 循环与分核 | 矩形块，块内增量S/D | rank轮转，每expert扫描 | 矩形块，每cell重算S/D | 平行度与offset扫描成本权衡。 |
| Queue/TBuf/寄存器/dynamic UB/通信 window | boundQ+idxQ，depth2，R式合并payload | 同左 | boundQ+idxQ，depth2，token/scale分开 | 无TBuf/dynamic UB/通信。 |
| 内存总占用与复用 | `2q+2qi`，q producer减32 | 同fast-RE | `2q+2qi`，无32B gap | queue slot串行复用。 |
| 搬运/Vector/SIMT/NDDMA/通信 API | `DataCopyPad/CreateVecIndex/Duplicate` | 同左 | 同左 | 仅AIV数据搬运，无SIMT/NDDMA/通信。 |
| 同步、精度与 tail | Queue；合并搬运；矩形tail | Queue；full/overload；rank tail | Queue；token/scale分开；矩形tail | 均不cast；index int32，sum用I。 |
| fallback/失败边界 | guard失败到R-003 | Host最终fallback | 未命中继续R-002 | 非法输入不由Device修复。 |

## 平台差异

| 项目 | A2 | A3 | A5 |
|---|---|---|---|
| 支持状态 | 官方README支持；本Direct交付未生成 | 官方README支持；本Direct交付未生成 | 官方README、OpDef与ascend950 binary支持；本卡目标。 |
| Host/Launcher | 官方membase路径；Direct固定仓不可见 | 官方membase路径；Direct固定仓不可见 | 官方regbase R/RE；转换派生显式Direct launcher与fast-RE。 |
| Kernel/资源 | 非本卡闭包 | 非本卡闭包 | AIV-only，32B UB block，双队列；无workspace。 |

## 限制与失败边界

- Direct 子集仅支持 fp16/bf16/int8 token、int32/int64 counts、可选一维fp32 scale、`expert_token_num_type=1`、`idx_type=0`；不得按官方更宽A5 dtype/shape集合调用。
- 调用方必须保证三个输入 contiguous、counts 非负、`sum(C)=A`、`0<H<16384`、输出 gather index 可由int32表示。Direct wrapper未调用 contiguous 转换且Host不读取counts值；违约可能导致错误偏移或GM越界。
- Direct Meta拒绝空tensor，所以 tiler的`A==0`保护在本入口不可达。所有分核除法还依赖`N,E,P>0`与可用UB大于index预留。
- 无-scale 清零、fast-RE、Torch binding、普通POD和显式launcher均为Device派生补充；官方固定提交不存在可链接的Direct源文件，不能把最近官方R/RE文件当作这些派生逻辑的逐行证据。
- 官方 entry 对未知tiling key没有输出；Direct launcher对越界枚举最后分支会落入int8/i64/scale实例，但已由wrapper dtype/属性检查限制。复用时不得绕过wrapper。
- 本次知识提取未执行编译、真机、数值或性能测试。

## 源码索引

### 链路索引

| 链路阶段 | 文件 | 关键符号 | 支撑内容 |
|---|---|---|---|
| 入口声明/约束 | `moe/moe_re_routing/README.md` | 产品表、参数与约束 | A5支持、语义、dtype、shape与属性。 |
| 平台注册 | `moe/moe_re_routing/op_host/moe_re_routing_def.cpp` | `ops::MoeReRouting` | ascend950 regbase接线与dtype矩阵。 |
| POD | `moe/moe_re_routing/op_host/moe_re_routing_tiling.h` | RE/R tiling data | 字段顺序与位宽。 |
| Host校验 | `moe/moe_re_routing/op_host/moe_re_routing_tiling_base.cpp` | `GetShapeAttrsInfo/CheckParam` | 官方shape/dtype/属性边界。 |
| RE selector | `moe/moe_re_routing/op_host/moe_re_routing_re_tiling.h` | `MoeReRoutingReTiling::IsCapable` | RE完整谓词。 |
| RE tiling | `moe/moe_re_routing/op_host/moe_re_routing_re_tiling.cpp` | `SplitCore/SplitUb/PostTiling` | 二维分核、UB、blockDim。 |
| R selector | `moe/moe_re_routing/op_host/moe_re_routing_r_tiling.h` | `MoeReRoutingRTiling::IsCapable` | Regbase fallback谓词。 |
| R tiling | `moe/moe_re_routing/op_host/moe_re_routing_r_tiling.cpp` | `SplitCore/SplitUb/PostTiling` | rank分核、UB gap、blockDim。 |
| Kernel router | `moe/moe_re_routing/op_kernel/moe_re_routing_apt.cpp` | `moe_re_routing` | key、模板实例、AIC guard。 |
| RE body | `moe/moe_re_routing/op_kernel/arch35/moe_re_routing_re_regbase.h` | `MoeReRoutingReRegbase` | cell循环、搬运、index、sum、tail。 |
| R body | `moe/moe_re_routing/op_kernel/arch35/moe_re_routing_r_regbase.h` | `MoeReRoutingRRegbase` | rank循环、full/overload、bound queue。 |
| 构建接线 | `moe/moe_re_routing/op_host/config/ascend950/moe_re_routing_binary.json` | `MoeReRouting_*` entries | A5 binary dtype组合。 |

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | R/RE字段顺序和全int64布局 | Direct普通struct必须与对应body一致；inactive字段仍保留 | `MoeReRoutingReTilingData/MoeReRoutingRTilingData`。 |
| 调用顺序 | zero(optional)→Init→Process→expert sum | 无scale清零必须在返回前完成；单Kernel stream不变 | 派生entry；官方 `InitAndProcess`。 |
| workspace/内存 | 两个depth2 queue、无workspace | q/qi、32B alignment、depth系数、hasScale拼接偏移 | 各body `Init/CopyIn/CopyOut`。 |
| 同步 | queue生命周期与核内PIPE_ALL | Free前不得复用；PIPE_ALL不提供跨核同步 | `EnQue/DeQue/FreeTensor`；派生清零。 |
| 精度与尾块 | 位模式搬运、I dtype列和、int32 index | 不得加入cast；保留rank/expert/UB/256尾块 | `ProcessTokenScale/CopyOutIndex/CalcExpertTokenNum`。 |
| 失败边界 | wrapper限制Direct子集，Route按优先级fallback | 不绕过dtype/shape/属性检查，不接受非法counts | 官方 `CheckParam` 与派生Meta/selector边界。 |
