---
type: API
title: Silu
description: 按元素做Silu激活运算，支持half和float数据类型，不支持源操作数与目的操作数地址重叠。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/Silu_interface/Silu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Silu

按元素做Silu运算，计算公式如下：

函数原型：
template <typename T, bool isReuseSource = false>
__aicore__ inline void Silu(const LocalTensor<T>& dstLocal, const LocalTensor<T>& srcLocal, uint32_t dataSize)

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- isReuseSource：是否允许修改源操作数。该参数预留，传入默认值false即可。
- dstLocal（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- srcLocal（输入）：源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 源操作数的数据类型需要与目的操作数保持一致。
- dataSize（输入）：实际计算数据元素个数。

约束：
- 操作数地址偏移对齐要求请参见通用说明和约束。
- 不支持源操作数与目的操作数地址重叠。
- 当前仅支持ND格式的输入，不支持其他格式。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Kirin X90、Kirin 9030。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetSiluTmpSize](get_silu_tmp_size.md)（`related`）：“用于获取Silu Tiling参数：Silu接口能完成计算所需最大临时空间大小和最小临时空间大小。”说明 Host 侧空间计算直接服务 Silu；“函数原型： template <typename T, bool isReuseSource = false> __aicore__ inline void Silu(const LocalTensor<T>& dstLocal, const LocalTensor<T>& srcLocal, uint32_t dataSize)”给出消费该 Tiling 结果的 Kernel 计算接口。
<!-- cannbot:related:end -->
