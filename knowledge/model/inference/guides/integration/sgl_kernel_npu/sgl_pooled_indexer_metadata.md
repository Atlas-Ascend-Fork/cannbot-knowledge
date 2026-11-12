---
type: Guide
title: SGLang pooled索引链的长度、页表和tail准备
description: 串联decode投影、pooled页表抽样、逐query因果长度展开及pool/tail索引展开，区分Torch与Triton后端和输出复用。
tags:
- task.implementation
- topic.compute.indexing
- topic.kv_cache
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/indexer/kpool_indexer_prepare_decode_input.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/indexer/build_pooled_page_table.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/indexer/expand_causal_seqlens.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/indexer/expand_kpool_group_and_tail_to_topk.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/kpool_indexer_prepare_decode_input.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/indexer/expand_causal_seqlens.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/indexer/build_pooled_page_table.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/torch_native/indexer/build_pooled_page_table.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/indexer/pool_key_indexer.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/indexer/pool_key_indexer.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/pool_key_indexer.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/pool_key_indexer.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/CMakeLists.txt
  role: supporting
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-09T11:21:10Z'
platforms:
- a2
- a3
- '950'
---

# SGLang pooled索引链的长度、页表和tail准备

## 配套接口原型

```python
from sgl_kernel_npu.operators.indexer import kpool_indexer_prepare_decode_input

def kpool_indexer_prepare_decode_input(
    x,
    weights_proj_weight,
    seqlens_32,
    block_tables,
    pool_size=4,
    n_heads_pow=32**-0.5,
    softmax_scale=128**-0.5,
    *,
    impl="auto",
):
    ...
```

```python
import torch
from sgl_kernel_npu.operators.indexer import build_pooled_page_table

def build_pooled_page_table(
    page_table_64: torch.Tensor,
    pool_size: int,
    *,
    impl="auto",
) -> torch.Tensor:
    ...
```

```python
import torch
from sgl_kernel_npu.operators.indexer import expand_causal_seqlens

def expand_causal_seqlens(
    cache_seqlens: torch.Tensor,
    query_lens: torch.Tensor,
    device: torch.device,
    total_q: int,
    max_query_len: int,
    *,
    seqlens_out: torch.Tensor | None = None,
    token_to_batch_out: torch.Tensor | None = None,
    impl="auto",
) -> tuple[torch.Tensor, torch.Tensor]:
    ...
```

```python
import torch
from sgl_kernel_npu.operators.indexer import expand_kpool_group_and_tail_to_topk

def expand_kpool_group_and_tail_to_topk(
    pool_indices: torch.Tensor,
    seq_lens_per_token: torch.Tensor,
    n_real: int,
    num_q_padded: int,
    pool_size: int,
    index_topk: int,
    *,
    impl="auto",
) -> torch.Tensor:
    ...
```

## 集成顺序与技术边界

本指南记录同一索引链的不同元数据任务，不把PyTorch-only页表助手归为已实现的Triton kernel。前四个元数据接口文档声明arch22/35支持；选池原生消费者另受下文平台与依赖边界限制。“已验证”是上游标注，不是本次实测。

1. decode准备入口将hidden states投影为head权重，得到完整pool长度与pooled页表。
2. packed query场景可先把每request KV/query长度展开为逐query因果长度和request编号。
3. 根据pooled key的选池结果，展开为token索引并追加未成pool的tail，padding填-1。

## decode投影与页表

`kpool_indexer_prepare_decode_input` 接BF16 X `[N,HIDDEN]`、FP32权重 `[HEADS,HIDDEN]`、int32 seqlens `[N]` 和连续int32 token页表 `[N,NUM_BLOCKS]`。FP32投影乘n_heads_pow*softmax_scale后转BF16，默认两因子32^-0.5与128^-0.5，不随heads自动改变。Triton/auto 要求 x、weights_proj_weight、seqlens_32 和 block_tables 全部连续。Triton要求heads为1..128的2次幂、pool_size严格4，hidden不必256整除。返回BF16 `[N,HEADS]`、int32完整pool数 `[N]` 与新pooled页表，输入不改。

独立 `build_pooled_page_table` 只有torch_native/auto：按最后一维每pool_size个页ID取首项，输出末维ceil(NUM_BLOCKS/pool_size)，支持非连续输入，不改dtype/前导维度，pool_size须正且整除128。它是输入设备上的Torch高级索引，没有Triton实现。decode准备会按需补零再抽样，不能把任意页表间隔认作物理连续性证明。

### 独立页表抽样的实际边界

固定实现只构造同设备idx=torch.arange(0,NUM_BLOCKS,pool_size)，再返回page_table_64[...,idx]。它选择已有页ID，不将ID除以pool_size、不重映射、不排序，也不验证每组ID物理连续。尾部不足一组仍取该组首项，末维为空时得到末维为空的新高级索引结果；这不是原Tensor的stride view。名称中的_64也不是dtype限制或NUM_BLOCKS必须被64整除的检查。

