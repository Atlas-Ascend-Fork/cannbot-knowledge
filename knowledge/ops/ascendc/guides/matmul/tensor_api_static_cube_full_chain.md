---
type: Guide
title: 静态 Tensor 范式 Cube 全链路（MakeTensor 布局驱动与 Mutex 流水互斥）
description: tensor_api 静态 Cube 编程范式的完整组装链：InitSocState/GetBlockIdx 入口与多核分片，MakeMemPtr+MakeFrameLayout+MakeTensor 构造 GM/L1/L0A/L0B/L0C 分层张量，Slice+MakeCoord/MakeShape 切本核 tile，MakeCopy/MakeMmad 原子构造，Mutex::Lock/Unlock 按存储资源编排 MTE2/MTE1/M/FIX 四段流水，Mmad 首块初始化与累加语义，含尾块/多级缓冲/bias/在线反量化变体。
tags:
- task.implementation
- topic.implementation.memory_management
- topic.implementation.synchronization
- topic.programming_model.execution_unit.cube
status: draft
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/92ab0ff5fcdc0c5d8bb48be128b2c6a77654acde/examples/01_simd_cpp_api/00_introduction/02_matrix/matmul_tensor_api/matmul.asc
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/92ab0ff5fcdc0c5d8bb48be128b2c6a77654acde/examples/01_simd_cpp_api/03_basic_api/03_matrix_compute/mmad_tensor_api/mmad_tensor_api.asc
  role: supporting
- resource: https://gitcode.com/cann/asc-devkit/blob/92ab0ff5fcdc0c5d8bb48be128b2c6a77654acde/examples/01_simd_cpp_api/03_basic_api/00_data_movement/copy_in_tensor_api/copy_in_tensor_api.asc
  role: supporting
- resource: https://gitcode.com/cann/asc-devkit/blob/92ab0ff5fcdc0c5d8bb48be128b2c6a77654acde/include/tensor_api/utils/utils.h
  role: supporting
created_at: '2026-10-10T11:12:43Z'
updated_at: '2026-11-10T07:06:44Z'
platforms:
- '950'
---

# 静态 Tensor 范式 Cube 全链路（MakeTensor 布局驱动与 Mutex 流水互斥）

## 适用场景

用 `tensor_api/tensor.h` 静态 Tensor 编程范式自排 Cube 矩阵流水的场景：不经高阶 Matmul 模板、也不用 basic_api 的 `DataCopy(Nd2NzParams)`/`LoadData` 经典形态，而是以 Layout 对象显式描述各存储层级的数据分形，由 `MakeCopy`/`MakeMmad` 原子完成搬运与计算。矩阵乘（matmul）、矩阵搬运（copy_in）、量化矩阵乘（mmad+quant）共用同一范式骨架。

## 链路骨架

提炼自官方样例 `matmul_tensor_api/matmul.asc`（`__global__ __cube__` 核）：

