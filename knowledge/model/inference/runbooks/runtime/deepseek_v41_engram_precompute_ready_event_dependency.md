---
type: Runbook
title: 异步预计算提前读取：让消费流等待对应结果
description: 可迁移机制：预计算按结果身份建立生产完成到消费的依赖，并另查生命周期；ready、ev5与GE helper仅为本文recipes实例。
tags:
- task.debugging
- topic.implementation.synchronization
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:38:52Z'
platforms:
- '950'
aliases:
- DeepSeek V4.1 Engram 预计算在消费层等待 ready
---

# 异步预计算提前读取：让消费流等待对应结果

## 适用性与框架边界

本卡以**异步生产者、结果身份、完成依赖和实际消费者**为主线。主机上有结果句柄，不等于设备结果已能读取。

| 层次 | 读用范围 |
|---|---|
| 通用原则 | 只提前计算不依赖当前层状态的部分；消费流须等待同一结果的生产完成，并单独保证张量在整个消费期间存活。 |
| 成立前提 | 已确认哪些输入可提前取得、每份结果对应哪个 batch/层/行域，以及所用执行模式的真实完成与生命周期合同。 |
| recipes 专属 | 首/末 Engram 层调度、pending/ready 字段、ev5 与 GE helper 是本文实现。ev5 在 GMM 前，不能当 GMM 完成；record_stream 只登记指定流，不能证明主消费流生命周期。GE helper 不建立这组 native ready 依赖。 |
| vLLM / 其他框架入口 | 从模型执行的输入准备、异步预计算 producer、实际模型 consumer 与流/图依赖追踪；不要照搬层号选择、字典键或事件编号。 |

本轮只核验 recipes 固定源码，没有设备竞态、vLLM 接入或图等价性验收。

## 适用场景

Engram 从 token 上下文构造 Hash，用行号查记忆表（Embedding），再以 WKV 线性投影生成 Gate 所需的 key/value 等数据。Hash、查表和 WKV 只依赖 token 与固定权重，可以在主计算流抵达消费层前提交；Gate 还依赖该层当时的 hidden_states，所以必须留在消费层。这里的 WKV 是 Engram 自己的投影，不是注意力 KV cache。

stream 是设备有序队列，副流提交函数返回只说明主机已发出任务。ready event 表达“预计算生产完再消费”的跨流依赖；resource event 表达有意的资源排序；record_stream 登记张量在某个流的生命周期使用。这三者不能互相替代。

上面的生产消费诊断可按目标执行模式复用；下述 ready API 与调度条件限 recipes 中 DeepSeek V4.1 eager/npugraph_ex、enable_engram_multi_stream 且 with_engram 成立。开关缺省继承 enable_multi_streams；调度只处理配置中的首个与末个 Engram 层。路线为 recommended_fastpath 的当前实现合同核查。目标平台 950；仅固定源码静态核验，未运行 CPU/NPU、编译、图、精度或性能测试，CANN/外部包版本未知。recipes 的 GE helper 不执行 native ready record/wait，也不建立这组 native ready 依赖；不能从同一调用位置推导其图内等价完成依赖成立。

## 现象

结果句柄已存在或主机提交函数已返回，均不保证对应设备张量完成。本文 recipes 中，pending 字典已有元组或主机已从 Decoder 函数返回，同样不能代替设备完成合同。另有一处注释把 resource ev[5] 称作 post-GroupedMM，但实际 TP/EP 代码在路由/Dispatch 后、self.moe_ffn 之前记录。若据注释判断 WKV 完全避开专家矩乘竞争，就超出了代码证据。本轮没有实际竞态、资源竞争或时间线测量。

## 根因与判别方法

把“结果归属”“结果完成”“存储存活”分开核对，避免用一个 pending 标记代替三类合同。下表的字段、元组与事件位置属于 recipes 参考实例；目标框架按自己的结果协议与同步语义检查。

