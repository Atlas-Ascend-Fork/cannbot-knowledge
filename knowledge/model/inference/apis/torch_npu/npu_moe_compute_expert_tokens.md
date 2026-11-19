---
type: API
title: MoE 专家末行二分查找（torch_npu.npu_moe_compute_expert_tokens）
description: torch_npu.npu_moe_compute_expert_tokens：MoE 专家末行二分查找。MoE（Mixture of Experts，混合专家模型）计算中，通过二分查找的方式查找每个专家处理的最后一行的位置。 区分累计结束偏移和每专家count，说明发布A2、主线950范围及排序、长度与专家数约束。
tags:
- task.lookup
- topic.mixture_of_experts
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_compute_expert_tokens.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_compute_expert_tokens.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gpt_oss/models/modeling_gpt_oss.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_compute_expert_tokens.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_compute_expert_tokens.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_compute_expert_tokens.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_compute_expert_tokens.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_moe_compute_tokens.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_moe_compute_tokens.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
created_at: '2026-11-10T03:38:45Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- '950'
aliases:
- torch_npu.npu_moe_compute_expert_tokens
---


# npu_moe_compute_expert_tokens：累计结束偏移与950范围

## 版本与范围

发布A2范围依据ascend_26_0_pt28，主线新增950PR及DT与更严格输入范围按独立固定快照记录，主线配套尚未确认。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_moe_compute_expert_tokens(sorted_expert_for_source_row, num_expert) -> Tensor
```

对已按专家排序的一维专家 ID，通过查找每个专家最后处理行的位置得到边界 Tensor。它服务于累计结束位置的消费方式，不能仅凭 expert_tokens 名称当作独立 count。

## 参数与组合限制

发布固定来源产品表只确认A2；主线新增950PR及DT见下文。sorted_expert_for_source_row 是一维 INT32 ND，shape 长度小于 2147483647；num_expert 是总专家数。返回一维、dtype 与输入相同。来源支持推理和图模式；未排序输入或把累计边界直接传给 count 接口不符合此语义。

## 验证与模型关联

用已知专家排序的小样本和缺席专家检查各边界，必要时先差分得到 count；再确认下游 GMM 的 group_list_type 与该表示一致。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gpt_oss/models/modeling_gpt_oss.py#L183)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)
- [专家并行中的阶段与通信选择](../../concepts/parallelism/expert_parallel.md)

## 主线范围与精确累计定义

发布只确认A2；主线中英文增加950PR及DT，未增加A3。主线中文要求输入为非递减的一维INT32专家ID，值在[0,num_expert-1]，元素数小于2^24、0<num_expert≤2048，返回shape为(num_expert,)；英文省略值域、排序和返回shape的部分文字，不据省略放宽中文约束。发布的2147483647长度与旧示例另作版本事实，不能沿用为主线上限。

两固定测试的二分参考均返回最后一个≤i的位置加1，即每个专家的累计结束偏移：专家序列[0,0,0,1,1,2]对应[3,5,6]，独立count需差分为[3,2,1]，不是零基末行[2,4,5]。这是静态参考代码的含义，未运行测试。缺席专家的累计值保持前一边界，不应把累计表示直接送入要求count的GMM。

生成schema分配(num_expert,)且沿用输入dtype，Meta固定INT32但不检查实际排序或计算累计值；两版GE只是MoeComputeExpertTokens。测试用randint(0,num_expert)包含上端点，与主线中文值域冲突，装饰器只列Ascend910B，不能据随机测试源码扩出新产品或有效ID。

## 已有 OpPlugin 7.3.0 文档与版本边界

### MoE 专家末行二分查找：torch_npu.npu_moe_compute_expert_tokens

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

MoE（Mixture of Experts，混合专家模型）计算中，通过二分查找的方式查找每个专家处理的最后一行的位置。

### 文档签名

```text
torch_npu.npu_moe_compute_expert_tokens(sorted_expert_for_source_row, num_expert) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_compute_expert_tokens.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_compute_expert_tokens.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_compute_expert_tokens.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_compute_expert_tokens.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_compute_expert_tokens.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_compute_expert_tokens.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_moe_compute_tokens.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_moe_compute_tokens.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
