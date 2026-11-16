---
type: Guide
title: 经典 Cube 搬运流水全链与 LocalMemAllocator/TBuf 两种内存分配形式
description: Cube 核数据流水全链：TPosition 定位的 L1/L0A/L0B/L0C 分级分配、DataCopy(Nd2Nz) GM→L1、LoadData L1→L0（2201 与 3510 变体差异）、Mmad 计算与 Fixpipe 回写，SetFlag/WaitFlag 串联 MTE2_MTE1/MTE1_M/M_FIX 流水依赖；覆盖经典 TBuf 与静态 Tensor LocalMemAllocator 两种内存分配形式。
tags:
- task.implementation
- topic.implementation.memory_management
- topic.implementation.synchronization
- topic.programming_model.execution_unit.cube
status: draft
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/92ab0ff5fcdc0c5d8bb48be128b2c6a77654acde/examples/01_simd_cpp_api/00_introduction/02_matrix/matmul_basic_api/matmul_basic_api.asc
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/92ab0ff5fcdc0c5d8bb48be128b2c6a77654acde/examples/01_simd_cpp_api/03_basic_api/00_data_movement/data_copy_gm2l1/data_copy_gm2l1.asc
  role: supporting
- resource: https://gitcode.com/cann/asc-devkit/blob/92ab0ff5fcdc0c5d8bb48be128b2c6a77654acde/examples/01_simd_cpp_api/03_basic_api/03_matrix_compute/fixpipe_l0c2gm/fixpipe_l0c2gm.asc
  role: supporting
created_at: '2026-10-10T06:41:29Z'
updated_at: '2026-10-10T09:52:36Z'
platforms:
- '950'
- a2
- a3
---

# 经典 Cube 搬运流水全链与 LocalMemAllocator/TBuf 两种内存分配形式

## 适用场景

直接编排 Cube 核数据流水（不经高阶 Matmul 模板）：basic_api 自排 Mmad/Fixpipe 的算子、需要精细控制 L1/L0 分块与流水事件的场景。两种内存分配形式：经典 TPipe+TBuf 时代的 `TBuf<TPosition>` 声明式分配，与静态 Tensor 编程的 `LocalMemAllocator` 顺序分配。

## 链路骨架（静态 Tensor 形态，`__cube__` 核）

```cpp
__global__ __cube__ void mmad_custom(__gm__ uint8_t* a, __gm__ uint8_t* b, __gm__ uint8_t* c)
{
    AscendC::InitSocState();
    uint32_t mIterIdx = AscendC::GetBlockIdx() % (M / singleCoreM);   // 按 M 分核
    aGM.SetGlobalBuffer(...);  bGM.SetGlobalBuffer(...);  cGM.SetGlobalBuffer(...);

    AscendC::LocalMemAllocator<Hardware::L1>  l1Allocator;    // 分级分配器
    AscendC::LocalMemAllocator<Hardware::L0A> l0aAllocator;
    AscendC::LocalMemAllocator<Hardware::L0B> l0bAllocator;
    AscendC::LocalMemAllocator<Hardware::L0C> l0cAllocator;
    LocalTensor<half> a1Local = l1Allocator.Alloc<TPosition::A1, half>(baseM * baseK);   // A1/B1 在 L1
    LocalTensor<half> a2Local = l0aAllocator.Alloc<TPosition::A2, half>(baseM * baseK);  // A2/B2 在 L0A/L0B
    LocalTensor<float> cLocal = l0cAllocator.Alloc<TPosition::CO1, float>(baseM * baseN);

    AscendC::DataCopy(a1Local, aGM, AscendC::Nd2NzParams{1, baseM, baseK, 0, K, baseM, 1, 0});  // GM→L1（ND→NZ）
    AscendC::SetFlag<HardEvent::MTE2_MTE1>(EVENT_ID0);
    AscendC::WaitFlag<HardEvent::MTE2_MTE1>(EVENT_ID0);   // MTE1 等 MTE2

    AscendC::LoadData(a2Local, a1Local, AscendC::LoadData2DParamsV2{...});   // L1→L0A（3510 整块）
    AscendC::SetFlag<HardEvent::MTE1_M>(EVENT_ID0);
    AscendC::WaitFlag<HardEvent::MTE1_M>(EVENT_ID0);      // M 等 MTE1

    AscendC::Mmad(cLocal, a2Local, b2Local, AscendC::MmadParams{...});       // L0A×L0B→L0C
    AscendC::SetFlag<HardEvent::M_FIX>(EVENT_ID0);
    AscendC::WaitFlag<HardEvent::M_FIX>(EVENT_ID0);       // FIX 等 M

    AscendC::Fixpipe(cGM, cLocal, ...);                   // L0C→GM，接口名是 Fixpipe
}
```

**经典 TBuf 分配形式（与上文的静态 Tensor 分配形式对比）**：两种分配形式的数据流水与事件链完全一致（DataCopy(Nd2Nz) → LoadData → Mmad → Fixpipe，三段 SetFlag/WaitFlag 不变），差异只在内存声明与分配方式——

