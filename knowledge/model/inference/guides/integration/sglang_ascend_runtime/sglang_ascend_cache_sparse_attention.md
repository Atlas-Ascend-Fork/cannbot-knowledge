---
type: Guide
title: SGLang稀疏卸载Attention的BSND Decode与TND Prefill交接
description: 说明紧凑selected KV的TopK重编号、dummy空行、hit/miss消费依赖、Prefill完整前缀物化及CP分支边界。
tags:
- task.implementation
- topic.attention
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/sparsity_driven_kv_offload/attention.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/sparsity_driven_kv_offload/manager.py
  role: implementation
created_at: '2026-11-08T11:53:42Z'
updated_at: '2026-11-09T04:33:25Z'
platforms: []
aliases:
- forward_sparsity_driven_kv_offload
---

# SGLang稀疏卸载Attention的BSND Decode与TND Prefill交接

入口要求q_rope、k_rope、topk_indices，manager必须已初始化；忽略传入v，因为MLA共享latent既作K也作V。save_kv_cache为真先以offload_v2保存当前forward紧凑KV，不把out_cache_loc当源行索引。

Decode先归一化TopK，宽度须正且不超过device sparse window；小于固定窗口时仅给 Attention 所用 topk_2d 补 -1；物化仍收到原 topk_indices。B>1 且 K<window 时，manager 按原 K 生成扁平目标步长，而 selected buffer 按 window 分请求，存在跨请求写读错位（如 B2/K2/window4 第二请求写槽2、3而读取从4开始）。该组合不能因补齐分支存在就视为完整支持，应保证原始 K=window 或另行修复并验证步长。要求KV头数1，为padded query heads创建零初始化selected [B,window,1,latent+rope]，触发manager物化，当前流等hit_done/miss_done后才读取。

原逻辑token索引转换成selected buffer内0..window-1的局部索引；无效槽仍-1，不可把原全context索引直接送紧凑buffer。KV有效长度按TopK mask求和并clamp至少1；空行首槽改指0以避免零长度 Kernel 路径，但零值仅在该槽未被物化写入时成立。Attention 的 mask 还把 seq_lens<=0 行判为空，manager 的物化 mask 只检查请求编号与 TopK 非负/未越界、不检查 seq_lens；有效请求配合法 TopK 即使 seq_lens<=0 仍可能写首槽，不能保证其为零。query长度均1，使用npu_sparse_flash_attention的BSND/BSND、sparse_mode=0、attention_mode=2，再裁掉padded query heads。

返回前还等待refill_done和slot_map_done，这两个事件是下一步缓存状态安全的条件，不可删掉只看当前输出就绪。计时要覆盖物化、Attention和状态刷新，而不只测融合Attention本体。

非Decode路径用TND和sparse_mode=3。普通Prefill通过get_forward_kv物化完整Host prefix，KV累计边界是cumsum真实seq_lens；其余模式的长度来自forward metadata、CPU int lengths或设备seq_lens，不能混为逐请求长度与累计长度。满足DSA Prefill CP及metadata时先走do_cp_balance_attn，不会无条件套上述完整Host拼接路径；组合是否满足上下文分片语义需另核验。

验证同时覆盖单/多请求、短于/等于窗口K、空行、padded头、Prefix Extend与CP；比较原native路径和卸载结果，记录Host回传及各事件。函数含动态分配与部分Host控制，不能单凭Decode静态shape宣称所有Prefill/投机图模式已验收。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
