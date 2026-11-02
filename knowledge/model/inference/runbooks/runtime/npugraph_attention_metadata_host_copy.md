---
type: Runbook
title: DSpark 捕获报 aclrtMemcpy 107030：把 Attention metadata 的 Host 构造移到图外
description: 在 DSpark GQA 的图外 prepare_decode_inputs 中准备长度张量与 Attention metadata，再传给
  forward_spec_decode；固定容量属性并以张量携带动态长度，目标 NPU 验收仍待完成。
tags:
- task.debugging
- topic.graph_execution
- topic.attention
- topic.speculative_decoding
status: draft
sources: []
created_at: '2026-10-30T03:17:18Z'
updated_at: '2026-10-30T09:01:39Z'
platforms:
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      execution_mode:
      - npugraph_ex
      phase:
      - decode
---

# DSpark 捕获报 aclrtMemcpy 107030：把 Attention metadata 的 Host 构造移到图外

## 现象

在 Kimi K3 的 DSpark GQA 草稿模型启用 npugraph Decode 时，排查首个捕获失败点出现的 `aclrtMemcpy`、`107030`、`stream is capture`。目标路径是 Qwen3 GQA 草稿层使用的 Flash Attention metadata 构造，不是主模型的 MLA cache 分配。若错误后才出现通信超时，应先保留首发栈，不能直接把后续超时当根因。

这份适配针对“图内从 Python 长度列表创建 device Tensor”的实现。没有完整的修前/修后 NPU 运行日志可供本卡验收；以下代码证明了输入准备位置的变化，不证明错误已经在任意环境消失，因此保留 draft。

## 适用场景

- 工程入口：`modeling_dspark.py` 中 `K3DSparkForCausalLM.prepare_decode_inputs()` → `run_decode_proposal()` → `forward_spec_decode()` → `K3DSparkModel.forward()` → GQA attention。
- 模式与平台：昇腾 950PR/DT 的 DSpark GQA、固定形状 Decode、npugraph 捕获；确切 CANN、PyTorch、torch_npu 组合需从部署环境核对，本卡没有完成上板版本矩阵。
- 适用粒度：具有这些准备入口和 tensor 参数的实现。先检查实际调用链，不要求所有草稿模型采用同一 API。
- 采用条件：只有确认张量构造位于捕获区、且来源确为 Host 数据时采用；eager 可作正确性对照。主模型 MLA、其他 DSpark 接口及在线请求动态 shape 不在本卡已确认范围内。

## 输入契约与根因

Host 的长度列表进入 `torch.tensor(..., device=...)`，会引入 Host 到设备的数据构造。若这一步发生在捕获区域，会把不允许的同步复制带入图。单纯把 `torch.tensor` 换成另一种写法，仍在图内读取 Python 列表或回传 Host 值，不能解决边界问题。

第二个问题是属性与数据混用：`max_seqlen_kv` 会进入图属性，逐轮使用 `max(actual_seq_kvlen)` 会让属性随生成增长。修正将容量上界固定为 `max_cache_len`，真实长度仍由 Tensor `seqused_kv` 传递。固定容量不意味着把所有请求的有效 KV 长度都改成容量上限。

| 输入 | 含义与构造 | 应保持的条件 |
|---|---|---|
| `cu_seqlens_q` | int32 累积 Q 边界，包含起始 0；本实现每个本地请求提出 `next_n` 个位置 | 请求数和真实分段一致 |
| `seqused_q` | `cu_seqlens_q[1:] - cu_seqlens_q[:-1]` | 与 Q 输入分段一致，不能用 KV 长度代替 |
| `seqused_kv` | 每个 owner-local 请求的上下文长度加 `next_n` | 值逐轮变化，仍作为图输入流动 |
| `fia_metadata` | 用上述长度、head 信息和布局生成的 metadata | 与本轮 block table、位置和长度匹配 |
| `max_seqlen_kv` | `self.model.max_cache_len` | 属性固定、覆盖真实长度，不承担有效长度语义 |

