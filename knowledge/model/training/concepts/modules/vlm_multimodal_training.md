---
type: Concept
title: VLM 多模态训练（TorchTitan Qwen3.5 与 MindSpeed-MM）
description: 当前 TorchTitan Qwen3.5 上游复用、视觉 mask 上限、视频 MRoPE 和 VL CP 拒绝条件；保留 MindSpeed-MM 的模型注册、数据接入、loss 归一与微调契约。
tags:
- task.design
- topic.model_architecture
- topic.multimodal
status: stable
sources:
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/examples/qwen3_5/readme.md
  role: primary
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/patches/torchtitan/hf_datasets/multimodal/mm_collator.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/qwen3_5/__init__.py
  role: implementation
- resource: cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/docs/zh/guides/practices/fsdp2_qwen3vl_migration_practice.md
  role: supporting
- resource: cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/mindspeed_mm/fsdp/models/qwen3vl_moe/modeling_qwen3_vl_moe.py
  role: supporting
- resource: cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/mindspeed_mm/fsdp/models/qwen3vl_moe/npu_patch.py
  role: supporting
- resource: cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/docs/zh/features/optimization/vlm_model_loss_calculate_type.md
  role: supporting
- resource: cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/mindspeed_mm/fsdp/loss/loss_func.py
  role: supporting
- resource: cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/mindspeed_mm/fsdp/features/memory/chunkloss/chunkloss.py
  role: supporting
- resource: cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/mindspeed_mm/fsdp/train/train_engine.py
  role: supporting
- resource: cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/mindspeed_mm/fsdp/params/feature_args.py
  role: supporting
- resource: cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/docs/zh/features/data/building_data_for_VLModel.md
  role: supporting
- resource: cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/mindspeed_mm/fsdp/data/data_utils/func_utils/mm_plugin.py
  role: supporting
- resource: cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/mindspeed_mm/fsdp/data/dataloader/data_collator.py
  role: supporting
- resource: cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/mindspeed_mm/fsdp/data/datasets/huggingface/qwen2vl_dataset.py
  role: supporting
- resource: cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/mindspeed_mm/fsdp/tools/data_tool/llava_instruct_2_mllm_demo_format.py
  role: supporting
- resource: cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/mindspeed_mm/fsdp/tools/data_tool/generate_mock_data_for_vlmodel.py
  role: supporting
created_at: '2026-06-23T00:00:00Z'
updated_at: '2026-10-29T15:39:13Z'
platforms:
- agnostic
---

# VLM 多模态训练（当前 TorchTitan Qwen3.5 与 MindSpeed-MM）

## 当前 TorchTitan NPU 路径

当前仓库使用 `torchtitan_npu.models.qwen3_5` 复用社区模型/recipe，并在导入时安装视觉 mask、连续视频 MRoPE 和 FLA 兼容补丁；原 `models/vlm`、SigLIP2 子类、`npu_vlm` gate 与 entry.py 白名单已移除，不再作为当前接入契约。

`examples/qwen3_5/qwen3_5_debugmodel_1p_cpt_512.sh` 默认 qwen35_debugmodel、cc12m-test、seq512、10步；MoE 8进程入口默认 qwen35_debugmodel_moe、EP8/DP-shard8、spmd_types。它们是 debug/CPT 样例，不证明真实模型或完整 SFT 已验收。

默认启用 GDN override，MoE dispatcher 是可选性能项、默认关闭；`ENABLE_NPU_MOE_DISPATCHER=1` 可启用。用户显式 OVERRIDE_IMPORTS 优先，空字符串可禁用默认 override。脚本透传给当前 `torchtitan_npu.train`，数据、tokenizer 与上游路径须匹配安装环境。

## 视觉 mask 与并行边界

视觉 eager Flex 兼容层只处理显式标记、等长、各 head 共享的 self-attention mask，dense bool mask 在一次 vision forward 内缓存给各 block 复用；编译追踪时在同样形状/语义条件下使用有界 dense SDPA。物化上限为16,777,216个 bool 元素，超过会在下发前失败，应减少图像最大像素、帧数或视觉序列长度。

