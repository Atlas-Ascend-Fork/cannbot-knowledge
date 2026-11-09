---
type: Runbook
title: 融合MoE重复相加：确认shared输出贡献归属
description: 可迁移机制：按返回值合同确定routed与shared的唯一合并出口；整批忽略chunk、dummy整行丢弃仅为本文MegaMoE接口条件。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.compute.quantization
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:38:52Z'
platforms:
- '950'
aliases:
- DeepSeek V4.1 MegaMoE 的 shared 贡献只计一次
---

# 融合MoE重复相加：确认shared输出贡献归属

## 适用性与框架边界

本卡先检查**分支贡献由谁计算、在哪里相加**。在具有 shared expert 的模型中，一条 shared 输出不能同时由融合后端和外层各加一次。

| 层次 | 读用范围 |
|---|---|
| 通用原则 | 为 routed、shared、路由权重应用和最终归并指定明确所有者；是否已含 shared 由返回值合同决定。 |
| 成立前提 | 模型确实有 shared 分支，且已确认所选后端的输出 schema；不能凭 fused/MoE/routed 等名字推断。 |
| recipes 专属 | 本文 AscendC MegaMoE Prefill 被调用方按“已含 shared”使用，入口整批提交并忽略 chunk；空 rank 采用 dummy，调用后丢弃整行输出。这些都不是所有后端要求。 |
| vLLM / 其他框架入口 | 检查 MoE prepare/dispatch、experts、finalize/归并和模型 shared 分支的贡献归属；TopK 权重可能在不同阶段应用，按实际路径核对。 |

本轮只核验参考调用方；既没有验收外部融合数值，也没有验证 vLLM 接入或兼容性。

## 适用场景

MoE 的 routed 分支按每个 token 的 TopK 选择专家，对各专家结果乘路由权重并合回；shared 分支则为每个真实 token 计算固定的共享前馈输出。正常层输出包含“routed 加权和 + shared”一次。本文 recipes 实例中的 MegaMoE 把专家分发、两次专家矩乘、SwiGLU 激活和合并交给同一融合后端；名字中的 MoE 不说明返回值是否含 shared，必须看调用合同。

下面的接口与容量条件限 recipes / CANN Executor 中 DeepSeek V4.1 主模型 AscendC MegaMoE 的 Prefill（一次处理已有上下文多 token）调用路径。Decode 逐步生成 token，使用其他入口。此路径要求 EP（专家并行）>1（专家分布到多个 rank，即通信进程）、TP（张量并行）=1（本路径不再切专家中间通道）、routed 量化为 w4a8mxfloat4；构造前兼容 w4a8float4 别名。还受分离部署模式与 is_mtp 开关约束，依赖 cann_ops_transformer 的融合算子、symmetric buffer 和通信组。symmetric buffer 是配套的跨 rank 融合通信暂存与初始化协议资源，不能用普通局部张量替代其合同。

路线为 recommended_fastpath 的调用方契约核查，粒度限此后端入口。目标平台 950 来自模型支持说明；本轮只有固定源码静态核验，未运行 CPU/NPU、编译、图、精度或性能测试。CANN 与外部融合包版本未知；DeepGEMM 权重转换和 exponent 打包由其他卡讨论。

## 现象

可迁移的症状是切后端后某分支贡献改变倍数，或拆分与融合的总输出不对应。本文实例中，若从非融合路径切到此 Prefill 后端，仍独立计算并相加 shared，就会重复计入共享分支。另一类入口错误是沿用分块容量估计：模型仍计算 Double Routing 的全局 chunk 数，但 MegaMoE 分支不接收该参数，而是整批提交。本轮未观测到实际重复输出、容量报错或通信故障；这些是静态合同给出的排查条件。

## 根因与判别方法

先把返回值分解为承诺包含的贡献，再检查每条贡献是否仅有一个合并出口。下表的权重布局、容量和 dummy 是 recipes MegaMoE 的具体合同，不能直接当作目标后端 schema。

