---
type: Runbook
title: vLLM Ascend DSpark 加载失败：同 checkpoint 量化继承与 PP 隔离
description: 排查草稿缺weight_offset、weight_scale、scale_bias等量化参数，区分同checkpoint草稿和独立草稿，核对MRv2配置重建、分区屏蔽、双模块绑定与异常恢复。
tags:
- task.debugging
- topic.speculative_decoding
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_v2/patch_dspark.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/dspark/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/worker/test_patch_dspark_pp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_dspark_model_loading.py
  role: evidence
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/dspark/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/eagle/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/__init__.py
  role: constraint
created_at: '2026-10-29T13:13:15Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T14:55:50Z'
---

# vLLM Ascend DSpark 加载失败：同 checkpoint 量化继承与 PP 隔离

## 信号、假设与范围

W4A8/W8A8目标可加载，同checkpoint DSpark却在weight_offset、weight_scale、scale_bias等key上失败时，先核对草稿是否被构造成未量化层。该错误类型来自固定patch的原因说明与相应控制流，不是本仓抓取的运行日志；相同KeyError也可能由错误权重或映射引起。

本卡聚焦MRv2的load_dspark_model及Ascend wrapper；不将所有DSpark、任意路径别名或硬件视为相同情况。硬件整项证据未知，保持draft。

## 同源权重与独立权重分开裁决

| 条件 | 固定实现行为 | 探针 |
| --- | --- | --- |
| draft_model_config.model == model_config.model | 临时将get_draft_quant_config返回值绑定target quant_config | 比较实际字符串值、quant_config身份与每类Layer的真实参数 |
| 字符串不同的独立草稿 | 保留草稿自己的量化识别 | 不因target是W4A8就强制覆盖独立草稿格式 |
| 同文件的路径别名/不同revision | wrapper仅做字符串相等判断，无路径或内容归一化 | 不能把相同文件夹内容自动算入继承分支，也不能由相同字符串证明revision一致 |

上游load_dspark_model创建draft配置但保留target模型元数据，VllmConfig post-init可能恢复target quant_config，因此又显式调用get_draft_quant_config覆盖。不能只改target的quantization字符串来修复已经构造好的草稿Layer。

上游另将draft PP设1、TP按draft配置、关闭elastic EP，并按具体draft能力决定是否保留EPLB；不支持EPLB时草稿冗余专家数归0而target保留原配置。draft attention显式值优先，只有DeepSeek-V4/V4.1默认沿target backend，其余架构不自动沿用。词表共享还检查输入/输出vocab兼容性，不能用继承量化绕开。

## PP与导入绑定

目标手工VLLM_PP_LAYER_PARTITION属于target，不属于PP1草稿。受支持PP路径的wrapper仅在本次加载上下文临时屏蔽该变量；目标parallel_config和真实PP group不被伪装为PP1。target末stage没有embedding时，仅对PP>1且具post_process的draft跳过早期共享，交给已定义的本地加载；其他情形保留原共享规则。

原生speculator在import时按名绑定load_dspark_model，所以Ascend同时替换utils模块和speculator模块引用。固定Worker patch入口有patch_dspark导入声明，但只看到文件被导入仍不足以证明实际调用已走wrapper；需在真正Worker进程核对两个绑定。临时量化/embedding函数指针在finally恢复，分区mask也由上下文恢复；这不构成并发加载线程隔离的证明。

## 诊断、验证与回退

保存target/draft两个config及revision、own格式、实际模型类、同源判定、最终quant_config、缺失key、两个模块函数绑定、PP分区与本地embedding。按加载→共享→post_process顺序检查；修复后要求真实权重加载、logits与无投机参考通过，再谈图/PD/性能。所引mock单测表达同源/独立、PP1/PP2及成功/抛错后的恢复，本次未执行这些用例。

类型或revision不符、必要参数仍缺失、异常后符号未恢复或数值失败时停止，恢复匹配版本的target/draft完整配置或关闭DSpark。不要删除缺参检查、伪造target PP group或统一强制量化来称适配完成。后处理的basis与词表副本见[草稿对齐](../../guides/integration/vllm_ascend_draft_quarot_alignment.md)。


## 加载通过后继续检查采样与派生接口

量化继承只解决Layer构造与权重合同；继续核对[词表概率空间](../precision/vllm_ascend_dspark_vocab_probability_space.md)中的独立head/d2t、MRv1回退与MRv2 scatter，及[块布局接口](../../guides/integration/vllm_ascend_dspark_block_markov_contract.md)中的K/Q和Markov前驱。Kimi等重建子类还保留父类后处理hook，不能由wrapper成功返回就推导全部派生方法、confidence和KV writer已可运行。
