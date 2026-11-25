---
{
  "type": "Runbook",
  "title": "DiT W8A8 动态量化在 NPU Profile 中的核查链路：三层算子名映射与\"量化算子占比极小\"的配置归因",
  "description": "Ascend NPU 上对视频 DiT 模型做选择性 W8A8 量化（权重离线 INT8 + 激活 per-token 动态量化）后，用 CANN Profiler（`op_statistic.csv` / `operator_details.csv`）确认量化是否真正生效、并解释\"量化相关算子占比极小\"时适用。",
  "tags": [
    "task.debugging",
    "topic.precision"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-20T14:17:04Z",
  "platforms": []
}
---

# DiT W8A8 动态量化在 NPU Profile 中的核查链路：三层算子名映射与"量化算子占比极小"的配置归因

## 适用场景

Ascend NPU 上对视频 DiT 模型做选择性 W8A8 量化（权重离线 INT8 + 激活 per-token 动态量化）后，用 CANN Profiler（`op_statistic.csv` / `operator_details.csv`）确认量化是否真正生效、并解释"量化相关算子占比极小"时适用。本例为 cann-recipes-infer davinci DiT int8 转换产物（`selected-targets.json` 选 10 层 / ignore 150 层）加 `int8_config.json`（w8a8/dynamic/per_channel/per_token/symmetric）的单次 dit_forward profile。

## 触发与观测

- 触发（source 0 seq 42/76，用户问题）：INT8 profile 中"量化的算子占比这么少"，怀疑量化未生效。
- 配置观测一（source 0 seq 106，int8_config.json 逐字）：`"quantization_config": {"enabled": true, "mode": "w8a8", "activation_method": "dynamic", "weight_granularity": "per_channel", "activation_granularity": "per_token", "symmetric": true, ...}`，`ignored_layers` 为长列表。
- 配置观测二（source 0 seq 115）：`selected-targets.json targets 10 ignore 150`（alpha 0.7、branch_gate [0.024, 0.997]），目标层集中在 `block.layers.*.attention.linear_proj/linear_qkv` 与少量 `mlp.up_gate_proj`。
- 统计观测（source 0 seq 108，op_statistic.csv 逐字）：MatMulV3 以两种 Core Type 出现——AI_CORE 115 次 268025.014us 占 43.674%、MIX_AIC 36 次 102010.019us 占 16.622%；FusedInferAttentionScore MIX_AIC 15.391%；量化侧仅 `QuantBatchMatmulV3` MIX_AIC 18 次 6259.185us 占 1.02%、`DynamicQuant` AI_VECTOR_CORE 18 次 773.495us 占 0.126%。

## 探针与操作

```
cat acceptance/work-*/derived10/selected-targets.json | head -80
cat acceptance/work-*/int8_config.json | sed -n '/quantization_config/,$p' | head -80
head -8 acceptance/work-*/profile-int8/dit_forward_profile/*/ASCEND_PROFILER_OUTPUT/op_statistic.csv
rg -i -n 'quant|matmul|dynamic' .../ASCEND_PROFILER_OUTPUT/{op_statistic.csv,operator_details.csv,kernel_details.csv}
```

## 机制与判别

- 名称三层映射（source 0 seq 108/148，operator_details.csv 逐字记录）：框架调用层 `npu::npu_dynamic_quant`（含 Input Shapes 如 `"3584,5120;"`）→ ACLNN 层 `aclnnDynamicQuantV2`（device total 67.5015us）→ 统计层 `DynamicQuant`；`npu::npu_quant_matmul` → `aclnnQuantMatmulV5`（3584×5120 一次 621.772us）→ 统计层 `QuantBatchMatmulV3`。非量化的 `aten::matmul` → `aclnnMatmul`。即"算子名是否带 Quant"要看统计层命名，量化 matmul 显示为 QuantBatchMatmulV3 而非 MatMulV3。
- 占比归因（判别）：量化算子占比小 ≠ 未生效。本次仅 10/160 个线性层被量化（选择性量化），且 DynamicQuant 本身是轻量 vector-core 算子（avg 42.972us/call）；真正的大头仍是未量化层的 MatMulV3（AI_CORE+MIX_AIC 合计约 60%）。生效证据链 = 配置（activation_method: dynamic）+ 算子执行记录（DynamicQuant 18 次与 QuantBatchMatmulV3 18 次成对出现，且 shape 与目标层 3584/126/95×5120 对应）。

## 验证信号

- 全部为对本次 profile/配置产物的工具读取（tool_observed，CSV/JSON 逐字行）；未做 BF16 vs INT8 的同 workload 端到端或单算子耗时对比（无 performance_comparison）。

## 适用与失效边界

- 名称映射与"配置→算子记录"核查法适用于 torch_npu 动态量化 + CANN Profiler 场景；`aclnnDynamicQuantV2/aclnnQuantMatmulV5` 的具体版本号随 CANN 演进可能变化，使用时应以 operator_details.csv 实际记录为准。
- "占比小属正常"的结论依赖选择性量化配置（10/160 层）；全量量化模型中 DynamicQuant/Quant matmul 次数应与被量化线性层数一致，占比形态不同。
- 本轨迹未量化端到端收益；INT8 与 BF16 的 op_statistic 对比方法（调用次数一致、总耗时下降、generation_seconds 是否改善）在会话中仅为指导性建议，无实测数据支撑。

## 附：断言存档

- 选择性 W8A8 动态量化（权重 per_channel INT8 + 激活 per_token dynamic，int8_config.json enabled:true/mode:w8a8/activation_method:dynamic/symmetric:true；selected-targets.json 仅选 10 层、ignore 150 层，目标集中在 block.layers.*.attention.linear_proj/linear_qkv）的 DiT 推理 profile 中量化算子占比极小（DynamicQuant 18 次 773.495us 占 0.126%、QuantBatchMatmulV3 18 次 6259.185us 占 1.02%）是配置使然而非未生效：大头仍是未量化层的 MatMulV3（AI_CORE 115 次 268025.014us 占 43.674% + MIX_AIC 36 次 102010.019us 占 16.622%）。生效证据链 = 配置 activation_method:dynamic + operator_details.csv 中 npu::npu_dynamic_quant→aclnnDynamicQuantV2、npu::npu_quant_matmul→aclnnQuantMatmulV5 记录成对出现（统计层分别汇总为 DynamicQuant / QuantBatchMatmulV3，量化 matmul 不显示为 MatMulV3），且 shape（3584/126/95 × 5120）与目标层对应。

```text
"quantization_config": {
    "enabled": true,
    "mode": "w8a8",
    "activation_method": "dynamic",
    "weight_granularity": "per_channel",
    "activation_granularity": "per_token",
    "symmetric": true,
```