当前 **Qwen3.5-VL 配置的 CP 会在 parallelizer 拒绝**，视觉 mask 尚未完成 CP metadata 适配；纯文本长上下文专用 CP recipe 是另一范围。不能沿用旧 VLM 的“FSDP/HSDP only”概括所有当前模型，也不能由纯文本 CP 能力推出 VL CP 可用。

## 连续视频 MRoPE

multimodal collator 在模型 Config 之前构造位置，后期 override 无法修复已生成的位置。当前补丁按 image/video 的完整 T/H/W grid 构造3D MRoPE，要求 patch_order=block，并按 packed positions 的重启区分文档；apply 检查上游函数签名且幂等安装。视觉 token 顺序、视频 grid 与 packed 边界必须一起核对，不能将视频简单退化为不相关帧的图像 grid。

## MindSpeed-MM VLM 训练

[mindspeed-mm](../frameworks/mindspeed_mm.md) 提供真实大模型的独立 NPU 训练路线：Qwen3-VL-30B-A3B 这类 MoE VLM 从 HF 迁入**插件式 FSDP2 后端**后做全量 / LoRA 微调。这里是**理解类** VLM（视觉编码器 + 文本解码器 + 输出头），训练目标是文本 token 的交叉熵；与生成侧 DiT/VAE 的多模态训练（[multimodal-dit-vae-train](multimodal_dit_vae_train.md)）属两类不同的多模态训练任务。

### Qwen3-VL 的 FSDP2 迁移

接入一个新 VLM 的本质是让它被 FSDP2 训练流程识别、构建、施加分片。Qwen3-VL 走 **Transformers 模型接入**：模型类仍继承 HF `PreTrainedModel`，框架按 `AutoConfig.from_pretrained` 自动构建并加载权重，无需自写加载逻辑；只在顶层类加 `@model_register.register("qwen3_vl_moe")`，注册名即 YAML 的 `model.model_id`。但 Qwen3-VL 要在 **forward 内部**改造（插入序列并行的切分/聚合通信、累加 MoE 负载均衡 aux loss），import 上游类满足不了，于是把 `modeling_qwen3_vl_moe.py` 整体拷进 `mindspeed_mm/fsdp/models/qwen3vl_moe/` 再改，并保持与上游 diff 最小以便跟随升级。

改造分必做与可选两类：

- **必做**：`forward` 接收 dataloader 的 batch 字段、返回带 `.loss` 的输出对象（训练引擎以 `model(**batch, use_cache=False)` 调用并读 `output.loss`）；继承 HF 的模型还要 `accepts_loss_kwargs = False`。补齐这些即可跑通。
- **可选增强**：长序列才需 forward 适配 CP（否则保持 `parallel.ulysses_parallel_size: 1`）；追求性能才把热点算子换 `fsdp/ops/` 融合算子——`npu_patch.py` 把 vision 的 `apply_rotary_pos_emb_vision`、text 的 `apply_rotary_pos_emb` 都换成 half-rope NPU 算子、`Qwen3VLMoeTextRMSNorm.forward` 换 NPU RMSNorm、`Qwen3VLMoeTextExperts.forward` 换 fused MoE；MoE 才需 aux loss。

分片 / 冻结 / 重计算填的都是模型模块树路径（`model.visual.blocks.{*}` / `model.language_model.layers.{*}` / `lm_head`，`{*}` 通配层号）：`parallel.fsdp_plan.apply_modules` 列出逐个 `fully_shard` 的子模块、最后再分片最外层 model；`model.freeze: [model.visual]` 微调时冻结视觉编码器（`requires_grad=False`、不再为其存梯度/优化器状态）；`features.recompute_plan.apply_modules` 对视觉与 LLM 两段开重计算。大模型用 `training.init_model_with_meta_device: true` + DCP（分布式检查点）权重：先在 meta 设备只建结构、再由 DCP 按分片直接加载到各卡（30B bf16 约 60GB，避免多卡主机内存重复占用），离线 `hf_to_dcp` 转换为 DCP 是可选方式；也可用 `training.load` 直接指向 HF safetensors 目录，load_format=auto 会识别并调用 load_hf_checkpoint，meta 初始化不要求必须先转换DCP。FSDP2 装配、per-parameter DTensor sharding、`tensor_parallel_size` 必须为 1 等单后端约束见框架页，此处不重复。

