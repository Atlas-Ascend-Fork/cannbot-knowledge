---
type: Operator
title: "ForeachNorm A5 Direct Invoke 算子知识"
description: "说明 cann_bench::foreach_norm 在 A5 上的接口语义、Direct Host/Launcher 参数生成、按重要性排序的模板 Route、分组启动图与单 Kernel 两阶段 AIV 实现。"
tags: [task.implementation, task.lookup, topic.data_movement, topic.memory, topic.precision, topic.programming_model]
status: stable
verified:
  - by: process:ops-knowledge-route-priority
    at: "2026-08-25T20:47:20Z"
  - by: process:ops-knowledge-direct53-ingest
    at: "2026-08-25T20:03:11Z"
sources:
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/foreach/foreach_norm/README.md
    role: header
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/foreach/foreach_norm/op_host/foreach_norm_def.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/foreach/foreach_utils/op_host/foreach_reduce_tiling_def.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/foreach/foreach_utils/op_host/foreach_reduce_regbase_tiling.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/foreach/foreach_utils/op_host/foreach_reduce_regbase_tiling.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/foreach/foreach_norm/op_kernel/arch35/foreach_norm.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/foreach/foreach_norm/op_kernel/arch35/foreach_norm_regbase.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/foreach/foreach_norm/op_kernel/CMakeLists.txt
    role: implementation
created_at: "2026-08-25T19:26:55Z"
updated_at: "2026-08-25T20:47:20Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# ForeachNorm A5 Direct Invoke 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | `cann_bench::foreach_norm(Tensor[] x, float scalar) -> Tensor[]`；PrivateUse1 实现 `foreach_norm_npu`；Host launcher 为 `launch_foreach_norm_{float,half,bfloat16}`。 |
| 计算语义 | 对列表内每个 Tensor 独立计算 p-范数；交付件把 scalar 映射为离散编译期 mode，输出每项一个 0-D 标量。 |
| 输入输出 | 同设备、同 dtype、连续 ND TensorList；dtype 为 FP32/FP16/BF16；输出 dtype/device 与对应输入相同。 |
| 执行类型 | 全部可达节点均为 `AIV_VECTOR` MicroAPI；每个至多四 Tensor 的 group 启动一个 Kernel，单 Kernel 内完成两阶段归约；无 Cube/AIC、MIX_CV、SIMT、NDDMA 或通信节点。 |
| Kernel 路线 | 按 dtype×scalar mode 全覆盖并分为 P0～P3；列表超过四项时，同一 Route 在当前 stream 上形成 `ceil(N/4)` 个顺序 Kernel 节点。 |
| 核心资源 | 每核静态 VECCALC ping/pong 各 126464 B、共享 partial 区 32 B、FP32 RegTensor；逻辑调用拥有 320×FP32=1280 B GM workspace。 |
| 来源闭包 | `direct_implementation_closed`：交付件的 schema、Meta/PrivateUse1、分组 metadata、dtype launcher、所有可达 entry、实际 body、workspace/sync 与构建注册均闭合；Frontmatter 仅列固定 Commit 的官方机制来源。 |
| 验证状态 | 已完成源码闭包检查；本次知识提取未执行编译、真机、数值或性能测试。 |

## 接口与语义

### 计算语义

令列表第 `t` 个 Tensor 含 `n_t` 个元素，`a_i=abs(x_t[i])`。交付件 Direct 语义为：

| scalar 条件 | mode/tag | Stage-1 聚合 | Stage-2 输出 |
|---|---|---|---|
| `p==0` | `zero` | `sum(x_i!=0)` | 原值 |
| `p==1` | `one` | `sum(a_i)` | 原值 |
| `p==2` | `two` | `sum(x_i*x_i)` | `sqrt(sum)` |
| `p==+Inf` | `pos_inf` | `max(a_i)` | 原值 |
| `p==-Inf` | `neg_inf` | `min(a_i)` | 原值 |
| 其它有限/非有限值 | `general` | `sum(exp(p*ln(a_i)))` | `exp(ln(sum)/p)` |
| `p==3` | `three` | `sum(a_i*a_i*a_i)` | `exp(ln(sum)/3)` |
| `p==1.5` | `one_half` | `sum(a_i*sqrt(a_i))` | `exp(ln(sum)/1.5)` |
| `p==4` | `four` | `sum((x_i*x_i)^2)` | 连续两次 `sqrt` |
| `p==5` | `five` | `sum((a_i*a_i)^2*a_i)` | `exp(ln(sum)/5)` |
| `p==2.5` | `two_half` | `sum((a_i*a_i)*sqrt(a_i))` | `exp(ln(sum)/2.5)` |
| `p==-1` | `neg_one` | `sum(1/a_i)` | `exp(-ln(sum))` |

空 Tensor 由其输出核直接写零。所有输入路线在寄存器中使用 FP32 聚合；FP16/BF16 输入先升为 FP32，输出以 `CAST_RINT` 降回原 dtype。NaN scalar 不命中任何等值分支，进入 `general`。这张卡描述的是交付件 Direct ABI，不把官方 ACLNN ABI 补造成 Direct ABI。

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| `x` | 非空 TensorList；每项连续 ND；每组最多四项 | 列表统一 FP32/FP16/BF16 | 所有项必须在同一设备；元素在逻辑拼接域上分核，但每个 Tensor 独立归约。 |
| `scalar` | C++ `double` 属性，launch 前收窄为 FP32 | schema `float` | 无默认值；按 `isinf`、0、1、2、3、1.5、4、5、2.5、-1 的顺序选 mode。 |
| `y` | 每个输入对应一个 0-D、1-element、连续 Tensor | 同对应 `x` | `torch::empty({}, tensor.options())` 创建；不与输入别名。 |
| `workspace` | 320 个连续 FP32 元素 | FP32 | 当前逻辑调用唯一 owner；各 group 在同 stream 顺序复用。 |

### 入口与版本

**官方相关来源**：固定 Commit 的 README 明确支持 Ascend 950PR/950DT，OpDef 注册 `ascend950` 且允许 FP16/FP32/BF16，`op_kernel/CMakeLists.txt` 把 `arch35/foreach_norm.cpp` 接到 `ascend950`。官方 A5 文档把公开 scalar 约束收窄到 1 或 2；arch35 entry 另有 `+Inf` 检测并把其它值落到 p=2 body。

**交付件 Direct 适配/派生**：`TORCH_LIBRARY_FRAGMENT` 声明 `cann_bench::foreach_norm`，Meta 只建立标量输出，PrivateUse1 绑定 `foreach_norm_npu`。交付件不经过官方 OpDef、ListTensorDesc、tiling registry、系统 workspace 或 ACLNN executor；它以 dtype 专用 `extern "C"` launcher 和离散参数直接启动 DAV-3510 AIV kernel，并扩展为上表 scalar mode。因此官方 scalar 约束只说明机制来源边界，不限制这份 Direct 契约，也不能据此宣称这些扩展 mode 是官方原生接口。

## Host/Launcher 执行流程

### 参数校验与前处理

`foreach_norm_npu` 的真实顺序为：拒绝空列表；用首 Tensor 建立 device guard；拒绝 FP32/FP16/BF16 之外 dtype；逐项检查同设备、同 dtype、连续；创建每项 0-D 输出；创建 320-element FP32 workspace；按 scalar 优先级得到 mode；每四项建立一个 `ForeachNormLaunchGroup`，未使用槽由值初始化保持空指针/零；读取当前 NPU stream；按 dtype 调一个 launcher。Host 不读取 Tensor 数值。

`OpCommand::RunOpApi("ForeachNorm", acl_call)` 只包裹调度与对象生命周期；lambda 对所有 group 顺序 launch 后固定返回 0。Host 校验失败会在 launch 前抛出；launcher 为 `void`，交付件没有单独把 Device launch 状态转换成 callback 错误码。

### 参数、Workspace 与生命周期

令 group 内 Tensor 数 `G<=4`、`s=sizeof(T)`、`E=sum(n_j)`、平台 AIV 核数 `C`：

```text
elementsPerCore = 4096 / max(s,1)                    # element
b0 = clamp(ceil(E/elementsPerCore), 1, C)           # block/core
B = max(b0,G)                                       # launch blockDim
L = ceil(E/B)                                       # flattened elements per block；E=0 时 L=0
workspace = 4*80*sizeof(float) = 1280 bytes
```

对非空 Tensor `j`，Host 计算：

```text
firstBlock_j = floor(prefix_j/L)
lastBlock_j  = floor((prefix_j+n_j-1)/L)
partialCount_j = lastBlock_j-firstBlock_j+1
meta_j = firstBlock_j | (partialCount_j<<8) | (middleStart_j<<16)
middleStart_{j+1} = middleStart_j + partialCount_j
```

`meta` 是 tensor-major packed partial 索引。workspace Tensor 被 lambda 按值捕获，所有 group 使用同一 GM 地址；同 stream 的 group launch 顺序与单 launch 内的 `SyncAll` 使前一 group 完成消费后才允许后一 group 覆盖。输出 Tensor 由返回 vector 持有。

### 启动图与失败传播

```text
cann_bench::foreach_norm / PrivateUse1
  -> validate + outputs + one 1280-B workspace
  -> scalar -> mode；dtype -> launch suffix
  -> for group g=0..ceil(N/4)-1 on current stream
       -> foreach_norm_<dtype>_<tag>_kernel<<<B,nullptr,stream>>>
          -> Stage 1: flattened spans -> per-tensor FP32 partials -> workspace
          -> SyncAll<MTE3,MTE2>
          -> Stage 2: blockIdx<G -> tensor-major partial reduce -> y[g*4+blockIdx]
```

