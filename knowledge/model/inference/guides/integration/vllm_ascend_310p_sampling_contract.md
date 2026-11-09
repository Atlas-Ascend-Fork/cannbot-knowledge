---
type: Guide
title: vLLM Ascend 310P 采样接入：参数、CPU RNG、拒绝采样与主机计数
description: 沿 Ascend310PSampler 与 RejectionSampler310V2 核对参数拒绝、temperature/top-k/top-p、CPU generator身份与逆CDF、MTP点质量接受和残余分布、host buffer容量与copy stream/event同步，并对照独立Native签名和分块边界。 Ascend310PSampler._add_request_impl先拒绝不支持的采样参数，再对越界req_idx返回；请求索引范围不能提前掩盖参数不支持。
aliases:
- Ascend310PSampler
- RejectionSampler310V2
- probabilistic_rejection_sample_cpu
- _prepare_cpu_generators_310p
- _sample_from_cdf_310p
- synchronize_cpu
- Ascend310PSampler._add_request_impl：参数拒绝与请求槽范围
tags:
- task.implementation
- task.debugging
- task.optimization
- topic.model_adaptation
- topic.speculative_decoding
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/worker/v2/sampler.py
  role: primary
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/rejection_sampler.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/worker/v2/rejection_sampler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/worker/v2/sample_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/worker/v2/spec_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/worker/v2/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/test_rejection_sampler_310p_buffer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/test_model_runner_v2_310p.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/worker/v2/model_state.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/model_runner.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/_310p/rejection_sampler.py
  role: implementation
created_at: '2026-11-02T06:28:19Z'
updated_at: '2026-11-04T03:05:17Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 310P 采样接入：参数、CPU RNG、拒绝采样与主机计数

本卡的采样拒绝表属于所列旧版本。目标为7d9e时，min_p、penalties及输出logprobs已有不同实现，先读[7d9e运行时差异](vllm_ascend_7d9e_runtime_delta_contract.md)的310P节，分别核对后处理顺序、raw分布与未闭合功能。

## 任务与证据范围

为310P命名的MRv2路径适配新模型，或排查采样参数被拒、固定seed重排后序列变化、MTP接受长度错误、host buffer缩容或CPU读取尚未完成的拷贝时，先锁定实际sampler和rejection sampler。固定Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2：sampler305行、rejection203行、sample_utils136行、spec_utils546行及buffer UT70行全文；Main Runner仅1290–1458、Runner UT仅1–63与614–766。ModelState476行和pin复用同SHA全文阅读。独立Native5df63a7203cdb9328d824a27b682e77c7b9928be的rejection sampler470行全文，Native Runner仅1635–1669。

Main pin实际配对544f182d9f0c9bfe8bd7645525951d5e3692a542。独立5df用于解释版本差异，不证明与该Main的生产ABI兼容。全部源码与测试只作数据，未运行上游导入、UT或NPU。类名、注释、CPU fixture与stream代码没有证明任一完整硬件/模型交集，保持draft/空平台。

[投机方法选择](../optimization/vllm_ascend_speculative_method_selection.md)解释算法和方法配置；[投机接受率诊断](vllm_ascend_runtime_guard_spec_acceptance.md)拥有运行时诊断入口；[310P状态接入](vllm_ascend_310p_model_state_contract.md)拥有位置、prefill与Mamba状态生命周期。本文闭合采样producer到CPU计数consumer，不覆盖模型加载、完整Device算子或端到端性能。

## 先核对显式参数拒绝与请求槽状态

Ascend310PSampler.add_request签名为req_idx、sampling_params两个参数。固定Runner UT中的_add_request helper虽然接收prompt_len，却直接丢弃它再调用两参数方法；不能据此宣称新旧Native签名已自动兼容。_add_request_impl先收集不支持字段并抛NotImplementedError，之后才检查req_idx范围；不能假定无效槽会优先静默返回。

| 字段 | 此实现的拒绝条件 |
| --- | --- |
| min_p | 非0 |
| repetition_penalty | 非1 |
| presence_penalty、frequency_penalty | 任一非0 |
| logprobs、prompt_logprobs | 任一非None |
| bad_words、logit_bias、allowed_token_ids | 任一为真值 |

