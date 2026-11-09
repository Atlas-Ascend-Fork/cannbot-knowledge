---
type: Guide
title: "vLLM Ascend MRv2拒绝采样：验证坐标、残差重采样与有效输出（rejection_sample）"
description: "沿 rejection_sample、_probabilistic_rejection_kernel、resample、_categorical_finalize_kernel、_compute_local_logits_stats_kernel 与 stats_num_logits 核对MRv2验证和残差重采样，区分完整proposal与点质量、block与synthetic、请求坐标、RNG位置盐及num_sampled有效前缀，保留paired544和独立5df边界。 补充共享PyTorch greedy的变长、bonus、synthetic及310P输出/host容量边界。"
aliases:
- rejection_sample
- _probabilistic_rejection_kernel
- resample
- _categorical_finalize_kernel
- _compute_local_logits_stats_kernel
- stats_num_logits
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.speculative_decoding
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/rejection_sampler_utils.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/v2/spec_decode/resample.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/v2/test_spec_decode.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/triton/test_resample.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_v2/patch_triton.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/rejection_sampler.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/rejection_sampler_utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/v1/worker/gpu/spec_decode/rejection_sampler_utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/sample/rejection_greedy.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/worker/v2/rejection_sampler.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/sample/rejection_sampler.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/test_rejection_sampler_310p_buffer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/worker/v2/spec_decode/rejection_sampler_utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/spec_decode/entropy_verify.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/docs/source/user_guide/feature_guide/speculative_decoding.md
  role: constraint
created_at: '2026-11-02T10:59:39Z'
updated_at: '2026-11-04T03:49:24Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend MRv2拒绝采样：验证坐标、残差重采样与有效输出

## 接入任务与证据范围

接入新草稿模型后出现接受长度错误、恢复token分布异常、请求换槽后token串扰、有效输出尾部污染或版本迁移异常时，沿target验证、接受前缀、拒绝或bonus恢复、有效计数逐段核对。本卡拥有MRv2默认NPU验证和残差重采样合同；[普通采样管线](vllm_ascend_mrv2_sampling_pipeline_contract.md)保留参数处理、补丁及异步输出，[310P采样](vllm_ascend_310p_sampling_contract.md)保留CPU generator与inverse CDF，[DSpark块采样](vllm_ascend_dspark_block_markov_contract.md)保留proposal生成和Markov反馈。

Main固定ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，选定8个范围为5全文、3有界：全文读取rejection_sampler_utils.py521行、resample.py481行、worker/v2/test_spec_decode.py290行、MRv2 patch_triton.py80行和pin1行；有界读取resample E2E的1–85/320–590、utils710–748及独立Native rejection_sampler147–215/243–291/400–470。UT全文阅读不代表其全部speculator分派均由本卡完成生产。

另三份约束依赖保持未新增绑定：独立Native5df的rejection_sampler_utils.py1–505、实际paired544同文件185–348/398–574，以及Main共享PyTorch greedy111行。两份Native文件按各自commit读取，不用当前checkout替代paired Git对象；已有Native caller、patch、utils和pin的canonical owner保持。来源、UT和E2E均只作数据，未导入上游、执行测试、编译或运行NPU，保持draft、空平台与framework=vllm部分Scope。

## 先固定入口和四类坐标

Main补丁同时替换Native rejection_sampler_utils.rejection_sample和rejection_sampler.rejection_sample；只修改定义模块可能遗漏此前导入的函数引用。还应确认模型是否通过[ModelState协议](../../concepts/frameworks/vllm_model_state_protocol.md)返回custom sampler，而不是假定所有Runner均经过这条默认实现。

| 对象 | 坐标 | 接入约束 |
| --- | --- | --- |
| req_idx、cu_num_logits | 当前batch请求行及紧凑logit前缀 | 每请求最后一行是bonus；请求行不是持久状态槽 |
| idx_mapping、expanded_idx_mapping | 请求行或logit行到持久request slot | temperature、seed与draft logits缓存按真实slot寻址 |
| expanded_local_pos | 本请求的草稿局部步号 | 不用全局logit行代替draft_logits第二维 |
| draft_sampled、pos | 验证token与位置流 | 验证第i行读取后一个位置的draft token，bonus另走恢复 |

