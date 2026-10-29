---
type: Optimization
title: vLLM MoE 权重预取：token 门控与部分权重比例（平台待核验）
description: 固定 vLLM Ascend 实现将专家权重预取接入路由与量化 MLP，按单次 forward token 数门控并使用部分权重比例；平台及具体阶段尚未确认，保留为草稿。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.data_movement
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/78777237a9ae95af88ce6068b000635f96aafe25/vllm_ascend/ops/weight_prefetch.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/78777237a9ae95af88ce6068b000635f96aafe25/vllm_ascend/ops/moe/experts_selector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/78777237a9ae95af88ce6068b000635f96aafe25/vllm_ascend/ops/moe/moe_mlp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/78777237a9ae95af88ce6068b000635f96aafe25/vllm_ascend/ascend_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/78777237a9ae95af88ce6068b000635f96aafe25/docs/source/user_guide/configuration/additional_config.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/pull/3203
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/78777237a9ae95af88ce6068b000635f96aafe25/vllm_ascend/worker/model_runner_v1.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/78777237a9ae95af88ce6068b000635f96aafe25/vllm_ascend/ascend_forward_context.py
  role: supporting
created_at: '2026-10-20T11:23:20Z'
updated_at: '2026-10-22T03:20:00Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      objective:
      - latency
      framework:
      - vllm
      model_features:
        all_of:
        - moe
---

# vLLM MoE 权重预取：token 门控与部分权重比例（平台待核验）

## 条件与规则入口

本案例补充[权重预取决策](../rules/decode_weight_prefetch_ordering.md)的另一种实施方式。固定版本为 vLLM Ascend 的 PR #3203 合并提交 `78777237a9ae95af88ce6068b000635f96aafe25`；PR 具名 Qwen3MoE，但本次没有核对完整模型调用图、硬件运行或独立收益。

原材料的 A2 声明在本次核对的 PR、配置文档和相关源码中尚未得到支持，因此 `platforms: []`、状态为 `draft`。不继承 LongCat 规则卡或其他案例的平台；Scope 只记录已核对的框架、MoE 和时延目标，不声明阶段或执行模式。

## 实施差异

- `select_experts` 在路由选择前调用 `maybe_prefetch_moe_weight_preprocess`；`quant_apply_mlp` 中调用对应 postprocess，然后进入专家矩阵乘路径。ModelRunner 会构造 WeightPrefetchMethod，并在执行及图捕获上下文中传入该对象和 model_instance；这补齐到框架入口的静态链路，但仍不是目标模型运行或收益验证。
- preprocess 通过 `hidden_states.shape[0] >= MOE_PREFETCH_TOKEN_THRESHOLD` 门控，本版本常量为 96；没有直接检查 `is_prefill`。这表示单次 forward token 数条件，不能将其等同于 batch 或据此声明“仅 Decode”。满足 token 门槛也不证明任一阶段均已支持或获益。
- 预取字节数按权重大小乘配置比例计算；本版本默认比例字典中的 MoE `gate_up` 为 0.8，attention 的 qkv/o 为 1.0。这是固定配置，不是通用最优比例或其他实现应采用的默认值。
- 权重定位使用 `model_instance.model.layers[layer_idx].mlp.experts.w13_weight`，preprocess 内推进 `layer_idx`。模块树和层号状态是该实现的前提；改变调用点、模块命名或 forward 生命周期时须重新核对。

## 配置与回退

配置入口为 `weight_prefetch_config`。固定实现的 `WeightPrefetchConfig.__init__` 与配置表均以 `enabled=False` 为缺省值；PR prose 另称默认开启，保留此冲突，不能用 PR prose 取代固定实现。需要启用或回退时显式填写 `enabled`，并核对实际加载结果。

`prefetch_ratio` 由配置字典整体替换，未做递归合并；只传某一模块时需核对其他模块的有效配置。本文不提供未经运行验证的启动配方。

## 观测、验证与剩余缺口

PR 只定性描述降低搬运等待，没有独立 benchmark 数字。已读取的相关单卡测试仅使用通用 `npu` 设备标识，且部分预取上下文被 mock；不能用测试文件存在或 PR 合入推导 A2 平台验证、预取收益或模型端到端正确性。

转为稳定卡前仍需固定平台与模型路径，检查完整调用链、token 门控、层号推进、预取发起/消费依赖及回退；在固定工作负载下比较精度和目标时延，记录 warmup、重复次数与波动。本次没有执行上游代码或测试，不新增 `verified`。

## Evidence

- [权重预取源码](https://github.com/vllm-project/vllm-ascend/blob/78777237a9ae95af88ce6068b000635f96aafe25/vllm_ascend/ops/weight_prefetch.py)：完整核对 `ModuleWeightPrefetchConfig`、`WeightPrefetchMethod`、token 门控、权重路径和状态推进。
- [专家选择源码](https://github.com/vllm-project/vllm-ascend/blob/78777237a9ae95af88ce6068b000635f96aafe25/vllm_ascend/ops/moe/experts_selector.py) 与 [专家 MLP 源码](https://github.com/vllm-project/vllm-ascend/blob/78777237a9ae95af88ce6068b000635f96aafe25/vllm_ascend/ops/moe/moe_mlp.py)：完整读取两个文件，核对 preprocess/postprocess 的静态调用位置。
- [配置源码](https://github.com/vllm-project/vllm-ascend/blob/78777237a9ae95af88ce6068b000635f96aafe25/vllm_ascend/ascend_config.py)：核对 `WeightPrefetchConfig` 的默认比例与 `enabled=False`、字典替换行为。
- [配置文档](https://github.com/vllm-project/vllm-ascend/blob/78777237a9ae95af88ce6068b000635f96aafe25/docs/source/user_guide/configuration/additional_config.md) 与 [PR #3203](https://github.com/vllm-project/vllm-ascend/pull/3203)：保留配置表与 PR prose 的默认值冲突，不把定性收益表述当作独立实验结果。

## 本轮来源核对与剩余缺口

ModelRunner 初始化预取对象，在两处 forward context 调用中传入对象及 self.model；context 从 model.start_layer 初始化 layer_idx，preprocess 再按层推进。若目标模型缺少这一属性或层级路径不兼容，不能视为已支持。

本版本配置源码与配置表都以 enabled=False 为默认，部署应以明确配置及实际生效值为准；PR 的“默认开启”措辞不作为运行默认值。没有确认仅 Decode，token>=96 仍只是单次 forward 的门控。单卡测试使用通用 NPU 且部分预取上下文被 mock，不足以绑定具体卡型或证明实际预取收益；保留 draft、未知平台及原有有限 Scope。
