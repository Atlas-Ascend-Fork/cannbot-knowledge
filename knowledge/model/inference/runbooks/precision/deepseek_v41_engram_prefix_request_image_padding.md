---
type: Runbook
title: 历史哈希跨边界：隔离请求并遵守图像截断语义
description: 可迁移机制：packed历史按请求隔离、有效长度与存储步长分开；图像截断、engram_pad_id与token_map仅依本文Engram模型语义成立。
tags:
- task.debugging
- topic.precision
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:38:52Z'
platforms:
- '950'
aliases:
- DeepSeek V4.1 Engram 回看不跨请求与图像边界
---

# 历史哈希跨边界：隔离请求并遵守图像截断语义

## 适用性与框架边界

本卡以**历史窗口的请求归属、语义边界和存储坐标**为主线；不使用 recipes 的开发者也能据此检查输入构造。

| 层次 | 读用范围 |
|---|---|
| 通用原则 | packed 请求不能借到另一请求的历史；有效 token 长度与物理行跨度必须区分，padding 不能冒充真实历史。 |
| 成立前提 | 历史窗口、当前 query 是否已在历史中、pad 的 ID 命名空间与模型阻断规则均已确定；应以目标模型定义为准。 |
| recipes / 模型专属 | Engram 的 token_map、engram_pad_id、遇最近图像就截断更早历史，以及先算完整 hash 再取 CP 片段，属于本文模型语义或实现选择。**图像截断不是所有多模态模型要求。** |
| vLLM / 其他框架入口 | 检查模型输入准备、请求历史状态、tokenizer/多模态占位符语义和分片后的有效行；不要将全部 metadata 构造归给 Scheduler。 |

本轮没有验证 vLLM 的 Engram 支持或输入布局；迁移时沿用请求隔离原则，模型专有 mask/pad 规则须重新确认。

## 适用场景

Engram 用当前 token 与有限历史构造 n-gram 上下文 hash，以此检索记忆表，再由后续投影与 Gate 决定如何把检索内容加入隐藏状态。hash 决定“取哪一行”，Gate 不能纠正取错行。因此在查表或 Gate 精度之前，要先确认历史窗口没有跨到另一个请求；对于本文 Engram 语义，还要确认不会跨过图像回看更早文本。

Prefill 一次处理整段上下文，packed Prefill 把多个请求放进一条存储序列；Decode 逐步生成，必须从请求缓存恢复真实历史。成块 speculative query 一次含 B 个请求、每请求 Q 个待验证 token，仍须按请求隔离。CP（上下文并行）把序列分段分给 rank，本实现先在完整序列构造 hash，再选择本 rank 片段。

下面的 pad、图像与 hash 细节限 DeepSeek V4.1 的 recipes Engram 输入构造与消费合同；请求隔离与行坐标诊断可按自身模型语义复用。路线为 recommended_fastpath 的诊断核查。目标平台 950；本轮仅固定源码与历史补丁核验，未执行 CPU 纯函数对照、NPU、编译、精度或性能测试，CANN/外部包版本未知。

## 现象

历史代码用字面 0 补短 Decode 历史，只替换图像本身，可能仍让更早文本跨越图像进入窗口。Prefill 若按有效长度推进带 padding 的物理 offset，第二个请求的 mask 会写到错误行。历史补丁明确改变了这些构造方式，本轮没有实际数值故障或修复恢复记录。

## 根因与判别方法

先分开三种边界：请求所有权是隔离约束，图像等特殊 token 是否阻断由模型定义，padding/stride 是存储与有效性协议。下表及随后图像推演采用本文 Engram 的具体语义，并不为其他多模态模型规定回看边界。

| 数据或符号 | 轴、单位与来源 | 消费者 |
|---|---|---|
| input_ids | Prefill 的扁平 token 序列或 Decode 的 B×Q 个原始 tokenizer ID | token_map → hash |
| prefix_input_ids | [B,N-1]；原始 ID，N 为最大 n-gram 长度 | token_map → Decode shift |
| engram_pad_id / pad_id | 原始 tokenizer 的 pad / token_map 映射后的 pad | 输入构造 / hash 内部填充 |
| token_map | 原始词表 ID→压缩词表 ID 的索引表 | query 和 prefix 的同一映射 |
| actual_seq_lengths_q | 每请求真实 token 数，单位为行 | Prefill mask 有效写入范围 |
| padded_seq_lengths | 每请求在物理存储中的行跨度 | 下一请求 offset |
| ngram_shift_mask | [总存储行数,N] 布尔值；列 k 表示回看 k 步是否可用 | shift_stack 无效位置替换成压缩 pad |
| hashes | [B,Q,Engram层数,hash列数]；Prefill B=1、Q为打包行数 | 各层查表；CP 后选择本地行 |

