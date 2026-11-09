---
type: Runbook
title: Attention元数据复用：限定step与请求布局
description: Attention元数据仅可在相同step、请求行序和完整依赖布局内复用；按实际metadata builder/backend核对失效条件，recipes键名及事件不作框架通用协议。
tags:
- task.optimization
- topic.attention
- topic.kv_cache
- topic.performance.analysis
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:36:07Z'
platforms:
- '950'
aliases:
- DeepSeek V4.1 Attention元数据的step复用边界
---

# Attention元数据复用：限定step与请求布局

## 适用性与框架边界

本卡是**可迁移机制**：元数据只有在依赖值、请求组成/行序、算子布局和存储有效期都一致时才能复用。可共享的是同一步中合同相同的执行计划或派生输入；不是跨请求、跨 step 永久缓存，也不是所有层共享同一对象的建议。

recipes 的 `kernel_metadata` 字典、ratio0/2/1、c2a/c1a、CP prev/next、event0/1/2 与发布点是具体方案；全头生成器和现有 TODO 也限定其可复用范围。其他引擎应依据自己的 builder 输出和 backend 合同决定可复用部分，不能复制键名或事件编号。

vLLM 读者可从 **ModelRunner 的输入准备、attention metadata builder 与实际 Attention backend**核对依赖；Scheduler 选择本 step 的请求/token，不能据此把全部 metadata 构造归给它。未验证 vLLM 的具体对象、模型或后端，角色对应仅帮助定位自有实现。

## 现象

推理性能分析中，每个解码层都出现相似的长度计算、slot dtype 转换、元数据生成或主机到设备传输，可检查它们是否只依赖本次请求状态，能够移到层循环之前。复用的是描述算子如何执行的 metadata（元数据/执行计划），不是跨步不变的 KV 内容；依赖变化后沿用旧计划也可能造成错误。

要做这类移动，先给派生输入写出依赖集合、所属 step/请求行序与最后消费者。下面的 recipes 例子中，DeepSeek V4.1 的历史修改把窗口写入槽归一化、压缩 top-k 长度和 Attention 元数据移到 step 入口，当前还统一生成 Indexer 元数据。step 指本次前向处理的一批查询，可能是 Prefill（整段提示词）或 Decode（逐步生成）。素材没有成对 profiler 结果，本卡解释已实现的复用边界，不承诺收益。

## 适用场景

诊断适用于自有引擎的计划/长度派生复用；下文精确对象与生成器只覆盖混合量化 MLA（多头潜在注意力）和 QLI/QSLI 的“生成元数据 → 执行算子”双入口集成。QLI 是量化 Lightning 索引器，QSLI 是在候选块内选择的量化稀疏 Lightning 索引器，二者用于决定 Attention 读取哪些历史 KV（Key/Value，键/值）。源码目标 950，CANN/torch_npu 版本与 NPU 运行未验；适用粒度 `same_operator`，路线优先级 `recommended_fastpath` 仅表示当前实现，保持静态诊断草稿。

CP（上下文并行）把长提示词分给多个设备，Zigzag 前后两段的因果可见范围不同，各有一份元数据。TP（张量并行）会改变头的分布；当前生成器使用模型全头数，并留有 TP 分片头支持的 TODO，不能外推成任意头分片都可共用。

## 根因与判别方法

先列出自有元数据的真实依赖：step 身份、请求集合/行序与有效边界、布局/头数、算法参数以及异步存储寿命；仅当这些依赖一致才考虑共享。再分清长度的轴和单位，决定失效条件。下表字段为 recipes 示例，其他引擎按职责对应。以下数值都应来自本次真实请求，而非缓存容量或 padding 后总 shape。

| 元数据 | 轴与含义 | 生产者 → 消费者 |
|---|---|---|
| `actual_seq_k [B]` | B 个请求各自的真实历史 KV 长度，单位为原始 token | 请求状态 → 压缩长度/索引器 |
| `position_ids [T]` | packed T 行 query 各自的请求内零基绝对位置 p | 输入准备 → 因果可见长度 |
| `cu_seq_lens_q [B+1]` | 累计 query 行边界，首项0；相邻差是本次该请求的 query 数 | 打包器 → Attention/Indexer |
| r、压缩长度/余数 | 每 r 个原始 token 对应一个压缩位置；长度为 L//r，余数为 L%r | 请求真实 L → 压缩 reader |
| `cmp_topk_length [T,1]` | 当前路径每 query 可见压缩位置数 `min(floor((p+1)/r),index_topk)` | query 位置 → Attention 元数据与执行 |
| window/cache slots | 每个待写行的物理槽，`-1` 无效；普通窗口 block 0 保留为 null | 调度与 CP 更新 → 归一化 → writer |
| `kernel_metadata[类型]` | 依赖长度、头数、通道、layout、量化模式等的算子执行计划 | step 生成器 → 各层对应算子 |

