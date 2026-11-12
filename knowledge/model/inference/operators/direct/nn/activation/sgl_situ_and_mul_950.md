---
type: Operator
title: "SituAndMul 950 Direct Invoke 算子知识"
description: "闭合浮点SiTU四列块与24特化、设备端group有效前缀、FP32饱和及int64行地址，区分Direct未调公共check和int32调度容量。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/activation/situ_and_mul.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/activation/situ_and_mul.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/__init__.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/setup.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/torch_wheel.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernel-group.yml
    role: supporting
created_at: "2026-11-09T09:34:29Z"
updated_at: "2026-11-10T07:06:47Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# SituAndMul 950 Direct Invoke 算子知识

## 算子速览

`sgl_kernel_npu.implementation.triton.activation.situ_and_mul.situ_and_mul(x,group_list=None,group_list_type=None,beta=4.0,linear_beta=25.0)` 是浮点SiTU激活：gate/up两半FP32饱和与乘法，新输出[...,d]；不量化，也不是标准SiLU别名。完整Direct/Device、四tile×三group×两linear共24特化闭合。

draft准确区分：Direct函数不会调用公开_check_inputs，调用方必须满足共享合同；仅有效行前缀写入、padding未定义，metadata数值不回Host检查，属性缓存/physical compiler资源外部。已有[SiTU API](../../../../apis/sgl_kernel_npu/sgl_situ_and_mul.md)已全文阅读。

## 接口与语义

### 计算语义

x[...,2d]=[g|u]；`a=beta*tanh(g/beta)*sigmoid(g)`；linear_beta=L非None则`v=L*tanh(u/L)`，否则v=u；y=a*v。beta/L有限正、生产FP16/BF16/FP32，内部gate/up先FP32，输出转x.dtype。没有scale量化或额外输出。

### 输入、输出与属性

| 项 | 合同与真实读取 |
|---|---|
| x | strided浮点Tensor、至少1维、末维2d且d>0、非空调用NPU；前导展平N |
| group_list=None | 全N行有效，group_list_type忽略 |
| cumulative type0 | 连续非空同deviceint32/int64[E]，最后一项为R，公共要求非负单调且R≤N，无起始哨兵 |
| count type1 | 同上、逐项非负，R=sum(group)≤N；Device先窄化每项int32再sum |
| beta/linear_beta | 有限正Python实数、排除bool；linear None禁用up饱和；Direct未显式校验 |
| output | 新连续[...,d]同dtype/device；仅[0,R)行定义，余行不清零 |

### 入口与版本

