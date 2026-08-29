---
type: Concept
title: MindSpeed-MM（昇腾 NPU 多模态大模型训练套件）
description: >-
  MindSpeed-MM 面向 VLM、DiT 图像/视频生成和 Omni 训练，提供 Megatron-mcore 与插件式 FSDP2 两条后端，
  由 NON_MEGATRON 分流。FSDP2 通过 model/data 注册表和顶层 YAML 接入新模型，使用逐参数 DTensor
  sharding、逐模块 fully_shard 和 reshard_after_forward 切换 ZeRO-2/3；其约束包括禁用分布式优化器与
  Megatron 完全重计算、桥接式 TP=1、仅 DCP 检查点。Bridge 层按架构解析模型，通过通配参数映射
  双向拆分、合并和重排权重；Canonical Model 保留 HF 计算布局，使 LoRA 可跨 HF/Megatron 复用。
  套件还通过 verl_plugin 接入 GRPO、DanceGRPO 和 Sora-DPO。
tags:
- task.implementation
- topic.architecture
- topic.reinforcement_learning
- topic.multimodal
status: stable
sources:
- resource: https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/README.md
  role: primary
- resource: https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/docs/zh/features/fsdp2.md
  role: supporting
created_at: '2026-06-24T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# MindSpeed-MM（昇腾 NPU 多模态大模型训练套件）

## Summary

MindSpeed-MM 是昇腾 NPU 的**多模态大模型训练套件**，建在 [mindspeed](mindspeed.md) 训练加速底座之上，覆盖 **VLM 理解 / DiT 视频图像生成 / Omni 全模态** 三类模态。它提供两套训练后端——传统 Megatron-mcore 路线，与新版**插件式 FSDP2**（一份顶层 YAML + 注册表解耦模型/数据/特性，per-parameter sharding 的 DTensor 替代 FSDP1 的 FlatParameter）；用 **Bridge + Canonical Model** 两层抽象做 HF↔Megatron 的权重映射与计算等价转换；并经 `verl_plugin` 支持多模态生成式 RL。DiT/VAE/DiT-Cache 见 [dit](../../../inference/concepts/modules/dit.md)、[vae](../../../inference/concepts/modules/vae.md)、[dit-cache](../../../inference/concepts/techniques/dit_cache.md)。

## 双训练后端：Megatron-mcore vs 插件式 FSDP2

仓内**同时存在两套容易混淆的后端**，入口、配置、模型/数据接入方式都不同（下表逐维度对照）。新增模型/数据集**推荐优先接入新版插件式 FSDP2**；Megatron 桥接式属过渡形态，仅用于存量入口兼容、后续不再迭代新特性。

| 维度 | 新版插件式 FSDP2（主线） | Megatron-mcore 路线（旧 / 桥接） |
|---|---|---|
| 常见入口 | `mindspeed_mm/fsdp/train/trainer.py`，或 `fsdp/tasks/*` 任务专用入口 | `pretrain_vlm.py` / `pretrain_omni.py` / `pretrain_sora.py` / `pretrain_transformers.py` |
| 配置形态 | 一份顶层 YAML（`parallel`/`data`/`model`/`features`/`training`/`tools` 六段） | 主训练配置 + 额外 `fsdp2_config.yaml`（桥接式 FSDP2 时） |
| 启用方式 | 启动脚本直传顶层 YAML；`training.plugin` 递归导入插件触发注册 | 命令行 `--use-torch-fsdp2`、`--fsdp2-config-path` |
| 模型接入 | `@model_register.register` + `ModelHub.build` | `model_provider` / `forward_step` / `loss_func` |
| 数据接入 | `@data_register.register` + `build_mm_dataset/build_mm_dataloader` | `train_valid_test_datasets_provider` / `get_batch` |
| 分片字段 | `parallel.fully_shard_parallel_size`、`parallel.fsdp_plan.apply_modules` | `sharding_size`、`sub_modules_to_wrap` |
| 分片表示 | PyTorch FSDP2 / per-parameter DTensor | Megatron TP/PP/CP/DP 切分 |

**设计取舍**：Megatron 路线靠融合算子（`linear_qkv`/`linear_fc1`）+ 5D 并行换性能，但模型适配成本高、权重与 HF 不兼容；插件式 FSDP2 与模型结构解耦、新模型接入成本低（量级是写一个注册类 + 一份 YAML），代价是单后端约束更多（见下）。两条路线靠启动脚本里的 `NON_MEGATRON=true` 环境变量在入口处分流。