| 节点/边 | 参数或交接介质 | ordering、owner/lifetime | 失败传播 |
|---|---|---|---|
| Host→group kernel | 4×输入/输出 GM 指针、4×长度、4×meta、mode、p；`B` 为 grid | launcher 按值传参；Tensor owner 覆盖 stream 工作期 | Host 校验失败阻断全部节点；launcher 无显式返回码 |
| Stage-1→Stage-2 | 同一 1280-B FP32 workspace；实际 slice `[middleStart,middleStart+partialCount)` | `SyncAll<true,{PIPE_MTE3,PIPE_MTE2}>` 保证 partial 写后读 | Device 侧无 fallback；同步是同一 kernel 的硬依赖 |
| group g→g+1 | 同一 workspace 被覆盖 | 同一 current stream 顺序；前一 kernel 的 Stage-2 已消费 | lambda 固定返回 0，不逐 launch 检查 |
| Kernel→y | 每 Tensor 一个 dtype 元素 | 输出 Tensor owner；每个输出仅 `blockIdx==tensor index` 的核写 | 空 Tensor 写零；其它核不写该输出 |

## Route 与参数设计

### 分核与资源计算

每核处理扁平区间 `[blockIdx*L,min(E,(blockIdx+1)*L))`，再与各 Tensor 的 `[prefix,prefix+n)` 求交。一个核最多触达四个 Tensor；每个交集调用一次 `ProcessSegment`。segment 按固定 126464-B 槽分 tile：FP32 每 tile 31616 元素，FP16/BF16 每 tile 63232 元素。每个 FP32 vector repeat 为 64 元素，主循环一次处理两个 repeat，即 128 元素；尾部先处理最多 64 个 lane 的 A，再按需处理 B。

静态 VECCALC 地址账为 `126464+126464+32=252960 B`。交付件 Host 不查询 UB 并校验该常量，故 Direct 前提是目标 DAV-3510 为这些静态地址提供至少 252960 B。workspace 固定 320 FP32；若平台 `C>80`，`calc_foreach_norm_blocks` 未显式再钳到 80，固定 workspace 与 8-bit `firstBlock/partialCount` 也会失去证明；A5 路线依赖 `C<=80`。

### Route 选择

下表按实现复用时的重要性展示，P0 最高；`Host顺序` 独立保留真实判断链，因此展示次序不等于执行判断次序。

| 重要性 | 展示序 | Route | Route 特征 | 适用域 | 实现前提 | Host顺序、短路与 fallback |
|---|---:|---|---|---|---|---|
| P0 | 1 | R-003 FP32 TWO | FP32 square+sum，Stage-2 sqrt | `dtype=FP32,p==2` | FP32 tile、FP32 partial、静态 UB/workspace 上界成立 | H4；H1～H3 均未命中；否则继续 H5 |
| P0 | 2 | R-015 FP16 TWO | B16 unpack，FP32 MulAddDst，sqrt 后 RINT FP16 | `dtype=FP16,p==2` | B16 unpack/pack 与 CAST_RINT 可用 | H4；同上 |
| P0 | 3 | R-014 FP16 ONE | B16 unpack，FP32 abs+sum，RINT FP16 | `dtype=FP16,p==1` | FP32 累加与 FP16 回写范围可接受 | H3；H1/H2 未命中；否则继续 H4 |
| P0 | 4 | R-026 BF16 ONE | BF16 unpack，FP32 abs+sum，RINT BF16 | `dtype=BF16,p==1` | BF16 cast traits 与 FP32 partial 可用 | H3；同上 |
| P0 | 5 | R-002 FP32 ONE | 纯 FP32 abs+sum | `dtype=FP32,p==1` | FP32 tile 与 mask tail 成立 | H3；同上 |
| P0 | 6 | R-027 BF16 TWO | BF16 unpack，FP32 MulAddDst，sqrt 后 RINT | `dtype=BF16,p==2` | BF16 cast traits、FP32 sqrt 可用 | H4；未命中则继续 H5 |
| P1 | 7 | R-028 BF16 POS_INF | BF16→FP32 abs/max，RINT BF16 | `dtype=BF16,p=+Inf` | 非负 max neutral=0；Inf 输入传播 | H1 `isinf` 立即短路并按符号选正 Inf |
| P1 | 8 | R-007 FP32 THREE | `abs³` 代数特化，ln-exp 开三次根 | `dtype=FP32,p==3` | FP32 MulAddDst 与通用根可用 | H5；未命中继续 H6 |
| P1 | 9 | R-031 BF16 THREE | BF16→FP32 `abs³`，通用根后 RINT | `dtype=BF16,p==3` | BF16 cast 与 FP32 ln/exp 可用 | H5；同上 |
| P1 | 10 | R-020 FP16 ONE_HALF | `abs*sqrt(abs)`，ln-exp 得 2/3 次幂 | `dtype=FP16,p==1.5` | FP32 sqrt/ln/exp 与 RINT FP16 可用 | H6；未命中继续 H7 |
| P1 | 11 | R-032 BF16 ONE_HALF | BF16→FP32 的 1.5 阶代数特化 | `dtype=BF16,p==1.5` | BF16 cast 与 FP32 root 管线可用 | H6；同上 |
| P1 | 12 | R-009 FP32 FOUR | square-of-square，Stage-2 两次 sqrt | `dtype=FP32,p==4` | 两次 FP32 sqrt 顺序不可改 | H7；未命中继续 H8 |
| P1 | 13 | R-010 FP32 FIVE | `abs²→abs⁴→abs⁵`，通用五次根 | `dtype=FP32,p==5` | FP32 多项式与 ln/exp 可用 | H8；未命中继续 H9 |
| P1 | 14 | R-011 FP32 TWO_HALF | `abs²*sqrt(abs)`，通用 0.4 次幂 | `dtype=FP32,p==2.5` | FP32 sqrt/MulAddDst/ln-exp 可用 | H9；未命中继续 H10 |
| P1 | 15 | R-024 FP16 NEG_ONE | FP32 reciprocal sum，ln-exp 求倒数，RINT | `dtype=FP16,p==-1` | 输入零值域需由调用契约约束；无 epsilon | H10；未命中进入 H11 GENERAL |
| P2 | 16 | R-006 FP32 GENERAL | catch-all `exp(p*ln(abs(x)))` | FP32 且所有专门谓词未命中 | Host double 与 Device FP32 p 收窄边界可接受 | H11 最终 fallback；无后继 Route |
| P2 | 17 | R-018 FP16 GENERAL | B16→FP32 通用幂与根，RINT FP16 | FP16 且所有专门谓词未命中 | FP32 超越函数与 RINT FP16 可用 | H11 最终 fallback |
| P2 | 18 | R-030 BF16 GENERAL | BF16→FP32 通用幂与根，RINT BF16 | BF16 且所有专门谓词未命中 | BF16 cast 与 FP32 超越函数可用 | H11 最终 fallback |
| P2 | 19 | R-004 FP32 POS_INF | FP32 abs/max | `dtype=FP32,p=+Inf` | max neutral=0 | H1 `isinf` 正号短路 |
| P2 | 20 | R-016 FP16 POS_INF | FP16→FP32 abs/max，RINT FP16 | `dtype=FP16,p=+Inf` | B16 cast 与 max neutral 成立 | H1 正号短路 |
| P2 | 21 | R-001 FP32 ZERO | CompareNE/Select 转 FP32 count | `dtype=FP32,p==0` | count 的 FP32 可表达范围可接受 | H2；仅在 H1 非 Inf 后判断 |
| P2 | 22 | R-013 FP16 ZERO | FP16→FP32 count，RINT FP16 | `dtype=FP16,p==0` | 输出 count 的 FP16 表达边界可接受 | H2；未命中继续 H3 |
| P2 | 23 | R-025 BF16 ZERO | BF16→FP32 count，RINT BF16 | `dtype=BF16,p==0` | 输出 count 的 BF16 表达边界可接受 | H2；同上 |
| P2 | 24 | R-005 FP32 NEG_INF | abs/min，tail 以 FLT_MAX 中和 | `dtype=FP32,p=-Inf` | invalid lane 必须 Select 为 FLT_MAX | H1 `isinf` 负号短路 |
| P2 | 25 | R-017 FP16 NEG_INF | FP16→FP32 min，RINT FP16 | `dtype=FP16,p=-Inf` | FLT_MAX tail neutral 与 B16 cast 可用 | H1 负号短路 |
| P2 | 26 | R-029 BF16 NEG_INF | BF16→FP32 min，RINT BF16 | `dtype=BF16,p=-Inf` | 同上 | H1 负号短路 |
| P3 | 27 | R-008 FP32 ONE_HALF | FP32 `abs*sqrt(abs)` 特化 | `dtype=FP32,p==1.5` | FP32 sqrt 与通用根可用 | H6；未命中继续 H7 |
| P3 | 28 | R-012 FP32 NEG_ONE | FP32 reciprocal sum 与倒数根 | `dtype=FP32,p==-1` | 非零输入；无 epsilon | H10；未命中到 H11 |
| P3 | 29 | R-019 FP16 THREE | FP16→FP32 `abs³`，RINT | `dtype=FP16,p==3` | B16 cast 与通用根可用 | H5；未命中继续 H6 |
| P3 | 30 | R-021 FP16 FOUR | FP16→FP32 四次幂与双 sqrt | `dtype=FP16,p==4` | 双 sqrt 与 RINT FP16 | H7；未命中继续 H8 |
| P3 | 31 | R-022 FP16 FIVE | FP16→FP32 五次幂与通用根 | `dtype=FP16,p==5` | 多项式/ln-exp/RINT 可用 | H8；未命中继续 H9 |
| P3 | 32 | R-023 FP16 TWO_HALF | FP16→FP32 2.5 阶特化 | `dtype=FP16,p==2.5` | sqrt/MulAddDst/ln-exp/RINT 可用 | H9；未命中继续 H10 |
| P3 | 33 | R-033 BF16 FOUR | BF16→FP32 四次幂与双 sqrt | `dtype=BF16,p==4` | BF16 cast、双 sqrt 可用 | H7；未命中继续 H8 |
| P3 | 34 | R-034 BF16 FIVE | BF16→FP32 五次幂与通用根 | `dtype=BF16,p==5` | BF16 cast 与 FP32 ln-exp 可用 | H8；未命中继续 H9 |
| P3 | 35 | R-035 BF16 TWO_HALF | BF16→FP32 2.5 阶特化 | `dtype=BF16,p==2.5` | BF16 cast、sqrt/MulAddDst 可用 | H9；未命中继续 H10 |
| P3 | 36 | R-036 BF16 NEG_ONE | BF16→FP32 reciprocal sum 与倒数根 | `dtype=BF16,p==-1` | 非零输入；BF16 RINT；无 epsilon | H10；未命中到 H11 |

