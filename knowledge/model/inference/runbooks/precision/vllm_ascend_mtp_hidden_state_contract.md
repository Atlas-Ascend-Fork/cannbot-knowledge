---
type: Runbook
title: vLLM Ascend MTP 精度：logits、递归隐状态与最终 RMSNorm
description: 区分deepseek_mtp.py、Kimi K3、GLM5-Next的二元返回与V4原始HC Tensor，沿MRv1/MRv2核对logits折叠、归一化和feedback，避免错误状态交换与多层轮转推断。
  核对MTP index共享：load_eagle_model把target的topk_indices_buffer更新到全部持引用的draft子模块，并按index_share_for_mtp_iteration门控首步压缩和后续复用。
tags:
- task.debugging
- topic.speculative_decoding
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/model_executor/models/deepseek_mtp.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_mtp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/kimi_k3_mtp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/mtp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/llm_base_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/target_dependent_ar/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_mtp_rotation.py
  role: evidence
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/models/kimi_k3/amd/mtp.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/models/kimi_k3/common/mtp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/target_dependent_ar/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/mtp/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/eagle/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v4/mtp.py
  role: implementation
created_at: '2026-10-29T13:13:15Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-03T02:54:05Z'
aliases:
- vllm.v1.worker.gpu.spec_decode.eagle.utils.load_eagle_model
- MTPSpeculator.share_mtp_topk_indices
- MTPSpeculator.on_prefill_end
---

# vLLM Ascend MTP 精度：logits、递归隐状态与最终 RMSNorm

## 触发条件与范围

MTP首步尚可、后续草稿分布或接受长度异常，或新模型移植后重复最终RMSNorm时，沿实际返回值和消费者检查。固定vLLM v0.32.0 / 5df63a72与Ascend ceac1a2b；以下是静态接口证据，不是跨硬件精度结论。

## 模型输出和logits分支分别解释

原有三条二元路径令h表示decoder residual相加后的最终归一化前状态，n(h)表示对应shared-head RMSNorm；V4行另用X表示未折叠的HC状态，二者维度和语义不能混同。外层compute_logits与递归输入分别核对：

| 模型路径 | forward输出及消费者拆分 | compute_logits额外动作 |
| --- | --- | --- |
| DeepSeek通用MTP（deepseek_mtp.py路径，Ascend包装继承） | (h, n(h))；启用sequence parallel时先all_gather并裁到positions对应token数 | 对第一项再做shared_head即最终norm，随后词表投影；logits与feedback各接受一次最终norm |
| Kimi K3 AMD MTP（Ascend重建容器后继承） | (n(h), h)，通过add-RMSNorm同时生成两项 | 第一项直接进head，不再做最终norm |
| GLM5-Next MTP | (n(h), n(h))，两项同值 | 第一项只进head，不再做最终norm；get_top_tokens也使用该归一化后状态 |
| DeepSeek V4 MTP（deepseek_v4/mtp.py） | 裸Tensor X；消费者按(X,X)使用，方法配置下V1为[N,hc_mult,H]、V2为[N,hc_mult×H] | reshape为HC，hc_norm/HC混合折叠到H，再shared_head.norm和词表投影；forward未产生另一份norm后feedback |

由函数注解为Tensor、类名、历史架构白名单，不能推出运行时只返回Tensor。把Kimi的第二项当已归一化状态，或在GLM第一项上再套一次norm，均不符合相应实现约定。DeepSeek的两个元素也不能交换后仍按旧compute_logits处理。

## Runner怎样消费

MRv1的`_split_draft_outputs`对Tensor返回(ret,ret)，对长度2的tuple/list返回两项；其他非空tuple/list退成第一项两用，空序列在取第一项时失败。首轮和后续draft循环均把第一项选为sample_hidden_states、第二项写回hidden_states缓存用于下一次草稿。这个容错分支不证明多于2项是新模型可依赖的稳定ABI。

