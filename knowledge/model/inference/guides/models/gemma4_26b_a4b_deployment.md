---
type: Guide
title: Gemma-4 文本 Decoder 当前部署
description: 当前gemma_4入口、单一Decode配置、Page cache混合布局与等长限制、MC2/图后端和RoPE验收。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/models/modeling_gemma4.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/agentic/optimization_report.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/config/gemma4_rank_8_8ep_decode.yaml
  role: example
created_at: '2026-10-21T09:56:17Z'
updated_at: '2026-10-29T14:25:50Z'
platforms:
- a2
- a3
---

# Gemma-4 文本 Decoder 当前部署

## 准备与配置

当前目录为models/gemma_4，覆盖A2/A3文本Decoder，视觉塔未覆盖。README环境CANN9.0.0、PyTorch2.8.0、torch_npu2.8.0.post4（发布26.0.0）、Python3.11；按requirements锁定transformers等实际依赖，源码头部上游版本注释不是安装版本。

准备完整BF16权重，复制models/gemma_4/chat_template.jinja到权重目录；config/gemma4_rank_8_8ep_decode.yaml设置model_path。当前示例world8、Attention/Dense TP1、MoE EP8、Embedding/LMHead TP8、batch8、输入256/输出32，默认GE。

```bash
bash executor/scripts/infer.sh --model gemma_4 --yaml gemma4_rank_8_8ep_decode.yaml
```

旧gemma4_rank_8_8ep_gegraph_decode.yaml已撤下，不能在新目录照抄旧配置名。

## 当前缓存、路由和图执行

当前为统一Page cache，两套attention类型分别分配block pool。Sliding TND，Full Prefill BNSD/Decode PA的BSH视图；同batch Prefill必须等长，入口会显式拒绝变长。不要再配置runner连续缓存或BSND shim。

纯EP Decode固定MC2 dispatch/combine，参数在权重处理后预置避免首步构图变化；旧local_experts和moe_ep_decode_mode开关已删除。A2专家/rank能力需按实际算子确认，不能靠已移除的自动回退。当前EP8为128/8=16专家/rank。

Decode可GE或npugraph_ex，Prefill eager；GE使用torchair算子与Tensor长度，npugraph Decode用host list。enable_static_kernel仅npugraph_ex生效，enable_cache_compile默认false，缓存按共享执行器处理。

## 数值核对

Full K/V共享投影但不共享cache，scale=1.0。当前partial RoPE抽取两半成对维度，频率按full head_dim和factor计算；避免照搬旧前缀切片。Dense激活按配置，专家图Decode实际为F.gelu(tanh)*up，报告npu_fast_gelu文字已落后于实现。原报告字节一致的基线声明不代替目标build复测。

## 验证与回退

固定prompt/seed/权重和长度，对照eager/目标图后端，核对所有sliding/full输出、缓存slot、路由和生成token；再测冷编译、稳态、内存与重复统计。失败时恢复合法等长输入和eager基线，不能切到已删除local_experts。

最新来源[A2观测](../../optimizations/benchmark_observations/gemma4_a2_source_benchmark.md)和[A3观测](../../optimizations/benchmark_observations/gemma4_a3_source_benchmark.md)分组读取；旧路由模式消融不再作为当前可执行配置。本次未运行NPU。


## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/README.md)（primary）
- [modeling_gemma4.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/models/modeling_gemma4.py)（implementation）
- [optimization_report.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/agentic/optimization_report.md)（supporting）
- [gemma4_rank_8_8ep_decode.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/config/gemma4_rank_8_8ep_decode.yaml)（example）