```text
if isinf(p): tag = p>0 ? pos_inf : neg_inf
else if p==0/1/2/3/1.5/4/5/2.5/-1: tag = matching specialization
else: tag = general
if dtype==FP32/FP16/BF16: launch suffix float/half/bfloat16
else: fail before launch
```

### 模板/实现执行矩阵

| 重要性 | Route（同级按展示序） | key/selector 与适用域 | 执行拓扑与实际 body | 内存、同步与精度 | tail/fallback |
|---|---|---|---|---|---|
| P0 | R-003, R-015, R-014, R-026, R-002, R-027 | FP32/FP16/BF16 的 ONE/TWO；Host H3/H4 | 每 group 单 AIV Kernel；`KernelForeachNorm<T,ONE/TWO>` | 静态双槽+FP32 partial+SyncAll；B16 升精度/RINT | mask tail；谓词不命中沿 Host 链继续 |
| P1 | R-028, R-007, R-031, R-020, R-032, R-009, R-010, R-011, R-024 | 已离散化的 Inf/3/1.5/4/5/2.5/-1 专门模板 | 同一两阶段拓扑；实际 `AccumulateVector<T,MODE>` 代数特化 | FP32 registers；按 mode 使用 Max、Sqrt、MulAddDst 或 ln-exp | 精确谓词不命中继续；NEG_ONE 零值无兜底 |
| P2 | R-006, R-018, R-030, R-004, R-016, R-001, R-013, R-025, R-005, R-017, R-029 | GENERAL fallback 与 0/±Inf 边界语义 | GENERAL 用超越函数；ZERO 用 Compare/Select；±Inf 用 Max/Min | 相同 workspace/SyncAll；NEG_INF tail=FLT_MAX；B16 RINT | GENERAL 是 H11 终点；其它不命中继续 Host 链 |
| P3 | R-008, R-012, R-019, R-021, R-022, R-023, R-033, R-034, R-035, R-036 | 其余 dtype×专门 mode 组合 | 复用对应编译期 mode body，不走 runtime router | dtype 只改变 load/store 与降精度；静态 byte 布局不变 | 精确谓词不命中按 H5～H11 继续 |

### 隐藏性能 Guard

| Guard | Host/Tiling 条件 | Device/资源原因 | 影响 Route | 不满足时去向 | 源码符号 |
|---|---|---|---|---|---|
| A5 build | `NPU_ARCH=ascend950 -> dav-3510` | MicroAPI、static local addressing、`__schedmode__(1)` | 全部 | 构建配置失败 | 交付件 top CMake；官方 `op_kernel/CMakeLists.txt` |
| TensorList 合法性 | 非空、统一 device/dtype、连续 | 固定三组 launcher 与裸 GM 地址 | 全部 | `TORCH_CHECK`，不 launch | `foreach_norm_npu` |
| group 上限 | `G<=4`，通过 Host 分组保证 | x/y/n/meta 固定四槽；partial 局部区至少 G 个 float | 全部 | 切到下一 group，不是 Device fallback | `ForeachNormLaunchGroup`、分组循环 |
| AIV 核数 | A5 路线要求 `1<=C<=80` | workspace 仅 320 float；meta block 字段 8 bit；官方也是 80-core cap | 全部 | 无交付件 fallback；超界未闭合 | `calc_foreach_norm_blocks` |
| 静态 UB | 可用静态 VECCALC `>=252960 B` | ping/pong/partial 固定地址 | 全部 | 无 Host 检查或 fallback | `INPUT_*_ADDR`、`PARTIAL_BUFFER_ADDR` |
| tile/repeat | tile bytes=126464；repeat=64 FP32 lane；pairs→uint16 | 最大 pairs 为 494，未溢出 uint16 | 全部 | tail mask | `ProcessSegment`、`ComputeTile` |
| workspace metadata | `partialCount<256,middleStart<65536` | `meta` 分别用 8/16 bit | 全部 | 无运行时检查 | Host meta packing、Device decode |
| scalar 收窄 | C++ double→float 后传 Device | Device `p_` 与所有 transcendental 为 FP32 | 全部 | 无 FP64 route | `foreach_norm_npu`、`FinishTensor` |
| 空域 | 列表非空但单 Tensor 可 `n==0` | 不产生 partial；输出核必须显式写零 | 全部 | `OutputZero` | `Process` |

### POD/ABI

Direct entry 不传序列化 struct；下表 ABI 是 launch 形参序列。因字段是独立函数参数，`sizeof/alignof/offsetof` 不适用，必须保持顺序、位宽与 Host/Device 声明一致。

| 结构 | 字段 | 类型/位宽 | ABI 布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| entry args | `x0` | GM_ADDR/指针宽 | ordinal 0 | GM addr | group.x[0] | `Init`→x_[0] | inactive 槽为空 |
| entry args | `x1` | GM_ADDR/指针宽 | ordinal 1 | GM addr | group.x[1] | `Init`→x_[1] | 同上 |
| entry args | `x2` | GM_ADDR/指针宽 | ordinal 2 | GM addr | group.x[2] | `Init`→x_[2] | 同上 |
| entry args | `x3` | GM_ADDR/指针宽 | ordinal 3 | GM addr | group.x[3] | `Init`→x_[3] | 同上 |
| entry args | `y0` | GM_ADDR/指针宽 | ordinal 4 | GM addr | group.y[0] | `OutputZero/FinishTensor` | inactive 槽为空 |
| entry args | `y1` | GM_ADDR/指针宽 | ordinal 5 | GM addr | group.y[1] | 同上 | 同上 |
| entry args | `y2` | GM_ADDR/指针宽 | ordinal 6 | GM addr | group.y[2] | 同上 | 同上 |
| entry args | `y3` | GM_ADDR/指针宽 | ordinal 7 | GM addr | group.y[3] | 同上 | 同上 |
| entry args | `n0` | int64/64 | ordinal 8 | element | `numel()` | flattened span | `>=0` |
| entry args | `n1` | int64/64 | ordinal 9 | element | `numel()` | 同上 | inactive 为 0 |
| entry args | `n2` | int64/64 | ordinal 10 | element | `numel()` | 同上 | inactive 为 0 |
| entry args | `n3` | int64/64 | ordinal 11 | element | `numel()` | 同上 | inactive 为 0 |
| entry args | `tensorCount` | int32/32 | ordinal 12 | tensor | `min(4,remaining)` | segment/output loops | 1～4 |
| entry args | `meta0` | uint32/32 | ordinal 13 | packed index | Host first/count/start | Stage-1 offset、Stage-2 slice | 8/8/16-bit |
| entry args | `meta1` | uint32/32 | ordinal 14 | packed index | 同上 | 同上 | inactive 为 0 |
| entry args | `meta2` | uint32/32 | ordinal 15 | packed index | 同上 | 同上 | inactive 为 0 |
| entry args | `meta3` | uint32/32 | ordinal 16 | packed index | 同上 | 同上 | inactive 为 0 |
| entry args | `workspace` | GM_ADDR/指针宽 | ordinal 17 | GM addr | 320-FP32 Tensor | partial write/read | 非空，group 间复用 |
| entry args | `mode` | int32/32 | ordinal 18 | enum | scalar selector | entry 显式忽略 | 实际由 symbol tag 固化 |
| entry args | `p` | float/32 | ordinal 19 | scalar | `float(scalar)` | general/最终幂 | double 已收窄 |
| launcher-only | `numBlocks` | int64/64 | entry 外 | block | `calc_*` 后 max G | launch grid/GetBlockNum | A5 要求<=80 |
| launcher-only | `stream` | void*/指针宽 | entry 外 | stream | current NPU stream | `<<<...>>>` | group ordering |

### Route 源码闭包

| 重要性 | Route（同级按展示序） | Host/Tiling producer | POD/参数 | Kernel entry/router 节点 | Kernel body/直接依赖 | 构建接线 |
|---|---|---|---|---|---|---|
| P0 | R-003, R-015, R-014, R-026, R-002, R-027 | `foreach_norm_npu`、`calc_foreach_norm_blocks` | 离散 entry args | 对应 dtype+`two/one` entry | `RunKernelMode<T,MODE>`→实际 ONE/TWO specialization | `register_direct_launch_op` |
| P1 | R-028, R-007, R-031, R-020, R-032, R-009, R-010, R-011, R-024 | 同上；H1/H5～H10 | 同上 | 对应 dtype+专门 tag entry | 对应 POS_INF/THREE/ONE_HALF/FOUR/FIVE/TWO_HALF/NEG_ONE body | 同上 |
| P2 | R-006, R-018, R-030, R-004, R-016, R-001, R-013, R-025, R-005, R-017, R-029 | 同上；含 H11 fallback | 同上 | 对应 general/zero/pos_inf/neg_inf entry | GENERAL/ZERO/±INF specialization | 同上 |
| P3 | R-008, R-012, R-019, R-021, R-022, R-023, R-033, R-034, R-035, R-036 | 同上 | 同上 | 对应 dtype+专门 tag entry | 对应剩余编译期 mode body 与 B16 cast helper | 同上 |

## Kernel 实现

### 公共执行流程

