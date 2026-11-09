---
type: Guide
title: vLLM Ascend packed cache 准备：C2 环、MXFP4 与折叠索引缓存
description: 串联 DeepSeek V4.1 packed cache 的物理 page/row、完成对、C2 device 元数据、FP32 compressor ring 与 MXFP4 128维量化/八行折叠；保留 A5 与共享路径边界。
aliases:
- DSV41_PACKED_CACHE C2 ring metadata
- quantize_mxfp4_indexer fold_indexer_cache_rows
- compressor_from_projected TOKEN_ALIGNED
tags:
- task.implementation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/packed_cache_slot_mapping.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/c2_ring_metadata.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/quantize_mxfp4_indexer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/fold_indexer_cache.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/compressor/compressor_triton.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/dsv41_cache.md
  role: constraint
created_at: '2026-11-03T06:14:54Z'
updated_at: '2026-11-03T06:14:54Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend packed cache 准备：C2 环、MXFP4 与折叠索引缓存

## 范围与坐标

固定 Main `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`；五个 Python 程序完整 AST 投影及 dsv41_cache 文档原文，不是实机结果。逻辑 token、物理 flat slot、page/row、compressed row 与 folded group 是不同坐标。文档明确 packed cache 由 A5 profile 的 DSV41_PACKED_CACHE 选择；共享 compressor/index preparation 的文件名不能扩展为全部硬件 packed 支持。

## 槽位和 C2 元数据

`packed_cache_slot_mapping.py` 只接受 ratio1/2。真实有效末端取 query_start_loc[actual_reqs] 与 actual_tokens 的较小值；negative slot、padding 写 -1。ratio2 同时要求 slot奇数、position奇数且非skip_update，physical=slot//2，再除PAGE_SIZE为page/row。ratio1直接用slot，**不消费skip_update来屏蔽全部写入**；不能把文档泛称的“跳过更新”套到所有比例。page_size正值、输出容量/布局、实际元数据范围仍由caller保证。

`c2_ring_metadata.py` 输出[5,R]控制：历史start=max(seq_len-query_len,0)、本轮used、query start、projection start、有效首block。skip_update令used=0且完成mask为false；完成的奇position取前一position作RoPE源，其余取0。even/padding也会读取RoPE表第0行而非不读，所以source表必须至少有合法row0。程序分别以64请求/16token块写控制和RoPE，shape检查不等于dtype/device/值范围全校验。graph重放保留地址但每次更新device内容。

## MXFP4 与八行折叠

`quantize_mxfp4_indexer.py` 固定最后维128，每32值一组，64数据字节+4 E8M0 scale字节。amax至少 `6*2^-126`，scale=amax/6向上取power-of-two指数并夹到[1,254]。E2M1 magnitude阈值用严格大于 `.25/.75/1.25/1.75/2.5/3.5/5`，幅度夹6，sign由value<0决定；不要换成未经对照的通用FP4 cast或假设tie-to-even。偶数值在低nibble，奇数值在高nibble。NaN/Inf的通用可靠语义没有完整显式输入校验，需独立测异常输入。

standalone先contiguous返回uint8 data/scales。fused writer要求[T,128]、int32/64[T,2]slots及uint8四维cache尾(1,64)/(1,4)，使用int64 page/row与真实页stride。负坐标不写cache，但仍读取输入并量化；非负超界不被自动clamp，caller要保证有效。`fold_indexer_cache.py` 再按8行组写544字节：前512为8×64 key，后32为8×4 scale；纯拷贝不再量化。page行数须8整除，slots需contiguous int32[T,2]，只更新选中行，其余保留。

## Compressor 参考入口与 projected 入口

`compressor_triton.py::compressor` 固定hidden5120/D512、ratio2..128；双projection到FP32后以逐维score softmax池化，**先round BF16再FP32 RMS**并写BF16，eps=1e-20。跨chunk的residual读旧ring，池化结束再写最后min(used,cache_size)行。meta由CPU/NumPy构造，tensor `_ints` 会D2H；32槽pinned upload ring的event仅保护staging复用，不证明所有消费者跨流生命周期都安全。该入口不能描述为完整device-only graph元数据。

`compressor_from_projected` 是另一路：要求同NPU contiguous FP32 K/score/ring、ring[blocks,32,2D]、int32[5,R]、正power-of-two D和token-aligned BF16 out；先zero out，ratio固定2，不做上述RMS。完成token位置写pool，其余保持零；block0为null保留，合法block>0才读写，这与允许index0的其他状态copy不同。metadata和max_query_len必须覆盖实际请求，空tokens/requests/query_bound早退。两入口共用helper但不能合并数值或null协议。

ring物理row被提升int64后乘cache_size*2D；D512时page65536越过int32元素坐标，是来源文档给出的回归边界。验证应检查大页距、非零storage offset、null/padding页不变、fresh/历史、ratio跨界、量化阈值/零值、折叠字节准确和graph新元数据。没有运行上游tests/NPU或给出本次性能收益。
