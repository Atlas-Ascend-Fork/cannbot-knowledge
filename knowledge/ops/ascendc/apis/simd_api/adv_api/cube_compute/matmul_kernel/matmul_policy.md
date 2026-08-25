---
type: API
title: MatmulPolicy
description: 模板参数，用于定义Matmul可拓展模块策略，支持上三角、下三角、NBuffer33、MxMatmul、SplitM、SplitN等内置策略。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/MatmulPolicy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# MatmulPolicy

模板参数MatmulPolicy用于定义Matmul可拓展模块策略。目前支持设置以下几种Matmul内置模板策略。 - MatmulPolicy（默认模板策略） 启用Matmul API的默认实现策略。

涵盖以下类别：MatmulPolicy、TrianUpperMatmulPolicy/TrianLowerMatmulPolicy、NBuffer33MatmulPolicy、MatmulWithScalePolicy/SplitMMatmulPolicy/SplitNMatmulPolicy。

约束：
- TrianUpperMatmulPolicy当前只支持Norm模板和MDL模板。
- TrianLowerMatmulPolicy当前只支持Norm模板和MDL模板。
- NBuffer33MatmulPolicy：
- 当前只支持MDL模板。
- A矩阵、B矩阵的内存逻辑位置只支持TPosition::GM。

适用平台：Ascend 950PR/Ascend 950DT、Atlas A2 系列、Atlas A3 系列。未列出的产品形态不在本卡已确认范围内；详细支持矩阵以固定来源的“产品支持情况”为准。

<!-- cannbot:related:start -->
## 相关

- [Matmul Kernel侧接口](matmul_kernel.md)（`related`）：Matmul Kernel 总览给出对象初始化、计算与输出生命周期，说明策略参数在哪个对象流程中生效。
- [MatmulCallBackFunc](matmul_call_back_func.md)（`related`）：《MatmulCallBackFunc》说明模板参数，支持用户定制化Matmul的A、B、C矩阵搬入搬出功能，传入自定义回调函数指针替换默认搬运函数。；《MatmulPolicy》说明模板参数，用于定义Matmul可拓展模块策略，支持上三角、下三角、NBuffer33、MxMatmul、SplitM、SplitN等内置策略。。二者在回调类型由Matmul模板参数、配置与Policy实例化，并经注册宏和用户自定义信息进入Kernel侧Matmul对象上存在可执行的直接衔接。
- [MatmulConfig](matmul_config.md)（`related`）：MatmulPolicy 选择扩展策略，MatmulConfig 选择模板配置；二者共同确定 Matmul 对象的编译期行为但职责不同。
- [Matmul使用说明](matmul_usage.md)（`related`）：Matmul 使用说明展示由模板参数实例化对象并执行计算的入口，使策略类型与实际对象声明相衔接。
- [MatmulTemplateParams](matmul_template_params.md)（`same_topic`）：MatmulPolicy 是 MatmulTemplateParams 中用于替换扩展策略的模板参数，决定上/下三角、SplitM/SplitN 等内置模块。
<!-- cannbot:related:end -->
