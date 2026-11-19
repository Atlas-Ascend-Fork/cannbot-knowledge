---
type: Guide
title: 原生量化与QAT：准备、转换和模块产品边界
description: 整理TorchAO配置/Observer/FakeQuantize与量化模块的独立支持表，保留950DT和旧数值对照工具差异；补主线量化flip源码门槛与构建期接线边界。并含 q_* 量化张量描述符与 quantize_per_tensor/per_channel 的 op-plugin 双派发路实现。
tags:
- task.optimization
- topic.precision
- topic.compute.quantization
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/Quantization.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/Quantization.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/Quantization.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/Quantization.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/Quantization.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/Quantization.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/Quantization.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/Quantization.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/Quantization.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/Quantization.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/Quantization.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/Quantization.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/Quantization.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/Quantization.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-Tensor.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/ops/QuantizedFlipKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/ops/QuantizedFlipKernelNpu.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torchnpugen/gen_backend_stubs.py
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/QuantizeTensorKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/QuantizeTensorKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantizePerTensorKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantizePerTensorKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantizePerChannelKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantizePerChannelKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/QuantizePerTensorKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/QuantizePerTensorKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/QuantizePerChannelKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/QuantizePerChannelKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-09T13:33:55Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 原生量化与QAT：准备、转换和模块产品边界

## 固定版本与证据

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的PyTorch2.7.1、2.9至2.14中英文原生支持页。按具体类/方法、文档版本与A2/A3训练系列、950DT分别消费，未收录不等于已证实不支持；不扩展950PR，不回推26.0/PyTorch2.8发布组合，不补造清单没有给出的参数或默认值。本卡仅静态审阅，未运行上游、采样、量化、训练或设备实验。

## 准备、转换和融合必须分别核对

prepare_qat、QuantStub/DeQuantStub/QuantWrapper、ns.fx.utils.compute_sqnr列三类产品，convert中文只列A2/A3、英文明确950DT不支持。中文fuse_modules.fuse_modules、add_quant_dequant/swap_module/propagate_qconfig_/default_eval_fn也列三类产品，quantize_fx.fuse_fx只列A2/A3，英文均未收录这些额外条目。清单中个别函数标成class，不因此发明可构造的类对象或替换真实签名。

准备和fake quant对象支持不证明完整“准备→校准/QAT→转换→量化执行”链路成立，更不等于底层已有相应NPU量化Kernel。不同命名空间的原生量化、TorchNPU自定义量化算子和TorchAir量化融合不共享一张支持表。

## 配置对象与Observer的局部范围

QConfigMapping及from_dict/set_global/set_module_name_object_type_order/set_object_type/to_dict、两个get_default_*_mapping列三类产品；set_module_name中文只列A2/A3、英文950不支持，set_module_name_regex两侧明确950不支持。

BackendConfig的模式配置/命名/字典转换，BackendPatternConfig的dtype、pattern、fuser、观察方式、QAT/reference/root模块配置和字典转换，DTypeConfig/DTypeWithConstraints、ObservationType及三个已列枚举项均列三类产品。Fuse/Prepare/ConvertCustomConfig的字典转换、保留属性、float→observed/observed→quantized映射、量化输入输出索引、不可追踪和独立子模块配置，以及StandaloneModuleConfigEntry也列三类产品。这些配置对象的表不证明所选模式、dtype或backend组合具有实现。

ObserverBase及with_args/with_callable_args，MinMaxObserver及calculate_qparams/forward/reset_min_max_vals，MovingAverageMinMaxObserver、PerChannelMinMaxObserver及reset_min_max_vals、MovingAveragePerChannelMinMaxObserver、Histogram/Placeholder/Recording/NoopObserver、observer状态保存/加载和所列default observer对象均列三类产品；RecordingObserver提示可能回退CPU。

中文还对AffineQuantizedObserverBase及calculate_qparams/forward/with_args、Granularity/MappingType/PerAxis/PerBlock/PerRow/PerTensor/PerToken/TorchAODType/get_block_size列三类产品，英文没有这一组。名字并不提供block大小、scale布局、舍入/饱和、对称性和合法数值范围，不据枚举存在补造量化格式合同。

