---
type: Guide
title: CANN Executor 模型接入：注册、ForwardMetaData 与加载钩子
description: 新模型接入 Executor：注册与加载钩子、ForwardMetaData、变长 batch 的 packed logits、Prefill 每请求最后一个 token、缓存声明和 YAML 配置。
tags:
- task.implementation
- topic.model_adaptation
- topic.kv_cache
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/design/executor_design.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/forward_metadata.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/scripts/function.sh
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-migrator/references/framework_templates.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-runtime-debug/SKILL.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-quantization/SKILL.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/configuration_longcat_flash.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/support_models.py
  role: supporting
created_at: '2026-11-09T09:23:44Z'
updated_at: '2026-11-10T01:26:11Z'
platforms:
- agnostic
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - cann_executor
aliases:
- packed logits
- 变长 batch logits
- Prefill 末 token
---

# CANN Executor 模型接入：注册、ForwardMetaData 与加载钩子

## 适用范围与入口

适用于固定版本 Recipes 的统一 Executor 扩展。先按注意力、MoE、量化和 MTP 结构选参考实现：标准 Dense 看 models/qwen，标准 MoE 看 models/qwen3_moe，MLA+MoE 看 models/deepseek_r1。参考模型已经优化过，不能把它的所有特性当成最小接入条件。

模型通过 executor/core/support_models.py 的注册入口解析；构造器接收 config、infer_config、comm_manager（模型可另带 prefix）。实现 forward(input_ids, position_ids, forward_metadata, **kwargs)、load_weights(weights)，需要加载后处理时实现 process_weights_after_loading；check_model_settings 用于模型自己的可行性检查。ModelWorker 只在方法存在时委托后处理，不会自动遍历新模型的所有量化模块。

## 输入、缓存与输出

input_ids 是 packed [TotalTokens]，不是固定 [B,S]。ForwardMetaData 的 is_prefill 表示阶段；actual_seq_lengths_q/kv 是逐请求长度，actual_seq_lengths_cu_q/kv 是累计边界，另有 list 版本供具体算子使用。slot_mapping 与 block_table 按缓存分组键取值；attention_mask 是否传入由具体 attention 路径决定，不能全局规定 Decode 必须为空。

Prefill 选择每请求最后一个有效 token 的 logits，常规输出 [B,1,V]；Decode 输出 [B,q_len,V]，投机验证不一定 q_len=1。模型通过 get_cache_info 声明 CacheEntry，由管理器分配和绑定；无声明的回退路径需核对 init_cache(device)，不要把旧模板 cache_unit 当成当前统一契约。CP、混合缓存和多模态另读各自契约，视觉 embedding 由模型参数透传，不塞入 ForwardMetaData。

## HF Config 与建模接口兼容

自定义 Config 先保留 checkpoint 的字段语义，再处理运行代码要求的属性。rope_parameters 为 None 时，不应直接下标；是否能由 rope_theta 和默认 rope_type 构造，取决于模型原定义，不能给所有 YaRN/动态 scaling 模型硬套默认值。auto_map 指向上游模型代码时，统一注册入口应解析到已适配的 Config/模型类，避免意外导入原始 modeling。

多模态模型应区分 embedding 的 vocab_size 与 lm_head 使用的 text_vocab_plus_multimodal_special_token_size；dual/multi-sublayer 模型还要区分物理层数、Attention 子层数和 num_hidden_layers 的实际含义，不能机械除2或改配置以绕过 shape 错误。当前 LongCat 的层组织以其配置类与建模循环核对。

权重加载入口若访问 _keys_to_ignore_on_load_unexpected 等 HF 属性，先检查自定义基类、Transformers 版本及加载协议。缺属性、缺权重、合法忽略键是不同问题，不用扩大忽略列表掩盖实际漏加载。

## 配置与验证

model_name/model_path/exe_mode 属于 model_config；world_size 与各 TP 度属于 parallel_config；batch_size、max_new_tokens、block_size 属于 scheduler_config。当前配置还包括 data_config、disagg_config 和 speculative_config，并非旧模板所说固定四或五组。模型专属开关放 model_config.custom_params。

统一启动入口为 bash executor/scripts/infer.sh --model <注册名> --yaml <配置名>。启动器先检查模型自己的 infer.py，再回退 executor/offline/infer.py；无需为统一部署额外复制推理循环。

先验证实际权重完整加载与后处理，再跑 eager 的不等长多请求、Prefill→Decode、EOS 和缓存释放。比较逐请求执行与 packed 执行，确认末 token 和位置一致。随机权重跑通不能验收生成精度；单卡显存不足只能记录需多卡验证，不能记为已跑通。

## 相关知识

- [执行器机制](../../concepts/frameworks/cann_executor.md)
- [Packed Sequence 请求边界](../../concepts/techniques/packed_sequence_metadata.md)
- [模型导入遮蔽](../../runbooks/runtime/model_package_namespace_shadowing.md)
- [加载后处理未触发](../../runbooks/runtime/moe_post_load_hook_missing.md)

## Evidence

- [docs/design/executor_design.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/design/executor_design.md)
- [executor/core/model_worker/model_worker.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py)
- [executor/utils/forward_metadata.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/forward_metadata.py)
- [executor/scripts/function.sh](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/scripts/function.sh)
- [.agents/skills/model-infer-migrator/references/framework_templates.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-migrator/references/framework_templates.md)

- [.agents/skills/model-infer-runtime-debug/SKILL.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-runtime-debug/SKILL.md)（supporting）

- [.agents/skills/model-infer-quantization/SKILL.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-quantization/SKILL.md)（supporting）

- [models/longcat_flash/models/configuration_longcat_flash.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/configuration_longcat_flash.py)（supporting）

- [executor/core/support_models.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/support_models.py)（supporting）