本文 recipes 的 Decode 历史输入合同包含当前 query，因此先取 ids[:-1]，再取最近 N-1 项。从右往左遇到最近图像后，该图像及更早项全部用原始 pad 填掉；不足的左侧历史也用同一个原始 pad。进入 NgramHashState.forward 后 query 与 prefix 一起 token_map，内部不能再混入原始 pad 或假设 pad 就是 0。

教学推演（非实测）：假设 N=4，历史为 [文本a,图像,文本b,当前t]，需要的三项前缀为 [pad,pad,b]。仅替换图像会得到 [a,pad,b]，回看三步的 hash 仍带入图像前的 a。短历史 [b,t] 应得到 [pad,pad,b]；若原始 pad ID 不是 0，补 0 就会映射到另一压缩 ID。

Prefill 对每请求从 local_pos=0 重新计算距离 d：请求起点视作之前有阻断，图像位置 d=0，其后位置 d 递增。只有 d>k 的 shift 可用。再假设两个请求真实长度为 3、2，存储 stride 为 5、4：有效行是 [0,3) 与 [5,7)，中间 [3,5) 应保持 mask=False。若第二请求从 offset=3 开始，mask 即使局部公式正确也写错物理行。这个小例子解释为何 seq_len 与 stride 必须是两个元数据。

## 诊断路径

1. 在自己的框架找到请求打包器、历史状态、特殊 token/pad 语义、上下文 hash 与分片器。若目标模型有本文 Engram 的图像阻断规则，再记录图像特殊 ID。记录每个请求的真实历史、query 排布、有效长度和存储 stride；先核对实际输入准备/历史状态生产者是否把当前 token 包含在历史中。
2. 用一个可手算的短序列记录原始历史、每次回看的可用性和送入 hash 的实际 ID；若有 token_map，再记录映射后的值。预期每行只引用同一请求允许的历史；本文 Engram 另要求只引用最近图像之后的 token、无效 shift 使用压缩 pad。其他模型按其边界与 ID 表示核验。若 hash 异常，先找第一个错误 shift，不直接归因给查表或 Gate。
3. 对 packed Prefill 画出每请求的物理区间，检查 padding 不参与有效历史、下一请求按物理 stride 推进；本文用 mask=False 表示无效 padding。分片比较须保留各有效行所需的合法历史；本文 CP 实例在同一全序列 hash 上选择对应行。若在局部片段重算，应另证边界历史足够且结果等价，不能无条件按本地起点补 pad。
4. 对 B>1、Q>1 记录 flatten 顺序与恢复 [B,Q] 的结果，确保每行 query 对应自己的 prefix。元素数能整除 B 只是必要条件，不证明排布正确。
5. 修正后先运行该框架的纯函数序列对照，再比较 packed/unpacked、CP 开/关的有效 token hash 和最终模型输出；对本文 Engram 语义还应覆盖图像位于窗口边缘、多个图像及短历史。以下原代码是对照材料，未在本轮执行。

<details>
<summary>recipes / CANN Executor 完整实现对照（可选阅读）</summary>

## 快速检查

有 recipes 源码时可选定位以下符号；诊断不依赖这些类名。

```bash
rg -n '_engram_decode_prefix_row|engram_pad_id|distance_from_blocker|offset \+= stride|padded_lens|batch_size = prefix_input_ids' models/deepseek_v4_1/models/modules/attention_data.py models/deepseek_v4_1/models/modules/engram.py
```

## 系统信息

以下原样块属于 metadata 输入构造、hash 状态与模型 CP 选择。历史 before 是完整因果块，不能当当前推荐实现。依赖配置、tokenizer、PyTorch 及可选 TileLang hash；未证明任意调度器布局都可自动适配。

## 机制代码

### 历史 before：前缀构造

