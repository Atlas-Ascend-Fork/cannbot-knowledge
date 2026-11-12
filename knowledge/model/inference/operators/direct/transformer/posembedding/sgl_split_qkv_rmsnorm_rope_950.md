---
type: Operator
title: "SplitQkvRmsnormRope 950 Direct Invoke 算子知识"
description: "闭合QKV拆分的16种norm/bias/partial/配对特化与KVhead网格，记录FP32连续计算、bias源码读集合、表读取及arange准入边界。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/split_qkv_rmsnorm_rope.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/norm_utils.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/norm/split_qkv_rmsnorm_rope.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/__init__.py
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
created_at: "2026-11-09T09:39:40Z"
updated_at: "2026-11-10T07:06:47Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# SplitQkvRmsnormRope 950 Direct Invoke 算子知识

## 算子速览

精确入口 `sgl_kernel_npu.implementation.triton.norm.split_qkv_rmsnorm_rope.split_qkv_rmsnorm_rope`：拆连续Q/K/V，可选逐headFP32 RMSNorm及成对bias，再对Q/K做全/部分NeoX或GPT-J RoPE，V原值复制。四flags共16特化及空Host路线全部源码闭合；同文件Gemma gate是后续独立入口，不合并。

draft保留未guard的arange/toolchain准入、资源/整数域和当前设备属性cache边界；public支持同时注明硬件待验证。已有[API](../../../../apis/sgl_kernel_npu/sgl_split_qkv_rmsnorm_rope.md)已完整读并链接，相关pos_cache API也已读以确认不同舍入语义不混入。

## 接口与语义

### 计算语义

input[N,Q+2K]=[Qin|Kin|Vin]，D=head_dim。eps非None：各head `a=x/sqrt(mean(x²)+eps)*w+b`（bias可无）；否则a=x。前R列 `y=a*cos+rho(a)*sin`，后D-R列保留a；NeoX两半、GPT-J相邻偶奇配对且频率取表前半并重复。真实norm用1/tl.sqrt，FP32norm/affine和RoPE间不降精度，最终store转inputdtype。V不参与任何算术。

### 输入、输出与属性

| 项 | 可达元信息检查 |
|---|---|
| input | 连续strided FP16/BF16/FP32二维，NPU，宽Q+2K |
| Q/K/D | 正Pythonint排bool，K%D=0，Q%K=0 |
| sin/cos | 连续同device浮点，ndim≥2，末维相同正偶R≤D，各numel=N*R；重复半表值约束不做数值检查 |
| eps/weight | epsNone跳norm，否则有限正实数/排bool及qw/kw连续同device三浮点numel≥D |
| bias | 成对同时None/同时存在；存在时各连续同device浮点numel≥D，即使epsNone也检查 |
| is_neox_style | bool；True两半/False相邻 |
| output | 新连续Q[N,Q]、K/V[N,K]，输入dtype/device；N0新空三Tensor，输入不写 |

### 入口与版本

