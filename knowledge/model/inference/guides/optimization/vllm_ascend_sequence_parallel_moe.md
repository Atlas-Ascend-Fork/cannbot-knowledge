---
type: Guide
title: vLLM Ascend SP MoE：FlashComm 门控与有效 token 布局
description: 说明 SP MoE 的 FlashComm 开关、DP1/TP/EP 门控与中文 PO 对照，核对 all-gather 后 unpad、zero-pad、TP2/4/8
  融合及平台待核验边界。
tags:
- task.optimization
- topic.parallelism
- topic.mixture_of_experts
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/sequence_parallelism.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/hardware_profile.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/sequence_parallelism.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/sp_moe.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ascend_config.py
  role: implementation
created_at: '2026-10-29T09:40:13Z'
updated_at: '2026-11-03T09:26:24Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend SP MoE：FlashComm 门控与有效 token 布局

## 范围与开关

本版本 SP 文档覆盖 MoE 路径，目标是消除 Attention O-proj TP all-reduce 后复制 token 在专家侧的重复计算/通信。要求 TP>1、enable_expert_parallel=true，并且FlashComm解析后的有效开关开启。文档示例使用`additional_config.enable_flashcomm1=true`，它不是唯一开启入口；只设并行尺寸不能代替FlashComm开关。

固定ceac实现先用`validate_additional_config_bool`（Pydantic bool规则）验证`additional_config.enable_flashcomm1`，再与环境变量`VLLM_ASCEND_ENABLE_FLASHCOMM1`的`strip().lower() in ("1", "true")`结果取OR。这里没有“JSON优先覆盖环境变量”的关闭优先级：JSON false与env true的OR仍为true，不能靠JSON false关闭环境已开启的FlashComm；非法JSON配置也不能跳过前置验证借env兜底。该commit还用`effective_flashcomm = flashcomm_explicitly_enabled or enable_dsa_cp`让DSA-CP自动开启FlashComm；DSA-CP自身的indexer、SP MoE及runner/PCP约束仍须满足。[ceac开关解析](https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py#L762-L815)

固定3164已删除`enable_dsa_cp`入口和自动开启分支，但保留经过验证的JSON值OR同名环境变量；不要把ceac的DSA-CP关闭参数带入3164。开关为true也不替代`use_sequence_parallel_moe`支持门控：源码在不支持的配置上给出禁用告警，仍需核对实际并行配置和执行路径。[3164开关解析](https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ascend_config.py#L752-L765)

关闭时同时省略或设false的JSON开关，并在每个worker启动环境取消该环境变量或设为`0`/`false`；ceac还须省略或关闭`enable_dsa_cp`。例如JSON false、env`" TRUE "`时两版本仍开启；JSON false、env`"0"`且ceac DSA-CP关闭时才关闭；JSON true即使env`"0"`仍开启。环境只认归一化后的`1`/`true`，不能把Pydantic对JSON值的bool规则套到env字符串上。

Ascend 不要求 DP>1，DP1 的 TP/EP 也可用；不能把上游 vLLM 对 DP、all2all backend 的门槛原样套到插件。硬件和通信算子的实际支持仍需按目标 profile 检查，本卡不把流程存在作为所有平台收益证明。

## 布局与融合边界

各 rank 沿 token 维分片，在 attention 边界聚合，reduce-scatter 后送 norm/router/all-to-all/专家计算，并恢复输出约定。不同 DP rank 有效 token 数不同，all-gather 后的缓冲不是连续有效 token，需按每 rank 长度 unpad/zero-pad；错误布局可能不报 shape 错却掉精度。

fuse_gemm_comms 可在受支持设备融合 bias-free row-parallel projection 与 token 维 reduce-scatter；来源限定 BF16/FP16、TP2/4/8，不匹配图继续 unfused。开启 pass 不代表所有 GEMM 已融合，需实际 IR/时间线。

## 验证与回退

先对齐每 rank token 数、padding、router indices 和输出顺序，再逐项打开 FlashComm 与融合，比较实际执行、数值和通信。性能对照应保存每个worker的原始JSON、环境变量、固定revision，以及解析后的`effective_flashcomm`、`use_sequence_parallel_moe`和启停日志；ceac另记DSA-CP状态，3164不再使用该项。关闭组必须确认所有开启来源都关闭，不能只把JSON改false便标为FlashComm off。保持模型、workload、硬件/软件、DP/TP/EP及融合设置一致后再比较指标，并用实际执行路径确认开关落地。

旧谓词风险见[SP 门控诊断](../../runbooks/precision/sp_gate_narrow_env_predicate_misses_shared_expert_dp.md)，不要复制旧环境变量判断替代当前有效配置。关闭 FlashComm/融合分别回退，保留正确基线。本次只核对固定源码与布尔边界，没有运行NPU、数值精度或性能验证。


## 平台证据待补

SP指南限定MoE、TP/EP与FlashComm，未明确列出产品集合；局部融合段的supported devices与通用profile不能证明整项SP功能的具体硬件范围。据此撤回原平台枚举，保持draft/空平台；这是证据不足，不能解读为这些平台不支持。


## 中文PO与接线复核

sequence_parallelism.po的17条有效非空译文已全文对照77行英文，0obsolete/fuzzy且msgid均匹配。中文与英文一致保留DP1可用但仍需TP>1、EP、FlashComm开关的门控；all-gather后的有效token必须按rank长度unpad/zero-pad，不能只据汇总shape当连续有效区。

融合段仍限定受支持设备上的bias-free row-parallel、BF16/FP16与TP2/4/8，不匹配图走unfused；这是局部融合约束，没有补齐整项SP的硬件产品集合，继续draft/空平台。PO与代码片段、实际pass/设备收益分别核验，本次未运行生成器、线上HTML构建或NPU。

## 保留流程图中的局部pattern

固定sp_moe图将self-attention后的TP ReduceScatter、post-attention norm、TP AllGather、sp_chunk与专家通信画为不同阶段，并列出Alltoall EP与AllGather EP/ReduceScatter EP两条专家分支。图中的AllGatherChunkNoOpPattern只针对图示的聚合后再切分往返，其他norm/residual融合pattern也有各自边界，不能把整条MoE图一概视作同一个融合算子。

图上“sp_chunk要求DP>1”标注属于该局部pattern，不覆盖本卡当前文档已说明的DP1+TP/EP可用条件。残差chunk、可选deepstack输入与下一层norm的图示也不是任意模型都具备的接线。先保留有效token和padding、所选通信及实际pass结果，再判断融合是否发生；图片没有提供新的硬件或实测收益。
