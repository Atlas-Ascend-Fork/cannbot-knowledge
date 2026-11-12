---
type: Operator
title: "MarkovSampleStepLocal A2/A3 Direct Invoke 算子知识"
description: "闭合无gather的本地Markov采样24种partial特化及finish，记录step舍入、Philox/外部noise所有权、keptlogits、索引bits与完整GM流量。"
tags: [task.implementation, task.lookup, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/sample/markov_sample_step_triton.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/sample/markov_sample.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/__init__.py
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
created_at: "2026-11-09T10:17:01Z"
updated_at: "2026-11-10T07:06:47Z"
platforms: [a2, a3]
cann_versions: ["9.1.0"]
---

# MarkovSampleStepLocal A2/A3 Direct Invoke 算子知识

## 算子速览

精确 `sgl_kernel_npu.implementation.triton.sample.markov_sample.markov_sample_step_triton`，独立冻结 `gather=None,gather_logits=None`；logits_out可None或合法独立预分配（不alias输入）。bias加base后按stepdtype舍入，温度0argmax、非零用内部Philox或给定指数noise选择，最后返回全局tokenID。全部自有Host、三JIThelper、partial与finish两节点闭合，无dot/Cube，VV。

draft保留无完整device/value/整数资源guard和随机流所有权；原callbacks全域核心缺源仍defer，不以local卡替代分布式实现。全文读过的[API](../../../../apis/sgl_kernel_npu/sgl_markov_sample_step.md)链接复用。

## 接口与语义

### 计算语义

B行、base宽P>0、bias有效宽0≤W≤P。`value=round_step(FP32(base)+FP32(bias))`（bias只W内），score=value若温度0，否则value/temp-log(exp_noise)。选有效W内NaN优先、最大值并列最小globalidx=vocab_start+i；无有效列贡献/返回2147483647。logits_out存在时写所有P列的舍入base+bias，不只W，padding保留无bias的舍入base，但选取仍maskW。

内部随机协议：quad=(part*BLOCK+vocab_start)//4+tl.arange(0,BLOCK//4)，每个四元组有独立块内计数器；Philox counter=(uint32quad,uint32row,uint32step,uint32(offset&0xffffffff))，KEY参数与10rounds；四word按w0,w1,w2,w3次序交错，转int64再&0xffffffff避免符号扩展；u=(FP32(bits)+.5)*2^-32，expnoise由补偿-log(1-u)函数生成。未宣称与任意外部库随机序列逐位相同，primitivePhilox/lowering仍需实际工具链。提供externalnoise时不生成噪声，key/step忽略，offset仍是必填/被_check。

### 输入、输出与属性

| 项 | 合同/真实检查 |
|---|---|
| base/bias | 同NPU浮点[B,P]/[B,W]，B/P正、W可0，列stride1；实际_check检查ndim/batch/宽关系/stride但不完整dtype/device |
| temperatures | 连续FP32[B]；推荐非负有限，0贪心；SAMPLEfalse需调用方保证全0 |
| key/offset/step | key/step Pythonint；offset同device单元素int64，Device只读取低32bit且不更新 |
| step_dtype | FP32/BF16/FP16，由_ROUND_CODE0/1/2检查 |
| vocab_start | 全局分片起点，必须4整除；globalidx须0≤id<2147483647，后者无完整guard |
| callbacks | 两者均None冻结；原callbackcore实现未固定，不在此图 |
| logits_out | None或独立[B,P]同device stepdtype、末stride1，原地写此buffer但不alias任何输入 |
| exp_noise | None或同deviceFP32[B,P]、列stride1、正噪声；检查shape/device/dtype/stride，正值不读回验证 |
| return | 新int64[B]tokens，同device，输入/noise/offset不修改，keptout按需修改 |

### 入口与版本

全keyword-only签名为(base_logits,bias,temperatures,key,offset,step,step_dtype,vocab_start=0,gather=None,gather_logits=None,logits_out=None,has_sampled_rows=None,exp_noise=None)，本predicate严格不调用回调。auto/triton仅转发，torch_native外部reference不并入实现。SGLcommit `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`，CANN9.1.0为README/CI配置非本次运行，完整Tritonbinary未固定。

## Host/Launcher 执行流程

### 参数校验与前处理

_check检查二维/批量/有效宽/列stride、temperature shape/dtype/stride、offsetdtype/numel、stepdtype、vocab4对齐、keptoutshape/type/stride；externalnoise再检查shape/device/type/stride。没有完整同NPU/浮点/温度值/noise正值/globalidx上限guard。B0不属公开域且没有快返，不能虚构空路线。

_launch_partial：BLOCK=1024若noiseNone，否则min(4096,nextpow2P)，Qp=ceil(P/BLOCK)>0，partialempty[B,Qp,2]FP32，grid1=min(BQp,Pcores)，num_warps1。返回view[B,2Qp]，不会再分配copy。local收集直接gathered=partial；tokensempty[B]int64，finishgrid=min(B,Pcores)、F=nextpow2Qp、WORLD1、num_warps1。

### 参数、Workspace 与生命周期

真实内部GMscratch8B*Qp B，tokens8B B；keptout为调用方独立缓冲BP*dstep，不由此函数分配，noise为输入无需生成GM。没有请求方workspace/POD/ACLNN，不能把内部partial写成零scratch。partial/view局部引用存活至finishlaunch，实际异步回收由frameworkallocator，输入/offset/noise/keptout须按框架流规则存活。

helper无参cache取current_device、AIC/vectorassert正，无deviceguard，调用方设置/保持同device属性相容。无自有hostwait或stream参数；partial→finish依同次当前框架流顺序。没有随机offset自增或externalnoise刷新，graphreplay的新随机性归调用方。

### 启动图与失败传播

import→_check/可选noisecheck→functools.partial绑定Host参数→partialKernel→直接partialview→finishKernel→return。本域不经过store-onlylocal/gather_logits/第二partial，HAS_BIAS/SELECT恒true；keptout只是同partial的STORE分支。异常直接传播，无fallback。package原生库为导入依赖，不是图内sampling核心。

## Route 与参数设计

### 分核与资源计算

partial按task=row*Qp+part，以grid1 program轮转覆盖BQp任务；每partBLOCK词、真实P读/keptstore、W有效选择。finish按row轮转，F=nextpow2Qp，localworld1归约所有parts。BLOCK来源externalnoise是否存在，即使SAMPLEfalse忽略噪声也仍改变分块。COUNT/SIZE均需实际JIT整数可表示。

### Route 选择

8个STORE×SAMPLE×USE_EXP_NOISE组合，再×ROUND0/1/2共24partial特化；SAMPLEtrue内部runtime每行温度0/非0分支均闭合。R-025finish共享所有24，PARTS=Qp、WORLD1。has_sampled_rowsFalse不是自动从temperature值推断，必须调用者保证。无autotune。

### 模板/实现执行矩阵

| Route | STORE | SAMPLE | EXP_NOISE | ROUND |
|---|---|---|---|---|
| R-001 | false | false | false | 0 |
| R-002 | false | false | false | 1 |
| R-003 | false | false | false | 2 |
| R-004 | false | false | true | 0 |
| R-005 | false | false | true | 1 |
| R-006 | false | false | true | 2 |
| R-007 | false | true | false | 0 |
| R-008 | false | true | false | 1 |
| R-009 | false | true | false | 2 |
| R-010 | false | true | true | 0 |
| R-011 | false | true | true | 1 |
| R-012 | false | true | true | 2 |
| R-013 | true | false | false | 0 |
| R-014 | true | false | false | 1 |
| R-015 | true | false | false | 2 |
| R-016 | true | false | true | 0 |
| R-017 | true | false | true | 1 |
| R-018 | true | false | true | 2 |
| R-019 | true | true | false | 0 |
| R-020 | true | true | false | 1 |
| R-021 | true | true | false | 2 |
| R-022 | true | true | true | 0 |
| R-023 | true | true | true | 1 |
| R-024 | true | true | true | 2 |
| R-025 | — | — | — | shared finish |

base/bias浮点dtype load先FP32，输出kept按stepdtype；原回调全域未知不纳入成功。自有节点无tl.dot/Cube/AIC/MIX，逐节点确认为VV，不按目录推定。

### 隐藏性能 Guard

_NO_INDEX保留int32max；idx.to(float32,bitcast=True)和finishbitcastint32/符号mask要求合法tokenID非负且小于哨兵，Host只检查4对齐未限制范围。Philox counter各项uint32截断，offset高32bit不参与本实现counter；调用方不要误认为传int64即可无限新流。内部u的FP32舍入可到1，helper给expnoiseinf，score可-inf，不无证替换为torch随机primitive。大Qp导致finishF和partialGM增长，资源/整数域无完整guard。

### POD/ABI

| 字段 | 分类/消费 |
|---|---|
| partial B/X/T/OFFSET/L/P/E | runtime指针：bias/base/temp/offset/keptout/partial/noise；inactive指针可占位但flag禁用解引用 |
| BS/XS/LS/ES | runtime元素行stride：bias/base/kept/noise，inactive传0 |
| WIDTH/PADDED/VOCAB_START/PARTS/ROWS | runtimeW/P/vstart/Qp/B→mask/索引/任务（源无constexpr标注，具体specialization由Triton） |
| KEY/STEP | runtime随机参数，externalnoise/greedy分支不消费 |
| BLOCK/ROUND | constexpr上述BLOCK/0–2→arange/舍入helper |
| HAS_BIAS/STORE/SELECT | constexprtrue/可选/true |
| SAMPLE/USE_EXP_NOISE/PHILOX_ROUNDS | constexprhas_sampled_rows!=False/noise存在/10 |
| _select_block value,T,OFFSET,P,E,ES,row,part,i,valid,PARTS,KEY,STEP,VOCAB_START | 调用方SSA/指针/参数→完整helper消费，非额外launchABI |
| _select_block BLOCK/SAMPLE/USE_EXP_NOISE/PHILOX_ROUNDS | constexpr同partial |
| _round_to_step_dtype(value,ROUND) | FP32SSA/constexpr→0直返、1BF16往返、2FP16往返 |
| _negative_log1p_negative(uniform) | FP32SSA→补偿expnoise |
| finish P/OUT/BS | runtimepartial/tokens/B |
| finish PARTS/WORLD/BLOCK | constexprQp/1/F→候选索引/归约 |
| grids/num_warps | min(BQp,cores)/min(B,cores)，均1warp元参数，physical线程解释外部 |

无自定义POD/序列化offset，候选两FP32的逻辑槽8B明确，idx槽是int32位模式不是数值float索引。JIT ABI/未注释标量实际位宽不猜测，bitcast/uint32/int64等显式转换按源列出。

### Route 源码闭包

完整375行所有Host/_check/_launch和3helper/两Kernel已读，publicwrapper完整读。本predicate排除所有callbackcore，keptout仍本地自有STORE。根setup→stage_runtime完整Python包→build_wheel/setup_refactor，sample/backendinit无Device。tl.philox/log/reduction/cast是外部primitive，未生成/安装/执行工具链。

## Kernel 实现

### 公共执行流程

partial：读base+bias→step-round→可选keptout→按温度/噪声选局部候选，FP32槽存最大值与int32索引bits；finish：读所有parts并重复NaN优先/最小索引，int64写tokens。无atomic或跨program共享写。

### Route R-001：STORE=false SAMPLE=false EXTERNAL=false ROUND=0

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_outNone，has_sampled_rowsFalse，合同必须所有温度0，exp_noiseNone，step_dtype=FP32。HAS_BIAS/SELECT恒true，local世界1；BLOCK=1024，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，保持FP32；不写logits。不读温度并固定0，不生成/读取噪声，score=value；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | 无写 |
| temperature | 不读 |
| noise/RNG | OFFSET/KEY/STEP均不Device读取 |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。外部noise/贪心分支不构建Philox临时。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias  +8B*Qp` B。S为实际非零温度行数，本域S0；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND0真实FP32在选取前；kept输出同stepdtype |
| temperature | has_sampled_rowsFalse忽略Tensor值，调用方保证全部0 |
| RNG | 没有RNG消费，即使传expnoise也只影响BLOCK选择 |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |


### Route R-002：STORE=false SAMPLE=false EXTERNAL=false ROUND=1

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_outNone，has_sampled_rowsFalse，合同必须所有温度0，exp_noiseNone，step_dtype=BF16。HAS_BIAS/SELECT恒true，local世界1；BLOCK=1024，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，toBF16再toFP32；不写logits。不读温度并固定0，不生成/读取噪声，score=value；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | 无写 |
| temperature | 不读 |
| noise/RNG | OFFSET/KEY/STEP均不Device读取 |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。外部noise/贪心分支不构建Philox临时。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias  +8B*Qp` B。S为实际非零温度行数，本域S0；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND1真实BF16→FP32在选取前；kept输出同stepdtype |
| temperature | has_sampled_rowsFalse忽略Tensor值，调用方保证全部0 |
| RNG | 没有RNG消费，即使传expnoise也只影响BLOCK选择 |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |


### Route R-003：STORE=false SAMPLE=false EXTERNAL=false ROUND=2

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_outNone，has_sampled_rowsFalse，合同必须所有温度0，exp_noiseNone，step_dtype=FP16。HAS_BIAS/SELECT恒true，local世界1；BLOCK=1024，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，toFP16再toFP32；不写logits。不读温度并固定0，不生成/读取噪声，score=value；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | 无写 |
| temperature | 不读 |
| noise/RNG | OFFSET/KEY/STEP均不Device读取 |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。外部noise/贪心分支不构建Philox临时。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias  +8B*Qp` B。S为实际非零温度行数，本域S0；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND2真实FP16→FP32在选取前；kept输出同stepdtype |
| temperature | has_sampled_rowsFalse忽略Tensor值，调用方保证全部0 |
| RNG | 没有RNG消费，即使传expnoise也只影响BLOCK选择 |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |


### Route R-004：STORE=false SAMPLE=false EXTERNAL=true ROUND=0

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_outNone，has_sampled_rowsFalse，合同必须所有温度0，exp_noise存在，step_dtype=FP32。HAS_BIAS/SELECT恒true，local世界1；BLOCK=min(4096,nextpow2(P))，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，保持FP32；不写logits。不读温度并固定0，不生成/读取噪声，score=value；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | 无写 |
| temperature | 不读 |
| noise/RNG | 外部noise只作Hostshape检查、不Device读取 |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。外部noise/贪心分支不构建Philox临时。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias  +8B*Qp` B。S为实际非零温度行数，本域S0；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND0真实FP32在选取前；kept输出同stepdtype |
| temperature | has_sampled_rowsFalse忽略Tensor值，调用方保证全部0 |
| RNG | 没有RNG消费，即使传expnoise也只影响BLOCK选择 |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |


### Route R-005：STORE=false SAMPLE=false EXTERNAL=true ROUND=1

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_outNone，has_sampled_rowsFalse，合同必须所有温度0，exp_noise存在，step_dtype=BF16。HAS_BIAS/SELECT恒true，local世界1；BLOCK=min(4096,nextpow2(P))，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，toBF16再toFP32；不写logits。不读温度并固定0，不生成/读取噪声，score=value；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | 无写 |
| temperature | 不读 |
| noise/RNG | 外部noise只作Hostshape检查、不Device读取 |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。外部noise/贪心分支不构建Philox临时。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias  +8B*Qp` B。S为实际非零温度行数，本域S0；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND1真实BF16→FP32在选取前；kept输出同stepdtype |
| temperature | has_sampled_rowsFalse忽略Tensor值，调用方保证全部0 |
| RNG | 没有RNG消费，即使传expnoise也只影响BLOCK选择 |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |


### Route R-006：STORE=false SAMPLE=false EXTERNAL=true ROUND=2

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_outNone，has_sampled_rowsFalse，合同必须所有温度0，exp_noise存在，step_dtype=FP16。HAS_BIAS/SELECT恒true，local世界1；BLOCK=min(4096,nextpow2(P))，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，toFP16再toFP32；不写logits。不读温度并固定0，不生成/读取噪声，score=value；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | 无写 |
| temperature | 不读 |
| noise/RNG | 外部noise只作Hostshape检查、不Device读取 |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。外部noise/贪心分支不构建Philox临时。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias  +8B*Qp` B。S为实际非零温度行数，本域S0；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND2真实FP16→FP32在选取前；kept输出同stepdtype |
| temperature | has_sampled_rowsFalse忽略Tensor值，调用方保证全部0 |
| RNG | 没有RNG消费，即使传expnoise也只影响BLOCK选择 |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |


### Route R-007：STORE=false SAMPLE=true EXTERNAL=false ROUND=0

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_outNone，has_sampled_rows不是False（True或None），exp_noiseNone，step_dtype=FP32。HAS_BIAS/SELECT恒true，local世界1；BLOCK=1024，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→tl.philox→_negative_log1p_negative→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，保持FP32；不写logits。load温度；若温度非0，用Philox10轮生成BLOCK词噪声，score=value/temp-log(noise)；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | 无写 |
| temperature | 4B*Qp B读（每行每part一次） |
| noise/RNG | 8S*Qp B OFFSET标量逻辑读；每part BLOCK/4个Philox四word，无noiseGM |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。Philox4×(BLOCK/4)uint32→interleave→int64&mask→FP32uniform/expnoise均任务SSA；不假设其同时驻留峰值。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias +4B*Qp+8S*Qp +8B*Qp` B。S为实际非零温度行数，0≤S≤B；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND0真实FP32在选取前；kept输出同stepdtype |
| temperature | 非零才进入noise分支，0走argmax；负/NaN温度不在推荐合同 |
| RNG | counter/KEY/offset不写回，调用方管理重放/新step；FP32uniform可达1→expnoiseinf |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |


### Route R-008：STORE=false SAMPLE=true EXTERNAL=false ROUND=1

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_outNone，has_sampled_rows不是False（True或None），exp_noiseNone，step_dtype=BF16。HAS_BIAS/SELECT恒true，local世界1；BLOCK=1024，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→tl.philox→_negative_log1p_negative→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，toBF16再toFP32；不写logits。load温度；若温度非0，用Philox10轮生成BLOCK词噪声，score=value/temp-log(noise)；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | 无写 |
| temperature | 4B*Qp B读（每行每part一次） |
| noise/RNG | 8S*Qp B OFFSET标量逻辑读；每part BLOCK/4个Philox四word，无noiseGM |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。Philox4×(BLOCK/4)uint32→interleave→int64&mask→FP32uniform/expnoise均任务SSA；不假设其同时驻留峰值。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias +4B*Qp+8S*Qp +8B*Qp` B。S为实际非零温度行数，0≤S≤B；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND1真实BF16→FP32在选取前；kept输出同stepdtype |
| temperature | 非零才进入noise分支，0走argmax；负/NaN温度不在推荐合同 |
| RNG | counter/KEY/offset不写回，调用方管理重放/新step；FP32uniform可达1→expnoiseinf |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |


### Route R-009：STORE=false SAMPLE=true EXTERNAL=false ROUND=2

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_outNone，has_sampled_rows不是False（True或None），exp_noiseNone，step_dtype=FP16。HAS_BIAS/SELECT恒true，local世界1；BLOCK=1024，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→tl.philox→_negative_log1p_negative→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，toFP16再toFP32；不写logits。load温度；若温度非0，用Philox10轮生成BLOCK词噪声，score=value/temp-log(noise)；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | 无写 |
| temperature | 4B*Qp B读（每行每part一次） |
| noise/RNG | 8S*Qp B OFFSET标量逻辑读；每part BLOCK/4个Philox四word，无noiseGM |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。Philox4×(BLOCK/4)uint32→interleave→int64&mask→FP32uniform/expnoise均任务SSA；不假设其同时驻留峰值。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias +4B*Qp+8S*Qp +8B*Qp` B。S为实际非零温度行数，0≤S≤B；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND2真实FP16→FP32在选取前；kept输出同stepdtype |
| temperature | 非零才进入noise分支，0走argmax；负/NaN温度不在推荐合同 |
| RNG | counter/KEY/offset不写回，调用方管理重放/新step；FP32uniform可达1→expnoiseinf |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |


### Route R-010：STORE=false SAMPLE=true EXTERNAL=true ROUND=0

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_outNone，has_sampled_rows不是False（True或None），exp_noise存在，step_dtype=FP32。HAS_BIAS/SELECT恒true，local世界1；BLOCK=min(4096,nextpow2(P))，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，保持FP32；不写logits。load温度；若温度非0，maski<W读exp_noise，score=value/temp-log(noise)；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | 无写 |
| temperature | 4B*Qp B读（每行每part一次） |
| noise/RNG | 4S*W B外部noise读，S=非零温度行数 |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。外部noise/贪心分支不构建Philox临时。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias +4B*Qp+4S*W +8B*Qp` B。S为实际非零温度行数，0≤S≤B；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND0真实FP32在选取前；kept输出同stepdtype |
| temperature | 非零才进入noise分支，0走argmax；负/NaN温度不在推荐合同 |
| RNG | key/step/offset不用于噪声，外部noise刷新由调用方 |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |


### Route R-011：STORE=false SAMPLE=true EXTERNAL=true ROUND=1

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_outNone，has_sampled_rows不是False（True或None），exp_noise存在，step_dtype=BF16。HAS_BIAS/SELECT恒true，local世界1；BLOCK=min(4096,nextpow2(P))，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，toBF16再toFP32；不写logits。load温度；若温度非0，maski<W读exp_noise，score=value/temp-log(noise)；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | 无写 |
| temperature | 4B*Qp B读（每行每part一次） |
| noise/RNG | 4S*W B外部noise读，S=非零温度行数 |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。外部noise/贪心分支不构建Philox临时。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias +4B*Qp+4S*W +8B*Qp` B。S为实际非零温度行数，0≤S≤B；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND1真实BF16→FP32在选取前；kept输出同stepdtype |
| temperature | 非零才进入noise分支，0走argmax；负/NaN温度不在推荐合同 |
| RNG | key/step/offset不用于噪声，外部noise刷新由调用方 |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |


### Route R-012：STORE=false SAMPLE=true EXTERNAL=true ROUND=2

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_outNone，has_sampled_rows不是False（True或None），exp_noise存在，step_dtype=FP16。HAS_BIAS/SELECT恒true，local世界1；BLOCK=min(4096,nextpow2(P))，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，toFP16再toFP32；不写logits。load温度；若温度非0，maski<W读exp_noise，score=value/temp-log(noise)；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | 无写 |
| temperature | 4B*Qp B读（每行每part一次） |
| noise/RNG | 4S*W B外部noise读，S=非零温度行数 |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。外部noise/贪心分支不构建Philox临时。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias +4B*Qp+4S*W +8B*Qp` B。S为实际非零温度行数，0≤S≤B；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND2真实FP16→FP32在选取前；kept输出同stepdtype |
| temperature | 非零才进入noise分支，0走argmax；负/NaN温度不在推荐合同 |
| RNG | key/step/offset不用于噪声，外部noise刷新由调用方 |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |


### Route R-013：STORE=true SAMPLE=false EXTERNAL=false ROUND=0

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_out为合法独立[B,P]缓冲，has_sampled_rowsFalse，合同必须所有温度0，exp_noiseNone，step_dtype=FP32。HAS_BIAS/SELECT恒true，local世界1；BLOCK=1024，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，保持FP32；将所有i<P写logits_out，不只W。不读温度并固定0，不生成/读取噪声，score=value；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | BP*dstep B写，独立预分配不alias输入 |
| temperature | 不读 |
| noise/RNG | OFFSET/KEY/STEP均不Device读取 |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→GMlogits_out及scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。外部noise/贪心分支不构建Philox临时。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias + BP*dstep +8B*Qp` B。S为实际非零温度行数，本域S0；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND0真实FP32在选取前；kept输出同stepdtype |
| temperature | has_sampled_rowsFalse忽略Tensor值，调用方保证全部0 |
| RNG | 没有RNG消费，即使传expnoise也只影响BLOCK选择 |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |


### Route R-014：STORE=true SAMPLE=false EXTERNAL=false ROUND=1

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_out为合法独立[B,P]缓冲，has_sampled_rowsFalse，合同必须所有温度0，exp_noiseNone，step_dtype=BF16。HAS_BIAS/SELECT恒true，local世界1；BLOCK=1024，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，toBF16再toFP32；将所有i<P写logits_out，不只W。不读温度并固定0，不生成/读取噪声，score=value；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | BP*dstep B写，独立预分配不alias输入 |
| temperature | 不读 |
| noise/RNG | OFFSET/KEY/STEP均不Device读取 |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→GMlogits_out及scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。外部noise/贪心分支不构建Philox临时。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias + BP*dstep +8B*Qp` B。S为实际非零温度行数，本域S0；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND1真实BF16→FP32在选取前；kept输出同stepdtype |
| temperature | has_sampled_rowsFalse忽略Tensor值，调用方保证全部0 |
| RNG | 没有RNG消费，即使传expnoise也只影响BLOCK选择 |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |


### Route R-015：STORE=true SAMPLE=false EXTERNAL=false ROUND=2

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_out为合法独立[B,P]缓冲，has_sampled_rowsFalse，合同必须所有温度0，exp_noiseNone，step_dtype=FP16。HAS_BIAS/SELECT恒true，local世界1；BLOCK=1024，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，toFP16再toFP32；将所有i<P写logits_out，不只W。不读温度并固定0，不生成/读取噪声，score=value；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | BP*dstep B写，独立预分配不alias输入 |
| temperature | 不读 |
| noise/RNG | OFFSET/KEY/STEP均不Device读取 |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→GMlogits_out及scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。外部noise/贪心分支不构建Philox临时。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias + BP*dstep +8B*Qp` B。S为实际非零温度行数，本域S0；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND2真实FP16→FP32在选取前；kept输出同stepdtype |
| temperature | has_sampled_rowsFalse忽略Tensor值，调用方保证全部0 |
| RNG | 没有RNG消费，即使传expnoise也只影响BLOCK选择 |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |


### Route R-016：STORE=true SAMPLE=false EXTERNAL=true ROUND=0

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_out为合法独立[B,P]缓冲，has_sampled_rowsFalse，合同必须所有温度0，exp_noise存在，step_dtype=FP32。HAS_BIAS/SELECT恒true，local世界1；BLOCK=min(4096,nextpow2(P))，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，保持FP32；将所有i<P写logits_out，不只W。不读温度并固定0，不生成/读取噪声，score=value；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | BP*dstep B写，独立预分配不alias输入 |
| temperature | 不读 |
| noise/RNG | 外部noise只作Hostshape检查、不Device读取 |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→GMlogits_out及scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。外部noise/贪心分支不构建Philox临时。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias + BP*dstep +8B*Qp` B。S为实际非零温度行数，本域S0；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND0真实FP32在选取前；kept输出同stepdtype |
| temperature | has_sampled_rowsFalse忽略Tensor值，调用方保证全部0 |
| RNG | 没有RNG消费，即使传expnoise也只影响BLOCK选择 |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |


### Route R-017：STORE=true SAMPLE=false EXTERNAL=true ROUND=1

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_out为合法独立[B,P]缓冲，has_sampled_rowsFalse，合同必须所有温度0，exp_noise存在，step_dtype=BF16。HAS_BIAS/SELECT恒true，local世界1；BLOCK=min(4096,nextpow2(P))，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，toBF16再toFP32；将所有i<P写logits_out，不只W。不读温度并固定0，不生成/读取噪声，score=value；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | BP*dstep B写，独立预分配不alias输入 |
| temperature | 不读 |
| noise/RNG | 外部noise只作Hostshape检查、不Device读取 |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→GMlogits_out及scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。外部noise/贪心分支不构建Philox临时。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias + BP*dstep +8B*Qp` B。S为实际非零温度行数，本域S0；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND1真实BF16→FP32在选取前；kept输出同stepdtype |
| temperature | has_sampled_rowsFalse忽略Tensor值，调用方保证全部0 |
| RNG | 没有RNG消费，即使传expnoise也只影响BLOCK选择 |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |


### Route R-018：STORE=true SAMPLE=false EXTERNAL=true ROUND=2

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_out为合法独立[B,P]缓冲，has_sampled_rowsFalse，合同必须所有温度0，exp_noise存在，step_dtype=FP16。HAS_BIAS/SELECT恒true，local世界1；BLOCK=min(4096,nextpow2(P))，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，toFP16再toFP32；将所有i<P写logits_out，不只W。不读温度并固定0，不生成/读取噪声，score=value；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | BP*dstep B写，独立预分配不alias输入 |
| temperature | 不读 |
| noise/RNG | 外部noise只作Hostshape检查、不Device读取 |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→GMlogits_out及scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。外部noise/贪心分支不构建Philox临时。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias + BP*dstep +8B*Qp` B。S为实际非零温度行数，本域S0；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND2真实FP16→FP32在选取前；kept输出同stepdtype |
| temperature | has_sampled_rowsFalse忽略Tensor值，调用方保证全部0 |
| RNG | 没有RNG消费，即使传expnoise也只影响BLOCK选择 |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |


### Route R-019：STORE=true SAMPLE=true EXTERNAL=false ROUND=0

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_out为合法独立[B,P]缓冲，has_sampled_rows不是False（True或None），exp_noiseNone，step_dtype=FP32。HAS_BIAS/SELECT恒true，local世界1；BLOCK=1024，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→tl.philox→_negative_log1p_negative→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，保持FP32；将所有i<P写logits_out，不只W。load温度；若温度非0，用Philox10轮生成BLOCK词噪声，score=value/temp-log(noise)；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | BP*dstep B写，独立预分配不alias输入 |
| temperature | 4B*Qp B读（每行每part一次） |
| noise/RNG | 8S*Qp B OFFSET标量逻辑读；每part BLOCK/4个Philox四word，无noiseGM |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→GMlogits_out及scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。Philox4×(BLOCK/4)uint32→interleave→int64&mask→FP32uniform/expnoise均任务SSA；不假设其同时驻留峰值。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias + BP*dstep+4B*Qp+8S*Qp +8B*Qp` B。S为实际非零温度行数，0≤S≤B；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND0真实FP32在选取前；kept输出同stepdtype |
| temperature | 非零才进入noise分支，0走argmax；负/NaN温度不在推荐合同 |
| RNG | counter/KEY/offset不写回，调用方管理重放/新step；FP32uniform可达1→expnoiseinf |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |


### Route R-020：STORE=true SAMPLE=true EXTERNAL=false ROUND=1

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_out为合法独立[B,P]缓冲，has_sampled_rows不是False（True或None），exp_noiseNone，step_dtype=BF16。HAS_BIAS/SELECT恒true，local世界1；BLOCK=1024，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→tl.philox→_negative_log1p_negative→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，toBF16再toFP32；将所有i<P写logits_out，不只W。load温度；若温度非0，用Philox10轮生成BLOCK词噪声，score=value/temp-log(noise)；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | BP*dstep B写，独立预分配不alias输入 |
| temperature | 4B*Qp B读（每行每part一次） |
| noise/RNG | 8S*Qp B OFFSET标量逻辑读；每part BLOCK/4个Philox四word，无noiseGM |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→GMlogits_out及scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。Philox4×(BLOCK/4)uint32→interleave→int64&mask→FP32uniform/expnoise均任务SSA；不假设其同时驻留峰值。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias + BP*dstep+4B*Qp+8S*Qp +8B*Qp` B。S为实际非零温度行数，0≤S≤B；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND1真实BF16→FP32在选取前；kept输出同stepdtype |
| temperature | 非零才进入noise分支，0走argmax；负/NaN温度不在推荐合同 |
| RNG | counter/KEY/offset不写回，调用方管理重放/新step；FP32uniform可达1→expnoiseinf |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |


### Route R-021：STORE=true SAMPLE=true EXTERNAL=false ROUND=2

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_out为合法独立[B,P]缓冲，has_sampled_rows不是False（True或None），exp_noiseNone，step_dtype=FP16。HAS_BIAS/SELECT恒true，local世界1；BLOCK=1024，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→tl.philox→_negative_log1p_negative→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，toFP16再toFP32；将所有i<P写logits_out，不只W。load温度；若温度非0，用Philox10轮生成BLOCK词噪声，score=value/temp-log(noise)；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | BP*dstep B写，独立预分配不alias输入 |
| temperature | 4B*Qp B读（每行每part一次） |
| noise/RNG | 8S*Qp B OFFSET标量逻辑读；每part BLOCK/4个Philox四word，无noiseGM |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→GMlogits_out及scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。Philox4×(BLOCK/4)uint32→interleave→int64&mask→FP32uniform/expnoise均任务SSA；不假设其同时驻留峰值。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias + BP*dstep+4B*Qp+8S*Qp +8B*Qp` B。S为实际非零温度行数，0≤S≤B；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND2真实FP16→FP32在选取前；kept输出同stepdtype |
| temperature | 非零才进入noise分支，0走argmax；负/NaN温度不在推荐合同 |
| RNG | counter/KEY/offset不写回，调用方管理重放/新step；FP32uniform可达1→expnoiseinf |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |


### Route R-022：STORE=true SAMPLE=true EXTERNAL=true ROUND=0

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_out为合法独立[B,P]缓冲，has_sampled_rows不是False（True或None），exp_noise存在，step_dtype=FP32。HAS_BIAS/SELECT恒true，local世界1；BLOCK=min(4096,nextpow2(P))，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，保持FP32；将所有i<P写logits_out，不只W。load温度；若温度非0，maski<W读exp_noise，score=value/temp-log(noise)；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | BP*dstep B写，独立预分配不alias输入 |
| temperature | 4B*Qp B读（每行每part一次） |
| noise/RNG | 4S*W B外部noise读，S=非零温度行数 |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→GMlogits_out及scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。外部noise/贪心分支不构建Philox临时。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias + BP*dstep+4B*Qp+4S*W +8B*Qp` B。S为实际非零温度行数，0≤S≤B；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND0真实FP32在选取前；kept输出同stepdtype |
| temperature | 非零才进入noise分支，0走argmax；负/NaN温度不在推荐合同 |
| RNG | key/step/offset不用于噪声，外部noise刷新由调用方 |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |


### Route R-023：STORE=true SAMPLE=true EXTERNAL=true ROUND=1

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_out为合法独立[B,P]缓冲，has_sampled_rows不是False（True或None），exp_noise存在，step_dtype=BF16。HAS_BIAS/SELECT恒true，local世界1；BLOCK=min(4096,nextpow2(P))，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，toBF16再toFP32；将所有i<P写logits_out，不只W。load温度；若温度非0，maski<W读exp_noise，score=value/temp-log(noise)；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | BP*dstep B写，独立预分配不alias输入 |
| temperature | 4B*Qp B读（每行每part一次） |
| noise/RNG | 4S*W B外部noise读，S=非零温度行数 |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→GMlogits_out及scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。外部noise/贪心分支不构建Philox临时。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias + BP*dstep+4B*Qp+4S*W +8B*Qp` B。S为实际非零温度行数，0≤S≤B；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND1真实BF16→FP32在选取前；kept输出同stepdtype |
| temperature | 非零才进入noise分支，0走argmax；负/NaN温度不在推荐合同 |
| RNG | key/step/offset不用于噪声，外部noise刷新由调用方 |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |


### Route R-024：STORE=true SAMPLE=true EXTERNAL=true ROUND=2

#### 适用条件

##### 选择证据

冻结gather/gather_logits均None；logits_out为合法独立[B,P]缓冲，has_sampled_rows不是False（True或None），exp_noise存在，step_dtype=FP16。HAS_BIAS/SELECT恒true，local世界1；BLOCK=min(4096,nextpow2(P))，Qp=ceil(P/BLOCK)。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_check→_launch_partial→_markov_sample_partial_kernel→_round_to_step_dtype→_select_block→partialGM→R-025finish`。自有全部helper已读，没有外部gather/mathfallback。

##### 源码等价伪码

task=row*Qp+part按grid核数轮转，i=part*BLOCK+arange；读base前P、bias前W→FP32加，toFP16再toFP32；将所有i<P写logits_out，不只W。load温度；若温度非0，maski<W读exp_noise，score=value/temp-log(noise)；温度0保持value。仅i<W参与NaN优先max/最小全局idx，partial写(max,idxbits)。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/读取 |
|---|---|
| value/key | 各BLOCK FP32逻辑4BLOCK B；ROUND低dtype往返，physical分配未知 |
| base/bias | 完整BP*db/BW*dbias B读，paddingbase仍读取 |
| logits_out | BP*dstep B写，独立预分配不alias输入 |
| temperature | 4B*Qp B读（每行每part一次） |
| noise/RNG | 4S*W B外部noise读，S=非零温度行数 |
| partial | B*Qp*2FP32=8B*Qp B写，索引按int32位模式打包 |
| physical UB/workspace | 无显式UB/TQue/TBuf，GMpartial为真实scratch，compiler资源外部 |

##### 分层内存布局

`GMbase/bias→FP32add/step-round→GMlogits_out及scoreSSA[BLOCK]→NaN/max/min→GMpartial[B,Qp,2]`。外部noise/贪心分支不构建Philox临时。

##### 字节账与复用顺序

本partial节点逻辑GM `BP*db + BW*dbias + BP*dstep+4B*Qp+4S*W +8B*Qp` B。S为实际非零温度行数，0≤S≤B；仅SAMPLE=true、当前行温度非零且EXTERNAL=false时执行内部Philox及设备OFFSET读取，W0不额外关闭该分支但不产生有效候选；SAMPLE=false或EXTERNAL=true均无此设备读取，Python的offset检查另行保留。partial由Host分配，在R-025finish前保持有效；kept-logits/输入/noise异步存活按framework，不假设cache减少load或物理DMA事务相同。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| task | row/part商余唯一、无共享partial写/atomic |
| masks | base/store i<P、bias/selection/noise i<W；两种宽度不可混淆 |
| step精度 | ROUND2真实FP16→FP32在选取前；kept输出同stepdtype |
| temperature | 非零才进入noise分支，0走argmax；负/NaN温度不在推荐合同 |
| RNG | key/step/offset不用于噪声，外部noise刷新由调用方 |
| tie/NaN | 有效NaN先于其它候选并取最小globalidx；否则max并列最小globalidx；W0哨兵 |
| 边界 | globalidx须非负int32且<2147483647，避免与哨兵/符号mask冲突；无完整Hostguard |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| partial/round | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L28-L107) |
| selection与RNG | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L110-L164) |
| flags/block/launch | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L194-L252) |

