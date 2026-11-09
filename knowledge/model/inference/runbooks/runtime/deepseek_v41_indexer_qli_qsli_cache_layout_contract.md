---
type: Runbook
title: 量化Indexer缓存错读：区分独立scale与合并记录
description: Indexer接口诊断：仅匹配本文QLI/QSLI及K writer时使用split/combined规则；须联合验证scale编码、候选单位、实际slot分支与生产消费版本。
tags:
- task.debugging
- topic.attention
- topic.kv_cache
- topic.compute.quantization
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:36:07Z'
platforms:
- '950'
aliases:
- DeepSeek V4.1 QLI与QSLI的缓存消费单位
---

# 量化Indexer缓存错读：区分独立scale与合并记录

## 适用性与框架边界

本卡是**接口条件知识**：可借鉴的是按“每条 key、每组候选、每请求物理块”建立生产消费合同。本文 QLI 的 split K/scale 与 QSLI 的 combined 记录是特定算子 ABI，只有 writer、reader、scale 编码和地址单位精确匹配后，才能使用下列尺寸和槽映射。

`QLI/QSLI`、E8M0 pair、`PA_BBND`、candidate 元数据键、ratio 分支及独立 combined 管理器都不是 vLLM 通用缓存格式。特别是普通 ratio1 QSLI 当前实际走已有 slot 的 int64 fallback；带压缩位置的重建只是条件分支，不能当作默认路线。

vLLM 或其他引擎应先定位实际的 **稀疏 Attention/Indexer backend 与其 cache spec/布局适配**，再由 metadata builder 追候选和物理槽的生产者，必要时经 ModelRunner 检查执行输入。未核验选用本文接口的后端只能借鉴检查方法；这里没有确认 vLLM 支持这些算子。

## 现象

量化历史缓存接到另一个候选选择接口后，即使 dtype 与总字节数相同，也可能缺缓存、错读行或给出异常候选。先检查记录单位、数据/scale 排列、索引单位与 writer/reader 版本，不能用同 shape 的 Tensor 证明兼容。

以下匹配接口的实例中，QLI 读取 split K/scale，产生 top-k 与候选块；QSLI 在候选块内再选 top-k，读取 combined 记录。缺失 combined cache 的异常字符串是源码拒绝分支，后文保留完整证据，不是本轮运行日志。

## 适用场景

下列精确规则仅适用于匹配版本的 QLI/QSLI 与 K prologue 组合，以及其模型层间共享 Indexer 缓存、量化 K 写入与 QLI/QSLI 调用的集成，源码目标 950，本轮没有部署版本或 NPU 验证。适用粒度 `same_operator`，路线优先级 `recommended_fastpath` 描述当前实现，保持静态诊断草稿。普通路径的 query 使用 TND（packed token、头、通道），缓存使用接口标识 `PA_BBND` 的分页布局。CP（上下文并行）有独立临时缓存与 repack，不直接复用普通 slot 算法。

## 根因与判别方法

先把目标 reader 的记录宽度、量化格式、候选单位与地址函数同 writer 对齐；若名称相似但接口不同，应按目标 ABI 重新建表。对本文匹配接口，source 是拥有并写入某份 K 的来源层，后续 consumer 层只读取该来源层的缓存。K 前处理 prologue 执行投影、归一化、RoPE（旋转位置编码）与量化写入；QLI/QSLI 负责选择索引，不负责重新解释任意缓存。

| 符号/接口 | 单位、有效范围与生产消费关系 |
|---|---|
| D / index_head_dim | 一个未打包 Indexer key 的通道数；消费者按64维组成 scale pair，要求 D 可被64整除 |
| G / candidate_block_size | 一个候选块含 G 个 key；candidate 索引是块，最终 sparse 索引是压缩 KV 域中的零基位置 |
| S、r | scheduler 块覆盖的原始 token 单位、每压缩结果覆盖的原始 token 数；二者不能与候选块行数混用 |
| split K / scale | 每 key 分别占 D/2 字节 MXFP4（分组共享 scale 的4位浮点）数据、D/32 字节 E8M0 scale；QLI 分别接收二者 |
| scale pair | E8M0 为单字节 scale 编码；尾维 D/32 重解释成 `[D/64,2]`，不是每个2字节的 BF16（bfloat16）scale |
| combined 一行 | `G×(D/2+D/32)` 字节；CP repack 明确先放 G 个 key 的全部数据，再放它们的全部 scale |
| block table / slot | 表把请求内逻辑块映射到物理块；slot 把待写行映射到存储位置，必须服从该布局生产者的地址 ABI |
| candidate_indices / lengths | QLI 在同一步产生的候选块及每查询有效块数，QSLI 消费；padding 容量不是有效长度 |

