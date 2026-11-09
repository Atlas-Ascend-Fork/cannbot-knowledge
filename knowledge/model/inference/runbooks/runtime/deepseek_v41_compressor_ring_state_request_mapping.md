---
type: Runbook
title: 持久中间状态缓存错行：核对请求、位置与物理槽
description: 跨步中间状态异常时，分别核对请求所有权、逻辑位置、物理槽和释放时机；单块RingCache与slot公式仅适用于本文recipes方案。
tags:
- task.implementation
- topic.kv_cache
- topic.memory
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:36:07Z'
platforms:
- '950'
aliases:
- DeepSeek V4.1 Compressor state的请求寻址
---

# 持久中间状态缓存错行：核对请求、位置与物理槽

## 适用性与框架边界

本卡是**可迁移机制**：生成下一个结果的持久中间状态，与可供 Attention 检索的历史 KV 不是同一对象。诊断须分别确认请求所有权、逻辑 token 位置、物理地址和生存期；有限状态不必随完整历史长度增长，但容量由目标算法决定。

recipes 的单请求单块 `RingCache`、`CacheEntry` 声明、`state_block_table[:,0]`、metadata 字段、`block_id×C+p%C` 以及 `ratio/next_n` 容量选择，是一个具体实现。只有自有状态算法和消费者采用同样 ring 合同时才使用这些断言；它们不是 vLLM 缓存管理器 API 或普遍单块要求。

vLLM 或其他引擎可从 **模型持久状态/缓存管理、ModelRunner 的位置输入、attention metadata builder 与实际压缩/Attention backend**定位各职责。Scheduler 提供请求/token 调度结果，状态地址与更新含义仍需沿真实生产消费链核对；无需查找 recipes 的对象名。

## 现象

压缩历史 KV 的后端在跨组、长请求或请求复用后出现异常时，先辨认两类数据：可供 Attention 检索的历史记录，以及生成下一个压缩结果所需的有限状态。若把历史分页规则用于中间状态，即使短请求 shape 合法，长请求、回绕或释放后复用仍可能读写错行。

本卡的具体实例按压缩比例 r 保存最近组的 KV/gate 投影。recipes 历史修改从滑窗式 state 寻址转为请求固定 ring 块，并同时改动管理器、slot 和算子入口；没有失败栈或跨步数值证据。

## 适用场景

诊断适用于具有跨步持久中间状态的模型；下文固定单块/ring 规则仅覆盖 recipes Compressor 缓存分配与入口，源码目标 950，CANN 版本与 NPU 运行未核验。适用粒度 `same_operator`，路线优先级 `recommended_fastpath` 表示当前实现的选择，保持静态诊断草稿。主要解释普通模型 `next_n=0` 的路径；`next_n` 是投机生成待验证 token 数，非零时源码把容量改为 `next_n+1`，恢复/回滚须另验。

## 根因与判别方法

先在自有后端写出不变量：每个有效状态地址有明确请求所有者；逻辑位置到槽的映射符合状态更新算法；所有读者完成前不能释放或交给另一请求；共享状态的写者必须明确。容量、分页或环形选择由算法和消费接口决定。

下面是 recipes ring 合同的具体化：每个仍执行的请求持有一个物理 state block，直到请求结束；序列变长不增加表列，也不因滑窗前移释放。source 层产生共享数据，消费者不应各自重分配或覆盖它。轴表与公式均只解释这个实例。

| 量 | 轴、单位与生产消费关系 |
|---|---|
| r / `compress_ratio` | 每组压缩覆盖的原始 token 数；r>1 的 source 才声明中间 state |
| C / capacity | 每请求 state 块内槽数；普通路径 C=r，投机路径 C=next_n+1 |
| `state_cache [物理请求块,C,2,D]` | 32位浮点 FP32；2 分别承载 KV/gate 投影，D 为 head_dim 通道；入口 flatten 后为 `[物理请求块,C,2D]` |
| `state_block_table [请求数,1]` | 请求行映射到一个物理块 ID；调度器生产，Compressor 取第一列 |
| 位置 p 与 slot | p 为请求内绝对 token 位置，通用 ring slot 为 `block_id×C+p%C`；null 块不写 |
| `start_pos`、`seqused`、`cu_seqlens` | 本次每请求起点、有效 token 数、packed 输入边界；Compressor 据此更新状态并产生压缩行 |
| `kv`、`latent` | 压缩/归一化结果；pre-RoPE latent 留给 Indexer（稀疏候选选择器），另一份再做 RoPE（旋转位置编码）供 Attention |

**教学推演，非跨步实测。** 普通容量 C=2，请求拿到 block 3。位置4、5对应槽6、7；下一位置6重新使用槽6，请求仍持有同一块。若一次通用 scatter 同时提交位置4、5、6，仅最后两行保留为有效写入，映射为 `[-1,7,6]`，避免位置4与6并行争写槽6。这个规则只解释 ring 写入地址；Compressor 的压缩归约仍由算子结合起点和长度完成。

