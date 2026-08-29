---
type: API
title: MatmulCallBackFunc
description: 模板参数，支持用户定制化Matmul的A、B、C矩阵搬入搬出功能，传入自定义回调函数指针替换默认搬运函数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/MatmulCallBackFunc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# MatmulCallBackFunc

模板参数MatmulCallBackFunc支持用户定制化Matmul的A矩阵、B矩阵及C矩阵的搬入搬出功能，如非连续搬入或针对搬出设置不同的数据片段间隔等。具体方式为：用户根据实际需要，实现一个或多个自定义的搬运函数，定义Matmul对象时，通过模板参数MatmulCallBackFunc，传入实现的搬运函数的函数指针，传入的函数指针会替换Matmul流程中默认的搬运函数。 MatmulCallBackFunc中包含3个可由用户自定义的回调函数接口，即用户可配置3个函数指针。3个函数指针分别为C矩阵从L0C Buffer（CO1）拷贝到GM，A矩阵从GM拷贝到L1 Buffer（A1）），B矩阵从GM拷贝到L1 Buffer（B1）的回调函数指针。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Kirin X90。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品、Kirin 9030。

<!-- cannbot:related:start -->
## 相关

- [SetSelfDefineData](set_self_define_data.md)（`related`）：“用户可配置3个函数指针”定义回调入口，“设置需要的计算数据或在GM上存储的数据地址等信息，用于回调函数使用”说明回调依赖自定义运行数据时如何注入。
- [SetUserDefInfo](set_user_def_info.md)（`related`）：“用户可配置3个函数指针”定义 Matmul 回调，“设置算子tiling地址，用于回调函数使用”说明回调读取 tiling 信息时的配套初始化接口。
- [MatmulTemplateParams](matmul_template_params.md)（`same_topic`）：“通过模板参数MatmulCallBackFunc，传入实现的搬运函数的函数指针”定义回调定制方式，“MM_CB = MatmulCallBackFunc<nullptr, nullptr, nullptr>”给出该回调在 Matmul 模板参数中的实际槽位与默认值。
<!-- cannbot:related:end -->
