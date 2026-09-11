---
type: Concept
title: VLM 多模态训练适配（DenseMaskSDPA）
description: torchtitan-npu VLM/多模态训练适配（debug 模型 vlm_debugmodel_npu，无真权重/fake_backend）：适配上游 Llama3Siglip2Transformer，仅 FSDP/HSDP 数据并行（无 TP/CP/PP/EP）。npu_vlm converter 核心：用 DenseMaskSDPA（torchtitan_npu.models.multimodal）替换上游 FlexAttention，在 LLM inner_attention 与 SigLIP2 视觉编码器 Attention 两处生效。multimodal helper：build_text_document_causal_mask/build_encoder_causal_mask/build_valid_patch_mask/scatter_visual_embeddings（按 img_id 位置并入视觉嵌入）。VisionTransformerNpu 子类化 siglip2（零填充双线性位置编码 resize）。新多模态模型应复用 multimodal helper。 MindSpeed-MM 侧补 VLM 训练：Qwen3-VL-30B-A3B MoE 经插件式 FSDP2 后端迁移（HF 接入 + forward 内 CP 切分聚合/MoE aux loss + fsdp_plan.apply_modules 分片 + freeze visual + meta init/hf_to_dcp DCP + npu_patch 融合算子）、VLM loss 三口径（default/per_sample_loss/per_token_loss，对应 fixed_cross_entropy 的 alpha 与 reduction，修 micro_bs×grad_acc 的 global-batch 一致性）、多模态数据接入（ShareGPT messages/images + Qwen3VLPlugin 产 pixel_values/image_grid_thw）。
tags:
- task.design
- topic.model_architecture
- topic.multimodal
status: stable
sources:
- resource: https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/README.md
  role: primary
- resource: https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/feature_guides/vlm.md
  role: supporting
created_at: '2026-06-23T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# VLM 多模态训练适配（DenseMaskSDPA）

`torchtitan_npu.models.vlm` 把上游 `torchtitan.experiments.vlm` 的 `Llama3Siglip2Transformer`（SigLIP2 视觉编码器 + Llama3 解码器的 VLM **debug model**）适配到 NPU。这是一个**调试模型**（无真实权重，2 步 `fake_backend` 跑通），目的不是落地某个具体 VLM，而是固化一套 **VLM/多模态训练的 NPU 适配模式**：用 `DenseMaskSDPA` 替换上游 `FlexAttention`、用 dense-mask / scatter helper 处理图文混排、并约束为 FSDP/HSDP 纯数据并行。核心机制在 `torchtitan_npu/models/vlm/` 与 `models/multimodal/` 中。

## 模型入口与注册

`model_registry("debugmodel")` 取上游 `llama3_siglip2_configs["debugmodel"]()`，经 `to_npu_vlm_config` 转换后封装为 `ModelSpec(name="vlm", parallelize_fn=parallelize_vlm_npu, build_loss_fn=build_cross_entropy_loss, pipelining_fn=None)`。配置入口由 `config_registry.py` 暴露两个 CONFIG：

- `vlm_debugmodel_npu` —— `MultiModalTrainerConfig`，tokenizer 资产 `./tests/assets/tokenizer/vlm_tokenizer`，数据集 `cc12m-test`，`local_batch_size=1 / seq_len=256 / steps=2`，AdamW `lr=8e-4`，converter `npu_vlm`。
- `vlm_debugmodel_npu_compile` —— `replace(vlm_debugmodel_npu(), compile=CompileConfig(enable=True))`。

## 核心适配：FlexAttention → DenseMaskSDPA