所读Native caller先保存真实draft ids，再用invalid_drafts构造仅供验证的-1副本；参数处理与watermark上下文仍消费真实ids。[Grammar合同](vllm_ascend_grammar_mask_contract.md)拥有invalid标记的生产责任，不能仅给target logits加mask却遗漏这条验证输入。Main随机验证会先把负draft id夹到安全地址再拒绝它，不能把该中间地址解释为接受token0，也不能由此推导任意正越界id都有检查。

## processed target与raw draft必须匹配真实proposal

caller的sampler.apply_sampling_params先产生processed target logits；draft logits来自按持久slot和草稿步缓存的raw值，Native统计helper与Main恢复都按temperature缩放draft。不能对已处理target重复温度缩放，也不能把已经缩放的draft当raw再次除温度。

概率校正需要缓存所表达的q与真实proposal生成分布一致，包括token ID空间、mask、温度和其他处理。只提供同shape的logits或让函数返回成功，不证明新模型的自定义proposal满足这个前提；本卡没有闭合所有proposal生产者。

draft_logits=None表示点质量proposal，代码令log_q=0；它不表示任意未知q。Main把None换成1×1×1 dummy以提供有效pointer/stride，同时保留HAS_DRAFT_LOGITS=False。下游resample显式传入has_draft_logits=False才能保留相同语义，不能仅凭Tensor非空推断存在完整proposal分布。

## 版本分支决定统计buffer是否正确生产

stats_num_logits在精确0.32.0分支取num_speculative_steps，其余分支取真实num_logits，再传给导入的统计与局部残差helper。独立5df helper使用草稿步上界识别bonus；实际paired544选段使用num_logits及_is_bonus_logit的有界look-ahead，以后一行local position回到0识别请求尾部。

这两种同位置整数不是可以互换的调优参数。参数语义不匹配会改变哪些new_empty统计项被写入；不能把签名能调用当作初始化覆盖正确。本卡只确认所读两快照及Main选择逻辑，不宣称全部paired ABI、配置或安装环境通过。

vllm_version_is优先读VLLM_VERSION，否则读安装包版本，按PEP440 public版本比较并缓存结果。迁移时同时记录Main、实际Native commit、安装版本及环境覆盖，不能只按requirements标签或修改环境后期待既有方法自动重定义。

## greedy、概率、synthetic与block分开判断

_probabilistic_rejection_kernel对每请求从cu_num_logits取得验证行数，按实际temperature分支。普通greedy仅在draft等于target argmax时接受，并提前写target argmax作为拒绝恢复值。随机完整q路径比较`target_log_prob > log(u) + draft_log_prob`，点质量路径令后项为0；负draft占位不能接受。

synthetic按局部step读取conditional rate，以u<rate接受有效draft，即使它与target argmax不同；接受时保留draft，拒绝时仍需要真实target统计用于恢复。因此synthetic接受率不是模型正确率或无损加速证据。use_block_verification与非None synthetic_conditional_rates在分配、launch前显式互斥，不能当两个任意可叠加开关。

block随机路径另消费cumulative_log_p和下一位置残差质量。Main以prefix ratio与残差质量构造h，u<=h时把rejected_step更新为i+1，否则保留此前值；不能把这个更新协议改写成普通逐token比率检查的首次失败即停止。只有最终选定前缀和恢复位置可输出，暂写到矩阵其他列的draft不自动变成接受结果。greedy请求即使配置block，仍按greedy分支处理。

验证采用8192宽词表块，recovery采用1024宽块，二者的block索引不能混用。关键request slot与起始logit索引在指针算术前升int64，而RNG位置仍转int32；宽地址不等于随机位置也具有相同范围。

## 恢复分支与残差分布

resample读取验证写下的rejected_step，恢复第一枚未保留token或bonus，最后推进num_sampled一次。它不重新执行整条验证链，也不统一对所有请求相减q。

| 恢复位置 | 实际消费 |
| --- | --- |
| greedy、非bonus | 保留验证kernel已写的target argmax，只推进计数 |
| greedy bonus | 从各词表块的target最大值选择全局argmax |
| 随机bonus或invalid draft | 按当前target分布重采样，不减proposal |
| 随机有效draft被拒绝 | 完整q使用max(p-q,0)残差，点质量将被拒绝token质量置0 |

