---
type: Guide
title: FXRT IR数据模型与TorchCall/符号算子：Schema别名ref对与防双释放
description: 记录FXRT C++ IR的Storage/view双形状与FRACTAL_NZ格式、OpTorchCall从torch schema别名注解推导ref对并拒绝未声明别名、custom_call名称偏移平移、CPU符号推形算子族，以及仅注册样例Pass的PassManager边界。
tags:
- task.implementation
- topic.memory
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ir/common/dtype.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ir/common/intrusive_ptr.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ir/symbolic/symbolic.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ir/symbolic/symbolic.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ir/tensor/format.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ir/tensor/storage.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ir/tensor/storage.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ir/tensor/tensor.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ir/tensor/tensor.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ir/value/value.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ir/value/value.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_torch_call.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_torch_call.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_custom_call.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_custom_call.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_eval_symbolic_expr.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_eval_symbolic_expr.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_matmul.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_matmul.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_mul.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_mul.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/cpu/aten/aten_custom_call.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/cpu/aten/aten_custom_call.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/cpu/aten/op_python_call.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/cpu/aten/op_python_call.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/cpu/cpu_custom_operator.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/cpu/symbolic/binary_op.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/cpu/symbolic/binary_op.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/cpu/symbolic/broadcast_shape.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/cpu/symbolic/broadcast_shape.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/cpu/symbolic/size.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/cpu/symbolic/size.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/cpu/symbolic/eval_symbolic_expr.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/optimize/pass/pass.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/optimize/pass/pass.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/optimize/pass/ud.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/utils/gil_scoped.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/utils/shape_key_utils.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/profiler/profiler.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/profiler/profiler.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/common/logger.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/common/logger.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/common/visible.h
  role: implementation
created_at: '2026-11-13T04:14:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# FXRT IR数据模型与TorchCall/符号算子：Schema别名ref对与防双释放

## 固定来源与范围

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的FXRT C++ IR数据模型（src/ir）、op_base的TorchCall/custom_call/符号算子、CPU符号推形算子、PassManager框架与profiler/logger等基础件。静态阅读，未运行；整卡draft、platforms为空。Python侧ir.py与graph.h/cpp的图结构已由[FXRT推理运行时](torch_npu_fxrt_runtime.md)承载，本卡补C++侧数据模型与算子基类。

## IR Tensor的Storage/view双形状与格式

`ir::Tensor`持有view Shape/Strides/StorageOffset与底层Storage（含StorageShape与数据指针）双层元数据：view层描述逻辑视图，storage层描述物理占用。这个双形状结构是多个机制的基础：aclnn执行器哈希同时哈希两层形状（见[执行器缓存](torch_npu_fxrt_aclnn_executor_cache_and_op_registry.md)）、NZ权重的存储形状换算（见[特例算子](torch_npu_fxrt_quant_moe_fused_specialized_ops.md)）、view算子的UpdateTensorViewInfo（见[view零拷贝](torch_npu_fxrt_view_zero_copy_and_metadata_ops.md)）。format.h定义MemoryFormat枚举（ND/NCHW/NHWC/NC1HWC0/FRACTAL_Z/FRACTAL_NZ等），dtype.h定义IR dtype（含QInt8/QUInt4x2等量化类型）。Storage带引用计数（intrusive_ptr），Tensor浅共享Storage即构成别名。**判断“两个Tensor是否同一块内存”在FXRT里是Storage指针相等，不是data_ptr+offset相等**；带偏移的view与基础Tensor可能data_ptr不同但共享Storage。

## OpTorchCall：schema别名推导ref对，未声明别名即拒绝

`OpTorchCall`把调用转发给torch dispatcher（`aten.add`→`aten::add`）：Init时匹配torch.jit.Operator schema（MatchOpSchema），按schema的alias_info把“view输出别名某输入”与“inplace写别名输入”都记入refPairs_——运行时据此建立零拷贝别名（Builder的ref输出指向输入Storage），而不是每个输出各占一份设备指针。两个防御性边界：**用户自定义算子（torch.library.custom_op）没有alias注解时refPairs_为空，运行时退回执行期检测共享Storage**；**schema声明了alias却找不到可匹配输入时直接异常，不猜一个可能错误的ref关系**。`ToFxrtTensor`还记录输入Storage基地址集合：ref/view输出必须真的落在某输入Storage上；普通算子结果意外复用输入Storage（未声明别名的ref）会在接管所有权前被拒绝——**否则同一设备内存会被两个owner各释放一次（double free）**。输入转换用静态跳表按Value类型O(1)分发，首次运行后缓存converter。