上游在 LLM 解码层与 SigLIP2 视觉编码层都用 `FlexAttention`。NPU 改用 `DenseMaskSDPA`（继承 `LocalMapInnerAttention`，`models/multimodal/attention.py`）：接收**稠密布尔掩码**（PyTorch SDPA 语义，`True=可注意`），把 TorchTitan 的 `(B,S,H,D)` 转置为 `(B,H,S,D)` 后调 `F.scaled_dot_product_attention`，再转回。`DenseMaskSDPA.Config` 故意继承 `FlexAttention.Config` —— 因为 Trainer 只对 Flex/Varlen 配置类型调用 `model.get_attention_masks`，靠这一继承做派发，运行时模块仍是 `DenseMaskSDPA`。

替换在 config 转换期完成，不在运行期 rewrite：

- `to_npu_vlm_config`（`vlm/model.py`）逐层把解码 `attention.inner_attention` 设为 `DenseMaskSDPA.Config()`，并把 `encoder` 换为 NPU 视觉塔配置。
- `to_npu_vision_attention_config`（`vlm/siglip2.py`）对 SigLIP2 `Attention.inner_attention` 注入 `DenseMaskSDPA.Config()`。

因此 `vlm` 被列入 `entry.py` 的 `_SKIP_FLEX_TO_SDPA_REWRITE_MODELS` —— 它在自己的 config 路径里完成 Flex→Dense 替换并需要模型专属的稠密掩码，跳过 entry 通用的 Flex→SDPA + `mask_type="causal"` 重写。`npu_vlm` converter（见下）做事后校验：断言**解码层与编码层**的 `inner_attention` 都是 `DenseMaskSDPA`，否则报错。

## multimodal 稠密掩码 / scatter helper

通用 helper 集中在 `torchtitan_npu.models.multimodal`，新增多模态模型应复用而非在模型目录内重复实现。`Llama3Siglip2TransformerNpu.get_attention_masks`（`vlm/model.py`）要求 `extra_inputs["grid_thw"]` 与 `tokenizer.eos_id`，产出三类掩码：

| Helper（`models/multimodal/masks.py`） | 作用 |
|---|---|
| `build_text_document_causal_mask(tokens, eos_id)` | LLM 侧因果掩码 + 按 EOS 切分的文档间不可跨注意（`build_document_ids` 用 `eos.cumsum`） |
| `build_valid_patch_mask(grid_hw)` | 接收已切片的 `(B,S,2)` `grid_hw`（切片 `grid_thw[:, :, 1:]` 由 `get_attention_masks` 内的 `_grid_hw_from_grid_thw` 完成），用 `(grid_hw != PADDED_PATCH_COORDINATE).all(dim=-1)` 标记两坐标均非 padding 的图像 patch（padding 坐标 `PADDED_PATCH_COORDINATE = -1`） |
| `build_encoder_causal_mask(valid_patches)` | SigLIP2 编码器掩码，仅在有效 patch 上做因果注意；`allow_padding_self_attention=True` 给全 mask 行加自注意对角线，规避 dense SDPA 整行被 mask 时返回 NaN |

`scatter_visual_embeddings(hidden_states, tokens, visual_embeddings, visual_token_mask, image_token_id)`（`models/multimodal/scatter.py`）把投影后的视觉 embedding 按 `tokens == img_id` 的占位槽 `masked_scatter_` 进文本 hidden（带 `validate_token_count` 校验视觉 embedding 数与占位槽数一致）。前向顺序：视觉塔编码 → `projector` → `scatter_visual_embeddings` 合并 → 逐 Llama3 解码层（用 `llama3_masks`）。

## SigLIP2 视觉塔 NPU 子类

`VisionTransformerNpu`（`vlm/siglip2.py`）子类化上游 `siglip2.VisionTransformer`，手动重建各字段以避免先构造上游 `FlexAttention` 再替换；硬编码 `self.eos_id = 11`（对齐上游）。其 `VisionEmbeddingsNpu.forward` 用 `resize_positional_embeddings_zero_padded` 按每张图的 `grid_hw`（`spatial_h/w = max(grid)+1`）做 `F.interpolate(mode="bilinear", align_corners=False, antialias=True)` 缩放位置编码，padding 行**置零**。`VisionAttentionNpu` 把 q/k/v/out 投影后经 `inner_attention`（`DenseMaskSDPA`）做注意，输出 `rearrange` 回 `(b l (h d))`。