## 插件式 FSDP2 后端

### 链路与注册解耦

`Trainer` 把一次训练装配为：`torchrun → trainer.py → ConfigManager 加载顶层 YAML → import_plugin 递归导入 training.plugin 触发注册 → ModelHub.build 构建模型 →（可选）LoRA 注入 → ParallelApplier 应用 TP/EP/Recompute/FSDP2 → build_mm_dataset/dataloader → TrainEngine 跑 `model(**batch, use_cache=False).loss``。

三条注册表一致性约束：
- `model.model_id` ⇔ `@model_register.register("<model_id>")`；
- `data.dataset_param.dataset_type` ⇔ `@data_register.register("<dataset_type>")`；
- `training.plugin` 必须含模型/数据插件路径（用 `/` 写，导入时转 Python 包路径）。

模型接入三种方式（`BaseModel` 子类）：自定义模型（实现 `_from_config`/`from_pretrained`）、Transformers 模型（保持 HF `from_pretrained` 签名）、第三方 wrapper 适配。`ModelHub.build` 先试 `AutoConfig.from_pretrained`，成功走 Transformers 风格、失败走自定义构建。`features.loss_cfg.loss_type: raw` 时模型 `forward` 输出必须带 `.loss`。

### per-parameter sharding（为何弃 FSDP1）

FSDP1 把一组参数展平拼成 **FlatParameter** 表示通信桶，导致**桶内单参数难做差异化操作**（冻结、精度转换），状态字典逻辑长达数千行且需额外通信。FSDP2 移除 FlatParameter，**沿 0 维分片为 DTensor**，支持单参数便捷操作、免通信分片状态字典、更简洁初始化。实测 Llama-7B 相比 FSDP1 更高 MFU、峰值内存降 7%、loss 曲线一致。

### sharding 应用机制

`fully_shard_parallel_modules` 应用分片：
- `fsdp_plan.apply_modules` 模式匹配 `named_modules()`，按**后序遍历**（`_post_order_traverse`，子模块先于父模块）对命中子模块逐个 `fully_shard()`，最后再对最外层 model 调一次 `fully_shard()`；`apply_modules` 为空时只包装最外层。
- 混精由 `MixedPrecisionPolicy(param_dtype/reduce_dtype/output_dtype/cast_forward_inputs)` 承载，**在 YAML 配置生效，不再依赖 `--bf16`**。
- `cpu_offload` → `CPUOffloadPolicy(pin_memory=True)` 把参数/梯度/优化器状态 offload 到 CPU。
- `reshard_after_forward`：`True`=前向后立即重分片（省内存，ZeRO3 语义），`False`=保持聚合到反向（更快，ZeRO2 语义）。
- **退化路径**：`fully_shard_parallel_size==1` 且不用 meta init 时，框架退化为 DDP 包装（`find_unused_parameters=True`）便于小规模调试。

`set_modules_to_prefetch` 按 `apply_modules` 顺序自动推导前/反向预取边界（`num_to_forward_prefetch`/`num_to_backward_prefetch`），并对 MoE 专家做 E-FSDP 分组；模型可自定义同名方法覆盖默认逻辑。

### 单后端约束

- **不能开 megatron 分布式优化器**（与 FSDP2 冲突）；
- **必须关 megatron 完全重计算**（`--recompute-granularity/method/num-layers`），改用 `features.recompute_plan` / FSDP2 `recompute_modules`；
- **插件式 FSDP2** 的 `parallel.tensor_parallel_size` 当前仍要求为 `1`，非 1 触发校验错误（桥接式 `--use-torch-fsdp2` 路线无此硬约束）；
- 大模型推荐 `training.init_model_with_meta_device: true`（meta device 先建结构再按 `training.load` 灌权重，降初始化峰值内存）；
- 权重格式仅 `torch_dcp`/`torch_dist`（DCP），见检查点小节。

### 检查点：DCP

插件式后端默认 `DistributedCheckpointer`（`fsdp/checkpoint/dcp_checkpointer.py`），底层 `torch.distributed.checkpoint`（DCP）。加载支持：HF safetensors 目录直载、在线 HF→meta init、离线 `hf_to_dcp` 转 DCP 再 meta init、训练检查点续训（DCP 通用机制 tag `dcp-checkpoint`）。LoRA 在 FSDP2 sharding **之前**注入（`Trainer.enable_lora`），适配器权重与 HF 标准实现兼容（见 Canonical Model）。

## 支持模态与 models 目录组织

