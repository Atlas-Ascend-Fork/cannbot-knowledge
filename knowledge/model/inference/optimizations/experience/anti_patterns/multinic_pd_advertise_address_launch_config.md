---
type: Optimization
title: 多网卡主机上对外通告的传输地址用启动配置固定、不靠运行时网卡探测
description: 多网卡主机上对外通告的传输地址用启动配置固定、不靠运行时网卡探测。你在多网卡（multi-NIC）主机上部署需要对端互连的分布式服务，要决定「本 rank 对外通告哪个 IP」。观测实例：PD 分离在线推理 的 prefill rank 把 ZMQ PULL socket 地址（rank_ip/rank_port）注册进 Bootstrap，供 decode 端 PUSH metadata；多网卡主机上「对端应连哪个 IP」有歧义。
tags:
- task.debugging
- topic.kv_cache
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/315
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 多网卡主机上对外通告的传输地址用启动配置固定、不靠运行时网卡探测

## 适用场景

你在多网卡（multi-NIC）主机上部署需要对端互连的分布式服务，要决定「本 rank 对外通告哪个 IP」。观测实例：[PD 分离在线推理](../../../concepts/frameworks/online_pd_inference.md) 的 prefill rank 把 ZMQ PULL socket 地址（rank_ip/rank_port）注册进 Bootstrap，供 decode 端 PUSH metadata；多网卡主机上「对端应连哪个 IP」有歧义。

## 不要做什么

不要让运行时自动探测本机 IP 作为对外通告地址。多网卡主机上自动探测可能选错网卡，且两种失败方式代价不同：

- **bind 到错网卡**：socket 静默收不到包（沉默故障，难排查）。
- **通告了错网卡 IP**：对端连接失败（可观测故障，易定位）。

## 正确写法

把「接受侧监听」与「发布侧通告」解耦——bind 全网卡 + 通告来自启动配置的固定 IP：

```python
# Bind on all interfaces; advertise self.local_ip as rank_ip. Decouples
# accept-side from advertise-side (wrong NIC there yields an unreachable
# rank_ip, detectable vs a silent listener on the wrong interface).
self.rank_port = self.server_socket.bind_to_random_port("tcp://0.0.0.0")
...
if not disagg_config.local_ip:
    raise ValueError("KVTransferManager requires DisaggConfig.local_ip to be set "
                     "(server.py derives it from --ips[node_index])")
```

- bind `0.0.0.0`（接受侧监听所有网卡，对网卡选择鲁棒）。
- 通告地址取自启动配置显式给定的 `local_ip`（发布侧），缺失即抛 `ValueError`、不回退到探测。
- `local_ip` 由启动脚本从 `--ips`（合并的 prefill+decode IP 列表）按 `node_index` 取本节点 IP 注入，是通告 rank_ip 的**唯一来源**。

即：把网卡选择前移到 launch 脚本，运行时用单一确定值。

## 为何

解耦后接受侧对网卡选择鲁棒（bind 0.0.0.0 总能收）；发布侧一旦配错，故障从「静默丢包」降级为「可观测的不可达 IP」——错误更早暴露、更好定位。这是「让配置错误尽早以可观测方式失败」的加固取向。

## 适用边界

适用于任何多网卡下、对端寻址依赖通告 IP 的分布式传输通道（[KV cache 传输](../../../concepts/frameworks/kv_cache_manager.md) / PD 分离 KVTransfer）。参考实现绑定 cann-recipes-infer 的 online PD KVTransfer，但「bind 全网卡 + 通告启动配置固定 IP + 缺失即报错」的原则与具体传输后端无关。

## 相关

- 同属昇腾 PD 分离 KV 传输后端 bringup 的前置约束：[mooncake-ascend-hixl-kv-transfer-bringup](../../../runbooks/runtime/mooncake_ascend_hixl_kv_transfer_bringup.md)。

## 相关经验
- [PD 分离下 P 端 KV block 提前释放踩内存：等全 decode-rank ACK](../../../runbooks/runtime/pd_prefill_kv_block_release_vs_decode_pull.md)

## Evidence

- diff 事实（clone `@c695829cd2c0`，`executor/online/kv_transfer/transfer_manager.py::KVTransferManager._init_rank_socket` + `executor/core/config/inference_config.py::DisaggConfig`）：`bind_to_random_port("tcp://0.0.0.0")`、`local_ip` 缺失 `raise ValueError(...--ips[node_index]...)`、`DisaggConfig.local_ip` 字段及 docstring；代码内注释给出「多网卡歧义 + 沉默故障 vs 可观测故障」的为何。归因主语为本仓该实现取舍，非上游。
  - 溯源下探：[cann-recipes-infer-pr-315-refactor-online-batch](https://gitcode.com/cann/cann-recipes-infer/merge_requests/315)
