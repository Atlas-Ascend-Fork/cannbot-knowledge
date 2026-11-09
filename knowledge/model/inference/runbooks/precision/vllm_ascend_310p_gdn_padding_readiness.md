---
type: Runbook
title: vLLM Ascend GDN310P场景诊断：填充、接受长度与生产前提
description: 依据九个CPU场景诊断310P GDN状态或填充错位，核对PAD与NULL、accepted分层、容量和输出归属，区分参考测试与生产算子条件。
aliases:
- GDN310P场景诊断
- _mask_padded_recurrent_accepted_tokens
- _zero_padded_tokens
- _merge_spec_and_non_spec_outputs_310
tags:
- task.debugging
- topic.precision
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/ops/test_gdn_310.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/ops/fla/gdn_310.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/ops/gdn_attn_builder_310.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/gdn_attn_builder.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/ops/fla/chunk_gated_delta_rule.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/ops/test_chunk_gated_delta_rule_310.py
  role: evidence
created_at: '2026-10-31T11:43:07Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-31T11:52:04Z'
---

# vLLM Ascend GDN310P场景诊断：填充、接受长度与生产前提

## 症状与证据边界

310P GDN在MTP或batch收缩后状态错位、padding污染输出、accepted与offset不符，或CPU参考测试通过但生产chunk拒绝时，按实际phase和入口定位。主证据为固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2的test_gdn_310.py191行、9个CPU函数；core441、builder60及公共builder解释机制，均只作数据阅读，未复现真实设备故障。

整项平台/软件栈交集未验，保持draft/空平台。普通GDN图buffer诊断沿[已有元数据卡](vllm_ascend_gdn_graph_metadata_lifecycle.md)；本卡处理310P的实际sentinel、accepted层次与生产readiness。实现前提见[310P执行接入](../../guides/integration/vllm_ascend_310p_gdn_execution_contract.md)。

## 九个CPU场景的观察合同

| 固定test函数 | 输入与断言 |
|---|---|
| test_ascend_gdn_attention_310_uses_310p_backend | 310类返回对应backend，backend返回310 builder |
| test_builder310_reuses_common_graph_materialization | build/pad方法身份与公共实现一致，不能误写成独立算法 |
| test_zero_padded_tokens_masks_only_padded_token_positions | 有限CPU tensor沿指定token_dim保留前2项、尾部为0 |
| test_builder_prefill_shares_state_filtering | context[0,4,9]，按请求选择fresh/history mask |
| test_builder310_spec_padding_checks_request_and_token_capacities | req<=4、spec token<=16，两个量纲分开 |
| test_common_spec_padding_keeps_existing_token_limit | 公共builder仍限token<=4，不能跟着310P改大 |
| test_mask_padded_recurrent_accepted_tokens_zeros_dummy_requests | lengths[4,0,1]将accepted[2,3,4]转int32的[2,0,4] |
| test_builder310_pads_spec_decode_metadata_with_dummy_requests | live2/graph4，spec state尾PAD，accepted尾1，offset尾重复8；token溢出在改state前拒绝 |
| test_builder310_pads_non_spec_decode_metadata_with_dummy_requests | 普通decode state尾NULL0，offset[0,1,2,2,2]，无公共non-spec包装 |

fixture使用CPU Tensor、object.__new__和手工buffer，没有capture/replay或实际kernel。不能由方法身份、地址相同或test名称宣布NPU支持。

## 先核producer与consumer属于同一条路径

310 builder设置_SPEC_GRAPH_PAD_SLOT_ID=PAD_SLOT_ID和_USE_COMMON_KERNEL_METADATA=False；保留兼容类名。它共享分类和图物化，省略公共chunk/length/non-spec包装，consumer从顶层字段派生长度。

worker capability决定导入bundle，patch_idex_310实际替换Qwen core/state dtype/backend，RC还改Native backend builder。只检查类声明不足；记录实际实例、worker入口与所选builder。不要同时套公共registered conv hook和310直接weight读取。

## 请求容量与token容量分别检查

spec fixture两真实请求的state为[[3,30],[4,40]]，graph扩到4后尾两行PAD_SLOT_ID，mask False，offset[0,4,8,8,8]，accepted[2,3,1,1]。descriptor应别名这些持久buffer，actual_seq_lengths为None。

310P允许spec tokens到spec_token_indx.numel；公共builder仍用decode graph最大batch作为token界。溢出报错时先保存state buffer，不能通过扩大容量或去guard掩盖producer/consumer计数不一致。

普通decode使用NULL_BLOCK_ID=0、零长度offset尾，不能因spec用PAD=-1而统一修改。PAD也不能clamp为0；实际kernel可写block0，空请求必须由正确span/行裁剪保护。

## accepted1与accepted0来自不同层

仍启用的graph dummy metadata用accepted1配零长度span。recurrent wrapper先算diff(cu_seqlens)，_mask_padded_recurrent_accepted_tokens再对length0置accepted0；这是分层转换，不是任选一个常量。

core向spec conv和recurrent传[:num_spec_decodes]的state/accepted及N+1边界。保存slice前后形状、实际请求数和末offset，确认捕获padding没有作为真实state更新；不能只看配置的最大draft长度。

## 尾部mask与索引展开的限制

_zero_padded_tokens沿token_dim乘设备mask，有限值用例只验证这个合同。它不保证清NaN，不应为“修复padding”直接额外清整个cache。uniform spec-only在conv前遮投影、最终遮core，SP场景还保留输入padding后裁输出。

_flatten_state_indices在capture中按uniform slots reshape；eager ragged另有CPU compact和拷回。来源的is_pinned属性检查未调用方法，不能据non_blocking字样认定没有同步。记录实际query lengths/state表及capture状态，再判断是否满足分支前提。

_merge_spec_and_non_spec_outputs_310分别检查输出长度与token indices数量再索引合并；它不验证所有索引互斥、完整覆盖或kernel数值。prefill state回写仍用index_copy_，不要为消除一个输出算子而改所有写回。

## 参考测试通过而生产入口拒绝

test_chunk_gated_delta_rule_310_output_shape_and_dtype、test_chunk_gated_delta_rule_310_varlen_path与test_chunk_gated_delta_rule_310_varlen_tnd_path都调用chunk_gated_delta_rule_pytorch。它们用FP16输入、V12、mock NPU RMSNorm，核shape/dtype、FP32 final state以及TND/BTHD一致；没有覆盖生产chunk入口。

生产要求NPU和AscendC h/o、q/k/v FP16、value dim至少128且整除128；缺扩展、CPU或V12时应按真实guard诊断，不强制切reference。空token也先过这些guard；生产空输出请求finalstate时可能原样返回None初态，与参考FP32 clone逻辑不同。

## 修复、回退与交付

按已确认的bundle、字段层次、真实计数和扩展前提恢复匹配实现；保留出错前的state行、mask、offset/accepted、dtype/stride、输入布局和实际异常。旧版本镜像的图捕获限制与本版本CPU metadata设计分别记录，均不能跨版本推全平台图支持结论。

真实验收覆盖spec/普通decode/prefill混批、grow/shrink/idle、PAD与NULL、accepted转换、有限值/NaN尾、ragged eager与uniform capture、reference与production及连续步state。数值、state和同步正确后，再量CPU compact、H2D、WY、conv/recurrent/chunk和端到端成本。本卡没有NPU结果、吞吐收益、热恢复事务或Agent A/B结论。
