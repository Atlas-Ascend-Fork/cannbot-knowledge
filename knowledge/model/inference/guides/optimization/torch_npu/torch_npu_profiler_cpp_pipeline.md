---
type: Guide
title: TorchNPU Profiler 的 C++ 采集管线：绑定面、配置位图与数据接收器
description: 固定 _profiler 绑定入口、NPU 观察者回调、ProfilerMgr 的 datatype_config 位图拼装、warmup/子线程/停止语义与三路数据接收器，区分采集侧
  FeatureMgr 与解析侧 FeatureManager。
tags:
- task.debugging
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/profiler/init.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/profiler/npu_profiler.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/profiler/profiler_mgr.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/profiler/feature_mgr.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/profiler/mstx_mgr.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/toolkit/profiler/src/data_dumper.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/toolkit/profiler/src/data_reporter.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/profiler/combined_traceback.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/profiler/combined_traceback.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/profiler/containers.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/profiler/init.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/profiler/profiler_npu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/profiler/python/combined_traceback.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/profiler/unwind/unwind.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/profiler/unwind/unwind.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/profiler/utils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/toolkit/profiler/common/ring_buffer.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/toolkit/profiler/common/singleton.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/toolkit/profiler/common/thread.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/toolkit/profiler/inc/data_dumper.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/toolkit/profiler/inc/data_reporter.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/toolkit/profiler/src/data_dumper.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/toolkit/profiler/src/data_reporter.cpp
  role: implementation
created_at: '2026-11-13T04:24:55Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU Profiler 的 C++ 采集管线：绑定面、配置位图与数据接收器

## 固定版本与范围

静态审阅 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 `csrc/profiler/`（init/npu_profiler/profiler_mgr/feature_mgr/mstx_mgr）与 `csrc/toolkit/profiler/src/`（data_dumper/data_reporter）。发布 pin 未逐行比对。未确认产品范围，保持 `draft`、空平台；未启动采集、解析导出文件或运行性能实验。Python 侧 Profiler 配置与调度见[采集调度](torch_npu_profiler_capture_schedule.md)与[实验配置](../../../apis/torch_npu/profiler_experimental_config.md)；解析侧能力探测与 Feature 版本比较见[CANN 导出、分析与产物等待](torch_npu_profiler_cann_export_analyze_and_timeline_readiness.md)——其中的 FeatureManager 是解析侧字典比较，与本卡采集侧 `FeatureMgr` 不是同一组件。

## 绑定面与生命周期入口

`init.cpp` 把 `_profiler` 子模块挂到 `torch_npu._C`（:33 起）：`_supported_npu_activities` 固定返回 {CPU, NPU}（:101-104）；`_init_profiler/_warmup_profiler/_start_profiler/_stop_profiler/_finalize_profiler` 为主生命周期（其中 start/stop/finalize 释放 GIL）；`_enable_profiler_in_child_thread/_disable_profiler_in_child_thread` 为子线程路线；`_get_freq/_get_syscnt_enable/_get_syscnt/_get_monotonic/_get_host_uid` 暴露时钟与身份工具（:105-127）。`initNpuProfiler`（npu_profiler.cpp:145-170）对路径做软链接拒绝、目录存在/可写校验后才进入 `ProfilerMgr::Init`；软链接路径直接记错误返回，不会自动落到真实路径。

## 观察者回调与 msprof_tx-only 路线

`NpuProfilerThreadLocalState`（npu_profiler.cpp:52-108）把 `record_shapes/profile_memory/with_stack/with_flops/with_modules` 拷入通用 ProfilerConfig，`tracePython()` 要求 with_stack 或 with_modules 且 CPU activity。`startNpuProfiler`（:360-398）在已启用时直接报错返回；CPU trace 才注册全量回调；仅 NPU activity + msprof_tx 时以 `mstx_only` 只注册 USER_SCOPE 回调（源码注释：CPU 关闭时设备标注仍需 RecordFunction 回调，:390-396）。`pushRecordFunctionMstxRange`（:235-245）在 USER_SCOPE 且 npu_trace+msprof_tx 时把 range 推给 `mstxRangePush`（DOMAIN_RECORD_FUNCTION 域）。`enableProfilerInChildThread`（:346-358）固定 CPU-only 活动集，不复用主线程的 NPU trace。`reportMemoryDataToNpuProfiler`（:451-474）在 CANN 提供 `AclrtStreamGetId` 时记录数值 stream id，否则退化为指针数值——内存事件里的 stream 字段跨 CANN 版本口径不同。

