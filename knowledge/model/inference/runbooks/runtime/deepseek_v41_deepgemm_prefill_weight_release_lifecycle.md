---
type: Runbook
title: recipes专用：预填充实例的原权重释放策略
description: recipes/CANN Executor专用：静态PREFILL实例在转换后释放原权重；PREFILL/NONE不是batch阶段，不能据此指导vLLM按当前prefill/decode释放参数。
tags:
- task.debugging
- topic.memory
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:38:52Z'
platforms:
- '950'
aliases:
- DeepSeek V4.1：DeepGEMM 预填充权重生命周期
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - cann_executor
---

# recipes专用：预填充实例的原权重释放策略

## 适用性与框架边界

本卡是 **recipes / CANN Executor 专用的权重释放策略**，适用于所列 DeepSeek V4.1 DeepGEMM 后端。**PREFILL/NONE 是 recipes 静态部署角色，不等于一次 batch 的动态 prefill/decode 阶段。不能指导 vLLM 按当前 batch 阶段释放原权重。**

| 层次 | 读用范围 |
|---|---|
| 可借鉴原则 | 转换后表示是否可用、原消费者是否仍需参数、对象引用与底层 storage 是否存活，是不同问题。 |
| 成立前提 | 本文 backend 已 prepare 成功；实例的后续用途确实符合静态角色，且普通 GMM/shared 消费者不再需要被清空的成员。 |
| recipes 专属 | disagg_mode、PREFILL/NONE、process_weights_after_loading 尾部与 release_layer 是此执行器的生命周期决策；不映射为其他框架的 batch 调度条件。 |
| vLLM / 其他框架入口 | 仅借鉴核对模型 loader、量化 post-load、experts 权重所有权、图/异步引用及所有后续消费者；不要照搬释放门禁或成员清空步骤。 |

本轮没有重入、恢复、显存或 vLLM 验收；成员置空和 destroy 调用都不证明物理 storage 已回收。

## 适用场景

MoE routed expert 按 TopK 处理 token：Dispatch 发给目标专家，GMM1 做 Gate/Up、SwiGLU 激活、GMM2 做 Down，Combine 加权合回；shared expert 为所有 token 贡献固定前馈结果。普通 GMM 直接读取模型层原权重与 scale。这里的 DeepGEMM 融合后端先把它们转换成外部 kernel 的专用元组，运行时读取元组和通信 buffer。两个消费者需要的是不同参数集合。

本卡专门诊断 recipes / CANN Executor 中 DeepSeek V4.1 的加载后准备与释放：process_weights_after_loading → prepare_layer/release_layer → 融合 Prefill 或普通 GMM。Prefill 一次处理上下文多 token，Decode 逐步生成；模型加载角色 PREFILL 表示专用于预填充的对象，和某次调用 is_prefill=True 不是一回事。NONE 角色的释放门禁不同。这些是静态部署角色，不能把 vLLM 当前一批 token 属于 prefill/decode 当作同一门禁。

范围限当前 routed W4A8 MXFP4 和已准备成功的对应后端；MegaMoE 要求 NONE/PREFILL、非 MTP、EP（专家并行）>1、TP（张量并行）=1。rank 为并行通信中的计算进程。路线为 recommended_fastpath 的生命周期诊断顺序，未验证内存收益。目标平台 950；本轮只有固定源码静态核验，未实际加载 checkpoint、运行 CPU/NPU、编译、图、精度或性能测试，CANN/torch_npu/deep_gemm 版本未知。

## 现象

已完成 PREFILL post-load 的同一对象若再次 prepare、切入非 Prefill forward，或只换后端开关回到普通 GMM，就可能请求已置空的原参数。另一个常见误判是看到 del、成员 None 或 empty_cache 就断言显存已经下降。本轮没有实际空指针、内存下降、回退成功或恢复成功观测，下面解释静态路径为何存在这些边界。

## 根因与判别方法

以下状态机与成员名专属于本文 recipes 策略。应先列出实例整个后续生命周期内的消费者，再判断某表示能否释放；仅观察当前 forward 走哪条分支不足以决定。

