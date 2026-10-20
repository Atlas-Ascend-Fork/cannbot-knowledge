---
type: Guide
title: Chunk GDN/KDA 的任务切分
description: 说明准备与输出按 chunk 并行、状态更新按 head 分核且核内顺序遍历 chunk 的依据。
tags:
- task.design
- task.implementation
- topic.tiling
- topic.memory
status: stable
sources:
- resource: https://github.com/tile-ai/tilelang-ascend/blob/585ad8c3b5fae175f1d1661059d347645f1f9536/examples/linear_attention_and_rnn/opt_gdn_full.py
  role: primary
- resource: https://github.com/tile-ai/tilelang-ascend/blob/585ad8c3b5fae175f1d1661059d347645f1f9536/examples/linear_attention_and_rnn/opt_gdn/opt_gdn_chunk_cumsum.py
  role: implementation
- resource: https://github.com/tile-ai/tilelang-ascend/blob/585ad8c3b5fae175f1d1661059d347645f1f9536/examples/linear_attention_and_rnn/opt_gdn/opt_gdn_chunk_scaled_dot_kkt.py
  role: implementation
- resource: https://github.com/tile-ai/tilelang-ascend/blob/585ad8c3b5fae175f1d1661059d347645f1f9536/examples/linear_attention_and_rnn/opt_gdn/opt_gdn_solve_tril.py
  role: implementation
- resource: https://github.com/tile-ai/tilelang-ascend/blob/585ad8c3b5fae175f1d1661059d347645f1f9536/examples/linear_attention_and_rnn/opt_gdn/opt_gdn_wy_fast.py
  role: implementation
- resource: https://github.com/tile-ai/tilelang-ascend/blob/585ad8c3b5fae175f1d1661059d347645f1f9536/examples/linear_attention_and_rnn/opt_gdn/opt_gdn_chunk_h.py
  role: implementation
- resource: https://github.com/tile-ai/tilelang-ascend/blob/585ad8c3b5fae175f1d1661059d347645f1f9536/examples/linear_attention_and_rnn/opt_gdn/opt_gdn_chunk_o.py
  role: implementation
created_at: '2026-10-17T05:12:05Z'
updated_at: '2026-10-17T08:41:05Z'
platforms:
- a2
aliases:
- chunk_gdn
- chunk_kda
- opt_gdn
- chunk_h
---

# Chunk GDN/KDA 的任务切分

`opt_gdn_full.py` 依次执行前缀和、score、三角求解、W/U、chunk-h、chunk-o 六个阶段。除 chunk-h 外，其余阶段在所需输入就绪后，每个 batch、每个 head 下的各个 chunk 都可以独立计算，因此可以沿这三个维度划分任务并行执行。

chunk-o 中，每个 batch、每个 head 下的一个 chunk 对应一个独立任务：

```python
with T.Kernel(B * H * chunk_num, is_npu=True) as (cid, vid):
    bx = cid % chunk_num              # chunk
    by = (cid // chunk_num) % H       # head
    bz = (cid // chunk_num) // H      # batch
```

chunk-h 中，同一 head 的当前 chunk 依赖前一个 chunk 更新后的状态，因此每个 batch/head 对应一个任务，不同 head 分核并行，每个任务在核内顺序遍历所有 chunk。当前配置中 `BV=DV`、`bv_num=1`，源码如下，省略计算部分：

```python
with T.Kernel(B * H * bv_num, is_npu=True) as (cid, vid):
    bx = cid % bv_num                # V 列块
    by = (cid // bv_num) % H          # head
    bz = (cid // bv_num) // H         # batch
    # ...
    with T.Scope("C"):
        for i in T.serial(chunk_num):
            # 计算当前 chunk，并与 Vector 协作完成状态更新
            ...
```

chunk-h 保存每个 chunk 所需的入口状态和残差，chunk-o 读取它们计算输出，不需要等待前一个 chunk 的输出，因此可以按 chunk 并行。实际实现也可以将多个独立 chunk 合并到一个任务中，cumsum 就采用了这种组织方式。