对该单块合同，若沿用“绝对末位置除以 scheduler block_size 选表列”，请求增长后会尝试读取第二列甚至更多列，而当前 state 表只有第一列。scheduler 的历史 KV 块大小与这里的 C 单位不同，即使短请求暂时落在列0，也不能说明迁移已正确。

## 快速检查

1. 在自有引擎列出跨步状态、历史 KV 与请求映射的生产者、消费者和释放时机。先按算法确认状态容量是否有限；若本应有限却随历史增长而分页，检查是否误用了历史管理策略。
2. 对同一请求记录准入、若干 Decode 和结束时的所有者、逻辑位置、物理地址与容量。预期地址始终指向该请求仍存活的状态，释放后才允许重用；recipes 单块方案更具体地要求准入申请1块、表宽恒1、期间不再申请。
3. 用实际地址函数重算本次所有写槽，检查请求边界、无效目标与并行写碰撞。目标算法允许 ring 覆盖时，应确认旧写已失效且只保留所需尾部；recipes 的取模和尾部屏蔽例子用于说明这一点。
4. 核对消费算子的状态地址、起点、有效行数与 packed 请求边界，确认它们属于同一次输入。自有后端可能用状态指针或别的映射；recipes 则消费 state 表第一列与 `start_pos/seqused/cu_seqlens`，通用 slot builder 正确不能替代算子协议核对。
5. 在目标环境比较分步与完整 Prefill 的压缩结果，覆盖回绕、跨组、多请求和释放后复用。地址成立但输出偏离时继续查更新算法；有投机或 CP 时，另验回滚和临时状态交接。

## 完整代码

下列 recipes 完整实现用于核对本文证据。按块外导读比较输入、轴与生产消费关系；外部引擎应先完成上面的职责和接口检查。

<details>
<summary>recipes 状态缓存对照：完整声明、容量和 Compressor 入口</summary>

### 旧实现：按绝对末位置选择state页

旧方法用 `last_pos` 计算 `block_idx`，再从 state 表 gather 该列。阅读时把它与当前“每请求只有一列”的表契约对照，而不是只比较变量名。

```python
    def _add_state_block_table_1d(self, attn_metadata):
        start_pos = attn_metadata["start_pos"]
        seq_used_q = attn_metadata["seq_used_q"]
        block_table = attn_metadata["block_table"]
        last_pos = (start_pos + seq_used_q - 1).clamp_(min=0)
        block_idx = torch.div(last_pos, self.block_size, rounding_mode="floor").long()
        for ratio in dict.fromkeys(self.config.compress_ratios):
            if ratio <= 1:
                continue
            state_key = f"c{ratio}a_cmp_state"
            if state_key not in block_table:
                continue
            block_table[f"{state_key}_1d"] = block_table[state_key].gather(
                1, block_idx.view(-1, 1)).view(-1)
```

### 当前完整模型cache声明：state容量与scope

按三段阅读这份长分配函数：

1. `compressed_sources`、`source_to_layers` 和各 by_layer 字典确定谁拥有状态、谁共享缓存；这里创建的是分配声明及链接关系。
2. `_entry_specs` 与 `add_entry` 为各类缓存建立 dtype、行宽和 scope，窗口/历史 KV/Indexer 的记录不能替代 state 声明。
3. 循环末尾对 ratio=1 跳过 state，对 ratio>1 创建 FP32 双头 RingCache；`block_size = ratio if next_n == 0 else next_n + 1` 才是本卡容量来源。后续分配器据 CacheEntry 建 Tensor，setter 再把它链接到 source。

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

### 通用RingCache规则入口

请求单块、表宽1、环绕slot、尾部与null屏蔽统一见[KV Cache Manager](../../concepts/frameworks/kv_cache_manager.md)。这里保留V4.1模型声明与Compressor入口作为新增诊断证据：旧代码按绝对position选择表列，当前Compressor只消费第一列；普通state容量为ratio，有投机token时为next_n+1。

### 当前Compressor完整入口：state第一列与pre-RoPE latent

Compressor 入口先区分普通缓存与 CP 临时缓存，然后从 `state_block_table[:,0]` 取请求块，交给压缩算子。输出经归一化后 clone 成 pre-RoPE latent，原 KV 再旋转；因此 state、latent、最终 KV 是三个不同角色。