### VLM loss 计算口径

VLM 用交叉熵，但 HF 主流实现有个坑：**global batch size 固定时，`micro_batch_size × grad_acc_steps` 不同组合（如 32×2 vs 16×4）会跑出不同的 loss 曲线与终值**——根因是有效 token 数在归一时被错误处理（Qwen2.5-VL/Qwen3-VL 因 `num_token_in_batch` 传参错误、或干脆不计算它而中招）。MindSpeed-MM 给三种归一口径（FSDP2 后端 `features.loss_cfg.loss_type`，Megatron 后端 `--calculate-per-sample-loss` / `--calculate-per-token-loss` 二者互斥；`loss_type: raw` 则沿用模型自带 loss）。

labels 先 `F.pad(..., (0,1))` 右移成 next-token 目标 `shift_labels`，`loss_mask = shift_labels > -1` 标有效 token，再按口径选 `alpha`（归一分母）与 `reduction` 交给 `fixed_cross_entropy(logits, labels, alpha, reduction)`：

| `loss_type` | 归一步骤 | 实现（`alpha` / `reduction`） |
|---|---|---|
| `default` | 微批内对有效 token 求均值 → grad-acc 维均值 → DP 维均值（同 HF） | `alpha = loss_mask.sum()`（标量）、`reduction="sum"`，`loss = Σce / alpha` |
| `per_sample_loss` | **样本内**对有效 token 求均值 → 微批 → grad-acc → DP 均值 | `alpha = loss_mask.sum(1) * batch`、`reduction="none"`，逐样本 `loss.sum(1)/alpha` 再求和；变长由 `cu_seqlens` 切样本 |
| `per_token_loss` | 全局所有有效 token 的 ce 直接累加 ÷ 全局有效 token 总数 | `reduction="sum"`，`alpha = avg_per_step_token_num`（跨 DP `all_reduce(AVG)`，须配 `PrefetchGradAccDataLoader`，缺则报错） |

口径不是等价选择：样本长度不均（有的 response 很长、有的就一个 token）时，`per_token_loss` 会让 target token 多的长样本权重更大、引入样本间不平衡，需按数据分布选。开 CP 时 shift_labels 沿序列切分；per-sample alpha 只有提供 cu_seqlens 的打包样本分支才按序列切分，普通批次的 alpha 形状为[batch_size]、不做此切分。该 loss 在 `TrainEngine.set_loss_func` 处把 `loss_type` 编译成闭包挂到 `model.loss_function`；开 `enable_chunk_loss` 时按 `chunk_size` 沿序列分块算以省 logits 显存，与 [mm-activation-memory](../techniques/mm_activation_memory.md) 的 ChunkLoss 同源。

### 多模态数据接入

数据走本地多模态 **ShareGPT 风格**：每条样本 `messages`（`{"role","content"}` 列表）+ `images`/`videos`，文本里用 `<image>`/`<video>` 占位符标视觉插入点。COCO + LLaVA-Instruct-150K 这类原始集先用 `llava_instruct_2_mllm_demo_format.py` 转成上述目标格式；功能/性能测试可用 `generate_mock_data_for_vlmodel.py` 按指定图数/分辨率/文本长造虚构数据（序列长尽量贴 `cutoff_len`，否则截断图片占位符会训不动）。框架支持纯文本与有图/无图混合训练。

