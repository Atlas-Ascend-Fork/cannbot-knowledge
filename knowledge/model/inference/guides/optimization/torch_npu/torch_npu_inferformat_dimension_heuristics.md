---
type: Guide
title: TorchNPU InferFormat 维度启发式：5D/4D 基础格式推断与 NZ 降级
description: 固定 GuessBaseFormat/GuessStorageFormat/GuessFormatUnit 的维度规则、NZ dim<2
  降级告警与 TransData 维度补齐，避免把格式猜测当作显式 cast 契约。
tags:
- task.implementation
- topic.data_movement.layout_transform
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/InferFormat.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/InferFormat.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/InferFormat.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/InferFormat.h
  role: implementation
created_at: '2026-11-13T04:24:55Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU InferFormat 维度启发式：5D/4D 基础格式推断与 NZ 降级

## 固定版本与范围

静态审阅 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 `framework/InferFormat.cpp` 全文与 `InferFormat.h`。发布 pin 未比对。未确认产品范围，保持 `draft`、空平台；未运行设备或 cast 实验。显式格式转换 API 见[格式转换 API](../../../apis/torch_npu/cpp_npu_format_cast.md)与[npu_format_cast](../../../apis/torch_npu/npu_format_cast.md)；张量布局与存储描述的总体语义见[原生张量布局](torch_npu_native_tensor_layout.md)——该卡不覆盖 `GuessBaseFormat` 内部实现，本卡补上这一段。

## 纯维度规则的基础格式推断

`GuessBaseFormat`（InferFormat.cpp:46-53）只看维度数：5D→`ACL_FORMAT_NCDHW`、4D→`ACL_FORMAT_NCHW`、其余→`ACL_FORMAT_ND`。它不看尺寸数值（H/W 是否为 16 倍数等都不参与），因此"4D 张量推断为 NCHW"不代表物理存储已是 NCHW 排布，仅是基础格式标签。

## 存储格式的修正规则

`GuessStorageFormat`（:55-88）在给定 format 与 sizes 上修正：NZ 且 dim<2 直接降级 ND 并 `TORCH_WARN_ONCE`（"Cannot create tensor with NZ format while dim < 2"，标量与一维不支持 NZ）；基础格式 NCDHW 时按 dim 再修正——4D→NCHW（降维场景如 max/min，或 view/as_strided）、5D→NCDHW、其余→ND；NCHW 且 dim≠4→ND；dim==0 或 dim==1 且 size[0]==1 且基础格式 ND → ND（源码注释：算子把 0 维和 [1] 视为标量）。其余情况原样返回。`GuessFormatUnit`（:27-44）配套处理"shape infer 协同"场景：NCDHW 基础格式在 >4D 时保持；ND 且恰 4D 时双写 NCHW；NCDHW 4D 时降到 NCHW。

## 连续化与转换时的两个辅助

`GuessFormatWhenContiguous`（:10-25）：FakeTensor 无描述（data_ptr 为空）时固定 ND；origin_format 为 NCDHW 且 view 后维度数与 base 不一致且 ≤4 时改判 NCHW，否则返回 origin_format——连续化不会发明新格式，只继承或做 NCDHW 降维修正。`GuessStorageSizeWhenConvertFormat`（:90-103）：ND→NZ 转换时若 dim<2 会补 1 维到 2D（源码注释：仅 ND↔NZ 走 TransData，补维不影响存储），再交 `FormatHelper::GetStorageSizes` 计算物理尺寸。`IsDefiniteTensorWhenMetaDataChanges`（:105-114）：NCHW 基础格式且 size ≥5 维、或 NCDHW 且 ≠5 维时返回 true，用于元数据变更时判定"确定张量"。

## 优化判断

这些启发式决定**新张量默认拿什么格式标签**与**连续化/转换时的自动修正**：模型里 5D 张量默认 NCDHW、4D 默认 NCHW；对 NZ 张量做 reduce 到 1 维会得到 ND+告警。要固定物理布局时应显式 `npu_format_cast`，不要依赖维度推断。推断结果只是标签，物理存储尺寸另按[格式与存储尺寸](../../../apis/torch_npu/cpp_format_and_storage_sizes.md)核对。本卡未审阅所有调用点（如 EmptyTensor/OpPreparation 侧如何消费这些函数），也未比对发布版差异。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/InferFormat.cpp)（primary）：10-117（1-9 为 include 头部未逐行）。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/InferFormat.h)（implementation）：声明面（51 行，wc -l=50，末行无换行符）。

## 发布 pin 对照（f3ecfe4a）

卡内涉及的 2 个发布孪生文件已做真实机械比对（sha256 → 去空白 → token → 注释剥离 token → 语义 diff 五级），结论分述如下。

### 已绑定（等价/无行为差异）

- `torch_npu/csrc/framework/InferFormat.cpp`：注释差异等价（代码 token 流相同）。发布来源条目已入 frontmatter（release pin f3ecfe4a）。
- `torch_npu/csrc/framework/InferFormat.h`：唯一实质 token 差异：`#include <acl/acl_base.h>` 改为 `#include "third_party/acl/inc/acl/acl_base.h"`（构建布局差异，无运行时行为变化）。发布来源条目已入 frontmatter（release pin f3ecfe4a）。

（本节静态比对，未运行/未编译；结论按文件分列，未列出的文件未比对。）
