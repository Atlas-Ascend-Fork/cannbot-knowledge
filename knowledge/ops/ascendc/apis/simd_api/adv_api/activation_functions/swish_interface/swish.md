---
type: API
title: Swish
description: 神经网络中的Swish激活函数，按元素计算，支持通过beta参数控制函数形状，支持half和float数据类型。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/Swish_interface/Swish.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Swish

在神经网络中，Swish是一个重要的激活函数。计算公式如下，其中β为常数：

函数原型：
template <typename T, bool isReuseSource = false>
__aicore__ inline void Swish(const LocalTensor<T>& dstLocal, const LocalTensor<T>& srcLocal, uint32_t dataSize, const T scalarValue)

参数：
- T：操作数的数据类型。支持的数据类型为：half、float。
- isReuseSource：是否允许修改源操作数。该参数预留，传入默认值false即可。
- dstLocal（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- srcLocal（输入）：源操作数。 源操作数的数据类型需要与目的操作数保持一致。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- dataSize（输入）：实际计算数据元素个数。

约束：
- 操作数地址偏移对齐要求请参见通用说明和约束。
- 不支持源操作数与目的操作数地址重叠。
- 当前仅支持ND格式的输入，不支持其他格式。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [Sigmoid](../sigmoid_interface/sigmoid.md)（`related`）：Swish 与《Sigmoid》的实质衔接是：Swish kernel 与临时空间查询直接配套；SiLU 是 beta=1 的同公式变体，Sigmoid 是门控项。
- [GetSwishTmpSize](get_swish_tmp_size.md)（`same_topic`）：Swish 与《GetSwishTmpSize》的实质衔接是：Swish kernel 与临时空间查询直接配套；SiLU 是 beta=1 的同公式变体，Sigmoid 是门控项。
- [Silu](../silu_interface/silu.md)（`same_topic`）：Swish 与《Silu》的实质衔接是：Swish kernel 与临时空间查询直接配套；SiLU 是 beta=1 的同公式变体，Sigmoid 是门控项。
- [Swish接口](swish_interface.md)（`same_topic`）：Swish 与《Swish接口》的实质衔接是：Swish kernel 与临时空间查询直接配套；SiLU 是 beta=1 的同公式变体，Sigmoid 是门控项。
<!-- cannbot:related:end -->