正整数pool_size须整除128，即1、2、4、8、16、32、64、128。Host实际只有128 % pool_size == 0断言，没有单独的正值检查：0会在取模处失败，某些负数可通过整除断言后进入Torch arange的外部参数边界；不能由此把负数纳入公开支持。

## 选池消费者pool_key_indexer的原生接入

`sgl_kernel_npu.operators.indexer.pool_key_indexer` 的auto/aclnn延迟导入独立attentions扩展，实际调用torch.ops.attentions.pool_key_indexer，再由C++转发aclnnPoolKeyIndexer；仅主sgl-kernel wheel不足以保证扩展和vendor算子均存在。它接收query、完整pooled key和逐query/head权重，选pool后展开为token并追加未成pool尾部。与独立build_pooled_page_table的“只抽已有页ID”不同，该入口的打分/TopK由外部核心完成，封装不承诺选池顺序稳定。

| 项目 | 固定Python/C++接入合同 |
|---|---|
| 参数默认值 | topk=2048，pool_size=16，layout_q/layout_k="BSND"，mask_mode=3，quant_mode=-1，return_value=False，key_stride0=-1；没有自动失败回退 |
| dtype与输出 | query为FP16/BF16，pool_key和weights同dtype；新输出int32，四维query为[B,S,topk+pool_size-1]，二维/三维为[query.size(0),topk+pool_size-1]；不返回分数 |
| Host长度 | pool_tail_k及actual_seq_q/k是Host整数序列，不是NPU Tensor；actual_seq_*为None时传空aclIntArray。TND query长度为累计结束位置，分页key长度为逐请求有效完整pool数 |
| C++实际拒绝 | quant_mode!=-1、return_value=True、query rank不在2/3/4、pool_size<=0、topk<pool_size、三输入dtype不匹配或layout前缀不属于TND*/PA_*/BSND* |
| 不由包装补齐 | 二维/三维query直接转发，不reshape；layout前缀通过不等于任意后缀/stride/shape有效；同NPU、连续ND、页表、有效长度和topk整pool等仍按vendor合同准备 |

绑定把qDescale/kDescale设为undefined、kDescaleStride0设为-1，分数输出则创建[0] FP32 Tensor；因此不能把底层vendor可能存在的量化或returnValue模式当作这个公开binding已暴露的能力。pool_tail_k须在[0,pool_size)，实际Seq/页表要和完整pool缓存一致。此处topk是token级宽度，pool级选取数及padding规则由匹配vendor实现决定。

这条链要显式统一pool_size：decode Triton准备仅允许4，选池默认却为16，不能直接拼接默认参数；各阶段必须同时满足各自后端约束。公开选池支持表标arch35已验证、arch22未验证，文档同时声明尚无该binding硬件精度/性能验收结论；两种表述均不构成本次实测，不能把整个选池链推成A2/A3已验收。原生核心不在本SGL插件源中，这一节只覆盖已读接入合同，未声明完整CANN Device实现闭包。

## 逐query长度与缓冲复用

`expand_causal_seqlens` 用连续int32 cache_seqlens/query_lens `[B]`，host total_q=sum(query_lens)和max_query_len必须准确；显式device须与输入完全相同。每request产生以KV末端右对齐的可见长度和request id，输出分别int32/int64 `[total_q]`。例如KV10、query2产生9,10；零query不产出行，负起点取零。

可传seqlens_out/token_to_batch_out，原地覆盖并返回相同对象，适合保持消费者地址；输出互相及与输入不能重叠，shape/device/dtype须稳定，Triton/auto 还要求两个复用输出均连续（stride(0)=1）。Triton不回读设备长度核验host和上界，调用方保证非负和int32不溢出。空batch/total_q零返回空结果，不能把不匹配host容量交给graph重放。

## pool展开与tail

`expand_kpool_group_and_tail_to_topk` 接int32 pool_indices `[rows,N_POOL_TOPK]` 与连续逐token长度，Triton要求pool_size>=4、index_topk=N_POOL_TOPK*pool_size。实际n_real会截到输入较小行数，num_q_padded需覆盖它；返回int32 `[num_q_padded,index_topk+pool_size-1]`，保持pool顺序展开，再追加剩余tail，未使用tail和padding行-1。pool索引允许非连续行stride，结果可能非连续。

所有tensor同NPU，各auto均固定相应默认实现且不执行失败回退。验证需对照每阶段的值和布局，另检验地址复用、零query、非整pool尾部、无效padding和host总量一致性；不能仅检查最终topk shape。

## 证据与复核范围

本卡依据固定提交的第一方API说明蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。


相关的完整源码卡：[decode投影与页表准备](/model/inference/operators/direct/nn/index/sgl_kpool_indexer_prepare_decode_input.md)、[950实现](/model/inference/operators/direct/nn/index/sgl_kpool_indexer_prepare_decode_input_950.md)。
