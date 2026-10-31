---
type: Concept
title: NPU 图模式（ge_graph / npugraph_ex）
description: NPU 图模式 ge_graph / npugraph_ex 的执行与编译入口：GE 整图、NpuGraphEx、动态/静态编译、Decode 缓存和后端约束，区分当前接口与旧 ACLGraph tagged API。
tags:
- task.optimization
- topic.model_architecture
- topic.attention
- topic.graph_execution
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
created_at: '2026-04-15T00:00:00Z'
updated_at: '2026-10-29T15:57:02Z'
platforms:
- agnostic
---

# NPU 图模式（GE 与 npugraph_ex）

## 机制与当前入口

图编译/捕获把多算子前向交给后端调度，减少Host逐算子下发，可能同时改善融合、内存规划和执行开销。GE与npugraph_ex各自处理成图与执行，冷启动编译、持久缓存和稳态重放是不同测量对象，不能合并为一个收益。

当前cann-recipes-infer用model_config.exe_mode选择eager、ge_graph、npugraph_ex；旧acl_graph不是合法配置。共享ModelWorker仅对Decode调用已编译函数，Prefill为eager。动态能力还受模型、算子、元数据与控制流限制，不从当前阶段路由推导所有Prefill均不宜入图。

## 两条后端路径

GE使用TorchAir CompilerConfig与get_npu_backend，dynamic=False、fullgraph=True，缓存通过TorchAir cache_compile/ge_cache=True。npugraph_ex使用独立backend/options，dynamic取enable_dynamic_graph（默认True），可选static_kernel_compile。通用工具还传SuperKernel选项，具体模型可额外限制组合。

两者并非只替换名字：配置对象、缓存API、跨流同步和部分算子参数类型不同。当前主/draft分别编译main_decode/mtp_decode，缓存按实际decode宽度分区。npugraph_ex缓存的非预热执行跳guard，输入契约仍须严格覆盖。

## 选择与验证

从Host gap、设备时间线和真实业务指标判断候选；图执行不是必然更快。需验证输出、KV原地更新、packed token/投机宽度、动态长度和跨流生命周期，分别测首次编译与稳态。配置、后端与模型改变时，隔离或定向失效缓存。

- [图模式决策](../../optimizations/rules/graph_mode_enable_decision_profiling.md)
- [当前编译指南](../../guides/optimization/graph_mode_decode_only_compile_backends.md)
- [编译缓存](../../optimizations/rules/torchair_cache_compile_persisted_graph.md)
- [跨流同步](../../optimizations/rules/graph_mode_multi_stream_cross_stream_sync_api.md)
- [待核验记录](../../optimizations/cases/graph_backend_layout_unverified_observations.md)

本次未执行NPU编译，不将来源性能或历史排障假设当作已验证结论。


## Evidence

- [graph_utils.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/graph_utils.py)（primary）
- [model_worker.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py)（implementation）
- [execution_engine.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/engine/execution_engine.py)（implementation）
- [inference_config.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/inference_config.py)（constraint）
