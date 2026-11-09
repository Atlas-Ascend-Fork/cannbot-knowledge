---
type: Runbook
title: recipes专用：Engram预计算结果的后端协议
description: recipes/CANN Executor专用：Engram的native三元组与TileLang Prefill二元组须按同一适配分支生产消费；并非TileLang或vLLM标准协议。
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
- DeepSeek V4.1：Engram 后端与预计算元组
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - cann_executor
---

# recipes专用：Engram预计算结果的后端协议

## 适用性与框架边界

本卡是 **recipes / CANN Executor 专用后端适配协议**。native 三元组与 TileLang Prefill 二元组由这份 Engram 适配层定义；**它们不是 TileLang 语言标准，也不是 vLLM 标准接口**。

| 层次 | 读用范围 |
|---|---|
| 可借鉴原则 | 后端改变结果表示时，生产者、缓存和解包消费者必须采用同一协议；总元素数相同不足以证明等价。 |
| 成立前提 | 使用本文 DeepSeek V4.1 Engram 和 kernel_config.engram 选择器；Prefill+tilelang 才是二元组，native Prefill 与 Decode 保持三元组。 |
| recipes 专属 | tuple 长度、key/value/weight 与 kv/weight_fused 的轴/dtype、image mask、Decode 回落及非原位返回均属于此适配层。 |
| vLLM / 其他框架入口 | 仅借鉴检查模型预计算结果与后端 consumer 的表示信息、模式与生命周期；不能照搬本卡元组解包、配置或后端支持结论。 |

本轮没有 TileKernels 外部运行或 vLLM 接入验收，图支持与精度边界仍待实际版本验证。

## 适用场景

Engram 的 Hash 根据 token 与历史决定记忆表行号；Embedding 查出向量；WKV 把向量投影成 key/value；Gate 比较 key 与当前隐藏状态，决定把多少 value 加回。前三段不依赖当前层隐藏状态，可提前算；Gate 必须在该层消费。这里的 key/value 是检索内容投影，不是注意力缓存。

Prefill 一次处理上下文多 token，Decode 逐步生成。本卡专门讨论 recipes / CANN Executor 中 DeepSeek V4.1 kernel_config.engram 的 native/tilelang 选择：只有 is_prefill=True 且明确选择 tilelang 时，Hash 和 Gate 走对应融合入口；Decode 即使配置 tilelang 仍使用 native。路线为 recommended_fastpath 的数据合同核查，粒度限此后端适配。

目标平台 950；本轮仅固定源码静态核验，未运行 CPU/NPU、编译、图、精度或性能测试。CANN/TileKernels 版本未知。源码说明当前 Prefill TileLang 路线不用于 torch compile 入图；实际版本支持需另验，不能扩大为所有版本均不支持。

## 现象

native 预计算返回 (key,value,weight)，TileLang Prefill 返回 (kv,weight_fused)。若生产者与 Gate 选择不一致，会出现解包或布局问题；只切 Hash 或只切 Gate 也不能证明两端合同一致。本轮没有实际 tuple 错误、编译失败或加速结果。

## 根因与判别方法

这两个 recipes 适配元组描述同一组检索投影职责，但表示不同，不能按长度强行补一个元素。下表不是 TileLang 或其他推理框架的统一 schema。

| 数据 | 轴、单位与来源 | 消费者 |
|---|---|---|
| ngram_token_ids | [token行数,N]，压缩 ID；已完成历史/shift/mask，N 为最大 n-gram 长度 | TileLang Hash |
| hashes | [1,T,Engram层数,hash列数] 的表行号；TileLang 输出先重排轴 | 分层查表 |
| embeddings | [T,hash列数×表向量宽度] | 独立 WKV Linear |
| hidden_states | [T,M,D]；M=hc_mult 为隐藏副本数，D 为隐藏通道 | Gate |
| native key / value | [T,M,D] FP32 key / [T,D] value | native Gate |
| native weight | [M,D] FP32；q_weight×k_weight | native Gate，沿 D 求加权相似度 |
| TileLang kv | [T,M+1,D] BF16；保留投影未拆开的 M 份 key 与一份 value | engram_gate_fwd |
| weight_fused | [M,D] FP32；由独立权重乘积 kernel 产生 | TileLang Gate |
| gate / output | 每 token 每副本一个门值 / [T,M,D] | 向每份隐藏状态加入相应 value，供后续层 |