| 数据/资源 | 轴、来源或记录位置 | 消费者与含义 |
|---|---|---|
| full_input_ids | 完整序列的 token ID；上游输入 | 副流 Hash |
| engram_hashes | [B,T,Engram层数,hash列数] 行号；B为请求批维、T为该维内token行数，Prefill打包时B=1；Hash 产生 | 早/晚层查表，共用一份 |
| embeddings | [token行数,hash列数×表向量宽度] | 副流 WKV |
| kv / precomputed | native 为 key/value/weight；TileLang Prefill 为 kv/weight_fused，均保留 token 行对应关系 | 对应层 Gate；具体轴见下文 |
| side_pending | 主机字典，暂存早层 embeddings 和阶段标记 | 层循环稍后提交 WKV |
| pending_engram | layer_idx→已提交的预计算元组；不是完成状态表 | _wait_engram_ready 与 Decoder |
| ready[i] | 对应预计算提交之后在副流 record | 主流到消费层前 wait；eager/npugraph_ex |
| resource ev[5] | 主流路由/Dispatch 后、routed GMM 前 record；只在 eager 创建 | 早层 WKV 提交前等待资源边界 |
| record_stream(kv, engram_stream) | 指定的是生产副流 | allocator 使用登记，未证明主消费流生命周期 |

本文 recipes 结果协议中，native 元组中 key 为 [T,M,D]、value 为 [T,D]、weight 为 [M,D]；TileLang Prefill 中 kv 为 [T,M+1,D]、weight_fused 为 [M,D]。T 为本地 token 行，M 为隐藏副本数，D 为隐藏通道。调度器不解包，Gate 必须按相同后端与模式解释元组。

教学推演（非设备实测）：主流顺序为 Dispatch→record ev5→GMM1→激活→GMM2；副流在 wait ev5 后提交 WKV。ev5 只要求副流排在 Dispatch 边界之后，GMM1/GMM2 仍可能尚在执行。即使主机等 _run_decoder_layer 返回才提交 WKV，也不能把主机返回当作设备 GMM 完成。因此“ready 在 WKV 后，Gate 在 ready 后”可以表达数据依赖；“ev5 保证 GMM 已完成”则不成立。另设 early 层预计算写入 pending 后立即抵达 Gate：只有对应 ready 的 record/wait，才使字典中的数据句柄拥有消费前的完成约束。

## 诊断路径

1. 在自己的框架定位可预计算的数据生产者、使用当前层状态的消费者与层执行入口；若使用 Engram，再对应到 Hash、查表、检索投影和 Gate。记录每个结果对应的层号、batch 身份、token 行域和后端表示。先确认可预计算的部分确实不读取当前层隐藏状态。
2. 记录生产 stream、ready 的本轮对象/generation、record 所在算子之后的位置，以及 Gate 前 wait 的实际流。预期每次消费有同一批次的生产完成边，使用事件或该执行模式明确支持的等价依赖；缺失时先恢复该边或退回已验收的单流路径，再比较输出。
3. 分开记录 resource event。沿实际 record 调用向前后找到最近算子，不能只读编号或注释。若要证明 WKV 与专家矩乘没有某种竞争，需设备时间线或明确完成事件；recipes 的 ev5 不能作本实现的 GMM 完成依据，其他后端也应按自身 record 位置解读资源事件。
4. 记录 kv 的所有持有者、生产/消费流登记、pending.pop 和消费者结束的关系。recipes 本源码只对返回 kv 登记生产副流；还需检查主流使用期间的引用与 allocator reuse，不能把 ready wait 当作生命周期证明。
5. 复验单流/多流相同输入输出、早层/晚层、多 batch 和事件重录；分别验证 eager 与图模式。采用本文 recipes 首/末层调度时，早层就是第一个 Decoder 层、额外中间 Engram 层和缺失层需显式覆盖；所有框架还需核对输入/metadata 的上游生产依赖。

<details>
<summary>recipes / CANN Executor 完整实现对照（可选阅读）</summary>

## 快速检查

下列搜索为已有 recipes 源码的可选对照，外部框架按职责和实际事件边定位。

```bash
rg -n 'engram_ready_events|pending_engram|engram_resource_events|record_stream\(True, tensor|def _wait_engram_ready' models/deepseek_v4_1/models/modeling_deepseek.py
```

## 系统信息

以下来自模型调度和流工具，依赖 PyTorch、torch_npu、模型层与通信配置。源码注释中的意图原样保留，块外以实际调用位置说明边界；本卡未新增或执行同步实现。

## 机制代码

### 初始化

创建副流与每个配置层的 ready；resource_events 仅在 eager 创建，npugraph_ex 不继承该资源排序。注释中的 ev5 含义须与下面真实生产者对照。

