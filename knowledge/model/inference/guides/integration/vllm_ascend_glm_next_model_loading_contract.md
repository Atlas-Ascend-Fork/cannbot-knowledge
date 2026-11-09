---
type: Guide
title: vLLM Ascend GLM-Next整模接入：混合层、PP状态与权重加载
description: 适配GLM-Next时按实际层配置组织KDA/MLA与MLP，保留跨PP的mHC状态和SP限制，核对checkpoint映射、FP8 WK/scale配对与分片加载完整性。 核对mHC pre/post的hc_mult=4、V2/V3返回顺序、BF16/FP32布局与真实Host/Meta差异，保留950和非950 tiling边界。
  以Glm5NextModel.load_weights核对checkpoint的target/MTP跳层、融合shard映射和FP8 WK/scale按层配对，不把fused name命中当所有权重分片已到齐。
aliases:
- GLM-Next整模接入
- Glm5NextModel
- Glm5NextDecoderLayer
- _try_load_fp8_indexer_wk
- Glm5NextDecoderLayer.hc_pre：Host形状门禁
- torch.ops._C_ascend.npu_hc_pre_v3
- torch.ops._C_ascend.npu_hc_post
- Glm5NextModel.load_weights：checkpoint融合分片加载
tags:
- task.implementation
- topic.model_adaptation
- topic.precision
- topic.speculative_decoding
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/model.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/ops/mhc_ops.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_loader_compat.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_pp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_mhc.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_sfa_routing.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/attention.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/mla.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/kv_cache.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/indexer_kpool.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_pre/op_host/hc_pre_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_post/op_host/hc_post_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_pre/op_host/hc_pre_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_post/op_host/hc_post_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_pre/op_host/hc_pre_tiling_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_post/op_host/hc_post_tiling_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding_meta.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_post/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_post/op_host/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_post/op_host/hc_post_proto.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_post/op_host/hc_post_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_post/op_kernel/hc_post.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_post/op_kernel/hc_post_bfloat16.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_post/op_kernel/hc_post_d_split.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_post/op_kernel/hc_post_float32.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_pre/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_pre/op_host/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_pre/op_host/hc_pre_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_pre/op_kernel/hc_pre.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_pre/op_kernel/hc_pre_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_pre/op_kernel/hc_pre_base_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_pre/op_kernel/hc_pre_cube_compute.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_pre/op_kernel/hc_pre_cube_compute_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_pre/op_kernel/hc_pre_m_k_split_core.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_pre/op_kernel/hc_pre_m_k_split_core_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_pre/op_kernel/hc_pre_m_k_split_core_premix_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_pre/op_kernel/hc_pre_m_split_core_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/hc_pre/op_kernel/hc_pre_m_split_core_premix_arch35.h
  role: implementation
created_at: '2026-10-31T09:56:04Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-03T07:29:07Z'
---

# vLLM Ascend GLM-Next整模接入：混合层、PP状态与权重加载

## 消费任务与固定证据

新模型框架适配先按config确定每层类型和真实执行分支，再核对模型/PP状态与checkpoint producer-consumer。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2：本卡全文读取model.py 1114行、mHC shape helper20行、loader/PP/mHC/SFA routing UT47/143/68/92行；attention324、ops/mla316、缓存层288和KPool backend857复用同SHA全文记录。utils.py 1922行仅取196–217、1027–1039、1868–1876。

Native AutoWeightsLoader、scaled_dequantize、KDA/MoE/CANN实现和完整vision/processor没有由这些源码闭合。全部文件作为数据，未导入上游、运行UT、加载checkpoint、JIT或执行NPU/HCCL；整项硬件与实际软件栈交集待验，保持draft/空平台。部署角色与checkpoint条件沿[GLM-5.3-Flash](../models/vllm_ascend_glm53_flash_hybrid.md)保留。

