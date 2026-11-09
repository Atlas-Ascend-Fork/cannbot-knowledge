---
type: Guide
title: vLLM Ascend Ray 多机启动：通信、资源视图与模型拓扑
description: 以固定Qwen3多机教程区分物理通信、Ray资源发现与真实模型推理，核对启动前环境、共享路径、TP/PP映射和验收，硬件组合保持待确认。
tags:
- task.implementation
- topic.parallelism
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/features/ray.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/features/ray.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/pipeline_parallel.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/context_parallel.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen3-235B-A22B.md
  role: constraint
created_at: '2026-10-30T09:22:23Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-30T09:24:27Z'
---

# vLLM Ascend Ray 多机启动：通信、资源视图与模型拓扑


## 范围与证据阶段

当前Ray英文188行与ray.po的33条译文完整对照，全部原串匹配。教程以Qwen3-235B-A22B为例，未给整套流程的明确A2/A3/310P/950支持矩阵，故保持draft/空平台；不能从/dev/davinci设备名、8卡例子或翻译匹配推导所有硬件均验证。

当前教程仍以 Qwen3-235B-A22B 作启动例，但其当前模型页已声明自 vLLM Ascend v0.30.0 起停止支持/修复。拓扑方法可供适配参考，不恢复该 checkpoint 的维护承诺；实际部署先选已维护模型或明确作为重新适配，见[历史模型版本边界](../models/vllm_ascend_retired_model_version_boundary.md)。

按三层收集证据：物理/NPU互联可达；Ray节点与NPU资源正确发现；实际vLLM进程拓扑、模型输出与性能。前一层成功是后一层前提之一，不证明后续已完成。ray status、ray list nodes或Dashboard出现也不等于目标模型已占到正确设备。

## 统一环境在Ray启动前生效

每节点固定同一vLLM/vLLM Ascend、Python、权重/模型路径及通信环境。来源推荐容器和--net=host，bridge模式则需目标通信端口可达；/root/.cache挂载应按该例指向所有节点可达的共享目录。等价本地模型副本需另核对版本/内容一致，不能只因路径名相同就认定checkpoint相同。

HCCL_IF_IP为各节点自己的可达IP，GLOO_SOCKET_IFNAME/TP_SOCKET_IFNAME为本地网卡名，不能复制head的本地IP到全部worker。ASCEND_RT_VISIBLE_DEVICES确定本地可见设备；教程对Ray>2.1要求RAY_EXPERIMENTAL_NOSET_ASCEND_RT_VISIBLE_DEVICES=1，这是该固定来源的版本条件，目标Ray仍须核对。环境变量与VLLM_PP_LAYER_PARTITION等应在每节点ray start前设置；启动后仅在提交shell改export不保证actor继承，按来源需重启集群使更新生效。

## head、worker和端口职责

选择一个head执行ray start --head，其余worker以head可达地址:6379加入，--node-ip-address取worker本地地址。6379为教程集群加入示例，8265是默认Dashboard地址，8000是vLLM API示例；它们不是NPU传输端口或所有版本固定配置，不互相替代。

逐节点检查hccn配置、link/net_health、远端NPU地址及互通，再查看Ray各节点/NPU数量。示例0..7光模块探针不是任意硬件设备枚举方法，先用目标机器实际可见设备映射。来源容器--shm-size=1g是例子，不作为所有大模型最小/足够内存保证。本批未运行这些探针、容器或ray start。

## TP/PP映射与单一服务入口

Ray集群就绪后只在一个节点提交vllm serve，其他节点承载Ray调度的workers，不在每节点再启动一份相同API。两台各8NPU的例子给TP8 PP2，另给跨机TP16/PP1；两者均16个模型ranks，但通信、权重/KV布局和pipeline bubble不同，不宣称等价性能或自动物理放置符合期望。

每节点NPU数作TP、节点数作PP是该例的起点，不是所有拓扑的等式。检查真实rank到node/device/stage映射；模型需SupportsPP并通过Ascend模型表约束，规则见[PP接入](../integration/vllm_ascend_pipeline_partitioning.md)。资源数量足够不证明attention头数/KV heads、MoE通信或量化kernel可承受所选TP。该例的--enable-expert-parallel与TP同时出现，不将旧教程“纯EP或纯TP”推广到整模型排斥。

## 验收与失败定位

先以较小序列/并发、明确模型和实际rank映射确认启动及确定性输出，再增加PP/TP/EP、图和长序列，记录HCCL/actor错误与每节点资源。API返回choices只证明该请求服务链路；还要验证多rank实际参与、输出精度及相同负载下TTFT/TPOT/吞吐，不能以启动耗时替代稳态性能。

资源缺失先分容器设备可见、通信环境和Ray视图；actor已就绪但first request挂起，继续分模型配置、collective/graph与负载，不单靠重复ray start或提高memory utilization。回退到上一已验证拓扑后重新对齐环境/共享路径；本卡没有执行重启或外部服务操作。PCP/DCP会改变rank复用和传输条件，另见[CP拓扑](../integration/vllm_ascend_context_parallel_topology.md)，不把CP通用地乘入TP×PP×DCP。