这三个logits processors字段的空值与非空值行为不同；不要把拒绝分支写成所有SamplingParams或任意外部processor均已验证。penalties_state.output_bin_counts为None，返回SamplerOutput的logprobs_tensors和num_nans也为None；这些占位不是完整penalty/logprob/NaN能力证明。

temperature、top_k、top_p及seed保留CPU镜像和sampling_states的device字段。新增/删除请求置dirty；同步复制的是四个已分配数组，不能仅按本轮活跃请求数量估算H2D成本。未给seed的请求走默认随机源，显式seed创建对应source generator；槽复用要连同删除、重新初始化和映射更新一起验收。

构造时vocab未知会以1初始化top_k；_maybe_bind_vocab_size后用_top_k_np <= 1判定未设置并替换为实际vocab。因此“未知vocab下显式top_k=1”也落入该条件，需要额外验收。已构造ModelState提供vocab的路径与独立延迟绑定场景应分别记录，不能只验证默认top_k。

## 区分greedy快捷路径、温度缩放与随机数身份

_SAMPLING_EPS为1e-5；temperature达到该阈值的请求进入random判定。温度缩放跳过0和1，以FP32运算再写回原dtype；need_scale.any().item()包含主机可见判断，实际同步成本待测。无随机且无top-k/top-p加工时直接argmax；其余路径先构造FP32 logits副本，再按expanded_idx_mapping展开参数，调用共享apply_top_k_top_p。混合batch仍为greedy行保留argmax结果，不能把整batch的any_random当作每请求随机标志。

_prepare_cpu_generators_310p根据source对象identity复用CPU generator，首次从initial_seed初始化；cache只保留本次传入的对象集合，索引变化本身不等于source身份变化。_build_row_generators先调用一次prepare，_generate_request_uniforms_310p又对收到的generator集合调用prepare。两层输入对象可能不同，这是静态审阅发现的连续性风险；本次未执行随机序列，不能宣称缓存已证明请求重排后完全复现。

Agent验收应固定seed与输入，逐项覆盖单请求多步、请求重排、加入删除、槽复用、多个logit行引用同一请求、mixed greedy/random、默认generator以及跨常规采样/MTP路径切换。同时记录source对象与prepared generator身份、每次cache集合和每请求消费次数，再比较连续序列；只比较首token无法验证该风险。

_random_sample_310p在global_stream上生成每行一个CPU FP32 uniform，经pinned memory异步H2D，当前stream等待global_stream后做逆CDF。uniform用float32 tiny截断避免精确0；_sample_from_cdf_310p对非负权重做FP32 cumsum，以uniform乘每行总权重，再用searchsorted(right=True)。正确使用仍要求合法、有限且有正总质量的权重；这里没有补齐全零、NaN、无穷或负权重的防护证明。注释中的传输优化理由只能作为待测假设，不能作为已获得的吞吐提升。

## MTP随机验证是点质量draft合同

RejectionSampler310V2.__call__(logits,input_batch,draft_logits)直接del draft_logits。随机分支从input_ids_cpu和logits_indices_np恢复draft token，先经sampler.apply_sampling_params加工，再由probabilistic_rejection_sample_cpu处理。该helper按请求读取temperature与seeded generator，softmax得到目标概率；draft按点质量处理，接受条件为u < p(draft)。首个拒绝位置只清除该draft坐标，再从剩余权重的CDF抽取recover token并停止；全部通过后最后一行提供bonus token。它没有消费一般proposal分布q，也不能由此推出任意draft模型概率校正已实现。

temperature近零的请求按greedy一致性验证。专用greedy拒绝路径区分每请求恰好1个draft的MTP1与变长/MTP2+：前者target_rows来自各请求cu_num_logits起点，后者排除请求间穿插bonus行；draft_rows=target_rows+1，bonus_rows为各请求最后一行。input_ids、logits_indices、cu_num_logits、req映射与draft长度必须保持同一步的一致性，不能只检查张量形状。

输出使用PLACEHOLDER_TOKEN_ID初始化，而有效数直接以sampled != -1统计；应验证所配版本占位常量与字面值一致。get_num_sampled_and_rejected_cpu按batch位置处理结果，以idx_mapping_np查请求prefill长度；chunked prefill条件为seq_len < prefill_len，sampled/rejected都置0，其他请求由num_logits减实际sampled得到rejected。不要将batch位置与持久req_idx混用，也不要把填充请求的实际计数直接当作接受率样本。