| 符号或张量 | 轴、单位与来源 | 消费者或所有权 |
|---|---|---|
| x | [T,H]；本 rank 的真实 Prefill token 行 | Gate/TopK 与融合算子 |
| topk_ids / topk_weight | [T,K]；全局专家号 / 路由权重 | 融合算子的 routed 分发与合并 |
| l1/l2_weights | 每本地专家的 Gate/Up、Down 低精度权重 | 融合 routed 计算 |
| shared_l1/l2_weights | [1,2I,H] / [1,H,I]；shared 的逻辑输出/输入轴 | 同一次融合调用 |
| shared_l1/l2_weights_sf | [1,2I,H/64,2] / [1,H,I/64,2]；最后两轴为 MX scale 对布局 | 融合 shared 计算 |
| num_max_tokens_per_rank | 一次融合调用每 rank 的 token 容量上界 | symmetric buffer 分配与入口检查 |
| routed_output | [T,H]；调用方按“已含 shared”的融合输出使用 | 直接返回模型，不再相加 shared |
| dummy_x / ids / weight | 一行合成输入、专家号与零权重 | 空 rank 为 collective 参与；全部输出丢弃 |

低精度权重值与 scale 分开传；shared 权重在此合同中为 FP8，routed 为 packed FP4。uint8 scale 的 E8M0 适配是位模式 reinterpret，不是数值 cast，详见[已有 scale 接口卡](megamoe_mxfp8_scale_reinterpretation.md)。

教学推演（非上板观测）：设某 token 的 routed 加权和为 3、shared 为 2。普通拆分路径分别计算后相加得到 5；若融合返回值已是 5，模型再加 shared 会变成 7。变量名 routed_output 不改变返回值的合同。再设某个 EP rank 真实 T=0：它仍须按调用方约定参加一次 collective，但返回形状应为 [0,H]；dummy 的 shared 输出即使非零也不能成为真实 token 结果。这解释了“零路由权重”不能替代“丢弃整行输出”。

## 诊断路径

1. 在自己的框架找到 Gate/TopK、shared 前馈、融合专家入口和最终相加点。记录实际后端、Prefill/Decode 分支及其 schema：返回值承诺 routed-only 还是 routed+shared；不要凭函数名判断。
2. 建一张本次调用的贡献所有权表：routed 由谁算、shared 由谁算、哪个出口合并。若后端含 shared，模型侧只能消费完整输出；若后端不含 shared，才由外层合并。按真实 schema 决策，不能直接照搬本卡开关。
3. 记录 shared 权重/scale 的加载后 shape、转置、dtype、scale 块轴及传给融合算子的参数。若 layout guard 失败，先修布局适配；若通过却输出不符，用同一输入、权重和量化方案对照拆分路径，分别检查 routed、shared 和总和。
4. 记录每 rank 本次实际 T、融合调用次数、buffer 上界与真实切块位置，并查目标后端是否消费分块参数。仅在本文 recipes 实例中，MegaMoE 整批入口忽略 chunk 参数；修改 moe_chunk_max_len 不会缩小单次融合调用。超界应调整入口/容量配置并重新验收，不能仅调一个未被消费的分块参数。
5. 覆盖空 rank，并遵守所选后端的空输入协议；本文 recipes 实例要求它仍参与同一轮 collective，且 dummy 的全部输出被丢弃。零路由权重不会屏蔽 shared，因此不能只丢 routed 贡献。复验正常、空、容量边界及超界输入，先验输出归属与精度，再测性能；保留外部包版本和完整调用参数。

<details>
<summary>recipes / CANN Executor 完整实现对照（可选阅读）</summary>

## 快速检查

下列搜索仅用于已有 recipes 源码的可选对照；外部框架按上面的职责和输出所有权核验即可。

```bash
rg -n 'enable_mega_moe|shared_l1_weights|shared_l2_weights|def prefill|num_max_tokens_per_rank|routed_output' models/deepseek_v4_1/models/modeling_deepseek.py models/deepseek_v4_1/models/modules/op_impls/megamoe_backend.py
```

## 系统信息

以下是模型层和 MegaMoE 适配层的调用方代码，依赖 PyTorch、torch_npu、已初始化的 CommManager 及外部 cann_ops_transformer。外部融合实现不在本仓，不能从调用方推导其内部数值、通信正确性或性能。

## 机制代码

### 模型入口：DeepseekV41MoE.forward

