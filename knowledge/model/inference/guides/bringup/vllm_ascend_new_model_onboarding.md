---
type: Guide
title: vLLM Ascend 新模型适配：架构注册、prefix、权重与分阶段验收
description: 对照中文历史指南与 vLLM v0.32.0，核对 embed_input_ids、Attention 导入、惰性注册、prefix 和权重/状态协议；注册、dummy、真实模型精度与性能分别验收。 补充 Qwen2.5 Omni 的 registry 别名、Thinker 与输入表分层实例。 补充 v0.32 CLI 预检：FlexibleArgumentParser、重复参数告警、JSON合并、ModelDType及服务模型名与权重路径。
  补充 Native API 模型与LoRA预检、准入、流式错误和请求身份的分阶段验收。
tags:
- task.implementation
- topic.model_serving
- topic.architecture
- topic.attention
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/installation/supported_hardware.inc.md
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/docs/contributing/model/basic.md
  role: primary
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/docs/contributing/model/registration.md
  role: supporting
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/docs/contributing/model/tests.md
  role: evidence
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/model_executor/models/registry.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.agents/skills/vllm-ascend-model-adapter/SKILL.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.agents/skills/vllm-ascend-model-adapter/references/workflow-checklist.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.agents/skills/vllm-ascend-model-adapter/references/multimodal-ep-aclgraph-lessons.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.agents/skills/vllm-ascend-model-adapter/references/deliverables.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/modeling/adding_a_new_model.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/docs/models/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/utils/argparse_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/engine/arg_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/config/model.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/entrypoints/openai/models/serving.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen-VL-Dense.md
  role: evidence
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/entrypoints/serve/engine/serving.py
  role: supporting
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/entrypoints/generate/base/serving.py
  role: supporting
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/entrypoints/openai/completion/serving.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/README.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/AGENTS.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/core/batch_job_aware_scheduler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/core/kv_cache_config_builder.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/core/kv_cache_interface.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/core/recompute_scheduler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/weight_transfer/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/weight_transfer/sparse_hccl_engine.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/platform/patch_balance_schedule.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/platform/patch_kv_cache_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/__init__.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_adaptive_verification.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_ascend_ops.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_attn_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_bind_kv_cache.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_block_table.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_deepseek_v2.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_dflash_speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_dspark.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_eagle_speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_idex_310.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_input_batch.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_mamba_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_model_state.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_qwen3_dflash.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_spec_decode_310.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_triton.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_use_v2_model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_uva.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_v1/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_v1/patch_cudagraph.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_v1/patch_eagle3_pp_aux.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_v1/patch_idex_310.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/patch/worker/patch_v1/patch_mamba_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_v2/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_v2/patch_triton.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/sample/penalties.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/sample/rejection_sampler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/block_table.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/spec_decode_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v1/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v1/spec_decode/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v1/spec_decode/dflash2_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v1/spec_decode/dflash_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v1/spec_decode/dspark_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v1/spec_decode/llm_base_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v1/spec_decode/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v2/aclgraph_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v2/attn_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v2/block_table.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v2/kv_connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v2/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v2/model_states/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v2/model_states/default.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v2/model_states/encoder_only.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v2/model_states/hybrid_encoder.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v2/model_states/mamba_hybrid.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v2/pcp_manager.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v2/sample/penalties.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v2/sample/rejection_greedy.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v2/spec_decode/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v2/spec_decode/dflash/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v2/spec_decode/dflash2/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v2/spec_decode/lilicorr/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v2/spec_decode/rejection_sampler_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v2/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/xlite/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/xlite/xlite.py
  role: implementation
created_at: '2026-10-29T08:40:49Z'
updated_at: '2026-11-04T02:56:11Z'
platforms:
- a2
- a3
- 310p
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 新模型适配：架构注册、prefix、权重与分阶段验收

## 适用范围与交付

适用于将新模型接入 vLLM `v0.32.0` / `5df63a7203cdb9328d824a27b682e77c7b9928be`，并核对 Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 插件路径。四类平台是待选择的目标环境，不表示本流程已经证明任意新模型在所有硬件上可用。交付实际架构映射、实现与权重/状态契约、正确性结果和未支持功能。

## 先按目标版本和失败阶段进入

开始前保存 Ascend 实际 commit、Native 实际 commit/版本、硬件完整型号、MRv1/MRv2、checkpoint 的 `architectures` 与目标任务。先用这些输入选择下表，再执行适配阶段；同名版本号或模型家族不能替代这组身份。

