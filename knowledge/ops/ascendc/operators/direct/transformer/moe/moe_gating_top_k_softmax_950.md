---
type: Operator
title: "MoeGatingTopKSoftmax 950 Direct Invoke 算子知识"
description: "说明 calc_moe_gating_top_k_softmax_tiling 与三个 dtype 直调 launcher 在 950 上的接口语义、参数生成、四条 Route、单 AIV Kernel 启动图与 RegBase 实现。"
tags: [task.implementation, task.lookup, topic.data_movement, topic.memory, topic.precision, topic.programming_model]
status: stable
sources:
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_gating_top_k_softmax/op_kernel/moe_gating_top_k_softmax_apt.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_gating_top_k_softmax/op_kernel/arch35/moe_gating_top_k_softmax_tiling_def.h
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_gating_top_k_softmax/op_kernel/arch35/moe_gating_top_k_softmax_fullload_generalized_regbase.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_gating_top_k_softmax/op_host/moe_gating_top_k_softmax_tiling_arch35.cpp
    role: implementation
created_at: "2026-08-25T19:39:15Z"
updated_at: '2026-08-27T12:23:11Z'
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# MoeGatingTopKSoftmax 950 Direct Invoke 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | `calc_moe_gating_top_k_softmax_tiling`；`launch_moe_gating_top_k_softmax_{float,half,bfloat16}`，Direct Invoke |
| 计算语义 | 对最后一维专家 logits 做稳定 softmax，再按行取 top-k；同时给出 expert index 和展平 row index |
| 输入输出 | `x:[R,E]` 或把更高维前缀展平为 `R`，`finished:[R]` 可选；`y/expertIdx/rowIdx:[R,k]` |
| 执行类型 | 单 Kernel：`AIV_VECTOR`；entry 在 `AIC` 上立即返回 |
| Kernel 路线 | P0 R-001 无 finished/对齐；P1 R-002 有 finished/对齐；P2 R-003 无 finished/补齐；P3 R-004 有 finished/补齐 |
| 核心资源 | GM、5 个 depth=1 `TQue`、4 个 `TBuf`、MicroAPI 寄存器；Direct Invoke 不分配 workspace |
| 来源闭包 | `direct_implementation_closed`：官方 950 Host tiling、15 字段 POD、四 key router、RegBase Device body 已闭合；Direct 胶水只显式化 dtype/key launcher、平台查询并去掉未消费的保留 workspace |
| 验证状态 | 已完成源码闭包检查；本次知识提取未执行编译、真机、数值或性能测试。 |

## 接口与语义

### 计算语义

令输入展平为 `x[r,e]`，`0<=r<R`、`0<=e<E`。Device 对每行先在 FP32 中计算：

```text
m[r] = max_e x[r,e]
p[r,e] = exp(float(x[r,e]) - m[r]) / sum_j exp(float(x[r,j]) - m[r])
(y[r,t], expertIdx[r,t]) = 第 t 个降序 top-k (p[r,:], expert id)
```

`float16`/`bfloat16` 输入在加载后转 FP32；softmax、排序值和归约保持 FP32，写 `y` 时再以 `CAST_RINT` 降回输入 dtype。`float32` 不发生边界 cast。`E` 非 32 倍数时，补齐 lane 在求和和排序前被写成 `0.0f`，不参与有效 top-k。

`rowIdx` 由 `ArithProgression(rowIdxBase, 0, rows, k)` 生成基础序列，再加当前展平行号 `blockIdx*perCoreRowCount + loop*perLoopRowCount + j`；Direct 调用者必须保持该输出布局，不能把它改写为普通的逐行 `[r,r,...]` 假设。若传入 `finished[r]=true`，`y` 不变，所选 expert index 通过 `max(index, E)` 变为哨兵 `E`。

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| `x` | 连续，最后一维为 `E`；Direct 胶水接受 2D/3D 并展平前缀为 `R` | `float16`/`bfloat16`/`float32` | `R>0`，`1<=E<=2048` |
| `finished` | 可选连续 `[R]`，对应 `x` 的前缀 shape | `bool` | 缺省为空；存在时选择 `hasFinished=true` 模板，并把该行 expert index 置为 `E` 哨兵 |
| `k` | Host 标量 | `int64` | `1<=k<=min(E,1024)` |
| `y` | 与 `x` 相同前缀，末维为 `k` | 与 `x` 相同 | top-k softmax 值 |
| `expertIdx` | 与 `y` 相同 | `int32` | top-k expert id；finished 行为哨兵 `E` |
| `rowIdx` | 与 `y` 相同 | `int32` | Device 生成的展平 row 索引布局 |

### 入口与版本

固定版本为 CANN 9.1.0、950/Ascend 950。官方固定提交没有同名的 Direct Invoke launcher 文件；转换从 `moe_gating_top_k_softmax` 官方 entry、`MoeGatingTopKSoftmaxRegbaseTilingData`、`MoeGatingTopKSoftmaxRegbaseTiling` 和 `MoeGatingTopKSoftmaxFullloadGenerlized` 派生：

- 官方宏解析的 tiling POD 被等字段、等顺序的普通 POD 替代；
- 官方 `DTYPE_X × 4 key` router 被展开为 `3 dtype × 4 bool specialization` 的 12 个显式 entry，再由三个 dtype launcher 选择；
- `gert` 平台信息改由 `PlatformAscendCManager` 提供 AIV 数和 UB 字节数；
- 官方 Host 预留 16 MiB workspace，但官方 `Init/Process` 不读取 `workspace`，因此 Direct Invoke 的参数和启动图中没有 workspace。

除把两个跨目录公共 include 换成其命中符号的局部闭包外，官方 Kernel 类及成员函数保持字节一致；Host 的分核、UB row split、`E/k` 对齐、padding 和 key 公式保持同一运算顺序。

这是源码派生边界，不把 Direct Invoke 伪装成公开 ACLNN/API。

## Host/Launcher 执行流程

### 参数校验与前处理

1. 调用侧检查 `x` 为连续 2D/3D 且 dtype 为 FP16/BF16/FP32；检查 `finished`（若有）为同设备、连续 bool，shape 等于 `x.shape[:-1]`。
2. 取 `E=x.size(-1)`、`R=x.numel()/E`，检查 `R>0`、`1<=E<=2048`、`1<=k<=min(E,1024)`。
3. 为三个输出建立 `x.shape[:-1]+[k]` 的连续 GM 张量。
4. `calc_moe_gating_top_k_softmax_tiling(R,E,k,hasFinished,&params)` 查询 `aivNum` 和 `ubSize`；空 `params`、非法 shape、平台句柄为空、`aivNum<=0`、`ubSize==0` 或 UB 放不下一行时返回 `false`。
5. 从当前 NPU stream 取裸 stream；按 `x` dtype 调用对应 launcher。launcher 再按 `tilingKey` 选择 bool specialization。

