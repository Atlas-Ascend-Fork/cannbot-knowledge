---
type: Guide
title: vLLM Ascend MiniMax-M3 语言模型：MiniMaxM3SparseForCausalLM 的 SP、MoE 与加载
description: 适配 MiniMax-M3 语言模型时核对文本配置、稀疏层选择、显式 SP 状态与 PP 边界、辅助隐状态、SwiGLU OAI 和专家更新，以及融合投影权重加载；区分源码分支、CPU 模拟测试与真实硬件验收。
aliases:
- MiniMaxM3SparseForCausalLM
- MiniMaxM3Model
- MiniMaxM3DecoderLayer
- MiniMaxM3MoE
- MiniMaxM3SwiGLUOAI
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.parallelism
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/minimax_m3/minimax_m3.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/minimax_m3/test_minimax_m3.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/minimax_m3/test_minimax_m3_eplb.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/minimax_m3/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/common/ops/sequence_parallel.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
created_at: '2026-10-31T22:53:45Z'
updated_at: '2026-10-31T22:53:45Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend MiniMax-M3 语言模型：MiniMaxM3SparseForCausalLM 的 SP、MoE 与加载

## 适配任务与证据范围

MiniMaxM3SparseForCausalLM 把文本配置、MiniMaxM3Model、输出头、专家元信息和权重加载接口接到 vLLM。新模型适配 Agent 应先证明每层布局和 checkpoint 映射，再讨论融合或吞吐收益。模型支持表、启动配置和量化发布包见[MiniMax-M3 部署指南](../models/vllm_ascend_minimax_m3_runtime_variants.md)；图像和视频交给[视觉桥接指南](vllm_ascend_minimax_m3_vision_bridge_contract.md)，稀疏缓存及 attention 调用交给[稀疏后端指南](vllm_ascend_minimax_m3_sparse_backend_contract.md)。

本卡固定 Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，完整阅读语言实现 1609 行、模型 UT 436 行、EPLB UT 258 行、导出文件 21 行及 SP 原语 152 行。Main 配对 Native pin 是 544f182d9f0c9bfe8bd7645525951d5e3692a542，独立 Native 来源树 5df63a7203cdb9328d824a27b682e77c7b9928be 不能替代配对环境。所有来源仅按数据阅读，未导入上游模块或执行测试、模型、集合通信及 NPU。局部 A5 分支不能证明整项适配的硬件范围，故保持 draft、空平台。

## 文本配置与每层类型

包装器读取 hf_text_config；配置对象具备相应属性时，把服务 ModelConfig.max_model_len 写回文本配置。位置上限 helper 取现有 max_position_embeddings（缺省 8192）与 max_model_len 的较大值。RoPE 参数复制配置字典或使用默认 theta/partial 参数；实际 RoPE 实现和 checkpoint 位置编码约定仍须对照。

MLP 与 attention 的稀疏性独立：moe_layer_freq 缺失时默认使用 MoE，存在时按该层元素是否非零选择；sparse_attention_config 中的 sparse_attention_freq 单独决定稀疏 attention，缺失时集合为空。非零值 2 也选中该层。不能用“模型是 MoE”推导所有 attention 层都稀疏，或把频率表解释成只接受 1 的布尔列表。

MiniMaxM3DecoderLayer 在构造时选择稀疏/常规 attention 和 MoE/dense MLP。dense attention 仍使用 Native Attention 对象，替换后端声明的条件由稀疏后端 helper 控制；保留的 impl、Native API 和设备实现需要另行闭环。

## 显式 SP 状态、残差与 PP 传输

MiniMaxM3DecoderLayer 通过 input_is_sequence_parallel 判断输入布局。TP 大于 1 时，单 token 与一个分片可能出现同样 shape，不能以 hidden.shape 与 positions.shape 相等代替布局标记。use_sequence_parallel_moe 在本实现还影响 dense MLP，实际 MoE factory 的 SP 行为必须匹配。

