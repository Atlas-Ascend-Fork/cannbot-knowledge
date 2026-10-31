---
type: Concept
title: Kimi-K2-Thinking：MLA/MoE 与原生混合精度
description: 依据当前Kimi统一Executor实现说明64 heads、原始W4A16/BF16混合精度、packed MLA、CP与MTP边界。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.mixture_of_experts
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/models/modeling_deepseek.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/config/kimi_k2_thinking.yaml
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/kimi_k2_thinking/kimi_k2_thinking_inference_guide.md
  role: implementation
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T14:52:59Z'
platforms:
- a3
---

# Kimi-K2-Thinking：MLA/MoE 与原生混合精度

Kimi-K2-Thinking属于MLA与共享/路由专家MoE架构，当前实践说明Attention为64 heads，MoE W4A16、Attention BF16。head数减少是模型结构事实，不能单凭它保证投机解码收益。

当前models/kimi_k2_thinking保留独立建模适配，但已接统一CANN Executor，不再有私有infer.py/runner_deepseek.py部署链。Attention用packed TND，CacheEntry声明NoPE/RoPE分页缓存；FIA v2使用TND_NTD，输出NTD须按实际布局还原。Prefill CP按每请求头尾分段，临时计算KV与后续持久KV分开，见[CP案例](../../optimizations/cases/deepseek_kimi_a3_prefill_cp.md)。

默认原始权重直载，量化scheme由checkpoint及模块loader识别；当前YAML只指model_path，没有独立mm_quant_mode/gmm_quant_mode字段。默认不代表纯BF16，也不能由同族R1反推完整W8A8C8方案：Kimi代码虽有C8类型/守卫分支，当前README没有给完整C8权重、scale和验证配方。

当前支持enable_mla_prolog、多流及GE SuperKernel相关分支；统一配置提供eager/ge_graph/npugraph_ex，默认样例用npugraph_ex。模型MTP类已注册，校验next_n不超过3，但默认样例为0；需要匹配的MTP权重，不能把代码存在当作收益已验证。

长序列文档的4K单机/256K多机和1~24节点是实践建议，不能当成当前默认配置或任意batch的容量上限。部署环境、开关及验收见[当前Guide](../../guides/models/kimi_k2_thinking_deployment.md)。

## 相关机制

- [MLA](../modules/mla.md)与[在线权重切分](../techniques/online_weight_split.md)
- [MTP](../techniques/mtp_speculative_decoding.md)与[计时](../../optimizations/rules/mtp_decode_timing_two_metric_split.md)
- [局部TP](../../optimizations/rules/local_tp_memory_heavy_projections.md)与[MoE多流](../techniques/moe_multi_stream.md)


## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/README.md)（primary）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/models/modeling_deepseek.py)（implementation）
- [kimi_k2_thinking.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/config/kimi_k2_thinking.yaml)（implementation）
- [kimi_k2_thinking_inference_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/kimi_k2_thinking/kimi_k2_thinking_inference_guide.md)（implementation）
