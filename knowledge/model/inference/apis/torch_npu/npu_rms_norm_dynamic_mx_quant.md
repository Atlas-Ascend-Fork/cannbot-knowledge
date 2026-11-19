---
type: API
title: npu_rms_norm_dynamic_mx_quant：950 FP4/FP8与占位rstd
description: 说明RMSNorm加beta后的MXFP4/8量化、物理打包及Eager和图模式rstd的有效性。
tags:
- task.lookup
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_rms_norm_dynamic_mx_quant.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_rms_norm_dynamic_mx_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RmsNormDynamicMxQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RmsNormDynamicMxQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rms_norm_dynamic_mx_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rms_norm_dynamic_mx_quant.py
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

# npu_rms_norm_dynamic_mx_quant：950 FP4/FP8与占位rstd

## 版本与范围

本文依据 `ascend_main_candidate` 中 OpPlugin 的固定主线提交；该候选的软件配套尚未确认。不能据此推定 26.0.0 发布组合支持此接口或下列参数。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_rms_norm_dynamic_mx_quant(x, gamma, *, beta=None, epsilon=1e-06, scale_alg=0, round_mode="rint", dst_type=torch.float4_e2m1fn_x2) -> (Tensor, Tensor, Tensor)
```

本卡聚焦 FP8 路径：先沿 x 末维做 RMSNorm、加可选 beta，再以块大小 32 做 MX 量化，返回 (y,mxscale_out,rstd_out)。y 与 x 同 shape；mxscale_out 逻辑 E8M0、实际 UINT8，shape 为 x 前缀加 (ceil(ceil(D/32)/2),2)。

## 参数与组合限制

- x 为 1–7 维 FP16/BF16 ND；gamma 为一维长度 D，与 x 同 dtype 或 FP32；beta 若存在与 gamma 的 shape/dtype/格式一致。支持空及非连续 Tensor，epsilon 默认 1e-6。
- FP8 的 dst_type 明确选择 E4M3 或 E5M2、round_mode="rint"，scale_alg 只取 0 或 1；量化轴和 norm 轴固定为最后一维，不提供通用 axis/block_size 参数。
- Eager 中仅 requires_grad=True 才写出有效 rstd；False 时为 shape=[0] 的空占位。图模式不支持反向，rstd 固定为值 0、shape=[] 的标量占位，不可交给反向计算。
- 来源还列出 FP4；固定包装、Meta和GE转换器均明确物理y为UINT8、末轴N/2，不能按页面同shape文字解读物理容器。FP4 只允许 scale_alg=0 且输入末维为偶数。

## 验证与模型关联

逐步对比 RMSNorm、beta、FP8 量化及 scale 编码，分别检查 requires_grad 开关与图模式的 rstd 占位，避免误把占位当作有效统计。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py#L1163)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## FP4物理输出与有效统计量

主线中英文仅确认950PR及DT的训练/推理与单算子/图模式，图路径不支持反向。两固定版本C++、Meta及TorchAir直接确认FP4 y为UINT8、物理末轴N/2，输入N需偶数；文档“同shape”是未区分逻辑与物理的描述。E2M1/E1M2均只算法0、可rint/floor/round，不能套基础MX的E2M1算法2。默认296按同版本schema解释，页面的torch.float4命名不自动构成跨PyTorch版本可用类型名。

算法0用组内绝对值最大指数减目标emax（E2M1/E1M2/E4M3FN/E5M2为2/0/8/15）；算法1仅FP8，目标幅度比值经正规/非正规数指数进位形成E8M0。尾块pad与尺度配对布局是数据契约，不能把实际UINT8当普通整数scale或直接接逐token FP32消费者。

两固定包装只检查x.requires_grad决定rstd输出，gamma/beta是否需要梯度不替代这个条件；有效时按gamma秩构造保留norm维为1的FP32规格（公开gamma仍一维），否则返回[0]空槽。底层aclnnRmsNormDynamicMxQuant缺失会明确报升级，无自动拆算降级。Meta始终给完整rstd，两个GE Converter都传output_rstd=False，未自行构造零常量；图零标量是公开页说明，应与设备验证分开。

特殊值按公开页分别记录：Inf使y为0、尺度槽255且pad0、有效rstd为0；NaN使y为0、尺度槽255、有效rstd为NaN。不能用量化y为0排除输入异常，也不向空占位套有效统计值。固定发布已有schema/Meta/包装/Converter却缺同名公开页，不据代码回填产品支持。

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_rms_norm_dynamic_mx_quant.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_rms_norm_dynamic_mx_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RmsNormDynamicMxQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RmsNormDynamicMxQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rms_norm_dynamic_mx_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rms_norm_dynamic_mx_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）
