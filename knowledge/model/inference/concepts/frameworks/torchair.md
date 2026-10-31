---
type: Concept
title: TorchAir
description: 当前 TorchAir GE 后端与独立 npugraph_ex 接口、模型特定组合限制、Decode 路由和性能归因边界。
tags:
- task.implementation
- topic.architecture
- topic.graph_execution
- topic.speculative_decoding
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/graph_utils.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/engine/execution_engine.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/inference_config.py
  role: constraint
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T13:49:53Z'
platforms:
- a3
---

# TorchAir 与当前推理图后端

## 作用

TorchAir为torch.compile提供昇腾图后端，GE路径将捕获图交给Ascend IR/GE编译调度，减少逐算子Host开销。当前推理框架另有npugraph_ex捕获重放路径，使用独立backend/options接口，不再将历史CompilerConfig的reduce-overhead参数表当作其当前配置。

## 当前配置

GE通过CompilerConfig设置frozen_parameter、tiling_schedule_optimize与StableRDFS，torch.compile使用get_npu_backend；持久缓存走TorchAir cache_compile/ge_cache=True。npugraph_ex直接选择backend=npugraph_ex，options包含static_kernel_compile等；dynamic由enable_dynamic_graph控制。

模型可用性与通用工具选项分别检查。比如LongCat拒绝npugraph_ex+SuperKernel，而通用编译函数已可传该选项；不能统一断言所有模型/后端都支持或都禁止。HCCL的AIV展开属于配套通信设置，不能当作TorchAir本身的通用要求。

## 执行与验证

共享ModelWorker对Decode调用已编译模型，Prefill仍eager；主/draft使用不同编译接口。稳定控制流、算子参数类型、Cache mutation和跨流同步决定适配是否正确。图与MTP的组合按模型worker和验证宽度核对，不以某个SGLang入口限制推导所有模型。

R1等来源性能包含量化、并行和多项优化，不归因于TorchAir单项。本次未进行图编译/精度/性能复测。

- [图编译指南](../../guides/optimization/graph_mode_decode_only_compile_backends.md)
- [跨流同步](../../optimizations/rules/graph_mode_multi_stream_cross_stream_sync_api.md)
- [缓存规则](../../optimizations/rules/torchair_cache_compile_persisted_graph.md)


## Evidence

- [graph_utils.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/graph_utils.py)（primary）
- [model_worker.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py)（implementation）
- [execution_engine.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/engine/execution_engine.py)（implementation）
- [inference_config.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/inference_config.py)（constraint）
