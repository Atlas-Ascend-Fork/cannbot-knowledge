---
type: API
title: DropOut
description: 根据MaskTensor对SrcTensor进行过滤，支持字节模式和比特模式两种过滤方式
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/data_filter/DropOut.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# DropOut

提供根据MaskTensor对SrcTensor（源操作数，输入Tensor）进行过滤的功能，得到DstTensor（目的操作数、输出Tensor）。仅支持输入shape为ND格式。 该过滤功能包括两种模式，字节模式和比特模式。 - 字节模式

函数原型：
template <typename T, bool isInitBitMode = false, uint32_t dropOutMode = 0>
__aicore__ inline void DropOut(const LocalTensor<T>& dstLocal, const LocalTensor<T>& srcLocal, const LocalTensor<uint8_t>& maskLocal, const float keepProb, const DropOutShapeInfo& info)

参数：
- T：操作数的数据类型。不同型号支持的数据类型请参考[支持的数据类型](#li15391852101816)。
- isInitBitMode：在比特模式下，是否需要在接口内部初始化（默认false）。
- dropOutMode：选择执行何种输入场景： 0：默认值，由接口根据输入shape推断运行模式，注意，推断不符合预期的场景，需设置对应模式 1：执行字节模式，且maskLocal含有脏数据 2：执行字节模式，且maskLocal不含有脏数据 3：执行比特模式，且maskLocal不含有脏数据 4：执行比特模式，且maskLocal含有脏数据
- dstLocal（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- srcLocal（输入）：源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 srcLocal的数据类型需要与目的操作数保持一致。

约束：
- srcTensor和dstTensor的Tensor空间可以复用。
- srcLocal和dstLocal地址对齐要求请见：通用说明和约束。
- 仅支持输入shape为ND格式。
- maskLocal含有脏数据的场景，要求info.maskLastAxis中有效数值的个数，应为2的整数倍。
- maskLocal含有脏数据的场景，maskLocal中的数据可能会被修改，脏数据可能会被舍弃。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Kirin X90、Kirin 9030。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetDropOutMaxMinTmpSize](get_drop_out_max_min_tmp_size.md)（`same_topic`）：GetDropOutMaxMinTmpSize 与《DropOut》的实质衔接是：GetDropOutMaxMinTmpSize 给 DropOut kernel 分配可用临时空间，两者必须以相同 shape/type 契约调用。
<!-- cannbot:related:end -->