布局也属于接口：metadata 中 Q/输出为 `TND`，KV 为 `PA_BBND`，不能只移动构造位置却保留另一算子版本的布局参数。

## 原实现与完整准备方法

旧 `K3DSparkModel.forward()` 在图内构造长度和 metadata。下列为该类方法原文；依赖原模型的投影、norm、层列表及 attention 实现，不能单独粘贴成独立网络：

```python
def forward(
    self,
    input_ids: torch.Tensor,
    target_hidden_states: torch.Tensor,
    context_cos_sin: Tuple[torch.Tensor, torch.Tensor],
    draft_cos_sin: Tuple[torch.Tensor, torch.Tensor],
    context_slot_mapping: torch.Tensor,
    draft_slot_mapping: torch.Tensor,
    block_table: torch.Tensor,
    actual_seq_qlen: list[int],
    actual_seq_kvlen: list[int],
    cache_data: Tuple[Dict[str, torch.Tensor], ...],
) -> torch.Tensor:
    # The legacy FIA v2 API consumed cumulative Q lengths as a Python
    # list. The transformer-op API requires both cumulative and per-row
    # lengths as device int32 tensors.
    cu_seqlens_q = torch.tensor(
        [0, *actual_seq_qlen],
        dtype=torch.int32,
        device=input_ids.device,
    )
    seqused_q = cu_seqlens_q[1:] - cu_seqlens_q[:-1]
    seqused_kv = torch.tensor(
        actual_seq_kvlen,
        dtype=torch.int32,
        device=input_ids.device,
    )
    batch_size, max_seqlen_q = input_ids.shape[:2]
    max_seqlen_kv = max(actual_seq_kvlen)
    fia_metadata = flash_attn_metadata(
        batch_size=batch_size,
        cu_seqlens_q=cu_seqlens_q,
        seqused_q=seqused_q,
        seqused_kv=seqused_kv,
        num_heads_q=self.layers[0].self_attn.total_num_heads,
        num_heads_kv=self.layers[0].self_attn.num_kv_heads,
        head_dim=self.layers[0].self_attn.head_dim,
        max_seqlen_q=max_seqlen_q,
        max_seqlen_kv=max_seqlen_kv,
        mask_mode=0,
        win_left=-1,
        win_right=-1,
        layout_q="TND",
        layout_kv="PA_BBND",
        layout_out="TND",
    )
    attn_metadata = {
        "context_slot_mapping": context_slot_mapping,
        "draft_slot_mapping": draft_slot_mapping,
        "block_table": block_table,
        "fia_metadata": fia_metadata,
        "cu_seqlens_q": cu_seqlens_q,
        "seqused_q": seqused_q,
        "seqused_kv": seqused_kv,
        "max_seqlen_kv": max_seqlen_kv,
    }
    context_states, _ = self.hidden_norm(
        self.fc(target_hidden_states)
    )
    hidden_states = self.embed(input_ids)
    residual = None
    for layer, layer_cache in zip(self.layers, cache_data):
        hidden_states, residual = layer(
            hidden_states,
            residual,
            context_states,
            context_cos_sin,
            draft_cos_sin,
            attn_metadata,
            layer_cache,
        )
    hidden_states, _ = self.norm(hidden_states, residual)
    return hidden_states
```

新实现将准备工作放在图外 `prepare_decode_inputs()`，并把结果装入 `decode_inputs`。下面保留完整方法，包含位置、slot、采样噪声及静态标记，避免只移动四个变量而遗漏调用契约。它依赖原类已初始化的 TP 配置、rotary embedding、cache 和 `build_paged_slot_mapping`：

