---
type: API
title: SGL Kpool环形tail写入、汇聚与分页cache更新接口
description: 串联四个Kpool API的计划字段、有效请求判定、softmax汇聚和可变状态，区分函数名与实际旋转行为。
tags:
- task.implementation
- topic.kv_cache
- topic.memory
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/kpool_write_tail_and_maybe_compress.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/kpool_assemble_softmax_rotate_write_cache.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/kpool_decode_update_and_maybe_write_cache.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/scatter_kpool_tail_updates.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/torch_native/mem_cache/scatter_kpool_tail_updates.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/mem_cache/scatter_kpool_tail_updates.py
  role: implementation
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-09T04:38:09Z'
platforms:
- a2
- a3
- '950'
aliases:
- kpool_write_tail_and_maybe_compress
- kpool_assemble_softmax_rotate_write_cache
- kpool_decode_update_and_maybe_write_cache
- scatter_kpool_tail_updates
---

# SGL Kpool环形tail写入、汇聚与分页cache更新接口

## 调用入口

```python
from typing import Optional
import torch
from sgl_kernel_npu.operators.mem_cache import kpool_write_tail_and_maybe_compress

def kpool_write_tail_and_maybe_compress(
    index_k_cache: torch.Tensor,
    key: torch.Tensor,
    score: torch.Tensor,
    tail_k: torch.Tensor,
    tail_score: torch.Tensor,
    ape: torch.Tensor,
    req_pool_indices: torch.Tensor,
    write_start: torch.Tensor,
    tail_logical_start: torch.Tensor,
    write_loc: torch.Tensor,
    out_cache_loc: torch.Tensor,
    num_draft_tokens: int,
    effective_n_per_batch: Optional[torch.Tensor] = None,
    *,
    num_programs: Optional[int] = None,
    impl="auto",
) -> None:
    ...

from typing import Optional
import torch
from sgl_kernel_npu.operators.mem_cache import kpool_assemble_softmax_rotate_write_cache

def kpool_assemble_softmax_rotate_write_cache(
    index_k_cache: torch.Tensor,
    chunk_k: torch.Tensor,
    chunk_score: torch.Tensor,
    tail_k: torch.Tensor,
    tail_score: torch.Tensor,
    req_pool_idx: torch.Tensor,
    n_from_tail: torch.Tensor,
    chunk_src_start: torch.Tensor,
    tail_logical_base: torch.Tensor,
    ape: torch.Tensor,
    loc: torch.Tensor,
    write_mask: Optional[torch.Tensor] = None,
    *,
    num_programs: Optional[int] = None,
    impl="auto",
) -> None:
    ...

import torch
from sgl_kernel_npu.operators.mem_cache import kpool_decode_update_and_maybe_write_cache

def kpool_decode_update_and_maybe_write_cache(
    buf: torch.Tensor,
    tail_k: torch.Tensor,
    tail_score: torch.Tensor,
    key: torch.Tensor,
    slot_score: torch.Tensor,
    ape: torch.Tensor,
    block_tables: torch.Tensor,
    req_pool_indices: torch.Tensor,
    positions: torch.Tensor,
    seq_lens: torch.Tensor,
    out_cache_loc: torch.Tensor,
    *,
    pool_size: int,
    slots_per_page: int,
    head_dim: int = 128,
    impl="auto",
) -> None:
    ...

import torch
from sgl_kernel_npu.operators.mem_cache import scatter_kpool_tail_updates

def scatter_kpool_tail_updates(
    pool,
    chunk_k: torch.Tensor,
    chunk_score: torch.Tensor,
    tail_k: torch.Tensor,
    tail_score: torch.Tensor,
    req_pool_idx: torch.Tensor,
    dst_logical_start: torch.Tensor,
    chunk_src_start: torch.Tensor,
    n_write: torch.Tensor,
    *,
    impl="auto",
) -> None:
    ...
```

## 共同状态模型

