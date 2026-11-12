---
type: API
title: 旧SwiGLU浮点输出与SiLU后限幅接口
description: 说明旧activation.swiglu_quant的need_quant=False数学、有效前缀与未写scale，区分INT8和MXFP8的限幅位置，保留未知平台及实际Host边界。
tags: [task.implementation, topic.compute.elementwise.activation, topic.precision]
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/activation/swiglu_quant.py
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/activation/swiglu_mxfp8_quant.py
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_swiglu_quant.py
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/setup.py
  role: supporting
created_at: "2026-11-09T15:48:41Z"
updated_at: '2026-11-10T07:03:17Z'
platforms: []
---

# 旧SwiGLU浮点输出与SiLU后限幅接口

## 入口与适用范围

本卡固定sgl-kernel-npu提交 `dda6d36b0cdb4081e102d14c0a2fb276fc416e69` 的旧模块，唯一数学为 `need_quant=False`，没有impl分发：

```python
from sgl_kernel_npu.activation.swiglu_quant import swiglu_quant
out, unused_scale = swiglu_quant(
    x, group_list, group_list_type, need_quant=False,
    do_limit=False, limit=7.0,
)
```

平台保持未知草稿：当前活动test_swiglu_quant.py的两个callee都使用默认need_quant=True，只定义BF16 INT8两限幅用例，没有调用本False分支。不能借同函数的A3/950 CI给本卡作产品或CANN版本承诺；本次没有执行编译、数值、真机、graph或性能验证，没有verified。这里完整保存已读自有Host/JIT事实，仍是API Reference，不称完整VV Operator或source_closed。

## 数学、布局与返回值

设X的Host shape为[S,H]，C=floor(H/2)，前C项为gate g、后C项为up u。Device整row先转FP32，计算：

```text
silu = g * sigmoid(g)
do_limit=False: y = silu * u
do_limit=True:  y = min(silu,limit) * max(min(u,limit),−limit)
out = y.to(x.dtype)
```

限幅在SiLU后对gate结果做单边上界，对up做双边±limit，不能与先clip raw gate再SiLU等同；旧MXFP8模块的need_quant=False也先clip gate，两个DO_LIMIT=True数学不同。limit负值/非finite、x NaN/Inf都无完整Host guard，不能推断稳定数值合同。奇H没有被拒绝：只提取[0,C)、[C,2C)，最后一项不参与输出，调用方不应默默丢特征。

| 返回/输入 | 源码布局、类型与写入 |
|---|---|
| x | Host直接解包s,h=x.shape；Device使用row*H+arange(0,H)，无stride形参、不contiguous或reshape。 |
| out | torch.empty([S,C],dtype=x.dtype,device=x.device)，有效前R行写入转换后的FP32激活，不修改x。 |
| unused_scale | torch.empty([S],float32,x.device)始终分配并返回；**SCALE=False从未写任何scale项**，即使row有效也不能消费它。 |
| group_list | 必传、名义[E]，int32/int64；只生产总有效行数，不做expert重排。 |

need_quant=False没有amax/除scale、floor或INT8 clamp，也没有量化分支的1536 extract循环。因此不能把INT8的零scale/1536尾slice边界照搬到本浮点分支。最后到x.dtype的舍入由Triton cast/store primitive决定，源码没有显式RNE/CAST_ROUND参数，不能编造位级保证。

## Host检查、分组与已知读取终点

Host先要求group_list_type为0或1，否则ValueError；再解包X的两个维度、分配out与scale，读取E=group_list.shape[0]，按GL dtype选A。int64取A=ceil(E/8)*8，int32取A=ceil(E/16)*16，其他dtype ValueError；两种实际单元均64字节，注释“32-byte”不改变表达式。没有X dtype/NPU/连续/偶H/正shape断言，也不校验GL rank/非空/设备/连续/数值范围；None会在读取shape/dtype时失败，没有可用None路径。

```text
group_list_type=1:
  gl=load GL[0:A],mask< E,other=0
  R=sum(gl.to(int32))
group_list_type=0:
  R=load(GL[E]).to(int32)          # 名义1D E项之外
```

cumulative并非新版situ/OAI公共API的“读最后有效项E−1”合同：Host把shape0当E后，实际读取GL[E]，在row guard之前就发生。它是源码可见的名义越视图终点，不推定读到何值，也不把继续可见body当安全支持。int64转int32及sum无溢出检查，count R不夹到S；R>S会按R读写分配外，R<S的输出后缀未初始化。

## 实际JIT、分核与地址