该块同时包含旧 Prefill mask 和 Decode prefix：prefix_len 曾在 CP>1 时置零，短历史使用字面 0，图像仅替换自身。它展示被调整的机制，没有相应运行前后结果。

```python
        engram_prefix_ids = None
        engram_shift_mask = None
        prefix_len = max(0, int(self.config.engram_max_ngram_size) - 1) if self.cp_size == 1 else 0
        if prefix_len:
            if is_prefill:
                # Packed prefill tokens must not borrow history across a request
                # boundary or an image token, dist is the gap to the nearest blocker.
                total_tokens = input_ids.reshape(-1).numel()
                engram_shift_mask = torch.zeros(
                    total_tokens,
                    prefix_len + 1,
                    dtype=torch.bool,
                    device=input_ids.device,
                )
                flat_ids = input_ids.reshape(-1)
                image_token_id = self.config.image_token_id
                offset = 0
                for seq_len in actual_seq_lengths_q.tolist():
                    seq_len = int(seq_len)
                    local_pos = torch.arange(seq_len, device=input_ids.device)
                    order = torch.arange(prefix_len + 1, device=input_ids.device)
                    image_mask = flat_ids[offset:offset + seq_len] == image_token_id
                    dist = local_pos - torch.cummax(local_pos.masked_fill(~image_mask, -1), 0).values
                    # pad count = max(0, prefix_len + 1 - dist)
                    engram_shift_mask[offset:offset + seq_len] = (
                        dist[:, None] > order[None, :]
                    )
                    offset += seq_len
            else:
                requests = getattr(batch, "requests", None) if batch is not None else None
                if requests is not None:
                    histories = [request.get_all_token_ids() for request in requests]
                else:
                    histories = []
                histories = histories[:bsz] + [[]] * max(0, bsz - len(histories))
                image_token_id = self.config.image_token_id
                engram_pad_id = self.config.engram_pad_id
                engram_prefix_ids = torch.tensor(
                    [
                        # all_token_ids includes the current query token t;
                        # Engram needs the tokens immediately before it. Image
                        # tokens are padded out.
                        ([0] * max(0, prefix_len - len(ids[:-1][-prefix_len:])))
                        + [engram_pad_id if tid == image_token_id else tid
                           for tid in ids[:-1][-prefix_len:]]
                        for ids in histories
                    ],
                    dtype=torch.long, device=input_ids.device)
```

### Decode 单行：_engram_decode_prefix_row

输入一请求原始历史、窗口长度、图像与 pad ID；输出固定 N-1 长度前缀。tail 排除当前 query，blocked 在反向遍历遇图像后保持 True，所以更早文本同样被屏蔽。

```python
def _engram_decode_prefix_row(ids, prefix_len, image_token_id, engram_pad_id):
    # all_token_ids includes the current query token t; Engram needs the
    # tokens immediately before it. n-grams must not span image tokens: an
    # image token and everything farther away is padded out, and a short
    # history is left-padded with engram_pad_id.
    tail = ids[:-1][-prefix_len:]
    row, blocked = [], False
    for tid in reversed(tail):
        blocked = blocked or tid == image_token_id
        row.append(engram_pad_id if blocked else tid)
    row.reverse()
    return [engram_pad_id] * (prefix_len - len(tail)) + row
```

### Prefill/Decode 统一生产者：build_engram_hash_inputs

输入真实 token、有效长度、请求历史及可选 padded stride；输出两者之一：Decode prefix 或 Prefill shift mask。seq_lens 限制有效写入，strides 决定 offset，distance_from_blocker 决定每个 shift 的语义。

