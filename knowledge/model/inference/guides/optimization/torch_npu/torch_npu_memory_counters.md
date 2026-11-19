---
type: Guide
title: TorchNPU 显存观测：allocated、reserved 与 npu-smi 的统计范围
description: 区分张量使用、缓存分配器和设备总占用，解释 empty_cache 后 npu-smi 仍有占用，避免把统计差异直接判为泄漏。
tags:
- task.debugging
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/memory_management/memory_faq.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/memory_management/memory_faq.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/memory_management/memory_resource_overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/memory_management/memory_resource_overview.md
  role: constraint
created_at: '2026-11-08T11:58:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- agnostic
---

# 显存统计的层次

## 指标含义

memory_allocated 反映当前 Tensor 实际占用；memory_reserved 反映缓存分配器管理的总量，包括已分配和可复用缓存；npu-smi 的设备统计还包含驱动、HCCL 等框架外开销。它们的统计边界不同，不能要求三个读数相等。

## 观测顺序

在同一设备、进程和负载阶段记录各指标，结合对象生命周期判断变化。empty_cache 可以释放分配器管理的未用缓存，不能释放仍被活跃 Tensor 引用的内存，也不能清除驱动和 HCCL 的全部占用。因此 reserved 降低但 npu-smi 仍较高，单凭这一点不能认定泄漏。

## 验证和失效边界

比较固定输入重复运行、对象释放前后与进程退出后的观测，必要时进一步检查通信组件和分配快照。不要用不同时间点的总量强推逐字节等式，也不能把正常统计差异当作忽略持续增长的理由。

本卡的统计层次定义与具体硬件型号无关；实际容量、计时和驱动开销需在目标设备记录。来源为固定主线 FAQ，本次未采集设备内存。

## 版本入口

- [软件栈来源与适用性](../../../concepts/frameworks/ascend_software_stack_baselines.md)：来源快照、部署配套和实际运行验证分别核对。

## FAQ的不等式是层次示意

中英文FAQ都用npu-smi > reserved > allocated概括统计范围；不把该写法当作所有状态必须严格大于的验收公式，尤其不能跨设备/进程和不同采样时刻硬比较。概述的峰值重置与累计计数重置也不是同一窗口：reset_peak_memory_stats与reset_accumulated_memory_stats分别核对，不把清计数当清内存。

FAQ所称“无需额外处理”针对统计范围正常不同这一现象，不排除业务持续增长、未释放对象或组件独占内存需要进一步归因。保留字节/设备/进程与采样窗口，再解释层次差异；本文没有执行npu-smi或内存查询。

## Evidence

- [docs/zh/developer_notes/memory_management/memory_faq.md](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/memory_management/memory_faq.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/memory_management/memory_faq.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/memory_management/memory_resource_overview.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/memory_management/memory_resource_overview.md)（constraint）