| 数据或状态 | 轴、来源与所有者 | 消费者 |
|---|---|---|
| 原 routed w13/w2 | 分配时 [E,2I,H/2] / [E,H,I/2] packed FP4；post-load 可改变物理格式；E为本rank专家数 | prepare 读取 .data；普通 GMM 读取并转置 |
| 原 routed scale | 对应 [E,输出通道,输入块]，post-load 形成 scale 二元尾轴 | prepare 与普通 GMM |
| 原 shared 参数 | Gate/Up、Down 权重与相应 scale，布局取决实际 scheme 与 post-load | shared prepare 与普通 shared Linear |
| _megamoe_static_kwargs | 两层转换后权重/scale 元组、可选 shared 元组与 clamp | DeepGEMM run |
| x、TopK、buffer | [T,H] token 隐藏状态、[T,K] 专家选择及其通信暂存 | 融合执行 |
| disagg_mode | 模型加载角色字符串；构造时保存 | post-load 的 release 门禁 |
| is_prefill | 本次 forward 布尔标志 | 路径选择，不负责恢复参数 |
| 原成员是否 None | Python 模块是否仍持有原参数引用 | 重入/回退前的必要检查，不能代表 storage 全部死亡 |

H 是隐藏通道，I 是专家中间通道。低精度值与 scale 一起定义矩乘输入，因此恢复一个 weight 名字而缺少 scale，同样不是完整原参数状态。

教学推演（非运行结果）：把“原参数可访问”记为 O，把“转换元组已准备”记为 F。

| 阶段 | O | F | 可由源码确定的动作 |
|---|---|---|---|
| 成功加载与通用 post-load 后 | 有 | 尚未由后端准备 | prepare 可从原成员读取 |
| prepare 成功后 | 有 | 有 | 两套成员并存；是否共享 storage 未知 |
| PREFILL 且有 release_layer 后 | 无（原成员置 None） | 有 | DeepGEMM run 仍读取 F |
| NONE 的同一 post-load 尾部 | 有 | 有 | 此门禁不调用 release |

假设第三行对象只把 is_prefill 改为 False：分支选择改变，但 O 仍为无。普通 apply 继续访问原成员，修改标志不会逆向重建它们。再次 prepare 仍需读取原 routed/shared 参数：有 shared 时先构造其参数并检查 shape，之后才读取 routed 参数的 .data。即使 F 与原权重数值等价，所列代码没有从 F 恢复 O 的逆变换；“参数可用性”和“数学等价”是不同问题。

所有权还要下钻一层：模块名→Tensor/Parameter 对象→底层 storage；转换元组可能复制或 alias，外部 buffer、图或异步任务也可能保留引用。成员置空只移除这一条引用；empty_cache 不能证明活跃 storage 已回收。Context.destroy 调用外部 buffer.destroy 后把自己的字段清空，也不能推出 backend 的同一 buffer 引用、层内转换元组与所有外部资源都已释放。

## 诊断路径

1. 在本文 recipes 实例找到静态加载角色配置、通用 post-load、融合 prepare、原权重 release 和所有 forward 分支。其他框架仅复用所有权核验思路，不按当前 batch 阶段设置本文角色或触发释放。分别记录角色、本次 is_prefill、实际后端；不要把其中一个字段当作另外两者。
2. 每层在加载、prepare 和 release 后记录原 weight/scale 是否存在、转换元组是否齐备、prepare 是否成功及本轮对象身份。预期先 prepare 成功，再只对不再需要原消费者的角色释放。若原成员已空，先停止选择依赖它们的分支，不在同一对象上盲目重跑 prepare。
3. 沿真实消费者查参数来源。融合 run 从静态元组读取；普通 GMM/Linear 从原层成员读取。若切后端后失败，先找第一个缺失成员，再查表示转换，避免把生命周期故障当作量化误差。
4. 需要回到原参数路径时，用完整 checkpoint 新建与角色/后端匹配的实例，完成通用 post-load 并验证输出；这是待执行恢复路线，本轮未验证成功。若另存原参数，须独立记录其数值、storage alias 和释放责任，不能假设转换元组可逆。
5. 若要判断显存，记录设备同步边界、各表示同时存在时的 allocated/reserved 与峰值、活跃引用/alias、旧图和异步任务状态；另记 context/backend/buffer 的销毁责任。先验数值和路径可用性，再报告实测内存变化。

<details>
<summary>recipes / CANN Executor 完整实现对照（可选阅读）</summary>

## 快速检查

下列搜索是 recipes 实现的可选导航。外部框架可按上述状态与消费者来源执行检查，不依赖同名类。

