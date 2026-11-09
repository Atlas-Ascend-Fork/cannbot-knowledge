---
type: Guide
title: vLLM Ascend V4 MTP 接入：HC递归状态、层号与权重加载
description: 接入V4普通MTP时核对HC维度、logits折叠与递归反馈，检查第0层权重命名、mix_placement专家加载及Sink重载，按真实Runner验收。
aliases:
- DeepSeekV4MTP
- DeepSeekMultiTokenPredictorLayer
- mtp.0.emb.tok_emb.weight
- V4MTP适配
tags:
- task.implementation
- topic.model_adaptation
- topic.speculative_decoding
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v4/mtp.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_deepseek_v4_mtp_eplb.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_deepseek_v4_weight_loader_reload.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v4/model.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/llm_base_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/spec_decode/target_dependent_ar/speculator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/target_dependent_ar/speculator.py
  role: implementation
created_at: '2026-10-31T05:26:28Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-31T05:34:54Z'
---

# vLLM Ascend V4 MTP 接入：HC递归状态、层号与权重加载

## 任务与来源范围

接入DeepSeek V4普通MTP时，先固定实际模型类、target/draft两个config、checkpoint与Runner，再分别验证递归HC状态、logits head和权重命名。依据Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2的deepseek_v4/mtp.py完整570行、专属本地MoE计数UT完整34行、已读CPU Sink重载测试，以及明确列出的spec-layer helper和MRv1/MRv2调用片段。Native 5df63a7203cdb9328d824a27b682e77c7b9928be是独立v0.32参考，不代表Main配对544f的全部接口已兼容。

本卡串联V4 MTP模型构造与加载；输出/反馈的跨模型比较见[递归状态与最终norm](../../runbooks/precision/vllm_ascend_mtp_hidden_state_contract.md)，实际共享见[LM-head归属](../../runbooks/precision/vllm_ascend_mtp_head_ownership.md)，部署见[V4模型指南](../models/vllm_ascend_deepseek_v4_deployment_contracts.md)。它与[V4 DSpark](vllm_ascend_dsv4_dspark_adapter.md)的输入特征、整块骨干和层数配置不同，不能只改method。整项硬件范围与真实数值未验证，保持draft/空平台。

## 构造、配置和输入融合

DeepSeekV4MTP创建DeepSeekMultiTokenPredictor，后者按model_config.hf_config的num_nextn_predict_layers建0起始数字字符串层，缺省1；predictor层又取speculative_config.draft_model_config.hf_config。两份config的H、hc_mult、层数、量化和版本应实际对齐，不凭同一VllmConfig就认定内容相同。

每层使用独立e_proj/h_proj、enorm/hnorm、SharedHead、V4 decoder和HC混合参数。输入embedding在position=0先置零后enorm；previous hidden按[N,hc_mult,H]解释再hnorm。e_proj(embedding)增加HC轴，与h_proj(previous HC)相加，不是旧DeepSeek的eh_proj拼接，也不是DSpark的target aux投影。

config存在index_topk时才分配max_num_batched_tokens×index_topk的INT32 buffer；is_v32只是这段实现的变量名，不能据此判定vLLM产品版本。实际cache、indexer复用和容量另需consumer证据。

## 原始HC状态与logits分支

该predictor层forward返回decoder的原始HC状态，未执行注释掉的hc_head调用。use_v2_model_runner为真时flatten(1)得到[N,hc_mult×H]，否则保留[N,hc_mult,H]。这描述本方法按布尔配置的行为，实际Worker/Runner和输入缓冲区仍需核对；类名或环境预期不能替代生效路径。

HC混合参数hc_head_fn形状为[hc_mult,hc_mult×H]、hc_head_scale为[1]、hc_head_base为[hc_mult]，均以FP32构造；参数实际权重是否完整加载仍需核对。compute_logits按当前层把输入view回HC，再执行hc_head：展平到hc_mult×H，用FP32、无weight的hc_norm归一，线性/scale/base/sigmoid加hc_eps形成混合，求和到H并转回原dtype；随后SharedHead.forward只做H维RMSNorm，再由LogitsProcessor消费head权重投影到词表。HC轴归一和最终H维norm是两个阶段，不能机械套“所有MTP只返回最终norm后二元组”。

MRv1已读_split_draft_outputs把裸Tensor同时作为logit_hidden和feedback_hidden；Native MRv2的_run_model同样两用裸Tensor，只对tuple做两项解包，Ascend再广播复制PCP的两项状态。这里V4的forward没有另造norm后feedback，不能把logits侧折叠后的H维结果反馈给下一次所需HC输入。已读片段没有闭合全部buffer reshape、capture或跨rank生命周期，适配必须验证真实shape与索引，不能只看局部函数能调用。

## SP、K与选层分别验收

