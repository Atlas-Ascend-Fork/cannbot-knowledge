---
type: Optimization
title: SGLang KV静态预算与mem-fraction-static的正确调参方向
description: 用_profile_available_bytes说明权重后free内存、非静态slack、Mamba和多模态预留的扣费，并保留FAQ关于KV占用方向的冲突。
tags:
- task.optimization
- topic.kv_cache
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/kv_cache_configurator.py#L2967-L3037
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/fields/memory.py
  role: supporting
created_at: '2026-11-08T11:53:43Z'
updated_at: '2026-11-08T11:53:43Z'
platforms: []
---

# SGLang KV静态预算与mem-fraction-static的正确调参方向

## 场景与公式

当前SGLang在权重加载后的可用空间中规划KV，_profile_available_bytes先gc.collect，再通过get_available_gpu_memory取free值（分布式时依组取保守口径）。单位为GiB，最终乘2^30转字节：

```text
slack = pre_model_load_memory * (1 - mem_fraction_static)
rest = current_free_memory - slack - mm_runtime_reservation
```

Mambaish模型在非unified memory下还扣实际状态预算。部分post-capture-KV模式对Mamba需要最小pre-capture activation reserve，使slack不能无条件趋零；只有满足明确Prefill full-graph、显式Mamba size和请求上限条件才豁免这条补足。

## 调参方向与失效边界

其他项不变，增大mem_fraction_static会减小非静态slack、增加可给KV的预算，不是减少KV占用；它可能解决“权重加载后静态预算没有留给KV”的初始化失败，却压缩后续激活/workspace余量。若rest<=0，源码计算minimum=1-free/pre并提示把fraction调高到最小可行值之上；这个阈值提示不包含所有后续模型风险或测得的稳定上限。

反过来，运行期激活OOM常需减小静态fraction、batch/token或图桶，不能因启动错误建议上调就把同一方向用于所有OOM。字段解析、模型override、Mamba/多模态预留和图捕获阶段会继续改变实际空间；不要把这个局部公式当整模型全部内存账。

## 实施、代价与验收

先区分初始化“no memory for KV”和运行期/图捕获OOM，记录权重前容量、权重后free、fraction、MM/Mamba reserve与最后KV token容量。以固定模型、并行、batch和上下文逐步改一个变量，复核冷启动与多轮峰值、TTFT/TPOT及精度。回退为保存的上一配置和对应池重建，不在活请求中改变已规划容量。

若文档将“增大fraction”写成“减少KV占用”，应按上述固定实现保留为来源冲突，不机械入库为优化规则；也不能因此改写其他框架/旧Recipes中不同预算代码的语义。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