### Route R-025：本地候选最终归约

#### 适用条件

##### 选择证据

所有24partial实例后必达，gathered直接partial.view，WORLD1、PARTS=Qp、F=nextpow2Qp；B/P正，无回调。

#### Device 数据流

##### 函数级调用链

`markov_sample_step_triton→_markov_sample_finish_kernel→load/bitcast/NaNmax/min/store`；没有其它自有helper/Kernel。

##### 源码等价伪码

每row：i=arangeF，valid=i<Qp；rank=i//Qp（local均0有效）、part=i%Qp，offset=((rank*B+row)*Qp+part)*2；读value及idxbits→bitcastint32→idx&0x7fffffff，排除idx哨兵；NaN优先、否则max，最小获胜idx，storeint64。全无有效候选时哨兵。

#### 内存与数据搬运

##### 资源与搬运表

| 对象 | 逻辑规模/GM |
|---|---|
| value/idx | 各F槽，FP32/int32；physical缓冲未知 |
| nan/wins/masks | F逻辑布尔，rank/part/offset由SSA计算 |
| GMpartial | 完整8B*Qp B读 |
| GMtokens | 8B B写 |
| workspace | 无新scratch，复用Hostpartial寿命 |

##### 分层内存布局

GMpartial[B,Qp,2]→value/idxbitsSSA[F]→NaN/max/min→GMint64tokens[B]。索引槽不得做float数值变换，local无需外部transport编码。