## ProfilerMgr 的配置位图与 warmup

`PrepareProfilerConfig`（profiler_mgr.cpp:120-166）把 trace_level 映射为 datatype 位图，metrics 非 `ACL_AICORE_NONE` 时叠加 AICORE_METRICS，l2_cache/msprof_tx/npu_memory/op_attr 各占一位；npu_memory 另设 `ACL_PROF_SYS_HARDWARE_MEM_FREQ=50`（不支持时仅告警）；`Level0 + record_shapes` 只有 `FeatureMgr::IsSupportFeature(FEATURE_AICORE_SHAPE)` 通过才叠加 AICORE_SHAPE 位，否则退回框架侧 record_shapes 并告警（:153-160）。`WarmupMsProfiler`（:79-97）建 config 后调 `AclProfilingWarmup`，`ACL_ERROR_PROF_MODULES_UNSUPPORTED` 只告警；`EnableMsProfiler`（:99-115）复用 warmup 已建的 config 再 `AclProfilingStart`，设备回调注册失败同样仅告警。`Warmup`（:214-246）同时启动 CPU 侧 FRAMEWORK 数据接收器；`Start`（:247-285）在未 warmup 时才建接收器，record_op_args 会调用 `AclopStartDumpArgs` 把算子参数转储到 `<path>_op_args`；`Stop`（:287-313）按相反顺序停接收器、`AclProfilingStop/DestroyConfig`、清 mstx 域过滤，record_op_args 打开过则 `AclopStopDumpArgs`。`Finalize` 只调 `AclProfilingFinalize`。

## 数据接收器与 toolkit 层

`StartDataReceiver/StopDataReceiver`（profiler_mgr.cpp:320-336）同时启动三路接收器：`dataReceiver_`、`traceDataReceiver_`、`dataReceiverWithLock_`（容量分别为 capacity_/trace_capacity_）。上传侧 `Upload` 在 warmup 阶段直接丢弃（:338-343 起），标记类数据经 `UploadWithLock` 走带锁接收器。toolkit 的 `data_dumper.cpp` 负责把 FRAMEWORK 目录数据落盘、`data_reporter.cpp` 是异步上报队列（带独立线程与退出收尾）；两者与 `common/ring_buffer.h`、`thread.h` 共同构成落盘链。msprof 侧导出是否成功仍要看 CANN 产物，接收器启动不保证数据完整。

## 采集侧 FeatureMgr

`feature_mgr.cpp`（:12-52）以 NAME_TABLE 登记特性名，`Init` 时经 msprofiler 查询能力，`FormatFeatureList` 把能力列表回填给查询方；当前消费点是 AICORE_SHAPE 位判断。它是采集期能力协商，输出进入 datatype 位图；解析侧 `_feature_manager.py` 的字典比较（版本/compatibility 字符串）不消费这份协商结果，两边不能互推。

## 优化判断

排查"配置了但没采到"时按链路定位：Python 配置 → `NpuTraceConfig` 位图（本卡 PrepareProfilerConfig）→ msprof 配置创建/warmup 告警 → 接收器与 FRAMEWORK 目录 → CANN 导出。`_supported_npu_activities` 只有 CPU/NPU 两类，其他活动枚举在此层不存在。本卡未审阅 python_tracer、unwind 栈回溯、mstx 域管理与 data_dumper/data_reporter 全文逐行，不包含任何采集开销或产物完整性的运行结论。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/profiler/init.cpp)（primary）：33、101-140（绑定面全量）。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/profiler/npu_profiler.cpp)（primary）：26-108（状态与上下文）、145-170（init 路径校验）、171-245（输入形状解析与 mstx range）、326-474（warmup/子线程/start/stop/finalize/内存上报）。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/profiler/profiler_mgr.cpp)（primary）：70-166（Warmup/Enable/PrepareProfilerConfig）、214-343（Warmup/Start/Stop/Finalize/接收器/Upload）。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/profiler/feature_mgr.cpp)（implementation）：12-52。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/profiler/mstx_mgr.cpp)（implementation）：19-60（mark/rangeStart/rangeEnd 头部；域与内存注册部分未逐行）。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/toolkit/profiler/src/data_dumper.cpp)（implementation）：结构级阅读（类职责与落盘入口）。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/toolkit/profiler/src/data_reporter.cpp)（implementation）：结构级阅读（异步队列与线程收尾）。

