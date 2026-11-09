---
type: Runbook
title: vLLM Ascend 旧执行计时配方排查：ProfileExecuteDuration 与孤立中文PO
description: 遇到 VLLM_ASCEND_MODEL_EXECUTE_TIME_OBSERVE、capture_async 或 pop_captured_sync
  旧配方时，区分孤立PO、版本化符号模板与当前实现，选择Profiler或框架链路采集并保留异步计时边界。
tags:
- task.debugging
- task.optimization
- topic.performance.analysis
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/performance_and_debug/profile_execute_duration.po
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/profiling_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/generate_zh_docs.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/envs.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/profiler/torch_npu_profiler.py
  role: supporting
created_at: '2026-10-29T18:12:42Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T18:12:42Z'
---

# vLLM Ascend 旧执行计时配方排查：ProfileExecuteDuration 与孤立中文PO


## 信号与证据范围

旧文档要求设置VLLM_ASCEND_MODEL_EXECUTE_TIME_OBSERVE，调用ProfileExecuteDuration().capture_async和pop_captured_sync，但当前环境没有预期输出、符号导入失败，或Agent准备照旧配方新增全局同步。固定Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 中仍存在对应中文PO，当前英文docs/source/developer_guide/performance_and_debug/profile_execute_duration.md不存在。

该PO描述用NPU event异步观察设备时间，相比每阶段torch.npu.synchronize()+CPU时钟减少同步开销；capture_async为非阻塞采样点，pop_captured_sync为阻塞取回。它没有提供本次环境的实现、硬件范围或实测收益，不能据此直接调用旧API。此卡是当前诊断任务，保持draft/空平台，不把历史PO登记成当前有效API。

## 三项静态探针

1. 固定提交中核对英文正文路径。中文生成器按PO推导同路径.md，仅在英文文件存在时生成；缺源只打印Source not found，不凭PO独立生成功能页。因此仓内PO存在不证明当前中文站有该页，更不能证明旧链接当前可访问。
2. 在完整vllm_ascend源码中查ProfileExecuteDuration、VLLM_ASCEND_MODEL_EXECUTE_TIME_OBSERVE和pop_captured_sync。当前命中只见profiling_config.py中旧capture_async符号字符串；utils.py未找到对应定义，envs.py注册表没有该环境变量。静态未找到不证明运行环境绝无外部注入或历史包，应另按实际安装包/版本验证，不能制造一个已确定删除版本。
3. 检查符号模板的版本条件。旧ProfileExecuteDuration.capture_async项为min_version=0.9.1、max_version=0.14.0rc1；另一record_function_or_nullcontext项为min_version=0.15.0rc1。这只是外部服务采样器的符号筛选数据，不是旧功能引入/删除版本的证明；文件头的POT时间也不是运行版本。

## 选择当前证据路径

若要看算子与设备时间线，使用[服务剖析](../../guides/optimization/vllm_ascend_service_profiling.md)核对ProfilerConfig、目标rank与窗口，再按[控制成功却缺trace](../validations/vllm_ascend_profiler_false_success.md)检查生命周期与字段支持。若要关联请求、调度、模型和KV传输，使用[MS Service Profiler](../../guides/optimization/vllm_ascend_ms_service_profiler_contract.md)并核对当前实际函数/Runner能否绑定。

迁移的目标是保留所需观测语义，不能按函数名将旧异步device event计时换成CPU函数耗时。CPU范围可能包含下发/等待，也可能在NPU异步完成前结束；未核对stream、事件、同步点、图replay和重叠关系时，不能把两者当成同一指标或把各阶段简单相加。

不要只为复刻旧输出在热路径逐阶段加全设备同步；旧PO本身正说明这会改变同步开销。需要最小复现时另按目标环境定义观测点、数据取回与开销对照，不能以本卡静态解释声称已经实现无开销计时。

## 验收、停止与历史边界

保留原URL/PO、固定提交、实际安装版本、符号/变量搜索、目标观测语义、实际新产物和关闭采集的性能对照。旧配方缺实现或目标事件时保持未验证，修复文档版本与采集方案后再测。此处不自动删除PO、不修改上游、不补写失去上下文的旧实现，也未运行NPU、服务或中文站构建。
