---
type: Guide
title: vLLM Ascend Triton GLM KPool：尾环写入与逻辑索引执行契约
description: 保留旧 Triton GLM KPool 的 FP32 raw tail、BF16 completed pool、两阶段防覆盖、head 加权打分、256MiB scratch 与 tail packing；与现 CANN 模型路径区分，供迁移和回归诊断。
aliases:
- glm5_next_kpool_tail_compress_and_write_cache_triton
- glm5_next_lightning_indexer_triton
- FP32 KPool tail ring PACK_TAIL
tags:
- task.implementation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/glm5_next_kpool_tail_compress.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/glm5_next_lightning_indexer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/glm5_next_kpool_tail_compress.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/glm5_next_lightning_indexer.md
  role: constraint
created_at: '2026-11-03T06:14:54Z'
updated_at: '2026-11-04T03:05:17Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Triton GLM KPool：尾环写入与逻辑索引执行契约

7d9e取消中间版本的INT8 completed-pool与pooled_scales路径，见[7d9e运行时差异](vllm_ascend_7d9e_runtime_delta_contract.md)的KPool节。wrapper签名、cache dtype与scale buffer应按同一提交核对，不能只改一个dtype沿用旧ABI。

## 固定来源与派发边界

固定 Main `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`，两个程序完整 AST 投影、两个配套文档原文读取；未导入、JIT、NPU 或测量。现 GLM 模型 CANN 路径与历史 Triton helper 的派发/测试状态，按[KPool空工作量 Runbook](../../runbooks/runtime/vllm_ascend_kpool_empty_work_graph_contract.md)判断；不能因 helper 仍存在便当生产默认或已验收回退。

## 尾环：先完成所有历史读，再播种新尾

`glm5_next_kpool_tail_compress.py` 使用 FP32 K/gate、FP32 `[blocks,2,C,D]` tail 和 BF16 `[blocks,B,1,D]` completed cache。P=index_kpool、C>=P；每请求只用 tail table 第0列，历史 p 在该页内 `p%C`，APE 按 pool offset 编址。两平面与所有页 stride 保留，不可与现 CANN `[blocks,C,2D]` 直接 view 互换。

第一 launch 只对非负、有效 slot、真实 query 末端前且 `(pos+1)%P==0` 的 token 产出 completed pool；本轮 query 内直接读 K/gate，较早行读旧 tail，逐维 softmax(gate+APE) 加权 K。第二 launch 每请求仅播种最后 min(query_len,C) 行，保证连续位置下 modulo-C 目的唯一；短请求保留其余历史。顺序避免长 prefill 的新写覆盖仍需读取的旧历史，不能融合后依赖 program 顺序。

非 MTP C=P 保留未完成池；MTP C=P+spec 保留 committed open pool 与候选，拒绝后逻辑长度回退、替换 token 覆盖对应槽。它不能重建未初始化历史，prefix hit 要 pool 对齐或提供重建。head dim 可按最高128列 tile拆分，地址仍用物理 stride。`compute_topk=False` 的 caller 仍需推进两个 cache；它不是 kernel 自己的选择参数。FP32 tail 改 BF16 会引入跨 chunk 舍入差异，应作为独立数值变更。

## 选择：完整池打分、扩展和 causal tail

`glm5_next_lightning_indexer.py` 先 FP32 计算 `qbar=sum_heads(weights*query)`，对 `min((pos+1)//P,pool_len)` 个可见池打分，`torch.topk` 取至多 topk/P 池并扩展为逻辑 token，不是物理 cache slot。NaN/负无穷和不可见项映射最低有限 FP32，正无穷映射最高有限值；最低 sentinel 不参与有效扩展。相等分数无稳定顺序保证。

输出宽 `topk+P-1`，缺省 tail 在 topk 后；`pack_tail=True` 时接在 `min(floor((pos+1)/P)*P,topk)` 后。真实末端外行和 alignment 列写-1，已有 output buffer 需要同设备 int32、连续列、非重叠行与足够容量；T之后行不动。P、D、topk倍数、request ends 和 cache block 有效性是调用契约，物理块 clamp 不能修复坏元数据。

score 按256MiB预算切 token chunk，但至少分配一整行，极长单行仍可能超预算。可选 prefill packed cache 另有256MiB预算，条件含 tokens>=32、多于请求行、可选择池且完整 span适合 int32；两个 scratch 不能只算一个。FULL 图由模型禁用 packing，因为 padded rows 不证明重用且 replay 不重新跑 Python dispatch。索引扩展在512行门槛切256/4096列块，打分使用128池 tile等形状规则；这些是固定源码策略，不是硬件通用最优参数。

全 cache span适合int32时用vector offsets；更大时用int64页基址+int32页内偏移，要求页内span不超int32且block size为2次幂。所有请求末端非降、位置与seq_len一致，cache有效页、query/weights布局均需caller保证。有效元数据不因“返回shape正常”而得到证明。

## Agent 复现与迁移判据

记录旧/新入口、P/C/D、global写入与local选择坐标、真实页stride、cache dtype、prefix与MTP回退状态。覆盖跨pool与环绕、long prefill、query内外混合历史、拒绝重算、空池/空query、图padding、输出额外行和大于int32的物理span。索引做精确语义比较并允许等分tie，pool输出按BF16舍入参考；现 CANN迁移另外验证布局转换与synthetic过滤。源码和历史文档不构成当前所有硬件的精度/性能验收。