**教学推演，非缓存实测。** 只为说明单位，设 D=64、G=2、S=8、r=1。一条 split K 是32字节数据加另一张表中的2字节 scale；一条 combined 记录则是“两条 K 的64字节数据，随后两条 scale 的4字节”，共68字节。不能把 `[K0,scale0,K1,scale1]` 直接当成这个记录。此时 split 每物理块有8个 key 行；模型为 combined 管理器声明的块宽为 `(S×r)/G=4` 个记录行。把 split 表交给 combined reader，即使 dtype 不报错，也不能保证读到同一组 key。

模型中 split 管理器的逻辑 block_size 为 S×r、compress_ratio=r，物理宽度换算为 S；combined 管理器的 block_size 为 `(S×r)/G`、compress_ratio=1。这个分配事实**不能推导任意 writer 的 slot 都应再除以 G**：普通 K prologue 属于外部算子，`storage_mode=1` 如何解释 slot，当前仓库未提供足够后端实现。

slot 代码还存在一条容易误读的边界：只有同时存在相应 `position_ids_c[str(r)]` 和 block table，才按 `floor((start+used)/r)-floor(start/r)` 重建写入行与请求归属。当前普通 metadata 只建立 ratio2 的压缩位置，QSLI metadata 固定 ratio1，因此普通 QSLI 使用已有 slot_mapping 转 int64 的 fallback。可选重建分支不是默认已生效路线；ratio2 的 position_ids_c 还已乘2供 RoPE 使用，不能未经核对搬到新配置。

## 快速检查

1. 在自己的后端画出“K 写入 → 候选生产 → 稀疏选择”的实际链，确认是否精确匹配本文 QLI/QSLI ABI。先按自身 reader/writer 合同标出每行单位和写权限；只有匹配时，才要求 QLI split pair 与 QSLI combined 分开，不能仅补同 shape Tensor。
2. 对匹配的 split/combined 接口，分别记录 K/scale/combined 的 shape、stride、dtype、每行字节和量化分组，按实际 D/G/S/r 重算上述预算。D/64、S/G 不整除或 scale 编码不同，支持 ABI 不匹配，应先停止该布局替换。
3. 在 recipes 该接口适配中追踪**本次实际走到**的 slot 分支；其他实现也应按自己的实际地址函数验证，记录键、start_pos、有效输入行、有效输出行和 padding。对当前 ratio1 普通 QSLI，预期看到 int64 fallback；若要启用重建分支，先检查压缩位置的单位、请求归属和生产者地址函数，不能只看分支代码存在。
4. 在同版本 writer/reader 上用不同哨兵区分 split 与 combined 存储，逐字节检查目标行、未命中行与 padding 槽。仅 CP repack 的顺序符合上例，仍不能证明普通外部 K prologue 的地址实现相同；地址解释应联合验收。
5. 记录 QLI candidate_indices/lengths 与 QSLI 读取时的请求、query、真实 KV 长度。候选源必须先产生同一步结果；长度超预算或跨请求串用，应查元数据传递。最终 sparse_indices 已是压缩 KV 域零基位置，不应再补旧窗口拼接 offset。

## 完整代码

下列 recipes 完整实现用于核对本文证据。按块外导读比较输入、轴与生产消费关系；外部引擎应先完成上面的职责和接口检查。

<details>
<summary>recipes QLI/QSLI 接口对照：完整分配、slot 分支与读写调用</summary>

### 历史适配前：QSLI复用分离K与scale

历史方法把 split K 与独立 descale_k 一起交给 QSLI。阅读它的目的，是与后面的 combined 消费接口比较，不能继续把这段当作当前正确调用方式。

