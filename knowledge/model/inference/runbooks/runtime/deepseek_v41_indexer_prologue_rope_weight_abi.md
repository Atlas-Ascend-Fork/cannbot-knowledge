---
type: Runbook
title: 融合Indexer前处理：核对输入阶段与权重布局
description: 融合Indexer接口诊断：先确认输入所处阶段、RoPE与量化scale合同，再按实际后端匹配权重方向和物理格式；NZ仅适用于本文Ascend接口。
tags:
- task.implementation
- topic.attention
- topic.compute.quantization
- topic.data_movement.layout_transform
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:36:07Z'
platforms:
- '950'
aliases:
- DeepSeek V4.1 Indexer prologue布局联动
---

# 融合Indexer前处理：核对输入阶段与权重布局

## 适用性与框架边界

本卡是**接口条件知识**：融合边界改变后，输入处于投影前/后、RoPE 前/后或量化前/后的阶段必须与 consumer 一致；权重布局与调用入口要由同一个实际后端选择决定。仅在目标接口的输入阶段、dtype、scale 和格式要求精确匹配时，才能采用下文具体转换。

文中 Ascend Indexer prologue 的 output-major `FRACTAL_NZ`、MXFP8/MXFP4、E8M0 pair、二维 sin/cos、K norm FP32 与副作用写 cache 都是接口合同。recipes 的 `selected_op_kernels`、注册器与强制转换分支是参考实现；NZ 不是所有 Indexer、Linear 或 vLLM 的标准权重格式。

vLLM 或其他引擎可按 **Attention/Indexer 前处理、模型加载/量化方法、backend 权重后处理**三条职责核对实际选择与实参，ModelRunner 负责运行时输入衔接。无需找到 recipes 的 OpKernel 或同名配置；没有验证 vLLM 绑定本文融合算子。

## 现象

把投影、位置编码和量化融合后，数学作用相近仍可能因输入阶段、rank、权重方向或 scale 布局不符而失败。先沿运行路径确认实际 consumer 接收的语义阶段，再沿初始化路径确认权重已经转换到同一接口所需格式，两条链必须汇合。

本文接口实例的 Q/W 路径从当前特征产生量化查询与每头打分权重；K 路径从 pre-RoPE latent 生成量化 K 并直接写缓存。它们解释下文 ABI 轴表，不能作为其他后端的通用处理顺序。

## 适用场景

适用于检查融合边界与权重后处理是否一致；以下精确转换只覆盖本文 Ascend Indexer prologue 接口及 recipes kernel_config 适配，源码目标 950，CANN 版本与 NPU 验证未知。适用粒度 `same_operator`，路线优先级 `recommended_fastpath` 仅表示匹配算子包下当前优先选择的实现，保持静态诊断草稿。native 为框架组合运算路径，fused 为融合路径；缺少成对测量，不能把 native 称为已验证的性能 fallback。

## 根因与判别方法

先为自有融合入口列输入语义阶段、物理格式、输出角色和写入副作用；任一不符就按目标合同重新适配，不能只改函数名。以下匹配接口中，MXFP8/MXFP4 分别是分组共享 scale 的8位/4位浮点格式，E8M0 为单字节 scale 编码。Q/W 融合范围是：qr 动态量化成 MXFP8 → wq_b 投影 → Q 的部分 RoPE（旋转位置编码）→ Q 量化成 MXFP4，同时计算 weights_proj(x) 与缩放。K 则从尚未做 RoPE 的 latent 出发，执行 wk、归一化、RoPE 和缓存写入。若把已旋转的 Attention KV 当作 latent 输入 K 路径，会混淆生产者职责；此处应核对调用关系，不能只靠末维相同来代换。

| 符号/输入 | 轴与单位 | 本卡需核对的消费者契约 |
|---|---|---|
| T、E | packed token 行数、模型隐藏通道；x 展平为 `[T,E]` | weights_proj 生成每查询/每 Indexer 头的打分权重 |
| L / q_lora_rank | qr 的投影输入通道数，qr 为归一化后的 BF16 `[T,L]` | 动态 MXFP8 量化及 wq_b |
| Hi、Di | Indexer 头数、每头通道数 | Q 为每行 Hi 个 Di 维向量，量化后每字节打包两个 FP4 值 |
| P / scale_pair_dim | `ceil(L/64)`；每个 pair 含2个 E8M0 单字节 scale | qr scale 视为 `[T,P,2]`，wq_b scale 视为 `[Hi×Di,P,2]` |
| Dr / rope_head_dim | 做部分旋转的通道数 | 通用 sin/cos 为 `[T,1,1,Dr]`，融合入口接收 `[T,Dr]` |
| wk / wq_b / weights_proj | 分别投影 K、Q、头权重 | 对应融合核要求 output-major（按输出维组织）FRACTAL_NZ 分块存储，不能沿用普通 Linear 转置规则 |
| latent / cache_index | pre-RoPE 的 K 输入行、每行目标槽 | K prologue 无返回值，按写入模式更新指定缓存 |

