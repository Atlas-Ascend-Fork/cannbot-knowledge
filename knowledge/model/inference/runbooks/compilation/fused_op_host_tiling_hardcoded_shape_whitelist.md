---
type: Runbook
title: 昇腾融合算子 host-tiling 的硬编码 shape 白名单 / 必填输入契约拦截新结构模型 bringup
description: 昇腾融合算子 host-tiling 的硬编码 shape 白名单 / 必填输入契约拦截新结构模型 bringup。把一个结构参数（head-num / query 压缩维 / 专家数 / head-dim）与已支持模型不同的新模型接到昇腾现成融合算子上时，若算子在 host 侧 tiling 校验阶段直接报错、或某维度被拒，先怀疑算子把某个 shape 硬编码进了白名单/断言，而不是你的建模文件写错。这类拦截的正确处置是改算子侧放开白名单 / 补泛化，而非改模型 config 迁就算子。
tags:
- task.debugging
- topic.attention
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/118
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/127
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/71
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/359
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/167
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 昇腾融合算子 host-tiling 的硬编码 shape 白名单 / 必填输入契约拦截新结构模型 bringup

## 适用场景

把一个**结构参数（head-num / query 压缩维 / 专家数 / head-dim）与已支持模型不同**的新模型接到昇腾现成融合算子上时，若算子在 host 侧 tiling 校验阶段直接报错、或某维度被拒，先怀疑**算子把某个 shape 硬编码进了白名单/断言**，而不是你的建模文件写错。这类拦截的正确处置是**改算子侧放开白名单 / 补泛化，而非改模型 config 迁就算子**。

## 问题信号（对号入座）

- **MLA prolog**：`mla_prolog`（MLA_PROLOG_V3）host tiling 硬编码只接受 Hcq（压缩 query 维 / `q_lora_rank`）=1536（DeepSeek 系值）；Hcq 不同的 MLA 模型（如 GLM-5 = 2048）被拦下报 `Hcq allows only 1536, got 2048`。
- **Lightning Indexer**：`lightning_indexer` 算子专化到 indexer query head-num（N1）=64，不支持其它 head-num；N1≠64 的 DSA 类模型无法直接复用。
- **MoE 门控**：CANN 的 `aclnnMoeGatingTopK`（`torch_npu.npu_moe_gating_top_k`）在旧版本把路由专家数上限写死 256，超 256 专家的 MoE（如 Kimi-K2-Thinking 的 384 专家）在 tiling 阶段直接失败。
- **线性注意力 CP 核**：ZECO CP GatedDeltaNet 核硬编码 head_dim K=128（`assert K==128`，BK=BV=128），`chunk_gated_delta_rule_npu` 一旦传入 `cp_group` 就走 ZECO 路径，K≠128 直接命中 assert 崩溃、无回退。
- **必填输入契约**：`lightning_indexer` 在 key layout=PA_BSND 时，tiling 解析会强校验 `block_table` 与 `actual_seq_lengths_key` 非空、且 `block_table` dtype=int32，任一不满足即 `GRAPH_FAILED` 并打 `OPS_LOG_E`。

## 根因

昇腾融合算子把 host tiling 做成「按已知模型的固定 shape 特化」以简化 kernel 分支——特化点表现为**硬编码常量白名单 / assert / 必填输入约束**。它们不是技术本身的限制，而是**该参考实现只覆盖了标定过的那组 shape**。新结构模型的维度落在白名单外时被 host 校验挡下，报错常在 tiling/prepare 阶段而非 kernel 计算阶段。

## 修法 / 手段

- **在算子侧放开约束**：把硬编码常量改成从入参/config 读取并做泛化适配（如 mla_prolog 放开 Hcq 白名单、lightning_indexer 放开 N1 head-num 拦截并适配 N1 泛化点），而不是改建模文件去凑那个常量。
- **专家数超上限**：升级到已放开专家上限的 CANN 版本，或换用支持大专家数的门控算子路径。
- **CP 核 head_dim**：给非 128 head_dim 的混合注意力模型上 CP 前，**先确认核的 head_dim 约束**（ZECO=128）；不满足则不要传 `cp_group`（回落非 CP 路径）或改核适配。
- **必填输入契约**：走 PA_BSND 的 LI 调用必须备齐 `block_table`（int32）与 `actual_seq_lengths_key`。

## 风险 / 边界

- 放开白名单后须重新验证精度/性能（特化常量往往对应过 tiling 调优）。
- 上面各常量是各自参考实现在其钉定版本的值，可能随版本演进；迁移前以目标 commit 的算子源为准。

## 相关经验

- ZECO CP GDN 的完整机制与约束见 [qwen3-next-gdn-context-parallel-zeco](../../guides/experience/interventions/qwen3_next_gdn_context_parallel_zeco.md)。
- FIA 的 `actual_seq_lengths_kv` 类型随后端不同（另一类算子输入契约）见 [fia-actual-seq-lengths-kv-backend-type](../runtime/fia_actual_seq_lengths_kv_backend_type.md)。
- 融合算子按硬件条件门控回退见 [fused-op-hardware-conditional-fallback](../../optimizations/experience/rules/fused_op_hardware_conditional_fallback.md)。
- 另见 [AscendC 算子 host 侧未覆盖运行时可达配置空间：缺省可选输入被无条件读取、模板参数取值未全枚举 → 特定 config 崩溃 / npu fail / 无 tiling key](ascendc_op_host_optional_input_and_tiling_key_coverage.md)。

## Evidence