**教学推演，非元数据执行观测。** 两请求历史长度为5和8，本次分别处理末尾2行和1行，query 位置为 `[3,4,7]`，累计 query 边界为 `[0,2,3]`。取 r=2 且 top-k 预算足够，按请求得到压缩长度 `[2,4]`、余数 `[1,0]`；按 query 得到可见长度 `[2,2,4]`。这两组长度不能互换。下一步请求长度或位置变化，就应重新生成计划；同一步内相同契约的层才可共用。若选择器主动只留下更少候选，位置公式也不能自动替代真实有效候选数。

recipes 当前 Attention 按 ratio 0/2/1 分别生成，其中0只有窗口，1仍有共享 KV；Indexer 固定生成 c2a QLI、c1a candidate QLI、c1a QSLI。CP prev/next 再各生成一套，层内只按键读取。

多流时还要分别检查执行顺序与存储寿命，按自有后端的完成通知与所有权协议核对。recipes 的具体发布序列为：生产端先记录 event0，元数据流等待输入依赖；Attention 元数据发布后记录 event1，再生成 Indexer 元数据并记录 event2。Attention 层0等1，首个 Indexer 等2。`record_stream` 用于跟踪异步使用期间的 Tensor 生命周期，不能代替消费者等待；这些 helper 还受开关与执行模式影响，不能凭名字推断任意图模式都具有同样保证。

## 快速检查

1. 在自己的框架找到元数据 builder、层循环与算子执行入口，记录每 step 实际调用次数及依赖输入。只有依赖请求状态、与层参数无关的部分才有复用候选资格；若某层头布局或预算不同，应使用不同计划。
2. 从请求状态、打包器和 selector 分别取真实 L、p、累计 query 边界和有效候选长度，用上例同样的方法核算。请求轴与 query 轴错配时先修数据流，不能用相同 shape 证明可复用。
3. 核对复用/失效条件覆盖 step、请求集合与行序、有效长度、算法分支、头数/layout及分段可见范围。改变任一依赖后检查是否重建；在 recipes 中还应区分 ratio、窗口/压缩类型与 CP prev/next。不同合同共用计划或跨步直接沿用，支持缓存边界过宽。
4. 沿实际 stream/graph 模式检查生产、复制、发布、等待以及 Tensor 存活。预期消费者在对应计划可用后执行，且存储未提前回收。只调用 record_stream 或只看到 event 对象存在，都不足以排除竞态；还需读 helper 分支和运行时间线。
5. 在目标环境比较上移前后元数据字节、Attention 输出和每 step 调用次数，覆盖长度变化、padding、CP 与 capture/replay（图捕获/回放）。若字节不同，先定位哪项依赖变了；字节相同但输出异常，继续查消费顺序、缓存内容和实际算子版本。QSLI 计划长度与 QLI 实际输出长度也须成对核对。

## 完整代码

下列 recipes 完整实现用于核对本文证据。按块外导读比较输入、轴与生产消费关系；外部引擎应先完成上面的职责和接口检查。

<details>
<summary>recipes 元数据对照：完整生成器、长度轴与事件生产消费</summary>

### 上移前：层内调用metadata算子

前版每层 prepare_fa_kwargs 都先拼好窗口/压缩参数，再调用 metadata 算子并复制到 Q 设备。输入 q 的头数与通道直接参与计划；理解这点才能判断上移后哪些层可以共享。

