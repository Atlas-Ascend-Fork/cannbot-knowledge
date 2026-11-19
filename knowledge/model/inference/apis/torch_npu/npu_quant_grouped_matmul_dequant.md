---
type: API
title: npu_quant_grouped_matmul_dequant：分组量化反量化与NZ分流
description: 核对分组量化矩阵反量化的权重NZ分流、trans与Meta布局检查，并区分两个skip测试的参考和运行结论。
tags:
- task.implementation
- topic.compute.quantization
- topic.mixture_of_experts
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantGroupedMatmulDequantNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantGroupedMatmulDequantNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_quant_grouped_matmul_dequant.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_quant_grouped_matmul_dequant.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-11T06:24:37Z'
platforms: []
updated_at: '2026-11-14T01:59:28Z'
---

# npu_quant_grouped_matmul_dequant：分组量化反量化与NZ分流

## 固定版本与调用形状

本卡依据OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`和发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的完整Host包装、完整测试及所列Schema/Meta函数。两版所述包装合同一致，发布配套为ascend_26_0_pt28，主线配套未知；未获得完整平台矩阵，保持draft和空platforms。以下是静态实现与测试意图，没有运行验证。

```text
npu_quant_grouped_matmul_dequant(x, quantized_weight, weight_scale, group_list,
  *, bias=None, x_scale=None, x_offset=None, smooth_scale=None,
  quant_mode='pertoken') -> Tensor
```

它融合输入量化、分组矩阵乘及反量化，输出仍按x的dtype分配；不能因权重是INT8就将返回当作INT32累加值。需要与[路由量化五返回](npu_moe_init_routing_quant.md)分别核对：此处x的Meta约束为FP16，不能直接假设接收前者expanded_x的INT8容器。

## 权重格式决定ACLNN入口

is_nz_format直接读取权重的NPUStorageDesc，将FRACTAL_NZ、FRACTAL_NZ_C0_4和FRACTAL_NZ_C0_16均识别为NZ。NZ分支首次以函数内static bool查询`aclnnQuantGroupedMatmulDequantWeightNZ`是否可用；查询失败TORCH_CHECK要求升级CANN，没有在此回退普通入口、转换格式或定义最低CANN版本。普通格式走`aclnnQuantGroupedMatmulDequant`，两路均将trans固定为true，不能把这理解成包装已实际转置或复制权重。

两路参数顺序相同：x、quantized_weight、weight_scale、group_list、bias、x_scale、x_offset、smooth_scale、quant_mode_attr、trans、out。前四个可选Tensor按optional本身传递，不在此补默认数值；quant_mode存在时取string_view.data并cast为char*，None时传nullptr。Schema默认字符串pertoken与显式None不同，本包装没有检查模式字符串取值、字符串存储终止、分组单调性、bias广播或scale数值。

输出shape固定[x.size(0),weight_scale.size(1)]，dtype/device沿x.options；包装没有完整rank、dtype或矩阵维度检查，依赖shape索引和下游实现，不能将缺少局部检查当作支持任意组合。

## Meta检查与错误文案区别

两版Meta要求x为二维FP16，quantized_weight为三维INT8，weight_scale为二维FP32。实际谓词为x.shape[1]==quantized_weight.shape[2]，weight_scale.shape[0]==weight.shape[0]，weight_scale.shape[1]==weight.shape[1]，即常见x=[M,K]、weight=[G,N,K]、scale=[G,N]，输出为[M,N]。第一个维度错误消息误写成weight.shape[1]，应以检查表达式中的shape[2]为准。

Meta直接返回device='meta'、dtype=x.dtype的空结果；不校验group_list的值、分组总token数、可选量化参数或NZ kernel可用性。Meta成功只说明这些检查通过，不证明Eager后端或数值已验证，也不由Schema的all_version登记推导所有CANN/设备均支持。

## 两个被skip的测试能说明什么

两版87行测试字节完全相同，两个方法都叠加了`unittest.skip`和Ascend310P装饰器。它们是静态示例，不能算已执行的产品支持或精度证明。尺寸均G=4/M=64/K=256/N=512，group_list=[7,29,31,64]按累计行端点消费；原权重[G,K,N]在调用前transpose(1,2).contiguous()成为[G,N,K]，与trans=true/Meta维度配套。

动态pertoken参考以每行absmax/127构造scale，将x转置后通过NPU quantize、axis=-1和倒数scale得到INT8，再逐组float矩阵乘，乘[G,N]权重通道尺度与各行输入尺度，最后转Half并拼接。静态pertensor参考先乘[K]smooth_scale，再用单元素输入scale的倒数repeat到K交给同一NPU quantize；逐组float矩阵乘后乘权重尺度和输入scale、转Half。调用分别省略或传x_scale/smooth_scale，两者均未传bias/x_offset。参考也依赖NPU算子，不是独立纯CPU实现。

示例随机weight由randn().char()产生，尺度也为无额外约束的randn；没有覆盖NZ、空组、非法端点、bias/x_offset、零scale或None模式，不能推导一般量化数值合同。接入模型时应固定权重布局、group_list含义、输入量化方式和通道尺度方向，先做真实分组端点及数值对照，再比较融合前后的整段耗时与内存；本卡没有收益数字、设备运行或新增verified。

## Evidence



## 精确审阅范围

- [QuantGroupedMatmulDequantNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantGroupedMatmulDequantNpuOpApi.cpp)（primary）：1–85；完整本地文件。
- [QuantGroupedMatmulDequantNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantGroupedMatmulDequantNpuOpApi.cpp)（implementation）：1–65；完整本地文件。
- [test_quant_grouped_matmul_dequant.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_quant_grouped_matmul_dequant.py)（example）：1–87；完整本地文件。
- [test_quant_grouped_matmul_dequant.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_quant_grouped_matmul_dequant.py)（example）：1–87；完整本地文件。
- [_meta_registrations.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）：4929–4968；仅此片段，不提升整文件。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：6780–6782；仅此片段，不提升整文件。
- [_meta_registrations.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）：4573–4612；仅此片段，不提升整文件。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：6580–6582；仅此片段，不提升整文件。