## 并行：FSDP/HSDP only

`parallelize_vlm_npu`（`vlm/parallelize.py`）先 `_validate_supported_parallel_dims`：若启用 `tp` / `pp` / `cp` 直接 `NotImplementedError("VLM NPU currently only supports FSDP/HSDP data parallelism.")`；再 `_validate_npu_vlm_converter` 校验 `npu_vlm` 在 `model.converters` 中，然后委托上游 `parallelize_vlm`。`vlm_debugmodel_npu` 的并行配置为 `data_parallel_shard_degree=-1`（FSDP）、`tp/cp/pp_degree=1`、`fsdp_reshard_after_forward="always"`（无 TP/CP/PP/EP）。详见 [fsdp](../parallelism/fsdp.md)。

## npu_vlm converter

`npu_vlm` 是 feature-gate converter（`converters/features/vlm.py`，`@register_model_converter("npu_vlm")`）。它**不改模型**（NPU 注意力已由 `to_npu_vlm_config` 在 config 期选定），只在 `convert` 中校验：模型是 `Llama3Siglip2TransformerNpu`、解码层与编码层的 `inner_attention` 均为 `DenseMaskSDPA`。converter 注册/装配机制见 [model-custom-converter](../frameworks/model_custom_converter.md)。

## 运行

```bash
PYTHONPATH=/path/to/torchtitan:$PWD:${PYTHONPATH:-} \
NGPU=1 \
MODULE=torchtitan_npu.models.vlm \
CONFIG=vlm_debugmodel_npu \
COMM_MODE=fake_backend \
bash scripts/run_train.sh \
  --training.local_batch_size 1 \
  --training.seq_len 256 \
  --dataloader.max_patches_per_image 64 \
  --dataloader.max_images_per_batch 4
```

`cc12m-test`（调试切片）/ `cc12m` 数据集、`vlm_tokenizer` 资产、`fake_backend` 通信 + 2 步均为 debug 配置。

## MindSpeed-MM VLM 训练

[mindspeed-mm](../frameworks/mindspeed_mm.md) 把上面那套 debug-model 的 NPU 适配模式落到真实大模型：Qwen3-VL-30B-A3B 这类 MoE VLM 从 HF 迁入**插件式 FSDP2 后端**后做全量 / LoRA 微调。这里是**理解类** VLM（视觉编码器 + 文本解码器 + 输出头），训练目标是文本 token 的交叉熵；与生成侧 DiT/VAE 的多模态训练（[multimodal-dit-vae-train](multimodal_dit_vae_train.md)）属两类不同的多模态训练任务。

### Qwen3-VL 的 FSDP2 迁移

接入一个新 VLM 的本质是让它被 FSDP2 训练流程识别、构建、施加分片。Qwen3-VL 走 **Transformers 模型接入**：模型类仍继承 HF `PreTrainedModel`，框架按 `AutoConfig.from_pretrained` 自动构建并加载权重，无需自写加载逻辑；只在顶层类加 `@model_register.register("qwen3_vl_moe")`，注册名即 YAML 的 `model.model_id`。但 Qwen3-VL 要在 **forward 内部**改造（插入序列并行的切分/聚合通信、累加 MoE 负载均衡 aux loss），import 上游类满足不了，于是把 `modeling_qwen3_vl_moe.py` 整体拷进 `mindspeed_mm/fsdp/models/qwen3vl/` 再改，并保持与上游 diff 最小以便跟随升级。

改造分必做与可选两类：

