---
type: Guide
title: vLLM Ascend Kimi K3 MTP 接入：继承边界、prefix 与权重完整性
description: 按KimiK3MTPModel实际映射重建Ascend decoder容器并继承固定vLLM forward/loader，核对禁用block
  residual、MTP层名、packed参数、EPLB副本和递归接口。
tags:
- task.implementation
- topic.model_adaptation
- topic.speculative_decoding
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/kimi_k3_mtp.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/kimi_k3.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_eplb.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_kimi_k3_eplb.py
  role: evidence
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/models/kimi_k3/amd/mtp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/models/kimi_k3/amd/linear.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/model_executor/models/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/model_executor/model_loader/mtp_validation.py
  role: constraint
created_at: '2026-10-29T13:13:15Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T13:13:15Z'
---

# vLLM Ascend Kimi K3 MTP 接入：继承边界、prefix 与权重完整性

## 范围和可复用边界

KimiK3MTPModel映射AscendKimiK3MTP；它并非把AMD类直接当NPU实现使用，也不是K3DSparkModel的别名。Ascend重建predictor、predictor-layer和顶层容器，选择AscendKimiDecoderLayer、MoE bookkeeping及replica loader；forward、compute_logits和大部分权重加载继承固定vLLM的AMD MTP模块。硬件/Runner/部署支持必须另查，注册和类构造不构成MTP已在所有K3平台验证。

## 容器和prefix决定真实层身份

层范围是[num_hidden_layers, num_hidden_layers+num_nextn_predict_layers)，ModuleDict用绝对数字字符串键。num_nextn_predict_layers需与真实checkpoint匹配并满足实际调用的正数前提，不能由空容器构造成功推断forward取模安全。向decoder传入的prefix末段必须为该数字，因为AscendKimiDecoderLayer从它解析layer_idx，再选择KDA/MLA与MoE/Dense路径；不能把新模块起名mtp_block后丢失数字层身份。

MTP浅拷贝config并将attn_res_block_size=None。草稿从target隐状态开始，没有主模型累积的block residual tensor，不能照搬主模型attn-residual历史。enorm、hnorm、eh_proj和SharedHead保留匹配权重名；输入融合布局与[最终norm/feedback约定](../../runbooks/precision/vllm_ascend_mtp_hidden_state_contract.md)一起验收。仅替换构造器不证明所有继承forward中的外部算子已经适配。

## 权重映射链

1. Ascend的map_weight_name先移除language_model.，用get_spec_layer_idx_from_weight_name识别MTP层，再将decoder子权重插入.mtp_block；enorm/hnorm/eh_proj/shared_head留原层，embed_tokens提升到model级。
2. 两处同名spec-layer helper在此固定版本最终都来自上游models.utils；其前缀识别和改写仍要分别检查，不能把任意model.layers风格自动推广到其他模型。
3. loader在无w13_weight_packed目标时把.weight_packed按目标改为.weight；scale后缀另行匹配，不进行量化格式转换。Q/K/V、beta、full-rank gate和conv1d的stacked shard由真实配置决定，q_lora存在时才启用对应fused QKV目标。
4. routed experts走expert-aware loader，shared experts走自己的Linear合并；跳过PP missing层、非MTP层、额外bias或无匹配参数不是所有权重都成功加载的证明。多模态前缀去掉后，视觉权重不应伪装成MTP text权重。
5. 共享embedding只从首个spec层提升加载。返回loaded_params按最终参数名统计；每个预期MTP层至少出现一个命中才通过该文件的missing-layer检查，不能将“每层出现”当作“每个必需tensor、scale都齐全”。

Kimi的该缺层检查直接执行；上游DeepSeek MTP另有默认True的context-local completeness开关，用上下文关闭后finally恢复。关闭它不补齐权重，也不能作为Kimi的通用开关；本卡不建议以跳过检查完成适配。

## EPLB与本地层注册

Ascend先从非PPMissingLayer的Ascend predictor层中收集真正AscendKimiMoE，再按实际本地层设置moe_layers和num_moe_layers；没有本地MoE时计数为0，不能按target总层数注册。物理/本地/冗余专家数来自真实MoE实例，更新物理placement不能静默改变已分配本地槽数。

load_eplb_expert_weights在继承loader之外为初始placement的所有副本流式分派权重，不能只扩expert mapping后仍在首次命中break。具体布局与scale/metadata保留见[EPLB接入](vllm_ascend_eplb_model_weight_contract.md)。这些mock测试不证明A2冗余专家可用，实际硬件限制仍取专门指南。该129行MTP包装没有DeepSeek式的显式head所有权setter，不能据loaded_params自动推断最终has_own_lm_head；继续检查实际对象、继承链及Runner共享结果。

## 新模型适配验收

依次冻结真实architecture、prefix、目标/草稿config和checkpoint；检查所有必需参数与scale的加载集合，覆盖packed/unpacked、不同文件顺序、非MoE、本地无MoE、PP missing及冗余副本。再检查首步/K步的logits和反馈状态、prefix/chunk/回滚及目标SLO。MTP层数与K不能互换，未闭合的算子、KV/状态和Runner组合保持待验证。

失败关闭投机并恢复已验证完整版本/权重；不把K3部署教程的DSpark路径直接改名为MTP。教程范围见[Kimi K3模型指南](../models/vllm_ascend_kimi_k3_kda_mla.md)。本次仅读取源码/测试，未执行上游模块、编译或NPU验证。
