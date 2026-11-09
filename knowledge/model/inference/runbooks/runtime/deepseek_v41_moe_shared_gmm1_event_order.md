---
type: Runbook
title: recipes专用：shared分支与GMM1的事件排程
description: recipes/CANN Executor专用：核对low_latency_tp的shared分段流水、GMM1资源等待与Finalize数据依赖，非其他框架通用事件图。
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
- DeepSeek V4.1 shared Down 按 GMM1 事件排序
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - cann_executor
---

# recipes专用：shared分支与GMM1的事件排程

## 适用性与框架边界

本卡是 **recipes / CANN Executor 专用排程说明**，只适用于下列 DeepSeek V4.1 native stream 分支。具体事件、事件池和开关不能搬成 vLLM 的同步步骤。

| 层次 | 读用范围 |
|---|---|
| 可借鉴原则 | 跨流读取需等待真实生产完成，事件对象需与本轮提交对应；生命周期登记单独检查。 |
| 成立前提 | 本文 low_latency_tp、enable_multi_streams、shared A8 float8、routed MXFP4 与非 Prefill 条件同时成立；native 流/事件合同有效。 |
| recipes 专属 | shared_pipeline、moe_gmm1、shared_expert 事件图及 enable_shared_pipeline 是此执行器的资源排程。**GMM1→shared Down 是额外资源排序，shared Down 的数学计算不依赖 routed GMM1 的结果。** |
| vLLM / 其他框架入口 | 仅借鉴检查 experts/shared 分支/最终归并的真实读写依赖与异步流生命周期；不要据此为自己的 shared Down 增加同名或同位置等待。 |

本轮没有设备时间线、重入、图或 vLLM 运行验收；本文专用排程不证明其为所有引擎必要或最快方案。

## 适用场景

MoE 的 routed 分支先把每个 token 分给所选专家，再执行 GMM1（Gate/Up 分组矩乘）、SwiGLU 激活、GMM2（Down 分组矩乘）和反路由合并；shared 分支对同一批 token 做固定前馈。两者可以在不同 NPU stream 上提交，但最终合并一定要读到完整 shared 输出。stream 是有序任务队列，event 为其他队列建立等待边界；CPU 函数返回张量不等于 NPU 运算已经完成。

本卡专门覆盖 recipes / CANN Executor 中 DeepSeek V4.1 low_latency_tp 的 shared 流水：TP（张量并行）将专家中间通道切成各 rank（通信进程）的局部部分，Finalize 合并 routed/shared 部分和后统一 all_reduce。该流水要求 low_latency_tp、enable_multi_streams、shared A8 float8 和 routed W4A8MxFp4MoEGMMMethod 同时成立，并仅在非 Prefill 入口启用。Prefill 一次处理上下文多 token，Decode 每步生成 token；普通 shared 与 EP（专家并行）Decode 使用另一些等待点。

路线为 recommended_fastpath 的提交协议核查，粒度限当前 native stream 实现。目标平台为 950；本轮仅静态源码核验，未运行 CPU/NPU、编译、图、精度或性能测试，CANN 和 custom SwiGLU 包版本未知。

## 现象

如果主流在路由前等待完整 shared，会缩短可并行区间；如果删除最终等待，Finalize 又可能过早读取 shared。当前实现把 shared 的 GateUp、SwiGLU、Down 分段提交，并在串行 Decoder 层间复用 metadata 中的事件池。本轮没有实际竞态、图失败或加速观测，诊断目标是检查提交图是否表达了需要的边界。

## 根因与判别方法

shared Down 只在数学上依赖自己的激活结果和 Down 权重，routed GMM1 不为它生产输入。shared Down 等 routed GMM1 是 recipes 本实现选择的资源排序；Finalize 等 shared 完成则是输出的数据依赖。两者意义不同。另一个 Engram 资源事件 ev[5] 在路由之后、GMM 之前，不可代替本卡的 moe_gmm1[0]。

