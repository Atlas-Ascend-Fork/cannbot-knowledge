---
type: API
title: AllGather 与矩阵乘通算融合（torch_npu.npu_all_gather_base_mm）
description: torch_npu.npu_all_gather_base_mm：AllGather 与矩阵乘通算融合。TP切分场景下，融合`allgather`和`matmul`，执行通信和计算流水并行。 限定推理需显式选择 aiv，说明输入切分、拓扑、双输出及量化 scale 的组合条件。
tags:
- task.lookup
- topic.parallelism
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_all_gather_base_mm.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_all_gather_base_mm.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-image-3.0/adaptor_patches/hunyuan.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_all_gather_base_mm.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_all_gather_base_mm.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AllGatherBaseMatmulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_all_gather_base_mm.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AllGatherBaseMatmulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_all_gather_base_mm.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/all_gather_matmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/all_gather_matmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py
  role: implementation
created_at: '2026-11-10T03:38:40Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
aliases:
- torch_npu.npu_all_gather_base_mm
---


# npu_all_gather_base_mm：推理 AIV 路线与 Gather 输出

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_all_gather_base_mm(x1, x2, hcom, world_size, bias=None, x1_scale=None, x2_scale=None, gather_index=0, gather_output=True, comm_turn=0, output_dtype=None, comm_mode=None) -> tuple[Tensor, Tensor]
```

计算 AllGather(x1)@x2，返回 (output,gather_out)。本卡聚焦推理，必须显式 comm_mode="aiv"；默认 ai_cpu 的来源约束只确认训练，不能因产品表支持推理硬件就省略模式。gather_output=False 时第二项为空 Tensor。

## 参数与组合限制

- x1/x2 为二维、同 dtype FP16/BF16/INT8，K 相等且 256≤K<65535；x1 不支持转置输入，x2 的转置仍需满足归约轴。x2 的 NZ 仅 aiv 支持。
- hcom 必须为目标通信域的 HCCL 名称，world_size 与实际域一致。A2 为 2/4/8 rank、HCCS all-mesh；A3 为 2/4/8/16/32 rank、HCCS double-ring。
- gather_index 和 comm_turn 都只能为 0；签名列举 gather_index=1 的含义不代表该版本支持。
- bias 当前不支持非零输入，保持 None；不要把普通线性层的非零 bias 直接放入融合入口。
- AIV 量化时 x1_scale=FP32(M,1)，x2_scale 为 FP32 或 INT64(1,N)。INT64 scale 由 npu_trans_quant_param 产生，输出为 FP16；两个 scale 均 FP32 时输出可选 FP16/BF16，默认 BF16。
- 必须核对驱动固件与 CANN 的配套，来源要求为 8.0.RC2 或更高配套；接口替换不代替所有 rank 的拓扑和数值验证。

## 验证与模型关联

与显式 AllGather 后 matmul 比较两个输出及 rank 顺序；检查不请求 gather 输出时的空占位，再对 AIV 与量化路线分别测量净收益。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-image-3.0/adaptor_patches/hunyuan.py#L501)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 主线产品分支、局部尺度与包装冲突

本卡原有推理路线仍限定A2/A3。主线双语另列950PR/DT基础浮点、训练ai_cpu/ccu分支：仅ND权重，不支持scale及output_dtype，可非零bias；这不扩充本卡AIV推理的平台范围。主线文档列950的2/4/8/16/32/64卡，但两版C++包装均只接受2/4/8/16/32，64会在下发前被拒绝，须保留文档与实现冲突。

主线明确A2/A3量化时只传本rank的x1_scale=[m,1]，由底层与输入一起Gather；全局共享x2_scale不Gather，不应先手工聚合左尺度后再交入口重复通信。主线input段遗漏INT8而量化分支仍存在，发布页则明确列INT8；这些文字差异不能抹平为所有产品统一类型表。主线AIV明确要求gather_output=True，发布页未列此限制；已有False占位描述不证明主线AIV合法关闭。

主线950 CCU限制总量m*k*输入元素字节数*卡数≤63*256MB，且实际shape可更严，CCU限单机UB域、AICPU可跨机UB域。这是训练分支的独立条件，不把它套到A2/A3的HCCS mesh/ring和AIV量化。

## Eager与GE、Meta的不同边界

两版C++都按x2_scale存在判断量化，INT64 scale强制FP16，否则按output_dtype或默认BF16分配；只传x1_scale不会进入该分支。Meta对应分配相同dtype，但world_size<=0时改成1，不验证实际域或合法卡数，不能用Meta成功证明可运行。

两版基础GE只接受同类型FP16/BF16。发布GE签名没有两scale、output_dtype或comm_mode；主线显式拒绝两scale和output_dtype，非arch35还拒绝显式comm_mode。需要量化图路径时应核对独立quant接口，不能把Eager支持INT8与“接口有图模式”合成基础GE支持INT8量化。

两版测试逐字节相同，仅两个A2八卡入口；量化参考仍用NPU量化Matmul且只检FP16，未覆盖BF16、INT64尺度、非零bias、关闭Gather或950/64卡。没有执行设备、进程、通信或性能测量。

## 已有 OpPlugin 7.3.0 文档与版本边界

### AllGather 与矩阵乘通算融合：torch_npu.npu_all_gather_base_mm

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

TP切分场景下，融合`allgather`和`matmul`，执行通信和计算流水并行。

### 文档签名

```text
torch_npu.npu_all_gather_base_mm(x1, x2, hcom, world_size, bias=None, x1_scale=None, x2_scale=None, gather_index=0, gather_output=True, comm_turn=0, output_dtype=None, comm_mode=None) -> tuple[Tensor, Tensor]
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_all_gather_base_mm.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_all_gather_base_mm.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_all_gather_base_mm.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_all_gather_base_mm.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AllGatherBaseMatmulKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_all_gather_base_mm.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AllGatherBaseMatmulKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_all_gather_base_mm.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/all_gather_matmul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/all_gather_matmul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py)（implementation）
