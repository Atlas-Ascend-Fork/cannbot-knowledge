---
type: Operator
title: "FusedSplitQkNorm A2/A3 Direct Invoke 算子知识"
description: "闭合MLA低秩三段拆分的四bias特化、FP32独立RMSNorm与PE复制，保留空输入、完整元信息校验及非二次幂arange准入边界。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/fused_split_qk_norm.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/fused_split_qk_norm.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/norm_utils.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/norm/fused_split_qk_norm.py
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
created_at: "2026-11-09T09:21:40Z"
updated_at: "2026-11-09T09:24:37Z"
platforms: [a2, a3]
cann_versions: ["9.1.0"]
---

# FusedSplitQkNorm A2/A3 Direct Invoke 算子知识

## 算子速览

`sgl_kernel_npu.implementation.triton.norm.fused_split_qk_norm.fused_split_qk_norm` 把MLA低秩投影[N,Rq+Rk+Dr]拆为Q/K/旋转K三段，前两段分别FP32 RMSNorm与独立weight/bias，末段直接复制。不是attention、RoPE旋转或矩阵乘。完整自有校验、空输入Host路线、四bias特化均闭合。

draft保留真实编译准入边界：三个arange直接以正rank/dim为终点，Host未限制二次幂；公开合同的任意正整数不能据此推定每个shape可编译。支持声明自身注明硬件仍待验证；本次无运行证据。复用全文读过的[公开API](../../../../apis/sgl_kernel_npu/sgl_fused_split_qk_norm.md)。

## 接口与语义

### 计算语义

令H=Rq+Rk+Dr、Z=[Q|K|PE]。`Qout=Q*rsqrt(mean(Q²)+eps)*qw+(qb if enabled else 0)`；K独立同式，均方分别除Rq/Rk，不合并统计；`PEout=PE`。对象只提供属性，不调用forward或对象自带epsilon，显式eps统一控制两段。

### 输入、输出与属性

| 项 | 合同与真实检查 |
|---|---|
| Z | torch.Tensor、strided、FP16/BF16/FP32、连续二维、宽恰H、NPU |
| Rq/Rk/Dr | 正Python int，排除bool；未检查二次幂 |
| qw/kw及可选qb/kb | Tensor，strided/连续、同device、三浮点dtype任意、numel≥对应rank；并未要求1D或同输入dtype |
| eps | int/float，排除bool，有限且>0 |
| 三输出 | 新连续[N,Rq]、[N,1,Rk]、[N,1,Dr]，同输入dtype/device；输入/权重/bias均只读 |

### 入口与版本