```python
        # Engram multi-stream configuration
        custom_params = self.infer_config.model_config.custom_params
        self.engram_tp_size = int(custom_params.get("engram_tp_size", 1))
        self.enable_engram_offload = bool(custom_params.get("enable_engram_offload", False))
        self.enable_engram_multi_stream = bool(
            custom_params.get("enable_engram_multi_stream", self.enable_multi_streams)
        )
        exe_mode = self.infer_config.model_config.exe_mode
        self.engram_stream = None
        self.engram_layer_ids = ()
        self.engram_ready_events = ()
        self.engram_resource_events = None
        if self.enable_engram_multi_stream and self.with_engram:
            self.engram_stream = create_stream("engram_precompute", exe_mode)
            self.engram_layer_ids = tuple(
                self.engram_layout.layer_ids if self.engram_layout else ())
            self.engram_ready_events = tuple(
                create_event(exe_mode, True) for _ in self.engram_layer_ids)
            # Resource events gate Cube/Vector overlap on Layer-0 (ev[5] =
            # post-GroupedMM boundary, consumed by the wkv wait on the side
            # stream).  Eager only.
            if exe_mode not in ("ge_graph", "npugraph_ex"):
                self.engram_resource_events = tuple(
                    create_event(exe_mode, True) for _ in range(6)
                )
```

### 初始提交：_schedule_engram_multistream

输入完整 token、历史/mask 与 metadata；副流产生整份 hashes 和早层 embeddings。pending 初始为空，side_pending 的 embeddings_done 表示主机已提交到该阶段，不是设备完成。函数返回三个句柄供层循环使用。

```python
    def _schedule_engram_multistream(self, input_ids, is_prefill, exe_mode, attn_metadata,
                                     prefix_input_ids=None, ngram_shift_mask=None):
        """Submit hash (Stage 0) + embedding (Stage 1) for the early engram
        layer to the side stream before the layer loop starts.

        wkv (Stage 2) is submitted later from _run_decoder_layer after
        Layer-0's GroupedMM completes, so wkv (Cube) does not contend
        with GroupedMM (Cube).

        Returns: (pending, side_pending, engram_hashes)
            pending:       {layer_idx: (key,value,weight)} — empty initially;
                           early entry filled after Layer-0.
            side_pending:  mutable dict carrying embeddings
                           from here to _run_decoder_layer; None if disabled.
            engram_hashes: hash tensor computed on the side stream; needed
                           for late-layer submission; None if disabled.
        """
        if not (self.enable_engram_multi_stream and self.with_engram):
            return {}, None, None

        early = self.engram_layer_ids[0] if self.engram_layer_ids else None
        if (early is None or early >= len(self.layers)
                or getattr(self.layers[early], "engram", None) is None):
            return {}, None, None

        # Mutable result table populated by the decoder layer loop.
        pending = {}
        side_pending = {'stage': 'init'}

        with npu_stream_switch(True, self.engram_stream, exe_mode=exe_mode):
            engram_hashes = self.compute_engram_hashes(
                input_ids, is_prefill, attn_metadata,
                prefix_input_ids=prefix_input_ids,
                ngram_shift_mask=ngram_shift_mask)
            early_layer = self.layers[early]
            layer_hash_index = early_layer.engram.layer_hash_index
            layer_engram_hash = engram_hashes[:, :, layer_hash_index, :]
            embeddings = early_layer.engram.precompute_embeddings(
                layer_engram_hash, is_prefill=is_prefill)
            side_pending['embeddings'] = embeddings
            side_pending['stage'] = 'embeddings_done'

        record_stream(True, embeddings, self.engram_stream, exe_mode)

        return pending, side_pending, engram_hashes
```

### 晚层提交：_submit_late_engram

在早层消费者的主机调用返回后提交末层预计算，复用 hashes，不重算上下文 hash。kv 后 record 对应 ready；随后对各 tensor 登记的仍是生产副流。

