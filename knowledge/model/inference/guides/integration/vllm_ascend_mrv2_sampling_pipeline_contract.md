---
type: Guide
title: vLLM Ascend 常规MRv2采样：参数管线、补丁接线与异步输出
description: 沿 apply_top_k_top_p_npu、SamplingStates、LogprobTokenIdsState 与 SamplingMaskTensors 核对处理顺序、融合采样门控、categorical RNG、raw/processed分数、Trace Replay及AsyncOutput消费；保留配对版本、旧新函数名和mask签名边界。
  apply_top_k_top_p_npu负责常规MRv2的top-k/top-p参数加工。
aliases:
- apply_top_k_top_p_npu
- SamplingMaskTensors
- LogprobTokenIdsState
- SamplingStates
- PROCESSED_LOGPROBS_MODES
- apply_trace_tokens
- apply_top_k_top_p_npu：常规MRv2采样参数过滤
tags:
- task.implementation
- task.debugging
- task.optimization
- topic.model_adaptation
- topic.precision
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_v2/patch_triton.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/sample/apply_top_k_top_p.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/sample/min_p.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/sample/gumbel.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/sample/logprob.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/sample/trace_replay.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/v2/sample/sampling_mask.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/v2/sample/categorical_sample.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/sample/penalties.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/sample/bad_words.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/v2/sample/fill_logprob_token_idx.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/worker/test_patch_v2_gumbel.py
  role: evidence
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/sample/sampler.py
  role: primary
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/sample/states.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/sample/output.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/sample/logprob.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/sample/logits_processor/interface.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/sample/trace_replay.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/async_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_runner.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/model_runner.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/sample/ops/topk_topp_sampler.py
  role: constraint
created_at: '2026-11-02T08:27:23Z'
updated_at: '2026-11-03T07:29:07Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 常规MRv2采样：参数管线、补丁接线与异步输出

## 接入任务与固定范围

新模型接入常规MRv2后出现参数未生效、固定seed变化、logprobs与强制token错配、mask返回失败或CPU过早读取结果时，先沿默认Sampler、模块补丁、输出表示和异步消费建立完整调用表。本卡解释普通采样管线，不能把它直接套到模型状态替换的custom_sampler，也不能用函数同名代替版本匹配。

Main固定ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，独立Native固定5df63a7203cdb9328d824a27b682e77c7b9928be。23个选定范围为21全文与2有界：Main patch_triton80行、7个worker/sample实现67/91/274/171/43/225/185行、categorical440行、sampling_mask111行、fill_logprob54行及UT91行；Native Sampler356行、SamplingStates132行、Output202行、Logprob271行、processor接口158行、TraceReplay113行和AsyncUtils277行全文。Main worker入口90行与pin全文；regular Main Runner仅1104–1215，Native Runner仅425–514、1592–1720、2088–2275。Native topk wrapper另由固定Git对象只读450–570行，保持defer依赖，不计新增覆盖。

Main实际配对pin是544f182d9f0c9bfe8bd7645525951d5e3692a542，独立5df不是该pin。本卡指出跨快照接口差异，没有证明生产配对发生相同错误；全部源码、kernel和测试定义只作数据，未导入、运行或编译。保持draft、空平台和framework=vllm的部分Scope，实际模型、硬件、NPU图、数值与性能均待验证。

[310P采样](vllm_ascend_310p_sampling_contract.md)拥有其CPU generator、逆CDF和参数拒绝；[ModelState协议](../../concepts/frameworks/vllm_model_state_protocol.md)拥有custom_sampler钩子；[输入坐标](vllm_ascend_v2_request_input_coordinates.md)与[UVA元数据](vllm_ascend_uva_metadata_contract.md)拥有持久slot、当前batch和staged buffer。本文复用这些入口，新增实际参数加工、分数及输出的合同。

## 先确认默认对象与真实模块绑定

Main worker入口在HAS_TRITON为真时导入patch_v2.patch_triton，这发生在STANDARD_WORKER_PATCHES能力分支之前；不能仅凭硬件名字或该capability判断采样补丁是否装载。独立Native仅在最后PP rank且非pooling模型构造默认Sampler或watermark sampler，随后model_state.custom_sampler仍可替换sampler/rejection_sampler。

patch_triton分别重绑已提前导入函数的sampler、gumbel、base speculator、DSpark和EAGLE模块；只改定义模块不保证旧的from-import引用更新。UT91定义了这五个consumer的绑定身份检查，以及mock DSpark参数分发；它绕过构造、替换实际采样，不是NPU或完整模型证明。

记录每进程实际类/MRO、函数的module/qualname与签名、HAS_TRITON、实际watermark/custom sampler、融合分支布尔值和版本pin。Main的lmhead TP分支复制了部分Native sample分发；Native另有batch-sharded采样和空owner-rank分支。这里没有闭合各自的分片/恢复实现，不能据dispatch尾部相似就声明所有并行路径一致。

## 请求slot、staged写入与处理顺序

