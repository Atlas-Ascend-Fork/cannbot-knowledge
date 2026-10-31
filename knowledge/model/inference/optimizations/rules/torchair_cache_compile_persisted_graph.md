---
type: Optimization
title: torchair cache_compile 图编译缓存落盘复用：调用约定、缓存失效与后端/版本约束
description: ge_graph Decode 低时延部署中，SuperKernel 调度融合与持久图编译缓存分别处理下发与冷启动编译开销；按融合范围核对 GE/npugraph_ex 的 cache_compile 调用、缓存签名、失效和复用边界。
tags:
- task.optimization
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
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T16:10:39Z'
platforms:
- agnostic
---

# 图编译缓存：当前入口与失效边界

## 适用与收益

图编译首次成本较高、且重复启动复用相同模型与部署配置时，可评估持久缓存。它针对重复成图/编译成本，不能据此归因稳态TPOT改善。eager不走编译工具，模型还可拒绝eager+缓存组合。

## 当前调用

enable_cache_compile=True时，GE用TorchAir cache_compile（dynamic=False、fullgraph=True、ge_cache=True）；npugraph_ex用torch.npu.npugraph_ex.inference.cache_compile，传自己的options和enable_dynamic_graph。关闭该开关时两者分别回到普通torch.compile。

当前cache_dir为model_config.output_path/compile_cache，可追加decode_q_len_<N>命名空间。主模型用main_decode、draft用mtp_decode等独立callable，不能靠旧CASE_NAME/_spec后缀替代当前接口。旧acl_graph的reduce-overhead、clone_input和历史版本下限不作为当前使用条件。

## 缓存与输入契约

变更软件、模型结构、权重布局、并行、shape关键配置或custom op时，隔离或定向失效匹配缓存，并重新预热校验。不能保证所有配置变化都由缓存自动识别，也不无条件清空共享缓存目录。

当前npugraph_ex持久缓存的非warmup执行跳过guard检查，这不放宽输入shape、地址、动态长度或分支契约。上线前必须覆盖实际输入域，主/draft和投机宽度分别检查。

## 验证与回退

分别记录冷启动、缓存命中后的启动与稳态指标，验证输出与图缓存确实复用；未命中或发生重编译时检查callable、命名空间与实际输入。关闭缓存开关只取消持久缓存，切eager才取消当前图路由。本次未执行编译或性能实验。

- [当前编译指南](../../guides/optimization/graph_mode_decode_only_compile_backends.md)
- [图模式决策](graph_mode_enable_decision_profiling.md)


## Evidence

- [graph_utils.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/graph_utils.py)（primary）
- [model_worker.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py)（implementation）
- [execution_engine.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/engine/execution_engine.py)（implementation）
- [inference_config.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/inference_config.py)（constraint）