```python
    def _submit_late_engram(self, engram_hashes, is_prefill, exe_mode):
        """Submit the late engram layer after the early layer's gating is done.

        Called from the layer loop once the early engram consumer has returned.
        No resource gating is needed — the late precompute overlaps with the
        intermediate decoder layers (2..N-2), which provide enough mixed
        Cube/Vector work to avoid contention.
        """
        if len(self.engram_layer_ids) < 2:
            return None
        late = self.engram_layer_ids[-1]
        if (late >= len(self.layers)
                or getattr(self.layers[late], "engram", None) is None):
            return None
        late_layer = self.layers[late]
        late_idx = len(self.engram_layer_ids) - 1
        with npu_stream_switch(True, self.engram_stream, exe_mode=exe_mode):
            layer_hash_index = late_layer.engram.layer_hash_index
            layer_engram_hash = engram_hashes[:, :, layer_hash_index, :]
            kv = late_layer.engram.precompute(layer_engram_hash, is_prefill=is_prefill)
            record_event(True, self.engram_ready_events, late_idx, exe_mode)
        for tensor in kv:
            record_stream(True, tensor, self.engram_stream, exe_mode)
        return kv
```

### 消费前等待：_wait_engram_ready

输入即将执行的 Decoder 和 pending；有预计算且层号在配置中时，主流等该层 ready。它既不提交缺失预计算，也不检查元组后端是否匹配。

```python
    def _wait_engram_ready(self, decoder_layer, pending_engram, exe_mode):
        """Wait for the side stream to finish before consuming precomputed results."""
        layer_idx = decoder_layer.layer_idx
        precomputed = pending_engram.get(layer_idx)
        if precomputed is None:
            return
        if layer_idx in self.engram_layer_ids:
            wait_event(True, self.engram_ready_events,
                       self.engram_layer_ids.index(layer_idx), exe_mode)
```

### 调度中枢：_run_decoder_layer

函数把当前层预计算交给 Decoder，并在两个主机边界追加副流任务。按表定位长函数：

| 段落 | 中间变量 | 数据/资源含义 |
|---|---|---|
| 消费入口 | current_precomputed、layer_engram_hashes | 选择已提交元组或单流 hash |
| 当前 Decoder 调用 | resource_events、kv_cache | 仅第一个 Decoder 获得资源事件；kv_cache 是注意力资源，区别于 Engram kv |
| 第一个 Decoder 返回后 | early、engram_side_pending、kv | 等可选 ev5 后提交早层 WKV，record ready[0]，放进 pending |
| 早层返回后 | late_result | 提交末层预计算，保存对应 pending |

注释把返回与 post-GroupedMM 相联系，但没有设备同步证明；以真实 record/wait 为准。

```python
    def _run_decoder_layer(self, decoder_layer, hidden_states, pre_mix, attn_metadata,
                           residual, is_prefill, cur_topk_list, input_ids, image_mask,
                           prefill_moe_global_chunks,
                           engram_hashes, pending_engram, exe_mode,
                           engram_side_pending=None):
        """Invoke one decoder layer with appropriate engram arguments."""
        layer_idx = decoder_layer.layer_idx
        consumes_engram = getattr(decoder_layer, "engram", None) is not None
        use_engram_ms = self.enable_engram_multi_stream and self.with_engram

        current_precomputed = pending_engram.get(layer_idx) if consumes_engram else None
        layer_engram_hashes = None
        if not use_engram_ms and engram_hashes is not None and consumes_engram:
            layer_hash_index = decoder_layer.engram.layer_hash_index
            layer_engram_hashes = engram_hashes[:, :, layer_hash_index, :]

        # Only Layer-0 needs resource events (ev[5] = post-GroupedMM
        # boundary consumed by the wkv wait on the side stream).
        resource_events = self.engram_resource_events if layer_idx == 0 else None

        kv_cache = self.kv_cache_by_layer[layer_idx]
        kv_cache.shared_idx = self.shared_idx
        kv_cache.candidates = self.candidates
        hidden_states, pre_mix = decoder_layer(
            hidden_states,
            pre_mix,
            attn_metadata=attn_metadata,
            past_residual=residual,
            is_prefill=is_prefill,
            cur_topk_list=cur_topk_list,
            input_ids=input_ids,
            image_mask=image_mask,
            prefill_moe_global_chunks=prefill_moe_global_chunks,
            kv_cache=kv_cache,
            engram_hashes=layer_engram_hashes,
            engram_precomputed=current_precomputed,
            engram_resource_events=resource_events,
        )
        self.shared_idx = kv_cache.shared_idx
        self.candidates = kv_cache.candidates

        early = self.engram_layer_ids[0] if self.engram_layer_ids else None

        # After Layer-0 completes: submit wkv (Stage 2) to the side stream.
        # wkv waits on ev[5] (post-GroupedMM) so it only starts after
        # GroupedMM (Cube) finishes, avoiding Cube contention.  The main
        # stream continues to Layer-1 immediately.
        if (use_engram_ms and layer_idx == 0 and engram_side_pending is not None
                and engram_side_pending.get('stage') == 'embeddings_done'
                and early is not None):
            early_layer = self.layers[early]
            with npu_stream_switch(True, self.engram_stream, exe_mode=exe_mode):
                wait_event(self.engram_resource_events is not None,
                           self.engram_resource_events, 5, exe_mode)
                kv = early_layer.engram.precompute_kv(
                    engram_side_pending['embeddings'], is_prefill=is_prefill)
                record_event(True, self.engram_ready_events, 0, exe_mode)
            for tensor in kv:
                record_stream(True, tensor, self.engram_stream, exe_mode)
            pending_engram[early] = kv

        # After the early engram layer's gating completes on the main stream,
        # submit the late engram layer to the same side stream.  By this point
        # the early precompute is already consumed, so the late precompute
        # cannot block the early ready event.
        if use_engram_ms and layer_idx == early and len(self.engram_layer_ids) > 1:
            late_result = self._submit_late_engram(
                engram_hashes, is_prefill, exe_mode)
            if late_result is not None:
                pending_engram[self.engram_layer_ids[-1]] = late_result

        return hidden_states, pre_mix
```