| 数据或事件 | 轴、单位或生产位置 | 消费者与约束 |
|---|---|---|
| hidden_states | [T,H]；主流产生的 token 隐藏向量 | routed 与 shared GateUp |
| shared_merged_x | [T,2I_r]；T为token行数，H为隐藏通道，I_r为本rank专家中间宽度；副流 GateUp 结果 | 副流 SwiGLU |
| shared_h / shared_scale | [T,I_r] 量化激活及其通道块 scale | 副流 Down |
| expert_output | [展开专家行数,H]；主流 GMM2 部分输出 | Finalize |
| hidden_states_share | [T,H]；副流 Down 部分输出 | 主流 Finalize |
| shared_expert[0] | 主流输入发布后 record | 副流 GateUp 前 wait |
| shared_pipeline[0] | 主流完成路由提交后 record | 副流 SwiGLU 前 wait |
| moe_gmm1[0] | 量化方法在 GMM1 调用后 record | 副流 Down 前 wait |
| shared_expert[1] | 副流 Down 后 record | 主流 Finalize 前 wait |

教学推演（非时间线实测）：设主流顺序为输入→路由→GMM1→激活→GMM2→Finalize，副流为 GateUp→SwiGLU→Down。即使 shared_h 已就绪，当前协议仍让 Down 排在 GMM1 事件之后；若将事件 record 移到 GMM1 之前，等待它就不再保证这一资源排序。反之，routed GMM2 先结束也不保证 shared Down 结束，所以 Finalize 仍须等待 shared_expert[1]。若把同一完成等待提前到路由前，数值依赖可能满足，但原计划的重叠窗口会被改变；是否影响性能须另测。

生命周期是第三个问题：event 管先后，record_stream 让 allocator 追踪张量在指定流上的使用；它既不提交完成事件，也不自动涵盖未登记的所有消费者。原代码有输入登记到 shared 流、shared 输出登记到主流的调用，但中间张量、捕获重放与重入仍要单独验收。

## 诊断路径

1. 在本文 recipes native 路径找到输入生产者、shared 三阶段、routed 两次矩乘和最终合并。记录各阶段实际 stream、张量身份、设备与有效行，确认 TP 部分和及 shared 只在最终出口消费一次。
2. 为每条跨流边记录“哪个阶段后 record、哪个阶段前 wait、事件对象和本轮 generation”。先查数据依赖，再查有意的资源排序；不能把相同数字编号当作同一语义事件。
3. 若 Finalize 早于 shared 就绪，追踪输出事件；若 Down 违反本文额外资源排程而过早进入，核对 GMM1 事件是否在正确算子后、wait 是否在当前副流生效。若只有输入偶发异常，检查 GateUp 前的输入就绪边和生命周期登记。
4. 核对事件池所属请求/forward。串行层可复用同一对象的协议不自动支持两个并发 forward；记录重录与等待对应关系，发现跨轮覆盖应先隔离资源或恢复已验收的串行调度。
5. 修正后用同输入权重与关闭多流的路径比较逐阶段和最终输出，再用设备时间线确认预期顺序。图 capture/replay、allocator reuse、多层重复执行与并发分别验收，不能用一张性能图替代精度与生命周期检查。

<details>
<summary>recipes / CANN Executor 完整实现对照（可选阅读）</summary>

## 快速检查

下列搜索为 recipes 实现的可选导航；没有该仓库时按上述阶段和 event 边检查自己的实现。

```bash
rg -n 'shared_pipeline|moe_gmm1|gmm1_events|shared_expert_events|enable_shared_pipeline' models/deepseek_v4_1/models/modeling_deepseek.py module/quantization/mxfp4.py models/deepseek_v4_1/models/modules/attention_data.py
```

## 系统信息

原样代码来自 metadata、模型、量化方法和流工具。依赖 PyTorch、torch_npu、通信组及外部 custom SwiGLU；TP 配置限 eager/npugraph_ex。GE 的流作用域与 native Event API 不是同一个完成协议。

## 机制代码

### 事件池创建

metadata 持有两个 stream 和四组事件；它们可跨串行 Decoder 层传递。此片段仅创建对象，没有证明每轮 wait 都绑定正确 record。

