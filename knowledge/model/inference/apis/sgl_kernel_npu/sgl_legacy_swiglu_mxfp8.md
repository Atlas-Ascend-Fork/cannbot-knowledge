---
type: API
title: 旧SwiGLU的Triton MXFP8与限幅浮点接口
description: 保存旧Triton SwiGLU在SiLU前限幅、每32元素E4M3与E8M0量化及浮点分支，明确累计group越视图、slice尾块和未知平台边界。
tags: [task.implementation, topic.compute.elementwise.activation, topic.precision]
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/activation/swiglu_mxfp8_quant.py
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_swiglu_mxfp8_quant.py
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/activation/swiglu_quant.py
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py
  role: header
created_at: "2026-11-09T15:57:47Z"
updated_at: "2026-11-09T15:57:47Z"
platforms: []
---

# 旧SwiGLU的Triton MXFP8与限幅浮点接口

## 入口与范围

固定sgl-kernel-npu提交 `dda6d36b0cdb4081e102d14c0a2fb276fc416e69` 的旧模块入口：

```python
from sgl_kernel_npu.activation.swiglu_mxfp8_quant import swiglu_quant
payload, scale = swiglu_quant(
    x, group_list, group_list_type,
    need_quant=True, do_limit=False, limit=7.0,
)
```

这是自有Triton整行SwiGLU+每32元素MXFP8算法，也保存实际可达need_quant=False的浮点分支。平台未知，保持draft API Reference与platforms=[]，不猜CANN版本，不称完整Operator/source_closed。存在本模块的pytest源码定义，不等于活动CI接线或真实执行；没有把NPU字符串、注释中的模型名、别的native量化产品范围转移到本入口。本次未执行编译、测试、真机或性能验证。

## 激活与量化数学

X的Host shape为[S,H]，C=floor(H/2)，前C为g，后C为u；整H项先load再转FP32。数学是：

```text
DO_LIMIT=False: v = g * sigmoid(g) * u
DO_LIMIT=True:  g1=min(g,L);u1=max(min(u,L),-L)
                v = g1 * sigmoid(g1) * u1
```

gate在SiLU前单边限幅，up双边限幅。它与旧INT8 swiglu_quant的“SiLU后限制gate结果”不同；DO_LIMIT=False激活相同不代表两个量化ABI等价。没有alpha或OAI的(up+1)项。limit负值/NaN/Inf以及X非finite无Host数值guard，不推导稳定特例输出。

True分支把每row按连续32列分组。设t为一组FP32激活：

```text
amax=max(abs(t))
m=max(amax,1e-4)
m2=m/448
bits=bitcast_int32(m2)
e=(bits>>23)&255
if e<255 and (bits&0x7fffff)!=0: e+=1
inv_scale=exp2(127-float32(e))
q=cast_e4m3fn(clamp(t*inv_scale,-448,448))
store uint8(e)
```

对正常有限正m2，这是向上取2幂scale：s=2^(e-127)，每组一个E8M0偏置指数；scale并非逐row FP32值。零组也经1e-4下限得到正的2幂scale，payload为零。对NaN/Inf、指数255及其转换，源码没有额外修复，不能把普通有限值的推导推广为完整异常合同。E4M3转换由Triton cast primitive承担，未显式选择RNE等模式，也没有native SiTU路径的先BF16舍入步骤。

## Host参数、返回与检查

| 参数/返回 | 实际合同 |
|---|---|
| x | 直接s,h=x.shape解包为rank2；无reshape/contiguous或stride参数。 |
| group_list | 必传，E=shape[0]；int32/int64，取A=ceil(E/16)*16或ceil(E/8)*8。 |
| group_list_type | 只接受0/1，否则ValueError；没有None/dense分支。 |
| need_quant=True | 检查C%32==0；out=empty([S,C],float8_e4m3fn)，scale原始empty([S,C/32],uint8)，返回scale.view(float8_e8m0fnu)。 |
| need_quant=False | 不做C%32检查；out dtype=x.dtype，scale为uint8[S,floor(C/32)]，整个scale未写但仍返回。 |
| do_limit/limit | 作为constexpr传JIT；Host没有非负/finite检查。 |

A的两个表达式均64字节对齐，不是注释所称的32字节，也不是自动next_power_of_2。没有group rank/非空/设备/连续/值范围检查；X dtype/NPU/连续/偶H/正维度也没有显式保证。奇H只提取[0,C)和[C,2C)，最后一项不参与激活，不能默认为合理的丢列行为。need_quant=True仅有C%32检查，不能据此承诺所有C都能编译或安全执行。

payload与scale都是新分配，不改X/group。True的scale view与uint8 buffer共享同一字节storage，无数值转换或额外Kernel。文档建议为grouped_matmul view成[S,C/64,2]，还需要C可被64整除；Host只检查32，不能保证该额外view总合法。任何输出只写前R行，后S-R行仍未初始化。

## 分组与已知读取终点

```text
type=1: R=sum(load(group[0:A],mask< E,other=0).to(int32))
type=0: R=load(group[E]).to(int32)
```

cumulative实际地址是[E]，在名义E项1D group之外，且发生于row early-return之前；不是读取最后项[E-1]。添加一个sentinel同时增大shape0仍会使Host传更大的E，不能以测试构造了前导0来修正实际地址。未确定的读取值不能被编造成确定运行轨迹。count各项转int32再sum，无溢出/负值检查，无R<=S夹取。以下后续body只以group读取成功、0<=R<=S及调度整数域合法为条件。R>S会驱动分配外访问；R<S后缀未写；group仅决定总前缀，不负责expert重排。

## 单JIT图、分核与尾块

