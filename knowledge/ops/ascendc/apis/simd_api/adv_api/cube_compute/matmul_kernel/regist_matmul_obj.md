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

- [Matmul高阶API开启纯Cube模式](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_pure_cube.md)（`explains`）：《REGIST_MATMUL_OBJ》明确“初始化Matmul对象。”；它与《Matmul高阶API开启纯Cube模式》的“本案例呈现了在矩阵乘算子场景中，开启Matmul高阶API的纯Cube模式对算子性能的提升效果。如下图所示，Matmul API默认使用MIX模式，即用户从AIV侧发起消息，通过消息通信框架中转消息后，在AIC侧执行Matmul计算。这套消息处理机制会带来额外的Scalar性能开销。相较于MIX模式，纯Cube模式可以直接跳过消息通信框架，完成Matmul计算，提升算子性能。”在实际调用参数、数据流或结果校验上直接衔接。
- [GetMatmulApiTiling](get_matmul_api_tiling.md)（`related`）：REGIST_MATMUL_OBJ 要求传入 TCubeTiling；GetMatmulApiTiling 是 Host 侧获得这一 tiling 的配套入口。
- [GetNormalConfig](get_normal_config.md)（`related`）：GetNormalConfig 与《REGIST_MATMUL_OBJ》的实质衔接是：GetNormalConfig 生成 MatmulConfig 并选择 Norm/MDL/Basic 等模板参数；batchLoop 和 VecND2NZ 会直接要求 IterateNBatch、local workspace 与对应搬运路径，tiling/注册材料说明配置如何被消费。
- [GetSubBlockIdx](get_sub_block_idx.md)（`related`）：GetSubBlockIdx 与《REGIST_MATMUL_OBJ》的实质衔接是：Matmul 子核 ID 在 REGIST_MATMUL_OBJ 后初始化，可由 SetSubBlockIdx 覆盖；基础/C API 的逻辑 ID 与 subBlockNum 给出分离架构编号边界，故障卡验证双 AIV 契约。
- [Init](init.md)（`related`）：Tiling 固定时应在 REGIST_MATMUL_OBJ 阶段完成初始化；只有 tiling 运行期变化时才单独反复调用 Init。
- [MatmulCallBackFunc](matmul_call_back_func.md)（`related`）：《MatmulCallBackFunc》说明模板参数，支持用户定制化Matmul的A、B、C矩阵搬入搬出功能，传入自定义回调函数指针替换默认搬运函数。；《REGIST_MATMUL_OBJ》说明初始化Matmul对象。。二者在回调类型由Matmul模板参数、配置与Policy实例化，并经注册宏和用户自定义信息进入Kernel侧Matmul对象上存在可执行的直接衔接。
- [Matmul使用说明](matmul_usage.md)（`related`）：Matmul 使用说明落实 REGIST 必须早于 InitBuffer、对象数上限和多对象 tiling 配对的调用顺序。
- [Matmul Kernel侧接口](matmul_kernel.md)（`same_topic`）：“Matmul Kernel侧接口”处理提供Matmul矩阵乘的Kernel侧接口，包含模板参数、配置类、Init、SetTensorA/B、Iterate等方法及使用说明。；“REGIST_MATMUL_OBJ”明确初始化Matmul对象。。实质衔接：Kernel 侧总览额外给出了注册对象、Init、设置 A/B、Iterate、GetTensorC 的最小调用顺序；只连接这条正文明确的主路径。
- [SetSubBlockIdx](set_sub_block_idx.md)（`same_topic`）：SetSubBlockIdx：SetSubBlockIdx与GetSubBlockIdx是同一 AIV 子核身份的写读契约，REGIST_MATMUL_OBJ会自动设置该值；双 AIV flag runbook说明错误 subBlock 身份如何破坏跨核同步。 目标卡《REGIST_MATMUL_OBJ》补充：初始化Matmul对象。
<!-- cannbot:related:end -->
