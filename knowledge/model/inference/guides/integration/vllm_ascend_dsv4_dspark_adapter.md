---
type: Guide
title: vLLM Ascend DSV4 草稿适配：mHC、合并WKV与权重重映射
description: 按DSV4的mtp权重命名接入块草稿，核对mHC辅助特征、合并Context WKV的量化前缀与额外内存、逐层SWA/TurboQuant写入及Sink重载。
aliases:
- DSparkDeepseekV4ForCausalLM
- DeepseekV4DSparkModel
- context_wkv_proj
- DSV4草稿
tags:
- task.implementation
- topic.model_adaptation
- topic.speculative_decoding
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v4/dspark.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/four_card/spec_decode/test_dspark_deepseekv4.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_deepseek_v4_dspark_context_wkv.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_dspark_vocab_mapping.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_deepseek_v4_weight_loader_reload.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v4/model.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/dsa_v1.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/model_executor/models/qwen3_dspark.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_rope_proxy.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_rope_write_back.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/rope_dsv4.py
  role: implementation
created_at: '2026-10-31T04:50:25Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-31T04:57:03Z'
---

# vLLM Ascend DSV4 草稿适配：mHC、合并WKV与权重重映射

## 任务与版本范围

为新模型适配Agent接入DeepSeek V4的块草稿，并为性能Agent定位上下文投影、额外权重、缓存写入和重载成本。依据Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2的deepseek_v4/dspark.py完整677行，配合所列缓存/模型片段和测试定义。Native 5df63a7203cdb9328d824a27b682e77c7b9928be的共享head接口是独立v0.32快照，与Main配对544f不同，不据两份代码可读就认定ABI已兼容。

本卡负责DSV4草稿模型本身的构造、Context WKV与checkpoint映射；[通用块布局与采样](vllm_ascend_dspark_block_markov_contract.md)、[量化继承与PP加载](../../runbooks/runtime/vllm_ascend_dspark_draft_quant_loading.md)、[词表概率空间](../../runbooks/precision/vllm_ascend_dspark_vocab_probability_space.md)和[部署配方](../models/vllm_ascend_deepseek_v4_deployment_contracts.md)仍分别消费。DSV4与V4.1是不同实现，整项硬件范围和模型数值未验证，保持draft/空平台。

## mtp命名不决定执行方式

DSparkDeepseekV4ForCausalLM采用DeepseekV4DSparkModel；checkpoint把草稿参数放在mtp.*，但这里不是每token顺序执行普通MTP的模块。target选定层hidden先经main_proj/main_norm组合并预计算上下文KV，草稿骨干输出整块hidden，随后消费Markov反馈和confidence。method、实际模型类与checkpoint训练协议都要保留，不能只将MTP配方的开关改成dspark。

draft配置来自speculative_config.draft_model_config.hf_config。n_mtp_layers优先，缺失时读dspark_num_mtp_layers，缺省3；int(num_layers or 3)使零值回到3，但本函数没有完整的正数/类型配置校验。运行时层key为num_hidden_layers+i，构造prefix仍是mtp.i。dspark_target_layer_ids的次序决定辅助拼接，main_proj输入宽度是hidden_size×tap数；宽度相等不证明tap语义正确。

每个草稿层复用DSV4 decoder、Attention和MoE，mHC输入embedding扩为hc_mult份。第一层关联main_proj/main_norm，最后层关联norm、Markov和HC head参数；不能将所有权重都塞进同一层。HC head在float32中做展平、均方归一、线性和sigmoid混合，再转回输入dtype；它不是每位置confidence的同一个head。

## 合并Context WKV的量化与内存取舍

context_wkv_proj将各草稿层的WKV合为一次MergedColumnParallelLinear，输出按[token,num_layers,head_dim]解释。它是运行时合成模块，checkpoint量化描述没有这个名字，因此用mtp.0.self_attn.wkv作为量化scheme选择prefix，并且disable_tp=True。这只给出当前选择方式，仍须检查各层真实格式是否适合堆叠，不能据第0层prefix认定任意混合量化都兼容。