本卡补足整模编排和加载；[MLA包装](vllm_ascend_glm_next_mla_wrapper_contract.md)负责投影/参数路径和backend factory，[物理池规划](vllm_ascend_glm_next_pool_planning_contract.md)负责分组/页/容量，[KPool接入](vllm_ascend_glm_next_kpool_cache_contract.md)负责cache/query/state推进，分别验收。

## 根据实际配置确定混合层

_validate_supported_config在index_topk非None时要求index_kpool_always_select_tail=True，否则NotImplementedError。_is_kda_layer按layer_types[layer_idx]=="linear_attention"选择KDA，MTP层强制走MLA。MLA所需v_head_dim/kv_lora_rank显式assert，mla_use_nope传给主attention的skip_rope。

MLP类型独立由mlp_layer_types决定：即使n_routed_experts存在，也只在当前MLP type为sparse时构造MoE；其他层用dense MLP。MTP层超出base列表时取最后一个MLP type，列表为空才用sparse默认。不能把整个模型归为“每层都是KDA”或“每层都是MoE”。

模型is_v32用index_topk是否非None判断；utils.enable_sfa则检查属性存在且无compress_ratios，model_uses_kpool_indexer检查index_kpool属性存在，model_uses_sfa_sparse再排除KPool。属性存在与值非None是不同条件，实际Transformers配置、selector输入和backend必须一起核对。UT里的SimpleNamespace缺属性例不证明所有optional字段配置都正确选路。

Glm5NextForCausalLM声明HasInnerState、SupportsPP、MixtureOfExperts、IsHybrid和supports_replayssm；条件生成包装也声明hybrid/inner-state。这些接口让框架选择集成路径，不能代替每种配置、硬件和功能组合的运行证据。

## MLP/MoE与SP的执行归属

dense MLP支持silu，可选SiluAndMulWithClamp，使用gate/up融合与down projection。SP设置使这些权重复制并关闭普通TP切分；非SP按TP结果归并。激活类型不符直接拒绝。

MoE持有EP group/rank、逻辑与冗余expert数、本地physical expert区间、GateLinear和noaux_tc的FP32 correction bias，并交给FusedMoEFactory；底层dispatch/quant/kernel没有在本卡读取。internal router模式把hidden同时放入router_logits槽，由fused路径计算gate一次；外部router模式先显式算gate。

MoE只有在自己负责SP chunk时才切分输入、执行后all_gather并裁回原num_tokens。mHC decoder已持有SP shard时传already_sequence_parallel=True，避免再次chunk。decoder对SP非MTP层关闭attention o_proj普通reduce，mHC路径在attention后显式pad/reduce_scatter；MTP保留普通reduce。不能从某一局部开关推全部SP/EP/DP/非mHC组合安全。

pad_sequence_parallel_tokens用(-tokens)%TP计算第一维padding，padding为0也调用functional.pad，以免tracing对分支特化。SP collective、MoE内部调度与性能仍需实际版本/设备验证。

## mHC状态按真实三维Tensor组织

hc_expand的源码是unsqueeze(1).expand(-1,n,-1).contiguous()，产生[T,n,D]；docstring的展平描述不能代替真实shape。hc_contract对dim=1取mean，其n参数没有参与计算。结构背景见[通用mHC](../../concepts/modules/mhc.md)，该页的DeepSeek-V4默认值和hc_head不能直接替换当前GLM执行。

| 阶段 | 当前GLM状态流 |
|---|---|
| 第一层/无待处理post | layer0先expand，再hc_pre，保留residual与post/comb |
| 后续有deferred post | hc_post_pre先完成前一层post，再执行本层pre |
| attention | SP先gather完整token序列，执行attention，再pad/reduce_scatter回shard |
| FFN | post-attention mixing与pre-FFN mixing后，执行MLP/MoE |
| 非最后base层 | 返回x、residual、post、comb，将FFN post留给下一层 |
| 最后base层 | 显式hc_post并contract回[T,D]，清除待处理状态 |

