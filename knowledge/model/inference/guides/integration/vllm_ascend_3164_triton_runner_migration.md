---
type: Guide
title: vLLM Ascend 3164 Triton迁移：Runner归属、采样掩码与拒绝器预热
description: '核对V1/V2 Triton目录迁移、request-major五字段采样mask、V1拒绝器声明式JIT键及MRv2熵验证边界，区分搬迁、ABI改变和来源性能证据。 '
aliases:
- sampling_mask_from_logits_npu
- rows_per_request
- RejectionWarmupContext
- register_rejection_warmup
- build_rejection_warmup_context
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.speculative_decoding
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/sample/sampling_mask.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/reject_sample.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/v2/sample/sampling_mask.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/csrc/moe/grouped_matmul_situ_quant/README.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/README.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/apply_grammar_bitmask.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/block_table/compute_slot_mappings.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/apply_grammar_bitmask.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/bincount.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/categorical_sample.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/compute_slot_mappings.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/entropy_verify.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/fill_logprob_token_ids.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/min_p.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/num_nans.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/prepare_dflash_inputs.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/prepare_nonempty_keypool_inputs.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/resample.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/sampling_mask.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/thinking_budget.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/topk_log_softmax.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/triton_description_specification.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/metrics/num_nans.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/sample/categorical_sample.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/sample/fill_logprob_token_idx.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/sample/thinking_budget.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/spec_decode/entropy_verify.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/spec_decode/prepare_dflash_inputs.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/spec_decode/resample.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/v1/bincount.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/v1/compute_slot_mapping.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/v1/docs/apply_penalties.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/v1/docs/compute_slot_mapping.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/v1/docs/reject_sample.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/v1/docs/spec_decode.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/v1/penalty.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/v1/reject_sample.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/v1/spec_decode/ngram.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/v1/spec_decode/utils.py
  role: implementation
created_at: '2026-11-03T07:04:15Z'
updated_at: '2026-11-03T07:04:15Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# Triton Runner与采样接口迁移

## 固定版本与读取边界

比较Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2与3164adc8fe75892fbf7f99f524bb72fddf1e6efd。变更通过完整原文diff、完整Python AST变化和必要上下文读取；相同文件用完整Git blob字节相等证明复用旧知识。未把delta当目标整文件原文FULL，未运行upstream、Triton/JIT、测试或NPU。本文是框架集成迁移合同，不代替完整Operator生产或具体平台的运行验证。

[ceac采样状态](vllm_ascend_triton_sampling_state_contract.md)、[草稿拒绝合同](vllm_ascend_triton_draft_rejection_contract.md)与[普通MRv2采样管线](vllm_ascend_mrv2_sampling_pipeline_contract.md)继续解释旧版本算法；下面只写迁移差异。目录重命名不表示模型、硬件或Native ABI已通过兼容测试。

## 先按生产Caller区分V1、V2和共享算子

3164的README明确：V1-only放v1/，V2放主包而非v2/，共享Runner、数学kernel和工具保留功能目录。一个模型只支持V2，不会使它的所有数学kernel成为V2-only。迁移需同步生产import、patch导入引用、warmup注册、测试mock与文档，不能只修定义文件。

| 原ceac相对ops/triton路径 | 3164路径或职责 | 语义裁决 |
| --- | --- | --- |
| v2/apply_grammar_bitmask.py | apply_grammar_bitmask.py | 整blob相等，保留packed grammar与cu_num_logits坐标合同 |
| v2/block_table/compute_slot_mappings.py | block_table/compute_slot_mappings.py | 整blob相等，仍为V2块表接口 |
| v2/metrics/num_nans.py | metrics/num_nans.py | 整blob相等；NaN计数不等于有限支持mask |
| v2/sample/categorical_sample.py、fill_logprob_token_idx.py、thinking_budget.py | sample/对应文件 | 整blob相等，原RNG、logprob搬运与marker状态合同不变 |
| v2/spec_decode/prepare_dflash_inputs.py、resample.py | spec_decode/对应文件 | 整blob相等；输入生产和拒绝后恢复仍是两个接口 |
| compute_slot_mapping.py、spec_decode/ngram.py | v1/compute_slot_mapping.py、v1/spec_decode/ngram.py | 整blob相等；不将V1 slot helper换成V2复数接口 |
| bincount.py、penalty.py、spec_decode/utils.py | v1/对应文件 | 增加JIT wrapper，不能仅按目录搬迁判断完整blob相等 |
| reject_sample.py | v1/reject_sample.py | 原kernel主体AST相等；新增预热类/上下文，旧root路径删除 |
| v2/sample/sampling_mask.py | sample/sampling_mask.py | 旧路径删除且ABI改变，见下节 |