## 发布 pin 对照（f3ecfe4a）

卡内涉及的 30 个发布孪生文件已做真实机械比对（sha256 → 去空白 → token → 注释剥离 token → 语义 diff 五级），结论分述如下。

### 已绑定（等价/无行为差异）

- `torch_npu/csrc/profiler/combined_traceback.cpp`：全空白折叠后逐字节等价（重排版）。发布来源条目已入 frontmatter（release pin f3ecfe4a）。
- `torch_npu/csrc/profiler/combined_traceback.h`：全空白折叠后逐字节等价（重排版）。发布来源条目已入 frontmatter（release pin f3ecfe4a）。
- `torch_npu/csrc/profiler/containers.h`：注释差异等价（代码 token 流相同）。发布来源条目已入 frontmatter（release pin f3ecfe4a）。
- `torch_npu/csrc/profiler/init.h`：唯一实质差异：发布版删除 `#include <torch/csrc/python_headers.h>`。发布来源条目已入 frontmatter（release pin f3ecfe4a）。
- `torch_npu/csrc/profiler/profiler_npu.cpp`：唯一实质 token 差异：acl_rt.h include 路径改为 third_party 相对路径。发布来源条目已入 frontmatter（release pin f3ecfe4a）。
- `torch_npu/csrc/profiler/python/combined_traceback.cpp`：全空白折叠后逐字节等价（重排版）。发布来源条目已入 frontmatter（release pin f3ecfe4a）。
- `torch_npu/csrc/profiler/unwind/unwind.cpp`：唯一实质差异：发布版在一处宏续行补上反斜杠续行符。发布来源条目已入 frontmatter（release pin f3ecfe4a）。
- `torch_npu/csrc/profiler/unwind/unwind.h`：全空白折叠后逐字节等价（重排版）。发布来源条目已入 frontmatter（release pin f3ecfe4a）。
- `torch_npu/csrc/profiler/utils.cpp`：唯一实质差异：flops 日志文案发布版为 "compuation"（主线为 "computation"），仅提示文本。发布来源条目已入 frontmatter（release pin f3ecfe4a）。
- `torch_npu/csrc/toolkit/profiler/common/ring_buffer.h`：注释差异等价（代码 token 流相同）。发布来源条目已入 frontmatter（release pin f3ecfe4a）。
- `torch_npu/csrc/toolkit/profiler/common/singleton.h`：注释差异等价（代码 token 流相同）。发布来源条目已入 frontmatter（release pin f3ecfe4a）。
- `torch_npu/csrc/toolkit/profiler/common/thread.h`：注释差异等价（代码 token 流相同）。发布来源条目已入 frontmatter（release pin f3ecfe4a）。
- `torch_npu/csrc/toolkit/profiler/inc/data_dumper.h`：注释差异等价（代码 token 流相同）。发布来源条目已入 frontmatter（release pin f3ecfe4a）。
- `torch_npu/csrc/toolkit/profiler/inc/data_reporter.h`：差异为成员名 values→datas（9 处）与 python_tracer_types.h→profiler_python.h include；数据通道结构不变。发布来源条目已入 frontmatter（release pin f3ecfe4a）。
- `torch_npu/csrc/toolkit/profiler/src/data_dumper.cpp`：唯一实质差异：落盘失败日志文案发布版为 "cerate file failed"（主线为 "create file failed"），仅提示文本。发布来源条目已入 frontmatter（release pin f3ecfe4a）。
- `torch_npu/csrc/toolkit/profiler/src/data_reporter.cpp`：注释差异等价（代码 token 流相同）。发布来源条目已入 frontmatter（release pin f3ecfe4a）。

### 版本边界（发布 pin 行为不同，按 pin 分述）

- **`torch_npu/csrc/profiler/feature_mgr.cpp`**：AICORE_SHAPE 特性项发布版不存在。
  - 主线 NAME_TABLE 含 `{"AICORE_SHAPE", FEATURE_AICORE_SHAPE}`（:15）、feature map 含映射（:21），`IsSupportFeature` 有该 case 与降级告警（:111-112）。
  - 发布版全文无 AICORE_SHAPE（token 级确认，0 命中）。
  - 发布版 Init 后对不支持特性以 printf "[WARN]" 输出（主线走 TORCH_NPU_WARN_ONCE/ASCEND_LOGW）。
  - 对本卡结论的影响：本卡「采集侧 FeatureMgr」与 PrepareProfilerConfig 的 AICORE_SHAPE 位门控只在主线成立；发布 pin 无该特性协商路径。
