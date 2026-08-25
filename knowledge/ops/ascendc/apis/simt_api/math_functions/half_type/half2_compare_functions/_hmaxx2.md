---
type: API
title: __hmaxx2
description: 获取两个half2类型数据各分量的最大值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/half_type/half2_compare_functions/__hmaxx2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __hmaxx2

功能：获取两个half2类型数据各分量的最大值。

函数原型：half2 __hmaxx2(const half2 x, const half2 y)

参数：x（输入）源操作数，y（输入）源操作数。

返回值：输入数据各分量的最大值。该接口受全局饱和寄存器影响，。特殊值：(0,-0,0)→0；(-0,0,0)→0；(-0,-0,-0)→-0；(任一分量为inf,inf)→ASCRT_MAX_NORMAL_FP16；(-inf,-inf,-inf)→-ASCRT_MAX_NORMAL_FP16；(任一分量为nan,nan)→0。

约束：无。需包含头文件 simt_api/asc_fp16.h。

支持平台：仅 Ascend 950PR/Ascend 950DT 支持，其他 Atlas 系列产品不支持。

<!-- cannbot:related:start -->
## 相关

- [__hmaxx2](../../bfloat16_type/bfloat16x2_compare_functions/_hmaxx2.md)（`related`）：BFloat16x2 版本执行相同逐分量最大值，但精度格式与特殊值范围不同。
- [__hminx2](_hminx2.md)（`related`）：__hmaxx2 与 __hminx2 共享 half2 双分量输入、饱和寄存器和特殊值边界，但选择相反最值，适合成对实现或测试 clamp。
- [__hmaxx2_nan](_hmaxx2_nan.md)（`same_topic`）：“__hmaxx2_nan”处理获取两个half2类型数据中各分量的最大值。任一分量为nan时对应结果为nan。；“__hmaxx2”明确获取两个half2类型数据各分量的最大值。。实质衔接：这些函数分别去掉 NaN 传播、切换 max/min、缩为标量或显式检测 NaN，直接刻画 half2 最大值的边界语义。
<!-- cannbot:related:end -->