```bash
rg -n 'disagg_mode == "PREFILL"|prepare_layer\(module\)|release_layer\(module\)|def release_layer|weight = None|weight_scale = None|_megamoe_static_kwargs|self.moe_ffn = self.experts|self.moe_ffn\(\*\*gmm_args\)|layer.w13_weight.transpose' models/deepseek_v4_1/models/modeling_deepseek.py models/deepseek_v4_1/models/modules/op_impls/deepgemm_backend.py module/quantization/mxfp4.py
```

## 系统信息

机制位于模型 post-load 与分流、DeepGEMM 适配层、通用 FusedMoEGMM 及 MXFP4 apply。外部转换、allocator 与通信包的行为没有设备证据。pack、shared 构建、dummy、context 和注册的完整依赖闭环见[scale 配对卡](../precision/deepseek_v41_deepgemm_e8m0_pair_pack_contract.md)。

## 完整代码

以下保留原完整函数/因果块，未在本轮运行。阅读顺序是“角色与绑定→通用后处理→prepare/release/run→普通消费者”；重点对照每段从哪个成员读取、把结果交给谁，而不是只搜索 None。

### 融合开关

构造时保存 disagg_mode 并结合开关、模式和 is_mtp 决定是否启用。之后单独改字符串不能重做这些构造动作。

```python
        self.disagg_mode = self.infer_config.disagg_config.disaggregation_mode
        self.enable_mega_moe = (
            self.infer_config.model_config.custom_params.get("enable_mega_moe", False)
            and self.disagg_mode in ("NONE", "PREFILL")
            and not self.is_mtp
        )
```

### 后端绑定

创建 context/backend 并将 backend 传入 MoE 层；实际实现由选择器决定，不是所有 MegaMoE 后端都有 release_layer。

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

### 配置门禁

此片段限制 EP、TP 和 routed 量化，不能证明转换已成功，更不能证明原参数已可释放。

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

### 完整 process_weights_after_loading

长函数先逐模块转置/格式转换及准备静态资源，再进入后端尾部。请先定位三个锚点：

| 段落 | 关键变量 | 生命周期含义 |
|---|---|---|
| 模块遍历 | quant_method、is_transpose、is_weight_nz | 原参数变成消费者所需的加载后表示 |
| 固定资源准备 | full_attn_sink 等 | 其他模块的完整上下文，不是 MoE 已释放的信号 |
| 后端尾部 | release_layer、prepare_layer(module) | PREFILL 才取 release；每层严格先 prepare，再有条件 release |

NONE 不取 release；getattr 返回 None 的后端也不调用它。

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

### prepare_layer：保存转换结果

有 shared 时，函数先构造 shared 参数并读取/检查其 shape，之后才读取原 routed 成员的 .data；转换后保存静态字典。各中间量与所有权如下：

| 变量 | 来源与去向 |
|---|---|
| w13/w2、w13_sf/w2_sf | 原模块成员的数据引用 |
| *_nd、*_int8、*_sf_flat、*_sf_packed | 转换所需临时视图/张量；局部 del 只删除这些名字 |
| fused_w13/fused_w2 与 scale | 外部 transform 返回，存入 _megamoe_static_kwargs |
| shared_l1/l2 | 可选 shared 转换元组，同样保存供融合 run |

函数没有“已 prepare/release”重入守卫；调用前需保证原成员仍可访问。临时 del 不等于 release_layer，后者才修改模块原成员。

```python
    def prepare_layer(self, moe) -> None:
        n_shared = getattr(moe, "n_shared_experts", 0) or 0
        if n_shared > 0:
            shared_l1, shared_l2 = self.build_shared_args(moe)
        else:
            shared_l1, shared_l2 = None, None

        moe._megamoe_dummy_chunk = self.build_dummy_chunk(moe)

        experts = moe.experts
        w13 = experts.w13_weight.data
        w2 = experts.w2_weight.data
        w13_sf = experts.w13_weight_scale.data
        w2_sf = experts.w2_weight_scale.data

        w13_nd = torch_npu.npu_format_cast(w13.contiguous(), 2).view(torch.uint8).contiguous()
        w2_nd = torch_npu.npu_format_cast(w2.contiguous(), 2).view(torch.uint8).contiguous()
        w13_int8 = w13_nd.view(torch.int8)
        w2_int8 = w2_nd.view(torch.int8)

        w13_sf_flat = w13_sf.reshape(w13_sf.shape[0], w13_sf.shape[1], -1)
        w2_sf_flat = w2_sf.reshape(w2_sf.shape[0], w2_sf.shape[1], -1)
        w13_sf_packed = _pack_ue8m0_exponents(w13_sf_flat)
        w2_sf_packed = _pack_ue8m0_exponents(w2_sf_flat)

        (fused_w13, fused_w13_sf), (fused_w2, fused_w2_sf) = \
            self.deep_gemm.transform_weights_for_mega_moe(
                (w13_int8, w13_sf_packed), (w2_int8, w2_sf_packed))

        del w13_nd, w2_nd, w13_int8, w2_int8
        del w13_sf_flat, w2_sf_flat, w13_sf_packed, w2_sf_packed
        torch.npu.empty_cache()

        if shared_l1 is not None:
            shared_l1, shared_l2 = self.deep_gemm.transform_weights_for_mega_moe(
                shared_l1, shared_l2)

        moe._megamoe_static_kwargs = {
            "l1_weights": (fused_w13, fused_w13_sf),
            "l2_weights": (fused_w2, fused_w2_sf),
            "shared_l1_weights": shared_l1,
            "shared_l2_weights": shared_l2,
            "activation_clamp": moe.swiglu_limit,
        }
```

