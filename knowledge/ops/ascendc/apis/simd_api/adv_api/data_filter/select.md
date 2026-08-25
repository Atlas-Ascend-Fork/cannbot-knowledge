---
type: API
title: Select
description: 根据maskTensor值在两个源操作数间按元素选取，mask为0取src0否则取src1
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/data_filter/Select.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Select

给定两个源操作数src0和src1，根据maskTensor相应位置的值（非bit位）选取元素，得到目的操作数dst。选择的规则为：当Mask的值为0时，从src0中选取，否则从src1选取。 该接口支持多维Shape，需满足maskTensor和源操作数Tensor的前轴（非尾轴）元素个数相同，且maskTensor尾轴元素个数大于等于源操作数尾轴元素个数，maskTensor多余部分丢弃不参与计算。 - maskTensor尾轴需32字节对齐且元素个数为16的倍数。

函数原型：
template <typename T, typename U, bool isReuseMask = true>
__aicore__ inline void Select(const LocalTensor<T>& dst, const LocalTensor<T>& src0, T src1, const LocalTensor<U>& mask, const LocalTensor<uint8_t>& sharedTmpBuffer, const SelectWithBytesMaskShapeInfo& info)

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- U：掩码Tensor mask的数据类型。支持的数据类型为：bool、int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t。
- isReuseMask：是否允许修改maskTensor。默认为true。 取值为true时，仅在maskTensor尾轴元素个数和srcTensor尾轴元素个数不同的情况下，maskTensor可能会被修改；其余场景，maskTensor不会修改。 取值为false时，任意场景下，maskTensor均不会修改，但可能会需要更多的临时空间。
- dst（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- src0(srcTensor) src1(srcTensor)（输入）：源操作数。源操作数Tensor尾轴需32字节对齐。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。

约束：
- 源操作数与目的操作数可以复用。
- 操作数地址对齐要求请参见通用地址对齐约束。
- maskTensor尾轴元素个数和源操作数尾轴元素个数不同的情况下， maskTensor的数据有可能被接口改写。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GE图模式263: 自定义VF Select被禁](../../../../runbooks/compilation/ge_263_vf_select.md)（`exemplifies`）：正式 Select 接口页给出支持模式和参数约束，可验证 VF 调用是否落在文档契约内。
- [Select](../../basic_api/memory_vector_compute/compare_and_select/select.md)（`related`）：基础 Select 提供更底层的 UB 选择路径，并具有不同的 mask 模式和尾块约束，适合在高阶接口之外做实现选型。
- [Select](../../basic_api/reg_vector_compute/compare_and_select/select.md)（`related`）：Reg Select 将条件选择留在寄存器链中，补充高阶 Tensor Select 之外避免中间 UB 往返的实现路线。
- [GetSelectMaxMinTmpSize](get_select_max_min_tmp_size.md)（`same_topic`）：该 Host 接口给出高阶 Select 执行所需 workspace 上下界，是调用 Select 前完成 Tiling 资源分配的直接配套契约。
<!-- cannbot:related:end -->
