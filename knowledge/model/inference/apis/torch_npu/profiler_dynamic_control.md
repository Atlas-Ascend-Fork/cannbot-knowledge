---
type: API
title: dynamic_profile接口：目录、文件、划步与恢复计数
description: 区分init与start参数和主线set_state，记录配置模式、排队与版本边界。
tags:
- task.lookup
- task.debugging
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-init.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-init.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-init.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-set_state.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-set_state.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-start.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-start.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-start.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-step.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-step.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-step.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/dynamic_profile.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/dynamic_profile.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_dynamic_profiler/_dynamic_profiler_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_dynamic_profiler/_dynamic_profiler_config_context.py
  role: implementation
created_at: '2026-11-09T20:03:47Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# dynamic_profile接口：目录、文件、划步与恢复计数

## 固定版本和支持范围

文档分别来自OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文；实现分别核对TorchNPU发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b与独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf。发布组合ascend_26_0_pt28有独立配套证据，两个仓库主线提交不自动配套，不能用新参数回推发布版。

本卡平台限定A2/A3。部分OpPlugin主线接口页列950DT，但同一固定PyTorch主线原生Profiler支持页对相关入口另有明确不支持说明，且不同方法产品表并不相同；版本与命名空间冲突见[采集指南](../../guides/optimization/torch_npu/torch_npu_profiler_capture_schedule.md)，不以类级表扩展全部方法。旧Atlas条目不自动映射新型号。这里只做静态来源审阅，未导入上游、运行设备采集、解析或性能实验。


## 公共入口

init(path)接收目录并准备/监视profiler_config.json；start(config_path=None)显式触发一次，给具体JSON文件，不是只给目录。文档start示例的start_config_path为占位，不能覆盖参数说明。step()在业务后划步，无参数；显式窗口业务放start与step之间。

当前profile活动时start告警返回；未提供有效路径时退回监控配置路径，文件无内容/读取失败不会证明已采到所需窗口。init重复调用会告警并不重复初始化；init之前step/start没有同等自动初始化保证，装饰器捕获错误不代表流程成功。

## 主线恢复与模式差异

主线set_state(state_step)要求dict，取cur_step默认0，必须非负int；发布dynamic_profile没有此接口。它设置已完成训练步数以避免重启后从相对0重新计数，不读训练checkpoint或自动恢复模型。该新增页未列950，不能从init/start产品表扩展。

发布step仅维护一个待执行配置，后到的覆盖先前；主线配置文件模式仍取最新，但Dynolog模式进入上限5的队列，不能泛称所有方式“只保留最后一次”。非空REQUEST_TRACE_ID去重，最多记10000个、淘汰最旧；到达已过期会丢弃，在截止前已入队但被前项延误可延迟执行并告警。发布无这些队列/恢复代码。

主线step先增加cur_step、再拉配置和推进/启动窗口；总窗口active+warmup，用repeat1的内部schedule。设置步数不自动重置所有内部状态，不应在活动采集中任意改计数。

## 产品和验证

init/start/step主线页增加950DT，set_state未列；本卡共同平台保持A2/A3。配置文件模式/Dynolog的实际环境及rank、轮询和解析差异见[动态采集指南](../../guides/optimization/torch_npu/torch_npu_dynamic_profiler.md)。保存配置时间、模板存在或step函数返回None都不是采集开始/结束的证据，须核对执行日志与实际窗口。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-init.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-init.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-init.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-set_state.md)（primary）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-set_state.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-start.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-start.md)（primary）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-start.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-step.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-step.md)（primary）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-step.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/dynamic_profile.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/dynamic_profile.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_dynamic_profiler/_dynamic_profiler_utils.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_dynamic_profiler/_dynamic_profiler_config_context.py)（implementation）
