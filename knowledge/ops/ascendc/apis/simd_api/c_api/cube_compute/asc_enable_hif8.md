---
type: API
title: AscEnableHif8
description: 用于设置Mmad计算开启HiF8模式，开启后L0A Buffer/L0B Buffer中的8bit数据将在参与矩阵乘法运算前被转化为hifloat8_t类型数据。
tags:
- task.lookup
- topic.programming_model.execution_unit.cube
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_compute/asc_enable_hif8.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
---

# asc_enable_hif8

## 功能说明

用于设置Mmad计算开启HiF8模式，开启该模式后L0A Buffer/L0B Buffer中的8bit数据将在参与矩阵乘法运算前被转化为hifloat8_t类型数据。

## 函数原型

 ```cpp
__aicore__ inline void asc_enable_hif8()
```

## 返回值说明

无

## 流水类型

PIPE_S

## 约束说明

无

## 调用示例

```cpp
constexpr uint64_t total_length = 128;
// 左/右矩阵以 int8_t 存放于 L0A/L0B（需先完成 GM/L1→L0 搬运）
__cc__ int32_t c_matrix[total_length];
__ca__ int8_t a_matrix[total_length];
__cb__ int8_t b_matrix[total_length];

uint16_t left_height = 16;  // M
uint16_t n_dim = 16;        // K
uint16_t right_width = 16;  // N

// 在 asc_mmad 前调用：将 L0 中的 8bit 操作数转换为 hifloat8_t 后参与矩阵运算
asc_enable_hif8();

uint8_t unit_flag = 0;
bool disable_gemv = false;
bool c_matrix_source = false;
bool c_matrix_init_val = true;
asc_mmad_sync(c_matrix, a_matrix, b_matrix, left_height, n_dim, right_width,
              unit_flag, disable_gemv, c_matrix_source, c_matrix_init_val);
```


<!-- cannbot:related:start -->
## 相关

- [AscEnableFp8](asc_enable_fp8.md)（`related`）：用于设置Mmad计算开启FP8模式。该接口会关闭HiF8模式（与asc_enable_hif8相反），开启该模式后L0A Buffer/L0B Buffer中的FP8数据在参与Mmad计算之前不会被转化为hifloat8_t类型数据。；用于设置Mmad计算开启HiF8模式，开启该模式后L0A Buffer/L0B Buffer中的8bit数据将在参与矩阵乘法运算前被转化为hifloat8_t类型数据。两接口控制同一 Mmad 输入解释点的互斥模式，必须一起理解才能正确选择低精度路径。
<!-- cannbot:related:end -->
