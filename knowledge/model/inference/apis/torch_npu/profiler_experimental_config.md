---
type: API
title: _ExperimentalConfig：默认值、扩展开关与规范化顺序
description: 列出性能采集扩展选项、发布主线差异和配置回退，强调最终值验收。
tags:
- task.lookup
- task.debugging
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-_ExperimentalConfig.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-_ExperimentalConfig.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-_ExperimentalConfig.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/experimental_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/experimental_config.py
  role: implementation
created_at: '2026-11-09T20:03:47Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# _ExperimentalConfig：默认值、扩展开关与规范化顺序

## 固定版本和支持范围

文档分别来自OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文；实现分别核对TorchNPU发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b与独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf。发布组合ascend_26_0_pt28有独立配套证据，两个仓库主线提交不自动配套，不能用新参数回推发布版。

本卡平台限定A2/A3。部分OpPlugin主线接口页列950DT，但同一固定PyTorch主线原生Profiler支持页对相关入口另有明确不支持说明，且不同方法产品表并不相同；版本与命名空间冲突见[采集指南](../../guides/optimization/torch_npu/torch_npu_profiler_capture_schedule.md)，不以类级表扩展全部方法。旧Atlas条目不自动映射新型号。这里只做静态来源审阅，未导入上游、运行设备采集、解析或性能实验。


## 常用选项

构造仅配置后续采集，不代表调用时已经采样。文档默认profiler_level=Level0、aic_metrics=AiCoreNone，而两固定Python构造默认指标均为PipeUtilization，随后Level0/none检查将其关掉；显式传Level1且省略指标时两者效果不同。

| 选项 | 文档默认与职责 |
| --- | --- |
| export_type | Text；支持字符串/列表，Text与Db另有CANN条件 |
| mstx / 兼容msprof_tx | False；收集MSTX，旧msprof_tx有弃用提示 |
| mstx_domain_include/exclude | 空列表；需开MSTX，二者同时非空只保留include |
| l2_cache | False；独立L2采集 |
| op_attr | False；aclnn属性，文档Level_none不生效 |
| data_simplification | True；解析后删除规定中间数据，保留日志等；示例False不是默认 |
| record_op_args | False；独立*_ascend_pt_op_args目录 |
| gc_detect_threshold | None关闭；非负毫秒阈值，0全部GC |
| host_sys | 空列表；CPU/MEM/DISK/OSRT为进程级、NETWORK系统级 |
| sys_io / sys_interconnection | False；分别NIC/RoCE/MAC与HCCS/PCIe等 |

主线HostSystem增加NUMA，发布类无此成员；不能按主线指南回推26.0。GC还要求CPU活动，系统工具/权限与架构约束见[Host指南](../../guides/optimization/torch_npu/torch_npu_profiler_gc_and_host_system.md)。

## 实际规范化和版本差异

两实现Level_none且两个MSTX开关均False时自动开mstx；非法bool选项多回False，data_simplification非法非None回True，GC非数值/负数回None。host_sys不是list或任一成员非法会清空整组；domain列表成员须str并去重，MSTX未开则清空过滤。

非法export_type回Text；发布op_attr只有显式Db才保留，主线还允许CANN支持Text默认导DB时保留。合法成员并不自动证明底层工具支持。

检查先执行Level/指标依赖，再规范化非法Level/指标，并未循环重复依赖检查；不能将“通常会重置”描述成任意非法组合都得到同一规范结果。构造签名int提示与实际Level/指标字符串常量也不能混为数字枚举。使用合法显式成员，查看profiler_info里的最终配置并核对产物。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-_ExperimentalConfig.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-_ExperimentalConfig.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-_ExperimentalConfig.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/experimental_config.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/experimental_config.py)（implementation）
