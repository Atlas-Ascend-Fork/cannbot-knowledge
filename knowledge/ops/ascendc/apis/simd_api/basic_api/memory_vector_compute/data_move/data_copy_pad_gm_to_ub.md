---
type: API
title: DataCopyPad
description: 将数据从GM非对齐搬运至UB，可根据需要自行填充数据。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopyPad_GMToUB.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# DataCopyPad

将数据从GM非对齐搬运至UB，可根据需要自行填充数据。

DataCopyPad（GMToUB非对齐数据搬运）从Global Memory将数据非对齐搬运至Unified Buffer时，可根据开发者的需要自行填充数据。SetPadValue用于设置DataCopyPad需要填充的数值。 具体支持的数据通路为（以逻辑位置TPosition表示）： - Global Memory -> Unified Buffer - GM -> VECIN - GM -> VECOUT

本接口组包含 逻辑位置TPosition, SetPadValue, SetPadValue。

本接口属于 UB 矢量计算数据搬移接口，用于不同存储间的数据拷贝。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [DataCopy GM→UB 需 32B 对齐，非对齐 C 统计输出全零](../../../../../runbooks/precision/datacopy_gm_to_ub_non_32b_aligned_silent_zero.md)（`exemplifies`）：《DataCopyPad》说明将数据从GM非对齐搬运至UB，可根据需要自行填充数据。；《DataCopy GM→UB 需 32B 对齐，非对齐 C 统计输出全零》说明Ascend950 上 1D GM→UB 用 DataCopy 时若 C*sizeof(dtype) 非 32B 对齐则搬运失败、统计输出全零；应改用 DataCopyPad 处理非对齐。。二者在GM到UB非对齐搬入依赖Pad参数、32B最小DMA和LocalTensor/offset/rightPad合同，UB到GM方向的重载不同上存在可执行的直接衔接。
- [DataCopyPad CopyIn 小输入 32B DMA 越界](../../../../../runbooks/compilation/datacopypad_copyin_32b_dma.md)（`exemplifies`）：《DataCopyPad CopyIn 小输入 32B DMA 越界》说明DataCopyPad CopyIn 不论 DataCopyExtParams.blockLen 写多少，底层 DMA 引擎按 32 字节（1 DataBlock）粒度读 GM；当 Host 仅按有效元素数分配 < 32B 输入、SetGlobalBuffer(ptr,N) 只声明逻辑可读范围不扩大物理分配时，DMA 实读 32B 越过已映射内存 → device error 507035 / segfault。判别：小输入（有效元素 × sizeof(T) < 32B）+ SetGlobalBuffer N < ceil(32/sizeof(T)) + Host 分配未对齐到 32B。；《DataCopyPad》说明将数据从GM非对齐搬运至UB，可根据需要自行填充数据。。二者在小输入越界由GM物理分配小于32B DMA粒度触发；GM到UB DataCopyPad接口和SetGlobalBuffer共同界定逻辑范围与物理读取的差异上存在可执行的直接衔接。
- [DataCopyPad UB→GM 四参调用导致编译失败](../../../../../runbooks/compilation/datacopypad_ub_to_gm_has_no_pad_params.md)（`exemplifies`）：《DataCopyPad》说明将数据从GM非对齐搬运至UB，可根据需要自行填充数据。；《DataCopyPad UB→GM 四参调用导致编译失败》说明DataCopyPad 搬出方向只接受 GlobalTensor、LocalTensor 与 DataCopyExtParams 三参；误带 PadExtParams 会令模板匹配失败。。二者在GM到UB非对齐搬入依赖Pad参数、32B最小DMA和LocalTensor/offset/rightPad合同，UB到GM方向的重载不同上存在可执行的直接衔接。
- [DataCopyPad rightPad 字段为 uint8_t](../../../../../runbooks/compilation/datacopypad_rightpad_uint8_t.md)（`exemplifies`）：《DataCopyPad》说明将数据从GM非对齐搬运至UB，可根据需要自行填充数据。；《DataCopyPad rightPad 字段为 uint8_t》说明AscendC DataCopyPadExtParams 的 rightPad 量字段类型是 uint8_t，用 static_cast<uint16_t> 填充会触发 C++11 narrowing 编译错误；编译器建议改 static_cast<uint8_t>。。二者在GM到UB非对齐搬入依赖Pad参数、32B最小DMA和LocalTensor/offset/rightPad合同，UB到GM方向的重载不同上存在可执行的直接衔接。
- [DataCopyPad 五参编译失败—LocalTensor 子视图替代偏移](../../../../../runbooks/compilation/datacopypad_offset_via_tensor_subview.md)（`exemplifies`）：《DataCopyPad》说明将数据从GM非对齐搬运至UB，可根据需要自行填充数据。；《DataCopyPad 五参编译失败—LocalTensor 子视图替代偏移》说明CANN 9.0.1 的 GM→UB DataCopyPad 不接收第五个目标偏移参数；先对 LocalTensor 取元素偏移子视图，再调用四参数重载。。二者在GM到UB非对齐搬入依赖Pad参数、32B最小DMA和LocalTensor/offset/rightPad合同，UB到GM方向的重载不同上存在可执行的直接衔接。
- [DataCopyPad 加载缺少 Pad 参数导致编译失败](../../../../../runbooks/compilation/datacopypad_gm_to_ub_requires_pad_params.md)（`exemplifies`）：《DataCopyPad》说明将数据从GM非对齐搬运至UB，可根据需要自行填充数据。；《DataCopyPad 加载缺少 Pad 参数导致编译失败》说明dav-3510 的 GM 到 UB DataCopyPad 扩展重载需要第四个 Pad 参数，不能照搬 UB 到 GM 的三参数形式。。二者在GM到UB非对齐搬入依赖Pad参数、32B最小DMA和LocalTensor/offset/rightPad合同，UB到GM方向的重载不同上存在可执行的直接衔接。
- [DataCopyPad 无匹配重载 LocalTensor 实参不一致](../../../../../runbooks/compilation/datacopypad_localtensor.md)（`exemplifies`）：《DataCopyPad》说明将数据从GM非对齐搬运至UB，可根据需要自行填充数据。；《DataCopyPad 无匹配重载 LocalTensor 实参不一致》说明Ascend950（dav-3510）上 scatter kernel 把 reduce/CopyOut 缓冲声明为 LocalTensor<int8_t>、而 updates 队列产出 LocalTensor<T>，bisheng 编译报 no matching function for call to DataCopyPad/ApplyScatterReduce 并附 candidate not viable: no known conversion from LocalTensor<float> to const LocalTensor<int8_t>。判别方法：LocalTensor<E> 模板实参为强类型、E 不一致无隐式转换，DMA 重载全部 not viable。。二者在GM到UB非对齐搬入依赖Pad参数、32B最小DMA和LocalTensor/offset/rightPad合同，UB到GM方向的重载不同上存在可执行的直接衔接。
- [多块 DataCopyPad dst 基址非 32B 对齐崩溃](../../../../../runbooks/compilation/datacopypad_dst_32b.md)（`exemplifies`）：《DataCopyPad》说明将数据从GM非对齐搬运至UB，可根据需要自行填充数据。；《多块 DataCopyPad dst 基址非 32B 对齐崩溃》说明多块 DataCopyPad(DataCopyExtParams) 把跨 slice 的 x0/x1 分段搬进 UB 时，若 head 块拷贝写入非 32B 整数倍字节长度，后续 middle/tail 块的 dst 基址随拷贝累积到非 32B 对齐地址，触发 MTE 地址未对齐 → vector core exception (EE9999 / 507035 rtDeviceSynchronizeWithTimeout)。判别方法：多块搬运上板即 EE9999，且 middle dst 基址字节偏移 firstLen*sizeof(T) 对 32 取余非零即命中；修复方向是按 alignUpS 步长重排 UB 为补齐布局，让每块 dst 基址 32B 对齐。。二者在GM到UB非对齐搬入依赖Pad参数、32B最小DMA和LocalTensor/offset/rightPad合同，UB到GM方向的重载不同上存在可执行的直接衔接。
- [DataCopy](data_copy_gm_and_ub_continuous.md)（`related`）：连续 DataCopy 依赖 32B 块对齐，GM 到 UB 尾块非对齐时应改 DataCopyPad 并显式填充。
- [DataCopyPad](data_copy_pad_ub_to_gm.md)（`related`）：《DataCopyPad》说明将数据从GM非对齐搬运至UB，可根据需要自行填充数据。；《DataCopyPad》说明将数据从UB非对齐搬运至GM。。二者在GM到UB非对齐搬入依赖Pad参数、32B最小DMA和LocalTensor/offset/rightPad合同，UB到GM方向的重载不同上存在可执行的直接衔接。
- [DataCopyPad（GMToL1非对齐数据搬运）](../../cube_compute/cube_compute_load/data_copy_pad_gm_to_l1.md)（`related`）：《DataCopyPad》明确“将数据从GM非对齐搬运至UB，可根据需要自行填充数据。”；它与《DataCopyPad（GMToL1非对齐数据搬运）》的“该接口提供从Global Memory到L1 Buffer的数据非对齐搬运功能，可以根据开发者的需要自行填充数据。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetPadValue](../data_move_aux_config/set_pad_value_isasi.md)（`related`）：DataCopyPad说明将数据从GM非对齐搬运至UB，可根据需要自行填充数据；对SetPadValue而言，SetPadValue 配置搬运补齐值；C API 的 copy-pad SPR 设置和 DataCopyPad 的左/右 padding 是其实际消费位置。
- [数据搬运](data_move.md)（`related`）：《DataCopyPad》说明将数据从GM非对齐搬运至UB，可根据需要自行填充数据。；《数据搬运》说明矢量数据搬运接口集，涵盖 DataCopy、DataCopyPad、Copy 等 GM/UB 间连续、高维切分、非对齐搬运接口。。二者在GM到UB非对齐搬入依赖Pad参数、32B最小DMA和LocalTensor/offset/rightPad合同，UB到GM方向的重载不同上存在可执行的直接衔接。
<!-- cannbot:related:end -->