##### 字节账与复用顺序

finish逻辑读取8BQp、写8B B；加前序partial总scratch往返16BQp B。partial必须在finish结束前保持有效，Python局部引用与framework异步allocator处理回收；keptout不会被finish读取，令牌选择依据partial有效W。

#### 同步、精度与尾块

##### 同步与数值边界表

| 项 | 边界 |
|---|---|
| 交接 | partial→finish框架流顺序，源码无hostwait/event |
| padding | i<Qp，loadvalue其他-inf、idx其他0但后续valid仍false |
| idxbits | loadfloat32后bitcastint32，&NOIDX，要求原合法非负int32；sentinel不参与max |
| NaN/tie | 有NaN按最小globalidx，否则最大值并列最小idx；跨parts保持同规则 |
| 空有效分片 | W0全部NOIDX，result保持2147483647，输出类型int64 |
| 核间 | 每row一个逻辑owner，无atomic/barrier |

#### 关键实现

##### 符号证据表

| 符号 | 定位 |
|---|---|
| finish | [body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L167-L191) |
| local调用 | [launcher](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L354-L375) |

## 算子特定优化

### Trick T-001：Philox四word按全局token四元组映射

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L140-L155)：

```python
            # One Philox call yields four words; word k goes to token 4 * q + k.
            quad = (part * BLOCK + VOCAB_START) // 4 + tl.arange(0, BLOCK // 4)
            lane = tl.zeros([BLOCK // 4], tl.int64)
            w0, w1, w2, w3 = tl.philox(
                KEY,
                quad.to(tl.uint32),
                (lane + row).to(tl.uint32),
                (lane + STEP).to(tl.uint32),
                ((lane + tl.load(OFFSET)) & 0xFFFFFFFF).to(tl.uint32),
                PHILOX_ROUNDS,
            )
            bits = tl.interleave(tl.interleave(w0, w2), tl.interleave(w1, w3))
            # Triton-Ascend can sign-extend Philox uint32 words when widening.
            bits = bits.to(tl.int64) & 0xFFFFFFFF
            uniform = (bits.to(tl.float32) + 0.5) * _UNIFORM_SCALE
            exp_noise = _negative_log1p_negative(uniform)
```