```python
def prepare_decode_inputs(
    self,
    input_dict: Dict,
    main_next_tokens: torch.Tensor,
    target_hidden_states: torch.Tensor,
) -> Dict:
    context_positions = input_dict["target_hidden_positions"]
    block_table = input_dict["block_table"]
    slot_block_table = input_dict["slot_block_table"]
    cache_data = input_dict["cache_data"]
    decode_batch_size = self.infer_config.scheduler_config.batch_size_per_dp_rank
    local_batch = decode_batch_size // self.attn_tp_size
    context_lengths = (
        context_positions.view(local_batch, -1).max(dim=1).values + 1
    )
    last_context_position = context_lengths - 1
    active_rows = last_context_position >= 0
    offsets = torch.arange(
        1,
        self.next_n + 1,
        device=context_positions.device,
        dtype=torch.long,
    )
    draft_positions = last_context_position.unsqueeze(1) + offsets.unsqueeze(0)
    draft_positions = torch.where(
        active_rows.unsqueeze(1),
        draft_positions,
        torch.full_like(draft_positions, -1),
    )
    context_cos, context_sin = self.model.rotary_emb(context_positions)
    draft_cos, draft_sin = self.model.rotary_emb(draft_positions)
    context_slot_mapping = build_paged_slot_mapping(
        context_positions,
        slot_block_table,
        self.block_size,
    )
    draft_slot_mapping = build_paged_slot_mapping(
        draft_positions,
        slot_block_table,
        self.block_size,
    )
    stable_next_tokens = main_next_tokens[:, :1]
    actual_seq_qlen = [self.next_n * (idx + 1) for idx in range(local_batch)]
    context_lengths_list = context_lengths.detach().cpu().tolist()
    actual_seq_kvlen = [
        length + self.next_n for length in context_lengths_list
    ]
    # Build transformer FA metadata outside the compiled graph. Creating
    # device tensors from Python lists inside NPUGraph capture triggers a
    # synchronous host-to-device copy, which is unsupported in GLOBAL mode.
    cu_seqlens_q = torch.tensor(
        [0, *actual_seq_qlen],
        dtype=torch.int32,
        device=context_positions.device,
    )
    seqused_q = cu_seqlens_q[1:] - cu_seqlens_q[:-1]
    seqused_kv = torch.tensor(
        actual_seq_kvlen,
        dtype=torch.int32,
        device=context_positions.device,
    )
    # This bound flows through decode_inputs into a graph ATTR, so its
    # value must stay constant across steps: a per-step exact value would
    # recompile the captured graph every round. The exact per-step lengths
    # are carried by the seqused_kv tensor at runtime.
    max_seqlen_kv = self.model.max_cache_len
    fia_metadata = flash_attn_metadata(
        batch_size=local_batch,
        cu_seqlens_q=cu_seqlens_q,
        seqused_q=seqused_q,
        seqused_kv=seqused_kv,
        num_heads_q=self.model.layers[0].self_attn.total_num_heads,
        num_heads_kv=self.model.layers[0].self_attn.num_kv_heads,
        head_dim=self.model.layers[0].self_attn.head_dim,
        max_seqlen_q=self.next_n,
        max_seqlen_kv=max_seqlen_kv,
        mask_mode=0,
        win_left=-1,
        win_right=-1,
        layout_q="TND",
        layout_kv="PA_BBND",
        layout_out="TND",
    )
    sample_noise = None
    if self.temperature > 0:
        sample_noise = torch.empty(
            local_batch,
            self.next_n,
            self.config.vocab_size,
            device=target_hidden_states.device,
            dtype=torch.float32,
        ).exponential_()
    decode_inputs = {
        "main_hidden": target_hidden_states.contiguous(),
        "main_next_tokens": stable_next_tokens,
        "cached_len": context_lengths,
        "context_cos": context_cos,
        "context_sin": context_sin,
        "draft_cos": draft_cos,
        "draft_sin": draft_sin,
        "context_slot_mapping": context_slot_mapping,
        "draft_slot_mapping": draft_slot_mapping,
        "block_table": block_table,
        "cu_seqlens_q": cu_seqlens_q,
        "seqused_q": seqused_q,
        "seqused_kv": seqused_kv,
        "fia_metadata": fia_metadata,
        "max_seqlen_kv": max_seqlen_kv,
        "cache_data": cache_data,
        "sample_noise": sample_noise,
    }
    if self.execute_mode != "eager":
        for value in decode_inputs.values():
            if isinstance(value, torch.Tensor):
                torch._dynamo.mark_static(value)
            elif isinstance(value, tuple):
                for layer_cache in value:
                    for cache_value in layer_cache.values():
                        if isinstance(cache_value, torch.Tensor):
                            torch._dynamo.mark_static(cache_value)
    return decode_inputs
```