- **必做**：`forward` 接收 dataloader 的 batch 字段、返回带 `.loss` 的输出对象（训练引擎以 `model(**batch, use_cache=False)` 调用并读 `output.loss`）；继承 HF 的模型还要 `accepts_loss_kwargs = False`。补齐这些即可跑通。
- **可选增强**：长序列才需 forward 适配 CP（否则保持 `parallel.ulysses_parallel_size: 1`）；追求性能才把热点算子换 `fsdp/ops/` 融合算子——`npu_patch.py` 把 vision 的 `apply_rotary_pos_emb_vision`、text 的 `apply_rotary_pos_emb` 都换成 half-rope NPU 算子、`Qwen3VLMoeTextRMSNorm.forward` 换 NPU RMSNorm、`Qwen3VLMoeTextExperts.forward` 换 fused MoE；MoE 才需 aux loss。

分片 / 冻结 / 重计算填的都是模型模块树路径（`model.visual.blocks.{*}` / `model.language_model.layers.{*}` / `lm_head`，`{*}` 通配层号）：`parallel.fsdp_plan.apply_modules` 列出逐个 `fully_shard` 的子模块、最后再分片最外层 model；`model.freeze: [model.visual]` 微调时冻结视觉编码器（`requires_grad=False`、不再为其存梯度/优化器状态）；`features.recompute_plan.apply_modules` 对视觉与 LLM 两段开重计算。大模型用 `training.init_model_with_meta_device: true` + DCP（分布式检查点）权重：先在 meta 设备只建结构、再由 DCP 按分片直接加载到各卡（30B bf16 约 60GB，避免多卡主机内存重复占用），训练前需先 `mm-convert GenericDCPConverter hf_to_dcp` 把 HF 权重转成 DCP。FSDP2 装配、per-parameter DTensor sharding、`tensor_parallel_size` 必须为 1 等单后端约束见框架页，此处不重复。

### VLM loss 计算口径

VLM 用交叉熵，但 HF 主流实现有个坑：**global batch size 固定时，`micro_batch_size × grad_acc_steps` 不同组合（如 32×2 vs 16×4）会跑出不同的 loss 曲线与终值**——根因是有效 token 数在归一时被错误处理（Qwen2.5-VL/Qwen3-VL 因 `num_token_in_batch` 传参错误、或干脆不计算它而中招）。MindSpeed-MM 给三种归一口径（FSDP2 后端 `features.loss_cfg.loss_type`，Megatron 后端 `--calculate-per-sample-loss` / `--calculate-per-token-loss` 二者互斥；`loss_type: raw` 则沿用模型自带 loss）。

labels 先 `F.pad(..., (0,1))` 右移成 next-token 目标 `shift_labels`，`loss_mask = shift_labels > -1` 标有效 token，再按口径选 `alpha`（归一分母）与 `reduction` 交给 `fixed_cross_entropy(logits, labels, alpha, reduction)`：

| `loss_type` | 归一步骤 | 实现（`alpha` / `reduction`） |
|---|---|---|
| `default` | 微批内对有效 token 求均值 → grad-acc 维均值 → DP 维均值（同 HF） | `alpha = loss_mask.sum()`（标量）、`reduction="sum"`，`loss = Σce / alpha` |
| `per_sample_loss` | **样本内**对有效 token 求均值 → 微批 → grad-acc → DP 均值 | `alpha = loss_mask.sum(1) * batch`、`reduction="none"`，逐样本 `loss.sum(1)/alpha` 再求和；变长由 `cu_seqlens` 切样本 |
| `per_token_loss` | 全局所有有效 token 的 ce 直接累加 ÷ 全局有效 token 总数 | `reduction="sum"`，`alpha = avg_per_step_token_num`（跨 DP `all_reduce(AVG)`，须配 `PrefetchGradAccDataLoader`，缺则报错） |

