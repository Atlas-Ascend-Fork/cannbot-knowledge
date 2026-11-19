---
type: API
title: 单输入交错 RoPE 位置编码（torch_npu.npu_interleave_rope）
description: torch_npu.npu_interleave_rope：单输入交错 RoPE 位置编码。针对单输入`x`进行旋转位置编码。 说明奇偶维重排公式、发布与主线产品范围，以及包装、Meta和图转换的边界。
tags:
- task.lookup
- topic.attention
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_interleave_rope.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_interleave_rope.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_interleave_rope.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/InterleaveRopeNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_interleave_rope.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/InterleaveRopeNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_interleave_rope.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_interleave_rope.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AutogradErrorFallback.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_autograd_error_fallback.py
  role: example
created_at: '2026-11-10T03:38:44Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_interleave_rope
---


# npu_interleave_rope：D=64重排与950输入差异

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_interleave_rope(x, cos, sin) -> Tensor
```

对单个 x 做旋转位置编码，返回与 x 同 shape、dtype、格式的 Tensor；cos/sin 提供旋转分量。函数名称不意味着支持任意 RoPE 权重排列或任意 head dimension。

## 参数与组合限制

- x 为连续四维 ND、形状 (B,N,S,D)，dtype 为 FP16/BF16。
- cos/sin 为连续四维 ND，dtype 与 x 相同；sin 的形状与 cos 一致，S 可为 1 或与 x.S 相同。
- 三个输入 D 必须等于 64，cos/sin 的 N 必须等于 1；不能把一般 BNSD 广播规则扩大到任意 N/D。
- 来源支持 A2/A3 推理、单算子及图模式；不据此替代 npu_rotary_mul 或其他 RoPE 接口。

## 验证与模型关联

使用同一旋转约定作参考，检查 cos/sin 广播、token 位置和 D；以 D≠64、N≠1 作为不符合此契约的反例。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py#L861)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 主线950与布局变换

OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 保留A2/A3的FP16/BF16与连续性约束；950额外确认FP32和非连续输入，输出仍连续。各产品D=64、cos/sin的N=1与S广播限制保持，不能推广任意head dimension。

公式先将x尾轴按(D/2,2)拆分、转置后重排成前后两半，再执行RotateHalf及cos/sin组合。以x=[1,2,3,4]说明该重排为[1,3,2,4]，不是对原输入直接套前后半旋转。仅作为代数解释，不是D=4的产品支持示例。

## 完整公式、产品形态与消费端实现

发布页两张公式图片与主线中英文公式对应：先令q=x.reshape(B,N,S,D//2,2).transpose(-1,-2).reshape(B,N,S,D)，再计算q*cos+RotateHalf(q)*sin，其中RotateHalf(q)=concat(-q[...,D//2:],q[...,:D//2])。它将原始奇偶维分成前后两半，不能省略重排后直接使用普通RoPE参考。旧图中的公式已逐张核对，不将Markdown未抽到公式文字视为没有额外约束。

主线产品明确950PR及DT，增加FP32和非连续输入；A2/A3保留FP16/BF16与连续输入。主线英文一般段落仍沿用旧类型/连续性文字，随后产品条目给出950例外；按产品限定记录，不能把例外扩到A2/A3。输出公开不支持非连续，三个输入仍四维ND且D=64，cos/sin的N=1、S为1或x.S，sin与cos同shape/dtype/layout。不从示例或一般广播常识增加其他B/N组合。

两固定C++全文相同：按x的shape/options另分配输出后调用aclnnInterleaveRope，没有在包装内检查D、dtype或广播。两个Meta仅empty_like(x)，两个GE转换器仅调用ge.InterleaveRope；它们不验证公式约定，也不能代替产品契约或证明任意非连续输出合法。发布A2/A3明确推理的单算子及图模式；主线新增产品没有改变固定D限制。未运行样例或性能实验。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 单输入交错 RoPE 位置编码：torch_npu.npu_interleave_rope

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

针对单输入`x`进行旋转位置编码。

### 文档签名

```text
torch_npu.npu_interleave_rope(x, cos, sin) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_interleave_rope.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_interleave_rope.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_interleave_rope.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/InterleaveRopeNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_interleave_rope.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/InterleaveRopeNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_interleave_rope.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_interleave_rope.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

## 主线无反向实现的抛错边界

主线 [d84e9b1d6a558e5f27973cd4329f62968e46fdda 的 AutogradErrorFallback.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AutogradErrorFallback.cpp)（全 17 行读毕）为 `npu_interleave_rope` 注册 PyTorch 内置 `autogradNotImplementedFallback`（`AutogradPrivateUse1` dispatch key 上的 boxed 内核；源注释自述对任意算子 schema 通用、无需匹配各自签名）。实际门槛与动作：前向照常执行；仅当对依赖本算子输出的张量调用 `.backward()` 时抛 `RuntimeError`，源注释给出的文案模式是 `derivative for 'npu::xxx' is not implemented`，主线[官方用例](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_autograd_error_fallback.py)只断言 "not implemented" 子串，完整文案未运行核对。用例以 `requires_grad` 叶子张量进入前向构造依赖，且仅声明在 A5 / Ascend950 验证、其它机型自动跳过。

失败与版本边界：该注册只覆盖 `npu_interleave_rope` 单 schema，不涉及其他 RoPE 接口的反向状态。
发布 dedc316708372c9a8bfde4527abd2a94b74840f5 没有该文件，且全仓不含任何 `autogradNotImplementedFallback` 注册（rg 负向核实），发布组合下反向缺失的行为未由本节建立。本节为静态阅读，未运行反向。
