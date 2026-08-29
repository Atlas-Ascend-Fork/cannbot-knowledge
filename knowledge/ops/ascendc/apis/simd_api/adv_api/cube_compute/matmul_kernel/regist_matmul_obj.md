---
type: API
title: REGIST_MATMUL_OBJ
description: 初始化Matmul对象。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/REGIST_MATMUL_OBJ.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# REGIST_MATMUL_OBJ

初始化Matmul对象。

参数：
- tpipe（输入）：Tpipe对象。
- workspace（输入）：系统workspace指针。
- ...（输入）：可变参数，传入Matmul对象和与之对应的Tiling结构，要求Tiling结构的数据类型为TCubeTiling结构。 Tiling参数可以通过Host侧GetTiling接口获取，并传递到kernel侧使用。

约束：
- 在分离模式中，本接口必须在InitBuffer接口前调用。
- 在程序中，最多支持定义4个Matmul对象。
- 在Matmul的内部实现中使用了CrossCoreSetFlag和CrossCoreWaitFlag进行核间同步控制，因此开发者同时使用CrossCoreSetFlag（或CrossCoreWaitFlag）和Matmul时，需注意避免核间同步flagId冲突。
- 当代码中只有一个Matmul对象时，本接口可以不传入tiling参数，通过Init接口单独传入tiling参数。
- 当代码中有多个Matmul对象时，必须满足Matmul对象与其tiling参数一一对应，依次传入，具体方式请参考调用示例。

<!-- cannbot:related:start -->
## 相关

- [Matmul高阶API开启纯Cube模式](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_pure_cube.md)（`explains`）：纯 Cube 指南说明“用户使用Matmul高阶API编写算子代码时，可以使用REGIST_MATMUL_OBJ宏，无需区分AIV和AIC”，并据此对比 MIX 消息开销；接口卡则明确“初始化Matmul对象。”，把指南中的宏落到对象初始化及其 tiling/同步资源合同。
- [Init](init.md)（`related`）：Init 页说明“开发者可以先通过［REGIST_MATMUL_OBJ］(regist_matmul_obj.md)不传入Tiling参数对单个Matmul对象进行初始化，后续通过Init接口单独传入Tiling参数”；注册页说明“当代码中只有一个Matmul对象时，本接口可以不传入tiling参数，通过Init接口单独传入tiling参数。”，双方明确给出同一注册后再初始化的调用合同。
<!-- cannbot:related:end -->
