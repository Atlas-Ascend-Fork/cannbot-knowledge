---
type: API
title: GetDataBlockSizeInBytes
description: 获取当前芯片版本一个DataBlock的大小，单位为Byte。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetDataBlockSizeInBytes.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- '910'
- kirin_x90
- kirin_9030
source_headers:
- include/basic_api/kernel_operator_sys_var_intf.h
---

# GetDataBlockSizeInBytes

## 功能说明

头文件路径为：`"basic_api/kernel_operator_sys_var_intf.h"`。

获取当前芯片版本一个DataBlock的大小，单位为Byte。

开发者根据DataBlock的大小来计算API指令中待传入的[repeatTime、dstBlkStride、srcblkStride、dstRepStride、srcRepStride等参数值](../../memory_vector_compute/simd_compute/high_dim_split.md)。

## 函数原型

```cpp
__aicore__ inline constexpr int16_t GetDataBlockSizeInBytes()
```

## 参数说明

无

## 返回值说明

当前芯片版本一个DataBlock的大小，单位为Byte。

## 约束说明

无

## 调用示例

如下样例通过`GetDataBlockSizeInBytes`获取DataBlock的大小并计算`repeatTime`的值：

```cpp
int16_t dataBlockSize = AscendC::GetDataBlockSizeInBytes();
// 每个repeat有8个DataBlock,可计算8 * dataBlockSize / sizeof(half)个数，mask配置为迭代内所有元素均参与计算
uint64_t mask = 8 * dataBlockSize / sizeof(half);
// 共计算512个数，除以每个repeat参与计算的元素个数，得到repeatTime
uint8_t repeatTime = 512 / mask;
// dstBlkStride, src0BlkStride, src1BlkStride = 1,单次迭代内数据连续读取和写入
// dstRepStride, src0RepStride, src1RepStride = 8,相邻迭代间数据连续读取和写入
AscendC::Add(dstLocal, src0Local, src1Local, mask, repeatTime, { 1, 1, 1, 8, 8, 8 });
```


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [AddLayerNormQuant 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/norm/add_layer_norm_quant_950.md)（`related`）：算子声明的固定版本源码包含对 `GetDataBlockSizeInBytes(...)` 的直接调用（第 54 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/norm/add_layer_norm_quant/op_kernel/arch35/add_layer_norm_quant_regbase_helper.h#L54)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