```python
    def compressor_prolog(
        self,
        x: torch.Tensor,
        attn_metadata: Dict,
        kv_cache,
        tmp_cache=None,
    ):
        # tmp_cache is set only by the CP path, where attn_metadata is one zigzag segment's metadata.
        ratio_key = f"{self.compress_ratio}"
        cos_sin = attn_metadata["cos_sin"]
        rope_cos, rope_sin = cos_sin[f"c{ratio_key}a"]

        if self.compress_ratio == 1:
            kv = torch.nn.functional.linear(x.view(-1, self.dim), self.wkv.weight)
            if tmp_cache is not None:
                # Slots and rope follow the packed rows the compressor operator emits, while this
                # projection keeps the CP padding of every request, so drop it the same way.
                valid_rows = attn_metadata["valid_rows"]
                kv = torch.nn.functional.pad(
                    kv.index_select(0, valid_rows), (0, 0, 0, kv.shape[0] - valid_rows.numel()))
        else:
            if tmp_cache is not None:
                cu_seqlens = attn_metadata["cu_seq_lens"][ratio_key]
                seq_used_q = attn_metadata["cmp_seq_used_q"][ratio_key]
                start_pos = attn_metadata["start_pos"][ratio_key]
                state_cache = tmp_cache["state_cache_by_layer"][self.layer_idx]["state_cache"]
                state_block_table = attn_metadata["tmp_block_table"][f"c{ratio_key}a_cmp_state"]
            else:
                cu_seqlens = attn_metadata["cu_seq_lens_q"]
                seq_used_q = attn_metadata["seq_used_q"]
                start_pos = attn_metadata["start_pos"]
                state_cache = kv_cache.state_cache
                state_block_table = attn_metadata["block_table"][f"c{ratio_key}a_cmp_state"]
            cmpr_input_kwargs = {
                "x": x.view(-1, self.dim),
                "wkv": self.wkv.weight,
                "wgate": self.wgate.weight,
                "seqused": seq_used_q,
                "start_pos": start_pos,
                "cmp_ratio": self.compress_ratio,
                "cu_seqlens": cu_seqlens,
                "state_cache": state_cache.flatten(-2),
                "state_block_table": state_block_table[:, 0],
            }
            kv = self.compressor_ops(**cmpr_input_kwargs)

        kv = torch_npu.npu_rms_norm(
            kv,
            self.norm.weight,
            self.norm.variance_epsilon,
        )[0]
        latent = kv.clone()
        kv_rope_view = kv.view(-1, 1, 1, self.head_dim)
        rope_cos = rope_cos.view(-1, 1, 1, self.rope_head_dim)
        rope_sin = rope_sin.view(-1, 1, 1, self.rope_head_dim)
        torch.ops.cann_ops_transformer.inplace_partial_rotary_mul(
            kv_rope_view,
            rope_cos,
            rope_sin,
            rotary_mode="interleave",
            partial_slice=self.partial_slice,
        )
        return kv, latent
```

### 容量预算的规范入口

固定RingCache的并发预算沿用[KV Cache Manager](../../concepts/frameworks/kv_cache_manager.md#容量与显存预算)；V4.1每块的FP32双头和容量取自上面的CacheEntry，不能套Attention历史KV的随序列分页预算。

</details>

## 设计决策

状态的所有权、分配容量、地址函数与消费者协议应共同定义；只换缓存类型名不能完成语义迁移。采用环形方案前须证明只保留有限历史就足够，并处理同批覆盖和请求结束后的重用。

recipes 具体实现需联合改动 cache 类型、allocator 预算、表宽、slot builder 和消费算子。普通容量取 ratio，投机时取 next_n+1；这不是所有后端的通用常量。Compressor 归一化后 clone pre-RoPE latent 供 Indexer，再旋转另一份 Attention KV；有限 state、latent 与量化历史记录具有不同数值角色和生存期。

## 系统信息

recipes 实现需要支持RingCache的 cache manager、block pool、FP32 state tensor与950 Compressor算子。普通state的逻辑布局为 `[request_block,capacity,2,head_dim]`，送入算子前最后两维flatten。模型CacheEntry对source层分配state，消费者不应各自重新计算或覆盖source状态。

## 部署验收

自有引擎应按状态合同验收所有权、更新和释放；对 recipes 单块方案，待验：连续prefill/decode跨压缩组与环绕边界、同batch多请求、请求结束释放后重用、null dummy请求；核对首次准入需1块、已准入需0块，block table恒宽1，state总内存与序列长度无关。跨步输出应对齐一段完整prefill的参考结果；有speculation则加回滚与接受不同token数的验收。本轮未执行。

## 验证信号

本轮只读取固定 Git 源码并恢复原始 blob 与函数字节。以下是实现的静态核对结果，不是模型/NPU 执行结果；未运行源仓脚本、测试、编译或推理。

- 当前RingCacheManager每请求准入申请一块、之后复用；block table最大宽度为1，slot builder按容量取模并丢弃会碰撞的旧写。（来源平台：950模型源码目标，未上板；证据等级：artifact_verified；范围：源码）
- 固定state预算按并发数加null block计算；Compressor从state table第一列取得block ID。（来源平台：950模型源码目标，未上板；证据等级：artifact_verified；范围：源码）

## 预防

审查state缓存时先标出其数据角色、容量单位与请求生命周期；把分配、地址与算子更新放在同一链路检查，避免用Attention历史KV的分页规则推导有限状态。

## 坏实践

按当前绝对position选state表列；把`capacity`与scheduler block_size混为一谈；让一次并行scatter的所有历史行写入同一环形槽；仅检查shape而不检查请求block是否已经被释放重用。

## 失效边界

没有上板证明的跨步一致性、并发释放与回滚测试。CP prefill使用临时state并额外同步末segment状态，不能只凭本卡普通路径省略那些同步。next_n不为0时，state容量与接受token逻辑必须联合检查；通用ring slots不替代Compressor内部压缩计算。
