---
type: Guide
title: SGLang Diffusion SenseNova去噪：前缀缓存与循环外预计算
description: 说明FIA可用时BNSD缓存、Host可见长度、非FIA多batch的布尔mask回退和think_mode长度风险，及NPU时间/噪声嵌入预计算。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/models/sensenova_u1/neo_unify/modeling_neo_chat.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/models/sensenova_u1/neo_unify/modeling_qwen3.py
  role: implementation
created_at: '2026-11-08T12:27:29Z'
updated_at: '2026-11-09T04:32:43Z'
platforms: []
---

# SGLang Diffusion SenseNova去噪：前缀缓存与循环外预计算

## 缓存与布局

去噪前预分配prefix K/V缓存；NPU且FIA可用时使用BNSD，在prefix未被think_mode额外扩展的路径，将真实prefix与当前token按约定布局写入，actual KV长度为真实prefix+当前长度，padding数量独立传递。非FIA路径采用BSND，NPU不传该FIA专用actual lengths；NPU batch>1且无FIA时，t2i_generate构造带显式query维度的连续布尔key-padding mask并继续去噪，modeling_qwen3接受该mask进入注意力分支。

有效prefix长度与物理预分配容量不同。单batch、不等长文本和后续采样需用真实长度控制可见性，避免读取未写padding。已有cache不能跨不兼容请求条件复用。think_mode会由_generate_think写入思考token和追加文本、扩展cache，但随后prepare_flash_kv_cache仍接收扩展前condition_prefix_lengths，并据此拷贝prefix和计算actual长度；当前快照存在长度未同步的静态实现风险，不能保证该模式包含完整扩展prefix，本次未做数值复现。

## 循环优化与验收

NPU提前计算时间步和noise scale嵌入，CFG窗口相关条件在Host循环外准备，减少每步小算子及同步。它不改变去噪步序列或CFG数学定义。比较相同seed、prefix长度与CFG窗口下逐步输出，检查cache重置、尾部未初始化区、think_mode长度同步与多batch mask回退，再测循环Host开销。本文只做静态来源核对，没有运行精度/性能测试。
