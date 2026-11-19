---
type: Guide
title: MoE Dispatch/Combine v2 发布配套：通信组、拓扑与容量
description: 按 26.0.0 来源检查 A2/A3 的组隔离、TP 限制、算法、mask、缓冲区和静态图配套，独立于较新模型调用。
tags:
- task.implementation
- topic.mixture_of_experts
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_dispatch_v2.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_combine_v2.md
  role: constraint
created_at: '2026-11-09T01:54:44Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# 发布版 MoE 通信的接入与验收

## 适用范围

本文固定 `ascend_26_0_pt28` 的 OpPlugin 提交，聚焦 A2/A3、普通专家、无共享/特殊专家的非量化路线；动态通信量化的附加条件在 API 卡说明。950 MXFP、较新软件的特殊专家组合不能按本页推定兼容。配套文档存在不等于已在设备验证。

## 建组与输入检查

1. dispatch_v2 与 combine_v2 必须使用相同 EP 域，这个域不能混入其他算子；TP 域也须相同或双方都无 TP，启用时同样隔离其他算子。
2. group_ep、world size、专家数、TP 配置、shared 配置和 global_bs 在所有 rank 及两接口之间保持一致；来源还要求若干组/拓扑属性在网络不同层一致。rank ID 在各自域内唯一且落在 [0,world_size)。
3. 普通专家数须整除 EP 专家 rank 数。本页无共享专家时分母为 ep_world_size；local_expert_num>1 不支持 TP。A2 不支持 TP；A3 仅支持 TP=2 或无 TP，启用时 EP/TP 名称必须不同。A3 的 rank 计数按单 DIE，而不是整张双 DIE 卡。
4. A3 无 TP 的 fullmesh_v2 必须显式 tp_world_size=1 才生效；不能用“0 和 1 都表示无 TP”替代此模板的附加前提。A2 的 fullmesh、hierarchy 与 A3 的模板名字不同，不逐字照搬 comm_alg。

## 算法、shape 与容量

| 路线 | 主要 shape 限制 |
| --- | --- |
| A2 fullmesh | EP size∈{2,3,4,5,6,7,8,16,32,64,128,256}；0<BS≤256；0<H≤7168 且 H 为 32 倍数 |
| A2 hierarchy | EP size∈{16,32,64}；配驱动/HDK≥25.0.RC1.1 时 0<BS≤512、0<H≤10240 且 H 为 32 倍数 |
| A3 默认/fullmesh_v1 | EP size 在 [2,768]；0<BS≤512，H∈[1024,8192] |
| A3 fullmesh_v2 | 0<BS≤256、0<K≤12，tp_world_size=1；H∈[1024,8192] |
| A3 hierarchy | EP size 为 [16,256] 内 16 的倍数，专家数≤512，0<BS≤256；只支持 TP=1、共享专家为 0，且不支持二维 mask、特殊专家、弹性缩容或性能打点 |

普通路线 K≤16 且不超过专家数；moe_expert_num≤1024。A3 还需 local_expert_num*ep_world_size≤2048。A2 多机场景仅支持交换机组网，不能照搬双机直连配置。

普通专家输出容量 A：global_bs=0 时至少为 BS*ep_world_size*min(local_expert_num,K)，否则至少为 global_bs*min(local_expert_num,K)。各 rank 的 BS 不同则 global_bs 取 max_bs*ep_world_size，且所有 token 必须有效；BS 相同时可传 0 或 BS*ep_world_size。

x_active_mask 的一维形态要求 True 连续位于 False 前。A2 hierarchy 不支持 mask；A2 fullmesh 的二维 mask 属于实验能力，A3 hierarchy 也不支持二维 mask。本页普通路线优先不传 mask。

HCCL 缓冲区须按所选算法、最大 BS、H、专家数与 TP 配置计算，不能一律使用默认 200MB。A2 fullmesh 的来源下界为 2*(BS*ep_world_size*min(local_expert_num,K)*H*sizeof(uint16)+2MB)；其他算法有不同公式，必须分别核对两接口的固定来源，并满足二者要求。不从一个模型的 helper 或 comm_alg 字符串自行推换预算公式。

## 配套、验证与回退

先验收 Eager 路由、专家计算和 combine 的全局 token 身份、路由权重与参考输出，再验收静态图及所有 rank 的调用一致性。assist/EP/TP 计数是配套接口间的不透明数据，不解析后跨版本复用。

来源指出框架自 8.0.0 起对图末节点 Meta/inferShape 强校验；CANN 与框架不配套时，单独成图的 dispatch 可能出现 shape 不匹配。应核对实际配套并保留报错、shape 和版本，不能通过改写辅助输出尺寸掩盖问题。

性能评估保持相同路由负载，记录 HCCL 缓冲、算法、卡数、精度和稳态时延；失败时恢复已验证的通信路径。本次仅完成来源审阅，未运行多卡或图模式实验。

## 相关知识

- [Dispatch API](../../apis/torch_npu/npu_moe_distribute_dispatch_v2.md)
- [Combine API](../../apis/torch_npu/npu_moe_distribute_combine_v2.md)
- [当前模型选择](../../concepts/techniques/moe_dispatch_combine_v2.md)
- [软件栈版本基线](../../concepts/frameworks/ascend_software_stack_baselines.md)

## Evidence

- [发布版 Dispatch](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_dispatch_v2.md)
- [发布版 Combine](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_combine_v2.md)
