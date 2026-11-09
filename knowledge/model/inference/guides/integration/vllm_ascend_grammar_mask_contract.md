---
type: Guide
title: vLLM Ascend grammar mask接线：请求行、投机窗口与V1/V2路径
description: 按 StructuredOutputsWorker、_build_grammar_mapping 与 grammar_invalid_drafts
  对齐 MASK_STRIDE、cu_num_logits和自适应验证，核对异步复制、NPU launcher、V1 CPU回退与合法负无穷。
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/structured_outputs.py
  role: primary
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/structured_output/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/v2/apply_grammar_bitmask.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_v2/patch_triton.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_apply_grammar_bitmask_triton.py
  role: supporting
created_at: '2026-10-29T21:54:22Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T21:54:22Z'
---

# vLLM Ascend grammar mask接线：请求行、投机窗口与V1/V2路径


## 适配任务与边界

新Runner/投机方法改变logits行数后，结构化输出失效、请求间mask错位、adaptive verification裁剪后仍消费旧行，或把grammar写入的-inf当原始数值错误。固定原生v0.32与Ascend ceac，仅追踪所需Host接口及调用协议；整项硬件未知，保持draft/空平台。

本卡不充当Triton Operator完整生产：只读kernel/launcher和测试定义，未运行Device producer、编译、精度/性能或所有shape/backend验证。图捕获可用、进程stream别名正确和NPU执行必须另取证。

## V2 CPU布局与Device最终布局

StructuredOutputsWorker预分配int32 logits_indices及[max_num_logits,ceil(vocab_size/32)] grammar_bitmask，另持copy stream。apply_grammar_bitmask无grammar_req_ids直接返回；否则拷mask，构造mapping，再在copy stream拷mapping，当前stream等待复制后launch，末尾copy stream反向等待当前stream，避免复用/释放过早。

这些代码使用原生torch.cuda stream命名；Ascend patch_triton替换kernel符号本身不证明所有CUDA→NPU stream适配已成立。固定worker import仅在HAS_TRITON时加载对应patch_v2.patch_triton；核对实际进程加载与设备运行，而不是只搜到替换语句就宣称可达。

_build_grammar_mapping按input_batch.req_ids映射grammar_req_ids。无draft-count数组时从CPU cu_num_logits_np差值取position数；存在数组时用每请求scheduled draft数+num_bonus_tokens，即使自适应验证已在CPU把实际logit布局压成bonus-only，也保持已调度mask布局。请求ID缺失会在字典索引处失败，没有自动猜请求的通用回退。

每项不是绝对行号，而是req_idx * MASK_STRIDE + position。MASK_STRIDE必须大于最大编码position，否则取模/整除会改变请求归属。mask行数必须等于mapping长度；该断言不是任意shape、dtype、范围、重复mapping和capacity的全部验证。

## cu_num_logits与inactive位置

Ascend kernel从Device cu_num_logits解析每请求最终起始行与真实行数，再加position。position>=真实行数时不store，避免自适应裁剪后对inactive draft写logits；合法vocab之外也不写。这里的掩码不能替代任意req_idx、负mapping、越界cu数组或错误MASK_STRIDE的上游验证。

packed int32每word32个词项，bit为0的词项被原地置负无穷；允许项保持原logit，未涉及的请求行不因这次mask统一重置。schema语法约束与业务内容正确性分别验收，也不能用“全部logits有限”要求覆盖mask后的合法-inf。

## 投机invalid drafts与reasoning边界

grammar_invalid_drafts在没有grammar请求或draft总数为0时返回None；否则按每请求num_acceptable_drafts建立阈值，缺该列表时将整个grammar draft窗口视为需拒绝。Device expanded_local_pos > row_limit生成无效行，0号位置不作为draft i+1；非grammar请求保留最大阈值。仅阈值都不小于draft数时可提前None。

manager的grammar_bitmask按请求scheduled tokens串行产生各position+bonus的行；-1 padding之后改用full mask，遇到grammar拒绝/终止则复制上一个有效失败行，临时推进后rollback。reasoning gate还可能给full mask，所以bitmask存在不证明每个draft都已按语法验证，invalid_drafts与拒绝采样须一并传递。

manager的非投机大batch填mask并行阈值为严格>128，分块16；这不是“batch达到128就多线程”，也不是GPU/NPU launch核数。enable_in_reasoning与request-local reasoner决定约束开始位置，细节见[backend生命周期](vllm_ascend_structured_output_backend.md)。

## Ascend V1/V2与LM-head TP

所读MRv1采样片段将logits保存dtype后搬CPU转float，应用原生apply_grammar_bitmask，再搬回NPU及原dtype；源码注释说明该路径没有直接复用原生torch.compile优化。CPU传输/转换是这个固定路径事实，不推导所有Runner通用瓶颈或固定收益。

标准V2非lmhead_tp路径委派super.sample；Ascend自有LM-head TP分支先把compute_logits输入补齐到各rank一致capacity，再裁回真实num_logits。只有grammar_output非None且logits行数>0才apply mask，随后计算grammar_invalid_drafts，再按有无draft与rejection_sampler选普通/拒绝采样。不能在不同rank用不同row count，也不能跳过invalid_drafts而只保留mask。这里只读完整sample方法，不宣称完整Runner/模型/310P路径闭合。

Ascend launcher把二维(num_masks,num_vocab_blocks)任务均分到min(VectorCore数,total_tasks)个program，以循环处理；固定实现传multibuffer=False。注释提到A2/A3收益和A5可再启用，不是实测或运行时按芯片切换。total_tasks=0、容量/词表边界、不同stride/dtype与后端编译仍需目标环境验证。

## 验证信号与相邻诊断

按请求记录CPU scheduled布局、mask行数、编码mapping、Device cu_num_logits、expanded_local_pos、acceptable-drafts、logits真实/补齐行和实际采样入口。对比mask前后：禁止项-inf、允许项不变、inactive位置不写、跨请求不串扰，投机拒绝与输出schema同时验收。

已读nightly测试定义使用64行、16请求×4logits、vocab151936、BLOCK_SIZE8192、MASK_STRIDE8、BF16，后4项为inactive，并覆盖全允许/全禁用/交替bit；skipif只允许A2/A3/A5。它是单shape测试计划，不是全平台/所有dtype或本次运行结果，不能据此把整卡标为stable。

原始数值归因沿[Runtime Guard logits时点](../../runbooks/precision/vllm_ascend_runtime_guard_logits_attribution.md)，最终语法/接口验收沿[结构化输出验收](../../runbooks/validations/vllm_ascend_structured_output_acceptance.md)。复制完成、kernel完成、grammar FSM状态、HTTP结束与业务答案正确是不同证据。