冻结短路径加包名前缀即Direct函数。public operator才_check_inputs（type0/1、末维偶数、groupdtype、非空group）再分发；Direct不执行这四项，不能借门面guard填补入口。auto/triton直达，torch_native/量化变体均非本图。SGLcommit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`，CANN9.1.0为README/CI固定背景，非本次运行；Triton及libdevice二进制未完整固定。

## Host/Launcher 执行流程

### 参数校验与前处理

h=x.shape[-1]、N=x.numel()//h；N0直接分配空输出返回（h0会先除0，不属于合同）。非空helper获P，max_rows=INT32_MAX-(P-1)=2³¹-P，N超过则ValueError，随后output分配，x.reshape(N,h).contiguous()。input若原packed则可复用底层，否则复制。group按numel E，E_P2=next_power_of_2(E)；Direct无E/dtype/device/typeguard，错误group_type非0在Kernel落count分支，不等于公开可接受。

### 参数、Workspace 与生命周期

Host传beta及1/beta，L None用1.0占位并DO_LINEARfalse；故beta0可能在launch参数求值处除0，不是Device自动稳定化。无调用方workspace/POD/ACLNN；可能输入copy是内部GM临时，输出allocation为Nd*dx。helper无参cache/current_device，assertAIC/vector正，未绑定x.device。Tensor/临时copy异步生命周期与copy→Kernel流顺序归框架，源码没有显式event/wait/stream。

### 启动图与失败传播

import→shape/rows→N0空返回或helper→int32rowsguard→output→packedcopy→autotune/JIT单Kernel→返回。group总数在每program设备端计算，无Host同步/元数据数值扫描。所有异常传播，无fallback；包原生库导入前提不作为此数学图native算子。autotune重复执行也只覆盖有效前缀，未写padding不能比较。

## Route 与参数设计

### 分核与资源计算

P核；合法R≤N≤2³¹-P，q=ceil(R/P)，program p行[pq,min((p+1)q,R))；row_begin≥R提前返回。预留P-1防int32末行调度roundup，不能因rowoffint64取消调度限制。每行H方向分BLOCK_H，自含gate/up对应列，末列mask。R0不写output任何元素。

### Route 选择

四Htile={1024,2048,4096,8192}且multibuffer=True；显式autotunekey=[HALF_COLS,HAS_GROUP_LIST]，内部constexprspecialization/cache外部。group=none/cumulative/count三种，linear禁用/启用两种。所有24矩阵项属于同一浮点SiTU语义的可选参数，不含quant。

### 模板/实现执行矩阵

| Route | Htile | group | up饱和 |
|---|---:|---|---|
| R-001 | 1024 | none | false |
| R-002 | 1024 | none | true |
| R-003 | 1024 | cumulative | false |
| R-004 | 1024 | cumulative | true |
| R-005 | 1024 | count | false |
| R-006 | 1024 | count | true |
| R-007 | 2048 | none | false |
| R-008 | 2048 | none | true |
| R-009 | 2048 | cumulative | false |
| R-010 | 2048 | cumulative | true |
| R-011 | 2048 | count | false |
| R-012 | 2048 | count | true |
| R-013 | 4096 | none | false |
| R-014 | 4096 | none | true |
| R-015 | 4096 | cumulative | false |
| R-016 | 4096 | cumulative | true |
| R-017 | 4096 | count | false |
| R-018 | 4096 | count | true |
| R-019 | 8192 | none | false |
| R-020 | 8192 | none | true |
| R-021 | 8192 | cumulative | false |
| R-022 | 8192 | cumulative | true |
| R-023 | 8192 | count | false |
| R-024 | 8192 | count | true |

每项再有x三浮点dtype、group存在时两整数dtype；FP32math同body。无tl.dot/Cube/AIC/MIX节点，libdevice.tanh/tiling物理同步均primitive边界。

### 隐藏性能 Guard

没有全d行常驻UB，tile逻辑资源随BLOCK_H而非d；multibuffer=True是compiler选项不是已知depth2内存事实。group各项须保证窄化与sum不溢出（非负且总≤N提供足够前提），仅HostNguard不能防非法group值。typed0只读last不检查monotonic；大E归约资源未guard。尺寸/地址还需实际JIT可表示。

### POD/ABI

| 字段 | 类别/消费 |
|---|---|
| x_ptr/group_list_ptr/out_ptr | runtime指针；无group时用x_2d占位但false分支不读 |
| TOTAL_COLS/HALF_COLS | constexpr h/d→行步长/分段/H循环 |
| NUM_EXPERTS/NUM_EXPERTS_ALIGNED | constexpr E/E_P2→group last或maskedreduce |
| GROUP_LIST_TYPE | constexpr→0last/elsecount，公开只允许0/1 |
| N_ROWS | runtime N→无group时R |
| NUM_CORES | constexpr P→分行 |
| HAS_GROUP_LIST | constexpr→metadata分支 |
| BETA/INV_BETA | constexpr beta/1beta→gate |
| DO_LINEAR_BETA | constexpr→up分支 |
| LINEAR_BETA/INV_LINEAR_BETA | constexpr L/1L，None用1占位 |
| BLOCK_H | constexpr四候选→arange/循环 |
| multibuffer | 配置True，physical allocation外部 |
| grid | (P,) |

无序列化POD/字段偏移或自定义ABI。Device group/count调度int32、rowoffsetint64明确；其它整数lowering位宽/范围不伪造。

### Route 源码闭包

完整133行Direct/Kernel、helper、publicsharedcheck已读；Direct是否可达guard准确区分。根setup→stage_runtime完整Python包→build_wheel/setup_refactor；activation/backend包无Device。externalreshape/contiguous、tanh/sigmoid/primitive及framework流边界明示，不以Torchreference补实现。

## Kernel 实现

### 公共执行流程

metadata得R→分行/earlyreturn→逐行Htileload两半→FP32SiTU→可选up饱和→乘→cast/store。无group统计GMscratch、无原子、无跨核交接。N0不启动，下列完整24配置。

### Route R-001：Htile1024 / group=none / linear=false

#### 适用条件

##### 选择证据

非空N、BLOCK_H=1024来自四候选且multibuffer=True；HAS_GROUP_LIST=false，R=N；DO_LINEAR_BETA=false。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→N_ROWS→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步1024：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=up；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各1024FP32逻辑lane，单张量4096 B；不是同时物理占用证明 |
| group | 无读取 |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[1024]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx` B（group=none直接使用N_ROWS，不读取group占位指针）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 无group访问 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，仅gate tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |


