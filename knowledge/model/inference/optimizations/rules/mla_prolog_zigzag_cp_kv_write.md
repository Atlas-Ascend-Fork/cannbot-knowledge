---
type: Optimization
title: MLA CP Prefill：先恢复全序，再分别写计算与持久缓存
description: 更新当前MLA CP临时BSND、全序恢复、两类PA视图与真实物理槽散点写入，撤回旧连续布局限制。
tags:
- task.optimization
- topic.attention
- topic.kv_cache
- topic.parallelism
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/engine/execution_engine.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T14:49:38Z'
platforms:
- agnostic
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - prefill
      parallelism:
        all_of:
        - cp
      model_features:
        all_of:
        - mla
---

# MLA CP Prefill：先恢复全序，再分别写计算与持久缓存

## 当前两阶段写入

V3.2-Exp的npu_mla_prolog_v3在CP Prefill只计算本地token，先写临时BSND缓存 `[1,local_token_num,1,D]`，不传最终paged cache_index；INT8将nope、rope和scale打包，rope参数只占位。非CP用PA_BSND并传slot_mapping，直接写最终页。

CP分支AllGather各rank latent，按cp_metadata.restore_indices恢复每请求补齐后的全局顺序，再分别写两套PA空间：

| 视图 | 索引 | 生命周期 |
| --- | --- | --- |
| 当前层计算缓存 | global_slot_mapping/global_block_table | 包括补齐token，供两段因果FA使用，消费后释放引用 |
| 后续Decode/传输缓存 | persistent_valid_indices选真实token，再按persistent_slot_mapping写 | Offline为请求所有者，PREFILL角色为全局有效token |

当前写回使用npu_scatter_nd_update_，不再要求每batch从0连续分配，也不使用全零kv_scatter_update_indices或旧reverse_split_list。Indexer Key与INT8 scale也必须采用对应计算/持久视图，不能只修正主MLA KV。

## 正确性与验收

本地token直接配全局slot会错位；AllGather后未恢复顺序也会错。写入合法物理页的关键是token与对应slot一致，而不是某个scatter API天然正确。Q的头尾长度必须与计算视图因果坐标一致，padding不能泄漏进持久缓存或输出。

覆盖CP1/CP>1、INT8/非量化、多请求不等长、无本地所有者和offload；逐token对齐非CP基线，并检查缓存实际消费地址。关闭CP回到非CP直写路径时仍需重核组、缓存和配置。见[ZigZag因果长度](causal_cp_prefill_zigzag_actual_seqlens.md)。本次为静态源码核对。


## Evidence

- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py)（primary）
- [execution_engine.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/engine/execution_engine.py)（implementation）
- [indexer.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py)（implementation）