#### 机制与设计原因

quad对齐全局词表，counter结合row/step/offset低32bit，nestedinterleave恢复四word次序；int64&mask修正uint32拓宽可能符号扩展。按block局部生成不物化noiseGM。上游规避说明不是本次复现。

#### 迁移边界

vocab_start4对齐、BLOCK1024可整除4、counter可表示/截断语义由调用方接受；KEY/offset/step更新所有权外部。externalnoise路径完全跳过Philox，不套其计数器给任意外部RNG。

#### 错误做法

遗漏uint32mask、交换四word顺序，或误认函数会自增offset保证重放新噪声。

### Trick T-002：最大值与索引bits成对存partial，保留NaN及稳定并列

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L157-L164)：

```python
    nan = valid & (key != key)
    has_nan = tl.sum(nan.to(tl.int32), 0) > 0
    maximum = tl.max(tl.where(valid & ~nan, key, -float("inf")), 0)
    wins = tl.where(has_nan, nan, valid & (key == maximum))
    idx = tl.min(tl.where(wins, i + VOCAB_START, _NO_INDEX), 0)
    maximum = tl.where(has_nan, float("nan"), maximum)
    tl.store(P + (row * PARTS + part) * 2, maximum)
    tl.store(P + (row * PARTS + part) * 2 + 1, idx.to(tl.float32, bitcast=True))
```

