---
type: Optimization
title: MoE Decode：按当前后端编排共享与路由专家
description: 更新GE stream22和npugraph_ex原生流/事件的共享专家编排，明确combine解耦仍不证明实际重叠。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.graph_execution
- topic.implementation.synchronization
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/models/modeling_glm.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/models/modeling_deepseek.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/patches/stage1/0003-feat-moe-multi-stream.patch
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T14:57:06Z'
platforms:
- agnostic
---

# MoE Decode：按当前后端编排共享与路由专家

## 独立分支及合流

共享专家与路由专家可并行，但最终相加必须等待两边真实输出。enable_multi_streams只为相应Decode分支组织多流，不等于Prefill微批开关，也不能凭多流推导收益。

当前R1、V3.2-Exp、GLM-5和Kimi的统一Executor实现按后端区别：

| 后端 | 共享专家路径 | 依赖 |
| --- | --- | --- |
| GE | stream22先gate/up，在路由dispatch后做激活/量化，再按路由专家输出依赖做down | npu_wait_tensor连接各段；最终相加 |
| npugraph_ex | 独立原生NPU流执行共享专家 | record_stream管理生命周期，event0等输入，event1标记共享输出；主流在消费前wait |

旧stream11+acl_graph tagged-event分支已不适用。当前V3.2-Exp的MC2 combine不再通过shared_expert_x合并，而在combine后显式相加；原生流分支仍在combine前wait共享完成，因此接口解耦也不证明combine已经与共享计算重叠。

## SGLang 集成另行核对

Qwen3-Next stage1补丁由ENABLE_NPU_DEEPEP_MOE_MULTI_STREAM控制，通过全局shared_expert_stream与wait_stream分三段：gate/up、sigmoid/activation、down/门控乘，最后与DeepEP路由输出相加。这是SGLang补丁链，不能复制成统一Executor配置。LongCat的ScMoE是第二段Attention/FFN与MoE的另一种并行结构，见[多流机制](../../concepts/techniques/moe_multi_stream.md)。

## 验收与回退

固定模型、后端、量化、batch和图缓存；逐项检查输入可见性、临时张量生命周期、共享/路由输出合流，再看timeline是否有有效重叠和尾部等待。不要在本来Host或带宽受限时按空闲算力预估收益。关闭对应模型多流开关恢复基线并重验；本次仅静态核对，无硬件收益数字。


## Evidence

- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py)（primary）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py)（implementation）
- [modeling_glm.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/models/modeling_glm.py)（implementation）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/models/modeling_deepseek.py)（implementation）
- [0003-feat-moe-multi-stream.patch](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/patches/stage1/0003-feat-moe-multi-stream.patch)（implementation）