```python
        self.enable_multi_streams = self.infer_config.model_config.custom_params.get("enable_multi_streams", False)
        self.low_latency_tp = bool(
            self.infer_config.model_config.custom_params.get("low_latency_tp", False)
        )
        self.metadata_stream = torch.npu.Stream() if self.enable_multi_streams else None
        self.shared_expert_stream = torch.npu.Stream() if self.enable_multi_streams else None
        self.moe_events = {}
        if self.enable_multi_streams:
            self.moe_events = {
                "shared_expert": [torch.npu.Event() for _ in range(2)],
                "shared_expert_internal": [torch.npu.Event()],
                "shared_pipeline": [torch.npu.Event()],
                "moe_gmm1": [torch.npu.Event()],
            }
```

### 流水开关

此片段检查 TP、多流、shared 量化和 routed 量化方法；缺一条件时不能假定 shared 已被拆成三段。

```python
        shared = getattr(self, "shared_experts", None)
        self.enable_shared_pipeline = (
            self.low_latency_tp and self.enable_multi_streams and shared is not None
            and "float8" in shared.mm_quant_mode and "a8" in shared.mm_quant_mode
            and isinstance(self.experts.quant_method, W4A8MxFp4MoEGMMMethod)
        )
```

### metadata 发布

字典把同一资源对象交给层；不是逐层新建事件。

```python
        attn_metadata["shared_expert_stream"] = self.shared_expert_stream
        attn_metadata["metadata_stream"] = self.metadata_stream
        attn_metadata["moe_events"] = self.moe_events
        attn_metadata["attention_events"] = self.attention_events
```

### DecoderLayer.forward：资源如何到达 FFN

本函数先执行可选 Engram、注意力及归一化，再进入 ffn。hidden_states 是数据流，attn_metadata 里的 shared_expert_stream 与 moe_events 是同步资源流；它们在同一层入口汇合。

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

### shared GateUp：shared_expert_gate_up

输入 [T,H]；主流发布输入事件并登记跨流使用，副流等待后返回 Gate/Up 的融合张量 [T,2I_r]。该返回值还没有包含激活和 Down。

```python
    def shared_expert_gate_up(self, hidden_states, shared_expert_stream, shared_expert_events):
        """Start the shared gate/up projection while the main stream computes routing."""
        record_stream(True, hidden_states, shared_expert_stream)
        record_event(True, shared_expert_events, 0)
        with npu_stream_switch(True, shared_expert_stream):
            wait_event(True, shared_expert_events, 0)
            return self.shared_experts.gate_up_proj(hidden_states.view(-1, hidden_states.shape[-1]))
```

### TP 调度中心：moe_infer_tp

输入路由选择及可选 shared_merged_x；输出最终 TP 求和结果。按以下四段阅读长函数：

| 代码段 | 主要变量 | 负责的边界 |
|---|---|---|
| 路由与参数构造 | expanded_x、row_idx、expert_tokens | 生成 routed 行布局；Engram ev[5] 此时就记录 |
| shared 激活 | shared_h、shared_scale | 等 shared_pipeline，再提交副流激活 |
| routed FFN 与 shared Down | gmm1_events、hidden_states_share | GMM1 后的事件放行副流 Down |
| Finalize 与 all_reduce | output | 等 shared 完整结果，合并并求和 |

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

### shared 激活：swiglu_a8float8

输入 Gate/Up 两半，返回中间激活及可选 scale。函数按宽度与模式选融合量化或普通 SiLU×Up；fallback 返回 None scale，后续 Down 必须按这一返回合同调用，不能只盯 stream 忽略数据格式。

