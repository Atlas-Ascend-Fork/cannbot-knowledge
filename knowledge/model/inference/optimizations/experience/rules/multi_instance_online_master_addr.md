---
type: Optimization
title: 多实例 online PD 部署每台 MASTER_ADDR 须指本实例组长（扁平 IP 列表下取整）
description: 多实例 online PD 部署每台 MASTER_ADDR 须指本实例组长（扁平 IP 列表下取整）。多机多实例 online（PD 分离）服务化部署时，集群把「多个各自独立组 torch.distributed 的实例」摊成一份扁平节点 IP 列表喂给启动脚本（online 模式按 PD_ROLE 从 PREFILL_IPS / DECODE_IPS 取整份跨全部同角色实例的扁平列表）。此时每台 server 的 MASTER_ADDR 与 IP 列表处理若沿用单实例逻辑，会让各实例无法按自己的组长独立建组——症状是 prefill 节点在多机多实例时 node_idx/ips 设置不对（rendezvous 冲突、可表现为分布式建组 timeout）。
tags:
- task.optimization
- topic.kv_cache
- topic.parallelism
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/483
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 多实例 online PD 部署每台 MASTER_ADDR 须指本实例组长（扁平 IP 列表下取整）

## 适用场景

多机多实例 online（[PD 分离](../../../concepts/frameworks/online_pd_inference.md)）服务化部署时，集群把「多个各自独立组 torch.distributed 的实例」摊成**一份扁平节点 IP 列表**喂给启动脚本（online 模式按 `PD_ROLE` 从 `PREFILL_IPS` / `DECODE_IPS` 取整份跨全部同角色实例的扁平列表）。此时每台 server 的 `MASTER_ADDR` 与 IP 列表处理若沿用单实例逻辑，会让各实例无法按自己的组长独立建组——症状是 prefill 节点在多机多实例时 node_idx/ips 设置不对（rendezvous 冲突、可表现为分布式建组 timeout）。

## 规则

每节点的 `MASTER_ADDR` 应按「本节点全局序号下取整到每实例节点数边界」选本实例组长，且**不得把该扁平列表裁剪到单实例长度**：

1. **online 模式保留全量扁平 IP 列表**：IP 列表截断（`IPs=(${IPs[@]:0:$SERVER_NUM})`，`SERVER_NUM==1` 时退化为仅本机 IP）只应对**离线单实例**路径生效——外层包 `if [ "$mode" != "online" ]; then ... fi`。否则会把"跨全部实例的扁平列表"砍成只剩第一个实例，其余实例丢失自己的 IP 列表，`MA_NUM_HOSTS` 与 node_idx 全错。
2. **MASTER_ADDR 按本实例组长定位**（不是恒取全局 `IPs[0]`）：
   ```sh
   export MASTER_ADDR=${IPs[$(( VC_TASK_INDEX / SERVER_NUM * SERVER_NUM ))]}
   ```
   整除再乘 `SERVER_NUM` 把全局节点序号下取整到 `SERVER_NUM` 边界，即本实例首个 server（组长）在扁平列表中的下标。`SERVER_NUM = ceil(WORLD_SIZE / chip_num)` 是本实例的 server 数，`VC_TASK_INDEX` 是本机 IP 在扁平列表中的下标。
   例：`SERVER_NUM=2`、3 个实例 → `IPs=[i0s0,i0s1,i1s0,i1s1,i2s0,i2s1]`；某机 `VC_TASK_INDEX=3` → `IPs[3//2*2]=IPs[2]=i1s0`（实例 1 的组长）。恒取 `IPs[0]=i0s0` 会让所有实例都把 rendezvous 指向实例 0 的组长，各实例无法独立建组。

## 可迁移原则

凡"多个各自独立组 torch.distributed 的实例被摊成一份扁平节点 IP 列表喂给启动脚本"，每节点 `MASTER_ADDR` 都应按"本节点全局序号下取整到每实例节点数边界"选本实例组长，且不得把列表裁剪到单实例长度。变量名（`VC_TASK_INDEX`/`SERVER_NUM`/`PREFILL_IPS`）与"online 分支"是该参考实现的细节，原则本身不受其约束。HIXL/HCCS KV 传输的对齐前置见 [hixl-hccs-ipc-2mib-alignment](hixl_hccs_ipc_2mib_alignment.md)。

## 参考实现

[cann-recipes-infer executor](../../../concepts/frameworks/cann_executor.md) 启动脚本 `executor/scripts/function.sh` 的 `get_rank()` 与 `check_env_vars()`。

## Evidence

- `diff 事实`（@f1b12b68）：online 保留全量 IP 列表 + `MASTER_ADDR` 的 per-instance 下取整计算，与同 sha 全量 `function.sh` 的 `mode`/`SERVER_NUM`/`VC_TASK_INDEX`/`PD_ROLE` 语义对上。"修前多实例 rendezvous 指向实例 0 → 各实例无法独立建组"为据代码逻辑的推断（源未附故障日志），故 `distributed_timeout` 仅作可迁移失败面向标注、不断言具体报错串。
- 溯源下探：[cann-recipes-infer-pr-483-fix-online-fix-multi-device-bug](https://gitcode.com/cann/cann-recipes-infer/merge_requests/483)

<!-- cannbot:related:start -->
## 相关

- [在线 PD 分离推理执行机制（Online PD-Disaggregated Inference）](../../../concepts/frameworks/online_pd_inference.md)（`related`）：每节点的 `MASTER_ADDR` 应按「本节点全局序号下取整到每实例节点数边界」选本实例组长，且**不得把该扁平列表裁剪到单实例长度**：；**服务实例（service instance）**：一组并行运行的 rank 构成一个 Prefill 或 Decode 实例，持有一份完整的 TP × CP × DP 并行拓扑；实例可跨节点。。规则卡给出多实例节点列表中 rendezvous 地址的分组算法，机制卡定义每个 Prefill/Decode 服务实例及其可跨节点拓扑；联合阅读可把 MASTER_ADDR 计算绑定到正确实例边界。
<!-- cannbot:related:end -->