### 参数、Workspace 与生命周期

```text
C = AIV core 数
A = align_up(E, 32)
K8 = align_up(k, 8)
perCore = ceil_div(R, C)
blockDim = needCore = ceil_div(R, perCore) = min(R,C)
lastCore = R - (needCore-1)*perCore
```

Host 的 UB 保守计账为：

```text
rowBytes = (4*A + 32) + 12*K8 + 12*A + 16*A
fixedBytes = 8*A
maxRowsInUb = floor((ubSize - fixedBytes) / rowBytes)
```

随后对普通 core 的 `perCore` 与尾 core 的 `lastCore` 分别执行：

```text
loopCount = ceil_div(coreRows, maxRowsInUb)
perLoopRows = ceil_div(coreRows, loopCount)
lastLoopRows = coreRows - (loopCount-1)*perLoopRows
```

`params` 由 120 字节 tiling POD、8 字节 `tilingKey`、8 字节 `blockDim` 组成。它在 Host 栈上生成，launcher 在入队前按值复制 tiling POD给 Kernel 参数。输入、输出由调用者持有并至少存活到 stream 完成；`TPipe` 和所有 UB 资源只在单次 Kernel block 生命周期内有效。`workspace_total=0`。

### 启动图与失败传播

```text
Direct caller
  -> calc_moe_gating_top_k_softmax_tiling
  -> dtype launcher(params, stream)
     -> 单个 AIV entry<<<blockDim, nullptr, stream>>>(x, finished, y, expertIdx, rowIdx, tilingData)
        -> op.Init(...)
        -> op.Process()
```

| 节点/边 | entry/介质 | 范围与布局 | ordering / owner / lifetime | 失败传播 |
|---|---|---|---|---|
| Host tiling | `calc_moe_gating_top_k_softmax_tiling` | 生产 key、`blockDim`、15 字段 POD | Host 同步完成后才 launch；调用者持有 `params` | `false` 阻断 launch |
| Kernel K0 | 12 个 dtype/bool/pad 显式 entry 之一 | 单 AIV Kernel；每个 block 覆盖连续 row 段 | 当前 stream 入队；GM 由调用者、UB 由 K0 持有 | direct wrapper 无 Device 返回码；launch/runtime 错误由上层运行时处理 |
| K0 输出边 | `y/expertIdx/rowIdx` GM | 均为 `[R,k]` 连续布局 | 同一 Kernel 内 Queue→GM；stream 完成后可消费/释放 | 无后继 Kernel |
| workspace | N/A | Direct Invoke 没有中间 slice | N/A | N/A |

## Route 与参数设计

### 分核与资源计算

四条 Route 共用相同分核和行切片公式。`GetBlockIdx()` 决定 core；最后一个 block 读 `lastCore*` 字段，其余 block 读 `perCore*` 字段。GM row 基址分别是 `blockIdx*perCoreRowCount*E` 和 `blockIdx*perCoreRowCount*k`。每次循环的有效 `rowCount` 是普通 loop 的 `perLoopRowCount` 或最后 loop 的 `lastLoopRowCount`。

Host 按 FP32 最坏输入容量计账，故 FP16/BF16 的 `xInQueue` 实际字节更少。所有 TQue depth 都是 1；Kernel 没有 double buffer，也没有跨 Kernel workspace。

### Route 选择

P0→P3 只规定本卡的阅读顺序，不参与 tiling 或 launcher 判定；`Host顺序` 严格对应 Direct 源码的实际分支次序。

| Host顺序 | 重要性 | Route | 特征 | 适用域 | 实现前提 | Key/模板 | Host 真实选择、短路与 fallback |
|---:|---|---|---|---|---|---|---|
| 1 | P0 | R-001 无 finished/对齐 | 最短数据路：不搬 `finished`，不清 pad lane | `finished` 缺省，`E%32==0`；三种输入 dtype | calculator 生成合法 POD；`A=E`；实例化 `<T,false,false>` | `100000`；`<T,false,false>` | launcher 首个 `if` 命中后短路；未命中进入顺序 2 |
| 2 | P1 | R-002 有 finished/对齐 | 在 P0 上增加 bool 搬运与 expert 哨兵合并 | `finished` 存在且 shape/dtype 合法，`E%32==0` | `finished` GM 有效；实例化 `<T,true,false>` | `100001`；`<T,true,false>` | 第一个 `else if` 命中后短路；未命中进入顺序 3 |
| 3 | P2 | R-003 无 finished/补齐 | 不搬 `finished`，但对 softmax 尾 lane 清零 | `finished` 缺省，`E%32!=0` | `A=align_up(E,32)`；pad mask 精确覆盖 `[E,A)`；实例化 `<T,false,true>` | `100010`；`<T,false,true>` | 第二个 `else if` 命中后短路；未命中进入顺序 4 |
| 4 | P3 | R-004 有 finished/补齐 | 同时启用 bool 哨兵与 pad lane 处理 | `finished` 存在，`E%32!=0` | 同时满足 P1 的 finished GM 前提和 P2 的 pad 前提；实例化 `<T,true,true>` | `100011`；`<T,true,true>` | wrapper 最终 `else`；合法 key `100011` 命中本 Route，任何未知手工 key 也会落入该 fallback |

```text
校验失败 -> 返回 false，阻断 launch
key = 100000
if hasFinished: key += 1                  # 独立判断，不短路下一判断
if E % 32 != 0: key += 10                 # 独立判断

if dtype == float32:
  float launcher
else if dtype == float16:
  half launcher
else:
  bfloat16 launcher                       # dtype 已在入口校验

launcher 内：
if key == 100000: R-001，短路返回该 entry
else if key == 100001: R-002，短路返回该 entry
else if key == 100010: R-003，短路返回该 entry
else: R-004 entry                         # key 100011 的合法终点，也是未知 key fallback
```

### 模板/实现执行矩阵

| 重要性 | Route | key/selector | dtype/shape/platform 完整命中条件 | 执行拓扑与 Kernel 节点 | 实际模板/body | 内存与同步特征 | tail/fallback |
|---|---|---|---|---|---|---|---|
| P0 | R-001 | `100000` | `T∈{float,half,bfloat16}`，无 finished，`E%32==0`，950 | K0 单 AIV | `MoeGatingTopKSoftmaxFullloadGenerlized<T,false,false>::Process` | finished Queue 分配但不读；Queue 同步 | E 无 pad；row/k 用 mask 与 `lastLoopKCount`；未命中按 Host顺序进入 R-002 |
| P1 | R-002 | `100001` | 同上但有 finished | K0 单 AIV | `<T,true,false>` | finished GM→Queue→寄存器；索引取 `max(idx,finished*E)` | E 无 pad；未命中进入 R-003 |
| P2 | R-003 | `100010` | 无 finished，`E%32!=0` | K0 单 AIV | `<T,false,true>` | 对齐 lane 在 softmax UB 清零 | `DataCopyPad` + pad mask；未命中进入最终 `else` |
| P3 | R-004 | `100011` | 有 finished，`E%32!=0` | K0 单 AIV | `<T,true,true>` | R-002 与 R-003 的编译期路径同时启用 | finished 哨兵 + pad mask；同时承接未知 key fallback |

