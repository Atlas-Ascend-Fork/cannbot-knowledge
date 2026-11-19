---
type: API
title: TorchNPU OpCommand：输入输出描述、属性与执行同步
description: 整理链式OpCommand成员和输入转换差异，区分Sync索引配置与立即流同步。
tags:
- task.implementation
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）class-at_npu-native-OpCommand.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）class-at_npu-native-OpCommand.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)class-at_npu-native-OpCommand.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpCommand.cpp
  role: implementation
created_at: '2026-11-09T18:55:54Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# TorchNPU OpCommand：输入输出描述、属性与执行同步

## 固定版本与产品范围

依据OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda及发布提交dedc316708372c9a8bfde4527abd2a94b74840f5的C++接口页，核对发布中文、主线中文和主线英文。以下A2/A3仅指训练系列；来源另列的旧Atlas训练/推理产品保留其原名，不据名称自动合并到新型号。多数beta页未列950，不等于明确不支持，也不能据整体TorchNPU支持950补入本卡。

发布配对PyTorch提交为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；文档与实现分开标注，不把两个仓库的独立主线视为已配套。本文是静态契约审阅，未编译、加载库或执行NPU；beta是上游接口身份，stable是知识卡审核状态。


## 类型与基础入口

`at_npu::native::OpCommand`定义于`torch_npu/csrc/framework/OpCommand.h`，封装底层算子调用，含构造/析构。Name设置算子名、SetCustomHandler设置PROC_FUNC、DynamicInputReg设置动态输入注册函数及数量/索引、Expect接收UnifiedResult的类型/形状/defined信息；这些准备步骤不证明后端算子已注册或支持所有输入。

## 输入、输出和属性成员

|入口族|契约与易混点|
|--|--|
|`Input()`|追加空输入。|
|`Input(const Tensor&, descName="", optional aclFormat=nullopt, realData="")`|常规Tensor输入，涉及contiguous处理；格式/真实数据描述参数各有用途。|
|`InputWithoutContiguous(const Tensor&, descName="", realData="")`|避免该入口的连续化处理；不证明任意底层算子支持非连续stride。|
|ArrayRef/IntArrayRef/浮点数组Input重载|输入数组及realShape、toType、CompileType、realDtype和descName等信息；IntArrayRef默认kLong，浮点数组默认kDouble，数组编译依赖默认MEMORY_HOST_COMPILE_DEPENDENT。|
|Scalar Input重载|给出Scalar和目标类型，编译依赖默认MEMORY_HOST_COMPILE_INDEPENDENT，不能与数组默认值混用。|
|`Inputs(TensorList)`|添加一组Tensor。|
|`InputScalarToNPUTensor(scalar, type)`|将标量按类型作为NPU Tensor输入；不能据入口名假定无分配/无拷贝。|
|`Output(Tensor&, descName="", optional format=nullopt, realType="")`|登记输出引用与描述；调用者仍须保证输出形状/类型和寿命。|
|`Attr(name,value)`、`Attr(name,value,cond)`|登记属性，后者cond=false不加入该属性；不是自动提供后端默认值的证明。|
|`Run()`|返回void，执行已准备命令；准备函数的链式返回与Run返回不同。|

多处说明简写返回OpCommand，原型实为`OpCommand&`；文档也有ArrayRef/optional模板参数显示不全，不能将不完整排版直接生成可编译声明。应使用实际版本头文件，不从相似重载猜测缺失模板。

## 两种Sync不相同

文档列`Sync(c10::SmallVector<int64_t,N>&)`及无参`Sync()`。发布配对cpp328–343行显示：前者保存sync_index，非空时设置sync标记，返回自身；后者当下取得当前NPU流并调用带超时的ACL流同步，返回自身。不能把带索引版本称为已经等待所有任务结束，也不能把无参版本说成仅设置稍后生效的标志。

Run的发布实现131–183行，在启用TaskQueue且不是同步流并且!sync时导出参数并入队；否则走直接运行分支并按阻塞选项同步。普通aclop路径会检查图捕获限制，不由OpCommand存在推导所有算子可捕获。只读到这些局部分支，不据此声明整个底层执行器、资源清理和所有错误路径已摄取。

## 框架调用与模型优化

输入连续化、标量转Tensor、数组描述和同步都会改变Host/Device开销；用真实消费者核对格式、类型、别名和异步资源寿命。自定义launch接入TaskQueue的API及回调边界另见[接入指南](../../guides/optimization/torch_npu/torch_npu_custom_op_taskqueue_adaptation.md)，不能把类文档当作Kernel/Host/Tiling生产工程教程。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/cpp/（beta）class-at_npu-native-OpCommand.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/cpp/（beta）class-at_npu-native-OpCommand.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/cpp/(beta)class-at_npu-native-OpCommand.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpCommand.cpp)（implementation）
