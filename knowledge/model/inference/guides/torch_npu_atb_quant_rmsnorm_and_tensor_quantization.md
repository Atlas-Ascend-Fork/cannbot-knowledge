---
type: Guide
title: ATB量化输入准备：RMSNorm与Tensor量化
description: 区分两条量化入口的固定参数、Tensor scale/offset、格式与输出合同，并记录测试参考、捕获范围和固定版本差异。
tags:
- task.optimization
- topic.memory
- topic.data_movement
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/QuantRmsNormAtb.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/QuantPerTensorAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/infer_op_params.h
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test__npu_quant_rms_norm.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_atb_quant_per_tensor.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/QuantRmsNormAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/QuantPerTensorAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/infer_op_params.h
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test__npu_quant_rms_norm.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_atb_quant_per_tensor.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_ops.py
  role: implementation
created_at: '2026-11-11T03:47:18Z'
updated_at: '2026-11-11T03:47:18Z'
platforms: []
---

# ATB量化输入准备：RMSNorm与Tensor量化

两版固定提交分别为主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`与发布`dedc316708372c9a8bfde4527abd2a94b74840f5`。下述CPP完整非注释token已逐对比较相同；测试只作静态参考，未导入或运行上游、加载ATB库或做设备测试。平台配套未完整确认，整卡保持draft与空平台，没有新增verified。

公共ParamSetter的contiguous、按请求转换ND、CPU clone、输出连续性检查，以及每次Setup、自动工作区、捕获分派和资源寿命复用[ATB执行生命周期](torch_npu_atb_paged_attention_execution_lifecycle.md)。Input的format_trans=True表示请求，是否发生物理转换取决于实际Tensor；Output直接描述调用方对象。

## 两条量化入口各自的参数与槽位

`atb::_npu_quant_rms_norm`注册PrivateUse1，schema首参名为self（CPP名x），随后为gamma、beta、scale、offset、可写output和eps，默认eps=1e-5，返回()。本地函数构造RmsNormParam，固定layerType=RMS_NORM_NORM(1)、normParam.quantType=全局QUANT_INT8(2)，把double eps赋给float epsilon；五个Input依次为x/gamma/beta/scale/offset，全部请求format_trans=True，再Output(output)。它没有另行分配输出，也没有在本地函数创建OptionalDeviceGuard；流与Context按公共执行代码核验，不能从其它入口补入guard。

NormParam其余字段保持默认：layerNormEps=1e-5（注释暂不使用）、rstd=False、precisionMode=HIGH_PRECISION_MODE(0)、modelType=LLAMA_MODEL(0)、dynamicQuantType=DYNAMIC_QUANT_UNDEFINED(0)。头文件说明量化场景不支持使用rstd或额外配置precisionMode/modelType，动态非对称量化暂不支持；该入口不开放这些配置。其量化类型是全局枚举，不能套用PagedAttentionParam内另一套0/1/2/3含义。

RmsNormParam总注释写输入输出末维相等、Atlas推理系列产品不支持BF16；所选量化测试则让gamma/beta末维128、scale/offset为单元素。这些声明与测试的作用范围分别保留，本地包装层未逐个校验形状，不能把总注释自行扩成所有量化辅助Tensor末维也必须128。精确辅助Tensor形状与运行配套继续按实际ATB核验。

`atb::_npu_quantize_per_tensor`同样为PrivateUse1、调用方可写y、返回()。它以x建立OptionalDeviceGuard，但实际ElewiseParam类型固定为ELEWISE_QUANT_PER_CHANNEL(17)。名称中的per_tensor不表示包装层只接收标量scale。参数对象还固定quantParam.inputScale=1.0、asymmetric=False、inputOffset=0、mulsParam.varAttr=0.0、outTensorType=ACL_DT_UNDEFINED；实际scale与zero_point分别作为第1/2号Tensor输入，x为第0号，三者全部请求format_trans=True，再Output(y)。不要把静态inputOffset=0误读成实际zero_point被忽略，或把ELEWISE_QUANT的A2注释移给此处选择的不同枚举。

两条入口分别取RmsNormParam和ElewiseParam的类型化OpParamCache，操作名为QuantRmsNormOperation与ElewiseCacheOperation，然后RunAtbCmd自动处理工作区。RmsNorm专用hash写epsilon/layerType/quantType；所读缓存头中Elewise沿用不写字段的默认HashOpParam，该入口属性固定。此事实不意味着输入Tensor内容缓存或运行时shape/数据被跳过，每次仍提交VariantPack并Setup。

Python API_LIST包含两个准确名字，生成的函数转发getattr(torch.ops.atb, api_name)；补丁入口把API_LIST绑定torch_npu顶层，因此测试使用torch_npu._npu_quant_rms_norm和torch_npu._npu_quantize_per_tensor。当前卡只覆盖这些名字的绑定，不扩大到其它ATB接口。

## RMS量化测试的参考计算与范围

两版test__npu_quant_rms_norm.py完整AST一致。参考函数先把x/gamma/beta/scale转FP32，gamma/beta squeeze首维，scale/offset取item；按batch、seq循环计算rms=sqrt(mean(x²)+eps)，y=x/rms×gamma+beta，再round(y/scale+offset)、clip[-128,127]并转INT8。测试seed=12，x为[4,1,128] FP16，gamma/beta为[1,128] FP16，scale=[0.3] FP16，offset=[2] INT8，out与x同shape但INT8，eps=1e-5；比较设备output与该CPU参考。用例标注SupportedDevices(Ascend910B)，本次未执行，不把装饰器或断言当作实测成功。

## Tensor量化测试和版本差异

两版TestElewiseQuantOperation构造函数设置ASCEND_LAUNCH_BLOCKING=0；benchmark用NumPy计算clip(round(x/scale)+offset,-128,127)，offset长度为0时省略加法，最后转INT8。这个分支是参考代码行为，实际普通用例并未覆盖空offset。主线先把x/scale转FP32再转NumPy，发布直接转NumPy，不能据此声称两版参考精度路径完全相同。

两版普通样例均使用x[1,16,16] FP16、scale/offset[16,16]、offset INT8、y[1,16,16] INT8，再比较参考输出。主线用确定性的0..31量化值配合循环scale[0.25,0.5,1,2]和offset[-10,9]构造输入；发布seed=6后随机x/scale/offset。它们为每通道Tensor参数提供具体参考，没有证明任意广播、零scale或未列dtype可用。

两版aclgraph样例先Eager算y，再在新Stream中capture相同全1输入到y1，capture_end后replay并比较y1与y；没有变更输入地址/shape或更新task的步骤。主线另有9维CPU scale异常用例，期待“ATB tensor supports at most 8 dimensions, but got 9”；发布没有此用例，且公共Common.cpp的MAX_DIM显式检查也只在主线出现。这是固定源码差异，不是发布设备能力结论。

采用时分别保存量化输入的dtype/shape、实际scale/offset、eps、输出对象和版本，再检查数据准备、Setup、工作区与数值。测试中的环境设置、捕获比较和设备标注均为原始测试设计；当前卡没有运行结果或性能收益断言。

## 固定证据

- [来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/QuantRmsNormAtb.cpp)（primary）：1–58。
- [来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/QuantPerTensorAtb.cpp)（implementation）：1–55。
- [来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/infer_op_params.h)（constraint）：46–68、105–223、671–745。
- [来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h)（implementation）：62–87、142–148。
- [来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test__npu_quant_rms_norm.py)（example）：1–60。
- [来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_atb_quant_per_tensor.py)（example）：1–73。
- [来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_ops.py)（implementation）：11–30、103–132。
- [来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/QuantRmsNormAtb.cpp)（implementation）：1–64。
- [来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/QuantPerTensorAtb.cpp)（implementation）：1–57。
- [来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/infer_op_params.h)（constraint）：49–71、108–225、670–744。
- [来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h)（implementation）：63–89、149–156。
- [来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test__npu_quant_rms_norm.py)（example）：1–60。
- [来源 13](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_atb_quant_per_tensor.py)（example）：1–63。
- [来源 14](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_ops.py)（implementation）：11–27、102–131。
