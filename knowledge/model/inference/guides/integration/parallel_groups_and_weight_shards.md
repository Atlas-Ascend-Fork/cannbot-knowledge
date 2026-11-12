---
type: Guide
title: 并行改造接入：通信组、RowParallelLinear 归约与权重分片
description: 不同 TP 模块交换激活与重排，核对通信组、RowParallelLinear 显式归约、TP/EP 权重分片和在线/离线切分，并区分 MoE routing、MC2 dispatch 的 quant_mode 编码。
tags:
- task.implementation
- topic.parallelism
- topic.mixture_of_experts
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-parallel-impl/references/framework_code_examples.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-parallel-impl/references/framework_moe_parallel.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-parallel-impl/references/standalone_parallel.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/comm_manager.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/linear.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen/models/modeling_qwen.py
  role: supporting
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_init_routing_v2.md
  role: supporting
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_distribute_dispatch_v2.md
  role: supporting
created_at: '2026-11-09T09:23:46Z'
updated_at: '2026-11-10T12:21:07Z'
platforms:
- agnostic
aliases:
- 不同 TP 模块交换激活
- 模块间激活重排
- 独立 Runner ParallelContext 建组
---

# 并行改造接入：通信组、RowParallelLinear 归约与权重分片

## 接入顺序与组语义

本卡同时说明 CANN Executor 和固定 Recipes 独立 Runner 的接入契约，故不把整卡限制为单一 framework。SGLang/vLLM 的内部通信管理未在这里验证，检索时应保留 unknown，并结合各自生命周期核对。

先从已确认的 parallel_config 建组，再构造并行模块。统一 Executor 由模型 init_parallel_comm_group 向 CommManager.register_group 声明组；所有 rank 按一致顺序参加建组。get_rank(name) 返回组内 rank，get_group(name) 返回 ProcessGroup，get_group_name(name) 返回融合通信算子使用的 HCCL 名称，三者不能互换。

Attention 的 QKV 用 attn_tp_group，dense MLP 用 dense_tp_group，独立 o_proj、Embedding、LMHead 分别取模型注册的对应组。ParallelLinear 构造参数是 tp_size/tp_rank，不是把 tp_group 直接塞进构造器。RowParallelLinear 本身不自动完成跨 rank AllReduce；模型应按其布局显式归约，SP 路径可用 ReduceScatter，不能既复用已有归约又补一次 AllReduce。

不同 TP 模块间交换激活时，相邻模块的 token/hidden 分片协议必须匹配；按源布局和目标布局执行 AllGather/ReduceScatter 重排。Qwen 的 SP-TP-SP 在层间维持 token 分片，进入计算前 AllGather、输出后 ReduceScatter；不能把它简化为所有模型出口都 AllReduce。

## MoE 与通信参数

Prefill 的 double-routing 与 Decode 的 MC2 dispatch/combine 分支按模型实现选择；不支持 MC2 时可保留等价 double-routing。MC2 使用单独注册的 moe_ep_group_mc2 名称，不能按相同 ranks 自动复用普通 EP 域。routing 的 expert_tokens_num_type 必须匹配 GMM group_list_type 的 token 分组编码；count 与 cumsum 不能混用，固定参考常用 count=1。

`quant_mode` 必须按具体接口选择。固定 op-plugin 7.3.0 文档与 Recipes 参考分支的对应关系如下，不能在 routing 与 MC2 dispatch 之间复用编码：

| MoE 接口 | 非量化 quant_mode | 动态量化 quant_mode |
| --- | --- | --- |
| `npu_moe_init_routing_v2` | -1 | 1 |
| `npu_moe_distribute_dispatch_v2` | 0 | 2 |

具体参数边界见 [routing_v2](../../apis/torch_npu/npu_moe_init_routing_v2.md) 与 [dispatch_v2](../../apis/torch_npu/npu_moe_distribute_dispatch_v2.md)。量化输出还要按相应返回协议传递 per-token scale。finalize 的 drop_pad_mode=2 是所示标准聚合路径的参数，需与 expanded_src_to_dst_row 等重排元数据配套，不对所有 finalize 重载强制取2。

HCCL_BUFFSIZE 应按 token、hidden、expert 分布和融合通信预算确定，来源的 512 是示例值，不是所有模型的要求。all_to_all_single 的 input/output splits 分别与输入/输出第0维相符，所有 rank 的 collective 次数和顺序一致。

## 权重与验收

在线切分由各模块 weight_loader 根据对应组的 rank 保留切片，各 rank 可读同一完整 checkpoint；离线转换必须读取模型自己的工具及支持模式。预切权重绑定拓扑，换 TP/EP 后不能沿用旧分片。scale、smooth scale、packed expert 和 MTP 权重也须按真实规则分片，并在加载后执行模型钩子。

先检查每 rank 的权重范围和 collective 顺序，再用真实输入验证 Prefill/Decode 和 eager/图模式。固定独立模板通过 `torchrun` 提供 RANK / WORLD_SIZE / LOCAL_RANK，由 Runner 执行 `dist.init_process_group("hccl")`，再用 `build_parallel_context` 构造 `ParallelContext`；建组后以 `parallel_ctx` 注入 modeling，而非沿用统一 Executor 的 `comm_manager` 构造签名。独立 Runner 要自行负责进程与组的生命周期，不能假定获得统一 Executor 的自动管理。回退时同时恢复配置、权重、组和匹配编译缓存。

相关：[HCCL 组陷阱](../../optimizations/rules/hccl_comm_group_construction_pitfalls.md)、[MC2 专用域](../../optimizations/rules/mc2_dedicated_comm_domain.md)、[权重转换](../deployment/quant_weight_conversion_path_selection.md)。

## Evidence

- [.agents/skills/model-infer-parallel-impl/references/framework_code_examples.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-parallel-impl/references/framework_code_examples.md)
- [.agents/skills/model-infer-parallel-impl/references/framework_moe_parallel.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-parallel-impl/references/framework_moe_parallel.md)
- [.agents/skills/model-infer-parallel-impl/references/standalone_parallel.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-parallel-impl/references/standalone_parallel.md)
- [executor/core/config/comm_manager.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/comm_manager.py)
- [module/linear.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/linear.py)
- [models/qwen/models/modeling_qwen.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen/models/modeling_qwen.py)
- [routing_v2 固定参数说明](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_init_routing_v2.md)（supporting）
- [dispatch_v2 固定参数说明](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_distribute_dispatch_v2.md)（supporting）