### Route R-002：Htile1024 / group=none / linear=true

#### 适用条件

##### 选择证据

非空N、BLOCK_H=1024来自四候选且multibuffer=True；HAS_GROUP_LIST=false，R=N；DO_LINEAR_BETA=true。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→N_ROWS→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步1024：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=linear_beta*tanh(up/linear_beta)；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各1024FP32逻辑lane，单张量4096 B；不是同时物理占用证明 |
| group | 无读取 |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[1024]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx` B（group=none直接使用N_ROWS，不读取group占位指针）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 无group访问 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，两tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |


### Route R-003：Htile1024 / group=cumulative / linear=false

#### 适用条件

##### 选择证据

非空N、BLOCK_H=1024来自四候选且multibuffer=True；HAS_GROUP_LIST=true/GROUP_LIST_TYPE=0，R=int32(last group)；DO_LINEAR_BETA=false。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→group最后项load→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步1024：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=up；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各1024FP32逻辑lane，单张量4096 B；不是同时物理占用证明 |
| group | 每program读末项1个，dg B |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[1024]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx+P*dg` B（所有Pprogram先读group再earlyreturn）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 只取最后项转int32，不验证其它项单调/范围 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，仅gate tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |


### Route R-004：Htile1024 / group=cumulative / linear=true

#### 适用条件

##### 选择证据

非空N、BLOCK_H=1024来自四候选且multibuffer=True；HAS_GROUP_LIST=true/GROUP_LIST_TYPE=0，R=int32(last group)；DO_LINEAR_BETA=true。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→group最后项load→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步1024：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=linear_beta*tanh(up/linear_beta)；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各1024FP32逻辑lane，单张量4096 B；不是同时物理占用证明 |
| group | 每program读末项1个，dg B |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[1024]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx+P*dg` B（所有Pprogram先读group再earlyreturn）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 只取最后项转int32，不验证其它项单调/范围 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，两tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |


### Route R-005：Htile1024 / group=count / linear=false

#### 适用条件

##### 选择证据

非空N、BLOCK_H=1024来自四候选且multibuffer=True；HAS_GROUP_LIST=true/GROUP_LIST_TYPE=1，R=sum(int32(group))；DO_LINEAR_BETA=false。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→groupmaskedload/int32sum→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步1024：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=up；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各1024FP32逻辑lane，单张量4096 B；不是同时物理占用证明 |
| group | 每program读E个，E*dg B，pad到E_P2再sumint32 |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[1024]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx+P*E*dg` B（所有Pprogram先读group再earlyreturn）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 各项先转int32再sum，非负和≤N前提防窄化/和溢出 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，仅gate tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |


### Route R-006：Htile1024 / group=count / linear=true

#### 适用条件

##### 选择证据