```python
def build_engram_hash_inputs(config, input_ids, is_prefill,
                             actual_seq_lengths_q, batch, padded_seq_lengths=None):
    """Build the hash inputs consumed by models.modules.engram.

    Returns (prefix_input_ids, ngram_shift_mask); decode builds
    prefix_input_ids [bsz, ngram_size-1] from the cached request
    histories, prefill builds ngram_shift_mask [total_tokens,
    ngram_size] (True = the token at that shift is usable) over the
    full sequence, before CP splits it. Either output is None when
    ngram_size <= 1 disables engram hashing entirely.

    CP pads every request at its own tail, so padded_seq_lengths gives the row
    stride of each request while actual_seq_lengths_q gives its valid span.
    """
    prefix_input_ids = None
    ngram_shift_mask = None
    prefix_len = max(0, int(config.engram_max_ngram_size) - 1)
    if prefix_len:
        if is_prefill:
            # Packed prefill tokens must not borrow history across a request
            # boundary or an image token.
            total_tokens = input_ids.reshape(-1).numel()
            ngram_shift_mask = torch.zeros(
                total_tokens,
                prefix_len + 1,
                dtype=torch.bool,
                device=input_ids.device,
            )
            flat_ids = input_ids.reshape(-1)
            image_token_id = config.image_token_id
            seq_lens = [int(seq_len) for seq_len in actual_seq_lengths_q.tolist()]
            strides = padded_seq_lengths if padded_seq_lengths is not None else seq_lens
            offset = 0
            for seq_len, stride in zip(seq_lens, strides):
                local_pos = torch.arange(seq_len, device=input_ids.device)
                order = torch.arange(prefix_len + 1, device=input_ids.device)
                image_mask = flat_ids[offset:offset + seq_len] == image_token_id
                distance_from_blocker = local_pos - torch.cummax(
                    local_pos.masked_fill(~image_mask, -1), 0
                ).values
                # A shift is valid only if it stays after the nearest blocker.
                ngram_shift_mask[offset:offset + seq_len] = (
                    distance_from_blocker[:, None] > order[None, :]
                )
                offset += stride
        else:
            bsz = actual_seq_lengths_q.shape[0]
            requests = getattr(batch, "requests", None) if batch is not None else None
            if requests is not None:
                histories = [request.get_all_token_ids() for request in requests]
            else:
                histories = []
            histories = histories[:bsz] + [[]] * max(0, bsz - len(histories))
            image_token_id = config.image_token_id
            engram_pad_id = config.engram_pad_id
            prefix_input_ids = torch.tensor(
                [
                    _engram_decode_prefix_row(ids, prefix_len, image_token_id, engram_pad_id)
                    for ids in histories
                ],
                dtype=torch.long, device=input_ids.device)
    return prefix_input_ids, ngram_shift_mask
```

### Hash 状态：NgramHashState.__init__

输入 tokenizer 和 Engram 布局，创建 token_map、乘数、模数和偏移；压缩词表大小不匹配会改变整张表的 hash，因此有一致性检查。pad_id 在此由原始配置映射得到。

```python
    def __init__(
        self,
        config,
        infer_config,
        layout: EngramLayout,
        tokenizer
    ):
        super().__init__()
        self.layout = layout
        self.config = config
        self.infer_config = infer_config
        self.engram_kernel = _get_engram_kernel(infer_config)
        self.max_ngram_size = layout.max_ngram_size
        # every hash multiplier derives from the compressed vocab size, so a mismatch there would
        # silently rehash the whole table
        token_map, vocab_size = build_compressed_token_map(tokenizer)
        assert vocab_size == config.engram_compressed_vocab_size, (vocab_size, config.engram_compressed_vocab_size)
        self.pad_id = token_map[config.engram_pad_id]
        flat = [[p for per_ngram in layer for p in per_ngram] for layer in layout.primes]
        offsets = [np.cumsum([0, *sizes[:-1]]) for sizes in flat]
        multipliers = compute_hash_multipliers(layout.layer_ids, layout.max_ngram_size, vocab_size)

        self.register_buffer("primes", torch.tensor(layout.primes), persistent=False)
        self.register_buffer("offsets", torch.tensor(np.array(offsets)), persistent=False)
        self.register_buffer("multipliers", multipliers, persistent=False)
        self.register_buffer("token_map", torch.tensor(token_map), persistent=False)
```

### Shift 与 hash 消费者：_get_ngram_hashes

本函数输入的是已经映射的 ID，先构造 shift_stack，再用 mask 替换无效回看，最后按层/表参数产生行号。

| 阶段 | 中间变量 | 作用 |
|---|---|---|
| shift_k_pad / shift_k_prefix | base_shifts | Prefill 左补 pad；Decode 拼真实前缀 |
| stack 与 where | tokens | 在 hash 前实施请求和图像阻断 |
| TileLang 分支 | ngram_token_ids、hashes_out | Prefill 的另一实现入口，输出轴还原 |
| 普通分支 | products、rolling、hashes | 逐项 XOR、取模并加表区间偏移 |

