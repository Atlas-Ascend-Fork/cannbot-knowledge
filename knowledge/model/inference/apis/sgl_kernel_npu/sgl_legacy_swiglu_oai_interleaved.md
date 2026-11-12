---
type: API
title: 旧OAI交错布局门控激活接口
description: 保存旧OAI偶奇交错gate与up、16行Triton分块及layer包装，区分新版分半布局，保留空输入、精度与未知平台边界。
tags: [task.implementation, topic.compute.elementwise.activation, topic.precision]
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/activation/swiglu_oai.py
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/swiglu_oai_quant.py
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py
  role: header
created_at: "2026-11-09T15:59:37Z"
updated_at: "2026-11-09T15:59:37Z"
platforms: []
---

# 旧OAI交错布局门控激活接口

## 范围与入口

固定sgl-kernel-npu提交 `dda6d36b0cdb4081e102d14c0a2fb276fc416e69` 的旧 `activation/swiglu_oai.py`，保存自有Triton body、layer适配和显式Torch对照。平台未知，保持draft API Reference与空平台，不猜CANN版本，不声称source_closed或完整Operator；本次没有执行编译、测试、真机或性能验证。

```python
from sgl_kernel_npu.activation.swiglu_oai import (
    swiglu_oai_triton, swiglu_oai, swiglu_oai_native,
)
out = swiglu_oai_triton(hidden_states, dim, gemm1_alpha, gemm1_clamp_limit)
out = swiglu_oai(layer, hidden_states)
reference = swiglu_oai_native(layer, hidden_states)
```

三个入口没有impl registry、自动回退、量化或group_list。swiglu_oai直接调用swiglu_oai_triton，dim=layer.w13_weight.shape[2]，alpha/limit来自layer.moe_runner_config.gemm1_alpha与gemm1_clamp_limit；不会读取weight值或执行GEMM。native是调用者显式选择的Torch数学对照，不是本Triton的失败fallback。

## 交错布局与数学

令view后的输入[B,N]，N=dim，D=floor(N/2)。合法偶N与packed storage下：

```text
g[b,c]=X[b,2c]       # 偶列
u[b,c]=X[b,2c+1]     # 奇列
g1=where(g>L,L,g)
u1=where(u>L,L,u)
u2=where(u1<−L,−L,u1)
sig=1/(1+exp(−g1*alpha))
y=(u2+1)*g1*sig
```

gate只限上界，up双边±L，gate经过alpha sigmoid，up有+1。它不是普通SiLU(g)*u，也不是把输入前半/后半当gate/up。clip用tl.where显式比较，非finite比较/exp行为不能由有限实数公式概括。

Triton load后没有.to(float32)，alpha/limit也不由Host强制float转换；中间promotion、exp近似、融合和store到输入dtype的舍入由实际Triton标量类型与compiler决定。不能补造“先全转FP32”或位级与Torch一致的保证。Host不检查alpha/limit的finite、正值或可表示范围；负limit的两次where顺序亦不等于合法区间裁剪。

## Host、shape与失败边界

Host先hidden_states.view(-1,dim)，故需总元素可按dim分组、view可成立，随后分配同dtype/device的empty([B,D])并返回二维输出；不会恢复输入原来的前导shape。没有.contiguous、stride参数、dtype/NPU/偶dim/正宽度/finite检查。view成功本身不保证实际storage符合Kernel线性packed地址，任意行padding或列stride不可直接套用。

Kernel行步长写成2D，而view行步长假定N。若N为奇数，2D=N-1，第二行及以后会按更短步长访问，不能只描述成“每行丢最后一列”；Host未拒绝该域。调用方应使用正偶dim和实际packed storage。维度不合法、view失败、缺少layer属性等会在Host处结束，不存在自动纠正。

```text
K=get_device_properties()[0]       # AIC数量，非返回的AIV数量
M=16
BLOCK_SIZE=ceil(B/(M*K))*M
BLOCK_NUM=ceil(B/BLOCK_SIZE)
launch grid=(BLOCK_NUM,)
```

合法B>0、K>0时BLOCK_SIZE是16倍数，BLOCK_NUM<=K。B=0时BLOCK_SIZE=0，随后cdiv(B,BLOCK_SIZE)有零除Host终点，未做新版空输入直接返回。当前设备由外部调用方选择，Host不把它设为输入device。没有显式大B地址/调度整数溢出guard。

## 实际JIT参数与数据流

唯一自有Device符号为 `swiglu_oai_kernel`，@triton.jit，无autotune/显式multibuffer选项：

| 参数 | 类型/用途 |
|---|---|
| hidden_states/gated_output | runtime输入/新输出GM指针 |
| gemm1_alpha/gemm1_clamp_limit | runtime数学标量，非tl.constexpr |
| output_dim | constexpr D，列arange、行步长与store |
| BLOCK_SIZE | constexpr每program行跨度，16倍数 |
| MINIBLOCK_SIZE | constexpr16 |
| BS | constexpr B，row mask |