```python
    def quant_sparse_lightning_indexer(
        self, q, q_scale, weights, indexer_cache, indexer_cache_scale, attn_metadata, offset
    ):
        if self.head_dim % MXFP4_SCALE_PAIR_SIZE:
            raise ValueError(
                "QSLI E8M0 scale pairs require index_head_dim divisible by "
                f"{MXFP4_SCALE_PAIR_SIZE}"
            )
        packed_dim = self.mxfp4_packed_dim

        q = q.view(-1, self.n_heads, packed_dim)
        descale_q = q_scale.view(torch.uint8).view(
            q.shape[0], self.n_heads, self.mxfp4_scale_pair_dim, MXFP4_SCALE_PAIR_GROUPS,
        )

        k = indexer_cache
        descale_k = indexer_cache_scale.view(torch.uint8).view(
            *indexer_cache_scale.shape[:3], self.mxfp4_scale_pair_dim,
            MXFP4_SCALE_PAIR_GROUPS,
        )

        block_table = attn_metadata["block_table"][f"c{self.compress_ratio}a_cmp_kv"]
        seqused_k = attn_metadata["actual_seq_k"]

        result = self.quant_sparse_lightning_indexer_ops(
            q=q,
            k=k,
            w=weights.view(-1, self.n_heads).float(),
            descale_q=descale_q,
            descale_k=descale_k,
            candidate_block_indices=attn_metadata["li_candidates"],
            candidate_block_length=attn_metadata["li_candidate_lengths"],
            cu_seqlens_q=attn_metadata["cu_seq_lens_q"].to(torch.int32),
            seqused_q=None,
            seqused_k=seqused_k.to(torch.int32),
            cmp_residual_k=None,
            block_table=block_table.to(torch.int32),
            output_idx_offset=None,
            metadata=None,
            topk=self.index_topk,
            candidate_block_size=self.candidate_block_size,
            quant_mode=1,
            max_seqlen_q=-1,
            mask_mode=3,
            cmp_ratio=self.compress_ratio,
            layout_q="TND",
            layout_kv="PA_BBND",
            return_value=False,
        )

        sparse_indices, _ = result
        return sparse_indices.view(q.shape[0], self.index_topk)
```

### 当前完整缓存分配与manager单位

按缓存的拥有关系和单位读这份长分配函数：

1. 开头的 `qsli_sources` 从 source→consumer 关系筛出确有后续 QSLI 的来源层，避免只凭层号或 Tensor shape 判断写权限。
2. `indexer_cache_dim/scale_dim` 定义每 key 的 split 字节数；`indexer_qsli_cache_dim` 再乘 G，定义每 combined 记录字节数。
3. `common` 与 `qsli_common` 使用不同 block_size、compress_ratio、manager_key，产生独立分配声明；后续 setter 将实际 Tensor 链接到相应 source/consumer。
4. 末尾 state 的 RingCache 属于 Compressor 中间状态，不是这两种 Indexer 历史记录。函数通过填充 cache_entries_by_layer 产生布局声明，而非直接完成 K 写入。