```python
    def swiglu_a8float8(self, merged_x):
        swiglu_limit_args = {}
        if self.swiglu_limit is not None:
            swiglu_limit_args["clamp_limit"] = self.swiglu_limit
        if self.low_latency_tp:
            d_limit = 64 if "mx" in self.mm_quant_mode else 256
            if merged_x.shape[-1] % d_limit == 0:
                intermediate_hidden_states, pergroup_scale, _ = torch.ops.custom.npu_swiglu_group_quant(
                    merged_x,
                    dst_type=torch.float8_e4m3fn,
                    round_scale=True if "mx" in self.mm_quant_mode else False,
                    quant_mode=1 if "mx" in self.mm_quant_mode else 0,
                    clamp_limit=self.swiglu_limit,
                    )
                return intermediate_hidden_states, pergroup_scale
        elif merged_x.shape[-1] % 256 == 0:
            intermediate_hidden_states, pergroup_scale, _ = torch.ops.cann_ops_nn.swiglu_group_quant(
                merged_x,
                dst_type=torch.float8_e4m3fn,
                round_scale=True if "mx" in self.mm_quant_mode else False,
                quant_mode=1 if "mx" in self.mm_quant_mode else 0,
                **swiglu_limit_args,
                )
            return intermediate_hidden_states, pergroup_scale
        # Fused kernels reject this width: clamp before silu, matching the
        # fused kernel's A=Min(A,limit), B=Clamp(B,+-limit) semantics.
        gate, up = merged_x.chunk(2, dim=-1)
        if self.swiglu_limit is not None:
            gate = gate.clamp(max=self.swiglu_limit)
            up = up.clamp(min=-self.swiglu_limit, max=self.swiglu_limit)
        intermediate_hidden_states = F.silu(gate) * up
        return intermediate_hidden_states, None
```

### routed GMM1 事件生产者：W4A8MxFp4MoEGMMMethod.apply

输入专家排序后的 x、分组表和 scale；输出 Down 结果。首次 grouped_matmul 产生 mm1_mm3，紧接着提交 gmm1_events record，再做激活和第二次 GMM。这里 record 在同一 stream 上排序于 GMM1 后；源码位置不代表主机已等待设备完成。

```python
    def apply(
        self,
        layer: torch.nn.Module,
        x: torch.Tensor,
        expert_tokens: torch.Tensor,
        group_list_type: int,
        pertoken_scale: torch.Tensor = None,
        final_output_dtype: torch.dtype = torch.bfloat16,
        **kwargs
    ):
        # Keep the torch_npu operator argument name. pertoken_scale does not
        # mean one scale for a whole token; the token dimension is indexed
        # independently, and each token stores MX scales per BLOCK_K hidden values.
        if pertoken_scale is None:
            x, pertoken_scale = torch_npu.npu_dynamic_mx_quant(x, dst_type=torch.float8_e4m3fn)
        num_tokens = x.shape[0]
        mm1_mm3 = torch_npu.npu_grouped_matmul(
            [x], [layer.w13_weight.transpose(1, 2)],
            antiquant_scale=[layer.w13_weight_scale.transpose(1, 2)],
            per_token_scale=[pertoken_scale],
            group_list=expert_tokens, split_item=3,
            output_dtype=torch.bfloat16, group_type=0,
            weight_dtype = torch_npu.float4_e2m1fn_x2,
            per_token_scale_dtype=torch_npu.float8_e8m0fnu,
            group_list_type=group_list_type,
            tuning_config=[0]
        )[0]

        record_event(layer.gmm1_events is not None, layer.gmm1_events, 0)
        swiglu_limit = kwargs.get("swiglu_limit", None)
        enable_cann_ops_nn = kwargs.get("enable_cann_ops_nn", False)
        if enable_cann_ops_nn and kwargs.get("low_latency_tp", False):
            # Low-latency TP path: repo custom op (separately deployed package).
            import custom_ops
            group_quant_kwargs = {}
            if swiglu_limit is not None:
                group_quant_kwargs["clamp_limit"] = swiglu_limit
            swiglu_expert_tokens = kwargs.get("swiglu_expert_tokens")
            glt = 2 if swiglu_expert_tokens is not None else 1
            swiglu_group_index = swiglu_expert_tokens if swiglu_expert_tokens is not None else expert_tokens
            group_quant_kwargs["group_index"] = swiglu_group_index
            group_quant_kwargs["dst_type"] = torch.float8_e4m3fn
            group_quant_kwargs["quant_mode"] = 1
            group_quant_kwargs["block_size"] = 32
            group_quant_kwargs["round_scale"] = True
            group_quant_kwargs["output_origin"] = False
            group_quant_kwargs["group_list_type"] = glt
            intermediate_h, pertoken_scale, _ = torch.ops.custom.npu_swiglu_group_quant(mm1_mm3, **group_quant_kwargs)
        elif enable_cann_ops_nn:
            intermediate_h, pertoken_scale, _ = torch.ops.cann_ops_nn.swiglu_group_quant(
                mm1_mm3,
                dst_type=torch.float8_e4m3fn,
                round_scale=True,
                quant_mode=1,
                clamp_limit=_get_swiglu_clamp_limit(swiglu_limit),
                group_index=expert_tokens)
        else:
            intermediate_h, pertoken_scale = torch_npu.npu_swiglu_mx_quant(
                                                mm1_mm3,
                                                group_index=expert_tokens,
                                                dst_type=torch_npu.float8_e4m3fn,
                                                activate_left=True,
                                            )
        out_hidden = torch_npu.npu_grouped_matmul(
            [intermediate_h],
            [layer.w2_weight.transpose(1, 2)], bias=None,
            antiquant_scale=[layer.w2_weight_scale.transpose(1, 2)],
            per_token_scale=[pertoken_scale],
            group_list=expert_tokens, split_item=3,
            output_dtype=final_output_dtype, group_type=0,
            weight_dtype = torch_npu.float4_e2m1fn_x2,
            per_token_scale_dtype=torch_npu.float8_e8m0fnu,
            group_list_type=group_list_type,
            tuning_config=[0]
        )[0]

        return out_hidden
```

