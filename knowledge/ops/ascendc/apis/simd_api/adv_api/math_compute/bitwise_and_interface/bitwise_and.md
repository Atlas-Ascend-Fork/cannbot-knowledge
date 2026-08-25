---
type: API
title: BitwiseAnd
description: 逐比特对两个输入进行与操作。 !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/BitwiseAnd_interface/BitwiseAnd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# BitwiseAnd

逐比特对两个输入进行与操作。

函数原型：
template <const BitwiseAndConfig& config = DEFAULT_BITWISE_AND_CONFIG, typename T>
__aicore__ inline void BitwiseAnd(const LocalTensor<T>& dst, const LocalTensor<T>& src0, const LocalTensor<T>& src1, const uint32_t count)

参数：
- config：BitwiseAnd算法的相关配置。此参数可选配，BitwiseAndConfig类型，具体定义如下方代码所示，其中参数的含义为： isReuseSource：该参数预留，传入默认值false即可。
- T：操作数的数据类型。支持的数据类型为：int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t、int64_t、uint64_t。
- dst（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- src0、src1（输入）：源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 源操作数的数据类型与目的操作数保持一致。
- count（输入）：参与计算的元素个数。

约束：
- 不支持源操作数与目的操作数地址重叠。
- 操作数地址对齐要求请参见通用地址对齐约束。

支持：Ascend 950PR/Ascend 950DT。不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetBitwiseAndMaxMinTmpSize](get_bitwise_and_max_min_tmp_size.md)（`related`）：该 Host 查询产生的空间下界和上界直接约束 Kernel BitwiseAnd 的 sharedTmpBuffer。
- [GetBitwiseAndTmpBufferFactorSize](get_bitwise_and_tmp_buffer_factor_size.md)（`related`）：本卡返回 maxLivedNodeCount/extraBuf 以推算 BitwiseAnd 单次处理量，BitwiseAnd 正文定义实际逐比特计算；前者的结果直接决定后者在固定 workspace 下的分块。
- [LogicalAnd](../logical_and_interface/logical_and.md)（`related`）：BitwiseAnd 对整数每一 bit 做与，LogicalAnd 把零/非零解释为布尔值；两者同名易混但语义不同，按需要位运算还是真值运算选型。
- [BitwiseAnd接口](bitwise_and_interface.md)（`same_topic`）：接口总览定义的 dtype、地址和临时空间契约由 BitwiseAnd 计算调用直接实现。
<!-- cannbot:related:end -->