## 判别与处理步骤

1. 从捕获失败栈回到 `forward_spec_decode`，检查其下游是否仍调用 `torch.tensor(Python列表, device=...)`，以及 metadata helper 是否位于捕获区。先确定首个实际站点；错误号本身不能唯一确定根因。
2. 沿 `run_decode_proposal` 的调用者核对准备时机。此实现逐轮入口是 `prepare_decode_inputs()`；同类的 `propose()` 仅预填上下文 cache，并返回空 proposal，不能把修改放在那里后就认为逐轮输入已经更新。
3. 图外同时生成四份 tensor，并增加 `forward_spec_decode` 与 `K3DSparkModel.forward` 的形参和透传。检查 `decode_inputs` 的键、两层函数签名、attention 字典和实际算子参数五处一致，避免部分仍消费旧列表。
4. 将属性上界固定为分配 cache 的容量，验证真实 `seqused_kv` 不超界。不要把动态长度也冻结，否则图能捕获但可能读错有效 cache。
5. 保留代码中的 owner-local 请求划分。`local_batch = decode_batch_size // attn_tp_size`，context、block table 和长度 tensor 必须描述同一批本地请求；不能把全 batch 的长度混入某个 owner 的 metadata。

## 设计决策

方案把“Host 构造”和“需要逐轮变化的设备输入”分开，而非消除真实长度变化。代码中的 `.cpu().tolist()` 仍在图外，因而不能据此宣称整个 proposal 无 Host 同步开销。`mark_static` 用于固定形状/布局约束，也不等于把张量内容固定为首轮值。

## 验证信号

本轮已核对：旧方法的构造位置、新方法的完整返回字典、逐层形参透传与固定容量属性。未执行 CPU 模型测试或 NPU capture/replay；没有修后通过的运行回执。

## 部署验收

在目标环境逐项执行以下验收，并保存实际输入摘要及首发异常：

- capture：四份 tensor 进入图之前已构造，捕获成功，图内不再出现该站点的同步 H2D。
- replay：至少两轮保持 shape/stride/dtype 相同，同时改变真实输入、位置和 KV 长度。对齐 eager 输出、cache 写入位置及历史保留；不能只重放同一份首轮输入。
- 容量与重编译：真实长度未越过 `max_cache_len`，统计重编译次数，确认未因逐步 KV 长度变化创建新图。
- 语义：确认 `seqused_kv` 的值确实更新，active/inactive 行与 slot 对齐。捕获通过只证明执行边界，不替代生成精度验收。

## 坏实践、回退与失效边界

- 仅关闭报错检查、把数据从 Host 复制换个 API、或把上界当真实长度，都不是本机制的完整修复。
- 主模型采用 MLA 并不意味着草稿路径也是 MLA；要按实际类和算子签名定位。
- 回退时切回相同权重、请求和长度的 eager 路线，成套恢复输入准备与形参，避免新旧接口混用。eager 成功不能证明图已修复。
- 未决优先项是取得目标环境修前首发栈与修后变化输入 replay 的成对结果。接口或布局版本不同，先重新核对 schema；普通 Host 同步排查可继续阅读[图断点与 Host 同步](../../guides/integration/graph_break_elimination_host_sync_unsupported_ops.md)。
