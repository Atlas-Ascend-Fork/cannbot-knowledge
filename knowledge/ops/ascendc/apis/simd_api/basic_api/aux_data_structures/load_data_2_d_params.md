---
type: API
title: LoadData2DParams
description: LoadData2DParams 是 LoadData 2D（L1→L0A/L0B）的参数结构体，以 512 字节分形为单位配置起始分形、迭代次数、源/目的分形间隔、转置与地址更新方向。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.cube
status: draft
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/LoadData_2D.md
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a/include/basic_api/kernel_struct_mm.h
  role: header
created_at: '2026-10-29T07:13:46Z'
updated_at: "2026-10-31T09:21:53Z"
platforms:
- '950'
- a2
- a3
- 310p
- 310b
- '910'
- kirin_x90
- kirin_9030
source_headers:
- include/basic_api/kernel_struct_mm.h
---

# LoadData2DParams

LoadData2DParams 是 `LoadData`（2D 数据搬运，L1→L0A/L0B）的参数结构体，以 512 字节分形为基本单位描述搬运起始分形、迭代次数、源/目的分形间隔、是否转置以及地址更新方向。接口侧另有同名别名 `LoadData2dParams`。

头文件：`include/basic_api/kernel_struct_mm.h`。别名与结构体声明位于 `:42-66`（固定 commit `016ba4a159eda090c4d60a1cdcd1ccca2a36cb0a`）。

## 结构体定义

```cpp
using LoadData2dParams = struct LoadData2DParams;
struct LoadData2DParams {
    __aicore__ LoadData2DParams() {}

    __aicore__ LoadData2DParams(
        const uint16_t startIndexIn, const uint8_t repeatTimesIn, const uint16_t srcStrideIn, const uint8_t sidIn,
        const uint16_t dstGapIn, const bool ifTransposeIn, const uint8_t addrModeIn)
        : startIndex(startIndexIn),
          repeatTimes(repeatTimesIn),
          srcStride(srcStrideIn),
          sid(sidIn),
          dstGap(dstGapIn),
          ifTranspose(ifTransposeIn),
          addrMode(addrModeIn)
    {}

    uint16_t startIndex = 0;
    uint16_t dstGap = 0;
    uint16_t srcStride = 0;
    bool ifTranspose = 0;
    uint8_t repeatTimes = 0;

    uint8_t sid = 0;
    uint8_t addrMode = 0;
};
```

## 字段说明

| 字段 | 类型 | 语义 |
| --- | --- | --- |
| startIndex | uint16_t | 分形矩阵 ID，即搬运起始位置是源操作数中的第几个分形（0 为第 1 个），取值 [0, 65535]，单位 512 字节，默认 0。 |
| repeatTimes | uint8_t | 迭代次数，每次迭代处理 512 字节数据，取值 [0, 255]；0 表示不搬运（NOP）。 |
| srcStride | uint16_t | 相邻迭代间源操作数前一分形与后一分形起始地址间隔，单位 512 字节，取值 [0, 65535]，默认 0；取 0 表示相邻迭代重复获取同一分形矩阵。 |
| sid | uint8_t | 文档标注为预留扩展参数、已废弃且不做业务处理，设置为 0 即可。 |
| dstGap | uint16_t | 相邻迭代间目的操作数前一分形**结束地址**与后一分形**起始地址**的间隔，单位 512 字节，取值 [0, 65535]，默认 0；取 0 表示相邻 repeat 目的地址间隔 1 个分形即连续存放。 |
| ifTranspose | bool | 是否对每个分形矩阵做转置，默认 false；只有 L1→L0A 与 L1→L0B 通路可开启，开启时源/目的操作数仅支持 b16 数据类型。 |
| addrMode | uint8_t | 多次迭代时源分形索引的更新方向：0（默认）递增，下一次 repeat index = startIndex + srcStride \* repeatTimes；1 递减，下一次 repeat index = startIndex - srcStride \* repeatTimes。文档标注目前仅 GM→L1 通路支持配置该参数，L1→L0 场景保持 0。 |

## 约束与注意事项

- 所有距离参数的单位都是 512 字节分形，与 DataCopyParams 的 32B DataBlock 语义不同，不能互换套用。
- `repeatTimes = 0` 是空操作；配置侧不要用 0 表示"尽量多搬"。
- `srcStride = 0` 有确切含义：相邻迭代复用同一源分形；`dstGap = 0` 则等价于目的侧连续排列。
- `ifTranspose` 只在 L1→L0A/L0B 通路且数据类型为 b16 时有效，其他组合不应依赖该开关。
- `addrMode` 文档只对 GM→L1 通路开放，L1→L0 场景保持默认 0，且该参数不影响性能。

## 来源锚点

- 声明：`include/basic_api/kernel_struct_mm.h:42-66`（`:42` 为别名 `using LoadData2dParams = struct LoadData2DParams;`）。
- 字段语义：`docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/LoadData_2D.md` 表2（`:82-93`）、产品支持情况 `:3-33`。

## 相关 runbook

- [V220 逐分形手工 3D im2col/L0A 装载](../../../../runbooks/compilation/ol_197_v220_manual_per_fractal_3d_im2col_cube_operand_loa.md)
- [DAV M200 上 Cube 仅可经 raw Mmad 使用](../../../../runbooks/compilation/dav_m200_cube_available_via_raw_mmad.md)