教学推演（非运行结果）：设 M=2、D=3，WKV 为每个 token 输出 9 个通道。native 拆为 6 个 key 通道再恢复 [2,3]，另外 3 个作为 value；TileLang 保留 [3,3]，由 Gate 按合同读取前两份 key 和一份 value。把 native 三元组直接交给接收两项的消费者，不会因两者总通道相同就等价；反过来把 kv 当 key，会多出一份轴。

native Gate 对每个 (token,副本) 单独沿 D 归一化，再计算加权点积、带符号平方根和 sigmoid；门值乘 value 后加到该副本隐藏状态。image_mask 为 True 时门值置零，表示该位置透传隐藏状态。fused_weight 仅替代 q_weight 与 k_weight 的乘积，既不读 embeddings，也不融合 WKV 矩乘。TileLang Gate 用 inplace=False，调用方必须使用返回 output。

## 诊断路径

1. 在本文 recipes Engram 中找到 Hash、Embedding、检索投影与 Gate；记录它们实际后端和 Prefill/Decode 标志。配置名相同不够，要核对生产者与消费者在本次调用选中相同 schema。
2. 在预计算出口记录 tuple 长度、每元素角色、shape/dtype/stride、token 行数与 M/D；在 Gate 入口记录同一信息。若只在多流失败，优先检查预计算缓存是否跨模式/后端复用，并另查其完成依赖。
3. 若元组匹配但输出不符，依次比较 hash 行号、查表向量、WKV 投影，再比较 Gate 的归一化轴、weight 乘积、clamp、signed sqrt 与 image mask。不能用 TileLang Hash 绕过请求历史和图像阻断。
4. 修正生产消费配对后，用同一输入权重分别对照 native Prefill、TileLang Prefill；再确认 Decode 仍按 native 三元组消费。保存 Gate 返回值与最终输出，不假设原输入已就地更新。
5. 精度、编译/capture 与性能分别验收；真实依赖或签名缺失时保留明确失败，若回退 native，应连同生产和消费一起切换并重新验收。

<details>
<summary>recipes / CANN Executor 完整实现对照（可选阅读）</summary>

## 快速检查

以下搜索仅为本文 recipes 源码的可选导航；其他框架只借鉴生产消费表示核验，不采用这里的元组或分支条件。

```bash
rg -n 'def _get_engram_kernel|engram_kernel =|is_prefill and self.engram_kernel|return kv, weight_fused|return key, value, weight|precomputed' models/deepseek_v4_1/models/modules/engram.py
```

## 系统信息

下列完整函数来自 Engram 模块，依赖 PyTorch、模型配置、独立线性层与可选 tile_kernels.engram。代码是静态机制材料，未在本轮执行。

## 机制代码

### 统一选择器：_get_engram_kernel

输入推理配置，返回 native 或 tilelang；缺省 native，其他值拒绝。Hash 状态和 Engram 消费者各自调用它，因此仍需确认两者拿到同一份配置。

```python
def _get_engram_kernel(infer_config: InferenceConfig) -> str:
    kernel_config = infer_config.model_config.custom_params.get("kernel_config", {})
    kernel = kernel_config.get("engram", "native")
    if kernel not in ("native", "tilelang"):
        raise ValueError(
            f"Unsupported kernel implementation {kernel!r} for 'engram'. "
            "Expected 'native' or 'tilelang'."
        )
    return kernel
```

### Hash：NgramHashState._get_ngram_hashes

先生成按历史位移排列的 token，再施加 mask，才在 Prefill+tilelang 时调用 engram_hash。该函数把外部输出从 [层,T,列] 重排成公共布局；普通分支用逐项 XOR、模数和区间偏移产生行号。

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

### 查表：precompute_embeddings

输入本层 hash，输出把多列查表向量拼在通道轴的 [T,hash列数×向量宽度]；不读取 hidden_states。

```python
    def precompute_embeddings(self, engram_hash, is_prefill=False):
        """Stage 1: embedding lookup — does not depend on hidden_states."""
        return self.multi_head_embedding(
            engram_hash,
            is_prefill=is_prefill,
        ).reshape(
            -1,
            self.multi_head_embedding.embedding_dim
            * self.n_hash_cols
        )
```