Direct签名(input,sin,cos,q_hidden_size,kv_hidden_size,head_dim,eps=None,q_weight=None,k_weight=None,q_bias=None,k_bias=None,is_neox_style=True)；冻结短路径加包名前缀精确。auto/triton转发，torch_native独立外部reference。SGLcommit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`，CANN9.1.0为README/CI配置，非本次环境；未固定完整Triton/CANN extension二进制。

## Host/Launcher 执行流程

### 参数校验与前处理

validate_split_qkv→qkv_shape/floating_tensor/positive_int→trig_tables→affine/epsilon/vector→is_neoxbool；launcherassertNPU，N0在此前校验后返回空输出，不查询核数。nonemptyhelper取P，g=Q/K，KVblock=D、Qblock=gD，分配三packed输出，nc=K/D，nr=ceil(P/nc)，grid(nr,nc,1)。原输入不连续化，validator要求已连续。断言依赖未启用Python-O。

### 参数、Workspace 与生命周期

无workspace/POD/ACLNN、无中间激活GM；output总N(Q+2K)dx B。helper无参cache取current_device、AIC/vector均assert正，无x.deviceguard，需相容设备属性。源码中weight/bias load位于行循环外；这里及各Route字节账均按源码层逻辑读取计算，不能直接代表编译后物理流量。无结果依赖的bias/表后半读取可能被优化消除；实际读取须固定工具链产物或测量证明。没有显式stream/wait/warp/stage；实际physicalallocation、异步Tensor存活/跨流规则归框架。

### 启动图与失败传播

import→校验树→NPUassert→N0空返回或helper/分配→单JITKernel的Q/K/V三阶段→返回。未使用全局空dict `kernels={}`作为实际缓存；实际JITcache归Triton。无CPUfallback或独立copyKernel；异常直接传播，包原生库加载仅导入前提。

## Route 与参数设计

### 分核与资源计算

nc=K/D完整KVheads；col j对应一个K/Vhead和g个连续Qhead。rowpid∈[0,nr)以nr步长遍历N，输出payload无重叠；nr*nc≥P且可能有rowpid≥N的空循环program。trig在Q/K每阶段每token/col重新读，affine每program各D项。Q/K块逻辑[g,D]/[1,D]。

### Route 选择

NORMS=eps非None，BIAS=q_bias非None，DO_PARTIAL=R≠D，DO_HALF=is_neox_style；四组合轴各二状态，总16。BIAStrue/NORMSfalse在源码中有bias load但结果不消费该值；优化后可消除，源码不保证实际设备读取。Host仍执行成对bias及元信息检查。H-000=N0无Device。

### 模板/实现执行矩阵

| Route | NORMS | BIAS | partial | NeoX |
|---|---|---|---|---|
| R-001 | false | false | false | true |
| R-002 | false | false | false | false |
| R-003 | false | false | true | true |
| R-004 | false | false | true | false |
| R-005 | false | true | false | true |
| R-006 | false | true | false | false |
| R-007 | false | true | true | true |
| R-008 | false | true | true | false |
| R-009 | true | false | false | true |
| R-010 | true | false | false | false |
| R-011 | true | false | true | true |
| R-012 | true | false | true | false |
| R-013 | true | true | false | true |
| R-014 | true | true | false | false |
| R-015 | true | true | true | true |
| R-016 | true | true | true | false |

input/表/启用affine可各独立三浮点dtype，Q/K输入/表/向量loadFP32、outputinputdtype；无tl.dot/Cube/AIC/MIX可达节点。无autotune，具体primitive物理分配外部。

### 隐藏性能 Guard

validator未检查D、R、gD的二次幂，但它们直接用于tl.arange（R/2也参与slice）；具体CANN Triton扩展是否支持是compiler准入边界，不能把任意合法正整数组合宣称可编译或反推必失败。Qblock=gD可随GQA组比放大，无UB查询。所有offset乘积须实际JIT类型可表示，行偏移没有显式int64转换。

### POD/ABI

| 字段 | 分类/消费 |
|---|---|
| input_ptr/sin_ptr/cos_ptr | runtimeTensor→packedload/trigload |
| q_ptr/k_ptr/v_ptr | runtime新输出→各store |
| q_weight_ptr/k_weight_ptr | runtime，可None；NORMStrue时各loadD |
| q_bias_ptr/k_bias_ptr | runtime，可None；BIAStrue时各loadD，不依赖NORMS |
| batch_size | runtimeN→row循环 |
| q_hidden_size/kv_hidden_size/total_hidden_size | constexprQ/K/Q+2K→colmask/段起点/步长 |
| eps | constexpr→NORMStrue分母，可None |
| Q_BLOCK_SIZE/KV_BLOCK_SIZE | constexprgD/D→arange/reshape |
| BIAS/NORMS | constexpr两flags→加载与计算分支 |
| HEAD_DIM/ROPE_DIM/HALF_ROPE_DIM | constexprD/R/R2→head归约/频率/配对 |
| PASS_DIM/DO_PARTIAL/DO_HALF | constexprD-R/部分旋转/配对模式→slice/insert |
| grid | (nr,nc,1) |

无自定义序列化POD/字段偏移；runtime指针/整数ABI归Triton，不虚构位宽。每个字段实际消费已列，未把装饰器当Hosttiling。

### Route 源码闭包

实现1–460行可达路径已完整读；norm_utils qkv_shape/trig_tables/affine及全部公共helper完整读。同文件Gemma入口在本图不可达。根setup→stage_runtime完整Python包→build_wheel/setup_refactor；norm/backendinit无Device。al.extract_slice/insert_slice是明确外部扩展primitive，不伪造其物理copy或别名合同。

## Kernel 实现

### 公共执行流程

Q向量加载/可选normaffine→两配对和部分旋转slice→store；独立K同构路径；Vcopy。所有读写仅该单Kernel，无GM统计、无自有跨核同步。

### Route R-001：norm=false bias=false partial=false neox=true

#### 适用条件

##### 选择证据

N>0，NORMS=(eps非None)=false，BIAS=(q_bias非None)=false，DO_PARTIAL=(R≠D)=false，DO_HALF=is_neox_style=true。R=D；bias须成对。具体arange/al.slice编译准入及资源另需实际工具链合同。

#### Device 数据流

##### 函数级调用链

`split_qkv_rmsnorm_rope→validate_split_qkv树→helper→split_qkv_rmsnorm_rope_kernel→Q阶段→K阶段→Vcopy`。load/reduce/sqrt/al.extract_slice/al.insert_slice/store是外部primitive，无另一自有Kernel。

##### 源码等价伪码

col j处理Q列[j*gD,(j+1)gD)内g个head及K/V第j个D列head；row r=rowpid+k*nr。Q/Kload转FP32、reshape[heads,D]；跳过norm，bias即使加载也不应用；整个D旋转，前后R/2配对rho=[-x2,x1]，完整sin/cos R列；FP32rope后store转输入dtype。V直接原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| Q/K值与norm/rope | Q逻辑[g,D]、K[1,D]FP32，单张量4gD/4D B；别名/峰值未知 |
| 旋转/切片 | Q[g,R]、K[1,R]；无pass；slice/insert的物理分配归compiler |
| sin/cos | 两阶段每token/col各读取完整R，两表字节宽ds/dc独立 |
| affine | 权重不读取；偏置不读取 |
| payloadGM | input与三输出各N*(Q+2K)*dx B |
| workspace/UB | 无显式分配/请求，物理资源外部 |

##### 分层内存布局

`GMpackedQKV→FP32Q[g,D]/K[1,D]→al.slice/rotation→低精度Q/KGM；V原值GMcopy`。Q/K阶段不同循环，不能从源码顺序保证物理buffer完全复用。

##### 字节账与复用顺序

以下为源码层静态逻辑口径；BIAS=true/NORMS=false的bias及GPT-J未使用表后半不保证编译后仍有物理读取。

完整有效payload读写2N(Q+2K)dx B；trig额外2N*nc*R*(ds+dc) B；affine读取如表（所有nr*nc program在行循环外load，即使其rowpid≥N）。此route总量相加，不假设cache/hoist或physicaltransaction。无中间GM/调用方workspace；输出新packedTensor，输入与参数异步生命周期归Torch/Triton，无显式free/wait。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 分核 | nr步长遍历token、nc完整head分列，地址不交叠，输出无atomic/barrier |
| head/tail | Q/K宽按完整head整除，colmask保护payload，trig R无mask依赖exact storage |
| norm/bias | inputFP32直接rope |
| pairing | NeoX两半，按每i对应表项 |
| partial | 全D旋转 |
| V | 同dtype直接load/store，不归一化/旋转 |
| compiler | SSA依赖与slice执行由Triton扩展负责，非二次幂D/R/gD准入未固定 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| Qnorm/rope | [Qbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L43-L199) |
| Knorm/rope/V | [K/Vbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L201-L372) |
| 四flags | [launch](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L424-L457) |


### Route R-002：norm=false bias=false partial=false neox=false

#### 适用条件

##### 选择证据

N>0，NORMS=(eps非None)=false，BIAS=(q_bias非None)=false，DO_PARTIAL=(R≠D)=false，DO_HALF=is_neox_style=false。R=D；bias须成对。具体arange/al.slice编译准入及资源另需实际工具链合同。

#### Device 数据流

##### 函数级调用链

`split_qkv_rmsnorm_rope→validate_split_qkv树→helper→split_qkv_rmsnorm_rope_kernel→Q阶段→K阶段→Vcopy`。load/reduce/sqrt/al.extract_slice/al.insert_slice/store是外部primitive，无另一自有Kernel。

##### 源码等价伪码

col j处理Q列[j*gD,(j+1)gD)内g个head及K/V第j个D列head；row r=rowpid+k*nr。Q/Kload转FP32、reshape[heads,D]；跳过norm，bias即使加载也不应用；整个D旋转，相邻偶奇配对rho=[-odd,even]，频率使用表前半并每值复制到偶/奇；FP32rope后store转输入dtype。V直接原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| Q/K值与norm/rope | Q逻辑[g,D]、K[1,D]FP32，单张量4gD/4D B；别名/峰值未知 |
| 旋转/切片 | Q[g,R]、K[1,R]；无pass；slice/insert的物理分配归compiler |
| sin/cos | 两阶段每token/col各读取完整R，两表字节宽ds/dc独立 |
| affine | 权重不读取；偏置不读取 |
| payloadGM | input与三输出各N*(Q+2K)*dx B |
| workspace/UB | 无显式分配/请求，物理资源外部 |

##### 分层内存布局

`GMpackedQKV→FP32Q[g,D]/K[1,D]→al.slice/rotation→低精度Q/KGM；V原值GMcopy`。Q/K阶段不同循环，不能从源码顺序保证物理buffer完全复用。

##### 字节账与复用顺序

以下为源码层静态逻辑口径；BIAS=true/NORMS=false的bias及GPT-J未使用表后半不保证编译后仍有物理读取。

完整有效payload读写2N(Q+2K)dx B；trig额外2N*nc*R*(ds+dc) B；affine读取如表（所有nr*nc program在行循环外load，即使其rowpid≥N）。此route总量相加，不假设cache/hoist或physicaltransaction。无中间GM/调用方workspace；输出新packedTensor，输入与参数异步生命周期归Torch/Triton，无显式free/wait。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 分核 | nr步长遍历token、nc完整head分列，地址不交叠，输出无atomic/barrier |
| head/tail | Q/K宽按完整head整除，colmask保护payload，trig R无mask依赖exact storage |
| norm/bias | inputFP32直接rope |
| pairing | GPT-J相邻，表后半有源码全宽load表达式但不参与结果，编译后物理读取未证明 |
| partial | 全D旋转 |
| V | 同dtype直接load/store，不归一化/旋转 |
| compiler | SSA依赖与slice执行由Triton扩展负责，非二次幂D/R/gD准入未固定 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| Qnorm/rope | [Qbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L43-L199) |
| Knorm/rope/V | [K/Vbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L201-L372) |
| 四flags | [launch](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L424-L457) |


### Route R-003：norm=false bias=false partial=true neox=true

#### 适用条件

##### 选择证据

N>0，NORMS=(eps非None)=false，BIAS=(q_bias非None)=false，DO_PARTIAL=(R≠D)=true，DO_HALF=is_neox_style=true。0<R<D；bias须成对。具体arange/al.slice编译准入及资源另需实际工具链合同。

#### Device 数据流

##### 函数级调用链

`split_qkv_rmsnorm_rope→validate_split_qkv树→helper→split_qkv_rmsnorm_rope_kernel→Q阶段→K阶段→Vcopy`。load/reduce/sqrt/al.extract_slice/al.insert_slice/store是外部primitive，无另一自有Kernel。

##### 源码等价伪码

col j处理Q列[j*gD,(j+1)gD)内g个head及K/V第j个D列head；row r=rowpid+k*nr。Q/Kload转FP32、reshape[heads,D]；跳过norm，bias即使加载也不应用；仅前R列旋转，pass[D-R]保留该时值，前后R/2配对rho=[-x2,x1]，完整sin/cos R列；FP32rope后store转输入dtype。V直接原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| Q/K值与norm/rope | Q逻辑[g,D]、K[1,D]FP32，单张量4gD/4D B；别名/峰值未知 |
| 旋转/切片 | Q[g,R]、K[1,R]；尾部[g,D-R]/[1,D-R]；slice/insert的物理分配归compiler |
| sin/cos | 两阶段每token/col各读取完整R，两表字节宽ds/dc独立 |
| affine | 权重不读取；偏置不读取 |
| payloadGM | input与三输出各N*(Q+2K)*dx B |
| workspace/UB | 无显式分配/请求，物理资源外部 |

##### 分层内存布局

`GMpackedQKV→FP32Q[g,D]/K[1,D]→al.slice/rotation→低精度Q/KGM；V原值GMcopy`。Q/K阶段不同循环，不能从源码顺序保证物理buffer完全复用。

##### 字节账与复用顺序

以下为源码层静态逻辑口径；BIAS=true/NORMS=false的bias及GPT-J未使用表后半不保证编译后仍有物理读取。

完整有效payload读写2N(Q+2K)dx B；trig额外2N*nc*R*(ds+dc) B；affine读取如表（所有nr*nc program在行循环外load，即使其rowpid≥N）。此route总量相加，不假设cache/hoist或physicaltransaction。无中间GM/调用方workspace；输出新packedTensor，输入与参数异步生命周期归Torch/Triton，无显式free/wait。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 分核 | nr步长遍历token、nc完整head分列，地址不交叠，输出无atomic/barrier |
| head/tail | Q/K宽按完整head整除，colmask保护payload，trig R无mask依赖exact storage |
| norm/bias | inputFP32直接rope |
| pairing | NeoX两半，按每i对应表项 |
| partial | 尾部保留归一化/原始FP32值后转outputdtype |
| V | 同dtype直接load/store，不归一化/旋转 |
| compiler | SSA依赖与slice执行由Triton扩展负责，非二次幂D/R/gD准入未固定 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| Qnorm/rope | [Qbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L43-L199) |
| Knorm/rope/V | [K/Vbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L201-L372) |
| 四flags | [launch](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L424-L457) |


### Route R-004：norm=false bias=false partial=true neox=false

#### 适用条件

##### 选择证据

N>0，NORMS=(eps非None)=false，BIAS=(q_bias非None)=false，DO_PARTIAL=(R≠D)=true，DO_HALF=is_neox_style=false。0<R<D；bias须成对。具体arange/al.slice编译准入及资源另需实际工具链合同。

#### Device 数据流

##### 函数级调用链

`split_qkv_rmsnorm_rope→validate_split_qkv树→helper→split_qkv_rmsnorm_rope_kernel→Q阶段→K阶段→Vcopy`。load/reduce/sqrt/al.extract_slice/al.insert_slice/store是外部primitive，无另一自有Kernel。

##### 源码等价伪码

col j处理Q列[j*gD,(j+1)gD)内g个head及K/V第j个D列head；row r=rowpid+k*nr。Q/Kload转FP32、reshape[heads,D]；跳过norm，bias即使加载也不应用；仅前R列旋转，pass[D-R]保留该时值，相邻偶奇配对rho=[-odd,even]，频率使用表前半并每值复制到偶/奇；FP32rope后store转输入dtype。V直接原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| Q/K值与norm/rope | Q逻辑[g,D]、K[1,D]FP32，单张量4gD/4D B；别名/峰值未知 |
| 旋转/切片 | Q[g,R]、K[1,R]；尾部[g,D-R]/[1,D-R]；slice/insert的物理分配归compiler |
| sin/cos | 两阶段每token/col各读取完整R，两表字节宽ds/dc独立 |
| affine | 权重不读取；偏置不读取 |
| payloadGM | input与三输出各N*(Q+2K)*dx B |
| workspace/UB | 无显式分配/请求，物理资源外部 |

##### 分层内存布局

`GMpackedQKV→FP32Q[g,D]/K[1,D]→al.slice/rotation→低精度Q/KGM；V原值GMcopy`。Q/K阶段不同循环，不能从源码顺序保证物理buffer完全复用。

##### 字节账与复用顺序

以下为源码层静态逻辑口径；BIAS=true/NORMS=false的bias及GPT-J未使用表后半不保证编译后仍有物理读取。

完整有效payload读写2N(Q+2K)dx B；trig额外2N*nc*R*(ds+dc) B；affine读取如表（所有nr*nc program在行循环外load，即使其rowpid≥N）。此route总量相加，不假设cache/hoist或physicaltransaction。无中间GM/调用方workspace；输出新packedTensor，输入与参数异步生命周期归Torch/Triton，无显式free/wait。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 分核 | nr步长遍历token、nc完整head分列，地址不交叠，输出无atomic/barrier |
| head/tail | Q/K宽按完整head整除，colmask保护payload，trig R无mask依赖exact storage |
| norm/bias | inputFP32直接rope |
| pairing | GPT-J相邻，表后半有源码全宽load表达式但不参与结果，编译后物理读取未证明 |
| partial | 尾部保留归一化/原始FP32值后转outputdtype |
| V | 同dtype直接load/store，不归一化/旋转 |
| compiler | SSA依赖与slice执行由Triton扩展负责，非二次幂D/R/gD准入未固定 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| Qnorm/rope | [Qbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L43-L199) |
| Knorm/rope/V | [K/Vbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L201-L372) |
| 四flags | [launch](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L424-L457) |


### Route R-005：norm=false bias=true partial=false neox=true

#### 适用条件

##### 选择证据

N>0，NORMS=(eps非None)=false，BIAS=(q_bias非None)=true，DO_PARTIAL=(R≠D)=false，DO_HALF=is_neox_style=true。R=D；bias须成对。具体arange/al.slice编译准入及资源另需实际工具链合同。

#### Device 数据流

##### 函数级调用链

`split_qkv_rmsnorm_rope→validate_split_qkv树→helper→split_qkv_rmsnorm_rope_kernel→Q阶段→K阶段→Vcopy`。load/reduce/sqrt/al.extract_slice/al.insert_slice/store是外部primitive，无另一自有Kernel。

##### 源码等价伪码

col j处理Q列[j*gD,(j+1)gD)内g个head及K/V第j个D列head；row r=rowpid+k*nr。Q/Kload转FP32、reshape[heads,D]；跳过norm，bias即使加载也不应用；整个D旋转，前后R/2配对rho=[-x2,x1]，完整sin/cos R列；FP32rope后store转输入dtype。V直接原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| Q/K值与norm/rope | Q逻辑[g,D]、K[1,D]FP32，单张量4gD/4D B；别名/峰值未知 |
| 旋转/切片 | Q[g,R]、K[1,R]；无pass；slice/insert的物理分配归compiler |
| sin/cos | 两阶段每token/col各读取完整R，两表字节宽ds/dc独立 |
| affine | 权重不读取；nr*nc*D*(dbq+dbk) B偏置读取（含idle rowprogram） |
| payloadGM | input与三输出各N*(Q+2K)*dx B |
| workspace/UB | 无显式分配/请求，物理资源外部 |

##### 分层内存布局

`GMpackedQKV→FP32Q[g,D]/K[1,D]→al.slice/rotation→低精度Q/KGM；V原值GMcopy`。Q/K阶段不同循环，不能从源码顺序保证物理buffer完全复用。

##### 字节账与复用顺序

以下为源码层静态逻辑口径；BIAS=true/NORMS=false的bias及GPT-J未使用表后半不保证编译后仍有物理读取。

完整有效payload读写2N(Q+2K)dx B；trig额外2N*nc*R*(ds+dc) B；affine读取如表（所有nr*nc program在行循环外load，即使其rowpid≥N）。此route总量相加，不假设cache/hoist或physicaltransaction。无中间GM/调用方workspace；输出新packedTensor，输入与参数异步生命周期归Torch/Triton，无显式free/wait。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 分核 | nr步长遍历token、nc完整head分列，地址不交叠，输出无atomic/barrier |
| head/tail | Q/K宽按完整head整除，colmask保护payload，trig R无mask依赖exact storage |
| norm/bias | bias有源码load表达式但不参与结果，物理读取可能被优化消除；inputFP32直接rope |
| pairing | NeoX两半，按每i对应表项 |
| partial | 全D旋转 |
| V | 同dtype直接load/store，不归一化/旋转 |
| compiler | SSA依赖与slice执行由Triton扩展负责，非二次幂D/R/gD准入未固定 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| Qnorm/rope | [Qbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L43-L199) |
| Knorm/rope/V | [K/Vbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L201-L372) |
| 四flags | [launch](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L424-L457) |


### Route R-006：norm=false bias=true partial=false neox=false

#### 适用条件

##### 选择证据

N>0，NORMS=(eps非None)=false，BIAS=(q_bias非None)=true，DO_PARTIAL=(R≠D)=false，DO_HALF=is_neox_style=false。R=D；bias须成对。具体arange/al.slice编译准入及资源另需实际工具链合同。

#### Device 数据流

##### 函数级调用链

`split_qkv_rmsnorm_rope→validate_split_qkv树→helper→split_qkv_rmsnorm_rope_kernel→Q阶段→K阶段→Vcopy`。load/reduce/sqrt/al.extract_slice/al.insert_slice/store是外部primitive，无另一自有Kernel。

##### 源码等价伪码

col j处理Q列[j*gD,(j+1)gD)内g个head及K/V第j个D列head；row r=rowpid+k*nr。Q/Kload转FP32、reshape[heads,D]；跳过norm，bias即使加载也不应用；整个D旋转，相邻偶奇配对rho=[-odd,even]，频率使用表前半并每值复制到偶/奇；FP32rope后store转输入dtype。V直接原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| Q/K值与norm/rope | Q逻辑[g,D]、K[1,D]FP32，单张量4gD/4D B；别名/峰值未知 |
| 旋转/切片 | Q[g,R]、K[1,R]；无pass；slice/insert的物理分配归compiler |
| sin/cos | 两阶段每token/col各读取完整R，两表字节宽ds/dc独立 |
| affine | 权重不读取；nr*nc*D*(dbq+dbk) B偏置读取（含idle rowprogram） |
| payloadGM | input与三输出各N*(Q+2K)*dx B |
| workspace/UB | 无显式分配/请求，物理资源外部 |

##### 分层内存布局

`GMpackedQKV→FP32Q[g,D]/K[1,D]→al.slice/rotation→低精度Q/KGM；V原值GMcopy`。Q/K阶段不同循环，不能从源码顺序保证物理buffer完全复用。

##### 字节账与复用顺序

以下为源码层静态逻辑口径；BIAS=true/NORMS=false的bias及GPT-J未使用表后半不保证编译后仍有物理读取。

完整有效payload读写2N(Q+2K)dx B；trig额外2N*nc*R*(ds+dc) B；affine读取如表（所有nr*nc program在行循环外load，即使其rowpid≥N）。此route总量相加，不假设cache/hoist或physicaltransaction。无中间GM/调用方workspace；输出新packedTensor，输入与参数异步生命周期归Torch/Triton，无显式free/wait。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 分核 | nr步长遍历token、nc完整head分列，地址不交叠，输出无atomic/barrier |
| head/tail | Q/K宽按完整head整除，colmask保护payload，trig R无mask依赖exact storage |
| norm/bias | bias有源码load表达式但不参与结果，物理读取可能被优化消除；inputFP32直接rope |
| pairing | GPT-J相邻，表后半有源码全宽load表达式但不参与结果，编译后物理读取未证明 |
| partial | 全D旋转 |
| V | 同dtype直接load/store，不归一化/旋转 |
| compiler | SSA依赖与slice执行由Triton扩展负责，非二次幂D/R/gD准入未固定 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| Qnorm/rope | [Qbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L43-L199) |
| Knorm/rope/V | [K/Vbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L201-L372) |
| 四flags | [launch](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L424-L457) |


### Route R-007：norm=false bias=true partial=true neox=true

#### 适用条件

##### 选择证据

N>0，NORMS=(eps非None)=false，BIAS=(q_bias非None)=true，DO_PARTIAL=(R≠D)=true，DO_HALF=is_neox_style=true。0<R<D；bias须成对。具体arange/al.slice编译准入及资源另需实际工具链合同。

#### Device 数据流

##### 函数级调用链

`split_qkv_rmsnorm_rope→validate_split_qkv树→helper→split_qkv_rmsnorm_rope_kernel→Q阶段→K阶段→Vcopy`。load/reduce/sqrt/al.extract_slice/al.insert_slice/store是外部primitive，无另一自有Kernel。

##### 源码等价伪码

col j处理Q列[j*gD,(j+1)gD)内g个head及K/V第j个D列head；row r=rowpid+k*nr。Q/Kload转FP32、reshape[heads,D]；跳过norm，bias即使加载也不应用；仅前R列旋转，pass[D-R]保留该时值，前后R/2配对rho=[-x2,x1]，完整sin/cos R列；FP32rope后store转输入dtype。V直接原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| Q/K值与norm/rope | Q逻辑[g,D]、K[1,D]FP32，单张量4gD/4D B；别名/峰值未知 |
| 旋转/切片 | Q[g,R]、K[1,R]；尾部[g,D-R]/[1,D-R]；slice/insert的物理分配归compiler |
| sin/cos | 两阶段每token/col各读取完整R，两表字节宽ds/dc独立 |
| affine | 权重不读取；nr*nc*D*(dbq+dbk) B偏置读取（含idle rowprogram） |
| payloadGM | input与三输出各N*(Q+2K)*dx B |
| workspace/UB | 无显式分配/请求，物理资源外部 |

##### 分层内存布局

`GMpackedQKV→FP32Q[g,D]/K[1,D]→al.slice/rotation→低精度Q/KGM；V原值GMcopy`。Q/K阶段不同循环，不能从源码顺序保证物理buffer完全复用。

##### 字节账与复用顺序

以下为源码层静态逻辑口径；BIAS=true/NORMS=false的bias及GPT-J未使用表后半不保证编译后仍有物理读取。

完整有效payload读写2N(Q+2K)dx B；trig额外2N*nc*R*(ds+dc) B；affine读取如表（所有nr*nc program在行循环外load，即使其rowpid≥N）。此route总量相加，不假设cache/hoist或physicaltransaction。无中间GM/调用方workspace；输出新packedTensor，输入与参数异步生命周期归Torch/Triton，无显式free/wait。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 分核 | nr步长遍历token、nc完整head分列，地址不交叠，输出无atomic/barrier |
| head/tail | Q/K宽按完整head整除，colmask保护payload，trig R无mask依赖exact storage |
| norm/bias | bias有源码load表达式但不参与结果，物理读取可能被优化消除；inputFP32直接rope |
| pairing | NeoX两半，按每i对应表项 |
| partial | 尾部保留归一化/原始FP32值后转outputdtype |
| V | 同dtype直接load/store，不归一化/旋转 |
| compiler | SSA依赖与slice执行由Triton扩展负责，非二次幂D/R/gD准入未固定 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| Qnorm/rope | [Qbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L43-L199) |
| Knorm/rope/V | [K/Vbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L201-L372) |
| 四flags | [launch](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L424-L457) |


### Route R-008：norm=false bias=true partial=true neox=false

#### 适用条件

##### 选择证据

N>0，NORMS=(eps非None)=false，BIAS=(q_bias非None)=true，DO_PARTIAL=(R≠D)=true，DO_HALF=is_neox_style=false。0<R<D；bias须成对。具体arange/al.slice编译准入及资源另需实际工具链合同。

#### Device 数据流

##### 函数级调用链

`split_qkv_rmsnorm_rope→validate_split_qkv树→helper→split_qkv_rmsnorm_rope_kernel→Q阶段→K阶段→Vcopy`。load/reduce/sqrt/al.extract_slice/al.insert_slice/store是外部primitive，无另一自有Kernel。

##### 源码等价伪码

col j处理Q列[j*gD,(j+1)gD)内g个head及K/V第j个D列head；row r=rowpid+k*nr。Q/Kload转FP32、reshape[heads,D]；跳过norm，bias即使加载也不应用；仅前R列旋转，pass[D-R]保留该时值，相邻偶奇配对rho=[-odd,even]，频率使用表前半并每值复制到偶/奇；FP32rope后store转输入dtype。V直接原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| Q/K值与norm/rope | Q逻辑[g,D]、K[1,D]FP32，单张量4gD/4D B；别名/峰值未知 |
| 旋转/切片 | Q[g,R]、K[1,R]；尾部[g,D-R]/[1,D-R]；slice/insert的物理分配归compiler |
| sin/cos | 两阶段每token/col各读取完整R，两表字节宽ds/dc独立 |
| affine | 权重不读取；nr*nc*D*(dbq+dbk) B偏置读取（含idle rowprogram） |
| payloadGM | input与三输出各N*(Q+2K)*dx B |
| workspace/UB | 无显式分配/请求，物理资源外部 |

##### 分层内存布局

`GMpackedQKV→FP32Q[g,D]/K[1,D]→al.slice/rotation→低精度Q/KGM；V原值GMcopy`。Q/K阶段不同循环，不能从源码顺序保证物理buffer完全复用。

##### 字节账与复用顺序

以下为源码层静态逻辑口径；BIAS=true/NORMS=false的bias及GPT-J未使用表后半不保证编译后仍有物理读取。

完整有效payload读写2N(Q+2K)dx B；trig额外2N*nc*R*(ds+dc) B；affine读取如表（所有nr*nc program在行循环外load，即使其rowpid≥N）。此route总量相加，不假设cache/hoist或physicaltransaction。无中间GM/调用方workspace；输出新packedTensor，输入与参数异步生命周期归Torch/Triton，无显式free/wait。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 分核 | nr步长遍历token、nc完整head分列，地址不交叠，输出无atomic/barrier |
| head/tail | Q/K宽按完整head整除，colmask保护payload，trig R无mask依赖exact storage |
| norm/bias | bias有源码load表达式但不参与结果，物理读取可能被优化消除；inputFP32直接rope |
| pairing | GPT-J相邻，表后半有源码全宽load表达式但不参与结果，编译后物理读取未证明 |
| partial | 尾部保留归一化/原始FP32值后转outputdtype |
| V | 同dtype直接load/store，不归一化/旋转 |
| compiler | SSA依赖与slice执行由Triton扩展负责，非二次幂D/R/gD准入未固定 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| Qnorm/rope | [Qbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L43-L199) |
| Knorm/rope/V | [K/Vbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L201-L372) |
| 四flags | [launch](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L424-L457) |


### Route R-009：norm=true bias=false partial=false neox=true

#### 适用条件

##### 选择证据

N>0，NORMS=(eps非None)=true，BIAS=(q_bias非None)=false，DO_PARTIAL=(R≠D)=false，DO_HALF=is_neox_style=true。R=D；bias须成对。具体arange/al.slice编译准入及资源另需实际工具链合同。

#### Device 数据流

##### 函数级调用链

`split_qkv_rmsnorm_rope→validate_split_qkv树→helper→split_qkv_rmsnorm_rope_kernel→Q阶段→K阶段→Vcopy`。load/reduce/sqrt/al.extract_slice/al.insert_slice/store是外部primitive，无另一自有Kernel。

##### 源码等价伪码

col j处理Q列[j*gD,(j+1)gD)内g个head及K/V第j个D列head；row r=rowpid+k*nr。Q/Kload转FP32、reshape[heads,D]；按headsum平方/D→1/sqrt(+eps)→乘weight；整个D旋转，前后R/2配对rho=[-x2,x1]，完整sin/cos R列；FP32rope后store转输入dtype。V直接原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| Q/K值与norm/rope | Q逻辑[g,D]、K[1,D]FP32，单张量4gD/4D B；别名/峰值未知 |
| 旋转/切片 | Q[g,R]、K[1,R]；无pass；slice/insert的物理分配归compiler |
| sin/cos | 两阶段每token/col各读取完整R，两表字节宽ds/dc独立 |
| affine | nr*nc*D*(dwq+dwk) B权重读取；偏置不读取 |
| payloadGM | input与三输出各N*(Q+2K)*dx B |
| workspace/UB | 无显式分配/请求，物理资源外部 |

##### 分层内存布局

`GMpackedQKV→FP32Q[g,D]/K[1,D]→RMSaffine→al.slice/rotation→低精度Q/KGM；V原值GMcopy`。Q/K阶段不同循环，不能从源码顺序保证物理buffer完全复用。

##### 字节账与复用顺序

以下为源码层静态逻辑口径；BIAS=true/NORMS=false的bias及GPT-J未使用表后半不保证编译后仍有物理读取。

完整有效payload读写2N(Q+2K)dx B；trig额外2N*nc*R*(ds+dc) B；affine读取如表（所有nr*nc program在行循环外load，即使其rowpid≥N）。此route总量相加，不假设cache/hoist或physicaltransaction。无中间GM/调用方workspace；输出新packedTensor，输入与参数异步生命周期归Torch/Triton，无显式free/wait。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 分核 | nr步长遍历token、nc完整head分列，地址不交叠，输出无atomic/barrier |
| head/tail | Q/K宽按完整head整除，colmask保护payload，trig R无mask依赖exact storage |
| norm/bias | FP32norm/affine后直接FP32rope，无中间低精度cast |
| pairing | NeoX两半，按每i对应表项 |
| partial | 全D旋转 |
| V | 同dtype直接load/store，不归一化/旋转 |
| compiler | SSA依赖与slice执行由Triton扩展负责，非二次幂D/R/gD准入未固定 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| Qnorm/rope | [Qbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L43-L199) |
| Knorm/rope/V | [K/Vbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L201-L372) |
| 四flags | [launch](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L424-L457) |


### Route R-010：norm=true bias=false partial=false neox=false

#### 适用条件

##### 选择证据

N>0，NORMS=(eps非None)=true，BIAS=(q_bias非None)=false，DO_PARTIAL=(R≠D)=false，DO_HALF=is_neox_style=false。R=D；bias须成对。具体arange/al.slice编译准入及资源另需实际工具链合同。

#### Device 数据流

##### 函数级调用链

`split_qkv_rmsnorm_rope→validate_split_qkv树→helper→split_qkv_rmsnorm_rope_kernel→Q阶段→K阶段→Vcopy`。load/reduce/sqrt/al.extract_slice/al.insert_slice/store是外部primitive，无另一自有Kernel。

##### 源码等价伪码

col j处理Q列[j*gD,(j+1)gD)内g个head及K/V第j个D列head；row r=rowpid+k*nr。Q/Kload转FP32、reshape[heads,D]；按headsum平方/D→1/sqrt(+eps)→乘weight；整个D旋转，相邻偶奇配对rho=[-odd,even]，频率使用表前半并每值复制到偶/奇；FP32rope后store转输入dtype。V直接原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| Q/K值与norm/rope | Q逻辑[g,D]、K[1,D]FP32，单张量4gD/4D B；别名/峰值未知 |
| 旋转/切片 | Q[g,R]、K[1,R]；无pass；slice/insert的物理分配归compiler |
| sin/cos | 两阶段每token/col各读取完整R，两表字节宽ds/dc独立 |
| affine | nr*nc*D*(dwq+dwk) B权重读取；偏置不读取 |
| payloadGM | input与三输出各N*(Q+2K)*dx B |
| workspace/UB | 无显式分配/请求，物理资源外部 |

##### 分层内存布局

`GMpackedQKV→FP32Q[g,D]/K[1,D]→RMSaffine→al.slice/rotation→低精度Q/KGM；V原值GMcopy`。Q/K阶段不同循环，不能从源码顺序保证物理buffer完全复用。

##### 字节账与复用顺序

以下为源码层静态逻辑口径；BIAS=true/NORMS=false的bias及GPT-J未使用表后半不保证编译后仍有物理读取。

完整有效payload读写2N(Q+2K)dx B；trig额外2N*nc*R*(ds+dc) B；affine读取如表（所有nr*nc program在行循环外load，即使其rowpid≥N）。此route总量相加，不假设cache/hoist或physicaltransaction。无中间GM/调用方workspace；输出新packedTensor，输入与参数异步生命周期归Torch/Triton，无显式free/wait。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 分核 | nr步长遍历token、nc完整head分列，地址不交叠，输出无atomic/barrier |
| head/tail | Q/K宽按完整head整除，colmask保护payload，trig R无mask依赖exact storage |
| norm/bias | FP32norm/affine后直接FP32rope，无中间低精度cast |
| pairing | GPT-J相邻，表后半有源码全宽load表达式但不参与结果，编译后物理读取未证明 |
| partial | 全D旋转 |
| V | 同dtype直接load/store，不归一化/旋转 |
| compiler | SSA依赖与slice执行由Triton扩展负责，非二次幂D/R/gD准入未固定 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| Qnorm/rope | [Qbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L43-L199) |
| Knorm/rope/V | [K/Vbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L201-L372) |
| 四flags | [launch](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L424-L457) |


### Route R-011：norm=true bias=false partial=true neox=true

#### 适用条件

##### 选择证据

N>0，NORMS=(eps非None)=true，BIAS=(q_bias非None)=false，DO_PARTIAL=(R≠D)=true，DO_HALF=is_neox_style=true。0<R<D；bias须成对。具体arange/al.slice编译准入及资源另需实际工具链合同。

#### Device 数据流

##### 函数级调用链

`split_qkv_rmsnorm_rope→validate_split_qkv树→helper→split_qkv_rmsnorm_rope_kernel→Q阶段→K阶段→Vcopy`。load/reduce/sqrt/al.extract_slice/al.insert_slice/store是外部primitive，无另一自有Kernel。

##### 源码等价伪码

col j处理Q列[j*gD,(j+1)gD)内g个head及K/V第j个D列head；row r=rowpid+k*nr。Q/Kload转FP32、reshape[heads,D]；按headsum平方/D→1/sqrt(+eps)→乘weight；仅前R列旋转，pass[D-R]保留该时值，前后R/2配对rho=[-x2,x1]，完整sin/cos R列；FP32rope后store转输入dtype。V直接原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| Q/K值与norm/rope | Q逻辑[g,D]、K[1,D]FP32，单张量4gD/4D B；别名/峰值未知 |
| 旋转/切片 | Q[g,R]、K[1,R]；尾部[g,D-R]/[1,D-R]；slice/insert的物理分配归compiler |
| sin/cos | 两阶段每token/col各读取完整R，两表字节宽ds/dc独立 |
| affine | nr*nc*D*(dwq+dwk) B权重读取；偏置不读取 |
| payloadGM | input与三输出各N*(Q+2K)*dx B |
| workspace/UB | 无显式分配/请求，物理资源外部 |

##### 分层内存布局

`GMpackedQKV→FP32Q[g,D]/K[1,D]→RMSaffine→al.slice/rotation→低精度Q/KGM；V原值GMcopy`。Q/K阶段不同循环，不能从源码顺序保证物理buffer完全复用。

##### 字节账与复用顺序

以下为源码层静态逻辑口径；BIAS=true/NORMS=false的bias及GPT-J未使用表后半不保证编译后仍有物理读取。

完整有效payload读写2N(Q+2K)dx B；trig额外2N*nc*R*(ds+dc) B；affine读取如表（所有nr*nc program在行循环外load，即使其rowpid≥N）。此route总量相加，不假设cache/hoist或physicaltransaction。无中间GM/调用方workspace；输出新packedTensor，输入与参数异步生命周期归Torch/Triton，无显式free/wait。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 分核 | nr步长遍历token、nc完整head分列，地址不交叠，输出无atomic/barrier |
| head/tail | Q/K宽按完整head整除，colmask保护payload，trig R无mask依赖exact storage |
| norm/bias | FP32norm/affine后直接FP32rope，无中间低精度cast |
| pairing | NeoX两半，按每i对应表项 |
| partial | 尾部保留归一化/原始FP32值后转outputdtype |
| V | 同dtype直接load/store，不归一化/旋转 |
| compiler | SSA依赖与slice执行由Triton扩展负责，非二次幂D/R/gD准入未固定 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| Qnorm/rope | [Qbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L43-L199) |
| Knorm/rope/V | [K/Vbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L201-L372) |
| 四flags | [launch](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L424-L457) |


### Route R-012：norm=true bias=false partial=true neox=false

#### 适用条件

##### 选择证据

N>0，NORMS=(eps非None)=true，BIAS=(q_bias非None)=false，DO_PARTIAL=(R≠D)=true，DO_HALF=is_neox_style=false。0<R<D；bias须成对。具体arange/al.slice编译准入及资源另需实际工具链合同。

#### Device 数据流

##### 函数级调用链

`split_qkv_rmsnorm_rope→validate_split_qkv树→helper→split_qkv_rmsnorm_rope_kernel→Q阶段→K阶段→Vcopy`。load/reduce/sqrt/al.extract_slice/al.insert_slice/store是外部primitive，无另一自有Kernel。

##### 源码等价伪码

col j处理Q列[j*gD,(j+1)gD)内g个head及K/V第j个D列head；row r=rowpid+k*nr。Q/Kload转FP32、reshape[heads,D]；按headsum平方/D→1/sqrt(+eps)→乘weight；仅前R列旋转，pass[D-R]保留该时值，相邻偶奇配对rho=[-odd,even]，频率使用表前半并每值复制到偶/奇；FP32rope后store转输入dtype。V直接原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| Q/K值与norm/rope | Q逻辑[g,D]、K[1,D]FP32，单张量4gD/4D B；别名/峰值未知 |
| 旋转/切片 | Q[g,R]、K[1,R]；尾部[g,D-R]/[1,D-R]；slice/insert的物理分配归compiler |
| sin/cos | 两阶段每token/col各读取完整R，两表字节宽ds/dc独立 |
| affine | nr*nc*D*(dwq+dwk) B权重读取；偏置不读取 |
| payloadGM | input与三输出各N*(Q+2K)*dx B |
| workspace/UB | 无显式分配/请求，物理资源外部 |

##### 分层内存布局

`GMpackedQKV→FP32Q[g,D]/K[1,D]→RMSaffine→al.slice/rotation→低精度Q/KGM；V原值GMcopy`。Q/K阶段不同循环，不能从源码顺序保证物理buffer完全复用。

##### 字节账与复用顺序

以下为源码层静态逻辑口径；BIAS=true/NORMS=false的bias及GPT-J未使用表后半不保证编译后仍有物理读取。

完整有效payload读写2N(Q+2K)dx B；trig额外2N*nc*R*(ds+dc) B；affine读取如表（所有nr*nc program在行循环外load，即使其rowpid≥N）。此route总量相加，不假设cache/hoist或physicaltransaction。无中间GM/调用方workspace；输出新packedTensor，输入与参数异步生命周期归Torch/Triton，无显式free/wait。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 分核 | nr步长遍历token、nc完整head分列，地址不交叠，输出无atomic/barrier |
| head/tail | Q/K宽按完整head整除，colmask保护payload，trig R无mask依赖exact storage |
| norm/bias | FP32norm/affine后直接FP32rope，无中间低精度cast |
| pairing | GPT-J相邻，表后半有源码全宽load表达式但不参与结果，编译后物理读取未证明 |
| partial | 尾部保留归一化/原始FP32值后转outputdtype |
| V | 同dtype直接load/store，不归一化/旋转 |
| compiler | SSA依赖与slice执行由Triton扩展负责，非二次幂D/R/gD准入未固定 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| Qnorm/rope | [Qbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L43-L199) |
| Knorm/rope/V | [K/Vbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L201-L372) |
| 四flags | [launch](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L424-L457) |


### Route R-013：norm=true bias=true partial=false neox=true

#### 适用条件

##### 选择证据

N>0，NORMS=(eps非None)=true，BIAS=(q_bias非None)=true，DO_PARTIAL=(R≠D)=false，DO_HALF=is_neox_style=true。R=D；bias须成对。具体arange/al.slice编译准入及资源另需实际工具链合同。

#### Device 数据流

##### 函数级调用链

`split_qkv_rmsnorm_rope→validate_split_qkv树→helper→split_qkv_rmsnorm_rope_kernel→Q阶段→K阶段→Vcopy`。load/reduce/sqrt/al.extract_slice/al.insert_slice/store是外部primitive，无另一自有Kernel。

##### 源码等价伪码

col j处理Q列[j*gD,(j+1)gD)内g个head及K/V第j个D列head；row r=rowpid+k*nr。Q/Kload转FP32、reshape[heads,D]；按headsum平方/D→1/sqrt(+eps)→乘weight加bias；整个D旋转，前后R/2配对rho=[-x2,x1]，完整sin/cos R列；FP32rope后store转输入dtype。V直接原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| Q/K值与norm/rope | Q逻辑[g,D]、K[1,D]FP32，单张量4gD/4D B；别名/峰值未知 |
| 旋转/切片 | Q[g,R]、K[1,R]；无pass；slice/insert的物理分配归compiler |
| sin/cos | 两阶段每token/col各读取完整R，两表字节宽ds/dc独立 |
| affine | nr*nc*D*(dwq+dwk) B权重读取；nr*nc*D*(dbq+dbk) B偏置读取（含idle rowprogram） |
| payloadGM | input与三输出各N*(Q+2K)*dx B |
| workspace/UB | 无显式分配/请求，物理资源外部 |

##### 分层内存布局

`GMpackedQKV→FP32Q[g,D]/K[1,D]→RMSaffine→al.slice/rotation→低精度Q/KGM；V原值GMcopy`。Q/K阶段不同循环，不能从源码顺序保证物理buffer完全复用。

##### 字节账与复用顺序

以下为源码层静态逻辑口径；BIAS=true/NORMS=false的bias及GPT-J未使用表后半不保证编译后仍有物理读取。

完整有效payload读写2N(Q+2K)dx B；trig额外2N*nc*R*(ds+dc) B；affine读取如表（所有nr*nc program在行循环外load，即使其rowpid≥N）。此route总量相加，不假设cache/hoist或physicaltransaction。无中间GM/调用方workspace；输出新packedTensor，输入与参数异步生命周期归Torch/Triton，无显式free/wait。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 分核 | nr步长遍历token、nc完整head分列，地址不交叠，输出无atomic/barrier |
| head/tail | Q/K宽按完整head整除，colmask保护payload，trig R无mask依赖exact storage |
| norm/bias | FP32norm/affine后直接FP32rope，无中间低精度cast |
| pairing | NeoX两半，按每i对应表项 |
| partial | 全D旋转 |
| V | 同dtype直接load/store，不归一化/旋转 |
| compiler | SSA依赖与slice执行由Triton扩展负责，非二次幂D/R/gD准入未固定 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| Qnorm/rope | [Qbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L43-L199) |
| Knorm/rope/V | [K/Vbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L201-L372) |
| 四flags | [launch](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L424-L457) |


### Route R-014：norm=true bias=true partial=false neox=false

#### 适用条件

##### 选择证据

N>0，NORMS=(eps非None)=true，BIAS=(q_bias非None)=true，DO_PARTIAL=(R≠D)=false，DO_HALF=is_neox_style=false。R=D；bias须成对。具体arange/al.slice编译准入及资源另需实际工具链合同。

#### Device 数据流

##### 函数级调用链

`split_qkv_rmsnorm_rope→validate_split_qkv树→helper→split_qkv_rmsnorm_rope_kernel→Q阶段→K阶段→Vcopy`。load/reduce/sqrt/al.extract_slice/al.insert_slice/store是外部primitive，无另一自有Kernel。

##### 源码等价伪码

col j处理Q列[j*gD,(j+1)gD)内g个head及K/V第j个D列head；row r=rowpid+k*nr。Q/Kload转FP32、reshape[heads,D]；按headsum平方/D→1/sqrt(+eps)→乘weight加bias；整个D旋转，相邻偶奇配对rho=[-odd,even]，频率使用表前半并每值复制到偶/奇；FP32rope后store转输入dtype。V直接原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| Q/K值与norm/rope | Q逻辑[g,D]、K[1,D]FP32，单张量4gD/4D B；别名/峰值未知 |
| 旋转/切片 | Q[g,R]、K[1,R]；无pass；slice/insert的物理分配归compiler |
| sin/cos | 两阶段每token/col各读取完整R，两表字节宽ds/dc独立 |
| affine | nr*nc*D*(dwq+dwk) B权重读取；nr*nc*D*(dbq+dbk) B偏置读取（含idle rowprogram） |
| payloadGM | input与三输出各N*(Q+2K)*dx B |
| workspace/UB | 无显式分配/请求，物理资源外部 |

##### 分层内存布局

`GMpackedQKV→FP32Q[g,D]/K[1,D]→RMSaffine→al.slice/rotation→低精度Q/KGM；V原值GMcopy`。Q/K阶段不同循环，不能从源码顺序保证物理buffer完全复用。

##### 字节账与复用顺序

以下为源码层静态逻辑口径；BIAS=true/NORMS=false的bias及GPT-J未使用表后半不保证编译后仍有物理读取。

完整有效payload读写2N(Q+2K)dx B；trig额外2N*nc*R*(ds+dc) B；affine读取如表（所有nr*nc program在行循环外load，即使其rowpid≥N）。此route总量相加，不假设cache/hoist或physicaltransaction。无中间GM/调用方workspace；输出新packedTensor，输入与参数异步生命周期归Torch/Triton，无显式free/wait。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 分核 | nr步长遍历token、nc完整head分列，地址不交叠，输出无atomic/barrier |
| head/tail | Q/K宽按完整head整除，colmask保护payload，trig R无mask依赖exact storage |
| norm/bias | FP32norm/affine后直接FP32rope，无中间低精度cast |
| pairing | GPT-J相邻，表后半有源码全宽load表达式但不参与结果，编译后物理读取未证明 |
| partial | 全D旋转 |
| V | 同dtype直接load/store，不归一化/旋转 |
| compiler | SSA依赖与slice执行由Triton扩展负责，非二次幂D/R/gD准入未固定 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| Qnorm/rope | [Qbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L43-L199) |
| Knorm/rope/V | [K/Vbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L201-L372) |
| 四flags | [launch](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L424-L457) |


### Route R-015：norm=true bias=true partial=true neox=true

#### 适用条件

##### 选择证据

N>0，NORMS=(eps非None)=true，BIAS=(q_bias非None)=true，DO_PARTIAL=(R≠D)=true，DO_HALF=is_neox_style=true。0<R<D；bias须成对。具体arange/al.slice编译准入及资源另需实际工具链合同。

#### Device 数据流

##### 函数级调用链

`split_qkv_rmsnorm_rope→validate_split_qkv树→helper→split_qkv_rmsnorm_rope_kernel→Q阶段→K阶段→Vcopy`。load/reduce/sqrt/al.extract_slice/al.insert_slice/store是外部primitive，无另一自有Kernel。

##### 源码等价伪码

col j处理Q列[j*gD,(j+1)gD)内g个head及K/V第j个D列head；row r=rowpid+k*nr。Q/Kload转FP32、reshape[heads,D]；按headsum平方/D→1/sqrt(+eps)→乘weight加bias；仅前R列旋转，pass[D-R]保留该时值，前后R/2配对rho=[-x2,x1]，完整sin/cos R列；FP32rope后store转输入dtype。V直接原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| Q/K值与norm/rope | Q逻辑[g,D]、K[1,D]FP32，单张量4gD/4D B；别名/峰值未知 |
| 旋转/切片 | Q[g,R]、K[1,R]；尾部[g,D-R]/[1,D-R]；slice/insert的物理分配归compiler |
| sin/cos | 两阶段每token/col各读取完整R，两表字节宽ds/dc独立 |
| affine | nr*nc*D*(dwq+dwk) B权重读取；nr*nc*D*(dbq+dbk) B偏置读取（含idle rowprogram） |
| payloadGM | input与三输出各N*(Q+2K)*dx B |
| workspace/UB | 无显式分配/请求，物理资源外部 |

##### 分层内存布局

`GMpackedQKV→FP32Q[g,D]/K[1,D]→RMSaffine→al.slice/rotation→低精度Q/KGM；V原值GMcopy`。Q/K阶段不同循环，不能从源码顺序保证物理buffer完全复用。

##### 字节账与复用顺序

以下为源码层静态逻辑口径；BIAS=true/NORMS=false的bias及GPT-J未使用表后半不保证编译后仍有物理读取。

完整有效payload读写2N(Q+2K)dx B；trig额外2N*nc*R*(ds+dc) B；affine读取如表（所有nr*nc program在行循环外load，即使其rowpid≥N）。此route总量相加，不假设cache/hoist或physicaltransaction。无中间GM/调用方workspace；输出新packedTensor，输入与参数异步生命周期归Torch/Triton，无显式free/wait。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 分核 | nr步长遍历token、nc完整head分列，地址不交叠，输出无atomic/barrier |
| head/tail | Q/K宽按完整head整除，colmask保护payload，trig R无mask依赖exact storage |
| norm/bias | FP32norm/affine后直接FP32rope，无中间低精度cast |
| pairing | NeoX两半，按每i对应表项 |
| partial | 尾部保留归一化/原始FP32值后转outputdtype |
| V | 同dtype直接load/store，不归一化/旋转 |
| compiler | SSA依赖与slice执行由Triton扩展负责，非二次幂D/R/gD准入未固定 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| Qnorm/rope | [Qbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L43-L199) |
| Knorm/rope/V | [K/Vbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L201-L372) |
| 四flags | [launch](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L424-L457) |


### Route R-016：norm=true bias=true partial=true neox=false

#### 适用条件

##### 选择证据

N>0，NORMS=(eps非None)=true，BIAS=(q_bias非None)=true，DO_PARTIAL=(R≠D)=true，DO_HALF=is_neox_style=false。0<R<D；bias须成对。具体arange/al.slice编译准入及资源另需实际工具链合同。

#### Device 数据流

##### 函数级调用链

`split_qkv_rmsnorm_rope→validate_split_qkv树→helper→split_qkv_rmsnorm_rope_kernel→Q阶段→K阶段→Vcopy`。load/reduce/sqrt/al.extract_slice/al.insert_slice/store是外部primitive，无另一自有Kernel。

##### 源码等价伪码

col j处理Q列[j*gD,(j+1)gD)内g个head及K/V第j个D列head；row r=rowpid+k*nr。Q/Kload转FP32、reshape[heads,D]；按headsum平方/D→1/sqrt(+eps)→乘weight加bias；仅前R列旋转，pass[D-R]保留该时值，相邻偶奇配对rho=[-odd,even]，频率使用表前半并每值复制到偶/奇；FP32rope后store转输入dtype。V直接原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/字节 |
|---|---|
| Q/K值与norm/rope | Q逻辑[g,D]、K[1,D]FP32，单张量4gD/4D B；别名/峰值未知 |
| 旋转/切片 | Q[g,R]、K[1,R]；尾部[g,D-R]/[1,D-R]；slice/insert的物理分配归compiler |
| sin/cos | 两阶段每token/col各读取完整R，两表字节宽ds/dc独立 |
| affine | nr*nc*D*(dwq+dwk) B权重读取；nr*nc*D*(dbq+dbk) B偏置读取（含idle rowprogram） |
| payloadGM | input与三输出各N*(Q+2K)*dx B |
| workspace/UB | 无显式分配/请求，物理资源外部 |

##### 分层内存布局

`GMpackedQKV→FP32Q[g,D]/K[1,D]→RMSaffine→al.slice/rotation→低精度Q/KGM；V原值GMcopy`。Q/K阶段不同循环，不能从源码顺序保证物理buffer完全复用。

##### 字节账与复用顺序

以下为源码层静态逻辑口径；BIAS=true/NORMS=false的bias及GPT-J未使用表后半不保证编译后仍有物理读取。

完整有效payload读写2N(Q+2K)dx B；trig额外2N*nc*R*(ds+dc) B；affine读取如表（所有nr*nc program在行循环外load，即使其rowpid≥N）。此route总量相加，不假设cache/hoist或physicaltransaction。无中间GM/调用方workspace；输出新packedTensor，输入与参数异步生命周期归Torch/Triton，无显式free/wait。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 分核 | nr步长遍历token、nc完整head分列，地址不交叠，输出无atomic/barrier |
| head/tail | Q/K宽按完整head整除，colmask保护payload，trig R无mask依赖exact storage |
| norm/bias | FP32norm/affine后直接FP32rope，无中间低精度cast |
| pairing | GPT-J相邻，表后半有源码全宽load表达式但不参与结果，编译后物理读取未证明 |
| partial | 尾部保留归一化/原始FP32值后转outputdtype |
| V | 同dtype直接load/store，不归一化/旋转 |
| compiler | SSA依赖与slice执行由Triton扩展负责，非二次幂D/R/gD准入未固定 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| Qnorm/rope | [Qbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L43-L199) |
| Knorm/rope/V | [K/Vbody](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L201-L372) |
| 四flags | [launch](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L424-L457) |

## 算子特定优化

### Trick T-001：KVhead分列使Q组与KVhead对应

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L415-L429)：

```python
    assert q_hidden_size % kv_hidden_size == 0
    Q_BLOCK_SIZE = q_hidden_size // kv_hidden_size * head_dim
    batch_size = input.shape[0]
    total_hidden_size = q_hidden_size + kv_hidden_size * 2
    q_output = torch.empty(
        batch_size, q_hidden_size, device=input.device, dtype=input.dtype
    )
    k_output = torch.empty(
        batch_size, kv_hidden_size, device=input.device, dtype=input.dtype
    )
    v_output = torch.empty(
        batch_size, kv_hidden_size, device=input.device, dtype=input.dtype
    )
    n_cols = kv_hidden_size // KV_BLOCK_SIZE
    n_rows = (num_vectorcore + n_cols - 1) // n_cols