| 当前任务与版本 | 首个判断和下一步 |
| --- | --- |
| 在 ceac 固定基线接入新模型 | 从[模型识别](#先识别模型再决定复用粒度)、[进程注册](#注册必须在实际消费进程生效)和[模型/权重契约](#模型与权重契约)开始；保留本卡入口声明的 Native 身份。 |
| 把 ceac 适配推进到 Ascend 3164 | 先读[3164 的 patch、Worker 与状态迁移](#3164固定增量先迁移patch入口再验收worker与状态)，确认真实模块和最终 callee，再重走验证；旧导入可解析不足以证明迁移完成。 |
| 检查 Native v0.32.0 / 5df 的协议、CLI 或服务请求 | 分别进入[旧/新模型接口](#中文旧适配指南与-v032-接口)、[CLI 与模型身份](#适配前先确认实际cli与模型身份)及[API 准入/流式失败](#native-api模型预检准入与流式失败分阶段验收)。独立 Native 5df 与 Main 配对 Native 不混作同一 ABI。 |
| 已能构造，但真实权重、状态或首请求失败 | 按[分阶段验证](#分阶段验证)和[dummy/真实权重两道门](#dummy真实权重与首请求的独立证据)定位失败层；满足[停止与回退](#停止与回退)条件时先恢复最近通过阶段。 |

本卡后半部的历史 PO、Native 协议和 3164 增量用于不同目标；目标 revision 不在这些快照内时，先核对应接口与调用方，再复用相应步骤，不将一个快照的路径或删项套给另一个。

## 先识别模型，再决定复用粒度

保存权重与 config 版本，核对 `architectures`、任务类型、Attention、MoE、位置编码、滑窗、共享 KV、递归状态及多模态 processor。查上游 registry、Ascend 注册和模型实现：模型名称相似或同为 MoE 只提供候选，不能证明结构和量化系数可互换。

上游 basic model 指南建议从相近实现适配并复用符合契约的 Attention/MoE 等共享层。模型专属结构仍独立实现；迁移其他框架时，字段名和回调不是通用协议，缓存语义和精度要求需要重新映射。

## 注册必须在实际消费进程生效

内建实现由上游 registry 管理；树外模型通过通用插件调用 `ModelRegistry.register_model(architecture, model_cls)`。固定 Ascend 的 `ascend_model` entry point 调用 `models.register_model()`，使用 `module:class` 字符串惰性注册，并可覆盖已有同名架构。

上游注册 API 对架构字符串和类/导入路径作类型与格式检查；同名条目会替换原映射。先确认最终加载类，避免无意覆盖另一实现。惰性路径有助于推迟模型模块导入，但注册成功不能证明类可检查、设备可初始化或权重可加载。插件进程职责见[插件架构](../../concepts/frameworks/vllm_ascend.md)。

## 模型与权重契约

| 项目 | 需要实现或核对的内容 | 典型错误 |
| --- | --- | --- |
| 构造 | 使用目标版本的 `VllmConfig` 和 `prefix`，逐层传递完整模块路径 | Attention 重名，选择性量化匹配错误 |
| 输入 | basic forward 的 `input_ids/positions` 按 token 扁平组织；保留 `inputs_embeds` 和相应中间张量协议 | 直接沿用 HF 的 batch×max-sequence 假设 |
| 文本嵌入 | 按模型组合需求提供 `embed_input_ids` | 多模态组合找不到统一文本嵌入入口 |
| 并行层 | 选择符合原语义的并行 Linear、Embedding 和 LM head | 切分轴、归约或 KV head 复制错误 |
| 加载 | 实现 `load_weights`；合并 QKV/FFN 时按分片标识加载各原始矩阵 | 名称相同但分片、排列或 scale 对不上 |
| Attention/KV | 核对 mask、位置、元数据、布局、层名和缓存可见性 | 首 token 正确但变长或多轮错误 |
| 混合状态 | 区分追加式 KV 与原地更新的 Mamba-like 状态，选择对应协议和状态 shape/dtype | 用普通 KV 生命周期处理递归状态 |

`prefix` 同时用于运行时层身份与非均匀量化选择，不只是日志名称。上游指南针对 attention-free、hybrid 和自定义 Mamba-like 层列出不同协议、状态方法及后端登记点；不能只把模型名加进 registry 就认为这些状态已接入。

## 分阶段验证

以下是根据来源接口与测试职责组织的工程顺序，不是本次已执行的模型结果：

1. 固定[环境](../deployment/vllm_ascend_versioned_environment.md)、模型和期望任务；检查实际 Worker/Runner，先建立最小正确路径。
2. 验证模型构造与权重加载。dummy weights 可检查构造、算子/API与请求路径，不能替代真实权重的映射、scale、分片及质量验收。
3. 生成模型按任务比较 token/text 或 logprobs；pooling 按对应测试比较向量相似度。多模态分别比较文本/token 与原始/缓存媒体的处理一致性。
4. 覆盖实际任务需要的变长、多请求、多轮、缓存和停止边界；增加并行、量化、图和投机能力时，每次单独记录有效配置、精度、失败和回退。
5. 正确性通过后使用[基准指南](../optimization/vllm_ascend_benchmark_workflow.md)建立性能对照。

上游测试指南把模型初始化测试与可选正确性测试分开描述；Agent 的工程交付仍须明确实际完成了哪一层，不能只用前者声称后者通过。硬件/功能范围没有证据时保持待验证。

## 停止与回退

架构不可检查、权重漏载、prefix 冲突、缓存/状态不一致或精度未达约定时停止性能比较，回到最近通过的阶段。保留模型与环境快照、参考输出、错误输入和实际执行类。Runner 可能因功能回退，见[选择规则](../../optimizations/rules/vllm_ascend_model_runner_selection.md)。

## Evidence

上游 basic、registration 和 tests 文档分别提供模型协议、注册方法与验证职责；registry 源码核对惰性路径与覆盖行为；Ascend 注册文件提供实际 NPU 模型入口。本次未实现新模型、编译上游或运行精度测试。


## 注册名与维护状态的交叉检查

按[固定注册映射](../../concepts/frameworks/vllm_ascend.md)区分target、兼容别名和draft类，再查[模型支持裁决](../models/vllm_ascend_model_support_resolution.md)的任务/硬件行。存在29个映射不代表29个模型均在所有平台受支持；上游可复用模型也可能没有Ascend专属覆盖。


## 草稿模型也要有独立加载与状态契约

新增MTP/DSpark不止登记architecture。先核对[head真实归属与PP副本](../../runbooks/precision/vllm_ascend_mtp_head_ownership.md)、[logits/feedback最终norm](../../runbooks/precision/vllm_ascend_mtp_hidden_state_contract.md)，再按[Kimi MTP容器复用](../integration/vllm_ascend_kimi_mtp_adaptation.md)或[GLM MLA DSpark骨干替换](../integration/vllm_ascend_glm_mla_dspark_adapter.md)逐项映射。权重“每层有命中”、构造成功和mock测试都不能替代每个必需参数、实际K步状态与NPU输出验收。



## dummy、真实权重与首请求的独立证据

固定源模型适配workflow明确以A2/A3环境说明两阶段验收；其中固定工作目录、端口和128k+bs16是环境/容量候选，不能直接扩成950、310P或任意新框架的统一配置。可迁移的是以下证据结构：

| 阶段 | 必须实际执行并保存 | 仍不证明 |
|---|---|---|
| dummy fast gate | 构造/注册、算子与API路径、服务目录及首个文本请求；VL再加图文请求 | 真实参数键、scale配对、实际分片、质量和完整层数验收 |
| real-weight gate | 完整目标checkpoint与必需参数；文本/目标媒体实际请求；HTTP与输出、原始栈 | 仅此smoke还不证明长上下文、多请求状态或任务准确率达标 |
| 完整功能/质量 | 所需图/并行/草稿和媒体组合、完整层数、任务[精度口径](vllm_ascend_accuracy_evaluation_contract.md) | 一项成功不等于任意多项全开支持 |
| 性能 | 已通过正确性的同口径对照、真实负载和目标SLO | 小样本示例吞吐不是模型性能上限 |

启动成功但首请求崩溃按[假就绪排查](../../runbooks/runtime/vllm_ascend_first_request_false_ready.md)继续定位；不能交付为“模型已可用”。临时减层仅加速隔离，不移除ViT结构，最终仍需完整模型通过。

## 功能与容量的交付语义

ACLGraph、EP、FlashComm1、MTP、多模态分别保留有效配置、请求证据与失败原因。区分实际支持且已验证、框架明确不支持、checkpoint缺必需参数、不适用；尚未验证单独保留未知，不能填进前四种确定结论。EP在无专家模型上不适用；来源的MoE验证清单不替代[当前SP门控](../optimization/vllm_ascend_sequence_parallel_moe.md)。MTP需要同时核对config与真实weight index。

理论max_model_len取模型配置，实践上限取明确硬件、TP/EP、权重和模式下确实启动并服务过的最大条件；二者同时报告。源码中的128k+bs16及32/64并发扩展仅是候选，资源不足应记录边界，不能为达成示例数字删除guard。

对旧经验中的FP8/NPU、图稳定性或processor修法，优先与当前层方法和实际接口裁决。回退只证明所测配置，不能用禁图/禁媒体后的结果替代原目标功能。最终精度配置的参考值与实际测量分开，报告版本unknown、少样本或缺原始日志都要明示。


## 中文旧适配指南与 v0.32 接口

adding_a_new_model.po的55条业务译文已完整读取，同名英文不存在，按历史指南与当前原生basic/registration、Ascend注册和backend片段对照，不能恢复为当前英文API规范。旧文从相近模型复用、区分从零实现和覆盖实现的思路可保留；ModelForCausalLM/Model/DecoderLayer/Attention/MLP层级只是decoder-only参考，不强加给pooling、ASR、encoder-decoder或全部多模态模型。

旧必需表列get_input_embeddings；vLLM v0.32.0 basic页为文本组合嵌入给embed_input_ids，并保留扁平input_ids/positions、inputs_embeds与intermediate_tensors协议。不能机械保留旧表，也不能反推get_input_embeddings在所有类均已删除；按目标任务/模型protocol读真实实现。旧from vllm.attention import Attention与当前basic的vllm.model_executor.layers.attention不同，按固定版本路径核对，而不是凭旧import拼模块。

prefix要求针对模型内vLLM感知模块、attention身份和选择性量化，不表示所有原生torch.nn.Module构造都接prefix。每层传全路径、相同层不重名；同时验证真实weight键/merged QKV分片与scale，不能用prefix字符串相似推加载正确。

basic示意代码本身也不能当现成模板：其MyDecoderLayer调用MyAttention时只给prefix，而展示的MyAttention构造还需要vllm_config。应按真实实现补齐构造/形状参数并检查各层签名，本批没有实例化这些类。指南里的CPU/CUDA或Mamba custom-op登记要求也不能替代Ascend实际kernel/ACLGraph接入。

## 历史eager注册与当前惰性映射

旧PO让models/__init__.py相对导入实现类后register_model；当前Ascend以module:class字符串注册29个architecture映射。architecture取checkpoint config.architectures的精确标识，别名映射和target/draft分别核对；未出现Ascend专属映射也不单独证明原生模型不能复用。

原生register_model对已有项记录debug并覆盖，旧文所谓warning不是当前判据；旧vllm/models_executor/models/registry.py路径也应按实际model_executor校正。没有warning既不证明覆盖失败，也不证明加载成功，不默认改原生registry加日志来代替真实类/消费进程确认。惰性字符串的格式登记与后续inspect、import、load_weights、设备forward分开；格式检查不验证完整运行能力。

原生文档的CUDA/fork导入错误说明惰性注册的动机，不是本次NPU复现；Ascend平台、ascend_model入口与全局patch职责另见[插件架构](../../concepts/frameworks/vllm_ascend.md)。模型注册入口只登记模型，不自动承担所有connector/loader的patch初始化。

## Attention选路不是自动适配完成

当前NPUPlatform.get_attn_backend_cls先按配置/硬件选择类路径，再尝试解析。ImportError分支返回路径，留到后续使用暴露缺包，不等于backend依赖已导入。KV dtype只在类自身__dict__显式声明supported_kv_cache_dtypes时检查；未声明跳过不等于任意dtype都支持，继承的CUDA默认集不作此处判据。它也不是对selector全部配置轴的统一验证。

选择表中MLA/SFA/DSA与PCP路径仍可使用_v1命名模块，不据文件后缀判Model Runner代际。compatibility分支可回退普通310P attention路径，这不是新增MLA/SFA支持；需要独立确认模型cache布局/算子和硬件范围。basic页的基础attention概述同样不能代替此实际表或支持矩阵。旧PO“导入Attention即可路由”只能关闭入口线索，不能关闭metadata、dtype、图、CP与真实权重/输出验收。

旧文要求功能、精度、性能后更新支持文档，仍按本卡分阶段门槛实施；注册日志或仅dummy首请求不构成这些测试结果。本批未导入模型/patch、修改registry、运行上游测试或NPU。


## 实例：模型家族、registry键与输入表分开

固定Native v0.32.0的registry563–586和supported_models.md列明选段给出一个可复用例：Qwen2_5OmniModel、Qwen2_5OmniForConditionalGeneration两个architecture键都到qwen2_5_omni_thinker:Qwen2_5OmniThinkerForConditionalGeneration。文档在Text Generation列该Thinker和3B/7B checkpoint，Inputs为文本、图像、视频、音频的允许组合；E与多项上标只解释输入形式，不是音频输出、Talker或全部Ascend硬件支持声明。

读取模型config键、最终Python类、实际任务API和所需输入输出四层证据，避免由家族“自然语音流式响应”简介自动增加后端功能。LoRA/PP的Native表✅也不能移植成目标Ascend组合已验收；具体历史PO与未知项见[Qwen2.5模型证据](../models/vllm_ascend_qwen25_legacy_evidence.md)。本段只补注册/支持表解释实例，原通用适配流程和平台范围不变；未读取整个Native表/模型实现或运行任何模型。


## 适配前先确认实际CLI与模型身份

新模型任务把“预期的配置”与“目标版本实际接收的配置”分开。这里选读Native vLLM v0.32.0固定提交的 FlexibleArgumentParser、EngineArgs参数注册/kwargs、ModelConfig字段和OpenAIModelRegistry视图；不是这些大文件全部实现，也未导入或运行上游。用于检查部署配方能否进入后续构造/权重与数值阶段，不能用CLI通过替代它们。

### 下划线、重复参数与处理顺序

FlexibleArgumentParser.parse_args先处理serve位置模型与config，再将长选项第一个点号前的下划线归一成连字符；等号后的值保留。--max_model_len 与 --max-model-len因此不是两个独立容量开关。JSON点号后的key不能按同一规则随意改名，也不能把模型路径中的字符按选项名处理。

regular_args_seen跟踪普通长选项；重复时记录duplicates并输出“Found duplicate keys”告警，没有在这个分支拒绝请求或移除所有重复普通项。随后调用标准ArgumentParser。_compute_kwargs/get_kwargs给dtype、max_model_len生成标量type/default/choices，EngineArgs.add_cli_args分别注册--dtype和--max-model-len；ModelDType列auto、half、float16、bfloat16、float、float32，max_model_len是输入加输出总长字段。它们不是“重复名称就自动取更保守值”的合并算法。

静态工程推断：这些普通标量选项在所有参数有效、沿用标准store action时，后出现值覆盖同一namespace字段。本机Python3.12源码的 _StoreAction.__call__只对dest执行setattr，作为这个推断的辅助观察；没有实际运行vLLM CLI。因此把视觉教程的重复项交给v0.32相应路径，namespace阶段可能得到后面的bfloat16与32768，不能认为先写float16/16384就满足DUO约束；后续ModelConfig校验、硬件初始化和真实推理仍是不同阶段。该结论不回写成旧v0.11教程的已观测行为。

新适配交付规范化后的普通参数清单，冲突时先按来源/硬件/内存裁决，保留一项明确值；不依赖告警替Agent完成裁决。参数少写一个并不证明软件版本、API或设备已兼容。--config插入的优先级与JSON点号合并有自己的规则，不能泛化成任意输入都按最后一项直接覆盖。

### JSON、默认工厂与只读观察的边界

同一parse_args内的recursive_dict_update会递归合并字典、拼接列表，标量冲突记录覆盖key，再把点号参数合并成JSON追加到处理后的argv。列表元素的+形式、完整JSON项、点号项和普通标量是不同路径，不以普通--dtype的顺序推任意compilation/additional config最终值。

get_kwargs返回缓存计算结果的deepcopy，但_compute_kwargs为某些字段读取/调用default_factory，还可能构造config默认对象；“只是查看参数”不自动等于完全没有初始化。源码审阅读取声明与分支；在准备好的实际运行环境中再保存最终解析配置和日志，本次没有调用这些上游工厂、导入Torch/NPU或执行--help探针。

### 四种名称与模型目录

| 身份 | 在适配中的用途 | 不能替代 |
| --- | --- | --- |
| checkpoint repo/path与revision | 固定权重、tokenizer、processor、quant配置和分片。 | 服务API名称或最终模型实现类。 |
| config.architectures | 查模型执行器ModelRegistry的注册键与惰性类。 | 用户请求中的model字段。 |
| 最终Python实现类 | 核对协议、Attention/MoE/混合state及load_weights。 | 模型目录已加载成功或服务已接受请求。 |
| BaseModelPath.name/served name | API目录与模型名匹配视图。 | 权重文件路径、HF repo或架构字符串。 |

OpenAIModelRegistry是API侧base模型视图，与模型执行器的架构ModelRegistry不同。is_base_model按name精确比较；该registry的check_model对空名或已列base名返回None，其余返回NotFoundError/HTTP404。show_available_models中ModelCard.id取name、root取model_path；OpenAIServingModels沿用base视图并添加已知LoRA的目录项。不要由root或磁盘路径推id相同，也不要从允许空名的这一方法推完整API会接受所有缺名请求。

已读范围没有闭合Engine、renderer、动态LoRA解析和全部API调用链，因此这里只解释目录/registry检查，不声称任意endpoint的最终路由已证明。生成请求时读取实际/v1/models的id并匹配已配置服务，保存真实请求与响应；目录成功不证明checkpoint forward可用。

### Worked example：Qwen3-VL 配方进入验收前的裁决

固定Main Qwen-VL-Dense.md在DUO块重复dtype和context，950块的权重ID/量化flag与表不一致，服务qwen3vl与请求HF模型名不同。先展开设备、端口、DP/TP位置参数，确认唯一FP16与明确上下文预算，检查真实量化产物，再核对API id；参见[Qwen3-VL输入与容量](../models/vllm_ascend_qwen3_vl_input_and_memory.md)。这是由文档和已读Native分支组织的静态预检实例，未修补上游、启动服务或证明更正后命令可执行。

形成实际参数、最终实现类和checkpoint证据后，回本卡原有dummy/real-weight/精度/功能/性能分阶段验收。配置告警、模型目录、注册成功、短文本或只图像的回退，都不能替代原目标视频、量化、图、投机与目标SLO。


## Native API：模型预检、准入与流式失败分阶段验收

以下补充固定 vLLM v0.32.0 的 BaseServing 与 GenerateBaseServing 两文件全文，以及 Completion 入口 1–158、445–655 行；没有运行上游模块、服务或 NPU。源码说明控制流程，不证明任一昇腾硬件或新模型已完成端到端适配。上一节的 API 模型视图还需结合实际请求检查。

### 模型名、LoRA 与默认多模态适配器

`_check_model` 先按 `_is_model_supported` 判断：空模型名直接接受，`VLLM_SKIP_MODEL_NAME_VALIDATION` 开启也会跳过名字检查，否则查 base model；随后接受已加载的 LoRA 名称。`VLLM_ALLOW_RUNTIME_LORA_UPDATING` 开启且模型名非空时还可能调用 `resolve_lora` 加载适配器，成功返回 LoRARequest 才接受。解析器返回的 400 ErrorResponse 保留；其他失败可形成含 `Valid aliases` 的 404。此函数还可能记录请求体，不能作为没有副作用的字典查询探针。开关绕过名字检查也不证明权重、架构或推理可用。

`_maybe_get_adapters` 优先选显式请求的已加载 LoRA。只有调用方允许 `supports_default_mm_loras` 时才尝试默认多模态 LoRA：从 messages 的内容 type 取下划线前缀，例如 audio_url 对应 audio，再与已加载 LoRA 名称匹配；恰好一个匹配才采用，多个匹配不自动合并。BaseServing 注释仍限定当前默认支持的调用场景；不能据此宣称 Completion、Chat 和 Responses 全部等价。

### Completion 的校验顺序与流式成功信号

`render_completion_request` 顺序是模型检查、`_preflight(request.n or 1)`、OnlineRenderer。`_preflight` 先检查 engine.errored 并抛出 dead_error，再执行 `check_admission(n)`，用于响应开始前的健康和容量准入。`_create_completion` 会先拒绝 stream 与 beam search 的组合；通过 render 后才形成 cmpl 前缀 request ID。Renderer 和后续完整生成循环未在本节闭合，不能把预检通过当首 token、正确输出或性能达标。

HTTP 200 流式连接建立后仍可能发生生成错误。已读 Completion 尾部会将 GenerationError 或其他异常转成 SSE 错误，再发送 `[DONE]`；所以 `[DONE]` 也须与错误事件、finish_reason、choices 和 usage 一起核对。`_raise_if_error` 对 finish_reason 为 error 抛出 GenerationError。可选 system_fingerprint 在启动时计算，失败置空；普通流式块不逐块附加，末尾 usage 块可携带，缺失不能单独判定适配失败。

### 请求身份、路由字段与输出诊断

`_base_request_id` 优先采用 `X-Request-Id`，包括空字符串（判断为 is not None），否则采用传入默认值或随机 UUID。`X-Vllm-Priority` 可解析为整数时覆盖 request.priority，解析失败回退请求值。session_id 优先请求体，其次非空 `X-Session-ID`，最后 vllm_xargs 内的非空字符串。`X-data-parallel-rank` 在此只做 int 解析，负数也能被解析；合法 rank 范围及真正路由还需下游证据。trace headers 只有检测到时才提取，日志中有字段不等于远端执行完成。

排查 tokenizer 输出时，`_get_decoded_token` 可返回 token_id 占位符，或优先用已有 decoded_token，最后才用 tokenizer；跳过 tokenizer 初始化但又需要 fallback 会报错。`decode_token_ids` 按请求顺序处理且保留重复 ID，无词表项返回空字符串及 None 字节并告警；已知 token 的 UTF-8 编码采用 replacement。`clamp_prompt_logprobs` 原地把负无穷改为 -9999，不是对 NaN、正无穷或全部越界概率的通用修复。

验收记录应分别保留：实际 API 模型名/LoRA 开关和加载状态、预检/准入错误、renderer 结果、首 token 与完整流、结束原因、真实 token 及质量。按[基准指标边界](../optimization/vllm_ascend_benchmark_workflow.md)解释服务端时间；有远端 prefill 时另查[PD 拒绝清理](../integration/vllm_ascend_pd_transfer_lifecycle.md)，不要将通知调用当设备释放证明。


## MRv2 上游追版的维护检查点

固定 Main 的 worker/v2/README.md 共65行，把MRv2标为实验开发状态并列出与Native的维护差异。以下是该快照声明的追版线索，不能把勾选状态当作任意模型、硬件或功能组合的验收表，也不能用文档中的旧位置替代当前调用链确认。本节只全文读取该README，不声称重新闭合它链接的所有实现。

| Native变更触发点 | Ascend侧需要重新确认的边界 |
| --- | --- |
| execute_model、sample_tokens及postprocess_sampled协议变化 | runtime_guard装饰器的step/sample同步与统计stash；README将runner函数体与decorator职责分开，不能只更新函数签名。 |
| MLA位置或输入准备变化 | set_cos_and_sin/update_cos_sin由谁生产与更新，真实模型能否内部承担；没有内部闭合前不删除Runner处理。 |
| KV descriptor、分配和reshape变化 | 连续K/V视图、PD的2MiB对齐以及真实connector要求；单独核对布局与生命周期，而非用分配成功替代传输正确。 |
| FULL图capture及FIA workspace变化 | 每个图的显式workspace持有/释放，以及weak_ref_workspaces相关后处理；文档声明的释放时机需在实际版本确认。 |
| Model/AR图管理器构造变化 | 是否仍能取得runner/speculator input_buffers及model_state.attn_metadata；对象构造成功不证明更新了真实图地址。 |
| extract_hidden_states及共享hybrid KV布局变化 | 文档标记复用Native speculator，但HiddenStateCacheSpec保留每层私有单Tensor分配/reshape，不覆盖Attention/Mamba共享存储；勾选不意味着可合并这两种存储。 |

这些检查点用于决定下一步读哪条实现和需要补哪些真实回归。按本卡原有dummy、真实权重、状态/图/并行、精度与性能阶段逐项留下证据；没有运行目标版本或设备时继续记录未知。采样的有效输出另见[拒绝验证与重采样](../integration/vllm_ascend_mrv2_rejection_resampling_contract.md)，AR草稿与图生命周期见[草稿包装器](../integration/vllm_ascend_ar_draft_wrapper_lifecycle.md)。


## 上游工程约定中可复用的适配检查点

固定Main AGENTS.md249行作为来源数据读取，不将其中命令或发布流程当成本次Agent权限。新增能力先复用上游扩展点；确需patch时记录原符号、platform/worker消费进程、最小变更理由与移除计划。MRv1、310P与MRv2路径分别核对，继承/组合Runner也可承载适配，不能为省事复制整套调度。

新增环境变量应集中在env_variables入口，声明默认值、取值范围与敏感性；导入时机仅在循环依赖、worker隔离或类型检查等有实际理由时延迟。可变全局注册/缓存要记录所有者、并发和模型生命周期；全局dict已有条目不是当前实例已生效的证明。

性能审查特别关注NPU tensor.item等device→Host同步：异步scheduler可能因此被Host读取阻塞。优先确认能否在device完成或将同步集中到必要边界，再用真实profile验证；删除同步而未保留依赖/正确性也不能作为优化。文档与面向用户的功能变更同步补技术说明，发布fragment/CI存在仅表示工程证据，不代替本卡dummy、真实权重、精度和性能分阶段验收。


## 3164固定增量：先迁移patch入口，再验收worker与状态

本节固定Main `3164adc8fe75892fbf7f99f524bb72fddf1e6efd` 的worker/runtime变更。保留前文ceac与独立Native5df的版本身份，不能将此节当paired Native全部ABI已验证。通过完整语义AST差异、同AST函数复用、注释及必要原始diff阅读提取变更；不是所有目标文件raw FULL，更未导入/执行上游、Triton、编译、NPU或Agent。

### patch路径、装载次序与代际

原patch_v2的MRv2公共入口移到worker根；Cudagraph和Eagle3 PP aux等V1专属patch进入patch_v1。Mamba state-copy、preprocess和layerwise copy覆盖也迁到V1子包；根patch_mamba_utils保留_TEMPORAL_TILES及实际共享postprocess职责。多处R100是字节相同的搬迁，不当作新的算子语义。删除空patch_v2/__init__不删除其已迁出的功能。

worker在HAS_TRITON分支先导入patch_ascend_ops，再patch_triton：前者放非Triton的AscendC causal-conv、NPU Q/K RMSNorm与torch mHC覆盖，后者可以再次覆盖conv update并安装MRv2采样/grammar/logprob接口。旧“非Triton实现就不依赖此导入gate”的推断不成立，需记录实际HAS_TRITON、profile和最终callee。V1的310P proposer方法替换另放patch_v1/patch_idex_310，共享IDEX入口不再顺手改V1 proposer。

KV bind的实现继续共享，但rebind由patch_attn_utils统一装到gpu.attn_utils及v1.worker.utils；只改定义文件不保证所有已按名捕获的引用生效。ModelWithContext移除若干显式转发方法，沿__getattr__委托；310P旧embed_input_ids补丁随之删除。模块路径、Python属性存在与最终消费者可达性是不同证据。

### 初始化、encoder与KV几何

MRv1将sampling/drafter、模型加载、Attention backend/builder/cache准备包进jit_warmup_registry.activate窗口；部分仅用__new__的对象缺registry时，专门load窗口可no-op。MRv1/V2不再调用旧early_kernel_warmup start/join，NZ线程仍保留。它只说明收集/调用生命周期变化，不能断言JIT已经执行或预热收益。

MRv2 state resolver先尊重模型自定义get_model_state_cls，再按hybrid、硬件、CrossAttention和ENCODER_ONLY分类；enable_prompt_embeds需所选class声明支持。新增EncoderOnly state用非causal PrefillNoCache metadata，不依赖普通KV group；hybrid encoder组合Mamba state与encoder metadata，仍显式不支持prompt embeddings和DBO。源码中的FULL分支不推翻该类说明的pooling PIECEWISE边界，需实际调用配置验收。

Mamba每层state类型数量改从该层spec.mamba_type对应copy funcs取得，不假定同模型所有层相同。RecomputeScheduler兼容4/5项encoder调度返回值，保留新增duplicate input引用，优先委托父类分配；旧接口回退才逐input allocate并更新EC connector。BatchJob队列移除先前peek对象时清_peeked，BalanceScheduler改用KV manager统一record_prefix_cache_stats，不能把统计更新当请求已执行。

Qwen4 cache planner接入group/内存/每块字节分支，Eagle标记只匹配真实MTP层，缺该组显式报错，避免把target Mamba组全当draft。MRv2 allocator对shared-slot descriptor验证offset、layer_stride、block_stride、大小和完整spec覆盖；Qwen4依role共享slab或给PLE/HIDDEN独立存储，QSA main/raw/compressed与GDN state分别reshape。具体模型区域与状态见[Qwen4缓存所有权](../integration/vllm_ascend_qwen4_exp_cache_ownership.md)，不能从pool字节相同推普通Attention view兼容。

descriptor-native Attention与Mamba共同出现时，只按必要Mamba页宽调整Attention，不再无条件把全部组抬成同一最大页。QSA metadata的CPU query_start_loc按实际请求裁剪；zeroer排除offload top-k scratch组件。Mamba connector新增finalize_step委托；PCP manager bind_config还重新与实际is_decode_sharded合取旧flag，不能只把配置对象赋值视作decode分片生效。

### 草稿、采样与权重传输

LiLiCorr只接MRv2；MRv1明确NotImplemented。MRv2复用上游LiLiCorr scoring和Ascend DFlash2 runtime guard，拒绝fine-grained及PCP×TP的target embedding/candidate LM head分片，普通TP是来源声明而非本次验证。DFlash2 selector使用上游稳定log1p(-u) helper和draft noise salt，不再用普通log(1-u)替代；仍拒绝非eager图。

DFlash context KV允许fused投影或逐层QKV投影；RoPE消费返回的key，key-only避免复制整个value替身，存在v_scale时再缩放value。mask_embedding缺失仅吞ModelScope特定NotExistError，其余错误保留。MRv1 MTP topk compact删去旧DSA-CP gather分支，直接委托模型及LIM compactor，不能继续传旧num_input_tokens/tp_group签名。

MRv2 rejection新增可选entropy verify：None时取Ascend typed配置，拒绝与upstream block verification组合，synthetic rates使entropy关闭，posterior threshold/alpha有独立范围校验；alpha>0才分配entropy partials。随机数下界复用_TL_RAND_MIN，resample仍接原拒绝结果。MRv1调用新的包装入口传显式grid和参数名，不能把重命名当数值等价已测。

penalty bincount改为按request×token tile持久分工：prompt先写每token byte flag，再打包32-bit mask，output token计数仍atomic add；零request直接返回。临时flag按expanded token行分配，最终mask按req_state_idx写回。输入token范围、重复expanded映射与图分配仍应验证，不据源码声称UB/性能问题已消失。

Sparse HCCL注册独立sparse_hccl key，复用上游sparse transport并拒绝PP、EPLB、量化或非ND权重。对实际AscendUnquantizedFusedMoEMethod暂时转置w13/w2参数.data供checkpoint loader看见，finally恢复原view，但已经写入的值不会回滚。trainer过滤空patch、用CUDA-wrapper适配父类调用并在实际NPU可用时同步发送；两端初始化/退出仍需真实测试。XLite新增Glm4MoeLite架构候选，静态量化按真实input_scale而非deq_scale列表是否非空判断，dummy以空Tensor或占位data_ptr辨别，不把占位误当实际scale。

每项迁移先保存实际模块、对象身份、callee、descriptor/state/view及失败阶段，再按本卡原dummy/真实权重/状态/质量/性能分阶段验收。旧导入能解析、patch被注册、图构造成功和源码中支持字样都不等同目标配置通过。