```python
    def prepare_fa_kwargs(
        self,
        q: torch.Tensor,
        win_kv: torch.Tensor,
        cmp_kv: Optional[torch.Tensor],
        cmp_sparse_indices: Optional[torch.Tensor],
        attn_metadata: Dict,
        is_prefill: bool,
    ):
        # V4.1 ratio 0 is window-only; ratio 1 still has indexed shared KV.
        has_cmp_kv = self.compress_ratio > 0
        win_key = "full_kv" if is_prefill else "win_kv"
        attn_kwargs = {
            "q": q,
            "win_kv": win_kv.view(torch.uint8),
            "win_sparse_indices": attn_metadata["win_sparse_indices"],
            "win_block_table": attn_metadata["block_table"][win_key],
            "cu_seqlens_q": attn_metadata["cu_seq_lens_q"],
            "seqused_q": None,
            "seqused_win_kv": attn_metadata["actual_seq_k"],
            "win_topk_length": attn_metadata["win_topk_length"],
            "sinks": self.attn_sink.detach(),  # The DSL ABI requires a plain Tensor.
            "quant_mode": 1,
            "softmax_scale": self.softmax_scale,
            "layout_q": "TND",
            "layout_kv": "PA_BBND",
            "return_softmax_lse": False,
        }
        if has_cmp_kv:
            # Preserve shared_idx; only the FA input uses zero-based [T, 1, K] indices.
            cmp_sparse_indices = cmp_sparse_indices.reshape(q.shape[0], 1, cmp_sparse_indices.shape[-1])
            cmp_sparse_indices = F.pad(
                cmp_sparse_indices, (0, self.config.index_topk - cmp_sparse_indices.shape[-1]), value=-1)
            ratio_key = str(self.compress_ratio)
            attn_kwargs.update({
                "cmp_kv": cmp_kv,
                "cmp_sparse_indices": cmp_sparse_indices,
                "cmp_block_table": attn_metadata["block_table"][f"c{ratio_key}a_cmp_kv"],
                "seqused_cmp_kv": attn_metadata["compressed_seq_lens"][ratio_key],
            })
            attn_kwargs["cmp_topk_length"] = attn_metadata["cmp_topk_length_by_ratio"][ratio_key]
        cmp_topk_length = attn_kwargs.get("cmp_topk_length")
        if cmp_topk_length is None:
            # The metadata operator requires both length tensors, even for WIN.
            cmp_topk_length = torch.zeros_like(attn_kwargs["win_topk_length"])
        metadata = self.sparse_attn_metadata_ops(
            attn_kwargs["win_topk_length"],
            cmp_topk_length,
            cu_seqlens_q=attn_kwargs["cu_seqlens_q"],
            num_heads_q=q.shape[1],
            num_heads_kv=win_kv.shape[2],
            head_dim=q.shape[-1],
            quant_mode=attn_kwargs["quant_mode"],
            layout_q=attn_kwargs["layout_q"],
            layout_kv=attn_kwargs["layout_kv"],
            has_win_kv=True,
            has_cmp_kv=has_cmp_kv,
        )
        attn_kwargs["metadata"] = metadata.to(q.device)
        return attn_kwargs
```

### 上移后：层内只读已生成metadata

后版只从 kernel_metadata 按 attention_type 取计划，其余候选、长度、表仍是执行参数。此函数返回 kwargs，不执行 Attention，也不会验证计划是否属于本 step。

```python
    def prepare_fa_kwargs(
        self,
        q: torch.Tensor,
        win_kv: torch.Tensor,
        cmp_kv: Optional[torch.Tensor],
        cmp_sparse_indices: Optional[torch.Tensor],
        attn_metadata: Dict,
        is_prefill: bool,
    ):
        # V4.1 ratio 0 is window-only; ratio 1 still has indexed shared KV.
        has_cmp_kv = self.compress_ratio > 0
        win_key = "full_kv" if is_prefill else "win_kv"
        attn_kwargs = {
            "q": q,
            "win_kv": win_kv.view(torch.uint8),
            "win_sparse_indices": attn_metadata["win_sparse_indices"],
            "win_block_table": attn_metadata["block_table"][win_key],
            "cu_seqlens_q": attn_metadata["cu_seq_lens_q"],
            "seqused_q": None,
            "seqused_win_kv": attn_metadata["actual_seq_k"],
            "win_topk_length": attn_metadata["win_topk_length"],
            "sinks": self.attn_sink.detach(),  # The DSL ABI requires a plain Tensor.
            "quant_mode": 1,
            "softmax_scale": self.softmax_scale,
            "layout_q": "TND",
            "layout_kv": "PA_BBND",
            "return_softmax_lse": False,
            "metadata": attn_metadata["kernel_metadata"][f"{self.attention_type}_metadata"],
        }
        if has_cmp_kv:
            # Preserve shared_idx; only the FA input uses zero-based [T, 1, K] indices.
            cmp_sparse_indices = cmp_sparse_indices.reshape(q.shape[0], 1, cmp_sparse_indices.shape[-1])
            cmp_sparse_indices = F.pad(
                cmp_sparse_indices, (0, self.config.index_topk - cmp_sparse_indices.shape[-1]), value=-1)
            ratio_key = str(self.compress_ratio)
            attn_kwargs.update({
                "cmp_kv": cmp_kv,
                "cmp_sparse_indices": cmp_sparse_indices,
                "cmp_block_table": attn_metadata["block_table"][f"c{ratio_key}a_cmp_kv"],
                "seqused_cmp_kv": attn_metadata["compressed_seq_lens"][ratio_key],
            })
            attn_kwargs["cmp_topk_length"] = attn_metadata["cmp_topk_length_by_ratio"][ratio_key]
        return attn_kwargs
```

