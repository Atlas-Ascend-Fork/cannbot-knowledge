---
type: API
title: SGLang GDN块内累积、三角求逆与WY接口链
description: 串联chunk_local_cumsum、chunk_scaled_dot_kkt、solve_tril与recompute_w_u_fwd，保留逆矩阵语义、分块边界缓存和精度限制。
tags:
- task.implementation
- topic.attention
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/gdn/solve_tril.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/gdn/chunk_local_cumsum.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/gdn/chunk_scaled_dot_kkt.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/gdn/recompute_w_u_fwd.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gdn/chunk_local_cumsum.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/attention/gdn/chunk_local_cumsum.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gdn/chunk_scaled_dot_kkt.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gdn/solve_tril.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gdn/recompute_w_u_fwd.py
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
- chunk_local_cumsum
- chunk_scaled_dot_kkt
- solve_tril
- recompute_w_u_fwd
---

# SGLang GDN块内累积、三角求逆与WY接口链

## 接口原型

```python
import torch
from sgl_kernel_npu.operators.attention.gdn import solve_tril

def solve_tril(A, cu_seqlens=None, output_dtype=torch.float, *, impl="auto"):
    ...
```

```python
import torch
from sgl_kernel_npu.operators.attention.gdn import chunk_local_cumsum

def chunk_local_cumsum(g, chunk_size, reverse=False, scale=None, cu_seqlens=None, head_first=False, output_dtype=torch.float32, *, impl='auto'):
    ...
```

```python
import torch
from sgl_kernel_npu.operators.attention.gdn import chunk_scaled_dot_kkt

def chunk_scaled_dot_kkt(k, beta, g_cumsum=None, cu_seqlens=None, chunk_size=64, output_dtype=torch.float32, *, impl='auto'):
    ...
```

```python
from sgl_kernel_npu.operators.attention.gdn import recompute_w_u_fwd

def recompute_w_u_fwd(k, v, beta, g_cumsum, A, cu_seqlens=None, *, impl="auto"):
    ...
```

## 四步接口与语义交接

GDN分块prefill先用chunk_local_cumsum在各chunk内累计对数衰减G，再由chunk_scaled_dot_kkt构造严格下三角 `A_ij=beta_i*(k_iᵀk_j)*exp(G_i-G_j)`，仅保留i>j且gate差<=0；solve_tril计算 `R=(I+A)^-1`；recompute_w_u_fwd再算 `W=R diag(beta*exp(G)) K↑`、`U=R diag(beta)V`。最后一步形参虽也叫A，实际要传R，不能传求逆前矩阵。

keys为 `[B,T,Hg,K]`，V为 `[B,T,H,V]`，beta/G为 `[B,T,H]`，H须是Hg整数倍；K↑按h//(H/Hg)共享key，不需复制。三角矩阵按行压为 `[B,T,H,C]`，末维是chunk宽C而非key特征维。WY返回w `[B,T,H,K]`、u `[B,T,H,V]`，分别转k/v dtype，输入不改。

## 各入口的不同约束

| 步骤 | Triton边界 |
| --- | --- |
| local_cumsum | chunk_size为正2次幂，GDN常用64；FP32累加后写回输入dtype，output_dtype须为None或g.dtype，None表示沿用输入类型，低精度输入不能直接用默认FP32输出；head_first+cu_seqlens被拒绝，head优先无时间尾块，且launch的BLOCK_T必须足够。 |
| scaled_dot_kkt | k为FP16/BF16、beta同dtype，g_cumsum必须显式给FP32且块内单调不增；输出默认FP32，尾列0。 |
| solve_tril | A支持FP16/BF16/FP32，C仅16/32/64，严格下三角且有限；用FP32分块逆再转换输出，尾chunk补零仅返回有效行。 |
| recompute_w_u | 可用FP16/BF16/FP32输入，C仅16/32/64，FP32内部计算，特征按128片处理并支持尾块；避免exp(G)溢出。 |

Triton输入须同NPU且连续。packed变长时B=1、cu_seqlens为int32/int64 `[N+1]`，从0到T严格递增、不支持空序列，边界处重新分块。solve/WY会缓存块索引，不要原地改cu_seqlens后期待缓存自动失效。调用方负责设备边界值有效性。

auto固定Triton，无后端失败回退。独立torch_native的solve可用任意正C与非连续输入，并通过FP32 solve_triangular求逆；WY同样覆盖任意正C，读取NPU边界tolist会同步。这些参考能力不扩大Triton边界。

复核可先检查 `(I+A)R≈I`，再对比W/U、短尾chunk和多序列边界；病态矩阵可放大误差。独立recurrent decode不需要此三角求逆链，Mega GDN也可绕过这些独立kernel。

## 证据与复核范围

本卡依据固定提交的第一方API说明蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。

## 相关知识

- [块进入状态与输出重建](sgl_gdn_chunk_state_and_output.md)

## 固定源码实现边界

上述公式和尾块描述保留公开数学意图；以下仅限定同一固定提交当前 Triton 实现能从源码证明的行为。本次未执行编译或真机、数值、性能测试，不把未指定 primitive 的行为推断成已发生故障。

