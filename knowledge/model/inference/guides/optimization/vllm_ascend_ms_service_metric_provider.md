---
type: Guide
title: vLLM Ascend MS Service Metric：provider、YAML与Prometheus进程域
description: 按 get_metric_provider、MetricProvider 与 MS_SERVICE_METRIC_CONFIG_PATH
  接入运行指标，核对provider声明、YAML符号、Core版本、Prometheus进程目录和配置重载，限定V1/EPLB插桩范围。
tags:
- task.implementation
- task.optimization
- topic.performance.analysis
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/ms_metrics/provider.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/ms_metrics/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/ms_metrics/config/base_metrics.yaml
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/ms_metrics/config/eplb_metrics.yaml
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/ms_metrics/handlers/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/ms_metrics/handlers/common.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/ms_metrics/handlers/eplb.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/setup.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/ms_service_metric.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/ms_service_metric.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/observability/test_ms_metrics_provider.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/eplb/core/eplb_worker.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/core/scheduler_profiling_chunk.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/core/recompute_scheduler.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_balance_schedule.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/model_runner.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/worker.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/eplb/core/eplb_device_transfer_loader.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/eplb/adaptor/vllm_adaptor.py
  role: constraint
created_at: '2026-10-29T21:04:05Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T21:04:05Z'
---

# vLLM Ascend MS Service Metric：provider、YAML与Prometheus进程域


## 任务与固定范围