零字节__init__.py在Git R100配对中可能跨block_table/metrics/sample/spec_decode目录；这是rename检测，不是这些功能互相替代的证据。空模块只承担包布局导航，没有独立kernel知识。文档与实现迁移也分别校验：fill_logprob_token_ids文档对应fill_logprob_token_idx实现，名称不完全一致不应被修成另一个API。

V1的reject_sample/spec_decode新增文档将legacy greedy/random/block/entropy及NGram定位在v1命名空间；MRv2使用worker/v2/spec_decode/rejection_sampler_utils与主包spec_decode/resample。V1元数据、概率buffer与RNG不能按同名阶段直接传给V2，310P共享PyTorch路径也没有因为这些移动而自动获得Triton能力。

## 采样mask改为request-major多提交token

新签名为from_logits(logits, cu_num_logits, num_sampled_tokens, max_num_kept, rows_per_request=1)。输出五字段：token_ids、packed_mask、counts、vocab_size、rows_per_request。旧三字段/四字段适配分支已删除，不能仍以是否传max_num_kept选择返回结构。

令输出row=r*rows_per_request+s，source_row=cu_num_logits[r]+s，只有s<num_sampled_tokens[r]时载入logits。cu可为chunk的非零起点；inactive slot用masked load的-inf填充，写零mask/零count，并非重复请求第一行的支持集。caller须保证正rows_per_request、累计offset覆盖、committed count同时不超过预留slot和该请求logit跨度；wrapper没有完整rank/type/offset验证。

每4096个vocab元素提取有限支持，NaN及±Inf均排除；每字节LSB对应较小token ID，尾部不置位，INT32累计count。packed shape为[R*rows_per_request,ceil(V/8)]。词表末轴stride!=1时只把局部logits变量连续化，不修改caller原view；该复制成本不在kernel-only profile中。空输出row数跳过launch。

compact token_ids始终是[R*rows_per_request,0] INT32，max_num_kept只为上游签名兼容，实际依靠精确packed-mask解码。来源说明旧Triton-Ascend动态scatter问题及可能增加CPU工作；空compact不是空支持或丢弃token。图回放允许device offset/count变化，但shape与rows_per_request专门化须保持；未执行图验证。

## V1拒绝与惩罚：注册键不等于运行时数值验收

v1/reject_sample.py新增六类AscendTritonJitKernel：单草稿greedy、一般greedy、expand、recovered-token、普通random及block-verify。ceac旧root文件删除，移入后kernel主体通过整AST对照保持，包装类本身不构成接受规则改进。

register_rejection_warmup在有效registry窗口内调用六个register；无spec配置或K<=0返回False。窗口外注册为no-op的生命周期由[统一启动预热](vllm_ascend_startup_kernel_warmup_contract.md)拥有。新文件定义/注册某wrapper不证明每个实际caller已经改用它，仍须检查运行时launch路由。

RejectionWarmupContext按cal_grid_and_block_size的不同BLOCK_SIZE挑代表batch，并包含最大batch，而非穷举capture sizes。单草稿专门类仅K=1注册；一般greedy在K=1只暖has_is_greedy=True，K>1覆盖有/无该指针。expand覆盖INT32、INT64和FP32并用Native MAX_SPEC_LEN。recovered-token键含no_draft_probs、sub_block和vocab专门化代表，runtime grid为请求数×max(1,K)。

