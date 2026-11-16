---
type: Guide
title: RegBase 寄存器范式：load-compute-store 与掩码条件计算
description: SIMD VF 寄存器级计算范式：外层向量核经 LocalMemAllocator 与事件同步完成 GM↔UB 搬运，asc_vf_call 进入 VF 函数后由 GetVecLen 定 repeat 粒度、MaskReg/RegTensor/UpdateMask/LoadAlign/StoreAlign 完成寄存器级 load-compute-store；含 Reg::Select 掩码条件计算变体。
tags:
- task.implementation
- topic.memory
- topic.programming_model.execution_unit.vector
status: draft
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/92ab0ff5fcdc0c5d8bb48be128b2c6a77654acde/examples/01_simd_cpp_api/00_introduction/04_reg_compute/add/add.asc
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/92ab0ff5fcdc0c5d8bb48be128b2c6a77654acde/examples/01_simd_cpp_api/03_basic_api/02_reg_vector_compute/mul/mul.asc
  role: supporting
- resource: cann-ops-raw/ascendc/ops-cv/bb717d075d129fd1fc7b96b2886824a1d153ed2f/image/resize_bilinear_v2/op_kernel/arch35/resize_bilinear_v2_c_parallel.h
  role: supporting
created_at: '2026-10-10T06:41:29Z'
updated_at: '2026-10-10T09:52:36Z'
platforms:
- '950'
---

# RegBase 寄存器范式：load-compute-store 与掩码条件计算

## 适用场景

950（arch35/3510）RegBase 编程：需要在寄存器上直接完成矢量计算（Add/Mul/Cast/Select 等）以获得最细粒度控制，或与 MicroAPI 枚举（MaskMergeMode/RegLayout/SatMode/PostLiteral）联合配置类型转换与掩码行为。

## 链路骨架

**外层（向量核：搬运与同步）**：

```cpp
__global__ __vector__ void vector_add(__gm__ uint8_t* x, __gm__ uint8_t* y)
{
    AscendC::InitSocState();
    xGm.SetGlobalBuffer(reinterpret_cast<__gm__ float*>(x));
    uint32_t coreOffset = AscendC::GetBlockIdx() * singleCoreLength;
    AscendC::LocalMemAllocator<Hardware::UB> ubAllocator;
    LocalTensor<float> yLocal = ubAllocator.Alloc<float, singleCoreLength>();

    AscendC::DataCopy(yLocal, xGm[coreOffset], singleCoreLength);   // GM→UB
    AscendC::SetFlag<HardEvent::MTE2_V>(EVENT_ID0);
    AscendC::WaitFlag<HardEvent::MTE2_V>(EVENT_ID0);

    __ubuf__ float* dstAddr = reinterpret_cast<__ubuf__ float*>(yLocal.GetPhyAddr());  // 取 UB 裸指针
    asc_vf_call<AddVF<float, singleCoreLength>>(dstAddr, singleCoreLength);            // 进入 VF 函数（C API 形态入口）

    AscendC::SetFlag<HardEvent::V_MTE3>(EVENT_ID0);
    AscendC::WaitFlag<HardEvent::V_MTE3>(EVENT_ID0);
    AscendC::DataCopy(yGm[coreOffset], yLocal, singleCoreLength);   // UB→GM
}
```

**内层（VF 函数：寄存器循环）**：

```cpp
template <typename T, uint32_t singleCoreLength>
__simd_vf__ inline void AddVF(__ubuf__ T* dstAddr, uint32_t count)
{
    constexpr uint32_t oneRepeatSize = AscendC::GetVecLen() / sizeof(T);   // repeat 粒度
    uint32_t repeatTimes = DivCeil(singleCoreLength, oneRepeatSize);
    AscendC::Reg::MaskReg mask;
    AscendC::Reg::RegTensor<T> srcReg, dstReg;
    for (uint32_t i = 0; i < repeatTimes; ++i) {
        mask = AscendC::Reg::UpdateMask<T>(count);          // 每轮重生成有效元素掩码
        // 注意：LoadAlign 无掩码参数、整 repeat 读取；本骨架要求单核长度按整 repeat 配置
        AscendC::Reg::LoadAlign(srcReg, dstAddr + i * oneRepeatSize);
        AscendC::Reg::LoadAlign(dstReg, dstAddr + i * oneRepeatSize);
        AscendC::Reg::Add(dstReg, dstReg, srcReg, mask);     // 寄存器计算
        AscendC::Reg::StoreAlign(dstAddr + i * oneRepeatSize, dstReg, mask);
    }
}
```

## 成员职责

