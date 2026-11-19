---
type: API
title: npu_add_rms_norm_dynamic_quant：双分支有效性与五输出
description: 说明输出 mask、平滑分支、INT4/FP8 产品差异以及无效槽返回空 Tensor。
tags:
- task.lookup
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_dynamic_quant.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_dynamic_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_dynamic_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddRmsNormDynamicQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_add_rms_norm_dynamic_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_add_rms_norm_dynamic_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputDtype.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputDtype.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/OpPreparation.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/TensorFactories.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/OpPreparation.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/TensorFactories.cpp
  role: implementation
created_at: '2026-11-09T06:25:22Z'
updated_at: '2026-11-09T22:10:09Z'
platforms:
- a2
- a3
- '950'
---

# npu_add_rms_norm_dynamic_quant：双分支有效性与五输出

## 版本和支持范围

依据 OpPlugin 固定主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`，按产品表和具体参数分支使用，不回推发布基线，不从单页类型名单推导任意混合组合。未执行上游代码、设备算子或图编译。

## 接口与计算

```text
npu_add_rms_norm_dynamic_quant(x1, x2, gamma, *, smooth_scale1=None,
    smooth_scale2=None, beta=None, epsilon=1e-6,
    output_mask=None, y_dtype=None) -> (y1, y2, x_out, scale1, scale2)
```

先Add，再RMSNorm乘gamma、可选加beta，然后由不同smooth_scale生成一或两路动态量化。x1/x2为同shape的2..8维FP16/BF16 ND，不支持空、可非连续；gamma及非空beta/smooth_scale均为一维尾轴D元素、dtype同x1。x_out是残差相加结果，不是归一化输出，也不表示输入被原地覆盖。

## 哪些返回槽有效

output_mask=None时第一路有效，第二路只有同时提供两份smooth_scale才有效；不允许仅smooth_scale2存在。显式mask长度2，不能都False；提供某路smooth_scale时对应mask必须True。禁用分支返回无效占位：公开页与Meta写[0]空Tensor，主线C++却分配零维标量，不能按空形状、数值0或有效输出消费。

scale1/scale2有效时为FP32、shape去掉x1末维。y_dtype默认None走INT8；INT4/quint4x2要求D被8整除，实际INT32承载且末维D/8。A2/A3仅列INT8/INT4，950另列FP8 E4M3FN/E5M2和hifloat8，后者用UINT8容器。默认INT8的每行max/127公式不能不经核对套到所有新dtype的实际量化尺度。

Meta按mask生成空槽，并确认默认无mask的第二路判定；不能把返回五项理解成永远生成两份有效量化结果。FP8的支持来自950分支，不扩大到A2/A3。


## 验证

先核对计算顺序、分组语义、scale方向与真实存储形状，再比较量化/反量化数值；覆盖空组、尾块、非连续和打包解码的实际需要。分别测内存与稳态收益，本文只有静态证据。

## 发布生成式路径与主线占位冲突

发布页、schema的output_mask默认[]且y_dtype为ScalarType Optional；主线改为Optional两位mask默认None、输出类型为int Optional。主线中英文新增950PR及DT的FP8/HiFloat8及INT4别名，A2/A3仍仅INT8/INT4。发布公开y“同shape”的INT4文字不代表物理输出：发布生成式size/dtype helper已经按N/8分配INT32并要求N被8整除，旧版不能直接套主线新类型。

主线C++的禁用分支不是文档和Meta所称的[0]空Tensor，而是用空维度列表{}请求零维标量；y和对应scale均如此。两个固定TorchNPU的OpPreparation均将shape原样传到empty工厂，工厂对{}保留零维、对{0}保留零元素默认shape，没有把两者互换。零维标量与零元素张量不同，两者都不能作为禁用分支的有效数值。主线Meta及GE Converter会给[0]空槽，因此不能仅凭Meta通过要求Eager输出形状也相同；这项跨仓静态核对不表示两个main已配套或已运行。

发布Meta的偏差更大：非None且不等于torch.int8的y_dtype一概按INT4处理；不根据mask[0]关闭y1，scale2也始终按完整前缀形状分配，默认None时y2完整。主线Meta修正类型映射及分支判断，但没有复现Eager的INT4末轴8整除检查。不要由旧Meta或主线Meta通过推定真实分支有效。

固定主线C++总是调用aclnnAddRmsNormDynamicQuantV2，没有逐接口能力探测回退；公开的smooth存在则对应mask必须True、无mask不可只提供smooth2等约束，不能由局部包装未检查而解除。固定发布没有该手写CPP，实际使用schema的gen_opapi声明，保留生成式表达式与手写路径的区别，不从文件缺失推断API不可用。

两个固定TorchAir Converter也不同：发布Converter没有y_dtype形参、只接GE AddRmsNormDynamicQuant；主线才增加目标类型、有效分支INT4重打包和禁用分支空常量。不能把发布公开的INT4参数直接视为此旧Converter已支持。量化后的五输出不提供rstd，max/127公式仅描述其INT8计算，不泛化到新FP8/HiFloat8。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_dynamic_quant.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_dynamic_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_add_rms_norm_dynamic_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddRmsNormDynamicQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_add_rms_norm_dynamic_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_add_rms_norm_dynamic_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputDtype.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputDtype.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/OpPreparation.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/TensorFactories.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/OpPreparation.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/TensorFactories.cpp)（implementation）