输入隐藏状态、模式标志和可选 chunk 数；Gate/TopK 在融合算子外执行。Prefill 且 enable_mega_moe 时跳过独立 shared 并直接返回 backend.prefill；普通路径继续用 Double Routing。low_latency_tp 与 Decode 是不同分支。

```python
    def forward(self, hidden_states, is_prefill=False, cur_topk_list=None, input_ids=None, image_mask=None,
                shared_expert_stream=None, prefill_moe_global_chunks=None, engram_resource_events=None,
                moe_events=None):
        moe_events = moe_events or {}
        shared_expert_events = moe_events.get("shared_expert", [])
        _, h = hidden_states.shape
        shared_merged_x = None
        if self.low_latency_tp:
            hidden_states_share = None
            if self.n_shared_experts > 0:
                if self.enable_shared_pipeline and not is_prefill:
                    shared_merged_x = self.shared_expert_gate_up(
                        hidden_states, shared_expert_stream, shared_expert_events)
                else:
                    hidden_states_share = self.forward_shared_expert(
                        hidden_states, shared_expert_stream, shared_expert_events)
        elif is_prefill:
            # With MegaMoE the shared experts run inside the operator, so the
            # model-side computation must be skipped to avoid double counting.
            if self.n_shared_experts > 0 and not self.enable_mega_moe:
                hidden_states_share = self.forward_shared_expert(
                    hidden_states, shared_expert_stream, shared_expert_events)
            else:
                hidden_states_share = None
        else:
            record_stream(self.enable_multi_streams, hidden_states, shared_expert_stream)
            record_event(self.enable_multi_streams, shared_expert_events, 0)

        # compute gating score
        if self.platform_version == PlatformVersion.ASCEND_950:
            logits = torch_npu.npu_fused_matmul(hidden_states.view(-1, h), self.gate.weight, fused_op_type="16cast32")
        else:
            logits = self.gate(hidden_states.view(-1, h).to(torch.float32))
        topk_idx, topk_weight, _ = OpKernel.gate_topk(
            self, logits, input_ids, image_mask, is_prefill=is_prefill
        )
        if self.force_eplb:
            topk_idx = cur_topk_list
        topk_idx = topk_idx.to(torch.int32)

        if self.low_latency_tp:
            return self.moe_infer_tp(
                hidden_states, topk_idx, topk_weight, hidden_states_share,
                moe_events, engram_resource_events, shared_expert_stream, shared_merged_x)

        # MOE EP
        if is_prefill:
            if self.enable_mega_moe:
                return self.megamoe_backend.prefill(
                    self,
                    hidden_states,
                    topk_idx,
                    topk_weight,
                )
            return self.moe_infer_double_routing(
                hidden_states, topk_idx, topk_weight, hidden_states_share,
                shared_expert_events, prefill_moe_global_chunks)
        else:
            return self.moe_infer_dispatch_combine(
                hidden_states, topk_idx, topk_weight, shared_expert_stream,
                moe_events, engram_resource_events=engram_resource_events)
```

### 配置门禁

以下配置片段约束 EP、TP 和 routed 量化；它不是完整配置检查函数，也不能替代后面 shared 数量与布局检查。

```python
        if (custom_params.get("enable_mega_moe", False)
                and infer_config.disagg_config.disaggregation_mode in ("NONE", "PREFILL")):
            if parallel_config.moe_ep_size <= 1:
                raise ValueError(
                    f"enable_mega_moe=True with moe_ep_size={parallel_config.moe_ep_size} "
                    "is not supported yet."
                )
            if parallel_config.moe_tp_size != 1:
                raise ValueError(
                    f"enable_mega_moe=True with moe_tp_size={parallel_config.moe_tp_size} "
                    "is not supported yet."
                )
            quant_config = getattr(config, "quant_config", None)
            gmm_quant_mode = None if quant_config is None else quant_config.gmm_quant_mode
            # "w4a8float4" is accepted because update_gmm_quant_mode normalizes it
            # to "w4a8mxfloat4" during model construction (MegaMoE only runs there).
            if gmm_quant_mode not in ("w4a8mxfloat4", "w4a8float4"):
                raise ValueError(
                    f"enable_mega_moe=True with gmm_quant_mode={gmm_quant_mode} "
                    "is not supported yet."
                )
```