每一行内部有 float/half/bfloat16 三个编译实例；Route key 和数据流不因 dtype 改变，差异仅在 GM↔FP32 的编译期 load/store cast。

### 隐藏性能 Guard

| Guard | Host/Tiling 条件 | Device/资源原因 | 影响 Route | 不满足时去向 | 源码符号 |
|---|---|---|---|---|---|
| 950 RegBase | 官方 `IsRegbaseSocVersion(context_)`；Direct 平台需返回 AIV/UB | body 使用 `__VEC_SCOPE__`、MicroAPI 与 RegTensor | 全部 | Host 失败，不 launch | `MoeGatingTopKSoftmaxRegbaseTiling::IsCapable`；`calc_moe_gating_top_k_softmax_tiling` |
| expert 上限 | `0<E<=2048` | Host 明确限制，排序 repeat 与 UB 随 E 增长 | 全部 | `false` | `DoOpTiling`；direct tiling calculator |
| UB 至少一行 | `ubSize > 8*A` 且 `maxRowsInUb>0` | 5 Queue、4 TBuf 必须同时初始化 | 全部 | `false` | `CalcMaxRowCountInUb`；`SplitRowInUb` |
| E 的 32 对齐 | `E%32==0` / `!=0` | `Sort32`/`Sort` 消费 `A=align_up(E,32)` | R-001/2 vs R-003/4 | 切 padding Route | `GetTilingKey`；`ComputeSoftmax` |
| 单 repeat sort | `A==32` | 可用 `Sort32`；更大 A 按行调用通用 `Sort` | 全部内部子支 | `A>32` 用通用 Sort | `ComputeTopK` |
| top1 reduce | `k==1 && E<=8 && A==32` | `ReduceMax` 直接产生 value/index，跳过完整排序 | 全部内部子支 | `Sort32` | `HandleOneRepeatSortNum` |
| k tail | `k % B32_VF_COUNT` | unaligned store 只提交有效 top-k | 全部 | `lastLoopKCount=B32_VF_COUNT`（整除）或余数 | `ComputeTopK` |
| core type | `g_coreType != AIC` | 算子仅有 AIV body | 全部 | AIC 立即返回 | 官方 entry 与 Direct entry body |
| launcher key | 只接受 tiling calculator 生成的四 key | direct wrapper 最后 `else` 会落入 finished+pad entry | 全部 | 禁止手工构造未知 key | dtype launcher wrapper |

### POD/ABI

`MoeGatingTopKSoftmaxRegbaseTilingData` 是 15 个连续 `int64_t`：`sizeof=120`、`alignof=8`。Direct 普通 POD 保持官方字段名、类型与顺序。

| 结构 | 字段 | 类型/位宽 | ABI 布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| tiling POD | `rows` | `int64_t/64` | offset 0 | row | `rows=R` | `InitIndices` 的 progression | `R>0` |
| tiling POD | `perCoreRowCount` | `int64_t/64` | offset 8 | row/core | `ceil_div(R,C)` | `Init` 普通 core 与 GM 基址 | 正数 |
| tiling POD | `lastCoreRowCount` | `int64_t/64` | offset 16 | row | `R-(needCore-1)*perCore` | 最后 block 的 `Init` | 正数 |
| tiling POD | `perCoreLoopCount` | `int64_t/64` | offset 24 | loop | `SplitRowInUb(perCore)` | 普通 block 的 `Process` 循环 | >=1 |
| tiling POD | `lastCoreLoopCount` | `int64_t/64` | offset 32 | loop | `SplitRowInUb(lastCore)` | 最后 block 的循环 | >=1 |
| tiling POD | `perCorePerLoopRowCount` | `int64_t/64` | offset 40 | row/loop | 普通 core `ceil_div(coreRows,loops)` | 普通 block UB 容量与 loop | <=maxRowsInUb |
| tiling POD | `perCoreLastLoopRowCount` | `int64_t/64` | offset 48 | row | 普通 core 尾式 | 普通 block 最后 loop | 1..perLoop |
| tiling POD | `lastCorePerLoopRowCount` | `int64_t/64` | offset 56 | row/loop | 尾 core split | 最后 block UB 容量与 loop | <=maxRowsInUb |
| tiling POD | `lastCoreLastLoopRowCount` | `int64_t/64` | offset 64 | row | 尾 core 尾式 | 最后 block 最后 loop | 1..perLoop |
| tiling POD | `expertCount` | `int64_t/64` | offset 72 | element/row | `E` | GM stride、mask、finished 哨兵 | 1..2048 |
| tiling POD | `k` | `int64_t/64` | offset 80 | element/row | Host 属性 | output stride、mask、top1 guard | 1..min(E,1024) |
| tiling POD | `expertCountAlign` | `int64_t/64` | offset 88 | FP32 element/row | `align_up(E,32)` | UB stride、Sort/Sort32 | 32 对齐 |
| tiling POD | `kAlign` | `int64_t/64` | offset 96 | FP32/int32 element/row | `align_up(k,8)` | output Queue stride | 8 对齐 |
| tiling POD | `padNegInfCount` | `int64_t/64` | offset 104 | element | `E%32` | padding mask 和 key | 0..31 |
| tiling POD | `sortRepeatTimes` | `int64_t/64` | offset 112 | 32-element repeat | `A/32` | 通用 `Sort<float,true>` | 1..64 |
| launch params | `tiling` | nested POD | offset 0；size 120 | bytes/POD | direct tiling calculator | launcher 按值复制给 entry | 生命周期覆盖 launch 调用 |
| launch params | `tilingKey` | `uint64_t/64` | offset 120 | key | `100000+[finished]+10*[pad]` | dtype launcher | 仅四合法值 |
| launch params | `blockDim` | `int64_t/64` | offset 128；struct size 136 | AIV block | `needCoreNum` | launch grid | 转 `uint32_t` 前必须为正且可表示 |

### Route 源码闭包