进入 SP 前先断言 hidden 行数不少于 positions 的实际 token 数，对 hidden 和已有 residual 裁剪。attention 前恢复完整序列；attention 输出按需要 reduce scatter。residual 只在进入 SP 时分片，连续 dense/MoE 层之间保持分片布局。离开 SP 则分别 gather hidden、residual，并裁回 positions 行数。[SP 原语指南](vllm_ascend_sp_primitive_contract.md)维护补齐、分片和 gather 的通用合同，模型调用方仍须传递正确状态。

dense MLP 的 TP 权重要求完整序列，先 gather，down projection 关闭自身结果归约，再由模型路径 reduce scatter 回分片。核对这一点可避免新增 MLP 直接消费 token 分片后重复归约或丢失 token。残差加法发生在哪个布局应逐层记录，不能只验证 attention 输出 shape。

MiniMaxM3Model 的首 PP 阶段拥有 embedding，末阶段拥有 final norm，其他阶段使用 PPMissingLayer。每个阶段从非 SP 布局开始；非首阶段从 intermediate_tensors 读取 hidden、residual 和辅助隐状态。非末阶段在传输前分别 gather hidden/residual 并裁掉补齐行，通过 pp_transport_aux_hidden_states_ 前缀携带辅助数据。空 intermediate 工厂也经相应传输 helper 包装。PP helper 的私有 API、真实通信与多阶段 Runner 消费还需配对 Native 验证。

VLLM_MOE_SKIP_PADDING 且存在 forward_context 时，模型保存原 is_padding，进入 SP 后计算 SP padding mask，离开 SP 和正常结束时恢复原值。本方法没有异常 finally；不能把正常路径恢复扩大成所有异常下都不会泄漏上下文。

## 辅助隐状态与输出消费

Eagle3、DSpark 才启用配置中的辅助层选择，其他方法清空选择。只在请求的层抓取快照：SP 路径先 hidden+residual，再 gather 并裁回实际 token；非 SP helper 同时接收 hidden 和 residual。缺少 residual 会产生 shape 正确但语义不一致的 draft 输入。

末阶段先执行 norm，必要时再 gather/crop；存在辅助输出时实际返回可为 `(hidden_states, aux_hidden_states)`。语言包装器直接转交模型结果，不能仅依据其 forward 返回注解断定始终为单一 Tensor。默认 Eagle 辅助层为 `(2, num_layers//2, num_layers-3)`，极小层数或自定义结构仍需核对索引。

输出 head 和 logits processor 只在末 PP 阶段构造。compute_logits_local 使用 skip_gather=True；调用方需要明确本地词表分片和后续归约责任，并避免把非末阶段对象当成可直接计算 logits 的完整模型。

## MiniMaxM3SwiGLUOAI 与量化分支

MiniMaxM3SwiGLUOAI 将 gate 只按上界 limit 钳位，将 up 按正负 limit 钳位，再计算 `gate * sigmoid(alpha * gate) * (up + beta)`。把 gate 也做双向截断会改变负区间数值。MLP 只接受 swigluoai 激活配置，其他值报错。

A5 或 MX 路径使用 Torch 小算子组合；MX 路径继续调用 DeviceOperator.npu_dynamic_quant，传入 E4 dtype 和 use_mxfp_quant=True，返回数值与 scale 的二元组。其他路径使用 interleaved=False 的 clipped_swiglu。开启 use_mx_quant 还要求 A5，且 gate_up/down 两个 quant method 的类名都精确等于 AscendW8A8MXFP8DynamicLinearMethod；不能仅由 weight dtype 或相似子类名推断启用。

down projection 直接接收激活 Tensor 或量化元组，因此适配时需核对 Linear 的输入协议和 scale 布局。这里没有证明所有量化格式、A5 profile 或融合 kernel 的误差与性能。

## MiniMaxM3MoE、路由和物理专家更新

