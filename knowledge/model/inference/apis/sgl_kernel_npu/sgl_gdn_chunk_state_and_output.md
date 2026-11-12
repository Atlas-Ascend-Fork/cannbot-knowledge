---
type: API
title: SGLang GDN块进入状态与输出重建接口
description: 说明chunk_delta_h与chunk_fwd_o的K×V状态、残差V、累计gate、返回顺序和等长多batch门控寻址限制。
tags:
- task.implementation
- topic.attention
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/gdn/chunk_delta_h.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/gdn/chunk_o.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gdn/chunk_delta_h.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/attention/gdn/chunk_delta_h.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gdn/gdn_utils.py
  role: implementation
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-09T12:37:46Z'
platforms:
- a2
- a3
- '950'
aliases:
- chunk_delta_h
- chunk_fwd_o
---

# SGLang GDN块进入状态与输出重建接口

## 接口原型

```python
import torch
from sgl_kernel_npu.operators.attention.gdn import chunk_delta_h

def chunk_delta_h(k, w, u, g=None, initial_state=None, output_final_state=False, chunk_size=64, save_new_value=True, cu_seqlens=None, *, impl='auto'):
    ...
```

```python
from sgl_kernel_npu.operators.attention.gdn import chunk_fwd_o

def chunk_fwd_o(q, k, v, h, g=None, scale=None, cu_seqlens=None, chunk_size=64, *, impl="auto"):
    ...
```

## 状态更新和交接

`chunk_delta_h(k,w,u,g,...)` 保存各块进入状态S，计算残差 `D=U-WS`，再更新 `S←S*exp(g_L)+K^T(D⊙decay)`，其中decay在g_L-g<=0时为exp(g_L-g)，正门控差对应系数置零。输入k为FP16/BF16 `[B,T,Hg,K]`，w为 `[B,T,H,K]`，u为 `[B,T,H,V]`，H是Hg的整数倍；g实际必填FP32 `[B,T,H]`，已经是累计对数gate，不能再累加。

initial_state为可选FP32 `[N,H,K,V]`，None表示零。注意这里是K、V顺序，与Ascend C chunk_gated_delta_rule和融合decode的V、K状态池不同。Triton只接受K/V在1..128、chunk_size=64；参考可接受其他正2次幂块宽。状态FP32累加，投影中间按输入dtype舍入。

返回 `(h,v_new,final_state)`：h是低精度 `[B,NT,H,K,V]` 各块进入状态；save_new_value=True时v_new为与u同shape/dtype的D，否则None；output_final_state=True时final_state为FP32 `[N,H,K,V]`，否则None。输入不改。packed B=1时NT是所有序列chunk总数，按序列再按块存放。

## 输出重建

`chunk_fwd_o(q,k,v,h,g,...)` 要求v传上一步残差D、h传每块进入状态，不是模型原始V、初始状态或最终状态。Q/K为 `[B,T,Hg,K]`，V为 `[B,T,H,V]`，h为 `[B,ceil(T/C),H,K,V]` 或packed `[1,total_chunks,H,K,V]`；输出同V shape/dtype，scale默认K^-0.5。Q/K/V可FP16/BF16/FP32且同dtype，全部同NPU连续，g虽默认None但实际必须tensor，否则AttributeError。

输出为 `scale*(diag(exp(G))*Q*H+tril((Q*K^T)⊙E)*V)`，其中E_ij在G_i<=G_j时为exp(G_i-G_j)，正门控差时为0；不能无条件使用指数差。attention权重乘V前转v.dtype，不能用全FP32公式推导逐位相同。等长B>1时来源保留特定展平门控寻址，若需独立逐序列gate应使用B=1+cu_seqlens的packed形式。

packed边界从0到T、序列为正，元数据索引有缓存，不原地修改边界。auto固定Triton；state参考用CPU FP64并保留两个低精度舍入点，output参考用FP32且保留权重转dtype。验证应同时比较h/D/final/output、头分组、尾块和独立序列状态，不能只看最终attention输出。

## 证据与复核范围

本卡依据固定提交的第一方API说明蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。

## 相关知识

- [块内三角求逆和WY变换](sgl_gdn_chunk_linear_system.md)

