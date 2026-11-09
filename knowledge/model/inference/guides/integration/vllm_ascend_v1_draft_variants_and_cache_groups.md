---
type: Guide
title: vLLM Ascend MRv1 草稿变体：多缓存组、窗口推进与隐藏状态提取
description: 核对 DFlash/DFlash2、Gemma4、GLM5-Next、Step3.5 和 ExtractHiddenStates 在 MRv1 的独立输入/采样/图元数据合同，以及异步拒绝后的 CPU/GPU 计数修正。
aliases:
- AscendDflashProposer
- AscendDflash2Proposer
- AscendGemma4Proposer
- AscendMultiKVCacheGroupMTPProposer
- AscendStep3p5MTPProposer
- AscendExtractHiddenStatesProposer
tags:
- task.implementation
- task.debugging
- topic.speculative_decoding
- topic.kv_cache
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/dflash_proposer.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/dflash2_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/gemma4_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/multi_kv_cache_group_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/step3p5.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/extract_hidden_states_proposer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/spec_decode_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/qwen3_dflash2.py
  role: primary
created_at: '2026-11-03T05:02:49Z'
updated_at: '2026-11-03T06:39:58Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend MRv1 草稿变体：多缓存组、窗口推进与隐藏状态提取

## 版本与方法边界

本卡固定 Main ceac1a2，完整读取六个 MRv1 proposer 和共用 spec_decode_utils.py；与[MRv2 DFlash合同](vllm_ascend_dflash_runner_graph_contract.md)、[MRv2 310P MTP](vllm_ascend_310p_mtp_proposer_contract.md)分版本/runner使用。未执行上游、Triton、图、模型或分布式测试。新增模型应先核真实工厂选中类、父类MRO、target/draft配置和每个物理 KV group，不能因方法名相同直接复用所有元数据。

## DFlash 与 DFlash2 的 query、context 和 selector

DFlash 为每请求构造 K+1 个 query（bonus+mask），另把 target hidden states 保存为 context。输入复制 grid 按 max(context总数,query总数)/256 向上取整并受 vectorcore 数限制，两个范围是独立 grid-stride 循环，不用二者之和。buffer 容量还需覆盖超过逻辑 query 上限的 graph padding。

first pass 由 kernel 生成 query/context positions 与两类 slot mapping，拒绝 token 数只在有效 device seq_lens 上扣除一次，再加 K+1；query_start_loc 改为固定跨度，causal=False、mask=None、状态设 ChunkedPrefill。该局部 actual_seq_lengths_q 赋的是每请求 K+1；后续 backend 若要求累计端点必须按真实 builder 转换，不混用[MRv2合同](vllm_ascend_dflash_runner_graph_contract.md)中的 padded 累计 query 约定。dummy slot mapping 全填 -1，profile 预计算 context KV；普通执行经 runnable 后刷新 FULL 参数。_raise_if_multimodal 为空只撤掉该处拒绝，不证明所有多模态链路已支持。

DFlash2 要 method=dflash 且 draft architectures 含 DFlash2DraftModel；MRv1 构造明确拒绝 probabilistic draft，返回 draft_probs=None。它要求完整 target LM head，draft_id_to_target_id 非空拒绝 reduced vocabulary。hidden 总行必须能被 K 整除，重排为 [requests,K,hidden]，每步 top-k candidates 和 unary logits 交 selector 得 [requests,K,topk,topk] 转移分数；从 input_ids 的每请求 anchor 出发 greedy walk，输出 [requests,K]。不能把路径 walk 改成每步独立 argmax，也不能由 MRv2 的概率接口推本实现支持随机 draft。

## 三种多组模型不能共享一张无条件块表

| 变体 | 每组数据与图准备 | 新模型适配中的检查点 |
| --- | --- | --- |
| Gemma4 | Native Gemma4Proposer 优先继承，Ascend 保留 ACL wrapper；centroid 不单独捕 CUDA 图。load 后把 wrapper 的 late-bound KV-sharing target 同步到 impl。 | draft 只用 backbone hidden，supports_mm_inputs=False；没有同步 target 时可能读自己cache，不能用同名 layer 推共享已完成。 |
| GLM5-Next multi-group MTP | 仅 model_type=glm5_next_mtp 或 Glm5NextMTPModel allowlist；每层必须找到物理 group，按 backend full name+gid 聚合，优先可执行组，cache-only组保留逻辑块。 | 单组委托父类；不因新增模型也有多组就自动选择该类。 |
| Step3.5 MTP | 每个 MTP 层/组独立缓存；按 speculative step 返回 metadata 字典列表，FULL/replay 更新按步骤索引。 | 不能把所有层塞到一个字典反复传；group 顺序、step数和真实层调用必须对齐，后续 step 越界会断言。 |

