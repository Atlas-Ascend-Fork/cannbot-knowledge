---
type: Operator
title: "AttnResidualMix 950 Direct Invoke 算子知识"
description: "闭合残差快照评分softmax与原值两遍混合，记录空输入别名、动态bank前缀、权重跨token复用和FP32及JIT整数资源边界。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/hyper_conn/attn_res_mix_fused.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/hyper_conn/attn_residual_mix.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/hyper_conn/attn_residual_mix.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/hyper_conn/__init__.py
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
created_at: "2026-11-09T09:36:51Z"
updated_at: "2026-11-09T09:36:51Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# AttnResidualMix 950 Direct Invoke 算子知识

## 算子速览

`sgl_kernel_npu.implementation.triton.hyper_conn.attn_residual_mix.attn_res_mix_fused` 对有效bank快照与prefix分别RMS归一化后点积打分、softmax，再按概率加权原始行值。末尾没有RMSNorm、残差相加或bank写回；不是attention QK矩阵乘。完整Host校验/空别名/单持久化Kernel两类B特化闭合。

draft保留FP32中间溢出、缺失大尺寸调度/地址guard、devicecache及compiler物理分配边界。已有[公开API](../../../../apis/sgl_kernel_npu/sgl_attn_residual_mix.md)全文读并复用。

## 接口与语义

### 计算语义

B=num_valid_blocks；v_r=bank[r]当r<B，否则prefix。`s_r=Σ_h(v_r,h*rsqrt(Σ_h v_r,h²/H+eps)*cw_h)`；`p=softmax(s)`；`y_h=Σ_{r=0}^B p_r*v_r,h`。评分归一化值不作为混合值，cw由调用方预先合并权重，函数只消费向量。FP32实现可近似/融合，不能声明逐位Torch等价。

### 输入、输出与属性

| 项 | 校验/合同 |
|---|---|
| prefix_sum | strided FP16/BF16/FP32二维[N,H]，H>0 |
| bank | strided同device三维[N,C,H]，独立浮点dtype，0≤B≤C |
| combined_weight | strided同device一维[H]，独立浮点dtype |
| B | Python int排除bool，越界ValueError |
| eps | Python int/float排除bool、有限正 |
| N0输出 | 返回prefix本身，别名；基本校验后、NPU/stride校验前返回 |
| N>0输出 | empty_like(prefix)，新存储，实际output行stride传Kernel；所有输入只读 |

### 入口与版本