## 当前状态更新实现的静态边界

原有状态公式、返回类型与 public 合同不变；以下单独限定 `chunk_delta_h` 当前固定 Triton body，不把输出重建段已有门控说明视为已覆盖状态入口，也不将 legacy/raw 域扩为 public 支持。

public adapter 对 auto/triton 检查 K/V 在1..128且 chunk_size=64，拒绝 g=None；指定 scalar Direct 则只有 K≤256 的弱 assert。body 固定128行和最多两片64列，raw K129..256 或 V>128不能因可到达就升级为公开支持，其分配尾域没有完整覆盖。当前 V≤64 时已编译排除第二片的 load/store/dot，不能用旧无此 guard 的 kernel 替代。[public 范围](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/attention/gdn/chunk_delta_h.py#L53-L69)、[Direct 分配与 gate 布局](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gdn/chunk_delta_h.py#L223-L254)、[当前 V 片 guard](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gdn/chunk_delta_h.py#L70-L106)。

**等长多 batch 的状态 gate 地址需单独限定**：Host 将 g 转为 `[B,H,Traw]`，Device 使用 `bos+h*Traw+t`，equal 的 bos=b*Traw，因此实际为 `(b+h)*Traw+t`，而独立 batch/head 的地址应为 `(b*H+h)*Traw+t`，缺 b*(H−1)*Traw。仅 b>0 且 H>1 有此偏移，B=1、H=1 或 b=0 不因这项地址差受影响；packed B=1 用 bos=cu[n] 时对应总 Traw 的 head 跨度。数值差异依实际 gate 值，这里没有真机或数值复现记录。[实际 gate 地址](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gdn/chunk_delta_h.py#L125-L136)。

**save_new_value=False 保留返回合同，但不能据此断言当前分支编译/执行可靠**：Host 令 v_new=None，body 在 SAVE_NEW_VALUE guard 之前仍计算 `v_new+bos*H*V+h*V`。该 None 算术是源码可见表达式；未执行具体 Triton frontend 编译，不给它补造指针值、确定报错或任何后续写已执行的轨迹。guard 内 residual store 被关闭，不等于 guard 外表达式已安全消除。[Host 存在性 producer](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gdn/chunk_delta_h.py#L246-L254)、[guard 外基址](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gdn/chunk_delta_h.py#L120-L125)、[残差 store 与更新](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gdn/chunk_delta_h.py#L140-L165)。

state 保持 FP32 递推，但投影前转 w.dtype，gated residual 更新前转 k.dtype；可选 v_new 在乘当前 decay 之前写 u.dtype。h 是低精度进入快照，final 是最后 FP32 state，initial_state 只读，这些 owner 与舍入点不能互换。Kᵀ block_ptr load 未显式指定 zero padding；W/U/h0 的 mask/other=0 不能自动推导为该 load 的同等保证。本次未执行编译、真机、数值或性能测试。[两次低精 cast 和写入顺序](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gdn/chunk_delta_h.py#L140-L165)。

完整64个精确 selector 与条件化生命周期见 [A2/A3 状态源码卡](../../operators/direct/transformer/attention/sgl_chunk_delta_h.md)和[950 状态源码卡](../../operators/direct/transformer/attention/sgl_chunk_delta_h_950.md)；闭包标签不表示运行正确性验收。

### DeltaH 变长缓存的精确范围

当前 chunk_delta_h 变长 Host 先调用 prepare_chunk_indices 取得总 NT 和 h 分配大小，再调用 prepare_chunk_offsets；Device 只接收 offsets/cu，索引表本身不传入。两者以及共同的 prepare_lens 都分别使用最多4项 tensor_cache，Tensor 参数以对象 `is` 匹配，不检查 `_version` 或内容。原地更新同一 cu_seqlens 会有复用旧长度、旧索引数和旧 offsets 的风险，换 chunk_size 也不能保证绕过独立的旧长度缓存。该结论严格限定已调用这些 helper 的 DeltaH 变长路径；融合 decode 的资源属性缓存属于另一机制，不能套用此 Tensor 缓存结论。[实际 helper/cache](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gdn/gdn_utils.py#L12-L91)。
