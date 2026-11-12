---
type: API
title: SGLang GQA共享稀疏decode的双入口与分发边界
description: 比较纯Triton与可选原生GQA入口，说明逻辑块映射、向量sink、分块舍入和A2/A3 UB限制。
tags:
- task.implementation
- topic.attention
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/flash_decode_bnsd_with_gqa_share_sparse.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/gqa_share_sparse_decode.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/flash_decode_bnsd_with_gqa_share_sparse.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/attention/flash_decode_bnsd_with_gqa_share_sparse.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/sparse_attention_score/op_kernel/arch22/sparse_attention_score_kernel_arch22.h
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gqa_share_sparse_attention.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gqa_share_sparse_decode.py
  role: implementation
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- a2
- a3
- '950'
aliases:
- gqa_share_sparse_decode
- flash_decode_bnsd_with_gqa_share_sparse
---

# SGLang GQA共享稀疏decode的双入口与分发边界

## 接口原型

```python
from sgl_kernel_npu.operators.attention import flash_decode_bnsd_with_gqa_share_sparse

def flash_decode_bnsd_with_gqa_share_sparse(
    q,
    sink,
    k_cache_bnsd,
    v_cache_bnsd,
    block_table,
    seq_lens,
    block_size,
    topk_idx,
    sm_scale=None,
    num_topk_chunks=None,
    max_num_topk_chunks=8,
    req_to_token=None,
    req_pool_indices=None,
    max_num_blocks=None,
    num_pages=None,
    sanitize_page_ids=False,
    topk_blocks_per_step=1,
    prefetch_idx=False,
    num_warps=None,
    num_stages=None,
    use_native=True,
    *,
    impl="auto",
):
    ...
```

```python
import torch
from sgl_kernel_npu.operators.attention import gqa_share_sparse_decode

def gqa_share_sparse_decode(q, sink, k_cache_bnsd, v_cache_bnsd, block_table, seq_lens, block_size, topk_idx, sm_scale=None, num_topk_chunks=None, max_num_topk_chunks=8, req_to_token=None, req_pool_indices=None, max_num_blocks=None, num_pages=None, sanitize_page_ids=False, topk_blocks_per_step=1, prefetch_idx=False, num_warps=None, num_stages=None, *, impl='auto'):
    ...
```

## 公共数据合同

两个入口都只消费调用方选好的逻辑KV块，不执行TopK。Q为FP16/BF16 `[B,QH,D]`，K/V为 `[pages,BS,KVH,D]`、同dtype，QH是KVH的整数倍。int32/int64 topk_idx为 `[KVH或QH,B,T]`，QH形式只取每个GQA组首头列表；-1为空槽，但原生入口还受下述有效前缀限制；重复块会重复参加注意力，不去重。seq_lens `[B]` 是每query可见KV长度而非最后下标。

页映射二选一：block_table `[B,maxBlocks]`，或req_to_token加req_pool_indices，直接映射用块首slot//BS。direct须同时给正max_num_blocks/num_pages，映射容量覆盖max_num_blocks*BS；sanitize只夹物理页，不检查请求/逻辑块。所有有效值有限、索引合法、张量同NPU且遵守连续性，长度在int32范围内。

可选sink为 `[QH,D]` 向量，先与Q点积再进入softmax分母，其value为0；不是MLA接口的 `[QH]` 标量logit。在各自合法输入范围内，只对选中且在可见前缀内的token做online softmax，正常算法合同中无有效token应输出0；固定纯Triton预取的单块边界见下文，不能对该域无条件保证空选输出0。原生路径不支持任意空槽位置。没有额外query位置参数，verify/prefill需展开query并提供每行因果seq_lens。返回同Q shape/dtype的新tensor，输入不改。

## 两个入口不能混为一谈

`gqa_share_sparse_decode` 的auto固定Triton，公开入口关闭原生路径，只可显式triton/torch_native。`flash_decode_bnsd_with_gqa_share_sparse` 的auto在use_native=True、无sink、D=BS=128且构建含原生时选Ascend C，否则Triton；显式后端直接执行，失败不换后端重试。Ascend C仅arch22，且索引预处理仍依赖Triton。纯Triton在arch22/35支持。

原生预处理只计数并清洗越界项，不压紧索引，随后把负项改为0；Device只消费前validTopK项。因此清洗后的有效项必须构成连续前缀，尾部才可为空槽。中间/前方有空槽或不可见块时，例如[-1,1]，会变成[0,1]却只计算块0；此类输入应显式选 impl="triton"。原生每行有效块还必须<=32：Device的validPhysicalIds/validTileSize固定32项，公开适配层和auto分发都没有检查该容量，超出会越界，也应显式选Triton。该A2/A3原生路径还一次加载整组G=QH/KVH到固定32KiB的Q L1区，要求round_up(G,16)*D*2<=32768；D=128时G<=128。auto未检查此容量，超界不能直接使用auto或ascendc，应显式选满足自身条件的Triton。此原生限制不适用于auto固定Triton的另一个gqa_share_sparse_decode入口。

Triton要求block_size为正的2次幂，topk_blocks_per_step先按max(1,int(value))归一化，归一化结果也必须为2次幂，不符合会断言失败。num_topk_chunks为不超列表长度的2次幂；单chunk省合并，多chunk需部分输出，部分结果按Q dtype保存，分块会影响舍入。权重乘V前也转KV dtype，与全FP32参考不保证逐位相同。D=BS=128时topk_blocks_per_step保持1，来源明确2会超已测试A2/A3 UB容量导致编译ub overflow，auto不会改参数重试。prefetch仅单块步长生效。

### 固定快照的单块预取边界

在纯Triton实际路径，若topk列表长度S=1、num_topk_chunks=1、归一化topk_blocks_per_step=1且prefetch_idx=True，launcher把CHUNK_SIZE_T下限设为2，但索引预取向量BLOCK_SIZE_T仅为next_power_of_2(S)=1。核心step=1的where+sum没有匹配lane，logical_block与physical_block均归约为0；随后仅以logical_block>=0判断有效。seq_lens>0时，第0物理页中的可见token可能额外参与注意力，不保证预取只是等价优化，甚至不能对原列表全为空槽的情形保证输出0。

这是固定源码的静态推导，未在设备复现。该单块域应关闭prefetch_idx，另用所选逻辑块的显式参考验证；普通非预取分支有topk_pos<max_topk保护。多chunk因chunk数不得超过列表长度，不包含上述S=1/C=1以外的推广；不能据此宣称所有prefetch组合都错误。新增[纯Triton A2/A3源码卡](../../operators/direct/transformer/attention/sgl_gqa_share_sparse_decode.md)和[950源码卡](../../operators/direct/transformer/attention/sgl_gqa_share_sparse_decode_950.md)分别列出完整路线及精度/资源边界。

验证应分别覆盖两页映射、GQA首头共享、重复块、空选择、sink和query因果前缀；合理选dtype/负载容差，并区分原生支持与参考可用范围。

## 证据与复核范围

本卡依据固定提交的第一方API说明蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。
