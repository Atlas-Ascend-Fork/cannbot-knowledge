---
type: Guide
title: SGLang Ascend MLA DCP：局部attention与自然对数LSE合并
description: 区分dense MLA和DSA的DCP局部计算入口、head交换与LSE归一化，保留dense MLA decode的FIA与head比限制及无法返回LSE的拒绝边界。
tags:
- task.implementation
- topic.attention
- topic.parallelism
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/dcp.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/dcp/comm.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/dsa_dcp.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_backend.py
  role: implementation
created_at: '2026-11-08T12:07:54Z'
updated_at: '2026-11-09T04:31:35Z'
platforms: []
aliases:
- forward_mla_attention_npu
- cp_lse_ag_out_rs_mla_npu
---

# SGLang Ascend MLA DCP：局部attention与自然对数LSE合并

## 场景与约束

Decode Context Parallel将历史KV分布到多个rank，每个rank须产生局部输出和归一化信息，再合并成全局attention。`get_mla_dcp_backend`会解开hybrid包装的full_attn_backend，判断由实际dense后端完成，不能只检查外层类名。

helper读取 `uses_dcp_partial_attention`：不需局部DCP时调用普通attn_mqa；需DCP时直接调用module.attn_mqa_for_dcp_decode，接入模块必须提供该专用入口（无属性检测或普通入口回退），并显式请求return_softmax_lse=True。输出暂时按本地head数×DCP size展开，合并后恢复本地head与kv_lora_rank。草稿worker可使用复制的完整KV，不能强制走target的分片规则。

## 合并机制

DSA采用 `cp_lse_ag_out_rs_mla_npu`：把局部attention与LSE转FP32，按head打包all_to_all_single，收集每个sender对本head的片段，再用npu_attention_update合并，最后还原输出dtype。dense MLA采用 `dcp_a2a_lse_reduce`，明确is_lse_base_on_e=True和a2a通信后端。两者要求输入是自然对数LSE，不能误传log2值或原始softmax_sum。

DSA专用算子先从softmax_max与softmax_sum生成 `max + log(sum)`；dense FIA直接返回LSE。dense MLA decode只有self.use_fia且layer.tp_q_head_num // layer.tp_k_head_num >= 8时进入可返回LSE的FIA分支；未启用FIA或head比不足8时，内部paged MLA只返回output，请求LSE会抛NotImplementedError。这是decode分支条件，不能直接套到target verify的独立路线；也不能通过忽略LSE获得正确全局归一化。

## 接入与代价

先保证page交错、本地KV长度和query head交换一致，再验证局部O/LSE形状，最后核对all-to-all前后的head布局。空DP参与者也须提供与通信一致的零输出及负无穷LSE，不能提前跳过必要collective。相较单rank增加FP32打包和通信成本，是否改善长上下文decode需结合带宽测量；本次没有测量。

建议用DCP=1作为基线，对跨页、每rank长度不等、verify每步因果长度和空rank进行数值对照。本文是模型通信与调用reference，不展开完整底层Device实现，平台兼容范围未确认。
