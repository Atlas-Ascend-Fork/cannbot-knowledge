---
type: Guide
title: kernel_details 字段解读：流水指标、控核与多流真实重叠
description: kernel_details.csv 字段解读：OP State 是执行状态，不能当作精度检查 pass/fail；区分 Type 的 HCCL/AI_CORE 与 Accelerator Core，解释 aic_mac_ratio、aic_mte2_ratio、aiv_mte3_ratio、时间、核数与重叠。
tags:
- task.optimization
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-perf-breakdown/references/kernel_data_guide.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-multi-stream/references/kernel-fields-lookup.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-multi-stream/references/timeline-overlap-check.md
  role: supporting
created_at: '2026-11-09T09:23:48Z'
updated_at: '2026-11-10T04:11:13Z'
platforms:
- a2
- a3
aliases:
- kernel_details.csv 字段
- aic_mac_ratio
- aic_mte2_ratio
- aiv_mte3_ratio
- aiv_vec_ratio
- Type 任务分类
- Accelerator Core
- OP State
- 任务执行状态
- Block Dim
- Block Num
- Mix Block Dim
- Mix Block Num
---

# kernel_details 字段解读：流水指标、控核与多流真实重叠

## 明细层级与基础字段

kernel_details.csv 一行通常对应一次设备 kernel/task 调用。Name/Type 标识任务，Step Id、Device_id、Model ID、Task ID、Context ID 提供上下文；不同版本有缺列和命名差异，先读取真实表头。OP State 记录任务执行状态，不等于数值精度或整网验收结果。Type 与 Accelerator Core 是不同字段，不能因都出现 AI_CORE/HCCL/MIX_AIC 就互相替代。

Start Time(us)、Duration(us)、Wait Time(us) 分别用于起始时刻、执行时长和等待信息；确认单位后再计算。Input Shapes、Output Shapes、Input Data Types、Output Data Types、Input Formats、Output Formats 可用于核对 shape/dtype 与转换，但未采集或为空不代表输入无形状。Block Dim/Block Num、Mix Block Dim/Mix Block Num 是并行资源线索，不等于无条件独占全部硬件核。

## 扩展指标与解释边界

字段名按来源完整保留，避免用 `aic_mte1/2_ratio` 一类缩写代替实际 CSV 列名。每组 time 字段以采集文件的 `(us)` 等单位后缀为准。

| 字段组 | 完整字段示例 | 解释与边界 |
| --- | --- | --- |
| Cube 时间与周期 | aicore_time(us)、aic_total_cycles | 设备任务的 AI Core 时间与周期，不能直接替代端到端 wall time |
| Cube 计算 | aic_mac_time(us)、aic_mac_ratio、cube_utilization(%) | MAC 活跃与利用率线索；确认 ratio 的定义及量纲 |
| Cube 搬运 | aic_mte1_time(us)、aic_mte1_ratio、aic_mte2_time(us)、aic_mte2_ratio、aic_fixpipe_time(us)、aic_fixpipe_ratio | 定位输入搬运/流水；高比例本身不证明 HBM 饱和 |
| Cube 标量与指令缓存 | aic_scalar_time(us)、aic_scalar_ratio、aic_icache_miss_rate | 标量与指令行为，结合任务类型和持续时间 |
| Cube 工作量 | aic_mac_fp16_ratio、aic_mac_int8_ratio、aic_cube_fops | fops 为固定来源的字段拼写；不由时间 ratio 推算总 FLOPs |
| Vector 时间与周期 | aiv_time(us)、aiv_total_cycles | Vector 时间和周期，需要与 Cube 分支的统计口径区分 |
| Vector 计算 | aiv_vec_time(us)、aiv_vec_ratio、aiv_scalar_time(us)、aiv_scalar_ratio | 分析 Vector/标量占用与拖尾 |
| Vector 搬运 | aiv_mte2_time(us)、aiv_mte2_ratio、aiv_mte3_time(us)、aiv_mte3_ratio | 分析搬入/搬出压力，仍需结合 timeline 和实际版本 |
| Vector 工作量与指令缓存 | aiv_vec_fp32_ratio、aiv_vec_fp16_ratio、aiv_vec_int32_ratio、aiv_vec_misc_ratio、aiv_vector_fops、aiv_icache_miss_rate | 区分类型组成、工作量和指令缓存行为 |
| 控核与混合任务 | Block Num、Mix Block Num、Block Dim、Mix Block Dim、Accelerator Core | 字段名随版本变化；Mix 任务同时观察主/从加速器核数 |

来源表将部分 ratio 标为0～1，其他列如 cube_utilization(%) 明确使用百分比；不能只看值域或列名就混用。HF32 Eligible 是资格标记，不证明该次已实际采用 HF32。扩展列是否存在由工具版本、等级、指标组、shape 开关和算子支持共同决定。

Type 的示例分类有 AI_CORE、AI_CPU、HCCL、MIX_AIC、MIX_AIV、FFTS_PLUS、DVPP；Accelerator Core 另有 AI_VECTOR_CORE、COMMUNICATION 等标识。Name 中的 HcomAllReduce 是通信线索，MatMulV3 / QuantBatchmatmulV3 / AddRmsNormCast、BroadcastTo、MemSet 是分析时可能遇到的计算或搬运任务名，不凭名称给所有版本强制分组。具体 Type、Core、shape、依赖和持续时间应同时核对；不要把脚本的 normalized_name 或 resource_hint 当作原始 profiler 字段。

## 设计候选与复盘所需字段

设计并行候选可先看 Stream ID、Task ID、Name、Shapes、Duration、Wait；验证真实 overlap 还必须拿同一次采集的 Start Time。将每个区间表示为 [start, start+duration]，两区间交集为 max(0, min(end1,end2)-max(start1,start2))；扩大到多 kernel 时按事件区间和依赖分析，不能重复累计重叠区间。

Stream ID 不同只证明流不同，不能证明时间重叠；有重叠也可能因资源竞争与拖尾没有净收益。不同 run 的 Start Time 不能互相比较，kernel Duration 的总和也不是多流 wall time。只抽取当前问题相关的几行几列，再结合 timeline 的等待边和关闭 profiler 的端到端测量。

相关：[采集指标选择](npu_profiling_collection_and_metrics.md)、[多流流程](multi_stream_optimization_workflow.md)。

## Evidence

- [.agents/skills/model-infer-perf-breakdown/references/kernel_data_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-perf-breakdown/references/kernel_data_guide.md)
- [.agents/skills/model-infer-multi-stream/references/kernel-fields-lookup.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-multi-stream/references/kernel-fields-lookup.md)
- [.agents/skills/model-infer-multi-stream/references/timeline-overlap-check.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-multi-stream/references/timeline-overlap-check.md)
