---
type: Guide
title: LLM Decode 图编译指南（当前 GE 与 npugraph_ex）
description: 当前 Decode-only 路由、主/draft独立接口、两种编译后端、宽度命名空间、队列修复与预热验收。
tags:
- task.optimization
- topic.graph_execution
- topic.model_serving
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
updated_at: '2026-10-29T13:49:53Z'
platforms:
- agnostic
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
---

# 当前 LLM Decode 图编译与验收

## 路由与接口

当前 Executor 只在非 Prefill 且 exe_mode 为 ge_graph/npugraph_ex 时调用编译模型；Prefill走eager。这个路由不证明其他执行器的Prefill无法入图。

ModelWorker.compile_model 编译主模型 main_decode 或 draft 的 mtp_decode，也支持显式 interface_name/compiled_attr。主/draft使用不同callable以避免不必要重编译；缺少所选接口会RuntimeError。ForwardMetaData、位置和Cache更新必须遵守当前模型契约，不能继续复制旧runner的decode/mtp_compile_decode绑定。

## 后端配置

| 项 | GE | npugraph_ex |
| --- | --- | --- |
| 普通入口 | torch.compile + torchair.get_npu_backend | torch.compile backend=npugraph_ex |
| 持久缓存 | torchair.inference.cache_compile，ge_cache=True | torch.npu.npugraph_ex.inference.cache_compile |
| dynamic | False | model_config.enable_dynamic_graph，默认True |
| 配置 | CompilerConfig：frozen_parameter、tiling_schedule_optimize、StableRDFS | options：frozen_parameter、static_kernel_compile、super_kernel_optimize |

编译工具先patch_for_hcom以适配集合通信。npugraph_ex的通用编译工具可传SuperKernel选项，但模型仍可拒绝该组合（如LongCat）；不能将某模型限制当作整个后端限制。

当前枚举只接受eager/ge_graph/npugraph_ex，acl_graph不再是合法值。enable_static_kernel仅npugraph_ex允许。GE忽略enable_dynamic_graph并告警。

## 已修复的任务队列行为

ModelConfig.validate在npugraph_ex或950平台统一写TASK_QUEUE_ENABLE=1，其他情况写2。旧版“已为1时反而改成2”的分支缺陷已不存在。注意950 eager也为1，不能宣称所有eager都为2；检查实际配置解析后的环境。

## 预热与缓存

缓存根目录实际是model_config.output_path/compile_cache，传decode_q_len时附加decode_q_len_<N>命名空间。当前主模型预热在开启持久缓存时按next_n+1确定该宽度；不能沿用CASE_NAME或_spec目录约定。

预热按PD角色选择Prefill/Decode；Prefill token预算和CP mini-batch共同决定dummy形状，多模态可另行构建视觉输入，draft按自身worker预热。dummy配置不应代替真实边界输入覆盖。

npugraph_ex+持久缓存的非warmup执行使用skip_guard_eval_unsafe=True。它不能证明任意新shape均安全；上线前应覆盖实际batch/投机宽度、长度列表、KV地址、分支与模型状态，不能用跳guard掩盖签名变化。

## 验收与回退

先保存eager输出，再比较预热后的图执行、首次编译耗时、重复请求重编译和稳态时延。出现精度差异、签名不稳定或无净收益时，恢复合法eager/单流配置并核对缓存与源软件。enable_cache_compile=False只关闭持久缓存，仍使用对应普通编译后端。本次仅静态复核，未运行编译或NPU推理。

## 相关入口

- [图模式决策](../../optimizations/rules/graph_mode_enable_decision_profiling.md)
- [编译缓存](../../optimizations/rules/torchair_cache_compile_persisted_graph.md)
- [跨流同步](../../optimizations/rules/graph_mode_multi_stream_cross_stream_sync_api.md)


## Evidence

- [graph_utils.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/graph_utils.py)（primary）
- [model_worker.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py)（implementation）
- [execution_engine.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/engine/execution_engine.py)（implementation）
- [inference_config.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/inference_config.py)（constraint）