```python
    def _init_model_cache_layout(self):
        self.cache_entries_by_layer = {i: [] for i in range(len(self.layers))}
        compressed_sources = {
            source for source in self.kv_source_layers
            if self.compress_ratios[source] > 1
        }
        # source_layer --> cmp_cache
        self.cmp_cache_by_layer = {source: torch.tensor([]) for source in self.kv_source_layers}
        # source_layer --> indexer_cache
        self.indexer_cache_by_layer = {
            source: torch.tensor([]) for source in self.kv_source_layers
        }
        self.indexer_cache_scale_by_layer = {
            source: torch.tensor([]) for source in self.kv_source_layers
        }
        index_layers = set(self.config.index_source_layers)
        qsli_sources = {
            source
            for source, consumers in self.source_to_layers.items()
            if any(consumer > source and consumer in index_layers for consumer in consumers)
        }
        # QSLI reads the combined cache owned by its source layer; QLI-only
        # sources do not need a QSLI cache placeholder.
        self.indexer_qsli_cache_by_layer = {
            source: torch.tensor([]) for source in qsli_sources
        }
        # layer --> win_kv
        self.win_kv_by_layer = {i: torch.tensor([]) for i in range(len(self.layers))}
        # source_layer & cmp_ratio == 2 --> state_cache
        self.state_cache_by_layer = {source: torch.tensor([]) for source in compressed_sources}
        # layer --> kv_cache
        self.kv_cache_by_layer = {
            i: KVCache(i, self.layer_to_source.get(i)) for i in range(len(self.layers))
        }

        self.shared_idx = None
        self.candidates = None

        self.head_dim = self.config.head_dim
        self.indexer_head_dim = self.config.index_head_dim
        self.cache_dtype = PACKED_KV_STORAGE_DTYPE
        self.win_cache_dtype = PACKED_KV_COMPUTE_DTYPE
        self.block_size = self.infer_config.scheduler_config.block_size
        win_cache_dim = get_kv_cache_dim(self.head_dim)
        cmp_cache_dim = get_kv_cache_dim(self.head_dim, is_compressed=True)
        if self.indexer_head_dim % MXFP4_SCALE_GROUP_SIZE:
            raise ValueError(
                f"MXFP4 index_head_dim must be divisible by {MXFP4_SCALE_GROUP_SIZE}, "
                f"got {self.indexer_head_dim}"
            )
        self.indexer_cache_dim = self.indexer_head_dim // MXFP4_VALUES_PER_BYTE
        self.indexer_cache_dtype = torch.uint8
        self.indexer_cache_scale_dim = self.indexer_head_dim // MXFP4_SCALE_GROUP_SIZE
        self.indexer_cache_scale_dtype = torch.uint8
        candidate_block_size = int(getattr(self.config, "candidate_block_size", 8))
        if self.block_size % candidate_block_size != 0:
            raise ValueError(
                "scheduler block_size must be divisible by candidate_block_size, "
                f"got block_size={self.block_size}, candidate_block_size={candidate_block_size}"
            )
        self.indexer_qsli_candidate_block_size = candidate_block_size
        self.indexer_qsli_cache_dim = candidate_block_size * (
            self.indexer_cache_dim + self.indexer_cache_scale_dim
        )
        self.indexer_qsli_cache_dtype = torch.uint8
        self.state_cache_dtype = torch.float32
        self.block_size = self.infer_config.scheduler_config.block_size
        self.next_n = self.infer_config.speculative_config.num_speculative_tokens
        self.window_size = self.config.sliding_window
        self._entry_specs = (
            ("win_kv", self.win_kv_by_layer, _Scope.PER_LAYER),
            ("cmp_cache", self.cmp_cache_by_layer, _Scope.SHARED),
            ("indexer_cache_scale", self.indexer_cache_scale_by_layer, _Scope.SHARED),
            ("indexer_cache", self.indexer_cache_by_layer, _Scope.SHARED),
            ("indexer_qsli_cache", self.indexer_qsli_cache_by_layer, _Scope.SHARED),
            ("state_cache", self.state_cache_by_layer, _Scope.SHARED_HEAD),
        )

        def add_entry(common, layer_idx, name, dim, dtype, **kwargs):
            num_head = kwargs.pop("num_head", 1)
            entry_common = dict(common)
            entry_common.update(kwargs)
            setter = lambda tensor, n=name, i=layer_idx: self._entry_link_setter(i, n, tensor)
            cache_entries.append(CacheEntry(
                cache_name=name,
                dim=dim,
                num_head=num_head,
                dtype=dtype,
                tensor_setter=setter,
                **entry_common))

        for layer_idx, _ in enumerate(self.layers):
            cache_entries = self.cache_entries_by_layer[layer_idx]
            win_setter = lambda tensor, i=layer_idx: self._entry_link_setter(
                i, f"win_kv_layer{i}", tensor)
            # every layer owns one win_kv
            cache_entries.append(CacheEntry(
                cache_name=f"win_kv_layer{layer_idx}",
                attn_type="SlidingWindow",
                dim=win_cache_dim,
                num_head=1,
                dtype=self.win_cache_dtype,
                needs_block=True,
                block_size=self.block_size,
                manager_key="win_kv",
                tensor_setter=win_setter,
                sliding_window=self.window_size,
            ))

            ratio = self.compress_ratios[layer_idx]
            if layer_idx not in self.source_to_layers or ratio < 1:
                continue

            # create cmp_cache/indexer cache for source layers
            common = dict(attn_type="FullAttention",
                          needs_block=True,
                          block_size=self.block_size * ratio,
                          manager_key=f"c{ratio}a_cmp_kv",
                          compress_ratio=ratio)

            add_entry(common, layer_idx, f"cmp_cache_src{layer_idx}", cmp_cache_dim, self.cache_dtype)
            add_entry(common, layer_idx, f"indexer_cache_src{layer_idx}", self.indexer_cache_dim,
                      self.indexer_cache_dtype)
            add_entry(common, layer_idx, f"indexer_cache_scale_src{layer_idx}",
                      self.indexer_cache_scale_dim, self.indexer_cache_scale_dtype)

            # QSLI consumes source-layer K/V in candidate-sized combined
            # blocks. QLI-only sources keep the split cache pair above.
            has_qsli_consumer = any(
                consumer > layer_idx and consumer in index_layers
                for consumer in self.source_to_layers.get(layer_idx, [])
            )
            if has_qsli_consumer:
                qsli_common = dict(
                    attn_type="FullAttention",
                    needs_block=True,
                    block_size=(self.block_size * ratio) // self.indexer_qsli_candidate_block_size,
                    manager_key=f"c{ratio}a_qsli_combined_kv",
                    compress_ratio=1,
                )
                add_entry(
                    qsli_common,
                    layer_idx,
                    f"indexer_qsli_cache_src{layer_idx}",
                    self.indexer_qsli_cache_dim,
                    self.indexer_qsli_cache_dtype,
                )

            if ratio == 1:
                continue
            # create state_cache for source layers (cmp_ratio > 1)
            block_size = ratio if self.next_n == 0 else self.next_n + 1
            cache_entries.append(CacheEntry(
                cache_name=f"state_cache_src{layer_idx}",
                attn_type="RingCache",
                dim=self.head_dim,
                num_head=2,
                dtype=torch.float32,
                needs_block=True,
                block_size=block_size,
                manager_key=f"c{ratio}a_cmp_state",
                tensor_setter=lambda tensor, i=layer_idx:
                self._entry_link_setter(i, "state_cache", tensor)))
```

