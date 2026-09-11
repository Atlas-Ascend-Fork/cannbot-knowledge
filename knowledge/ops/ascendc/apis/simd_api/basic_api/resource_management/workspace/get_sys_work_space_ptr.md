---
type: API
title: GetSysWorkSpacePtr
description: 获取系统workspace指针。部分高阶API如Matmul需要使用系统workspace，相关接口需要传入系统workspace指针，此时可以通过该接口获取。使用系统workspace时，host侧开发者需要自行申请系统workspace的空间，其预留空间大小可以通过GetLibApiWorkSpaceSize接口获取。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.memory_management
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/workspace/GetSysWorkSpacePtr.md
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
- include/basic_api/kernel_operator_swap_mem_intf.h
---

# GetSysWorkSpacePtr<a name="ZH-CN_TOPIC_0000001666431622"></a>

## 功能说明<a name="section618mcpsimp"></a>

获取系统workspace指针。部分高阶API如Matmul需要使用系统workspace，相关接口需要传入系统workspace指针，此时可以通过该接口获取。使用系统workspace时，host侧开发者需要自行申请系统workspace的空间，其预留空间大小可以通过[GetLibApiWorkSpaceSize](../../../../utils_api/platform_info/platform_ascend_c/get_lib_api_work_space_size.md)接口获取。

## 函数原型<a name="section620mcpsimp"></a>

```
__aicore__ inline __gm__ uint8_t* __gm__ GetSysWorkSpacePtr()
```

## 参数说明<a name="section622mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>

无

## 返回值说明<a name="section640mcpsimp"></a>

系统workspace指针。

## 调用示例<a name="section642mcpsimp"></a>

```
...
REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm, &tiling); // 初始化，传入系统workspace指针
// CopyIn阶段：完成从GM到LocalMemory的搬运
mm.SetTensorA(gm_a);    // 设置左矩阵A
mm.SetTensorB(gm_b);    // 设置右矩阵B
mm.SetBias(gm_bias);    // 设置Bias
// Compute阶段：完成矩阵乘计算
while (mm.Iterate()) { 
    // CopyOut阶段：完成从LocalMemory到GM的搬运
    mm.GetTensorC(gm_c); 
}
// 结束矩阵乘操作
mm.End();
```


<!-- cannbot:related:start -->
## 相关

- [507035 host tiling workspace 缺 RESERVED](../../../../../runbooks/compilation/register_none_tiling_reserved_workspace_507035.md)（`exemplifies`）：使用系统workspace时，host侧开发者需要自行申请系统workspace的空间，其预留空间大小可以通过GetLibApiWorkSpaceSize接口获取。`usrWorkspace = workspace + 16MB` 落在仅有 ~2MB 的 buffer 末尾之外 ~14MB，kernel 写 multiplier/addend 时 GM 越界 → 507035 向量核异常。接口卡的系统区申请合同直接解释该故障的越界地址；Host 总量计入平台 reserved 区即可同时覆盖系统指针和用户段。
- [GetLibApiWorkSpaceSize](../../../../utils_api/platform_info/platform_ascend_c/get_lib_api_work_space_size.md)（`related`）：获取AscendC API需要的workspace空间大小。；获取系统workspace指针。部分高阶API如Matmul需要使用系统workspace，相关接口需要传入系统workspace指针，此时可以通过该接口获取。使用系统workspace时，host侧开发者需要自行申请系统workspace的空间，其预留空间大小可以通过GetLibApiWorkSpaceSize接口获取。。GetLibApiWorkSpaceSize 给出 Host 侧预留容量，GetSysWorkSpacePtr 明确该容量由 Host 申请后在 Kernel 侧取得系统 workspace 指针，二者是同一 workspace 生命周期的容量端与地址端。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 2 / 2 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [grouped_matmul_add A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul_add.md)（`related`）：算子声明的固定版本源码包含对 `GetSysWorkSpacePtr(...)` 的直接调用（第 413 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul_add/op_kernel/grouped_matmul_add.cpp#L413)
- [grouped_matmul_add 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/gmm/grouped_matmul_add_950.md)（`related`）：算子声明的固定版本源码包含对 `GetSysWorkSpacePtr(...)` 的直接调用（第 413 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/gmm/grouped_matmul_add/op_kernel/grouped_matmul_add.cpp#L413)

### 知识正文中的调用示例

展示 7 / 7 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [UpsampleBicubic2dAAGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bicubic_2d_aa_grad.md)（`related`）：算子正文包含对 `GetSysWorkSpacePtr(...)` 的直接调用；本卡提供该接口契约。
- [DeformableConv2d A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/conv/deformable_conv2d.md)（`related`）：算子正文包含对 `GetSysWorkSpacePtr(...)` 的直接调用；本卡提供该接口契约。
- [FlashAttentionScoreGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/flash_attention_score_grad.md)（`related`）：算子正文包含对 `GetSysWorkSpacePtr(...)` 的直接调用；本卡提供该接口契约。
- [UpsampleBilinear2dAA A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bilinear_2d_aa.md)（`related`）：算子正文包含对 `GetSysWorkSpacePtr(...)` 的直接调用；本卡提供该接口契约。
- [LSTM A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/rnn/lstm.md)（`related`）：算子正文包含对 `GetSysWorkSpacePtr(...)` 的直接调用；本卡提供该接口契约。
- [NsaSelectedAttention A2 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/nsa_selected_attention.md)（`related`）：算子正文包含对 `GetSysWorkSpacePtr(...)` 的直接调用；本卡提供该接口契约。
- [UpsampleBilinear2dAABackward A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/cv/image/upsample_bilinear_2d_aa_backward.md)（`related`）：算子正文包含对 `GetSysWorkSpacePtr(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