数据链路三段各看条件复用：标准对话格式直接复用注册名 `huggingface` 的通用数据集（`@data_register.register("huggingface")`）；**多模态打包 Plugin**（`mm_plugin.py` 的 `PLUGINS` 表，按模型展开视觉 token）——Qwen3-VL 用 `Qwen3VLPlugin`（继承 `Qwen2VLPlugin`，按 Qwen3-VL 的视觉 token 占位/视频时间戳覆写，把 `<image>`/`<video>` 展开成带 vision 特殊 token 的序列并产出 `pixel_values`/`image_grid_thw`）；**collator** 复用 `DataCollatorForQwen2vl`，注册为 `collator_id: qwen3vl`。YAML `data` 段里 `template` 字段选定 Plugin，`attr` 做字段映射（**键是框架固定的概念名、值填你数据里的列名/取值**：`role_tag`/`content_tag` 对应消息内键名，经典 sharegpt 格式则填 `from`/`value`/`human`）。`preprocess_parameters.model_name_or_path` 在此只加载 tokenizer/processor、不加载训练权重（权重由 `training.load` 指定）。


## 验证范围

TorchTitan debug 冒烟与 MindSpeed-MM 真实模型微调分别验收：核对图像/视频占位、tokenizer/processor、packed 文档边界、有效 label、loss 口径、冻结模块及各路梯度。meta 初始化、HF/DCP 加载还要检查实际加载分支与权重一致性；不能把仅能导入或运行文本模型作为完整 VL 路径验证。本次没有运行 NPU 训练。

## Evidence

- [readme.md](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/examples/qwen3_5/readme.md)（primary）
- [mm_collator.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/patches/torchtitan/hf_datasets/multimodal/mm_collator.py)（implementation）
- [__init__.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/qwen3_5/__init__.py)（implementation）
- [fsdp2_qwen3vl_migration_practice.md](../../../../../cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/docs/zh/guides/practices/fsdp2_qwen3vl_migration_practice.md)（supporting）
- [modeling_qwen3_vl_moe.py](../../../../../cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/mindspeed_mm/fsdp/models/qwen3vl_moe/modeling_qwen3_vl_moe.py)（supporting）
- [npu_patch.py](../../../../../cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/mindspeed_mm/fsdp/models/qwen3vl_moe/npu_patch.py)（supporting）
- [vlm_model_loss_calculate_type.md](../../../../../cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/docs/zh/features/optimization/vlm_model_loss_calculate_type.md)（supporting）
- [loss_func.py](../../../../../cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/mindspeed_mm/fsdp/loss/loss_func.py)（supporting）
- [chunkloss.py](../../../../../cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/mindspeed_mm/fsdp/features/memory/chunkloss/chunkloss.py)（supporting）
- [train_engine.py](../../../../../cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/mindspeed_mm/fsdp/train/train_engine.py)（supporting）
- [feature_args.py](../../../../../cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/mindspeed_mm/fsdp/params/feature_args.py)（supporting）
- [building_data_for_VLModel.md](../../../../../cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/docs/zh/features/data/building_data_for_VLModel.md)（supporting）
- [mm_plugin.py](../../../../../cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/mindspeed_mm/fsdp/data/data_utils/func_utils/mm_plugin.py)（supporting）
- [data_collator.py](../../../../../cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/mindspeed_mm/fsdp/data/dataloader/data_collator.py)（supporting）
- [qwen2vl_dataset.py](../../../../../cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/mindspeed_mm/fsdp/data/datasets/huggingface/qwen2vl_dataset.py)（supporting）
- [llava_instruct_2_mllm_demo_format.py](../../../../../cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/mindspeed_mm/fsdp/tools/data_tool/llava_instruct_2_mllm_demo_format.py)（supporting）
- [generate_mock_data_for_vlmodel.py](../../../../../cann-recipes-raw/mindspeed-mm/0d2270c8ee178d7bfece88f356a5072bf8e2b3ed/mindspeed_mm/fsdp/tools/data_tool/generate_mock_data_for_vlmodel.py)（supporting）

## Links

- [TorchTitan NPU](../frameworks/torchtitan.md)
- [MindSpeed-MM](../frameworks/mindspeed_mm.md)
- [组件配置替换](../frameworks/model_custom_converter.md)
- [Chunk Loss](../techniques/chunk_loss.md)
- [MM 激活显存治理](../techniques/mm_activation_memory.md)
- [生成侧 DiT/VAE 训练](multimodal_dit_vae_train.md)
