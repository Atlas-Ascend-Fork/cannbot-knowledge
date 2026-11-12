---
type: API
title: SGLang FIA页表准备的当前块与因果长度
description: 说明fia_prep将稀疏逻辑块转为物理页、当前块置末、可复用输出与二次幂槽宽要求。
tags:
- task.implementation
- topic.attention
- topic.kv_cache
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/fia_prep.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/fia_prep.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/torch_native/attention/fia_prep.py
  role: implementation
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-09T04:38:56Z'
platforms:
- a2
- a3
- '950'
---

# SGLang FIA页表准备的当前块与因果长度

## 接口原型

```python
import torch
from sgl_kernel_npu.operators.attention import fia_prep

def fia_prep(ti, seq_lens, per_query_req, req_to_token, block_size, block_table_out=None, actual_kvlen_out=None, *, impl='auto'):
    ...
```

## 参数与语义

`fia_prep` 将稀疏逻辑页号转换成物理页表，保留其他选中块顺序，把当前query块放最后，actual_kvlen 计其他选中完整页长度；仅当当前页已在 ti 中选中时加其因果前缀长度。当前页未选中时仍追加其物理页，但不增加有效长度。物理页由req_to_token的块首slot整除block_size得到，不能直接把输入逻辑块号交给分页attention。

ti是int32 `[T,S]`、-1填充，固定两后端实现均按 query 行直接读取 seq_lens，故其为int32逐 query `[T]`，不会通过 per_query_req 查请求长度；多个 query 共享请求时调用方须先展开请求长度。第一方文档写 `[B]`，与当前实现存在差异。per_query_req为int32/int64 `[T]`，req_to_token为int32/int64 `[requests,max_ctx]`；block_size>0。同NPU连续输入。Triton当前要求S是2次幂，未选当前页时必须留出一个空槽，请求行、页索引与映射容量由调用方保证。

返回 `(block_table,actual_kvlen)`，分别int32 `[T,S]` 与 `[T]`。可传同shape/dtype输出缓冲block_table_out和actual_kvlen_out，覆盖后返回以便复用。auto与triton是同一入口，无自动参考回退；torch_native独立计算但可能因host元数据传输同步。

验证应覆盖当前页已选/未选、尾页因果前缀、多个query共享request和预分配输出身份，不能仅比较页表集合而忽略末槽与actual_kvlen。

## 证据与复核范围

本卡依据固定提交的第一方API说明蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。