非空N、BLOCK_H=1024来自四候选且multibuffer=True；HAS_GROUP_LIST=true/GROUP_LIST_TYPE=1，R=sum(int32(group))；DO_LINEAR_BETA=true。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→groupmaskedload/int32sum→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步1024：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=linear_beta*tanh(up/linear_beta)；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各1024FP32逻辑lane，单张量4096 B；不是同时物理占用证明 |
| group | 每program读E个，E*dg B，pad到E_P2再sumint32 |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[1024]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx+P*E*dg` B（所有Pprogram先读group再earlyreturn）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 各项先转int32再sum，非负和≤N前提防窄化/和溢出 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，两tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |


### Route R-007：Htile2048 / group=none / linear=false

#### 适用条件

##### 选择证据

非空N、BLOCK_H=2048来自四候选且multibuffer=True；HAS_GROUP_LIST=false，R=N；DO_LINEAR_BETA=false。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→N_ROWS→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步2048：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=up；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各2048FP32逻辑lane，单张量8192 B；不是同时物理占用证明 |
| group | 无读取 |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[2048]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx` B（group=none直接使用N_ROWS，不读取group占位指针）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 无group访问 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，仅gate tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |


### Route R-008：Htile2048 / group=none / linear=true

#### 适用条件

##### 选择证据

非空N、BLOCK_H=2048来自四候选且multibuffer=True；HAS_GROUP_LIST=false，R=N；DO_LINEAR_BETA=true。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→N_ROWS→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步2048：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=linear_beta*tanh(up/linear_beta)；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各2048FP32逻辑lane，单张量8192 B；不是同时物理占用证明 |
| group | 无读取 |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[2048]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx` B（group=none直接使用N_ROWS，不读取group占位指针）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 无group访问 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，两tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |


### Route R-009：Htile2048 / group=cumulative / linear=false

#### 适用条件

##### 选择证据

非空N、BLOCK_H=2048来自四候选且multibuffer=True；HAS_GROUP_LIST=true/GROUP_LIST_TYPE=0，R=int32(last group)；DO_LINEAR_BETA=false。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→group最后项load→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步2048：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=up；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各2048FP32逻辑lane，单张量8192 B；不是同时物理占用证明 |
| group | 每program读末项1个，dg B |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[2048]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx+P*dg` B（所有Pprogram先读group再earlyreturn）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 只取最后项转int32，不验证其它项单调/范围 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，仅gate tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |


### Route R-010：Htile2048 / group=cumulative / linear=true

#### 适用条件

##### 选择证据

非空N、BLOCK_H=2048来自四候选且multibuffer=True；HAS_GROUP_LIST=true/GROUP_LIST_TYPE=0，R=int32(last group)；DO_LINEAR_BETA=true。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→group最后项load→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步2048：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=linear_beta*tanh(up/linear_beta)；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各2048FP32逻辑lane，单张量8192 B；不是同时物理占用证明 |
| group | 每program读末项1个，dg B |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[2048]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx+P*dg` B（所有Pprogram先读group再earlyreturn）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 只取最后项转int32，不验证其它项单调/范围 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，两tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |


### Route R-011：Htile2048 / group=count / linear=false

#### 适用条件

##### 选择证据

非空N、BLOCK_H=2048来自四候选且multibuffer=True；HAS_GROUP_LIST=true/GROUP_LIST_TYPE=1，R=sum(int32(group))；DO_LINEAR_BETA=false。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→groupmaskedload/int32sum→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步2048：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=up；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各2048FP32逻辑lane，单张量8192 B；不是同时物理占用证明 |
| group | 每program读E个，E*dg B，pad到E_P2再sumint32 |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[2048]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx+P*E*dg` B（所有Pprogram先读group再earlyreturn）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 各项先转int32再sum，非负和≤N前提防窄化/和溢出 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，仅gate tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |


### Route R-012：Htile2048 / group=count / linear=true

#### 适用条件

##### 选择证据