```

#### 机制与设计原因

每列处理g个Qhead及一个KVhead，nr=ceil(P/nc)补行方向并以nr步长复用program；没有为Q、K、V单独launch。实际总program可能大于P，不能强称严格一核一program。

#### 迁移边界

Q/K及K/D必须整除，Qblock需满足实际arange/reshape合同；不同GQA比会改变资源大小。

#### 错误做法

将g当Qhead数量而忽略Khead列，或把nr*nc固定写成P。

### Trick T-002：GPT-J从表前半复制频率并用slice重排

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py#L80-L93)：

```python
        if not DO_HALF:
            sin_half = al.extract_slice(
                sin, offsets=(0, 0), sizes=(1, HALF_ROPE_DIM), strides=(1, 1)
            )
            cos_half = al.extract_slice(
                cos, offsets=(0, 0), sizes=(1, HALF_ROPE_DIM), strides=(1, 1)
            )
            sin = tl.zeros((1, ROPE_DIM), dtype=tl.float32)
            sin = al.insert_slice(
                sin, sin_half, offsets=(0, 0), sizes=(1, HALF_ROPE_DIM), strides=(1, 2)
            )
            sin = al.insert_slice(
                sin, sin_half, offsets=(0, 1), sizes=(1, HALF_ROPE_DIM), strides=(1, 2)
            )