**教学推演，非融合精度观测。** 假设有2行 qr、L=64，Indexer 有2个头且每头64通道。这里只推演 ABI 轴：qr 的 pair scale 是 `[2,1,2]`，wq_b 的 pair scale 是 `[128,1,2]`；相同的4字节输入 scale 不能按“每token一个 scalar”解释。若两行 RoPE 来自 `[2,1,1,Dr]`，展平为 `[2,Dr]` 不改变 token 对应关系，但沿错轴转置权重并不会被这个 reshape 修好。该例不声称这些输入满足任意版本后端的全部限制。

当前权重后处理把 K norm 权重转 FP32，并强制 Indexer wk 使用 output-major NZ；启用融合 Q/W 时 wq_b 和 weights_proj 也采用 NZ 且取消普通转置。NZ 是设备分块存储格式，Python shape 相同不意味着设备 format 相同。kernel 选择与这些转换必须在 warm-up（预热）和 graph capture（图捕获）之前一致完成。

## 快速检查

1. 在自己的引擎找到实际前处理 backend 与权重加载/量化后处理，记录**最终绑定结果**、输入阶段与要求的物理格式。先确认是否精确匹配本文接口；切换 consumer 后仍沿用不匹配的旧权重处理，支持初始化契约错配。
2. 对匹配本文 ABI 的 Q/W 接口，按上述表逐项记录 x、qr、scale、sin/cos 的 shape、dtype、numel 与物理 format。用真实 L 计算 pair 数，核对 wq_b 的输出维方向。numel 不符先查量化生产者；numel 相同仍须查 pair 的轴与编码。
3. 对匹配本文 ABI 的 K 接口，确认输入来自 Compressor 的 pre-RoPE latent、sin/cos 进入融合算子前为二维、norm 权重为 FP32，cache_index 与 latent 行一一对应。缓存布局的 split/combined 差异须另按对应写入契约检查。
4. 在目标环境核对加载后 wk/wq_b/weights_proj 的实际存储 format 和方向，再分别比较 native/fused 的 Q、Q-scale、头权重与最终 top-k。差异先出现在哪个中间量，就回到该生产阶段；近似并列候选还需单独分析，不能用最终索引相同代替所有数值检查。
5. K 是副作用写入，需比较目标 cache 的字节与未写槽，而不是等待一个返回 K。初始化和参数均符合仅排除 wrapper 级错误；外部融合后端、图回放与实际时延仍需独立验收。

## 完整代码

下列 recipes 完整实现用于核对本文证据。按块外导读比较输入、轴与生产消费关系；外部引擎应先完成上面的职责和接口检查。

<details>
<summary>recipes Ascend prologue 对照：完整 native/fused 入口和权重后处理</summary>

### native Q/W完整作用范围

native 方法依次生成头权重、Q、部分 RoPE 和 MXFP4 Q。返回三项的角色分别是 packed Q、Q scale、头权重；底层 Linear 的量化路径仍取决于模块配置，不能仅由这个 wrapper 判断逐位等价。

```python
@register_op_impl(op_type="indexer_prolog_qw")
def indexer_prolog_qw_native(module, x, qr, cos, sin):
    weights = module.weights_proj(x) * (
        module.softmax_scale * module.n_heads ** -0.5
    )
    q = module.wq_b(qr).view(-1, module.n_heads, module.head_dim)
    torch.ops.cann_ops_transformer.inplace_partial_rotary_mul(
        q.unsqueeze(2),
        cos,
        sin,
        rotary_mode="interleave",
        partial_slice=module.partial_slice,
    )
    q, q_scale = torch_npu.npu_dynamic_mx_quant(
        q, dst_type=torch_npu.float4_e2m1fn_x2
    )
    return q.view(torch.uint8), q_scale, weights
```