```text
for i in range(0,BLOCK_SIZE,16):
    rows=pid*BLOCK_SIZE+i+arange(16)
    m=rows<B
    cols=arange(D)
    g=load(X+rows[:,None]*2D+2*cols[None,:], mask=m[:,None])
    u=load(X+rows[:,None]*2D+2*cols[None,:]+1, mask=m[:,None])
    y=OAI_where_clip_exp(g,u,alpha,limit)
    store(out+rows[:,None]*D+cols[None,:],y,mask=m[:,None])
```

load没有other值，masked虚行不定义中间值，但最终store同row mask，不要求这些虚行产生数值。列没有tail mask/next_power_of_2 padding，D直接为arange上界，需满足当前CANN Triton shape与资源准入；不能据无Host宽度guard承诺任意D可编译。最后miniblock仅row mask，合法域内各program/row输出互不重叠。没有有效前缀group或未写真实row，只有最后miniblock的虚行被屏蔽。

该body无tl.dot、Cube、跨核通信或MIX；get_device_properties()[0]用AIC数分配program数量，不把向量数学变成Cube实现，也不能用它推导产品支持。

## Torch native对照

swiglu_oai_native先解包E,_,N=layer.w13_weight.size()，同样view(-1,N)，取[...,::2]与[...,1::2]，调用Torch clamp、sigmoid与乘加，返回二维激活；E及weight数据不参与计算。它是外部Torch primitive组合，没有本仓自有Device闭包或固定Kernel/物理资源保证。其数学适用于合法偶N，shape/rank、dtypepromotion、clamp/exp近似及舍入可与Triton有差别；不能从公式相同声称逐bit相同。旧layer包装不检查输入末维是否与weight第3维一致，只由view约束总元素，可能改变调用者预期的行分组。

## 资源、同步与生命周期

记dx为输入元素字节，d算术为实际promotion后的中间元素字节；以下不是确定物理UB峰值：

| 对象 | 字节/访问 |
|---|---|
| GM输入 | 合法packed [B,2D]，容量2BD*dx B，有效读同量 |
| GM输出 | 新分配[B,D]，BD*dx B，全真实row写入 |
| 一miniblock gate/up | 各16D元素，原始load逻辑16D*dx B |
| 中间gate/up/sig/glu/out | 各16D元素，字节随promotion；compiler可复用/融合 |
| 元数据 | 无group、scale、workspace或辅助GM |
| 虚行 | 最后不足16行的load/store按row mask抑制GM访问 |

有效payload总流量3BD*dx B，没有请求方workspace、显式UB/L1/L0 buffer、queue/event或atomic/barrier。单Kernel内每行独立，局部依赖由Triton compiler保序；16行整宽SSA可能随D增长，源码没有UB容量查询。没有自行hostwait、跨stream依赖、alias保护或state mutation；保持输入与输出直至当前流异步消费结束，view由框架保持原storage生命周期。

get_device_properties为零参数functools.cache，首次读取当前device的AIC/AIV数量并assert两者>0；cache不含device，切设备不自动刷新K，可能改变launch分块与性能。该算法grid仍按B覆盖合法行，不能无条件把缓存旧核数说成漏行。包导入依赖torch_npu/native共享库，非纯CPU standalone实现。

## 与既有卡的复用边界

[新版SwiGLU-OAI API](/model/inference/apis/sgl_kernel_npu/sgl_swiglu_oai_quant.md)和[新版浮点Device卡](/model/inference/operators/direct/nn/activation/sgl_swiglu_oai_float.md)使用分半布局、可选group、reshape/contiguous及AIV persistent分行；这里是交错布局、16行miniblock、AIC计数grid，不是同ABI别名。输入重新排列后才能比较合法有限值的数学，仍需单独处理精度、shape与空输入边界，不能把新卡A2/A3/950标签传播过来。

[SGLang GPT-OSS/Grok接入](/model/inference/guides/sglang_ascend/sglang_ascend_model_gptoss_grok_router_semantics.md)与[MiniMax接入](/model/inference/guides/sglang_ascend/sglang_ascend_model_minimax_qk_oai.md)属于另一固定来源的调用方上下文，不替代本旧Kernel的平台证据。候选核验包括交错输入、miniblock尾、包装属性/view、alpha/limit数值与dtype转换；本次均未执行。

## 固定源码

- [python/sgl_kernel_npu/sgl_kernel_npu/activation/swiglu_oai.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/activation/swiglu_oai.py)（primary）。
- [python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py)（implementation）。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/swiglu_oai_quant.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/activation/swiglu_oai_quant.py)（supporting）。
- [python/sgl_kernel_npu/sgl_kernel_npu/__init__.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py)（header）。