block完整q残差额外用已接受前缀ratio缩放target，形成正部`ratio*p-q`；计算块质量和最终选中块内token质量两阶段必须一致。点质量路径归一化时该共同因子抵消，不借此把任意full-q简化为删除一列。

_resample_kernel先按request×vocab block分配任务，计算局部质量；_categorical_finalize_kernel用一个uniform在全词表总质量区间定位块，再在该块内找token。不是每块独立抽样再随意选一个结果。bonus使用不同块的局部最大值时还需转换到同一尺度，否则跨块质量会错。

源码以position+(1<<29)给随机残差恢复区分RNG域；bonus保留原位置，不能直接沿用普通categorical的(1<<30)盐或310P CPU generator生命周期。seed、位置转int32及版本共同影响结果；这不证明任意位置范围下都不碰撞，也不提供跨实现同seed逐token一致的保证。验证抽样还夹离0以保持log(u)有限，不能据此声称FP64概率精度。

## 词表、容量和有效输出

完整draft存在时，两阶段均取min(target_vocab,draft_vocab)作为有效宽度。来源解释目标尾部可能来自padding；迁移必须证明token ID对齐及被裁部分确为padding，不能把任意缩小draft词表当作保留target全部概率质量的优化。词表映射见[DSpark概率空间诊断](../../runbooks/precision/vllm_ascend_dspark_vocab_probability_space.md)。

resample要求词表维contiguous，target词表为空显式拒绝；has_draft_logits=True还要求非None且draft词表维contiguous。它没有全面校验任意shape、dtype、正token范围、有限logits或温度，所有词质量为0时存在fallback token选择，不能当作有效分布证明。resample的num_reqs=0会返回，不由此推导上层整个rejection_sample空batch的分配和launch也已验证安全。

sampled按[num_reqs,K+1]用new_empty分配，验证和恢复只承诺num_sampled有效前缀。非前缀列可能未初始化或是block分支的暂存draft；不能通过统计整矩阵非负数恢复接受长度。最终caller还按prefill、seq_lens与请求映射修正num_sampled/num_rejected，异步输出等待D2H event后才按真实计数裁剪；这些职责分别沿普通采样与Runner合同核对。

use_fp64、fly_window_size>0以及任一非None watermark相关参数都会显式拒绝。接受这些关键字只为保留caller接口，不能删除guard来宣布FLy、水印或FP64已适配；历史熵阈值放宽规则也不因为出现block标志就自动接入此MRv2实现。

## Agent验证与性能拆分

所读UT定义block与synthetic互斥检查；E2E选段定义None/dummy等价、打乱request slot映射、target bonus分布、正部p-q、跨1024边界的block残差及点质量排除。fixture设4096次试验和0.03绝对容差，部分测试按A2/A3/A5跳过；这些只是该测试定义，不是执行结果或整卡硬件支持范围。本次未运行它们。

Agent先保存实际入口/补丁与custom sampler、版本分支、真实q生产方式、四类坐标、每请求实际草稿数、词表映射、温度/seed/position、rejected_step及最终num_sampled。先验证greedy有效前缀，再用可解析分布检查随机bonus和残差，覆盖零接受、全接受、占位draft、混合greedy/随机、请求换槽、词表块尾、部分-Inf及全零质量、None/dummy、synthetic与block，以及分chunk和整批的一致性。

只有功能与分布验证通过后，才分别测logits加工、8192统计、验证、1024残差归约、临时buffer及输出搬运，再比较接受率、有效输出token、TTFT/TPOT与端到端吞吐。接受率变化或CPU Query耗时不能作为NPU推理收益。失败保留概率和映射证据，恢复匹配版本与已验证采样配置；本卡没有新增模型、NPU、性能或Agent A/B结果。


## 共享 PyTorch greedy 回退：请求步数与有效前缀

固定 Main 的 rejection_greedy.py 共111行，是310P MRv2和MRv1共同使用的PyTorch helper；所在worker/v2目录表示共享代码归属，不能据目录名裁定所有调用方代际。补读310P caller的116–177行与MRv1 caller的500–563行，只闭合这里的行映射/分派，不把两个caller整文件计为全文。本节未执行PyTorch、UT或NPU。