### step级窗口cache slot归一化

窗口 slot 归一化把写入槽展平为 int64，并把保留 null block 范围映射为-1。它在窗口和 CP 元数据更新之后执行，不能提前对未完成的映射做缓存。

```python
    def _prepare_cache_slot_mapping(self, attn_metadata):
        """Normalize cache-write slots after window and CP metadata updates."""
        cache_slot_mapping = {}
        for key in ("win_kv", "full_kv"):
            slot_mapping = attn_metadata["slot_mapping"].get(key)
            if slot_mapping is None:
                continue
            slots = slot_mapping.reshape(-1).long()
            valid = slots >= self.block_size
            cache_slot_mapping[key] = slots.masked_fill(~valid, -1)
        return cache_slot_mapping
```

### 真实请求KV长度与压缩余数

请求轴上的真实 KV 长度分别除以每个 ratio，产生长度和余数两个字典。两者是后续 QLI 因果/压缩处理的输入，不能由 query Tensor 总行数替代。

```python
    def _add_compressed_seq_metadata(self, attn_metadata):
        actual_seq_k = attn_metadata["actual_seq_k"]
        compressed_seq_lens = {}
        compressed_seq_remainders = {}
        for ratio in dict.fromkeys(self.config.compress_ratios):
            if ratio < 1:
                continue
            ratio_key = f"{ratio}"
            compressed_seq_lens[ratio_key] = actual_seq_k // ratio
            compressed_seq_remainders[ratio_key] = actual_seq_k % ratio
        attn_metadata["compressed_seq_lens"] = compressed_seq_lens
        attn_metadata["compressed_seq_remainders"] = compressed_seq_remainders
```

### step级query可见压缩top-k长度

query 轴上的位置决定每个查询能看到多少已完成压缩位置，结果截到 index_topk。ratio0 对应全零压缩长度；这只是当前模型的可见位置口径，不是任意 selector 的有效计数算法。

```python
    def _prepare_cmp_topk_lengths(self, attn_metadata, device):
        """Compute valid compressed top-k lengths for every query once per step."""
        positions = attn_metadata["position_ids"].reshape(-1).to(device=device)
        lengths = {"0": torch.zeros_like(attn_metadata["win_topk_length"])}
        for ratio in dict.fromkeys(self.config.compress_ratios):
            if ratio <= 0:
                continue
            valid_length = (positions + 1) // ratio
            lengths[str(ratio)] = (
                valid_length.clamp_max(self.config.index_topk)
                .to(torch.int32)
                .view(-1, 1)
            )
        return lengths
```

### 当前完整Attention/LI metadata发布与CP分段

生成器先选普通单份或 CP 两份 metadata，再为每份生成 Attention 类型计划并发布 event1；随后生成 LI（Lightning Indexer）计划并发布 event2。record_stream 与 record/wait 的职责不同，阅读时不要把寿命记录当成执行屏障。

