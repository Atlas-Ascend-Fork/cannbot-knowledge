---
type: API
title: 旧SiTU逐行INT8与可选浮点接口
description: 保存旧SiTU两个wrapper的逐行INT8公式、浮点分支和Host失败域，明确累计group越视图读取、有效前缀、整行资源及未知平台边界。
tags: [task.implementation, topic.compute.elementwise.activation, topic.precision]
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/activation/situ.py
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_situ_mxfp8_quant.py
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py
  role: header
created_at: "2026-11-09T15:55:51Z"
updated_at: "2026-11-09T15:55:51Z"
platforms: []
---

# 旧SiTU逐行INT8与可选浮点接口

## 范围与入口

本卡固定sgl-kernel-npu提交 `dda6d36b0cdb4081e102d14c0a2fb276fc416e69` 的旧 `activation/situ.py`。两个实际Host入口共享SiTU公式，但参数、shape处理、失败域和浮点返回不同：

```python
from sgl_kernel_npu.activation.situ import situ_and_mul_quant, situ
q, scale = situ_and_mul_quant(
    x, group_list=None, group_list_type=None,
    beta=4.0, linear_beta=25.0, need_quant=True, quant_type=0,
)
q, scale = situ(
    hidden_states, group_list, group_list_type,
    need_quant=True, beta=4.0, linear_beta=25.0,
)
```

平台保持未知的draft API Reference，未声明CANN版本、source_closed或完整VV Operator。已有新版浮点SiTU卡与native MXFP8卡不是本INT8实现。测试文件test_situ_mxfp8_quant.py的主测试调用另一个AscendC MXFP8入口；这里只在benchmark baseline看到旧situ(...,need_quant=False)。文件“A5-only”描述不能提升为本INT8分支的平台证据。本次没有执行上游、编译、数值、真机或性能验证。

## 数学与量化顺序

设X为线性packed的[S,2C]，前半为gate g、后半为up u。载入后都转FP32：

```text
a = beta * tanh(g / beta) * sigmoid(g)
u1 = up                               if linear_beta is None
u1 = linear_beta * tanh(up/linear_beta) otherwise
v = a * u1
s = max(max_c(abs(v[c])) / 127, 1e-30)
q[c] = int8(clamp(floor(v[c]/s + 0.5), -128, 127))
```

这是soft saturation，不是硬clip。gate仍以原始g计算sigmoid；不能把它换成sigmoid(beta*tanh(...))。s是逐有效row的FP32标量，量化采用floor(z+0.5)，负半整数的行为不能描述成统一round-to-nearest-even。有限全零v产生正scale下限和q=0；与旧SwiGLU INT8没有epsilon的零scale不同。NaN/Inf、极端beta等没有完整Host数值guard，primitive的近似、融合、NaN传播与最终转换也不能外推为位级保证。

### 两个Host的实际合同

| 项 | situ_and_mul_quant | situ |
|---|---|---|
| 输入shape | 接受末维偶数的X，reshape(-1,last_dim)；输出恢复原前缀shape+C | 必须rank2且第二维偶数；输出[S,C] |
| group | 可None，None时处理S行，忽略group_list_type | 必传；直接访问dtype、numel，没有None路径 |
| group_list_type | 有group时要求0/1 | 总是要求0/1 |
| E | group.shape[0] | group.numel() |
| INT8选择 | need_quant且quant_type=0且C<=6144才launch | need_quant=True即launch，无C<=6144的Host限制 |
| 浮点选择 | need_quant=False或C>6144最终抛NotImplementedError；注释掉的浮点launch不执行 | need_quant=False实际执行浮点body，返回(out,None) |
| quant_type | 非0/1先ValueError；need_quant且1先NotImplementedError | 无此参数 |
| scale | 成功INT8返回float32[S] | 总分配float32[S]；True返回，False不写且返回None |

第一Host的docstring称“大C/False自动浮点fallback”，正文实际在else直接抛错；不能据docstring给调用者承诺回退。该失败发生前可能已reshape、分配out/scale及查询设备。其量化注释列C=3072/6144，但真实Host只判断C<=6144；该比较不保证任意小C都满足Triton arange/slice、编译资源等条件。第二Host虽无宽度上限，也不能据此承诺任意C可编译。