### 层循环

先提交初始 Hash/Embedding；每层先等 ready，再调用 _run_decoder_layer，随后 pop 当前 pending。pop 删除主机字典项，不是额外的设备完成屏障。

```python
        # --- Engram multi-stream scheduling ---
        # Multistream: hash + embedding on side stream; wkv after Layer-0.
        # Non-multistream: hash on main stream.
        pending_engram, side_pending, engram_hashes = self._schedule_engram_multistream(
            full_input_ids, is_prefill, exe_mode, attn_metadata,
            prefix_input_ids=prefix_input_ids,
            ngram_shift_mask=ngram_shift_mask)
        if engram_hashes is None and self.with_engram:
            engram_hashes = self.compute_engram_hashes(
                full_input_ids, is_prefill, attn_metadata,
                prefix_input_ids=prefix_input_ids,
                ngram_shift_mask=ngram_shift_mask)

        for layer_idx, decoder_layer in enumerate(self.layers):
            if layer_idx in self.collect_layer_ids:
                collected_hidden_states.append(hidden_states.mean(dim=1))
            self._wait_engram_ready(decoder_layer, pending_engram, exe_mode)
            hidden_states, pre_mix = self._run_decoder_layer(
                decoder_layer, hidden_states, pre_mix, attn_metadata, residual,
                is_prefill, cur_topk_list, input_ids, image_mask,
                prefill_moe_global_chunks,
                engram_hashes, pending_engram, exe_mode,
                engram_side_pending=side_pending)
            pending_engram.pop(layer_idx, None)
```

### EP 的 ev5 生产者

EP（专家并行）Dispatch 将 token 送到负责的专家 rank（通信进程）；GMM1/激活/GMM2 由 moe_ffn 执行，Combine 合回。下面 ev5 明确在 moe_ffn 前。其后 shared 分支和 Combine 是上下文，不改变该记录位置。