| 重要性 | Route | Key/selector | Host/Tiling producer | POD/参数 | Kernel entry/router 节点 | Kernel body/直接依赖 | 构建接线 |
|---|---|---|---|---|---|---|---|
| P0 | R-001 | `100000` | `DoOpTiling/GetTilingKey/PostTiling` → direct calculator | 15 字段 POD，`false,false` | 官方 key branch → direct `*_nf_np` | `MoeGatingTopKSoftmaxFullloadGenerlized<T,false,false>`；load/store helper | 官方 APT entry；Direct `register_direct_launch_op` 派生胶水 |
| P1 | R-002 | `100001` | 同上，`hasFinished=true` | 同 POD，`true,false` | 官方 key branch → direct `*_f_np` | `<T,true,false>` | 同上 |
| P2 | R-003 | `100010` | 同上，`padNegInfCount>0` | 同 POD，`false,true` | 官方 key branch → direct `*_nf_p` | `<T,false,true>` | 同上 |
| P3 | R-004 | `100011` | 两条件都成立 | 同 POD，`true,true` | 官方 key branch → direct `*_f_p` | `<T,true,true>` | 同上 |

## Kernel 实现

### 公共执行流程

四条 Route 都是单 AIV Kernel：`Init` 解析 POD、绑定每核 GM 区间并一次性初始化 Queue/TBuf；`Process` 先用 `InitIndices` 建 expert/row 基础索引，然后逐 UB row tile 严格执行：

```text
ComputeRowIdx -> CopyOutRowIdx -> CopyInX[/finished]
-> ComputeSoftmax(max, exp, ReduceSum, div)
-> ComputeTopK(Sort/Sort32/ReduceMax, finished sentinel)
-> CopyYExpertIdxOut
```

Queue 的 `AllocTensor/EnQue/DeQue/FreeTensor` 提供阶段可见性和 depth=1 复用顺序。softmax 和排序在同一个 Kernel 内通过 TBuf 交接；没有跨 Kernel GM/workspace 边。

### Route R-001（P0）：无 finished、E 对齐

#### 适用条件

| 项目 | 内容 |
|---|---|
| 特征 | 最短数据路；`finished` 物理 Queue 保留，但模板不搬运、不读取；E 无 pad 清零 |
| 适用域 | `finished` 缺省，`E%32==0`，`T∈{float,half,bfloat16}` |
| 实现前提 | calculator 生成 key `100000` 与合法 POD；launcher 首个分支命中 `<T,false,false>` |

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host/Tiling | `op_host/moe_gating_top_k_softmax_tiling_arch35.cpp` | `GetTilingKey` | `!hasFinished && padNegInfCount_==0` | `100000` |
| Router | `op_kernel/moe_gating_top_k_softmax_apt.cpp` | `moe_gating_top_k_softmax` | key `100000` | `<DTYPE_X,false,false>` |
| Direct launcher | 派生 launcher | `launch_moe_gating_top_k_softmax_{dtype}` | key `100000` | `moe_gating_{dtype}_nf_np` |

#### Device 数据流

##### 函数级调用链

```text
dtype launcher -> *_nf_np(x,null,y,expertIdx,rowIdx,tilingData)
  -> MoeGatingTopKSoftmaxFullloadGenerlized<T,false,false>::Init
  -> Process
     -> InitIndices
     -> [loop] ComputeRowIdx -> CopyOutRowIdx
     -> CopyInX -> ComputeSoftmax -> ComputeTopK -> CopyYExpertIdxOut
```

##### 源码等价伪码

```text
coreBase = blockIdx * perCoreRowCount
for loop in [0, coreLoopCount):
  n = (last loop) ? lastLoopRows : perLoopRows
  rowIdxUB[j,t] = progression[t] + coreBase + loop*perLoopRows + j
  GM.rowIdx[loopBase : loopBase+n*k] <- rowIdxUB[:,0:k]
  xUB[j,0:E] <- GM.x[coreBase+loop*perLoopRows+j,:]
  for each row: max <- ReduceMax(x); expUB <- exp(float(x)-max)
  sum <- ReduceSum(expUB[0:A]); softmaxUB <- expUB/sum
  if A==32: (k==1 && E<=8 ? ReduceMax : Sort32)
  else: Sort<float,true>(repeat=A/32)
  extract first k interleaved (value,index), cast value to T if needed
  GM.y, GM.expertIdx <- contiguous valid n*k
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| `xGm` | `coreBase*E + loop*perLoopRows*E` | `n*E` | T，row-major | caller | `CopyInX` | caller/stream | DMA pad 到 A |
| `xInQueue` | UB queue | `A*sizeof(T)*Rloop` | T | `CopyInX` | `ComputeSoftmax` | TPipe/一次 loop | depth 1 |
| `finishedInQueue` | UB queue | `32*Rloop` | bool block | 未写 | 未读 | TPipe/Kernel | 条件路径关闭但物理分配保留 |
| `softmaxBuf` | UB TBuf | `4*A*Rloop` | FP32 | `ComputeSoftmax` | `ComputeTopK` | TPipe/Kernel | exp 与归一结果原地复用 |
| `calcTmpBuf` sorted 区 | offset 0 | `8*A*Rloop` | value/index 交错 | Sort | TopK extract | TPipe/loop | 与 reduce 临时区分时复用 |
| `calcTmpBuf` sort tmp | `2*A*n` FP32 element | `16*A` bytes | FP32 scratch | Sort | Sort | TPipe/loop | 固定尾区 |
| `expertIdxBuf` | UB TBuf | `4*A*Rloop` | int32 | `InitIndices` | Sort | TPipe/Kernel | 同物理容量按 float 计 |
| `rowIdxBaseBuf` | UB TBuf | `4*A*Rloop` | int32 | `InitIndices` | `ComputeRowIdx` | TPipe/Kernel | 每 loop 只读 |
| 三个 output Queue | UB queue | 各 `4*K8*Rloop` | y 容量按 FP32，另两路 int32 | Compute | CopyOut | TPipe/loop | depth 1；仅写有效 k |

##### 分层内存布局

```mermaid
block-beta
  columns 4
  xq["xInQueue d=1 · A·sizeof(T)·Rloop"]:2
  fq["finishedInQueue d=1 · 32·Rloop"]:2
  yq["yOutQueue d=1 · 4·K8·Rloop"]:1
  eq["expertIdxOutQueue d=1 · 4·K8·Rloop"]:1
  rq["rowIdxOutQueue d=1 · 4·K8·Rloop"]:2
  ebuf["expertIdxBuf · 4·A·Rloop"]:1
  rbuf["rowIdxBaseBuf · 4·A·Rloop"]:1
  sbuf["softmaxBuf · 4·A·Rloop"]:2
  cbuf["calcTmpBuf · 8·A·Rloop + 16·A"]:4
