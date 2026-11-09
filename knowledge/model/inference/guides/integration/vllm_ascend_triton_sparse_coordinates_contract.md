---
type: Guide
title: vLLM Ascend Triton 稀疏坐标：DSpark 窗口、DCP 重映射与 PCP 搬运
description: 区分 DSpark logical/physical window、DCP order-preserving compact、PCP byte cache gather、MSA TopK postprocess 和 attention LSE anchor；供缓存越界、图padding与多卡索引诊断。
aliases:
- build_dspark_swa_slot_indices_triton build_dspark_swa_indices_triton
- remap_sparse_indices_triton copy_pcp_kv_cache
- prepare_attention_update index_decode_topk_fused
tags:
- task.implementation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/attention_update.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/batch_memcpy.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/build_window_indices.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/dsa_cp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/dspark_swa_indices.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/msa/msa_m3_index_postprocess.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/pcp_kv_cache.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/query_gather_prep.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/sparse_index_remap.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/spec_decode/dspark_swa_indices.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/dspark_swa_indices.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/msa_m3_index_postprocess.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/pcp_kv_cache.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/sparse_index_remap.md
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

# vLLM Ascend Triton 稀疏坐标：DSpark 窗口、DCP 重映射与 PCP 搬运

## 固定范围

固定 Main `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`，十个 Python 完整 AST 程序投影与四个文档原文读取。源码是实现与复现入口，本次未导入、执行JIT、NPU、多卡或性能测试。物理cache slot、逻辑token、稀疏block ID、DCP-local位置和LSE数值分别核对。

## 三类窗口不能互换

`build_window_indices.py` 对每query位置p产出 `length=min(p+1,W)`，从p+1-length到p，剩余-1；返回int32[T,1,W]与[T,1]，可用固定输出buffer。它没有block table，属于逻辑位置，负位置与输出stride/device等范围仍需caller保证。

`spec_decode/dspark_swa_indices.py` 对同请求全部draft query共用非因果窗口：prefix=seq_len-query_len，start=max(prefix-W,0)，visible=seq_len-start，枚举逻辑start+c。它用累计ends反查请求，**没有physical block table**。padding行在有效元数据下得零长度/-1，但query边界/seq_len有效性仍是caller契约。

`dspark_swa_indices.py` 是另一**物理slot**路径，先通过block table映射每列，再广播同请求多query。支持gate要求power-of-two block size、table pow2宽<=8192；实际wrapper本身不替caller完成所有gate检查。Q_POW2由spec+1决定，q_len不能超它，num_query_per_req决定capacity行带与清尾。FULL持久buffer必须传全容量而非active slice，否则pad cleanup会被裁掉并可能告警；缺省num_decode_tokens时 `.item()` 会Host同步。lens新分配固定int64，与eager随seq_lens dtype不同。文档记录A2/A3验证及950 fallback，不能从HAS_TRITON的静态检查推导所有硬件已跑。

## DCP 局部长度与稳定 compact

`dsa_cp.py` 将请求query区间裁到local_start/end，写local cumulative ends与缩短后的seq_len；没有本地query的请求seq_len=0。local_query_start_loc[0]由caller预置，kernel只写offset+1；可选start_pos仍是原seq_len-query_len，不能混作裁后end。

`sparse_index_remap.py` 对idx>=0按 `(idx//interleave)%dcp_size` 选owner，再转rank-local位置。先在<=128元素chunk里串行稳定compact并预填-1，再第二kernel按chunk顺序拼接，保留topk相对顺序。不能用原子reserve得到任意顺序来替代。文档记录旧编译器上tl.cumsum方案的稳定性问题，这是有版本的历史证据。wrapper会将非int32转换，转换前要确保值域；`rows=numel//topk_count`在空宽guard前计算，topk_count=0不是可靠安全入口，应由caller处理。正dcp/interleave、rank及真实index范围同样不能由签名自动保证。

## PCP 搬运、query准备与字节copy

`pcp_kv_cache.py` 用slot挑选行到contiguous packed：negative slot补零，two-cache拼K|RoPE，single C8将完整payload view为int8保留FP8/scale字节。真实cache stride参与寻址；非负slot须在allocation内。row batching按vector core与UB估计选1/2/4/8，单行和多行不同lowering，并非固定最优调参。它只准备all-gather输入，不完成collective/跨rank写回协议。

`query_gather_prep.py` 把token-major noPE|RoPE拼成head-major[H,T,D]，检查部分shape/dtype和tile可读范围；不满足fast-path返回None，caller应保留fallback。最后维按连续feature编址，不能传任意feature stride；shape相同也不能省略真实stride/地址核对。

`batch_memcpy.py` 每program从地址数组取一对uint8指针和字节数，分块masked copy，cast移到循环外；它不是memmove，不处理跨program overlap或提供producer/consumer同步。大小、地址、block power-of-two等由caller与Triton约束保证。

## MSA TopK 与 LSE anchor 的数值边界

`msa_m3_index_postprocess.py` 固定128token稀疏block，可见数 `max(0,(context+offset+128)//128)` 再clamp逻辑宽。prepare使不可见/补齐=-inf，initial=1e30、local=1e29，重叠时local覆盖initial。然后torch.topk，postprocess把不可见ID置-1并计数；tie不保证稳定ID顺序。contiguous score可能被原地修改，需原值先clone。K大于width会按16对齐扩存；score为0宽与negativecontext可处理，但可见score须初始化，forced sentinel并非压过任意浮点极值的数学保证。

`attention_update.py` 为多份LSE准备共同anchor与relative，最多16指针槽；无list长度和全形状检查，caller需非空且<=16、同rows与有效stride。无previous时anchor初值直接取L0，后续仅将finite score参加max；因此L0/previous的NaN或Inf不自动被统一修复。HAS_ANCHOR时第0relative保留 `score+(previous-anchor)` 特殊含义，不能当所有项都是score-anchor。该helper不是完整attention输出归并，也不为全空KV定义通用有限结果。

## Agent 验收

画出每一步坐标与sentinel，检查logical→physical、global→local、token→block、rawbytes→dtype的转换点。纯索引/搬运做精确比较，保留topk顺序、padding、未选行和guard；测试窗口跨block、超过一个compact chunk、每rank零贡献、empty请求、capacity变小后graph replay、table stride与大页址。LSE单独测finite、全-inf、NaN与previous anchor语义，并结合完整调用方判定。来源文档的历史加速比、测试计数与硬件矩阵不是本次实测。