```python
    def generate_kernel_metadata(self, attn_metadata):
        enable_metadata_multi_streams = self.enable_multi_streams
        metadata_stream = attn_metadata.get("metadata_stream")
        main_stream = torch.npu.current_stream() if enable_metadata_multi_streams else None
        if attn_metadata["is_prefill"] and self.cp_size > 1:
            # Each zigzag segment runs its own attention call and needs its own tiling metadata.
            target_metadata = [attn_metadata["prev"], attn_metadata["next"]]
        else:
            target_metadata = [attn_metadata]

        record_event(enable_metadata_multi_streams, self.metadata_event, 0)
        with npu_stream_switch(enable_metadata_multi_streams, metadata_stream):
            wait_event(enable_metadata_multi_streams, self.metadata_event, 0)
            device = attn_metadata["position_ids"].device
            for cur_metadata in target_metadata:
                win_topk_length = cur_metadata["win_topk_length"]
                for ratio in (0, 2, 1):
                    attention_type = "win" if ratio == 0 else f"c{ratio}a"
                    cmp_topk_length = cur_metadata["cmp_topk_length_by_ratio"][str(ratio)]

                    metadata = self.sparse_attn_metadata_ops(
                        ori_topk_length=win_topk_length,
                        cmp_topk_length=cmp_topk_length,
                        cu_seqlens_q=cur_metadata["cu_seq_lens_q"],
                        # TODO: Support TP-sharded query heads in sparse attention metadata.
                        num_heads_q=self.config.num_attention_heads,
                        num_heads_kv=1,
                        head_dim=self.config.head_dim,
                        quant_mode=1,
                        layout_q="TND",
                        layout_kv="PA_BBND",
                        has_ori_kv=True,
                        has_cmp_kv=ratio > 0,
                    )
                    metadata = metadata.to(device, non_blocking=True)
                    cur_metadata["kernel_metadata"][f"{attention_type}_metadata"] = metadata
                    record_stream(enable_metadata_multi_streams, metadata, main_stream)

            # Layer 0 only needs sparse-attention metadata.  Let it start
            # before the independent Indexer metadata is completed.
            record_event(enable_metadata_multi_streams, self.metadata_event, 1)
            # Each zigzag segment scores the cache on its own lengths, so it needs its own
            # Indexer metadata as well.
            for cur_metadata in target_metadata:
                self._generate_li_kernel_metadata(cur_metadata, main_stream)
            record_event(enable_metadata_multi_streams, self.metadata_event, 2)
```

### 当前完整QLI/QSLI metadata构造

Indexer 生成器固定构造三种配置，分别对齐 c2a QLI、c1a candidate QLI、c1a QSLI。candidate_lengths 为当前 ratio1 可见块数估计，真正 QSLI 执行还读取 QLI 返回的长度，两者一致性需部署检查。

