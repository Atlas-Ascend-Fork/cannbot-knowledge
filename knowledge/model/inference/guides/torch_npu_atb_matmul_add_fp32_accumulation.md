---
type: Guide
title: ATB矩阵累加：转置配置、FP32 C与输入连续化
description: 沿MatmulAddFP32核对固定转置和无bias累加、C输入输出别名、厂商局部条件及非连续矩阵测试的范围。
tags:
- task.optimization
- topic.memory
- topic.data_movement
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/LinearAtb.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/infer_op_params.h
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_atb_linear.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/LinearAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/infer_op_params.h
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_atb_linear.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_ops.py
  role: implementation
created_at: '2026-11-11T03:47:18Z'
updated_at: '2026-11-11T03:47:18Z'
platforms: []
---

# ATB矩阵累加：转置配置、FP32 C与输入连续化

两版固定提交分别为主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`与发布`dedc316708372c9a8bfde4527abd2a94b74840f5`。下述CPP完整非注释token已逐对比较相同；测试只作静态参考，未导入或运行上游、加载ATB库或做设备测试。平台配套未完整确认，整卡保持draft与空平台，没有新增verified。

公共ParamSetter的contiguous、按请求转换ND、CPU clone、输出连续性检查，以及每次Setup、自动工作区、捕获分派和资源寿命复用[ATB执行生命周期](torch_npu_atb_paged_attention_execution_lifecycle.md)。Input的format_trans=True表示请求，是否发生物理转换取决于实际Tensor；Output直接描述调用方对象。

## 固定Matmul累加配置

LinearAtb.cpp的准确入口为`atb::_npu_matmul_add_fp32`，注册PrivateUse1，schema接收x、weight和可写Tensor(a!) C，返回()。它以x建立OptionalDeviceGuard，从OpParamCache<LinearParam>取LinearOperation，参数固定transposeA=True、transposeB=False、hasBias=False、enAccum=True，outDataType保留头默认ACL_DT_UNDEFINED。

固定LinearParam头说明ACL_DT_UNDEFINED为浮点场景，enAccum只在Atlas 800I A2推理产品支持True，不能与hasBias=True或量化场景同时启用。入口实际选择无bias浮点累加；头里其它量化输出dtype、transpose限制有各自量化前提，不自动应用为本入口的额外dtype承诺。整卡仍未确认完整配套平台。

VariantPack顺序为Input(x)、Input(weight)、Input(C)、Output(C)，三个输入format_trans均默认False。C同时作为累加输入和直接输出，不是新结果分配，也不是bias Tensor。结合transposeA=True/transposeB=False，所选测试对应x.T @ weight + 原C；计算前后仍必须满足转置后的矩阵维数和C输出形状。函数名里的fp32不代替dtype校验：本地没有显式检查x/weight/C类型或shape，不应由名称推广为任意混合精度组合可用。

该类型没有独立HashOpParam字段特化，固定属性沿默认空hash模板；类型化缓存与每次Setup遵循公共生命周期。这不缓存输入数据，也不把C的旧值省略。Python API_LIST与转发/补丁把此准确名字绑定torch_npu._npu_matmul_add_fp32。

## 测试形状、输入连续化与比较路径

两版test_atb_linear.py完整AST相同。普通用例x和weight均[4096,8192] FP16，C为[8192,8192] FP32；先在设备侧执行torch.mm(x.T,weight)，再加原C作为参考，然后调用ATB原地更新C，把C加到初始全0 FP32 atb_res后比较，绝对/相对容差均0.001。这是测试指定的参考计算顺序，不是CPU FP32高精度matmul证明。

uncontiguous用例把x/weight底层shape扩为[4096,16384]后切片[:,::2]，逻辑shape仍[4096,8192]，C仍连续FP32。它只对两个只读矩阵的非连续输入作设计覆盖；公共Input会contiguous准备它们，Output(C)则直接检查C连续性。因此不能从该用例推出非连续C可写回，或推导无拷贝性能收益。

两个测试均标注SupportedDevices(Ascend910B)，仅检查上述正向数值比较，没有capture/replay、任务更新、其它dtype、梯度或性能计时。本次只读源码与AST，未运行这些大矩阵测试、导入torch_npu或加载动态库。采用时保存输入stride、转置后的维度、C原值和输出别名，区分输入整理时间、ATB Setup/执行和参考精度路径。

## 固定证据

- [来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/LinearAtb.cpp)（primary）：1–52。
- [来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/infer_op_params.h)（constraint）：226–290。
- [来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h)（implementation）：62–79、142–148。
- [来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_atb_linear.py)（example）：1–39。
- [来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_ops.py)（implementation）：11–30、103–132。
- [来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/LinearAtb.cpp)（implementation）：1–58。
- [来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/infer_op_params.h)（constraint）：228–291。
- [来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h)（implementation）：63–80、149–156。
- [来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_atb_linear.py)（example）：1–39。
- [来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_ops.py)（implementation）：11–27、102–131。