```cpp
AscendC::InitSocState();                                  // 入口初始化
using namespace AscendC::Te;
uint32_t mIterIdx = AscendC::GetBlockIdx() % mIter;       // 多核分片：行列号
uint32_t nIterIdx = AscendC::GetBlockIdx() / mIter;

// ① GM 张量：NDExt 布局 + Slice 切本核 tile
auto gmA = MakeTensor(MakeMemPtr(a), MakeFrameLayout<NDExtLayoutPtn>(M, K));
auto globalA = gmA.Slice(MakeCoord(mIterIdx * singleCoreM, 0), MakeShape(baseM, K));

// ② 分层布局：L1/L0A/L0C 用 NZ，L0B 用 ZN
auto l1ALayout  = MakeFrameLayout<NZLayoutPtn>(baseM, K);
auto l0BLayout  = MakeFrameLayout<ZNLayoutPtn>(baseK, baseN);
__cbuf__ half l1ABuf[baseM * K];   __ca__ half l0ABuf[baseM * baseK];
__cb__  half l0BBuf[baseK * baseN]; __cc__ float l0CBuf[baseM * baseN];
auto l1ATensor = MakeTensor(MakeMemPtr(l1ABuf), l1ALayout);   // ...各层同理

// ③ 搬运/计算原子（Operation + TraitDefault 成对构造）
auto copyGM2L1Atom  = MakeCopy(CopyGM2L1{}, CopyGM2L1TraitDefault{});
auto copyL12L0AAtom = MakeCopy(CopyL12L0A{}, CopyL12L0ATraitDefault{});
auto copyL0C2GMAtom = MakeCopy(CopyL0C2GM{}, CopyL0C2GMTraitDefault{});
auto mmadAtom = MakeMmad(MmadOperation{}, MmadTraitDefault{});

// ④ Mutex 按存储资源编排四段流水（MTE2 搬入 → MTE1 加载 → M 计算 → FIX 回写）
constexpr uint32_t L1_Index = 0, L0_Index = 1, L0C_Index = 2;
AscendC::Mutex::Lock<PIPE_M>(L0C_Index);                   // L0C 跨整个 K 循环持有
AscendC::Mutex::Lock<PIPE_MTE2>(L1_Index);
Copy(copyGM2L1Atom, l1ATensor, globalA);                  // GM → L1
AscendC::Mutex::Unlock<PIPE_MTE2>(L1_Index);
AscendC::Mutex::Lock<PIPE_MTE1>(L1_Index);                // L1 锁跨 K 循环
for (uint32_t kIter = 0; kIter < kLoop; ++kIter) {
    AscendC::Mutex::Lock<PIPE_MTE1>(L0_Index);
    Copy(copyL12L0AAtom, l0ATensor,                       // L1 → L0（Slice 切 K tile）
         l1ATensor.Slice(MakeCoord(0, kIter * baseK), MakeShape(baseM, baseK)));
    AscendC::Mutex::Unlock<PIPE_MTE1>(L0_Index);
    AscendC::Mutex::Lock<PIPE_M>(L0_Index);
    MmadParams para{baseM, baseN, baseK, 0, kIter == 0};  // 首块初始化、后续累加
    Mmad(mmadAtom.with(para), l0CTensor, l0ATensor, l0BTensor);
    AscendC::Mutex::Unlock<PIPE_M>(L0_Index);
}
AscendC::Mutex::Unlock<PIPE_MTE1>(L1_Index);
AscendC::Mutex::Unlock<PIPE_M>(L0C_Index);
AscendC::Mutex::Lock<PIPE_FIX>(L0C_Index);
Copy(copyL0C2GMAtom, globalC, l0CTensor);                 // L0C → GM 回写
AscendC::Mutex::Unlock<PIPE_FIX>(L0C_Index);
AscendC::PipeBarrier<PIPE_ALL>();                         // 收尾全流水栅栏
```

## 成员职责

| 环节 | 基础 API（本卡骨架） | 对应底层卡（SIMD C API / Tensor API 层级） |
|---|---|---|
| 入口/分核 | [InitSocState](../../apis/simd_api/basic_api/tool_interface/system_init/init_soc_state.md)、[GetBlockIdx](../../apis/simd_api/basic_api/tool_interface/system_resources_and_variables/get_block_idx.md) | SIMD C API：[asc_init](../../apis/simd_api/c_api/utils/sys_init/asc_init.md)、[get_block_idx](../../apis/simd_api/basic_api/tool_interface/system_resources_and_variables/get_block_idx.md)（同名接口，两形态共用卡） |
| 张量构造 | MakeTensor、MakeMemPtr、Slice | Tensor API：[make_tensor](../../apis/simd_api/tensor_api/tensor/make_tensor.md)、[make_mem_ptr](../../apis/simd_api/tensor_api/tensor/make_mem_ptr.md)、[slice](../../apis/simd_api/tensor_api/tensor/slice.md) |
| 布局 | MakeFrameLayout、MakeCoord、MakeShape | Tensor API：[make_frame_layout](../../apis/simd_api/tensor_api/layout/make_frame_layout.md)、[make_coord](../../apis/simd_api/tensor_api/layout/make_coord.md)、[make_shape](../../apis/simd_api/tensor_api/layout/make_shape.md) |
| 搬运 | Copy（原子标签 CopyGM2L1/CopyL12L0A/CopyL12L0B/CopyL0C2GM） | Tensor API：[copy GM→L1](../../apis/simd_api/tensor_api/matrix_compute/cube_compute_load/copy_gm_to_l1.md)、[copy L1→L0A](../../apis/simd_api/tensor_api/matrix_compute/cube_compute_load/copy_l1_to_l0a.md)、[copy L1→L0B](../../apis/simd_api/tensor_api/matrix_compute/cube_compute_load/copy_l1_to_l0b.md)、[copy L0C→GM](../../apis/simd_api/tensor_api/matrix_compute/cube_compute_store/copy_l0c_to_gm.md) |
| 计算 | Mmad | Tensor API：[mmad](../../apis/simd_api/tensor_api/matrix_compute/mmad_compute/mmad.md) |
| 流水互斥 | [Lock](../../apis/simd_api/basic_api/sync_control/intra_core_sync/lock.md)、[Unlock](../../apis/simd_api/basic_api/sync_control/intra_core_sync/unlock.md)、[PipeBarrier](../../apis/simd_api/basic_api/sync_control/intra_core_sync/pipe_barrier_isasi.md) | SIMD C API：[asc_lock](../../apis/simd_api/c_api/sync/intra_core_sync/asc_lock.md)、[asc_unlock](../../apis/simd_api/c_api/sync/intra_core_sync/asc_unlock.md)、[asc_sync_pipe](../../apis/simd_api/c_api/sync/intra_core_sync/asc_sync_pipe.md) |