- **块内 cumsum**：public adapter 要求 `BLOCK_T=nextPOT(floor(2^18/(H*C)))≥C` 且预算商为正；head_first 还要求时间整 tile，并拒绝与 cu_seqlens 组合。这些 guard 不等于 scalar Direct 全部已检查。当前 head_first body 从 `[H,Nc,C]` 经两次 `trans(2,0,1)` 得 `[Nc,C,H]`，再 reshape 为 `[H,BLOCK_T]`；两次置换不是互逆，一般 H>1 且 BLOCK_T>1 的非对称数据会改变 head/time 排列。H=1 或 BLOCK_T=1 的退化相符域及数据巧合需排除；这是静态索引推导。完整时间 tile 不能消除这项布局差异。[公开 guard](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/attention/gdn/chunk_local_cumsum.py#L70-L83)、[实际 head-first 置换](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gdn/chunk_local_cumsum.py#L63-L70)。
- **cumsum 反向尾块**：BTH 路线的 load 只给 boundary_check，没有显式 padding_option="zero"。reverse=True 且该 sequence 长度 L 不是 C 的整数倍时，同一末尾 chunk 的缺失后缀会进入 suffix 的语义域，不能直接保证这些 lane 为零；具体 primitive 行为本次未验证。正向有效 prefix 不依赖同 chunk 未来 padding，L%C=0 时 padding 属于其它 chunk，这两类条件不得一起判为失败。scan 后仍显式转输入 dtype，宽 output allocation 不能恢复已舍入的值。[BTH scan 与 store](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gdn/chunk_local_cumsum.py#L78-L88)。
- **KKT 与求逆尾块**：KKT 有效行的 padded 时间列 j≥L 被严格下三角 where 明确写零；这是原文“尾列0”的范围。但 K 维按128片加载，末特征片的 block_ptr load 未显式指定 zero padding，K%128≠0 时不能由时间列零值推导其特征 lane 为零。solve_tril 的16阶原子节点和当前64阶 merge 使用显式 mask/other=0；32阶 merge 的三次 block_ptr load 只有 boundary_check，也没有显式 zero padding。因此“尾 chunk 补零”作为数学意图不扩为当前32阶所有越界 lane 已初始化的实现保证。[KKT 分片及三角写出](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gdn/chunk_scaled_dot_kkt.py#L66-L98)、[32阶 load](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gdn/solve_tril.py#L303-L308)、[当前64阶 body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gdn/solve_tril.py#L493-L630)。
- **WY dtype 与精度**：当前 validator 允许 k/v/beta/G/A 各自独立取 FP16/BF16/FP32；k/v/A 要连续，beta/G 可由 Host 转为 BHT contiguous。局部矩阵转 FP32 不等于统一 IEEE 保证：U dot 显式 allow_tf32=False，W dot 使用默认 precision。G 表达式先 exp(load) 再转 FP32，源码未显式先转 FP32 再 exp。当前 equal batch 的 gate_bos=batch*H*Traw 与 packed gate_bos=bos 已区分；旧 legacy body 不能作为全域等价证据。[validator](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gdn/recompute_w_u_fwd.py#L15-L43)、[当前权重与两个 dot](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gdn/recompute_w_u_fwd.py#L91-L129)。

完整 Host、selector、字节账与条件边界见下列独立源码卡；闭包标签仅表可追溯，不表示已完成运行验收。

| 算子 | A2/A3 | 950 |
|---|---|---|
| 块内 cumsum | [源码卡](../../operators/direct/transformer/attention/sgl_chunk_local_cumsum.md) | [源码卡](../../operators/direct/transformer/attention/sgl_chunk_local_cumsum_950.md) |
| KKT 构造 | [源码卡](../../operators/direct/transformer/attention/sgl_chunk_scaled_dot_kkt.md) | [源码卡](../../operators/direct/transformer/attention/sgl_chunk_scaled_dot_kkt_950.md) |
| 三角求逆 | [源码卡](../../operators/direct/transformer/attention/sgl_solve_tril.md) | [源码卡](../../operators/direct/transformer/attention/sgl_solve_tril_950.md) |
| WY 重算 | [源码卡](../../operators/direct/transformer/attention/sgl_recompute_w_u_fwd.md) | [源码卡](../../operators/direct/transformer/attention/sgl_recompute_w_u_fwd_950.md) |

### 变长 helper 的对象身份缓存

当前 cumsum、KKT、solve 和 WY 的变长路径都会调用 gdn_utils.prepare_chunk_indices，并间接调用 prepare_lens。每个被 tensor_cache 装饰的 helper 各有最多4项缓存，Tensor 参数以 Python 对象 `is` 比较，非 Tensor 参数比较类型和值；没有检查 Tensor 的 `_version` 或数据内容。同一个 cu_seqlens 原地更新后，可能复用旧长度及分块表，不能把原文“不原地修改边界”仅理解为性能建议。即使更换 chunk_size 令索引表未命中，prepare_lens 仍可能以同一 cu 对象命中旧长度；这一边界只用于实际调用这些 helper 的路径，不泛化到不使用它们的 decode。[缓存与实际 producers](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gdn/gdn_utils.py#L12-L82)。
