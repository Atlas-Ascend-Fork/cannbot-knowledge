---
type: Guide
title: vLLM Ascend Gemma4 多模态塔（Multimodal Tower）：量化接入与包装器状态
description: 沿 Gemma4 构造函数核对视觉和音频塔的线性层替换、MXFP4/MXFP8 方法识别、实例级视觉补丁、LoRA 与 PLE 状态，区分逻辑激活 dtype、打包权重 dtype 和公开实验性支持边界。
aliases:
- Gemma4 Multimodal Tower
- AscendGemma4ForConditionalGeneration
- _patch_gemma4_vision_patch_embedder
- _ascend_gemma4_vision_patch_embedder_forward
- _ascend_activation_dtype
- _full_attn_layer_idxs
- Gemma4量化视觉塔
tags:
- task.implementation
- task.debugging
- topic.multimodal
- topic.precision
- topic.model_adaptation
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/gemma4_mm.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/__init__.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Gemma4.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
created_at: '2026-10-31T20:30:25Z'
updated_at: '2026-10-31T20:47:09Z'
platforms:
- a2
- a3
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Gemma4 多模态塔（Multimodal Tower）：量化接入与包装器状态

## 适配任务与证据边界

Gemma4 量化视觉塔接入时，重点检查 patch embedder 的输入转换是否读取了打包权重 dtype，以及重建构造函数是否漏掉父类后续路径依赖的状态。AscendGemma4ForConditionalGeneration 在 Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2 中继承 Native Gemma4ForConditionalGeneration，但自行从 nn.Module.__init__ 重建主要字段和模块。本卡负责这条构造与视觉补丁合同；checkpoint 选择、启动参数和模型支持表裁决复用 [Gemma4 部署指南](../models/vllm_ascend_gemma4_dense_moe.md)。

固定 Gemma4 教程 1–32 行声明 A2、A3、950 PR/DT 的模型范围，并描述 eager/graph；支持表保留 Experimental 标记。卡片平台承载这些公开模型范围内的接入知识，不代表全部型号、量化格式、输入模态和执行模式的交叉组合已经测通。教程明确记录的 MXFP4 路径仅面向 950；代码识别 MXFP8 不是所有硬件均获公开量化支持的证明。实际软件配对、权重与运行模式仍按 [版本化环境](../deployment/vllm_ascend_versioned_environment.md) 核对。

## 构造顺序：保留父类消费者需要的状态

构造函数保存 model_config、model_dtype=model_config.dtype、quant_config、multimodal_config 和 vllm_config。_enable_mm_lora 由 lora_config 存在且 enable_tower_connector_lora 为真共同决定；即使没有打开该功能，也要给继承的图像路径提供一致的布尔状态，不能省略字段后等到媒体请求才发现 AttributeError。

视觉塔由 AutoModel.from_config 建立；embed_vision 使用 Gemma4MultimodalEmbedder，并传递 quant_config 与相应 prefix。随后对视觉塔执行 recursive_replace_linear，把普通线性层替换到 Ascend 可消费的量化路径。仅保留视觉模块对象但漏掉递归替换，会让模型结构看似完整而线性层方法与量化 checkpoint 不一致。

如果 audio_config 存在，同样建立 audio_tower，调用其 post_init，再建立 embed_audio，并按 audio_tower 的 prefix 递归替换线性层；没有音频配置时两个字段均为 None。视觉 patch embedder 的特殊 forward 补丁只用于视觉入口，不能扩大成所有音频层或所有 Linear 都使用同一像素变换。

语言模型通过 init_vllm_registered_model 建立，使用 text_config、架构名 Gemma4ForCausalLM 与 language_model prefix。MoE 专家相关属性委托给语言模型；generation_config 中的 suppress_tokens 也被保存。视觉塔参数、连接器和语言模型各有命名与构造边界，迁移时需逐项保留。

## 量化方法判定与实例级 patch

_patch_gemma4_vision_patch_embedder 检查 vision_tower 的 patch_embedder.input_proj.quant_method。若方法对象外包有 quant_method，先解开这一层，再用 isinstance 匹配 AscendW4A4MXFP4DynamicLinearMethod 或 AscendW8A8MXFP8DynamicLinearMethod。它不是通过 checkpoint 文件名、张量 storage dtype 或任意包含 FP4/FP8 的字符串决定。

匹配后在该 patch embedder 实例上保存 _ascend_activation_dtype=model_dtype，并以 __get__ 绑定 _ascend_gemma4_vision_patch_embedder_forward。补丁作用于实例 forward，不能据此认定 Transformers 类本身被全局替换，也不能认定不匹配的方法自动采用相同补丁。排查时记录实际 input_proj 类型、解包前后 quant_method 类型、实例 forward 绑定和保存的激活 dtype。

