---
type: Guide
title: vLLM Ascend FA3 接入：训推一致性、独立 batch invariance 与图边界
description: 按A2/A3的中英文beta FA3合同核对外部依赖、四个来源测试模型和RL配置，区分batch invariance、内核/外部RoPE、图限制及训推一致性与性能验收。
tags:
- task.implementation
- topic.attention
- topic.reinforcement_learning
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/flash_attention.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/fa3_v1.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/flash_attention.po
  role: supporting
created_at: '2026-10-29T09:34:19Z'
updated_at: '2026-10-30T06:01:20Z'
platforms:
- a2
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend FA3 接入：训推一致性、独立 batch invariance 与图边界

## 适用范围与目标

来源版本 `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 的 FA3 是 A2/A3 beta 路径，目标是减少 RL 训推 Attention 实现差异。它可能慢于默认 FIA，不是默认性能优化建议；不外推到 950、310P 或未测试模型。

## 接入条件

使用 `rl_config.enabled=true` 与 `rl_config.enable_training_consistency=true`，并安装提供 flash_attn_with_kvcache 的 `flash_attn_npu_v3`。平台会检查包与符号，MLA/SFA 请求被拒绝；PCP 先走其分布式路径，不能由 RL 开关推导所有层均选 FA3。

`enable_batch_invariant` 是独立开关，不由 FA3 自动启用；种子、采样和通信确定性仍需单独核对。完整 RL 配置还会改变 NZ 和部分进程环境，记录这些联动，避免把多个变化的收益归因给 FA3。

## Attention 契约

FP16/BF16、因果、MQA/GQA、变长与分页 KV 在来源能力表中列出；滑窗、内核内 RoPE、ALiBi、softcapping、FP8 quantized Attention 不支持。RoPE 不在 FA3 内核支持不等于整个模型无法用 RoPE，来源使用外部回退。

适配调用区分每请求 KV 长度 cache_seqlens 与 Q 累积边界 cu_seqlens_q，page_table 必须对应当前 query 请求。混合 prefill/decode 分段时，prefill 的累积 Q 边界要扣除 decode token 偏移；不能直接把一个分段的边界套给另一个分段。

## 图与验收

文档建议 PIECEWISE；host tiling 路径没有完整 ACL capture 支持，实现明确拒绝非 eager 的 FULL_DECODE_ONLY。没有拒绝某个模式不等于它已验证可用，应检查最终图模式和数值。来源列举测试模型为部分 Qwen3 Dense 和 Qwen3-30B-A3B，不由此扩大为全部同族模型。

先在相同权重、输入、精度与采样下比较训练参考、FIA 与 FA3，覆盖变长和混合阶段；再测性能和额外开销。缺依赖、功能不符、输出偏差或图失败时，恢复默认 FIA 和原配置。本文未安装外部包或运行训推对照。

## Evidence

Flash Attention 文档给出平台和限制；平台选路与 fa3_v1 给出实际参数及错误分支。文档中“已开源”与 Future Improvements 中旧计划并存，以现有依赖和符号为准，不重复当成未来承诺。


## FA3中文能力表与训推验证口径

flash_attention.po的37条有效译文均匹配当前英文。flash_attn_with_kvcache参数语义与GPU FA3一致的来源表述，不表示功能齐全、kernel数值逐bit相同或自动实现所有RL确定性。A2/A3 beta、无MLA/SFA、无滑窗/ALiBi/softcapping/FP8及host tiling图限制仍同时成立，不由模型“也用FlashAttention”放宽。

rl_config.enabled与enable_training_consistency启用该路径；enable_batch_invariant独立。在这个配置入口下，文档称无需手动设置VLLM_BATCH_INVARIANT、HCCL_DETERMINISTIC、LCCL_DETERMINISTIC；仍应记录有效环境与配置联动，不能把无需手设理解为通信/算子确定性与本次结果无关。批次变化的验收另见[batch invariance](vllm_ascend_batch_invariance_validation.md)。

所列测试模型只有Qwen/Qwen3-0.6B、Qwen/Qwen3-1.7B、Qwen/Qwen3-8B、Qwen/Qwen3-30B-A3B，是上游报告，不是本次新增verified，也不扩展到所有Qwen、所有GQA或其他硬件。在线/离线示例temperature=.7、seed=42、max_tokens=100只是请求参数，不能把一段生成文本当训推golden或据同种子宣告逐字一致。

flash_attn_npu包与flash_attn_npu_v3模块、其中的算子符号分层核对；trainInferConsist是页面给出的外部分支名，本批未冻结/读取外部仓、wheel或安装说明，不能据分支链接推导具体ABI、当前包版本或安装已完成。开篇“已开源”与旧Future Improvements“计划开源”并存，按实际依赖证据裁决，未来ACL capture/更多型号/模型不写成当前支持。

Attention内核不提供RoPE与模型在外部采用PyTorch原生RoPE回退是两层机制；仍需核对目标模型的实际位置编码和调用链。固定权重/输入/精度分别比较训练参考、FIA、FA3与批次变化，覆盖变长/分页/混合阶段后再测性能；一致性目标并不排除性能退化。本批未安装依赖、启动服务或运行RL/NPU对照。