| 层 | API |
|---|---|
| 外层搬运 | [InitSocState](../../apis/simd_api/basic_api/tool_interface/system_init/init_soc_state.md)、[LocalMemAllocator/Alloc](../../apis/simd_api/basic_api/resource_management/local_mem_allocator/alloc.md)、[DataCopy](../../apis/simd_api/basic_api/memory_vector_compute/data_move/data_copy_gm_and_ub_continuous.md)、[SetFlag/WaitFlag](../../apis/simd_api/basic_api/sync_control/intra_core_sync/set_flag_wait_flag_isasi.md)、[GetPhyAddr](../../apis/simd_api/basic_api/data_structures/local_tensor/get_phy_addr.md) |
| 内层寄存器 | [GetVecLen](../../apis/simd_api/basic_api/tool_interface/system_resources_and_variables/get_vec_len.md)、[MaskReg](../../apis/simd_api/basic_api/reg_vector_compute/register_data_types/mask_reg.md)、[RegTensor](../../apis/simd_api/basic_api/reg_vector_compute/register_data_types/reg_tensor.md)、[UpdateMask](../../apis/simd_api/basic_api/reg_vector_compute/register_data_types/mask_reg.md)、[LoadAlign](../../apis/simd_api/basic_api/reg_vector_compute/reg_data_load/load_align_continuous.md)、[StoreAlign](../../apis/simd_api/basic_api/reg_vector_compute/reg_data_store/store_align_continuous.md) |
| 类型修饰 | [RegLayout](../../apis/simd_api/basic_api/reg_vector_compute/aux_data_types/reg_layout.md)、[SatMode](../../apis/simd_api/basic_api/reg_vector_compute/aux_data_types/sat_mode.md)、[MaskMergeMode](../../apis/simd_api/basic_api/reg_vector_compute/aux_data_types/mask_merge_mode.md)、[PostLiteral](../../apis/simd_api/basic_api/reg_vector_compute/aux_data_types/post_literal.md) |

**API 体系说明**：本卡外层与内层调用均为**基础 API**（PascalCase）；骨架中的 `asc_vf_call` 是进入 VF 函数的 **C API 形态入口**（snake_case，官方样例固定用法），与卡内基础 API 调用分属不同 API 层级，二者在样例中按上述分工配合使用。

## 跨 API 联动约束

1. **GetVecLen 决定 repeat 粒度**：骨架调用的是 `AscendC::GetVecLen()`，返回 VL 字节数（950 上为 256 字节），`oneRepeatSize = GetVecLen() / sizeof(T)` 才是每轮元素数。不要换成 C API `asc_get_vf_len` 的卡片来理解这个返回值。repeatTimes 由其整除向上取整；bf16/half 需按各自 `sizeof(T)` 计算。
2. **整 repeat 边界（本骨架的硬约束）**：`Reg::LoadAlign` 不带掩码、整 repeat 读取 UB；`UpdateMask` 只约束后续计算与 `StoreAlign` 写回，**不能约束装载**。因此本骨架要求单核长度按整 repeat 配置（官方 add 样例即此限定）；若长度任意，第二轮从 `i * oneRepeatSize` 发起整轮读取会越界——须改为按整轮容量分配并填充 UB，或使用目标 API 支持的有界尾部读法，不能把本骨架当任意尾长模板。
3. **UpdateMask 每轮重生成**：尾块的有效元素数随轮次递减（自动扣减已处理元素），漏更新会在尾块越界读写。
4. **GetPhyAddr 只取本 Tensor 地址**：返回 LocalTensor 的 `__ubuf__` 地址供 VF 函数使用；GM 地址不进寄存器装载路径（对抗验证实证的常见混淆）。
5. **类型转换的联合配置**：Cast 场景 RegLayout（排布）+ SatMode（饱和）+ MaskMergeMode（掩码未选中元素处理）是同一 CastTrait 的共同配置字段，需一起决策。
6. **架构门控**：本范式为 950/3510 专属，host 侧调度前经 [GetCurNpuArch](../../apis/utils_api/platform_info/platform_ascend_c/get_cur_npu_arch.md) 门控 Reg-base 扩展路径。

## 掩码条件计算变体（Reg::Select）

数据与掩码两路 DataCopy 入 UB 后，VF 函数内以 `Reg::Select(zReg, xReg, yReg, mask)` 按掩码逐元素选择；配合 `PostLiteral::POST_MODE_UPDATE` 的 LoadAlign/StoreAlign 可在 repeat 循环中自动步进地址，掩码与数据共用同一 repeat 粒度。

## 失效边界与常见错误

- 掩码跨轮复用（尾块越界）；
- 把 GlobalTensor::GetPhyAddr 的 GM 地址喂给 LoadAlign；
- 本骨架为单核直排；多核软件流水（tile 级双缓冲）见 [PyTorch 接入双缓冲流水](../torch_extensions/pytorch_event_driven_tile_pipeline.md)；朴素向量核骨架见 [LocalMemAllocator 向量核骨架](../vector/localmem_allocator_vector_kernel_skeleton.md)。

## 验证方式

- repeat 对拍：singleCoreLength 分别取整 repeat 与非整 repeat（掩码路径）；
- dtype 对拍：half/bf16 各自的 GetVecLen 粒度与精度；
- 混合掩码：Select 变体下掩码与数据错位场景的对拍。
