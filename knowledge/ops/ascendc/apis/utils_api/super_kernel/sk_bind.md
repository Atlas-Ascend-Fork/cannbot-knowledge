---
type: API
title: SK_BIND（SuperKernel）
description: 本接口为算子SuperKernel场景提供绑定原核函数和SK子函数的能力。核函数直调算子的完整适配方法请参见核函数直调算子额外适配说明。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/SuperKernel/SK_BIND.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---
# SK_BIND

## 功能说明
本接口为算子SuperKernel场景提供绑定原核函数和SK子函数的能力。核函数直调算子的完整适配方法请参见核函数直调算子额外适配说明。
## 函数原型
## 参数说明
GF：输入：核函数函数签名。
cap：输入：uint64_t类型，用于标记当前算子的SuperKernel特性。SuperKernel框架根据这些信息调整相应的同步和融合策略。各bit位可按位或组合：&bull; 1：early start wait flag，表示算子内使用了WaitPreTaskEnd接口。&bull; 2：early start set flag，表示算子内使用了SetNextTaskStart接口。&bull; 4：disable_dcci，表示当前算子需要SuperKernel框架关闭调用前后的DCCI ALL指令。详细说明请参见算子适配说明。&bull; 8：disable_batchmode_check，表示跳过当前算子的__schedmode__检查，使该算子可继续参与SuperKernel融合。例如，同时配置early start wait flag和early start set flag时，cap取值为3。
SK0：输入：SK子函数签名。
...：输入：SK1~SK3。可提供多个SK子函数签名，包含SK0最多四个函数签名。
## 返回值说明
无
## 约束说明
-   一个核函数最多绑定四个SK子函数。
-   核函数直调算子目前仅支持在npugraph_ex后端进入SuperKernel，不支持GE图模式。

<!-- cannbot:related:start -->
## 相关

- [SuperKernel原理介绍](../../../guides/programming_guide/advanced_programming/super_kernel/principles.md)（`explains`）：核函数直调算子额外适配说明：对于使用>>方式开发的Ascend C算子，进入SuperKernel前需要进行的额外适配工作。；本接口为算子SuperKernel场景提供绑定原核函数和SK子函数的能力。核函数直调算子的完整适配方法请参见核函数直调算子额外适配说明。；焦点指向的直调适配由 SK_BIND 提供原 Kernel 与 SK 子函数绑定合同。
- [核函数直调算子额外适配说明](../../../guides/programming_guide/advanced_programming/super_kernel/kernel_direct_call_adaptation.md)（`explains`）：本接口为算子SuperKernel场景提供绑定原核函数和SK子函数的能力。核函数直调算子的完整适配方法请参见核函数直调算子额外适配说明。；- 需要与普通Kernel函数通过SK_BIND宏绑定。。API 卡定义 SK_BIND 的绑定能力并指向直调适配说明，Guide 把该宏列为 SuperKernel 入口与普通 Kernel 配套的必需步骤。
<!-- cannbot:related:end -->
