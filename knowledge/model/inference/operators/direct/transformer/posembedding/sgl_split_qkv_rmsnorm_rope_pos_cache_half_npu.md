---
type: Operator
title: "SplitQkvRmsnormRopePosCacheHalf A2/A3 Direct Invoke 算子知识"
description: "闭合位置cache QKV融合的16网格与舍入特化、自有RNE helper和int32后clamp，计入共享频率读取与连续化，保留物理编译边界。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/norm_utils.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py
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
created_at: "2026-11-09T09:44:35Z"
updated_at: "2026-11-09T09:44:35Z"
platforms: [a2, a3]
cann_versions: ["9.1.0"]
---

# SplitQkvRmsnormRopePosCacheHalf A2/A3 Direct Invoke 算子知识

## 算子速览

`sgl_kernel_npu.implementation.triton.norm.split_qkv_rmsnorm_rope_pos_cache_half_npu.split_qkv_rmsnorm_rope_pos_cache_half_npu`：QKV拆分、可选headRMSNorm、position选packedcache NeoX旋转；Q/K可选RoPE前RNEBF16，最终全head必经BF16再转inputdtype，V原值。两网格×norm×bias×preBF16共16特化、空Host及所有helper闭合。

draft明确arange/整数/physical资源和未运行边界；位置先int32再clamp、两舍入不能省略。已有[位置cache API](../../../../apis/sgl_kernel_npu/sgl_qkv_pos_cache_half.md)完整读并复用，普通RoPE/Gemma语义独立。

## 接口与语义

### 计算语义

input[N,Q+2K]按Q/K/V拆分，各headD；eps非None做FP32 `A=x*rsqrt(mean(x²)+eps)*w+b`，否则A=x。precast开关真则A经自有bitRNEBF16，否则保持FP32；前R NeoX两半用cache[p,:R/2]cos、cache[p,R/2:]sin旋转。旋转两半各toBF16，未旋转尾部也toBF16（开关真时已是BF16），最后全head转inputdtype。p=clamp(to_int32(position),0,M-1)。weight为已准备实际乘数，不再加1。V原dtype直接copy。

### 输入、输出与属性

| 项 | 元信息合同 |
|---|---|
| input | 连续strided三浮点dtype二维[N,Q+2K]，NPU |
| Q/K/D | 正Pythonint排bool、Q%K=0、K%D=0、D二次幂 |
| positions | stridedint32/int64同device，numel=N，可任意原shape；连续化后按线性读取 |
| cache | strided三浮点同device二维[M,R]，M>0；可非连续，将contiguous |
| rope_dim | None默认D，否则正偶R≤D且cache宽R；未guardR/2二次幂 |
| eps/affine | epsNone或有限正；启用norm则qw/kw连续numel≥D；bias必须成对，存在即检查，无norm也检查/加载 |
| precast/threshold | bool cast_norm_to_bf16默认True，positivePythonint threshold默认1024排bool |
| outputs | 新连续Q[N,Q],K/V[N,K]，inputdtype/device，输入参数不写，N0新空三Tensor |

### 入口与版本