每个 group entry 直接实例化一个 `<T,MODE>`，没有 runtime router。`Init` 保存四槽指针/长度/meta、`GetBlockIdx/GetBlockNum`、workspace 和 p。`Process` 建立两个 buffer-free 事件，计算本核扁平区间并逐 Tensor 求交；`ProcessSegment` 让输入 GM 绕过 L2 allocation，以 126464-B ping/pong 搬入；`ComputeTile` 用两个 FP32 accumulator 并行归约两个 64-lane repeat，把每个 segment 的一个 partial 放在局部 32-B 区。所有 touched partial 用一次 MTE3 copy 写到 tensor-major workspace；`SyncAll<MTE3,MTE2>` 后，前 G 个核各自读取一个 Tensor 的全部 partial，完成第二阶段和最终幂，再写一个输出标量。

```mermaid
block-beta
  columns 4
  ping["input ping · 126464 B · addr 0"]:1
  pong["input pong · 126464 B · addr 126464"]:1
  partial["partial/output alias · 32 B · addr 252928"]:1
  regs["FP32 RegTensor · 编译器寄存器"]:1
```

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| input GM | `x_[tensor]+localOffset+tile*tileElements` | `current*sizeof(T)` | T/连续 ND | caller | `DataCopyPad` | 输入 Tensor 覆盖 launch | L2 allocation disabled；尾块按 byte 搬运 |
| ping/pong | 0 / 126464 B | 各 126464 B | T/线性 | MTE2 | `ComputeTile` | Kernel 静态 local | 512-B 对齐；slot 事件后轮换 |
| partial/output alias | 252928 B | 32 B=8×FP32 | Stage-1 FP32；Stage-2 T 标量 | `ComputeTile` 或 `FinishTensor` | MTE3 | 当前 block/阶段 | Stage-1 partial 消费后同址写输出 local |
| workspace | `middleStart+(blockIdx-firstBlock)` | 分配 320×FP32；每 Tensor slice=`partialCount` | FP32/tensor-major | Stage-1 MTE3 | Stage-2 MTE2 | 调用 owner；group 顺序复用 | `SyncAll` 前禁止读取/覆盖 |
| output GM | `y_[tensor]` | 1×T | T/0-D | `OutputZero/FinishTensor` | caller | 输出 Tensor | 每个 Tensor 唯一 writer |

```text
UB_static = 126464 + 126464 + 32 = 252960 bytes/core
dynamic_ub = N/A；采用编译期静态 LocalTensor 地址
workspace_total = 4 * 80 * sizeof(float) = 1280 bytes/call
required: UB_available >= 252960 bytes && GetCoreNumAiv() <= 80
```

| 复用子区 | 写入者 | 读取者/消费点 | 下一次覆盖 | 同步或释放依据 | 安全条件 |
|---|---|---|---|---|---|
| ping/pong slot | `DataCopyPad` MTE2 | `ComputeTile` Vector | 同 slot 的下下个 tile/segment | 对应 `MTE2_V` 后计算；`V_MTE2` 后可覆写 | event ID 与 slot 一一对应 |
| partial 32-B | `ComputeTile` 的 first-element store | Stage-1 MTE3 | Stage-2 output local | MTE3 copy 已发出且全核 SyncAll 完成 | touchedTensorCount<=4；容量>=4×FP32 |
| workspace | Stage-1 Kernel 当前 group | 同 Kernel Stage-2 | 下一 group Kernel | MTE3→MTE2 SyncAll；同 stream kernel 顺序 | 不并发复用同一 workspace |

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| slot 初始可写 | `SetFlag<V_MTE2>(ID0/1)` | `Process` | 每次 `WaitFlag<V_MTE2>` | ping/pong | N/A |
| GM→local→Vector | `DataCopyPad` + `Set/Wait<MTE2_V>` | MTE2 | `ComputeTile` | 当前 tile | byte tail；Vector currentMask |
| Vector→slot free | `SetFlag<V_MTE2>` | `ComputeTile` | 后续同 slot MTE2 | 当前 slot | 两 accumulator 合并后释放 |
| partial 写后读 | `SyncAll<true,{MTE3,MTE2}>` | Stage-1 MTE3 | Stage-2 MTE2 | workspace partial | 全部 partial 为 FP32 |
| local→output GM | `V_MTE3` event+`DataCopyPad` | Stage-2 Vector | MTE3 | 单标量 output local | B16 使用 CAST_RINT；FP32 直写 |

可达入口只有宏生成的 dtype×mode kernel。源码中 `RunKernel` 的 runtime-mode 版本、`*_finalize_kernel` 与 `KernelForeachNormFinalize` 保留编译但没有 Host launcher 调用，不属于正式 Route。

以下各 Route 按 P0～P3 展开并采用同一字段顺序；每节仍给出实际模板、mode 变换、dtype 精度和资源账，避免把“公共模板”当作闭包终点。

### Route R-003（P0）：FP32 TWO

#### 适用条件
##### 选择证据
`dtype==FP32 && p==2 -> float_two -> KernelForeachNorm<float,MODE_TWO>`。
#### Device 数据流
##### 函数级调用链
`entry -> Mul(x,x)+Add -> ReduceSum -> workspace -> SyncAll -> FinishTensor -> Sqrt -> y`。
##### 源码等价伪码
`partial=sum(x*x); tensor=sqrt(sum(partials))`。
#### 内存与数据搬运
##### 资源与搬运表
FP32 tile 31616；静态双槽、32-B partial、FP32 workspace。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`UB_static=252960B; workspace=1280B`；transformed register 在每 repeat 覆盖。
#### 同步、精度与尾块
##### 同步与数值边界表
FP32 multiply/add/sqrt；mask tail；分核改变加法结合顺序。
#### 关键实现
##### 符号证据表
`float_two_kernel`; `AccumulateVector<float,TWO>` 的 Mul+Add；`FinishTensor` 的 Sqrt。

### Route R-015（P0）：FP16 TWO

#### 适用条件
##### 选择证据
`dtype==FP16 && p==2 -> half_two`。
#### Device 数据流
##### 函数级调用链
`unpack -> FP32 MulAddDst(acc,x,x) -> workspace -> SyncAll -> Sqrt -> RINT half`。
##### 源码等价伪码
`half(sqrt(sum_fp32(fp32(x)^2)))`。
#### 内存与数据搬运
##### 资源与搬运表
双 half slot；FP32 registers/partial/workspace。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
B16 路径用 MulAddDst；最终 sqrt 与 RINT 均 FP32→half。
#### 关键实现
##### 符号证据表
`half_two_kernel`; TWO B16 branch；`FinishTensor`。

### Route R-014（P0）：FP16 ONE

#### 适用条件
##### 选择证据
`dtype==FP16 && p==1 -> half_one`。
#### Device 数据流
##### 函数级调用链
`unpack half -> FP32 Abs/Add/ReduceSum -> workspace -> SyncAll -> FP32 partial sum -> RINT half`。
##### 源码等价伪码
`half(sum_fp32(abs(fp32(x))))`。
#### 内存与数据搬运
##### 资源与搬运表
63232-half tile；双槽、32-B partial、FP32 workspace。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
FP32 累加后一次 RINT；tail mask。
#### 关键实现
##### 符号证据表
`half_one_kernel`; B16 cast traits；ONE specialization。

### Route R-026（P0）：BF16 ONE

#### 适用条件
##### 选择证据
`dtype==BF16 && p==1 -> bfloat16_one`。
#### Device 数据流
##### 函数级调用链
`unpack BF16 -> FP32 Abs/Add/ReduceSum -> workspace -> SyncAll -> RINT BF16`。
##### 源码等价伪码
`bf16(sum_fp32(abs(fp32(x))))`。
#### 内存与数据搬运
##### 资源与搬运表
63232-BF16 tile；双槽；FP32 partial/workspace。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
FP32 累加；最终 RINT BF16；tail mask。
#### 关键实现
##### 符号证据表
`bfloat16_one_kernel`; ONE specialization；BF16 cast traits。

### Route R-002（P0）：FP32 ONE

#### 适用条件
##### 选择证据
`dtype==FP32 && p==1 -> float_one -> KernelForeachNorm<float,MODE_ONE>`。
#### Device 数据流
##### 函数级调用链
`entry -> ComputeTile -> Abs+Add -> ReduceSum -> workspace -> SyncAll -> FinishTensor(Add+ReduceSum) -> y`。
##### 源码等价伪码
`partial=sum(abs(x)); tensor=sum(partials); store FP32`。
#### 内存与数据搬运
##### 资源与搬运表
FP32 GM tile 31616 元素；双 126464-B slot、32-B partial、tensor-major FP32 workspace。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B + 1280B GM workspace`；slot/event 与 workspace/SyncAll 生命周期同 R-001。
#### 同步、精度与尾块
##### 同步与数值边界表
全程 FP32；currentMask 限定 Abs，invalid lane 由 neutral 0 清理。
#### 关键实现
##### 符号证据表
Host scalar branch；`foreach_norm_float_one_kernel`; `AccumulateVector<float,ONE>`、`ReduceRegister<ONE>`。

### Route R-027（P0）：BF16 TWO

#### 适用条件
##### 选择证据
`dtype==BF16 && p==2 -> bfloat16_two`。
#### Device 数据流
##### 函数级调用链
`unpack -> FP32 MulAddDst(x,x) -> partial -> SyncAll -> Sqrt -> RINT BF16`。
##### 源码等价伪码
`bf16(sqrt(sum_fp32(fp32(x)^2)))`。
#### 内存与数据搬运
##### 资源与搬运表
BF16 双槽；FP32 accumulators/partial/workspace。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
B16 MulAddDst；FP32 sqrt；RINT BF16。
#### 关键实现
##### 符号证据表
`bfloat16_two_kernel`; TWO branch；`FinishTensor`。

### Route R-028（P1）：BF16 POS_INF

#### 适用条件
##### 选择证据
`dtype==BF16 && p==+Inf -> bfloat16_pos_inf`。
#### Device 数据流
##### 函数级调用链
`unpack -> FP32 Abs/Max/ReduceMax -> workspace -> SyncAll -> Max -> RINT BF16`。
##### 源码等价伪码
`bf16(max(abs(fp32(x))))`。
#### 内存与数据搬运
##### 资源与搬运表
BF16 双槽；FP32 neutral/partial/workspace。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
tail neutral 0；RINT BF16。
#### 关键实现
##### 符号证据表
`bfloat16_pos_inf_kernel`; POS_INF；BF16 store。

### Route R-007（P1）：FP32 THREE

#### 适用条件
##### 选择证据
`dtype==FP32 && p==3 -> float_three`。
#### Device 数据流
##### 函数级调用链
`entry -> Abs -> Mul(a,a) -> MulAddDst(acc,a^2,a) -> partial -> SyncAll -> exp(ln(sum)/3)`。
##### 源码等价伪码
`tensor=(sum(abs(x)^3))^(1/3)`。
#### 内存与数据搬运
##### 资源与搬运表
FP32 双槽；value/transformed 寄存器分别承载 a²/a；workspace FP32。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`；value 在下一 repeat 覆盖。
#### 同步、精度与尾块
##### 同步与数值边界表
FP32 乘加与 ln/exp；currentMask 保护输入尾部。
#### 关键实现
##### 符号证据表
`float_three_kernel`; `AccumulateVector<...,THREE>`；`FinishTensor` 通用根。

