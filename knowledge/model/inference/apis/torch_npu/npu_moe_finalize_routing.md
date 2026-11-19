---
type: API
title: MoE FFN 输出合并（torch_npu.npu_moe_finalize_routing）
description: torch_npu.npu_moe_finalize_routing：MoE FFN 输出合并。在MoE计算的最后，合并MoE FFN(Feedforward Neural Network)的输出结果。 说明行列映射、残差与专家bias，区分发布和主线950范围、k参数及ACLNN能力回退。
tags:
- task.lookup
- topic.mixture_of_experts
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_finalize_routing.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_finalize_routing.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_finalize_routing.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_finalize_routing.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeFinalizeRoutingV2KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_moe_finalize_routing_v2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeFinalizeRoutingV2KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_moe_finalize_routing_v2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_finalize_routing.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_finalize_routing.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
created_at: '2026-11-10T03:38:46Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- '950'
aliases:
- torch_npu.npu_moe_finalize_routing
---


# npu_moe_finalize_routing：专家恢复、残差与无权重TopK

## 版本与范围

发布A2与主线新增950PR及DT按固定版本分别限定；主线配套尚未确认，新增k及底层能力选择见下文。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_moe_finalize_routing(expanded_permuted_rows, skip1, skip2, bias, scales, expanded_src_to_dst_row, export_for_source_row, drop_pad_mode=0) -> Tensor
```

按 expanded_src_to_dst_row 恢复各专家 FFN 结果，按 scales 加权并相加，可再加入 skip1/skip2。返回 (N,H) Tensor、dtype 与专家输出一致。expert bias 在乘路由权重之前加入。

## 参数与组合限制

- 发布产品表只确认A2；主线另确认950PR及DT，没有A3。专家输出支持 FP16/BF16/FP32、ND；非 drop/pad 时 (N*K,H)，drop/pad 时 (E,C,H)。
- drop_pad_mode=0/1 使用按列排列的映射，2/3 使用按行排列；1/3 为 drop/pad。INT32 映射长度 N*K，普通模式值域 [0,N*K-1]，drop/pad 允许 -1 表示被丢弃项。
- skip1/skip2、bias、scales 是签名必选入参但允许 None；skip 与输出同 shape/dtype，bias=(E,H)、scales=(N,K)，expert ID 为 INT32(N,K)。
- 参数段明确 skip1=None 时 skip2 也必须 None，但参考代码处理了仅 skip2 的情况；本卡按参数限制使用，不把参考分支扩大为支持保证。scales=None 的多专家行为同样需要核对运行实现，不能从缺省权重直接推定任意 K 可用。

## 验证与模型关联

用可追踪的专家输出、路由权重和残差建立参考，检查映射行列约定、-1 丢弃、bias 的加法位置及 K>1 的恢复。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py#L534)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)
- [专家并行中的阶段与通信选择](../../concepts/parallelism/expert_parallel.md)

## 主线950范围、参数名与无scales路径

发布仅确认A2；主线中英文增加Ascend 950PR及DT，没有增加A3，仍仅推理。主线明确单算子与图模式，发布约束只写图模式但也包含单算子示例。主线软件配套尚未确认，不能把主线特性直接并入ascend_26_0_pt28发布组合。

主线文档把export_for_source_row改为expert_for_source_row并新增k=1；但两个固定schema都仍使用export_for_source_row这个拼写，主线仅追加Optional int k。文档关键字更名不证明生成接口接受新关键字，不能仅按文档改名调用；位置传参也仍须保持次序。发布没有新增k参数。

scales存在时，输出行数取scales.size(0)，K由权重矩阵给出；主线新增k用于scales=None时从长度N*K的映射推回N，通常须显式给出真实K。主线C++只在k>0时用映射长度整除k，没有在此校验正值、可整除性或全部产品条件，不能据此放宽公开契约。

## ACLNN能力选择与Meta差异

| 固定包装路径 | 选择及输出形状 |
| --- | --- |
| 发布无V2符号 | 要求skip1存在，按skip1分配输出，调用旧算子，不下传drop_pad_mode |
| 发布有V2 | 调V2，行数取scales首轴；scales=None取完整映射长度，不能推定任意多专家无权重合并 |
| 主线有V4 | 优先调V4，scales=None且k>0时按映射长度/k分配二维输出 |
| 主线无V4、有V2 | k只允许None或1，即使scales存在，非默认k也会被包装拒绝 |
| 主线V4/V2都无 | 先进入旧回退，要求skip1，忽略新增k及模式；不能把新参数接受行为视为整个运行栈一致 |

主线V4包装的其他额外可选输入均传空值，没有因此新增Python张量参数。能力检查缓存符号可用性，不提供本卡可断言的统一CANN最低版本；部署需核对实际运行库。

发布Meta在scales=None时直接empty_like专家输入，drop/pad可得到三维结果，与C++的二维输出不一致。主线Meta改用映射长度与k推导，但没有C++的k=None转1：显式None时k>0判断不一致。Meta按模式选列维，C++按输入是否三维选列维；这不使错误模式与输入组合合法。不能用Meta分配结果证明底层能力分支已经运行。

## 图路径与参考覆盖范围

两固定GE转换器在非arch35、skip1/bias/scales/expert映射都存在且mode=0时用旧MoeFinalizeRouting，否则用MoeFinalizeRoutingV2。主线把k传给GE V2，固定IR已增加该属性；GE节点名V2与Eager优先ACLNN V4分别管理，不按名字推断两者能力完全相同。None模式、能力回退与可选值需单独核对。

公开等价程序只用k*N+i列映射、从scales取K或默认1，没有实现模式2/3或新无scales多专家路径；它还无条件读取expert映射，并包含参数段不允许的仅skip2分支。它不能作为任意Optional组合的可执行金标准。-1分支将专家结果置0后仍可能加bias，不能只据参考代码宣称丢弃项必定连bias一起为0。

两份固定测试只列A2，覆盖mode=0及mode=1、scales=None且K=1的组合，未覆盖950、模式2/3、新k>1、-1丢弃或完整None组合。本次只静态审阅，未执行设备或图编译。

## 已有 OpPlugin 7.3.0 文档与版本边界

### MoE FFN 输出合并：torch_npu.npu_moe_finalize_routing

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

在MoE计算的最后，合并MoE FFN(Feedforward Neural Network)的输出结果。

### 文档签名

```text
torch_npu.npu_moe_finalize_routing(expanded_permuted_rows, skip1, skip2, bias, scales, expanded_src_to_dst_row, export_for_source_row, drop_pad_mode=0) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_finalize_routing.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_finalize_routing.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_finalize_routing.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_finalize_routing.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeFinalizeRoutingV2KernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_moe_finalize_routing_v2.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeFinalizeRoutingV2KernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_moe_finalize_routing_v2.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_finalize_routing.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_finalize_routing.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