hc_pre调用npu_hc_pre_v2，取layer_input/post_mix/res_mix；若post_mult不为2再校正post系数，随后按需单独RMSNorm。hc_post为NPU入口补leading维度；hc_post_pre在Python中顺序调用post和pre，不由函数名证明它是一发融合kernel。模型设置tau字段并不在这段hc_pre调用里显式传给CANN，不能据字段名推断底层温度参数。

非mHC或MTP decoder走普通attention/norm/MLP路径；普通base层做residual加和，MTP返回未相加的(hidden,residual)供shared-head fused add/norm。最终logits与feedback仍按[MTP隐状态合同](../../runbooks/precision/vllm_ascend_mtp_hidden_state_contract.md)解释，不能在新框架多做一次最终norm。

## PP边界必须携带deferred状态

第一PP rank拥有embedding，最后rank拥有final norm/LM head，其余用PPMissingLayer。make_layers划定本地层，_active_layers缓存固定slice。first rank优先inputs_embeds，否则embed input_ids；非first rank从IntermediateTensors直接读取。

| PP payload | shape / dtype |
|---|---|
| hidden_states | [T,D]，请求dtype |
| 非mHC residual | [T,D]，请求dtype |
| mHC residual | [T,n,D]，请求dtype |
| mHC post | [T,n,1]，FP32 |
| mHC comb | [T,n,n]，FP32 |

非last rank交出这组状态；下一个rank的首层继续hc_post_pre，不能丢post/comb后重新做独立pre。make_empty_intermediate_tensors必须与真实payload key和shape一致，profiling/dummy不能只给hidden。最后rank做final norm；SP最后先all_gather并裁到positions token数。

use_sequence_parallel_moe且PP world>1显式拒绝，原因是跨PP再次sp_shard会重新切已经切分的Tensor。TP head整除也有assert。空active stage、transport序列化和其他组合未在此闭合，SupportsPP声明不覆盖这些缺口。

## 稀疏索引buffer与Mamba接口

模型topk_indices_buffer行数为max_num_batched_tokens、dtype int32，visible width为topk+(pool-1 if pool>1 else0)，physical width向上对齐128列。以topk2048/pool4计算，visible2051、physical2176只是该配置的算术；它不同于PKI输出的可见索引数。Full MLA的index_topk=None不分配buffer。

Mamba dtype/shape/copy类方法委托Native KDA calculators，shape传KDA parallel size、heads/dim、conv kernel size和num_spec；RecoverSSM条件满足时追加记录并用num_spec+1容量。这里读取的是调用与门控，未重新实现Native shape/precision或commit调度；[RecoverSSM入口](../optimization/vllm_ascend_glm_kda_recoverssm.md)的限制独立保留。

## checkpoint映射与target/draft边界

Glm5NextModel.load_weights接受(name,tensor)或(name,tensor,kwargs)。跳过rotary inv_freq/cos_cached/sin_cached；get_spec_layer_idx_from_weight_name在num_nextn_predict_layers范围识别model.layers.N或layers.N前缀，target跳过这些MTP层。相同helper名也出现在[Kimi MTP](vllm_ascend_kimi_mtp_adaptation.md)和[V4 MTP](vllm_ascend_v4_mtp_adapter.md)，须保留各自模型/前缀规则。

| checkpoint分量 | 融合目标 / shard |
|---|---|
| gate_proj / up_proj | gate_up_proj / 0、1 |
| q_a_proj / kv_a_proj_with_mqa | fused_qkv_a_proj / 0、1；该融合模块不存在时继续检查其他映射，实际checkpoint/config仍须匹配 |
| indexer.wk / weights_proj | wk_weights_proj / 0、1 |
| KDA q/k/v/b/f_a/g_a | in_proj_qkvbfg_a / 0..5 |

expert名字要在普通stacked改名前排除，再按expert mapping传name、expert_id、shard_id，避免重复gate_up改写。default路径通过maybe_remap_kv_scale_name处理kv-scale remap、PPMissing和可选kwargs；stacked、expert与FP8 WK helper在这份源码里没有转发同一组kwargs。不要只因接口接受三元组就假设所有分支都消费额外参数。

