---
type: API
title: LoadData
description: 完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持GM到L0A/L0B Buffer及L1 Buffer到L0A/L0B Buffer通路。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/LoadData_2D.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# LoadData 2D

将数据从L1 Buffer搬运到L0A或L0B Buffer的2D模式搬运接口。支持连续数据搬运和基本的格式转换。通过LoadData2DParams配置搬运参数。函数原型通过模板参数指定数据类型和搬运方向（L0A或L0B）。参数包含dstTensor（L0A/L0B目的）、srcTensor（L1源）、loadDataParams（搬运参数含各维度切分、步长、偏移等）。约束：遵循Cube计算地址对齐和数据排布约束。

<!-- cannbot:related:start -->
## 相关

- [Cube 直调 retCode=0x26：AIV 误跑 Cube API 越界](../../../../../runbooks/compilation/cube_retcode_0x26_aiv_cube_api.md)（`exemplifies`）：函数体调用 Cube 专属 API（`AscendC::LoadData` / `AscendC::Mmad` / `AscendC::Fixpipe`）；将数据从L1 Buffer搬运到L0A或L0B Buffer的2D模式搬运接口。。运行手册把 LoadData 这类 L1→L0 Cube API 放入 AIV 核导致 0x26 的失败路线，直接展示接口所属执行单元约束在编译排障中的应用。
- [SIMD算子实现分离模式](../../../../../guides/operator_practice/simd_operator_impl/matrix_basic_api/decoupled_mode.md)（`explains`）：分离模式 Matmul 规格列出“LoadData（2D矩阵搬运）：L1 Buffer到L0 Buffer数据搬运 + NZ转ZZ/ZN格式转换接口”；LoadData 页定义“将数据从L1 Buffer搬运到L0A或L0B Buffer的2D模式搬运接口。”，两端就是矩阵输入从 L1 到 L0A/L0B 的直接调用链。
- [LoadData（BitMode 2D矩阵搬运）](load_data_2_d_bit_mode.md)（`same_topic`）：“将数据从L1 Buffer搬运到L0A或L0B Buffer的2D模式搬运接口。”与“LoadData 2D的位宽模式变体，支持int4等特定位宽数据类型的搬运。”是双方正文中的具体合同。两端执行同一 L1 到 L0A/L0B 的二维搬运，BitMode 端增加 int4 等位宽解释，互读能决定常规与特定位宽入口。
<!-- cannbot:related:end -->
