---
type: API
title: GetUBSizeInBytes
description: 获取UB空间的大小，单位为Byte。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/tool_interface/system_resources_and_variables/GetUBSizeInBytes.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/basic_api/kernel_operator_sys_var_intf.h
---

# GetUBSizeInBytes

## 功能说明

头文件路径为：`"basic_api/kernel_operator_sys_var_intf.h"`。

获取Unified Buffer（UB）空间的大小，单位为Byte。开发者根据UB的大小来计算循环次数等参数值。

## 函数原型

```cpp
__aicore__ inline constexpr uint32_t GetUBSizeInBytes()
```

## 参数说明

无

## 返回值说明

UB空间的大小。


Ascend 950PR/Ascend 950DT架构下，返回常量248KB，单位为Byte。


## 约束说明

无

## 调用示例

本调用示例通过GetUBSizeInBytes获取的UB空间大小，来计算tileNum的值。完整的算子样例请参考：[get\_ub\_size样例](https://gitcode.com/cann/asc-devkit/tree/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/01_simd_cpp_api/03_basic_api/09_utils/get_ub_size)。

```cpp
// totalLength为待处理的总数据长度(元素个数)
this->totalLength = totalLength;
// GetUBSizeInBytes() / sizeof(half) -> 计算UB能容纳多少个half类型元素
// 除2 -> 预留50%的UB空间
if (totalLength > AscendC::GetUBSizeInBytes() / sizeof(half) / 2) {
    this->tileLength = AscendC::GetUBSizeInBytes() / sizeof(half) / 2;
} else { // 防止分片大小超过实际数据总量
    this->tileLength = this->totalLength;
}
// 需要迭代的分片数量
this->tileNum = this->totalLength / this->tileLength;
```


<!-- cannbot:related:start -->
## 相关

- [GatherV2 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/index/gather_v2_950.md)（`related`）：“与 R-001 的行/列搬运相同，但分核与 `ubAvailable` 在 Device 用 `GetBlockNum/GetUBSizeInBytes-128KiB` 重算，避免 PCIe 地址由 SIMT 直接解引用。”记录 UB 可用量计算；“获取UB空间的大小，单位为Byte。开发者根据UB的大小来计算循环次数等参数值。”给出 GetUBSizeInBytes 的字节单位和用途，直接支撑减去 128 KiB 后的 buffer 分配。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 2 / 2 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Embedding 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/index/embedding_950.md)（`related`）：算子声明的固定版本源码包含对 `GetUBSizeInBytes(...)` 的直接调用（第 76 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/gather_v2/op_kernel/arch35/gather_v2_simd_two_dim_pcie.h#L76)
- [Take 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/index/take_950.md)（`related`）：算子声明的固定版本源码包含对 `GetUBSizeInBytes(...)` 的直接调用（第 76 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/gather_v2/op_kernel/arch35/gather_v2_simd_two_dim_pcie.h#L76)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