LogitsProcRequestState是frozen视图，但引用的请求缓冲由Runner原地更新；processor必须只读这些字段。slot会复用，add_request必须覆盖或中和前一请求的状态。LogitsContext的行对应logit row，expanded_idx_mapping映射到持久slot，不能把它与idx_mapping的batch行号交换。

Native Sampler.add_request合并SamplingStates、thinking budget及各processor的needs-processing标志，并更新logprob token-ID和可选trace状态。apply_staged_writes提交各自写入；接口声明它在请求状态刷新后、forward前按步调用。自定义processor的apply接收整批，包括add_request返回未启用的请求，必须自己用映射过滤行，不能假定框架已切出子batch。

固定顺序是logit_bias、penalties、bad_words、custom processors，再由thinking-budget forcing最后决定强制结束标记，随后temperature、min_p和top-k/top-p。bias加法与penalty缩放不交换；custom processor不能重新放大grammar已屏蔽的token，也不能覆盖thinking forcing的优先级。Runner可在进入Sampler前应用grammar，所以这里的raw logits不是必然未被grammar修改的compute_logits原始矩阵。

所有请求均不需要加工时，apply_sampling_params直接返回输入logits；否则先复制为FP32。不能把“常规Sampler总会FP32拷贝”写成不分条件的结论。processor返回新tensor与原地修改都被接口允许，适配方还需核对dtype、shape、词表和返回对象生命周期。

## SamplingStates与融合分支的门控

SamplingStates把top_k<=0或大于vocab的值规范为vocab；top_p与top_k有初始有效默认值。seed是否显式设置单独保存在seeds_set，未设置则生成seed；显式0同样是显式seed。logprobs=None使用NO_LOGPROBS=-1表示未请求，而用户logprobs=-1转为全vocab；logprobs=0仍可要求选中token的分数。

temperature为0表示greedy，为0或1时跳过温度kernel；这与310P的1e-5 random阈值不同。Native在有任何greedy、任何显式seed、请求processed logprobs，或根本没有top-k/top-p时不走融合采样；return_sampling_mask在构造时还禁用融合标志。实际是否使用FlashInfer/XPU仍取决于支持谓词及对象状态，Main重绑gumbel不覆盖已经选择的融合路径。

sample先加工但暂缓top-k/top-p，再按实际路线执行融合采样或mask加随机采样；不要重复温度缩放。Main apply_top_k_top_p_npu对0.32.0提供三参数，对main额外接受has_topp_only_rows但不消费该值。固定Native wrapper在无k/p时直接返回，HAS_TRITON为真时才调用被重绑的helper。

Main参考helper先计算并排序概率，再分别使用k与p屏蔽；已读Native非Triton fallback先在排序logits上做k，再对其结果softmax计算p。两处处理次序不同，不能未经数值验证宣称任意k/p组合完全等价。严格小于cutoff的比较还会保留边界ties，实际支持token数不保证恰好等于top_k。

## categorical替换与随机数、工作区边界

实际patch把gumbel_sample名字绑定到categorical_sample。Main实现先按8192粗块建立argmax、max、mass和8个1024细块质量，再用一个uniform选择粗块、细块与token；不能只因旧函数名就描述为逐词表Gumbel噪声。随机key来自请求seed与转为int32的position，draft另加1<<30盐；它不使用310P的CPU generator对象缓存。

use_fp64明确抛NotImplementedError；wrapper保留新旧位置参数顺序的桥接并检查logits_cache词表宽度。cache在温度处理之前写入；regular Native调用传apply_temperature=False避免重复缩放。空token批次有提前返回，但非法shape、零vocab、全NaN等任意输入并没有在这里完整预检。

随机分支没有正总质量时源码回落到token0；这不是有效grammar或概率分布已通过的证据。验证全屏蔽、NaN/Inf、极端温度、ties、请求重排/slot复用、同请求多行、position与draft盐，并比较多步分布和seed连续性，不能只比首token。

metadata工作区按token数与粗块数分配多组tensor，输入FP32副本、top-k/top-p排序、输出和cache又各有内存。8192/1024是固定实现参数，不是全硬件最优结论；先通过数值和生命周期，再量每段kernel、排序、临时分配、峰值内存与净token时延。

## raw/processed分数与custom token-ID的实际调用链

get_logprobs_dims仅在所有请求都无logprobs且custom token-ID宽度为0时返回None。Native Sampler实际调用compute_topk_scores；processed模式使用processed_logits，raw模式保留进入Sampler的张量。raw_logits/processed_logits分支返回gather后的FP32 logits，其字段仍叫logprobs，不能一律按归一化对数概率解释。

Main补丁写入sampler.compute_topk_logprobs，但独立5df Sampler调用的名字是compute_topk_scores。这一函数对象仍通过Native logprob模块全局名调用已被替换的compute_token_logprobs和_fill_logprob_token_ids_kernel。旧Main compute_topk_logprobs遇custom IDs的warning/fallback，仅说明真实进入该函数的路线；不能概括成独立5df整条custom logprob_token_ids均被拒绝。