```

##### 字节账与复用顺序

```text
UB_actual(T) = A*sizeof(T)*Rloop + 32*Rloop
             + 3*(4*K8*Rloop)
             + 3*(4*A*Rloop)
             + (8*A*Rloop + 16*A)
UB_actual(float) = Rloop*(24*A + 12*K8 + 32) + 16*A
UB_host_bound = Rloop*(32*A + 12*K8 + 32) + 8*A
UB_actual(float) <= UB_host_bound  当 Rloop>=1；Rloop=1 时相等
dynamic_ub = N/A
workspace_total = 0
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| `softmaxBuf` | max-exp 阶段写 FP32 exp | ReduceSum、Div、Sort | 下一 loop 的 Duplicate/exp | 同函数顺序；x Queue 在末尾 Free | Sort 完成后才进入下一 loop |
| `calcTmpBuf` 前区 | ReduceSum/Brcb 临时，再由 Sort 写 interleaved 结果 | Div、TopK extract | 下一 loop | 单线程程序序；Sort 完成后输出已入 Queue | sort scratch offset 不得侵入前区 |
| output Queue | Compute/TopK | CopyOut | `FreeTensor` 后下个 loop | EnQue→DeQue→FreeTensor | depth=1，不能跨 loop 提前 Alloc |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| GM→UB | `DataCopyPad` + `EnQue` | `CopyInX` | `ComputeSoftmax::DeQue` | x Queue | 每行 `blockLen=E*sizeof(T)`，dst stride 补到 A |
| softmax | MicroAPI mask、`ReduceMax/Exp/ReduceSum/Brcb/Div` | x Queue | Sort | softmax TBuf | FP16/BF16→FP32；mask 限制 E；A 对齐无 pad Route |
| top-k | `ReduceMax`/`Sort32`/`Sort<float,true>` | softmax TBuf | unaligned extract | calc TBuf | k 尾由 mask 与 `lastLoopKCount` 控制 |
| UB→GM | Queue + `DataCopyPad` | output Queue | GM | 三路输出 | y/expert 连续 `n*k`；rowIdx 逐行去 K8 pad |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `op_host/moe_gating_top_k_softmax_tiling_arch35.cpp` | `DoOpTiling/CalcMaxRowCountInUb/SplitRowInUb/PostTiling` | core、UB row tile、key、POD |
| Kernel entry/router | `op_kernel/moe_gating_top_k_softmax_apt.cpp` | `moe_gating_top_k_softmax` | key 100000 到 `<DTYPE_X,false,false>` |
| Device body/helper | `op_kernel/arch35/moe_gating_top_k_softmax_fullload_generalized_regbase.h` | `Init/Process/ComputeSoftmax/ComputeTopK` | GM/UB、FP32 softmax、sort、tail |

### Route R-002（P1）：有 finished、E 对齐

#### 适用条件

| 项目 | 内容 |
|---|---|
| 特征 | 在对齐主路上增加 bool GM→UB 和 expert index 哨兵合并 |
| 适用域 | `finished` 存在且合法，`E%32==0`，`T∈{float,half,bfloat16}` |
| 实现前提 | `finished` GM 在 stream 生命周期内有效；key `100001`；实例化 `<T,true,false>` |

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host/Tiling | `op_host/moe_gating_top_k_softmax_tiling_arch35.cpp` | `GetTilingKey` | `hasFinished && padNegInfCount_==0` | `100001` |
| Router | `op_kernel/moe_gating_top_k_softmax_apt.cpp` | `moe_gating_top_k_softmax` | key `100001` | `<DTYPE_X,true,false>` |
| Direct launcher | 派生 launcher | dtype wrapper | key `100001` | `*_f_np` |

#### Device 数据流

##### 函数级调用链

```text
dtype launcher -> *_f_np -> Init -> Process
  -> CopyInX(x,finished) -> ComputeSoftmax -> ComputeTopK
     -> DeQue finished -> cast bool to int32 -> broadcast -> finished*E
     -> expertIdx=max(sortedIndex, finished*E)
  -> CopyYExpertIdxOut
```

##### 源码等价伪码

```text
执行 R-001 的全部步骤；另对每行读取 finished[r]
sentinel = int32(finished[r]) * E
for t in 0:k: expertIdx[r,t] = max(sortedExpertIdx[r,t], sentinel)
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| R-001 全部资源 | 同 R-001 | 同 R-001 | 同 R-001 | 同 R-001 | 同 R-001 | 同 R-001 | 同 R-001 |
| `finishedGm` | `coreBase+loop*perLoopRows` | `n` | bool | caller | `CopyInX` | caller/stream | 每行 1 byte |
| `finishedInQueue` | UB queue | `32*Rloop` | bool，每行占 32-byte block | `CopyInX` | `ComputeTopK` | TPipe/loop | depth=1；EnQue/DeQue/Free |

##### 分层内存布局

```mermaid
block-beta
  columns 4
  base["R-001 全部 UB 子区"]:3
  finished["finishedInQueue d=1 · 32·Rloop"]:1
```

##### 字节账与复用顺序

```text
UB_total 与 R-001 相同；区别是 finishedInQueue 从“只分配”变为实际搬运和消费
workspace_total = 0
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| `finishedInQueue` | `CopyInX` | `ComputeTopK` | Free 后下一 loop | EnQue→DeQue→FreeTensor | 必须在 expert index 生成后才能释放 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| finished copy | `DataCopyPad` + Queue | GM | TopK DeQue | bool row | 每行 1 byte，UB 行跨度 32 bytes |
| sentinel | `Cast/Duplicate/Muls/Max` | finished Queue | expert output | index RegTensor | false 保持 `[0,E)`；true 变为 E |
| 其余 | 同 R-001 | 同 R-001 | 同 R-001 | 同 R-001 | E 对齐，无 pad |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `op_host/moe_gating_top_k_softmax_tiling_arch35.cpp` | `GetTilingKey` | finished 使 key `+1` |
| Kernel entry/router | `op_kernel/moe_gating_top_k_softmax_apt.cpp` | `<DTYPE_X,true,false>` | 启用 finished 编译分支 |
| Device body/helper | `op_kernel/arch35/moe_gating_top_k_softmax_fullload_generalized_regbase.h` | `CopyInX/ComputeTopK` | bool Queue 与 E 哨兵 |

### Route R-003（P2）：无 finished、E 补齐

#### 适用条件

