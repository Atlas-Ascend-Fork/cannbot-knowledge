---
type: API
title: 量化矩阵乘与 ReduceScatter 融合（torch_npu.npu_mm_reduce_scatter_base）
description: torch_npu.npu_mm_reduce_scatter_base：TP切分场景下，执行matmul和reduce_scatter的融合，融合算子内部执行计算和通信流水并行。 TP 通算融合支持 perchannel 与 pertoken量化，两侧 scale 粒度不同。 说明推理需选择 aiv、M 可整除 rank 数、sum 归约和量化输出限制。
tags:
- task.lookup
- topic.parallelism
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_mm_reduce_scatter_base.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mm_reduce_scatter_base.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-image-3.0/adaptor_patches/hunyuan.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_mm_reduce_scatter_base.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mm_reduce_scatter_base.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MatmulReduceScatterBaseKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_mm_reduce_scatter_base.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MatmulReduceScatterBaseKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_mm_reduce_scatter_base.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/matmul_reduce_scatter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/matmul_reduce_scatter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py
  role: implementation
created_at: '2026-11-10T03:38:45Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
aliases:
- torch_npu.npu_mm_reduce_scatter_base
- 量化矩阵乘 ReduceScatter
---


# npu_mm_reduce_scatter_base：推理 AIV 与 M 轴切分

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_mm_reduce_scatter_base(input, x2, hcom, world_size, *, reduce_op='sum', bias=None, x1_scale=None, x2_scale=None, comm_turn=0, output_dtype=None, comm_mode=None) -> Tensor
```

计算 matmul 后 ReduceScatter(sum)，每 rank 取得相应分片。input=(M,K)、x2=(K,N)，M 必须整除 world_size，不能把返回说明的“维度数相同”理解为输出每轴大小与 input 相同。本卡推理路线显式使用 comm_mode="aiv"；默认 ai_cpu 只确认训练。

## 参数与组合限制

- 输入二维、同 dtype FP16/BF16/INT8，ND；x2 的 NZ 仅 aiv 支持。256≤K<65535，input 不支持转置后的 Tensor，x2 转置后仍须满足 K 轴。
- reduce_op 只支持 sum，comm_turn 只支持 0，bias 暂不支持非零值，保持 None。
- world_size：A2 为 2/4/8、HCCS all-mesh；A3 为 2/4/8/16/32、HCCS double-ring。hcom 与实际域、各 rank 调用配套。
- AIV 量化的 x1_scale=FP32(M,1)、x2_scale 为 FP32/INT64(1,N)。INT64 scale 编码路径输出 FP16；两个 scale 均 FP32 时 output_dtype 可为 FP16/BF16，默认 BF16。
- 来源要求驱动固件与 CANN 满足 8.0.RC2 或更高配套。训练 ai_cpu 下，A2 的 AllGatherMatmul/MatmulReduceScatter/MatmulAllReduce 还要求同模型使用相同通信域，不能与其他融合算子的隔离规则混用。

## 验证与模型关联

与显式局部 matmul、跨 rank sum、按 rank 切分的参考比较，验证输出分片次序与 M/world_size；量化输出单独检查 scale 和误差。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-image-3.0/adaptor_patches/hunyuan.py#L607)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 发布返回文字修正与950训练范围

两版C++和Meta的输出均为[m/world_size,n]；发布页“shape维度和input保持一致”不能解释为各轴长度相同。主线补明M整除实际通信域卡数，以及只传x2_scale也可量化。主线组合表把INT64 scale写成由output_dtype指定、默认BF16，但同页返回段及两版C++/Meta均为INT64强制FP16，保留此冲突并以实际入口分配作为静态实现事实。

主线另列950PR/DT仅基础浮点、训练ai_cpu/ccu、ND权重及可非零bias，不支持scale/output_dtype；不会因此为本卡AIV推理增添950。其文档列64卡，固定C++却仍只接受到32卡。该基本接口的CCU总量上限为16*256MB，按m*n*输出元素字节数计算；独立quant扩展页的63*256MB不是这里的替代值。

## 量化图入口和测试覆盖

主线基础GE只接受FP16/BF16，并显式拒绝x1_scale/x2_scale/output_dtype；非arch35拒绝显式comm_mode，arch35默认ai_cpu并用V2节点。发布GE没有上述量化/模式关键字。A2/A3 Eager的INT8 AIV路线不能直接当成此基础GE路线；量化图应独立核对quant扩展接口。

两版测试逐字节一致，仅A2八卡。浮点比较ai_cpu/aiv；量化只走双FP32尺度、FP16/BF16输出，dequant_type固定1、is_nz固定False。存在only-x2-scale和NZ分支代码没有让它们成为实际被选中的用例，也未测试INT64 scale、950、64卡、非零bias或错误参数。Meta不检查M整除且非正world_size改为1，更不能代替这些校验。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 量化矩阵乘与 ReduceScatter 融合：torch_npu.npu_mm_reduce_scatter_base

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

TP切分场景下，执行matmul和reduce_scatter的融合，融合算子内部执行计算和通信流水并行。

### 输入、输出与行为

支持 perchannel（逐通道）和 pertoken 量化（逐 token），两侧 scale 的粒度不同。

| 量化参数 | 粒度 | shape | dtype |
| --- | --- | --- | --- |
| x1_scale | pertoken | [m,1] | float32 |
| x2_scale | perchannel | [1,n] | float32/int64 |

左矩阵按 token，右矩阵按输出通道；需要 int64 的 x2_scale 时先用 `npu_trans_quant_param` 编码，不能直接做数值类型转换。

### 文档签名

```text
torch_npu.npu_mm_reduce_scatter_base(input, x2, hcom, world_size, *, reduce_op='sum', bias=None, x1_scale=None, x2_scale=None, comm_turn=0, output_dtype=None, comm_mode=None) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_mm_reduce_scatter_base.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mm_reduce_scatter_base.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_mm_reduce_scatter_base.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_mm_reduce_scatter_base.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MatmulReduceScatterBaseKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_mm_reduce_scatter_base.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MatmulReduceScatterBaseKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_mm_reduce_scatter_base.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/matmul_reduce_scatter.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/matmul_reduce_scatter.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py)（implementation）