## FP8 WK按层配对，再写BF16融合分片

_try_load_fp8_indexer_wk只处理包含indexer.wk.且非wk_weights的名字：weight要求dtype精确为float8_e4m3fn，scale由weight_scale_inv名字识别。_pending_wk_fp8按layer prefix保存weight与scale，任一先到都可暂存；不能把这条guard外推到其他FP8格式。

两者齐全后，helper删除pending entry，按weight.shape[1]//scale.shape[1]推block_size，调用Native scaled_dequantize、GroupShape(block_size,block_size)、out_dtype=BF16，再把结果写入wk_weights_proj.weight的shard0，并记录fused name。head weights的shard1另由普通映射加载；Native dequant形状校验与数值实现未读取，也没有实际执行这次转换。

加载验收须覆盖三个边界：

1. 主迭代结束没有显式assert pending为空，孤立weight/scale、重复覆盖与缺项必须独立检查，不能以无异常认定完整。
2. FP8 helper早于后续PPMissing检查，且直接查fused params；实际Native AutoWeightsLoader的按rank过滤与输入顺序需要核对，不能据局部代码宣布所有PP FP8都正确或都故障。
3. loaded_params中出现fused name不能证明shard0和shard1都到齐；异常后也不能把本地pending缓存当事务恢复记录。按原checkpoint key、scale、分片和目标rank确认，失败恢复完整已验证加载状态。

这些是源码和验收缺口，不是已复现的FP8/PP问题。量化scale的TP规则另见[scale分片排查](../../runbooks/precision/vllm_ascend_quant_scale_tp_sharding.md)，不套用另一量化格式的group规则。

## 条件生成包装的映射与精度条件

Glm5NextForConditionalGeneration的hf_to_vllm_mapper将lm_head、model.language_model和model.visual前缀映射到语言模型/head与visual，展开.forget_gate.并把attn_hc/ffn_hc的fn/base/scale映射到当前直接参数。load-local mapper将顶层rot.*全部跳过；nested layer里的rot保留，不能扩大成“所有rotation权重都丢弃”。

vision构造明确用vision_config.rms_norm_eps并传quant_config=None，防止继承文本norm eps或全局FP8策略；其NaN动机来自注释，不是本次复现。language_model按注册架构Glm5NextForCausalLM初始化，PP placeholder factory转给语言模型；encoder graph config仅从parent buffer_keys移除pos_embeds。

完整VisionTransformer、processor、图像/视频placeholder与Native父类未在本卡读取，mark_tower_model包含image/video不等于部署支持已验。GLM-5.3-Flash参考脚本的video0条件继续保留，不能用包装层注册推翻它。

## 测试定义与Agent交付

| 已读测试 | 范围与证据强度 |
|---|---|
| loader UT47 | CPU假两元素参数，调用Native AutoWeightsLoader，quantized开/关，核对prefix/forget_gate/nested rot和顶层rot.*删除，class mapper未改；未运行 |
| PP UT143 | stub模型/假world2、四个测试定义，检查placeholder、payload和post/comb交接；没有真实attention/MoE/HCCL |
| mHC UT68 | NPU入口与RMSNorm被monkeypatch到Torch reference，比较post scale2/1.5及norm开关；不测试compiled NPU operator |
| SFA routing UT92 | mock Standard/FP8 family与selector，检查KPool共享SFA、310P/DCP拒绝及topk边界；不是硬件支持矩阵 |

Agent交付应包含实际config与逐层类型、模块/参数树、topk可见和物理宽度、每个PP边界状态、SP/PP有效配置、原checkpoint key→目标rank/参数/shard映射、FP8 scale配对与缺项清单。先核对这些producer-consumer，再验证逐层参考、完整加载、eager/graph、MTP与目标硬件质量/SLO。当前没有真实checkpoint、NPU数值、性能或下游Agent A/B结果。


## mHC pre/post的真实Torch与Host接口补充