- **`torch_npu/csrc/profiler/feature_mgr.h`**：FEATURE_AICORE_SHAPE 枚举值发布版不存在。
  - 主线枚举表含 `,FEATURE_AICORE_SHAPE`；发布版删除该值（连同 .cpp 的 NAME_TABLE 项）。
  - 另 acl_prof.h include 路径改 third_party 相对路径。
  - 对本卡结论的影响：同上：AICORE_SHAPE 协商链发布 pin 缺位。
- **`torch_npu/csrc/profiler/init.cpp`**：绑定面 GIL 释放与签名发布版不同。
  - 主线 `_start_profiler`/`_stop_profiler`/`_finalize_profiler` 等绑定带 `py::call_guard<py::gil_scoped_release>()`（:111-122），函数体内另有 8 处 `pybind11::gil_scoped_release`；发布版全文件无任何 GIL 释放声明。
  - 发布版 `_warmup_profiler` 多一个 `py::arg("activities")` 参数（:92）。
  - 主线 ExperimentalConfig 绑定为 `py::init<std::string, bool, bool, bool, bool, bool, ExperimentalConfig>`；发布版为含 `std::string`×2 与 `std::vector<std::string>` 的另一签名（:39）。
  - include 集不同：主线 profiler_api.h/mstx_range.h/NPUStream.h，发布版 npu_profiler.h。
  - 对本卡结论的影响：本卡「其中 start/stop/finalize 释放 GIL」与 warmup/ExperimentalConfig 签名描述只对应主线；发布 pin 的生命周期绑定不释放 GIL。
- **`torch_npu/csrc/profiler/mstx_mgr.cpp`**：mstx 域管理发布版为另一实现。
  - 主线含 thread_local `domainPushDepthStacks_`（`std::unordered_map<std::string, std::stack<RangePushContext>>`）与 `DOMAIN_RECORD_FUNCTION="record_function"` 常量、MsptiInterface.h include。
  - 发布版删除深度栈与该常量，命名改为 isProfTxEnable/isMsptiTxEnableImpl 等（38 个变更块，含 rangePush/rangePop 携 stream/domain 的重载删除）。
  - 发布版 `torch_npu::toolkit::profiler` 前缀直接内联使用。
  - 对本卡结论的影响：本卡 mstx 节（mark/rangeStart/rangeEnd 头部 19-60）只描述主线形态；发布 pin 域过滤/深度管理为另一实现，两版互推无效。
- **`torch_npu/csrc/profiler/mstx_mgr.h`**：mstx 管理器头文件发布版重写。
  - 主线声明 `rangePush/rangePop(const char*, const aclrtStream, const char* domain)` 重载与 DOMAIN_RECORD_FUNCTION 常量；发布版删除。
  - 发布版 isTorchNpuProfTxEnable→isProfTxEnable、isMsprofTxEnable→isMsptiTxEnableImpl，include 由 <stack>/<string> 改为 torch_npu Stream.h。
  - 对本卡结论的影响：同上。
- **`torch_npu/csrc/profiler/npu_profiler.cpp`**：状态类型与 include 链发布版不同。
  - 主线使用 ActiveProfilerType（配合 ProfilerStateBase）与成员 `mstx_range_pushed_`，include mstx_range.h/profiler_api.h/profiler_callbacks.h。
  - 发布版类型名互换位置（ProfilerStateBase/ActiveProfilerType 词序不同的别名链）、删除 `mstx_range_pushed_`，include 收敛到 npu_profiler.h。
  - 函数体结构（initNpuProfiler/startNpuProfiler/reportMemoryDataToNpuProfiler 等）在发布版行号整体前移，主要分支形态与主线一致（未逐行核对发布版全文）。
  - 对本卡结论的影响：本卡各 :N 行号锚（26-108/145-170/171-245/326-474）只对主线；发布 pin 同名函数需按发布文件重锚后再引用。