### CacheEntry逻辑与物理block size换算

这个属性将 CacheEntry 的逻辑块宽除以压缩比例得到物理行数，整除失败即拒绝；它解释分配单位，不代表 reader 或 writer 会自动替调用者修正索引。

```python
    @property
    def storage_block_size(self) -> int:
        """Calculate the physical block size when creating cache tensors."""
        if self.block_size % self.compress_ratio > 0:
            raise ValueError(
                "block_size must be divisible by compress_ratio when calculating "
                f"storage_block_size, but got cache_name={self.cache_name}, "
                f"block_size={self.block_size}, compress_ratio={self.compress_ratio}."
            )
        storage_block_size = self.block_size // self.compress_ratio
        return storage_block_size
```

### 当前普通metadata仅建立ratio2压缩位置

当前普通 metadata 只建立 ratio2 的位置及 slot。`position_ids_cmp*2` 是 RoPE 所用位置，不能直接把它认作所有布局的物理行号。

```python
    def get_cmp_metadata(self, attn_metadata, is_prefill):
        attn_metadata['position_ids_c'] = {}
        # 1. position_ids
        position_ids_func = self.generate_compressed_position_ids
        mask, position_ids_cmp = position_ids_func(attn_metadata, 2)
        attn_metadata['position_ids_c'].update(
            {str(2): position_ids_cmp * 2}
        )
        # 2. block_table
        kv_block_table = attn_metadata["block_table"][f"c2a_cmp_kv"]

        slot_mapping_func = self.get_slot_mapping_from_block_table
        attn_metadata["slot_mapping"][f"c2a_cmp_kv"] = slot_mapping_func(
            mask,
            position_ids_cmp,
            kv_block_table,
        )
```

### 当前完整Indexer slot构造及fallback

slot 构造器先复制 split 的已有槽，再处理 combined；先读缺 position/table 时的 fallback，再读可选重建分支。`compressed_len` 控制真实行数，`row_indices` 恢复每行所属请求，尾部才补无效槽。

```python
    def _prepare_indexer_slot_mapping(self, attn_metadata, device):
        """Build flattened int64 cache-write slots for Indexer cache updates."""
        indexer_slots = {
            key: slots.view(-1).to(device=device, dtype=torch.int64)
            for key, slots in attn_metadata["slot_mapping"].items()
            if key.startswith("c") and key.endswith("a_cmp_kv")
        }

        # QSLI stores one candidate-sized group of K values and scales in each
        # cache element.  Its cache manager therefore has a different block
        # size from the split QLI cache and needs slots based on compressed
        # positions rather than the ordinary token positions.
        for key in attn_metadata["slot_mapping"]:
            if not (key.startswith("c") and key.endswith("a_qsli_combined_kv")):
                continue
            try:
                ratio = int(key[1:key.index("a_")])
            except (ValueError, IndexError):
                continue
            position_ids_cmp = attn_metadata.get("position_ids_c", {}).get(str(ratio))
            block_table = attn_metadata["block_table"].get(key)
            if position_ids_cmp is None or block_table is None:
                indexer_slots[key] = attn_metadata["slot_mapping"][key].view(-1).to(
                    device=device, dtype=torch.int64
                )
                continue

            start_pos = attn_metadata["start_pos"] // ratio
            end_pos = (attn_metadata["start_pos"] + attn_metadata["seq_used_q"]) // ratio
            compressed_len = (end_pos - start_pos).to(torch.int32)
            valid_token_count = int(compressed_len.sum().item())
            valid_positions = position_ids_cmp[:valid_token_count]
            row_indices = torch.repeat_interleave(
                torch.arange(
                    compressed_len.numel(), dtype=torch.int32, device=position_ids_cmp.device
                ),
                compressed_len,
            )
            combined_block_size = (
                self.block_size * ratio
            ) // int(getattr(self.config, "candidate_block_size", 8))
            block_indices = valid_positions // combined_block_size
            block_offsets = valid_positions % combined_block_size
            block_ids = block_table[row_indices, block_indices]
            slots = block_ids * combined_block_size + block_offsets
            indexer_slots[key] = self.pad_tensor_tnd(
                slots.to(torch.int64), position_ids_cmp.numel(), self.slot_mapping_pad_value
            ).to(device=device, dtype=torch.int64)

        return indexer_slots
```

### 当前K prologue ABI