**API 体系说明**：本卡骨架使用**基础 API**（PascalCase：`MakeTensor`/`MakeCopy`/`Copy`/`Mmad`/`Mutex::Lock`/`InitSocState`，官方样例 92ab0ff5 原文形态）。表中底层卡按官方 API 层级标注——`simd_api/tensor_api/` 目录的 `make_tensor`/`copy`/`mmad` 等（snake_case，Layout 代数）属于 **Tensor API** 层级；`asc_init`/`asc_lock` 等（`asc_` 前缀，原生指针）属于 **SIMD C API** 层级。两个层级都与基础 API 基本一一映射，但各自是独立接口层，不是同一接口的两种命名；查底层卡时注意层级与参数形态差异。

## 跨 API 联动约束

1. **锁配对强制**：`Lock`/`Unlock` 必须同 pipe 同 id 严格成对，且 Unlock 始终写在 Lock 之后；相同 id 的 Lock/Unlock 对无论 pipe 是否相同都不得嵌套——违反任何一条均为未定义行为（[Lock 卡约束](../../apis/simd_api/basic_api/sync_control/intra_core_sync/lock.md)）。样例中 L0C 在 `PIPE_M` 的锁跨整个 K 循环持有（首块 Lock、末块 Unlock），语义是"整段累加完成前 FIX 不得读 L0C"。
2. **资源-MutexID 映射约定**：静态 Tensor 范式的 MutexID 由开发者自行管理（建议 0-27，28-31 系统预留）。官方样例按存储资源分配 ID（L1=0、L0=1、L0C=2、QUANT=3），并在不同 pipe 上复用同一资源 ID 表达生产者-消费者依赖：`PIPE_MTE2` 锁 L1 保护 GM→L1 写入，`PIPE_MTE1` 锁同一 L1 ID 让加载等待搬入完成。
3. **自管 MutexID 与资源管理接口互斥**：自行管理 MutexID 时不得同时使用 `TPipe.InitBuffer(TQue/TQueBind)`、`TBufPool.InitBuffer/InitBufPool`、`TQue/TQueBind` 的 `AllocTensor/FreeTensor/EnQue/DeQue` 等可能申请 MutexID 的接口——ID 撞车导致同步行为未定义；确需混用必须改走 `AllocMutexID/ReleaseMutexID`。
4. **LayoutPattern 位置契约**：搬运与计算要求源/目的张量满足特定 LayoutPattern 组合：GM 侧用 `NDExtLayoutPtn`（转置外扩 ND），L1A/L0A/L0C 用 `NZLayoutPtn`，L0B 用 `ZNLayoutPtn`。分形组合（A=NZ、B=ZN、C=NZ）是硬件层约束，两套 API 均遵循——C API [mmad 卡](../../apis/simd_api/tensor_api/matrix_compute/mmad_compute/mmad.md)明示 A(NZ)×B(ZN)→C(NZ)，本卡骨架的 MakeFrameLayout 分配（92ab0ff5 样例）同样实证；层级与 Pattern 错配是搬运/计算错位的根源。
5. **分片坐标联动**：`GetBlockIdx` 推导的 `mIterIdx/nIterIdx` 直接决定 `Slice(MakeCoord(偏移), MakeShape(尺寸))` 的偏移；coord+shape 与 GM 张量的全局形状必须自洽（越界即非法 tile）。
6. **首块初始化/累加语义**：两套 API 的对应参数语义一致——基础 API `MmadParams` 第 5 参 `cmatrixInitVal`（92ab0ff5 include 定义）、Tensor API `mmad_params` 的 `init_with_zero`（[mmad 卡](../../apis/simd_api/tensor_api/matrix_compute/mmad_compute/mmad.md)记录）——在 `kIter==0` 置 true（等价 `C = A*B`）、后续置 false（`C = A*B + C`），骨架样例实证；漏置首块标志会把 L0C 残留值累加进结果。