LogprobTokenIdsState保存每slot数量及staged token-ID数组，超MAX_LOGPROB_TOKEN_IDS抛ValueError。Native compute_topk_scores按请求选择custom IDs或top-k，始终保留sampled列，并用valid mask屏蔽未填位置；Main fill replacement把动态地址load移入if/else，NUM_TOPK=0时有独立分支。这是源码动作，不是编译器或任意token-ID范围已验证。

Native原compute_token_logprobs把每轮gather宽度限制到1024；被Main函数重绑后使用整段PADDED_TOPK并设BLOCK_SIZE=12944，不自动继承该上限。全vocab分数和大批请求应单独核对临时矩阵、kernel工作区及warmup覆盖。Native selected-rank kernel比较>=，旧Main rank kernel比较>；ties与基数可能不同，先确定实际调用对象，不能给整框架统一套一个rank定义。

## Trace Replay与mask的版本合同

trace在采样后、分数计算前覆盖sampled token，step由total_len-prompt_len得到；返回的是当前分布中被强制token的分数，不证明模型会自发生成该序列。Main apply_trace_tokens额外防止零请求kernel launch。服务入口、权重版本隔离和开关条件仍见[RL与Trace Replay](vllm_ascend_rl_weight_update.md)。

独立Native SamplingMaskTensors.from_logits接收cu_num_logits、num_sampled、max_num_kept及可选rows_per_request，保存固定请求槽、compact IDs、完整counts与packed bitmask；compact宽度最多2048，超过compact宽度的行由little-endian bitmask恢复精确支持集。counts统计finite logits，NaN和正负Inf不在支持集中，不能用top_k替代实际count。

Main sampling_mask_from_logits_npu的签名没有cu_num_logits或rows_per_request，返回的旧/四字段分支与独立5df接口不同；Native Sampler的调用也传了该cu参数。该静态跨快照差异需要按真实paired544安装核对，不能未经执行直接断言生产环境必然报错，也不能称继承后自动兼容新API。

Main对词表stride非1的logits调用contiguous，并在compact路径返回零宽token_ids以触发packed-mask解码回退；这增加复制或CPU解码的可能性，注释的临时规避原因不等于已经测得净性能。重建支持集时核对行布局、vocab、有效采样数、固定槽和位序；这里未验证MTP多槽或任意并行bucket可直接复用。

## 异步输出先复制，再更新与消费

独立Native sample_tokens在最后PP rank采样、可选广播并计算prompt分数后创建AsyncOutput，然后才postprocess_sampled及draft proposal。普通Sampler的num_sampled/num_rejected仍由prefill与有效行合同决定；不是把sampled矩阵所有行都当客户端可输出token。PCP恢复仅作为调用边界，内部global/local、图桶及一次性flag由其专用生命周期解释。

AsyncOutput保留GPU对象引用，使不同stream上的copy不提前失去源tensor；copy stream等待main stream，发起token、logprob、mask、计数及其他输出的D2H，最后记录blocking copy_event。get_output先等待该event，再按num_sampled裁剪每请求token并转换mask/logprob。to_cpu_nonblocking或拿到NumPy view不等于数据已可读，不能提前释放/复用源buffer或跳过完成事件。

postprocess_sampled随后委托post_update更新token历史、total_len、computed数、penalty计数并调用model_state.postprocess_state。本卡没有闭合该kernel、所有connector、PP/PCP和模型资源退役；输入坐标与状态所有权沿既有卡继续核对。AsyncUtils中torch.cuda的流合同也不构成Ascend运行时兼容证明。

num_nans仅在compute_nans使能时产生，而且采集点在Sampler参数加工之前；Runner此前的grammar修改另算。AsyncOutput只有拿到num_nans才按VLLM_RAISE_ON_LOGIT_NANS判断抛错；None或未告警不能证明finite。Runtime Guard另有窗口、延迟分类与请求映射，见[logits告警归因](../../runbooks/precision/vllm_ascend_runtime_guard_logits_attribution.md)。

## Agent验证与回退顺序

先保存真实进程/类/函数绑定、Main与配对Native、参数mode、请求slot/batch/logit映射和buffer地址。覆盖无加工/加工、custom processor启停、复用slot、全greedy/混合seed、各分数模式、custom IDs、trace、mask宽支持、非连续词表、chunked prefill、空owner rank及异常输出，再验证配对签名、图/eager和数值。

[图后端logprob验收](../bringup/vllm_ascend_graph_logprob_validation.md)提供特定短序列测试判据，不能替代全词表、同prefix、多步随机分布或异步生命周期验收。发生签名、索引、token/分数对应或事件错误时，保留原始结果并恢复已确认配对与执行配置；正确性通过后，再比较TPOT/吞吐、峰值内存及处理、采样、D2H、CPU解码各段。本次没有模型、NPU、UT、JIT、图、精度、性能或Agent A/B运行结果，也未登记verified。