#### 机制与设计原因

每part只写8B候选，idxbits借FP32槽位传输但不做数值转换；finish相同NaN优先/最小idx规则完成跨part选择，无共享原子计数。

#### 迁移边界

idx为非负int32且小于NOIDX，bit模式必须完整传输；原分布式callback不在本卡闭包，不能直接套其它后端候选layout。

#### 错误做法

把idx数值cast为float32导致>2²⁴索引损失，或忽略NaN优先/最小全局索引。

### Trick T-003：小uniform的补偿式指数噪声转换

#### 触发与源码依据

[连续源码](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py#L37-L44)：

```python
@triton.jit
def _negative_log1p_negative(uniform):
    # Compensate the rounding of 1-u: the CANN libdevice log1p loses small u.
    complement = 1.0 - uniform
    correction = (1.0 - complement) - uniform
    noise = -tl.log(complement) - correction / complement
    noise = tl.where(complement == 0.0, float("inf"), noise)
    return tl.where(uniform == 0.0, 0.0, noise)
```

#### 机制与设计原因

先计算1-u，再用(1-complement)-u纠正舍入，避免直接log1p路径对小u的损失；u1返回inf、u0返回0显式处理。没有数值误差界/真机结果。

#### 迁移边界

FP32primitive顺序/舍入须匹配，u来自本mapping；不能把内部expnoise默认当任意生成器一致序列。

#### 错误做法

以不同log1p/generator替换仍宣称相同随机流，或固定externalnoise却期待每次图重放新采样。

## 模板与实现对比

24partial特化+sharedfinish均覆盖，keptlogits输出不触发callback，不另拆其数学；step-round控制选择前精度，SAMPLEfalse只合法用于全0温度。callbacks原全域仍defer、Greedy含F.linear另任务也缺核心源，不借本卡替代。

## 平台差异

本卡A2/A3归属arch22；公开arch22/35支持，README/architectures映射A2/A3、950，注册非全部芯片实测。block4096注释动机在A3，不能写成950收益证明；CANN9.1.0 CI配置非本次运行或Tritonbinary等同。

## 限制与失败边界

仅local冻结域，所有输入同NPU/浮点与value/globalidx/counter/resource/JIT整数范围未完整guard；assert可关闭。NaN/Inf按真实分支传播，不宣称所有特殊值或外部噪声分布合法。无编译、随机序列/数值/性能/图重放测试或校验，无physicalUB产物；draft不作无条件安全复用。

## 源码索引

### 链路索引

| 阶段/源码 | 符号 | 事实 |
|---|---|---|
| [公开合同](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/sample/markov_sample_step_triton.md) | `markov_sample_step_triton` | 舍入/温度/Philox/外部噪声/平台 |
| [完整Direct/Device/helpers](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_sample.py) | `markov_sample_step_triton/_launch_partial/_check/_markov_sample_*` | 375行全部；冻结local无callbacks |
| [公开转发](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/sample/markov_sample.py) | `_triton_impl` | 关键字转发 |
| [属性helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py) | `get_device_properties` | 无参currentdevicecache |
| [sample包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/__init__.py) | `module init` | 无附加Device |
| [import边界](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py) | `_load_sgl_kernel_npu` | torch_npu/原生库与vendor初始化 |
| [backend包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/__init__.py) | `module init` | 懒加载包，无另一Device节点 |
| [构建入口](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/setup.py) | `main` | 完整Python wheel路径；本次未构建 |
| [源码打包](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/torch_wheel.py) | `stage_runtime/build_torch/build_wheel/setup_refactor` | 复制完整Python包、原生运行库与wheel |
| [平台/包说明](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md) | `REFACTOR/arch22/35 mapping` | 全部Python实现包含、产品映射、CANN9.1.0构建例 |
| [产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json) | `2201/3510` | a2/a3/950对应构建族 |
| [版本配置](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml) | `test-norm-ops` | CANN9.1.0/a3/950配置，非本次运行 |
| [CI消费](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernel-group.yml) | `run-kernel-group` | 对应版本容器/测试组参数 |

### 实现复用检查

冻结117唯一MarkovsampleAPI已全文读并链接；原callbacks全域defer不产Operator，此独立local两平台卡覆盖可选keptlogits但不回调，不修改API。全部固定同repo唯一primary，无verified。