Direct函数签名为(Z,q_a_layernorm,kv_a_layernorm,q_lora_rank,kv_lora_rank,qk_rope_dim,eps=1e-6)。auto/triton只延迟转发，torch_native独立参考不并入本图。固定SGL commit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`，CANN9.1.0来自README/CI norm配置，非本次环境；未固定Triton编译器二进制。

## Host/Launcher 执行流程

### 参数校验与前处理

validate_split_qk_norm按floating_tensor检查Z→positive_int检查三维→ndim/宽度→epsilon→两个对象weight存在性/vector→独立可选bias/vector；随后launcher额外assertNPU和三正维。全部为元信息，无设备值回读。实际assert依赖Python未启用-O，不能把assert当任何部署都不可绕过的保护。N=0也完成上述元信息校验。

### 参数、Workspace 与生命周期

分配Q[N,Rq]、K[N,Rk]、PE[N,Dr]；N0直接返回并对K/PE unsqueeze(1)，不启动JIT。N>0启动grid(N,)再unsqueeze。无workspace、POD、ACLNN、核数helper；无显式stream/wait/num_warps/stages，实际ABI/分配/lowering由框架负责。输出Tensor持有数据，unsqueeze是view；三输入及affine必须按框架异步使用规则存活。

### 启动图与失败传播

`import → validate树 → NPUassert → 分配 → N0返回或四bias特化之一的单Kernel → view返回`。元信息非法assert、分配或JIT/launch异常直接传播，无fallback。包初始化原生库是导入依赖，不是本Kernel调用原生矩阵/attention实现。

## Route 与参数设计

### 分核与资源计算

N>0时一program一token，grid=N；无分核roundup/循环任务。每行输入H元素，三输出总H元素；读取affine随token重复。FP32中间按Rq/Rk逻辑大小，不知道compiler是否并存/复用、物理UB/register/spill。

### Route 选择

| Host/Route | 条件 | 后续 |
|---|---|---|
| H-000 | N=0且元信息合法 | 仅空输出/view，无Device |
| R-001 | N>0,Qbias无,Kbias无 | 两affine乘 |
| R-002 | N>0,Qbias有,Kbias无 | Q另加bias |
| R-003 | N>0,Qbias无,Kbias有 | K另加bias |
| R-004 | N>0,两bias有 | 两段独立加bias |

### 模板/实现执行矩阵

Q/K flags各独立constexpr，四组合不能误作成对开关。Z、qw、kw及启用bias均可三浮点dtype组合，控制图相同、各向量字节宽独立计费。无tl.dot/Cube/AIC/MIX自有节点。没有autotune或shape到warp/stage规则。

### 隐藏性能 Guard

Host仅校验正rank，不向上补齐arange。非二次幂终点的CANN Triton扩展合同未固定，不能宣称编译失败或成功；以二次幂且资源可编译域使用是额外前提，不擅自缩窄公共API合同。无物理UB查询/容量限制，超大rank还受JIT整数/资源可表示域。

### POD/ABI

| 参数 | 生产/消费 |
|---|---|
| fused_ptr | Z→三段load |
| q_lora_ptr/k_nope_ptr/k_pe_ptr | 三empty→各store |
| q_rms_w_ptr/k_rms_w_ptr | 对象weight→对应affine |
| q_rms_b_ptr/k_rms_b_ptr | 对象bias或None→启用时load |
| total_hidden | H constexpr→输入行步长 |
| q_lora_rank/kv_lora_rank/qk_rope_dim | constexpr→arange、段起点、输出步长/除数 |
| eps | constexpr→两rsqrt |
| Q_HAS_BIAS/K_HAS_BIAS | constexpr→两独立if |
| grid | (N,) |

无自定义序列化、字节偏移或POD字段；指针/constexpr ABI是Triton边界，未虚构位宽。

### Route 源码闭包

完整149行实现及norm_utils可达8–69行全部读取，无未知自有函数。公开转发仅导入调用，不调用对象forward。根setup→stage_runtime完整Python包→build_wheel/setup_refactor的包路径已读；backend/norm初始化无Device。优化经验候选只读作去重判断，未引用其性能数字或原理来代替当前源码。

## Kernel 实现

### 公共执行流程

Q normalize/store→K normalize/store→PE copy/store；源码顺序表明三个段，无共享统计或额外Kernel，所有程序按token分离。H-000无Device对象/bytes。四实际特化如下。

### Route R-001：Q_HAS_BIAS=false，K_HAS_BIAS=false

#### 适用条件

##### 选择证据

N>0；launcher以`hasattr(norm,"bias") and norm.bias is not None`分别形成constexpr。本特化Q偏置关闭、K偏置关闭；无shape排序或autotune。Rq/Rk/Dr正但validator未检查二次幂，实际arange准入须匹配工具链。

#### Device 数据流

##### 函数级调用链

`fused_split_qk_norm→validate_split_qk_norm→kernel→Q平方和/rsqrt/affine→K平方和/rsqrt/affine→PE load/store`；validator递归到positive_int/epsilon/floating_tensor/vector，均为Host元信息。Device仅这一Kernel，无attention/RoPE算子。

##### 源码等价伪码

token p：输入base=pH；读Q[0,Rq)转FP32→sum(Q²)/Rq→rsqrt(+eps)→乘qw→storeq；读K[Rq,Rq+Rk)转FP32→sum(K²)/Rk→rsqrt(+eps)→乘kw→storek；读PE[Rq+Rk,H)→同dtype直接store。输出分别rowstride Rq/Rk/Dr。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 每token逻辑访问/资源 |
|---|---|
| 输入Z/输出三段 | 各Hd B，d为输入dtype字节宽 |
| Q/K FP32值/平方/affine | Rq与Rk lanes；每个对应逻辑张量4Rq或4Rk B，非物理同时占用证明 |
| qw/kw | Rq*dqw + Rk*dkw B读取，每token重复 |
| bias | 0 + 0 B读取；禁用分支不解引用其指针 |
| 统计 | Q/K各mean-square、rstd标量，逻辑FP32 |
| workspace/TQue/TBuf/物理UB | 无显式请求，N/A；compiler分配外部 |

##### 分层内存布局

`GM Z[N,H] + affine vectors → Q FP32 SSA/rowstat → Qout[N,Rq]；K FP32 SSA/rowstat → Kout[N,Rk]；PE SSA → PEout[N,Dr]`。分支源码顺序不能直接证明compiler一定复用Q/K物理buffer或固定峰值。

##### 字节账与复用顺序

一次调用逻辑GM总量 `N*(2Hd+Rq*dqw+Rk*dkw)` B；不假设weight缓存或物理transaction。无workspace/跨kernel交接；weight/bias只读，输出新分配，异步存活与跨流消费由Torch/Triton管理。unsqueeze仅输出view、不再DMA。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 已证边界 |
|---|---|
| program映射 | p一token，三输出行不交叠，无跨核共享写/atomic |
| 内部顺序 | SSA依赖，未显式物理barrier；Q/K无相互数值依赖 |
| rank尾 | arange终点直接Rq/Rk/Dr，mask是<同终点，没有向上补齐；非二次幂需具体Triton合同 |
| affine | 输入先FP32，均方/rsqrt/affine FP32路径，最终store转输入dtype；weight/bias可异dtype |
| PE | 同输入dtype直接复制，不归一化、不旋转；有限域内不添加舍入步骤 |
| 偏置 | Q 不读取，K 不读取；不是两者成对开关 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| Q路径 | [Q和独立bias](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/fused_split_qk_norm.py#L33-L50) |
| K路径 | [K和独立bias](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/fused_split_qk_norm.py#L55-L74) |
| PE路径 | [copy](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/fused_split_qk_norm.py#L79-L91) |
| flags | [launch尾参](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/fused_split_qk_norm.py#L127-L143) |


### Route R-002：Q_HAS_BIAS=true，K_HAS_BIAS=false

#### 适用条件

##### 选择证据

N>0；launcher以`hasattr(norm,"bias") and norm.bias is not None`分别形成constexpr。本特化Q偏置启用、K偏置关闭；无shape排序或autotune。Rq/Rk/Dr正但validator未检查二次幂，实际arange准入须匹配工具链。

#### Device 数据流

##### 函数级调用链

`fused_split_qk_norm→validate_split_qk_norm→kernel→Q平方和/rsqrt/affine→K平方和/rsqrt/affine→PE load/store`；validator递归到positive_int/epsilon/floating_tensor/vector，均为Host元信息。Device仅这一Kernel，无attention/RoPE算子。

##### 源码等价伪码

token p：输入base=pH；读Q[0,Rq)转FP32→sum(Q²)/Rq→rsqrt(+eps)→乘qw→加qb→storeq；读K[Rq,Rq+Rk)转FP32→sum(K²)/Rk→rsqrt(+eps)→乘kw→storek；读PE[Rq+Rk,H)→同dtype直接store。输出分别rowstride Rq/Rk/Dr。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 每token逻辑访问/资源 |
|---|---|
| 输入Z/输出三段 | 各Hd B，d为输入dtype字节宽 |
| Q/K FP32值/平方/affine | Rq与Rk lanes；每个对应逻辑张量4Rq或4Rk B，非物理同时占用证明 |
| qw/kw | Rq*dqw + Rk*dkw B读取，每token重复 |
| bias | Rq*dqb + 0 B读取；禁用分支不解引用其指针 |
| 统计 | Q/K各mean-square、rstd标量，逻辑FP32 |
| workspace/TQue/TBuf/物理UB | 无显式请求，N/A；compiler分配外部 |

##### 分层内存布局

`GM Z[N,H] + affine vectors → Q FP32 SSA/rowstat → Qout[N,Rq]；K FP32 SSA/rowstat → Kout[N,Rk]；PE SSA → PEout[N,Dr]`。分支源码顺序不能直接证明compiler一定复用Q/K物理buffer或固定峰值。

##### 字节账与复用顺序

一次调用逻辑GM总量 `N*(2Hd+Rq*dqw+Rk*dkw+Rq*dqb)` B；不假设weight缓存或物理transaction。无workspace/跨kernel交接；weight/bias只读，输出新分配，异步存活与跨流消费由Torch/Triton管理。unsqueeze仅输出view、不再DMA。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 已证边界 |
|---|---|
| program映射 | p一token，三输出行不交叠，无跨核共享写/atomic |
| 内部顺序 | SSA依赖，未显式物理barrier；Q/K无相互数值依赖 |
| rank尾 | arange终点直接Rq/Rk/Dr，mask是<同终点，没有向上补齐；非二次幂需具体Triton合同 |
| affine | 输入先FP32，均方/rsqrt/affine FP32路径，最终store转输入dtype；weight/bias可异dtype |
| PE | 同输入dtype直接复制，不归一化、不旋转；有限域内不添加舍入步骤 |
| 偏置 | Q 读取/加，K 不读取；不是两者成对开关 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| Q路径 | [Q和独立bias](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/fused_split_qk_norm.py#L33-L50) |
| K路径 | [K和独立bias](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/fused_split_qk_norm.py#L55-L74) |
| PE路径 | [copy](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/fused_split_qk_norm.py#L79-L91) |
| flags | [launch尾参](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/fused_split_qk_norm.py#L127-L143) |


### Route R-003：Q_HAS_BIAS=false，K_HAS_BIAS=true

#### 适用条件

##### 选择证据

N>0；launcher以`hasattr(norm,"bias") and norm.bias is not None`分别形成constexpr。本特化Q偏置关闭、K偏置启用；无shape排序或autotune。Rq/Rk/Dr正但validator未检查二次幂，实际arange准入须匹配工具链。

#### Device 数据流

##### 函数级调用链

`fused_split_qk_norm→validate_split_qk_norm→kernel→Q平方和/rsqrt/affine→K平方和/rsqrt/affine→PE load/store`；validator递归到positive_int/epsilon/floating_tensor/vector，均为Host元信息。Device仅这一Kernel，无attention/RoPE算子。

##### 源码等价伪码

token p：输入base=pH；读Q[0,Rq)转FP32→sum(Q²)/Rq→rsqrt(+eps)→乘qw→storeq；读K[Rq,Rq+Rk)转FP32→sum(K²)/Rk→rsqrt(+eps)→乘kw→加kb→storek；读PE[Rq+Rk,H)→同dtype直接store。输出分别rowstride Rq/Rk/Dr。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 每token逻辑访问/资源 |
|---|---|
| 输入Z/输出三段 | 各Hd B，d为输入dtype字节宽 |
| Q/K FP32值/平方/affine | Rq与Rk lanes；每个对应逻辑张量4Rq或4Rk B，非物理同时占用证明 |
| qw/kw | Rq*dqw + Rk*dkw B读取，每token重复 |
| bias | 0 + Rk*dkb B读取；禁用分支不解引用其指针 |
| 统计 | Q/K各mean-square、rstd标量，逻辑FP32 |
| workspace/TQue/TBuf/物理UB | 无显式请求，N/A；compiler分配外部 |

##### 分层内存布局

`GM Z[N,H] + affine vectors → Q FP32 SSA/rowstat → Qout[N,Rq]；K FP32 SSA/rowstat → Kout[N,Rk]；PE SSA → PEout[N,Dr]`。分支源码顺序不能直接证明compiler一定复用Q/K物理buffer或固定峰值。

##### 字节账与复用顺序

一次调用逻辑GM总量 `N*(2Hd+Rq*dqw+Rk*dkw+Rk*dkb)` B；不假设weight缓存或物理transaction。无workspace/跨kernel交接；weight/bias只读，输出新分配，异步存活与跨流消费由Torch/Triton管理。unsqueeze仅输出view、不再DMA。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 已证边界 |
|---|---|
| program映射 | p一token，三输出行不交叠，无跨核共享写/atomic |
| 内部顺序 | SSA依赖，未显式物理barrier；Q/K无相互数值依赖 |
| rank尾 | arange终点直接Rq/Rk/Dr，mask是<同终点，没有向上补齐；非二次幂需具体Triton合同 |
| affine | 输入先FP32，均方/rsqrt/affine FP32路径，最终store转输入dtype；weight/bias可异dtype |
| PE | 同输入dtype直接复制，不归一化、不旋转；有限域内不添加舍入步骤 |
| 偏置 | Q 不读取，K 读取/加；不是两者成对开关 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| Q路径 | [Q和独立bias](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/fused_split_qk_norm.py#L33-L50) |
| K路径 | [K和独立bias](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/fused_split_qk_norm.py#L55-L74) |
| PE路径 | [copy](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/fused_split_qk_norm.py#L79-L91) |
| flags | [launch尾参](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/fused_split_qk_norm.py#L127-L143) |


### Route R-004：Q_HAS_BIAS=true，K_HAS_BIAS=true

#### 适用条件

##### 选择证据

N>0；launcher以`hasattr(norm,"bias") and norm.bias is not None`分别形成constexpr。本特化Q偏置启用、K偏置启用；无shape排序或autotune。Rq/Rk/Dr正但validator未检查二次幂，实际arange准入须匹配工具链。

#### Device 数据流

##### 函数级调用链

`fused_split_qk_norm→validate_split_qk_norm→kernel→Q平方和/rsqrt/affine→K平方和/rsqrt/affine→PE load/store`；validator递归到positive_int/epsilon/floating_tensor/vector，均为Host元信息。Device仅这一Kernel，无attention/RoPE算子。

##### 源码等价伪码

token p：输入base=pH；读Q[0,Rq)转FP32→sum(Q²)/Rq→rsqrt(+eps)→乘qw→加qb→storeq；读K[Rq,Rq+Rk)转FP32→sum(K²)/Rk→rsqrt(+eps)→乘kw→加kb→storek；读PE[Rq+Rk,H)→同dtype直接store。输出分别rowstride Rq/Rk/Dr。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 每token逻辑访问/资源 |
|---|---|
| 输入Z/输出三段 | 各Hd B，d为输入dtype字节宽 |
| Q/K FP32值/平方/affine | Rq与Rk lanes；每个对应逻辑张量4Rq或4Rk B，非物理同时占用证明 |
| qw/kw | Rq*dqw + Rk*dkw B读取，每token重复 |
| bias | Rq*dqb + Rk*dkb B读取；禁用分支不解引用其指针 |
| 统计 | Q/K各mean-square、rstd标量，逻辑FP32 |
| workspace/TQue/TBuf/物理UB | 无显式请求，N/A；compiler分配外部 |

##### 分层内存布局

`GM Z[N,H] + affine vectors → Q FP32 SSA/rowstat → Qout[N,Rq]；K FP32 SSA/rowstat → Kout[N,Rk]；PE SSA → PEout[N,Dr]`。分支源码顺序不能直接证明compiler一定复用Q/K物理buffer或固定峰值。

##### 字节账与复用顺序

一次调用逻辑GM总量 `N*(2Hd+Rq*dqw+Rk*dkw+Rq*dqb+Rk*dkb)` B；不假设weight缓存或物理transaction。无workspace/跨kernel交接；weight/bias只读，输出新分配，异步存活与跨流消费由Torch/Triton管理。unsqueeze仅输出view、不再DMA。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 已证边界 |
|---|---|
| program映射 | p一token，三输出行不交叠，无跨核共享写/atomic |
| 内部顺序 | SSA依赖，未显式物理barrier；Q/K无相互数值依赖 |
| rank尾 | arange终点直接Rq/Rk/Dr，mask是<同终点，没有向上补齐；非二次幂需具体Triton合同 |
| affine | 输入先FP32，均方/rsqrt/affine FP32路径，最终store转输入dtype；weight/bias可异dtype |
| PE | 同输入dtype直接复制，不归一化、不旋转；有限域内不添加舍入步骤 |
| 偏置 | Q 读取/加，K 读取/加；不是两者成对开关 |

#### 关键实现

##### 符号证据表

| 符号 | 证据 |
|---|---|
| Q路径 | [Q和独立bias](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/fused_split_qk_norm.py#L33-L50) |
| K路径 | [K和独立bias](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/fused_split_qk_norm.py#L55-L74) |
| PE路径 | [copy](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/fused_split_qk_norm.py#L79-L91) |
| flags | [launch尾参](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/fused_split_qk_norm.py#L127-L143) |

## 算子特定优化

### Trick T-001：同任务内拆Q并完成统计与affine

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/fused_split_qk_norm.py#L33-L50)：

```python
    q_offs = tl.arange(0, q_lora_rank)
    q = tl.load(
        fused_ptr + base + q_offs,
        mask=q_offs < q_lora_rank,
        other=0.0,
    ).to(tl.float32)

    q_var = tl.sum(q * q, axis=0) / q_lora_rank
    q_rstd = tl.rsqrt(q_var + eps)

    qw = tl.load(q_rms_w_ptr + q_offs, mask=q_offs < q_lora_rank)
    q = q * q_rstd * qw

    if Q_HAS_BIAS:
        qb = tl.load(q_rms_b_ptr + q_offs, mask=q_offs < q_lora_rank)
        q += qb

    tl.store(q_lora_ptr + pid * q_lora_rank + q_offs, q, mask=q_offs < q_lora_rank)