套件在 `mindspeed_mm/models/` 下按模态/组件划分子包（非 per-model 堆砌）：

| 模态 | 子包/文件 | 说明 |
|---|---|---|
| VLM 理解 | `vlm_model.py`、`vl_model.py`、`qwen2vl_model.py`、`internvl_model.py`、`deepseekvl_model.py`、`vision/`、`text_decoder/`、`text_encoder/` | 视觉编码器 + 文本解码器组合，详见 [vlm-multimodal-training](../modules/vlm_multimodal_training.md) |
| DiT 视频/图像生成 | `predictor/dits`（DiT 骨干）、`diffusion/`（DDPM/IDDPM/RFlow/flow-match 调度器）、`ae/`（VAE：CausalVAE/WFVAE/Wan-VAE 等）、`sora_model.py` | 复用 [dit](../../../inference/concepts/modules/dit.md)、[vae](../../../inference/concepts/modules/vae.md)、[dit-cache](../../../inference/concepts/techniques/dit_cache.md)，仅训练侧语义在此 |
| Omni 全模态 | `omni/`（`mllm_model.py`、`mllms`）、`omni_model.py`、`audio/`、`whisper/` | 文/图/音/视频统一建模 |

新版插件式后端的模型实现另在 `mindspeed_mm/fsdp/models/<model_name>/`（如 `qwen3_5`、`qwen3vl`、`qwen3omni`、`ltx2`、`wan2_2`、`cosyvoice3`），与上述 mcore 路线 models 并存。

## Bridge HF 等价转换 + Canonical Model

Bridge 与 Canonical Model 两层抽象解决"Megatron 训练 ↔ HF 生态"的权重/计算不兼容：

**(1) Bridge（参数级权重映射）**，由 `bridge/models/conversion/` 实现：
- `auto_bridge.py::AutoBridge` — `from_hf_pretrained(path)` 按 HF config 的 `architectures` 后缀（`ForCausalLM`/`ForConditionalGeneration`/`NemotronH_Nano_VL_V2`）或 diffusion 模型的 `_class_name`（Wan/HunyuanVideo DiT，走 `CLASS_MODULE_MAPPING`）解析模型架构，再取对应 `MegatronModelBridge`；`load_hf_weights` 把 HF 权重灌进 Megatron 模型 list。
- `mapping_registry.py::MegatronMappingRegistry` — 持有一组 `MegatronParamMapping`，把通配模式编译成正则（`*`→`(\d+)` 层号、`**`→`(.*)`），双向查表：`megatron_to_hf_lookup` 命中后 `mapping.resolve(groups)` 把通配符替换成实际层号。
- `param_mapping.py` — 逐参数的拆分/合并/重排规则库（融合 `linear_qkv`↔独立 `q/k/v_proj` 等）。

**(2) Canonical Model（计算等价模型）**：在 Megatron 框架内"还原"HF 原生计算逻辑——**不融合** `linear_qkv`/`linear_fc1`，保持 `q_proj`/`k_proj`/`v_proj`、`gate_proj`/`up_proj` 分层独立，使
- 计算等价（数值与 HF 一致，仅浮点误差）、权重免拆分/合并直接互转、**LoRA 适配器跨框架通用**（融合实现下 qkv 的 LoRA-A 参数量仅为标准的 1/3，算法不等价）。
- 启用方式：模型 JSON 的 `vision_encoder`/`text_decoder` 下置 `canonical_model: true`；当前支持 `Qwen2.5-VL`。取舍：跨框架迁移/LoRA 强烈建议开；纯预训练无跨框架需求可不开（Megatron 融合算子性能略优）。

**命令行**：`mm-convert`（`checkpoint/convert_cli:main`，用 `jsonargparse.auto_cli` 把全部 `Commandable` 子类自动暴露为子命令）。Megatron 路线按模型提供独立 Converter（Qwen2/2.5/3-VL、InternVL、GLM、DeepSeekVL、Mistral3、Qwen2.5-Omni、Sora 系列 CogVideo/StepVideo/HunyuanVideo/Wan 等十余个），各支持 `hf_to_mm` / `mm_to_hf` / `resplit`；**插件式 FSDP2 后端则走通用 `GenericDCPConverter`（`hf_to_dcp` / `dcp_to_hf`，不区分模型结构）**，区别于 Megatron 路线的 per-model 转换器。通用权重转换工具另见 [model-custom-converter](model_custom_converter.md)。

## 生成式 RL 插件 verl_plugin

