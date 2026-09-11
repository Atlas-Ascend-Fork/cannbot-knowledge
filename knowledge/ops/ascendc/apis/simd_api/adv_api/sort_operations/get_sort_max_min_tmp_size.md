---
type: API
title: GetSortMaxMinTmpSize
description: 在host侧获取带SortConfig模板参数的Sort接口计算所需的最大和最小临时空间大小。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.ordering
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/sort_operations/GetSortMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
source_headers:
- include/adv_api/sort/sort_tiling_intf.h
---

# GetSortMaxMinTmpSize

## 功能说明

带SortConfig模板参数的kernel侧Sort接口的计算需要开发者预留/申请临时空间，本接口用于在host侧获取预留/申请的最大最小临时空间大小，开发者基于此范围选择合适的空间大小作为Tiling参数传递到kernel侧使用。

-   为保证功能正确，预留/申请的临时空间大小不能小于最小临时空间大小；
-   在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留/申请。

## 函数原型

```
void GetSortMaxMinTmpSize(const AscendC::TensorShape& srcShape, AscendC::TensorDataType valueType, AscendC::TensorDataType indexType, bool isReuseSource, const SortConfig& config, uint32_t& maxValue, uint32_t& minValue)
```

## 参数说明

**表1**  接口参数列表

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| srcShape | 输入 | 输入的shape信息，参数类型为[AscendC::TensorShape](../data_structures/tensor_shape.md)。 |
| valueType | 输入 | 输入、输出Value的数据类型，参数类型为[AscendC::TensorDataType](../data_structures/tensor_data_type.md)。与Sort接口的模板参数T保持一致。 |
| indexType | 输入 | 输入、输出Index的数据类型，参数类型为[AscendC::TensorDataType](../data_structures/tensor_data_type.md)。与Sort接口的模板参数U保持一致。 |
| isReuseSource | 输入 | 是否复用源操作数输入的空间。与Sort接口的参数isReuseSource保持一致。 |
| config | 输入 | Sort的相应配置：选择的排序算法，排序结果的升降序，输入输出是否带有索引数据。数据类型SortConfig，定义如下方代码所示。其中的参数hasSrcIndex、hasDstIndex与使用的Sort接口是否带有输入索引、输出索引的情况保持一致；当前hasSrcIndex = true, hasDstIndex = false组合不支持。 |
| maxValue | 输出 | Sort接口能完成计算所需的最大临时空间大小，超出该值的空间不会被该接口使用。在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留/申请。最大空间大小为0表示计算不需要临时空间。<br> 说明：maxValue仅作为参考值，有可能大于Unified Buffer（UB）剩余空间的大小，该场景下，开发者需要根据UB剩余空间的大小来选取合适的临时空间大小。 |
| minValue | 输出 | Sort接口能完成计算所需最小临时空间大小。为保证功能正确，接口计算时预留/申请的临时空间不能小于该数值。最小空间大小为0表示计算不需要临时空间。 |

```
enum class SortType {
    RADIX_SORT, // 使用基排序算法实现
    MERGE_SORT  // 使用归并排序实现
};
struct SortConfig {
    SortType type = SortType::RADIX_SORT; // 排序算法
    bool isDescend = false;               // 是否降序排序，默认值为false，输出结果升序排序
    bool hasSrcIndex = false;             // 是否带有输入索引
    bool hasDstIndex = false;             // 是否带有输出索引
};
```

## 返回值说明

无

## 约束说明

无

## 调用示例

完整的调用样例请参考[更多样例](../math_compute/more_examples.md)。

```
// 输入shape信息为1024;算子输入的数据类型为uint32_t;不允许修改源操作数
std::vector<int64_t> shape_vec = {1024};
AscendC::TensorShape srcShape(shape_vec);
AscendC::TensorDataType valueType = AscendC::TensorDataType::DT_UINT32;
AscendC::TensorDataType indexType = AscendC::TensorDataType::DT_UINT32;
bool isDescend = true;
bool hasSrcIndex = false;
bool hasDstIndex = false;
bool isReuseSource = false;
AscendC::SortConfig config;
config.type = AscendC::SortType::RADIX_SORT;
config.isDescend = isDescend;
config.hasSrcIndex = hasSrcIndex;
config.hasDstIndex = hasDstIndex;
uint32_t maxValue = 0;
uint32_t minValue = 0;
AscendC::GetSortMaxMinTmpSize(srcShape, valueType, indexType, isReuseSource, config, maxValue, minValue);
```


<!-- cannbot:related:start -->
## 相关

- [Sort](sort.md)（`related`）：host侧Tiling接口，用于获取Sort接口所需的最大和最小临时空间大小。；提供通过sharedTmpBuffer传入临时空间或由接口框架申请两种重载。临时空间大小通过GetSortMaxMinTmpSize获取。。Sort 明确把显式 sharedTmpBuffer 的容量查询委托给 GetSortMaxMinTmpSize，二者是直接的 Host Tiling 与 Kernel 调用合同。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 9 / 9 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Sort 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/sort_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSortMaxMinTmpSize(...)` 的直接调用（第 204 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/sort/op_host/arch35/sort_tiling_arch35.cpp#L204)
- [IndexFill 950 ACLNN 算子知识](../../../../operators/aclnn/nn/index/index_fill_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSortMaxMinTmpSize(...)` 的直接调用（第 75 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/index_fill/op_host/arch35/index_fill_tiling_simt_dense_indices.cpp#L75)
- [TopK 950 Direct Invoke 算子知识](../../../../operators/direct/math/math/top_k_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSortMaxMinTmpSize(...)` 的直接调用（第 1236 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/top_k_v2/op_host/arch35/top_k_v2_tiling_arch35.cpp#L1236)
- [IndexFillTensor 950 ACLNN 算子知识](../../../../operators/aclnn/nn/index/index_fill_tensor_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSortMaxMinTmpSize(...)` 的直接调用（第 75 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/index_fill/op_host/arch35/index_fill_tiling_simt_dense_indices.cpp#L75)
- [InplaceIndexFillTensor 950 ACLNN 算子知识](../../../../operators/aclnn/nn/index/inplace_index_fill_tensor_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSortMaxMinTmpSize(...)` 的直接调用（第 75 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/index_fill/op_host/arch35/index_fill_tiling_simt_dense_indices.cpp#L75)
- [ScatterNd 950 ACLNN 算子知识](../../../../operators/aclnn/nn/index/scatter_nd_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSortMaxMinTmpSize(...)` 的直接调用（第 498 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/scatter_nd_update/op_host/arch35/scatter_nd_update_tiling_regbase.cpp#L498)
- [ScatterNdUpdate 950 ACLNN 算子知识](../../../../operators/aclnn/nn/index/scatter_nd_update_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSortMaxMinTmpSize(...)` 的直接调用（第 498 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/scatter_nd_update/op_host/arch35/scatter_nd_update_tiling_regbase.cpp#L498)
- [Scatter 950 Direct Invoke 算子知识](../../../../operators/direct/nn/index/scatter_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSortMaxMinTmpSize(...)` 的直接调用（第 368 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/scatter_elements_v2/op_host/arch35/scatter_elements_v2_asc_tiling.cpp#L368)
- [UnsortedSegmentSum 950 Direct Invoke 算子知识](../../../../operators/direct/nn/index/unsorted_segment_sum_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSortMaxMinTmpSize(...)` 的直接调用（第 101 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/index/unsorted_segment_sum/op_host/arch35/unsorted_segment_sum_tiling_base.cpp#L101)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