Gemma4 为每组浅复制 common metadata，换该组 block table；实际 build 强制 SpecDecoding，避免继承 target 的 ChunkedPrefill 导致 FIA 选错路径。非 causal 时清 mask。共享 target 名称存在只说明静态接线，真实跨模型缓存寿命与数值仍需测试。

GLM multi-group 在初始化即预分配所有 group/step 的 slot buffers 和 graph 表，宽度按 logical block×kernel subdivisions 或 spec 上限计算，避免运行时首次分配破坏捕获地址。secondary 非 circular group 按 device positions/query boundaries 重算 slots，pad 区填 PADDING_SLOT_ID；每个 gid 每次刷新一次表，缺行清零。graph capture 的后续 draft 用每 padded row 一个 query，长度尾部清零并废弃 CPU mirror；compressed capture 明确 assert 拒绝。eager cache-only dataclass 会 clone Tensor 字段防覆盖，但 IndexerKPool metadata 特别保持原对象，不可自行“统一深拷贝”。第二步按 used positions+1 修正 seq_lens，并清 CPU computed/length缓存，防旧镜像再次覆盖真值。

Step3.5 的 secondary slot buffer 缓存在实例上，复制 group slots 并把尾部填哨兵；FULL 捕获前从 runner 播种各组元数据。propose 先更新本批 K，K=0 返回 [batch,0] 并清旧概率；图 dispatch 经 DP 同步后重做，LoRA/uniform与 padded请求共同决定 descriptor。ENPU 与传统模式刷新 full graph 参数的前后顺序不同，不可随意互换。

Step3.5 后续每层重跑完整 draft window：左移旧 token window、在 sample index 写新 token、更新 hidden states，position/逻辑 attention window 继续复用，切换 forward_context.attn_metadata 为对应 step。调用 model 与 compute_logits 均传 spec_step_idx，probability cache按step堆叠。它不是普通每次仅喂一个新 token 的缩窗循环。draft layer_types 不足会补 sliding_attention，hf_overrides 归一为 dict 后通过 get_draft_quant_config 取得方案；不能只从 config.json 无 quantization_config 推断没有 ModelSlim 元数据。

## 隐藏状态缓存并非生成草稿

AscendExtractHiddenStatesProposer 复用 Native 提取/缓存行为，没有实际 speculation。SP padding 必须在 graph dispatch 和 DP sync 之前；runner 缺 _pad_for_sequence_parallelism 或多DP时缺 _sync_metadata_across_dp 明确拒绝。它复用 runner 的 draft DP 同步，dummy/idle rank 也发相同调用，避免向同一 CPU group 混入不同形状/次序。DP同步后按本rank padded tokens重dispatch，不能单看target token数。

prepare_next_token_ids_padded 使用 discard indices+count 构 mask，从 request 最后已确认 token 取 backup。sampled token 落 [0,vocab) 即计入 valid_count；只有有效且未discard才选 sampled。被discard但数值有效的token仍可返回 valid_count=1，这是计数和选token的不同语义，消费者不能把两者混为 accepted。

## 异步计数修正与验证

共用 helper 的 PREPARE_INPUTS_BLOCK_SIZE=4，要与预热和实际 launcher 一致。有前批位置且 prev_draft>0 的请求，用 prev_gpu_computed+valid_count 修正设备 computed/accepted；新请求或非draft直接用 CPU值。prev_positions=-1 仅为安全 gather先clamp0，再由 participating mask屏蔽，调用方仍须保证正索引与buffer长度合法。

CPU optimistic length 则减去 rejected=prev_drafts+1-valid_count，按 num_reqs 前缀原地修正；对新请求/prefill不减。它不读设备真值、不自动校验 valid_count 范围；不能二次扣拒绝数或将 padded查询长度当真实已写长度。回归应覆盖批次重排、新/旧请求、K变0/变长、全拒绝/全接受、padding与cache-only组、KV-sharing、TP head以及eager/FULL。源码流程和未执行测试不能证明接受率、精度或加速。


## 3164 DFlash2 模型卷积补充

固定增量 `ceac1a2→3164adc8fe75892fbf7f99f524bb72fddf1e6efd`；完整变化与必要上下文静态读取，不标目标全文FULL，未执行upstream/JIT/NPU/图/通信/性能测试。

Qwen3 DFlash2 grouped conv只遍历tap<min(taps,block_size)，块外tap不贡献，避免短draft用padding扩到输入之外；kernel_projection不再硬设quant_config=None，而按实际模型quant config构造。checkpoint形状、两side delta与block边界仍按原合同，支持某量化描述不等于真实kernel/精度已验证。
