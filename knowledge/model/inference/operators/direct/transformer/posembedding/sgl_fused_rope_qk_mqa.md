---
type: Operator
title: "FusedRopeQkMqa A2/A3 Direct Invoke 算子知识"
description: "闭合MQA纯Q/K RoPE的四配对尾部特化、14stride字段和预选cache共享，保留原值尾复制、类型提升及physical资源边界。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/rope/fused_rope_qk_mqa.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/fused_rope_qk_mqa.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/rope_utils.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/rope/fused_rope_qk_mqa.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/__init__.py
    role: supporting
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
created_at: "2026-11-09T09:46:50Z"
updated_at: "2026-11-09T09:46:50Z"
platforms: [a2, a3]
cann_versions: ["9.1.0"]
---

# FusedRopeQkMqa A2/A3 Direct Invoke 算子知识

## 算子速览

精确Direct `sgl_kernel_npu.implementation.triton.rope.fused_rope_qk_mqa.fused_rope_qk_mqa(query,key,cos_sin,rotary_dim,is_neox_style)`，各token在独立Hq/Hk heads上做NeoX或GPT-J RoPE，cache已预先按token选行；不norm、不gather、不展开K。完整validator、四pair/tail特化与真实stride寻址闭合。

draft说明无本次运行/编译/物理资源证据；公开支持不作实测结论。已完整读并复用[MQA API](../../../../apis/sgl_kernel_npu/sgl_rope_qk_mqa.md)，不混入带RMS/位置int32clamp的其它算子。

## 接口与语义

### 计算语义

R=rotary_dim，m=R2；pair(a,b)=(j,j+m)若NeoX，否则(2j,2j+1)。`ya=xa*cos[t,j]-xb*sin[t,j]`、`yb=xa*sin[t,j]+xb*cos[t,j]`；尾[R,D)原值。Q/K头数独立、无整除关系，频率跨两者所有head共享；没有显式FP32cast或BF16中间舍入。按公开Triton提升合同：有FP32用FP32，FP16/BF16混合按FP16，最终store回Q/Kdtype；具体compiler融合/近似不作逐位承诺。

### 输入、输出与属性

| 项 | Host合同 |
|---|---|
| query/key | strided浮点[T,Hq,D]/[T,Hk,D]，维均正，同device/dtype，三浮点dtype |
| cos_sin | strided同device三浮点，可异dtype，[Ncache,R]、Ncache≥T；每行先cos半后sin半 |
| strides | 输入可非连续或零stride只读视图，各Tensor真实元素stride传Kernel |
| R/style | 正偶Pythonint排bool、R≤D；style bool |
| Triton附加 | NPU；Hq/Hk/R2二次幂，D-R为0或二次幂 |
| 输出 | empty_like(query/key)，新存储同shape/device/dtype，真实outputstrides传入，输入不写 |

### 入口与版本

