---
type: API
title: 旧零专家恒等贡献与路由元数据改写接口
description: 保存旧零专家权重求和乘hidden的Triton实现及scale与index原地改写，明确全masked首项、布局资源和未知平台边界。
tags: [task.implementation, topic.mixture_of_experts, topic.precision]
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/moe/zero_experts_compute_identity.py
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py
  role: header
created_at: "2026-11-09T16:02:27Z"
updated_at: "2026-11-09T16:02:27Z"
platforms: []
---

# 旧零专家恒等贡献与路由元数据改写接口

## 入口、状态与范围

```python
from sgl_kernel_npu.moe.zero_experts_compute_identity import (
    zero_experts_compute_identity_triton,
)
zero_result = zero_experts_compute_identity_triton(
    expert_indices, expert_scales, num_experts, zero_expert_type,
    hidden_states, identity_mask_value=0,
)
```

固定sgl-kernel-npu提交 `dda6d36b0cdb4081e102d14c0a2fb276fc416e69`。本入口计算被编码为零/恒等专家的加权hidden贡献，同时**原地改写**expert_indices与expert_scales；不执行真实专家MLP、GMM或MoE最终加和。zero_expert_type只在Host签名中出现，注释说应为identity，实际没有检查、传入JIT或分派；传其它值不会切换算法。

缺少本唯一入口的明确产品/活动CI支持证据，保存为draft API Reference、platforms=[]，不猜CANN版本或称完整Operator/source_closed。本次没有执行编译、测试、真机或性能验证；“TODO支持prefill”的注释不构成可用产品范围。

## 数学、掩码与副作用

以packed hidden[S,D]、indices/scales[S,K]为数学布局。对token s，先读取整K个旧indices，令m[k]=(idx[k]>=num_experts)，只在m位置读取旧scale，其余lane填0：

```text
w = sum_k(where(m[k], old_scale[k], 0))
zero_result[s,d] = hidden_states[s,d] * w
new_scale[k] = 0                        if m[k] else old_scale[k]
new_index[k] = identity_mask_value      if m[k] else old_index[k]
if all(m):
    new_index[0] = 0
```

all(m)时第0项强制0，其余masked项为identity_mask_value；不是“所有零专家保留原idx”，也不是只有全masked时才置零scale。正常专家项完全不写，索引负值不满足idx>=num_experts、不会被该算法纠正。恒等贡献的w由**改写前**scale求得；返回Tensor不等于完整MoE结果，实际专家贡献仍由别处计算和合并。第二次对已改写元数据调用不能重建原来的权重和，不能当无副作用/可重复读取的接口。

identity_tensor在JIT中显式为int32，之后store到indices元素类型；identity_mask_value若超int32域没有Host guard，不能借int64目标宣称完整int64保值。sum_scales、乘法与store没有源码显式FP32 cast或固定舍入选择，实际reduce提升、输入dtype promotion及转换归Triton primitive/compiler；没有finite、非负scale或归一化要求的检查。真实算式仍依赖输入数值，不能一概称结果无误差。

## Host参数、shape与检查缺口

Host直接S,D=hidden_states.shape，K=expert_indices.shape[1]，BD=min(65536,ceil(D/32)*32)，NBD=ceil(D/BD)，zero_result=torch.empty_like(hidden_states)，grid=[S]。没有autotune、核数helper或任何dtype/device/shape/value断言；expert_scales的shape不参与选择。实际数学前提是三输入对应行数、K一致、storage有效且同设备，indices/scales可写，hidden和输出实际packed地址符合下面的线性索引。

没有.contiguous、reshape或stride参数；empty_like还可能继承非默认memory format，不能将任意非连续hidden/output当packed写入。Host的S,D解包隐含rank2，indices至少有第二维，但不提供高级广播/补齐。D=0使BD=0，再算cdiv(D,BD)有Host零除终点；S=0仍形成零grid launch，源码无空输入短路。K直接作为arange长度，没有POT补齐/空K guard，BD只是32倍数，未必POT；65536上限和对齐注释不保证所有shape满足当前CANN Triton编译/资源准入。缺少实际编译证据时不编造确定失败。

## 单JIT执行、参数与地址

唯一Device为@triton.jit `experts_compute_identity_kernel`，四runtime GM ptr为indices/scales/hidden/zero_result，六constexpr为num_experts、D、NBD、BD、K、identity_mask_value。无独立POD结构、workspace、第二Kernel或外部核心数学callee。

```text
s=program_id(0)
k=arange(K)
idx=load(indices+s*K+k)                  # 无K mask
m=idx>=num_experts
weights=load(scales+s*K+k,mask=m,other=0)
w=sum(weights)
replacement=full(K,mask_value,int32)
if sum(~m)==0: replacement=where(k==0,0,replacement)
for tile in range(NBD):
    d=tile*BD+arange(BD); mask=d<D
    h=load(hidden+s*D+d,mask=mask)       # masked lane无other值
    store(result+s*D+d,h*w,mask=mask)
store(scales+s*K+k,zeros(K),mask=m)
store(indices+s*K+k,replacement,mask=m)
```

每program负责一个token，无grid-stride；合法packed行互不重叠。D>0时NBD覆盖所有D列，最后tile load/store都有d<D mask；masked虚列虽无other值，其store也被抑制。K域整vector无mask，需indices真实K项可读，scale只读写被选中项。没有tl.dot、Cube或自有通信；Vector数学不等于已知平台支持。

## 资源、同步与生命周期

记e_h/e_s/e_i为三个输入元素字节、M为全部token中masked路由项总数。以下是逻辑payload，非物理UB/寄存器峰值：

| 对象 | 访问/容量 |
|---|---|
| indices | 名义SK*e_i B，读全部SK项，写M项 |
| scales | 名义SK*e_s B，仅读/写M项；未masked项保持 |
| hidden | 名义SD*e_h B，每真实列读一次 |
| zero_result | empty_like新分配，合法packed域写SD*e_h B |
| 单token路由SSA | idx K项、weights K项、mask K lane、int32 replacement 4K B与zero K项 |
| 单D tile | hidden/result各BD元素，实际算术大小随promotion；尾mask只减GM访问 |
| 标量 | sum_scales与未masked计数，各token局部 |

有效GM总流量为(S*K+M)*e_i+2M*e_s+2S*D*e_h B。当前row先完成权重reduce，再逐hidden tile写结果，最后清scale、改indices；没有请求方workspace或显式UB/L1/L0、queue/event、barrier、atomic。SSA可由compiler复用，不能把各逻辑张量简单求和为固定峰值。

这个写入顺序不是跨Tensor的原子事务，也没有跨stream发布协议；同token或alias storage并发读写会破坏旧权重/新metadata关系。调用者必须保证输入/新输出及两路由Tensor异步生命周期，后续consumer在同一流或显式依赖之后消费修改结果；两个输入metadata与hidden/output不得通过重叠storage引入跨row依赖。包导入仍依赖torch_npu/native共享库，primitive与流安排为外部框架边界。

## 核验方向与固定源码

核验应分别覆盖无masked、部分masked、全masked时第0索引的特殊值、identity_mask_value非0、D尾tile，以及确认只有m位置的两metadata改变；参考w必须在调用前保存旧scale。不能以zero_result单独代表全部专家输出。上述仅是从源码整理的核验方向，本次均未执行。

- [python/sgl_kernel_npu/sgl_kernel_npu/moe/zero_experts_compute_identity.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/moe/zero_experts_compute_identity.py)（primary）。
- [python/sgl_kernel_npu/sgl_kernel_npu/__init__.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py)（header）。