为新模型框架增加Prometheus运行指标，或排查已装工具但没有目标阶段的数据。固定Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`；原生vLLM基线仍为v0.32.0，不由这张卡保证任意版本插件/外部Core兼容。工具整项硬件范围未取得证据，保持draft/空平台。本次未导入上游包、启动服务/HTTP/采集或执行NPU。

MS Service Metric由函数hooks收集指标并对接Prometheus；[MS Service Profiler](vllm_ascend_ms_service_profiler_contract.md)提供另一套JSON/YAML时间线采集。两者的配置入口、输出和重载操作分别核对，指标端点可访问不证明时间线、全部worker或所有模型路径均有数据。

## provider声明与实际插桩分开验收

setup.py在ms_service_metric.providers登记vllm-ascend = vllm_ascend.observability.ms_metrics:get_metric_provider，并把config/*.yaml作为package_data。get_metric_provider仅在被调用时导入外部ms_service_metric.provider_api.MetricProvider；包入口导出这个函数，不在入口导入时主动构造Core实例。

固定工厂返回name=vllm-ascend、priority=200、framework_package=vllm_ascend、owned_symbol_prefixes=(vllm_ascend.,)、handler_module_prefixes=(vllm_ascend.observability.ms_metrics.,)。这些是声明参数；实际provider选择、ownership/overlay默认值、排序冲突、重复hook组合及失败隔离属于外部Core。测试里的FakeMetricProvider默认overlay不等于真实安装版本默认值已被验证。

内置config_paths从本包config目录第一层glob("*.yaml")排序取得；固定提交有base_metrics.yaml与eplb_metrics.yaml两份、共12条symbol配置。这里不递归，也没有同时glob *.yml或大写扩展名。文档的用户自定义目录支持.yaml/.yml是外部加载流程，不能把两个入口的文件选择规则合成同一实现。

安装包缺YAML、entrypoint只存在于源码、工厂调用失败或Core不识别这些参数，都可能使贡献配置未生效。记录实际发行包、Core/Ascend/vLLM版本、provider返回和已加载配置，不能只用配置文件存在或静态import检查证明运行时插桩。

## 服务、配置与进程目录

文档要求单独安装ms_service_metric；Ascend推理本身不依赖这套外部指标Core。在服务启动前设置PROMETHEUS_MULTIPROC_DIR，每实例使用独立目录，启用ms-service-metric on后启动vLLM、施加请求，再观察/metrics。ms-service-metric off用于关闭采集；本次没有执行这些命令。

多进程目录可能保留上次运行文件。按文档，验证重启前只在确认没有运行服务使用该目录后处理旧文件；目录名、旧样本或/metrics返回200都不是本次实例的数据证明。核对各worker看到的目录、负载窗口、标签与采样时间。

MS_SERVICE_METRIC_CONFIG_PATH可以指向一个YAML文件或目录。文档规定目录模式按文件名读第一层.yaml/.yml，不递归；该目录也是自定义module:function Handler的模块根。用户维护自己的YAML与Handler，这部分resolver和完整配置schema不在本仓provider函数中实现。

文档要求修改YAML后ms-service-metric restart，修改Handler Python代码后重启vLLM服务，因为已导入模块不会动态重载。不能由这个操作说明推导当前Core具体如何通知每个子进程、如何合并用户覆盖或如何回收旧handler；需在目标版本按实际provider/hook日志验证。

## 12个配置点的消费边界

| 内置配置 | 声明的采样面 | 使用时核对 |
| --- | --- | --- |
| base_metrics.yaml | ProfilingChunk/Recompute/Balance Scheduler.schedule | 通用Core scheduler handler处理字段，定义存在不证明当前实际选择该scheduler |
| base_metrics.yaml | V1 NPUModelRunner.execute_model的DP初始化和phase handler，以及_prepare_inputs | 同一execute_model有两条配置；组合/次序由Core决定，默认V2不会由V1名字自动获得等价指标 |
| base_metrics.yaml | NPUWorker.compile_or_warm_up_model与8个engine:memory gauge | 内存统计口径/设备同步在外部handler，不能把名称当作已核验的显存分项恒等式 |
| eplb_metrics.yaml | EplbWorker.do_update、D2DExpertWeightLoader与adaptor map/weight方法 | 部分method只是提交或薄包装；phase_all_handler如何计时在外部Core，不能直接解释为真实NPU迁移完成时间 |

例如executor:model_runner_execute_model:duration声明在YAML，但该条未显式写type；不能仅凭duration后缀推断当前Core的默认histogram/schema。自定义EPLB hotness handler自己注册gauge，其他通用handler由ms_service_metric.provider_handlers提供，外部内部实现与版本仍待核验。

本次用自有静态AST扫描确认12条symbol都能在固定源码找到类/方法，未执行上游测试或模块。AST定义存在不证明动态替换、Runner选择、进程初始化、import/resolver和hook顺序实际匹配。

## 新增Ascend指标的接线

按文档选择真实module:Class.method与稳定通用handler；Ascend专用处理置于handlers/<feature>.py并在handlers/__init__.py重新导出，YAML使用vllm_ascend.observability.ms_metrics.handlers:function_name。通用MetricSpec、register_metrics与safe_recording从handlers/common.py复用，避免每个特性重复引入Core注册逻辑。

common.py集中导入MetricType/get_metric_recorder供特性handler使用，provider工厂另有自己的惰性MetricProvider导入。公共helper的录制异常保护不覆盖所有导入/原函数异常，注册与旧值边界见[缺指标或旧值排障](../../runbooks/runtime/vllm_ascend_ms_metric_missing_or_stale.md)。新增点要同时检查metadata、label names、进程身份、原函数返回与失败语义，不能只在YAML写一个名字。

## 中文资料、验收与剩余工作

ms_service_metric.po的17条有效非空译文已全文对照67行英文，0obsolete/fuzzy且msgid均匹配。它保留独立进程目录、文件/目录差别、Python handler重启和录制helper说明；PO复核不证明线上HTML已更新或外部Core已按文档运行。

验收保留真实provider/配置清单、函数签名、Runner/scheduler/进程、窗口/负载、recorder和Prometheus结果，分别验证缺symbol/handler错误只影响预期采样面，以及关闭采集后的基准。文档要求缺symbol不影响推理，这项运行保证需要Core消费者证据；本次不把静态声明、mock或端点200替代该证明。精度、吞吐、工具开销及全部硬件/模型/SDK版本仍未实测。
