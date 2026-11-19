---
type: Guide
title: torch_npu_run：启动器分层TCPStore与通信域分层的区别
description: 整理大集群启动参数和proxy连接结构，区分rendezvous与HCCL后端；缺少完整产品矩阵，保留草稿。
tags:
- task.implementation
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/distributed/startup_and_fault_tolerance/torch_npu_run.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/distributed/startup_and_fault_tolerance/torch_npu_run.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/link_setup_in_torchrun_mode.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/link_setup_in_torchrun_mode.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/link_setup_in_torch_npu_run_mode.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/link_setup_in_torch_npu_run_mode.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/troubleshooting_cases/port_number_distributed_task_in_use.md
  role: primary
created_at: '2026-11-09T15:45:50Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# torch_npu_run：启动器分层TCPStore与通信域分层的区别

## 版本与范围

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf中英文torch_npu_run页全文及四份图资产。页面没有独立产品支持表，保留draft及空platforms；不回推26.0/PyTorch2.8发布配套，也不把文档“无约束”当作所有环境已经验证。

## 两层连接与默认开关

来源介绍基于epoll的多线程TCP server及可选分层TCPStore。原torchrun示意所有节点agent/worker连接node0；分层方案文字明确每节点agent启动proxy，worker通过UnixSocket连接本地proxy，proxy再通过TCP连接node0的proxy。两种图的同语言副本逐字节相同，均已查看；图用agent标记节点角色，文字对proxy的细分不能省略或当成另一份HCCL域拓扑。

enable_tiered_parallel_tcpstore支持true/false，默认false；建议大规模集群再评估。来源O(n)到O(sqrt(n))是该连接模型的复杂度描述，没有给所有节点/worker比例和本机测量，不能作为启动时延或稳态训练加速保证。

## 参数如何对应启动身份

| 参数 | 本页合同 |
| --- | --- |
| nnodes | 节点数或min:max范围 |
| nproc_per_node | 每节点worker数；页列auto/cpu/gpu/整数，不据gpu文字推定NPU自动探测的全部别名规则 |
| node_rank | 节点编号，与worker的全局RANK和LOCAL_RANK分别核对 |
| rdzv_backend/rdzv_endpoint/rdzv_id | rendezvous机制、host:port服务和所有节点加入同一作业的ID |
| standalone | 单节点多进程启动入口 |
| master_addr/master_port | 页限定静态集合点的主节点地址/端口 |
| local_addr | 本节点IP |
| enable_tiered_parallel_tcpstore | 可选节点内/节点间分层，默认关闭 |

样例使用rdzv_backend=parallel，这是启动器rendezvous/store后端，不能替代训练脚本init_process_group(backend="hccl")。页面同时给master_addr/master_port的示例，仍保留上表对静态集合点的限定，不据样例补造全部elastic优先级。

## 使用和验收

文档给单机8卡和双机各8卡模板，IP、空闲端口和ddp_test.py均为替换项；双机分别node_rank 0/1，共用主节点信息，开启分层时两边一致传true。模板没有证明当前脚本、路由或设备数量可用。

记录各节点启动配置、rendezvous身份、proxy/worker连接及到首个训练步骤的时间，另测首次HCCL建域。它与[Scalable RootInfo](torch_npu_scalable_rootinfo.md)、[RankTable](torch_npu_ranktable_communication_init.md)属于不同层次；启动器分层不自动改变通信算子带宽、pg_options继承或训练状态恢复。本卡未启动进程或集群。

## 端口占用属于启动层问题

同提交中文Address already in use案例发生在torchrun的TCPStore bind/listen阶段，来源列残留进程或其他进程占相同端口两种可能。先辨认实际地址、端口及所有节点启动配置，不把此错误等同于HCCL已建域后的执行超时，也不因同机有其他Python进程就终止它。

将MASTER_PORT从29500改29580只是示例，后者不保证空闲；改端口后所有相关节点必须使用一致的有效rendezvous信息。它不替代本页rdzv_backend/master静态参数边界或自动处理其他任务。本卡没有查询或结束进程、绑定端口或启动分布式任务。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/distributed/startup_and_fault_tolerance/torch_npu_run.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/distributed/startup_and_fault_tolerance/torch_npu_run.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/link_setup_in_torchrun_mode.png)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/link_setup_in_torchrun_mode.png)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/link_setup_in_torch_npu_run_mode.png)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/link_setup_in_torch_npu_run_mode.png)（constraint）

- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/troubleshooting_cases/port_number_distributed_task_in_use.md)（primary）