非空N、BLOCK_H=2048来自四候选且multibuffer=True；HAS_GROUP_LIST=true/GROUP_LIST_TYPE=1，R=sum(int32(group))；DO_LINEAR_BETA=true。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→groupmaskedload/int32sum→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步2048：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=linear_beta*tanh(up/linear_beta)；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各2048FP32逻辑lane，单张量8192 B；不是同时物理占用证明 |
| group | 每program读E个，E*dg B，pad到E_P2再sumint32 |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[2048]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx+P*E*dg` B（所有Pprogram先读group再earlyreturn）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 各项先转int32再sum，非负和≤N前提防窄化/和溢出 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，两tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |


### Route R-013：Htile4096 / group=none / linear=false

#### 适用条件

##### 选择证据

非空N、BLOCK_H=4096来自四候选且multibuffer=True；HAS_GROUP_LIST=false，R=N；DO_LINEAR_BETA=false。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→N_ROWS→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步4096：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=up；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各4096FP32逻辑lane，单张量16384 B；不是同时物理占用证明 |
| group | 无读取 |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[4096]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx` B（group=none直接使用N_ROWS，不读取group占位指针）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 无group访问 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，仅gate tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |


### Route R-014：Htile4096 / group=none / linear=true

#### 适用条件

##### 选择证据

非空N、BLOCK_H=4096来自四候选且multibuffer=True；HAS_GROUP_LIST=false，R=N；DO_LINEAR_BETA=true。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→N_ROWS→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步4096：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=linear_beta*tanh(up/linear_beta)；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各4096FP32逻辑lane，单张量16384 B；不是同时物理占用证明 |
| group | 无读取 |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[4096]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx` B（group=none直接使用N_ROWS，不读取group占位指针）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 无group访问 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，两tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |


### Route R-015：Htile4096 / group=cumulative / linear=false

#### 适用条件

##### 选择证据

非空N、BLOCK_H=4096来自四候选且multibuffer=True；HAS_GROUP_LIST=true/GROUP_LIST_TYPE=0，R=int32(last group)；DO_LINEAR_BETA=false。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→group最后项load→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步4096：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=up；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各4096FP32逻辑lane，单张量16384 B；不是同时物理占用证明 |
| group | 每program读末项1个，dg B |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[4096]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx+P*dg` B（所有Pprogram先读group再earlyreturn）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 只取最后项转int32，不验证其它项单调/范围 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，仅gate tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |


### Route R-016：Htile4096 / group=cumulative / linear=true

#### 适用条件

##### 选择证据

非空N、BLOCK_H=4096来自四候选且multibuffer=True；HAS_GROUP_LIST=true/GROUP_LIST_TYPE=0，R=int32(last group)；DO_LINEAR_BETA=true。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→group最后项load→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步4096：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=linear_beta*tanh(up/linear_beta)；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各4096FP32逻辑lane，单张量16384 B；不是同时物理占用证明 |
| group | 每program读末项1个，dg B |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[4096]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx+P*dg` B（所有Pprogram先读group再earlyreturn）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 只取最后项转int32，不验证其它项单调/范围 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，两tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |


### Route R-017：Htile4096 / group=count / linear=false

#### 适用条件

##### 选择证据

非空N、BLOCK_H=4096来自四候选且multibuffer=True；HAS_GROUP_LIST=true/GROUP_LIST_TYPE=1，R=sum(int32(group))；DO_LINEAR_BETA=false。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→groupmaskedload/int32sum→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步4096：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=up；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各4096FP32逻辑lane，单张量16384 B；不是同时物理占用证明 |
| group | 每program读E个，E*dg B，pad到E_P2再sumint32 |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[4096]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx+P*E*dg` B（所有Pprogram先读group再earlyreturn）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 各项先转int32再sum，非负和≤N前提防窄化/和溢出 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，仅gate tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |


### Route R-018：Htile4096 / group=count / linear=true

#### 适用条件

##### 选择证据

