---
type: Guide
title: Kimi-K2-Thinking A3：当前统一 Executor 部署
description: 更新当前A3环境、kimi_k2_thinking.yaml、统一启动入口和真实custom_params，撤回旧私有runner与过时规模表。
tags:
- task.implementation
- topic.model_serving
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
created_at: '2026-10-21T09:56:19Z'
updated_at: '2026-10-29T14:52:59Z'
platforms:
- a3
---

# Kimi-K2-Thinking A3：当前统一 Executor 部署

## 环境和输入

当前README要求A3、CANN9.0.0、PyTorch2.8.0、torch_npu 2.8.0.post4（扩展v26.0.0）、Python3.11；按该模型requirements安装依赖，配置executor/scripts/set_env.sh的IP和CANN路径。原始Kimi-K2-Thinking权重放各节点相同可达路径，无本模型weight_convert.sh。

## 当前样例

models/kimi_k2_thinking/config/kimi_k2_thinking.yaml为当前离线样例，旧rank_64/rank_128 benchmark文件已删除：

| 配置 | 当前值 |
| --- | --- |
| world_size/cp_size | 32/32，CP只用于Prefill |
| batch_size/输入截断/最大新token | 32/65536/256 |
| attn_tp/o_proj_tp/dense_tp/moe_tp | 1/8/4/1 |
| embed_tp/lmhead_tp | 16/16 |
| exe_mode/static_kernel/cache_compile | npugraph_ex/true/false |
| next_n/force_eplb | 0/false |
| custom_params | enable_mla_prolog=true、enable_multi_streams=true、enable_superkernel=false |

量化配置来自实际权重，不从文件名推定。默认原生MoE W4A16/Attention BF16；不能原样套R1的C8系数或量化命令。

## 启动

从仓根执行：

```bash
bash executor/scripts/infer.sh --model kimi_k2_thinking --yaml kimi_k2_thinking.yaml
```

各节点分别启动。InfiniteBench长文本需放dataset/InfiniteBench；简单验证可改dataset=default并使用内置prompt。日志在模型res目录。

在线用--mode online与--pd-role prefill/decode，当前PD配置在模型config/pd下；须按PD两端拓扑、缓存布局和传输约束核对，不能把离线cp_size=32直接搬到在线D侧（强制CP1）。

## 开关与限制

enable_mla_prolog已是当前custom_params开关；多流和cache_compile属于图相关组合，eager打开会被模型拒绝。SuperKernel源码只在GE分支启用，npugraph_ex默认样例保持false；static_kernel只允许npugraph_ex。moe_chunk_max_len必须为正。

原生MTP需要独立的预测层权重，next_n支持0~3，默认关闭。先按[MTP接入](../integration/mtp_speculative_decode_model_onboarding.md)核对注册、隐状态与缓存，再测接受长度；64heads不能替代实测收益。

## 验收与回退

保存权重/量化配置、软件、rank/设备映射与完整输入，先验证合法eager基线（关闭图专属开关），再逐项启用融合、图、多流和静态核。覆盖多请求不等长、EOS/最大长度、CP所有者及长输入，记录输出、峰值内存、TTFT、Decode与服务端计时，分开冷启动/预热/稳态。

失败时恢复对应权重、配置和编译缓存；本次未运行模型，不宣称该部署或回退已验证。


## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/README.md)（primary）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/models/modeling_deepseek.py)（implementation）
- [kimi_k2_thinking.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/config/kimi_k2_thinking.yaml)（implementation）
- [kimi_k2_thinking_inference_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/kimi_k2_thinking/kimi_k2_thinking_inference_guide.md)（implementation）
