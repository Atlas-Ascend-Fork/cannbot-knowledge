---
type: Guide
title: Qwen Dense A2/A3 当前部署与量化验收
description: 当前Qwen Dense六类YAML、W8A8全量化导出与融合MLP、共享执行器和分阶段来源性能验收。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen/models/modeling_qwen.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/qwen/qwen_dense_optimization.md
  role: supporting
created_at: '2026-10-21T09:56:20Z'
updated_at: '2026-10-29T14:21:59Z'
platforms:
- a2
- a3
---

# Qwen Dense A2/A3 当前部署与量化验收

## 环境与变体

当前README要求CANN9.0.0+、PyTorch2.8.0、torch_npu v26.0.0（wheel2.8.0.post4）、transformers5.0.0、compressed-tensors0.6.0与Python3.11。Qwen3-8B有QK-Norm且attention_bias=False；Qwen2.5-7B没有QK-Norm且bias=True。按实际HF配置核对，不套用其他规格维度。

## 当前六类YAML与入口

models/qwen/config中，Qwen3-8B提供qwen3_8b_1tp/2tp与qwen3_8b_w8a8_1tp/2tp四种YAML；Qwen2.5提供qwen25_7b_instruct_1tp/2tp。设置model_path和输入输出预算，从仓库根运行：

```bash
bash executor/scripts/infer.sh --model qwen --yaml qwen3_8b_1tp.yaml
```

当前示例为offline，使用packed TND和Page Attention。图执行和缓存由共享执行器负责；旧QwenRunner编译与模型目录CASE_NAME缓存片段不是当前接口，实际缓存路径按[编译缓存规则](../../optimizations/rules/torchair_cache_compile_persisted_graph.md)核对。

## W8A8权重与融合分支

Qwen3-8B使用AMCT导出compressed-tensors W8A8：INT8 per-channel权重、per-token动态激活，覆盖attention q/k/v/o与MLP gate/up/down；框架通过fused_mapping映射非融合层名。不要仅量化MLP后套用这组全量化配置。当前README报告不匹配导出会输出异常，不解释为任意部分量化必然失效。

AMCT依赖安装可能改变torch_npu，完成后复核并恢复目标wheel；setuptools<82是来源流程的pkg_resources兼容建议。量化模型需实际命中mm_quant_mode=w8a8int8和dequant_swiglu_quant融合路径，见[模型机制](../../concepts/models/qwen_dense.md)，不能以YAML文件名证明量化已启用。

## 当前来源性能与验证

README给出Atlas A3/910C单die64GB、GE、输入截断4096/输出256的Qwen3-8B表：BF16 TP1/TP2 Prefill41.12/51.56ms，Decode15.48/10.35ms；W8A8 TP1/TP2 Prefill36.00/58.95ms，Decode10.46/7.90ms。TP2的Prefill在该表更慢，不能将Decode收益推广全部阶段。来源披露采集环境和日期，但缺原始逐轮样本/方差；本次未复测。

以相同prompt、权重、并行和软件对照BF16/W8A8，验token/任务质量、峰值内存、冷编译与稳态。异常时重载匹配BF16权重和配置；不能只关闭一个flag继续使用已量化张量。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen/README.md)（primary）
- [modeling_qwen.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen/models/modeling_qwen.py)（implementation）
- [qwen_dense_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/qwen/qwen_dense_optimization.md)（supporting）