### Route R-031（P1）：BF16 THREE

#### 适用条件
##### 选择证据
`dtype==BF16 && p==3 -> bfloat16_three`。
#### Device 数据流
##### 函数级调用链
`unpack -> FP32 Abs/square/MulAddDst -> partial -> SyncAll -> cube root -> RINT BF16`。
##### 源码等价伪码
`bf16((sum(abs(fp32(x))^3))^(1/3))`。
#### 内存与数据搬运
##### 资源与搬运表
BF16 双槽；FP32 register/partial/workspace。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
FP32 乘加/根，RINT BF16；tail mask。
#### 关键实现
##### 符号证据表
`bfloat16_three_kernel`; THREE specialization；root path。

### Route R-020（P1）：FP16 ONE_HALF

#### 适用条件
##### 选择证据
`dtype==FP16 && p==1.5 -> half_one_half`。
#### Device 数据流
##### 函数级调用链
`unpack -> FP32 Abs/Sqrt/MulAddDst -> partial -> SyncAll -> 2/3 root -> RINT half`。
##### 源码等价伪码
`half((sum(a*sqrt(a)))^(2/3)), a=abs(fp32(x))`。
#### 内存与数据搬运
##### 资源与搬运表
half 双槽；FP32 register/partial/workspace。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
FP32 sqrt/root，最终 RINT；tail mask。
#### 关键实现
##### 符号证据表
`half_one_half_kernel`; ONE_HALF specialization；B16 casts。

### Route R-032（P1）：BF16 ONE_HALF

#### 适用条件
##### 选择证据
`dtype==BF16 && p==1.5 -> bfloat16_one_half`。
#### Device 数据流
##### 函数级调用链
`unpack -> FP32 Abs/Sqrt/MulAddDst -> partial -> SyncAll -> 2/3 root -> RINT BF16`。
##### 源码等价伪码
`bf16((sum(a*sqrt(a)))^(2/3))`。
#### 内存与数据搬运
##### 资源与搬运表
BF16 双槽；FP32 value/transformed/partial/workspace。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
FP32 sqrt/root；RINT BF16；tail mask。
#### 关键实现
##### 符号证据表
`bfloat16_one_half_kernel`; ONE_HALF；BF16 cast。

### Route R-009（P1）：FP32 FOUR

#### 适用条件
##### 选择证据
`dtype==FP32 && p==4 -> float_four`。
#### Device 数据流
##### 函数级调用链
`entry -> Mul(x,x) -> MulAddDst(acc,x²,x²) -> partial -> SyncAll -> Sqrt -> Sqrt -> y`。
##### 源码等价伪码
`tensor=(sum(x^4))^(1/4)`。
#### 内存与数据搬运
##### 资源与搬运表
FP32 双槽、transformed=x²、partial/workspace FP32。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
两次 FP32 sqrt 实现四次根；tail mask。
#### 关键实现
##### 符号证据表
`float_four_kernel`; `AccumulateVector<...,FOUR>`；`FinishTensor` 双 Sqrt。

### Route R-010（P1）：FP32 FIVE

#### 适用条件
##### 选择证据
`dtype==FP32 && p==5 -> float_five`。
#### Device 数据流
##### 函数级调用链
`entry -> Abs -> square -> square -> MulAddDst(*abs) -> partial -> SyncAll -> exp(ln(sum)/5)`。
##### 源码等价伪码
`tensor=(sum(abs(x)^5))^(1/5)`。
#### 内存与数据搬运
##### 资源与搬运表
双槽；value 原地从 a² 变 a⁴；transformed 保留 a。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`；寄存器原地覆盖避免 UB 中间量。
#### 同步、精度与尾块
##### 同步与数值边界表
FP32 multiply/MulAddDst/ln-exp；tail mask。
#### 关键实现
##### 符号证据表
`float_five_kernel`; FIVE specialization；通用根。

### Route R-011（P1）：FP32 TWO_HALF

#### 适用条件
##### 选择证据
`dtype==FP32 && p==2.5 -> float_two_half`。
#### Device 数据流
##### 函数级调用链
`entry -> Abs -> Sqrt(a) -> square(a) -> MulAddDst(a²,sqrt(a)) -> partial -> SyncAll -> exp(ln(sum)/2.5)`。
##### 源码等价伪码
`tensor=(sum(abs(x)^2*sqrt(abs(x))))^0.4`。
#### 内存与数据搬运
##### 资源与搬运表
双槽；transformed 从 a 原地变 a²，value=sqrt(a)。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
FP32 sqrt/乘加/ln-exp；tail mask。
#### 关键实现
##### 符号证据表
`float_two_half_kernel`; TWO_HALF specialization；通用根。

### Route R-024（P1）：FP16 NEG_ONE

#### 适用条件
##### 选择证据
`dtype==FP16 && p==-1 -> half_neg_one`。
#### Device 数据流
##### 函数级调用链
`unpack -> FP32 Abs/Div(1,a)/Add -> partial -> SyncAll -> inverse via ln-exp -> RINT half`。
##### 源码等价伪码
`half((sum(1/abs(fp32(x))))^-1)`。
#### 内存与数据搬运
##### 资源与搬运表
half 双槽；FP32 reciprocal register/partial/workspace。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
无 epsilon；FP32 division，最终 RINT；tail mask。
#### 关键实现
##### 符号证据表
`half_neg_one_kernel`; NEG_ONE specialization；B16 casts。

### Route R-006（P2）：FP32 GENERAL

#### 适用条件
##### 选择证据
`dtype==FP32` 且全部专门值比较不命中（含 NaN）-> `float_general`。
#### Device 数据流
##### 函数级调用链
`entry -> Abs -> Ln -> Muls(p) -> Exp -> Add -> workspace -> SyncAll -> Ln(sum)*1/p -> Exp -> y`。
##### 源码等价伪码
`partial=sum(exp(p*ln(abs(x)))); tensor=exp(ln(sum)/p)`。
#### 内存与数据搬运
##### 资源与搬运表
FP32 双槽和 partial；transformed RegTensor 依次被 Abs/Ln/Muls/Exp 原地覆盖。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`；无额外 UB 物化。
#### 同步、精度与尾块
##### 同步与数值边界表
所有超越函数 FP32；0、负 p、NaN/Inf 数据沿 MicroAPI 语义传播；无数值 fallback。
#### 关键实现
##### 符号证据表
launcher `default` 分支；`AccumulateVector<float,GENERAL>`；`FinishTensor` reciprocalP 管线。

### Route R-018（P2）：FP16 GENERAL

#### 适用条件
##### 选择证据
`dtype==FP16` 且 scalar 未命中特化 -> `half_general`。
#### Device 数据流
##### 函数级调用链
`unpack -> FP32 Abs/Ln/Muls/Exp/Add -> workspace -> SyncAll -> FP32 root -> RINT half`。
##### 源码等价伪码
`half(exp(ln(sum(exp(p*ln(abs(fp32(x))))))/p))`。
#### 内存与数据搬运
##### 资源与搬运表
half 双槽；超越函数中间量只在 FP32 registers；无中间 GM。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
输入先升精度，最终一次 RINT；无特殊数值保护。
#### 关键实现
##### 符号证据表
`half_general_kernel`; GENERAL specialization；B16 load/store。

### Route R-030（P2）：BF16 GENERAL

#### 适用条件
##### 选择证据
`dtype==BF16` 且 scalar 未命中特化 -> `bfloat16_general`。
#### Device 数据流
##### 函数级调用链
`unpack -> FP32 Abs/Ln/Muls/Exp/Add -> partial -> SyncAll -> root -> RINT BF16`。
##### 源码等价伪码
`bf16(exp(ln(sum(exp(p*ln(abs(fp32(x))))))/p))`。
#### 内存与数据搬运
##### 资源与搬运表
BF16 双槽；FP32 transcendental registers/partial/workspace。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`；中间量寄存器原地覆盖。
#### 同步、精度与尾块
##### 同步与数值边界表
FP32 超越函数；最终 RINT BF16；无数值 fallback。
#### 关键实现
##### 符号证据表
`bfloat16_general_kernel`; GENERAL specialization；BF16 load/store。

### Route R-004（P2）：FP32 POS_INF

#### 适用条件
##### 选择证据
`dtype==FP32 && isinf(p)&&p>0 -> float_pos_inf`。
#### Device 数据流
##### 函数级调用链
`entry -> Abs+Max -> ReduceMax -> workspace -> SyncAll -> Max partials -> y`。
##### 源码等价伪码
`partial=max(abs(x)); tensor=max(partials)`，neutral 为 0。
#### 内存与数据搬运
##### 资源与搬运表
FP32 GM/双槽、32-B partial、FP32 workspace；无最终幂 buffer。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`；寄存器 Max 原地复用。
#### 同步、精度与尾块
##### 同步与数值边界表
currentMask 后 Abs；invalid lane 为 0，不扩大非负最大值。
#### 关键实现
##### 符号证据表
`float_pos_inf_kernel`; `Combine<POS_INF>`、`ReduceRegister<POS_INF>`。