DEAD 的局部变量赋值原样保留；不能据它的存在宣称所有 DEAD 输入已经正确覆盖。

```python
    def _get_ngram_hashes(
        self,
        input_ids: torch.Tensor,
        prefix_input_ids: torch.Tensor = None,
        ngram_shift_mask: torch.Tensor = None,
        is_prefill: bool = False,
    ) -> torch.Tensor:
        x = input_ids
        B, T = x.shape
        prefix = prefix_input_ids
        if prefix_input_ids is not None:
            mask = prefix_input_ids == self.DEAD
            prefix_input_ids = torch.where(mask, self.pad_id, prefix_input_ids)

        def shift_k_pad(k: int) -> torch.Tensor:
            if k == 0:
                return x
            shifted = F.pad(x, (k, 0), mode="constant", value=self.pad_id)[:, :T]
            return shifted

        def shift_k_prefix(k: int) -> torch.Tensor:
            """Shift a decode query after prepending its real token history."""
            if k == 0:
                return x
            if prefix is None:
                raise ValueError(
                    "prefix_input_ids can not be None on the decoding phase."
                )
            history_input = torch.cat([prefix, x], dim=1)
            start = prefix.shape[1] - k
            if start < 0:
                raise ValueError(
                    f"prefix_input_ids length {prefix.shape[1]} is insufficient for shift {k}"
                )
            shifted = history_input[:, start : start + T]
            return shifted

        shift_fn = shift_k_prefix if prefix is not None else shift_k_pad
        base_shifts = [shift_fn(k) for k in range(self.max_ngram_size)]
        # [B, L, max_ngram_size] for decode, [1, T, max_ngram_size] for prefill
        shift_stack = torch.stack(base_shifts, dim=-1)
        if ngram_shift_mask is not None:
            mask = ngram_shift_mask
            if mask.dim() == 2:
                mask = mask.unsqueeze(0)
            pad_value = shift_stack.new_full((), self.pad_id)
            shift_stack = torch.where(mask, shift_stack, pad_value)
        tokens = shift_stack

        if is_prefill and self.engram_kernel == "tilelang":
            from tile_kernels.engram import engram_hash

            ngram_token_ids = tokens.reshape(-1, self.max_ngram_size).to(torch.int32)
            hashes_out = engram_hash(
                ngram_token_ids,
                self.multipliers,
                self.primes.to(torch.int32),
                self.offsets.to(torch.int32),
            )
            # [n_engram_layers, T, num_out_cols] -> [1, T, n_engram_layers, num_out_cols]
            return hashes_out.permute(1, 0, 2).unsqueeze(0)

        # XOR the multiplied ids together one lookback at a time, so the running value after step i
        # is the hash of the (i+1)-gram; each lands in its own prime-sized bucket range
        products = tokens.unsqueeze(2) * self.multipliers  # [B, L, n_engram_layers, max_ngram_size]
        rolling, hashes = products[..., 0], []
        for i in range(1, self.layout.max_ngram_size):
            rolling = torch.bitwise_xor(rolling, products[..., i])
            hashes.append(rolling.unsqueeze(-1) % self.primes[:, i - 1])
        return torch.cat(hashes, dim=-1) + self.offsets
```

### 形状与 ID 映射：NgramHashState.forward

query/prefix 同时 token_map。Prefill 增加 batch 轴；Decode 根据 prefix 的 B 恢复 [B,Q]。该 reshape 保留已有扁平顺序，不会自动修复错误调度器顺序。

```python
    def forward(
        self, input_ids, is_prefill, prefix_input_ids=None, ngram_shift_mask=None
    ):
        input_ids = self.token_map[input_ids]
        if prefix_input_ids is not None:
            prefix_input_ids = self.token_map[prefix_input_ids]
        if is_prefill:
            input_ids = input_ids.unsqueeze(0)
        else:
            if prefix_input_ids is None:
                input_ids = input_ids.view(-1, 1)
            else:
                # Speculative verification packs B * Q query tokens into one
                # dimension, while Engram history remains [B, ngram_size - 1].
                # Restore [B, Q] so prefix and query rows describe the same
                # requests and n-grams may continue across the whole query block.
                batch_size = prefix_input_ids.shape[0]
                if input_ids.numel() % batch_size != 0:
                    raise ValueError(
                        "Engram decode input cannot be reshaped to the prefix batch: "
                        f"input_ids.numel()={input_ids.numel()}, batch_size={batch_size}"
                    )
                input_ids = input_ids.reshape(batch_size, -1)
        return self._get_ngram_hashes(
            input_ids,
            prefix_input_ids=prefix_input_ids,
            ngram_shift_mask=ngram_shift_mask,
            is_prefill=is_prefill,
        )
```