两Host只对group dtype支持int32/int64：int64取A=ceil(E/8)*8，int32取A=ceil(E/16)*16，即均按64字节元素数对齐。A不是next_power_of_2；源码未检查其是否满足编译器向量shape要求。均不验证group rank、连续、设备、非空、数值范围，不验证X dtype、NPU、stride或input/group设备一致。第一Host的reshape可能产生copy，也可能保留可view的行间padding，随后无.contiguous；第二Host直接传原tensor。Device不收stride，因此只在实际storage符合packed线性寻址时有该公式合同，不能推广到任意Torch view。

beta默认4、linear_beta默认25；None关闭up饱和。第一Host直接传beta并在Python算倒数，第二Host先float转换再算倒数。普通数值beta=0或启用的linear_beta=0会在构造launch参数时除零，而不是Device得到某个稳定输出；负数与非finite未被拒绝。两Host都没有显式空输入短路或新版大N调度上限检查，shape/reshape/编译的前置要求仍须满足。

## 分组、前缀与已知越视图读取

分组仅控制总有效row数，不做expert重排，也不按每个expert分别量化。实际两个JIT都执行：

```text
count(type=1): R=sum(load(group[0:A],mask=index<E,other=0).to(int32))
cumulative(type=0): R=load(group[E]).to(int32)
dense(仅situ_and_mul_quant): R=S
```

名义1D E项group的cumulative读取是[E]，不是最后有效项[E-1]；读取在row early-return之前。它是源码可见的名义越视图终点，不能推定实际读值，也不能把“仍有可见后续body”写成安全支持。较大底层storage不改变API名义shape及Host传E的事实。多维group在两Host的E定义还不同，均没有stride合同。

count的int64先窄化int32再求和，R无非负/溢出/<=S检查。合法count条件需各项及和可用int32表达且0<=R<=S；R>S会使后续按R读写分配外，R<S只写前R行，out与返回scale的[S-R]后缀仍为empty未初始化。不能比较或反量化这些后缀。R=0时body不写有效row；Host仍有分配与设备查询，不能把它写成无启动成本的空返回。

## 实际JIT图、参数与地址

成功INT8为单JIT launch：第一Host→`_situ_and_mul_quant_kernel`，第二Host→`_situ_kernel`。二者只见Vector式load、FP32 tanh/sigmoid、reduce、extract与store，无tl.dot、Cube、自有通信Kernel或第二阶段。两者固定grid=(P,)，P=get_device_properties()[1]，multibuffer=True，没有autotune；同文件独立浮点situ_and_mul的四候选autotune不应套到这两个整行JIT。

| 参数族 | 第一JIT | 第二JIT |
|---|---|---|
| GM | x_ptr/group_list_ptr/out_ptr/scale_ptr | 同四ptr |
| 列 | TOTAL_COLS=2C,HALF_COLS=C,COL_BLOCK_SIZE=C | 相同 |
| group | NUM_EXPERTS=E,NUM_EXPERTS_ALGIN=A,GROUP_LIST_TYPE,HAS_GROUP_LIST | NUM_EXPERTS=E,NUM_EXPERTS_ALIGNED=A,GROUP_LIST_TYPE，无None开关 |
| 行/核 | N_ROWS=S运行时值，NUM_CORES=P | 无N_ROWS，R必由group得到；NUM_CORES=P |
| SiTU | BETA,INV_BETA,DO_LINEAR_BETA,LINEAR_BETA,INV_LINEAR_BETA | 同 |
| 量化 | SCALE=True,DTYPE_MAX=127 | NEED_QUANT=True，127为body常量 |

以下伪码以group读取成功、shape/编译前提满足及合法R为条件，不跨越前述失败终点：

```text
n=(R-1)//P+1
begin=pid*n
if begin>=R:return
end=min(begin+n,R)
for row in [begin,end):
    c=arange(0,C)
    off=int64(row)*2C
    gate=load(X+off+c).float32
    up=load(X+off+C+c).float32
    v=SiTU(gate,up,beta,linear_beta)
    s=max(max(abs(v))/127,1e-30)
    store(scale+int64(row),s)
    block=extract_slice(v,offset=0,size=C,stride=1)
    q=clamp(floor(block/s+0.5),-128,127).int8
    store(out+int64(row)*C+c,q,mask=c<C)
```

R>0时n=ceil(R/P)，各program连续row区间不重叠，尾核early-return；不是grid-stride。row地址先转int64，避免row*2C保留int32，但R和调度的乘加仍无显式溢出guard。整行load没有列mask，依赖C本身是合法向量shape；Host将COL_BLOCK_SIZE=C，非零合法C时循环只有一个完整row slice。不能复制旧SwiGLU“固定1536最后slice越逻辑vector”的问题到这里。

