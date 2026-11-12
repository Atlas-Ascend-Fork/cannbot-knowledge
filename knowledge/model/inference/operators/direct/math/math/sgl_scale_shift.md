---
type: Operator
title: "FusedScaleShift A2/A3 Direct Invoke 算子知识"
description: "闭合scale/shift两Kernel五候选与11条广播路线，区分full优先、scale_constant与显式dtype转换，记录非二次幂行块和编译器分配边界。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/elementwise/fused_scale_shift.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/elementwise/scale_shift.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/__init__.py
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
created_at: "2026-11-09T09:24:06Z"
updated_at: "2026-11-09T09:28:21Z"
platforms: [a2, a3]
cann_versions: ["9.1.0"]
---

# FusedScaleShift A2/A3 Direct Invoke 算子知识

## 算子速览

精确入口 `sgl_kernel_npu.implementation.triton.elementwise.scale_shift.fused_scale_shift(x,scale,shift,scale_constant=1.0)`；按元素数选择同一scale/shift算子的广播模式。先匹配逐元素shift：`x*(scale_constant+scale)+shift`；否则广播shift：`x*(1+scale)+shift`，忽略scale_constant。完整Host、两Device、五配置及广播constexpr组合共11条实际路线闭合。

draft保留非二次幂行块112/96/80的arange扩展准入、device属性缓存及物理compiler边界，不宣称实际编译失败或运行成功。已有[公开合同](../../../../apis/sgl_kernel_npu/sgl_fused_scale_shift.md)全文读并复用。

## 接口与语义

### 计算语义

N=B*L,H通道。scale按numel1或H；shift按numelNH、1、H解释，NH优先。若Nt=NH，则c=scale_constant，否则c=1；`y[t,h]=x[t,h]*(c+s[h or 0])+shift[t,h or h or 0]`。N=1时channel shift也匹配full；H=1时“channel”与scalar的相等元素数实际走scalar constexpr（full分支除外）。这是一入口明确模式，不把常数语义抹平。

### 输入、输出与属性

| 项 | 真实Host检查 |
|---|---|
| x | Tensor/strided、连续NPU、三维且维正；FP32/FP16/BF16 |
| scale/shift | 同device、连续、相同三浮点dtype集合但可彼此不同；展平后只看元素数 |
| scale大小 | 1或H；full shift时必须H，H1时单元素也满足 |
| shift大小 | 1/H/NH |
| scale_constant | Python int/float、排除bool、有限；即便广播模式也校验，但不传其Kernel |
| output | empty_like(x)，新存储同shape/device/dtype；三输入不修改 |

### 入口与版本