## OpCustomCall的名称偏移平移

custom_call节点输入[0]是`ns.op_name`字符串，真实数据从[1]开始。`OpCustomCall::Init`先从CustomOpRegistry按短名创建，找不到（torch前端启用时）退回`OpTorchCall`；它把内层算子的ref对整体平移+1（op名占位），使运行时在custom_call节点输入上仍能对齐别名。InferShape/CalcWorkspace/Launch全部转发内层算子。**内层算子的“输入下标”与runtime看到的“节点输入下标”相差1**——排查别名/输入计数问题时先确认在哪个坐标系。

## 符号推形算子族与op_base基础算子

`op_eval_symbolic_expr`（op_base）与CPU侧`broadcast_shape`、`binary_op`、`size`构成符号shape运行时：`OpEvalSymbolicExpr`把操作数写入symVars后延迟求值symExpr，NeedLaunch=false；broadcast_shape按Sympy式广播规则推导符号形状。这些是前端SymbolicShapeManager（见[前端降级](torch_npu_fxrt_frontend_lowering.md)）编译期符号的运行时对应物。`op_matmul`只做二维[M,N]推形，`op_mul`/`op_shape`为简单基类实现。CPU aten目录的aten_custom_call/op_python_call是7–16行的转发stub，`cpu_custom_operator.h`提供CPU自定义算子基类。

## PassManager：框架在，样例Pass也在，但没有生产Pass

`optimize/pass`提供NodePass（Match/Replacement）+PassManager+UserDef（use-def链，含OrderedNodes维护图的执行序）框架与DA_REGISTER_PASS宏。**当前源码树里唯一注册的是"ManualSamplePass"样例**；Python入口的opt_graph调用被注释（见运行时卡）。因此“FXRT会自动跑C++图优化Pass”在当前提交不成立：框架存在≠有生产Pass在跑；新增Pass须自行注册并验证OrderedNodes顺序保持。profiler提供Python/Infer/RunGraph/RunOp/MemoryAlloc/MemoryFree/CopyData/StreamSync等stage与event枚举、JSON输出（nlohmann），logger提供VL_RUNTIME/VL_OPS等多级RT_VLOG与环境控制的日志过滤。`shape_key_utils.h`的`GenerateShapeKey`把图输入（为空时回退parameters）经VisitAllTensors把所有尺寸用"-"连接——**与运行时卡记录的ShapeKey一样无Tensor边界/rank/dtype**，同样的键碰撞边界适用于此实现。`GilReleaseWithCheck`在持有GIL时才释放（nanobind gil_scoped_release），供C++执行段避免死锁。

## 边界与验证方式

本卡未运行任何OpTorchCall/schema匹配路径：别名推导、double-free拒绝、ref对平移都应按实际模型核对（用带view/inplace输出的算子组合检查输出是否零拷贝、Storage计数是否单-owner）。QInt8/QUInt4x2在dtype枚举存在不表示设备算子已支持。PassManager空转结论仅对当前提交成立。验证时用schema带alias与不带alias的自定义算子各测一次，确认未声明别名时走执行期检测而非错误接管。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_torch_call.h)（primary）：全文件122行。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_custom_call.cpp)（implementation）：全文件74行。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ir/tensor/tensor.h)（implementation）：定向范围1–120。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ir/tensor/storage.h)（implementation）：定向范围1–100。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ir/common/dtype.h)（implementation）：定向范围1–80。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_eval_symbolic_expr.cpp)（implementation）：全文件47行。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/cpu/symbolic/broadcast_shape.cpp)（implementation）：全文件104行。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/optimize/pass/pass.cpp)（implementation）：定向范围160–173（样例Pass注册）。
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/utils/shape_key_utils.h)（implementation）：全文件54行。
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/profiler/profiler.h)（implementation）：定向范围1–70。