Kpool保存每请求的key/score环形tail，在凑满一个pool时逐通道计算FP32 softmax加权key，再存为BF16 pooled cache。ape提供每个pool位置的FP32加性score；读入历史、索引容量及无写冲突由上游保证，wrapper不完整检查设备数值。auto固定triton，不运行时回退。上游实现表声明arch22支持、arch35已验证，此处不把声明变成新实测。

## 四个入口的职责

| API | 输入与寻址 | 只允许的状态修改 |
| --- | --- | --- |
| kpool_write_tail_and_maybe_compress | key/score `[B*N,128]`，tail `[R,pool_size+N,128]`；write_start和tail_logical_start给逻辑起点；write_loc `[B,ceil(N/pool_size)]`给cache行 | 写tail_k/tail_score和完成pool的cache。有效batch即写全部N行；effective_n只决定哪些pool允许压缩，0也不阻止tail写入。out_cache_loc每batch首项=0时整体跳过。 |
| kpool_assemble_softmax_rotate_write_cache | 每pool计划包含req_pool_idx、n_from_tail、chunk_src_start、tail_logical_base和loc；先读tail前段，再补chunk；write_mask可跳过cache行 | 只写cache，tail/chunk只读。尽管名字含rotate，实际存未旋转、未量化的pooled key。支持全tail、空chunk。 |
| kpool_decode_update_and_maybe_write_cache | 每请求一个key/slot_score `[B,D]`；positions和seq_lens给当前进度，block_tables为int32页表 | 只写buf/tail_k/tail_score；out_cache_loc=0只用于跳过，请勿用作pool地址。恰好补满pool时，实际cache位置由页表确定。 |
| scatter_kpool_tail_updates | plan给请求、源起点、目标逻辑起点和n_write；读取pool.index_kpool | 只复制tail_k/tail_score，不汇聚、不量化；目标物理位置按tail容量取模，多个plan不能覆盖冲突。 |

## 布局和dtype

写/组装接口固定128通道：key/tail_k/cache为BF16，score可FP16/BF16/FP32，ape为 `[pool_size,128]` FP32。组装要求 `0<=n_from_tail<=pool_size`、tail容量和pool_size正。num_draft_tokens=N为正并整除key行数；显式num_programs须正，参考后端忽略该性能参数。

decode的head_dim默认128且须匹配tail；score覆盖BF16/FP32，ape是FP32。buf可为 `[num_pages,S*D]` 或 `[num_pages,S,1,D]`，必须满足 `stride(0)=S*D`，S=slots_per_page>0；pool、tail容量、页表均非空。空batch直接返回。

可变cache/tail必须连续，不能为便于调用而把非连续状态复制成临时Tensor后丢失更新。write_loc和计划字段也有连续要求；部分只读Tensor允许wrapper内部连续化。scatter的源目标dtype须兼容以避免隐式转换；两后端共同适用范围需保证 `0<=n_write<=pool.index_kpool`。Torch reference 仅生成 pool.index_kpool 个 slot，而 Triton 循环完整 n_write；超出上界时即使容量足够也可能写不同数量，例如 pool=4/n_write=5 分别复制4/5行，不能直接对拍为等价。

## 验证方式与失效边界

四入口都返回None。各后端要使用独立cache/tail副本，在上述共同输入边界内分别对照显式torch_native：检查部分tail填充、刚好补满pool、环绕、无效请求跳过、mask关闭及cache未写区的哨兵。decode必须额外用非平凡页表验证地址，不能只测全零页号。effective_n不能当tail写掩码；assembly不能当RoPE/量化融合。校验未完整覆盖的设备值域由调用方保证。

## 固定来源与验证状态

- [mem_cache/kpool_write_tail_and_maybe_compress.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/kpool_write_tail_and_maybe_compress.md)
- [mem_cache/kpool_assemble_softmax_rotate_write_cache.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/kpool_assemble_softmax_rotate_write_cache.md)
- [mem_cache/kpool_decode_update_and_maybe_write_cache.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/kpool_decode_update_and_maybe_write_cache.md)
- [mem_cache/scatter_kpool_tail_updates.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/scatter_kpool_tail_updates.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
