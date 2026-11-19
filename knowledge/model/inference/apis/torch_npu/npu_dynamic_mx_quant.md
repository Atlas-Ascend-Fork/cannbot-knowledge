---
type: API
title: npu_dynamic_mx_quant：950 MXFP 量化与 E8M0 布局
description: 说明主线 MXFP4/8 的实际存储、块大小、scale 算法组合和非尾轴交织，限制发布版外推。
tags:
- task.lookup
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dynamic_mx_quant.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/utils/convert_model.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_dynamic_mx_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DynamicMxQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DynamicMxQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_mx_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_mx_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T01:56:57Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- '950'
---

# npu_dynamic_mx_quant：950 MXFP 量化与 E8M0 布局

## 版本与范围

本文依据 `ascend_main_candidate` 中 OpPlugin 的固定主线提交；该候选的软件配套尚未确认。不能据此推定 26.0.0 发布组合支持此接口或下列参数。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_dynamic_mx_quant(input, *, axis=-1, round_mode="rint", dst_type=torch_npu.float4_e2m1fn_x2, block_size=32, scale_alg=0, dst_type_max=0.0, max_low_bound=0.0) -> (Tensor, Tensor)
```

按 axis 上的 block_size 分组计算 MX scale 并量化，返回 (y,mxscale)。FP8 输出保持 input shape；FP4 实际以 UINT8 承载两个值，最后一维减半。mxscale 逻辑为 E8M0，实际返回 UINT8，不能当作普通整数或逐 token FP32 scale。

## 参数与组合限制

- 仅覆盖此主线文档确认的 950 系列。input 为 1–7 维 FP16/BF16/FP32 ND，支持非连续；axis∈[-D,D-1]。
- block_size 为 (0,1024] 内 32 的倍数。FP32 输入只支持 block_size=32、axis 维≥32；scale_alg=2 也只支持块大小 32。
- E1M2 FP4 仅支持 scale_alg=0；E2M1 FP4 支持 0/2；E4M3/E5M2 FP8 支持 0/1。FP8 只支持 rint，FP4 可用 rint/floor/round，FP4 还要求 input 末维为偶数。
- mxscale 比 input 多一维，最后一维为 2；量化轴变为 ceil(ceil(axis_size/block_size)/2)，其余轴不变。非尾轴量化还需每两行交织，不能只 reshape 成普通二维 scale。
- dst_type_max 仅用于 E2M1 FP4、block_size=32，取 0 或 [6,12]。max_low_bound 只在 scale_alg=1 生效且非负；其他算法必须为 0。
- 本接口默认 FP4，不能因模型目标为 FP8 而省略 dst_type。

## 验证与模型关联

核对量化轴、奇数块数量的 padding、UINT8 解码以及下游要求的 scale 交织；分别验证 FP4 打包和 FP8 还原误差。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/utils/convert_model.py#L270)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 算法细节与后端属性回退

主线中英文的950仅PR及DT，推理、单算子和图模式。算法0用floor(log2(组内最大绝对值))-emax形成幂次尺度，E2M1/E1M2/E4M3FN/E5M2的emax分别为2/0/8/15；算法1先按目标最大值求浮点scale，再将指数上取整为E8M0可表示值，文档分别列正规数有非零尾数和非正规数尾数>0.5的进位条件。max_low_bound在求最大绝对值之后、形成scale之前做下界钳位，只能算法1使用。

算法2仅E2M1：dst_type_max为0/6/7时按文档的高位尾数条件选择ceil/floor指数，其余[6,12]取值走目标幅度比值及指数上取整。这个分支不同于算法0，不能仅因都输出E8M0而混用尺度；文档对部分边界的位级描述仍不足以承诺独立CPU实现完全等价。

固定发布快照已有接口声明和分配实现、没有公开同名页；发布schema/Converter没有max_low_bound。发布C++有V2才传dst_type_max，主线按V3→V2→旧入口选择：V2不传max_low_bound，旧入口也不传dst_type_max，均未在这层以非零值保护失败。相同调用返回不证明这些属性生效，不能按GE节点名称推断ACLNN版本号。

两版Meta拒绝scale_alg=None，C++却把该Optional的None归到0；不能以Eager默认替代图默认。主线TorchAir才增加max_low_bound属性，两版都将FP4转回UINT8物理打包、尺度描述保留E8M0。基础MX的Meta仍用int(math.ceil(...))计算轴维，与双轴主线改用符号整数除法不同，不将dynamic=True示例提升为全动态输入保证。

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dynamic_mx_quant.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_dynamic_mx_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DynamicMxQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DynamicMxQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_mx_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_mx_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