FakeQuantize、FixedQParamsFakeQuantize、FusedMovingAvgObsFakeQuantize及enable/disable_fake_quant、enable/disable_observer列三类产品；FakeQuantize和FusedMovingAvgObsFakeQuantize提示可能回退CPU。FakeQuantizeBase及七种default fake-quant对象只在中文列三类产品。QConfig与所列default/per-channel/dynamic/FP16-static/FP16-dynamic/float-qparams-weight-only/QAT/weight-only/activation-only/QAT-v2配置均列三类产品，不表示任意目标产品都有对应执行Kernel。

## QAT和量化模块的产品例外

| 条目 | 来源范围与限制 |
| --- | --- |
| intrinsic.qat.ConvBn1d、ConvBnReLU1d、ConvBnReLU2d | 中英文均A2/A3不支持、950DT支持 |
| intrinsic.qat.ConvBn2d | 中文A2/A3不支持、950DT支持，英文未列 |
| nn.qat.Linear | 中英文明确950DT不支持；中文from_float又单列三类产品，不由方法表扩类 |
| intrinsic.ConvBn1d | 中文三类产品，950DT底层卷积W不能超过1000000；英文未列此类 |
| quantized.functional.avg_pool3d | 中文只列950DT，A2/A3未列，英文无此条目 |
| quantized.dynamic.Linear | 英文三类均不支持，中文未列 |
| quantized.dynamic.LSTM/GRU/RNNCell/LSTMCell/GRUCell | 中英文三类产品，input仅FP32 |

intrinsic.LinearReLU、intrinsic.qat.LinearReLU及update_bn_stats/freeze_bn_stats列三类产品，freeze_bn_stats提示可能回退CPU。中文另对普通intrinsic的ConvReLU1d/2d/3d、ConvBn2d/3d、ConvBnReLU1d/2d/3d和BNReLU2d/3d，qat.ConvReLU2d/ConvBn3d/ConvBnReLU3d及nn.qat.Conv2d/Conv3d列三类产品，英文未全部收录。不要把普通intrinsic类表传播到同名qat或quantized类。

中文对intrinsic.quantized.BNReLU2d/3d、ConvReLU1d/2d，以及nn.quantized的ReLU6/ELU/LeakyReLU/Sigmoid、BatchNorm2d/3d、Conv1d/3d、ConvTranspose1d/2d、Embedding及from_float、FloatFunctional/FXFloatFunctional/QFunctional、LayerNorm和InstanceNorm1d/2d/3d列三类产品；quantized.Conv2d只有from_float独立表，不能补造类级产品表。functional.avg_pool2d/conv3d/interpolate/linear/max_pool1d/max_pool2d/leaky_relu/hardtanh/hardswish/threshold/elu/hardsigmoid/clamp也仅中文列三类产品。

quantizable.LSTM两侧列三类产品，MultiheadAttention及forward只在中文列三类产品。动态RNN的FP32 input不是权重/输出量化格式的完整说明，也不代表输入可直接换INT8；支持清单未定义scale/zero-point和打包布局。

## 旧版本数值对照与收录差异

quantize_qat/prepare、quantize_fx.prepare_fx/prepare_qat_fx/convert_fx仅中文2.7.1收录，列三类产品；prepare_for_propagation_comparison/compare_results/generate_numeric_debug_handle/pt2e.export_utils.model_is_exported仅中文2.7.1/2.9收录，列三类产品，extract_results_from_loggers仅这两页列A2/A3。后续缺项不直接证明实际包删除。

仅2.7.1中英文还列_numeric_suite的权重/激活匹配、模型输出和stub比较、Logger/ShadowLogger/OutputLogger及forward，Shadow及forward/add/add_scalar/cat/add_relu，以及_numeric_suite_fx的NSTracer及is_leaf_module、OutputLogger/OutputComparisonLogger及forward、权重/结果提取、logger/shadow添加/开关、n-shadows准备/转换/比较工具，均有三类产品表。Shadow.mul/mul_scalar则中文仅A2/A3、英文950不支持。

Shadow.add/add_scalar/mul/mul_scalar/cat的input只列BF16/FP16/FP32/FP64、UINT8/INT8/INT16/INT32/INT64、BOOL，add_relu则只列BF16/FP16/FP32、UINT8/INT8/INT32/INT64。旧诊断工具的局部dtype和方法不能推广给全部量化Kernel或当前版本。

## 优化验收