MRv2原生TargetDependentARSpeculator._run_model只对tuple执行两项解包，裸Tensor两用；不能依赖MRv1的list或任意长度退化行为。Ascend派生_run_model继续接收这两项，再按replicated PCP广播对应状态；本次仅读取该调用片段，不证明整个CP执行闭包完成。

## 输入norm、旋转和层选择

enorm/hnorm处理embedding与previous hidden，是特征融合前的输入norm，不等同表中的最终norm。DeepSeek在position=0屏蔽embedding后拼接；Kimi的fused_mtp_input产生[N,2H]并在两个输入分支分别norm，输出dtype/device沿inputs_embeds，零token直接返回空张量。此处只使用Host接口和张量语义，未完成Triton内核生产闭包。

GLM5-Next/AscendDeepSeek可先按checkpoint is_rot_used对输入hidden执行rot，再进入hnorm；每次forward按其输入basis应用该修正，所引GLM测试也覆盖回收状态的下一步输入；不能在同一次输入处理中额外重复旋转，更不能与QuaRot投影对齐公式混同。DeepSeek的rot通过loader映射进入顶层，GLM5-Next对缺失必要rot.weight有显式拒绝，不能从一者推另一者也有同样guard。

这些predictor可按spec_step_idx % num_mtp_layers选层，但已读取的普通MRv1 merged draft和MRv2 AR调用只传通用输入，并未显式传spec_step_idx。不能由配置有N层就承诺K步会轮转所有N层；需核对实际multi-module speculator或其他消费路径。加载MTP层数、K和运行时选层是三件事。

## Indexer复用的状态寿命

原生MRv2 MTP仅在PCP=1、draft配置index_share_for_mtp_iteration为真且模型提供set_skip_topk/compact_topk_indices时复用步间索引。每次prefill开始重置skip=False；step0后按每请求last_token_indices把多token索引行压到前部；step1+设True，结束再重置False。目标的topk_indices_buffer共享还须更新所有持有引用的draft子模块，不能只改容器属性。

这套复用门控不自动适用于Kimi的任意KDA状态、任意PCP或新后端。多步异常退出后要验证下一次首步重新计算索引，而不是沿用旧请求的reuse模式。

## 探针、验证与停止

保存每步真实返回结构、两项shape/dtype、最终norm前后参考、选层索引、sample所用行及feedback写回行。分别验证首步、K>1、混batch、接受/拒绝、抢占恢复和索引压缩；框架之间对齐的是logits与递归语义，不要求内部张量都相同。

输出不对齐先回最小eager/无投机参考，恢复匹配该模型的producer/compute_logits/consumer组合；不要靠增加K、强制共享头或额外norm掩盖问题。头权重是否真实加载另见[LM-head归属](vllm_ascend_mtp_head_ownership.md)。本次未运行模型、数值对照或K步验证。

## V4的HC递归边界

DeepSeekV4MTP不是前表deepseek_mtp.py通用路径的另一个名字。其forward返回未折叠HC，compute_logits才做hc_mult×H维的无weight FP32 hc_norm、混合及H维shared-head RMSNorm；归一化轴和作用分支必须同时说明，不能将一次最终norm的规则扩为所有HC步骤只允许一次RMSNorm。

MRv1所读裸Tensor拆分与Native MRv2的Tensor两用规则使X同时送logits分支和下一步feedback；不能用折叠后的H维值代替HC输入。V1三维/V2展平由该模型的use_v2_model_runner属性控制，实际buffer、Worker与图形状仍须验证，局部返回合同不是完整Runner运行证明。

V4的容器可以按num_nextn_predict_layers创建多层，并按spec_step_idx取模；但当前loader只接受mtp.0命名，已读普通调用又未显式传step索引，不能据K或层数承诺轮转。详细输入融合、SP恢复、层0权重与Sink/EPLB边界见[V4 MTP接入](../../guides/integration/vllm_ascend_v4_mtp_adapter.md)。这些都是固定源码与未执行测试的结论，没有新增NPU或K步验证结果。
