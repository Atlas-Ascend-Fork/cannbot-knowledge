---
type: Optimization
title: online PD 的 Gloo CPU 通信组：参考启动配置与网卡排查边界
description: dp_leader_group：跨 DP 的 DP-leader 间同步； tp_cpu_group：DP-leader → TP workers 广播 Python 对象（连续批调度的队列共识即依赖它做 Gloo poll-and-all-reduce）。
tags:
- task.optimization
- topic.kv_cache
- topic.parallelism
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/424
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-22T10:41:21Z'
platforms:
- agnostic
---

# online PD 的 Gloo CPU 通信组：参考启动配置与网卡排查边界

## 适用场景

做 [online PD 分离](../../concepts/frameworks/online_pd_inference.md)服务化 bringup、需要在 HCCL / NPU 集合通信之外再起一组 **gloo 后端的 CPU 进程组**用于跨进程协调时。这些 gloo CPU 组是 **online-only**（offline 推理不需要），典型用途：

- `dp_leader_group`：跨 DP 的 DP-leader 间同步；
- `tp_cpu_group`：DP-leader → TP workers 广播 Python 对象（[连续批调度的队列共识](../../runbooks/runtime/collective_participation_per_rank_consistency.md)即依赖它做 Gloo poll-and-all-reduce）。

## 问题信号

gloo 后端 CPU 进程组的初始化依赖**网卡选择**与 **IP 协议栈**：在多网卡 / 启用 IPv6 的主机上，gloo 默认可能**绑错网卡**或**尝试 IPv6**，导致 CPU 通信域初始化失败 / 挂起。它不属于 HCCL / NPU 侧，容易在 NPU 集合通信一切正常时被忽略。

## 规则

online 启动路径在 `server.py` 拉起之前、`mode == "online"` 分支里，按该固定启动脚本**显式 export 两个环境变量**：

```sh
export GLOO_IGNORE_IPV6=1
export GLOO_SOCKET_IFNAME=${GLOO_SOCKET_IFNAME:-$(ip route show default | awk '{print $5}' | head -n1)}
```

- `GLOO_IGNORE_IPV6=1`：让 gloo 忽略 IPv6，避免在启用 IPv6 的主机上尝试 IPv6 端点。
- `GLOO_SOCKET_IFNAME`：显式指定 gloo socket 绑定的网卡；缺省从**默认路由**推断（`ip route show default` 的第 5 字段 = 出口网卡名），并用 `${VAR:-...}` 允许外部预设覆盖。

这是参考实现采用的启动配置，不能据此断言多网卡或 IPv6 环境必然失败，也不能要求所有 Gloo 环境禁用 IPv6。应先确认目标栈是否识别这些变量，再核对各 rank 的网卡地址、路由和 CPU 组连通性。

## 可迁移原则 / 边界

固定脚本的 online 分支、默认路由网卡及 dp_leader_group/tp_cpu_group 是该实现的事实。来源没有展开初始化失败根因；网卡或 IPv6 与故障的因果只能作为待验证假设。保留原配置作对照，分别改变一个变量并记录初始化结果，不能把变量名称当作通用故障证据。

## 相关经验

- 多实例 online PD 的另一条启动 env 纪律（每台 `MASTER_ADDR` 须指本实例组长）见 [multi-instance-online-master-addr](multi_instance_online_master_addr.md)。
- 这些 gloo CPU 组被连续批调度用作队列推进的全组共识通道，见 [collective-participation-per-rank-consistency](../../runbooks/runtime/collective_participation_per_rank_consistency.md)。

## Evidence

- `diff 事实`（@1df57b2052e7）：`function.sh` 的 `launch_infer_task()` online 分支新增上述两个 env export、`init_cpu_groups` 从 `CommManager` 构造迁到 online 专属 `OnlineInference.__init__` 调用（附注释「Gloo CPU groups are online-only」），均逐字对上。核心断言（online 分支导出这两个 gloo env、`GLOO_SOCKET_IFNAME` 缺省取默认路由网卡）为 diff 事实；「否则绑错网卡 / IPv6 → 初始化失败 / 挂起」的因果为基于 gloo 标准语义的推断、未并入事实面。
- 溯源下探：[cann-recipes-infer-pr-424-refactor-online-cpu](https://gitcode.com/cann/cann-recipes-infer/merge_requests/424)