固定量化路线、实际版本、模块、配置、observer/fake-quant状态和目标设备，分别验证准备、统计、QAT、转换、前向/梯度和真实CPU回退，再比较精度、内存和稳态吞吐。配置成功或模型含量化类不等于命中融合Kernel，本卡未运行校准、量化转换或模型。

- [原生卷积的局部输入和产品约束](torch_npu_native_convolution_constraints.md)
- [原生FX与符号形状边界](../../inference/guides/optimization/torch_npu/torch_npu_native_fx_constraints.md)
- [CPU回退与兼容实现](../../inference/guides/optimization/torch_npu/torch_npu_cpu_fallback_and_compatible_impl.md)

## Tensor量化描述符与计算能力分开

同提交Tensor页is_quantized中文只列A2/A3、英文明确950不支持；int_repr/qscheme列三产品，中文额外列五个q_per_channel/q_scale/q_zero_point描述符三产品，英文未收录。产品查询支持不表示属性结果必为True，也不能证明已具备某种量化格式、打包布局或计算Kernel。

## 方法级self类型

| 方法/属性 | self类型范围 | 来源 |
| --- | --- | --- |
| `torch.Tensor.dequantize` | FP16/FP32/FP64/UINT8/INT8/INT16/INT32/INT64/BOOL | 中英文 |
| `torch.Tensor.int_repr`、`torch.Tensor.is_quantized`、`torch.Tensor.qscheme` | 未给独立self类型表 | 中英文 |
| `torch.Tensor.q_per_channel_axis`、`torch.Tensor.q_per_channel_scales`、`torch.Tensor.q_per_channel_zero_points`、`torch.Tensor.q_scale`、`torch.Tensor.q_zero_point` | 未给独立self类型表 | 仅中文 |

dequantize的局部self表包括浮点、整数及BOOL，不能用它替其他量化方法补dtype或扩大prepare/convert的产品范围。上节量化模块、Observer和FakeQuant的CPU回退条件仍分别核对。

## torch量化函数与数值比较工具

同提交torch页quantize_per_tensor/quantize_per_channel/dequantize两侧列三产品；dequantize的input为BF16/FP16/FP32/FP64、UINT8、INT8/16/32/64、BOOL、COMPLEX64/128，与Tensor.dequantize的self表不同，不能互相覆盖。

fake_quantize_per_channel_affine/per_tensor_affine及ao.ns.fx.utils.compute_cosine_similarity/compute_normalized_l2_error仅中文七版本列三产品、英文未收录，没有完整量化范围、axis、scale、零点或误差阈值规格。数值比较工具被列入不证明某套量化模型精度合格，也不覆盖前节prepare/convert的产品排除与CPU回退条件。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/Quantization.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/Quantization.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/Quantization.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/Quantization.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/Quantization.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/Quantization.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/Quantization.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/Quantization.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/Quantization.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/Quantization.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/Quantization.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/Quantization.md)（primary）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/Quantization.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/Quantization.md)（constraint）

- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-Tensor.md)（constraint）

- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-Tensor.md)（constraint）

- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-Tensor.md)（constraint）

- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-Tensor.md)（constraint）

- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-Tensor.md)（constraint）

- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-Tensor.md)（constraint）

- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-Tensor.md)（constraint）

- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-Tensor.md)（constraint）

- [固定来源 23](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-Tensor.md)（constraint）

- [固定来源 24](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-Tensor.md)（constraint）

- [固定来源 25](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-Tensor.md)（constraint）

- [固定来源 26](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-Tensor.md)（primary）

- [固定来源 27](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-Tensor.md)（constraint）

- [固定来源 28](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-Tensor.md)（constraint）

- [固定来源 29](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch.md)（constraint）

- [固定来源 30](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch.md)（constraint）

- [固定来源 31](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch.md)（constraint）

- [固定来源 32](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch.md)（constraint）

- [固定来源 33](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch.md)（constraint）

- [固定来源 34](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch.md)（constraint）

- [固定来源 35](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch.md)（constraint）

- [固定来源 36](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch.md)（constraint）

- [固定来源 37](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch.md)（constraint）

- [固定来源 38](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch.md)（constraint）

- [固定来源 39](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch.md)（constraint）

- [固定来源 40](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch.md)（primary）