main_proj只有在HF quantization_config.quant_method精确为fp8时传入量化对象，否则为None；embedding和合并WKV有自己的quant_config传入。格式名、target量化继承和逐层scheme是不同判断，按[ModelSlim适配](vllm_ascend_modelslim_scheme_adaptation.md)核对实际prefix、参数和处理后布局，不将所有Linear当同一精度。

_duplicate_context_wkv_weights先yield每个原始参数，只对完整匹配mtp.<数字>.attn.wkv.<后缀>且层号小于草稿层数的项，额外yield context_wkv_proj.<后缀>并附shard_id。detach的输入视图共享原storage，不是又复制一次checkpoint输入；但模型同时保留逐层WKV并分配合并投影参数，额外元素约hidden_size×head_dim×num_layers，量化元数据另计。一次投影减少launch是设计取舍，没有本卡的实测加速比或免费显存结论。

## Context KV：profile与真实写入分别判断

context_states或context_positions任一为空，函数直接返回。非空时先跑合并投影；即便context_slot_mapping=None，仍覆盖该投影的workspace profile，再返回而不做RoPE或缓存写入。因此profile跑过不说明真实context已存入，也不能为了跳过写入而跳过应计入的workspace。

真实mapping是逐层list，按层取项，某层None时跳过。函数没有像GLM适配器那样完整检查位置数、行数和list长度；调用者须提供一致的tap、位置、slot和层数。短list可在取索引时报错，不能将list存在当已验证。

每层KV先kv_norm，再对RoPE片段调用原地旋转；源码依赖rotary实现将结果写回输入storage，从而移除split/cat/contiguous复制。这里没有运行实际NPU算子，不能只比较Python返回值就宣称设备写回已证实。

一次RoPE lookup仍须包含全部实际层配置，再按rotary_emb.layername取对应cos/sin；共享代理对象不代表各层数值表相同。所读proxy测试分别覆盖共享配置和某层独立配置，不能为了减少lookup就给所有层套用第一层的表。

SWA writer遇到slot为空或cache缺失返回，只递归拆单元素list/tuple；不能把任意cache组树自动展平。TurboQuant路径先对context KV做与draft query一致的旋转basis变换，再按实际plan处理一维slot并调用write_dsa_cache；非TQ路径走基线plan的slot格式和compress_scatter。TQ缓存fixed plan、非TQ逐次保留基线选择，是已读DSA片段的边界，不代表完整kernel或所有缓存模式闭合。

模型为匹配AscendDSAImpl的草稿层共享一个OProjBufferPool，并在容量测量前reserve。池以(shape,dtype,device)复用地址；OTP关闭时reserve返回，开启时检查n_local_groups可被OTP size整除，再按捕获容量分配。其设计面向顺序层scratch，不能推任意重叠stream都可同时占用同一buffer，也不能把reserve调用当HBM已满足。

## 前向、词表与confidence接口

SP路径分片hidden和input_ids，层执行后做TP all-gather并裁回原token数；VLLM_MOE_SKIP_PADDING时临时改forward_context.is_padding，正常返回前恢复。这里没有try/finally包住层执行，不能承诺抛异常后同样恢复；错误进程/请求的后续状态需要额外处置。

wrapper接受inputs_embeds却没有把它传给内部forward，compute_logits忽略spec_step_idx。接口签名、SupportsEagle3或compile装饰器的存在都不证明多模态embedding、所有Runner或图组合已可用。

当前draft_id_to_target_id=None，map_draft_to_target直接返回id，compute_draft_logits走完整词表logits。config允许Markov侧draft_vocab_size字段，不等于此类实现了Qwen的缩表d2t加载/拒绝合同；改词表前须补齐真实head、映射与采样证据。confidence是head_hidden与前驱Markov embedding的head输出再sigmoid，不是已经测得的接受率；模块构造也不证明checkpoint确实加载了训练参数。

## checkpoint映射与失败边界

