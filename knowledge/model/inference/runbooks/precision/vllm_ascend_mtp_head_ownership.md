---
type: Runbook
title: vLLM Ascend MTP LM-head 归属：缺失权重、共享与 PP 嵌入
description: 排查MTP加载成功但logits或接受率异常，按真实loaded_weights、has_own_lm_head与Runner共享分支区分独立头、目标头和PP末阶段的本地embedding。
tags:
- task.debugging
- topic.speculative_decoding
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_mtp.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/mtp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/llm_base_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/mtp/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/target_dependent_ar/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_llm_base_proposer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_mtp_embedding.py
  role: evidence
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/mtp/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/eagle/utils.py
  role: implementation
created_at: '2026-10-29T13:13:15Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T13:18:30Z'
---

# vLLM Ascend MTP LM-head 归属：缺失权重、共享与 PP 嵌入

## 信号、范围与证据强度

目标模型无投机输出正常，开启MTP后logits、递归生成或接受率异常时，检查输出头是否实际加载。低接受率本身不能确认此根因。范围固定Ascend ceac1a2b与vLLM v0.32.0；本卡仅蒸馏加载与共享控制流，硬件产品范围未闭合，保持draft。

## 先从加载结果判定所有权

AscendDeepSeekMTP始终构造shared_head；构造出的head仍可能保留分配时内容。`_maybe_set_own_lm_head`检查真实加载集合是否含`model.layers.{mtp_start_layer_idx}.shared_head.head.weight`。没有则has_own_lm_head=False，有则True并暴露首个MTP层的head为顶层lm_head。GLM5-Next MTP也检查相同首层键，但其方法只设置标志，不据此新建顶层lm_head。

这不是通过torch.equal判断checkpoint是否有头。未加载随机内容与目标权重不相等，也不能证明是训练得到的独立头。首层标志不证明多层checkpoint中每个head都完整，需逐层保留实际加载清单。

| 消费路径 | 缺失 / 独立 / 相同的处理 | 不能外推的边界 |
| --- | --- | --- |
| MRv1 method=mtp且is_deepseek_mla | has_own_lm_head=False强制共享；否则只在每层权重与目标相等时共享 | 标志缺失并非强制共享；非DeepSeek MLA分支不能套用此判断 |
| MRv1目标head查找 | 顶层lm_head，继而get_language_model().lm_head、language_model.lm_head；不可达时告警并保留草稿head | 告警后没有共享成功的保证，不能继续写成正确加载 |
| MRv2原生MTP→load_eagle_model | `_should_share`默认无own标志时允许共享；声明own但缺顶层head则保留；两者都有head时还可按相等去重 | 不能照搬MRv1缺省标志语义；相等判断需发生在真实加载后 |
| MRv2成功共享头 | 同时替换draft顶层lm_head与各层shared_head.head | 只改顶层引用会遗漏实际compute_logits消费的逐层head |

MRv2路径由AscendMTPSpeculator的继承链进入原生MTPSpeculator.load_draft_model，后者调用load_eagle_model；不是只因函数名带eagle就排除MTP。DSpark/DFlash的独立或缩小词表头有另外门控，不能用MTP共享规则覆盖。

## PP末阶段的embedding是另一项检查

MRv1只在PP1尝试target embedding共享，普通MTP分支还以not use_compress决定是否共享；PP>1时不跨阶段别名stage0权重。MRv2会识别PPMissingLayer：需要target embedding、草稿又未声明自己有副本时可直接失败。GLM5-Next loader能在过滤MTP层之前加载顶层model.embed_tokens.weight，并支持model.language_model前缀；MTP专属embedding优先于通用embedding，文件顺序不改变优先级。

MRv2还会从BaseLayerWithLoRA取base_layer，草稿不因此继承target LoRA adapter。

不要把“head可在最后stage共享”解释成“embedding也在最后stage可共享”。是否持有本地embedding由真实加载结果和has_own_embed_tokens确认；只加载embedding也不能掩盖MTP层完全缺失。

## 探针、停止与回退

依次保存checkpoint revision与真实key、最终模型类、loaded_weights、首层索引、own标志、实际target/每层head和embedding对象，以及Runner路径。确认共享后的引用指向实际compute_logits消费者，再比对单步logits、K步生成和无投机参考；独立训练头不能仅为省显存被替换。

has_own_lm_head=False且target head不可达、PP末阶段无embedding副本、必要权重遗漏或输出不对齐时停止性能比较，关闭投机恢复已验证配置。权重所有权正确后仍需检查[最终RMSNorm与递归状态](vllm_ascend_mtp_hidden_state_contract.md)。所引单测用mock/CPU张量描述共享与PP行为，本次未执行；它们不提供NPU精度或硬件支持证明。