- [固定来源 41](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch.md)（constraint）

- [固定来源 42](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch.md)（constraint）

## 量化flip的源码级门槛与构建期接线

主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 `csrc/aten/ops/QuantizedFlipKernelNpu.cpp`（全文 32 行）给量化张量 flip 提供了一个免反量化实现，其分发注册**经构建期代码生成接线**：`torchnpugen/gen_backend_stubs.py` 的 `SPECIAL_REGISTERS["quantize"]` 配置（:1395-1400，dispatch_key=`QuantizedPrivateUse1`、filename=`QuantizedRegister`）经 `gen_quantize_register`（:1410-1420）按模板生成 `TORCH_LIBRARY_IMPL(aten, QuantizedPrivateUse1, m)` 注册体（:1344-1348），写入 `QuantizedRegister` 注册文件（:1378-1391）；当 `ACLNN_EXTENSION_SWITCH` 为假值（未设置或空串，:1283-1284）时，生成头 `#include "torch_npu/csrc/aten/ops/QuantizedFlipKernelNpu.h"`（:1292），注册体追加 `m.impl("flip", TORCH_FN(at_npu::native::quantized_flip));`（:1300）。固定源码树内没有该注册的静态 `TORCH_LIBRARY_IMPL` 实体或手写注册点：pin 根 rg `quantized_flip` 命中且仅命中三个文件——该 `.cpp`、其头文件与 `gen_backend_stubs.py:1300`。发布版本 无 `QuantizedFlipKernelNpu.*`，其 `gen_backend_stubs.py` rg `quantized_flip` 零命中（negative evidence）——接线为主线独有。注册的静态存在不等于运行可用：生成注册是否随实际构建产物编译生效、量化张量 flip 的运行与数值行为均未验证。不能把它的存在写成"主线已支持量化 flip"，也不能据此扩大上文 int_repr/qscheme 的文档支持表。

| 实际门槛 | 动作 | 失败/版本边界 |
| --- | --- | --- |
| dtype 非 `QUInt4x2`/`QUInt2x4` | 才继续；命中即 `TORCH_CHECK` "flip is not supported for tensor with data type ..."（:13-16） | 两种打包 dtype（4bit 打包的 `QUInt4x2` 与 2bit 打包的 `QUInt2x4`）均在实现内直接拒绝，与产品表无关 |
| dims 先过 `at::dim_list_to_bitset(dims, self.dim())`（:20；:18-19 注释声明对齐 native flip 的校验顺序） | 校验失败在 per-channel 拒绝**之前**抛出 | 即非法 dims 报 dims 错而非量化错，顺序为实现内显式设计 |
| `qscheme == kPerTensorAffine`（:21） | 否则 `TORCH_CHECK` "Setting strides is possible only on uniformly quantized tensor" | per-channel 量化张量不支持；与上文"方法级self类型"表中 q_per_channel 系列未给独立 self 表相互独立，不能互推 |
| 三关全过 | `int_repr()` 取整数表示 → `at::flip(repr, dims)` → `at::_empty_affine_quantized` 复用原 sizes/options/`q_scale`/`q_zero_point`/`suggest_memory_format` 建输出 → `NPUNativeFunctions::set_(result, flipped)`（:22-28） | 翻转在整数表示层完成，scale/零点保持不变，避免反量化-翻转-重量化；`at::flip`/`int_repr` 的设备侧实现未逐行核对，只声明该 wrapper 的组合语义 |

静态口径：以上为固定提交源码直读（实现文件全文与 torchnpugen 生成器相关行段），未运行任何量化张量 flip，未验证 `at::flip` 在量化 int 表示上的数值行为，也未验证生成注册在真实构建产物中的编译与生效；接线事实仅指该固定提交内构建脚本的静态声明，不推断历史或后续版本意图。

## 补充来源

- [固定来源 43](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/ops/QuantizedFlipKernelNpu.cpp)（primary，全文 1–32）

- [固定来源 44](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/ops/QuantizedFlipKernelNpu.h)（primary，全文 1–11）

- [固定来源 45](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torchnpugen/gen_backend_stubs.py)（primary，1278–1442：ACLNN 门控 :1283-1284、生成头 :1292、`m.impl("flip", …)` :1300、注册模板 :1344-1348、写入点 :1378-1391、quantize 配置 :1395-1400、`gen_quantize_register` :1410-1420）

