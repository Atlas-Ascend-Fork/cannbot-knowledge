---
type: API
title: npu_add_rms_norm_dynamic_mx_quant：950 残差与四输出顺序
description: 说明残差相加、归一化、beta与MXFP4/8融合的顺序、物理打包及双输入梯度和rstd边界。
tags:
- task.lookup
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_dynamic_mx_quant.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/models/modeling_hy_v3.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_dynamic_mx_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AddRmsNormDynamicMxQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddRmsNormDynamicMxQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_add_rms_norm_dynamic_mx_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_add_rms_norm_dynamic_mx_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
created_at: '2026-11-09T01:56:57Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- '950'
---

# npu_add_rms_norm_dynamic_mx_quant：950 残差与四输出顺序

## 版本与范围

本文依据 `ascend_main_candidate` 中 OpPlugin 的固定主线提交；该候选的软件配套尚未确认。不能据此推定 26.0.0 发布组合支持此接口或下列参数。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_add_rms_norm_dynamic_mx_quant(x1, x2, gamma, *, beta=None, epsilon=1e-06, scale_alg=0, round_mode="rint", dst_type=torch_npu.float4_e2m1fn_x2) -> (Tensor, Tensor, Tensor, Tensor)
```

本卡聚焦 FP8 路径：先 x=x1+x2，再 RMSNorm(x)+beta，最后做固定 32 元素块的 MX 量化。返回顺序为 (y,x_out,mxscale_out,rstd_out)，第二项是残差相加结果；这与普通 add_rms_norm 的返回顺序不同。

## 参数与组合限制

- x1 为 1–7 维 FP16/BF16 ND，x2 必须与其 shape/dtype/格式一致；gamma 为长度 D 的一维同 dtype 或 FP32，beta 若存在与 gamma 一致。支持空和非连续输入。
- 量化及归一化轴固定为末维。FP8 指定 E4M3/E5M2，round_mode 只能 rint，scale_alg∈{0,1}；x_out 与 x1 同 shape/dtype，FP8 y 同 shape。
- mxscale_out 逻辑 E8M0、实际 UINT8，shape 为前缀加 (ceil(ceil(D/32)/2),2)。有效 rstd 的归一化尾维保留为 1；Eager 的 requires_grad=False 返回空占位，图模式只给值 0 的标量占位且不支持反向。
- FP4 只允许 scale_alg=0、x1 末维为偶数；两固定包装、Meta与图转换器明确物理 y 为UINT8且末维N/2，公开同shape文字不能按物理字节照搬。
- Inf/NaN 等特殊值需按来源分别核对 y、x_out、scale 和 rstd，不能只用量化后的零值判定原输入正常。

## 验证与模型关联

分别比对残差相加、归一化、beta 和量化，按四输出顺序接线；验证输入梯度开关和图模式占位，不把 x_out 当作 scale 或 rstd。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/models/modeling_hy_v3.py#L1346)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 完整FP4契约与双输入梯度条件

主线中英文的950只确认PR及DT。FP4默认E2M1（296），另可E1M2（297），算法只能0，舍入可rint/floor/round；FP8 E5M2/E4M3FN可算法0/1且仅rint。算法0的共享指数emax依次为2/0/15/8，算法1先算目标幅度比值，再按文档的正规/非正规数条件上取整为E8M0；不等同于基础MX接口新增的算法2或幅度参数。

两固定版本包装、Meta与TorchAir Converter均直接证明FP4物理y尾维为N/2、UINT8承载两个值；不能再按公开页的“shape同x1”字面分配字节，也不是沿用INT4八值打包。残差x_out仍完整保留x1形状，四输出位置不变。

两固定包装显式要求x1.requires_grad与x2.requires_grad一致；只有两者都True才按norm尾维保留1分配有效FP32 rstd。只开一个输入梯度会被拒绝，只让gamma/beta需要梯度也不能据此认定rstd有效。包装缓存底层aclnnAddRmsNormDynamicMxQuant是否存在，缺失直接提示升级，没有降级到普通Add/RMSNorm的路径。

两版Meta始终分配非空rstd规格，并未复现Eager的[0]空占位或上述梯度一致性检查。两个固定GE Converter则传output_rstd=False并直接返回后端rstd；公开页将图rstd描述为零标量且不支持反向，这不是本次运行结果，也不是Converter显式构造的数值零。

中英文特殊值说明：Inf输入时量化y=0、x_out=Inf、尺度UINT8槽写255（pad为0）、有效rstd=0；NaN时y=0、x_out=NaN、尺度槽255、有效rstd=NaN。没有有效rstd的分支仍按占位规则，不能套这个表读取数据。固定发布快照已有上述代码而缺同名公开页，不回填其产品支持；没有执行设备实验。

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_dynamic_mx_quant.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_dynamic_mx_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AddRmsNormDynamicMxQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddRmsNormDynamicMxQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_add_rms_norm_dynamic_mx_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_add_rms_norm_dynamic_mx_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）