```python
    def moe_infer_dispatch_combine(self, x, topk_ids, topk_weight, shared_expert_stream, moe_events,
                                   engram_resource_events=None):
        """
        tp+ep mix strategy, for decode stage
        """
        num_tokens, h = x.shape
        hidden_states = x
        self.set_mc2_kwargs()

        # moe dispatch
        expert_ids = topk_ids
        dispatch_args = {
            "x": hidden_states,
            "expert_ids": expert_ids, # [n*topk]
            **self.dispatch_kwargs
        }
        # Resource boundary 4: dispatch is MIX_AIV (Vector window for wkv).
        if engram_resource_events is not None:
            record_event(True, engram_resource_events, 4,
                         self.infer_config.model_config.exe_mode)
        output = torch_npu.npu_moe_distribute_dispatch_v2(**dispatch_args)
        expand_x, dynamic_scale, expand_idx, expert_token_num, ep_recv_counts, tp_recv_counts = output[:6]

        # compute experts
        gmm_args = {
            "x": expand_x,
            "expert_tokens": expert_token_num,
            "group_list_type": 1,
            "swiglu_limit": self.swiglu_limit,
            "enable_cann_ops_nn": True
        }

        if "a16" not in self.gmm_quant_mode:
            if "mxfloat" in self.gmm_quant_mode:
                # match GMM operator requirement (dim0, dim1)->(dim0, dim1//2, 2)
                dynamic_scale = reshape_mx_scale(dynamic_scale)
            gmm_args.update({"pertoken_scale": dynamic_scale})

        # Resource boundary 5: GroupedMM is Cube-heavy, releases Vector window.
        if engram_resource_events is not None:
            record_event(True, engram_resource_events, 5,
                         self.infer_config.model_config.exe_mode)
        hidden_states_ordered_by_experts = self.moe_ffn(**gmm_args)

        shared_expert_events = moe_events.get("shared_expert", [])
        shared_expert_internal_events = moe_events.get("shared_expert_internal", [])
        record_event(self.enable_multi_streams, shared_expert_internal_events, 0)
        main_stream = torch.npu.current_stream() if self.enable_multi_streams else None
        with npu_stream_switch(self.enable_multi_streams, shared_expert_stream):
            wait_event(self.enable_multi_streams, shared_expert_events, 0)
            # shared_expert use multi streams
            hidden_states_share = self.shared_experts(hidden_states.view(-1, hidden_states.shape[-1]), \
                enable_decode_stream=self.enable_multi_streams,
                shared_expert_event=shared_expert_internal_events)
            record_event(self.enable_multi_streams, shared_expert_events, 1)
            record_stream(self.enable_multi_streams, hidden_states_share, main_stream)

        # moe combine
        combine_args = {
            "expand_x": hidden_states_ordered_by_experts,
            "expert_ids": topk_ids,
            "assist_info_for_combine": expand_idx,
            "expert_scales": topk_weight.to(torch.float32), # [n*topk]
            "ep_send_counts": ep_recv_counts,
            "tp_send_counts": tp_recv_counts,
            **self.combine_kwargs
        }
        hidden_states = torch_npu.npu_moe_distribute_combine_v2(**combine_args)
        wait_event(self.enable_multi_streams, shared_expert_events, 1)
        hidden_states = hidden_states + hidden_states_share
        hidden_states = hidden_states.view(num_tokens, self.hidden_dim)
        return hidden_states
```

### TP 的 ev5 生产者

TP（张量并行）在各 rank 上算专家中间维度部分和。本函数在本地路由后立即记录 ev5，然后才调用 moe_ffn；shared 所用的 moe_gmm1 是另一组事件，不能与 ev5 混用。

```python
    def moe_infer_tp(self, x, topk_ids, topk_weight, hidden_states_share, moe_events,
                     engram_resource_events=None, shared_expert_stream=None,
                     shared_merged_x=None):
        """Local routing over all experts; sum the TP-sharded FFN outputs."""
        shared_expert_events = moe_events.get("shared_expert", [])
        if not self.low_latency_tp:
            wait_event(self.enable_multi_streams and hidden_states_share is not None, shared_expert_events, 1)
        routing_args, routing_quantizes_input = self._build_moe_tp_routing_args(x, topk_ids)
        if engram_resource_events is not None:
            record_event(True, engram_resource_events, 4, self.exe_mode)
        expanded_x, row_idx, expert_tokens, pertoken_scale = torch_npu.npu_moe_init_routing_v2(
            x, **routing_args)
        if engram_resource_events is not None:
            record_event(True, engram_resource_events, 5, self.exe_mode)
        shared_h, shared_scale = None, None
        if shared_merged_x is not None:
            record_event(True, moe_events["shared_pipeline"], 0)
            with npu_stream_switch(True, shared_expert_stream):
                wait_event(True, moe_events["shared_pipeline"], 0)
                shared_h, shared_scale = self.shared_experts.swiglu_a8float8(shared_merged_x)
        gmm_args = self._build_moe_tp_gmm_args(
            expanded_x, expert_tokens, pertoken_scale, routing_quantizes_input)
        self.experts.gmm1_events = moe_events["moe_gmm1"] if shared_merged_x is not None else None
        expert_output = self.moe_ffn(**gmm_args)
        if shared_merged_x is not None:
            main_stream = torch.npu.current_stream()
            with npu_stream_switch(True, shared_expert_stream):
                wait_event(True, moe_events["moe_gmm1"], 0)
                hidden_states_share = self.shared_experts.down_proj(shared_h, shared_scale)
                record_stream(True, hidden_states_share, main_stream)
                record_event(True, shared_expert_events, 1)
        if self.low_latency_tp:
            # Only Finalize consumes the shared branch; routing and GMM are independent.
            wait_event(self.enable_multi_streams and hidden_states_share is not None, shared_expert_events, 1)
        output = torch_npu.npu_moe_finalize_routing(
            expert_output, skip1=hidden_states_share, skip2=None, bias=None,
            scales=topk_weight.to(expert_output.dtype),
            expanded_src_to_dst_row=row_idx,
            export_for_source_row=None, drop_pad_mode=2)
        # Shared experts are intermediate-dim sharded too: one reduce for
        # routed + shared partial outputs.
        dist.all_reduce(output, group=self.comm_manager.get_group("moe_tp_group"))
        return output
```