### 融合Q/W完整入口与scale pair

融合入口先把 qr 量化为 MXFP8，再按 L 计算 pair 轴，将输入和 wq_b scale 都重解释为 uint8 pair。最后把二维 sin/cos 与处理后的权重交给融合算子，整个作用范围须一起对照。

```python
@register_op_impl(op_type="indexer_prolog_qw", func_key="indexer_prolog_qw_ascendc")
def indexer_prolog_qw_ascendc(module, x, qr, cos, sin):
    qr, qr_scale = torch_npu.npu_dynamic_mx_quant(
        qr.view(-1, module.q_lora_rank),
        dst_type=torch.float8_e4m3fn,
    )
    qr = qr.view(torch.uint8)
    scale_pair_dim = (
        module.q_lora_rank + MXFP8_SCALE_PAIR_SIZE - 1
    ) // MXFP8_SCALE_PAIR_SIZE
    qr_scale = qr_scale.view(torch.uint8).view(
        qr.shape[0], scale_pair_dim, MXFP8_SCALE_PAIR_GROUPS,
    )
    wq_b_scale = module.wq_b.weight_scale.view(torch.uint8).view(
        module.n_heads * module.head_dim,
        scale_pair_dim,
        MXFP8_SCALE_PAIR_GROUPS,
    )
    return indexer_prologue_qw(
        x.view(-1, module.dim),
        qr,
        module.wq_b.weight.view(torch.uint8),
        module.weights_proj.weight,
        qr_scale,
        wq_b_scale,
        sin.view(-1, module.rope_head_dim),
        cos.view(-1, module.rope_head_dim),
        softmax_scale=module.softmax_scale * module.n_heads ** -0.5,
    )
```

### K融合入口：flat RoPE与cache写入参数

K 入口把 latent 与 sin/cos 展平到接口要求的二维形状，直接把 cache 与目标槽交给算子。storage_mode 决定分离或合并存储；函数不返回可供调用者再拼接的 K。

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

### 当前Indexer前向分派

Indexer 前向先等必要元数据，再运行已分派的 Q/W 实现；普通路径只有 owns_k 的 source 写 K，其余层读取共享缓存。CP（上下文并行）有单独前向，不应由普通路径推断其行为。

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

### 当前kernel选择与显式错误分支

kernel 选择先看显式配置，否则优先查已注册的当前平台 AscendC 实现，找不到才退回 native 名称；不存在的绑定会报 ValueError。后续权重转换必须读取这份实际选择。

```python
    def update_op_kernel_dict(self, op_types):
        """Bind requested implementations using kernel_config."""
        auto_import_modules(f"{__package__}.modules.op_impls")
        kernel_config = self.infer_config.model_config.custom_params.get("kernel_config", {})
        platform_version = self.infer_config.model_config.platform_version.value.lower()

        for op_type in op_types:
            if op_type in kernel_config:
                kernel_impl = kernel_config[op_type]
                used_kernel = f"{op_type}_{kernel_impl}_{platform_version}"
            else:
                default_kernel = f"{op_type}_ascendc_{platform_version}"
                used_kernel = (
                    default_kernel
                    if default_kernel in OpKernel.KERNEL_MAP
                    else f"{op_type}_native_{platform_version}"
                )
            if used_kernel not in OpKernel.KERNEL_MAP:
                raise ValueError(
                    f"Unsupported kernel implementation {used_kernel!r} for {op_type!r}."
                )
            OpKernel.op_impl_apply(op_type, used_kernel)
            self.selected_op_kernels[op_type] = used_kernel
            logger.info("%s use impl %s", op_type, used_kernel)
```

### 当前完整权重后处理：Indexer NZ/方向/Norm配套

按初始化顺序阅读这份长函数：

1. 从 `selected_op_kernels` 得到 use_indexer_prolog_qw，它同时决定 native 资源准备与融合权重处理条件。
2. 在 named_modules 循环中，Compressor norm 与 Indexer K norm 权重转 FP32；wo_a 的分组转置属于另一条投影链，不能照搬给 Indexer。
3. `is_indexer_prolog_qw_weight` 识别 wk，以及启用融合时的 wq_b/weights_proj，强制 NZ 并取消普通转置，再把这些参数交给 quant_method 后处理。
4. 函数随后还准备 MoE（混合专家）与固定 Attention 参数的通信资源；本卡只据前述分支核对 Indexer ABI。这些对 module 参数的修改必须在预热和图捕获之前完成，不返回一套可忽略的临时权重。