```python
    def _generate_li_kernel_metadata(self, attn_metadata, main_stream):
        """Generate and publish the fixed V4.1 QLI/QSLI metadata."""
        enable_metadata_multi_streams = self.enable_multi_streams
        position_ids = attn_metadata["position_ids"]
        candidate_topk = self.config.candidate_topk_blocks
        candidate_size = self.config.candidate_block_size
        qli_ratio = 2
        qli_candidate_ratio = 1
        qsli_ratio = 1

        qli_metadata = self.quant_lightning_indexer_metadata_ops(
            cu_seqlens_q=attn_metadata["cu_seq_lens_q"],
            seqused_q=None,
            seqused_k=attn_metadata["compressed_seq_lens"][str(qli_ratio)],
            cmp_residual_k=attn_metadata["compressed_seq_remainders"][str(qli_ratio)],
            batch_size=attn_metadata["actual_seq_k"].shape[0],
            max_seqlen_q=-1,
            max_seqlen_k=-1,
            num_heads_q=self.config.index_n_heads,
            num_heads_k=1,
            head_dim=self.config.index_head_dim,
            topk=self.config.index_topk,
            mask_mode=3,
            cmp_ratio=qli_ratio,
            layout_q="TND",
            layout_k="PA_BBND",
            candidate_topk_blocks=-1,
            candidate_block_size=-1,
        ).to(position_ids.device, non_blocking=True)
        attn_metadata["kernel_metadata"]["c2a_qli_metadata"] = qli_metadata
        record_stream(enable_metadata_multi_streams, qli_metadata, main_stream)

        qli_candidate_metadata = self.quant_lightning_indexer_metadata_ops(
            cu_seqlens_q=attn_metadata["cu_seq_lens_q"],
            seqused_q=None,
            seqused_k=attn_metadata["compressed_seq_lens"][str(qli_candidate_ratio)],
            cmp_residual_k=None,
            batch_size=attn_metadata["actual_seq_k"].shape[0],
            max_seqlen_q=-1,
            max_seqlen_k=-1,
            num_heads_q=self.config.index_n_heads,
            num_heads_k=1,
            head_dim=self.config.index_head_dim,
            topk=self.config.index_topk,
            mask_mode=3,
            cmp_ratio=qli_candidate_ratio,
            layout_q="TND",
            layout_k="PA_BBND",
            candidate_topk_blocks=candidate_topk,
            candidate_block_size=candidate_size,
        ).to(position_ids.device, non_blocking=True)
        attn_metadata["kernel_metadata"]["c1a_qli_candidate_metadata"] = qli_candidate_metadata
        record_stream(enable_metadata_multi_streams, qli_candidate_metadata, main_stream)

        candidate_lengths = torch.div(
            position_ids.reshape(-1) + qsli_ratio * candidate_size,
            qsli_ratio * candidate_size,
            rounding_mode="floor",
        ).clamp_min(1).clamp_max(candidate_topk).to(torch.int32).view(-1, 1)
        qsli_metadata = self.quant_sparse_lightning_indexer_metadata_ops(
            candidate_block_length=candidate_lengths,
            cu_seqlens_q=attn_metadata["cu_seq_lens_q"],
            seqused_q=None,
            seqused_k=attn_metadata["compressed_seq_lens"][str(qsli_ratio)],
            cmp_residual_k=None,
            batch_size=attn_metadata["actual_seq_k"].shape[0],
            max_seqlen_q=-1,
            max_seqlen_k=-1,
            num_heads_q=self.config.index_n_heads,
            num_heads_k=1,
            head_dim=self.config.index_head_dim,
            topk=self.config.index_topk,
            quant_mode=1,
            candidate_block_size=candidate_size,
            mask_mode=3,
            cmp_ratio=qsli_ratio,
            layout_q="TND",
            layout_k="PA_BBND",
        ).to(position_ids.device, non_blocking=True)
        attn_metadata["kernel_metadata"]["c1a_qsli_metadata"] = qsli_metadata
        record_stream(enable_metadata_multi_streams, qsli_metadata, main_stream)
```

### 当前消费者等待：Attention层0与首个Indexer

以下两份完整方法与前面的producer事件配对；这只是代码依赖关系，尚无多流或capture/replay运行结果。

Attention 消费端在层0等待 event1，CP 则在等待后分别用 prev/next 的计划执行两段，再合并输出。该调用关系说明依赖设计，不是多流无竞态的运行证明。

```python
    def sparse_attn(self, q, win_kv, cmp_kv, cmp_sparse_indices, attn_metadata, is_prefill):
        if is_prefill and self.cp_size > 1:
            if self.layer_idx == 0:
                wait_event(self.enable_multi_streams, attn_metadata["metadata_event"], 1)
            # The two zigzag segments see different causal ranges, so each runs with its own metadata.
            q_prev, q_next = q.chunk(2, dim=0)
            if cmp_sparse_indices is None:
                idx_prev, idx_next = None, None
            else:
                idx_prev, idx_next = cmp_sparse_indices.chunk(2, dim=0)
            o_prev = self.sparse_attn_ops(**self.prepare_fa_kwargs(
                q_prev, win_kv, cmp_kv, idx_prev, attn_metadata["prev"], is_prefill))[0]
            o_next = self.sparse_attn_ops(**self.prepare_fa_kwargs(
                q_next, win_kv, cmp_kv, idx_next, attn_metadata["next"], is_prefill))[0]
            output = torch.cat([o_prev, o_next], dim=0)
            return self.select_local_attn_heads(output)
        fa_kwargs = self.prepare_fa_kwargs(q, win_kv, cmp_kv, cmp_sparse_indices, attn_metadata, is_prefill)
        if self.layer_idx == 0:
            wait_event(self.enable_multi_streams, attn_metadata["metadata_event"], 1)
        return self.select_local_attn_heads(self.sparse_attn_ops(**fa_kwargs)[0])
```

首个 Indexer 等 event2 后进行 Q/W 前处理、可能的来源层 K 写入及索引计算。只有需要这些计划的消费者才在这里等待，不能删除等待后以单流样例通过作为优化证明。

