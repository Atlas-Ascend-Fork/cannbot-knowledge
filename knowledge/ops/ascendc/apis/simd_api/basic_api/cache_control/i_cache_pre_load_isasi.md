---
type: API
title: ICachePreLoad
description: 从指令所在GM地址预加载指令到ICache中，支持配置预取长度，提升指令读取效率。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.data_movement.memory_access
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cache_control/ICachePreLoad_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
source_headers:
- include/basic_api/kernel_operator_cache_intf.h
---

# ICachePreLoad\(ISASI\)<a name="ZH-CN_TOPIC_0000001834752537"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_operator_cache_intf.h"`。

开发者手动调用ICachePreLoad接口，能够从指令所在GM地址预加载指令到ICache中。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
__aicore__ inline void ICachePreLoad(const int64_t preFetchLen)
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
|--------|-----------|------|
| preFetchLen | 输入 | 预取长度。|



针对如下型号：

- Ascend 950PR/Ascend 950DT


- Atlas A3 训练系列产品/Atlas A3 推理系列产品


- Atlas A2 训练系列产品/Atlas A2 推理系列产品

preFetchLen参数单位为2K Byte，取值满足如下要求：

$$
\text{preFetchLen}< \dfrac{\text{ICache的大小}}{2K}
$$
 
其中，AIC和AIV的ICache大小分别为32KB和16KB。


针对Atlas 推理系列产品AI Core，传入该参数无效，预取长度均为128Byte。
 

## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>

无

## 调用示例<a name="section837496171220"></a>

```cpp
int64_t preFetchLen = 2; // 预取指令长度。
AscendC::ICachePreLoad(preFetchLen);
```


<!-- cannbot:related:start -->
## 相关

- [GetICachePreloadStatus](get_i_cache_preload_status_isasi.md)（`related`）：“获取Instruction Cache预加载状态，查询当前指令Cache的预加载配置是否生效。”与“约束：与GetICachePreloadStatus配合使用。头文件：basic_api/kernel_operator_cache_intf.h。”分别给出两端正文事实；ICachePreLoad 发起指令预加载，GetICachePreloadStatus 查询该配置是否生效，构成同一预加载操作的提交与状态确认链。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 5 / 5 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [FlashAttn 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/flash_attn_950.md)（`related`）：算子声明的固定版本源码包含对 `ICachePreLoad(...)` 的直接调用（第 782 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attn/op_kernel/arch35/flash_attn_kernel_noquant_gqa.h#L782)
- [FusedInferAttentionScore A2/A3 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/fused_infer_attention_score.md)（`related`）：算子声明的固定版本源码包含对 `ICachePreLoad(...)` 的直接调用（第 721 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/common/op_kernel/arch22/fia_kernel_nonquant.h#L721)
- [FusedInferAttentionScore 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/attention/fused_infer_attention_score_950.md)（`related`）：算子声明的固定版本源码包含对 `ICachePreLoad(...)` 的直接调用（第 703 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/common/op_kernel/arch35/fia_kernel_fullquant_mx.h#L703)
- [GQA 950 Direct Invoke 算子知识](../../../../operators/direct/transformer/attention/gqa_950.md)（`related`）：算子声明的固定版本源码包含对 `ICachePreLoad(...)` 的直接调用（第 809 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/common/op_kernel/arch35/fia_kernel_noquant_gqa.h#L809)
- [MHA 950 Direct Invoke 算子知识](../../../../operators/direct/transformer/attention/mha_950.md)（`related`）：算子声明的固定版本源码包含对 `ICachePreLoad(...)` 的直接调用（第 782 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attn/op_kernel/arch35/flash_attn_kernel_noquant_gqa.h#L782)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
