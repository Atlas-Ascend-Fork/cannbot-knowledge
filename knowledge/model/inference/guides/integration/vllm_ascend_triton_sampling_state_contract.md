---
type: Guide
title: vLLM Ascend Triton采样惩罚、Grammar与统计状态合同
description: 聚合惩罚直方图、grammar packed mapping、thinking marker缓存、NaN计数及MRv2采样文档，区分请求状态索引、RNG、输出所有权与版本边界。
aliases:
- apply_penalties_triton
- _apply_grammar_bitmask_kernel
- _load_effective_token_ascend
- get_num_nans
- SamplingMaskTensors.from_logits
tags:
- task.implementation
- task.debugging
- topic.model_serving
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/penalty.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/bincount.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/v2/apply_grammar_bitmask.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/v2/sample/thinking_budget.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/v2/metrics/num_nans.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/apply_penalties.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/min_p.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/topk_log_softmax.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/v2/sample/categorical_sample.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/v2/sample/sampling_mask.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/v2/sample/thinking_budget.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/v2/docs/apply_grammar_bitmask.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/v2/metrics/docs/num_nans.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/v2/sample/docs/fill_logprob_token_ids.md
  role: supporting
created_at: '2026-11-03T06:00:17Z'
updated_at: '2026-11-03T06:00:17Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Triton采样惩罚、Grammar与统计状态合同

## 来源与接口层次

固定 Main 的五个完整Python程序AST和九份算子文档。本文静态解释合同，未执行Triton、采样、UT或模型。categorical/min-p/logprob/mask文档引用的实现已有独立知识来源，本节补齐文档约束，不把只读文档当这些实现的新全文信用或本次NPU通过。

## Penalty直方图与哨兵

apply_penalties_triton先为prompt/output分别建立INT32直方图与mask，再原位更新logits：prompt或output出现过才施加重复惩罚，正logit除repetition、非正乘repetition；frequency只用output次数，presence只用output mask。repetition必须>0，由请求层保证，不是kernel自行校验。

bincount按256 token块、固定上界vectorcore网格与atomic_add计数；空token长度可直接零结果。但源码只用token<vocab_size筛选，没有token>=0条件，负值会进入地址计算。docs/apply_penalties.md先概述“[0,vocab)”筛选，后又要求padding>=vocab、由上层把-1转vocab；诊断采用后者与实际代码，不把-1直接传给helper。num_seqs=0时penalty入口仍可能零grid，应由调用者跳过。

logits和mask传真实二维stride，token先连续化；两份counts峰值与seq×vocab成正比，不把仅两kernel的launch数当总内存成本。记录输入/输出token哨兵与mask、原logits和三penalty，避免只按logits变化归因数值精度。

## Grammar映射不是直接logit行号

_apply_grammar_bitmask_kernel的launcher保留upstream[logical masks,vocab blocks]语法，实际将任务均分到min(vectorcore,total_tasks)个program，最多相差1，multibuffer=False。INT32每word32位，bit1保留，bit0原位写-inf，允许位不写回。

实际logits_indices编码 req_idx*MASK_STRIDE+position，kernel先商/余数拆开，再用cu_num_logits定位该请求真实logit行；position超出本请求跨度则不store。文档前面直述“行号”的公式不能替代后文packed示例与代码。必须核req索引、MASK_STRIDE大于最大position、cu边界和bitmask词数；只有vocab尾部store mask不保护所有上游索引。

文档A2/A3测试使用BF16、64×151936、block8192，graph支持待补，950优化不在该变更范围；不能以三类平台都在模板中出现就扩大本实现验证范围。

## Thinking budget的已提交/在途Token

_load_effective_token_ascend以互补masked load及单一where返回，committed取all_token_ids[state,pos]，in-flight取input_ids[cur_req_first_pos+pos-total_len+1]；多一个+1是协议的一部分。避免将循环内双分支return改回去，来源记录旧Triton-Ascend lowering问题。

marker cache按req_state_idx维护last start/end及scan_pos，负budget跳过；scan_pos大于当前committed长度会重置，冷扫描向后按block找最新marker，否则增量向前扫描。更新后的scan_pos保留MAX_LEN-1重叠以匹配跨步多token marker；取消/回退复用state时不能只清logits而保留旧cache。来源对未来Q4/3.6的删除建议是条件计划，未验证当前编译器即可删兼容实现。

## NaN统计与有限支持mask不同

get_num_nans要求rank2，按row stride和连续vocab寻址，8192块，转FP32后调用CANN isnan精确累加INT32。源码没有完整dtype/device/末维stride validator。±Inf不会被计为NaN；num_nans=0不代表softmax输入有有效支持。

sampling_mask文档则只保留isfinite且num_sampled_tokens>0的条目，NaN、+Inf、-Inf全部排除；uint8每字节LSB对应第一个token，counts为INT32。使用4096块和transpose+常量位权规避UB/编译器问题；末轴stride!=1局部连续复制，不改调用者原view。三字段或带max_num_kept的四字段接口分开，后者返回零宽compact token_ids，靠精确bitmask的tolists恢复，不能把空compact buffer当无有效token。

## Categorical、min-p和logprob文档的验收合同

- categorical用8192粗块和1024细块的概率质量层级，只用每row一次stateless uniform阈值贯穿两级；temperature0 greedy，非0才随机，apply_temperature=False表示已处理。raw logits_cache在温度处理前写，(request,col)不能重复别名；draft盐隔离随机流。use_fp64=True不支持，pos收窄int32。分布等价Gumbel不要求同seed输出同一token序列，需分布/重复确定性分别验。
- min-p按max_logit+log(p)筛小于阈值，p=0不写且仅因输入输出别名才安全，p=1保留所有并列最大；负p非法。逐token的expanded_idx_mapping与request state distinct，不把batch顺序当永久request ID。文档精度验收先比-inf mask完全一致，再比存活FP32值。
- topk_log_softmax实际对指定token做logsumexp归一后gather，不等于该kernel自行选top-k；文档固定tile12944与NaN propagate兼容，token ID须有效且矩阵行按topk紧密。source文档里的旧compute_topk_logprobs对自定义token可warn后fallback，不能泛称完全实现。
- fill_logprob_token_ids说明另一个自定义ID搬运kernel：采样token列0恒有效，自定义请求列优先覆盖top-k，其他位置保留初始化；num_cols=max(topk,maxcustom)，有效mask与INT64 IDs必须配套。分支内部load规避动态指针，不是增加任意索引容错。与上一条旧fallback属于各自接口/实现阶段，须按实际调用者核验，不混成一份当前保证。

## 交给Agent的验证

按真实Native/Ascend配对先确认patch绑定与调用签名，再记录persistent request mapping、padding/slot、marker cache、grammar位序、概率支持与RNG(seed,pos,salt)。计数/索引搬运要求bit-exact，数值/logprob按dtype容差，随机路径用分布与内部重复性，三种验收不互相替代。采样在模型图后eager执行的来源说明不表示所有kernel或新图组合已通过。