Direct参数(input_tensor,positions,cos_sin_cache,Q,K,D,eps=None,q_weight=None,k_weight=None,q_bias=None,k_bias=None,rope_dim=None,cast_norm_to_bf16=True,wide_grid_min_tokens=1024)。冻结短路径加包名前缀精确；auto/triton转发、torch_native外部。SGLcommit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`，CANN9.1.0为README/CI配置非本次运行；完整Triton/CANNextension二进制未固定。

## Host/Launcher 执行流程

### 参数校验与前处理

validate_pos_cache递归qkv_shape/floating/positive、Dpow2、rope默认/正偶≤D、affine/epsilon/vector、positionsdtype/device/numel、cache形状、castbool、threshold正int；launcherassertNPU，N0返回三空Tensor。nonemptyhelperP，pos.contiguous、cache.contiguous；Host的pos非int32/int64再toint32分支在完整assert有效的合法输入域不可达，不能扩展公开支持float位置。

### 参数、Workspace 与生命周期

input必须已连续；pos/cache可能分配N*dpos/MR*dcache B临时，输出N(Q+2K)dx B，无GMnorm/score中间、无请求方workspace/POD/ACLNN。helper无参cache/current_device、双核数assert，需与input设备相容；无显式stream/wait/warp/stage，连续化copy→Kernel排序和异步释放归框架。Host再次weight/bias长度ValueError保护与先前assert重复，合法域同结果。

### 启动图与失败传播

import→validate树/NPU→N0空返回或helper→pos/cache连续化→网格选择→输出/向量guard→单JITKernel+可选自有RNEhelper→返回。无fallback/host位置数值回读，不用.any/.item做索引检测；异常传播。包原生库是导入前提，reference不补本图。

## Route 与参数设计

### 分核与资源计算

per-head：nc=K/D，nr=ceil(P/nc)，qb=(Q/K)D,kb=D；wide：nc1,nrP,qbQ,kbK。行rowpid以nr步长遍历N、col对应qb/kb列，Q/K/V均同row循环，position和cache每token/col只读一次共享Q/K。两网格不改变数学，只改变tile及重复元数据读量。

### Route 选择

wide当N≥threshold且Q≤8192，否则per-head；再norms=(eps非None)、bias=(q_bias非None)、precast bool三轴。R可全/部分但同insert路径，无DO_PARTIAL或GPT-J开关。H-000=N0无Device/连续化。

### 模板/实现执行矩阵

| Route | 网格 | norms | bias | preBF16 |
|---|---|---|---|---|
| R-001 | per-head | false | false | false |
| R-002 | per-head | false | false | true |
| R-003 | per-head | false | true | false |
| R-004 | per-head | false | true | true |
| R-005 | per-head | true | false | false |
| R-006 | per-head | true | false | true |
| R-007 | per-head | true | true | false |
| R-008 | per-head | true | true | true |
| R-009 | wide | false | false | false |
| R-010 | wide | false | false | true |
| R-011 | wide | false | true | false |
| R-012 | wide | false | true | true |
| R-013 | wide | true | false | false |
| R-014 | wide | true | false | true |
| R-015 | wide | true | true | false |
| R-016 | wide | true | true | true |

position两整数dtype、input/cache/启用affine独立三浮点dtype，读/舍入控制如各route。无tl.dot/Cube/AIC/MIX自有节点，具体physicalallocation与primitive为Triton外部边界。

### 隐藏性能 Guard

Q≤8192常量源于注释910B3宽tile编译观察，不是所有A2/A3/950的资源证明或本次复现；保留真实选择guard，不复述注释微秒/倍数为当前性能。Dpow2但qb/kb宽度、R/2直接arange未guard二次幂；具体扩展准入未知，不推定必失败。index先窄化再clamp不保证保持原int64位置语义；base=p*stride0、rowoffset需JIT整数可表示，未全显式int64化。

### POD/ABI

| 字段 | 类型/消费 |
|---|---|
| input_ptr/pos_ptr/cos_sin_cache_ptr | runtime输入→payload/位置/cacheload |
| q_ptr/k_ptr/v_ptr | runtimeoutput→store |
| q_weight_ptr/q_bias_ptr/k_weight_ptr/k_bias_ptr | runtime可None；norms读weight、biasflag独立读bias |
| batch_size | runtimeN→row循环 |
| q_hidden_size/kv_hidden_size/total_hidden_size | constexprQ/K/Q+2K→地址/边界 |
| eps | constexpr有效eps或None路径传0占位 |
| q_block_size/kv_block_size | constexprqb/kb→列arange/tile |
| q_block_n/k_block_n | constexprqb/D,kb/D→reshape |
| bias/norms | constexpr→加载/计算 |
| head_dim/rope_dim/half_rope_dim | constexprD/R/R2→归约/频率/配对 |
| cos_sin_stride0 | 连续cache行元素stride→position地址 |
| cast_norm_to_bf16 | constexpr→自有RNEhelper与y_base |
| max_seq | constexprM→positionclamp |
| grid | (nr,nc,1) |

无自定义序列化/字节offset；位宽明确的helperuint32/int32position及BF16节点如源码，其他JIT ABI不猜测。

### Route 源码闭包

433行完整读取，RNEhelper及validator树完整闭合，公开适配全文读取。根setup→stage_runtime完整Python包→build_wheel/setup_refactor，norm/backend包无Device；contiguous为外部框架copy，al.slice及物理allocation为primitive边界，不把它们当自有kernel体。

## Kernel 实现

### 公共执行流程

循环前load启用weight/bias（idleprogram也读）；一row循环先位置/cache，再Qnorm/optionalRNE/NeoX/finalBF16、K同构、Vcopy。biastrue/normsfalse仍读bias而不应用。16特化全部如下。

### Route R-001：per-head norms=false bias=false preBF16=false

#### 适用条件

##### 选择证据

N>0、N<threshold或Q>8192，norms=false（epsNone）、bias=false（成对bias无）、cast_norm_to_bf16=false。R正偶≤D，可全/部分旋转，不另有partial分支。

#### Device 数据流

##### 函数级调用链

`Direct→validate_pos_cache树→helper/contiguous→split_qkv_rmsnorm_rope_half_pos_cache_kernel→al.slice/NeoX/BF16cast/store`。一个自有Kernel，helper源码完整，不用Torchreference补舍入。

##### 源码等价伪码

grid=(ceil(P/(K/D)),K/D)，qb=(Q/K)D,kb=D。每col沿rowpid步长nr：读position转int32再clamp0..M-1，从cache同一行读cos/sin各R/2并共享Q/K；各Q/KloadFP32按head直接用x；保持y_baseFP32；前R转FP32切两半、NeoX旋转，结果toBF16；未旋转尾部先toBF16，insert回全head→转inputdtype/store。V原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/访问 |
|---|---|
| Q/Ktile | qb/kb FP32，4qb/4kb B逻辑；reshape[qb/D,D]/[kb/D,D] |
| RNE临时 | 不调用helper；不伪造物理多buffer |
| rope | 每head前R，o1/o2FP32后BF16ro1/ro2，wholeheadBF16y_out |
| position/cache | 每token/col读1*dpos+R*dcache B，共N*nc*(dpos+R*dcache) |
| affine | 0 B权重；0 B偏置（含空rowprogram） |
| GMpayload | input及输出各N(Q+2K)dx B，无GMnorm/rope中间 |
| workspace/UB | 无请求方workspace/显式物理分配；contiguous临时另计 |

##### 分层内存布局

`GMposition→int32clamp→GMpackedcache半cos/半sin→FP32freq共享；GMQ/K→FP32→FP32rope→BF16wholehead→inputdtypeGM；V原值copy`。compiler物理UB/register/alias/spill未知。

##### 字节账与复用顺序

Kernel逻辑总 `2N(Q+2K)dx + N*nc*(dpos+R*dcache)` B；nc=K/D，元数据随col重复，Q/K在一个row循环内共用频率。非连续pos/cache各临时N*dpos、M*R*dcache B，若copy发生各额外读/写同大小。输入/临时与output异步存活归框架，无显式workspace交接或free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 覆盖 | row轮转×完整head列，无共享写/atomics/barrier |
| 索引 | int64position先toint32再clamp，非对原int64直接clamp；cache地址p*stride0仍需实际JIT可表示 |
| norms/bias | 跳norm，实际weight已是乘数不加1 |
| 舍入 | RoPE前不降精度；最终所有Q/K含尾部BF16再转inputdtype |
| R尾 | al.insert前R，原base尾保持该路径BF16；无PASS_DIM0slice问题 |
| V | 原dtypecopy，不跟Q/KBF16舍入 |
| 工具链 | Dpow2已guard，但qb/kb、R/2arange准入与physical allocation外部 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| fp32_to_bf16_rne | [helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L19-L25) |
| Q/K/共享cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L67-L228) |
| grid/launch | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L337-L431) |


### Route R-002：per-head norms=false bias=false preBF16=true

#### 适用条件

##### 选择证据

N>0、N<threshold或Q>8192，norms=false（epsNone）、bias=false（成对bias无）、cast_norm_to_bf16=true。R正偶≤D，可全/部分旋转，不另有partial分支。

#### Device 数据流

##### 函数级调用链

`Direct→validate_pos_cache树→helper/contiguous→split_qkv_rmsnorm_rope_half_pos_cache_kernel→fp32_to_bf16_rne→al.slice/NeoX/BF16cast/store`。一个自有Kernel，helper源码完整，不用Torchreference补舍入。

##### 源码等价伪码

grid=(ceil(P/(K/D)),K/D)，qb=(Q/K)D,kb=D。每col沿rowpid步长nr：读position转int32再clamp0..M-1，从cache同一行读cos/sin各R/2并共享Q/K；各Q/KloadFP32按head直接用x；调用bit-level RNE得BF16 y_base；前R转FP32切两半、NeoX旋转，结果toBF16；未旋转尾部保留y_baseBF16，insert回全head→转inputdtype/store。V原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/访问 |
|---|---|
| Q/Ktile | qb/kb FP32，4qb/4kb B逻辑；reshape[qb/D,D]/[kb/D,D] |
| RNE临时 | uint32位视图/lsb/u加法及BF16 y_base，均任务SSA；不伪造物理多buffer |
| rope | 每head前R，o1/o2FP32后BF16ro1/ro2，wholeheadBF16y_out |
| position/cache | 每token/col读1*dpos+R*dcache B，共N*nc*(dpos+R*dcache) |
| affine | 0 B权重；0 B偏置（含空rowprogram） |
| GMpayload | input及输出各N(Q+2K)dx B，无GMnorm/rope中间 |
| workspace/UB | 无请求方workspace/显式物理分配；contiguous临时另计 |

##### 分层内存布局

`GMposition→int32clamp→GMpackedcache半cos/半sin→FP32freq共享；GMQ/K→FP32→RNEBF16→FP32rope→BF16wholehead→inputdtypeGM；V原值copy`。compiler物理UB/register/alias/spill未知。

##### 字节账与复用顺序

Kernel逻辑总 `2N(Q+2K)dx + N*nc*(dpos+R*dcache)` B；nc=K/D，元数据随col重复，Q/K在一个row循环内共用频率。非连续pos/cache各临时N*dpos、M*R*dcache B，若copy发生各额外读/写同大小。输入/临时与output异步存活归框架，无显式workspace交接或free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 覆盖 | row轮转×完整head列，无共享写/atomics/barrier |
| 索引 | int64position先toint32再clamp，非对原int64直接clamp；cache地址p*stride0仍需实际JIT可表示 |
| norms/bias | 跳norm，实际weight已是乘数不加1 |
| 舍入 | RoPE前bitRNEBF16（epsNone亦生效）；最终所有Q/K含尾部BF16再转inputdtype |
| R尾 | al.insert前R，原base尾保持该路径BF16；无PASS_DIM0slice问题 |
| V | 原dtypecopy，不跟Q/KBF16舍入 |
| 工具链 | Dpow2已guard，但qb/kb、R/2arange准入与physical allocation外部 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| fp32_to_bf16_rne | [helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L19-L25) |
| Q/K/共享cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L67-L228) |
| grid/launch | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L337-L431) |


### Route R-003：per-head norms=false bias=true preBF16=false

#### 适用条件

##### 选择证据

N>0、N<threshold或Q>8192，norms=false（epsNone）、bias=true（成对bias存在）、cast_norm_to_bf16=false。R正偶≤D，可全/部分旋转，不另有partial分支。

#### Device 数据流

##### 函数级调用链

`Direct→validate_pos_cache树→helper/contiguous→split_qkv_rmsnorm_rope_half_pos_cache_kernel→al.slice/NeoX/BF16cast/store`。一个自有Kernel，helper源码完整，不用Torchreference补舍入。

##### 源码等价伪码

grid=(ceil(P/(K/D)),K/D)，qb=(Q/K)D,kb=D。每col沿rowpid步长nr：读position转int32再clamp0..M-1，从cache同一行读cos/sin各R/2并共享Q/K；各Q/KloadFP32按head直接用x；保持y_baseFP32；前R转FP32切两半、NeoX旋转，结果toBF16；未旋转尾部先toBF16，insert回全head→转inputdtype/store。V原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/访问 |
|---|---|
| Q/Ktile | qb/kb FP32，4qb/4kb B逻辑；reshape[qb/D,D]/[kb/D,D] |
| RNE临时 | 不调用helper；不伪造物理多buffer |
| rope | 每head前R，o1/o2FP32后BF16ro1/ro2，wholeheadBF16y_out |
| position/cache | 每token/col读1*dpos+R*dcache B，共N*nc*(dpos+R*dcache) |
| affine | 0 B权重；nr*nc*D*(dbq+dbk) B偏置（含空rowprogram） |
| GMpayload | input及输出各N(Q+2K)dx B，无GMnorm/rope中间 |
| workspace/UB | 无请求方workspace/显式物理分配；contiguous临时另计 |

##### 分层内存布局

`GMposition→int32clamp→GMpackedcache半cos/半sin→FP32freq共享；GMQ/K→FP32→FP32rope→BF16wholehead→inputdtypeGM；V原值copy`。compiler物理UB/register/alias/spill未知。

##### 字节账与复用顺序

Kernel逻辑总 `2N(Q+2K)dx + N*nc*(dpos+R*dcache)+nr*nc*D*(dbq+dbk)` B；nc=K/D，元数据随col重复，Q/K在一个row循环内共用频率。非连续pos/cache各临时N*dpos、M*R*dcache B，若copy发生各额外读/写同大小。输入/临时与output异步存活归框架，无显式workspace交接或free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 覆盖 | row轮转×完整head列，无共享写/atomics/barrier |
| 索引 | int64position先toint32再clamp，非对原int64直接clamp；cache地址p*stride0仍需实际JIT可表示 |
| norms/bias | bias虽load但不应用，实际weight已是乘数不加1 |
| 舍入 | RoPE前不降精度；最终所有Q/K含尾部BF16再转inputdtype |
| R尾 | al.insert前R，原base尾保持该路径BF16；无PASS_DIM0slice问题 |
| V | 原dtypecopy，不跟Q/KBF16舍入 |
| 工具链 | Dpow2已guard，但qb/kb、R/2arange准入与physical allocation外部 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| fp32_to_bf16_rne | [helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L19-L25) |
| Q/K/共享cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L67-L228) |
| grid/launch | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L337-L431) |


### Route R-004：per-head norms=false bias=true preBF16=true

#### 适用条件

##### 选择证据

N>0、N<threshold或Q>8192，norms=false（epsNone）、bias=true（成对bias存在）、cast_norm_to_bf16=true。R正偶≤D，可全/部分旋转，不另有partial分支。

#### Device 数据流

##### 函数级调用链

`Direct→validate_pos_cache树→helper/contiguous→split_qkv_rmsnorm_rope_half_pos_cache_kernel→fp32_to_bf16_rne→al.slice/NeoX/BF16cast/store`。一个自有Kernel，helper源码完整，不用Torchreference补舍入。

##### 源码等价伪码

grid=(ceil(P/(K/D)),K/D)，qb=(Q/K)D,kb=D。每col沿rowpid步长nr：读position转int32再clamp0..M-1，从cache同一行读cos/sin各R/2并共享Q/K；各Q/KloadFP32按head直接用x；调用bit-level RNE得BF16 y_base；前R转FP32切两半、NeoX旋转，结果toBF16；未旋转尾部保留y_baseBF16，insert回全head→转inputdtype/store。V原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/访问 |
|---|---|
| Q/Ktile | qb/kb FP32，4qb/4kb B逻辑；reshape[qb/D,D]/[kb/D,D] |
| RNE临时 | uint32位视图/lsb/u加法及BF16 y_base，均任务SSA；不伪造物理多buffer |
| rope | 每head前R，o1/o2FP32后BF16ro1/ro2，wholeheadBF16y_out |
| position/cache | 每token/col读1*dpos+R*dcache B，共N*nc*(dpos+R*dcache) |
| affine | 0 B权重；nr*nc*D*(dbq+dbk) B偏置（含空rowprogram） |
| GMpayload | input及输出各N(Q+2K)dx B，无GMnorm/rope中间 |
| workspace/UB | 无请求方workspace/显式物理分配；contiguous临时另计 |

##### 分层内存布局

`GMposition→int32clamp→GMpackedcache半cos/半sin→FP32freq共享；GMQ/K→FP32→RNEBF16→FP32rope→BF16wholehead→inputdtypeGM；V原值copy`。compiler物理UB/register/alias/spill未知。

##### 字节账与复用顺序

Kernel逻辑总 `2N(Q+2K)dx + N*nc*(dpos+R*dcache)+nr*nc*D*(dbq+dbk)` B；nc=K/D，元数据随col重复，Q/K在一个row循环内共用频率。非连续pos/cache各临时N*dpos、M*R*dcache B，若copy发生各额外读/写同大小。输入/临时与output异步存活归框架，无显式workspace交接或free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 覆盖 | row轮转×完整head列，无共享写/atomics/barrier |
| 索引 | int64position先toint32再clamp，非对原int64直接clamp；cache地址p*stride0仍需实际JIT可表示 |
| norms/bias | bias虽load但不应用，实际weight已是乘数不加1 |
| 舍入 | RoPE前bitRNEBF16（epsNone亦生效）；最终所有Q/K含尾部BF16再转inputdtype |
| R尾 | al.insert前R，原base尾保持该路径BF16；无PASS_DIM0slice问题 |
| V | 原dtypecopy，不跟Q/KBF16舍入 |
| 工具链 | Dpow2已guard，但qb/kb、R/2arange准入与physical allocation外部 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| fp32_to_bf16_rne | [helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L19-L25) |
| Q/K/共享cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L67-L228) |
| grid/launch | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L337-L431) |


### Route R-005：per-head norms=true bias=false preBF16=false

#### 适用条件

##### 选择证据

N>0、N<threshold或Q>8192，norms=true（eps非None）、bias=false（成对bias无）、cast_norm_to_bf16=false。R正偶≤D，可全/部分旋转，不另有partial分支。

#### Device 数据流

##### 函数级调用链

`Direct→validate_pos_cache树→helper/contiguous→split_qkv_rmsnorm_rope_half_pos_cache_kernel→al.slice/NeoX/BF16cast/store`。一个自有Kernel，helper源码完整，不用Torchreference补舍入。

##### 源码等价伪码

grid=(ceil(P/(K/D)),K/D)，qb=(Q/K)D,kb=D。每col沿rowpid步长nr：读position转int32再clamp0..M-1，从cache同一行读cos/sin各R/2并共享Q/K；各Q/KloadFP32按headRMSnorm×w；保持y_baseFP32；前R转FP32切两半、NeoX旋转，结果toBF16；未旋转尾部先toBF16，insert回全head→转inputdtype/store。V原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/访问 |
|---|---|
| Q/Ktile | qb/kb FP32，4qb/4kb B逻辑；reshape[qb/D,D]/[kb/D,D] |
| RNE临时 | 不调用helper；不伪造物理多buffer |
| rope | 每head前R，o1/o2FP32后BF16ro1/ro2，wholeheadBF16y_out |
| position/cache | 每token/col读1*dpos+R*dcache B，共N*nc*(dpos+R*dcache) |
| affine | nr*nc*D*(dwq+dwk) B权重；0 B偏置（含空rowprogram） |
| GMpayload | input及输出各N(Q+2K)dx B，无GMnorm/rope中间 |
| workspace/UB | 无请求方workspace/显式物理分配；contiguous临时另计 |

##### 分层内存布局

`GMposition→int32clamp→GMpackedcache半cos/半sin→FP32freq共享；GMQ/K→FP32normaffine→FP32rope→BF16wholehead→inputdtypeGM；V原值copy`。compiler物理UB/register/alias/spill未知。

##### 字节账与复用顺序

Kernel逻辑总 `2N(Q+2K)dx + N*nc*(dpos+R*dcache)+nr*nc*D*(dwq+dwk)` B；nc=K/D，元数据随col重复，Q/K在一个row循环内共用频率。非连续pos/cache各临时N*dpos、M*R*dcache B，若copy发生各额外读/写同大小。输入/临时与output异步存活归框架，无显式workspace交接或free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 覆盖 | row轮转×完整head列，无共享写/atomics/barrier |
| 索引 | int64position先toint32再clamp，非对原int64直接clamp；cache地址p*stride0仍需实际JIT可表示 |
| norms/bias | FP32norm/rsqrt/affine，实际weight已是乘数不加1 |
| 舍入 | RoPE前不降精度；最终所有Q/K含尾部BF16再转inputdtype |
| R尾 | al.insert前R，原base尾保持该路径BF16；无PASS_DIM0slice问题 |
| V | 原dtypecopy，不跟Q/KBF16舍入 |
| 工具链 | Dpow2已guard，但qb/kb、R/2arange准入与physical allocation外部 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| fp32_to_bf16_rne | [helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L19-L25) |
| Q/K/共享cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L67-L228) |
| grid/launch | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L337-L431) |


### Route R-006：per-head norms=true bias=false preBF16=true

#### 适用条件

##### 选择证据

N>0、N<threshold或Q>8192，norms=true（eps非None）、bias=false（成对bias无）、cast_norm_to_bf16=true。R正偶≤D，可全/部分旋转，不另有partial分支。

#### Device 数据流

##### 函数级调用链

`Direct→validate_pos_cache树→helper/contiguous→split_qkv_rmsnorm_rope_half_pos_cache_kernel→fp32_to_bf16_rne→al.slice/NeoX/BF16cast/store`。一个自有Kernel，helper源码完整，不用Torchreference补舍入。

##### 源码等价伪码

grid=(ceil(P/(K/D)),K/D)，qb=(Q/K)D,kb=D。每col沿rowpid步长nr：读position转int32再clamp0..M-1，从cache同一行读cos/sin各R/2并共享Q/K；各Q/KloadFP32按headRMSnorm×w；调用bit-level RNE得BF16 y_base；前R转FP32切两半、NeoX旋转，结果toBF16；未旋转尾部保留y_baseBF16，insert回全head→转inputdtype/store。V原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/访问 |
|---|---|
| Q/Ktile | qb/kb FP32，4qb/4kb B逻辑；reshape[qb/D,D]/[kb/D,D] |
| RNE临时 | uint32位视图/lsb/u加法及BF16 y_base，均任务SSA；不伪造物理多buffer |
| rope | 每head前R，o1/o2FP32后BF16ro1/ro2，wholeheadBF16y_out |
| position/cache | 每token/col读1*dpos+R*dcache B，共N*nc*(dpos+R*dcache) |
| affine | nr*nc*D*(dwq+dwk) B权重；0 B偏置（含空rowprogram） |
| GMpayload | input及输出各N(Q+2K)dx B，无GMnorm/rope中间 |
| workspace/UB | 无请求方workspace/显式物理分配；contiguous临时另计 |

##### 分层内存布局

`GMposition→int32clamp→GMpackedcache半cos/半sin→FP32freq共享；GMQ/K→FP32normaffine→RNEBF16→FP32rope→BF16wholehead→inputdtypeGM；V原值copy`。compiler物理UB/register/alias/spill未知。

##### 字节账与复用顺序

Kernel逻辑总 `2N(Q+2K)dx + N*nc*(dpos+R*dcache)+nr*nc*D*(dwq+dwk)` B；nc=K/D，元数据随col重复，Q/K在一个row循环内共用频率。非连续pos/cache各临时N*dpos、M*R*dcache B，若copy发生各额外读/写同大小。输入/临时与output异步存活归框架，无显式workspace交接或free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 覆盖 | row轮转×完整head列，无共享写/atomics/barrier |
| 索引 | int64position先toint32再clamp，非对原int64直接clamp；cache地址p*stride0仍需实际JIT可表示 |
| norms/bias | FP32norm/rsqrt/affine，实际weight已是乘数不加1 |
| 舍入 | RoPE前bitRNEBF16（epsNone亦生效）；最终所有Q/K含尾部BF16再转inputdtype |
| R尾 | al.insert前R，原base尾保持该路径BF16；无PASS_DIM0slice问题 |
| V | 原dtypecopy，不跟Q/KBF16舍入 |
| 工具链 | Dpow2已guard，但qb/kb、R/2arange准入与physical allocation外部 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| fp32_to_bf16_rne | [helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L19-L25) |
| Q/K/共享cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L67-L228) |
| grid/launch | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L337-L431) |


### Route R-007：per-head norms=true bias=true preBF16=false

#### 适用条件

##### 选择证据

N>0、N<threshold或Q>8192，norms=true（eps非None）、bias=true（成对bias存在）、cast_norm_to_bf16=false。R正偶≤D，可全/部分旋转，不另有partial分支。

#### Device 数据流

##### 函数级调用链

`Direct→validate_pos_cache树→helper/contiguous→split_qkv_rmsnorm_rope_half_pos_cache_kernel→al.slice/NeoX/BF16cast/store`。一个自有Kernel，helper源码完整，不用Torchreference补舍入。

##### 源码等价伪码

grid=(ceil(P/(K/D)),K/D)，qb=(Q/K)D,kb=D。每col沿rowpid步长nr：读position转int32再clamp0..M-1，从cache同一行读cos/sin各R/2并共享Q/K；各Q/KloadFP32按headRMSnorm×w+b；保持y_baseFP32；前R转FP32切两半、NeoX旋转，结果toBF16；未旋转尾部先toBF16，insert回全head→转inputdtype/store。V原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/访问 |
|---|---|
| Q/Ktile | qb/kb FP32，4qb/4kb B逻辑；reshape[qb/D,D]/[kb/D,D] |
| RNE临时 | 不调用helper；不伪造物理多buffer |
| rope | 每head前R，o1/o2FP32后BF16ro1/ro2，wholeheadBF16y_out |
| position/cache | 每token/col读1*dpos+R*dcache B，共N*nc*(dpos+R*dcache) |
| affine | nr*nc*D*(dwq+dwk) B权重；nr*nc*D*(dbq+dbk) B偏置（含空rowprogram） |
| GMpayload | input及输出各N(Q+2K)dx B，无GMnorm/rope中间 |
| workspace/UB | 无请求方workspace/显式物理分配；contiguous临时另计 |

##### 分层内存布局

`GMposition→int32clamp→GMpackedcache半cos/半sin→FP32freq共享；GMQ/K→FP32normaffine→FP32rope→BF16wholehead→inputdtypeGM；V原值copy`。compiler物理UB/register/alias/spill未知。

##### 字节账与复用顺序

Kernel逻辑总 `2N(Q+2K)dx + N*nc*(dpos+R*dcache)+nr*nc*D*(dwq+dwk)+nr*nc*D*(dbq+dbk)` B；nc=K/D，元数据随col重复，Q/K在一个row循环内共用频率。非连续pos/cache各临时N*dpos、M*R*dcache B，若copy发生各额外读/写同大小。输入/临时与output异步存活归框架，无显式workspace交接或free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 覆盖 | row轮转×完整head列，无共享写/atomics/barrier |
| 索引 | int64position先toint32再clamp，非对原int64直接clamp；cache地址p*stride0仍需实际JIT可表示 |
| norms/bias | FP32norm/rsqrt/affine，实际weight已是乘数不加1 |
| 舍入 | RoPE前不降精度；最终所有Q/K含尾部BF16再转inputdtype |
| R尾 | al.insert前R，原base尾保持该路径BF16；无PASS_DIM0slice问题 |
| V | 原dtypecopy，不跟Q/KBF16舍入 |
| 工具链 | Dpow2已guard，但qb/kb、R/2arange准入与physical allocation外部 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| fp32_to_bf16_rne | [helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L19-L25) |
| Q/K/共享cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L67-L228) |
| grid/launch | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L337-L431) |


### Route R-008：per-head norms=true bias=true preBF16=true

#### 适用条件

##### 选择证据

N>0、N<threshold或Q>8192，norms=true（eps非None）、bias=true（成对bias存在）、cast_norm_to_bf16=true。R正偶≤D，可全/部分旋转，不另有partial分支。

#### Device 数据流

##### 函数级调用链

`Direct→validate_pos_cache树→helper/contiguous→split_qkv_rmsnorm_rope_half_pos_cache_kernel→fp32_to_bf16_rne→al.slice/NeoX/BF16cast/store`。一个自有Kernel，helper源码完整，不用Torchreference补舍入。

##### 源码等价伪码

grid=(ceil(P/(K/D)),K/D)，qb=(Q/K)D,kb=D。每col沿rowpid步长nr：读position转int32再clamp0..M-1，从cache同一行读cos/sin各R/2并共享Q/K；各Q/KloadFP32按headRMSnorm×w+b；调用bit-level RNE得BF16 y_base；前R转FP32切两半、NeoX旋转，结果toBF16；未旋转尾部保留y_baseBF16，insert回全head→转inputdtype/store。V原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/访问 |
|---|---|
| Q/Ktile | qb/kb FP32，4qb/4kb B逻辑；reshape[qb/D,D]/[kb/D,D] |
| RNE临时 | uint32位视图/lsb/u加法及BF16 y_base，均任务SSA；不伪造物理多buffer |
| rope | 每head前R，o1/o2FP32后BF16ro1/ro2，wholeheadBF16y_out |
| position/cache | 每token/col读1*dpos+R*dcache B，共N*nc*(dpos+R*dcache) |
| affine | nr*nc*D*(dwq+dwk) B权重；nr*nc*D*(dbq+dbk) B偏置（含空rowprogram） |
| GMpayload | input及输出各N(Q+2K)dx B，无GMnorm/rope中间 |
| workspace/UB | 无请求方workspace/显式物理分配；contiguous临时另计 |

##### 分层内存布局

`GMposition→int32clamp→GMpackedcache半cos/半sin→FP32freq共享；GMQ/K→FP32normaffine→RNEBF16→FP32rope→BF16wholehead→inputdtypeGM；V原值copy`。compiler物理UB/register/alias/spill未知。

##### 字节账与复用顺序

Kernel逻辑总 `2N(Q+2K)dx + N*nc*(dpos+R*dcache)+nr*nc*D*(dwq+dwk)+nr*nc*D*(dbq+dbk)` B；nc=K/D，元数据随col重复，Q/K在一个row循环内共用频率。非连续pos/cache各临时N*dpos、M*R*dcache B，若copy发生各额外读/写同大小。输入/临时与output异步存活归框架，无显式workspace交接或free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 覆盖 | row轮转×完整head列，无共享写/atomics/barrier |
| 索引 | int64position先toint32再clamp，非对原int64直接clamp；cache地址p*stride0仍需实际JIT可表示 |
| norms/bias | FP32norm/rsqrt/affine，实际weight已是乘数不加1 |
| 舍入 | RoPE前bitRNEBF16（epsNone亦生效）；最终所有Q/K含尾部BF16再转inputdtype |
| R尾 | al.insert前R，原base尾保持该路径BF16；无PASS_DIM0slice问题 |
| V | 原dtypecopy，不跟Q/KBF16舍入 |
| 工具链 | Dpow2已guard，但qb/kb、R/2arange准入与physical allocation外部 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| fp32_to_bf16_rne | [helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L19-L25) |
| Q/K/共享cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L67-L228) |
| grid/launch | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L337-L431) |


### Route R-009：wide norms=false bias=false preBF16=false

#### 适用条件

##### 选择证据

N>0、N≥threshold且Q≤8192，norms=false（epsNone）、bias=false（成对bias无）、cast_norm_to_bf16=false。R正偶≤D，可全/部分旋转，不另有partial分支。

#### Device 数据流

##### 函数级调用链

`Direct→validate_pos_cache树→helper/contiguous→split_qkv_rmsnorm_rope_half_pos_cache_kernel→al.slice/NeoX/BF16cast/store`。一个自有Kernel，helper源码完整，不用Torchreference补舍入。

##### 源码等价伪码

grid=(P,1)，qb=Q,kb=K。每col沿rowpid步长nr：读position转int32再clamp0..M-1，从cache同一行读cos/sin各R/2并共享Q/K；各Q/KloadFP32按head直接用x；保持y_baseFP32；前R转FP32切两半、NeoX旋转，结果toBF16；未旋转尾部先toBF16，insert回全head→转inputdtype/store。V原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/访问 |
|---|---|
| Q/Ktile | qb/kb FP32，4qb/4kb B逻辑；reshape[qb/D,D]/[kb/D,D] |
| RNE临时 | 不调用helper；不伪造物理多buffer |
| rope | 每head前R，o1/o2FP32后BF16ro1/ro2，wholeheadBF16y_out |
| position/cache | 每token/col读1*dpos+R*dcache B，共N*nc*(dpos+R*dcache) |
| affine | 0 B权重；0 B偏置（含空rowprogram） |
| GMpayload | input及输出各N(Q+2K)dx B，无GMnorm/rope中间 |
| workspace/UB | 无请求方workspace/显式物理分配；contiguous临时另计 |

##### 分层内存布局

`GMposition→int32clamp→GMpackedcache半cos/半sin→FP32freq共享；GMQ/K→FP32→FP32rope→BF16wholehead→inputdtypeGM；V原值copy`。compiler物理UB/register/alias/spill未知。

##### 字节账与复用顺序

Kernel逻辑总 `2N(Q+2K)dx + N*nc*(dpos+R*dcache)` B；nc1消除跨col重复position/cache读，Q/K在一个row循环内共用频率。非连续pos/cache各临时N*dpos、M*R*dcache B，若copy发生各额外读/写同大小。输入/临时与output异步存活归框架，无显式workspace交接或free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 覆盖 | row轮转×完整head列，无共享写/atomics/barrier |
| 索引 | int64position先toint32再clamp，非对原int64直接clamp；cache地址p*stride0仍需实际JIT可表示 |
| norms/bias | 跳norm，实际weight已是乘数不加1 |
| 舍入 | RoPE前不降精度；最终所有Q/K含尾部BF16再转inputdtype |
| R尾 | al.insert前R，原base尾保持该路径BF16；无PASS_DIM0slice问题 |
| V | 原dtypecopy，不跟Q/KBF16舍入 |
| 工具链 | Dpow2已guard，但qb/kb、R/2arange准入与physical allocation外部 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| fp32_to_bf16_rne | [helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L19-L25) |
| Q/K/共享cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L67-L228) |
| grid/launch | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L337-L431) |


### Route R-010：wide norms=false bias=false preBF16=true

#### 适用条件

##### 选择证据

N>0、N≥threshold且Q≤8192，norms=false（epsNone）、bias=false（成对bias无）、cast_norm_to_bf16=true。R正偶≤D，可全/部分旋转，不另有partial分支。

#### Device 数据流

##### 函数级调用链

`Direct→validate_pos_cache树→helper/contiguous→split_qkv_rmsnorm_rope_half_pos_cache_kernel→fp32_to_bf16_rne→al.slice/NeoX/BF16cast/store`。一个自有Kernel，helper源码完整，不用Torchreference补舍入。

##### 源码等价伪码

grid=(P,1)，qb=Q,kb=K。每col沿rowpid步长nr：读position转int32再clamp0..M-1，从cache同一行读cos/sin各R/2并共享Q/K；各Q/KloadFP32按head直接用x；调用bit-level RNE得BF16 y_base；前R转FP32切两半、NeoX旋转，结果toBF16；未旋转尾部保留y_baseBF16，insert回全head→转inputdtype/store。V原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/访问 |
|---|---|
| Q/Ktile | qb/kb FP32，4qb/4kb B逻辑；reshape[qb/D,D]/[kb/D,D] |
| RNE临时 | uint32位视图/lsb/u加法及BF16 y_base，均任务SSA；不伪造物理多buffer |
| rope | 每head前R，o1/o2FP32后BF16ro1/ro2，wholeheadBF16y_out |
| position/cache | 每token/col读1*dpos+R*dcache B，共N*nc*(dpos+R*dcache) |
| affine | 0 B权重；0 B偏置（含空rowprogram） |
| GMpayload | input及输出各N(Q+2K)dx B，无GMnorm/rope中间 |
| workspace/UB | 无请求方workspace/显式物理分配；contiguous临时另计 |

##### 分层内存布局

`GMposition→int32clamp→GMpackedcache半cos/半sin→FP32freq共享；GMQ/K→FP32→RNEBF16→FP32rope→BF16wholehead→inputdtypeGM；V原值copy`。compiler物理UB/register/alias/spill未知。

##### 字节账与复用顺序

Kernel逻辑总 `2N(Q+2K)dx + N*nc*(dpos+R*dcache)` B；nc1消除跨col重复position/cache读，Q/K在一个row循环内共用频率。非连续pos/cache各临时N*dpos、M*R*dcache B，若copy发生各额外读/写同大小。输入/临时与output异步存活归框架，无显式workspace交接或free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 覆盖 | row轮转×完整head列，无共享写/atomics/barrier |
| 索引 | int64position先toint32再clamp，非对原int64直接clamp；cache地址p*stride0仍需实际JIT可表示 |
| norms/bias | 跳norm，实际weight已是乘数不加1 |
| 舍入 | RoPE前bitRNEBF16（epsNone亦生效）；最终所有Q/K含尾部BF16再转inputdtype |
| R尾 | al.insert前R，原base尾保持该路径BF16；无PASS_DIM0slice问题 |
| V | 原dtypecopy，不跟Q/KBF16舍入 |
| 工具链 | Dpow2已guard，但qb/kb、R/2arange准入与physical allocation外部 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| fp32_to_bf16_rne | [helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L19-L25) |
| Q/K/共享cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L67-L228) |
| grid/launch | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L337-L431) |


### Route R-011：wide norms=false bias=true preBF16=false

#### 适用条件

##### 选择证据

N>0、N≥threshold且Q≤8192，norms=false（epsNone）、bias=true（成对bias存在）、cast_norm_to_bf16=false。R正偶≤D，可全/部分旋转，不另有partial分支。

#### Device 数据流

##### 函数级调用链

`Direct→validate_pos_cache树→helper/contiguous→split_qkv_rmsnorm_rope_half_pos_cache_kernel→al.slice/NeoX/BF16cast/store`。一个自有Kernel，helper源码完整，不用Torchreference补舍入。

##### 源码等价伪码

grid=(P,1)，qb=Q,kb=K。每col沿rowpid步长nr：读position转int32再clamp0..M-1，从cache同一行读cos/sin各R/2并共享Q/K；各Q/KloadFP32按head直接用x；保持y_baseFP32；前R转FP32切两半、NeoX旋转，结果toBF16；未旋转尾部先toBF16，insert回全head→转inputdtype/store。V原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/访问 |
|---|---|
| Q/Ktile | qb/kb FP32，4qb/4kb B逻辑；reshape[qb/D,D]/[kb/D,D] |
| RNE临时 | 不调用helper；不伪造物理多buffer |
| rope | 每head前R，o1/o2FP32后BF16ro1/ro2，wholeheadBF16y_out |
| position/cache | 每token/col读1*dpos+R*dcache B，共N*nc*(dpos+R*dcache) |
| affine | 0 B权重；nr*nc*D*(dbq+dbk) B偏置（含空rowprogram） |
| GMpayload | input及输出各N(Q+2K)dx B，无GMnorm/rope中间 |
| workspace/UB | 无请求方workspace/显式物理分配；contiguous临时另计 |

##### 分层内存布局

`GMposition→int32clamp→GMpackedcache半cos/半sin→FP32freq共享；GMQ/K→FP32→FP32rope→BF16wholehead→inputdtypeGM；V原值copy`。compiler物理UB/register/alias/spill未知。

##### 字节账与复用顺序

Kernel逻辑总 `2N(Q+2K)dx + N*nc*(dpos+R*dcache)+nr*nc*D*(dbq+dbk)` B；nc1消除跨col重复position/cache读，Q/K在一个row循环内共用频率。非连续pos/cache各临时N*dpos、M*R*dcache B，若copy发生各额外读/写同大小。输入/临时与output异步存活归框架，无显式workspace交接或free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 覆盖 | row轮转×完整head列，无共享写/atomics/barrier |
| 索引 | int64position先toint32再clamp，非对原int64直接clamp；cache地址p*stride0仍需实际JIT可表示 |
| norms/bias | bias虽load但不应用，实际weight已是乘数不加1 |
| 舍入 | RoPE前不降精度；最终所有Q/K含尾部BF16再转inputdtype |
| R尾 | al.insert前R，原base尾保持该路径BF16；无PASS_DIM0slice问题 |
| V | 原dtypecopy，不跟Q/KBF16舍入 |
| 工具链 | Dpow2已guard，但qb/kb、R/2arange准入与physical allocation外部 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| fp32_to_bf16_rne | [helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L19-L25) |
| Q/K/共享cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L67-L228) |
| grid/launch | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L337-L431) |


### Route R-012：wide norms=false bias=true preBF16=true

#### 适用条件

##### 选择证据

N>0、N≥threshold且Q≤8192，norms=false（epsNone）、bias=true（成对bias存在）、cast_norm_to_bf16=true。R正偶≤D，可全/部分旋转，不另有partial分支。

#### Device 数据流

##### 函数级调用链

`Direct→validate_pos_cache树→helper/contiguous→split_qkv_rmsnorm_rope_half_pos_cache_kernel→fp32_to_bf16_rne→al.slice/NeoX/BF16cast/store`。一个自有Kernel，helper源码完整，不用Torchreference补舍入。

##### 源码等价伪码

grid=(P,1)，qb=Q,kb=K。每col沿rowpid步长nr：读position转int32再clamp0..M-1，从cache同一行读cos/sin各R/2并共享Q/K；各Q/KloadFP32按head直接用x；调用bit-level RNE得BF16 y_base；前R转FP32切两半、NeoX旋转，结果toBF16；未旋转尾部保留y_baseBF16，insert回全head→转inputdtype/store。V原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/访问 |
|---|---|
| Q/Ktile | qb/kb FP32，4qb/4kb B逻辑；reshape[qb/D,D]/[kb/D,D] |
| RNE临时 | uint32位视图/lsb/u加法及BF16 y_base，均任务SSA；不伪造物理多buffer |
| rope | 每head前R，o1/o2FP32后BF16ro1/ro2，wholeheadBF16y_out |
| position/cache | 每token/col读1*dpos+R*dcache B，共N*nc*(dpos+R*dcache) |
| affine | 0 B权重；nr*nc*D*(dbq+dbk) B偏置（含空rowprogram） |
| GMpayload | input及输出各N(Q+2K)dx B，无GMnorm/rope中间 |
| workspace/UB | 无请求方workspace/显式物理分配；contiguous临时另计 |

##### 分层内存布局

`GMposition→int32clamp→GMpackedcache半cos/半sin→FP32freq共享；GMQ/K→FP32→RNEBF16→FP32rope→BF16wholehead→inputdtypeGM；V原值copy`。compiler物理UB/register/alias/spill未知。

##### 字节账与复用顺序

Kernel逻辑总 `2N(Q+2K)dx + N*nc*(dpos+R*dcache)+nr*nc*D*(dbq+dbk)` B；nc1消除跨col重复position/cache读，Q/K在一个row循环内共用频率。非连续pos/cache各临时N*dpos、M*R*dcache B，若copy发生各额外读/写同大小。输入/临时与output异步存活归框架，无显式workspace交接或free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 覆盖 | row轮转×完整head列，无共享写/atomics/barrier |
| 索引 | int64position先toint32再clamp，非对原int64直接clamp；cache地址p*stride0仍需实际JIT可表示 |
| norms/bias | bias虽load但不应用，实际weight已是乘数不加1 |
| 舍入 | RoPE前bitRNEBF16（epsNone亦生效）；最终所有Q/K含尾部BF16再转inputdtype |
| R尾 | al.insert前R，原base尾保持该路径BF16；无PASS_DIM0slice问题 |
| V | 原dtypecopy，不跟Q/KBF16舍入 |
| 工具链 | Dpow2已guard，但qb/kb、R/2arange准入与physical allocation外部 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| fp32_to_bf16_rne | [helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L19-L25) |
| Q/K/共享cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L67-L228) |
| grid/launch | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L337-L431) |


### Route R-013：wide norms=true bias=false preBF16=false

#### 适用条件

##### 选择证据

N>0、N≥threshold且Q≤8192，norms=true（eps非None）、bias=false（成对bias无）、cast_norm_to_bf16=false。R正偶≤D，可全/部分旋转，不另有partial分支。

#### Device 数据流

##### 函数级调用链

`Direct→validate_pos_cache树→helper/contiguous→split_qkv_rmsnorm_rope_half_pos_cache_kernel→al.slice/NeoX/BF16cast/store`。一个自有Kernel，helper源码完整，不用Torchreference补舍入。

##### 源码等价伪码

grid=(P,1)，qb=Q,kb=K。每col沿rowpid步长nr：读position转int32再clamp0..M-1，从cache同一行读cos/sin各R/2并共享Q/K；各Q/KloadFP32按headRMSnorm×w；保持y_baseFP32；前R转FP32切两半、NeoX旋转，结果toBF16；未旋转尾部先toBF16，insert回全head→转inputdtype/store。V原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/访问 |
|---|---|
| Q/Ktile | qb/kb FP32，4qb/4kb B逻辑；reshape[qb/D,D]/[kb/D,D] |
| RNE临时 | 不调用helper；不伪造物理多buffer |
| rope | 每head前R，o1/o2FP32后BF16ro1/ro2，wholeheadBF16y_out |
| position/cache | 每token/col读1*dpos+R*dcache B，共N*nc*(dpos+R*dcache) |
| affine | nr*nc*D*(dwq+dwk) B权重；0 B偏置（含空rowprogram） |
| GMpayload | input及输出各N(Q+2K)dx B，无GMnorm/rope中间 |
| workspace/UB | 无请求方workspace/显式物理分配；contiguous临时另计 |

##### 分层内存布局

`GMposition→int32clamp→GMpackedcache半cos/半sin→FP32freq共享；GMQ/K→FP32normaffine→FP32rope→BF16wholehead→inputdtypeGM；V原值copy`。compiler物理UB/register/alias/spill未知。

##### 字节账与复用顺序

Kernel逻辑总 `2N(Q+2K)dx + N*nc*(dpos+R*dcache)+nr*nc*D*(dwq+dwk)` B；nc1消除跨col重复position/cache读，Q/K在一个row循环内共用频率。非连续pos/cache各临时N*dpos、M*R*dcache B，若copy发生各额外读/写同大小。输入/临时与output异步存活归框架，无显式workspace交接或free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 覆盖 | row轮转×完整head列，无共享写/atomics/barrier |
| 索引 | int64position先toint32再clamp，非对原int64直接clamp；cache地址p*stride0仍需实际JIT可表示 |
| norms/bias | FP32norm/rsqrt/affine，实际weight已是乘数不加1 |
| 舍入 | RoPE前不降精度；最终所有Q/K含尾部BF16再转inputdtype |
| R尾 | al.insert前R，原base尾保持该路径BF16；无PASS_DIM0slice问题 |
| V | 原dtypecopy，不跟Q/KBF16舍入 |
| 工具链 | Dpow2已guard，但qb/kb、R/2arange准入与physical allocation外部 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| fp32_to_bf16_rne | [helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L19-L25) |
| Q/K/共享cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L67-L228) |
| grid/launch | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L337-L431) |


### Route R-014：wide norms=true bias=false preBF16=true

#### 适用条件

##### 选择证据

N>0、N≥threshold且Q≤8192，norms=true（eps非None）、bias=false（成对bias无）、cast_norm_to_bf16=true。R正偶≤D，可全/部分旋转，不另有partial分支。

#### Device 数据流

##### 函数级调用链

`Direct→validate_pos_cache树→helper/contiguous→split_qkv_rmsnorm_rope_half_pos_cache_kernel→fp32_to_bf16_rne→al.slice/NeoX/BF16cast/store`。一个自有Kernel，helper源码完整，不用Torchreference补舍入。

##### 源码等价伪码

grid=(P,1)，qb=Q,kb=K。每col沿rowpid步长nr：读position转int32再clamp0..M-1，从cache同一行读cos/sin各R/2并共享Q/K；各Q/KloadFP32按headRMSnorm×w；调用bit-level RNE得BF16 y_base；前R转FP32切两半、NeoX旋转，结果toBF16；未旋转尾部保留y_baseBF16，insert回全head→转inputdtype/store。V原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/访问 |
|---|---|
| Q/Ktile | qb/kb FP32，4qb/4kb B逻辑；reshape[qb/D,D]/[kb/D,D] |
| RNE临时 | uint32位视图/lsb/u加法及BF16 y_base，均任务SSA；不伪造物理多buffer |
| rope | 每head前R，o1/o2FP32后BF16ro1/ro2，wholeheadBF16y_out |
| position/cache | 每token/col读1*dpos+R*dcache B，共N*nc*(dpos+R*dcache) |
| affine | nr*nc*D*(dwq+dwk) B权重；0 B偏置（含空rowprogram） |
| GMpayload | input及输出各N(Q+2K)dx B，无GMnorm/rope中间 |
| workspace/UB | 无请求方workspace/显式物理分配；contiguous临时另计 |

##### 分层内存布局

`GMposition→int32clamp→GMpackedcache半cos/半sin→FP32freq共享；GMQ/K→FP32normaffine→RNEBF16→FP32rope→BF16wholehead→inputdtypeGM；V原值copy`。compiler物理UB/register/alias/spill未知。

##### 字节账与复用顺序

Kernel逻辑总 `2N(Q+2K)dx + N*nc*(dpos+R*dcache)+nr*nc*D*(dwq+dwk)` B；nc1消除跨col重复position/cache读，Q/K在一个row循环内共用频率。非连续pos/cache各临时N*dpos、M*R*dcache B，若copy发生各额外读/写同大小。输入/临时与output异步存活归框架，无显式workspace交接或free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 覆盖 | row轮转×完整head列，无共享写/atomics/barrier |
| 索引 | int64position先toint32再clamp，非对原int64直接clamp；cache地址p*stride0仍需实际JIT可表示 |
| norms/bias | FP32norm/rsqrt/affine，实际weight已是乘数不加1 |
| 舍入 | RoPE前bitRNEBF16（epsNone亦生效）；最终所有Q/K含尾部BF16再转inputdtype |
| R尾 | al.insert前R，原base尾保持该路径BF16；无PASS_DIM0slice问题 |
| V | 原dtypecopy，不跟Q/KBF16舍入 |
| 工具链 | Dpow2已guard，但qb/kb、R/2arange准入与physical allocation外部 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| fp32_to_bf16_rne | [helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L19-L25) |
| Q/K/共享cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L67-L228) |
| grid/launch | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L337-L431) |


### Route R-015：wide norms=true bias=true preBF16=false

#### 适用条件

##### 选择证据

N>0、N≥threshold且Q≤8192，norms=true（eps非None）、bias=true（成对bias存在）、cast_norm_to_bf16=false。R正偶≤D，可全/部分旋转，不另有partial分支。

#### Device 数据流

##### 函数级调用链

`Direct→validate_pos_cache树→helper/contiguous→split_qkv_rmsnorm_rope_half_pos_cache_kernel→al.slice/NeoX/BF16cast/store`。一个自有Kernel，helper源码完整，不用Torchreference补舍入。

##### 源码等价伪码

grid=(P,1)，qb=Q,kb=K。每col沿rowpid步长nr：读position转int32再clamp0..M-1，从cache同一行读cos/sin各R/2并共享Q/K；各Q/KloadFP32按headRMSnorm×w+b；保持y_baseFP32；前R转FP32切两半、NeoX旋转，结果toBF16；未旋转尾部先toBF16，insert回全head→转inputdtype/store。V原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/访问 |
|---|---|
| Q/Ktile | qb/kb FP32，4qb/4kb B逻辑；reshape[qb/D,D]/[kb/D,D] |
| RNE临时 | 不调用helper；不伪造物理多buffer |
| rope | 每head前R，o1/o2FP32后BF16ro1/ro2，wholeheadBF16y_out |
| position/cache | 每token/col读1*dpos+R*dcache B，共N*nc*(dpos+R*dcache) |
| affine | nr*nc*D*(dwq+dwk) B权重；nr*nc*D*(dbq+dbk) B偏置（含空rowprogram） |
| GMpayload | input及输出各N(Q+2K)dx B，无GMnorm/rope中间 |
| workspace/UB | 无请求方workspace/显式物理分配；contiguous临时另计 |

##### 分层内存布局

`GMposition→int32clamp→GMpackedcache半cos/半sin→FP32freq共享；GMQ/K→FP32normaffine→FP32rope→BF16wholehead→inputdtypeGM；V原值copy`。compiler物理UB/register/alias/spill未知。

##### 字节账与复用顺序

Kernel逻辑总 `2N(Q+2K)dx + N*nc*(dpos+R*dcache)+nr*nc*D*(dwq+dwk)+nr*nc*D*(dbq+dbk)` B；nc1消除跨col重复position/cache读，Q/K在一个row循环内共用频率。非连续pos/cache各临时N*dpos、M*R*dcache B，若copy发生各额外读/写同大小。输入/临时与output异步存活归框架，无显式workspace交接或free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 覆盖 | row轮转×完整head列，无共享写/atomics/barrier |
| 索引 | int64position先toint32再clamp，非对原int64直接clamp；cache地址p*stride0仍需实际JIT可表示 |
| norms/bias | FP32norm/rsqrt/affine，实际weight已是乘数不加1 |
| 舍入 | RoPE前不降精度；最终所有Q/K含尾部BF16再转inputdtype |
| R尾 | al.insert前R，原base尾保持该路径BF16；无PASS_DIM0slice问题 |
| V | 原dtypecopy，不跟Q/KBF16舍入 |
| 工具链 | Dpow2已guard，但qb/kb、R/2arange准入与physical allocation外部 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| fp32_to_bf16_rne | [helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L19-L25) |
| Q/K/共享cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L67-L228) |
| grid/launch | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L337-L431) |


### Route R-016：wide norms=true bias=true preBF16=true

#### 适用条件

##### 选择证据

N>0、N≥threshold且Q≤8192，norms=true（eps非None）、bias=true（成对bias存在）、cast_norm_to_bf16=true。R正偶≤D，可全/部分旋转，不另有partial分支。

#### Device 数据流

##### 函数级调用链

`Direct→validate_pos_cache树→helper/contiguous→split_qkv_rmsnorm_rope_half_pos_cache_kernel→fp32_to_bf16_rne→al.slice/NeoX/BF16cast/store`。一个自有Kernel，helper源码完整，不用Torchreference补舍入。

##### 源码等价伪码

grid=(P,1)，qb=Q,kb=K。每col沿rowpid步长nr：读position转int32再clamp0..M-1，从cache同一行读cos/sin各R/2并共享Q/K；各Q/KloadFP32按headRMSnorm×w+b；调用bit-level RNE得BF16 y_base；前R转FP32切两半、NeoX旋转，结果toBF16；未旋转尾部保留y_baseBF16，insert回全head→转inputdtype/store。V原dtypecopy。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/访问 |
|---|---|
| Q/Ktile | qb/kb FP32，4qb/4kb B逻辑；reshape[qb/D,D]/[kb/D,D] |
| RNE临时 | uint32位视图/lsb/u加法及BF16 y_base，均任务SSA；不伪造物理多buffer |
| rope | 每head前R，o1/o2FP32后BF16ro1/ro2，wholeheadBF16y_out |
| position/cache | 每token/col读1*dpos+R*dcache B，共N*nc*(dpos+R*dcache) |
| affine | nr*nc*D*(dwq+dwk) B权重；nr*nc*D*(dbq+dbk) B偏置（含空rowprogram） |
| GMpayload | input及输出各N(Q+2K)dx B，无GMnorm/rope中间 |
| workspace/UB | 无请求方workspace/显式物理分配；contiguous临时另计 |

##### 分层内存布局

`GMposition→int32clamp→GMpackedcache半cos/半sin→FP32freq共享；GMQ/K→FP32normaffine→RNEBF16→FP32rope→BF16wholehead→inputdtypeGM；V原值copy`。compiler物理UB/register/alias/spill未知。

##### 字节账与复用顺序

Kernel逻辑总 `2N(Q+2K)dx + N*nc*(dpos+R*dcache)+nr*nc*D*(dwq+dwk)+nr*nc*D*(dbq+dbk)` B；nc1消除跨col重复position/cache读，Q/K在一个row循环内共用频率。非连续pos/cache各临时N*dpos、M*R*dcache B，若copy发生各额外读/写同大小。输入/临时与output异步存活归框架，无显式workspace交接或free。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 覆盖 | row轮转×完整head列，无共享写/atomics/barrier |
| 索引 | int64position先toint32再clamp，非对原int64直接clamp；cache地址p*stride0仍需实际JIT可表示 |
| norms/bias | FP32norm/rsqrt/affine，实际weight已是乘数不加1 |
| 舍入 | RoPE前bitRNEBF16（epsNone亦生效）；最终所有Q/K含尾部BF16再转inputdtype |
| R尾 | al.insert前R，原base尾保持该路径BF16；无PASS_DIM0slice问题 |
| V | 原dtypecopy，不跟Q/KBF16舍入 |
| 工具链 | Dpow2已guard，但qb/kb、R/2arange准入与physical allocation外部 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| fp32_to_bf16_rne | [helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L19-L25) |
| Q/K/共享cache | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L67-L228) |
| grid/launch | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L337-L431) |

## 算子特定优化

### Trick T-001：共享position频率且在设备端clamp

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L74-L92)：

```python
    # Single loop over batch: for each row process Q, K, V (avoids duplication, same cos/sin per row)
    for row_idx in tl.range(row_pid, batch_size, row_step):
        # ---- load cos/sin once per row (shared by Q and K RoPE) ----
        p = tl.load(pos_ptr + row_idx).to(tl.int32)
        # Clamp on-device: avoids OOB cos/sin loads without Python .any()/.item() sync (breaks NPU graph capture).
        p = tl.maximum(p, 0)
        p = tl.minimum(p, max_seq - 1)
        base = p * cos_sin_stride0
        offs = tl.arange(0, half_rope_dim)
        cos_f = (
            tl.load(cos_sin_cache_ptr + base + offs)
            .to(tl.float32)
            .reshape(1, half_rope_dim)
        )
        sin_f = (
            tl.load(cos_sin_cache_ptr + base + half_rope_dim + offs)
            .to(tl.float32)
            .reshape(1, half_rope_dim)
        )