| 输入/分支 | 当前映射与检查重点 |
| --- | --- |
| mtp.i及层号 | main_proj/main_norm放第一草稿层，norm/markov_head放最后层，其他decoder项为num_hidden_layers+i；最后stage的confidence_head映射到model全局head。 |
| standalone embed.weight/head.weight | 无rotation_path时允许映射embedding/LM-head；其他非MTP项通常跳过。不能由加载返回推target参数都由此drafter消费。 |
| context_wkv_proj | 走合并参数weight_loader并传shard_id；.scale按Ascend的weight_scale命名处理。 |
| FFN gate/up和共享专家 | 只对decoder层应用堆叠映射，head-stack直接走其fallback；专家交给expert_mapping及return_success加载，不从通用字符串推全部参数同样分片。 |
| vision router e_score_correction_bias_vl | 只有该目标参数不存在时才忽略vision-only偏置；文本草稿不能把它别名成text correction bias，否则会改文本路由。 |
| 未知或越界stage | remap没有统一范围拒绝，后续直接params_dict索引仍可KeyError；不能吞掉缺失参数后声称适配成功。 |

process_eagle_weight处理checkpoint自有embedding/head标志；最终loaded_params是唯一参数名集合，不是原始张量个数、checksum、全部shard完整性或整模型事务证明。逐层写入后失败也没有统一回滚合同；保存真实加载键、scheme、shard和异常，不把“loaded N params”当验收终点。

本文件没有实现Qwen样式的post_process对齐hook；rotation_path在这里用于选择加载分支，不能仅凭字段存在就认定已经完成QuaRot旋转或PP本地词表副本。外部loader、继承方法与实际head所有权仍需沿真实调用核对，不把其他模型的后处理表直接套给DSV4。

attn_sink必须通过参数当前weight_loader（或default loader）写入；普通TP在此loader前按本rank head区间切片，DSA-CP保留完整sink。Native layerwise reload会将层暂置meta并回放被loader捕获的更新，直接copy_可能丢失更新。这里已读源测试表达这一风险，没有执行线上reload。

## 来源测试证明了哪些条件

Context WKV的4个UT定义分别检查共享reserve调用、detach storage身份和shard_id、一次合并投影/跳过None层、没有mapping仍profile投影。decoder和Linear多处用mock/Identity代替，不能作真实量化、RoPE、TQ、NPU数值或性能结果。

另读proxy测试的DSpark部分，使用真实wrapper层级定位backend impl上的TurboQuant，按有/无变换与一维/已格式化slot四种组合检查writer分派，变换、plan和writer仍为mock。RoPE写回测试把平台设CPU，将npu_rotary_mul替为x*2+1，再检查输入被修改且返回同一对象；它约束Python写回语义，没有检验实际NPU旋转数学。

Sink CPU测试保留实际loader和映射，但以16个head的最小模型替代完整网络，覆盖target/MTP/DSpark、TP1和TP2/4/8全部rank、custom/default loader、DSA-CP，以及offset100/200两次meta reload后的原storage。vocab测试只用__new__检查属性存在，没有验证恒等映射数值或缩表正确性；V4.1出现在参数化里也不补齐其实现。

已有四卡E2E定义使用UploadWeight/DeepSeek-V4-Flash-DSpark-w4a8-test、TP4、maxlen4096、indexer INT8；target配置FULL_DECODE_ONLY而draft enforce_eager=True。普通K5预期接受长度3.33，DSA-CP K7预期3.45但显式skip（V1不在默认CI路径），动态K5预期3.35并设budget3/interval1/threshold0.7。它们是来源期望值，不是本仓结果，更不是任意GPU/NPU型号或长序列的通过证明。

## Agent验收与回退

保存checkpoint/revision、最终类、tap次序、层号映射、逐层量化scheme、合并投影额外内存、slot/缓存plan与Runner。先验证权重完整、辅助特征及context写入，再核对head/Markov/采样与无投机参考；逐步增加SP、图、CP或P/D。性能分别记录投影launch、workspace/峰值HBM、通信与target verify成本，不能只报一个接受率或少量输出一致。

必要字段/权重/slot不完整、数值错误、热更新丢失或HBM预算不足时，关闭新增草稿路径并回到匹配checkpoint/配置。底层DSA、Native完整接口、Device和全部组合仍有待生产范围；本卡没有import上游、安装、构建、运行UT/E2E、服务、NPU或Agent A/B。
