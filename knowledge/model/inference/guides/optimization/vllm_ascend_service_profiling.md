---
type: Guide
title: vLLM Ascend 服务剖析：profiler_config、采集端点与 PD 实例定位
description: 从固定文档与 Worker 消费路径说明 TorchNPU Profiler 的启用、端点控制、数据解析与 PD 独立采集，区分算子层和服务框架层证据。
tags:
- task.debugging
- task.optimization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/performance_and_debug/service_profiling_guide.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/installation/supported_hardware.inc.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/profiler/torch_npu_profiler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/profiler/__init__.py
  role: implementation
created_at: '2026-10-29T08:40:49Z'
updated_at: '2026-10-29T18:12:42Z'
platforms:
- a2
- a3
- 310p
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 服务剖析：profiler_config、采集端点与 PD 实例定位

## 适用范围与工具选择

本文基于 Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 的服务剖析文档与 Worker 调用点。目标是为已准备好的 Ascend 推理服务采集可定位的性能证据，不表示所有模型与硬件均已采集验证。

算子/Kernel 问题先看 Ascend PyTorch Profiler；服务框架函数、调度和请求链路可用 MS Service Profiler。前者通过服务 API 控制，后者还有独立安装、配置和符号采集机制。本卡闭合前者流程，不将后者的配置文件当作可互换参数。

## 配置与采集

当前文档使用在线 `--profiler-config` 或离线 `profiler_config`；不沿用旧的 `VLLM_TORCH_PROFILER_DIR` 配方。在线配置对象包含：

```json
{
  "profiler": "torch",
  "torch_profiler_dir": "./vllm_profile",
  "torch_profiler_with_stack": false
}
```

按目标环境启动服务，检查实际 profiler 配置与输出目录。关闭 Python stack 可控制数据量，但会失去相应堆栈线索，取舍应记录。预热并准备真实业务输入后，对该实例端口依次调用 `POST /start_profile`、发送目标请求、`POST /stop_profile`，再收集该时间窗产物。

固定文档说明端点仅在启动时启用非空 profiler 后注册。404 时先核对启动配置和访问的实例/端口，不直接归因于 NPU 工具故障。Worker 的 `profile()` 也拒绝未配置 profiler；wrapper 在首次 start 时惰性创建，因此“初始化期间还没有 profiler 对象”本身不代表未启用。

## 解析与观测

定位对应实例、rank 和时间窗的 `*ascend_pt` 目录，按文档使用 `torch_npu.profiler.profiler.analyse()` 解析。常见输出包括 `kernel_details.csv`、`operator_details.csv`、`op_statistic.csv`、`step_trace_time.csv` 和 `trace_view.json`。先确认采样覆盖了目标 workload，再沿时间线区分 host 下发、计算、通信和空闲。

例如，图优化步骤被调用不代表算子真正融合；需要查看真实 Kernel/任务条目及其时延。一次局部算子变快不能单独证明服务吞吐或 TPOT 改善，最终应按[基准测量流程](vllm_ascend_benchmark_workflow.md)复测。

## PD 与代理的边界

普通 PD 文档示例中的 P、D 是独立 vLLM 服务，各自配置 profiler、使用独立输出目录，并直接访问各自端口启停采集。示例 `load_balance_proxy_server_example.py` 不转发这两个端点，只访问代理可能漏采。

同一来源另说明 EPD 的 layerwise proxy 支持广播 profiling 控制。因此先确认实际代理实现，不能把“PD 代理不转发”推广为所有代理都不支持。保留 P/D/E 的角色、rank、请求窗口和产物对应关系，缺一侧 trace 时不宣称已定位完整传输链路。

## 验证、停止与回退

验收采集端点、目标请求、输出目录和解析产物，确认 trace 包含待诊断区间。没有目标步骤、端点访问错实例、目录混写或解析失败时先修正采集，再作根因判断。停止采集并恢复基线配置；profiler 采集开销应单独记录，收益用未开启采集的对照运行验证。

## Evidence

服务剖析文档给出工具分工、配置、端点、解析文件和两类代理边界；Worker 的 `profile()` 给出配置检查与惰性创建。本文未实际启动服务、调用采集 API 或生成 trace，不把命令配方视为已采集结果。


## 精度采集与系统调优的衔接

输出漂移或 NaN/Inf 需要中间张量证据时，使用[msprobe 采集排障](../../runbooks/precision/vllm_ascend_msprobe_dump_contract.md)核对配置、图/eager 依赖、调度步和基准对齐；TorchNPU 性能 trace 不替代数值比较。allocator、host/通信参数实验按[系统调优合同](vllm_ascend_system_tuning_contract.md)保留有效值与对照，再用本卡归因耗时；采集开启时的时延不能作为关闭采集后的正式收益。


## AISBench 定时采集与产物追溯

自动采集按[定时剖析及产物完整性](vllm_ascend_aisbench_profile_artifacts.md)核对正式请求起点、成功请求阈值、服务实例表、各节点/rank、raw/parsed和上传/合并状态。小索引能下载、tar存在或控制端点返回成功都不单独证明采到了目标窗口；工具侧验证、报告JSON与性能基线应按各自判据解释。


## 固定wrapper的有效字段与成功信号

TorchNPUProfilerWrapper固定CPU/NPU活动和实验采集项，仅接受torch与非空输出路径，并检查msmonitor_use_daemon互斥；堆栈字段映射为with_modules，不能按torch_npu同名with_stack直接解释。它继承的生命周期还包含延迟、最大Worker步数和warning后状态变化；完整探针见[控制成功却无目标trace](../../runbooks/validations/vllm_ascend_profiler_false_success.md)。特别核对首次trace名复用、step在forward前及未接入的原生schedule字段，不能只按控制返回判断成功。

服务框架JSON开关、版本符号文件生成与旧模板保留见[MS Service Profiler](vllm_ascend_ms_service_profiler_contract.md)；旧ProfileExecuteDuration配方按[孤立PO排查](../../runbooks/runtime/vllm_ascend_legacy_profile_execute_duration.md)定位实际版本，不从历史翻译推断当前可用API。这里补充的是源码条件，不新增四类硬件的运行验证。
