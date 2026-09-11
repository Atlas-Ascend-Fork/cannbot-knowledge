---
type: API
title: MakeCoord
description: 将传入的数据打包成Coord数据结构。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.development_mode.tensor_programming
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Coordinate/MakeCoord.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
---

# MakeCoord<a name="ZH-CN_TOPIC_0000002366586926"></a>

## 功能说明<a name="zh-cn_topic_0000002078486173_zh-cn_topic_0000001576727153_zh-cn_topic_0000001389787297_section36583473819"></a>

将传入的数据打包成Coord数据结构。

## 函数原型<a name="zh-cn_topic_0000002078486173_zh-cn_topic_0000001576727153_zh-cn_topic_0000001389787297_section13230182415108"></a>

```cpp
template <typename... Ts>
__aicore__ inline constexpr Coord<Ts...> MakeCoord(Ts const&... t)
```

## 参数说明<a name="zh-cn_topic_0000002078486173_zh-cn_topic_0000001576727153_zh-cn_topic_0000001389787297_section75395119104"></a>

<a name="zh-cn_topic_0000002078486173_zh-cn_topic_0000001576727153_zh-cn_topic_0000001389787297_table111938719446"></a>
<table><thead align="left"><tr id="zh-cn_topic_0000002078486173_zh-cn_topic_0000001576727153_zh-cn_topic_0000001389787297_row6223476444"><th class="cellrowborder" valign="top" width="17.22%" id="mcps1.1.4.1.1"><p id="p1085176175119"><a name="p1085176175119"></a><a name="p1085176175119"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="15.340000000000002%" id="mcps1.1.4.1.2"><p id="p1851763519"><a name="p1851763519"></a><a name="p1851763519"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="67.44%" id="mcps1.1.4.1.3"><p id="p148519610515"><a name="p148519610515"></a><a name="p148519610515"></a>描述</p>
</th>
</tr>
</thead>
<tbody><tr id="zh-cn_topic_0000002078486173_zh-cn_topic_0000001576727153_zh-cn_topic_0000001389787297_row152234713443"><td class="cellrowborder" valign="top" width="17.22%" headers="mcps1.1.4.1.1 "><p id="p1329915004219"><a name="p1329915004219"></a><a name="p1329915004219"></a>t</p>
</td>
<td class="cellrowborder" valign="top" width="15.340000000000002%" headers="mcps1.1.4.1.2 "><p id="p9731042114910"><a name="p9731042114910"></a><a name="p9731042114910"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="67.44%" headers="mcps1.1.4.1.3 "><p id="p39081929172310"><a name="p39081929172310"></a><a name="p39081929172310"></a>表示输入数据类型的形参包，具体使用方法和约束说明同<a href="../../../../utils_api/cpp_stdlib/container_functions/index.md">Std::tuple</a>。</p>
<p id="p116512845110"><a name="p116512845110"></a><a name="p116512845110"></a>输入的数据类型支持size_t和Std::<a href="../../../../utils_api/cpp_stdlib/type_traits/integral_constant.md">Int</a>。</p>
</td>
</tr>
</tbody>
</table>

## 返回值说明<a name="zh-cn_topic_0000002078486173_zh-cn_topic_0000001576727153_zh-cn_topic_0000001389787297_section25791320141317"></a>

Coord结构类型（[Std::tuple](../../../../utils_api/cpp_stdlib/container_functions/index.md)类型的别名）。

## 约束说明<a name="zh-cn_topic_0000002078486173_zh-cn_topic_0000001576727153_zh-cn_topic_0000001389787297_section19165124931511"></a>

无

## 调用示例<a name="zh-cn_topic_0000002078486173_zh-cn_topic_0000001576727153_zh-cn_topic_0000001389787297_section320753512363"></a>

```cpp
auto blockCoordM = Std::Int<11>{};
auto blockCoordN = Std::Int<12>{};
auto coord = AscendC::MakeCoord(blockCoordM, blockCoordN);
```


<!-- cannbot:related:start -->
## 相关

- [Coordinate简介](coordinate_intro.md)（`related`）：通过MakeCoord构造，可用于Tensor的元素索引和位置计算。；构造Coordinate坐标结构体。；简介给出的 Coordinate 生产步骤由 MakeCoord 的构造合同具体实现。
- [Crd2Idx](crd2_idx.md)（`related`）：将Coordinate坐标转换为Tensor中的线性索引（index）；构造Coordinate坐标结构体。MakeCoord 生成 Crd2Idx 的 Coordinate 输入，Crd2Idx 再结合 shape 计算线性偏移；联合阅读即可完成从多维坐标构造到 Tensor 索引的调用链。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 2 / 2 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [WeightQuantBatchMatmulNz 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/weight_quant_batch_matmul_nz_950.md)（`related`）：算子声明的固定版本源码包含对 `MakeCoord(...)` 的直接调用（第 535 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/common/cmct/prologue/block_prologue_b_antiquant_scmc_nd_nk_nz_kn.h#L535)
- [WeightQuantBatchMatmul 950 Direct Invoke 算子知识](../../../../../operators/direct/nn/matmul/weight_quant_batch_matmul_950.md)（`related`）：算子声明的固定版本源码包含对 `MakeCoord(...)` 的直接调用（第 144 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/common/cmct/block/block_mmad_a_prefetch_b_prologue.h#L144)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