非空N、BLOCK_H=4096来自四候选且multibuffer=True；HAS_GROUP_LIST=true/GROUP_LIST_TYPE=1，R=sum(int32(group))；DO_LINEAR_BETA=true。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→groupmaskedload/int32sum→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步4096：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=linear_beta*tanh(up/linear_beta)；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各4096FP32逻辑lane，单张量16384 B；不是同时物理占用证明 |
| group | 每program读E个，E*dg B，pad到E_P2再sumint32 |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[4096]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx+P*E*dg` B（所有Pprogram先读group再earlyreturn）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 各项先转int32再sum，非负和≤N前提防窄化/和溢出 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，两tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |


### Route R-019：Htile8192 / group=none / linear=false

#### 适用条件

##### 选择证据

非空N、BLOCK_H=8192来自四候选且multibuffer=True；HAS_GROUP_LIST=false，R=N；DO_LINEAR_BETA=false。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→N_ROWS→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步8192：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=up；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各8192FP32逻辑lane，单张量32768 B；不是同时物理占用证明 |
| group | 无读取 |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[8192]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx` B（group=none直接使用N_ROWS，不读取group占位指针）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 无group访问 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，仅gate tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |


### Route R-020：Htile8192 / group=none / linear=true

#### 适用条件

##### 选择证据

非空N、BLOCK_H=8192来自四候选且multibuffer=True；HAS_GROUP_LIST=false，R=N；DO_LINEAR_BETA=true。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→N_ROWS→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步8192：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=linear_beta*tanh(up/linear_beta)；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各8192FP32逻辑lane，单张量32768 B；不是同时物理占用证明 |
| group | 无读取 |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[8192]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx` B（group=none直接使用N_ROWS，不读取group占位指针）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 无group访问 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，两tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |


### Route R-021：Htile8192 / group=cumulative / linear=false

#### 适用条件

##### 选择证据

非空N、BLOCK_H=8192来自四候选且multibuffer=True；HAS_GROUP_LIST=true/GROUP_LIST_TYPE=0，R=int32(last group)；DO_LINEAR_BETA=false。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→group最后项load→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步8192：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=up；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各8192FP32逻辑lane，单张量32768 B；不是同时物理占用证明 |
| group | 每program读末项1个，dg B |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[8192]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx+P*dg` B（所有Pprogram先读group再earlyreturn）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 只取最后项转int32，不验证其它项单调/范围 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，仅gate tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |


### Route R-022：Htile8192 / group=cumulative / linear=true

#### 适用条件

##### 选择证据

非空N、BLOCK_H=8192来自四候选且multibuffer=True；HAS_GROUP_LIST=true/GROUP_LIST_TYPE=0，R=int32(last group)；DO_LINEAR_BETA=true。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→group最后项load→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步8192：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=linear_beta*tanh(up/linear_beta)；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各8192FP32逻辑lane，单张量32768 B；不是同时物理占用证明 |
| group | 每program读末项1个，dg B |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[8192]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx+P*dg` B（所有Pprogram先读group再earlyreturn）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 只取最后项转int32，不验证其它项单调/范围 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，两tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |


### Route R-023：Htile8192 / group=count / linear=false

#### 适用条件

##### 选择证据

非空N、BLOCK_H=8192来自四候选且multibuffer=True；HAS_GROUP_LIST=true/GROUP_LIST_TYPE=1，R=sum(int32(group))；DO_LINEAR_BETA=false。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→groupmaskedload/int32sum→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步8192：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=up；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各8192FP32逻辑lane，单张量32768 B；不是同时物理占用证明 |
| group | 每program读E个，E*dg B，pad到E_P2再sumint32 |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[8192]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx+P*E*dg` B（所有Pprogram先读group再earlyreturn）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 各项先转int32再sum，非负和≤N前提防窄化/和溢出 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，仅gate tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |


### Route R-024：Htile8192 / group=count / linear=true

#### 适用条件

##### 选择证据

非空N、BLOCK_H=8192来自四候选且multibuffer=True；HAS_GROUP_LIST=true/GROUP_LIST_TYPE=1，R=sum(int32(group))；DO_LINEAR_BETA=true。候选赢家外部，不把multibuffer=True换算物理队列深度。

#### Device 数据流

##### 函数级调用链

`situ_and_mul→helper→reshape/contiguous→autotune→_situ_and_mul_kernel→groupmaskedload/int32sum→FP32tanh/sigmoid/store`。libdevice.tanh为外部CANN Tritonprimitive，未见Cube节点。

