---
type: API
title: MoE Softmax 后 TopK 专家选择（torch_npu.npu_moe_gating_top_k_softmax）
description: torch_npu.npu_moe_gating_top_k_softmax：MoE Softmax 后 TopK 专家选择。MoE计算中，对输入`x`做Softmax计算，再做topk操作。 说明 TopK 权重、专家 ID 和 row_idx 的返回顺序、K 范围及 finished 的 shape。
tags:
- task.lookup
- topic.mixture_of_experts
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_gating_top_k_softmax.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_gating_top_k_softmax.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/models/modeling_gemma4.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_gating_top_k_softmax.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_gating_top_k_softmax.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeGatingTopKSoftmaxKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeGatingTopKSoftmaxKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_gating_top_k_softmax.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_gating_top_k_softmax.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AutogradErrorFallback.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_autograd_error_fallback.py
  role: example
created_at: '2026-11-10T03:38:47Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_moe_gating_top_k_softmax
---


# npu_moe_gating_top_k_softmax：先 Softmax 后选专家

## 版本与范围

发布A2/A3与主线新增950PR及DT按固定版本分别限定；主线配套尚未确认，迁移建议与实际可用参数不混用。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_moe_gating_top_k_softmax(x, finished=None, k=1) -> (Tensor, Tensor, Tensor)
```

先在专家轴做 Softmax，再选 TopK，返回 (y,expert_idx,row_idx)。y是全专家Softmax后保留的K个概率，不在这K项内重新归一化，shape 的末维变为 K；expert_idx 和 row_idx 都是 INT32、与 y 同 shape。row_idx 的位置排列用于后续路由，不是专家编号。

## 参数与组合限制

x 为二维或三维 ND、FP16/BF16/FP32；0<K≤专家轴长度，且 K≤1024。finished 可为 None，否则为 bool，shape 必须匹配 x.shape[:-1]；来源对其维数的文字与示例存在差异，按实际前缀 shape 及运行包核对，不推导任意广播。该接口没有分组选择、Sigmoid 或 routed_scaling_factor 参数，不可代用另一 gating 接口的配置。

## 验证与模型关联

与显式 Softmax+TopK 比较权重与专家 ID，并检查 row_idx 的展开顺序；有相等得分时不要假定文档未声明的 tie-break 规则。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/models/modeling_gemma4.py#L219)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)
- [专家并行中的阶段与通信选择](../../concepts/parallelism/expert_parallel.md)

## finished、950建议与运行分支

主线中文修正finished：shape为x.shape[:-1]、维数少1，True跳过、False参与。英文仍残留“2维/3维”的文字，两个固定C++实际都检查BOOL、少1维及完整前缀相同，不支持任意广播。旧页未明确mask极性，不能根据finished名称反向理解；无效行的数值或填充值也没有在本页建立完整协议。

主线新增950PR及DT并建议使用[npu_moe_gating_top_k_softmax_v2](npu_moe_gating_top_k_softmax_v2.md)获得更好性能。这是固定来源建议，没有本仓性能数字。C++和主线GE转换器虽打印将来不再支持的warning，仍继续调用旧算子；不把warning解释成该固定提交已移除或改成deprecated。

两个包装的host检查允许0≤k≤专家数且未检查1024上限，k=0或输入任一轴为0会在底层调用前返回已分配结果；公开仍要求0<k且k≤1024，代码少检查不扩充产品契约。Meta只分配shape，不核验finished、dtype或全部k条件。旧接口第三返回仍是INT32 row_idx，不能按V2的FP32可选softmax输出使用。

## 已有 OpPlugin 7.3.0 文档与版本边界

### MoE Softmax 后 TopK 专家选择：torch_npu.npu_moe_gating_top_k_softmax

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

MoE计算中，对输入`x`做Softmax计算，再做topk操作。

### 文档签名

```text
torch_npu.npu_moe_gating_top_k_softmax(x, finished=None, k=1) -> (Tensor, Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_gating_top_k_softmax.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_gating_top_k_softmax.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_gating_top_k_softmax.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_gating_top_k_softmax.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeGatingTopKSoftmaxKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeGatingTopKSoftmaxKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_gating_top_k_softmax.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_gating_top_k_softmax.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

## 主线无反向实现的抛错边界

主线 [d84e9b1d6a558e5f27973cd4329f62968e46fdda 的 AutogradErrorFallback.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AutogradErrorFallback.cpp)（全 17 行读毕）为 `npu_moe_gating_top_k_softmax` 注册 PyTorch 内置 `autogradNotImplementedFallback`（`AutogradPrivateUse1` dispatch key 上的 boxed 内核；源注释自述对任意算子 schema 通用、无需匹配各自签名）。实际门槛与动作：前向照常执行；仅当对依赖本算子输出的张量调用 `.backward()` 时抛 `RuntimeError`，源注释给出的文案模式是 `derivative for 'npu::xxx' is not implemented`，主线[官方用例](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_autograd_error_fallback.py)只断言 "not implemented" 子串，完整文案未运行核对。用例以 `requires_grad` 叶子张量进入前向构造依赖，且仅声明在 A5 / Ascend950 验证、其它机型自动跳过。

失败与版本边界：该注册只覆盖本 schema。同族 [npu_moe_gating_top_k](npu_moe_gating_top_k.md) 的内部反向是主线生成式路径且其唯一反向测试标记跳过（见该卡），[softmax v2](npu_moe_gating_top_k_softmax_v2.md) 也不在本注册列表；都不能据此推本入口可训练，也不能推它们不可训练。
发布 dedc316708372c9a8bfde4527abd2a94b74840f5 没有该文件，且全仓不含任何 `autogradNotImplementedFallback` 注册（rg 负向核实），发布组合下反向缺失的行为未由本节建立。本节为静态阅读，未运行反向。
