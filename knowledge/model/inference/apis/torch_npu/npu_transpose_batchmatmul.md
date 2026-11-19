---
type: API
title: 三维转置批量矩阵乘（torch_npu.npu_transpose_batchmatmul）
description: torch_npu.npu_transpose_batchmatmul：执行张量`input`与张量`weight`的矩阵乘计算。 三维转置批量矩阵乘，仅支持三维输入并限定转置排列。 说明发布与主线三维批量矩阵乘的排列、产品差异，保留切分轴和scale输出类型冲突。
tags:
- task.lookup
- topic.compute.composite
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_transpose_batchmatmul.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_transpose_batchmatmul.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_transpose_batchmatmul.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_transpose_batchmatmul.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_transpose_batchmatmul.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/TransposeBatchMatMulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_transpose_batchmatmul.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/TransposeBatchMatMulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/transpose_batchmatmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/transpose_batchmatmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
created_at: '2026-11-10T03:38:51Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_transpose_batchmatmul
- 转置批量矩阵乘
---


# npu_transpose_batchmatmul：三维排列、切分与量化输出

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_transpose_batchmatmul(input, weight, *, bias=None, scale=None, perm_x1=[0,1,2], perm_x2=[0,1,2], perm_y=[1,0,2], batch_split_factor=1) -> Tensor
```

融合三维 batch matmul 与指定排列，返回三维 Tensor。无 scale 时输出为浮点；有 scale 时文档及Meta规定输出为 INT8、形状 (M,1,B*N)，C++分配差异见后文；batch_split_factor 只能为 1。

## 参数与组合限制

- input/weight 支持 FP16/BF16/FP32、ND、非连续 Tensor，必须为三维，归约 K 相等；input 为 (B,M,K) 或 (M,B,K)，weight 为 (B,K,N)。
- perm_x1 只支持 [0,1,2] 或 [1,0,2]；perm_x2 只支持 [0,1,2]，perm_y 只支持 [1,0,2]。bias 在该版本不支持，保持 None。
- K、N 要能被 16 整除；B、N 在 [1,65536) 内，末轴不大于 65535。perm_x1=[1,0,2] 时 K*B<65536，否则 K<65536。
- batch_split_factor 在 [1,N] 内且能整除 N；大于 1 时输出 (factor,M,B*N/factor)。scale 为 int64/uint64 的一维 (B*N)，还要求 B*N<65536。
- 以上为发布来源确认的 A2/A3 推理及图模式；主线950差异见下节。不是一般 permute+bmm 任意排列接口。

## 验证与模型关联

显式执行同一排列与 bmm 作参考，分别检查无 scale、有 scale、split_factor>1 的形状、dtype 和量化误差。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py#L991)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 主线产品、排列与切分轴冲突

主线双语公开增加950PR/DT推理，允许weight=(B,N,K)、perm_x2=[0,2,1]，发布公开页仍仅A2/A3及weight=(B,K,N)。主线中文把原有末轴、B/N上限和K/N对齐约束置于A2/A3段；英文参数开头仍重复这些全局上限，随后再列产品分支。保留这组语言差异，不据主线950段未重复某限制宣称任意维度都可用。

batch_split_factor的主线中文写切分B、范围[1,B]并整除B，主线英文和发布中文却写N及[1,N]。两版C++与Meta只把输出分配为(factor,M,B*N/factor)，并没有在分配阶段验证应整除哪个原始轴。这只能核实输出容量，不能用整数除法替文档冲突选定一个通用合法区间。scale存在时，公开两版都限定factor=1。

## scale输出的类型差异及静态证据

公开页和两版Meta都将scale分支的输出设为INT8；两版C++虽然采用量化分支的(M,1,B*N)形状，却仍使用input.options()分配，因此其分配类型随浮点input。此处存在实现与公开/Meta不一致，不能仅凭Meta或函数名保证Eager实际返回INT8，也不据静态差异断言所有运行路径必然失败。

两版C++在weight为NZ且input不是NZ时切换aclnnTransposeBatchMatMulWeightNz，其余走普通入口；公开ND输入范围没有因此扩展成任意格式组合。Cube模式由HF32开关并结合全局透传设置取得，两固定TorchAir转换器则传递torch.npu.matmul.allow_hf32，均不是本次性能或精度测量。

两版测试共各9个入口全部被skip，拟测仅A2。量化CPU参考是浮点MatMul后乘scale、转整数并裁剪，scale用npu_trans_quant_param(round_mode=1)构造；这段跳过的参考没有消除C++分配差异。无scale、factor=4及NZ例子也不能算已运行覆盖，亦未证明主线950或转置weight分支。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 三维转置批量矩阵乘：torch_npu.npu_transpose_batchmatmul

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

执行张量`input`与张量`weight`的矩阵乘计算。

### 输入、输出与行为

该版转置批量矩阵乘仅支持三维 Tensor。转置排列由 perm_x1/perm_x2/perm_y 分别指定：perm_x1 对应 input，perm_x2 对应 weight，perm_y 对应输出。

| 输入维数 | 是否支持 |
| --- | --- |
| 2 | no |
| 3 | yes |
| 4 | no |

该表只判断维数，三维输入还须满足该版具体约束：perm_x1 支持 [0,1,2] 或 [1,0,2]，perm_x2 仅支持 [0,1,2]，perm_y 仅支持 [1,0,2]；不能把“支持转置”理解为任意排列。K、N 需能被128整除；带 scale 时 batch_split_factor 只能为1，bias 当前不支持。

### 文档签名

```text
torch_npu.npu_transpose_batchmatmul(input, weight, *, bias=None, scale=None, perm_x1=[0,1,2], perm_x2=[0,1,2], perm_y=[1,0,2], batch_split_factor=1) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_transpose_batchmatmul.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_transpose_batchmatmul.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_transpose_batchmatmul.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_transpose_batchmatmul.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_transpose_batchmatmul.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/TransposeBatchMatMulKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_transpose_batchmatmul.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/TransposeBatchMatMulKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/transpose_batchmatmul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/transpose_batchmatmul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）