| 项目 | 内容 |
|---|---|
| 特征 | 无 bool 输入搬运；softmax 尾段的无效 FP32 lane 在归约和排序前清零 |
| 适用域 | `finished` 缺省，`E%32!=0`，`T∈{float,half,bfloat16}` |
| 实现前提 | `A=align_up(E,32)`；key `100010`；pad mask 覆盖 `[E,A)`；实例化 `<T,false,true>` |

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host/Tiling | `op_host/moe_gating_top_k_softmax_tiling_arch35.cpp` | `GetTilingKey` | `!hasFinished && padNegInfCount_>0` | `100010` |
| Router | `op_kernel/moe_gating_top_k_softmax_apt.cpp` | router | key `100010` | `<DTYPE_X,false,true>` |
| Direct launcher | 派生 launcher | dtype wrapper | key `100010` | `*_nf_p` |

#### Device 数据流

##### 函数级调用链

```text
dtype launcher -> *_nf_p -> Init -> Process
  -> CopyInX(DataCopyPad to A)
  -> ComputeSoftmax(exp valid E -> Duplicate padded exp lanes to 0 -> ReduceSum/Div)
  -> ComputeTopK -> CopyOut
```

##### 源码等价伪码

```text
A = align_up(E,32); rem=E%32
执行有效 E lane 的 stable exp
从 duplicateIndex=E-rem 起，用构造 mask 将当前 32-lane 尾段中超出 E 的 lane 清 0
对完整 A 做 ReduceSum 和 Sort；零 pad 不改变 softmax 分母，且不进入正 softmax 的有效 top-k
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| R-001 全部资源 | 同 R-001，A 大于 E | 同公式 | 同 R-001 | 同 R-001 | 同 R-001 | 同 R-001 | GM→UB 每行补到 A |
| `softmaxBuf` 尾 lane | `row*A + E .. row*A+A-1` | `A-E` | FP32 | `Duplicate(0)` | ReduceSum/Sort | 当前 loop | mask 只覆盖 pad lane |

##### 分层内存布局

```mermaid
block-beta
  columns 4
  valid["softmaxBuf valid · E FP32/row"]:3
  pad["softmaxBuf pad · (A-E) FP32/row = 0"]:1
  other["其余 UB 子区同 R-001"]:4
```

##### 字节账与复用顺序

```text
UB_total 仍使用 A=align_up(E,32) 代入 R-001 公式
workspace_total = 0
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| softmax pad lane | Duplicate 0 | ReduceSum、Sort | 下一 loop | 同函数顺序 | mask 必须精确覆盖 `[E,A)` |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| input tail | `DataCopyPad` | GM x | softmax | x UB 尾块 | 有效 E，物理 A |
| exp tail | masked `Duplicate(0.0f)` | exp 结果 | ReduceSum/Sort | `[E,A)` | pad 不计入分母/候选 |
| 其余 | 同 R-001 | 同 R-001 | 同 R-001 | 同 R-001 | k/row tail 同 R-001 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `op_host/moe_gating_top_k_softmax_tiling_arch35.cpp` | `DoOpTiling/GetTilingKey` | `A=align_up(E,32)`，非零余数使 key `+10` |
| Kernel entry/router | `op_kernel/moe_gating_top_k_softmax_apt.cpp` | `<DTYPE_X,false,true>` | 启用 pad 编译分支 |
| Device body/helper | `op_kernel/arch35/moe_gating_top_k_softmax_fullload_generalized_regbase.h` | `ComputeSoftmax` | pad mask 与零填充 |

### Route R-004（P3）：有 finished、E 补齐

#### 适用条件

| 项目 | 内容 |
|---|---|
| 特征 | 同时启用 bool 哨兵和 E 尾 lane 清零；是 launcher 的最终 `else` 目标 |
| 适用域 | 合法调用为 `finished` 存在且 `E%32!=0`；未知手工 key 也会被 wrapper 导向此 entry |
| 实现前提 | key 应由 calculator 生成 `100011`；同时满足 P1 的 finished GM 和 P2 的 pad mask 前提；实例化 `<T,true,true>` |

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host/Tiling | `op_host/moe_gating_top_k_softmax_tiling_arch35.cpp` | `GetTilingKey` | `hasFinished && padNegInfCount_>0` | `100011` |
| Router | `op_kernel/moe_gating_top_k_softmax_apt.cpp` | router | key `100011` | `<DTYPE_X,true,true>` |
| Direct launcher | 派生 launcher | dtype wrapper | key `100011` 或 wrapper 非法 key 尾分支 | `*_f_p`；后者不是 Host 可达 Route |

#### Device 数据流

##### 函数级调用链

```text
dtype launcher -> *_f_p -> Init -> Process
  -> CopyInX(x,finished) -> ComputeSoftmax(pad lane=0)
  -> ComputeTopK(finished index sentinel) -> CopyOut
```

##### 源码等价伪码

```text
先执行 R-003 的 E 尾 lane 清零和 softmax/top-k；
再执行 R-002 的 finished*E 哨兵合并；
y 与 rowIdx 不因 finished 改变。
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| 全部 UB/GM | R-002 finished 边 + R-003 pad 边 | R-001 字节公式，A 对齐 | T/FP32/bool/int32 | 对应阶段 | 对应阶段 | 单 Kernel | 两个编译期条件同时启用 |

##### 分层内存布局

```mermaid
block-beta
  columns 4
  base["R-001 基础 UB"]:2
  finished["finished Queue · 32·Rloop"]:1
  pad["softmax pad · 4·(A-E)·Rloop"]:1
```

##### 字节账与复用顺序

```text
UB_total = R-001 公式；finished Queue 已包含在公式中，pad 已包含在 A 中
workspace_total = 0
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| finished Queue | `CopyInX` | `ComputeTopK` | Free 后下一 loop | Queue 协议 | 同 R-002 |
| softmax pad lane | `ComputeSoftmax::Duplicate` | ReduceSum/Sort | 下一 loop | 程序序 | 同 R-003 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| x/finished ingress | 两个 depth=1 Queue | GM | softmax/top-k | 两路输入 | E pad 与 bool 行 stride 独立 |
| pad + sentinel | masked zero；`Cast/Muls/Max` | softmax/finished | Sort/output | FP32 lane/int32 index | y 按有效 E 归一；finished index=E |
| output | Queue→GM | compute | caller | 三路输出 | k/row tail 同 R-001 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | `op_host/moe_gating_top_k_softmax_tiling_arch35.cpp` | `GetTilingKey` | 两个 key 增量叠加为 100011 |
| Kernel entry/router | `op_kernel/moe_gating_top_k_softmax_apt.cpp` | `<DTYPE_X,true,true>` | 两个编译期条件同时启用 |
| Device body/helper | `op_kernel/arch35/moe_gating_top_k_softmax_fullload_generalized_regbase.h` | `CopyInX/ComputeSoftmax/ComputeTopK` | finished、padding、sort、output 完整闭环 |

## 算子特定优化

### Trick T-001：FP32 稳定 softmax 与 UB 原地复用

#### 触发与源码依据