- **`torch_npu/csrc/profiler/npu_profiler.h`**：头文件布局发布版完全重建。
  - 主线 npu_profiler.h 为 8 行 include 聚合头（profiler_api.h/profiler_callbacks.h/mstx_range.h/profiler_mgr.h/data_reporter.h）。
  - 发布版为 202 行类型定义头：NpuActivityType/MemoryComponentType/MemoryDataType/MemoryAllocatorType/MemoryUsage、python_tracer Command 等，include mstx_mgr.h/MsProfilerInterface.h 与 third_party acl 头。
  - 对本卡结论的影响：下游（init.cpp、npu_profiler.cpp 等）的 include/类型消费关系两版不同；本卡绑定面章节的文件组织描述只对应主线。
- **`torch_npu/csrc/profiler/profiler_mgr.cpp`**：PrepareProfilerConfig 的 record_shapes 门控发布版不存在。
  - 主线 `Level0 + record_shapes` 经 `FeatureMgr::IsSupportFeature(FEATURE_AICORE_SHAPE)` 判断后叠加 `ACL_PROF_AICORE_SHAPE` 位（:154-158），并有 `#ifndef ACL_PROF_AICORE_SHAPE` 兜底常量（:12-13）；发布版两者全无（record_shapes 不参与 datatype 位图）。
  - 主线告警走 ASCEND_LOGW/TORCH_NPU_WARN_ONCE；发布版改 printf "[WARN]%s,%s:%u..."（如 AiCMetrics 提示）。
  - 发布版 `msprof_tx_.store(...)` 移位；`record_shapes` 消费链发布版不存在。
  - 对本卡结论的影响：本卡「ProfilerMgr 的配置位图与 warmup」一节的 AICORE_SHAPE 位门控与告警方式只对应主线；发布 pin record_shapes 仅由框架侧 RecordFunction 承载。
- **`torch_npu/csrc/profiler/profiler_mgr.h`**：ProfilerMgr 头文件发布版接口面不同。
  - 主线配置结构含 `bool record_shapes` 成员；发布版删除（与其位图门控缺失一致）。
  - 主线 `GetMstxDomainIncludeAndExclude` 在发布版改为 `IsMstxDomainEnabled(domainName)`；acl_prof.h include 路径改 third_party 相对路径。
  - 对本卡结论的影响：同上；跨版本引用 ProfilerConfig 字段需按 pin 核对。
- **`torch_npu/csrc/profiler/profiler_python.cpp`**：Python tracer 发布版为另一实现。
  - 182 个 token 变更块：主线 atomic/mutex/unordered_set 组合在发布版改为 deque 等结构；TraceTag/TraceEvent 类型由 python_tracer_types.h 移入 profiler_python.h（发布版）。
  - include 链不同（python_frame_utils.h→utils.h 等）；事件结构与调度形态两版互推无效。
  - 对本卡结论的影响：本卡未审阅 python_tracer 的声明在两版下都成立，但两版 tracer 实现不同，后续审计不得跨 pin 复用行号或结构名。
- **`torch_npu/csrc/profiler/profiler_python.h`**：TraceTag/TraceEvent 定义位置发布版不同。
  - 主线 include python_tracer_types.h；发布版删除该 include 并在头内定义 `enum class TraceTag{kPy_Call,...}` 与 `struct TraceEvent`。
  - 对本卡结论的影响：同上。
- **`torch_npu/csrc/profiler/utils.h`**：发布版新增 NPURecordFunction 类。
  - 发布版新增 `class TORCH_NPU_API NPURecordFunction`（构造按 use_npu_simple 开启 at::enableRecordFunction 等）；主线无该类。
  - include 面：主线 record_function.h/NPUException.h，发布版 object_ptr.h/python_compat.h/NPUException.h。
  - 对本卡结论的影响：发布 pin 的 RecordFunction 包装面比主线多一层；本卡优化判断节提到的标记观测不受影响。
- **`torch_npu/csrc/toolkit/profiler/common/utils.cpp`**：发布版删除 SplitString 工具。
  - 发布版删除 `Utils::SplitString` 定义（连同 .h 声明与 <vector>/time.h include）；其余为注释差异。
  - 对本卡结论的影响：本卡数据接收器/落盘链结论不直接依赖 SplitString；发布 pin 无此工具。
- **`torch_npu/csrc/toolkit/profiler/common/utils.h`**：发布版删除 SplitString 声明。
  - 删除 `static std::vector<std::string> SplitString(...)` 声明与 <vector> include；其余为注释差异。
  - 对本卡结论的影响：同上。

（本节静态比对，未运行/未编译；结论按文件分列，未列出的文件未比对。）
