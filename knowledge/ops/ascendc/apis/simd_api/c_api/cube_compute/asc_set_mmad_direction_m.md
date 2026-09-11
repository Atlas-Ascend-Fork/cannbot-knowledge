---
type: API
title: AscSetMmadDirectionM
description: 设置矩阵乘加计算（Mmad）时逐列生成结果分形，只改变L0C Buffer上分形生成顺序，不改变计算结果。适用于UnitFlag场景下与搬出顺序一致以提升性能。
tags:
- task.lookup
- topic.programming_model.execution_unit.cube
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_compute/asc_set_mmad_direction_m.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
source_headers:
- include/c_api/asc_simd.h
---

# asc_set_mmad_direction_m

## 功能说明

本接口用于设置矩阵乘加计算（Mmad）时逐列生成矩阵计算结果分形。该配置只改变L0C Buffer上结果分形的生成顺序，不改变计算结果、乘加次数或输出格式。

在开启UnitFlag的场景下，当L0C Buffer上结果分形的生成顺序与数据搬出指令的搬出顺序保持一致时，可以获得更好的性能表现，因此本接口可用于以下场景：

- UnitFlag关闭时作为所有搬出场景的默认配置（此时不同的结果生成方向通常没有实质性能差异）。
- UnitFlag开启且搬出时不进行随路格式转换，且未因开启B8/B4量化触发Channel Merge功能。
- UnitFlag开启且搬出时开启Nz2DN随路格式转换。

## 函数原型

```c
__aicore__ inline void asc_set_mmad_direction_m()
```

## 参数说明

无

## 返回值说明

无

## 流水类型

PIPE_S

## 约束说明

- 本接口需在矩阵乘加指令（[asc_mmad](asc_mmad.md)、[asc_mmad_mx](asc_mmad_mx.md)）执行前调用，以此来确保模式配置在矩阵乘加计算过程中生效。
- 方向配置一旦写入会持续生效，后续矩阵乘加指令若不显式重新配置，将沿用当前方向配置。如需切换为逐行生成矩阵计算结果分形，请重新调用[asc_set_mmad_direction_n](asc_set_mmad_direction_n.md)接口。


## 调用示例