补充读取两族OpDef87/54行和HcPost通用tiling231行全文；HcPre通用tiling仅取1–172/611–749，950 pre header取425–502/793–813，950 post header取14–42/61–233；共享Torch包装1477–1662及schema3347–3374、Meta1052–1133/1841–1843和本模型518–572为有界读取。这是GLM接入的Host/形状facet，不代表这些文件其他tiling候选、完整Device同步、Sinkhorn数值或所有硬件组合已闭合。原模型、PP与SP合同继续保持。

真实Torch HcPre要求x为3维`[T,4,D]`或4维`[B,S,4,D]`，各维为正，x为BF16；hc_mult属性和实际stream维都固定4，hc_fn为FP32 `[24,4D]`，hc_scale为FP32 `[3]`，hc_base为FP32 `[24]`。不能只改变配置n就得到任意mHC stream数支持。可选pre_mix仅V3接收，要求FP32且shape严格等于x去掉D，即`[T,4]`或`[B,S,4]`。

底层Torch V2返回`(y,post,comb_frag)`：y去掉hc轴且为BF16，post为前导维加`[4]`/FP32，comb_frag为前导维加`[4,4]`/FP32。V3再返回FP32 pre，shape同post。GLM wrapper随后返回的是`(post.unsqueeze(-1),comb,layer_input)`，与底层顺序不同；适配时不能直接以模型返回变量顺序解释Torch tuple。

V2和V3共用run_hc_pre_fusion，真实调用会构造第四个pre输出；V2仅在返回给Python时丢弃它。因此V2返回三项不等于底层只分配三份输出，也不能把Meta分配模型当作真实峰值。包装将norm_eps/hc_eps按ACLNN属性次序传入，Agent应以真实schema和最终调用核对，避免交换两个同为浮点的参数。所读shape checker和Host属性读取没有穷尽Sinkhorn迭代数及epsilon数学域校验，缺少拒绝不能替代数值验证。

HcPost Torch入口比Host更窄：x必须`[B,S,D]`且各维为正，residual必须`[B,S,hc,D]`，post为`[B,S,hc]`，comb为`[B,S,hc,hc]`；x与residual同dtype，post与comb同dtype，两组可分别选择FP16/BF16/FP32。GLM用unsqueeze/squeeze把本地`[T,D]`与三维mHC状态适配到这个入口，不能省略包装直接传2维x。Host虽接受x为2维或3维，也不扩大已注册Torch包装的合法域。

HcPre和HcPost Meta主要按输入符号shape构造结果，没有调用真实Torch的完整shape/dtype检查；HcPost Meta甚至直接沿用residual形状构造输出。Meta能推形不证明空batch、hc数、系数和dtype能走真实入口，profiling/dummy输入也必须满足实际合同。

两族OpDef注册ascend910b/ascend910_93/ascend950，Host按实际SoC选择950独立路径；这不是本次NPU支持证明。非950 HcPre同时检查shape中的hc与属性一致且等于4；可选pre_mix用GetOptionalInputTensor判断，第四输出用有效shape判断，避免把placeholder的非空指针当成真实值。950已读片段则分别使用GetInputShape/GetOutputShape非空判断，可选值在真实编译占位路径的行为尚需独立核验，不能跨实现搬用判空结论。

非950 HcPre的workspace至少208MiB，或按Cast/分K中间结果与square-sum求和后加16MiB取更大值。950已读K拆分分支按其kBlockFactor、bs和hcMix另算workspace再加16MiB；不能把非950的208MiB保底套给全部路径，也不从这些字段推导模型总显存。HcPost两条Host路径使用16MiB workspace，通用路径按2048元素处理D段，950按4096并依据x是否FP32选择key0/1；这些是源码分派，不是性能测试结果。

新框架应先核上述输入与tuple ABI，再对照原PP payload和延迟post状态；分别验证GLM post倍数校正、额外RMSNorm、V2/V3、3/4维、可选pre_mix与实际硬件。没有本次编译、HCCL、Sinkhorn数值、模型输出或性能结果，不因Host字段齐全宣称完整mHC Operator或任意新模型已适配。