- 适用 Route：P0 R-001～P3 R-004，所有 dtype。
- 触发条件：每个有效 row tile；FP16/BF16 由 `LoadOneTensorForDtypeT` 升到 FP32。
- Golden 来源：[`moe_gating_top_k_softmax_fullload_generalized_regbase.h:272-281`](https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_gating_top_k_softmax/op_kernel/arch35/moe_gating_top_k_softmax_fullload_generalized_regbase.h)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
AscendC::MicroAPI::ReduceMax(reduceVreg, reduceMidRreg, mask);
AscendC::MicroAPI::Duplicate(dupVreg, reduceVreg, mask);
for (uint16_t j = 0; j < expertCountLoops; j++) {
    offset = rowLoopsOffset + j * repeatCount;
    ops::LoadOneTensorForDtypeT<T>(xTensorAddr, vreg0, mask, offset);
    AscendC::MicroAPI::Sub(vreg0, vreg0, dupVreg, mask);
    AscendC::MicroAPI::Exp(vreg0, vreg0, mask);
    AscendC::MicroAPI::DataCopy(xTensorFp32Addr + offset, vreg0, mask);
    mask = AscendC::MicroAPI::UpdateMask<int32_t>(remain);
}
```

#### 机制与设计原因

先求每行最大值再做 `exp(x-max)`，避免直接指数化的溢出；exp 直接写 `softmaxBuf`，后续 `Div` 又原地覆盖同一 TBuf，省去第二个整行 FP32 中间张量。MicroAPI mask 来自当前有效 E，repeat 来自 `B32_VF_COUNT=VRegBytes/4`。

#### 迁移边界

- 适用：最后一维独立 softmax，且整行或分段 row tile 能驻留 UB。
- 前提：950 RegBase、FP32 exp/reduce/div；保持 max、exp、sum、div 顺序。
- 失效：若 E/UB 超出本 Host 计账上界或平台不是 RegBase，当前 Direct tiling 返回失败，不能静默切到该 body。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓未提供可验证反例；迁移时不得删去减最大值或让 pad lane 进入 ReduceSum。

### Trick T-002：单 repeat 的 top1 归约捷径

#### 触发与源码依据

- 适用 Route：P0 R-001～P3 R-004 的内部子支。
- 触发条件：`expertCountAlign==32 && k==1 && expertCount<=8`。
- Golden 来源：[`moe_gating_top_k_softmax_fullload_generalized_regbase.h:335-357`](https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_gating_top_k_softmax/op_kernel/arch35/moe_gating_top_k_softmax_fullload_generalized_regbase.h)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
if (k_ == 1 && expertCount_ <= B32_BLOCK_COUNT) {
    __VEC_SCOPE__ {
        __local_mem__ float *softmaxTensorAddr = (__local_mem__ float *)softmaxTensor.GetPhyAddr();
        __local_mem__ float *sortedTensorAddr = (__local_mem__ float *)sortedTensor.GetPhyAddr();
        AscendC::MicroAPI::RegTensor<float> valueAndIndexReg;
        AscendC::MicroAPI::MaskReg maskForValueAndIndex = AscendC::MicroAPI::CreateMask<uint32_t, AscendC::MicroAPI::MaskPattern::VL2>();
        AscendC::MicroAPI::MaskReg maskForExpertCount;
        uint32_t uint32ExpertCount_ = static_cast<uint32_t>(expertCount_);
        int64_t kvExpertCountAlign_ = expertCountAlign_ * KEY_VALUE_FACTOR;


        for (uint16_t i = 0; i < static_cast<uint16_t>(rowCount); i++) {
            AscendC::MicroAPI::DataCopy(valueAndIndexReg, softmaxTensorAddr + i * expertCountAlign_);
            uint32_t expertCountForMask = uint32ExpertCount_;
            maskForExpertCount = AscendC::MicroAPI::UpdateMask<uint32_t>(expertCountForMask);
            AscendC::MicroAPI::ReduceMax(valueAndIndexReg, valueAndIndexReg, maskForExpertCount);
            DataCopy(sortedTensorAddr + kvExpertCountAlign_ * i, valueAndIndexReg, maskForValueAndIndex);
        }
    }
} else {
    Sort32(sortedTensor, softmaxTensor, expertIdxTensor, rowCount);
}
```

#### 机制与设计原因

只需 top1 且专家数不超过 8 时，`ReduceMax` 直接生成 value/index 对，跳过 `Sort32` 的完整 32 元素排序网络；输出仍落到与通用排序相同的 interleaved `sortedTensor`，所以后续提取代码无需分叉。

#### 迁移边界

- 适用：只取一个最大值且 MicroAPI 归约能保留匹配 index 的场景。
- 前提：`A==32`、`E<=8`、`k==1`，并保留 `VL2` value/index store 布局。
- 失效：`E>8` 或 `k>1` 用 `Sort32`；`A>32` 用逐行 `Sort<float,true>`。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

把该捷径扩大到 `k>1` 会缺少其余排序项；源码明确以 `else` 回到 Sort 路径。

### Trick T-003：Host 保守 UB 行计账统一三种 dtype

#### 触发与源码依据

