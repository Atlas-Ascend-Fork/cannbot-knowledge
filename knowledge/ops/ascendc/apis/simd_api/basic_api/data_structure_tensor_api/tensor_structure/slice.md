---
type: API
title: Slice（基础API）
description: 需要包含的头文件为：#include "tensor_api/tensor.h"。 Slice用于从张量指定坐标处切出一个子张量。根据输入的起始坐标coord和切片描述信息info，计算新的起始存储位置，并构造对应的子张量，子张量保持与原张量相同的存储位置类型。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/tensor_structure/Slice.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Slice（基础API）

从张量指定坐标处切出子张量。根据起始坐标 coord 和切片描述信息 info 计算新起始位置，构造子张量，保持与原张量相同的存储位置类型。头文件 `tensor_api/tensor.h`。仅 950 支持。

<!-- cannbot:related:start -->
## 相关

- [ACLNN 561000 非连续张量需 AutoContiguous](../../../../../runbooks/compilation/aclnn_561000_autocontiguous.md)（`exemplifies`）：ACLNN 561000 非连续张量需 AutoContiguous 与《Slice（基础API）》的实质衔接是：561000 来自 OpParamDef 未声明连续性策略；AutoContiguous/IgnoreContiguous、Input/OpDef 和非连续 Load/Store/Slice/Transpose 卡共同决定转换还是保留 strides。
- [DataCopy尾chunk非32B对齐触发ERR99999](../../../../../runbooks/compilation/datacopy_chunk_32b_err99999.md)（`exemplifies`）：《DataCopy尾chunk非32B对齐触发ERR99999》说明Ascend C DataCopy 在 UB↔GM 方向要求 count*sizeof(T) 为 32 字节对齐，否则搬运量对 32B 向下取整。当纯搬运算子尾 chunk 的实际元素数不满足 32B 对齐时，UB→GM 写方向触发 ERR99999、GM→UB 读方向静默丢尾部数据。判别方法：尾部元素数*sizeof(T)%32!=0 即命中。；《Slice（基础API）》说明需要包含的头文件为：#include "tensor_api/tensor.h"。 Slice用于从张量指定坐标处切出一个子张量。根据输入的起始坐标coord和切片描述信息info，计算新的起始存储位置，并构造对应的子张量，子张量保持与原张量相同的存储位置类型。。二者在DataCopy尾chunk错误由有效字节数非32B倍数触发，DataCopyPad的逐行、stride、padding和最小DMA卡给出修复边界上存在可执行的直接衔接。
- [SwiGLU 高级 API 在非32B对齐 slice 上精度失败](../../../../../runbooks/precision/swiglu_adv_api_fails_non_32b_aligned_slice.md)（`exemplifies`）：Slice（基础API） 与《SwiGLU 高级 API 在非32B对齐 slice 上精度失败》的实质衔接是：Slice 根据 coord 和 layout 计算子张量基址且保留存储位置；Tensor/ViewEngine 负责视图构造，非连续及非 32B 对齐案例直接约束后续高阶 API 和 DMA 使用。
- [多块 DataCopyPad dst 基址非 32B 对齐崩溃](../../../../../runbooks/compilation/datacopypad_dst_32b.md)（`exemplifies`）：Slice（基础API） 与《多块 DataCopyPad dst 基址非 32B 对齐崩溃》的实质衔接是：Slice 根据 coord 和 layout 计算子张量基址且保留存储位置；Tensor/ViewEngine 负责视图构造，非连续及非 32B 对齐案例直接约束后续高阶 API 和 DMA 使用。
- [跨 slice 批量 vector 源地址非 32B 对齐触发 507035](../../../../../runbooks/compilation/slice_vector_32b_507035.md)（`exemplifies`）：Slice（基础API） 与《跨 slice 批量 vector 源地址非 32B 对齐触发 507035》的实质衔接是：Slice 根据 coord 和 layout 计算子张量基址且保留存储位置；Tensor/ViewEngine 负责视图构造，非连续及非 32B 对齐案例直接约束后续高阶 API 和 DMA 使用。
- [Pointer（基础API）](pointer.md)（`related`）：Slice 基于 Pointer 偏移生成子视图，地址空间和生命周期仍继承原指针。
- [Tensor数据结构](tensor_structure.md)（`related`）：Slice 从 Tensor 生成共享存储的子视图，继承 Pointer 生命周期。
- [Coord（基础API）](../layout_structure/coord.md)（`same_topic`）：焦点处理Coord 参与 Layout 坐标映射和 Tensor Slice 的用法；Slice（基础API）正文说明“需要包含的头文件为：#include "tensor_api/tensor.h"。 Slice用于从张量指定坐标处切出一个子张量。根据输入的起始坐标coord和切片描述信息info，计算新的起始存储位置，并构造对应的子张量，子张量保持与原张量相同的存储位置类型”。候选把 Coord 构造、Layout 映射、Crd2Idx 与 Slice 的正文调用关系展开。
- [Layout](../layout_structure/layout.md)（`same_topic`）：Slice（基础API） 与《Layout》的实质衔接是：Slice 根据 coord 和 layout 计算子张量基址且保留存储位置；Tensor/ViewEngine 负责视图构造，非连续及非 32B 对齐案例直接约束后续高阶 API 和 DMA 使用。
- [MakeCoord](../layout_structure/make_coord.md)（`same_topic`）：Slice（基础API） 与《MakeCoord》的实质衔接是：Slice 根据 coord 和 layout 计算子张量基址且保留存储位置；Tensor/ViewEngine 负责视图构造，非连续及非 32B 对齐案例直接约束后续高阶 API 和 DMA 使用。
- [MakeTensor](make_tensor.md)（`same_topic`）：Slice（基础API） 与《MakeTensor》的实质衔接是：Slice 根据 coord 和 layout 计算子张量基址且保留存储位置；Tensor/ViewEngine 负责视图构造，非连续及非 32B 对齐案例直接约束后续高阶 API 和 DMA 使用。
- [Tensor](tensor.md)（`same_topic`）：Slice（基础API） 与《Tensor》的实质衔接是：Slice 根据 coord 和 layout 计算子张量基址且保留存储位置；Tensor/ViewEngine 负责视图构造，非连续及非 32B 对齐案例直接约束后续高阶 API 和 DMA 使用。
- [ViewEngine](view_engine.md)（`same_topic`）：ViewEngine 与《Slice（基础API）》的实质衔接是：ViewEngine 持有 Iterator，并与 Layout 组成 Tensor 视图；MakeMemPtr/MakeTensor、Slice 和 shape/stride 查询共同决定 Begin 指向的物理位置。
<!-- cannbot:related:end -->