冻结短路径加包名前缀为精确函数。auto/triton只转发；torch_native独立参考不合并其计算/资源。固定SGL commit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`；CANN9.1.0为README/CI固定参数，非本次环境核验；Triton二进制未完整固定。

## Host/Launcher 执行流程

### 参数校验与前处理

循环验证三Tensor、layout/dtype/device/contiguous→xNPU/ndim/正维→常数类型有限→读取N/H→scale/shift.view(-1)→元素数guard→full分支scaleHguard。所有为元信息，无设备值回读；assert依赖未启用Python-O。分配output后从get_device_properties取P并grid(P,)；helper无参cache/current_device，assertAIC与vector均正，未按x.device设guard，切设备需核对属性相容。

### 参数、Workspace 与生命周期

无workspace/POD/ACLNN executor或显式物理缓冲。Torch保持view底层输入与output，异步完成/stream与compiler临时资源归框架。无显式num_warps/num_stages或host wait。输出分配/属性/JIT异常传播；没有CPUfallback。

### 启动图与失败传播

import→校验/展平→empty_like→helper→full优先dispatch→相应autotune/JIT单Kernel→返回output。两个Kernel不会串联。autotune可重复测量候选，但只读输入、每次全覆盖输出，无累积状态。包原生库加载是导入前提，不是本算术图调用native算子。

## Route 与参数设计

### 分核与资源计算

a×b tile，b128；R=ceil(N/a),Q=ceil(H/128),T=RQ；p轮转t=p+jP<T，row=t//Q,col=t%Q。每tile输出唯一，行/列尾mask。逻辑临时a×128规模不等于物理UB；整数乘积/offset须在实际JIT可表示域。

### Route 选择

先Nt=NH→kernel_2候选a96/80/64且channel scale；否则kernel候选a128/112及scale/shift scalar-or-channel四constexpr组合。用户autotune key均[N,H]，内部specialization键/胜者外部，不按候选顺序指定胜者。

### 模板/实现执行矩阵

| Route | Kernel | a×b | scale | shift | c |
|---|---|---|---|---|---|
| R-001 | kernel | 128×128 | scalar | scalar | 1 |
| R-002 | kernel | 128×128 | scalar | channel | 1 |
| R-003 | kernel | 128×128 | channel | scalar | 1 |
| R-004 | kernel | 128×128 | channel | channel | 1 |
| R-005 | kernel | 112×128 | scalar | scalar | 1 |
| R-006 | kernel | 112×128 | scalar | channel | 1 |
| R-007 | kernel | 112×128 | channel | scalar | 1 |
| R-008 | kernel | 112×128 | channel | channel | 1 |
| R-009 | kernel_2 | 96×128 | channel | full | scale_constant |
| R-010 | kernel_2 | 80×128 | channel | full | scale_constant |
| R-011 | kernel_2 | 64×128 | channel | full | scale_constant |

每行再有三输入dtype的3³组合，控制流相同、ds/dt/dx字节宽独立；无tl.dot/Cube/AIC/MIX节点。H1会消去broadcast channel的“≠1”分支，不能重复当真实可达route实例。

### 隐藏性能 Guard

112/96/80非二次幂而用于tl.arange端点，具体CANN Triton是否扩展支持尚缺固定合同；卡片保留真实配置、不擅自修正，也不写必编译失败。无UB查询/阈值；H不必二次幂因为列arange固定128并有mask。scale_constant只影响full，不能把所有route当相同常数表达式。

### POD/ABI

| 参数 | Kernel/消费 |
|---|---|
| x_ptr/scale_ptr/shift_ptr/output_ptr | 两Kernel指针→load/store；scale/shift view不另拷贝 |
| num_tokens/hidden_size | runtime N/H→任务与偏移 |
| scale_numel/shift_numel | kernel constexpr→各scalar/channelif；kernel_2没有此参数 |
| scale_constant | 仅kernel_2 constexpr→加scale |
| block_l/block_c | 对应候选constexpr→arange与tile |
| kernel_num | P constexpr→任务步长 |
| grid | (P,) |

无自定义序列化ABI/字段位宽或偏移；JIT指针/标量ABI与physical allocation外部，未填猜测POD。

### Route 源码闭包

225行含所有Host/assert和两Kernel，helper完整读，public适配只转发。根setup→torch_wheel.stage_runtime完整复制Python包→build_wheel/setup_refactor；elementwise/backend init无Device。无未知自有节点，不以外部Torch参考代替Device body。

## Kernel 实现

### 公共执行流程

二维任务轮转→mask/广播输入→scale加常数→乘x→加shift→转换输出dtype/store；无归约/GM中间输出，以下逐所有配置/广播组合展开。

### Route R-001：广播shift 128×128 / scale=scalar / shift=scalar

#### 适用条件

##### 选择证据

shift.numel≠N*H，kernel配置 tile(128,128)。scale_numel=1，shift_numel=1。候选列表非胜者顺序，实际autotune选择外部；arange端点二次幂，仍需compiler资源准入。

#### Device 数据流

##### 函数级调用链

`fused_scale_shift→get_device_properties→autotune→fused_scale_shift_kernel→load/mul/add/store`；无额外自有Device。

##### 源码等价伪码

N=B*L，R=ceil(N/128)，Q=ceil(H/128)。program p处理t=p+jP<RQ；row=t//Q,col=t%Q，构造128×128索引。load x二维mask/other0；load scale[0]无mask；load shift[0]无mask；`y=x*(1.0+scale)+shift`；显式转output元素dtype并二维maskstore。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 每task逻辑访问/规模 |
|---|---|
| x/output | 128×128元素；有效m×n时各m*n*dx B读/写 |
| scale | 1元素，ds B无mask，广播m行 |
| shift | 1元素，dt B无mask |
| 输出算术 | 128×128逻辑SSA，实际dtype推广依赖primitive；不强称全部FP32 |
| workspace/UB/TQue/TBuf | 无显式分配，compiler物理分配外部 |

##### 分层内存布局

GM x[N,H]/scale/shift→mask或scalar SSA→广播与算术→GM output[N,H]。scalar shift无显式FP32转换。源码逻辑张量不是实际UB缓冲对象。

##### 字节账与复用顺序

令R=ceil(N/128),Q=ceil(H/128)。输入输出合计2NHdx B；scale读取R*Q*ds B；shift读取R*Q*dt B。按源码load逻辑次数计，不假设compiler hoist、cache或DMA事务。每输入只读，output独立新存储，异步生命周期归Torch/Triton；无workspace交接或显式回收事件。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 任务覆盖 | 模P轮转与商余二维映射唯一，输出不交叠、无原子/barrier |
| 行/列尾 | x/output二维mask，channel向量列mask/other0；scalar无mask但Host保证numel1 |
| 算术 | 固定1.0加scale；未向Kernel传scale_constant，shift保留加载dtype，输出显式转dx |
| dtype | x/scale/shift独立三浮点dtype，隐式promotion与融合属于Triton，不能套所有FP32中间的统一精度 |
| compiler | 资源与物理lowering外部 |
| 同步 | SSA依赖由compiler执行；无显式stream/host等待；输入值非有限时无修复 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| candidate与body | [kernel](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L13-L75) |
| dispatch | [Host先匹配full](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L188-L223) |


### Route R-002：广播shift 128×128 / scale=scalar / shift=channel

#### 适用条件

##### 选择证据

shift.numel≠N*H，kernel配置 tile(128,128)。scale_numel=1，shift_numel≠1且=H。候选列表非胜者顺序，实际autotune选择外部；arange端点二次幂，仍需compiler资源准入。

#### Device 数据流

##### 函数级调用链

`fused_scale_shift→get_device_properties→autotune→fused_scale_shift_kernel→load/mul/add/store`；无额外自有Device。

##### 源码等价伪码

N=B*L，R=ceil(N/128)，Q=ceil(H/128)。program p处理t=p+jP<RQ；row=t//Q,col=t%Q，构造128×128索引。load x二维mask/other0；load scale[0]无mask；按列mask读shift[h]并转FP32；`y=x*(1.0+scale)+shift`；显式转output元素dtype并二维maskstore。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 每task逻辑访问/规模 |
|---|---|
| x/output | 128×128元素；有效m×n时各m*n*dx B读/写 |
| scale | 1元素，ds B无mask，广播m行 |
| shift | 128列逻辑，n*dt B读并转FP32 |
| 输出算术 | 128×128逻辑SSA，实际dtype推广依赖primitive；不强称全部FP32 |
| workspace/UB/TQue/TBuf | 无显式分配，compiler物理分配外部 |

##### 分层内存布局

GM x[N,H]/scale/shift→mask或scalar SSA→广播与算术→GM output[N,H]。shift显式FP32转换。源码逻辑张量不是实际UB缓冲对象。

##### 字节账与复用顺序

令R=ceil(N/128),Q=ceil(H/128)。输入输出合计2NHdx B；scale读取R*Q*ds B；shift读取R*H*dt B。按源码load逻辑次数计，不假设compiler hoist、cache或DMA事务。每输入只读，output独立新存储，异步生命周期归Torch/Triton；无workspace交接或显式回收事件。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 任务覆盖 | 模P轮转与商余二维映射唯一，输出不交叠、无原子/barrier |
| 行/列尾 | x/output二维mask，channel向量列mask/other0；scalar无mask但Host保证numel1 |
| 算术 | 固定1.0加scale；未向Kernel传scale_constant，shift转FP32，输出显式转dx |
| dtype | x/scale/shift独立三浮点dtype，隐式promotion与融合属于Triton，不能套所有FP32中间的统一精度 |
| compiler | 资源与物理lowering外部 |
| 同步 | SSA依赖由compiler执行；无显式stream/host等待；输入值非有限时无修复 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| candidate与body | [kernel](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L13-L75) |
| dispatch | [Host先匹配full](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L188-L223) |


### Route R-003：广播shift 128×128 / scale=channel / shift=scalar

#### 适用条件

##### 选择证据

shift.numel≠N*H，kernel配置 tile(128,128)。scale_numel≠1且=H，shift_numel=1。候选列表非胜者顺序，实际autotune选择外部；arange端点二次幂，仍需compiler资源准入。

#### Device 数据流

##### 函数级调用链

`fused_scale_shift→get_device_properties→autotune→fused_scale_shift_kernel→load/mul/add/store`；无额外自有Device。

##### 源码等价伪码

N=B*L，R=ceil(N/128)，Q=ceil(H/128)。program p处理t=p+jP<RQ；row=t//Q,col=t%Q，构造128×128索引。load x二维mask/other0；按列mask读取scale[h]；load shift[0]无mask；`y=x*(1.0+scale)+shift`；显式转output元素dtype并二维maskstore。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 每task逻辑访问/规模 |
|---|---|
| x/output | 128×128元素；有效m×n时各m*n*dx B读/写 |
| scale | 128列逻辑，n*ds B有效，广播m行 |
| shift | 1元素，dt B无mask |
| 输出算术 | 128×128逻辑SSA，实际dtype推广依赖primitive；不强称全部FP32 |
| workspace/UB/TQue/TBuf | 无显式分配，compiler物理分配外部 |

##### 分层内存布局

GM x[N,H]/scale/shift→mask或scalar SSA→广播与算术→GM output[N,H]。scalar shift无显式FP32转换。源码逻辑张量不是实际UB缓冲对象。

##### 字节账与复用顺序

令R=ceil(N/128),Q=ceil(H/128)。输入输出合计2NHdx B；scale读取R*H*ds B；shift读取R*Q*dt B。按源码load逻辑次数计，不假设compiler hoist、cache或DMA事务。每输入只读，output独立新存储，异步生命周期归Torch/Triton；无workspace交接或显式回收事件。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 任务覆盖 | 模P轮转与商余二维映射唯一，输出不交叠、无原子/barrier |
| 行/列尾 | x/output二维mask，channel向量列mask/other0；scalar无mask但Host保证numel1 |
| 算术 | 固定1.0加scale；未向Kernel传scale_constant，shift保留加载dtype，输出显式转dx |
| dtype | x/scale/shift独立三浮点dtype，隐式promotion与融合属于Triton，不能套所有FP32中间的统一精度 |
| compiler | 资源与物理lowering外部 |
| 同步 | SSA依赖由compiler执行；无显式stream/host等待；输入值非有限时无修复 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| candidate与body | [kernel](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L13-L75) |
| dispatch | [Host先匹配full](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L188-L223) |


### Route R-004：广播shift 128×128 / scale=channel / shift=channel

#### 适用条件

##### 选择证据

shift.numel≠N*H，kernel配置 tile(128,128)。scale_numel≠1且=H，shift_numel≠1且=H。候选列表非胜者顺序，实际autotune选择外部；arange端点二次幂，仍需compiler资源准入。

#### Device 数据流

##### 函数级调用链

`fused_scale_shift→get_device_properties→autotune→fused_scale_shift_kernel→load/mul/add/store`；无额外自有Device。

##### 源码等价伪码

N=B*L，R=ceil(N/128)，Q=ceil(H/128)。program p处理t=p+jP<RQ；row=t//Q,col=t%Q，构造128×128索引。load x二维mask/other0；按列mask读取scale[h]；按列mask读shift[h]并转FP32；`y=x*(1.0+scale)+shift`；显式转output元素dtype并二维maskstore。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 每task逻辑访问/规模 |
|---|---|
| x/output | 128×128元素；有效m×n时各m*n*dx B读/写 |
| scale | 128列逻辑，n*ds B有效，广播m行 |
| shift | 128列逻辑，n*dt B读并转FP32 |
| 输出算术 | 128×128逻辑SSA，实际dtype推广依赖primitive；不强称全部FP32 |
| workspace/UB/TQue/TBuf | 无显式分配，compiler物理分配外部 |

##### 分层内存布局

GM x[N,H]/scale/shift→mask或scalar SSA→广播与算术→GM output[N,H]。shift显式FP32转换。源码逻辑张量不是实际UB缓冲对象。

##### 字节账与复用顺序

令R=ceil(N/128),Q=ceil(H/128)。输入输出合计2NHdx B；scale读取R*H*ds B；shift读取R*H*dt B。按源码load逻辑次数计，不假设compiler hoist、cache或DMA事务。每输入只读，output独立新存储，异步生命周期归Torch/Triton；无workspace交接或显式回收事件。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 任务覆盖 | 模P轮转与商余二维映射唯一，输出不交叠、无原子/barrier |
| 行/列尾 | x/output二维mask，channel向量列mask/other0；scalar无mask但Host保证numel1 |
| 算术 | 固定1.0加scale；未向Kernel传scale_constant，shift转FP32，输出显式转dx |
| dtype | x/scale/shift独立三浮点dtype，隐式promotion与融合属于Triton，不能套所有FP32中间的统一精度 |
| compiler | 资源与物理lowering外部 |
| 同步 | SSA依赖由compiler执行；无显式stream/host等待；输入值非有限时无修复 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| candidate与body | [kernel](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L13-L75) |
| dispatch | [Host先匹配full](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L188-L223) |


### Route R-005：广播shift 112×128 / scale=scalar / shift=scalar

#### 适用条件

##### 选择证据

shift.numel≠N*H，kernel配置 tile(112,128)。scale_numel=1，shift_numel=1。候选列表非胜者顺序，实际autotune选择外部；arange(0,112)非二次幂，具体CANN Triton扩展准入尚未固定，未宣称编译成功或失败。

#### Device 数据流

##### 函数级调用链

`fused_scale_shift→get_device_properties→autotune→fused_scale_shift_kernel→load/mul/add/store`；无额外自有Device。

##### 源码等价伪码

N=B*L，R=ceil(N/112)，Q=ceil(H/128)。program p处理t=p+jP<RQ；row=t//Q,col=t%Q，构造112×128索引。load x二维mask/other0；load scale[0]无mask；load shift[0]无mask；`y=x*(1.0+scale)+shift`；显式转output元素dtype并二维maskstore。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 每task逻辑访问/规模 |
|---|---|
| x/output | 112×128元素；有效m×n时各m*n*dx B读/写 |
| scale | 1元素，ds B无mask，广播m行 |
| shift | 1元素，dt B无mask |
| 输出算术 | 112×128逻辑SSA，实际dtype推广依赖primitive；不强称全部FP32 |
| workspace/UB/TQue/TBuf | 无显式分配，compiler物理分配外部 |

##### 分层内存布局

GM x[N,H]/scale/shift→mask或scalar SSA→广播与算术→GM output[N,H]。scalar shift无显式FP32转换。源码逻辑张量不是实际UB缓冲对象。

##### 字节账与复用顺序

令R=ceil(N/112),Q=ceil(H/128)。输入输出合计2NHdx B；scale读取R*Q*ds B；shift读取R*Q*dt B。按源码load逻辑次数计，不假设compiler hoist、cache或DMA事务。每输入只读，output独立新存储，异步生命周期归Torch/Triton；无workspace交接或显式回收事件。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 任务覆盖 | 模P轮转与商余二维映射唯一，输出不交叠、无原子/barrier |
| 行/列尾 | x/output二维mask，channel向量列mask/other0；scalar无mask但Host保证numel1 |
| 算术 | 固定1.0加scale；未向Kernel传scale_constant，shift保留加载dtype，输出显式转dx |
| dtype | x/scale/shift独立三浮点dtype，隐式promotion与融合属于Triton，不能套所有FP32中间的统一精度 |
| compiler | 非二次幂行arange需工具链扩展准入 |
| 同步 | SSA依赖由compiler执行；无显式stream/host等待；输入值非有限时无修复 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| candidate与body | [kernel](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L13-L75) |
| dispatch | [Host先匹配full](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L188-L223) |


### Route R-006：广播shift 112×128 / scale=scalar / shift=channel

#### 适用条件

##### 选择证据

shift.numel≠N*H，kernel配置 tile(112,128)。scale_numel=1，shift_numel≠1且=H。候选列表非胜者顺序，实际autotune选择外部；arange(0,112)非二次幂，具体CANN Triton扩展准入尚未固定，未宣称编译成功或失败。

#### Device 数据流

##### 函数级调用链

`fused_scale_shift→get_device_properties→autotune→fused_scale_shift_kernel→load/mul/add/store`；无额外自有Device。

##### 源码等价伪码

N=B*L，R=ceil(N/112)，Q=ceil(H/128)。program p处理t=p+jP<RQ；row=t//Q,col=t%Q，构造112×128索引。load x二维mask/other0；load scale[0]无mask；按列mask读shift[h]并转FP32；`y=x*(1.0+scale)+shift`；显式转output元素dtype并二维maskstore。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 每task逻辑访问/规模 |
|---|---|
| x/output | 112×128元素；有效m×n时各m*n*dx B读/写 |
| scale | 1元素，ds B无mask，广播m行 |
| shift | 128列逻辑，n*dt B读并转FP32 |
| 输出算术 | 112×128逻辑SSA，实际dtype推广依赖primitive；不强称全部FP32 |
| workspace/UB/TQue/TBuf | 无显式分配，compiler物理分配外部 |

##### 分层内存布局

GM x[N,H]/scale/shift→mask或scalar SSA→广播与算术→GM output[N,H]。shift显式FP32转换。源码逻辑张量不是实际UB缓冲对象。

##### 字节账与复用顺序

令R=ceil(N/112),Q=ceil(H/128)。输入输出合计2NHdx B；scale读取R*Q*ds B；shift读取R*H*dt B。按源码load逻辑次数计，不假设compiler hoist、cache或DMA事务。每输入只读，output独立新存储，异步生命周期归Torch/Triton；无workspace交接或显式回收事件。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 任务覆盖 | 模P轮转与商余二维映射唯一，输出不交叠、无原子/barrier |
| 行/列尾 | x/output二维mask，channel向量列mask/other0；scalar无mask但Host保证numel1 |
| 算术 | 固定1.0加scale；未向Kernel传scale_constant，shift转FP32，输出显式转dx |
| dtype | x/scale/shift独立三浮点dtype，隐式promotion与融合属于Triton，不能套所有FP32中间的统一精度 |
| compiler | 非二次幂行arange需工具链扩展准入 |
| 同步 | SSA依赖由compiler执行；无显式stream/host等待；输入值非有限时无修复 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| candidate与body | [kernel](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L13-L75) |
| dispatch | [Host先匹配full](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L188-L223) |


### Route R-007：广播shift 112×128 / scale=channel / shift=scalar

#### 适用条件

##### 选择证据

shift.numel≠N*H，kernel配置 tile(112,128)。scale_numel≠1且=H，shift_numel=1。候选列表非胜者顺序，实际autotune选择外部；arange(0,112)非二次幂，具体CANN Triton扩展准入尚未固定，未宣称编译成功或失败。

#### Device 数据流

##### 函数级调用链

`fused_scale_shift→get_device_properties→autotune→fused_scale_shift_kernel→load/mul/add/store`；无额外自有Device。

##### 源码等价伪码

N=B*L，R=ceil(N/112)，Q=ceil(H/128)。program p处理t=p+jP<RQ；row=t//Q,col=t%Q，构造112×128索引。load x二维mask/other0；按列mask读取scale[h]；load shift[0]无mask；`y=x*(1.0+scale)+shift`；显式转output元素dtype并二维maskstore。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 每task逻辑访问/规模 |
|---|---|
| x/output | 112×128元素；有效m×n时各m*n*dx B读/写 |
| scale | 128列逻辑，n*ds B有效，广播m行 |
| shift | 1元素，dt B无mask |
| 输出算术 | 112×128逻辑SSA，实际dtype推广依赖primitive；不强称全部FP32 |
| workspace/UB/TQue/TBuf | 无显式分配，compiler物理分配外部 |

##### 分层内存布局

GM x[N,H]/scale/shift→mask或scalar SSA→广播与算术→GM output[N,H]。scalar shift无显式FP32转换。源码逻辑张量不是实际UB缓冲对象。

##### 字节账与复用顺序

令R=ceil(N/112),Q=ceil(H/128)。输入输出合计2NHdx B；scale读取R*H*ds B；shift读取R*Q*dt B。按源码load逻辑次数计，不假设compiler hoist、cache或DMA事务。每输入只读，output独立新存储，异步生命周期归Torch/Triton；无workspace交接或显式回收事件。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 任务覆盖 | 模P轮转与商余二维映射唯一，输出不交叠、无原子/barrier |
| 行/列尾 | x/output二维mask，channel向量列mask/other0；scalar无mask但Host保证numel1 |
| 算术 | 固定1.0加scale；未向Kernel传scale_constant，shift保留加载dtype，输出显式转dx |
| dtype | x/scale/shift独立三浮点dtype，隐式promotion与融合属于Triton，不能套所有FP32中间的统一精度 |
| compiler | 非二次幂行arange需工具链扩展准入 |
| 同步 | SSA依赖由compiler执行；无显式stream/host等待；输入值非有限时无修复 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| candidate与body | [kernel](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L13-L75) |
| dispatch | [Host先匹配full](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L188-L223) |


### Route R-008：广播shift 112×128 / scale=channel / shift=channel

#### 适用条件

##### 选择证据

shift.numel≠N*H，kernel配置 tile(112,128)。scale_numel≠1且=H，shift_numel≠1且=H。候选列表非胜者顺序，实际autotune选择外部；arange(0,112)非二次幂，具体CANN Triton扩展准入尚未固定，未宣称编译成功或失败。

#### Device 数据流

##### 函数级调用链

`fused_scale_shift→get_device_properties→autotune→fused_scale_shift_kernel→load/mul/add/store`；无额外自有Device。

##### 源码等价伪码

N=B*L，R=ceil(N/112)，Q=ceil(H/128)。program p处理t=p+jP<RQ；row=t//Q,col=t%Q，构造112×128索引。load x二维mask/other0；按列mask读取scale[h]；按列mask读shift[h]并转FP32；`y=x*(1.0+scale)+shift`；显式转output元素dtype并二维maskstore。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 每task逻辑访问/规模 |
|---|---|
| x/output | 112×128元素；有效m×n时各m*n*dx B读/写 |
| scale | 128列逻辑，n*ds B有效，广播m行 |
| shift | 128列逻辑，n*dt B读并转FP32 |
| 输出算术 | 112×128逻辑SSA，实际dtype推广依赖primitive；不强称全部FP32 |
| workspace/UB/TQue/TBuf | 无显式分配，compiler物理分配外部 |

##### 分层内存布局

GM x[N,H]/scale/shift→mask或scalar SSA→广播与算术→GM output[N,H]。shift显式FP32转换。源码逻辑张量不是实际UB缓冲对象。

##### 字节账与复用顺序

令R=ceil(N/112),Q=ceil(H/128)。输入输出合计2NHdx B；scale读取R*H*ds B；shift读取R*H*dt B。按源码load逻辑次数计，不假设compiler hoist、cache或DMA事务。每输入只读，output独立新存储，异步生命周期归Torch/Triton；无workspace交接或显式回收事件。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 任务覆盖 | 模P轮转与商余二维映射唯一，输出不交叠、无原子/barrier |
| 行/列尾 | x/output二维mask，channel向量列mask/other0；scalar无mask但Host保证numel1 |
| 算术 | 固定1.0加scale；未向Kernel传scale_constant，shift转FP32，输出显式转dx |
| dtype | x/scale/shift独立三浮点dtype，隐式promotion与融合属于Triton，不能套所有FP32中间的统一精度 |
| compiler | 非二次幂行arange需工具链扩展准入 |
| 同步 | SSA依赖由compiler执行；无显式stream/host等待；输入值非有限时无修复 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| candidate与body | [kernel](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L13-L75) |
| dispatch | [Host先匹配full](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L188-L223) |


### Route R-009：逐元素shift 96×128 / scale=channel / shift=full

#### 适用条件

##### 选择证据

shift.numel=N*H优先匹配，scale.numel=H；kernel_2配置 tile(96,128)。无scalar/channel constexpr分支。候选列表非胜者顺序，实际autotune选择外部；arange(0,96)非二次幂，具体CANN Triton扩展准入尚未固定，未宣称编译成功或失败。

#### Device 数据流

##### 函数级调用链

`fused_scale_shift→get_device_properties→autotune→fused_scale_shift_kernel_2→load/mul/add/store`；无额外自有Device。

##### 源码等价伪码

N=B*L，R=ceil(N/96)，Q=ceil(H/128)。program p处理t=p+jP<RQ；row=t//Q,col=t%Q，构造96×128索引。load x二维mask/other0；按列mask读取scale[h]；按x同offset二维mask读shift并转FP32；`y=x*(scale_constant+scale)+shift`；显式转output元素dtype并二维maskstore。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 每task逻辑访问/规模 |
|---|---|
| x/output | 96×128元素；有效m×n时各m*n*dx B读/写 |
| scale | 128列逻辑，n*ds B有效，广播m行 |
| shift | 二维tile，m*n*dt B读，转换FP32 |
| 输出算术 | 96×128逻辑SSA，实际dtype推广依赖primitive；不强称全部FP32 |
| workspace/UB/TQue/TBuf | 无显式分配，compiler物理分配外部 |

##### 分层内存布局

GM x[N,H]/scale/shift→mask或scalar SSA→广播与算术→GM output[N,H]。shift显式FP32转换。源码逻辑张量不是实际UB缓冲对象。

##### 字节账与复用顺序

令R=ceil(N/96),Q=ceil(H/128)。输入输出合计2NHdx B；scale读取R*H*ds B；shift读取N*H*dt B。按源码load逻辑次数计，不假设compiler hoist、cache或DMA事务。每输入只读，output独立新存储，异步生命周期归Torch/Triton；无workspace交接或显式回收事件。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 任务覆盖 | 模P轮转与商余二维映射唯一，输出不交叠、无原子/barrier |
| 行/列尾 | x/output二维mask，channel向量列mask/other0；scalar无mask但Host保证numel1 |
| 算术 | scale_constant为constexpr加scale，shift转FP32，输出显式转dx |
| dtype | x/scale/shift独立三浮点dtype，隐式promotion与融合属于Triton，不能套所有FP32中间的统一精度 |
| compiler | 非二次幂行arange需工具链扩展准入 |
| 同步 | SSA依赖由compiler执行；无显式stream/host等待；输入值非有限时无修复 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| candidate与body | [kernel_2](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L78-L132) |
| dispatch | [Host先匹配full](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L188-L223) |


### Route R-010：逐元素shift 80×128 / scale=channel / shift=full

#### 适用条件

##### 选择证据

shift.numel=N*H优先匹配，scale.numel=H；kernel_2配置 tile(80,128)。无scalar/channel constexpr分支。候选列表非胜者顺序，实际autotune选择外部；arange(0,80)非二次幂，具体CANN Triton扩展准入尚未固定，未宣称编译成功或失败。

#### Device 数据流

##### 函数级调用链

`fused_scale_shift→get_device_properties→autotune→fused_scale_shift_kernel_2→load/mul/add/store`；无额外自有Device。

##### 源码等价伪码

N=B*L，R=ceil(N/80)，Q=ceil(H/128)。program p处理t=p+jP<RQ；row=t//Q,col=t%Q，构造80×128索引。load x二维mask/other0；按列mask读取scale[h]；按x同offset二维mask读shift并转FP32；`y=x*(scale_constant+scale)+shift`；显式转output元素dtype并二维maskstore。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 每task逻辑访问/规模 |
|---|---|
| x/output | 80×128元素；有效m×n时各m*n*dx B读/写 |
| scale | 128列逻辑，n*ds B有效，广播m行 |
| shift | 二维tile，m*n*dt B读，转换FP32 |
| 输出算术 | 80×128逻辑SSA，实际dtype推广依赖primitive；不强称全部FP32 |
| workspace/UB/TQue/TBuf | 无显式分配，compiler物理分配外部 |

##### 分层内存布局

GM x[N,H]/scale/shift→mask或scalar SSA→广播与算术→GM output[N,H]。shift显式FP32转换。源码逻辑张量不是实际UB缓冲对象。

##### 字节账与复用顺序

令R=ceil(N/80),Q=ceil(H/128)。输入输出合计2NHdx B；scale读取R*H*ds B；shift读取N*H*dt B。按源码load逻辑次数计，不假设compiler hoist、cache或DMA事务。每输入只读，output独立新存储，异步生命周期归Torch/Triton；无workspace交接或显式回收事件。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 任务覆盖 | 模P轮转与商余二维映射唯一，输出不交叠、无原子/barrier |
| 行/列尾 | x/output二维mask，channel向量列mask/other0；scalar无mask但Host保证numel1 |
| 算术 | scale_constant为constexpr加scale，shift转FP32，输出显式转dx |
| dtype | x/scale/shift独立三浮点dtype，隐式promotion与融合属于Triton，不能套所有FP32中间的统一精度 |
| compiler | 非二次幂行arange需工具链扩展准入 |
| 同步 | SSA依赖由compiler执行；无显式stream/host等待；输入值非有限时无修复 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| candidate与body | [kernel_2](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L78-L132) |
| dispatch | [Host先匹配full](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L188-L223) |


### Route R-011：逐元素shift 64×128 / scale=channel / shift=full

#### 适用条件

##### 选择证据

shift.numel=N*H优先匹配，scale.numel=H；kernel_2配置 tile(64,128)。无scalar/channel constexpr分支。候选列表非胜者顺序，实际autotune选择外部；arange端点二次幂，仍需compiler资源准入。

#### Device 数据流

##### 函数级调用链

`fused_scale_shift→get_device_properties→autotune→fused_scale_shift_kernel_2→load/mul/add/store`；无额外自有Device。

##### 源码等价伪码

N=B*L，R=ceil(N/64)，Q=ceil(H/128)。program p处理t=p+jP<RQ；row=t//Q,col=t%Q，构造64×128索引。load x二维mask/other0；按列mask读取scale[h]；按x同offset二维mask读shift并转FP32；`y=x*(scale_constant+scale)+shift`；显式转output元素dtype并二维maskstore。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 每task逻辑访问/规模 |
|---|---|
| x/output | 64×128元素；有效m×n时各m*n*dx B读/写 |
| scale | 128列逻辑，n*ds B有效，广播m行 |
| shift | 二维tile，m*n*dt B读，转换FP32 |
| 输出算术 | 64×128逻辑SSA，实际dtype推广依赖primitive；不强称全部FP32 |
| workspace/UB/TQue/TBuf | 无显式分配，compiler物理分配外部 |

##### 分层内存布局

GM x[N,H]/scale/shift→mask或scalar SSA→广播与算术→GM output[N,H]。shift显式FP32转换。源码逻辑张量不是实际UB缓冲对象。

##### 字节账与复用顺序

令R=ceil(N/64),Q=ceil(H/128)。输入输出合计2NHdx B；scale读取R*H*ds B；shift读取N*H*dt B。按源码load逻辑次数计，不假设compiler hoist、cache或DMA事务。每输入只读，output独立新存储，异步生命周期归Torch/Triton；无workspace交接或显式回收事件。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 任务覆盖 | 模P轮转与商余二维映射唯一，输出不交叠、无原子/barrier |
| 行/列尾 | x/output二维mask，channel向量列mask/other0；scalar无mask但Host保证numel1 |
| 算术 | scale_constant为constexpr加scale，shift转FP32，输出显式转dx |
| dtype | x/scale/shift独立三浮点dtype，隐式promotion与融合属于Triton，不能套所有FP32中间的统一精度 |
| compiler | 资源与物理lowering外部 |
| 同步 | SSA依赖由compiler执行；无显式stream/host等待；输入值非有限时无修复 |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| candidate与body | [kernel_2](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L78-L132) |
| dispatch | [Host先匹配full](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L188-L223) |

## 算子特定优化

### Trick T-001：按实际元素数优先选择full shift

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L188-L193)：

```python
    # The elementwise-shift kernel reads one scale value per hidden channel.
    # Reject a scalar here instead of reading beyond its allocation.
    if shift_numel == x_numel:
        assert (
            scale_numel == hidden_size
        ), f"Elementwise shift requires {hidden_size} scale values, got {scale_numel}"
