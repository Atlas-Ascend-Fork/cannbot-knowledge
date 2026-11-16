---
type: Guide
title: PyTorch 接入的事件驱动 tile 流水（单组地址复用与四向事件）
description: 框架接入（pybind/torch_library）下的向量核 tile 流水：GetBlockNum/GetBlockIdx 分核后，x/y/z 各复用一块 UB（非双缓冲），V_MTE2/MTE2_V/V_MTE3/MTE3_V 四向事件驱动 tile 循环——循环前预授权事件，重叠发生在不同缓冲之间（x/y 搬入与上一 tile z 搬出），同缓冲的下一 tile 搬入必须等本 tile 计算释放；host 侧经 NPUStream 直发 kernel。
tags:
- task.implementation
- topic.implementation.synchronization
- topic.implementation.memory_management
status: draft
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/92ab0ff5fcdc0c5d8bb48be128b2c6a77654acde/examples/01_simd_cpp_api/02_features/00_framework/00_pytorch/torch_library/add_custom.asc
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/92ab0ff5fcdc0c5d8bb48be128b2c6a77654acde/examples/01_simd_cpp_api/02_features/00_framework/00_pytorch/pybind/add_custom.asc
  role: supporting
created_at: '2026-10-10T06:41:29Z'
updated_at: '2026-10-10T09:52:36Z'
platforms:
- '950'
- a2
- a3
---

# PyTorch 接入的事件驱动 tile 流水（单组地址复用与四向事件）

## 适用场景

PyTorch 自定义算子（pybind 或 torch_library 注册）内的高吞吐向量核：数据长度远超单段 UB，需要 tile 级事件驱动流水。与[直排骨架](../vector/localmem_allocator_vector_kernel_skeleton.md)的差别即循环化 + 四向事件状态机。

**流水的真实重叠范围**：样例为 x/y/z 各复用一块 UB 地址（`BUFFER_NUM=2` 只把 block 切成更小的 tile，不产生第二份物理缓冲），因此同缓冲的「下一 tile 搬入」必须等「本 tile 计算」释放（`V_MTE2`），不存在「搬入下一 tile 与计算当前 tile」的重叠；本结构允许的重叠发生在**不同缓冲之间**——x/y 搬入与上一 tile z 搬出（V_MTE3/MTE3_V 事件对）可并行。若需要真正双缓冲（两份物理缓冲交替），需按缓冲维度分配两组地址并成对维护事件，不在本样例范围。

## 链路骨架

`__global__` 入口只做 `InitSocState`、构造 `KernelAdd`、调用 `Process`，再 `PipeBarrier<PIPE_ALL>()`。分核和事件循环在类成员函数里，`blockLength` 是成员，不能写进自由函数。

```cpp
// KernelAdd::Init
this->blockLength = totalLength / AscendC::GetBlockNum();
xGm.SetGlobalBuffer((__gm__ half*)x + this->blockLength * AscendC::GetBlockIdx(), this->blockLength);
yGm.SetGlobalBuffer((__gm__ half*)y + this->blockLength * AscendC::GetBlockIdx(), this->blockLength);
zGm.SetGlobalBuffer((__gm__ half*)z + this->blockLength * AscendC::GetBlockIdx(), this->blockLength);

// KernelAdd::Process。BUFFER_NUM=2 用来把 block 切成更小的 tile，物理上仍是各一块 x/y/z。
constexpr int32_t BUFFER_NUM = 2;
int32_t loopCount = this->tileNum * BUFFER_NUM;
AscendC::LocalMemAllocator<AscendC::Hardware::UB> ubAllocator;
AscendC::LocalTensor<half> xLocal = ubAllocator.Alloc<half, tileLength>();
AscendC::LocalTensor<half> yLocal = ubAllocator.Alloc<half, tileLength>();
AscendC::LocalTensor<half> zLocal = ubAllocator.Alloc<half, tileLength>();

AscendC::SetFlag<AscendC::HardEvent::V_MTE2>(EVENT_ID0);   // 预授权：首轮 MTE2 可以搬入
AscendC::SetFlag<AscendC::HardEvent::MTE3_V>(EVENT_ID0);   // 预授权：首轮 V 可以写 zLocal
for (int32_t i = 0; i < loopCount; ++i) {
    AscendC::WaitFlag<AscendC::HardEvent::V_MTE2>(EVENT_ID0);
    AscendC::DataCopy(xLocal, xGm[i * tileLength], tileLength);
    AscendC::DataCopy(yLocal, yGm[i * tileLength], tileLength);
    AscendC::SetFlag<AscendC::HardEvent::MTE2_V>(EVENT_ID0);
    AscendC::WaitFlag<AscendC::HardEvent::MTE2_V>(EVENT_ID0);
    AscendC::WaitFlag<AscendC::HardEvent::MTE3_V>(EVENT_ID0);
    AscendC::Add(zLocal, xLocal, yLocal, tileLength);
    AscendC::SetFlag<AscendC::HardEvent::V_MTE2>(EVENT_ID0);
    AscendC::SetFlag<AscendC::HardEvent::V_MTE3>(EVENT_ID0);
    AscendC::WaitFlag<AscendC::HardEvent::V_MTE3>(EVENT_ID0);
    AscendC::DataCopy(zGm[i * tileLength], zLocal, tileLength);
    AscendC::SetFlag<AscendC::HardEvent::MTE3_V>(EVENT_ID0);
}
AscendC::WaitFlag<AscendC::HardEvent::V_MTE2>(EVENT_ID0);  // 回收循环前的预授权
AscendC::WaitFlag<AscendC::HardEvent::MTE3_V>(EVENT_ID0);
```