```python
    def process_weights_after_loading(self):
        """
        Do weight transpose, format cast to NZ, and scale dtype cast after loading weights.
        """
        float_scales_map = [
            "gate_up_proj",
            "q_b_proj",
            "wq_b",
        ]
        float_smooth_scales_map = [
            "down_proj"
        ]
        enable_weight_nz = self.infer_config.model_config.enable_weight_nz
        indexer_prolog_qw_kernel = getattr(self, "selected_op_kernels", {}).get(
            "indexer_prolog_qw", ""
        )
        use_indexer_prolog_qw = indexer_prolog_qw_kernel.startswith(
            "indexer_prolog_qw_ascendc_"
        )

        indexer_weights_stream = None
        for module_name, module in self.named_modules():
            # Create native Q/W resources after kernel selection, before graph capture.
            if (isinstance(module, Attention) and module.low_latency_tp and module.compress_ratio > 0
                    and not module.is_mla_rank and module.is_index_source and not use_indexer_prolog_qw):
                if indexer_weights_stream is None:
                    indexer_weights_stream = create_stream("separate_mla_weights")
                module.indexer_weights_stream = indexer_weights_stream
            if (isinstance(module, Indexer)
                    and self.low_latency_tp):
                module.use_fused_prolog_qw = use_indexer_prolog_qw
            if module_name.endswith("compressor.norm"):
                module.weight.data = module.weight.data.to(torch.float32)
            if module_name.endswith("attn.indexer.k_norm"):
                module.weight.data = module.weight.data.to(torch.float32)

            if module_name.startswith("vision_model.") and isinstance(module, nn.Linear):
                if enable_weight_nz:
                    module.weight.data = torch_npu.npu_format_cast(module.weight.data, 29)
                continue

            if "wo_a" in module_name:
                config = self.config
                head_dim_per_group = config.num_attention_heads * config.head_dim // config.o_groups
                module.weight.data = module.weight.data.view(-1, config.o_lora_rank, head_dim_per_group) \
                                                   .transpose(1, 2).contiguous()
                if config.quant_config.mm_quant_mode == "w8a8mxfloat8":
                    scale_data = reshape_mx_scale(module.weight_scale.data)
                    module.weight_scale.data = scale_data.view(-1, config.o_lora_rank, *scale_data.shape[1:]) \
                                                   .transpose(1, 2).contiguous()
                if enable_weight_nz:
                    module.weight.data = torch_npu.npu_format_cast(module.weight.data, 29)
                continue

            quant_method = getattr(module, "quant_method", None)
            scales_dtype = {}
            for scale_name in float_scales_map:
                if scale_name in module_name:
                    scales_dtype["scale_dtype"] = torch.float
                    break

            for smooth_scale_name in float_smooth_scales_map:
                if smooth_scale_name in module_name:
                    scales_dtype["smooth_scale_dtype"] = torch.float
                    break

            is_wq_b_transpose = self.config.num_attention_heads * self.config.head_dim > MATMUL_MAX_AXIS_VALUE
            is_c1a_compressor = (
                module_name.endswith(".compressor.wkv")
                and self.get_submodule(module_name.rsplit(".", 1)[0]).compress_ratio == 1
            )
            is_weight_nz = enable_weight_nz and not (
                ("compressor" in module_name and not is_c1a_compressor)
                or module_name.endswith(".ffn.gate")
                or (self.enable_mega_moe and ".shared_experts." in module_name)
                or (is_wq_b_transpose and "attn.wq_b" in module_name)
                or ("markov_w2" in module_name)
                or ("confidence_head" in module_name)
            )

            is_transpose = False if "compressor" in module_name else True

            # Indexer prologue kernels consume output-major weights in
            # FRACTAL_NZ.  The K prologue uses the same layout for wk.
            is_indexer_prolog_qw_weight = (
                module_name.endswith("attn.indexer.wk")
                or (
                    use_indexer_prolog_qw
                    and module_name.endswith(("attn.indexer.wq_b", "attn.indexer.weights_proj"))
                )
            )
            is_weight_nz = is_indexer_prolog_qw_weight or is_weight_nz

            is_transpose = is_transpose and not is_indexer_prolog_qw_weight
            if isinstance(quant_method, QuantizeMethodBase):
                quant_method.process_weights_after_loading(
                    module,
                    is_nz=is_weight_nz,
                    is_transpose=is_transpose,
                    scales_dtype=scales_dtype,
                )

            moe_quant_methods = (
                Fp8PerTileMoEGMMMethod,
            )
            if isinstance(quant_method, moe_quant_methods) and self.moe_ep_size > 1:
                all_experts_smooth_scale = module.smooth_scale_1.data.new_empty(
                    module.smooth_scale_1.data.shape[0] * self.moe_ep_size,
                    module.smooth_scale_1.data.shape[1],
                )
                dist.all_gather_into_tensor(
                    all_experts_smooth_scale,
                    module.smooth_scale_1.data,
                    group=self.comm_manager.get_group("moe_ep_group"),
                )
                module.smooth_scale_1.data = all_experts_smooth_scale

        # Fixed inference weights: gather once, before warm-up and graph capture.
        for module in self.modules():
            if (isinstance(module, Attention) and module.low_latency_tp and module.compress_ratio > 0
                    and module.is_mla_rank and module.attn_tp_size > 1):
                module.full_attn_sink = module.attn_sink.new_empty(module.n_heads)
                dist.all_gather_into_tensor(
                    module.full_attn_sink, module.attn_sink.detach().contiguous(),
                    group=self.comm_manager.get_group(module.attn_group_name),
                )

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

应让真实后端选择同时决定运行时入口与加载后的权重处理，而不是由两个独立配置猜测。在 recipes 中，选择kernel与权重布局后处理必须使用同一selected_op_kernels结果。不能只覆盖Python调用函数而继续按普通Linear转置权重，也不能根据全局enable_weight_nz=False就禁掉融合prologue的强制NZ要求。native与fused实现保留相同输出角色，但native实际调用的Linear内部量化路径由权重/quant_config决定，不能仅凭这两个wrapper声称数值逐位等价。

## 系统信息

recipes 实现依赖OpKernel registry、950 prologue算子、支持动态MX量化的torch_npu、以及按所选实现执行的权重后处理。Q/W输出为packed MXFP4 Q、其scale与每头打分权重。native Q/W包装函数本身没有显式保证打分权重返回FP32；QLI/QSLI调用处才将打分权重显式转为FP32。K入口的scale cache是否独立由storage_mode决定；普通split/combined cache写入单位与未验证的外部地址语义见[QLI与QSLI缓存消费单位](deepseek_v41_indexer_qli_qsli_cache_layout_contract.md)。

## 部署验收

待验：记录最终selected_op_kernels，检查wk/wq_b/weights_proj实际存储format和方向、Norm dtype及所有scale view的numel；对同一输入比较native/fused的Q、Q-scale、weights与最终top-k，单独检查近似并列分数和RoPE尾段。K侧用逐字节cache对照，覆盖padding slot与combined模式。本轮没有执行。

## 验证信号

本轮只读取固定 Git 源码并恢复原始 blob 与函数字节。以下是实现的静态核对结果，不是模型/NPU 执行结果；未运行源仓脚本、测试、编译或推理。

- 主线K prologue对sin/cos显式reshape为二维，Q/W融合显式构造MXFP8 pair scale。（来源平台：950源码目标，未上板；证据等级：artifact_verified；范围：源码）
- 当前kernel选择默认找已注册AscendC实现，找不到再选native；显式选择不存在的实现会走ValueError分支。（来源平台：950源码目标，未上板；证据等级：artifact_verified；范围：源码）
- 权重后处理在代码中针对Indexer强制output-major NZ，并把K norm转FP32。（来源平台：950源码目标，未上板；证据等级：artifact_verified；范围：源码）

## 预防

每次替换融合入口都同步审查参数的shape、dtype、layout、权重方向和初始化时机；把selected kernel结果纳入验收记录，避免以配置意图代替实际绑定结果。

## 坏实践

只替换函数名而保留旧权重转置；把四维RoPE tensor直接送给要求二维的入口；将scalar scale、BF16 scale和E8M0 pair混用；看到默认改成fused就宣称时延或精度已通过。

## 失效边界

外部prologue后端源码与部署二进制未在此素材中完整提供，当前只能核对wrapper与权重ABI。不同quant_config、非MXFP8权重、head_dim/q_lora_rank不满足后端约束、图捕获之后再换kernel以及低时延分卡路径都需要独立验收。没有native/fused成对成本，不将native写成已验证性能fallback。