### Route R-016（P2）：FP16 POS_INF

#### 适用条件
##### 选择证据
`dtype==FP16 && p==+Inf -> half_pos_inf`。
#### Device 数据流
##### 函数级调用链
`unpack -> FP32 Abs/Max/ReduceMax -> workspace -> SyncAll -> Max -> RINT half`。
##### 源码等价伪码
`half(max(abs(fp32(x))))`。
#### 内存与数据搬运
##### 资源与搬运表
half 双槽；FP32 partial/workspace；neutral=0。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
尾 lane 为 0；最终 RINT half。
#### 关键实现
##### 符号证据表
`half_pos_inf_kernel`; POS_INF Combine/ReduceMax；B16 store。

### Route R-001（P2）：FP32 ZERO

#### 适用条件
##### 选择证据
`dtype==FP32 && p==0 -> launch_float/zero -> KernelForeachNorm<float,MODE_ZERO>`。
#### Device 数据流
##### 函数级调用链
`entry -> Init -> Process -> ProcessSegment -> ComputeTile -> AccumulateVector<float,ZERO>(CompareNE+Select+Add) -> workspace -> SyncAll -> FinishTensor -> y`。
##### 源码等价伪码
`partial += (x!=0); tensor=sum(partials); store FP32`，尾 lane 由 currentMask 变为 0。
#### 内存与数据搬运
##### 资源与搬运表
GM FP32→31616-element ping/pong；局部 partial 8×FP32；workspace slice 为 meta 指定的 FP32 区间。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`UB_static=252960B; workspace=1280B`；事件允许 compute 完成后覆盖同一 slot，SyncAll 后才覆盖 workspace。
#### 同步、精度与尾块
##### 同步与数值边界表
MTE2_V/V_MTE2 保护双槽；MTE3→MTE2 SyncAll 保护 partial；FP32 count，mask tail，空 Tensor 写 0。
#### 关键实现
##### 符号证据表
Host `foreach_norm_npu`; entry `foreach_norm_float_zero_kernel`; body `AccumulateVector<float,MODE_ZERO>`、`FinishTensor`。

### Route R-013（P2）：FP16 ZERO

#### 适用条件
##### 选择证据
`dtype==FP16 && p==0 -> half_zero -> KernelForeachNorm<half,MODE_ZERO>`。
#### Device 数据流
##### 函数级调用链
`entry -> DIST_UNPACK_B16 -> Cast FP32 -> CompareNE/Select/Add -> partial -> SyncAll -> StoreFromFloat CAST_RINT -> y`。
##### 源码等价伪码
`count_nonzero(fp32(half)); cast_rint result to half`。
#### 内存与数据搬运
##### 资源与搬运表
每槽 63232 half；partial/workspace FP32；输出区复用 32-B partial 地址。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`；硬事件与 SyncAll 闭合。
#### 同步、精度与尾块
##### 同步与数值边界表
half→FP32 count→CAST_RINT half；masked tail；空 Tensor half 0。
#### 关键实现
##### 符号证据表
`half_zero_kernel`; `LoadAsFloat<half>`、ZERO specialization、`StoreFromFloat<half>`。

### Route R-025（P2）：BF16 ZERO

#### 适用条件
##### 选择证据
`dtype==BF16 && p==0 -> bfloat16_zero -> KernelForeachNorm<bfloat16_t,MODE_ZERO>`。
#### Device 数据流
##### 函数级调用链
`entry -> unpack BF16/Cast FP32 -> CompareNE/Select/Add -> partial -> SyncAll -> CAST_RINT BF16`。
##### 源码等价伪码
`bf16(count_nonzero(fp32(x)))`。
#### 内存与数据搬运
##### 资源与搬运表
每槽 63232 BF16；FP32 partial/workspace；32-B output alias。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
BF16→FP32 count→RINT BF16；空域写 BF16 0。
#### 关键实现
##### 符号证据表
`bfloat16_zero_kernel`; `LoadAsFloat<bfloat16_t>`；ZERO；B16 store。

### Route R-005（P2）：FP32 NEG_INF

#### 适用条件
##### 选择证据
`dtype==FP32 && isinf(p)&&p<=0 -> float_neg_inf`。
#### Device 数据流
##### 函数级调用链
`entry -> Abs+Select(FLT_MAX tail)+Min -> ReduceMin -> workspace -> SyncAll -> Min partials -> y`。
##### 源码等价伪码
`partial=min(abs(x)); tensor=min(partials)`；无效 lane 替成 `FLT_MAX`。
#### 内存与数据搬运
##### 资源与搬运表
同 FP32 静态布局；neutral register 为 `3.402823466e38F`。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`；Select 后 transformed 可覆盖。
#### 同步、精度与尾块
##### 同步与数值边界表
Min 的 tail 用最大有限 FP32 中和；空 Tensor 特例仍输出 0。
#### 关键实现
##### 符号证据表
`float_neg_inf_kernel`; `NeutralValue<NEG_INF>`、`ReduceMin`。

### Route R-017（P2）：FP16 NEG_INF

#### 适用条件
##### 选择证据
`dtype==FP16 && p==-Inf -> half_neg_inf`。
#### Device 数据流
##### 函数级调用链
`unpack -> FP32 Abs/Select FLT_MAX/Min -> workspace -> SyncAll -> ReduceMin -> RINT half`。
##### 源码等价伪码
`half(min(abs(fp32(x))))`，空 Tensor 单独写 0。
#### 内存与数据搬运
##### 资源与搬运表
half 双槽；FP32 neutral/partial/workspace。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
FLT_MAX 中和尾 lane；结果 RINT half。
#### 关键实现
##### 符号证据表
`half_neg_inf_kernel`; NEG_INF specialization；B16 cast。

### Route R-029（P2）：BF16 NEG_INF

#### 适用条件
##### 选择证据
`dtype==BF16 && p==-Inf -> bfloat16_neg_inf`。
#### Device 数据流
##### 函数级调用链
`unpack -> FP32 Abs/Select FLT_MAX/Min -> partial -> SyncAll -> ReduceMin -> RINT BF16`。
##### 源码等价伪码
`bf16(min(abs(fp32(x))))`；空 Tensor 输出 0。
#### 内存与数据搬运
##### 资源与搬运表
BF16 双槽；FP32 neutral/partial/workspace。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
tail 用 FLT_MAX 中和；RINT BF16。
#### 关键实现
##### 符号证据表
`bfloat16_neg_inf_kernel`; NEG_INF；BF16 cast。

### Route R-008（P3）：FP32 ONE_HALF

#### 适用条件
##### 选择证据
`dtype==FP32 && p==1.5 -> float_one_half`。
#### Device 数据流
##### 函数级调用链
`entry -> Abs -> Sqrt(a) -> MulAddDst(acc,a,sqrt(a)) -> partial -> SyncAll -> exp(ln(sum)/1.5)`。
##### 源码等价伪码
`tensor=(sum(abs(x)*sqrt(abs(x))))^(2/3)`。
#### 内存与数据搬运
##### 资源与搬运表
FP32 双槽；transformed=a、value=sqrt(a)；无中间 GM。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
FP32 sqrt/乘加/根；masked tail。
#### 关键实现
##### 符号证据表
`float_one_half_kernel`; mode specialization；`FinishTensor`。

### Route R-012（P3）：FP32 NEG_ONE

#### 适用条件
##### 选择证据
`dtype==FP32 && p==-1 -> float_neg_one`。
#### Device 数据流
##### 函数级调用链
`entry -> Abs -> Div(1,a) -> Add -> partial -> SyncAll -> exp(-ln(sum)) -> y`。
##### 源码等价伪码
`tensor=(sum(1/abs(x)))^-1`。
#### 内存与数据搬运
##### 资源与搬运表
双槽；transformed 从 abs 原地变 reciprocal；workspace FP32。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
零元素触发 FP32 division 语义；无 epsilon；tail mask。
#### 关键实现
##### 符号证据表
`float_neg_one_kernel`; `Div(transformed,one,transformed)`；通用根。

### Route R-019（P3）：FP16 THREE

#### 适用条件
##### 选择证据
`dtype==FP16 && p==3 -> half_three`。
#### Device 数据流
##### 函数级调用链
`unpack -> FP32 Abs/square/MulAddDst -> partial -> SyncAll -> cube root via ln-exp -> RINT half`。
##### 源码等价伪码
`half((sum(abs(fp32(x))^3))^(1/3))`。
#### 内存与数据搬运
##### 资源与搬运表
half 双槽；FP32 value/transformed/partial/workspace。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
FP32 乘加和根，末端 RINT half；tail mask。
#### 关键实现
##### 符号证据表
`half_three_kernel`; THREE specialization；`FinishTensor`。

### Route R-021（P3）：FP16 FOUR

#### 适用条件
##### 选择证据
`dtype==FP16 && p==4 -> half_four`。
#### Device 数据流
##### 函数级调用链
`unpack -> FP32 square/MulAddDst(square,square) -> partial -> SyncAll -> Sqrt twice -> RINT half`。
##### 源码等价伪码
`half((sum(fp32(x)^4))^(1/4))`。
#### 内存与数据搬运
##### 资源与搬运表
half 双槽；FP32 transformed/partial/workspace。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
两次 FP32 sqrt 后 RINT；tail mask。
#### 关键实现
##### 符号证据表
`half_four_kernel`; FOUR specialization；dual Sqrt。

### Route R-022（P3）：FP16 FIVE

#### 适用条件
##### 选择证据
`dtype==FP16 && p==5 -> half_five`。
#### Device 数据流
##### 函数级调用链
`unpack -> FP32 Abs/a²/a⁴/MulAddDst(*a) -> partial -> SyncAll -> fifth root -> RINT half`。
##### 源码等价伪码
`half((sum(abs(fp32(x))^5))^(1/5))`。
#### 内存与数据搬运
##### 资源与搬运表
half 双槽；register 原地复用；FP32 partial/workspace。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
FP32 多项式与 ln-exp；最终 RINT。
#### 关键实现
##### 符号证据表
`half_five_kernel`; FIVE specialization；B16 store。