实际符号 `_swiglu_quant_kernel` 只有@triton.jit，无autotune。Host用get_device_properties()[1]为P，grid=(P,)，multibuffer=True。四GM ptr为X/group/out/scale；constexpr为TOTAL_COLS=H、HALF_COLS=C、COL_BLOCK_SIZE=B、E/A、GROUP_LIST_TYPE、NUM_CORES=P、SCALE=need_quant、DO_LIMIT与LIMIT。

每program取得R后，n=(R-1)//P+1，处理[pid*n,min((pid+1)*n,R))；begin>=R直接return。合法R>0时为ceil(R/P)连续row段，不是grid-stride。每row先int64(row)*H，load完整H项FP32，再extract两个C项。row地址int64不等于R/分核乘加均有大数guard。R=0不写out，Host仍分配、查询与launch；没有显式空输入短路。

True的B=1024仅当C==2048，其余C固定B=1536；NUM_SUB_BLK=B/32，分别32或48。对每个col_blk_idx=0,B,...，先extract大小B的v，再reshape[B/32,32]、reduce/缩放、payload cast，最后payload store带列<C mask、scale store带组<C/32 mask。**mask仅保护最终GM store，不保护此前extract大小B**：除C=2048专门路线外，C不是1536倍数时，最后slice逻辑范围可能超过v[C]，包括C<1536；Host没有拒绝。源码可见该表达式，但本次未编译，不伪造确定编译错误或特定运行输出。C=2048/B1024完整两片，C为1536倍数也没有这个slice余数问题；其余编译shape/资源前提仍需满足。

无列tail的X整H load、整行v和上述slice构成实际资源域，不能描述成通用masked Htile。没有tl.dot、Cube、atomic、跨核barrier或自有第二Kernel。

## False分支的独立浮点语义

SCALE=False仍计算SiLU前可选clip后的FP32 v，直接store out[row*C+arange(C)]为x.dtype。跳过每32分组、amax、1e-4下限、指数bitcast、FP8转换、B片循环及所有scale写入，因此量化最后slice的风险不传播到False分支。scale仍是未初始化uint8[S,floor(C/32)]，不是E8M0数值也不是可用反量化因子，调用方必须忽略。

False继承group[E]、count窄化、有效前缀和packed storage边界。与旧INT8模块False在DO_LIMIT=False的激活可一致；DO_LIMIT=True时限幅顺序不同，不能替代。没有自动fallback到Torch/native量化入口。

## 逻辑字节账、精度与生命周期

记dx=X元素字节、dg=group元素字节；资源均为逻辑payload，未声称物理UB/寄存器峰值：

| 对象 | 规模与访问 |
|---|---|
| GM X | 名义SH*dx B，前R行读RH*dx B；stride未传入。 |
| GM group | 名义E*dg B；count各P program冗余读E*dg，cumulative各读1项但名义越视图。 |
| True payload | 分配SC B，有效写RC B。 |
| True raw scale/view | 分配S*(C/32) B，有效写R*(C/32) B；view不复制。 |
| False out/scale | 分配SC*dx及S*floor(C/32) B，仅out前R行写；scale全部未写。 |
| 当前row逻辑值 | cur_x FP32为4H B，gate/up/v各4C B；可能为slice/SSA别名。 |
| True量化片 | FP32 blk及q转换前各4B B；amax/m/m2/inv/e等各B/32项、每项4 B，payload B B、scale B/32 B；不能直接相加为活跃峰值。 |
| count逻辑向量 | int32 A项=4A B，masked原dtype读E项。 |

有效True逻辑GM流量RH*dx+RC+R*C/32，加group冗余读取；False为RH*dx+RC*dx再加group。没有请求方workspace、显式UB/L1/L0/queue/event或手工double buffer。multibuffer=True仅编译选项；compiler的寄存器/UB分配、primitive近似与异步流安排是外部边界。

get_device_properties为零参数functools.cache，首次读取当前NPU的AIC/AIV数量并assert两者>0，实际只用AIV。切设备不会自动刷新缓存；不缓存group内容。包导入依赖torch_npu/native共享库。调用方保持X、group、out和scale/view直至当前流消费结束；无自有跨stream、并发修改或任意输入输出alias保护。

## 已有知识与核验

测试源码包含BF16 count两限幅的False、cumulative False、C1536 True与C2048 True，以及scale边界用例。它们是未执行的核验定义；cumulative测试同样受实际GL[E]终点限制，不能用assert文字反证源码地址。候选核验应只消费有效前缀，先确认分组地址/尾slice，再比较FP32激活、逐32指数与payload；不读取empty后缀/False scale。

[旧INT8 A3源码卡](/model/inference/operators/direct/nn/activation/sgl_legacy_swiglu_int8.md)与[旧浮点后限幅Reference](/model/inference/apis/sgl_kernel_npu/sgl_legacy_swiglu_float_postclip.md)使用不同限幅顺序或scale。[native SwiGLU分组量化API](/model/inference/apis/sgl_kernel_npu/sgl_swiglu_group_quant.md)是另一入口与实现，不能把其950范围借给本卡。[SGLang MXFP8 MoE接入](/model/inference/guides/sglang_ascend/sglang_ascend_quant_mxfp8_moe.md)说明调用方布局与集成条件，不替代本Triton Device算法。

## 固定源码

- [python/sgl_kernel_npu/sgl_kernel_npu/activation/swiglu_mxfp8_quant.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/activation/swiglu_mxfp8_quant.py)（primary）。
- [python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py)（implementation）。
- [tests/python/sgl_kernel_npu/test_swiglu_mxfp8_quant.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_swiglu_mxfp8_quant.py)（supporting）。
- [python/sgl_kernel_npu/sgl_kernel_npu/activation/swiglu_quant.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/activation/swiglu_quant.py)（supporting）。
- [python/sgl_kernel_npu/sgl_kernel_npu/__init__.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py)（header）。