## 成员职责

| 环节 | API |
|---|---|
| 分核 | [GetBlockNum](../../apis/simd_api/basic_api/tool_interface/system_resources_and_variables/get_block_num.md)、[GetBlockIdx](../../apis/simd_api/basic_api/tool_interface/system_resources_and_variables/get_block_idx.md) |
| 内存 | [LocalMemAllocator/Alloc](../../apis/simd_api/basic_api/resource_management/local_mem_allocator/alloc.md)（tile 粒度） |
| 同步 | [SetFlag/WaitFlag](../../apis/simd_api/basic_api/sync_control/intra_core_sync/set_flag_wait_flag_isasi.md)（四向事件） |
| 搬运/计算 | [DataCopy](../../apis/simd_api/basic_api/memory_vector_compute/data_move/data_copy_gm_and_ub_continuous.md)、向量计算 API（插件） |

## 跨 API 联动约束

1. **四向事件状态机**：`V_MTE2`（MTE2 等 V 释放读缓冲）、`MTE2_V`（V 等搬入完成）、`V_MTE3`（MTE3 等 V 产出）、`MTE3_V`（V 等写出完成）——每个方向都是"消费者 Wait、生产者 Set"。
2. **循环前预授权**：首轮尚无生产者，必须先 `SetFlag(V_MTE2)`/`SetFlag(MTE3_V)` 把初始权限发给 MTE2/V，否则首轮 WaitFlag 死等。
3. **tile 长度与核均分**：`blockLength = totalLength / GetBlockNum()`。样例另有 `BUFFER_NUM = 2`，`runtimeTileLength = blockLength / tileNum / BUFFER_NUM`，并且必须等于模板参数 `tileLength`。循环次数是 `tileNum * BUFFER_NUM`，不是 `tileNum`。尾块不足整 tile 时需掩码路径（见[RegBase 范式](../regbase/reg_load_compute_store_pattern.md)）。
4. **释放与等待交替次序**：读缓冲的释放（V_MTE2 Set）必须在计算后、下一次搬入前；写缓冲的释放（MTE3_V Set）必须在写出后。次序颠倒引发覆盖或死等。

## 失效边界与常见错误

- 漏预授权首轮事件，或循环结束后不回收这两次预授权：起步死等，或事件计数残留到下一次使用；
- 把 `this->blockLength` 写进 `__global__` 自由函数：`blockLength` 是 `KernelAdd` 的成员；
- 事件方向记反（把"谁等谁"记成"谁通知谁"）；
- tile 累计长度与 blockLength 不符时尾块漏算；
- host 侧异步：torch 侧 stream 与 kernel 启动经 `<<<num_blocks, 0, stream>>>` 直发，勿在 host 侧等待后再提交下一算子（丧失流水收益）。

## 验证方式

- tileNum=1 退化为直排对拍，再逐级加大 tileNum 验证重叠正确性；
- 事件死等检测：超时看门狗下 kernel 不退出即事件状态机错误；
- 吞吐对比：直排 vs 事件驱动 tile 流水（不同缓冲的搬入/搬出重叠）的耗时差即流水收益；
- 同址复用场景另测「搬入与计算不可重叠」的超时/告警不触发（事件链正确时不应死等）。