### 开关生效条件

enable_mega_moe 仅在指定分离部署模式且非 is_mtp 时生效。用户配置写了 True 不代表当前层最终走融合分支。

```python
        self.disagg_mode = self.infer_config.disagg_config.disaggregation_mode
        self.enable_mega_moe = (
            self.infer_config.model_config.custom_params.get("enable_mega_moe", False)
            and self.disagg_mode in ("NONE", "PREFILL")
            and not self.is_mtp
        )
```

### 后端绑定

模型初始化获取本 rank Prefill token 上界，创建上下文与适配器，再传给 MoE 层。通信组在此绑定，不是在每次 forward 临时选择。

```python
        self.megamoe_context = None
        self.megamoe_backend = None
        self.selected_op_kernels = {}
        if self.enable_mega_moe:
            self.update_op_kernel_dict(("megamoe",))
            self.megamoe_context, self.megamoe_backend = OpKernel.megamoe(
                config,
                get_max_local_prefill_tokens(self.infer_config, config.sliding_window),
                self.comm_manager,
                ep_group_name="dspark_megamoe_ep_group" if is_mtp else "megamoe_ep_group",
            )
            kwargs["megamoe_backend"] = self.megamoe_backend
```

### 容量计算：get_max_local_prefill_tokens

输入调度和上下文并行配置；输出单次本地 token 上界。CP（上下文并行）会分段和填充，因此不能直接把全局 token 预算当作每 rank 精确行数；实际行数仍须在入口记录。

```python
def get_max_local_prefill_tokens(infer_config: InferenceConfig, segment_min_len: int):
    """Upper bound on the prefill tokens one rank computes in a single step."""
    max_prefill_tokens = infer_config.scheduler_config.max_prefill_tokens
    cp_size = infer_config.parallel_config.cp_size
    if cp_size <= 1:
        return max_prefill_tokens
    # CP pads every request to 2 * cp_size segments and hands two of them to each rank.
    segments = 2 * cp_size
    segment_len = max((max_prefill_tokens + segments - 1) // segments, segment_min_len)
    extra_requests = infer_config.scheduler_config.cp_mini_batch - 1
    return 2 * segment_len + 2 * extra_requests * (segment_min_len + 1)
```

### 资源创建：MegaMoEContext.__init__

num_max_tokens_per_rank、专家数、TopK、H 与 I 共同用于外部 symmetric buffer 分配。函数先检查依赖、通信组和正容量，再保存算子入口与 buffer。这里的 sym_buffer 是跨 rank 融合通信资源，普通局部 tensor 分配不能替代。

```python
    def __init__(
        self,
        config,
        num_max_tokens_per_rank: int,
        comm_manager: CommManager,
        ep_group_name: str,
    ) -> None:
        try:
            from cann_ops_transformer.ops import get_symm_buffer_for_mega_moe, mega_moe
        except ImportError as exc:
            raise ImportError(
                "MegaMoE backend requires cann_ops_transformer.ops with "
                "get_symm_buffer_for_mega_moe and mega_moe."
            ) from exc

        if comm_manager is None:
            raise RuntimeError("MegaMoE backend requires an initialized CommManager.")
        if not comm_manager.has_group(ep_group_name):
            raise RuntimeError(
                f"MegaMoE backend requires communication group {ep_group_name!r}."
            )

        # Per-rank upper bound for one mega_moe call, which feeds the whole
        # local prefill batch in a single call (no chunking).
        if num_max_tokens_per_rank <= 0:
            raise ValueError(
                "enable_mega_moe=True requires a positive max_prefill_tokens, "
                f"got {num_max_tokens_per_rank}."
            )

        self.num_max_tokens_per_rank = num_max_tokens_per_rank
        self.group = comm_manager.get_group(ep_group_name)
        self.mega_moe = mega_moe
        self.sym_buffer = get_symm_buffer_for_mega_moe(
            self.group,
            num_experts=config.n_routed_experts,
            num_max_tokens_per_rank=num_max_tokens_per_rank,
            num_topk=config.num_experts_per_tok,
            hidden=config.hidden_size,
            intermediate_hidden=config.moe_intermediate_size,
            max_recv_token_num=0,
            dispatch_quant_mode=4,
            dispatch_quant_out_dtype=torch.float8_e4m3fn,
            combine_quant_mode=0,
            comm_alg="",
            topk_weights_type=0,
        )
```

