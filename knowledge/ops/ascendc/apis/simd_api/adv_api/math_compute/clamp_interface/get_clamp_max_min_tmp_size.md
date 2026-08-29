---
type: API
title: GetClampMaxMinTmpSize
description: 在host侧获取ClampMax/ClampMin/Clamp接口所需的最大和最小临时空间大小，供开发者选择合适的Tiling参数传入kernel侧。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Clamp_interface/GetClampMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetClampMaxMinTmpSize

host侧Tiling接口，用于获取ClampMax/ClampMin/Clamp接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetClampMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape信息；typeSize为输入数据类型字节数（half传2）；isReuseSource与ClampMax/ClampMin接口保持一致；maxValue输出最大临时空间大小（超出部分不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间，需开发者自行裁剪）；minValue输出最小临时空间大小（实际预留空间不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大，kernel侧计算性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [ClampMax](clamp_max.md)（`related`）：临时空间大小BufferSize的获取方式请参考GetClampMaxMinTmpSize。；host侧Tiling接口，用于获取ClampMax/ClampMin/Clamp接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。ClampMax 的执行需要右侧公共 Clamp 家族接口给出的临时空间范围，但该 Host 接口同时服务 ClampMin 与 Clamp，因此是直接依赖而不是仅属于 ClampMax 的单一合同。
- [ClampMin](clamp_min.md)（`related`）：提供两种重载：通过sharedTmpBuffer入参传入临时空间（开发者自行管理，可复用，内存利用率高），或由接口框架申请临时空间（需预留空间，大小通过GetClampMaxMinTmpSize获取）。；host侧Tiling接口，用于获取ClampMax/ClampMin/Clamp接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。。ClampMin 的框架申请重载明确使用右侧公共接口确定预留大小，但右侧还覆盖另外两个 Clamp 操作，所以保持相关关系。
- [Clamp（数学计算）](clamp.md)（`related`）：“host侧Tiling接口，用于获取ClampMax/ClampMin/Clamp接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”；“将输入中除nan值以外大于max的数替换为max，小于min的数替换为min，小于等于max和大于等于min的数保持不变，作为输出。当min大于max时，将除nan值外所有值替换为max。min和max可以为标量或LocalTensor。”。焦点 Host 接口为 Clamp kernel 计算临时空间上下界，连接 kernel 语义与 workspace 选择。
- [GetClampTmpBufferFactorSize](get_clamp_tmp_buffer_factor_size.md)（`related`）：“host侧Tiling接口，用于获取ClampMax/ClampMin/Clamp接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”；“推算公式：currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。”。焦点接口从 shape 求可用空间范围，factor 接口反向从固定缓冲求单次处理元素数，二者共同完成 Clamp workspace 与 tile 大小设计。
<!-- cannbot:related:end -->