Direct签名(prefix_sum,bank,num_valid_blocks,combined_weight,variance_epsilon)。冻结短路径加包名前缀为精确符号，publicauto/triton仅转发、reference外部。固定SGLcommit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`；CANN9.1.0为README/CI配置而非本次运行，未固定完整Triton二进制。

## Host/Launcher 执行流程

### 参数校验与前处理

validate_mix_inputs逐Tensor/type/layout/ndim/dtype→shapeH及匹配→同device→B类型/范围→eps类型有限正。N0直接returnprefix，允许满足基础元信息的CPU/hidden非unitstride空view。非空才assertNPU、prefix/bank末stride1及cwstride1；token/bank行stride可任意合法视图。基本assert可被Python-O关闭，B范围ValueError仍在。

### 参数、Workspace 与生命周期

非空output=empty_like(prefix)，helper取P，BH=nextpow2(H)、NB=nextpow2(B+1)，multibuffer=True传launch。无score矩阵GM分配、无workspace/POD/ACLNN；物理UB/寄存器与multibuffer缓冲数未由编译产物证实。helper无参cache取current_device、双核数assert，未按prefix.device设guard。输入/输出异步生命周期和跨流依赖归框架，未显式wait/stream。

### 启动图与失败传播

import→基础校验→N0别名返回或非空NPU/stride校验→empty_like→helper→单Kernel→返回。无输入contiguouscopy（使用真实rowstrides）、无fallback或第二Kernel。异常直接传播；包原生库加载为导入前提，不是图内native attention算子。

## Route 与参数设计

### 分核与资源计算

非空q=ceil(N/P)，program p负责[pq,min((p+1)q,N))，空段earlyreturn；非空program数A=ceil(N/q)。cw在earlyreturn后、token循环前load一次，本program复用；两次row循环每token读取bank有效B行+prefix各一次。BH/ NB二次幂padding，全H归约并除真实H。

### Route 选择

| 路线 | 条件 | 行为 |
|---|---|---|
| H-000 | N0 | 校验基础元信息后别名返回，无Kernel |
| R-001 | N>0,B0 | 仍评分/softmax/第二遍读prefix，新输出 |
| R-002 | N>0,B>0 | bank有效前缀+prefix评分/混合 |

### 模板/实现执行矩阵

prefix/bank/cw三浮点dtype独立3³实例，load全转FP32，store回prefixdtype。N/B被do_not_specialize保持runtime，但NB由B+1向上二次幂，跨NB变化仍为不同constexpr实例，不宣称任意B同编译物。无autotune/tl.dot/Cube/AIC/MIX节点，multibuffer=True不能推物理缓冲深度。

### 隐藏性能 Guard

源码无N/row调度int32容量guard，token*stride亦未显式to(int64)，不同于SiTU实现；所有尺寸/地址在实际JIT类型可表示域是必要前提，不能宣称超大N安全。BH/NB完整逻辑张量随H/B增长，无物理资源查询。有限输入仍可FP32score溢出，softmax减max不能修复inf-inf；B0也不做恒等短路。

### POD/ABI

| 字段 | 类型/消费 |
|---|---|
| prefix_ptr/bank_ptr/cw_ptr/out_ptr | runtimeTensor→读/读/读/写 |
| N/B | runtime/do_not_specialize→token分核/row循环 |
| stride_pm | runtime元素stride→prefixrow |
| stride_bm/stride_bb | runtime元素stride→banktoken/快照 |
| stride_om | runtime元素stride→outputrow |
| H/BLOCK_H | constexpr真实H/补齐BH→mask/归约/步长 |
| EPS | constexpr→评分rms |
| NUM_CORES | constexprP→连续分核 |
| NB | constexprnextpow2(B+1)→scores/arange |
| multibuffer/grid | True/(P,) |

无自定义序列化POD/字段偏移；JIT位宽/指针ABI及runtime标量specialization归compiler，不编造。

### Route 源码闭包

完整191行实现包含validator及唯一Device，helper和公开适配已读。根setup→stage_runtime完整Python包→build_wheel/setup_refactor，hyper_conn/backendinit无Device。primitive max/exp/reduction及physicalallocation是外部框架边界；不以Torchreference填补实际路径。

## Kernel 实现

### 公共执行流程

earlyreturn后加载cw，逐token评分→score向量softmax→重读原值混合→store。bank后缀不读，不写快照。空输入无Device资源。

### Route R-001：B=0仅prefix

#### 适用条件

##### 选择证据

N>0、B=0。同一Kernel的runtime B控制两次row循环内row<B分支；无autotune或另一个数学入口。NB=next_power_of_2(B+1)。

#### Device 数据流

##### 函数级调用链

`attn_res_mix_fused→validate_mix_inputs→helper→_attn_res_mix_fused_kernel→load/sum/rsqrt/exp/where/store`，全部自有函数已读。

##### 源码等价伪码

program按q=ceil(N/P)分token连续段，空段返回；先loadcw一次转FP32。每token：scores[NB]=-inf；row0..B分别读仅prefix，zero-pad H→BH，算rsqrt(sum(v²)/H+eps)、score=sum(v*rstd*cw)，用row_offsets==row写scores；softmax(scores-max)；output[BH]=0，第二遍重读同原始值，prob=sum(where(row_offsets==row,probabilities,0))，output+=prob*v；Hmask写出prefixdtype。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑元素/流量 |
|---|---|
| cw/value/output | 各BH FP32逻辑，单张量4BH B；物理并存/复用未知 |
| scores/exp/probabilities | 各NB FP32逻辑4NB B |
| bank | 不读取任何bank值 |
| prefix | 每token两遍H*dp B |
| cw | 每active program读H*dw B，跨本program多个token复用 |
| output | 每tokenH*dp B写；workspace/GM中间统计无 |

##### 分层内存布局

`GMbank/prefix→FP32value[BH]→score[NB]→softmax[NB]→重新读GM原值→FP32out[BH]→GMout`。scores不物化GM；一Kernel不代表只读原值一次。

##### 字节账与复用顺序

令q=ceil(N/P)、A=ceil(N/q)（N>0、P>0合法整数域），实际A个非空program在earlyreturn后loadcw。总逻辑流量 `NH*( 3dp)+A*H*dw` B，其中仅prefix两遍读取及output写；无统计GM输出/调用方workspace。outputempty_like可能按输入layout保留stride，寻址使用真实stride_om；GMspan为(N-1)*stride_om+H元素，不强称所有nonempty输出packed。物理UB/register/spill属于compiler，输出/三输入异步存活归框架。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| token间 | q分割无共享写，原始输入只读，无atomic/barrier |
| hidden尾 | BH向上二次幂、Hmask load other0/store；均方除真实H |
| scores尾 | NB-(B+1)项保持-inf；有限score_max时exp尾0，不参与概率 |
| bank后缀 | B0没有bankload，可含NaN |
| 数值 | 全部输入load转FP32，softmax减max稳定化，但有限输入仍可导致中间overflow/Inf；需score与exp分母可定义 |
| B0值 | 理想/无溢出FP32路径softmax单有效项为1，值等于prefix；仍走评分/两遍读，不跳过数值计算 |
| 同步 | 两遍顺序由SSA/循环依赖交给compiler，未指定物理事件/流wait |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| score/softmax | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/hyper_conn/attn_residual_mix.py#L91-L112) |
| original-value混合 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/hyper_conn/attn_residual_mix.py#L114-L135) |
| tile/grid | [launch](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/hyper_conn/attn_residual_mix.py#L171-L190) |


### Route R-002：B>0有效bank前缀及prefix

#### 适用条件

##### 选择证据

N>0、0<B≤bank容量。同一Kernel的runtime B控制两次row循环内row<B分支；无autotune或另一个数学入口。NB=next_power_of_2(B+1)。

#### Device 数据流

##### 函数级调用链

`attn_res_mix_fused→validate_mix_inputs→helper→_attn_res_mix_fused_kernel→load/sum/rsqrt/exp/where/store`，全部自有函数已读。

##### 源码等价伪码

program按q=ceil(N/P)分token连续段，空段返回；先loadcw一次转FP32。每token：scores[NB]=-inf；row0..B分别读bank前B行，最后prefix，zero-pad H→BH，算rsqrt(sum(v²)/H+eps)、score=sum(v*rstd*cw)，用row_offsets==row写scores；softmax(scores-max)；output[BH]=0，第二遍重读同原始值，prob=sum(where(row_offsets==row,probabilities,0))，output+=prob*v；Hmask写出prefixdtype。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑元素/流量 |
|---|---|
| cw/value/output | 各BH FP32逻辑，单张量4BH B；物理并存/复用未知 |
| scores/exp/probabilities | 各NB FP32逻辑4NB B |
| bank | 每token两遍B*H*db B |
| prefix | 每token两遍H*dp B |
| cw | 每active program读H*dw B，跨本program多个token复用 |
| output | 每tokenH*dp B写；workspace/GM中间统计无 |

##### 分层内存布局

`GMbank/prefix→FP32value[BH]→score[NB]→softmax[NB]→重新读GM原值→FP32out[BH]→GMout`。scores不物化GM；一Kernel不代表只读原值一次。

##### 字节账与复用顺序

令q=ceil(N/P)、A=ceil(N/q)（N>0、P>0合法整数域），实际A个非空program在earlyreturn后loadcw。总逻辑流量 `NH*(2B*db+3dp)+A*H*dw` B，其中bank/prefix分别两遍读取，outputdp写；无统计GM输出/调用方workspace。outputempty_like可能按输入layout保留stride，寻址使用真实stride_om；GMspan为(N-1)*stride_om+H元素，不强称所有nonempty输出packed。物理UB/register/spill属于compiler，输出/三输入异步存活归框架。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| token间 | q分割无共享写，原始输入只读，无atomic/barrier |
| hidden尾 | BH向上二次幂、Hmask load other0/store；均方除真实H |
| scores尾 | NB-(B+1)项保持-inf；有限score_max时exp尾0，不参与概率 |
| bank后缀 | 只读row<B，未使用容量后缀不读，可含NaN |
| 数值 | 全部输入load转FP32，softmax减max稳定化，但有限输入仍可导致中间overflow/Inf；需score与exp分母可定义 |
| B0值 | 非本特化 |
| 同步 | 两遍顺序由SSA/循环依赖交给compiler，未指定物理事件/流wait |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| score/softmax | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/hyper_conn/attn_residual_mix.py#L91-L112) |
| original-value混合 | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/hyper_conn/attn_residual_mix.py#L114-L135) |
| tile/grid | [launch](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/hyper_conn/attn_residual_mix.py#L171-L190) |

## 算子特定优化

### Trick T-001：融合评分softmax混合，统计不物化GM

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/hyper_conn/attn_residual_mix.py#L106-L114)：

```python
            inverse_rms = tl.rsqrt(tl.sum(value * value) / H + EPS)
            score = tl.sum(value * inverse_rms * combined_weight)
            scores = tl.where(row_offsets == row, score, scores)

        scores_max = tl.max(scores)
        exp_scores = tl.exp(scores - scores_max)
        probabilities = exp_scores / tl.sum(exp_scores)

        output = tl.zeros([BLOCK_H], dtype=tl.float32)