将代码保存为`example.asc`后，可通过`bisheng`命令编译运行，其中`--npu-arch`参数需根据实际产品型号指定对应的NPU架构，具体产品与NPU架构的映射关系请参考[\_\_NPU\_ARCH\_\_](../../../../guides/programming_guide/language_extension/simd_builtin_keywords.md#npu-arch)。

以Ascend 950PR/Ascend 950DT产品（对应NPU架构为`dav-3510`）为例，编译运行命令如下：

```bash
bisheng example.asc -o main --npu-arch=dav-3510 && ./main
```

以下调用示例代码仅Ascend 950PR/Ascend 950DT产品支持。

```cpp
#include <chrono>
#include <cstdint>
#include <iostream>
#include <vector>
#include "c_api/asc_simd.h"
#include "acl/acl.h"

namespace {
constexpr uint32_t M = 16, K = 32, N = 16;

__global__ __cube__ void asc_set_mmad_direction_m_kernel(
    __gm__ int8_t* a, __gm__ int8_t* b, __gm__ int32_t* output, uint32_t n_first)
{
    asc_init();
    __cbuf__ int8_t a_l1[M * K], b_l1[K * N];
    __ca__ int8_t a_l0[M * K];
    __cb__ int8_t b_l0[K * N];
    __cc__ int32_t c_l0[M * N];
    asc_set_gm2l1_nz_para(1, 1, 32, 0);
    asc_copy_gm2l1_nd2nz(a_l1, a, K, 0, M, K, 0, false);
    asc_set_gm2l1_nz_para(1, 1, 32, 0);
    asc_copy_gm2l1_nd2nz(b_l1, b, N, 0, K, N, 0, false);
    asc_sync_notify(PIPE_MTE2, PIPE_MTE1, EVENT_ID0);
    asc_sync_wait(PIPE_MTE2, PIPE_MTE1, EVENT_ID0);
    asc_copy_l12l0a(a_l0, a_l1, 0, 0, 1, 1, 1, 1);
    asc_copy_l12l0b_trans(b_l0, b_l1, static_cast<uint16_t>(0), static_cast<uint8_t>(1),
        static_cast<uint16_t>(2), static_cast<uint16_t>(1), static_cast<uint16_t>(0), static_cast<uint16_t>(0));
    asc_sync_notify(PIPE_MTE1, PIPE_M, EVENT_ID0);
    asc_sync_wait(PIPE_MTE1, PIPE_M, EVENT_ID0);
    if (n_first) asc_set_mmad_direction_n();
    else asc_set_mmad_direction_m();
    asc_mmad(c_l0, a_l0, b_l0, M, K, N, 0, true, false, true);
    asc_sync_notify(PIPE_M, PIPE_FIX, EVENT_ID0);
    asc_sync_wait(PIPE_M, PIPE_FIX, EVENT_ID0);
    asc_set_l0c_copy_nz_para(1, 0, 0);
    asc_copy_l0c2gm(output, c_l0, N, M, N, M, 0, 0, 0,
        static_cast<uint64_t>(QuantMode_t::NoQuant), 0, false, true,
        static_cast<uint64_t>(QuantMode_post::NoConv), 0, false, 0, false, false, false, false);
    asc_sync_pipe(PIPE_ALL);
}

void print_row(const char* label, const std::vector<int32_t>& data)
{
    std::cout << label << ':';
    for (uint32_t i = 0; i < 8; ++i) std::cout << ' ' << data[i];
    std::cout << " ..." << std::endl;
}
} // namespace

int main()
{
    std::vector<int8_t> a(M * K), b(K * N);
    std::vector<int32_t> m_first(M * N), n_first(M * N), golden(M * N);
    for (uint32_t row = 0; row < M; ++row) for (uint32_t k = 0; k < K; ++k)
        a[row * K + k] = static_cast<int8_t>((row + k) % 5 - 2);
    for (uint32_t k = 0; k < K; ++k) for (uint32_t col = 0; col < N; ++col)
        b[k * N + col] = static_cast<int8_t>((k + 2 * col) % 7 - 3);
    for (uint32_t row = 0; row < M; ++row) for (uint32_t col = 0; col < N; ++col)
        for (uint32_t k = 0; k < K; ++k) golden[row * N + col] += a[row * K + k] * b[k * N + col];
    aclInit(nullptr);
    aclrtSetDevice(0);
    int8_t *a_device = nullptr, *b_device = nullptr;
    int32_t *m_device = nullptr, *n_device = nullptr;
    aclrtMalloc(reinterpret_cast<void**>(&a_device), a.size(), ACL_MEM_MALLOC_HUGE_FIRST);
    aclrtMalloc(reinterpret_cast<void**>(&b_device), b.size(), ACL_MEM_MALLOC_HUGE_FIRST);
    aclrtMalloc(reinterpret_cast<void**>(&m_device), m_first.size() * sizeof(int32_t), ACL_MEM_MALLOC_HUGE_FIRST);
    aclrtMalloc(reinterpret_cast<void**>(&n_device), n_first.size() * sizeof(int32_t), ACL_MEM_MALLOC_HUGE_FIRST);
    aclrtMemcpy(a_device, a.size(), a.data(), a.size(), ACL_MEMCPY_HOST_TO_DEVICE);
    aclrtMemcpy(b_device, b.size(), b.data(), b.size(), ACL_MEMCPY_HOST_TO_DEVICE);
    auto start = std::chrono::steady_clock::now();
    asc_set_mmad_direction_m_kernel<<<1, 0>>>(a_device, b_device, m_device, 0);
    aclrtSynchronizeDevice();
    auto middle = std::chrono::steady_clock::now();
    asc_set_mmad_direction_m_kernel<<<1, 0>>>(a_device, b_device, n_device, 1);
    aclrtSynchronizeDevice();
    auto finish = std::chrono::steady_clock::now();
    aclrtMemcpy(m_first.data(), m_first.size() * sizeof(int32_t), m_device,
        m_first.size() * sizeof(int32_t), ACL_MEMCPY_DEVICE_TO_HOST);
    aclrtMemcpy(n_first.data(), n_first.size() * sizeof(int32_t), n_device,
        n_first.size() * sizeof(int32_t), ACL_MEMCPY_DEVICE_TO_HOST);
    print_row("M-first output row 0", m_first);
    print_row("N-first output row 0", n_first);
    print_row("Golden row 0", golden);
    std::cout << "M-first us: " << std::chrono::duration_cast<std::chrono::microseconds>(middle - start).count()
              << ", N-first us: " << std::chrono::duration_cast<std::chrono::microseconds>(finish - middle).count()
              << std::endl;
    const bool passed = m_first == golden && n_first == golden;
    std::cout << (passed ? "[Success] asc_set_mmad_direction_m preserves MMAD values."
                         : "[Failed] asc_set_mmad_direction_m result mismatch.") << std::endl;
    aclrtFree(a_device); aclrtFree(b_device); aclrtFree(m_device); aclrtFree(n_device);
    aclrtResetDevice(0);
    aclFinalize();
    return passed ? 0 : 1;
}
```



<!-- cannbot:related:start -->
## 相关

- [AscMmad](asc_mmad.md)（`related`）：本接口是Ascend C面向昇腾AI芯片的矩阵乘加（Mmad）核心计算接口；本接口需在矩阵乘加指令（asc_mmad、asc_mmad_mx）执行前调用，以此来确保模式配置在矩阵乘加计算过程中生效。；方向 M 配置是 asc_mmad 执行前的持久前置状态，直接决定结果分形生成顺序。
- [AscSetMmadDirectionN](asc_set_mmad_direction_n.md)（`related`）：M 方向接口规定“如需切换为先沿列方向、再沿行方向生成矩阵计算结果分形，请重新调用asc_set_mmad_direction_n接口。”；N 方向接口反向规定“如需切换为先沿行方向、再沿列方向生成矩阵计算结果分形，请重新调用asc_set_mmad_direction_m接口。”，两端构成依搬出顺序切换结果生成方向的成对配置。
- [UnitFlag](../../basic_api/cube_compute_isasi/mmad_compute_key_features/unit_flag.md)（`related`）：方向 M 卡把使用条件限定为“在开启UnitFlag的场景下，当L0C Buffer上结果分形的生成顺序与数据搬出指令的搬出顺序保持一致时，可以获得更好的性能表现”；UnitFlag 卡说明“Mmad 和 Fixpipe 接口的单元标志机制，以 L0C Buffer 512B 内存块为粒度实现精细化数据同步，降低同步延迟。”，解释方向配置为何必须与细粒度生产/消费顺序一致。
<!-- cannbot:related:end -->