MiniMaxM3MoE 根据 EP group/rank 计算逻辑专家、冗余专家、物理专家和本地物理区间；本地数量使用 physical/EP 的整数商。TP 大于逻辑专家数会报错，但该检查不能替代所有全局专家整除条件。共享专家中间宽度为 intermediate_size 乘共享专家数，其 MLP 关闭自身结果归约。

gate 的参数及输出保持 FP32，correction bias 也是 FP32，专用 loader 检查 shape 并转换 dtype。FusedMoEFactory 接收 swigluoai_uninterleave、alpha/beta/limit、renormalize=True、路由缩放及 EPLB/冗余专家配置。初始化同时设置 experts.global_redundant_expert_num 和 experts.moe_config 中对应字段。

internal router 路径把 hidden 放进 router_logits 参数槽，由内部处理；external router 则先计算 gate，再传结果。只按参数名判断“已有 logits”会导致重复 gate。专家 kernel、真实 EP 通信和 router 实现仍是外部依赖。

包装器只聚合当前 PP 阶段非 Missing 的 MoE 层；没有 MoE 时专家统计为零。update_physical_experts_metadata 要求本地物理数量不变，更新包装器与各 MoE 的物理/冗余数，调用 update_expert_map，并同步两个冗余字段。视觉语言包装器还要刷新自身持有的专家元信息，不能只改内层语言对象。expert_weights 接口的空列表也不能解释成一套独立加载的专家副本。

## 权重名字、融合分片与可观察加载结果

顶层 mapper 将 language_model.model、language_model.lm_head 映射到模型和输出头，排除 vision_tower、projector、patch_merge；实际遍历仍委托 AutoWeightsLoader。MiniMaxM3Model 的 loader 去掉一个前导 model.，跳过 mtp. 和 rotary inv_freq，把 weight_scale_inv 规范化为 weight_scale，其他 scale_inv 转为 scale。

普通 Q/K/V 映射到 qkv_proj 的 q/k/v 分片；index Q/K 先尝试 split indexer，再尝试融合 QKV；dense gate/up 分别映射 0/1。路由专家名先排除普通 stacked mapping，再按专家 w1/gate、w2/down、w3/up 映射。缺失 bias、非本 PP 参数、部分 index 参数及 KV scale remap 都有独立跳过路径。支持 MoE loading 的 fallback 只在 shape 完全一致时走 default loader，否则要求显式 mapping。

spec helper get_spec_layer_idx_from_weight_name 期待 model.layers.N 前缀，而本循环较早剥离 model.。这是静态输入名字边界：应核对 AutoWeightsLoader 实际传入的名称及 helper 调用顺序，再判断是否命中；本卡没有复现“所有 spec 权重都失败”的结论。

已处理 tensor 数、唯一 loaded 参数集合和带原因的 skip 计数是不同观测。它们均不能单独证明完整 checkpoint 已加载；还要逐参数检查 PP 归属、预期专家分片、重复目标、量化 scale 和未消费键。

## 验证顺序与未闭环边界

先用真实配置生成每层 attention/MLP 类型表和 PP 归属表，再记录每个 SP 转换的实际行数、补齐行数、residual 布局及辅助输出层。权重验收输出源键到目标参数/分片的映射与 skip 理由。随后才在指定硬件、软件与 checkpoint 上比较 TP/EP/PP、padding、spec 方法及量化组合的数值和性能。

来源 UT 用 CPU dummy、mock collective、简化 norm/attention 和量化 stub 检查 residual-added aux、SP 连续层、PP 边界、router 输入及专家元信息更新。测试文件仅阅读，未在本次执行；这些设计不构成真实 NPU、分布式集合通信、量化精度或性能证据。

本卡闭环的是固定版本语言适配框架合同。Native AutoWeightsLoader、Linear、MoE、RoPE、PP transport 的全部实现，稀疏 Device kernel、真实模型加载、图重放与 Agent 任务效果仍须独立验证。来源固定和知识检索通过均不生成 verified 事件。