- 静态 Tensor 分配形式（上文骨架）：`__cbuf__/__ca__/__cb__/__cc__` 存储类声明 + `LocalMemAllocator<Hardware::L1/L0A/L0B/L0C>` 逐层 `Alloc`，地址由分配器静态管理；
- 经典 TBuf 分配形式：`AscendC::TBuf<AscendC::TPosition::A1> a1Buf;` + `pipe.InitBuffer(a1Buf, len)`——经 TPipe 托管分配（注意是 [TPipe::InitBuffer](../../apis/simd_api/basic_api/resource_management/t_pipe/init_buffer.md)，不是资源池上的 [TBufPool::InitBuffer](../../apis/simd_api/basic_api/resource_management/t_buf_pool/init_buffer.md)，同名接口调用对象不同）。

## 成员职责

| 环节 | API |
|---|---|
| 分核/入口 | [InitSocState](../../apis/simd_api/basic_api/tool_interface/system_init/init_soc_state.md)、[GetBlockIdx](../../apis/simd_api/basic_api/tool_interface/system_resources_and_variables/get_block_idx.md) |
| 内存 | [LocalMemAllocator](../../apis/simd_api/basic_api/resource_management/local_mem_allocator/local_mem_allocator_constructor.md)/[Alloc](../../apis/simd_api/basic_api/resource_management/local_mem_allocator/alloc.md)、[TPosition](../../apis/simd_api/basic_api/aux_data_structures/t_position.md)、[TPipe](../../apis/simd_api/basic_api/resource_management/t_pipe/t_pipe_intro.md)/[TPipe::InitBuffer](../../apis/simd_api/basic_api/resource_management/t_pipe/init_buffer.md)（经典形态） |
| 搬运 | [DataCopy GM→L1](../../apis/simd_api/basic_api/cube_compute_isasi/cube_compute_load/data_copy_gm_to_l1_continuous.md)、[LoadData 2D](../../apis/simd_api/basic_api/cube_compute_isasi/cube_compute_load/load_data_2_d.md)（2201）/ [LoadData 2D V2](../../apis/simd_api/basic_api/cube_compute_isasi/cube_compute_load/load_data_2_d_v2.md)（3510）、[Fixpipe](../../apis/simd_api/basic_api/cube_compute_isasi/cube_compute_store/fixpipe_l0_c_to_gm.md) |
| 同步 | [SetFlag/WaitFlag](../../apis/simd_api/basic_api/sync_control/intra_core_sync/set_flag_wait_flag_isasi.md) |

## 跨 API 联动约束

1. **TPosition-层级绑定**：A1/B1↔L1、A2/B2↔L0A/L0B、CO1/CO2↔L0C——`Alloc` 的模板参数与分配器层级必须配对，错配在编译期或运行期失败。
2. **三段事件链方向固定**：`MTE2_MTE1`（LoadData 等 DataCopy）→ `MTE1_M`（Mmad 等 LoadData）→ `M_FIX`（Fixpipe 等 Mmad）；方向反写会读到未完成数据。
3. **Nd2Nz 参数语义**：`{ndNum, nValue, dValue, srcNdMatrixStride, srcDValue, dstNzC0Stride, dstNzNStride, dstNzMatrixStride}`——源按 ND 布局步进、目的按 NZ 布局步进，base 块形状（baseM/baseK/baseN）同时决定 DataCopy 与 LoadData 的切分参数。
4. **预算→分块→布局自洽**：baseM/baseK/baseN 必须装得进 L1/L0 预算（自排流水手工核算），分块参数又决定 LoadData/Fixpipe 的步进与 repeat。
5. **LoadData 的 arch 变体**：2201 用逐 16 块循环 + `LoadData2DParams{startIndex, repeatTimes, srcStride, sid, dstGap, ifTranspose, addrMode}`；3510 用整块 + `LoadData2DParamsV2{mStartPosition, kStartPosition, mStep, kStep, srcStride, dstStride, ifTranspose, sid}`。官方样例分成两支：`#if defined(__NPU_ARCH__) && (__NPU_ARCH__ == 2201)` 与 `#elif defined(__NPU_ARCH__) && (__NPU_ARCH__ == 3510)`。

## 失效边界与常见错误

- **arch 变体错配**（对抗验证高频陷阱）：2201 参数形态用在 3510 编译目标上（或引用了错误 arch 的知识卡），切分语义完全不同；
- 事件方向写反或 EVENT_ID 复用冲突；
- base 块超 L1/L0C 预算：LoadData/Fixpipe 越界，需回退 base 块并重算 Nd2Nz 步进；
- 本流水不覆盖 Vector 侧消费——AIV 侧衔接见[Cube+Vector 融合范式](cube_vector_fusion_pattern.md)；高阶封装见[高阶 Matmul 全链路](high_level_matmul_full_chain.md)。

## 验证方式

- 分核对拍：单核（M ≤ singleCoreM）先过，再多核对拍；
- 事件链压力：base 块调大观察 LoadData 死等（MTE1_M 提前等待未完成搬运）；
- Fixpipe 布局对拍：cGM 输出与参考矩阵按 NZ→ND 还原后比较。
