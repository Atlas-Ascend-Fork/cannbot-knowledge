---
type: API
title: REGIST_MATMUL_OBJ
description: 初始化Matmul对象。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.programming_model.execution_unit.cube
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/REGIST_MATMUL_OBJ.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms: []
---

# REGIST\_MATMUL\_OBJ

## 功能说明

初始化Matmul对象。

## 函数原型

```
REGIST_MATMUL_OBJ(tpipe, workspace, ...)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| tpipe | 输入 | Tpipe对象。 |
| workspace | 输入 | 系统workspace指针。 |
| ... | 输入 | 可变参数，传入Matmul对象和与之对应的Tiling结构，要求Tiling结构的数据类型为[TCubeTiling结构](../matmul_tiling/t_cube_tiling_struct.md#tcubetiling-struct)。<br><br>Tiling参数可以通过Host侧[GetTiling](../matmul_tiling/get_tiling.md)接口获取，并传递到kernel侧使用。 |

## 返回值说明

无

## 约束说明

-   在分离模式中，本接口必须在[InitBuffer](../../../basic_api/resource_management/t_pipe/init_buffer.md)接口前调用。
-   在程序中，最多支持定义4个Matmul对象。
-   在Matmul的内部实现中使用了[CrossCoreSetFlag](../../../basic_api/sync_control/inter_core_sync/cross_core_set_flag_isasi.md)和[CrossCoreWaitFlag](../../../basic_api/sync_control/inter_core_sync/cross_core_wait_flag_isasi.md)进行核间同步控制，因此开发者同时使用CrossCoreSetFlag（或CrossCoreWaitFlag）和Matmul时，需注意避免核间同步flagId冲突。Matmul高阶API内部占用的flagId范围与定义的Matmul对象数目相关。假设定义了N个Matmul对象，则Matmul高阶API内部占用的flagId范围为\[0, 2 \* N - 1\]。Matmul最多支持定义4个对象，此时flagId占用范围为\[0, 7\]。
-   当代码中只有一个Matmul对象时，本接口可以不传入tiling参数，通过[Init](init.md)接口单独传入tiling参数。
-   当代码中有多个Matmul对象时，必须满足Matmul对象与其tiling参数一一对应，依次传入，具体方式请参考调用示例。
-   在分离模式中，调用本接口后，AIC核不会主动执行接口，仅在AIV核执行到下述接口后，才会触发AIC核的执行，其他接口则不会在AIC核上执行。
    -   [Matmul核函数（Kernel）侧接口](index.md)。
    -   [DataCopy(GMToL1连续数据搬运)](../../../basic_api/cube_compute_isasi/cube_compute_load/data_copy_gm_to_l1_continuous.md)、[DataCopy(GMToL1高维切分数据搬运)](../../../basic_api/cube_compute_isasi/cube_compute_load/data_copy_gm_to_l1_highdim_split.md)、[DataCopy(GMToL1随路转换-ND2NZ搬运)](../../../basic_api/cube_compute_isasi/cube_compute_load/data_copy_gm_to_l1_nd2_nz.md)。

## 调用示例

```
Tpipe pipe;
// 推荐：初始化单个matmul对象，传入tiling参数
REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm, &tiling);
// 推荐：初始化多个matmul对象，传入对应的tiling参数
REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm1, mm1tiling, mm2, mm2tiling, mm3, mm3tiling, mm4, mm4tiling);
// 初始化单个matmul对象，未传入tiling参数。注意，该场景下需要使用Init接口单独传入tiling参数。这种方式将matmul对象的初始化和tiling的设置分离，比如，Tiling可变的场景，可通过这种方式多次对Tiling进行重新设置
REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm);
mm.Init(&tiling);
```


<!-- cannbot:related:start -->
## 相关

- [Matmul高阶API开启纯Cube模式](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_pure_cube.md)（`explains`）：纯 Cube 指南说明“用户使用Matmul高阶API编写算子代码时，可以使用REGIST_MATMUL_OBJ宏，无需区分AIV和AIC”，并据此对比 MIX 消息开销；接口卡则明确“初始化Matmul对象。”，把指南中的宏落到对象初始化及其 tiling/同步资源合同。
- [Init](init.md)（`related`）：Init 页说明“开发者可以先通过［REGIST_MATMUL_OBJ］(regist_matmul_obj.md)不传入Tiling参数对单个Matmul对象进行初始化，后续通过Init接口单独传入Tiling参数”；注册页说明“当代码中只有一个Matmul对象时，本接口可以不传入tiling参数，通过Init接口单独传入tiling参数。”，双方明确给出同一注册后再初始化的调用合同。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 2 / 2 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [grouped_matmul_add A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul_add.md)（`related`）：算子声明的固定版本源码包含对 `REGIST_MATMUL_OBJ(...)` 的直接调用（第 413 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul_add/op_kernel/grouped_matmul_add.cpp#L413)
- [grouped_matmul_add 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul_add_950.md)（`related`）：算子声明的固定版本源码包含对 `REGIST_MATMUL_OBJ(...)` 的直接调用（第 413 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul_add/op_kernel/grouped_matmul_add.cpp#L413)

### 知识正文中的调用示例

展示 7 / 7 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [UpsampleBicubic2dAA A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bicubic_2d_aa.md)（`related`）：算子正文包含对 `REGIST_MATMUL_OBJ(...)` 的直接调用；本卡提供该接口契约。
- [DeformableConv2d A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/conv/deformable_conv2d.md)（`related`）：算子正文包含对 `REGIST_MATMUL_OBJ(...)` 的直接调用；本卡提供该接口契约。
- [FlashAttentionScoreGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_score_grad.md)（`related`）：算子正文包含对 `REGIST_MATMUL_OBJ(...)` 的直接调用；本卡提供该接口契约。
- [UpsampleBicubic2dAAGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bicubic_2d_aa_grad.md)（`related`）：算子正文包含对 `REGIST_MATMUL_OBJ(...)` 的直接调用；本卡提供该接口契约。
- [FlashAttentionUnpaddingScoreGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_unpadding_score_grad.md)（`related`）：算子正文包含对 `REGIST_MATMUL_OBJ(...)` 的直接调用；本卡提供该接口契约。
- [UpsampleBilinear2dAABackward A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bilinear_2d_aa_backward.md)（`related`）：算子正文包含对 `REGIST_MATMUL_OBJ(...)` 的直接调用；本卡提供该接口契约。
- [NsaSelectedAttention A2 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/nsa_selected_attention.md)（`related`）：算子正文包含对 `REGIST_MATMUL_OBJ(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
