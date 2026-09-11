---
type: API
title: GetCurNpuArch
description: 获取当前硬件平台芯片架构版本号。
tags:
- task.lookup
- topic.implementation.api_layer.utils_api
- topic.programming_model.system_variable
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetCurNpuArch.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
source_headers:
- include/utils/tiling/platform/platform_ascendc.h
---

# GetCurNpuArch<a name="ZH-CN_TOPIC_0000002543243123"></a>

## 功能说明<a name="zh-cn_topic_0000001664705472_zh-cn_topic_0000001442758437_section36583473819"></a>

获取当前硬件平台芯片架构版本号。

## 函数原型<a name="zh-cn_topic_0000001664705472_zh-cn_topic_0000001442758437_section13230182415108"></a>

```
NpuArch GetCurNpuArch(void) const
```

## 参数说明<a name="zh-cn_topic_0000001664705472_zh-cn_topic_0000001442758437_section189014013619"></a>

无

## 返回值<a name="zh-cn_topic_0000001664705472_zh-cn_topic_0000001442758437_section25791320141317"></a>

当前硬件平台架构号的枚举类。该枚举类和AI处理器型号的对应关系请通过CANN软件安装后文件存储路径下include/platform/soc\_spec.h头文件获取。


- Ascend 950PR/Ascend 950DT：DAV\_3510


- Atlas A3 训练系列产品/Atlas A3 推理系列产品：DAV\_2201


- Atlas A2 训练系列产品/Atlas A2 推理系列产品：DAV\_2201


- Atlas 200I/500 A2 推理产品：DAV\_3002


- Atlas 推理系列产品AI Core：DAV\_2002


- Atlas 推理系列产品Vector Core：DAV\_2002


- Atlas 训练系列产品：DAV\_1001


## 约束说明<a name="zh-cn_topic_0000001664705472_zh-cn_topic_0000001442758437_section19165124931511"></a>

无

## 调用示例<a name="zh-cn_topic_0000001664705472_zh-cn_topic_0000001442758437_section320753512363"></a>

```
ge::graphStatus TilingXXX(gert::TilingContext* context) {
    auto ascendcPlatform = platform_ascendc::PlatformAscendC(context->GetPlatformInfo());
    auto npuArch = ascendcPlatform.GetCurNpuArch();
    // 根据所获得的版本型号自行设计Tiling策略
    // DAV_XXX请替换为实际的架构号
    if (socVersion == NpuArch::DAV_XXXX) {
        // ...
    }
    return ret;
}
```



<!-- cannbot:related:start -->
## 相关

- [Ascend arch 变体查证链路 SoC→ini→NpuArch→dispa](../../../../runbooks/compilation/arch_variant_lookup_chain_soc_ini_npuarch_dispatcher.md)（`exemplifies`）：- `AIC_version` 与 `NpuArch` 互为印证：`NpuArch=3510` → dispatcher 的 `__NPU_ARCH__==3510` 分支；`AIC_version=AIC-C-310` → `dav_c310/` 目录名。任一即可定位变体，且都来自 ini 硬证据。；当前硬件平台架构号的枚举类。该枚举类和AI处理器型号的对应关系请通过CANN软件安装后文件存储路径下include/platform/soc_spec.h头文件获取。 - Ascend 950PR/Ascend 950DT：DAV_3510 - Atlas A3 训练系列产品/Atlas A3 推理系列产品：DAV_2201 - Atlas A2 训练系列产品/Atlas A2 推理系列产品：DAV_2201；焦点按 NpuArch 选择编译期 dispatcher 变体，目标提供产品到 DAV 架构枚举的权威映射入口。
- [NPU架构版本2002](../../../../guides/programming_guide/advanced_programming/hardware_implementation/hardware_constraints/npu_arch_2002.md)（`explains`）：NPU架构版本2002不支持Generic Addressing通用寻址（针对UB、stack、GM等地址空间），因此语言层面地址空间必须匹配。；Atlas 推理系列产品AI Core：DAV_2002；GetCurNpuArch 的返回映射可在运行或 Host 选择阶段识别 DAV_2002，随后应用焦点卡的地址空间约束。
- [NPU架构版本3002](../../../../guides/programming_guide/advanced_programming/hardware_implementation/architecture_spec/npu_arch_3002.md)（`explains`）：对应的产品型号为；获取当前硬件平台芯片架构版本号；连接静态架构映射与平台查询 API。

<!-- cannbot:api-operator:start -->
### 知识正文中的调用示例（部分算子）

展示 10 / 12 个已匹配算子；每个 API 最多展示 10 个自动关联。
以下仅有知识正文中的调用证据，未作为源码调用结果。

- [Hardtanh 950 ACLNN 算子知识](../../../../operators/aclnn/math/conversion/hardtanh_950.md)（`related`）：算子正文包含对 `GetCurNpuArch(...)` 的直接调用；本卡提供该接口契约。
- [Threshold 950 ACLNN 算子知识](../../../../operators/aclnn/nn/activation/threshold_950.md)（`related`）：算子正文包含对 `GetCurNpuArch(...)` 的直接调用；本卡提供该接口契约。
- [DistributeBarrier 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/mc2/distribute_barrier_950.md)（`related`）：算子正文包含对 `GetCurNpuArch(...)` 的直接调用；本卡提供该接口契约。
- [Asin 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/asin_950.md)（`related`）：算子正文包含对 `GetCurNpuArch(...)` 的直接调用；本卡提供该接口契约。
- [QuantConvolution 950 ACLNN 算子知识](../../../../operators/aclnn/nn/conv/quant_convolution_950.md)（`related`）：算子正文包含对 `GetCurNpuArch(...)` 的直接调用；本卡提供该接口契约。
- [MoeDistributeCombineSetup 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/mc2/moe_distribute_combine_setup_950.md)（`related`）：算子正文包含对 `GetCurNpuArch(...)` 的直接调用；本卡提供该接口契约。
- [InplaceAsin 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/inplace_asin_950.md)（`related`）：算子正文包含对 `GetCurNpuArch(...)` 的直接调用；本卡提供该接口契约。
- [LayerNormBackward A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/norm/layer_norm_backward.md)（`related`）：算子正文包含对 `GetCurNpuArch(...)` 的直接调用；本卡提供该接口契约。
- [MoeDistributeCombineTeardown 950 ACLNN 算子知识](../../../../operators/aclnn/transformer/mc2/moe_distribute_combine_teardown_950.md)（`related`）：算子正文包含对 `GetCurNpuArch(...)` 的直接调用；本卡提供该接口契约。
- [InplaceLerps 950 ACLNN 算子知识](../../../../operators/aclnn/math/math/inplace_lerps_950.md)（`related`）：算子正文包含对 `GetCurNpuArch(...)` 的直接调用；本卡提供该接口契约。

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