```

#### 机制与设计原因

不用GM物化拆分输入或均方中间值，Q先FP32统计再affine；K保持独立同构路径。源代码减少中间GM输出，未测性能提升。

#### 迁移边界

分段统计长度、权重地址、bias flags独立，Rq/Rk不同不能复用同统计。低精度输出仍有最终store舍入。

#### 错误做法

调用layernorm对象forward导致改变epsilon/语义，或将两bias强制共同开关。

### Trick T-002：旋转K保持原值复制

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/fused_split_qk_norm.py#L79-L91)：

```python
    pe_offs = tl.arange(0, qk_rope_dim)
    pe_base = k_base + kv_lora_rank

    k_pe = tl.load(
        fused_ptr + pe_base + pe_offs,
        mask=pe_offs < qk_rope_dim,
    )

    tl.store(
        k_pe_ptr + pid * qk_rope_dim + pe_offs,
        k_pe,
        mask=pe_offs < qk_rope_dim,
    )
```

#### 机制与设计原因

PE独立从第三段读取并按同dtype写出，避免把旋转子空间错误纳入K统计；此函数名字含QK而不实际执行旋转。

#### 迁移边界

段起点必须为Rq+Rk；Dr按实际工具链arange合同可编译；无推广到RoPE表/旋转语义。

#### 错误做法

PE做RMSNorm、套用K权重，或把unsqueeze当实际搬运。

## 模板与实现对比

四bias特化共享一个body但读集合与GM字节不同；N0是纯Host路线。公共任意正整数元信息与compiler arange准入边界分开，未自行修源。三返回均同输入dtype，weight/bias可以不同浮点dtype；不借torch_native宣称Triton逐位等价。

## 平台差异

本卡A2/A3归属arch22；公开arch22/35支持但同时声明实际硬件执行待验证，README/architectures映射A2/A3、950。源代码无硬件分支；CANN9.1.0 CI norm/a3/950配置非本次运行，亦非A2实测。Triton arange扩展与物理资源须匹配实际编译器。

## 限制与失败边界

非二次幂rank/Dr准入、assert可关闭、资源与JIT地址整数域均须另核对；不把metadata合法当运行安全。有限输入域按FP32计算仍可能溢出，非有限值无额外修复。无编译、运行、测试/校验、性能和物理UB分配结果，draft保留条件而不推荐无条件安全复用。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开合同](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/fused_split_qk_norm.md) | `fused_split_qk_norm` | 三段布局/affine/平台声明待真机 |
| [Direct及Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/fused_split_qk_norm.py) | `fused_split_qk_norm[_kernel]` | 完整149行/空输入/四bias特化 |
| [校验依赖](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/norm_utils.py) | `validate_split_qk_norm/positive_int/epsilon/floating_tensor/vector` | 全部可达元信息assert |
| [公开门面](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/norm/fused_split_qk_norm.py) | `_triton_impl` | 对象属性转发，不调用forward |
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

冻结117/legacy候选公开API与优化聚合已完整读；API链接复用，聚合非同级Operator，不复用无源码性能数字。只新增唯一Direct两平台卡，不并入QKV/RoPE/attention任务，单repo一primary、无verified。