## q_* 量化张量描述符与 quantize_per_tensor/per_channel 的 op-plugin 双派发路

本节核对op-plugin登记面10名。主线与发布两版本 yaml `quant:` 段登记 `q_scale`/`q_zero_point`/`q_per_channel_scales`/`q_per_channel_zero_points`/`q_per_channel_axis`/`qscheme` 仅 `acl_op: v2.2`（主线7707–7723、发布7469–7485，逐字相同；对应实现文件编译门 `VERSION_BETWEEN(V2R2, VERSION_NEWEST)`，即v2.2起，无op_api登记）；`quantize_per_tensor`/`quantize_per_channel`/`_quantize_per_tensor_impl.out`/`_quantize_per_channel_impl.out` 在official段登记 acl_op+op_api all_version（主线4048–4055、7495–7501；发布3936–3942、7281–7287）。

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| q_* 六描述符 acl_op（主线与发布两版本逐字节相同）：一律委托 `at::native::q_scale_quant(self)` 等上游host访问器；唯一例外 `q_per_channel_zero_points` 在返回前 `result.to(at::Device(at::kPrivateUse1))` 把CPU结果搬回NPU（QuantizeTensorKernelNpu.cpp 23–52） | 六名无独立设备kernel——属性读全走ATen量化张量元数据（QTensor抽象，上游六个固定版本外）；q_per_channel_zero_points的 `.to` 是一次真实D2D/H2D搬运；上文产品表"中文列五描述符三产品"是docs口径，不因本层委托事实扩大 |
| `_quantize_per_tensor_impl.out` op_api（V2R1与V2R2+两段相同主体）：dtype映射 QInt8→kChar、QUInt8→kByte、QInt32→kInt（**其余dtype静默落到kInt**），`axis=1` 硬编码，单次 `EXEC_NPU_CMD(aclnnQuantize, self, scales, zero_points, output_dtype, axis, result)`（QuantizePerTensorKernelNpuOpApi.cpp 25–43/79–97） | 无TORCH_CHECK——未列dtype不报错按Int执行；aclnnQuantize内核语义未核对 |
| `quantize_per_tensor` op_api V2R1：`{1}` Float scale张量与`{1}` Int零点张量在设备上按 `scale_tensor[0] = scale_float` 索引写构造，输出按映射dtype申请后转调 `_quantize_per_tensor_impl_out`（45–67）；V2R2+：直接 `return at::native::quantize_per_tensor(self, scale, zero_point, dtype)`（99–101） | 索引写 `operator[]` 本身经派发（设备侧写入路径未核对）；V2R2+的上游`at::native::quantize_per_tensor`（QTensor分配，六个固定版本外）最终经下述PRIVATEUSE1 stub回到本文件实现 |
| per-tensor PRIVATEUSE1 stub（V2R2+）：`REGISTER_PRIVATEUSE1_DISPATCH(quantize_tensor_per_tensor_affine_stub, ...)` 注册NPU版 `quantize_tensor_per_tensor_affine_npu`（同V2R1张量构造+impl+`set_(qtensor, result)`）与 `dequantize_tensor_per_tensor_affine_npu`（`set_(result, qtensor)` 共享存储视图→`_npu_dtype_cast` Float→**`(rtensor - zero_point) * scale` 算术组合**）（104–160） | 反量化per-tensor是三op算术组合而非单一aclnn命令；`set_`视图共享后 `result` 与 `qtensor` 别名，行为边界未展开 |
| `_quantize_per_channel_impl.out` op_api（三段V2R1/V2R2/V2R3+主体相同）：同dtype映射，`axis` 为实参直传 `aclnnQuantize`（39–56/112–129/245–262） | 与per-tensor唯一差异是axis来源（实参 vs 硬编码1） |
| `quantize_per_channel` op_api 三段演进：V2R1 自带实现——`make_warp_dim(axis)` 归一 + 五个TORCH_CHECK（scales/zero_points dim==1、两者长度相等、axis<=rank-1、scales长度==axis维长，原文"Scales' dim should be equal to 1."等）+ 映射dtype申请后转调impl（58–85）；V2R2 先 `zero_points.to(CPU, kLong).contiguous()` **CPU Long往返**再 `at::native::quantize_per_channel`（131–139）；V2R3+ 直接 `at::native::quantize_per_channel(self, scales, zero_points, axis, dtype)`（264–271） | 五个TORCH_CHECK在V2R1只存在于op_api包装；V2R2+的检查随stub迁移（见下）；CPU Long往返是V2R2独有中间态，按原文记录不判意图 |
| per-channel PRIVATEUSE1 stub（V2R2/V2R3+）：`quantize_tensor_per_channel_affine_npu` 重复五个TORCH_CHECK + `apply_tensor_without_format` + （V2R3+）`zero_points.to(Int).contiguous()` 后转调impl并 `set_`；`dequantize_tensor_per_channel_affine_npu` 同检查 + `set_`视图 + cast Float + `quantize_reshape_size`（axis维保留、其余置1）reshape scales/zero_points后 `(rtensor - zp_reshape) * scales_reshape` 广播组合（146–216/278–348） | 反量化per-channel按reshape广播算术组合；V2R2 stub内zero_points先回NPU Int，V2R3+只在计算前 `.to(Int).contiguous()`——两段细节不同，均按原文记录 |
| acl_op路（QuantizePerTensorKernelNpu.cpp / QuantizePerChannelKernelNpu.cpp）：ACE命令"Quantize"，per-tensor带attr `axis=1`+`dtype`字符串（"torch.qint8"/"torch.quint8"/"torch.qint32"，默认qint8）；per-channel把scales/zero_points先 `quantize_reshape_size` reshape成广播形再入命令；两文件同样分V2R1/V2R2+（或V2R3+）版本段，`quantize_per_*` 的V2R2+亦转 `at::native`（QuantizePerTensor 23–70/83–110；QuantizePerChannel 37–93/119–154/182–） | ACE"Quantize"与aclnnQuantize是两套接口，语义/数值等价性未核对；dtype字符串attr与opapi路的枚举映射同构 |
| pin差 | QuantizeTensorKernelNpu.cpp 主线与发布两版本逐字节相同；QuantizePerTensor/PerChannel 的opapi与aclops主线与发布两版本仅排版差异（diff -wB过滤后语义一致）；yaml条目逐字相同 |

