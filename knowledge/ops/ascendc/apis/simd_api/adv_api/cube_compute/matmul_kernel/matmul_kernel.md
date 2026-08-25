---
type: API
title: Matmul Kernel侧接口
description: 提供Matmul矩阵乘的Kernel侧接口，包含模板参数、配置类、Init、SetTensorA/B、Iterate等方法及使用说明。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/Matmul_Kernel.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Matmul Kernel侧接口

提供矩阵乘计算的 Kernel 侧接口，通过模板参数与 MatmulConfig 配置矩阵排布、数据类型及计算模式。
核心流程为 Init 初始化后，使用 SetTensorA/SetTensorB 设置左右矩阵，SetTensorScaleA/SetTensorScaleB 设置量化缩放因子，SetBias/SetAntiQuantScalar 等设置偏置与反量化参数，再经 Iterate/IterateAll/IterateBatch 执行计算，最后 GetTensorC/AsyncGetTensorC 获取结果。
支持多种配置获取方法（GetNormalConfig、GetMDLConfig、GetIBShareNormConfig 等）适配不同硬件特性，并提供 SetHF32、SetQuantVector、SetSparseIndex 等高级特性开关。
REGIST_MATMUL_OBJ 宏用于注册 Matmul 对象，使其在 Kernel 中可用。

<!-- cannbot:related:start -->
## 相关

