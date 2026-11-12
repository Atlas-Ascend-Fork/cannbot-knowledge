---
type: Guide
title: SGLang 昇腾 Gemma4 多模态 PLE 的静态 shape 适配
description: 说明 graph 兼容 token 替换、PP 首末 stage 分工、positions 修改与 multimodal mask 的模型约束。
tags:
- task.implementation
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/gemma4_mm.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/managers/mm_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/gemma4_causal.py
  role: constraint
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-09T04:35:29Z'
platforms: []
---

# SGLang 昇腾 Gemma4 多模态 PLE 的静态 shape 适配

## PLE 与图 shape

Gemma4 多模态 forward 在首 PP rank 的入口校验要求 input_ids/input_embeds 恰有一个；但该快照调用 general_mm_embed_routine 时没有转发 input_embeds，后者重新生成 embedding，纯文本路径直接调用 embed_tokens(input_ids)。因此这项互斥校验不证明仅提供 input_embeds 的路径已接通，当前应使用 input_ids 入口。生成 PLE IDs 时使用 torch.where 逐类把 image/video/audio token 替换为 text pad_id，保持原 shape，避免 boolean indexing 在 NPU graph 中产生动态输出大小；不能直接把多模态占位 token 交给 PLE 表。

位置按模型约定加1。SGLANG_GEMMA_OUT_OF_PLACE_POSITION_MUTATION 决定用 positions+1 还是原地 positions+=1；共享 positions 的调用方必须识别这一副作用，不能重复偏移。

## PP 与多模态边界

PLE 表和 projection 只在首 rank，后续 stage 通过 PP proxy 接收 per_layer_inputs；各 rank 会准备 prefill 的 image attention，但仅 use_bidirectional_attention="vision" 时继续，且当前只为 FA4（含FA3升级FA4）、特定XPU或Triton backend安装相应双向元数据；其他backend（包括未命中这些路线的Ascend）告警后回退causal。图像跨度还须完整落在当前chunk，FA4/Triton跨chunk图像保留causal，不能把函数调用等同于mask已生效。通用 multimodal embed routine 按 stage 跳过不拥有的 embedding，末 PP rank 才进行 logits，并按是否 tied 选择 head。

创建的 Gemma4TextModel 还会拒绝 PP world_size>1、hidden_size_per_layer_input>0 且 graph 未禁用的组合：PLE 多stage应传 --disable-cuda-graph 或改用TP，保持token shape的替换不会解除这个守卫。验证多种 modality token、纯文本input_ids、未接通的input_embeds负例、PP=1的graph/eager及多stage eager、位置复用与mask回退。保持形状的替换解决特定图约束，不证明整套 Gemma4 VLM 已在所有 NPU 产品验证。回退应保留模型 PLE/mask 语义，必要时重建 eager runner；本次未执行模型或性能测试。