### 流作用域

GE 使用图作用域标签，native 使用 NPU stream；选了流不等于建立 ready 依赖。

```python
def npu_stream_switch(
    switch_flag: bool,
    stream: Union[str, torch.npu.Stream],
    stream_priority: int = 0,
    exe_mode: Optional[str] = None,
):
    if not switch_flag:
        return FakeContextManager()

    if exe_mode == "ge_graph":
        return tng.scope.npu_stream_switch(stream, stream_priority)
    return torch.npu.stream(stream)
```

### 事件记录

只在 native API 条件成立时 record。

```python
def record_event(switch_flag: bool, events: tuple, idx: int, exe_mode: Optional[str] = None):
    """Records the specified NPU event if switch_flag is True."""
    if use_native_stream_api(switch_flag, exe_mode):
        events[idx].record()
```

### 当前流等待

wait 使用当前流；需要核对调用时正在主流还是副流作用域。

```python
def wait_event(switch_flag: bool, events: tuple, idx: int, exe_mode: Optional[str] = None):
    """
    Waits for the specified NPU event to complete if switch_flag is True.

    Note: torch.npu.Event.wait() does NOT support passing a stream explicitly now.
    Internally, it uses torch.npu.current_stream().
    """
    if use_native_stream_api(switch_flag, exe_mode):
        events[idx].wait()
```

### 生命周期登记

仅登记显式传入的流；当前预计算调用传的是 engram_stream。

```python
def record_stream(
    switch_flag: bool,
    out: torch.Tensor,
    stream: Union[str, torch.npu.Stream],
    exe_mode: Optional[str] = None,
):
    """
    Conditionally tracks the tensor's lifecycle on a specific NPU stream
    to prevent premature memory deallocation during asynchronous operations.
    """
    if use_native_stream_api(switch_flag, exe_mode):
        out.record_stream(stream)
```

### native API 条件

GE 返回 False，因而以上 native record/wait 都不执行。

```python
def use_native_stream_api(switch_flag: bool, exe_mode: Optional[str] = None):
    return switch_flag and exe_mode != "ge_graph"
```

### 创建流

GE 返回标签，其他模式创建 native stream；标签不是 native 完成事件。

```python
def create_stream(stream_tag: str, exe_mode: Optional[str] = None) -> Union[str, torch.npu.Stream]:
    if exe_mode == "ge_graph":
        return stream_tag
    return torch.npu.Stream()
```

### 创建事件

GE 分支返回 None，不是可用 ready Event。

```python
def create_event(exe_mode: Optional[str] = None, switch_flag: bool = True):
    if use_native_stream_api(switch_flag, exe_mode):
        return torch.npu.Event()
    return None
```

### 关闭功能时的上下文

本对象本身没有同步行为。

```python
class FakeContextManager:
    def __init__(self) -> None:
        pass

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        pass
```

### 最终消费者：DecoderLayer.forward

函数开头用 engram_precomputed 或 engram_hashes 执行 Engram，再进入注意力和 FFN。Gate 在此接触当前 hidden_states；这解释了等待必须发生在调用 Decoder 之前。随后 resource_events 经 FFN 到达上面 TP/EP 的真实 ev5 生产者。