实际JIT符号为 `_swiglu_quant_kernel`，装饰器只有@triton.jit，无autotune/显式warp/stage。Host用get_device_properties()[1]得到Cores，以grid=(Cores,)启动，SCALE=False、DO_LIMIT与LIMIT为constexpr，multibuffer=True。其余constexpr为TOTAL_COLS=H、HALF_COLS=C、COL_BLOCK_SIZE=1536（本False分支不消费）、E/A、GROUP_LIST_TYPE与DTYPE_MAX=127（本False分支不消费）；四GM参数仍全部传入。

```text
# 源码等价伪码；以group读取成功、0<=R<=S且row*H/row*C及lane加法均处于有符号int32可表示域为条件
rows=(R−1)//Cores+1
begin=pid*rows
if begin>=R:return
end=min((pid+1)*rows,R)
for row in [begin,end):
  cur=load X[row*H+arange(H)].to(float32)
  g=extract(cur,0,C);u=extract(cur,C,C)
  y=(DO_LIMIT?min(g*sigmoid(g),L)*clip(u,−L,L):g*sigmoid(g)*u)
  store out[row*C+arange(C)] = y.to(out.dtype)
# scale_ptr完全未写；没有1536片循环
```

行号与row*H、row*C未先转int64，乘法和最终线性元素偏移须处于有符号int32可表示域；0<=R<=S只约束行数，不保护地址溢出。合法R>0且上述地址前提成立时rows=ceil(R/Cores)，每program处理连续row段，尾program可直接return，不是grid-stride；不同program写域不重叠，没有atomic/barrier。R=0时不写out，Host仍分配和查询设备属性，没有空输入短路；X为空但R>0不受保护。没有显式POD/UB参数、workspace或第二Kernel。

## 逻辑资源、精度与生命周期

| 对象 | 容量/逻辑payload | producer→consumer及边界 |
|---|---|---|
| GM X | S*H*e(X) B；有效row读H项 | 调用方→FP32 cur_x；没有stride处理。 |
| GM group | E*e(GL) B；count每program冗余读E项 | 调用方→int32 sum；cumulative名义超视图读取。 |
| GM out | S*C*e(X) B，前R行写 | FP32激活→目标dtype新存储，后缀未初始化。 |
| GM scale | 4*S B，全部未写 | Host empty占位；调用方必须丢弃，不能反量化。 |
| program逻辑值 | cur_x4H B，gate/up/y各4C B，count转换4A B | 当前row SSA/slice；别名/融合/活跃峰值由compiler决定。 |

multibuffer=True是编译选项，不能据此声称有两个手工UB buffer或把逻辑数组总量当确定物理UB/寄存器峰值。全程FP32激活，最后转回x.dtype；不存在量化scale精度、epsilon下限或分组scale布局。调用方需保持X/GL/out到当前流消费结束，无自有跨stream/alias保护。

get_device_properties是无参数functools.cache，读当前NPU的AIC/AIV核数并要求两者>0；只使用Vector核数但AIC检查仍发生。cache不含device，切设备不自动刷新，GL内容本身并未缓存。包导入还要torch_npu和libsgl_kernel_npu.so，不能把本页当无需NPU环境的独立CPU实现。

## 复用、核验与相关知识

比较只取count合法且int32线性地址计算不溢出的前缀out，保留FP32 SiLU后clip与输出dtype舍入；不比较未写后缀或任何unused_scale。应分别确认DO_LIMIT两路线、limit边界、GL count和cumulative故障终点、非连续输入的线性寻址与空域；上述为可执行核验方向，本次均未执行。没有把Source可见缺陷说成依赖缺失，也不因平台未知丢弃已读算法。

[同源逐行INT8 A3源码卡](/model/inference/operators/direct/nn/activation/sgl_legacy_swiglu_int8.md)与[950源码卡](/model/inference/operators/direct/nn/activation/sgl_legacy_swiglu_int8_950.md)保存True分支；这些平台标签不传播到本False分支。[专家激活限幅与融合守卫](/model/inference/optimizations/sglang_ascend/sglang_ascend_moe_activation_fusion.md)是固定SGLang调用方集成证据，与本kernel commit分开，不替代自有Device算法或平台依据。

## 固定源码

- [python/sgl_kernel_npu/sgl_kernel_npu/activation/swiglu_quant.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/activation/swiglu_quant.py)（primary）。
- [python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py)（implementation）。
- [python/sgl_kernel_npu/sgl_kernel_npu/activation/swiglu_mxfp8_quant.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/activation/swiglu_mxfp8_quant.py)（supporting）。
- [tests/python/sgl_kernel_npu/test_swiglu_quant.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_swiglu_quant.py)（supporting）。
- [python/sgl_kernel_npu/sgl_kernel_npu/__init__.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py)（header）。
- [python/sgl_kernel_npu/setup.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/setup.py)（supporting）。