### Route R-023（P3）：FP16 TWO_HALF

#### 适用条件
##### 选择证据
`dtype==FP16 && p==2.5 -> half_two_half`。
#### Device 数据流
##### 函数级调用链
`unpack -> FP32 Abs/Sqrt/square/MulAddDst -> partial -> SyncAll -> 0.4 root -> RINT half`。
##### 源码等价伪码
`half((sum(a²*sqrt(a)))^0.4)`。
#### 内存与数据搬运
##### 资源与搬运表
half 双槽；FP32 value/transformed/partial/workspace。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
FP32 math，RINT half；tail mask。
#### 关键实现
##### 符号证据表
`half_two_half_kernel`; TWO_HALF specialization；root path。

### Route R-033（P3）：BF16 FOUR

#### 适用条件
##### 选择证据
`dtype==BF16 && p==4 -> bfloat16_four`。
#### Device 数据流
##### 函数级调用链
`unpack -> FP32 square/MulAddDst(square,square) -> partial -> SyncAll -> Sqrt twice -> RINT BF16`。
##### 源码等价伪码
`bf16((sum(fp32(x)^4))^(1/4))`。
#### 内存与数据搬运
##### 资源与搬运表
BF16 双槽；FP32 transformed/partial/workspace。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
双 FP32 sqrt 后 RINT BF16；tail mask。
#### 关键实现
##### 符号证据表
`bfloat16_four_kernel`; FOUR specialization；dual Sqrt。

### Route R-034（P3）：BF16 FIVE

#### 适用条件
##### 选择证据
`dtype==BF16 && p==5 -> bfloat16_five`。
#### Device 数据流
##### 函数级调用链
`unpack -> FP32 Abs/a²/a⁴/MulAddDst -> partial -> SyncAll -> fifth root -> RINT BF16`。
##### 源码等价伪码
`bf16((sum(abs(fp32(x))^5))^(1/5))`。
#### 内存与数据搬运
##### 资源与搬运表
BF16 双槽；register 原地复用；FP32 partial/workspace。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
FP32 math；末端 RINT BF16；tail mask。
#### 关键实现
##### 符号证据表
`bfloat16_five_kernel`; FIVE specialization；BF16 store。

### Route R-035（P3）：BF16 TWO_HALF

#### 适用条件
##### 选择证据
`dtype==BF16 && p==2.5 -> bfloat16_two_half`。
#### Device 数据流
##### 函数级调用链
`unpack -> FP32 Abs/Sqrt/square/MulAddDst -> partial -> SyncAll -> 0.4 root -> RINT BF16`。
##### 源码等价伪码
`bf16((sum(a²*sqrt(a)))^0.4)`。
#### 内存与数据搬运
##### 资源与搬运表
BF16 双槽；FP32 registers/partial/workspace。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
FP32 sqrt/乘加/root；RINT BF16。
#### 关键实现
##### 符号证据表
`bfloat16_two_half_kernel`; TWO_HALF；root path。

### Route R-036（P3）：BF16 NEG_ONE

#### 适用条件
##### 选择证据
`dtype==BF16 && p==-1 -> bfloat16_neg_one`。
#### Device 数据流
##### 函数级调用链
`unpack -> FP32 Abs/Div(1,a)/Add -> partial -> SyncAll -> inverse via ln-exp -> RINT BF16`。
##### 源码等价伪码
`bf16((sum(1/abs(fp32(x))))^-1)`。
#### 内存与数据搬运
##### 资源与搬运表
BF16 双槽；FP32 reciprocal/partial/workspace。
##### 分层内存布局
`block-beta: ping[126464B] | pong[126464B] | partial/output[32B]`。
##### 字节账与复用顺序
`252960B; workspace 1280B`。
#### 同步、精度与尾块
##### 同步与数值边界表
零值无 epsilon；FP32 division/root，RINT BF16；tail mask。
#### 关键实现
##### 符号证据表
`bfloat16_neg_one_kernel`; NEG_ONE specialization；BF16 cast。

## 算子特定优化

### Trick T-001：同一 AIV launch 内完成 tensor-major partial 与第二阶段归约

#### 触发与源码依据

- 适用 Route：R-001～R-036，任一 Tensor 跨一个以上 block 时价值最明确。
- 触发条件：Host 已生产每 Tensor 的 partial 起点与跨度；Stage-1 MTE3 写完成后执行全核同步。
- Golden 来源：[`foreach_norm_regbase.h:96-113`](https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/foreach/foreach_norm/op_kernel/arch35/foreach_norm_regbase.h)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
DataCopyExtParams copyParams{1, tensorNum * static_cast<uint32_t>(sizeof(float)), 0, 0, 0};
DataCopyPad(workTensorGM_[1ULL * coreMiddleOffset_], outLocal, copyParams);
outQueue_.FreeTensor(outLocal);
SyncAll();
for (uint16_t i = blockIdx_; i < totalTensorCount_; i += needCoreNum_) {
    outTensorGM_.SetGlobalBuffer(GetGlobalTensorAddr(i, outDesc_));
    if (tensorDataCountList_[i] == 0) {
        OutputZero();
        continue;
    }
    ReduceCompute(tensorMiddleCountList_[i], tensorMiddleStartList_[i]);
    CopyOut();
}
```

#### 机制与设计原因

官方机制用每核连续 partial 写、`SyncAll` 和核间轮转完成 Stage-2。交付件保留同一 launch 两阶段拓扑，但把 metadata 压成 `firstBlock/partialCount/middleStart`，只为最多四个 Tensor 写 tensor-major workspace；`SyncAllConfig{PIPE_MTE3,PIPE_MTE2}` 精确约束写 partial 的 MTE3 与读 partial 的 MTE2。这避免独立 finalize launch 和第二套 launcher/POD；workspace 只物化每个 block×Tensor 交集的一个 FP32 标量。

#### 迁移边界

- 适用：列表归约可由结合型 sum/min/max 合并，并能为每个输出分配唯一 Stage-2 writer。
- 前提：全核同步合法；workspace 容量覆盖全部 partial；metadata 不溢出；同 launch 的 blockDim 至少覆盖输出 Tensor 数。
- 失效：无法全核同步、partial 运算不具可合并顺序或输出数大于可分配 writer 时，需拆成显式 finalize Kernel 并建立 stream 边。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

省略 Stage-1→Stage-2 的 MTE3/MTE2 可见性会让 Stage-2 读取未完成 partial；固定官方源码明确把 `SyncAll` 放在两阶段之间。

### Trick T-002：固定双槽 streaming DMA 与双 accumulator 隐藏搬运/归约依赖

#### 触发与源码依据

- 适用 Route：R-001～R-036 的所有非空 segment。
- 触发条件：segment 被切成一个或多个 126464-B tile；slot 以 `inputSlot&1` 轮换。
- Golden 来源：[`foreach_norm_regbase.h:63-73`](https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/foreach/foreach_norm/op_kernel/arch35/foreach_norm_regbase.h)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
workTensorGM_.SetGlobalBuffer((__gm__ float*)(workspace), MAX_TENSOR_CONT + MAX_CORE_CONT);
blockIdx_ = GetBlockIdx();
inDesc_ = ListTensorDesc((__gm__ void*)inputs);
outDesc_ = ListTensorDesc((__gm__ void*)outputs);
ParseTilingData(tilingData);
tPipe->InitBuffer(inQueue_, BUFFER_NUM_, inputsTensorUbSize_ * sizeof(T));
tPipe->InitBuffer(outQueue_, 1, maxTensorNumPerCore_ * sizeof(float));
maxDataCount_ = inputsTensorUbSize_;
```

#### 机制与设计原因

官方 body 的 `BUFFER_NUM_=2` 给出双输入槽机制。交付件 Direct 派生取消活动 `TPipe/TQue`，把两个槽固定在 0 和 126464 B，并以两个独立 hard event 维护 `MTE2 copy -> Vector consume -> slot free`；每次主循环同时加载 A/B 两个 64-lane repeat，各自累加后再合并，减少串行 accumulator 依赖。输入仅消费一次，交付件还设置 `CACHE_MODE_DISABLE` 避免为一次性流式读取分配 L2。关键前提是静态局部地址账 252960 B 可用。

#### 迁移边界

- 适用：单遍流式、tile 间只需一个标量状态的 AIV 归约。
- 前提：目标 A5 支持对应 hard-event pipe；两个 slot 基址满足 512-B 对齐；tile byte 数与 dtype 整除；静态 UB 上界成立。
- 失效：UB 小于 252960 B、需要跨 tile 保留大中间量或平台事件协议不同，必须恢复动态 tiling/Queue 或减小 tile。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

在 `V_MTE2` 尚未表示消费完成时覆盖 slot，会破坏当前 Vector 读取；交付件以 slot 独立 event 阻止该覆盖。固定官方源码未提供静态地址版的可验证反例。

### Trick T-003：Host scalar 分流到编译期 mode，消除热循环 runtime 分支

#### 触发与源码依据