K prologue 是写入算子，没有返回 K 的步骤。latent 与二维 sin/cos 一起输入，cache_index、storage_mode 和 combined_block_size 决定缓存写入契约。

```python
    def write_prologue_k(self, latent, cos_k, sin_k, k_cache, k_scale_cache, cache_index,
                         storage_mode=0, combined_block_size=-1):
        """Project, norm, rope and quantize index K of one segment straight into a cache."""
        self.indexer_prologue_k_op(
            latent=latent.view(-1, self.wk.input_size),
            wk=self.wk.weight.detach(),
            norm_weight=self.k_norm.weight.detach(),
            # RotaryEmbedding returns [T, 1, 1, Dr], while the fused K
            # prologue ABI requires flat [T, Dr] RoPE tensors.
            rope_sin=sin_k.reshape(-1, self.rope_head_dim),
            rope_cos=cos_k.reshape(-1, self.rope_head_dim),
            k_cache=k_cache,
            k_scale_cache=k_scale_cache,
            cache_index=cache_index,
            norm_eps=self.eps,
            storage_mode=storage_mode,
            combined_block_size=combined_block_size,
        )
```

### 同一个source向split与combined两种cache写入

当前 source 对 split 与 combined 分别调用一次 K prologue。第二次传 None scale cache 和 storage_mode=1；这不是把 split 结果在 Python 中简单拼接，也没有完成注释中的未来单次写入合并。

```python
    def update_indexer_cache(self, latent, attn_metadata: Dict, kv_cache):
        """Write index K of every local token into the persistent caches."""
        cos_k, sin_k = attn_metadata["cos_sin"][f"c{self.compress_ratio}a"]
        # QLI keeps K and K-scale in separate caches.  A source layer can
        # also serve QSLI consumers, in which case the same K must be
        # written to the combined cache as well.
        slot_mapping_key = f"c{self.compress_ratio}a_cmp_kv"
        self.write_prologue_k(
            latent, cos_k, sin_k, kv_cache.indexer_cache, kv_cache.indexer_cache_scale,
            attn_metadata["indexer_slot_mapping"][slot_mapping_key])

        qsli_cache = getattr(kv_cache, "indexer_qsli_cache", None)
        if qsli_cache is None:
            return
        # The source layer currently updates the split QLI cache and the packed QSLI cache
        # separately. This compatibility path will be consolidated at layer 20 so one K update
        # serves both cache layouts.
        qsli_slot_mapping_key = f"c{self.compress_ratio}a_qsli_combined_kv"
        qsli_slot_mapping = attn_metadata["indexer_slot_mapping"].get(qsli_slot_mapping_key)
        if qsli_slot_mapping is None:
            raise KeyError(f"Missing Indexer QSLI slot mapping: {qsli_slot_mapping_key}")
        self.write_prologue_k(
            latent, cos_k, sin_k, qsli_cache, None, qsli_slot_mapping,
            storage_mode=1, combined_block_size=self.candidate_block_size)
```

### 根据candidate消费角色分派

分派由 uses_candidates 决定。QSLI 必须拿到来源层 combined cache；缺失时直接拒绝，比在错误布局上继续计算更早暴露集成问题。

```python
    def compute_sparse_indices(self, q, q_scale, weights, indexer_cache, indexer_cache_scale,
                               attn_metadata, offset, qsli_cache):
        if self.uses_candidates:
            if qsli_cache is None:
                raise RuntimeError(
                    "QSLI requires the source layer's combined indexer cache"
                )
            return self.quant_sparse_lightning_indexer(
                q, q_scale, weights, qsli_cache, attn_metadata, offset
            )
        return self.quant_lightning_indexer(
            q, q_scale, weights, indexer_cache, indexer_cache_scale, attn_metadata, offset
        )
```

### QLI完整消费：split K/scale与candidate输出

QLI 把 Q/K 的 E8M0 scale 解释成 pair，使用真实或压缩 KV 长度及对应表；candidate source 还把候选块和有效长度写回同一步 metadata，供后续 QSLI 使用。