- [Matmul高阶API开启IBShare模板共享B矩阵数据](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_ibshare_b.md)（`explains`）：Matmul高阶API开启IBShare模板共享B矩阵数据 与《Matmul Kernel侧接口》的实质衔接是：IBShare 的 B-only 配置受 MatmulConfig、tiling 策略、preload/MDL 和 kernel Iterate 契约共同约束，直接影响 L1 复用。
- [单次矩阵乘局部输出](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/single_matmul_local_output.md)（`explains`）：单次矩阵乘局部输出 与《Matmul Kernel侧接口》的实质衔接是：Partial Output 只允许 MDL 的 Iterate+GetTensorC 连续写，跳过 K 累加且禁用 Bias/IterateAll；Matmul Kernel、异步/对齐和精度材料直接约束该链。
- [IterateAll](iterate_all.md)（`related`）：《IterateAll》说明调用一次IterateAll，会计算出singleCoreM \ singleCoreN大小的C矩阵。迭代顺序可通过tiling参数iterateOrder调整。；《Matmul Kernel侧接口》说明提供Matmul矩阵乘的Kernel侧接口，包含模板参数、配置类、Init、SetTensorA/B、Iterate等方法及使用说明。。二者在IterateAll一次完成singleCoreM×singleCoreN，异步模式必须配WaitIterateAll并按GetTensorC/输出场景消费结果上存在可执行的直接衔接。
- [MatmulCallBackFunc](matmul_call_back_func.md)（`related`）：《MatmulCallBackFunc》说明模板参数，支持用户定制化Matmul的A、B、C矩阵搬入搬出功能，传入自定义回调函数指针替换默认搬运函数。；《Matmul Kernel侧接口》说明提供Matmul矩阵乘的Kernel侧接口，包含模板参数、配置类、Init、SetTensorA/B、Iterate等方法及使用说明。。二者在回调类型由Matmul模板参数、配置与Policy实例化，并经注册宏和用户自定义信息进入Kernel侧Matmul对象上存在可执行的直接衔接。
- [MatmulPolicy](matmul_policy.md)（`related`）：Matmul Kernel 总览给出对象初始化、计算与输出生命周期，说明策略参数在哪个对象流程中生效。
- [MatmulTemplateParams](matmul_template_params.md)（`related`）：Matmul Kernel 入口说明对象通过模板参数和 MatmulConfig 绑定矩阵排布、dtype 与计算模式，正是 MatmulTemplateParams 的消费位置。
- [GetOffsetC](get_offset_c.md)（`same_topic`）：GetOffsetC 与《Matmul Kernel侧接口》的实质衔接是：GetOffsetC 返回当前 Matmul 分片在完整 C 矩阵的位置；Iterate 推进分片，GetTensorC 消费结果，Kernel/使用说明给出该预留位置信息所在的执行链。
- [GetTensorC](get_tensor_c.md)（`same_topic`）：“Matmul Kernel侧接口”处理提供Matmul矩阵乘的Kernel侧接口，包含模板参数、配置类、Init、SetTensorA/B、Iterate等方法及使用说明。；“GetTensorC”明确Iterate后获取C矩阵分片，可输出到GM或UB，支持同步与异步两种模式。。实质衔接：Kernel 侧总览额外给出了注册对象、Init、设置 A/B、Iterate、GetTensorC 的最小调用顺序；只连接这条正文明确的主路径。
- [Init](init.md)（`same_topic`）：“Matmul Kernel侧接口”处理提供Matmul矩阵乘的Kernel侧接口，包含模板参数、配置类、Init、SetTensorA/B、Iterate等方法及使用说明。；“Init”明确对Matmul对象的Tiling数据进行初始化，根据Tiling参数进行资源划分。Tiling参数可变场景下可多次调用。。实质衔接：Kernel 侧总览额外给出了注册对象、Init、设置 A/B、Iterate、GetTensorC 的最小调用顺序；只连接这条正文明确的主路径。
- [Iterate](iterate.md)（`same_topic`）：“Matmul Kernel侧接口”处理提供Matmul矩阵乘的Kernel侧接口，包含模板参数、配置类、Init、SetTensorA/B、Iterate等方法及使用说明。；“Iterate”明确每调用一次计算一块baseM*baseN的C矩阵，内部维护迭代进度并偏移A、B矩阵首地址。。实质衔接：Kernel 侧总览额外给出了注册对象、Init、设置 A/B、Iterate、GetTensorC 的最小调用顺序；只连接这条正文明确的主路径。
- [Matmul使用说明](matmul_usage.md)（`same_topic`）：“Matmul Kernel侧接口”处理提供Matmul矩阵乘的Kernel侧接口，包含模板参数、配置类、Init、SetTensorA/B、Iterate等方法及使用说明。；“Matmul使用说明”明确Ascend C提供一组Matmul高阶API，方便用户快速实现Matmul矩阵乘法的运算操作。。实质衔接：Kernel 侧总览额外给出了注册对象、Init、设置 A/B、Iterate、GetTensorC 的最小调用顺序；只连接这条正文明确的主路径。
- [REGIST_MATMUL_OBJ](regist_matmul_obj.md)（`same_topic`）：“Matmul Kernel侧接口”处理提供Matmul矩阵乘的Kernel侧接口，包含模板参数、配置类、Init、SetTensorA/B、Iterate等方法及使用说明。；“REGIST_MATMUL_OBJ”明确初始化Matmul对象。。实质衔接：Kernel 侧总览额外给出了注册对象、Init、设置 A/B、Iterate、GetTensorC 的最小调用顺序；只连接这条正文明确的主路径。
- [SetTensorA](set_tensor_a.md)（`same_topic`）：“Matmul Kernel侧接口”处理提供Matmul矩阵乘的Kernel侧接口，包含模板参数、配置类、Init、SetTensorA/B、Iterate等方法及使用说明。；“SetTensorA”明确设置矩阵乘的左矩阵A。。实质衔接：Kernel 侧总览额外给出了注册对象、Init、设置 A/B、Iterate、GetTensorC 的最小调用顺序；只连接这条正文明确的主路径。
- [SetTensorB](set_tensor_b.md)（`same_topic`）：“Matmul Kernel侧接口”处理提供Matmul矩阵乘的Kernel侧接口，包含模板参数、配置类、Init、SetTensorA/B、Iterate等方法及使用说明。；“SetTensorB”明确设置矩阵乘的右矩阵B。。实质衔接：Kernel 侧总览额外给出了注册对象、Init、设置 A/B、Iterate、GetTensorC 的最小调用顺序；只连接这条正文明确的主路径。
<!-- cannbot:related:end -->