- 适用 Route：R-001～R-036；每个 scalar 只命中一个 tag。
- 触发条件：Host 按固定优先级确定 mode，再由 launcher switch 选择显式 `__schedmode__(1)` symbol。
- Golden 来源：[`foreach_norm.cpp:34-47`](https://gitcode.com/cann/ops-nn/blob/26311e64257d6d54e5876cf1cc95104a3f378860/foreach/foreach_norm/op_kernel/arch35/foreach_norm.cpp)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
if (modelCode == POSITIVE_INF_SCALAR_NORM_MODEL_CODE) {
    ForeachNormNDRegbase<T, POSITIVE_INF_SCALAR_NORM_MODEL_CODE, ForeachReduceTilingDataRegbase> op;
    op.Init(inputs, output, workspace, tilingData, tPipe);
    op.Process();
} else if (modelCode == ONE_SCALAR_NORM_MODEL_CODE) {
    ForeachNormNDRegbase<T, ONE_SCALAR_NORM_MODEL_CODE, ForeachReduceTilingDataRegbase> op;
    op.Init(inputs, output, workspace, tilingData, tPipe);
    op.Process();
} else {
    ForeachNormNDRegbase<T, TWO_SCALAR_NORM_MODEL_CODE, ForeachReduceTilingDataRegbase> op;
```

#### 机制与设计原因

官方实现把 p=+Inf/1/2 映射到模板常量。交付件沿用这一思路并扩成 dtype×mode 的显式 entry；entry 接收的 runtime `mode` 被 `(void)mode` 丢弃，热循环的 `if constexpr` 只保留目标 Abs/Mul/Sqrt/Ln/Exp/Min/Max 序列。因而不同 scalar 的指令选择在 launch 前完成，且 p=2 的 FP32 Mul+Add 与 B16 MulAddDst 差异也在编译期消解。

#### 迁移边界

- 适用：scalar 值域包含少量高频常量，且 binary 体积允许多实例。
- 前提：Host 与 launcher 的 enum/tag 映射完全一致；general 必须是最终 default；float 等值比较语义可接受。
- 失效：scalar 连续分布且实例爆炸不可接受时，需保留 runtime mode 或只特化高频值。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

若只修改 Host enum 而未同步 launcher switch 分支与宏 tag，会静默启动错误数学模板；Direct ABI 因 entry 内忽略 runtime mode，不能在 Device 端纠正。

## 模板与实现对比

| 重要性 | Route（同级按展示序） | 主要实现特征 | dtype/精度差异 | 资源与同步 | fallback/失败边界 |
|---|---|---|---|---|---|
| P0 | R-003, R-015, R-014, R-026, R-002, R-027 | ONE/TWO 的 abs/sum 或 square/sum+sqrt；编译期去除 mode 分支 | FP32 直算；FP16/BF16 unpack 到 FP32、末端 RINT | 固定双槽、双 accumulator、FP32 workspace、SyncAll | H3/H4 不命中继续；dtype/布局错误在 Host 失败 |
| P1 | R-028, R-007, R-031, R-020, R-032, R-009, R-010, R-011, R-024 | Max、代数幂、sqrt 或 reciprocal 专门模板 | 全部 FP32 聚合；B16 只在边界 cast | 相同 252960-B static local；无额外中间 GM | 精确 scalar 谓词不命中继续；NEG_ONE 无零值兜底 |
| P2 | R-006, R-018, R-030, R-004, R-016, R-001, R-013, R-025, R-005, R-017, R-029 | GENERAL catch-all 与 ZERO/±INF 边界模板 | GENERAL 使用 FP32 ln-exp；ZERO count 降回输出 dtype | 相同 workspace；NEG_INF tail 额外使用 FLT_MAX neutral | GENERAL 为 H11 最终 fallback；静态 UB/meta 超界无 fallback |
| P3 | R-008, R-012, R-019, R-021, R-022, R-023, R-033, R-034, R-035, R-036 | 其余 dtype×专门 mode 复用同一源码模板 | T 决定 load/store 与 RINT，MODE 决定算术序列 | byte 布局和 hard-event/SyncAll 协议不变 | 按 H5～H11 短路；无 runtime mode router |

mode 维度对比：ZERO 用 Compare/Select；ONE 用 Abs+Sum；TWO 用 square+sqrt；±Inf 用 Max/Min；THREE/ONE_HALF/FOUR/FIVE/TWO_HALF 用乘法或 sqrt 的代数特化；NEG_ONE 用 reciprocal；GENERAL 用 ln-exp。除 ZERO、ONE、TWO、FOUR、±Inf 外，Stage-2 统一用 `exp(ln(sum)/p)`。

## 平台差异

| 项目 | A2 | A3 | A5 |
|---|---|---|---|
| 支持状态 | 官方 README 支持；不在本卡 Direct 构建范围 | 官方 README 支持；不在本卡 Direct 构建范围 | 官方 README/OpDef/CMake 明确支持；本卡目标 |
| Host/Launcher | 固定 Direct 交付件未提供对应构建接线 | 固定 Direct 交付件未提供对应构建接线 | `ascend950 -> dav-3510`，PrivateUse1+三个 direct launcher |
| Kernel/资源 | 官方非 arch35 body，不在本卡闭包 | 官方非 arch35 body，不在本卡闭包 | arch35 机制来源；交付件静态 252960-B VECCALC、80-core workspace 前提 |

## 限制与失败边界

- Direct 输入列表不能为空；dtype 必须统一为 FP32/FP16/BF16；所有 Tensor 必须同设备且连续。输出是新建 0-D Tensor，不支持 caller 提供输出或原地别名。
- 交付件按四项分组但没有总列表长度上限；源码可证明多 group 顺序启动，跨 group 必须继续维持同 stream 与 workspace 生命周期前提，本次未执行运行验证。
- `sum(n_j)`、prefix、blockLength 使用 int64，但没有显式溢出检查；meta 的 first/count 为 8 bit、middleStart 为 16 bit。A5 闭包依赖 AIV 核数不超过 80。
- 静态 VECCALC 需求 252960 B 没有 Host capability guard；迁移到更小 UB 的平台会越界，且没有 fallback。
- workspace 固定 1280 B；其 owner 是调用内 FP32 Tensor，group 仅因同 stream 顺序而安全复用。改变为多 stream/并发 group 时必须为每个并发 launch 分片。
- `double scalar` 在 launch 前收窄为 FP32；GENERAL、NEG_ONE 等不做 domain 修正、epsilon、overflow/underflow 或 NaN 兜底。空 Tensor 对所有 mode 固定输出 0。
- scalar mode 的等值判断发生在 Host `double` 上，而 Device `p` 是收窄后的 FP32；极小非零 double 可能在 Device 变成 0 但仍运行 GENERAL。ZERO 的 count 也先以 FP32 聚合再降到输出 dtype，超出 FP16/BF16 可精确表达范围时会按 cast 语义舍入或溢出。
- 浮点加法规约按 block/tile 分组，结果不保证与串行逐元素相同结合顺序；FP16/BF16 最终使用 `CAST_RINT`。
- 源码中的 runtime `RunKernel`、独立 finalize entries/classes 没有 Host 可达 launcher，属于 inactive reference，不得当作 fallback 或第二 Kernel Route。
- 官方 A5 公开约束只支持 scalar 1/2，而交付 Direct 扩展 12 mode；扩展是派生事实，不是官方接口支持声明。
- 本次知识提取未执行编译、真机、数值或性能测试。

## 源码索引

### 链路索引

Frontmatter 与本索引只收录转换相关的官方固定 Commit 文件；交付件 Direct 文件以相对单元名在正文中标识，不生成不可达或本机来源 URL。

| 链路阶段 | 文件 | 关键符号 | 支撑内容 |
|---|---|---|---|
| 入口声明/约束 | `foreach/foreach_norm/README.md` | 产品支持、功能与参数表 | A5 支持、官方 dtype/scalar 边界 |
| 平台注册 | `foreach/foreach_norm/op_host/foreach_norm_def.cpp` | `ForeachNorm::ForeachNorm` | ascend950、dtype/layout 注册 |
| POD | `foreach/foreach_utils/op_host/foreach_reduce_tiling_def.h` | `ForeachReduceTilingDataRegbase` | 官方 256 Tensor/80 core 与 partial metadata 机制 |
| Host selector | `foreach/foreach_utils/op_host/foreach_reduce_regbase_tiling.h` | `ForeachReduceRegbaseTiling::IsCapable` | RegBase 平台能力选择 |
| Host/Tiling | `foreach/foreach_utils/op_host/foreach_reduce_regbase_tiling.cpp` | `AssignDataToEachCore`、`DoOpTiling`、`PostTiling` | 4096-B seed、80-core cap、UB、workspace、schedmode |
| Kernel entry/router | `foreach/foreach_norm/op_kernel/arch35/foreach_norm.cpp` | `foreach_norm`、`ForeachNormImpl` | A5 dtype/model 模板分派 |
| Kernel body | `foreach/foreach_norm/op_kernel/arch35/foreach_norm_regbase.h` | `ForeachNormNDRegbase` | 两阶段归约、double buffer、FP32 partial、SyncAll |
| 构建接线 | `foreach/foreach_norm/op_kernel/CMakeLists.txt` | `add_kernel_sources` | arch35 source→ascend950 |

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | Direct 可用四槽离散参数代替官方 ListTensorDesc/POD | entry 参数顺序/位宽、meta 8/8/16 bit、inactive 槽零值必须一致 | 交付件 `FOREACH_NORM_KERNEL_ARGS`；官方 `ForeachReduceTilingDataRegbase` 仅作机制来源 |
| 调用顺序 | Host 分组→mode/dtype launcher→Stage-1→SyncAll→Stage-2 | group 共用 workspace 时必须同 stream 顺序 | `foreach_norm_npu`、`KernelForeachNorm::Process` |
| workspace/内存 | tensor-major FP32 partial；双输入槽 | 1280-B 总量、252960-B static local、slot 地址和 partial 地址不可重叠 | `meta` producer、`INPUT_*_ADDR`、`PARTIAL_BUFFER_ADDR` |
| 同步 | slot hard event；MTE3→MTE2 全核同步 | partial 未全局可见前不得 Stage-2；slot 未消费前不得覆盖 | `ProcessSegment`、`SyncAll<PARTIAL_SYNC>` |
| 精度与尾块 | B16→FP32 聚合→RINT B16；FP32 mask tail | NEG_INF tail 必须用 FLT_MAX；GENERAL 顺序与 p 收窄不可擅改 | `LoadAsFloat`、`AccumulateVector`、`FinishTensor` |
| 失败边界 | Host 明确拒绝空列表/混合 dtype/device/非连续 | 不可把 inactive finalize 或官方 ACLNN 当 Direct fallback | `foreach_norm_npu`、launcher macro |