```

#### 机制与设计原因

scores[NB]保留任务内SSA，softmax后同Kernel第二遍消费原值，避免scoreGM中间矩阵和第二Kernel。代价是原值两遍读取，不是单遍数据流或已测性能收益。

#### 迁移边界

scores无效行保-inf、有效score有限，NB≥B+1；原始值参与混合，不能复用已归一化值替代。

#### 错误做法

额外输出RMSNorm/残差加法改变数学；宣称融合使bank只读一次也与源码相反。

### Trick T-002：早退后加载共享评分权重并复用token循环

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/hyper_conn/attn_residual_mix.py#L77-L91)：

```python
    block_size = (N - 1) // NUM_CORES + 1
    pid = tl.program_id(0)
    token_start = pid * block_size
    if token_start >= N:
        return
    token_end = tl.minimum(token_start + block_size, N)

    hidden_offsets = tl.arange(0, BLOCK_H)
    hidden_mask = hidden_offsets < H
    row_offsets = tl.arange(0, NB)
    combined_weight = tl.load(cw_ptr + hidden_offsets, mask=hidden_mask, other=0.0).to(
        tl.float32
    )

    for token in range(token_start, token_end):
```

#### 机制与设计原因

空program先返回，活跃program只loadcw一次并复用所分token，逻辑cw读A*H*dw而非N*H*dw。hiddenpadding显式0、真实H作均方分母。

#### 迁移边界

P与grid一致、分核整数可表示，cw连续unitstride；程序分组变化会改变权重读取次数。

#### 错误做法

用补齐BH代替H做均方除数，或读取未使用bank容量后缀。

## 模板与实现对比

H-000别名不同于非空新输出；B0仍走数值评分，理想恒等不代表任意有限大值下FP32永不溢出。B动态但NB specialization，不能只看do_not_specialize就宣称所有B复用同编译物。原值第二遍、实际输出stride和无GM统计均已闭合。

## 平台差异

本卡950归属arch35；公开arch22/35声明支持，README/architectures映射A2/A3及950。自有body无硬件分支，CANN9.1.0 CI配置非本次运行/实际compiler或A2实测；物理资源随工具链变化。

## 限制与失败边界

基本assert可关闭；devicecache、JIT尺寸/stride整数域、BH/NB资源未guard。输入有限不足以保证FP32中间不溢出，复用需保证评分/softmax可定义；未用bank后缀不读。无编译、测试/校验、真机或性能结果；draft不作为无条件安全模板。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开合同](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/hyper_conn/attn_res_mix_fused.md) | `attn_res_mix_fused` | normalize评分/原值混合/空别名/平台 |
| [完整Host/Device](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/hyper_conn/attn_residual_mix.py) | `attn_res_mix_fused/validate_mix_inputs/_attn_res_mix_fused_kernel` | 191行/尾部/两遍load |
| [公开适配](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/hyper_conn/attn_residual_mix.py) | `_triton_impl` | auto/triton转发 |
| [hyper_conn包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/hyper_conn/__init__.py) | `module init` | 无Device |
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

冻结117/legacy同主题API已完整读，链接复用；只新增唯一attention-residual混合Direct两平台实现卡，不并入QKattention/最终norm等其它数学。全部同repo固定source唯一primary，无verified。
