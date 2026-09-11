---
type: API
title: MatmulGetTmpBufSize
description: 本接口用于在调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C
  Buffer的使用大小。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.programming_model.execution_unit.cube
status: draft
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/get_Matmul_compute_space/MatmulGetTmpBufSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-04T01:25:11Z'
platforms: []
source_headers:
- include/adv_api/matmul/matmul_tiling.h
---

# MatmulGetTmpBufSize

## 功能说明

本接口用于在调用[GetTiling](../matmul_tiling/get_tiling.md)接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer（UB）/L0C Buffer的使用大小。

## 函数原型

```
int32_t MatmulGetTmpBufSize(optiling::TCubeTiling& tiling, matmul_tiling::SysTilingTempBufSize& bufSize)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| tiling | 输入 | Matmul单核Tiling的结构体，即MatmulTiling对象得到的TCubeTiling结构体。 |
| bufSize | 输出 | Tiling中L1 Buffer/UB/L0C Buffer的使用大小。<br><br>SysTilingTempBufSize结构定义如下方代码所示。 |

```
struct SysTilingTempBufSize {
    int32_t ubSize = 0;  // UB大小
    int32_t l1Size = 0;  // L1 Buffer大小
    int32_t l0cSize = 0; // L0C Buffer大小
};
```

## 返回值说明

-1表示获取失败； 0表示获取成功。

## 约束说明

无

## 调用示例

```
auto ascendcPlatform = platform_ascendc::PlatformAscendC(context->GetPlatformInfo());
matmul_tiling::MatmulApiTiling tiling(ascendcPlatform);
optiling::TCubeTiling tilingData;
...                                         // 初始化tilingData，详见MatmulTiling类使用说明
    int ret = tiling.GetTiling(tilingData); // 获取Tiling参数
SysTilingTempBufSize bufSize;
MatmulGetTmpBufSize(tilingData, bufSize);
```


<!-- cannbot:related:start -->
## 相关

- [GetTiling](../matmul_tiling/get_tiling.md)（`related`）：“- tiling（输出）：Tiling结构体存储最终的tiling结果。TCubeTiling结构介绍请参考表1。/optiling::TCubeTiling：带有optiling命名空间的TCubeTiling结构体，，该结构体为Host侧定义的Matmul TilingData。”；“本接口用于在调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。”。MatmulGetTmpBufSize 明确消费 GetTiling 的结果以计算三级 Buffer 资源预算。
- [SetLocalWorkspace](../matmul_kernel/set_local_workspace.md)（`related`）：“具体需要申请的UB（VECCALC）临时空间大小由tiling接口MatmulGetTmpBufSize给出”明确 SetLocalWorkspace 的容量来源；“本接口用于在调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。”定义该容量查询的调用阶段和输出范围。
- [MatmulGetTmpBufSizeV2](matmul_get_tmp_buf_size_v2.md)（`same_topic`）：“本接口用于在调用GetTiling接口获取Tiling参数后，根据Tiling结构体信息获取L1 Buffer/Unified Buffer/L0C Buffer的使用大小。”与“TCubeTiling为Kernel侧定义的Matmul TilingData，与入参为带AscendC::tiling命名空间的TCubeTiling结构体的GetTiling接口配合使用。”描述同一 Matmul 临时空间查询契约，V2 明确了 kernel 侧结构和配套重载。
<!-- cannbot:related:end -->