### 整批调用：MegaMoEBackend.prefill

输入 [T,H] 和 TopK 信息，返回 [T,H]。关键分支如下；源注释提到 per-chunk，但实际此入口每次处理整个本地 Prefill batch。

| 条件 | 行为与输出 |
|---|---|
| buffer 不存在或 T 超上界 | 在调用前拒绝 |
| T=0 | 用预建 dummy 调一次 collective，再返回零行输出 |
| T>0 | 一次 _run_mega_moe，结果按已含 shared 直接返回 |

```python
    def prefill(
        self,
        moe,
        x: torch.Tensor,
        topk_ids: torch.Tensor,
        topk_weight: torch.Tensor,
    ) -> torch.Tensor:
        if self.sym_buffer is None:
            raise RuntimeError("MegaMoE backend requires an initialized sym_buffer.")

        num_tokens, hidden = x.shape
        if num_tokens > self.context.num_max_tokens_per_rank:
            raise RuntimeError(
                f"MegaMoE got {num_tokens} tokens on this rank, above the symmetric "
                f"buffer bound {self.context.num_max_tokens_per_rank}."
            )

        if num_tokens == 0:
            # mega_moe is a collective op and documents num_tokens >= 1, so an
            # empty prefill batch is padded with a 1-token dummy (ids = arange,
            # distinct experts) whose output is discarded. The call itself must
            # still happen to keep per-chunk collectives aligned across ranks.
            # Shared experts run inside the op on the dummy token as well.
            dummy_x, dummy_ids, dummy_weight = moe._megamoe_dummy_chunk
            self._run_mega_moe(moe, dummy_x, dummy_ids, dummy_weight)
            return x.new_empty(0, hidden)

        # mega_moe computes routed AND shared experts: the returned Y already
        # contains the shared-expert contribution, so no model-side add is
        # needed (the former independent-stream shared-expert path is removed).
        routed_output = self._run_mega_moe(moe, x, topk_ids, topk_weight)
        return routed_output.view(num_tokens, hidden)
```

### 空 rank 输入：build_dummy_chunk

dummy 的设备和 dtype 跟随加载后的 gate.weight；专家号取不同编号、路由权重为零。其目的仅是满足外部 collective 非空输入合同，不能把该行写入真实序列。

```python
    @staticmethod
    def build_dummy_chunk(moe) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        hidden = int(moe.hidden_dim)
        topk = int(moe.top_k)

        # dummy_x follows the gate weight device/dtype after weight loading.
        # topk ids/weights use the gate_topk/MegaMoE contract.
        # Empty chunks have no real gate output; synthetic ids/weights only
        # satisfy MegaMoE's collective input contract, and the dummy output
        # is discarded.
        dummy_x = moe.gate.weight.new_zeros((1, hidden))
        dummy_ids = torch.arange(
            topk, dtype=torch.int32, device=dummy_x.device
        ).unsqueeze(0)
        dummy_weight = torch.zeros(
            (1, topk), dtype=torch.float32, device=dummy_x.device
        )
        return dummy_x, dummy_ids, dummy_weight
```

### scale 视图：_reinterpret_scale_as_e8m0

输入 uint8 scale 时保持相同字节宽度，改成 E8M0 dtype 视图；已有其他 dtype 时原样返回。它没有验证源字节的数值编码。

```python
def _reinterpret_scale_as_e8m0(scale: torch.Tensor) -> torch.Tensor:
    """Reinterpret uint8-packed MX scales as float8_e8m0fnu (same byte width)."""
    if scale.dtype == torch.uint8:
        return scale.view(dtype=torch.float8_e8m0fnu)
    return scale
```

### shared 布局适配：build_shared_args

输入加载后的 shared 专家；仅允许一个 shared。Gate/Up 和 Down 的权重从模型 [in,out] 视图转回融合算子的 [out,in]，scale 同步交换输入块轴和输出轴，再增加专家轴。shape guard 检查的是这份实现选择的布局；输出四组列表交给 prepare_layer。