SP使用sp_shard处理[N,H] embedding及[N,hc_mult,H]状态，分片的是token轴；源码说明通用2D padding方案会误补HC轴。decoder后all-gather并裁到positions的原token数；正常路径恢复forward_context.is_padding，没有try/finally保证异常恢复。decoder在本路径收到input_ids=None，哈希MoE等新decoder要求需另核，不能按相同hidden宽度直接替换。

forward和compute_logits都可用spec_step_idx % num_mtp_layers选层，但已读MRv1首步/后续及Native MRv2普通调用没有显式传该索引。配置N层、名义K、实际选层是三件事；默认参数0不证明K步轮转所有N层。源模型也没有由构造成功提供正层数、权重完整或全PP管线保证。

## 当前loader仅接受第0层命名

get_spec_layer_idx_from_weight_name在该V4 model文件中仅检查weight_name.startswith("mtp.")，命中就返回0，不解析层号或使用config。随后loader断言名字含mtp.0.并重写到runtime layer0；不能由容器能创建N层推导loader接受mtp.1或所有N层权重。

| checkpoint输入 | 当前重写与消费 |
| --- | --- |
| raw embed.weight/head.weight | 只有quant.get_name()精确deepseek_v4_fp8时先改为mtp.0嵌入/头名字；其他非mtp项通常跳过。 |
| mtp.0.emb.tok_emb.* | 提升为model.embed_tokens.*。 |
| HC参数、e_proj/h_proj、enorm/hnorm、norm/head | 放model.layers.0的非mtp_block位置；norm/head再转shared_head.norm/head。 |
| decoder项 | 插入model.layers.0.mtp_block；attn/ffn和W1/W2/W3分别按真实参数名映射。 |
| scale、router bias | .scale转weight_scale，gate.bias转e_score_correction_bias；格式和真实params_dict仍要一致。 |

no_mtp_block_in_name是子串名单，不是完整checkpoint schema；另一个_rewrite_spec_layer_name辅助方法也不能当本loader已执行的路径。SharedHead带逐层量化对象，container embedding没有传入quant参数；构造了模块不等于权重已实际加载或共享，需要检查每个实际消费者。

## 专家加载、计数和Sink更新

loader先调用AITER共享专家开关方法，但结果立即被Ascend mix_placement覆盖；最终条件取后者，不能从rocm变量名判断实际控制权。初始调用自身仍有依赖，不据覆盖赋值宣称任意包版本都可导入。

mix_placement启用时将shared experts追加到routed experts之后；widened共享权重按专家数切chunk，gate/up按dim0、down weight字符串分支按dim1，并要求该维整除。随后交expert-aware weight_loader和return_success处理本地专家；量化scale、分片与副本仍需实际布局证据。stacked mapping当前仅列gate/up→gate_up_proj，不能因可选QKV注释或条件就声称本表支持QKV融合。

loaded_params是记名集合，不是全部输入tensor、shard或实际写入的验证。部分跳过位于内层chunk循环，continue不必然退出外层weight循环，外层仍可能记入原名；缺param或后续失败也没有整模型事务回滚。验收应记录真实loader调用、目标参数与必需key/scale，不用“loaded N”或无异常代替完整加载。

Sink走参数当前weight_loader或default loader，普通TP用head_start/heads_per_rank切片，DSA-CP保留完整sink；不能改成直接copy_绕过layerwise-meta回放。既有CPU测试覆盖target/MTP/DSpark最小16-head模型、TP1和TP2/4/8各rank、custom/default、DSA-CP与两次更新，未由本批执行，也不覆盖全模型、SP、图或所有NPU组合。

set_moe_parameters按实际本地层收集MoE，num_moe_layers=len(moe_layers)，不是全局num_nextn_predict_layers。34行UT以配置4层、fake本地2层断言计数2；这不证明构造器已正确做PP分区或EPLB运行收敛。通用路由/权重迁移继续按[EPLB接入](vllm_ascend_eplb_model_weight_contract.md)验收。

## Agent交付、测量与回退

保存实际类、两个config、raw HC的shape/dtype、position0处理、每次spec_step_idx、每层head/embedding对象、权重原名→目标名→shard/expert、真实加载与Sink更新记录。先确认递归状态和logits分支，再对齐无投机参考与K步接受/拒绝、抢占和混batch；多层权重、真实PP、图和共享缓存需逐项验证。

性能分别记录draft计算、HC投影/折叠、head、target verify、通信和新增HBM，使用相同模型/采样/负载与端到端口径，不把接受率或局部launch数当净收益。shape、必要权重、选层、Sink或输出不符时关闭新增MTP路径并恢复匹配版本/配置，不删assert或改层号掩盖问题。

本卡只完成所列源码范围与测试定义的知识生产；没有上游import、安装/build/测试、服务、NPU或Agent A/B，Native、完整decoder/Device与所有模型硬件组合仍待继续闭合。