本节静态阅读：未构造任何量化张量、未运行量化/反量化；`at::native::quantize_per_*`/`q_*_quant` 的QTensor分配与元数据读取在上游ATen（六个固定版本外）；aclnnQuantize与ACE"Quantize"内核的舍入模式、饱和边界未核对。上文QAT/prepare/convert各节的产品表和950DT边界不因本节实现事实扩大。

### q_*/quantize_per_* 补充证据

- [QuantizeTensorKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/QuantizeTensorKernelNpu.cpp)（primary）：18–73；完整本地小文件，与发布逐字节相同。
- [QuantizeTensorKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/QuantizeTensorKernelNpu.cpp)（implementation）：18–73；逐字节相同。
- [QuantizePerTensorKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantizePerTensorKernelNpuOpApi.cpp)（primary）：20–161；V2R1段20–69、V2R2+段71–161。
- [QuantizePerTensorKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantizePerTensorKernelNpuOpApi.cpp)（implementation）：20–161；与主线仅排版差异（diff -wB过滤后语义一致）。
- [QuantizePerChannelKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantizePerChannelKernelNpuOpApi.cpp)（primary）：20–352；V2R1段20–87、V2R2段89–220、V2R3+段222–352。
- [QuantizePerChannelKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantizePerChannelKernelNpuOpApi.cpp)（implementation）：20–352；与主线仅排版差异。
- [QuantizePerTensorKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/QuantizePerTensorKernelNpu.cpp)（implementation）：17–112；V2R1段17–72、V2R2+段74–112。
- [QuantizePerTensorKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/QuantizePerTensorKernelNpu.cpp)（implementation）：17–112；与主线仅排版差异。
- [QuantizePerChannelKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/QuantizePerChannelKernelNpu.cpp)（implementation）：17–219；V2R1/V2R2/V2R3+三段。
- [QuantizePerChannelKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/QuantizePerChannelKernelNpu.cpp)（implementation）：17–219；与主线仅排版差异。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：4048–4055、7495–7501、7706–7723；quantize四名official段与q_*六名quant段完整字段。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：3936–3942、7281–7287、7468–7485；同口径，与主线逐字相同。