### 投影与格式选择：precompute_kv

WKV 先独立执行，得到 M+1 份 D 通道。只有 Prefill+tilelang 才保留 BF16 kv 并调用 fused_weight；其他条件拆分 key/value，生成 FP32 weight，返回三元组。

```python
    def precompute_kv(self, embeddings, is_prefill=False):
        """Stage 2: wkv projection — Cube-heavy, does not depend on hidden_states.

        For prefill with the TileLang backend: return (kv_bf16, weight_fused) where
        kv_bf16 is [T, hc)mult+1, D] bfloat16 (unsplit) and weight_fused is
        [hc_mult, D] float32 (from fused_weight kernel).
        Otherwise returns (key, value, weight) through the native PyTorch path.
        """
        kv = self.wkv(embeddings)
        if is_prefill and self.engram_kernel == "tilelang":
            from tile_kernels.engram import fused_weight

            kv = kv.reshape(-1, self.hc_mult + 1, self.hidden_size)
            if kv.dtype != torch.bfloat16:
                kv = kv.to(torch.bfloat16)
            weight_fused = fused_weight(
                self.q_weight.to(torch.bfloat16),
                self.k_weight.to(torch.bfloat16),
            )
            return kv, weight_fused
        key, value = kv.split([self.hc_mult * self.hidden_size, self.hidden_size], dim=-1)
        key = key.float().unflatten(-1, (self.hc_mult, self.hidden_size))
        weight = self.q_weight.float() * self.k_weight.float()
        return key, value, weight
```

### 组合预计算：precompute

串联查表与投影，并传递 is_prefill。注释对“Prefill 返回二元组”的简写必须按实际条件解读：native Prefill 仍是三元组。

```python
    def precompute(self, engram_hash, is_prefill=False):
        """Run Stage 1 + Stage 2 together.  Returns (key, value, weight)
        for decode or (kv_bf16, weight_fused) for prefill."""
        embeddings = self.precompute_embeddings(engram_hash, is_prefill=is_prefill)
        return self.precompute_kv(embeddings, is_prefill=is_prefill)
```

### 消费者：Engram.forward

本函数在同一条件下选择元组解包方式，未预计算时现场调用相同生产者。按以下段落定位：

| 段落 | 关键变量 | 输出职责 |
|---|---|---|
| TileLang 分支 | kv、weight_fused、output | 调外部 Gate，返回新的 output |
| native 取数 | key、value、weight | 消费三元组或现场构造 |
| native Gate | rstd、dot、gate_input、gate | 每 token/副本独立归一化、门控并加回 value |

```python
    def forward(self, hidden_states, engram_hash=None, is_prefill=False,
                engram_metadata=None, image_mask=None, precomputed=None):
        """Stage 3: gating — depends on hidden_states.

        hidden_states: [T, HC_MULT, D]
        precomputed: optional (key, value, weight) from the native backend,
                     or (kv_bf16, weight_fused) from TileLang prefill.
        image_mask: True at image spans, where the gate shuts for pass-through.
        """
        if is_prefill and self.engram_kernel == "tilelang":
            from tile_kernels.engram import engram_gate_fwd

            if precomputed is not None:
                kv, weight_fused = precomputed
            else:
                embeddings = self.precompute_embeddings(engram_hash, is_prefill=is_prefill)
                kv, weight_fused = self.precompute_kv(embeddings, is_prefill=is_prefill)

            output, _, _, _, _ = engram_gate_fwd(
                hidden_states,
                kv,
                weight_fused,
                self.eps,
                self.clamp_value,
                save_for_backward=False,
                image_token_mask = image_mask,
                inplace=False,
            )
            return output

        # Native PyTorch path for decode and for prefill without TileLang.
        engram_metadata = engram_metadata or {}

        if precomputed is not None:
            key, value, weight = precomputed
        else:
            embeddings = self.precompute_embeddings(engram_hash, is_prefill=is_prefill)
            key, value, weight = self.precompute_kv(embeddings)

        h, eps = hidden_states.float(), self.eps
        # normalized per (token, hc copy) over `dim`, NOT jointly over the copies
        rstd = torch.rsqrt(h.square().mean(-1) + eps) * torch.rsqrt(key.square().mean(-1) + eps)
        dot = (h * weight * key).sum(-1) * rstd * self.hidden_size**-0.5
        # signed sqrt before the sigmoid, matching the training kernel
        gate_input = dot.abs().clamp_min(self.clamp_value).sqrt()
        gate = torch.sigmoid(torch.where(dot >= 0, gate_input, -gate_input))
        if image_mask is not None:
            gate = gate.masked_fill(image_mask.unsqueeze(-1), 0)
        return (h + gate.unsqueeze(-1) * value.float().unsqueeze(-2)).to(hidden_states.dtype)
```