```python
    @staticmethod
    def build_shared_args(moe) -> tuple:
        """Build mega_moe shared-expert inputs from this layer's shared expert.

        Only n_shared_experts == 1 is supported (the sole guard lives here,
        not in check_model_config_before_loading). Model-side layout (950
        post-loading) serves npu_quant_matmul: the weight is a transposed
        [in, out] view with uint8 MX scales, while mega_moe expects:
            shared_l1_weights (1, 2*int_h, hidden)
            shared_l2_weights (1, hidden, int_h)
        Derived tensors are prepared once after weight loading.
        """
        n_shared = getattr(moe, "n_shared_experts", None) or 0
        if n_shared != 1:
            raise RuntimeError(
                "MegaMoE shared expert path only supports n_shared_experts=1"
            )
        shared = moe.shared_experts
        hidden = moe.hidden_dim
        int_h = moe.intermediate_size

        # Post-loading stores weights as transposed [in, out] views; verify the
        # expected layout, then transpose back to logical [out, in].
        w1 = shared.gate_up_proj.weight
        if tuple(w1.shape) != (hidden, 2 * int_h):
            raise RuntimeError(
                f"unexpected shared gate_up_proj layout: {tuple(w1.shape)}"
            )
        w1 = w1.transpose(-2, -1).reshape(1, 2 * int_h, hidden)

        w2 = shared.down_proj.weight
        if tuple(w2.shape) != (int_h, hidden):
            raise RuntimeError(
                f"unexpected shared down_proj layout: {tuple(w2.shape)}"
            )
        w2 = w2.transpose(-2, -1).reshape(1, hidden, int_h)

        # MX scales are stored as (in/64, out, 2) transposed views of the
        # logical (out, in/64, 2) layout.
        s1 = shared.gate_up_proj.weight_scale
        if tuple(s1.shape) != (hidden // 64, 2 * int_h, 2):
            raise RuntimeError(
                f"unexpected shared gate_up_proj scale layout: {tuple(s1.shape)}"
            )
        s1 = s1.transpose(0, 1).reshape(1, 2 * int_h, hidden // 64, 2)

        s2 = shared.down_proj.weight_scale
        if tuple(s2.shape) != (int_h // 64, hidden, 2):
            raise RuntimeError(
                f"unexpected shared down_proj scale layout: {tuple(s2.shape)}"
            )
        s2 = s2.transpose(0, 1).reshape(1, hidden, int_h // 64, 2)

        return (
            [w1],
            [w2],
            [_reinterpret_scale_as_e8m0(s1)],
            [_reinterpret_scale_as_e8m0(s2)],
        )
```

### 参数所有权：prepare_layer

将 routed 和 shared 的两层权重、scale、激活及 dtype 标记放入同一静态参数字典，并预建 dummy。shared_weight1/2_type 为 FP8，与 routed 的 FP4 标记不同。

```python
    def prepare_layer(self, moe) -> None:
        s_w1, s_w2, s_s1, s_s2 = self.build_shared_args(moe)
        moe._megamoe_dummy_chunk = self.build_dummy_chunk(moe)
        moe._megamoe_static_kwargs = {
            "l1_weights": [moe.experts.w13_weight],
            "l2_weights": [moe.experts.w2_weight],
            "weight1_type": torch_npu.float4_e2m1fn_x2,
            "weight2_type": torch_npu.float4_e2m1fn_x2,
            "l1_weights_sf": [
                _reinterpret_scale_as_e8m0(moe.experts.w13_weight_scale)
            ],
            "l2_weights_sf": [
                _reinterpret_scale_as_e8m0(moe.experts.w2_weight_scale)
            ],
            "activation": "swiglu",
            "activation_clamp": moe.swiglu_limit,
            "shared_l1_weights": s_w1,
            "shared_l2_weights": s_w2,
            "shared_l1_weights_sf": s_s1,
            "shared_l2_weights_sf": s_s2,
            "shared_weight1_type": torch.float8_e4m3fn,
            "shared_weight2_type": torch.float8_e4m3fn,
            "shared_expert_quant_out_dtype": torch.float8_e4m3fn,
        }
```

### 算子调用：_run_mega_moe

动态 x、TopK 与 sym_buffer 和上述静态参数合并，一起传入外部 mega_moe。调用方只取第一个返回值并按完整融合输出使用；本段没有额外 shared 相加。