### release_layer：原成员置空

routed 四个 weight/scale 成员均置 None；有 shared 时也清空其两层 weight/scale。静态转换元组没有在这里清空。末尾 empty_cache 不证明这些表示之间没有 storage alias，也不证明底层物理回收。

```python
    def release_layer(self, moe) -> None:
        experts = moe.experts
        experts.w13_weight = None
        experts.w2_weight = None
        experts.w13_weight_scale = None
        experts.w2_weight_scale = None
        if getattr(moe, "n_shared_experts", 0) or 0:
            shared = moe.shared_experts
            shared.gate_up_proj.weight = None
            shared.gate_up_proj.weight_scale = None
            shared.down_proj.weight = None
            shared.down_proj.weight_scale = None
        torch.npu.empty_cache()
```

### _run_mega_moe：只消费转换元组

输入 x 与 TopK，动态量化后将值、scale、索引和权重写入同一有效 token 区间；从 _megamoe_static_kwargs 取融合权重，交外部算子写 y。它不从 None 的原成员重建参数，因而与普通 consumer 的前提不同。

```python
    def _run_mega_moe(
        self,
        moe,
        x: torch.Tensor,
        topk_ids: torch.Tensor,
        topk_weight: torch.Tensor,
    ) -> torch.Tensor:
        buffer = self.sym_buffer
        num_tokens = x.shape[0]
        hidden = x.shape[1]

        x_fp8, x_scale = torch_npu.npu_dynamic_mx_quant(
            x.contiguous(), dst_type=torch.float8_e4m3fn)
        x_scale_u8 = x_scale.view(torch.uint8)
        if x_scale_u8.dim() > 2:
            x_scale_u8 = x_scale_u8.flatten(1)
        x_sf_packed = _pack_ue8m0_exponents(x_scale_u8)

        buffer.x[:num_tokens].copy_(x_fp8)
        buffer.x_sf[:num_tokens].copy_(x_sf_packed)
        buffer.topk_idx[:num_tokens].copy_(topk_ids.to(torch.int64))
        buffer.topk_weights[:num_tokens].copy_(topk_weight)

        y = torch.empty((num_tokens, hidden), dtype=torch.bfloat16, device=x.device)

        kwargs = moe._megamoe_static_kwargs
        self.deep_gemm.fp8_fp4_mega_moe(
            y,
            kwargs["l1_weights"],
            kwargs["l2_weights"],
            buffer,
            shared_l1_weights=kwargs["shared_l1_weights"],
            shared_l2_weights=kwargs["shared_l2_weights"],
            activation='swiglu',
            activation_clamp=kwargs["activation_clamp"],
        )
        return y
```

### MoE.forward：本次调用如何分流

模型在外部计算 Gate/TopK；仅 Prefill 且 enable_mega_moe 时返回后端输出并跳过独立 shared。非 Prefill 进入 Dispatch/Combine，low_latency_tp 另有分支。这里没有原参数恢复步骤。

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

### 普通专家绑定

构造时 self.moe_ffn=self.experts；改变后端开关不会自动把该普通消费者变成转换元组消费者。

```python
        self.experts = FusedMoEGMM(
            num_experts=self.n_routed_experts,
            hidden_size=self.hidden_dim,
            intermediate_size=self.intermediate_size,
            bias=False,
            quant_config=config.quant_config,
            tp_size=self.moe_tp_size,
            tp_rank=self.comm_manager.get_rank("moe_tp_group") if self.moe_tp_size > 1 else 0,
            ep_size=self.moe_ep_size,
            ep_rank=self.comm_manager.get_rank("moe_ep_group") if self.moe_ep_size > 1 else 0,
            prefix=f"{prefix}.experts",
        )
        self.moe_ffn = self.experts
```

