---
type: API
title: SetFmatrix
description: 调用LoadData（卷积数据搬运）时设置FeatureMap的属性描述，包括l1H、l1W、padList和fmatrixMode，需在LoadData接口前调用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_load_aux_config/SetFmatrix.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetFmatrix

调用 LoadData（卷积数据搬运）时设置 FeatureMap 属性描述。当 LoadData 模板参数 isSetFMatrix 为 false 时，须通过本接口设置 FeatureMap 属性。头文件 `basic_api/kernel_operator_mm_intf.h`。

参数：l1H[1,32767]源操作数高度、l1W[1,32767]源操作数宽度、padList[4]（left/right/top/bottom，每个 [0,255]，默认 {0,0,0,0}）、fmatrixMode（FmatrixMode 类型，当前仅支持 FMATRIX_LEFT，左右矩阵均用该配置）。

支持 950/a2/a3/Atlas 200I/500 A2/Atlas 推理 AI Core/Kirin X90/9030，不支持 Vector Core 和 Atlas 训练系列。