```

#### 机制与设计原因

full Kernel固定按列读scale，Host必须挡住H>1的scalar输入；元素数重合按真实优先级走full，保证指针读取的storage长度前提。没有运行安全证明之外的性能结果。

#### 迁移边界

先检查Nt=NH再做其它广播解释，且assert未被关闭；若改成scalar scale full支持须同时改Device读取语义。

#### 错误做法

只按调用者原shape猜channel模式，或把N1的Nt=H强行送广播Kernel。

### Trick T-002：广播Kernel只读一份列向量

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py#L57-L62)：

```python
        if scale_numel == 1:
            scale = tl.load(scale_ptr)
        else:
            scale_offsets = dim_offsets[None, :]
            scale_mask = dim_offsets[None, :] < hidden_size
            scale = tl.load(scale_ptr + scale_offsets, mask=scale_mask, other=0.0)
```

#### 机制与设计原因

scalar只load一个值；channel读取[1,128]逻辑向量后广播行块，不在GM复制N份scale。逻辑读取次数随R/Q变化，不能假设所有program缓存共享或实际只读一次。

#### 迁移边界

scale必须连续且numel符合分支；datatype promotion按真实加载dtype，不默认为所有中间FP32。

#### 错误做法

把广播Kernel常数1替换scale_constant，或用kernel_2公式做所有分支参考。

## 模板与实现对比

11条路线由两Kernel/five候选/constexpr广播组成，同一公开scale_shift语义含明确模式选择。channel/full shift有显式FP32转换，scalar shift没有；x/scale也没有显式FP32 cast，不能声明统一全FP32计算。最终output显式转换为输入dtype。

## 平台差异

本卡A2/A3归属arch22；公开arch22/35均支持，README/architectures映射A2/A3及950，自有代码无硬件分支。CI CANN9.1.0 a3/950为配置证据非本次执行/A2实测；非二次幂arange与资源lowering须匹配工具链。

## 限制与失败边界

所有guard为assert、可被-O关闭；设备helper缓存不绑定x.device。非二次幂候选的compiler准入及物理资源未证明，不宣称故障或安全上限。有限输入按各dtype实际promotion/舍入使用，NaN/Inf无修复。未运行编译、autotune、上游测试或校验，无真机/性能复现，draft保留边界。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开合同](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/elementwise/fused_scale_shift.md) | `fused_scale_shift` | 分支优先级/常数/平台 |
| [Direct及Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/scale_shift.py) | `fused_scale_shift[_kernel/_kernel_2]` | 完整225行/校验/两Kernel五配置 |
| [公开转发](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/elementwise/scale_shift.py) | `_triton_impl` | auto/triton独立转发 |
| [elementwise包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/elementwise/__init__.py) | `module init` | 无Device |
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

冻结117/legacy同主题API已完整读，链接复用；只新增唯一Direct两平台卡，不改API/不拆无授权新语义，全部source同repo唯一primary、无verified。
