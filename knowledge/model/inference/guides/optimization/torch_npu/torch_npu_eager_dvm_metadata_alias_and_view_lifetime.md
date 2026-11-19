---
type: Guide
title: Eager DVM融合的Tensor复用与别名边界
description: 解释Storage上的融合值、Tensor与逻辑shape精确匹配、读写前flush、View输入存活及输出Store选择。
tags:
- task.optimization
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_kernel.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_kernel.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_ops.cpp
  role: implementation
created_at: '2026-11-11T02:59:24Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Eager DVM融合的Tensor复用与别名边界

## 固定来源与入口

本卡静态审阅OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`的Eager lazy-fusion实现。整卡产品矩阵与发布配套待核，状态为draft、平台为空。本次只读取源码，运行数值和性能验收待执行。公开环境与线程使用条件见[Eager DVM融合](torch_npu_eager_lazy_fusion.md)。

## 复用同时检查Tensor身份与逻辑shape

TransType将Bool、Int、Half、Float和BFloat16分别映射为DVM的Bool、Int32、Float16、Float32和BFloat16，其他类型返回kDataTypeEnd。各handler在此映射之外继续执行自己的dtype准入。

每个NPU Storage的lazy_fusion_data_指向当前登记的DvmOp。MatchTensorMeta比较TensorImpl、data_ptr、storage_offset、dtype、rank、sizes和strides。MatchDvmShape另外比较是否提供shape override，以及提供时的逻辑shape。MatchDvmOp要求两项同时成立。共享Storage、元素数相同或物理sizes相同都不足以独立判定命中。

Input命中后复用已有NDObject。输入Load登记reloadable_from_gm=True，融合输出登记False。读取前的NeedFlushForInput对非reloadable对象发生精确匹配失败时请求flush。Input内部再次遇到此类失配会触发内部断言，因此PrepareFusionInput应在当前算子修改DVM图之前调用。

Input新建Load时实际以`&load->shape`登记DvmOp，即使这次Input原始shape参数为空。按所读MatchDvmShape条件，之后以空shape请求时，其override存在性与该记录不同。采用时应依据这条调用链判断缓存复用范围，形状注释与日志名称只提供定位线索。

## 写目标和View输入

PrepareWritableOutput在已有Storage融合值与写目标元数据或逻辑shape不匹配时先提交待融合图。所选Add消费者先处理可写目标和内存重叠检查，再PrepareFusionInputs，随后取得kernel并生成计算节点。这些准备顺序发生在Output登记之前。

ViewInput记录实际view的地址、尺寸、步幅及相对Storage字节地址计算的元素offset，同时强引用base Tensor。它还将该view元数据登记到base Storage，以便后续写入整块base时检测失配。普通Input对无shape override的非连续输入使用strided Load，显式override分支使用普通Load。

IsViewLoadable要求Tensor已定义、rank大于0、每维size为正、stride非负、末维stride为1且末维size不为1。所选InputCheck还要求NPU和允许的dtype，并在O2级别且调用方允许非连续输入时采用该条件。非连续Output也有对应断言。各handler仍有自己的额外门控。

## 输出写回和精度转换

Output先把计算对象转换到目标Tensor的dtype。inplace输出沿已登记Store逆序查找相同Tensor元数据，将最近匹配的旧Store置为skip，然后登记新Store。这里只消除该精确匹配的旧写回，任意重叠view仍须走前述准备检查。

Store持有Storage弱引用，Flush跳过已失效Storage和标记skip的Store。非连续输出使用其保存的strides生成strided Store，原地输出另设置StoreInplace。Load持有的强引用和Store的弱引用采用不同生命周期。

Input与ViewInput默认允许BF16入口转换。NeedBf16ToFp32Cast首次调用后缓存SocVersion是否不等于Ascend950的判断，对应Ascend950系列（包含旧称Atlas A5）的这一局部条件。所选Add handler仍明确将BF16公共计算类型设为FP32，因此应同时核对入口转换和后续handler显式Cast。该局部判断的产品含义保留在具体分支中。

## 采用验证

分别覆盖普通Tensor复用、兄弟view、逻辑广播shape变化、未物化融合结果的slice后复用和inplace覆盖。保存真实入口、融合边界、shape/stride、Storage身份与输出数值，观察flush次数与实际搬运。输出分配及TaskQueue提交顺序见[融合提交和工作区](torch_npu_eager_dvm_flush_workspace_and_allocation_reentry.md)。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_kernel.cpp)（primary），读取范围 1–792。
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_kernel.h)（implementation），读取范围 1–451。
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_ops.cpp)（implementation），读取范围 1–385。