```python
    def quant_lightning_indexer(
        self, q, q_scale, weights, indexer_cache, indexer_cache_scale, attn_metadata, offset=0
    ):
        if self.head_dim % MXFP4_SCALE_PAIR_SIZE:
            raise ValueError(
                "QLI E8M0 scale pairs require index_head_dim divisible by "
                f"{MXFP4_SCALE_PAIR_SIZE}"
            )
        packed_dim = self.mxfp4_packed_dim

        q = q.view(-1, self.n_heads, packed_dim)
        q_descale = q_scale.view(torch.uint8).view(
            q.shape[0], self.n_heads, self.mxfp4_scale_pair_dim, MXFP4_SCALE_PAIR_GROUPS,
        )

        k = indexer_cache
        k_descale = indexer_cache_scale.view(torch.uint8).view(
            *indexer_cache_scale.shape[:3], self.mxfp4_scale_pair_dim,
            MXFP4_SCALE_PAIR_GROUPS,
        )

        ratio_key = str(self.compress_ratio)
        seqused_k = (attn_metadata["actual_seq_k"] if self.compress_ratio == 1
                     else attn_metadata["compressed_seq_lens"][ratio_key])
        block_table = get_cmp_block_table(attn_metadata, self.compress_ratio)
        cmp_residual_k = (
            None if self.compress_ratio == 1
            else attn_metadata["compressed_seq_remainders"][ratio_key]
        )

        result = self.quant_lightning_indexer_ops(
            q=q,
            k=k,
            w=weights.view(-1, self.n_heads).float(),
            descale_q=q_descale,
            descale_k=k_descale,
            cu_seqlens_q=attn_metadata["cu_seq_lens_q"].to(torch.int32),
            seqused_q=None,
            seqused_k=seqused_k.to(torch.int32),
            cmp_residual_k=(None if cmp_residual_k is None
                            else cmp_residual_k.to(torch.int32)),
            block_table=block_table.to(torch.int32),
            topk=self.index_topk,
            quant_mode=1,
            max_seqlen_q=-1,
            mask_mode=3,
            cmp_ratio=self.compress_ratio,
            layout_q="TND",
            layout_k="PA_BBND",
            return_value=False,
            metadata=attn_metadata["kernel_metadata"][
                f"c{self.compress_ratio}a_qli_candidate_metadata"
                if self.is_candidate_source else f"c{self.compress_ratio}a_qli_metadata"
            ],
            candidate_topk_blocks=self.candidate_topk_blocks if self.is_candidate_source else -1,
            candidate_block_size=self.candidate_block_size if self.is_candidate_source else -1,
        )
        sparse_indices, _, candidate_indices, candidate_lengths = result
        if self.is_candidate_source:
            attn_metadata["li_candidates"] = candidate_indices
            attn_metadata["li_candidate_lengths"] = candidate_lengths

        return sparse_indices.view(q.shape[0], self.index_topk)
```

### QSLI完整消费：combined K与candidate输入

QSLI 读取 combined K 和独立的 qsli_combined_kv 表，没有独立 descale_k 参数；它消费 QLI 的 candidate 列表，最后返回 `[packed查询数,index_topk]` 的压缩 KV 索引。

```python
    def quant_sparse_lightning_indexer(
        self, q, q_scale, weights, indexer_qsli_cache, attn_metadata, offset
    ):
        if self.head_dim % MXFP4_SCALE_PAIR_SIZE:
            raise ValueError(
                "QSLI E8M0 scale pairs require index_head_dim divisible by "
                f"{MXFP4_SCALE_PAIR_SIZE}"
            )
        packed_dim = self.mxfp4_packed_dim

        q = q.view(-1, self.n_heads, packed_dim)
        descale_q = q_scale.view(torch.uint8).view(
            q.shape[0], self.n_heads, self.mxfp4_scale_pair_dim, MXFP4_SCALE_PAIR_GROUPS,
        )

        k = indexer_qsli_cache
        if k.dim() == 4 and k.shape[-2] == 1:
            k = k.squeeze(-2)

        block_table = get_cmp_block_table(
            attn_metadata, self.compress_ratio, suffix="qsli_combined_kv")
        seqused_k = attn_metadata["compressed_seq_lens"][str(self.compress_ratio)]

        result = self.quant_sparse_lightning_indexer_ops(
            q=q,
            k=k,
            w=weights.view(-1, self.n_heads).float(),
            descale_q=descale_q,
            candidate_block_indices=attn_metadata["li_candidates"],
            candidate_block_length=attn_metadata["li_candidate_lengths"],
            cu_seqlens_q=attn_metadata["cu_seq_lens_q"].to(torch.int32),
            seqused_q=None,
            seqused_k=seqused_k.to(torch.int32),
            cmp_residual_k=None,
            block_table=block_table.to(torch.int32),
            output_idx_offset=None,
            metadata=attn_metadata["kernel_metadata"][
                f"c{self.compress_ratio}a_qsli_metadata"
            ],
            topk=self.index_topk,
            candidate_block_size=self.candidate_block_size,
            quant_mode=1,
            max_seqlen_q=-1,
            mask_mode=3,
            cmp_ratio=self.compress_ratio,
            layout_q="TND",
            layout_k="PA_BBND",
            return_value=False,
        )

        sparse_indices, _ = result
        return sparse_indices.view(q.shape[0], self.index_topk)
```

