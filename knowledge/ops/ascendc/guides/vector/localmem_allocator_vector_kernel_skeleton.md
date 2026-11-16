---
type: Guide
title: LocalMemAllocator 向量核骨架与两种同步变体
description: 静态 Tensor 编程的向量核最小骨架：InitSocState 入口、LocalMemAllocator 顺序分配 UB、DataCopy 搬运与事件同步，对比 SetFlag/WaitFlag 精确同步与 PipeBarrier 粗粒度同步两种变体的取舍。
tags:
- task.implementation
- topic.implementation.memory_management
- topic.implementation.synchronization
- topic.programming_model.execution_unit.vector
status: draft
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/92ab0ff5fcdc0c5d8bb48be128b2c6a77654acde/examples/01_simd_cpp_api/02_features/04_compile/00_basic_compile/add_kernel.asc
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/92ab0ff5fcdc0c5d8bb48be128b2c6a77654acde/examples/01_simd_cpp_api/02_features/00_framework/04_aclgraph/add.asc
  role: supporting
- resource: cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_acos/op_kernel/arch35/foreach_acos_simt.h
  role: supporting
created_at: '2026-10-10T06:41:29Z'
updated_at: '2026-10-10T09:52:36Z'
platforms:
- '950'
- a2
- a3
---

# LocalMemAllocator 向量核骨架与两种同步变体

## 适用场景

静态 Tensor 编程模式下编写 `__vector__` 向量核：单段数据搬入-计算-搬出的直排算子（Add/激活/逐元素类），或框架接入（aclgraph/GE/PyTorch）下复用同一 kernel。计算 API（Add、LeakyRelu、Erf 等）是骨架外的可替换插件。

## 链路骨架

来自 SDK 官方样例（basic_compile，三个编译形态共用同一 kernel）：

```cpp
template <uint32_t blockLength>
__vector__ __global__ void add_custom(__gm__ float* x, __gm__ float* y, __gm__ float* z)
{
    AscendC::InitSocState();                          // 1. 入口：初始化核函数侧 SOC 状态

    AscendC::GlobalTensor<float> xGm, yGm, zGm;       // 2. GM 绑定（按 block_idx 分片）
    xGm.SetGlobalBuffer(x + block_idx * blockLength, blockLength);

    AscendC::LocalMemAllocator<AscendC::Hardware::UB> ubAllocator;   // 3. UB 顺序分配
    AscendC::LocalTensor<float> xLocal = ubAllocator.Alloc<float, blockLength>();
    AscendC::LocalTensor<float> yLocal = ubAllocator.Alloc<float, blockLength>();
    AscendC::LocalTensor<float> zLocal = ubAllocator.Alloc<float, blockLength>();

    AscendC::DataCopy(xLocal, xGm, blockLength);      // 4. GM→UB（MTE2 流水）
    AscendC::SetFlag<AscendC::HardEvent::MTE2_V>(EVENT_ID0);
    AscendC::WaitFlag<AscendC::HardEvent::MTE2_V>(EVENT_ID0);   // 5. Vector 等搬运完成

    AscendC::Add(zLocal, xLocal, yLocal, blockLength);            // 6. 计算（插件）

    AscendC::SetFlag<AscendC::HardEvent::V_MTE3>(EVENT_ID0);
    AscendC::WaitFlag<AscendC::HardEvent::V_MTE3>(EVENT_ID0);     // 7. MTE3 等计算完成
    AscendC::DataCopy(zGm, zLocal, blockLength);       // 8. UB→GM 回写

    AscendC::PipeBarrier<PIPE_ALL>();                  // 9. basic_compile 样例的收尾屏障
}
```

## 成员职责

| API | 职责 |
|---|---|
| [InitSocState](../../apis/simd_api/basic_api/tool_interface/system_init/init_soc_state.md) | 入口必调：清残留 Mask/CTRL 状态，缺失会精度错误 |
| [GlobalTensor 构造](../../apis/simd_api/basic_api/data_structures/global_tensor/global_tensor_constructor.md) / [SetGlobalBuffer](../../apis/simd_api/basic_api/data_structures/global_tensor/set_global_buffer.md) | 描述并绑定 GM 地址与长度 |
| [LocalMemAllocator 构造](../../apis/simd_api/basic_api/resource_management/local_mem_allocator/local_mem_allocator_constructor.md) / [Alloc](../../apis/simd_api/basic_api/resource_management/local_mem_allocator/alloc.md) | 按申请顺序分配片上内存，免除手动地址偏移 |
| [DataCopy](../../apis/simd_api/basic_api/memory_vector_compute/data_move/data_copy_gm_and_ub_continuous.md) | GM↔UB 搬运（MTE2/MTE3 流水） |
| [SetFlag/WaitFlag](../../apis/simd_api/basic_api/sync_control/intra_core_sync/set_flag_wait_flag_isasi.md) | 事件精确同步：HardEvent 模板参数声明等待方向 |
| [PipeBarrier](../../apis/simd_api/basic_api/sync_control/intra_core_sync/pipe_barrier_isasi.md) | 粗粒度全流水屏障（收尾用） |

## 跨 API 联动约束

1. **事件方向语义**：`MTE2_V` 表示 Vector 流水等待 MTE2（搬运）完成；`V_MTE3` 表示 MTE3（回写）等待 Vector 完成。方向写反会等待自己生产的数据，死等或读到脏数据。
2. **SetFlag/WaitFlag 成对且 EVENT_ID 一致**：同一事件的生产与消费使用相同 EVENT_ID；同类多事件用不同 ID 区分。
3. **Alloc 顺序即地址顺序**：LocalMemAllocator 按申请顺序分配，多次 Alloc 的地址依赖申请次序，不可交叉释放语义假设。
4. **InitSocState 是静态 Tensor 范式强制入口**：TPipe 范式下不需要，两范式不可混用入口约定。

## 两种同步变体取舍

- **SetFlag/WaitFlag（精确）**：搬入-计算-回写之间按事件精确衔接，允许 MTE2 搬运下一 tile 与本 tile 计算重叠（软件流水的基础），适合性能敏感路径；
- **PipeBarrier（粗粒度）**：aclgraph/msprof 等工具与框架样例使用 `PipeBarrier<PIPE_ALL>()` 做整段收尾，代码最简但无重叠，适合演示与工具型 kernel。

## 失效边界与常见错误

- 漏调 InitSocState：残留 Mask/CTRL 状态导致精度错误（对抗验证实证：SetFlag 卡约束明示该入口必需）；
- 事件方向混淆：HardEvent 模板参数的方向是"谁等谁"，不是"谁通知谁"；
- 用 GM 侧 GetPhyAddr 喂寄存器装载：`GetPhyAddr` 返回的是本 Tensor（LocalTensor）地址，GM 地址不进寄存器装载路径；
- 骨架不适用于 Cube 核（需 [Cube 搬运流水](../matmul/classic_cube_pipeline_two_forms.md)）与寄存器范式（需 [RegBase 范式](../regbase/reg_load_compute_store_pattern.md)）。

## 验证方式

- 编译期：`__vector__` 核 + LocalMemAllocator 模板参数检查（UB/Hardware 枚举）；
- 运行期：单核直排样例对拍（Add 样例三编译形态同 kernel）；事件死等表现为 kernel 不退出；
- 精度：尾块对拍（blockLength 非整 repeat 时启用掩码路径参见 RegBase 范式卡）。