口径不是等价选择：样本长度不均（有的 response 很长、有的就一个 token）时，`per_token_loss` 会让 target token 多的长样本权重更大、引入样本间不平衡，需按数据分布选。开 CP 时 `shift_labels` 与 per-sample 的 `alpha` 都经 `split_forward_gather_backward_with_cp` 沿序列切给各 rank。该 loss 在 `TrainEngine.set_loss_func` 处把 `loss_type` 编译成闭包挂到 `model.loss_function`；开 `enable_chunk_loss` 时按 `chunk_size` 沿序列分块算以省 logits 显存，与 [mm-activation-memory](../techniques/mm_activation_memory.md) 的 ChunkLoss 同源。

### 多模态数据接入

数据走本地多模态 **ShareGPT 风格**：每条样本 `messages`（`{"role","content"}` 列表）+ `images`/`videos`，文本里用 `<image>`/`<video>` 占位符标视觉插入点。COCO + LLaVA-Instruct-150K 这类原始集先用 `llava_instruct_2_mllm_demo_format.py` 转成上述目标格式；功能/性能测试可用 `generate_mock_data_for_vlmodel.py` 按指定图数/分辨率/文本长造虚构数据（序列长尽量贴 `cutoff_len`，否则截断图片占位符会训不动）。框架支持纯文本与有图/无图混合训练。

数据链路三段各看条件复用：标准对话格式直接复用注册名 `huggingface` 的通用数据集（`@data_register.register("huggingface")`）；**多模态打包 Plugin**（`mm_plugin.py` 的 `PLUGINS` 表，按模型展开视觉 token）——Qwen3-VL 用 `Qwen3VLPlugin`（继承 `Qwen2VLPlugin`，按 Qwen3-VL 的视觉 token 占位/视频时间戳覆写，把 `<image>`/`<video>` 展开成带 vision 特殊 token 的序列并产出 `pixel_values`/`image_grid_thw`）；**collator** 复用 `DataCollatorForQwen2vl`，注册为 `collator_id: qwen3vl`。YAML `data` 段里 `template` 字段选定 Plugin，`attr` 做字段映射（**键是框架固定的概念名、值填你数据里的列名/取值**：`role_tag`/`content_tag` 对应消息内键名，经典 sharegpt 格式则填 `from`/`value`/`human`）。`preprocess_parameters.model_name_or_path` 在此只加载 tokenizer/processor、不加载训练权重（权重由 `training.load` 指定）。

## Evidence

