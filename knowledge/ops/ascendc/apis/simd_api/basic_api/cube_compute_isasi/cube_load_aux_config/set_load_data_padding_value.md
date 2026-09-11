---
type: API
title: SetLoadDataPaddingValue
description: 调用LoadData（卷积数据搬运）接口时设置Pad填充的数值，当LoadData模板参数isSetPadding为false时通过本接口设置。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.cube
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_load_aux_config/SetLoadDataPaddingValue.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- kirin_x90
- kirin_9030
source_headers:
- include/basic_api/kernel_operator_mm_intf.h
---

# SetLoadDataPaddingValue<a name="ZH-CN_TOPIC_0000001834740625"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_operator_mm_intf.h"`。

用于调用[LoadData（卷积数据搬运）](../cube_compute_load/load_data_3_d.md)接口时设置Pad填充的数值。LoadData（卷积数据搬运）的模板参数isSetPadding设置为false时，用户需要通过本接口设置Pad填充的数值，设置为true时，本接口设置的填充值不生效。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
template <typename T>
__aicore__ inline void SetLoadDataPaddingValue(const T padValue)
```

## 参数说明<a name="section622mcpsimp"></a>

**表1** 参数说明

| 参数名称 | 输入/输出 | 含义 |
| ------ | ------ | ------ |
| padValue | 输入 | Pad填充值的数值。 |

## 数据类型

<br>
<br>
<br>
<br>
<br>
<br>


## 返回值说明

无

## 约束说明<a name="section633mcpsimp"></a>

无

## 调用示例<a name="section642mcpsimp"></a>

参考[调用示例](set_fmatrix.md#section642mcpsimp)

展示代码示例片段：

```cpp
// LoadData（卷积数据搬运）v2指令完成img2col的过程，可知img2col后A矩阵高度为ho * wo，根据ho和wo的计算公式，代入卷积核宽度、卷积核滑动步长、卷积核膨胀系数等参数可知：A矩阵的高度为CeilAlign(k, fractalShape[0])；img2col后A矩阵宽度为ci * kh * kw,代入kh=1，kw=1，可知A矩阵的宽度为CeilAlign(m, fractalShape[1])。最后，配置loadDataParams.enTranspose = true，将整个A矩阵转置并且将其中每一个分形转置
// 使用load3d接口，实现NZ2ZZ
AscendC::LoadData3DParamsV2<T> loadDataParams;
// 设置loadDataParams相关参数
...
// 设置不在LoadData（卷积数据搬运）接口内部设置相关属性，通过外部接口显式调用设置
static constexpr AscendC::IsResetLoad3dConfig LOAD3D_CONFIG = {false, false};

// 使用SetLoadDataPaddingValue接口，设置LoadData（卷积数据搬运）接口的padValue参数
AscendC::SetLoadDataPaddingValue(0);

AscendC::LoadData<T, LOAD3D_CONFIG>(a2Local, a1Local, loadDataParams);
```


<!-- cannbot:related:start -->
## 相关

- [LoadData](../cube_compute_load/load_data_3_d.md)（`related`）：设置 LoadData（卷积数据搬运）接口的 Pad 填充值。当 LoadData 模板参数 isSetPadding 为 false 时须通过本接口设置；为 true 时本接口不生效。；将数据从L1 Buffer搬运到L0A或L0B Buffer的3D模式搬运接口。。SetLoadDataPaddingValue 为 LoadData 3D 卷积搬运提供模板未内嵌 padding 时的 Pad 值配置，二者在同一次搬运调用中衔接。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 4 / 4 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [AllGatherMatmul A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/all_gather_matmul.md)（`related`）：算子声明的固定版本源码包含对 `SetLoadDataPaddingValue(...)` 的直接调用（第 315 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/all_gather_matmul_v2/op_kernel/all_gather_matmul_aiv_mode.h#L315)
- [AlltoAllMatmul A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/allto_all_matmul.md)（`related`）：算子声明的固定版本源码包含对 `SetLoadDataPaddingValue(...)` 的直接调用（第 166 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/allto_all_matmul/op_kernel/arch22/allto_all_matmul.h#L166)
- [AlltoAllQuantMatmul A2 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/allto_all_quant_matmul.md)（`related`）：算子声明的固定版本源码包含对 `SetLoadDataPaddingValue(...)` 的直接调用（第 166 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/allto_all_matmul/op_kernel/arch22/allto_all_matmul.h#L166)
- [MatmulReduceScatter A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/matmul_reduce_scatter.md)（`related`）：算子声明的固定版本源码包含对 `SetLoadDataPaddingValue(...)` 的直接调用（第 147 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/matmul_reduce_scatter_v2/op_kernel/matmul_reduce_scatter_aiv_mode.h#L147)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