## HcPre/HcPost Device：分派、pre_mix与CV存储寿命

补充同一Main两族剩余21路径（20种字节），直接读取CMake、HcPost proto与两份Device入口，较大tiling/header按完整结构投影检查定义/分支/常量/调用，并展开下列数学、拷贝与交接选段。来源表区分raw_full，不将结构投影当完整算子Device语义穷尽。本节服务GLM接入和排障，原框架/Host合同、PP deferred post与状态Scope保持；外部Matmul/primitive、全模板可达性、编译、NPU数值与性能仍未验证。

### 根据实际编译guard与key选实现

HcPre入口声明MIX_AIC_1_2，workspace为空或GetUserWorkspace为空直接返回；文件存在不保证输出已写。`__DAV_C310__`选择arch35头，不能把这个编译macro按数字猜成310P产品。所读Host已有950分支，仍需实际构建产物匹配。

| HcPre key | 入口实际实例化 | 调度合同 |
| --- | --- | --- |
| 非arch35 0/1 | 同一Membase KSplit Part1，分别配Part2的两种模板参数 | stage1产分K matmul/square-sum暂存，stage2规约并生成pre/post/comb与y |
| 非arch35 2 | KSplit Part1 + 独立PremixPart2 | 外部pre_mix参与y的合并；不是把属性改名即可复用普通pre权重 |
| arch35 1000/1002 | MKSplit普通/带premix的两阶段实例 | 分M/K并行与stage2再规约；两个TPipe分阶段管理 |
| arch35 1001/1003 | MSplit普通/带premix的单实例 | 按M切分，各实例中推进Cube/Vector与后半输出；不能沿用MK的workspace/事件推算 |

这些分支没有为未知key提供另一条计算fallback。HcPost的arch35入口按key0实例化FP32路线、key1实例化B16路线；非arch35使用DSplit模板。不能由HcPost Host接受的一般shape或dtype组合推导每个已编译特化都具备同样能力。

### 实现职责矩阵

| 文件子族 | 已提炼facet |
| --- | --- |
| 两族CMake与HcPost proto | recursive收集、BUILD_OPEN_PROJECT/BUILD_OPS_RTY_KERNEL分支、auto-sync关闭与relocatable选项；Post推形取residual shape、输出dtype取x，而不是穷尽四输入一致性 |
| `hc_pre_tiling.h`、`hc_post_tiling.h` | Host与Device间bs/D/hc、core、row/tail、M/K tile和workspace字段协议；不得跨旧/arch35结构猜同布局 |
| `hc_pre_base.h` | sigmoid、pre/post、4×4 reduce、row softmax/归一化、广播/尾部和y加权转换；hcMult4有专门实现，不等于任意stream数 |
| `hc_pre_base_arch35.h` | 寄存器cast/ND2NZ、分段平方和/逆RMS、packed/element-major Sinkhorn、premix及y；mask、row-gap和LocalMemBar属于真实数据布局合同 |
| `hc_pre_cube_compute.h`、`*_arch35.h` | L1/L0 ping-pong、ND/NZ搬运、Mmad/Fixpipe、预取和事件；HF32设置独立于Tensor标称FP32 |
| `hc_pre_m_k_split_core.h` | 非arch35 K/M块分工、两阶段工作区规约，普通/compact/premix后半路径；不能用一个prefill/decode标签代替实际key和tiling |
| `hc_pre_m_k_split_core_arch35.h`、`*_premix_arch35.h` | arch35 MK stage1的cast/平方和与matmul并行，stage2的分组规约、可选pre输出及Sinkhorn；premix有独立stage1/2实现 |
| `hc_pre_m_split_core_arch35.h`、`*_premix_arch35.h` | arch35 M-only CV流水和UB pool重用；premix把四段cast保留后链式累加y，不能当普通MSplit只多一个参数 |
| `hc_post_d_split.h` | 沿D分块读取x/residual与post/comb广播，FP32累积后按目标dtype输出；真D尾段与对齐stride分别处理 |
| `hc_post_float32.h`、`hc_post_bfloat16.h` | arch35寄存器四路残差乘加与post*x，分别处理FP32/B16输入及系数转换；B16结果最后RINT写回 |

