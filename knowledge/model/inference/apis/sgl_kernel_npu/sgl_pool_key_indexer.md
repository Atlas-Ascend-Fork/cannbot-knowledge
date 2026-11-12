---
type: API
title: SGLang PoolKeyIndexer的host长度与外部扩展边界
description: 记录PoolKeyIndexer的池展开、host整数序列、单索引输出及独立attentions/vendor依赖，保留硬件验收缺口。
tags:
- task.implementation
- topic.attention
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/indexer/pool_key_indexer.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-08T11:04:14Z'
platforms:
- '950'
---

# SGLang PoolKeyIndexer的host长度与外部扩展边界

## 接口原型

```python
from sgl_kernel_npu.operators.indexer import pool_key_indexer

def pool_key_indexer(
    query,
    pool_key,
    weights,
    pool_tail_k,
    actual_seq_q=None,
    actual_seq_k=None,
    block_table=None,
    topk=2048,
    pool_size=16,
    layout_q="BSND",
    layout_k="BSND",
    mask_mode=3,
    quant_mode=-1,
    return_value=False,
    key_stride0=-1,
    *,
    impl="auto",
):
    ...
```

## 语义与输入位置

`pool_key_indexer` 对pooled key打分选pool，展开为token位置并追加未成完整pool的尾部，返回int32索引、不返回分数，不保证pool排列稳定。auto与aclnn是同一实现，经torch.ops.attentions.pool_key_indexer绑定转发aclnnPoolKeyIndexer，没有torch_native。

Q为FP16/BF16 `[B,S,H,D]`、TND `[T,H,D]` 或二维 `[T,H*D]`，后二者直接转发不重排BSND。pool_key与Q同dtype，BSND为 `[B,P,1,D]`，分页需配套页表；weights为同dtype `[B,S,H]` 或 `[T,H]`。所有tensor同NPU、连续ND且物理存储与layout一致。

pool_tail_k必须host整数list/tuple `[B]`，每项0..pool_size-1，不能给NPU tensor；actual_seq_q/k也为host整数序列，分别是packed query累计结束位置和有效pooled-key长度。页表为NPU int32。topk是token级宽度，至少pool_size且按其倍数使用；pool_size>0、quant_mode仅-1、return_value必须False，key_stride0=-1仅表示未指定，Python不推导。

## 输出与验收边界

输出在query设备，为四维Q下 `[B,S,topk+pool_size-1]` 或二维/三维Q下 `[T,topk+pool_size-1]`，尾部无效槽-1，输入不改。layout前缀检查通过不代表任意后缀、shape和stride均获vendor支持。

需要单独构建csrc/attentions扩展及提供vendor算子的CANN/custom-op环境，仅主kernel wheel不足。来源表列arch35“已验证”，正文又明确binding无硬件精度/性能验收结论，arch22也未验证；本卡保留950范围draft并保留该矛盾，不把表中“已验证”当实测事件。

验收应确认扩展与vendor身份，使用独立确定性排名数据检查pool展开、host元数据与tail，不用auto和aclnn互相比当独立golden。

## 证据与复核范围

本卡依据固定提交的第一方API说明蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。
