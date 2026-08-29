---
type: API
title: AscL13dFmatrixConfig
description: 用于设置3D格式搬运接口的Feature map属性参数，包括宽高和四周填充大小。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/struct/asc_l13d_fmatrix_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# AscL13dFmatrixConfig

asc_l13d_fmatrix_config用于设置asc_copy_l12l0a/asc_copy_l12l0b的3D格式搬运接口的Feature map属性参数。
约束：asc_l13d_fmatrix_config类型的联合体变量被定义后必须对l1_height和l1_width进行赋值以符合实际场景及取值范围要求。
详见源文档获取完整说明。

<!-- cannbot:related:start -->
## 相关

- [AscSetL13dFmatrix](../cube_data_move/asc_set_l13d_fmatrix.md)（`related`）：asc_l13d_fmatrix_config用于设置asc_copy_l12l0a/asc_copy_l12l0b的3D格式搬运接口的Feature map属性参数；设置Feature map属性描述，用于在调用asc_copy_l12l0a/asc_copy_l12l0b的3D格式搬运接口时配置填充数值。结构体卡定义 Feature map 配置载体，设置接口把该描述写入 3D 搬运状态；联合阅读可确定 asc_copy_l12l0a/b 前的参数构造与设置顺序。
<!-- cannbot:related:end -->
