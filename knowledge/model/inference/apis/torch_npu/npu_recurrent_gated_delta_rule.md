---
type: API
title: 变步长 RGDR 线性注意力（torch_npu.npu_recurrent_gated_delta_rule）
description: torch_npu.npu_recurrent_gated_delta_rule：对线性注意力执行门控递归状态更新与输出计算。 变步长 Recurrent Gated Delta Rule（RGDR），线性注意力的门控递归与状态更新。 说明 Decode/投机场景的独立长度、状态索引、接受 token 数和静态图限制。
tags:
- task.lookup
- topic.attention
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_recurrent_gated_delta_rule.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_recurrent_gated_delta_rule.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5_3/models/kda.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_recurrent_gated_delta_rule.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RecurrentGatedDeltaRuleKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_recurrent_gated_delta_rule.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_recurrent_gated_delta_rule.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RecurrentGatedDeltaRuleKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_recurrent_gated_delta_rule.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/recurrent_gated_delta_rule.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/recurrent_gated_delta_rule.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
created_at: '2026-11-10T03:38:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_recurrent_gated_delta_rule
- RGDR
- Recurrent Gated Delta Rule
---


# npu_recurrent_gated_delta_rule：短步长与原地状态

## 版本与范围

本文分别核对 `ascend_26_0_pt28` 发布来源组合与固定主线。发布范围为A2/A3、BF16状态；主线增加的950PR/DT及状态类型在专节限定，主线组合配套未知。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_recurrent_gated_delta_rule(query, key, value, state, *, beta=None, scale=None, actual_seq_lengths=None, ssm_state_indices=None, num_accepted_tokens=None, g=None, gk=None) -> Tensor
```

按短序列递推更新 Gated Delta Rule 状态，返回 BF16 的 out=(T,Nv,Dv)。state 是输入兼输出，原地更新，不另外返回 final_state；它与 chunk 接口返回新状态的方式不同。

## 参数与组合限制

- q/k=(T,Nk,Dk)，value=(T,Nv,Dv)，state=(BlockNum,Nv,Dv,Dk)，均 BF16 ND。BlockNum≥T，Nk/Nv 在 [1,256]，Dk/Dv 在 [1,512]。
- 尽管签名写 None，参数说明将 beta、scale、actual_seq_lengths、ssm_state_indices 列为必填。beta=(T,Nv) BF16；scale 显式按模型传入。
- actual_seq_lengths 为 INT32(B,) 的每序列独立长度 Li∈[1,8]，T=sum(Li)；不要传 chunk 文档图示例中的累计数组。
- ssm_state_indices 为 INT32(T,)，每项在 [0,BlockNum)；num_accepted_tokens 可 None（每 batch 默认接受 1 个）或 INT32(B,)、每项在 [1,Li]。
- 可选 g=(T,Nv)、gk=(T,Nv,Dk) 为 FP32，分别经指数形成衰减，None 表示全 0。仅支持推理、单算子及静态图。
- 原地状态、投机接受长度和回滚策略应按实际模型一起核对，不能只凭输出 shape 判定多请求状态隔离正确。

## 验证与模型关联

用逐 token 递推作参考，同时检查输出、被索引的 state 和未触及状态块；覆盖 Li=1/8、不同接受长度及不同请求的状态映射。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5_3/models/kda.py#L399)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 主线state类型与实际必填参数

OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 产品页确认A2/A3/950，q/k/value仍BF16，但state允许BF16或FP32，且仅0轴/1轴允许非连续。不能把主线state的FP32扩展回推旧发布页。

Schema显式标记state可写，包装直接传给后端更新。scale=None在C++被直接拒绝；TND下beta、scale、actual_seq_lengths和ssm_state_indices仍按产品约束必传，即使Meta只检查value三维。每个Li为独立长度1..8，不是累计边界；状态索引、接受数量、q/k∈[-1,1]、beta∈(0,1)以及给定g/gk<0等值约束由用户保证，算子不能完整校验。

文档g/gk的None表示对数衰减参数为0，即exp(0)=1，不应误解成把历史状态乘0。显式functional包装先clone state并返回(out,state_copy)，与公开原地版本的输入修改/内存开销不同，不据名称自行切换接口。

## 发布与主线图类型边界

发布产品页仅列A2/A3、BF16状态；主线页扩到950PR/DT并允许FP32 state，但没有按产品逐项解释该新增类型。两个固定GE生成定义仍把query/key/value/beta/state/out统一声明为BF16的T1。因此主线页的FP32 state不能直接当成该固定静态图路径已支持，更不能回推发布。需分别验收产品、状态dtype、执行后端与实际配套。

两C++的functional分支都clone state后返回(out,state_copy)，普通分支直接修改state且只回out。主线functional Meta保留输入state dtype，发布Meta却固定为BF16；对于FP32状态，不能把Meta输出或同名functional视为两版本行为完全相同。

两版GE底层明确输出(out,stateOut)。functional Converter先TensorMove再返回该二元组，结构与其双返回Schema一致；普通Converter也直接返回该二元组，却对应单Tensor Schema。真实图路径是否已功能化、状态别名如何回写，需要检查实际图产物，不以转换器存在认定无误，也没有将这个静态差异报告成已实测故障。

## 缩放、门控与状态索引

两C++都拒绝scale=None，普通分支仅局部检查value维数，functional另查state四维；没有自动填公式的Dk**-0.5，也未完整校验beta、长度内容、索引和接受数。两版GE把scale显式转交生成函数；底层IR的1.0默认不等于上层传None能成功使用该默认。

每序列长度独立为1..8且合计T，接受数为1..Li，不能沿用因果卷积文档另有争议的Li-1。g/gk有值时主线要求严格负，对数参数None为0意味着乘1。矩阵状态轴为Dv,Dk，文档扩展公式中Diag与state的相乘顺序有轴解释疑点；所有示例Dk=Dv且gk=None，不能据此证明非方形状态的逐K门控应如何重写，须对照实际gk路径验收。

索引值合法不自动证明请求调度或重复状态映射安全；同时核对原地更新、投机读取的历史块、各token写回和未触及块，不能只检查最终输出shape。

## 唯一参考测试的局限

主线92行测试与发布只有20行完整空白差异；唯一方法无条件skip并仅标A2。参考在NPU上逐token计算，不是独立CPU黄金结果。它把g生成在[0,1]，与主线g<0约束不同；gk始终None，状态仅BF16，索引仅顺序排列。

普通入口仅比较out，功能式入口才比较返回状态，没有检查所有未触及状态、原输入保留、950、FP32、非连续轴或静态图。参考允许scale=None自动Dk**-0.5也不能覆盖当前C++必填检查。本文未运行代码，不新增数值、梯度、设备或性能验证。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 变步长 RGDR 线性注意力：torch_npu.npu_recurrent_gated_delta_rule

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

对线性注意力执行门控递归状态更新与输出计算。

### 输入、输出与行为

变步长 Recurrent Gated Delta Rule（RGDR）用于线性注意力的门控递归。每个时间步消费 q/k/v 和旧状态，更新新状态并计算输出；文档以线性时间复杂度描述其长距离依赖处理机制，这不构成当前模型吞吐或精度的实测保证。

### 文档签名

```text
torch_npu.npu_recurrent_gated_delta_rule(query, key, value, state, *, beta=None, scale=None, actual_seq_lengths=None, ssm_state_indices=None, num_accepted_tokens=None, g=None, gk=None) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_recurrent_gated_delta_rule.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_recurrent_gated_delta_rule.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_recurrent_gated_delta_rule.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RecurrentGatedDeltaRuleKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_recurrent_gated_delta_rule.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_recurrent_gated_delta_rule.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RecurrentGatedDeltaRuleKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_recurrent_gated_delta_rule.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/recurrent_gated_delta_rule.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/recurrent_gated_delta_rule.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