- [torchtitan-npu](https://gitcode.com/cann/torchtitan-npu) — [`docs/feature_guides/vlm.md`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/feature_guides/vlm.md)（VLM debug model 运行入口）
- 模型入口与注册（@8f128cd）：[`config_registry.py`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/models/vlm/config_registry.py)（`vlm_debugmodel_npu`）、[`vlm/__init__.py`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/models/vlm/__init__.py)（`model_registry`）
- multimodal 稠密掩码 / scatter helper（@8f128cd）：[`masks.py`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/models/multimodal/masks.py)、[`scatter.py`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/models/multimodal/scatter.py)、[`vlm/model.py`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/models/vlm/model.py)（`forward` / `get_attention_masks`）
- SigLIP2 视觉塔 NPU 子类（@8f128cd）：[`vlm/siglip2.py`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/models/vlm/siglip2.py)（`VisionTransformerNpu` / `VisionEmbeddingsNpu` / `resize_positional_embeddings_zero_padded`）

MindSpeed-MM 部分（[mindspeed-mm](https://gitcode.com/Ascend/MindSpeed-MM)，钉定 ref `8e740b46cb82…`，blob base `https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/`）：

- Qwen3-VL FSDP2 迁移：[`docs/zh/features/fsdp2_qwen3vl_migration_practice.md`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/docs/zh/features/fsdp2_qwen3vl_migration_practice.md)（Transformers 接入 / forward 内部改造 / `fsdp_plan.apply_modules` / `freeze: model.visual` / meta init + `hf_to_dcp`）、[`mindspeed_mm/fsdp/models/qwen3vl/modeling_qwen3_vl_moe.py`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/mindspeed_mm/fsdp/models/qwen3vl/modeling_qwen3_vl_moe.py)（`@model_register.register("qwen3_vl_moe")`）、[`mindspeed_mm/fsdp/models/qwen3vl/npu_patch.py`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/mindspeed_mm/fsdp/models/qwen3vl/npu_patch.py)（vision/text half-rope、`Qwen3VLMoeTextRMSNorm`、`Qwen3VLMoeTextExperts` fused-MoE 算子替换）
- VLM loss 口径：[`docs/zh/features/vlm_model_loss_calculate_type.md`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/docs/zh/features/vlm_model_loss_calculate_type.md)（default / per_sample / per_token 三口径 + global-batch 一致性问题）、[`mindspeed_mm/fsdp/loss/loss_func.py`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/mindspeed_mm/fsdp/loss/loss_func.py)（`get_loss_func_params` 选 `alpha`/`reduction`、`build_loss_func`、`per_token_loss` 须 `avg_per_step_token_num`）、[`mindspeed_mm/fsdp/features/memory/chunkloss/chunkloss.py`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/mindspeed_mm/fsdp/features/memory/chunkloss/chunkloss.py)（`fixed_cross_entropy` 按 `alpha` 归一的标量/per-sample/per-token 分支）、[`mindspeed_mm/fsdp/train/train_engine.py`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/mindspeed_mm/fsdp/train/train_engine.py)（`set_loss_func`：`loss_type→build_loss_func`、`raw` 回退、挂 `model.loss_function`）、[`mindspeed_mm/fsdp/params/feature_args.py`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/mindspeed_mm/fsdp/params/feature_args.py)（`LossArguments.loss_type` / `router_aux_loss_coef`）
- 多模态数据接入：[`docs/zh/features/building_data_for_VLModel.md`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/docs/zh/features/building_data_for_VLModel.md)（ShareGPT 格式 / `<image>` 占位 / 纯文混合 / mock 数据）、[`mindspeed_mm/fsdp/data/data_utils/func_utils/mm_plugin.py`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/mindspeed_mm/fsdp/data/data_utils/func_utils/mm_plugin.py)（`Qwen3VLPlugin` 继承 `Qwen2VLPlugin`、`PLUGINS` 表、`get_mm_plugin`）、[`mindspeed_mm/fsdp/data/dataloader/data_collator.py`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/mindspeed_mm/fsdp/data/dataloader/data_collator.py)（`DataCollatorForQwen2vl`、`collator_id "qwen3vl"`）、[`mindspeed_mm/fsdp/data/datasets/huggingface/qwen2vl_dataset.py`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/mindspeed_mm/fsdp/data/datasets/huggingface/qwen2vl_dataset.py)（`@data_register.register("huggingface")`）、[`mindspeed_mm/fsdp/tools/data_tool/llava_instruct_2_mllm_demo_format.py`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/mindspeed_mm/fsdp/tools/data_tool/llava_instruct_2_mllm_demo_format.py) / [`generate_mock_data_for_vlmodel.py`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/mindspeed_mm/fsdp/tools/data_tool/generate_mock_data_for_vlmodel.py)

## Links

- 框架总览与 MODULE/CONFIG 入口机制：[torchtitan](../frameworks/torchtitan.md)
- converter 注册/装配：[model-custom-converter](../frameworks/model_custom_converter.md)
- 数据并行：[fsdp](../parallelism/fsdp.md)
- [mindspeed-mm](../frameworks/mindspeed_mm.md)（MindSpeed-MM 是 VLM 多模态训练的框架载体）
- [multimodal-dit-vae-train](multimodal_dit_vae_train.md)（同域·生成侧：DiT/VAE 多模态训练，与本页理解类 VLM 训练对照）
- [mm-activation-memory](../techniques/mm_activation_memory.md)（同域：FSDP2 后端 ChunkLoss/激活显存优化，VLM loss 分块算的承载）