## 变体扩展（可选特性，与主链正交）

- **动态形状与尾块**（mmad_tensor_api 样例）：`actualSingleCoreM/N` 按 `% baseM` 裁剪尾块尺寸，`MakeFrameLayout` 逐 tile 以 `curM/curN/curK` 重建——布局对象随尾块变化，不能只构造一次。
- **多级 L1 缓冲**：`stepK>1` 时 L1 布局扩为 `(baseM*stepM, baseK*stepK)`，K 循环内以 `kIter % stepK` 做 L1 内环形分片，GM→L1 的重填只在 `kIter % stepK == 0` 触发。
- **bias 通路**：`CopyL12BT` 原子 + 独立 `L1_BIAS/L0_BIAS` MutexID，bias 经 L1 转入 L0 参与计算。
- **UnitFlag 跨阶段握手**（[unit_flag 卡](../../apis/simd_api/tensor_api/matrix_compute/mmad_compute_key_features/unit_flag.md)）：开启 UnitFlag 时，Mmad 侧 `para.unitFlag`（中间块 2、尾块 3）与回写侧 `FixpipeParams.unitFlag=3` 必须协同，标志错位会使 Fixpipe 在错误的分块边界读 L0C。
- **在线反量化**（[quant_pre 卡](../../apis/simd_api/tensor_api/matrix_compute/cube_store_key_features/quant_pre.md)）：`CopyL0C2GM` 可携带 quant 张量（L1 中转）在回写时完成量化格式转换。

## 失效边界与常见错误

- **锁序列缺陷静默失败**：Lock/Unlock 不成对、同 id 嵌套、Unlock 先于 Lock 均属未定义行为，无编译期报错，表现为偶发数据竞争或结果错乱——交付前应静态核对每个 (pipe, id) 的锁计数平衡；
- **平台边界（本卡不覆盖 a2/a3）**：本卡骨架所引全部 Tensor API 卡与 Mutex 流水互斥均为 950（3510）范围；2201 架构（A2/A3）不能直接套用——同步需改用 `SetFlag/WaitFlag` 实现相同效果（[Cube 矩阵计算编程指南](../programming_guide/programming_model/ai_core_simd_programming/cpp_tensor_programming/cube_matrix_computation.md)明示），接口可用性亦需按 2201 另行核对；
- **范式混用**：本链的 `MakeTensor/MakeCopy/Mmad`（tensor_api 静态形态）与 [LocalMemAllocator+DataCopy(Nd2Nz)+LoadData 经典形态](classic_cube_pipeline_two_forms.md)、[TPipe+REGIST_MATMUL_OBJ 高阶形态](high_level_matmul_full_chain.md)是三套独立封装，锁/事件机制与内存声明方式不可交叉混用；
- `cmatrixInitVal` 漏置或非首块误置导致累加语义错误；
- L0B 布局误用 NZ（应为 ZN）导致矩阵乘维度错位。

## 验证方式

- 单核先行：`GetBlockIdx()==0` 的 tile 对拍通过后再开多核；
- 尾块对拍：M/N/K 不整除 base 时逐 tile 比对参考实现；
- 锁序列静态检查：每 (pipe, id) 的 Lock/Unlock 计数平衡、无同 id 嵌套；
- UnitFlag/quant 开关对拍：关闭 UnitFlag 与开启后的结果一致性与回写边界核对。
