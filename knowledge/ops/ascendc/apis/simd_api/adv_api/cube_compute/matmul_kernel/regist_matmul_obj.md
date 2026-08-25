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
