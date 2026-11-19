---
type: Guide
title: 原生弹性训练：Agent、Rendezvous与启动范围
description: 区分Agent和后端组件支持，保留torchrun条目、etcd、健康检查与日志子项的950DT限制。
tags:
- task.implementation
- topic.parallelism
- topic.checkpointing
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-distributed-elastic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-distributed-elastic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-distributed-elastic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-distributed-elastic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-distributed-elastic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-distributed-elastic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-distributed-elastic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-distributed-elastic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-distributed-elastic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-distributed-elastic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-distributed-elastic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-distributed-elastic.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-distributed-elastic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-distributed-elastic.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/SECURITYNOTE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/SECURITYNOTE.en.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/SECURITYNOTE.md
  role: constraint
created_at: '2026-11-09T13:25:17Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
- '950'
---

# 原生弹性训练：Agent、Rendezvous与启动范围

## 固定版本与范围

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的PyTorch2.7.1、2.9至2.14中英文原生支持页。来源仅给所列产品和接口的支持/约束信息；未收录不等于已证实不支持，缺少的参数与组合不补造。按A2/A3训练系列和950DT分别消费，不扩展950PR，不回推26.0/PyTorch2.8发布组合，也不证明主线与其他框架配套。本卡仅静态审阅，未执行上游、训练、进程启动或设备实验。

## Agent与启动入口分层

ElasticAgent及get_worker_group/run、WorkerSpec及get_entrypoint_name、WorkerState及is_running、Worker/WorkerGroup、LocalElasticAgent、SimpleElasticAgent及列出的分配rank、初始化/监控/重启/启动/停止/关闭worker与rendezvous方法、RunResult列三类产品。内部方法有表不等于它们已成为可任意覆盖的稳定扩展协议。

torch.distributed.run.main仅中文2.12..2.14收录，明确950DT不支持；英文未列该入口。它与Agent组件的表层次不同，不据Agent支持就宣传950任意torchrun弹性训练，也不能反向解释为所有950训练启动器均不可用。

multiprocessing.start_processes、PContext/MultiprocessContext/SubprocessContext/RunProcsResult，errors.record/ChildFailedError/ErrorHandler/ProcessFailure列三类产品。DefaultLogsSpecs/LogsDest/LogsSpecs及两种Specs.reify中文只列A2/A3、英文950不支持。健康检查create_healthcheck_server、HealthCheckServer及start/stop有同样较窄范围。

## Rendezvous后端分别消费

RendezvousParameters及get/get_as_bool/get_as_int、RendezvousHandlerRegistry、dynamic_rendezvous.create_handler、c10d_rendezvous_backend.create_backend、DynamicRendezvousHandler及from_backend、RendezvousBackend及get_state/name/set_state、RendezvousTimeout及close/heartbeat/join/last_call、C10dRendezvousBackend及get_state/name/set_state列三类产品。registry.get_rendezvous_handler只在2.13/2.14收录，不把旧页缺项视作实现不支持。

RendezvousHandler及get_backend/get_run_id/is_closed/next_rendezvous/num_nodes_waiting/set_closed/shutdown列三类产品，use_agent_store却中文只列A2/A3、英文950不支持。RendezvousInfo、RendezvousStoreInfo及build、RendezvousError/GracefulExitError/ClosedError/TimeoutError/ConnectionError/StateError也有较窄范围；异常类的产品表不等于运行时错误不可能发生。

etcd_rendezvous_backend.create_backend、EtcdRendezvousHandler、EtcdStore及add/check/get/set/wait、EtcdRendezvousBackend及get_state/name/set_state中文仅列A2/A3、英文950不支持。英文另把etcd_server.EtcdServer列三类均不支持，中文缺项；这是服务端类条目，不能扩成所有外部etcd服务和已列客户端后端均不可用。

## 计时、事件与观测组件

timer.configure/debug_info_logging.log_debug_info_for_expired_timers/expires、Local/FileTimerServer与Client、TimerRequest/TimerServer及clear_timers/get_expired_timers/register_timers、TimerClient及acquire/release列三类产品；并未给全部超时默认值、故障检测与重启协议。

metrics的ConsoleMetricHandler/NullMetricHandler、configure/prof/put_metric，events.record/get_logging_handler/Event/EventSource/EventMetadataValue列三类产品。MetricHandler基类、events.construct_and_record_rdzv_event、control_plane.worker_main中文只列A2/A3、英文明确950不支持；不能由子组件表补全控制面和观测体系。

## 验收

固定启动器、rendezvous/store、日志与健康检查组件及进程组，核对rank分配、成员变化、故障退出/重启和训练状态恢复，再测重启停顿与稳态性能。页面没有保证弹性缩扩容下任意模型、优化器和HCCL通信安全；本卡未启动进程、服务或集群任务。

## Rendezvous与HCCL的网络端口分开

两固定提交的安全声明给通信矩阵：PyTorch主机侧源端口由OS临时分配；static启动默认目的29500，c10d rendezvous示例默认29400，以rdzv_endpoint指定地址和端口；torch_npu_run示例默认29500，以master-addr/master-port配置。它们是各自启动模式的文档值，不能当所有启动器、Store实现或任意服务的同一固定端口。

HCCL项另列默认60000，HCCL_IF_BASE_PORT取1024..65520，文档说明默认占从基址起16个Host端口；该通信由CANN HCCL控制，TorchNPU不直接控制。这个表不代替特定CANN版本、网卡/拓扑与独立Store环境变量的契约，也不表示只放行一个rendezvous端口就覆盖全部通信。

声明把分布式功能限定内部通信，指出未提供授权协议和消息加密；这不是某配置已启用认证/加密的证据。附带iptables是占位符和示例IP/端口，且允许规则用eno1、拒绝示例用eth0，不能不核对网卡就当通用可执行配方。本文仅保留配置层次，未启动进程、探测端口或操作防火墙。资源不足、退出或超时仍据具体日志定位，不由端口表唯一归因网络问题。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-distributed-elastic.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-distributed-elastic.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-distributed-elastic.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-distributed-elastic.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-distributed-elastic.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-distributed-elastic.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-distributed-elastic.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-distributed-elastic.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-distributed-elastic.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-distributed-elastic.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-distributed-elastic.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-distributed-elastic.md)（primary）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-distributed-elastic.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-distributed-elastic.md)（constraint）

- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/SECURITYNOTE.md)（primary）

- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/SECURITYNOTE.en.md)（constraint）

- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/SECURITYNOTE.md)（constraint）