```python
    def forward(
        self,
        hidden_states: torch.Tensor,
        pre_mix: torch.Tensor,
        attn_metadata: Optional[Dict] = None,
        past_residual: Optional[torch.Tensor] = None,
        is_prefill: Optional[bool] = False,
        cur_topk_list: Optional[torch.Tensor] = None,
        input_ids: Optional[torch.Tensor] = None,
        image_mask: Optional[torch.Tensor] = None,
        prefill_moe_global_chunks: Optional[int] = None,
        kv_cache: Optional[KVCache] = None,
        engram_hashes: Optional[torch.Tensor] = None,
        engram_precomputed=None,
        engram_resource_events=None,
        **kwargs,
    ) -> Tuple[torch.FloatTensor]:
        if self.engram is not None and (engram_hashes is not None or engram_precomputed is not None):
            engram_metadata = attn_metadata.get("engram", {})
            hidden_states = self.engram(
                hidden_states, engram_hashes, is_prefill=is_prefill,
                engram_metadata=engram_metadata, image_mask=image_mask,
                precomputed=engram_precomputed)
        residual = hidden_states
        hidden_states, post, comb, attn_pre = OpKernel.hc_pre(hidden_states, pre_mix,
                                                        self.hc_attn_fn, self.hc_attn_scale,
                                                        self.hc_attn_base, self.hc_mult, self.hc_sinkhorn_iters,
                                                        self.norm_eps, self.hc_eps)

        hidden_states = self.attn_norm(hidden_states)
        hidden_states = self.attn(
            x=hidden_states,
            attn_metadata=attn_metadata,
            is_prefill=is_prefill,
            kv_cache=kv_cache,
        )
        hidden_states = OpKernel.hc_post(
            hidden_states, residual, post, comb, is_prefill=is_prefill
        )

        residual = hidden_states
        hidden_states, post, comb, ffn_pre = OpKernel.hc_pre(hidden_states, attn_pre, self.hc_ffn_fn, self.hc_ffn_scale,
                                                    self.hc_ffn_base, self.hc_mult, self.hc_sinkhorn_iters,
                                                    self.norm_eps, self.hc_eps)

        hidden_states = self.ffn_norm(hidden_states)
        hidden_states = self.ffn(hidden_states,
            is_prefill=is_prefill,
            cur_topk_list=cur_topk_list,
            input_ids=input_ids,
            image_mask=image_mask,
            shared_expert_stream=attn_metadata.get('shared_expert_stream', None),
            prefill_moe_global_chunks=prefill_moe_global_chunks,
            engram_resource_events=engram_resource_events,
            moe_events=attn_metadata.get("moe_events"),
        )
        hidden_states = OpKernel.hc_post(
            hidden_states, residual, post, comb, is_prefill=is_prefill
        )
        return hidden_states, ffn_pre
```

</details>

## 设计决策

Hash/Embedding/WKV 的提前提交与 Gate 的延后消费解耦，但必须保留对应 ready 边。资源排序与数据正确性分开验收，生命周期再单独核对。当前源码不足以证明 WKV 完全避开 Cube（矩阵计算单元）竞争，或 GE 图具有等价 native ready 同步。

## 验证信号

- [来源平台：950（仅源码目标，未上板）；证据等级：artifact_verified，静态源码] 早/晚层预计算后 record 对应 ready，层循环在 Decoder 消费前调用 _wait_engram_ready。
- [来源平台：950（仅源码目标，未上板）；证据等级：artifact_verified，静态源码] ev5 实际在 routed GMM 前记录；预计算 kv 的 record_stream 只登记生产副流；GE 不执行 native ready wait。

没有竞态消除、图执行、精度或性能通过信号；保持 draft，未生成 verified 事件。

## 部署验收

待执行：采集主副流与每轮 event 的设备时间线；对照单流输出，覆盖早/晚/单层、额外中间层和多 batch；验证主流消费期间 storage 生命周期。若要主张无 GMM 竞争，另取明确完成或时间线证据。

## 坏实践

凭 pending 有元组或主机返回判断设备完成、用 record_stream 代替 ready、按 post-GroupedMM 注释解释 ev5、把 eager 资源事件结论套到图模式，都会跨越证据边界。

## 失效边界

优先未决项为 ev5 实际排序对竞争的影响及主消费流的 allocator 生命周期。early=第一个 Decoder 时，预计算在其返回后才提交的结构需单独验收；超过早/末两处 Engram、输入/metadata 上游生产依赖、重入与图模式都没有板端证明。