MindSpeed-MM 内有多条生成式 RL 路径：① `verl_plugin/`（`verl_npu/plugin.py` 把 [verl](verl.md) 适配到昇腾）复现 **GRPO**（当前样例 Qwen2.5-VL / Qwen3-VL）；② 仓内**原生 RL 路径**（与 verl 无关）——**DanceGRPO**（`posttrain_flux_dancegrpo.py` → `tasks/rl/soragrpo` FluxGRPOTrainer）、**Sora-DPO**（`posttrain_sora_dpo.py` → `tasks/rl/dpo` SoRADPOTrainer）。

## Evidence

源页：[mindspeed-mm](https://gitcode.com/Ascend/MindSpeed-MM)（钉定 ref `8e740b46cb82…`）。blob base `https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/`：

- 插件式后端入口与装配链：`mindspeed_mm/fsdp/train/trainer.py`（`Trainer.initialize` / `get_model` / `enable_lora`）、`mindspeed_mm/fsdp/train/train_engine.py`。
- FSDP2 sharding/混精/预取：`mindspeed_mm/fsdp/distributed/fully_shard_parallel.py`（`fully_shard_parallel_modules` / `get_mixprecision_policy` / `set_modules_to_prefetch`）。
- FSDP1→FSDP2 取舍与单后端约束：[`docs/zh/features/fsdp2.md`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/docs/zh/features/fsdp2.md)、[`docs/zh/features/fsdp2_developer_migration_guide.md`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/docs/zh/features/fsdp2_developer_migration_guide.md)、[`docs/zh/pytorch/quickstart_fsdp2.md`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/docs/zh/pytorch/quickstart_fsdp2.md)。
- Bridge 参数映射：`bridge/models/conversion/auto_bridge.py`（`AutoBridge`）、`mapping_registry.py`（`MegatronMappingRegistry`）、`param_mapping.py`。
- Canonical Model + 转换 CLI：[`docs/zh/features/canonical_model.md`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/docs/zh/features/canonical_model.md)、[`docs/zh/features/mm_convert.md`](https://gitcode.com/Ascend/MindSpeed-MM/blob/8e740b46cb8290be0addf060e3e063d0b0380aa6/docs/zh/features/mm_convert.md)、`checkpoint/convert_cli.py`。
- 生成式 RL：`verl_plugin/README.md`、`verl_plugin/verl_npu/plugin.py`、`posttrain_flux_dancegrpo.py`、`posttrain_sora_dpo.py`。

## Links

- 训练底座：[mindspeed](mindspeed.md)
- 多模态训练模块：[vlm-multimodal-training](../modules/vlm_multimodal_training.md)
- 多模态数据流水：[multimodal-data](../techniques/multimodal_data.md)（在线数据重排 + 异步预处理 iterable dataset + 序列 Packing；理解类 MM 训练的数据入口）
- 并行：[fsdp](../parallelism/fsdp.md)
- 激活显存优化：[mm-activation-memory](../techniques/mm_activation_memory.md)（FSDP2 后端的 Chunk-MBS 微批切块 + 异步激活 Offload）
- RL 框架：[verl](verl.md)
- 权重转换：[model-custom-converter](model_custom_converter.md)
- 异构并行：[hetero-parallel](../parallelism/hetero_parallel.md)（MindSpeed-MM 多模态分组并行 / 动态 DP-CP）
- 跨域复用（不重述）：[dit](../../../inference/concepts/modules/dit.md)、[vae](../../../inference/concepts/modules/vae.md)、[dit-cache](../../../inference/concepts/techniques/dit_cache.md)
- [ldt-disaggregated-training](../techniques/ldt_disaggregated_training.md)（MM 多模态分层解耦训练：Qwen2.5-VL 边云协同安全训练）
- [multimodal-dit-vae-train](../modules/multimodal_dit_vae_train.md)（承载的多模态生成训练：扩散 DiT + VAE 家族）

<!-- cannbot:related:start -->
## 相关

- [MindSpeed-MM 数据流水（在线重排 + 异步预处理 + 序列 Packing）](../techniques/multimodal_data.md)（`related`）：MindSpeed-MM 的数据侧用三段互补流水应对：**在线数据重排**（`--use-data-balance`）按样本长度在 DP 间重排、让编码器与 LLM 两段算力各自均衡；**异步预处理 iterable dataset**（`async_preprocess`）把单样本预处理甩给后台 worker、用流水掩盖预处理 / IO 时延；**序列 Packing**（`use_txt_dynamic_batching`）把多条变长序列拼到近 `max_seq_len` 再以 TND layout 喂入，降 pad 并均衡卡间 token 数。；MindSpeed-MM 是昇腾 NPU 的**多模态大模型训练套件**，建在 ［mindspeed］(mindspeed.md) 训练加速底座之上，覆盖 **VLM 理解 / DiT 视频图像生成 / Omni 全模态** 三类模态。前者是后者理解类训练的数据实现入口，后者给出双后端和模型注册边界，可直接把数据流水接回训练套件。
- [MindSpeed（昇腾大模型训练加速框架 + 低精度训练）](mindspeed.md)（`related`）：“MindSpeed Core 是**亲和加速底座**，向上派生面向不同场景的套件，向下落到 PyTorch / MindSpore → CANN → 昇腾硬件。DeepSeek-V3 低精度 LLM 场景用的是 **MindSpeed LLM 套件**：”与“MindSpeed-MM 是昇腾 NPU 的**多模态大模型训练套件**，建在 ［mindspeed］(mindspeed.md) 训练加速底座之上，覆盖 **VLM 理解 / DiT 视频图像生成 / Omni 全模态** 三类模态。它提供两套训练后端——传统 Megatron-mcore 路线，与新版**插件式 FSDP2**（一份顶层 YAML + 注册表解耦模型/数据/特性，per-parameter sharding 的 DTensor 替代 FSDP1 的 FlatParameter）；用 **Bridge + Canonical Model** 两层抽象做 HF↔Megatron 的权重映射与计算等价转换；并经 `verl_plugin` 支持多模态生成式 RL。DiT/VAE/DiT-Cache 见 ［dit］(../../../inference/concepts/modules/dit.md)、［vae］(../../../inference/concepts/modules/vae.md)、［dit-cache］(../../../inference/concepts/techniques/dit_cache.md)。”是双方正文中的具体合同。MindSpeed 卡界定 Core 为套件底座，MindSpeed-MM 卡明确其建立在该底座之上并给出多模态后端，能够解释框架层次和上层能力归属。
- [VLM 多模态训练适配（DenseMaskSDPA）](../modules/vlm_multimodal_training.md)（`related`）：［mindspeed-mm］(../frameworks/mindspeed_mm.md) 把上面那套 debug-model 的 NPU 适配模式落到真实大模型：Qwen3-VL-30B-A3B 这类 MoE VLM 从 HF 迁入**插件式 FSDP2 后端**后做全量 / LoRA 微调。这里是**理解类** VLM（视觉编码器 + 文本解码器 + 输出头），训练目标是文本 token 的交叉熵；与生成侧 DiT/VAE 的多模态训练（［multimodal-dit-vae-train］(multimodal_dit_vae_train.md)）属两类不同的多模态训练任务。；MindSpeed-MM 是昇腾 NPU 的**多模态大模型训练套件**，建在 ［mindspeed］(mindspeed.md) 训练加速底座之上，覆盖 **VLM 理解 / DiT 视频图像生成 / Omni 全模态** 三类模态。它提供两套训练后端——传统 Megatron-mcore 路线，与新版**插件式 FSDP2**（一份顶层 YAML + 注册表解耦模型/数据/特性，per-parameter sharding 的 DTensor 替代 FSDP1 的 FlatParameter）；用 **Bridge + Canonical Model** 两层抽象做 HF↔Megatron 的权重映射与计算等价转换；并经 `verl_plugin` 支持多模态生成式 RL。DiT/VAE/DiT-Cache 见 ［dit］(../../../inference/concepts/modules/dit.md)、［vae］(../../../inference/concepts/modules/vae.md)、［dit-cache］(../../../inference/concepts/techniques/dit_cache.md)。。VLM 模块卡给出真实模型迁入插件式 FSDP2 的路径，框架卡定义承载该路径的多模态套件与后端。
- [分层解耦训练 LDT（Layerwise Disaggregated Training / U 形拆分学习）](../techniques/ldt_disaggregated_training.md)（`related`）：MindSpeed-MM 覆盖 Qwen2.5-VL 多模态（`model.json` 里 `"patch": {"layerwise_disaggregated_training": true}`）。；MindSpeed-MM 是昇腾 NPU 的**多模态大模型训练套件**，建在 ［mindspeed］(mindspeed.md) 训练加速底座之上，覆盖 **VLM 理解 / DiT 视频图像生成 / Omni 全模态** 三类模态。前者给出 LDT 的具体承载配置，后者定义承载套件与训练范围。
<!-- cannbot:related:end -->
