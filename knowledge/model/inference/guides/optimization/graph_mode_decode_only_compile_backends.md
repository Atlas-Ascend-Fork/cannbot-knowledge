---
type: Guide
title: LLM Decode 图模式：编译配置、backend 定界与精度排查
description: LLM 图模式的 GE/npugraph_ex 编译配置、backend/aot_eager 精度定界、frozen_parameter 冻结与非连续权重、dynamic 长度和版本故障。
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
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-graph-mode/SKILL.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-graph-mode/references/npugraph_ex-guide.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-graph-mode/references/llm-model-guide.md
  role: supporting
- resource: https://www.hiascend.com/document/detail/zh/Pytorch/730/modthirdparty/torchairuseguide/torchair_00031.html
  role: supporting
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-11-10T02:01:56Z'
platforms:
- agnostic
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
aliases:
- 图模式精度与 backend 分层定界
- frozen_parameter 非连续权重
- GE npugraph_ex options 配置
- LLM Decode 图编译指南
- config.debug.run_eagerly
- save_npugraph_tensor
---

# LLM Decode 图模式：编译配置、backend 定界与精度排查

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

## 按版本核对配置与故障

迁移旧 Skill 的配置时，区分三层：InferenceConfig 的模型开关、graph_utils 实际传给后端的参数、安装版本 TorchAir/npugraph_ex 支持的 options。不能把参考指南里整份 options 表当成统一 YAML 字段，也不能假定示例默认值等于当前框架默认值。

| 参考选项 | 用途与检查点 |
| --- | --- |
| force_eager | npugraph_ex 定界用，不能当 GE 的等价配置；用匹配版本的接口确认可用性 |
| inplace_pass / input_inplace_pass / pattern_fusion_pass | 图变换开关；改变前后需检查变异、别名和输出，不凭关闭某项就判定根因 |
| reuse_graph_pool_in_same_fx / use_graph_pool / clone_input / clone_output | 图池、输入输出生命周期与复制相关；具体默认值和安全条件按安装后端确认 |
| frozen_parameter / static_kernel_compile / remove_noop_ops | 冻结参数、静态 kernel 与清理开关；固定框架 npugraph_ex 实际开启 frozen_parameter，并按 enable_static_kernel 配置静态编译 |
| capture_limit | 某些版本的捕获次数限制，不是修改 batch/shape 合法性的替代手段 |

旧指南“LLM Decode 一律 dynamic=False”不适用于该框架的默认 enable_dynamic_graph=True。遇到 `hit recompile_limit`，先检查每步变化的 `kv_len` / `actual_seq_lengths_kv` 及重编译日志中的 guard；长度 list 的 Python 值变化、Tensor 值变化、shape/stride 变化是不同 guard 条件，不能仅提高重编译次数上限来掩盖签名变化。读取实际调用重载后再决定 dynamic 或静态标记。FIA 的 torch_npu host list 与 GE 包装 Tensor 签名见[长度参数诊断](../../runbooks/runtime/fia_actual_seq_lengths_kv_backend_type.md)，不能跨版本统一转换。

仅图模式精度异常时，依次比较原 eager、torch.compile backend=eager（捕获）、backend=aot_eager（含功能化），再检查目标后端的逐算子定界方式与完整图。不同后端没有天然完全等价的 debug 开关；关闭冻结参数或图优化仅用于对照。若 parameter 非连续，结合真实 stride、冻结前后输出和该模块的后处理检查，先参见[gate 权重布局](../../runbooks/runtime/ge_graph_moe_gate_router_weight_layout.md)，不能把所有错误都归因于 frozen_parameter。

官方文档索引与 torch_npu 接口列表只提供导航，不构成接口/产品支持保证；选择与当前软件版本一致的后端文档，并以具体接口及模型路径核验。不要把未在该版本运行过的 save_npugraph_tensor 等示例写成已经验证的取值工具。

## 旧图内取值示例的适用性

旧精度参考给过 `torch_npu.save_npugraph_tensor` 例子；本次固定 Recipes 没有实际模型调用，尚不能承诺任意 tensor list、私有格式、路径创建或目标图后端均可用。该名字可作为版本核对入口，不能把历史示例写成已经过 NPU 验证的通用取值工具。

GE 的 `config.debug.run_eagerly` 与 npugraph_ex 的 force_eager 不等价。TorchNPU 7.3.0 文档将前者用于图执行前以 Eager 运行 FX graph，帮助定界图变换与执行器；max-autotune 下其他功能配置不与其同时生效，reduce-overhead 下可组合的项目也受该版本限制。通用定义见 [TorchAir 诊断配置](../../concepts/frameworks/torchair.md#版本化诊断配置)，不要把旧 reduce-overhead 配置表当成当前独立 npugraph_ex 的 options。

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

- [.agents/skills/model-infer-graph-mode/SKILL.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-graph-mode/SKILL.md)（supporting）

- [.agents/skills/model-infer-graph-mode/references/npugraph_ex-guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-graph-mode/references/npugraph_ex-guide.md)（supporting）

- [.agents/skills/model-infer-graph-mode/references/llm-model-guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-graph-mode/references/llm-model-guide.md)（supporting）

- [https://www.hiascend.com/document/detail/zh/Pytorch/730/modthirdparty/torchairuseguide/torchair_00031.html](https://www.hiascend.com/document/detail/zh/Pytorch/730/modthirdparty/torchairuseguide/torchair_00031.html)（supporting）
