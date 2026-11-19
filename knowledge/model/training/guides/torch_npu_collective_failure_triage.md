---
type: Guide
title: TorchNPU 通信故障：输入连续性、建链等待与执行超时
description: 按输入检查、Socket 建链和 Notify 执行阶段收敛故障，关注跨 rank 首个异常及缓冲区别名。
tags:
- task.debugging
- topic.parallelism
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/troubleshooting_cases/communication_operator_transfers_Non-contiguous_tensors.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/troubleshooting_cases/communication_domain_link_establishment_timeout.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/troubleshooting_cases/HCCL_timeout.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/HCCL_EVENT_TIMEOUT.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/distributed/（beta）torch-distributed-ProcessGroupHCCL.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/HCCL_EVENT_TIMEOUT.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/socket_timeout.png
  role: constraint
created_at: '2026-11-09T03:52:43Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# TorchNPU 通信故障：输入连续性、建链等待与执行超时

## 版本与任务

依据 TorchNPU `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的所选故障案例，并以 OpPlugin `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的 HCCL 域产品页限定 A2/A3 训练。这里只归纳已选案例，不保证所有同码异常根因相同。

## 输入校验失败

Tensors must be contiguous / ERR02002 的案例发生在通信输入不连续。定位真实调用及 Tensor 的连续性、shape、dtype 和设备，再按需求建立连续输入；不要只改打印出来的错误码。

contiguous() 可能返回新存储。对于 all_reduce 等原地接口，如果对临时拷贝通信，原来的视图/参数未必收到结果；应明确下游读取哪个对象，必要时在正确同步后按业务语义回写。连续化也会产生拷贝和峰值内存，不能作为免费性能优化。

## Socket Timeout 与 HCCL 执行超时分开

建链 Socket Timeout 的来源列出 rank0 网络异常、rank0 提前退出或更晚进入建链等原因。先检查所有节点最早错误、参与者、地址及到达时间，不仅盯着最后报超时的等待方。

EI0002 表示 Notify 等待超时，可能涉及对端退出、慢 rank、样本数/调用次数不同或链路问题；来源实例是一张卡退出。不能只加大 timeout，也不能仅因一个 rank 报错就认定它是故障源。

## 不同层的 timeout

HCCL_CONNECT_TIMEOUT、HCCL_EXEC_TIMEOUT、ProcessGroup timeout 和 HCCL_EVENT_TIMEOUT 属于不同层。固定 EVENT 页面给出单位 s、默认 1868、0 永不超时，配置时要求大于 HCCL_EXEC_TIMEOUT；它不是“所有 HCCL 超时”的统一开关。ProcessGroup/Watchdog 的具体次序见相应版本卡，不从一个默认值推定所有设置的合法顺序。

## 采证与验收

保留各 rank 的组、操作序号、输入信息、退出/到达时间、最早错误和最后推进点，必要时开启状态保存。检查恢复后的调用次序、输出与缓冲区，再测试真实负载；没有复现证据时保留多种可能性。

- [状态文件的配置时机和身份](torch_npu_hccl_status_capture.md)
- [Watchdog 与异步处理](torch_npu_hccl_watchdog_timeout.md)
- [非等长 Gather](../apis/torch_npu/all_gather_into_tensor_uneven.md)
- [变长 All-to-All](../apis/torch_npu/all_to_all_vc.md)

## 完整案例与Socket截图的身份

三份案例全文再核对：Socket Timeout截图是rank1从rank0读取hcclUniqueId的store.get等待失败，末尾同时提示rank0崩溃或网络配置可能性，不能把所有Socket超时唯一归为网卡故障。图里的旧Python路径、地址和源码行号不当作本机信息。

EI0002长日志给的1800秒是该历史记录的默认执行超时，不替换当前安装环境的实际值；Non-contiguous例子的ERR02002也只是这一输入路径。调用contiguous后应明确通信结果写入哪个存储及回写时机，不能靠新Tensor变量名消除原有依赖或梯度/别名关系。本次未运行通信。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/troubleshooting_cases/communication_operator_transfers_Non-contiguous_tensors.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/troubleshooting_cases/communication_domain_link_establishment_timeout.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/troubleshooting/troubleshooting_cases/HCCL_timeout.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/HCCL_EVENT_TIMEOUT.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/distributed/（beta）torch-distributed-ProcessGroupHCCL.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/HCCL_EVENT_TIMEOUT.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/socket_timeout.png)（constraint）
