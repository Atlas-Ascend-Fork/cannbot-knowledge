---
type: API
title: 旧路由专家缩放与共享专家相加接口
description: 保存旧MoE routed乘常数再加shared的Host与Triton grid-stride实现，明确packed寻址、尾块、精度和未知平台边界。
tags: [task.implementation, topic.mixture_of_experts, topic.precision]
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/moe/mul_add.py
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py
  role: header
created_at: "2026-11-09T16:00:55Z"
updated_at: "2026-11-09T16:00:55Z"
platforms: []
---

# 旧路由专家缩放与共享专家相加接口

## 入口与数学

固定sgl-kernel-npu提交 `dda6d36b0cdb4081e102d14c0a2fb276fc416e69` 的旧模块：

```python
from sgl_kernel_npu.moe.mul_add import mul_add
output = mul_add(routed_input, shared_input, scaling_factor)
```

对合法packed二维同shape输入[B,D]，逐元素计算 `output[b,d]=routed_input[b,d]*scaling_factor+shared_input[b,d]`。scaling只施于routed，shared不再乘同一factor；没有sigmoid gate、expert归约、通信或原地累加。输出新分配[B,D]，dtype/device随routed_input，返回单个Tensor，不修改两输入。

保留为未知平台的draft API Reference，不猜CANN版本或承诺完整Operator/source_closed。现有乘加primitive/GroupedMatmulAdd同名检索结果不是本MoE入口；[Qwen shared overlap集成](/model/inference/optimizations/sglang_ascend/sglang_ascend_model_qwen_moe_shared_overlap.md)讲调用方双流/gate责任，不包含本旧JIT。该集成来源及其他API的产品范围不传播到此卡。本次没有执行上游、编译、真机或性能验证。

## Host与参数

Host先调用get_device_properties取得P=AIV核数，再读取routed_input.shape[0]/[1]为B/D，T=next_power_of_2(D)，G=min(B,P)，empty分配输出，launch grid=(G,1,1)。没有autotune、空输入短路、参数校验、reshape/contiguous或stride传参。第二输入shape/dtype/device、scaling_factor类型/finite以及routed rank2/正D均未被显式验证。

数学合同要求两输入实际packed[B,D]且GM地址有效。Host不提供Torch式广播；shared_input[B,1]或不同shape不会自动扩展。rank>2仍只使用前两shape并返回二维输出，不能当保留任意前缀shape。B=0时G=0仍提交launch表达式，本次未执行，不能宣称框架接受该空grid。D与T还受Triton shape和资源限制。地址乘加没有源码显式int64提升或大shape guard，不能用Host Python整数掩盖Device索引宽度边界。

| JIT参数 | 分类/消费 |
|---|---|
| input1_ptr/input2_ptr/output_ptr | runtime GM routed/shared/new output |
| factor | tl.constexpr，乘routed；不同factor可形成不同编译specialization |
| batch_size/hidden_size | constexpr B/D，row循环和mask/地址 |
| BLOCK_SIZE | constexpr T，POT列向量 |

唯一Device为@triton.jit `mul_add_kernel`；没有自有POD序列化、workspace参数或第二Kernel。

## 分核、地址与尾块

```text
p=program_id(0)
G=num_programs(0)
cols=arange(T); mask=cols<D
off=p*D+cols
for row in range(p,B,G):
    r=load(input1+off,mask,other=0)
    s=load(input2+off,mask,other=0)
    store(output+row*D+cols,r*factor+s,mask)
    off += G*D
```

B>0、P>0时G>=1，每program按row grid-stride推进；input offset也每轮递增G*D，后续row不重复读首row。每真实row恰有一个program负责，P限制grid不限制覆盖行数。D的非POT尾在两load和store上同mask，invalidlane填0，只是真实D列有GM访问。没有group有效前缀/未写真实row；合法域内输出全写。

load后无显式.to(float32)，没有独立精度开关。实际输入dtype、constexpr factor与Triton promotion决定中间算术，compiler可融合乘加，store转换为output/routed dtype；不能声称固定FP32累积、统一舍入模式或与分开的Torch mul/add逐bit一致。不同dtype、NaN/Inf和极端factor未设Host guard。

## 逻辑资源与同步

| 对象 | 逻辑字节/生命周期 |
|---|---|
| routed | 名义B*D*e_r B，每有效元素读一次 |
| shared | 名义B*D*e_s B，每有效元素读一次；无自动broadcast |
| output | 新分配B*D*e_r B，每有效元素写一次 |
| 当前row r/s | 各T元素，原dtype逻辑payload T*e_r及T*e_s |
| 当前row计算值 | T元素，大小随promotion，可能与输入SSA复用 |
| 列/地址/mask | T lane逻辑索引/布尔，物理压缩/寄存器分配由compiler决定 |

合法有效GM总流量BD*(2e_r+e_s) B。没有显式UB/L1/L0分配、queue/event、请求方workspace、atomic、跨核barrier或通信；局部load→算术→store由Triton保序，物理UB/寄存器峰值不可由逻辑张量求和确定。行独立允许避免全局同步，但不构成跨stream依赖保证。

get_device_properties为零参数functools.cache，首次读取当前NPU的AIC/AIV核数并assert两者>0，此处只用AIV；切设备后不自动刷新P。旧P仍被min(B,P)用于grid，合法G>0时grid-stride保持行覆盖，不能无条件说缓存导致漏行。没有输入数据缓存。包导入依赖torch_npu/native共享库；输入/输出storage需存活到当前流完成，无自有hostwait、并发修改或alias防护。

## 核验方向与固定源码

可在合法shape/dtype/packed域比较routed*factor+shared，分别检查G<B的多轮row推进、D非POT尾和factor为0/1及非整数时的精度边界；不得把shared预缩放或gate数学混入参考。上述为未执行的核验方向，平台/编译资源证据仍未知。

- [python/sgl_kernel_npu/sgl_kernel_npu/moe/mul_add.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/moe/mul_add.py)（primary）。
- [python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py)（implementation）。
- [python/sgl_kernel_npu/sgl_kernel_npu/__init__.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py)（header）。