### 普通完整 shared：forward_shared_expert

该入口一次提交 shared 的完整前馈，并发布 shared_expert[1]，不使用 TP 三段流水。输入与输出分别登记到其跨流使用方。

```python
    def forward_shared_expert(self, hidden_states, shared_expert_stream, shared_expert_events):
        main_stream = torch.npu.current_stream() if self.enable_multi_streams else None
        record_stream(self.enable_multi_streams, hidden_states, shared_expert_stream)
        record_event(self.enable_multi_streams, shared_expert_events, 0)
        with npu_stream_switch(self.enable_multi_streams, shared_expert_stream):
            wait_event(self.enable_multi_streams, shared_expert_events, 0)
            # shared_expert use multi streams
            hidden_states_share = self.shared_experts(hidden_states.view(-1, hidden_states.shape[-1]))
            record_event(self.enable_multi_streams, shared_expert_events, 1)
            record_stream(self.enable_multi_streams, hidden_states_share, main_stream)
        return hidden_states_share
```

### EP Decode：moe_infer_dispatch_combine

EP 把 token 发给拥有目标专家的 rank。此函数的 expand_x、expert_token_num 与接收计数由 Dispatch 产生；routed FFN 后发布 shared_expert_internal[0]。shared 在自己的 forward 内等该事件再做 Down；主流 Combine 结束后仍等 shared_expert[1] 才相加。它与 TP 的 GMM1 边界不同。

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

### EP shared 内部等待：forward_a8float8

先做 GateUp 与激活，再按 enable_decode_stream 等内部事件，最后调用 Down。pergroup_scale 决定 Down 的参数形式。

```python
    def forward_a8float8(self, x, enable_decode_stream=False, shared_expert_event=None):
        merged_x = self.gate_up_proj(x)
        intermediate_hidden_states, pergroup_scale = self.swiglu_a8float8(merged_x)
        wait_event(enable_decode_stream, shared_expert_event, 0)
        if pergroup_scale is None:
            return self.down_proj(intermediate_hidden_states)
        return self.down_proj(intermediate_hidden_states, pergroup_scale)
```

### record_event

按当前流提交事件。是否调用 native API 取决于模式开关。

```python
def record_event(switch_flag: bool, events: tuple, idx: int, exe_mode: Optional[str] = None):
    """Records the specified NPU event if switch_flag is True."""
    if use_native_stream_api(switch_flag, exe_mode):
        events[idx].record()
```

### wait_event

等待作用于当前流，源注释明确不支持显式 stream 参数；必须确认调用所在的流作用域。

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

### record_stream

登记指定张量在指定流的生命周期使用，不建立生产完成依赖。

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

### npu_stream_switch

关闭时返回空上下文；GE 与 native stream 走不同分支。仅进入流作用域不等于数据已就绪。

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

### MoE.forward：选择何种 shared 入口