##### 源码等价伪码

各program先得R，q=ceil(R/P)，行区间[pq,min((p+1)q,R))，row_begin≥R则返回；逐行、h步8192：从packed gate[row*2d+h]与up[row*2d+d+h]maskedload→FP32；a=beta*tanh(g/beta)*sigmoid(g)；u=linear_beta*tanh(up/linear_beta)；store cast(a*u)。rowoff显式int64，h<d尾mask。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| gate/up/a/out | 各8192FP32逻辑lane，单张量32768 B；不是同时物理占用证明 |
| group | 每program读E个，E*dg B，pad到E_P2再sumint32 |
| GM输入/输出 | 完整有效前缀读取2R*d*dx、写R*d*dx B；未写N-R行 |
| 请求方workspace/UB | 无显式请求/分配，compiler外部；输入连续化临时另计 |

##### 分层内存布局

`strided x→[可能Torch packed copy] GM[N,2d]→gate/up FP32SSA[8192]→tanh/sigmoid→GMout[N,d]有效前缀`。group统计任务内SSA，不落GM/不回Host。

##### 字节账与复用顺序

此route Kernel逻辑流量 `3R*d*dx+P*E*dg` B（所有Pprogram先读group再earlyreturn）。输出分配N*d*dx B；若输入需连续化，临时分配N*2d*dx B，额外逻辑读/写各N*2d*dx B。编译器multibuffer/寄存器/UB峰值未知，不机械乘2。输出/输入copy/group异步生命周期归框架，无自定义free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 行分配 | 合法0≤R≤N与int32调度域下行区间不交叠，Htile也不重叠 |
| group | 各项先转int32再sum，非负和≤N前提防窄化/和溢出 |
| 有效行0 | earlyreturn，不写任何输出；padding不可读 |
| 精度 | gate/up先FP32，两tanh及sigmoid/mul，store转输入dtype；近似/融合归primitive |
| 尾列 | h<d load other0/storemask；无整行常驻要求 |
| 同步 | 每program独立，无原子/barrier，SSA由compiler保序；流与copy依赖外部Torch/Triton |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| group与分行 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L63) |
| Htile与FP32算术 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85) |
| 常量/launcher | [入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L88-L133) |

## 算子特定优化

### Trick T-001：对应gate/up列分块而非整行驻留

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L68-L85)：

```python
    h_offs = tl.arange(0, BLOCK_H)
    for row_idx in range(row_begin, row_end):
        # int64 row offset: row_idx * stride stays int32 by default on triton-ascend
        # (no auto-promote), which overflows when N*d is large (e.g. N=32768, d=33792).
        row_off = row_idx.to(tl.int64) * TOTAL_COLS
        gate_base = x_ptr + row_off
        up_base = x_ptr + row_off + HALF_COLS
        out_base = out_ptr + row_idx.to(tl.int64) * HALF_COLS
        for h_start in range(0, HALF_COLS, BLOCK_H):
            h_idx = h_start + h_offs
            mask = h_idx < HALF_COLS
            gate = tl.load(gate_base + h_idx, mask=mask, other=0.0).to(tl.float32)
            up = tl.load(up_base + h_idx, mask=mask, other=0.0).to(tl.float32)
            situ_a = BETA * libdevice.tanh(gate * INV_BETA) * tl.sigmoid(gate)
            if DO_LINEAR_BETA:
                up = LINEAR_BETA * libdevice.tanh(up * INV_LINEAR_BETA)
            out = situ_a * up
            tl.store(out_base + h_idx, out.to(out_ptr.dtype.element_ty), mask=mask)
```

#### 机制与设计原因

每个输出列只依赖对应gate/up列，H维任意大时用固定tile流式消费，rowoffset先转int64避免大N*d的默认int32乘溢出风险。仅源码机制，不给出UB实际峰值或性能收益。

#### 迁移边界

需要packed[N,2d]；仅reshape可能保留paddingstride，因此Host额外contiguous。rowoffsetint64与int32行调度限制分别保留。