- `diff 事实`（@2c45117）：`mla_prolog` host tiling 硬编码 Hcq=1536 白名单；`lightning_indexer` 专化 N1=64。
- `diff 事实`（@239c0c1）：`aclnnMoeGatingTopK` 旧版专家上限 256。
- `diff 事实`（@d13c484）：ZECO CP GDN 核 `assert K==128`、BK=BV=128、无回退。
- `diff 事实`（@f066b2a）：`LIInfoParser::GetAndCheckOptionalInput()` 在 PA_BSND 下强校验 block_table/actual_seq_lengths_key 非空、block_table int32。
- 溯源下探：[cann-recipes-infer-issue-118-requirement-custom-npu-lightning-indexer-query-n](https://gitcode.com/cann/cann-recipes-infer/issues/118)、[cann-recipes-infer-issue-127-question-glm-5-mla-prolog-v3-hcq-1536-2048](https://gitcode.com/cann/cann-recipes-infer/issues/127)、[cann-recipes-infer-issue-71-bug-report-910b4-2-kimi-k2-thinking-warm-up-aclnnfusedinferattentionscor](https://gitcode.com/cann/cann-recipes-infer/issues/71)、[cann-recipes-infer-pr-359-support-context-parallel-execution-of-gateddeltanet-attention-in-qwen3-n](https://gitcode.com/cann/cann-recipes-infer/merge_requests/359)、[cann-recipes-infer-pr-167-fix-fix-li-log](https://gitcode.com/cann/cann-recipes-infer/merge_requests/167)

<!-- cannbot:related:start -->
## 相关

- [AscendC 算子 host 侧未覆盖运行时可达配置空间：缺省可选输入被无条件读取、模板参数取值未全枚举 → 特定 config 崩溃 / npu fail / 无 tiling key](ascendc_op_host_optional_input_and_tiling_key_coverage.md)（`related`）：昇腾融合算子把 host tiling 做成「按已知模型的固定 shape 特化」以简化 kernel 分支——特化点表现为**硬编码常量白名单 / assert / 必填输入约束**。它们不是技术本身的限制，而是**该参考实现只覆盖了标定过的那组 shape**。新结构模型的维度落在白名单外时被 host 校验挡下，报错常在 tiling/prepare 阶段而非 kernel 计算阶段。；在昇腾上开发 / 适配 ［AscendC］(../../concepts/frameworks/ascendc.md) 自定义算子（proto 的 InferShape/InferDataType 回调、op_host tiling 校验、模板 tiling-key 定义）时，出现「某一部分 config 路径运行时失败、另一些 config 正常」的分裂现象：不传某个可选输入就崩、开/关某个量化开关就报「tiling key 缺失」。根因几乎都在**算子 host 侧没有覆盖到运行时实际可达的那个配置**——缺省的可选输入仍被无条件读取，或模板实例化矩阵漏枚举了某个会被走到的参数取值。失败落在 host 侧 tiling/prepare 阶段或直接 npu fail，不在 kernel 计算阶段。。两卡从不同侧面覆盖 host 配置空间缺口：固定 shape/必填输入白名单与可选输入/tiling-key 漏枚举均在 kernel 前失败。
- [昇腾融合算子按硬件条件门控回退到非融合等价路径（SoC 白名单 / matmul 65535 轴上限）](../../optimizations/experience/rules/fused_op_hardware_conditional_fallback.md)（`related`）：昇腾融合算子把 host tiling 做成「按已知模型的固定 shape 特化」以简化 kernel 分支——特化点表现为**硬编码常量白名单 / assert / 必填输入约束**。它们不是技术本身的限制，而是**该参考实现只覆盖了标定过的那组 shape**。新结构模型的维度落在白名单外时被 host 校验挡下，报错常在 tiling/prepare 阶段而非 kernel 计算阶段。；在昇腾上适配模型时，融合算子（单算子融合 / NZ 权重 / 融合 matmul）并非对所有 SoC 和所有 shape 都可用。它们常带**硬件/形状条件的门控**：不满足时须回退到"小算子拼接 / 普通 matmul(ND) / 非融合"的等价路径，否则精度/加载出问题。移植或调优时，检查融合算子路径是否有 SoC 白名单或轴上限守卫，并确保有对应 fallback。下面两条是已固化进本仓的实例（写"路由把这组条件当作融合路径不适用"、而非"算子在该硬件上不能运行"）。。Runbook识别参考实现 shape 白名单，规则卡给出硬件或 shape 门控失败时切换非融合等价路径的处置原则。
- [调用昇腾融合算子撞 host-tiling 参数/布局拦截：按报错对号量化场景·cacheMode 维度·TND 必填输入契约](fused_op_tiling_param_layout_contract.md)（`related`）：昇腾融合算子把 host tiling 做成「按已知模型的固定 shape 特化」以简化 kernel 分支——特化点表现为**硬编码常量白名单 / assert / 必填输入约束**。它们不是技术本身的限制，而是**该参考实现只覆盖了标定过的那组 shape**。新结构模型的维度落在白名单外时被 host 校验挡下，报错常在 tiling/prepare 阶段而非 kernel 计算阶段。；这些不是随机崩溃，而是 host-tiling 校验按「量化场景 / cacheMode / 布局」逐项核对入参、任一不符即以 `OPS_LOG_E`+`GRAPH_FAILED` 或 `GRAPH_PARAM_INVALID` 精确拦截。报错文案带期望值 vs 实际值，可直接对号定位违约参数。。两卡共同处理 kernel 前的 host-tiling 拦截：一张识别硬编码 shape 白名单，另一张按量化、cacheMode 与布局定位合同违约。
<!-- cannbot:related:end -->
