---
type: API
title: MoE 路由初始化与 gating 结果接入（torch_npu.npu_moe_init_routing）
description: torch_npu.npu_moe_init_routing：MoE 路由初始化与 gating 结果接入。MoE的routing计算，根据torch_npu.npu_moe_gating_top_k_softmax的计算结果做routing处理。 说明row_idx的槽位方向、排序后active_num裁剪与完整映射，区分发布和主线产品范围。
tags:
- task.lookup
- topic.mixture_of_experts
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_init_routing.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_init_routing.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gpt_oss/models/modeling_gpt_oss.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_init_routing.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_init_routing.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeInitRoutingKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeInitRoutingKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_init_routing.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_init_routing.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
created_at: '2026-11-10T03:38:47Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_moe_init_routing
---


# npu_moe_init_routing：旧路由映射与主线产品扩展

## 版本与范围

发布A2与主线A3、950PR及DT按固定版本分别记录，主线配套尚未确认；不能与v2路由参数混用。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_moe_init_routing(x, row_idx, expert_idx, active_num) -> (Tensor, Tensor, Tensor)
```

根据 expert_idx 排序并展开 token，返回 expanded_x、expanded_row_idx、expanded_expert_idx。x=(N,H)、expert_idx/row_idx=(N,K)，expanded_x=(min(N,active_num)*K,H)，映射和专家排序输出保留完整 N*K 路由关系。

## 参数与组合限制

发布产品表仅确认A2；主线新增A3与950PR及DT，按版本分别限定。x 为二维 ND、FP16/BF16/FP32，来源要求 shape 大小小于 2^24；row_idx、expert_idx 为 INT32。row_idx 记录原始行位置且 shape 与 expert_idx 相同，不能直接用独立 token count 替代。active_num先取min(active_num,N)，再乘K作为专家排序后输出行数，不等于仅选前active_num个原token，也不同于v2的所有专家共同处理行数。

## 验证与模型关联

构造少量 token、每个 token 多专家的可追踪样例，检查专家排序、展开行及恢复映射；再验证 active_num 截断后的有效行数。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gpt_oss/models/modeling_gpt_oss.py#L177)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)
- [专家并行中的阶段与通信选择](../../concepts/parallelism/expert_parallel.md)

## 主线扩展与row_idx的准确方向

发布仅A2；主线增加A3与950PR及DT，仍仅推理。主线中文明确单算子及图模式，英文仅提图模式，没有单独否定单算子。输入与索引的dtype、形状限制保留；英文将2^24限制表述为元素数，中文写shape大小，不扩成任意更大输入。

公开参考的row_idx按arange(N*K).reshape(K,N).T构造，即t+k*N，而不是token优先的t*K+k。按expert_idx稳定排序得到sorted_row_idx后，expanded_row_idx[sorted_row_idx[i]]=i，再以sorted_row_idx%N取原token。这一映射不能与另一token_permute接口的槽位编号混用。

两固定C++均明确检查二维、INT32索引、匹配shape、active_num≥0，随后把active_num裁到N；特征输出为裁剪后行数乘K，两份映射仍完整N*K。Meta与GE Converter的active_num=99只是内部默认，公开schema仍要求显式传入。两C++都包含“after 630转移到AscendSpeed”的旧warning，没有可确认的年份或发布版本，不据它给出日期承诺或把当前API标为deprecated。

## 已有 OpPlugin 7.3.0 文档与版本边界

### MoE 路由初始化与 gating 结果接入：torch_npu.npu_moe_init_routing

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

MoE的routing计算，根据torch_npu.npu_moe_gating_top_k_softmax的计算结果做routing处理。

### 文档签名

```text
torch_npu.npu_moe_init_routing(x, row_idx, expert_idx, active_num) -> (Tensor, Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_init_routing.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_init_routing.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_init_routing.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_init_routing.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeInitRoutingKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeInitRoutingKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_init_routing.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_init_routing.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
