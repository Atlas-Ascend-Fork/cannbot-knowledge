---
type: API
title: aclprofCreateConfig
description: "按 Device 列表、AI Core 指标及采集开关创建 Profiling 配置，可复用；使用后须 DestroyConfig 释放。"
tags:
- task.lookup
- topic.performance.analysis
- topic.implementation.resource_lifecycle
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/25-03_Operation_APIs.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_prof.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/dfx/msprof/collector/dvvp/msprofiler/prof_acl_api.cpp
  role: implementation
source_headers:
- include/external/acl/acl_prof.h
created_at: '2026-09-15T00:00:00Z'
updated_at: "2026-10-30T08:26:15Z"
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---

# aclprofCreateConfig

## 功能说明

创建aclprofConfig类型的数据，表示创建Profiling配置数据。
aclprofConfig类型数据可以只创建一次、多处使用，用户需要保证数据的一致性和准确性。
如需销毁aclprofConfig类型的数据，请参见[aclprofDestroyConfig](aclprof_destroy_config.md)。

## 函数原型

```c
aclprofConfig *aclprofCreateConfig(uint32_t *deviceIdList, uint32_t deviceNums, aclprofAicoreMetrics aicoreMetrics, const aclprofAicoreEvents *aicoreEvents, uint64_t dataTypeConfig)
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | :---: | --- |
| deviceIdList | 输入 | Device ID列表。须根据实际环境的Device ID配置。|
| deviceNums | 输入 | Device的个数。需由用户保证deviceIdList中的Device个数与deviceNums参数值一致，否则可能会导致后续业务异常。 |
| aicoreMetrics | 输入 | 表示AI Core性能指标采集项。请参见aclprofAicoreMetrics。 |
| aicoreEvents | 输入 | 表示AI Core事件，目前配置为NULL。 |
| dataTypeConfig | 输入 | 用户选择如下多个宏进行逻辑或（例如：ACL_PROF_ACL_API \| ACL_PROF_AICORE_METRICS），作为dataTypeConfig参数值。每个宏表示某一类性能数据，详细说明如下：<br><br>  - ACL_PROF_ACL_API：表示采集接口的性能数据，包括Host与Device之间、Device间的同步异步内存复制时延等。<br>  - ACL_PROF_TASK_TIME：采集算子下发耗时、算子执行耗时数据以及算子基本信息数据，提供更全面的性能分析数据。<br>  - ACL_PROF_TASK_TIME_L0：采集算子下发耗时、算子执行耗时数据。与ACL_PROF_TASK_TIME和ACL_PROF_TASK_TIME_L2相比，由于不采集算子基本信息数据，采集时性能开销较小，可更精准统计相关耗时数据。<br>  - ACL_PROF_TASK_TIME_L2：采集算子下发耗时、算子执行耗时数据、算子基本信息数据（包括attr），提供更全面的性能分析数据。<br>  - ACL_PROF_GE_API_L0：采集动态Shape算子在Host调度主要阶段的耗时数据，可更精准统计相关耗时数据。<br>  - ACL_PROF_GE_API_L1：采集动态Shape算子在Host调度阶段更细粒度的耗时数据，提供更全面的性能分析数据。<br>  - ACL_PROF_OP_ATTR：控制采集算子的属性信息，当前仅支持aclnn算子。<br>  - ACL_PROF_AICORE_METRICS：表示采集AI Core性能指标数据，逻辑或时必须包括该宏，aicoreMetrics入参处配置的性能指标采集项才有效。<br>  - ACL_PROF_TASK_MEMORY：控制CANN算子的内存占用情况采集开关，用于优化内存使用。单算子场景下，按照GE组件维度和算子维度采集算子内存大小及生命周期信息（单算子API执行方式不采集GE组件内存）；静态图和静态子图场景下，在算子编译阶段按照算子维度采集算子内存大小及生命周期信息。<br>  - ACL_PROF_AICPU：表示采集AI CPU任务的开始、结束数据。<br>  - ACL_PROF_L2CACHE：表示采集L2 Cache数据和TLB页表缓存命中率。<br>  - ACL_PROF_HCCL_TRACE：控制通信数据采集开关。<br>  - ACL_PROF_MSPROFTX：获取用户和上层框架程序输出的性能数据。可在采集进程内（[aclprofStart](../profiling_data_collection/aclprof_start.md)接口、[aclprofStop](../profiling_data_collection/aclprof_stop.md)接口之间）调用msproftx扩展接口或mstx接口开启记录应用程序执行期间特定事件发生的时间跨度，并写入性能数据文件，再使用msprof工具解析该文件，并导出展示性能分析数据。<br>  - ACL_PROF_TRAINING_TRACE：控制迭代轨迹数据采集开关；打开ACL_PROF_TASK_TIME开关时工具默认同时打开该开关。<br>  - ACL_PROF_RUNTIME_API：控制runtime api性能数据采集开关。<br>  - ACL_PROF_API_STATS：控制acl api的统计开关，打开此开关后，profiling会启用在线分析模式，统计acl api的性能数据。该模式下，其他开关无效。<br/>  - ACL_PROF_AICORE_SHAPE：CANN层算子的Shape数据采集开关，须配置ACL_PROF_TASK_TIME_L0。 |

## 返回值说明

- 返回aclprofConfig类型的指针，表示成功。
- 返回nullptr，表示失败。


## 约束说明

- 使用[aclprofDestroyConfig](aclprof_destroy_config.md)接口销毁aclprofConfig类型的数据，如不销毁会导致内存未被释放。
- 与[aclprofDestroyConfig](aclprof_destroy_config.md)接口配对使用，先调用aclprofCreateConfig接口再调用[aclprofDestroyConfig](aclprof_destroy_config.md)接口。

## 最小调用示例

以下示例来自 Runtime 固定 commit `b523035a08ef573b6bc476c8ab2a34733ba069a4` 的 `example/`，可作为最小调用入口：

- [`5_performance/profiling/0_create_config/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/profiling/0_create_config/main.cpp#L36)
- [`5_performance/profiling/1_msproftx/main.cpp`](../../../../cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/example/5_performance/profiling/1_msproftx/main.cpp#L144)