单草稿快路径要求每请求恰好一枚draft，assert batch_size等于draft token数。普通模式始终在第0列写target argmax，仅draft相等时写第1列bonus；synthetic模式按rate[0]与uniform比较，并拒绝负draft，接受时第0列写draft、拒绝时写target。bonus实参需匹配实际squeeze(1)：310P caller构造[B,1]，不能照helper旁的[B]注释直接传一维Tensor。

变长路径从累计draft数减每请求draft数得到起点，repeat_interleave建立token到请求的映射，再找每请求首次不接受位置。普通模式比较draft与target argmax；synthetic按请求局部步查rate，接受时写draft、首次拒绝时写target。copy_len=min(first_mismatch+1,draft_count)，全接受在draft_count列补bonus，零draft请求在第0列补bonus。max_spec_len=0有单独分支，不依赖对空维求min。调用方必须提供相互一致的累计数、每请求数、紧凑token顺序和足够输出宽度；helper不是这些元数据的完整校验器。

is_greedy只允许本helper写greedy请求的相应位置，随机行留给后续路径；非有效尾部保持原值。MRv1只在所有请求greedy且draft数全为1时选单步快路径，混合batch走通用helper，再继续随机采样。310P caller另把每请求最后一行视为bonus，变长映射移除交错bonus行；不能把带bonus的logit累计数直接当紧凑draft索引。

310P caller先以-1填满输出，再用非-1数统计num_sampled，并把未完成chunked prefill计数置0。这一具体初始化约束不同于前述标准MRv2的new_empty加显式计数，不能把整矩阵非负计数迁移给后者。快路径不接受时第1列也留原值，复用未清理buffer会污染计数；输出前缀与调用方初始化须一起验收。

专项70行UT只定义host buffer容量回归：mock父类/NPU/pin后初始化容量32，先向前1行copy，再向前4行copy，断言容量没有缩小。它不运行完整采样路径，也不证明greedy、synthetic、分布或310P设备正确性。Agent需另在目标环境验证变长/零draft、全接受/首拒绝、混合greedy、batch缩小后扩张及异步输出；这里的读取没有新增任何执行结果。


## 2026-11-03 main 增量：熵验证接入与标准拒绝器分界

本节新增固定3164adc8fe75892fbf7f99f524bb72fddf1e6efd，rejection_sampler_utils.py只读取相对ceac的完整变更hunk，entropy_verify.py全文读取；不是新提交整份caller/全部Device实现闭包。旧ceac正文中未接入熵阈值的结论保留其版本边界。新提交pin仍指paired544，未运行上游或NPU。

rejection_sample新增use_entropy_verify可选实参：None才从Ascend配置读取enable_entropy_verify与两个posterior参数，显式布尔值绕过该配置读取。entropy与use_block_verification同时为真在launch前ValueError；随后synthetic存在时关闭entropy。实际启用时校验threshold属于(0,1]、alpha>=0。不能用“额外kwargs被接收”推旧版本已有此行为，也不能据synthetic优先就删除block互斥检查。

alpha>0才分配entropy_partials并增加按logit行×词表块的扫描。helper用target已有max/sumexp合成全局LSE，对采样参数处理后的logits计算FP32概率及带epsilon的熵局部和；greedy或不属于draft步的行写0。温度在此用于区分greedy，不能再把processed target除温度。alpha=0跳过词表扫描，但仍按常量posterior_threshold放宽概率比率条件。

随机普通分支新增_entropy_verify，比较p/q>=threshold*u，要求q>0；synthetic分支在前仍以配置rate判断，greedy另走原分支。alpha>0的threshold=min(exp(-H*alpha),posterior_threshold)。这是改变接受准则的近似模式，不能沿用标准拒绝器的分布保持结论；恢复采样仍须按真实proposal与有效前缀核对。新文件也迁移resample到ops/triton/spec_decode路径，并从实际Native导入_TL_RAND_MIN；目录重排和名字相同不证明旧导入路径或任意Native版本ABI兼容。

性能比较需单独计熵扫描、临时buffer、额外接受token与target/draft计算，再测端到端质量及吞吐。没有运行测试、模型或设备，本节不增加硬件范围、verified或性能结果。