## 保持host buffer容量，并在CPU消费前同步

构造时按max_num_reqs预分配sampled_tokens_cpu、num_sampled_cpu、num_rejected_cpu。随机路径用copy_写入[:num_reqs]，保持容量；直接将较小本轮tensor赋给成员会使后续batch增长失败。buffer UT70行以CPU对象和mock stream/event模拟1到4请求的前缀拷贝，未实际执行完整随机__call__、NPU DMA或真实并发。

greedy路径在_copy_stream等待main_stream后发起device到host的三份非阻塞前缀copy，记录_copy_event并置_copy_pending。synchronize_cpu仅在pending时等待event；Main Runner.postprocess在读取这些CPU计数前调用它，再执行请求CPU记账、model_state.postprocess及host镜像更新。提前读CPU成员、覆盖尚未消费的buffer或漏掉调用会破坏该顺序。随机路径设pending为False，不提供对前一轮未消费greedy copy的独立等待；适配方应保证每步结果消费与缓冲复用的调用顺序。

常规采样的Runner分支在本地重写prefill相关num_sampled/num_rejected；grammar_output存在时显式拒绝。要把sampler输出、Runner返回和CPU bookkeeping一起核对，不能只看到SamplerOutput构造成功就宣称structured output或所有prefill计数闭合。

## 对照Native后再迁移接口和性能策略

独立Native5df的RejectionSampler.__call__还有第四个invalid_drafts参数，本地310P覆盖与已读Main caller均传三个参数。Native Runner有界调用展示四参数接口，说明跨pin迁移必须追踪实际调用链。不要仅因继承关系或相同类名跳过签名、输入映射及返回字段核验。

Native父实现以1GiB FP32 processed logits预算划分chunk，不拆分单个request；该预算不是完整临时张量或显存上限。Main覆盖调用不自动继承Native父__call__中的chunking、invalid_drafts mask、NaN/logprob处理、block/synthetic/adaptive路径。父构造保存相关字段也不证明310P覆盖已消费。310P apply_sampling_params始终生成FP32副本，随机验证还涉及softmax与CPU概率处理；应分别测量vocab、总logit行数、请求长度分布和草稿步数带来的峰值内存与传输。

性能验收分离greedy与random、MTP1与变长draft、grow/shrink batch、不同vocab及host消费时机；观察FP32副本、softmax、D2H概率/argmax、CPU RNG、H2D uniform、copy event等待各段。先通过token/分布、seed连续性、映射与计数正确性，再比较TTFT、TPOT、接受长度、吞吐和峰值内存。本卡没有运行数据，所有数值误差、随机分布与硬件性能结论均为未知。


## 同版本 MRv1 的 310P 随机恢复不能套用 MRv2 覆盖

补充完整读取worker/v1/_310p/rejection_sampler.py106行，并复核共享sample_utils72–115；原本MRv2来源、状态、硬件未知范围与正文不变。MRv1 AscendRejectionSampler310.forward在contextmanager中临时替换sample.rejection_sampler模块的sample_recovered_tokens为绑定方法，finally恢复原引用，然后委托父forward；它不是MRv2 RejectionSampler310V2的__call__覆盖。该模块属性替换没有在本地提供多线程/多实例隔离，不能只凭finally声称任意并发安全。

恢复helper创建[batch,vocab] FP32指数噪声q，fill_exponential_310p在CPU准备generator、以active_mask=count>0控制显式seeded请求的随机数消费，再异步搬到目标device。active_mask不等于不为其他行分配/产生默认uniform；q是指数噪声，区别于draft proposal分布。是否多次调用/重排仍保留原章节的generator identity和连续性待验边界。

use_block_verify为真派发blockwise PyTorch恢复，否则普通PyTorch恢复；两者都显式传draft_probs、target_probs和噪声，IS_NGRAM按draft_probs is None决定。不能把MRv2覆盖del draft_logits、点质量CPU验证的合同扩到MRv1，或据共享文件名宣称两者probabilistic/entropy/block/synthetic全等价。recovered_token_ids以empty_like(draft ids)分配，只能消费实际有效位置；父forward与后续采样/计数必须一起核对。本节没有全文重读这两个共享恢复函数、执行随机分布或真机，继续保留未知。