### 普通 Decode：moe_infer_dispatch_combine

Dispatch 产生展开行 expand_x、scale、专家计数与合并索引；self.moe_ffn 消费这些行并进入下面的 FusedMoEGMM.forward。之后 Combine 用 TopK 权重合回，再加 shared。所有这些步骤都没有从 F 重建原 weight/scale。engram ev[5] 在 FFN 前记录，是资源边界，不能作为原权重已无设备消费者的证明。

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

### FusedMoEGMM.forward

该层将 layer=self 交给当前 quant_method.apply；x、分组表与 scale 是动态输入，原权重仍由 apply 从 layer 成员取出。

```python
    def forward(self, x: torch.Tensor,
                expert_tokens: torch.Tensor,
                group_list_type: int = 0,
                pertoken_scale: torch.Tensor = None,
                final_output_dtype: torch.dtype = torch.bfloat16,
                **kwargs,
                ):
        if self.quant_method is None:
            raise RuntimeError("self.quant_method must not be None")

        # Matrix multiply.
        final_hidden_states = self.quant_method.apply(
            layer=self,
            x=x,
            expert_tokens=expert_tokens,
            group_list_type=group_list_type,
            pertoken_scale=pertoken_scale,
            final_output_dtype=final_output_dtype,
            **kwargs,
        )

        return final_hidden_states
```

### MXFP4 apply：原参数消费者

完整函数包括三段：GMM1 读取 w13_weight 与 scale，激活生成 intermediate_h 与新 scale，GMM2 读取 w2_weight 与 scale。SwiGLU 的具体分支不会改变两个原成员读取点；若成员已空，修改激活实现不能恢复它们。

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

</details>

## 设计决策

在本文 recipes 策略中，转换元组服务融合 consumer，原成员服务普通 consumer，释放门禁绑定静态加载角色。PREFILL/NONE 不表示调度器当前 batch 的阶段。不能把 PREFILL 的释放策略无条件搬到 NONE，也不能把“保留原参数”直接写成所有 Decode/图路径已通过。需要回退时应重建并验收完整实例；这一恢复路线尚未执行。

## 预防

将角色、调用模式、原成员状态和转换元组状态一起保存。任何释放、后端切换或 post-load 重入前，列出仍读取原参数的消费者及图/异步引用；角色改名不产生参数恢复。

## 验证信号

- [来源平台：950（仅源码目标，未上板）；证据等级：artifact_verified，静态源码] post-load 只在 PREFILL 取可选 release，逐层先 prepare 再 release；NONE 不走该门禁。
- [来源平台：950（仅源码目标，未上板）；证据等级：artifact_verified，静态源码] prepare 保存转换元组，release 清空 routed/shared 原成员，融合 run 读取静态元组。
- [来源平台：950（仅源码目标，未上板）；证据等级：artifact_verified，静态源码] 普通 forward→Dispatch/Combine→FusedMoEGMM→MXFP4 apply 仍直接读取原 weight/scale。

未实际执行再次 prepare、角色回退、销毁、图或显存对比；保持 draft，未生成 verified 事件。

## 部署验收

以下待执行验收限本文 recipes 策略：分别新建静态 PREFILL/NONE 实例，用同 checkpoint 检查每层成员状态及对应路径数值；业务若需切换，用重新加载实例验收通信、图与资源销毁。内存测量须覆盖转换时多份表示共存和所有引用/alias，区分成员清空、缓存回收与 storage 存活。

## 坏实践

把 empty_cache 当活跃 storage 已释放、将 release 扩大到所有角色、对已释放对象再次 prepare、只改 disagg_mode/is_prefill 就声称恢复普通 GMM，或让旧图/异步任务继续使用未经检查的权重，均缺少必要状态与同步证明。

## 失效边界

外部 transform 是否复制或 alias、buffer 各持有者与销毁同步、allocator 回收时点、峰值、post-load 重入和图生命周期均未验证。该 release_layer 只在所列后端存在；通用 getattr 门禁不说明其他后端行为。没有真实失败、恢复成功、NPU 编译、整网数值或性能结论。vLLM 与其他引擎的 batch 阶段、权重所有权和混合执行策略不能从此静态角色策略推导。
