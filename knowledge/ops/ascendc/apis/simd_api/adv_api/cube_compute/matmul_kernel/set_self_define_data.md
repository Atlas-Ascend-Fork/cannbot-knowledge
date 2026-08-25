---
type: API
title: SetSelfDefineData
description: 启用模板参数MatmulCallBackFunc（自定义回调函数）时，设置需要的计算数据或在GM上存储的数据地址等信息，用于回调函数使用。复用同一个Matmul对象时，可以多次调用本接口重新设置对应数据信息。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetSelfDefineData.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetSelfDefineData

启用模板参数[MatmulCallBackFunc](matmul_template_params.md#matmul-callback-func)（自定义回调函数）时，设置需要的计算数据或在GM上存储的数据地址等信息，用于回调函数使用。复用同一个Matmul对象时，可以多次调用本接口重新设置对应数据信息。

函数原型：
__aicore__ inline void SetSelfDefineData(const uint64_t dataPtr)
__aicore__ inline void SetSelfDefineData(T dataPtr)

参数：
- dataPtr（输入）：设置的算子回调函数需要的计算数据或在GM上存储的数据地址等信息。其中，类型T支持用户自定义基础结构体。

约束：
- 若回调函数中需要使用dataPtr参数时，必须调用此接口；若回调函数不使用dataPtr参数，无需调用此接口。
- 当开启MixDualMaster（双主模式）场景时，即模板参数enableMixDualMaster设置为true，不支持使用该接口。
- 本接口必须在SetTensorA接口、SetTensorB接口之前调用。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Kirin X90。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [MatmulCallBackFunc](matmul_call_back_func.md)（`related`）：《MatmulCallBackFunc》说明模板参数，支持用户定制化Matmul的A、B、C矩阵搬入搬出功能，传入自定义回调函数指针替换默认搬运函数。；《SetSelfDefineData》说明启用模板参数MatmulCallBackFunc（自定义回调函数）时，设置需要的计算数据或在GM上存储的数据地址等信息，用于回调函数使用。复用同一个Matmul对象时，可以多次调用本接口重新设置对应数据信息。。二者在回调类型由Matmul模板参数、配置与Policy实例化，并经注册宏和用户自定义信息进入Kernel侧Matmul对象上存在可执行的直接衔接。
- [SetTensorA](set_tensor_a.md)（`related`）：SetSelfDefineData：SetSelfDefineData 只为 MatmulCallBackFunc 提供每次复用可更新的数据指针，模板声明决定回调契约，且正文明确要求它先于 SetTensorA/SetTensorB。 目标卡《SetTensorA》补充：设置矩阵乘的左矩阵A。
- [SetTensorB](set_tensor_b.md)（`related`）：SetSelfDefineData：SetSelfDefineData 只为 MatmulCallBackFunc 提供每次复用可更新的数据指针，模板声明决定回调契约，且正文明确要求它先于 SetTensorA/SetTensorB。 目标卡《SetTensorB》补充：设置矩阵乘的右矩阵B。
- [MatmulTemplateParams](matmul_template_params.md)（`same_topic`）：SetSelfDefineData：SetSelfDefineData 只为 MatmulCallBackFunc 提供每次复用可更新的数据指针，模板声明决定回调契约，且正文明确要求它先于 SetTensorA/SetTensorB。 目标卡《MatmulTemplateParams》补充：创建Matmul对象时需要传入的模板参数，包括A/B/C/Bias类型信息、MatmulConfig、MatmulCallBackFunc和MatmulPolicy。
- [SetUserDefInfo](set_user_def_info.md)（`same_topic`）：SetUserDefInfo 与《SetSelfDefineData》的实质衔接是：SetUserDefInfo 只在 MatmulCallBackFunc 使用 tilingPtr 时需要；SetSelfDefineData承载回调的可变数据，模板参数和使用说明决定回调是否启用。
<!-- cannbot:related:end -->