```

#### 机制与设计原因

Q/K同row循环只读一次position及cos/sin半表，按col复用；先int32再max/min，无Host读值同步。wide nc1进一步减少跨col重复metadata读取，不等于已测性能结论。

#### 迁移边界

cache连续packed、M>0、base整数可表示；int64转换发生在clamp前，超int32位置语义不能解释成原值clamp。

#### 错误做法

先在Host .any/.item校验改变图捕获/同步性质，或按完整重复半表布局读packedcache。

### Trick T-002：仅RoPE前用自有bitRNE，最终BF16另有路径

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py#L19-L25)：

```python
@triton.jit
def fp32_to_bf16_rne(x):
    """Deterministic FP32 -> BF16 (round-to-nearest-even). Keep ONLY for RMSNorm cast."""
    u = tl.cast(x, tl.uint32, bitcast=True)
    lsb = (u >> 16) & 1
    u = (u + (0x7FFF + lsb)) & 0xFFFF0000
    return tl.cast(u, tl.float32, bitcast=True).to(tl.bfloat16)
```

#### 机制与设计原因

FP32bits取高16位最低bit，增加0x7fff+lsb再截低16位，实现有限可表示域的nearest-even BF16舍入。helper只用于precast，最终rope用普通toBF16；不得把两个转换点合并或宣称最终舍入helper也被调用。

#### 迁移边界

按实际uint32bitcast/加法语义；特殊NaN/Inf/溢出不额外处理，不以函数名代替这些数值边界。epsNone时precast仍生效。

#### 错误做法

关闭precast便取消最终Q/KBF16，或将未旋转尾部保FP32写出，均改变合同。

## 模板与实现对比

16特化区分网格/norm/bias/precast，R全/部分不新增不同Kernel分支。两次BF16与普通QKV/Gemma不同，不借它们的FP32精度结论替代。V维持inputdtype原值；位置/缓存连续化临时GM成本已计。

## 平台差异

本卡A2/A3归属arch22；公开arch22/35支持但硬件执行仍待验证，README/architectures映射A2/A3、950。wideguard依据注释910B3，不推广成950验证；CANN9.1.0 CI配置非本次运行或binary等同。

## 限制与失败边界

assert可关闭，非二次幂tile与物理资源/地址域未完全guard；输入有限仍可能norm或rope产生超范围值，自有RNE不处理所有特殊值。index窄化改变超int32位置解释。无编译、上游运行、测试或校验/性能结论，draft不宣称安全部署。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开合同](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.md) | `split_qkv_rmsnorm_rope_pos_cache_half_npu` | 位置int32clamp/两次BF16/网格/平台 |
| [Direct/Device/helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py) | `split_qkv_rmsnorm_rope_pos_cache_half_npu/split_qkv_rmsnorm_rope_half_pos_cache_kernel/fp32_to_bf16_rne` | 完整433行 |
| [校验树](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/norm_utils.py) | `validate_pos_cache/qkv_shape/affine` | Dpow2、位置/cache、完整元信息 |
| [公开转发](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/norm/split_qkv_rmsnorm_rope_pos_cache_half_npu.py) | `_triton_impl` | 独立poscache入口 |
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

冻结117/legacy唯一poscacheAPI已全文读并链接，普通QKV/Gemma相关卡只用于区分语义；只新增本Direct两平台Operator。全部固定同repo唯一primary，无verified。