```python
    def _run_mega_moe(
        self,
        moe,
        x: torch.Tensor,
        topk_ids: torch.Tensor,
        topk_weight: torch.Tensor,
    ) -> torch.Tensor:
        static_kwargs = moe._megamoe_static_kwargs
        mega_moe_kwargs = {
            "x": x,
            "topk_ids": topk_ids,
            "topk_weights": topk_weight,
            "sym_buffer": self.sym_buffer,
            **static_kwargs,
        }
        routed_output, _ = self.mega_moe(**mega_moe_kwargs)
        return routed_output
```

### 分块参数的生产者

下面函数仍为普通 MoE 计算全局 chunk 数；它的存在不证明每个后端消费该值。

```python
    def get_prefill_moe_global_chunks(self, hidden_states, is_prefill):
        if not is_prefill:
            return None
        moe_chunk_max_len = self.infer_config.model_config.custom_params.get("moe_chunk_max_len", 65536)
        moe_ep_group = None
        if self.moe_ep_size > 1:
            moe_ep_group = self.comm_manager.get_group("moe_ep_group")
        return get_moe_num_chunks(hidden_states, moe_chunk_max_len, moe_ep_group)
```

### 模型 forward 中的 chunk 变量

该片段创建 prefill_moe_global_chunks；对照前面的 MegaMoE 调用可见其没有被传入。

```python
        residual = None
        prefill_moe_global_chunks = self.get_prefill_moe_global_chunks(hidden_states, is_prefill)
        attn_metadata["oproj_max_tokens"] = self.get_prefill_oproj_max_tokens(hidden_states, is_prefill)
```

### 加载后准备入口

所有 DeepseekV41MoE 层加载后执行 prepare_layer。release_layer 是否存在及是否调用取决于后端和分离部署模式；本卡不把这段调用解释为已物理回收显存。

```python
        if self.megamoe_backend is not None:
            release_layer = (
                getattr(self.megamoe_backend, "release_layer", None)
                if self.disagg_mode == "PREFILL"
                else None
            )
            for module in self.modules():
                if isinstance(module, DeepseekV41MoE):
                    self.megamoe_backend.prepare_layer(module)
                    if release_layer is not None:
                        release_layer(module)
```

</details>

## 设计决策

以输出合同确定唯一合并出口，是可迁移决策。本文 recipes 融合路径把 shared 的计算和最终输出所有权交给同一个后端，所以模型跳过独立 shared。该实例的整批入口按整批 token 上界分配资源，空 rank 通过 dummy 保持 collective 参与；目标后端可有不同的切块与空输入协议。这三个合同分别约束数值计数、容量和通信调用，需一起核查。

## 验证信号

- [来源平台：950（仅源码目标，未上板）；证据等级：artifact_verified，静态源码] 模型在 MegaMoE Prefill 跳过独立 shared；prepare_layer 向同一次调用提供 shared 两层权重和 scale。
- [来源平台：950（仅源码目标，未上板）；证据等级：artifact_verified，静态源码] 正常输出直接返回，空输入调用 dummy 后返回空输出；MegaMoE Prefill 入口不接收 Double Routing 的 chunk 参数。

上述证据只支持调用方委派与返回值使用合同，尚未验证外部融合输出是否满足该合同。无 kernel、图、精度或性能通过信号；保持 draft，未生成 verified 事件。

## 部署验收

待执行：记录真实外部包版本和 schema，核验所有配置门禁与权重布局；用相同输入/量化对照拆分路径的 routed、shared 和总输出；覆盖空 rank、容量边界与超界拒绝。精度通过后单独测耗时和显存，不能据静态融合入口承诺收益。

## 坏实践

在融合输出上再次加 shared、凭 routed_output 名字判断内容、跳过空 rank collective、仅调未被消费的 chunk 参数来规避整批容量，都会违反当前入口合同。

## 失效边界

外部 mega_moe 的真实 schema、通信拓扑要求、数值与性能未随源码取得。AscendC 的 shared 数量限制在 build_shared_args 中检查；不是所有后端都有同一限制。Decode、其他平台、DSpark 通信域和 DeepGEMM 适配应分别核验，不能从本卡推导。