### Engram.__init__

保存后端选择、D/M 和本层 hash 索引，创建查表器、WKV 与 q/k 权重。n_hash_cols 决定 embeddings 输入宽度；WKV 的输出宽度为 D×(M+1)，与上面两种拆分合同一致。

```python
    def __init__(self, config, infer_config, layer_id, engram_layout, prefix, comm_manager=None):
        super().__init__()
        self.layer_id = layer_id
        self.config = config
        self.infer_config = infer_config
        self.engram_kernel = _get_engram_kernel(infer_config)
        self.comm_manager = comm_manager
        self.hidden_size = config.hidden_size
        self.hc_mult = config.hc_mult
        self.layer_hash_index = engram_layout.layer_ids.index(layer_id)

        self.multi_head_embedding = MultiHeadEmbedding(
            engram_layout.num_embeddings[self.layer_hash_index],
            engram_layout.head_dim,
            infer_config=self.infer_config,
            comm_manager=self.comm_manager,
            engram_layout=engram_layout,
            layer_id=self.layer_id,
        )
        self.n_hash_cols = (engram_layout.max_ngram_size - 1) * engram_layout.n_heads
        self.wkv = ReplicatedLinear(self.n_hash_cols * engram_layout.head_dim,
                                    self.hidden_size * (config.hc_mult + 1),
                                    params_dtype=torch.float8_e4m3fn,
                                    quant_config=config.quant_config,
                                    prefix=f"{prefix}.wkv",
                                    )
        self.eps = config.rms_norm_eps
        self.q_weight = nn.Parameter(torch.ones(config.hc_mult, self.hidden_size))
        self.k_weight = nn.Parameter(torch.ones(config.hc_mult, self.hidden_size))
        self.clamp_value = 1e-6
```

### NgramHashState.__init__

Hash 也使用同一选择器，同时建立压缩词表映射、乘数、模数与表区间偏移。词表压缩大小断言防止整表行号体系不一致；本函数不验证外部 TileLang 数值等价。

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

</details>

## 设计决策

recipes 用统一配置连接 Hash 和 Gate，表示适配仍需保留两端相同条件。二/三元组是这份适配层的实现合同，不能据此要求其他 TileLang 内核或 vLLM 后端返回相同结构。区分权重乘积融合和检索投影融合，能避免跳过仍存在的 WKV 阶段；区分返回输出与输入存储，能避免忽略非原位结果。

## 验证信号

- [来源平台：950（仅源码目标，未上板）；证据等级：artifact_verified，静态源码] Hash 与 Engram 均由 native/tilelang 选择器控制；仅 Prefill+tilelang 生产/消费二元组。
- [来源平台：950（仅源码目标，未上板）；证据等级：artifact_verified，静态源码] native Prefill 和 Decode 采用三元组；WKV 是独立 Linear，TileLang Gate 以 inplace=False 调用。

没有外部 kernel、图、精度或性能通过信号；保持 draft，未生成 verified 事件。

## 部署验收

待执行：保存 native/TileLang 的 hash、投影、元组与 Gate 输出对照，包含图像；开关多流并确认 Decode 合同不变；单独验收真实版本的 torch compile/capture，保存原始失败与误差分布。

## 坏实践

混用两种元组、让 Hash 跳过边界 mask、把 fused_weight 当 WKV 融合、忽略非原位返回值，或仅因 Prefill 可选就把 Decode 一起切换，都不满足当前合同。

## 失效边界

TileKernels 实际签名、精度与图版本支持未知；非有限值、signed-zero 和 clamp 边界未做对照。文档性能描述未独立确认，本卡不承诺收益。
