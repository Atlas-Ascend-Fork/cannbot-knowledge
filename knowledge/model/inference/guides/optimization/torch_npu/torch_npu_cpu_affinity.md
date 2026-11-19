---
type: Guide
title: TorchNPU CPU 绑核：NUMA、容器与每流队列限制
description: 说明粗细粒度绑核、force 的作用范围、NPU 亲和模式和线程竞争验证。
tags:
- task.optimization
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/automatic_core_binding.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/performance_tuning/CPU_AFFINITY_CONF.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/taskqueue/stream_taskqueue_parallel_delivery.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/performance_tuning/CPU_AFFINITY_CONF.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/automatic_core_binding.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/thread_core_binding_principle.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/thread_core_binding_principle.png
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-utils/torch_npu-utils.reset_thread_affinity.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-utils/torch_npu-utils.reset_thread_affinity.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-utils/torch_npu-utils.reset_thread_affinity.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-utils/torch_npu-utils.set_thread_affinity.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-utils/torch_npu-utils.set_thread_affinity.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-utils/torch_npu-utils.set_thread_affinity.md
  role: constraint
created_at: '2026-11-09T02:11:09Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# TorchNPU CPU 绑核：NUMA、容器与每流队列限制

## 版本与范围

固定 TorchNPU 主线文档，聚焦 A2/A3；不是所有发布版本的默认配置。仅静态审阅，未测量收益。

## 配置与边界

CPU_AFFINITY_CONF 未设或 mode=0 不绑核；1 为粗粒度，将同卡业务线程限制在其核区间；2 在此基础上把主线程、二级流水等热点线程固定到不同核，非热点线程使用剩余核。可用 npu0:0-3 等闭区间定制，同卡可写多个区间，未指定的卡使用默认均分范围。

先用 lscpu 和 npu-smi info -t topo 核对实际 NUMA/NPU 映射；容器或虚拟机的编号可能改变。默认检测到已有亲和性冲突会跳过并告警。force:1 仅跳过软件冲突检查，不能越过 OS/Cgroup 允许的 CPU 范围。

npu_affine:1 的 NPU 亲和绑核仅支持 A2 训练系列，不能由通用 CPU_AFFINITY_CONF 的 A3 支持推出该子模式也支持 A3。PER_STREAM_QUEUE 可能有多个二级流水线程，明确不支持细粒度绑核；不能把两项优化直接叠加。

子线程继承主线程亲和性，需在创建位置管理 set_thread_affinity/reset_thread_affinity；额外业务线程和 DataLoader 争用可能使性能下降。

## 验证

检查实际允许核、每线程绑定结果与日志，再对比 Host 下发、跨卡波动及端到端稳态时间。配置成功不是收益证明。

- [TaskQueue 线程与队列](torch_npu_taskqueue_delivery.md)


## 默认分区与细粒度线程顺序

中英文环境页均按CPU核总数除以NPU卡总数给每卡默认区间，例如160核/8卡时卡0为[0,19]、卡1为[20,39]。细粒度模式主线程固定到区间首核、二级流水线程到第二核，其他热点线程依次分配，非热点线程用剩余核；自定义闭区间不等于自动确认NUMA拓扑。force未配或0仍检测冲突，1只跳过软件检查。

该环境页列950DT，但本指南还依赖每流队列和自动绑核开发说明，整卡保留A2/A3范围；950DT环境条目单列在[设备与流指南](torch_npu_native_device_stream_scope.md)，npu_affine子模式仍严格仅A2。

## 绑核时机图不固定机器核号

两语言图分别查看：业务前后显示共享区间，业务中将热点线程分核，剩余核给其他线程。图中CPU0..23等是示例；英文Reverse thread对应中文反向线程，不能误解为反转亲和性的API或硬编码线程名称。示意恢复阶段没有给异常路径的自动清理保证，仍需管理自建子线程继承与恢复。

推荐入口是Host下发慢或卡间耗时波动，先看真实NUMA与允许核区间，再比较收益。按CPU总数/NPU总数均分是默认编号分区规则，本身没有证明每段与物理NUMA一一对应；npu_affine的A2限制和PER_STREAM_QUEUE细粒度互斥继续按前文处理。

## API版本差异单独消费

补核OpPlugin发布与主线两语言set/reset接口页：主线set支持多个闭区间，发布仅单区间；None自动非主线程绑核与reset恢复主线程范围不能混同。完整参数和包装校验见[线程绑核API](../../../apis/torch_npu/thread_affinity.md)。

API产品表列950DT及A2/A3推理条目，不消除本指南npu_affine仅A2和每流队列细粒度互斥；整卡仍保留其更窄范围。先set、创建子线程、再reset的例子并不自动对所有异常恢复或既有子线程重绑负责。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/automatic_core_binding.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/performance_tuning/CPU_AFFINITY_CONF.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/taskqueue/stream_taskqueue_parallel_delivery.md)（constraint）

- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/performance_tuning/CPU_AFFINITY_CONF.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/automatic_core_binding.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/thread_core_binding_principle.png)（constraint）

- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/thread_core_binding_principle.png)（constraint）

- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-utils/torch_npu-utils.reset_thread_affinity.md)（constraint）

- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-utils/torch_npu-utils.reset_thread_affinity.md)（primary）

- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-utils/torch_npu-utils.reset_thread_affinity.md)（constraint）

- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-utils/torch_npu-utils.set_thread_affinity.md)（constraint）

- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-utils/torch_npu-utils.set_thread_affinity.md)（primary）

- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-utils/torch_npu-utils.set_thread_affinity.md)（constraint）