```python
    def forward(
        self,
        x: torch.Tensor,
        qr: torch.Tensor,
        attn_metadata: Dict,
        latent,
        kv_cache,
        offset: int = 0
    ):
        if self.is_first_indexer:
            wait_event(
                self.enable_metadata_multi_streams,
                attn_metadata.get("metadata_event"),
                2,
            )
        cos, sin = attn_metadata["cos_sin"]["comp"]
        # Fused scope: MXFP8 quantization of qr, MXFP8 Q projection with wq_b,
        # partial RoPE on Q, MXFP4 Q quantization, and weights_proj(x) with
        # softmax scaling. The native implementation preserves this same scope.
        q, q_scale, weights = OpKernel.indexer_prolog_qw(self, x, qr, cos, sin)

        if attn_metadata["is_prefill"] and self.cp_size > 1:
            return self.forward_cp(q, q_scale, weights, latent, attn_metadata, kv_cache, offset)

        if self.owns_k and latent is not None:
            self.update_indexer_cache(latent, attn_metadata, kv_cache)
        return self.compute_sparse_indices(
            q, q_scale, weights, kv_cache.indexer_cache, kv_cache.indexer_cache_scale,
            attn_metadata, offset, getattr(kv_cache, "indexer_qsli_cache", None))
```

</details>

## 设计决策

先区分可共享的纯派生值、具有请求所有权的映射与 backend 专属执行计划；只提升依赖相同的部分，并保留使消费可见与存储存活的边。复用的是同一步、同请求布局且具有相同算子契约的元数据，不是跨请求/跨step永久缓存。recipes 中，QLI/QSLI metadata当前固定针对c2a QLI、c1a candidate QLI、c1a QSLI；新增压缩ratio需同时修改producer与consumer键，不能仅改变模型config。QSLI metadata的候选块长度按 `floor((p+G)/G)` 在当前ratio=1路径裁剪到候选块预算，实际QSLI仍读取candidate source返回的candidate_lengths；二者一致性要由部署验收确认。

## 系统信息

recipes 实现需要同一步生成的position_ids、cu_seq_lens_q、actual_seq_k、block_table与slot_mapping。前者描述每query因果位置，actual_seq_k描述每请求真实长度，cu_seq_lens_q描述packed query边界；它们的轴与padding约定不同，不能靠同一shape替代。

## 性能影响

源码显示层内metadata算子调用与重复长度计算被移出；减少调用次数的机制可重建，时延与内存收益未测量。主线仍有部分dtype转换和QSLI slot构造的host读取，不能笼统宣称所有小算子或同步都已消失。

## 部署验收

待验：对同输入比对上移前后的metadata字节与Attention输出，统计每step实际metadata调用次数；覆盖多请求不同有效长度、压缩余数、padding、CP prev/next、capture/replay时step长度变化。确认每个消费者在对应event之后执行，并核对QSLI实际candidate_lengths与metadata用长度。本轮未执行。

## 验证信号

本轮只读取固定 Git 源码并恢复原始 blob 与函数字节。以下是实现的静态核对结果，不是模型/NPU 执行结果；未运行源仓脚本、测试、编译或推理。

- 历史前后函数证实metadata算子由层内调用改为读取kernel_metadata；当前生成器在step入口按类型生成并记录完成事件。（来源平台：950源码目标，未上板；证据等级：artifact_verified；范围：源码）
- 当前长度函数使用真实request KV长度、query position及压缩ratio，CP每个segment独立生成，不以Tensor首维估算有效长度。（来源平台：950源码目标，未上板；证据等级：artifact_verified；范围：源码）

## 预防

在缓存元数据之前先列明它依赖的所有长度、layout、head数与候选预算；每个维度变化都应触发重新生成，producer/consumer键和stream依赖一起审查。

## 坏实践

把任意padding shape套入`floor((p+1)/r)`；跨step复用旧metadata；CP两段共用一份metadata；去掉wait只看单流样例通过；仅凭源码移除一处算子就填写性能百分比。

## 失效边界

当前固定ratio集合、全头metadata与低时延头切分存在模型专用约束；源码还有TP-sharded query heads的TODO，不能推广为任意TP metadata公式。候选源未产齐可见位置、可变候选预算或外部算子更改mask规则时需重验长度口径。缺少runtime、graph replay和多流竞态输出，复用正确性仍需上板验收。
