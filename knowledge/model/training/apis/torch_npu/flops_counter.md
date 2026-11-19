---
type: API
title: FlopsCounter：重计算计数、状态切换与返回顺序
description: 保存单例计数状态图和pause语义，区分FLOPs计数、MFU/HFU与运行测量。
tags:
- task.lookup
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-utils/（beta）torch_npu-utils-FlopsCounter.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-utils/（beta）torch_npu-utils-FlopsCounter.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-utils/(beta)torch_npu-utils-FlopsCounter.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/flops_count.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/flops_count.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/flopcount/FlopCountContext.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/flopcount/FlopCountContext.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/flopcount/FlopCount.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/figures/参数状态.png
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/figures/参数状态.png
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/figures/parameter_states.png
  role: constraint
created_at: '2026-11-09T19:09:59Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- '950'
---

# FlopsCounter：重计算计数、状态切换与返回顺序

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5的中文页及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda的中英文页。A2/A3在本卡指训练系列，主线新增950DT确认不回推到发布版，不扩到950PR。旧Atlas产品只保留来源条目，不自动映射其他新型号。

发布配对PyTorch提交为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；补充独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf时单独指出，两个main不构成自动配套。以下为静态合同，没有编译、导入、加载模型、设备运行或性能测量。


## 范围和构造

`torch_npu.utils.FlopsCounter()`是单例上下文的包装。该接口发布只列A2训练，主线新增950DT，**未列A3**；本卡因此仅a2/950。文档统计MM、BMM、AllgatherMM、ReduceScatterMM、FA等常见Cube算子，不等于模型所有算子都被覆盖，也不是设备实测指令计数。

## 状态与计数

|操作|enabled / paused及结果|
|--|--|
|首次创建|False / False，recordedCount和traversedCount均0。|
|start()|仅将enabled设True，不清旧计数，也不把既有paused清False。|
|pause()|paused=True，启用时只累计含重计算的traversedCount。|
|resume()|paused=False；只有enabled=True才会恢复两类计数，未启用时调用不等于start。|
|stop()|禁用并reset：两个标志False，两计数清0。先取结果再stop，避免把清零误当未统计。|
|get_flops()|返回`[recordedCount, traversedCount]`，依次是不含/含重计算；不是反序。|

两版中文同字节图和英文图逐一查看，图的四态与发布C++Context/宏一致：enabled为True才加traversed，且!paused才加recorded。pause表达用户指定的重计算区间，不自动识别所有重计算。

## 包装与使用限制

公开utils入口导出`_FlopsCounter as FlopsCounter`；直接从flops_count子模块取同名类另有弃用提示。包装的__enter__调用未在类中定义的count_enable，__exit__也调用count_disable且没有标准异常参数签名，不能据有魔法方法就提供`with FlopsCounter()`配方；使用文档start/pause/resume/get/stop。

所查发布C++单例计数为普通整数及布尔状态，不能据单例推定多线程独立或无竞争。算子计数只是MFU/HFU的分子线索；还需对应时间、设备数量与相同口径的峰值，计数本身不是利用率或优化收益。本文没有运行统计或测时。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-utils/（beta）torch_npu-utils-FlopsCounter.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-utils/（beta）torch_npu-utils-FlopsCounter.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-utils/(beta)torch_npu-utils-FlopsCounter.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/flops_count.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/flops_count.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/__init__.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/__init__.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/flopcount/FlopCountContext.h)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/flopcount/FlopCountContext.cpp)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/flopcount/FlopCount.h)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/figures/参数状态.png)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/figures/参数状态.png)（constraint）
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/figures/parameter_states.png)（constraint）