本函数在 low_latency_tp、Prefill 与 EP Decode 之间选路；只有 enable_shared_pipeline 且非 Prefill 时返回 shared_merged_x 进入 TP 分段调度。Gate/TopK 仍在主路径产生，后续分别转入 TP、融合 Prefill 或 EP Dispatch/Combine。

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

### native API 条件

GE 模式不执行本组 native Event 与 record_stream 包装。

```python
def use_native_stream_api(switch_flag: bool, exe_mode: Optional[str] = None):
    return switch_flag and exe_mode != "ge_graph"
```

### 关闭多流时的上下文

该对象没有额外同步动作。

```python
class FakeContextManager:
    def __init__(self) -> None:
        pass

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        pass
```

### low_latency_tp 配置门禁

此配置片段限制执行模式与并行布局，并要求各 TP rank 路由一致；不能只修改流工具分支就宣称 GE 已支持。

```python
        low_latency_tp = bool(custom_params.get("low_latency_tp", False))
        if low_latency_tp:
            if parallel_config.world_size % 2:
                raise ValueError("low_latency_tp requires an even world_size for MLA/LI rank pairs")
            if exe_mode not in ("eager", "npugraph_ex"):
                raise ValueError("low_latency_tp uses native streams; select eager or npugraph_ex")
            if parallel_config.attn_tp_size <= 1:
                raise ValueError("low_latency_tp requires attn_tp_size > 1")
            if parallel_config.attn_tp_size != parallel_config.world_size:
                raise ValueError("low_latency_tp requires attn_tp_size == world_size")
            # Low-latency TP keeps one identical token layout through the model.
            for tp_name in (
                "moe_tp_size", "o_proj_tp_size", "lmhead_tp_size",
                "embed_tp_size", "dense_tp_size", "shared_tp_size",
            ):
                setattr(parallel_config, tp_name, parallel_config.world_size)
            parallel_config.attn_dp_size = 1
            parallel_config.embed_dp_size = 1
            parallel_config.moe_ep_size = 1
            if config.num_attention_heads % parallel_config.attn_tp_size != 0:
                raise ValueError("num_attention_heads must be divisible by attn_tp_size")
            if config.o_groups % parallel_config.attn_tp_size != 0:
                raise ValueError("o_groups must be divisible by attn_tp_size")
            if config.moe_intermediate_size % parallel_config.moe_tp_size != 0:
                raise ValueError("moe_intermediate_size must be divisible by moe_tp_size")
            if model_config.force_eplb:
                raise ValueError("Basic MoE TP requires force_eplb=False for identical routing on all ranks")
```

</details>

## 设计决策

recipes 把数据完成等待放在真实消费点以保留可能的重叠，同时用 GMM1 边界控制共享资源提交次序。后者服务这份排程，不应当作 shared 专家数学依赖。事件池复用以串行层链为前提，数据可见性与生命周期必须各自成立。本卡没有设备证据量化任何重叠收益。

## 验证信号

- [来源平台：950（仅源码目标，未上板）；证据等级：artifact_verified，静态源码] metadata 创建并传递事件池；TP 激活与 Down 分别等 shared_pipeline 和 moe_gmm1。
- [来源平台：950（仅源码目标，未上板）；证据等级：artifact_verified，静态源码] routed 量化方法在第一次 GMM 后 record；主流 Finalize 前等 shared_expert[1]。

固定源码核验只证明提交协议，未验证竞态消除、并发重入或图重放。保持 draft，未生成 verified 事件。

## 部署验收

待执行：保存主副流设备时间线及每个事件的本轮身份；与关闭多流路径对照输出；覆盖多层串行重录、不同 batch、allocator reuse 和 capture/replay。并发 forward 用独立实验检查资源隔离。

## 坏实践

用 record_stream 代替 wait、在多个并发 forward 间无隔离重录同一事件池，或把 GMM1 完成边界移到 GMM1 前，均不满足本文 recipes 选择的协议。其他引擎是否需要这条资源边，应由自身排程和测量决定。stream 存在本身也不保证输入就绪。

## 失效边界

GE 的 native record/wait 不执行；本 TP 路径配置仅允许 eager/npugraph_ex。外部算子支持版本、实际重叠和性能未知；事件池的并发重入安全尚未验证。