冻结短路径加包名前缀精确，auto/triton延迟转发，torch_native外部reference可有更宽尺寸域，不反向放宽本入口guard。固定SGLcommit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`，CANN9.1.0为README/CI固定配置非本次运行；Triton编译器二进制未完整固定。

## Host/Launcher 执行流程

### 参数校验与前处理

validate_rope_inputs完整检查Tensor/layout/ndim/dtype、正维、共享T/D和Q/Kdtype、同device、R类型范围偶数、stylebool、cache尺寸；再NPUassert与Hq/Hk/R2/tail二次幂assert。无设备值回读、无contiguouscopy，T0不属合同，不应虚构空输入捷径。assert可被Python-O关闭。

### 参数、Workspace 与生命周期

empty_like创建两输出，grid(T,)launch。无helper核数查询/cache、workspace/POD/ACLNN/explicitstream/wait/warp/stage；异步Tensor存活/流交接和物理buffer归框架。没有Host位置选择，调用方必须传已对齐cache行。

### 启动图与失败传播

import→validator→NPU与pow2assert→两输出分配→单JITKernel→return。无fallback或额外copy/normKernel；异常直接传播。包原生库导入依赖不是数学图调用native算子。

## Route 与参数设计

### 分核与资源计算

每program=token，grid=T；Hq与Hk全heads并行逻辑tile，各pair宽m。所有arange终点由Host明确pow2guard；tail0通过constexprif剪去不构建0长度arange。无需T二次幂。大head数/m逻辑tile增长，源码无UB容量guard，尺寸/stride地址还须JIT可表示。

### Route 选择

两个style×tail0/正两轴共四特化。无autotune、硬件宏或核数固定grid；下表既是完整可达Device矩阵，也不包含torch_native的通用size实现。

### 模板/实现执行矩阵

| Route | style | tail |
|---|---|---|
| R-001 | NeoX | 0 |
| R-002 | NeoX | D-R>0/pow2 |
| R-003 | GPT-J | 0 |
| R-004 | GPT-J | D-R>0/pow2 |

query/key同三dtype×cache三dtype共九实例，隐式promotion分界在math，store同Q/Kdtype。无tl.dot/Cube/AIC/MIX节点；physicalallocation与typepromotionprimitive边界明确。

### 隐藏性能 Guard

全Hq/Hk一次处理、没有head分块/容量阈值，pow2合法不等于任意大shape资源可编译。输入零stride合法只读，但输出依empty_like分配/真实stride，不能用输入stride替代输出stride。pid*stride未显式int64转换，超大地址乘积需另核对实际JIT位宽。

### POD/ABI

| 字段 | 分类/消费 |
|---|---|
| query_ptr/key_ptr/cos_sin_ptr/out_q_ptr/out_k_ptr | runtimeTensor指针，前三读/后两写 |
| stride_qt/stride_qh/stride_qd | runtimeQ三元素stride |
| stride_kt/stride_kh/stride_kd | runtimeK三元素stride |
| stride_ct/stride_cd | runtimecache两元素stride |
| stride_oqt/stride_oqh/stride_oqd | runtimeoutQ三元素stride |
| stride_okt/stride_okh/stride_okd | runtimeoutK三元素stride |
| Hq/Hk/D_HEAD/D_ROPE | constexprheads/D/R→arange/tail |
| IS_NEOX_STYLE | constexpr→pairing |
| grid | (T,) |

全部14stride字段列明，无自定义序列化POD/字段offset；JIT标量/指针ABI不猜位宽。

### Route 源码闭包

完整172行Direct/Device及53行rope_utils、public转发已读；rope/backend包无Device。根setup→stage_runtime完整Python包→build_wheel/setup_refactor打包。每条数学路径自有body明确，load/mul/add/sub/store及physicalallocation归Tritonprimitive边界，不把其它norm入口补作此实现。

## Kernel 实现

### 公共执行流程

按style产生pair索引，读一次cos/sin，Q所有heads旋转输出，K独立heads旋转输出，若tail>0各自原值copy。两组输出互相独立，无shared scratch。

### Route R-001：NeoX两半 / 全维旋转

#### 适用条件

##### 选择证据

is_neox_style=true、R=D；Hq/Hk/R2均正二次幂，T正不要求二次幂。constexprif选择配对和是否编译tail，不存在T0路线。

#### Device 数据流

##### 函数级调用链

`fused_rope_qk_mqa→validate_rope_inputs→dimensionpow2assert→fused_rope_qk_mqa_kernel_opt→load/mul/add/sub/store`；无自有helper或其它Kernel，不展开Khead。

##### 源码等价伪码

token t=programid，d=arange(R2)；pair a=d,b=d+R2；cache[t,d]cos、cache[t,d+R2]sin一次读取。按真实stride读所有Hq的q1/q2，算q1*cos-q2*sin、q1*sin+q2*cos，写对应a/b；Hk独立同式。D==R，compile-time剪去tail arange与访问。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/流量 |
|---|---|
| cos/sin | 各R2元素，字节宽dc；每token共R*dc B |
| q1/q2/qout1/qout2 | 各Hq×R2逻辑lane，实际算术dtype按隐式promotion |
| k1/k2/kout1/kout2 | 各Hk×R2逻辑lane，不展开Hq |
| tail | 无 |
| payloadGM | 每token读/写各(Hq+Hk)*D*dx B，所有inputstrides真实传入 |
| 物理UB/workspace | 无显式分配/请求，compiler物理布局/复用外部 |

##### 分层内存布局

`GM预选cache行→cos/sin SSA[R2]广播head；GMQ/K真实stride→两配对SSA[heads,R2]→算术→真实outputstrideGM`。outputempty_like可能保留合法layout，不能把整个输出一概描述为packed。

##### 字节账与复用顺序

完整调用逻辑GM `2T*(Hq+Hk)*D*dx + T*R*dc` B，不含因stride导致的真实事务放大。缓存额外行不读。无中间GM/统计/请求方workspace；所有SSA规模不相加作UB峰值，Q/K阶段不保证物理buffer别名。input/out异步存活/跨流消费由框架管理，无显式free/wait。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 映射 | 一program一token，Hq/Hk一次全读，每列pair互不交叠，无atomic/barrier |
| 尾mask | 无mask，全部arange范围由Hostguard保证，Tgrid与Tensor数匹配 |
| 类型 | 没有显式FP32转换；三dtype的提升按Tritonprimitive/公开合同，最终store转换Q/Kdtype |
| cache | 第t行已由调用方按实际位置选好，不含positions/gather/clamp |
| 尾部 | constexpr完全不构建tail |
| 精度 | 低精度乘加及fusion/舍入外部，不承诺Torch逐位；finite域内也需防算术overflow |
| 同步 | SSA依赖交compiler，无核间通信/用户workspace生命周期 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| pairing/cache/Q | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/fused_rope_qk_mqa.py#L37-L72) |
| K/tail | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/fused_rope_qk_mqa.py#L74-L114) |
| sizeassert/launch | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/fused_rope_qk_mqa.py#L117-L172) |


### Route R-002：NeoX两半 / 尾部copy

#### 适用条件

##### 选择证据

is_neox_style=true、0<R<D且D-R二次幂；Hq/Hk/R2均正二次幂，T正不要求二次幂。constexprif选择配对和是否编译tail，不存在T0路线。

#### Device 数据流

##### 函数级调用链

`fused_rope_qk_mqa→validate_rope_inputs→dimensionpow2assert→fused_rope_qk_mqa_kernel_opt→load/mul/add/sub/store`；无自有helper或其它Kernel，不展开Khead。

##### 源码等价伪码

token t=programid，d=arange(R2)；pair a=d,b=d+R2；cache[t,d]cos、cache[t,d+R2]sin一次读取。按真实stride读所有Hq的q1/q2，算q1*cos-q2*sin、q1*sin+q2*cos，写对应a/b；Hk独立同式。再dp=arange(D-R)，按每Tensor真实stride原值copyQ/K尾部。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/流量 |
|---|---|
| cos/sin | 各R2元素，字节宽dc；每token共R*dc B |
| q1/q2/qout1/qout2 | 各Hq×R2逻辑lane，实际算术dtype按隐式promotion |
| k1/k2/kout1/kout2 | 各Hk×R2逻辑lane，不展开Hq |
| tail | Q Hq*(D-R)、K Hk*(D-R)原dtype逻辑值 |
| payloadGM | 每token读/写各(Hq+Hk)*D*dx B，所有inputstrides真实传入 |
| 物理UB/workspace | 无显式分配/请求，compiler物理布局/复用外部 |

##### 分层内存布局

`GM预选cache行→cos/sin SSA[R2]广播head；GMQ/K真实stride→两配对SSA[heads,R2]→算术→真实outputstrideGM；tail原值load/store`。outputempty_like可能保留合法layout，不能把整个输出一概描述为packed。

##### 字节账与复用顺序

完整调用逻辑GM `2T*(Hq+Hk)*D*dx + T*R*dc` B，不含因stride导致的真实事务放大。缓存额外行不读。无中间GM/统计/请求方workspace；所有SSA规模不相加作UB峰值，Q/K阶段不保证物理buffer别名。input/out异步存活/跨流消费由框架管理，无显式free/wait。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 映射 | 一program一token，Hq/Hk一次全读，每列pair互不交叠，无atomic/barrier |
| 尾mask | 无mask，全部arange范围由Hostguard保证，Tgrid与Tensor数匹配 |
| 类型 | 没有显式FP32转换；三dtype的提升按Tritonprimitive/公开合同，最终store转换Q/Kdtype |
| cache | 第t行已由调用方按实际位置选好，不含positions/gather/clamp |
| 尾部 | 无浮点算术，原dtypecopy；输入可零stride只读 |
| 精度 | 低精度乘加及fusion/舍入外部，不承诺Torch逐位；finite域内也需防算术overflow |
| 同步 | SSA依赖交compiler，无核间通信/用户workspace生命周期 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| pairing/cache/Q | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/fused_rope_qk_mqa.py#L37-L72) |
| K/tail | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/fused_rope_qk_mqa.py#L74-L114) |
| sizeassert/launch | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/fused_rope_qk_mqa.py#L117-L172) |


### Route R-003：GPT-J相邻 / 全维旋转

#### 适用条件

##### 选择证据

is_neox_style=false、R=D；Hq/Hk/R2均正二次幂，T正不要求二次幂。constexprif选择配对和是否编译tail，不存在T0路线。

#### Device 数据流

##### 函数级调用链

`fused_rope_qk_mqa→validate_rope_inputs→dimensionpow2assert→fused_rope_qk_mqa_kernel_opt→load/mul/add/sub/store`；无自有helper或其它Kernel，不展开Khead。

##### 源码等价伪码

token t=programid，d=arange(R2)；pair a=2d,b=2d+1；cache[t,d]cos、cache[t,d+R2]sin一次读取。按真实stride读所有Hq的q1/q2，算q1*cos-q2*sin、q1*sin+q2*cos，写对应a/b；Hk独立同式。D==R，compile-time剪去tail arange与访问。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/流量 |
|---|---|
| cos/sin | 各R2元素，字节宽dc；每token共R*dc B |
| q1/q2/qout1/qout2 | 各Hq×R2逻辑lane，实际算术dtype按隐式promotion |
| k1/k2/kout1/kout2 | 各Hk×R2逻辑lane，不展开Hq |
| tail | 无 |
| payloadGM | 每token读/写各(Hq+Hk)*D*dx B，所有inputstrides真实传入 |
| 物理UB/workspace | 无显式分配/请求，compiler物理布局/复用外部 |

##### 分层内存布局

`GM预选cache行→cos/sin SSA[R2]广播head；GMQ/K真实stride→两配对SSA[heads,R2]→算术→真实outputstrideGM`。outputempty_like可能保留合法layout，不能把整个输出一概描述为packed。

##### 字节账与复用顺序

完整调用逻辑GM `2T*(Hq+Hk)*D*dx + T*R*dc` B，不含因stride导致的真实事务放大。缓存额外行不读。无中间GM/统计/请求方workspace；所有SSA规模不相加作UB峰值，Q/K阶段不保证物理buffer别名。input/out异步存活/跨流消费由框架管理，无显式free/wait。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 映射 | 一program一token，Hq/Hk一次全读，每列pair互不交叠，无atomic/barrier |
| 尾mask | 无mask，全部arange范围由Hostguard保证，Tgrid与Tensor数匹配 |
| 类型 | 没有显式FP32转换；三dtype的提升按Tritonprimitive/公开合同，最终store转换Q/Kdtype |
| cache | 第t行已由调用方按实际位置选好，不含positions/gather/clamp |
| 尾部 | constexpr完全不构建tail |
| 精度 | 低精度乘加及fusion/舍入外部，不承诺Torch逐位；finite域内也需防算术overflow |
| 同步 | SSA依赖交compiler，无核间通信/用户workspace生命周期 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| pairing/cache/Q | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/fused_rope_qk_mqa.py#L37-L72) |
| K/tail | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/fused_rope_qk_mqa.py#L74-L114) |
| sizeassert/launch | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/fused_rope_qk_mqa.py#L117-L172) |


### Route R-004：GPT-J相邻 / 尾部copy

#### 适用条件

##### 选择证据

is_neox_style=false、0<R<D且D-R二次幂；Hq/Hk/R2均正二次幂，T正不要求二次幂。constexprif选择配对和是否编译tail，不存在T0路线。

#### Device 数据流

##### 函数级调用链

`fused_rope_qk_mqa→validate_rope_inputs→dimensionpow2assert→fused_rope_qk_mqa_kernel_opt→load/mul/add/sub/store`；无自有helper或其它Kernel，不展开Khead。

##### 源码等价伪码

token t=programid，d=arange(R2)；pair a=2d,b=2d+1；cache[t,d]cos、cache[t,d+R2]sin一次读取。按真实stride读所有Hq的q1/q2，算q1*cos-q2*sin、q1*sin+q2*cos，写对应a/b；Hk独立同式。再dp=arange(D-R)，按每Tensor真实stride原值copyQ/K尾部。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/流量 |
|---|---|
| cos/sin | 各R2元素，字节宽dc；每token共R*dc B |
| q1/q2/qout1/qout2 | 各Hq×R2逻辑lane，实际算术dtype按隐式promotion |
| k1/k2/kout1/kout2 | 各Hk×R2逻辑lane，不展开Hq |
| tail | Q Hq*(D-R)、K Hk*(D-R)原dtype逻辑值 |
| payloadGM | 每token读/写各(Hq+Hk)*D*dx B，所有inputstrides真实传入 |
| 物理UB/workspace | 无显式分配/请求，compiler物理布局/复用外部 |

##### 分层内存布局

`GM预选cache行→cos/sin SSA[R2]广播head；GMQ/K真实stride→两配对SSA[heads,R2]→算术→真实outputstrideGM；tail原值load/store`。outputempty_like可能保留合法layout，不能把整个输出一概描述为packed。

##### 字节账与复用顺序

完整调用逻辑GM `2T*(Hq+Hk)*D*dx + T*R*dc` B，不含因stride导致的真实事务放大。缓存额外行不读。无中间GM/统计/请求方workspace；所有SSA规模不相加作UB峰值，Q/K阶段不保证物理buffer别名。input/out异步存活/跨流消费由框架管理，无显式free/wait。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 映射 | 一program一token，Hq/Hk一次全读，每列pair互不交叠，无atomic/barrier |
| 尾mask | 无mask，全部arange范围由Hostguard保证，Tgrid与Tensor数匹配 |
| 类型 | 没有显式FP32转换；三dtype的提升按Tritonprimitive/公开合同，最终store转换Q/Kdtype |
| cache | 第t行已由调用方按实际位置选好，不含positions/gather/clamp |
| 尾部 | 无浮点算术，原dtypecopy；输入可零stride只读 |
| 精度 | 低精度乘加及fusion/舍入外部，不承诺Torch逐位；finite域内也需防算术overflow |
| 同步 | SSA依赖交compiler，无核间通信/用户workspace生命周期 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| pairing/cache/Q | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/fused_rope_qk_mqa.py#L37-L72) |
| K/tail | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/fused_rope_qk_mqa.py#L74-L114) |
| sizeassert/launch | [Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/fused_rope_qk_mqa.py#L117-L172) |

## 算子特定优化

### Trick T-001：频率跨Q/K头共享但不展开K

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/fused_rope_qk_mqa.py#L48-L59)：

```python
    # cos / sin (shared across all heads for this position)
    cos = tl.load(cos_sin_ptr + pid_t * stride_ct + d * stride_cd)
    sin = tl.load(cos_sin_ptr + pid_t * stride_ct + (d + D_ROPE // 2) * stride_cd)

    # ================= Q (all Hq heads at once) =================
    head_offs = tl.arange(0, Hq)
    q_base = query_ptr + pid_t * stride_qt

    q1 = tl.load(
        q_base + head_offs[:, None] * stride_qh + idx_even[None, :] * stride_qd
    )
    q2 = tl.load(q_base + head_offs[:, None] * stride_qh + idx_odd[None, :] * stride_qd)
```

#### 机制与设计原因

cache每token只读R项，广播到Hq并继续被Hk使用，K只处理自身head数；没有先expandK或物化扩展GM。逻辑流量公式可复验，未测性能。

#### 迁移边界

预选cache行与token已对齐，head数可不整除但各需满足当前Tritonpow2guard；不同输入输出stride必须分别传入。

#### 错误做法

把cache当全位置表直接传而期待gather，或复制K到Hq改变内存/结果shape。

### Trick T-002：编译期剪掉零尾部路径

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/fused_rope_qk_mqa.py#L92-L104)：

```python
    # ================= pass-through (compile-time pruning) =================
    if D_HEAD > D_ROPE:
        dp = tl.arange(0, D_HEAD - D_ROPE)
        # Q pass-through
        q_pass = tl.load(
            q_base + head_offs[:, None] * stride_qh + (dp + D_ROPE)[None, :] * stride_qd
        )
        tl.store(
            oq_base
            + head_offs[:, None] * stride_oqh
            + (dp + D_ROPE)[None, :] * stride_oqd,
            q_pass,
        )
```

#### 机制与设计原因

D_HEAD/D_ROPE constexpr决定是否构建tailarange，R=D时不创建0长度tensor；部分旋转时按真实stridecopy，不做浮点算术。

#### 迁移边界

正tail必须当前pow2guard通过，不能以torch_native的任意tail成功放宽此Direct域。

#### 错误做法

将未旋转尾部清0/再norm，或无条件构建arange(0,0)。

## 模板与实现对比

四特化共享纯RoPE语义，pow2guard覆盖所有无maskarange端点；与QKV拆分RMS/位置cache不同，无中间降精度或索引clamp。低精度提升按当前primitive，不能宣称所有中间FP32。

## 平台差异

本卡A2/A3归属arch22；公开arch22/35支持，README/architectures映射A2/A3、950，无硬件分支。CANN9.1.0 CI配置非本次执行、实际binarycompiler一致性或A2实测；资源lowering须实际工具链确认。

## 限制与失败边界

assert可关闭，pow2guard不覆盖所有整数/物理资源容量；大head/tile/stride可超编译或地址域。finite输入仍可低精度算术overflow，尾原值copy不代表所有NaNpayload必须位同。无编译、真机、上游测试/校验或性能证据；draft保留明确平台支持与未验证的区别。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开合同](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/rope/fused_rope_qk_mqa.md) | `fused_rope_qk_mqa` | MQA/head独立/预选cache/类型提升 |
| [Direct/Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/fused_rope_qk_mqa.py) | `fused_rope_qk_mqa/fused_rope_qk_mqa_kernel_opt` | 完整172行/真实stride/四特化 |
| [元信息检查](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/rope_utils.py) | `validate_rope_inputs` | 完整53行无设备值同步 |
| [公开转发](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/rope/fused_rope_qk_mqa.py) | `_triton_impl` | auto/triton直达 |
| [rope包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/rope/__init__.py) | `module init` | 无附加Device |
| [import边界](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py) | `_load_sgl_kernel_npu` | torch_npu/原生库与vendor初始化 |
| [backend包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py) | `module init` | 懒加载包，无另一Device节点 |
| [构建入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/setup.py) | `main` | 完整Python wheel路径；本次未构建 |
| [源码打包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/torch_wheel.py) | `stage_runtime/build_torch/build_wheel/setup_refactor` | 复制完整Python包、原生运行库与wheel |
| [平台/包说明](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md) | `REFACTOR/arch22/35 mapping` | 全部Python实现包含、产品映射、CANN9.1.0构建例 |
| [产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json) | `2201/3510` | a2/a3/950对应构建族 |
| [版本配置](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml) | `test-norm-ops` | CANN9.1.0/a3/950配置，非本次运行 |
| [CI消费](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernel-group.yml) | `run-kernel-group` | 对应版本容器/测试组参数 |

### 实现复用检查

冻结117/legacy唯一MQA API已全文读并链接，只新增本唯一Direct两平台Operator；不重复API或借torch_native扩大支持。全部固定同repo唯一primary、无verified。
