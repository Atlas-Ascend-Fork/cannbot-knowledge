---
type: API
title: __isnanx2
description: 判断half2类型数据的两个分量是否为nan。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__isnanx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __isnanx2

功能：判断half2类型数据的两个分量是否为nan。

函数原型：half2 __isnanx2(half2 x)

参数：x（输入）源操作数。

返回值：判断输入数据各分量是否为nan，为nan时对应分量结果为1，否则为0。特殊值：nan→1；±0→0；±inf→0；ASCRT_MAX_NORMAL_FP16→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [IsNan接口](../../../../simd_api/adv_api/math_compute/is_nan_interface/is_nan_interface.md)（`related`）：《IsNan接口》处理“按元素判断浮点数是否为NaN，并提供临时空间大小获取接口。”。《__isnanx2》提供“判断half2类型数据的两个分量是否为nan。”，其具体合同或探针直接接入IsNan 的 Kernel/Tiling 合同、跨 dtype 谓词与 Cast 保留 NaN 的前置条件。
- [__hbleux2](_hbleux2.md)（`related`）：__hbleux2 与《__isnanx2》的实质衔接是：half2 unordered LE 布尔接口需与 mask、ordered LE、isnan 和比较入口对照。
- [__hbltx2](_hbltx2.md)（`related`）：__hbltx2 与《__isnanx2》的实质衔接是：ordered/unordered 与 bool/mask 形式围绕 half2 小于比较的 NaN 和逐 lane 返回契约互相补足。
- [__hequx2](_hequx2.md)（`related`）：__hequx2 与《__isnanx2》的实质衔接是：half2 unordered equality 的 bool/mask 形式与 ordered equality、isnan 共同界定逐 lane 返回和 NaN 行为。
- [__heqx2_mask](_heqx2_mask.md)（`related`）：__heqx2_mask 与《__isnanx2》的实质衔接是：ordered equality 的 mask、bool 与 unordered 形态围绕 half2 的逐 lane 返回及 NaN 规则互补。
- [__hgex2](_hgex2.md)（`related`）：__hgex2 与《__isnanx2》的实质衔接是：half2 ordered GE 的 mask/bool 形态和 unordered 变体围绕逐 lane 返回与 NaN 规则互补，isnan 明确特殊值分支。
- [__hgtux2_mask](_hgtux2_mask.md)（`related`）：__hgtux2_mask 与《__isnanx2》的实质衔接是：half2 unordered greater-than mask 与 ordered mask、反向 less-than、bool/boolean-all 返回及 isnan 共同界定逐 lane 位图和 NaN 为 true 的语义。
- [__hisnan](../half_compare_functions/_hisnan.md)（`related`）：标量 half NaN 判定可作为 __isnanx2 每个分量的验证 oracle。
- [__hleux2](_hleux2.md)（`related`）：__hleux2 与《__isnanx2》的实质衔接是：half2 unordered ≤ 的 mask、boolean-all、反向 ≥、bfloat16 与 isnan 形态共同界定逐 lane 返回和 NaN 为 true 的语义。
- [__hlex2_mask](_hlex2_mask.md)（`related`）：__hlex2_mask 与《__isnanx2》的实质衔接是：half2 ordered ≤ mask 与 ordered boolean、boolean-all、unordered、反向 ≥ 和 isnan 共同界定位图返回及 NaN 为 false 的规则。
- [__hmaxx2_nan](_hmaxx2_nan.md)（`related`）：“__hmaxx2_nan”处理获取两个half2类型数据中各分量的最大值。任一分量为nan时对应结果为nan。；“__isnanx2”明确判断half2类型数据的两个分量是否为nan。。实质衔接：这些函数分别去掉 NaN 传播、切换 max/min、缩为标量或显式检测 NaN，直接刻画 half2 最大值的边界语义。
- [__hneux2](_hneux2.md)（`related`）：焦点处理half2 unordered-not-equal 的 mask/数值/bool 返回形态；__isnanx2正文界定“判断half2类型数据的两个分量是否为nan”。候选只改变 ordered/unordered NaN 规则或 mask/bool/数值编码，直接指导比较 API 选择。
- [__isnanx2](../../bfloat16_type/bfloat16x2_compare_functions/_isnanx2.md)（`related`）：bfloat16x2 同名函数采用相同逐分量 NaN 判定，可对照 half2/bfloat16x2 路径。
- [__hgeux2](_hgeux2.md)（`same_topic`）：__hgeux2 与《__isnanx2》的实质衔接是：__hgeux2 的关键是 half2 逐 lane、unordered NaN 为真和 half2 数值返回；mask 版、ordered GE、反向 LE 与 isnan 入口分别核对返回形态和 NaN 分支。
- [__hgex2_mask](_hgex2_mask.md)（`same_topic`）：__hgex2_mask 与《__isnanx2》的实质衔接是：__hgex2_mask 返回 half2 ordered ≥ 的位图；数值返回版、反向 ≤、unordered ≥ 与 isnan 卡共同核对返回形态和 NaN 为 false/true 的分支。
- [__hgtx2](_hgtx2.md)（`same_topic`）：__hgtx2 与《__isnanx2》的实质衔接是：__hgtx2 返回 half2 ordered > 的逐 lane 0/1；mask、boolean-all、unordered >、反向 < 与 isnan 入口用于核对返回形态和 NaN=false。
<!-- cannbot:related:end -->