### CP辅助证据：combined行内数据顺序

以下完整方法只证明CP辅助repack的行内顺序，不证明普通路径外部K prologue的地址实现。

这份 CP repack 用两个切片明示 `[全部K,全部scale]` 的行内顺序。src/dst 从各自 null block 之后开始；它只证明此辅助路径，不能代替普通外部 writer 的地址证据。

```python
    def repack_qsli_cache(self, tmp_cache, batch_size):
        """Rewrite the rows QSLI reads: one entry holds a group of keys followed by their scales."""
        qsli = tmp_cache.get("qsli_cache")
        if qsli is None:
            return
        cmp_blocks, qsli_blocks, rows_per_block = tmp_cache["qsli_layout"]
        group = self.candidate_block_size
        cache = tmp_cache["indexer_cache"]
        block_size = cache.shape[1]
        keys = cache.view(-1, self.mxfp4_packed_dim)
        scales = tmp_cache["indexer_cache_scale"].view(-1, self.mxfp4_scale_dim)
        combined = qsli.view(-1, qsli.shape[-1])
        rows = cmp_blocks * block_size // group
        for request in range(batch_size):
            src = (request * cmp_blocks + 1) * block_size
            dst = (request * qsli_blocks + 1) * rows_per_block
            combined[dst:dst + rows] = torch.cat([
                keys[src:src + rows * group].view(rows, -1),
                scales[src:src + rows * group].view(rows, -1),
            ], dim=-1)
```

</details>

## 设计决策

布局决策应由真实消费接口与共享拓扑驱动，不以 dtype 或大小推断可替换。在 recipes 中，只有拥有后续QSLI Indexer消费者的source才分配combined cache；QLI-only source保留split pair。source执行K投影/归一化/RoPE/量化写入，消费者只读；普通路径当前调用两次K prologue分别写两种布局，源码注释提及未来合并计划，但该计划不是已完成优化。

QLI candidate source把candidate_indices和candidate_lengths保存在同一步metadata；QSLI读取它们，与`seqused_k`、`cu_seqlens_q`、layout与mask_mode配套。输出sparse_indices已经是压缩KV域下的零基索引，主线直接view返回；旧的窗口拼接offset与排序逻辑已删除，不应再次加减offset。

## 系统信息

recipes 实现依赖950的Indexer K prologue、QLI/QSLI算子与相应metadata生成器。K prologue是无返回值的cache写入算子；调用者不能等待它返回K再按另一布局手工拼接。缓存对象的共享拓扑由source-to-consumer关系决定，不能用cache张量shape推断谁拥有写权限。

## 部署验收

待验：验证D/64整除、S能被G整除，逐请求核对compressed有效行数、slot数与latent行数；检查candidate source先于QSLI消费，candidate长度不越界；给combined cache与split pair填不同哨兵，逐字节验证只写目标位置。覆盖多请求不同start_pos、压缩余数、无有效压缩输出、cache边界与padding。CP模式额外检查repack后的数据先后顺序与独立临时block table。本轮均未执行。

## 验证信号

本轮只读取固定 Git 源码并恢复原始 blob 与函数字节。以下是实现的静态核对结果，不是模型/NPU 执行结果；未运行源仓脚本、测试、编译或推理。

- 主线QLI显式传入独立descale_k，QSLI只传combined K且使用独立qsli_combined_kv block table；缺cache与缺slot有明确错误分支。（来源平台：950源码目标，未上板；证据等级：artifact_verified；范围：源码）
- 主线分配宽度、storage_block_size换算、int64 slot构造及K prologue storage_mode参数可从完整函数重建。（来源平台：950源码目标，未上板；证据等级：artifact_verified；范围：源码）
- source对split和combined分别更新，未出现注释中计划的单次写入合并。（来源平台：950源码目标，未上板；证据等级：artifact_verified；范围：源码）

## 预防

给每个张量标注“每key/每candidate group/每请求block”的单位；把scale类型、cache writer、cache reader和slot来源作为不可拆分的ABI审查项。

## 坏实践

因为dtype同为uint8就共用QLI/QSLI缓存；给QSLI继续传split descale_k；把每key交错`[K,scale,K,scale]`当作`[所有K,所有scale]`；从padding总shape反推真实压缩行数；把未来注释当成当前单次写入实现。

## 失效边界

源码依赖外部算子包，当前仓库没有K prologue/QLI/QSLI的完整后端实现与上板结果，无法独立证明combined地址函数和数值正确性。必须以匹配版本的生产者/消费者联合验收为准。CP通过临时scratch、量化行gather和显式repack建立combined cache，不应直接替换为这里的普通槽算法；speculation和PD传输也需额外检验metadata与缓存生命周期。