- 适用 Route：P0 R-001～P3 R-004。
- 触发条件：计算 `maxRowCountInUb`。
- Golden 来源：[`moe_gating_top_k_softmax_tiling_arch35.cpp:92-97`](https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_gating_top_k_softmax/op_host/moe_gating_top_k_softmax_tiling_arch35.cpp)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
int64_t inQueue = static_cast<int64_t>(expertCountAlign_ * sizeof(float) + BLOCK_BYTES);
int64_t outQueue = static_cast<int64_t>(kAlign_ * sizeof(float) + kAlign_ * sizeof(float) + kAlign_ * sizeof(float));
int64_t bufQueue = static_cast<int64_t>(expertCountAlign_ * sizeof(float) + expertCountAlign_ * sizeof(float) + expertCountAlign_ * sizeof(float));
int64_t sortTmpQueue =  static_cast<int64_t>(expertCountAlign_ * sizeof(float) * CONSTANT_TWO * CONSTANT_TWO);
int64_t sortedQueue = static_cast<int64_t>(expertCountAlign_ * sizeof(float) * CONSTANT_TWO);
maxRowCountInUb = static_cast<int64_t>((ubSize - sortedQueue) / (inQueue + outQueue + bufQueue + sortTmpQueue));
```

#### 机制与设计原因

Host 把 x 输入也按 FP32 容量计，使一个 tiling 公式可安全覆盖 float/half/bfloat16；并把 `8*A` 作为固定项从 UB 先扣除，再按每行成本求容量。对实际 `calcTmpBuf=8*A*Rloop+16*A`，该计账在 `Rloop>=1` 时不低估总 UB：一行时相等，多行时更保守。

#### 迁移边界

- 适用：多个输入 dtype 复用一个 FP32 中间计算 body。
- 前提：所有 Queue/TBuf 公式和 depth 与本实现相同，`A/K8` 对齐不变。
- 失效：增加 Queue depth、改变 sort scratch 布局或引入额外 TBuf 后必须重算，不能沿用该上界。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

仅按逻辑有效 `E` 或 FP16 输入字节估算 UB 会漏掉 FP32 对齐 buffer；固定仓 Host 明确以 `expertCountAlign*sizeof(float)` 计账。

## 模板与实现对比

| 对比维度 | P0 R-001 无完成/对齐 | P1 R-002 有完成/对齐 | P2 R-003 无完成/补齐 | P3 R-004 有完成/补齐 | 设计选择依据 |
|---|---|---|---|---|---|
| 命中条件/优先级 | `!finished,E%32=0` | `finished,E%32=0` | `!finished,E%32!=0` | `finished,E%32!=0` | 两个独立 bool 编译维度形成 4 key |
| 模板与 dtype | `<T,false,false>` | `<T,true,false>` | `<T,false,true>` | `<T,true,true>` | 每 Route 各有 3 个 T 实例 |
| 循环与分核 | 共用 | 共用 | 共用 | 共用 | 与 bool specialization 无关 |
| Queue/TBuf/寄存器 | finished Queue 只分配 | finished Queue 搬运 | pad lane 清零 | 两者同时 | UB 物理布局保持一致 |
| 内存总占用与复用 | 基线公式 | 相同 | A 对齐后同公式 | 相同 | Host 按最坏 FP32 容量计账 |
| 搬运/Vector API | softmax + sort | 加 bool copy/index Max | 加 pad Duplicate | 两者同时 | 编译期消除无关计算分支 |
| 同步、精度与 tail | Queue；FP32；k mask | 同上 + finished Queue | 同上 + E pad mask | 两种 mask | row/k tail 共用 |
| fallback/失败边界 | 无 Device fallback | 无 | 无 | 无；非法手工 key 的 wrapper else 会误落此 entry | 只能使用 calculator 生成 params |

## 平台差异

| 项目 | A2 | A3 | 950 |
|---|---|---|---|
| 支持状态 | 本 Direct 交付固定源码范围不可见 | 本 Direct 交付固定源码范围不可见 | 支持；目标为 Ascend 950/RegBase |
| Host/Launcher | 未纳入本卡 | 未纳入本卡 | `PlatformAscendCManager` 查询 AIV/UB，3 dtype launcher × 4 entry |
| Kernel/资源 | 未纳入本卡 | 未纳入本卡 | arch35 `MoeGatingTopKSoftmaxFullloadGenerlized`，单 AIV、无 workspace |

## 限制与失败边界

- 仅覆盖 CANN 9.1.0、950/Ascend 950 Direct Invoke；不外推 ACLNN、A2/A3 或 v2 语义。
- 输入必须连续，`R>0`、`1<=E<=2048`、`1<=k<=min(E,1024)`；Host tiling 还要求平台句柄、正 AIV 数和足够 UB。
- `rowIdx` 的基础 progression 是 ABI 语义的一部分；复用时必须按官方 `ArithProgression(...,0,rows,k)` 与行基址加法保持布局。
- Direct wrapper 的最终 `else` 不是合法 key 校验：未知手工 key 会进入 R-004 entry。调用者只能传入 calculator 生成的 100000/100001/100010/100011。
- `blockDim` 在 launcher 中窄化为 `uint32_t`；当前值由 `min(R,aivNum)` 产生，禁止绕过 calculator 写入任意 64 位值。
- 官方 Host 的 16 MiB workspace 是保留量而非 Device 数据边；Direct 转换去除它的前提是当前固定 body 不读取 workspace。若替换 body，必须重新审计。
- 固定官方 Device helper `LoadOneTensorForDtypeT/StoreUnAlignOneTensor` 来自 CANN 公共头；Direct 转换只局部闭合命中符号，未把公共库其余实现当作本算子知识。
- 本次知识提取未执行编译、真机、数值或性能测试。

## 源码索引

### 链路索引

| 链路阶段 | 文件 | 关键符号 | 支撑内容 |
|---|---|---|---|
| 入口/router | `moe/moe_gating_top_k_softmax/op_kernel/moe_gating_top_k_softmax_apt.cpp` | `moe_gating_top_k_softmax` | 四 key、AIC return、模板实例、Init/Process |
| POD | `moe/moe_gating_top_k_softmax/op_kernel/arch35/moe_gating_top_k_softmax_tiling_def.h` | `MoeGatingTopKSoftmaxRegbaseTilingData` | 15 字段顺序和类型 |
| Kernel body | `moe/moe_gating_top_k_softmax/op_kernel/arch35/moe_gating_top_k_softmax_fullload_generalized_regbase.h` | `MoeGatingTopKSoftmaxFullloadGenerlized` | Queue/TBuf、softmax、top-k、finished、tail |
| Host/Tiling | `moe/moe_gating_top_k_softmax/op_host/moe_gating_top_k_softmax_tiling_arch35.cpp` | `MoeGatingTopKSoftmaxRegbaseTiling` | 950 capability、分核、UB、key、workspace、POD producer |

Direct 的普通 POD、12 个显式 entry、3 个 dtype launcher、平台查询和 `register_direct_launch_op` 是从上述四个官方文件派生的交付胶水；固定提交不存在可引用的同名 Direct 文件，因此不把不可达或非官方 URL 写入 `sources`。

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | 15 个连续 int64 字段 | 字段顺序、offset、单位；launcher 按值传 POD | `MoeGatingTopKSoftmaxRegbaseTilingData` |
| 调用顺序 | 单 Kernel 内 rowIdx→x/finished→softmax→top-k→输出 | Queue producer/consumer 和每 loop 顺序 | `Process` |
| workspace/内存 | Direct workspace=0；5 Queue+4 TBuf | depth=1、A/K8 对齐、calcTmp 分区、Host 保守式 | `Init`；`CalcMaxRowCountInUb` |
| 同步 | TQue EnQue/DeQue/Free，单 stream 单 Kernel | depth=1 buffer 未消费前不得覆盖 | `CopyInX/ComputeSoftmax/ComputeTopK/CopyOut*` |
| 精度与尾块 | FP32 stable softmax，RINT 写回，E/k/row tail | max-exp-sum-div 顺序、pad mask、unaligned post update | `ComputeSoftmax/ComputeTopK` |
| 失败边界 | Host `false` 阻断 launch | 不绕过 shape/UB/platform 校验，不构造未知 key | direct calculator；`IsCapable/DoOpTiling` |