```

#### 机制与设计原因

extract前半sin，再以stride2插入偶列和奇列，cos同构；匹配相邻通道旋转。源码表达式读取完整R表，后半无结果依赖，是否消除由编译器决定；不虚构slice为零拷贝/真实UB位置。

#### 迁移边界

NeoX与GPT-J两套配对必须和表布局一致，partial只改前R；normFP32→ropeFP32不添加低精度中间舍入。

#### 错误做法

把原表所有R项直接用于GPT-J或套入pos_cache_half两次BF16舍入。

## 模板与实现对比

16特化的norm/bias读集合、频率构造和partialtail不同，共用唯一逻辑QKV拆分可选RMS/RoPE；Gemma1+weight/gate和poscacheBF16语义独立，按后续冻结job处理。N0新空输出非别名。public重复半表是调用合同，validator只检查元信息。

## 平台差异

本卡950归属arch35；公开arch22/35支持同时写硬件待验证，README/architectures映射A2/A3和950。自有代码无硬件分支，CANN9.1.0 CI配置非本次运行/编译器一致性或A2实测。arange/al扩展及physical资源须以实际工具链核对。

## 限制与失败边界

元信息assert可关闭，未guard非二次幂准入、UB/寄存器资源或超大offset整数域；finite输入仍可FP32平方/score溢出，rope表值不做数值检查。未运行构建/Kernel/测试或校验，无真机/性能复现，draft保留条件而不修源。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开合同](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/split_qkv_rmsnorm_rope.md) | `split_qkv_rmsnorm_rope` | QKV/可选norm/两RoPE/硬件待验证 |
| [Direct及Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope.py) | `split_qkv_rmsnorm_rope[_kernel]` | 可达1–460行；Gemma同居非本入口 |
| [元信息树](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/norm_utils.py) | `validate_split_qkv/qkv_shape/trig_tables/affine/epsilon/vector` | 全部校验递归已读 |
| [公开转发](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/norm/split_qkv_rmsnorm_rope.py) | `_triton_impl` | auto/triton直达，独立reference |
| [属性helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py) | `get_device_properties` | 无参cache/currentdevice |
| [import边界](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py) | `_load_sgl_kernel_npu` | torch_npu/原生库与vendor初始化 |
| [backend包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py) | `module init` | 懒加载包，无另一Device节点 |
| [norm包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/__init__.py) | `module init` | 无附加启动节点 |
| [构建入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/setup.py) | `main` | 完整Python wheel路径；本次未构建 |
| [源码打包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/torch_wheel.py) | `stage_runtime/build_torch/build_wheel/setup_refactor` | 复制完整Python包、原生运行库与wheel |
| [平台/包说明](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md) | `REFACTOR/arch22/35 mapping` | 全部Python实现包含、产品映射、CANN9.1.0构建例 |
| [产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json) | `2201/3510` | a2/a3/950对应构建族 |
| [版本配置](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml) | `test-norm-ops` | CANN9.1.0/a3/950配置，非本次运行 |
| [CI消费](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernel-group.yml) | `run-kernel-group` | 对应版本容器/测试组参数 |

### 实现复用检查

冻结117/legacy同主题API与poscache相关API已全文读，前者链接复用，后者用于排除不同舍入语义。只新增本Direct两平台卡、无API覆盖，全部同repo固定source唯一primary、无verified。