## situ的浮点False分支

`situ(...,need_quant=False)`仍经过相同group读取、分核、FP32整行SiTU和参数倒数计算，但跳过amax、scale store、extract/floor/clamp/INT8转换，直接将v cast到hidden_states.dtype后存[S,C]前R行。Host仍分配4S字节scale，Device完全不写，返回值第二项为None；调用者没有可用scale。该分支同样继承cumulative[E]、packed寻址和count有效前缀边界。

这与同文件`situ_and_mul`的Htile浮点body数学相同，但整行资源、group E定义及Host合同不同；也与`situ_and_mul_quant(...,need_quant=False)`的NotImplementedError终点不同，不可互相当自动alias。最终cast的舍入由Triton primitive确定，源中没有显式RNE模式。

## 逻辑资源、同步与生命周期

记e为X元素字节、dg为group元素字节。以下是逻辑payload与访问量，不是编译器物理UB峰值：

| 对象 | 字节与有效域 | 生命周期 |
|---|---|---|
| X | storage名义2SCe；有效row逻辑读2RCe | 调用方保持至当前流Kernel完成；reshape可能另有Torch临时 |
| group | 名义E*dg；count每个program读E*dg，累计总P*E*dg；cumulative每program读dg但名义地址越视图 | 全P核先读group再row early-return；无Host内容拷贝/校验 |
| INT8 out | 新分配SC B，写RC B | 前R行可消费；后缀未写；不原地改X |
| FP32 scale | 新分配4S B，INT8写4R B；False全未写 | True可反量化有效前缀；False不返回 |
| 浮点out | 新分配SCe B，写RCe B | 仅situ False；输入dtype输出 |
| program逻辑值 | gate/up/a/v各4C B，量化block FP32为4C B、INT8为C B、scale4 B；count转换4A B | 当前row SSA/slice，可别名/融合，不能简单求和为峰值 |

有效INT8逻辑GM流量为2RCe+RC+4R，再加group读取；False为3RCe再加group。没有申请自有workspace、手工UB/L1/L0、queue/event、atomic或跨核barrier；各row局部reduce与SSA依赖由Triton/compiler安排。multibuffer=True不是手工双buffer证明。整行tanh/reduce与full-C量化使逻辑资源随C增大，源码“fits UB”注释不能替代物理分配或实测。

get_device_properties为零参数functools.cache，首次读取当前NPU的AIC/AIV核数并assert两者>0；这里只用AIV数，但AIC检查仍执行。cache不含device key，切设备后不自动更新P；不是对group内容或X的缓存。包导入依赖torch_npu及native共享库；Torch allocation/reshape、CANN Triton primitive、编译器和当前流调度为外部边界，未把它们伪造成自有源码闭合。调用者保持输入、group、输出/scale与潜在reshape临时到异步消费结束；没有自有跨stream、alias或并发修改保护。

## 复用与核验边界

同合法count输入、相同FP32参数和packed storage下，两INT8 wrapper的公式可比较；分别覆盖linear_beta=None/启用、零行/零值、有效前缀、不同group dtype及Host异常。cumulative[E]应当作为静态边界检查，不能从未确定读取值编造数值故障轨迹。所有核验方向均未在本次执行。

[新版公开浮点SiTU API](/model/inference/apis/sgl_kernel_npu/sgl_situ_and_mul.md)与[浮点Device源码卡](/model/inference/operators/direct/nn/activation/sgl_situ_and_mul.md)采用不同Host和cumulative最后项寻址，不覆盖这里的INT8/旧GL[E]事实。[native SiTU MXFP8接口](/model/inference/apis/sgl_kernel_npu/sgl_situ_mxfp8_quant.md)输出E4M3/E8M0，另含BF16舍入，不是本逐行INT8路线。[旧SwiGLU浮点接口](/model/inference/apis/sgl_kernel_npu/sgl_legacy_swiglu_float_postclip.md)的硬限幅也不是SiTU soft saturation。

## 固定源码

- [python/sgl_kernel_npu/sgl_kernel_npu/activation/situ.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/activation/situ.py)（primary）。
- [python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py)（implementation）。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/situ_and_mul.py)（supporting）。
- [tests/python/sgl_kernel_npu/test_situ_mxfp8_quant.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_situ_mxfp8_quant.py)（supporting）。
- [python/sgl_kernel_npu/sgl_kernel_npu/__init__.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py)（header）。