#### 错误做法

取消contiguous却按packed地址消费，或只见int64offset便取消N≤2³¹-Pguard。

### Trick T-002：设备端group统计定义有效前缀

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py#L43-L55)：

```python
    # total_rows: from group_list (routed MoE) or N_ROWS (dense / shared, no group_list).
    if HAS_GROUP_LIST:
        if GROUP_LIST_TYPE == 0:  # cumulative counts; the last entry is the total
            total_rows = tl.load(group_list_ptr + NUM_EXPERTS - 1).to(tl.int32)
        else:  # count
            gl_offsets = tl.arange(0, NUM_EXPERTS_ALIGNED)
            gl_mask = gl_offsets < NUM_EXPERTS
            group_list = tl.load(group_list_ptr + gl_offsets, gl_mask, other=0).to(
                tl.int32
            )
            total_rows = tl.sum(group_list)
    else:
        total_rows = N_ROWS
```

#### 机制与设计原因

cumulative只读last；count将E补齐二次幂、mask0并int32sum；不把元数据总数同步到Host，减少源码中设备值回读依赖。每program重复统计的逻辑代价明确，不声称只读一次。

#### 迁移边界

group连续同device且合法数值；只消费有效前缀，padding保持未定义，countnarrowing和sum需可表示。

#### 错误做法

累积编码额外加起始哨兵改变E含义，或比较整张output含未写padding。

## 模板与实现对比

24特化的读取metadata、up饱和和tile不同，数学统一SiTU可选参数；量化situ_and_mul_quant不在此冻结入口。public少量guard不属于Direct可达链，卡片明确调用差异而未改API。输入copy是外部Torch节点，有GM成本。

## 平台差异

本卡950归属arch35；公开arch22支持但只报告A3验证/A2未单测，arch35报告A5（950构建族）验证；README/architectures映射A2/A3及950。上游报告不等于本次复测，代码无硬件分支；CANN9.1.0 CI配置非当前compiler或物理分配证明。

## 限制与失败边界

仅合法有效前缀可读；Direct绕过共享check，dtype/layout/device、group整数值、beta/L正有限均调用方保证。Nguard不覆盖非法metadata或全部地址整数域，multibuffer不能当固定物理buffer。未运行上游、编译、autotune、测试或校验，无真机/性能证据；draft不作无条件安全推荐。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开合同](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/activation/situ_and_mul.md) | `situ_and_mul` | SiTU浮点语义/group前缀/A3与arch35验证报告 |
| [Direct及Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py) | `situ_and_mul/_situ_and_mul_kernel` | 完整133行/四Htile/三group与两linear状态 |
| [公开校验/转发](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/activation/situ_and_mul.py) | `_check_inputs/_triton_impl` | 四项公共check；Direct不调用 |
| [activation包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/__init__.py) | `module init` | 无Device |
| [设备helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py) | `get_device_properties` | current_device、无参cache、两核数assert |
| [import边界](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py) | `_load_sgl_kernel_npu` | torch_npu/原生库与vendor初始化 |
| [backend包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py) | `module init` | 懒加载包，无另一Device节点 |
| [构建入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/setup.py) | `main` | 完整Python wheel路径；本次未构建 |
| [源码打包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/torch_wheel.py) | `stage_runtime/build_torch/build_wheel/setup_refactor` | 复制完整Python包、原生运行库与wheel |
| [平台/包说明](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md) | `REFACTOR/arch22/35 mapping` | 全部Python实现包含、产品映射、CANN9.1.0构建例 |
| [产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json) | `2201/3510` | a2/a3/950对应构建族 |
| [版本配置](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml) | `test-norm-ops` | CANN9.1.0/a3/950配置，非本次运行 |
| [CI消费](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernel-group.yml) | `run-kernel-group` | 对应版本容器/测试组参数 |

### 实现复用检查

冻结117/legacy同主题API已完整读，链接复用，仅新增本浮点Direct两平台Operator，不混入量化/SiLU不同数学语义。全部同repo固定source唯一primary，无verified。
