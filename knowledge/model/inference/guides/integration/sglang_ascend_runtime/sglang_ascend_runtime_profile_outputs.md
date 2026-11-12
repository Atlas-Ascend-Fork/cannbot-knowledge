---
type: Guide
title: SGLang NPU性能采集的Profiler补丁、输出与版本分支
description: 说明GPU活动名映射NPU、旧采集器Level1 PipeUtilization配置与V2不同、NPU trace handler输出和停止时跨rank屏障。
tags:
- task.debugging
- topic.performance.analysis
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/managers/scheduler_components/profiler_manager.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/observability/profile_utils.py
  role: implementation
created_at: '2026-11-08T12:07:27Z'
updated_at: '2026-11-09T04:34:03Z'
platforms: []
aliases:
- SGLANG_PROFILE_V2
- PipeUtilization
---

# SGLang NPU性能采集的Profiler补丁、输出与版本分支

NPU启动时通过apply_torch_npu_patches把profiler.profile和CPU/CUDA活动替换为torch_npu实现，因此请求中的GPU标签可能实际采集NPU。旧patch API按指定列表应用，新API调用全量patch，必须记录TorchNPU版本，不能仅凭用户参数名推断输出设备。

旧_start_profile在torch活动非空时使用tensorboard_trace_handler输出目录，并给NPU ExperimentalConfig：Text、Level1、PipeUtilization，msprof_tx/l2_cache/op_attr/record_op_args关闭，data_simplification=False。with_stack默认True、record_shapes默认False；这些均会影响开销与可见信息，Level1未记录的细节不能从trace缺失推断任务不存在。

SGLANG_PROFILE_V2 将采集委托 ProfileManager，当前仅支持阶段触发：配置须满足 start_step=None、profile_by_stage=True、merge_profiles=False。manual_start/manual_stop 均抛 NotImplementedError，SchedulerProfilerManager 的手动启停也会委托至此，不能切换V2后沿用旧路径的手动操作；其_ProfilerTorch同样用NPU trace handler，但此构造点没有旧路径的ExperimentalConfig，不能宣称两代默认采样指标完全相同。两者NPU停止后不走普通export_chrome_trace文件命名分支，应从handler生成目录寻找产物；停止包含CPU组barrier，部分rank没有对应停止会影响完成。

MEM与CUDA_PROFILER仍分别调用torch.cuda.memory/cudart路径，此处没有证明其全部能力已被NPU补丁实现；优先使用已明确的NPU profiler路径并核对运行环境。采集结果必须标明预热、Prefill/Decode、shape、并行、量化和采集设置，拆分Host等待/通信/AIV/AIC与端到端指标。本文仅记录采集实现，未实际生成或分析真机trace。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
