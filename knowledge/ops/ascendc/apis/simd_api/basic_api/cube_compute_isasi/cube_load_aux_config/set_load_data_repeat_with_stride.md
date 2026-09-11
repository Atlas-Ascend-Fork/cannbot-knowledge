---
type: API
title: SetLoadDataRepeatWithStride
description: 设置LoadDataWithStride接口的repeat参数，通过一次调用完成多个迭代的数据搬运，并配置输出矩阵K轴方向偏移。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.cube
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_load_aux_config/SetLoadDataRepeatWithStride.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/basic_api/kernel_operator_mm_intf.h
---

# SetLoadDataRepeatWithStride<a id="ZH-CN_TOPIC_0000002583382412"></a>

## 功能说明<a id="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_operator_mm_intf.h"`。

用于设置[LoadDataWithStride](../cube_compute_load/load_data_with_stride.md)接口的repeat参数。设置repeat参数后，可以通过调用一次LoadDataWithStride接口完成多个迭代的数据搬运，还用于配置输出矩阵K轴方向偏移。

## 函数原型<a id="section620mcpsimp"></a>

```cpp
__aicore__ inline void SetLoadDataRepeatWithStride(const LoadDataRepeatParamWithStride& repeatParams)
```

## 参数说明<a id="section622mcpsimp"></a>

**表1** 参数说明

| 参数名称 | 输入/输出 | 含义 |
| --- | --- | --- |
| repeatParams | 输入 | 设置[LoadDataWithStride](../cube_compute_load/load_data_with_stride.md)接口的repeat参数，类型为SetLoadDataRepeatWithStride。<br>具体定义请参考：`${INSTALL_DIR}/asc/include/basic_api/kernel_struct_mm.h`，`${INSTALL_DIR}`请替换为CANN软件安装后文件存储路径。<br>参数说明请参考[表2](#table15780447181826)。 |

**表2** LoadDataRepeatParamWithStride结构体参数说明<a name="table15780447181826"></a>  

| 参数名称 | 含义 |
| -------- | ---- |
| repeatStride | height/width方向上的前一个迭代与后一个迭代起始地址的距离，取值范围：repeatStride∈[0, 65535]，默认值为0。<br>&nbsp;&nbsp;&nbsp;&nbsp;&bull; repeatMode为0，repeatStride的单位为16个元素。<br>&nbsp;&nbsp;&nbsp;&nbsp;&bull; repeatMode为1，repeatStride的单位为32/sizeof(data_type)个元素，data_type指源操作数的数据类型。 |
| repeatTime | height/width方向上的迭代次数，取值范围：repeatTime∈[0, 255]。默认值为1。 |
| repeatMode | 控制repeat迭代的方向，取值范围：repeatMode∈[0, 1]。默认值为0。<br>&nbsp;&nbsp;&nbsp;&nbsp;&bull; 0：迭代沿height方向；<br>&nbsp;&nbsp;&nbsp;&nbsp;&bull; 1：迭代沿width方向。 |
| dstStride | 输出矩阵K轴方向偏移，以512字节的分形为单位。 |

## 返回值说明<a id="section4219135304839"></a>

无

## 约束说明<a id="section633mcpsimp"></a>

- repeatTime=0表示不执行搬运，LoadDataWithStride接口将被视为NOP（空操作）。
- 调用[LoadDataWithStride](../cube_compute_load/load_data_with_stride.md)接口时，必须配置本接口中的dstStride参数，若不使能repeat模式，repeatTime、repeatStride、repeatMode使用默认构造值。

## 调用示例<a id="section1761417552405"></a>

本接口用于配合LoadDataWithStride接口使用，展示代码示例片段：

```cpp
// LoadDataWithStride指令完成img2col的过程，可知 img2col后A矩阵高度为ho * wo,根据ho和wo的计算公式，代入卷积核宽度、卷积核滑动步长、卷积核膨胀系数等参数可知：A矩阵的高度为CeilAlign(k, fractalShape[0])；img2col后A矩阵宽度为ci * kh * kw，代入kh=1，kw=1，可知A矩阵的宽度为CeilAlign(m, fractalShape[1])。最后，配置loadDataParams.enTranspose = true，将整个A 矩阵转置并且将其中每一个分形转置。
AscendC::LoadData3DParamsV2<T> loadDataParams;

// 设置loadDataParams相关参数
...

// 使用SetLoadDataRepeatWithStride接口，设置LoadDataWithStride接口的repeat参数
AscendC::LoadDataRepeatParamWithStride repeatParams;
repeatParams.repeatTime = 1;  // height/width方向上的迭代次数
repeatParams.repeatStride = 1;  // height/width方向上前后迭代起始位置的距离
repeatParams.repeatMode = 0;  // 迭代方向：0：迭代沿height; 1：迭代沿width
repeatParams.dstStride = CeilDivision(m, fractalShape[0]);  // 输出矩阵K轴方向偏移
AscendC::SetLoadDataRepeatWithStride(repeatParams);

AscendC::LoadDataWithStride(a2Local, a1Local, loadDataParams);
```


<!-- cannbot:related:start -->
## 相关

- [LoadDataWithStride](../cube_compute_load/load_data_with_stride.md)（`related`）：将数据从L1 Buffer搬运到L0A或L0B Buffer，支持源侧带步长的数据搬运。；设置 LoadDataWithStride 接口的 repeat 参数，通过一次调用完成多个迭代的数据搬运，并配置输出矩阵 K 轴方向偏移。。前者执行源侧带 stride 的 L1 到 L0A/L0B 搬运，后者直接配置该接口的 repeat 次数与 K 轴偏移，组成多迭代 stride 搬运的参数设置和执行链。
- [SetLoadDataRepeat](set_load_data_repeat.md)（`related`）：焦点卡写明“repeatStride［0,65535］相邻迭代起始地址距离”，候选卡写明“设置 LoadDataWithStride 接口的 repeat 参数”。前者服务普通 LoadData，后者服务 LoadDataWithStride，可据搬运接口选择 repeat 配置。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Conv2D 950 Direct Invoke 算子知识](../../../../../operators/direct/nn/conv/conv_2d_950.md)（`related`）：算子声明的固定版本源码包含对 `SetLoadDataRepeatWithStride(...)` 的直接调用（第 343 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/conv/conv2d_v2/op_kernel/arch35/conv2d_small_kernel.h#L343)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