### CP 消费点：compute_engram_hashes

先计算完整序列 hash，再 select_cp_segments。这样 n-gram 可以跨 CP 片段边界，但仍受请求与图像 mask 限制。

```python
    def compute_engram_hashes(self, input_ids, is_prefill, attn_metadata,
                              prefix_input_ids=None, ngram_shift_mask=None):
        """Hash the full sequence, then keep this rank's segments: n-grams reach across segments."""
        hashes = self.engram_hash(
            input_ids, is_prefill,
            prefix_input_ids=prefix_input_ids,
            ngram_shift_mask=ngram_shift_mask)
        if is_prefill and self.cp_size > 1:
            hashes = select_cp_segments(hashes.squeeze(0), attn_metadata["cp_metadata"]).unsqueeze(0)
        return hashes
```

### metadata 输入调用

CP Prefill 从分段长度算每请求 padded_lens，连同实际长度传给构造器；MTP 分支另有选择，不在这里补造相同语义。

```python
        bsz = actual_seq_lengths_q.shape[0]
        is_cp_prefill = is_prefill and self.cp_size > 1

        padded_lens = None
        if is_cp_prefill:
            padded_lens = [
                seg_len * self.cp_size * 2 for seg_len in self.get_cp_segment_lens(metadata_get("cp_metadata"))
            ]

        engram_prefix_ids, engram_shift_mask = None, None
        if not self.is_mtp:
            engram_prefix_ids, engram_shift_mask = build_engram_hash_inputs(
                self.config, input_ids, is_prefill,
                actual_seq_lengths_q, batch, padded_lens,
            )
```

### metadata 发布

向后传 prefix、shift_mask 和实际长度；这些必须与本次 input_ids 行序属于同一批请求。

```python
        if not self.is_mtp:
            engram_metadata = {
                "prefix_input_ids": engram_prefix_ids,
                "shift_mask": engram_shift_mask,
                "actual_seq_lengths": actual_seq_lengths_q.to(
                    device=input_ids.device,
                    dtype=torch.int32,
                ),
            }
        else:
            engram_metadata = {}
```

</details>

## 设计决策

padding 是 hash 输入语义，不只是补 shape。请求边界与模型定义的阻断规则决定哪些回看有效；本文 Engram 将图像作为阻断。CP stride 决定这些布尔值落在哪一行。应先验证 ID 命名空间和行坐标，再比较 hash 值。

## 验证信号

- [来源平台：950（仅源码目标，未上板）；证据等级：artifact_verified，静态源码] 当前 Decode 从真实历史去除 query，遇最近图像后屏蔽更早项，短历史用配置原始 pad。
- [来源平台：950（仅源码目标，未上板）；证据等级：artifact_verified，静态源码] Prefill mask 按有效长度写入、按 padded stride 推进；forward 映射 query/prefix 并恢复 B×Q。

本轮未执行 CPU 或 NPU 数值对照；历史修改不构成实测修复成功。保持 draft，未生成 verified 事件。

## 部署验收

待执行：手工列出空/短/完整历史和图像边界的预期 prefix/shift；对比 packed/unpacked、CP 开/关的有效行 hash；覆盖 B>1、Q>1 后验证模型输出。

## 坏实践

在本文 Engram 合同下，用字面 0 代替配置 pad、仅屏蔽图像自身、用有效长度推进 padded 存储坐标，或在 CP 局部片段独立补历史后声称等价，都会混淆不同职责。

## 失效边界

历史数量、query flatten 顺序与 stride 来自上游调度器，函数不能纠正所有不一致输入。CPU 对照尚未执行；DEAD 路径与可选 hash 后端数值仍需真实输入验收。图像截断、query 排除及 pad 映射仅在相同模型/输入语义下成立，不能用于改变其他多模态模型的历史规则。