ngram/ngram_gpu或PP<=1只注册无draft概率分支，否则有/无概率都覆盖；这是该配置的键生成策略，不能推广为任意新proposal不需要q。block开关还需K>=3。random键含synthetic/entropy、ori-target存在性、局部/全局词表、阈值alpha、epsilon与sub_block；改变这些设置可能再编译。synthetic与entropy实际算法的互斥/优先级继续按caller校验，不凭键空间认定组合有效。

v1/bincount新增TokenBinCountsAndMaskKernel，SEQ_BLOCK=256；v1/penalty新增ApplyAllPenaltiesKernel，BLOCK_SIZE=2048。词表代表按max(1,global_vocab//TP)生成，penalty暖FP32 logits；原histogram和惩罚kernel主体未改变。prepare_inputs_padded新增BLOCK_SIZE=4的wrapper与最小INT32/INT64假tensor。dummy输入只覆盖编译签名，不验证真实历史、越界sentinel、概率或分配容量，caller必须确认真实dtype/stride专门化命中。

## MRv2熵验证与bincount文档属于不同证据层

entropy_verify新增helper已由[MRv2拒绝与残差合同](vllm_ascend_mrv2_rejection_resampling_contract.md)维护：processed target计算FP32熵，threshold=min(exp(-alpha*H),posterior_threshold)，q>0且p/q>=threshold*u才接受；alpha=0用常阈值并跳过熵扫描。它主动改变标准拒绝的目标分布，恢复仍用原残差，不能当标准block verification或V1算法复用证明。新文档中的旧v2/spec_decode路径与当前实际主包路径有差别，按固定源码及生产import定位。

熵文档要求有效有限支持、offset/request-state一致、真实proposal概率与有效前缀；正alpha的有限性仍是caller条件。它记录8192统计与1024恢复grid乘积需受编译后端上限约束，65535是其验证栈，不由此硬编码所有未来后端。来源测试guard涵盖的硬件多于其记录实际运行设备；本卡不继承guard为平台验证。

新增docs/bincount.md描述的是V2 admission时persistent prompt位图与output counts，不是上面的V1 get_token_bin_counts_and_mask。其staged request数R也不是全部活跃decode请求数。来源算法先清按32对齐的INT8 flags与选定output row，以1024-history tiles写prompt presence/atomic output multiplicity，再按128 bitmap-word tiles打包；有界P=min(Vector cores,T)，每program连续承担q或q+1块。scratch仍R*ceil(V/32)*32字节，负载均分不保证ragged等时。

打包以INT32 view读取四个0/1 byte，乘0x01020408提取四bit nibble，再合成32位word，尾flag必须先清零。固定格式常量用tl.constexpr(value)，注解形式普通int在文档所述Triton3.6会失败。重复prompt的非atomic同值byte写没有一般race-free证明，output multiplicity仍需atomic。文档中的独立packed-workspace试验未被提升为当前实现，不能擅换算法。

性能Agent需保留该文档反例：短prompt多request和output-only相对main可能回退；单算子大幅改善、launch-limit修复、admission调用频次与decode模型吞吐不是同一分母。来源的当前编译修复SHA、早期算子/模型SHA、A3测试、A2未跑及A5范围均分别记录；不将历史表格写成当前3164全模型提速或本次结果。隔离冷编译、初始化、device task和E2E，保留质量与TTFT回退。

## 文档导航和迁移验收

grammar、categorical、NaN、fill-logprob、thinking-budget、DFlash、resample及slot-map文档随实现改路径，min-p/top-k文档改patch导入位置；这些导航变更没有新增数值实现。triton_description_specification要求按生产caller定位V1-only与主包V2。SiTU README仅将测试入口从test_grouped_matmul_situ_quant_weight_nz.py改为test_grouped_matmul_situ_quant.py，不构成新的量化、平台或性能结论。

Agent先固定Ascend与实际Native commit/安装版本，再核对旧import是否仍被缓存、patch是否覆盖被导入引用、registry时序与键覆盖。采样mask验证ragged offsets、零/多个提交token、inactive无对应source row、空batch、vocab尾与非连续view保留；V1拒绝验证有效前缀、synthetic/entropy/block及proposal概率。记录实际调用和编译产物后再测数值、分布、图与性能，不能以迁移表、fake tensor或ready日志替代。