量化权重可能以整型或其他打包表示存储，其 dtype 不能直接作为输入激活的逻辑 dtype。这里保存 model_config.dtype，是为了让量化 Linear 自己处理激活量化；若上游 forward 仍将像素转换到 input_proj.weight.dtype，就可能在进入线性层前丢失小数和动态范围。

## 视觉 forward 的计算顺序

_ascend_gemma4_vision_patch_embedder_forward 先执行 `pixel_values=2*(pixel_values-.5)`，再转换到 _ascend_activation_dtype，然后送入 input_proj。position_embeddings 按原路径产生，并转换到 hidden_states.dtype 后相加。

因此必须分别观察原始像素、居中缩放结果、input_proj 输入 dtype、投影输出 dtype 和位置嵌入 dtype。先把浮点像素转成打包权重 dtype 再缩放，或在位置嵌入相加时无意扩大 dtype，均不是该实现的等价迁移。是否使用额外融合、特定 kernel 或达到怎样的数值误差，不能从这段 Python 包装直接推出。

本卡未完整阅读 AutoModel 具体类、recursive_replace_linear 递归实现和 MXFP4/MXFP8 Linear 的内部计算。这里闭合的是“构造何时替换—识别什么方法—实例如何绑定—传什么激活”的框架接入，不声称覆盖全部塔算子、权重量化算法或底层 Device 实现。

## PLE、双向视觉 attention 与继承路径

ple_dim 读取 text_config.hidden_size_per_layer_input；若其非 None 且为正，创建 per_layer_embeddings，形状为 `[max_num_batched_tokens,num_hidden_layers,ple_dim]` 的零缓冲，device 跟随语言模型的 embed_tokens，dtype 使用 model_dtype；否则相应状态为 None。迁移 PLE 时需保留 token 容量、层数、最后维度及所属 device，不能只创建同名属性。

_full_attn_layer_idxs 初始为空，仅在 use_bidirectional_attention=="vision" 且 layer_types 存在时收集 layer_type 不为 sliding_attention 的层下标。这是构造阶段为继承的视觉 attention 路径准备的状态，不等价于已经证明所有 attention 分支、图捕获或数值结果正确。把所有层都当 full attention，或按层号经验硬编码，会改变来源合同。

MoE 包装器显式转交 language_model 的 moe_layers、num_moe_layers、num_logical_experts、num_physical_experts、num_local_physical_experts、num_routed_experts、num_expert_groups、num_shared_experts 和 num_redundant_experts；这些是上层专家布局与负载均衡消费的元信息，不是重新构造一份专家权重或证明所有 EPLB 路径可用。_suppress_token_ids 从 try_get_generation_config() 返回配置的 suppress_tokens 取得，未提供配置时为 None。

由于该类重建父类初始化，升级 Native/Transformers 后应比较继承方法读取的字段集合。当前已显式保存的 LoRA、PLE、full-attention 下标、音频空值和 suppress_tokens 是接入检查点；不能将本卡当成未来父类新增字段的自动兼容承诺。

## 公开量化范围与性能判断

公开教程的 950 MXFP4 checkpoint 使用 EcoTech 量化描述，并要求 quantization=ascend；具体权重与启动选择由已有部署指南维护。MXFP8 方法出现在 isinstance 判定中，说明本补丁识别该方法类；它不提供每个 Gemma4 变体、每种硬件和音视频输入的独立支持矩阵。Experimental 标签、文档与代码的证据层级必须一并带入 Agent 的决策。

这段修改保证预期的输入路径与状态，源码本身没有给出可泛化的 TTFT、tokens/s、HBM、精度或图模式收益。性能比较应固定模型变体、权重、软件提交、硬件、视觉尺寸/帧数、并发和执行模式，并检查实际量化方法命中后再测；不能以 storage dtype 更小就推导整个视觉链路更快。

## 验证信号、回退与 Evidence

适配 Agent 可先做结构检查：对有/无音频配置、有/无 tower-connector LoRA、有/无 PLE，以及 vision 双向 attention 的配置分别核对模块和状态；确认视觉/音频递归替换及各 prefix 的权重归属。对匹配和不匹配的 quant_method 都检查实际 forward 绑定，避免把条件补丁变成全局假设。

在授权的模型验证环境中，用含小数像素的输入检查进入 input_proj 前的值和 dtype，比较位置嵌入相加前后 dtype，再对完整多模态输出做精度、eager/graph 和性能对照。需要回退时保留原 checkpoint、配置与方法类型，恢复经明确配对验证的模型/依赖组合；仅删除实例补丁可能恢复原先按打包权重 dtype 转换的风险，不能把“能启动”当作精度验收。

固定来源为 gemma4_mm.py 全文 179 行和模型注册表全文；硬件/公开量化边界来自 Gemma4 教程注明范围与支持表的 Gemma4 行。全部作为源码和文档数据阅读。本次没有执行上游导入、Transformers 构造、UT、权重加载、NPU、精度、编译或性能实验；未填写 verified 事件。Scope 只声明 framework=vllm，其余特征未知时继续保留未知。