### 数学顺序和premix不可混用

stage1同时准备展平hc×D输入的matmul与平方和；stage2将分K的结果合并，按`1/sqrt(square_sum/K+normEps)`归一mixes。三组hc_scale与hc_base分别作用于pre、post与comb。pre为sigmoid后加hcEps，post为sigmoid后乘2；GLM层中post_mult的再校正仍以上文模型wrapper为准，不能在Device或新wrapper又重复乘一次。

comb先按行减max、exp和归一，再加hcEps、列归一，后续执行行/列交替迭代。compact与arch35 packed/element-major路线有不同布局/归约实现；epsilon加到元素还是分母必须按具体函数核对。有限迭代和epsilon不意味着数值上每行/列严格等于1，不能以理想双随机矩阵替代当前离散实现。iterTimes参与`iterTimes-1`调用，不把未知0/负值或超大值视作已有统一Host拒绝/安全上限。

普通y按预测pre系数对原hc流加权相加；premix路线的y则使用调用方pre_mix。即使hasPreOut时仍输出根据当前mixes预测的pre，也不说明该pre就是本次生成y使用的外部pre_mix。A3 PremixPart2明确在ProcessY处选择外部系数；arch35 premix把加权y更早融合到cast阶段，stage2仍可独立生成pre/post/comb。这两份pre的来源应在Agent记录中分开。

HcPost按`y[h,d]=x[d]*post[h]+sum_j(residual[j,d]*comb[j,h])`合并，不能把comb的两个hc轴交换。arch35寄存器实现显式读四路residual及comb同一目标列，用0/3/1/2顺序乘加后加post*x；DSplit为逐残差路累加。乘加顺序、FMA、B16转换与最终RINT可能影响离散值，不从同一实数公式推导不同template bitwise等价。

arch35 Post代码中的四个明确lane不能由参数名hcParam推成任意hc数支持；GLM Pre当前hc=4保持。本节不据这项局部静态证据宣称实际Host已经放行/拒绝了每种非4情况，独立调用HcPost时仍需核真实Host与特化交集。

### 资源、事件与图重放

普通KSplit stage1由AIV cast/平方和与AIC matmul交接，CrossCore flags在本地MTE/FIX事件间配对，stage末显式SyncAll<false>后销毁第一TPipe，再进入第二TPipe规约。不能把Destroy当作外部stream同步，也不能删掉stage末同步而假定新pipe自动等数据。arch35也有独立flags、MTE3/Vector事件和多级buffer轮换，具体key不可直接互换事件表。

源码确实把cast、matmul部分和及square-sum写入GM/workspace，部分MSplit又从共享L1与UB池推进；不能把另一仓mHC概念的“中间数据留UB”概述搬成本Main所有分支零HBM暂存。workspace分配、峰值、全局/局部同步和图捕获地址均需按所选template和实际core数跟踪。

两份Cube helper使用不同L1/L0资源与预取组织；arch35明确SetHF32Mode(1)/SetHF32TransMode(1)，旧helper也设置HF32转换模式。FP32输入/输出类型不等于全程IEEE matmul或任意后端相同精度。新硬件、D、M和权重尺寸必须重新确认合法tiling与资源，不能把编译macro、固定L1/L0常量或历史性能转授新平台。

同一UB pool、Tensor queue与L1 ping-pong会在后续tile重用；可选pre输出、post/comb与y有独立store顺序，Python返回不证明跨stream读者已经完成。适配先固定key、bs/D/hc、pre_mix/hasPreOut、normal/compact布局与完整workspace区间，检查D尾块、M余数、K块规约、四流索引、post校正和PP deferred状态，再做eager/graph与逐层数值基线，最后分解Cube/Vector/搬运和端到端收益。本次未执行这些运行验收。
