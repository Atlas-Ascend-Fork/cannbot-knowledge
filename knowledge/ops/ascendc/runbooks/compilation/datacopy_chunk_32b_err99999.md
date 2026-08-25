---
type: "Runbook"
title: "DataCopy尾chunk非32B对齐触发ERR99999"
description: "Ascend C DataCopy 在 UB↔GM 方向要求 count*sizeof(T) 为 32 字节对齐，否则搬运量对 32B 向下取整。当纯搬运算子尾 chunk 的实际元素数不满足 32B 对齐时，UB→GM 写方向触发 ERR99999、GM→UB 读方向静默丢尾部数据。判别方法：尾部元素数*sizeof(T)%32!=0 即命中。"
tags: ["task.debugging", "topic.data_movement.data_copy", "topic.alignment"]
status: stable
sources: []
created_at: "2026-08-18T10:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# DataCopy尾chunk非32B对齐触发ERR99999

## 适用场景

- 工程形态：ops-direct-invoke Kernel 直调（`op_kernel/*.asc` + `op_extension/*_torch.cpp` + CMake 直编 `.so`），非 aclnn 算子仓流程。
- API 路径：`DataCopy(ub, srcGm, count)` / `DataCopy(dstGm, result, count)`；`GlobalTensor<T>::SetGlobalBuffer(ptr, len)`；`TPipe` + `TQue<TPosition::VECIN/VECOUT, DB=2>`；`Adds(out, data, (T)0, count)` 做 passthrough。
- 验证过的平台与 CANN 版本：Ascend950PR（chip 957c，dav-3510），CANN 9.1.0。`platforms: [950]` 仅此平台实测。
- 适用粒度：`operator_family`——任何在 UB↔GM 之间用 `DataCopy` 做纯搬运/拼接、且输出尾部元素数可能非 32B 对齐的向量算子（Slice/Concat/Split/Reshape 搬运路径、Gather 尾块等）均适用。
- 路线优先级：`recommended_fastpath`——尾 chunk 读写双向 32B 向上补齐是搬运类算子默认应采用的写法。
- 不适用或未验证场景：Cube 类算子（`DataCopy` 的 cube 通路对齐约束不同）；GM→GM 的 `DataCopy`（仅 UB 侧约束）；a3/a2 平台未验证，推断可迁移但未实测（见 `## 失效边界`）。

## 判别方法

触发（tool_observed）：在 Ascend950PR 上实现 `torch.slice` 算子的连续搬运 kernel（`op_kernel/Slice_kernel.asc` 的 `ContiguousCopy<T>` / `ContiguousCopyBF16`）。kernel 编译通过、基础精度 9 个 case 全过，但扩展精度测试中当输出尾部元素数 `tailElements` 不满足 32 字节对齐时，UB→GM 方向的 `DataCopy` 触发 `ERR99999 UNKNOWN application exception`。复现命令（Python 侧）：

```python
# 32B 对齐 → PASS
torch.ops.npu_test.slice(x_bool_100, 0, 10, 42, 1)  # 32 元素 → 32 bytes → aligned

# 非 32B 对齐 → FAIL (ERR99999)
# 55 元素 → 55 bytes → NOT aligned
```

报错原文（取自审查报告 `docs/REVIEW.md`，该文件经 file_read tool_result 保留于 trace seq210，非 redacted）：

```
[ERROR] ERR99999 UNKNOWN applicaiton exception
[AIV Block 0/1] [Slice] block=0 dtype=4 myTotal=55 step=1 srcOffset=10 myOffset=0
```

探针：对任一用 `DataCopy` 做 UB↔GM 搬运的 kernel，检查尾 chunk 的搬运量是否满足 32B 对齐——即 `tailCount * sizeof(T) % 32 == 0` 是否成立。可直接用上述非对齐尾部 case（bool、55 元素）运行一次：命中 `ERR99999` 即判为本卡所述的向下取整机制问题；同时检查 `ChkSz` 这类"尾 chunk 取实际剩余"的 helper 返回值是否被直接喂给 `DataCopy`。

触发态代码（verbatim，修复前 `ContiguousCopy<T>`，`op_kernel/Slice_kernel.asc` 第 88-120 行，取自 trace seq305 file_read tool_result，非 redacted）：

```cpp
    template<typename T>
    __aicore__ inline void ContiguousCopy()
    {
        uint64_t nChunks = (myTotal_ + chunkSize_ - 1) / chunkSize_;
        if (nChunks == 0) return;

        __gm__ T* srcPtr = reinterpret_cast<__gm__ T*>(srcRaw_);
        __gm__ T* dstPtr = reinterpret_cast<__gm__ T*>(dstRaw_);

        for (uint64_t c = 0; c < nChunks; c++) {
            uint32_t cs = ChkSz(c, nChunks);
            uint64_t srcOff = srcOffset_ + myOffset_ + c * chunkSize_;
            uint64_t dstOff = myOffset_ + c * chunkSize_;

            GlobalTensor<T> srcGm;
            srcGm.SetGlobalBuffer(srcPtr + srcOff, cs);
            GlobalTensor<T> dstGm;
            dstGm.SetGlobalBuffer(dstPtr + dstOff, cs);

            auto ub = inQ_.AllocTensor<T>();
            DataCopy(ub, srcGm, cs);
            inQ_.EnQue(ub);
            auto data = inQ_.DeQue<T>();

            auto out = outQ_.AllocTensor<T>();
            Adds(out, data, (T)0, cs);
            outQ_.EnQue(out);
            inQ_.FreeTensor(data);
            auto result = outQ_.DeQue<T>();
            DataCopy(dstGm, result, cs);
            outQ_.FreeTensor(result);
        }
    }
```

`ContiguousCopyBF16`（第 122-153 行）结构完全相同，仅 `T=bfloat16_t`，同样用 `cs = ChkSz(c, nChunks)` 做 read/write，无对齐补齐。`ChkSz` 对尾 chunk 返回 `myTotal_ - c*chunkSize_`，对 bool（sizeof=1）尾部 55 元素即 55 字节，不满足 32B 对齐。

观测：bool 输出尾部 55 元素（55 bytes，`55 % 32 = 23 ≠ 0`）命中 `ERR99999`；32B 对齐的 bool case（32 元素）通过。修复后 bool/bf16 非对齐尾部扩展精度通过，9/9 基础精度全过、复审从 FAIL 74/100 改判 PASS 80/100。

判别与解释（interpretation，agent 根因分析）：Ascend C `DataCopy` 对 UB↔GM 方向有硬约束——`count * sizeof(T)` 需要 32 字节对齐，若不对齐，搬运量将对 32 字节做向下取整（API 文档《基础数据搬运.md》第 91 行原文，经 `REVIEW.md` 引用保留于 seq210）。原实现对尾 chunk 用实际元素数 `cs` 直接做 `DataCopy`：当 `cs * sizeof(T) % 32 != 0` 时，搬运量被向下取整到 `floor(cs*sizeof(T)/32)*32`，尾部若干元素根本没被搬，UB→GM 写方向触发 `ERR99999`，GM→UB 读方向则静默丢尾部数据。以 bool, tail=55 为例：`55 bytes → floor(55/32)*32 = 32 bytes`，尾部 23 字节未搬运，写方向报 `ERR99999`、读方向尾部 23 字节为未初始化垃圾。这不是精度逻辑错，而是搬运量计算被 API 向下取整的机制问题。机制判定：尾部元素数 `* sizeof(T) % 32 != 0` 且 `DataCopy` 直接用未补齐的 `count` → 命中本判别规则。

## 验证信号

来源：本 trace 在 Ascend950PR（CANN 9.1.0）上开发并审查 `torch.slice` 连续搬运 kernel，扩展精度测试覆盖 bool/bf16 非 32B 对齐尾部 case；`docs/REVIEW.md` 经 file_read 保留于 trace seq210，记录 `ERR99999` 与 API 约束原文。

- `ERR99999 UNKNOWN application exception`，bool 输出尾部 55 元素（55 bytes，非 32B 对齐）触发；32B 对齐 case 通过。（来源平台：950；证据等级：artifact_verified）
- API 约束原文 `count * sizeof(T) 需要 32 字节对齐，若不对齐，搬运量将对 32 字节做向下取整`（《基础数据搬运.md》第 91 行，经 `REVIEW.md` 引用）。（来源平台：950；证据等级：artifact_verified）
- 修复后扩展精度 bool/bf16 非对齐尾部 case 通过，9/9 基础精度全过、复审从 FAIL 74/100 改判 PASS 80/100（bash 运行测试观测，verbatim stdout 未由 adapter 保留）。（来源平台：950；证据等级：tool_observed）

## 失效边界

- `DataCopy` 的 32B 向下取整约束在 DAV_3510（Ascend950）上实测确认；a2 与 a3 未在本 trace 实测，推断同约束可迁移（同属 Ascend C 向量核 `DataCopy` 语义）但**未验证**。
- 写方向用 `alignedCs` 向上补齐会向输出 GM 多写若干补齐字节（`alignedCs - rawCs` 个垃圾元素）。其安全性依赖 PyTorch NPU 分配器的块状分配——若调用方用极紧凑、无 padding 的自定义 GM 分配器，多写补齐字节可能越界，需额外保证输出 GM 尾部有 `alignedCs - rawCs` 字节余量。
- `DataCopy` 在 Cube 通路或 GM→GM 直搬场景的对齐约束不同，本卡不适用。
- 本卡只判别失败机制（trigger/probe/observation/interpretation），不包含修复后的 verbatim 完整函数。

## 坏实践

- 只对读方向 `SetGlobalBuffer(alignedCs)` 而写方向仍 `DataCopy(dstGm, result, rawCs)`——读补齐了，写还在向下取整，尾部依然丢，`ERR99999` 不消。
- 用 `GetValue/SetValue` 逐元素处理尾 chunk 绕过对齐——违反矢量算子规范且性能极差。
- 把 `SetGlobalBuffer` 长度设为 `rawCs` 而 `DataCopy` 传 `alignedCs`——`SetGlobalBuffer` 长度小于实际搬运量，越界不安全。
- 把 `ChkSz`（尾 chunk 取实际剩余）的返回值直接喂给 `DataCopy` 而不做 32B 补齐——即本卡触发态。

<!-- cannbot:related:start -->
## 相关

- [Slice（基础API）](../../apis/simd_api/basic_api/data_structure_tensor_api/tensor_structure/slice.md)（`exemplifies`）：《DataCopy尾chunk非32B对齐触发ERR99999》说明Ascend C DataCopy 在 UB↔GM 方向要求 count*sizeof(T) 为 32 字节对齐，否则搬运量对 32B 向下取整。当纯搬运算子尾 chunk 的实际元素数不满足 32B 对齐时，UB→GM 写方向触发 ERR99999、GM→UB 读方向静默丢尾部数据。判别方法：尾部元素数*sizeof(T)%32!=0 即命中。；《Slice（基础API）》说明需要包含的头文件为：#include "tensor_api/tensor.h"。 Slice用于从张量指定坐标处切出一个子张量。根据输入的起始坐标coord和切片描述信息info，计算新的起始存储位置，并构造对应的子张量，子张量保持与原张量相同的存储位置类型。。二者在DataCopy尾chunk错误由有效字节数非32B倍数触发，DataCopyPad的逐行、stride、padding和最小DMA卡给出修复边界上存在可执行的直接衔接。
- [DataCopyExtParams blockLen 窄化编译失败](datacopyextparams_block_len_requires_uint32.md)（`related`）：《DataCopy尾chunk非32B对齐触发ERR99999》说明Ascend C DataCopy 在 UB↔GM 方向要求 count*sizeof(T) 为 32 字节对齐，否则搬运量对 32B 向下取整。当纯搬运算子尾 chunk 的实际元素数不满足 32B 对齐时，UB→GM 写方向触发 ERR99999、GM→UB 读方向静默丢尾部数据。判别方法：尾部元素数*sizeof(T)%32!=0 即命中。；《DataCopyExtParams blockLen 窄化编译失败》说明DataCopyExtParams 的 blockLen 接收 uint32_t，模板表达式 D* sizeof(T) 须显式窄化后再做 DataCopyPad。。二者在DataCopy尾chunk错误由有效字节数非32B倍数触发，DataCopyPad的逐行、stride、padding和最小DMA卡给出修复边界上存在可执行的直接衔接。
- [DataCopyPad CopyIn 小输入 32B DMA 越界](datacopypad_copyin_32b_dma.md)（`related`）：《DataCopy尾chunk非32B对齐触发ERR99999》说明Ascend C DataCopy 在 UB↔GM 方向要求 count*sizeof(T) 为 32 字节对齐，否则搬运量对 32B 向下取整。当纯搬运算子尾 chunk 的实际元素数不满足 32B 对齐时，UB→GM 写方向触发 ERR99999、GM→UB 读方向静默丢尾部数据。判别方法：尾部元素数*sizeof(T)%32!=0 即命中。；《DataCopyPad CopyIn 小输入 32B DMA 越界》说明DataCopyPad CopyIn 不论 DataCopyExtParams.blockLen 写多少，底层 DMA 引擎按 32 字节（1 DataBlock）粒度读 GM；当 Host 仅按有效元素数分配 < 32B 输入、SetGlobalBuffer(ptr,N) 只声明逻辑可读范围不扩大物理分配时，DMA 实读 32B 越过已映射内存 → device error 507035 / segfault。判别：小输入（有效元素 × sizeof(T) < 32B）+ SetGlobalBuffer N < ceil(32/sizeof(T)) + Host 分配未对齐到 32B。。二者在DataCopy尾chunk错误由有效字节数非32B倍数触发，DataCopyPad的逐行、stride、padding和最小DMA卡给出修复边界上存在可执行的直接衔接。
- [DataCopyPad rightPad 字段为 uint8_t](datacopypad_rightpad_uint8_t.md)（`related`）：《DataCopy尾chunk非32B对齐触发ERR99999》说明Ascend C DataCopy 在 UB↔GM 方向要求 count*sizeof(T) 为 32 字节对齐，否则搬运量对 32B 向下取整。当纯搬运算子尾 chunk 的实际元素数不满足 32B 对齐时，UB→GM 写方向触发 ERR99999、GM→UB 读方向静默丢尾部数据。判别方法：尾部元素数*sizeof(T)%32!=0 即命中。；《DataCopyPad rightPad 字段为 uint8_t》说明AscendC DataCopyPadExtParams 的 rightPad 量字段类型是 uint8_t，用 static_cast<uint16_t> 填充会触发 C++11 narrowing 编译错误；编译器建议改 static_cast<uint8_t>。。二者在DataCopy尾chunk错误由有效字节数非32B倍数触发，DataCopyPad的逐行、stride、padding和最小DMA卡给出修复边界上存在可执行的直接衔接。
- [DataCopyPad stride 表示 block 间隙](../precision/datacopypad_stride_is_inter_block_gap.md)（`related`）：《DataCopy尾chunk非32B对齐触发ERR99999》说明Ascend C DataCopy 在 UB↔GM 方向要求 count*sizeof(T) 为 32 字节对齐，否则搬运量对 32B 向下取整。当纯搬运算子尾 chunk 的实际元素数不满足 32B 对齐时，UB→GM 写方向触发 ERR99999、GM→UB 读方向静默丢尾部数据。判别方法：尾部元素数*sizeof(T)%32!=0 即命中。；《DataCopyPad stride 表示 block 间隙》说明二维跨步 DataCopyPad 中 local stride 是相邻 block 间额外 gap；把对齐补齐字节再次作为 gap 会二次跳过 UB 空间并导致后续行读写垃圾。。二者在DataCopy尾chunk错误由有效字节数非32B倍数触发，DataCopyPad的逐行、stride、padding和最小DMA卡给出修复边界上存在可执行的直接衔接。
- [DataCopyPad 尾块改逐行一维搬入](../precision/datacopypad_partial_2d_blocks_use_per_row_copy.md)（`related`）：《DataCopy尾chunk非32B对齐触发ERR99999》说明Ascend C DataCopy 在 UB↔GM 方向要求 count*sizeof(T) 为 32 字节对齐，否则搬运量对 32B 向下取整。当纯搬运算子尾 chunk 的实际元素数不满足 32B 对齐时，UB→GM 写方向触发 ERR99999、GM→UB 读方向静默丢尾部数据。判别方法：尾部元素数*sizeof(T)%32!=0 即命中。；《DataCopyPad 尾块改逐行一维搬入》说明2D DataCopyPad 的多块参数未把短块落到 256B UB 行首，会让 LoadAlign 读错行；逐行 blockCount=1 可消除歧义。。二者在DataCopy尾chunk错误由有效字节数非32B倍数触发，DataCopyPad的逐行、stride、padding和最小DMA卡给出修复边界上存在可执行的直接衔接。
- [DataCopyPad 无匹配重载 LocalTensor 实参不一致](datacopypad_localtensor.md)（`related`）：《DataCopy尾chunk非32B对齐触发ERR99999》说明Ascend C DataCopy 在 UB↔GM 方向要求 count*sizeof(T) 为 32 字节对齐，否则搬运量对 32B 向下取整。当纯搬运算子尾 chunk 的实际元素数不满足 32B 对齐时，UB→GM 写方向触发 ERR99999、GM→UB 读方向静默丢尾部数据。判别方法：尾部元素数*sizeof(T)%32!=0 即命中。；《DataCopyPad 无匹配重载 LocalTensor 实参不一致》说明Ascend950（dav-3510）上 scatter kernel 把 reduce/CopyOut 缓冲声明为 LocalTensor<int8_t>、而 updates 队列产出 LocalTensor<T>，bisheng 编译报 no matching function for call to DataCopyPad/ApplyScatterReduce 并附 candidate not viable: no known conversion from LocalTensor<float> to const LocalTensor<int8_t>。判别方法：LocalTensor<E> 模板实参为强类型、E 不一致无隐式转换，DMA 重载全部 not viable。。二者在DataCopy尾chunk错误由有效字节数非32B倍数触发，DataCopyPad的逐行、stride、padding和最小DMA卡给出修复边界上存在可执行的直接衔接。
- [NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写](nddma_nddmaconfig_datacopypad.md)（`related`）：《DataCopy尾chunk非32B对齐触发ERR99999》说明Ascend C DataCopy 在 UB↔GM 方向要求 count*sizeof(T) 为 32 字节对齐，否则搬运量对 32B 向下取整。当纯搬运算子尾 chunk 的实际元素数不满足 32B 对齐时，UB→GM 写方向触发 ERR99999、GM→UB 读方向静默丢尾部数据。判别方法：尾部元素数*sizeof(T)%32!=0 即命中。；《NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写》说明Ascend950/CANN9.1.0 下 NDDMA DataCopy 的非 32B 对齐尾轴须显式设 NdDmaConfig.loopRpSize 右填充(仅 loop0 进硬件指令)且 UB→GM 回写用 DataCopyPad(DataCopyExtParams) 字节粒度；缺 padding 或用 DataCopy(DataCopyParams)(blockLen 以 32B 块为单位)会触发 DYN_COMPILE_FAILURE。。二者在DataCopy尾chunk错误由有效字节数非32B倍数触发，DataCopyPad的逐行、stride、padding和最小DMA卡给出修复边界上存在可执行的直接衔接。
- [postReduceUbSize 不足致 Phase2 读破坏](euclidean_norm_group_post_reduce_ub_size_phase2_chunk.md)（`related`）：目标卡给出 DataCopy 非 32B 尾 chunk 的向下取整/ERR99999 判据，可辅助本卡确认 Phase2 blockLen 非 32B 是搬运边界问题而非 ReduceSum 数值错误。
- [合并尾块的非 32B 行导致 PathB 数据损坏](../precision/datacopypad_rows_must_keep_32_byte_block_length.md)（`related`）：《DataCopy尾chunk非32B对齐触发ERR99999》说明Ascend C DataCopy 在 UB↔GM 方向要求 count*sizeof(T) 为 32 字节对齐，否则搬运量对 32B 向下取整。当纯搬运算子尾 chunk 的实际元素数不满足 32B 对齐时，UB→GM 写方向触发 ERR99999、GM→UB 读方向静默丢尾部数据。判别方法：尾部元素数*sizeof(T)%32!=0 即命中。；《合并尾块的非 32B 行导致 PathB 数据损坏》说明PathB 把 inner 余数合入最后一个二维 DataCopyPad 块后，blockLen 不再是 32B 的整数倍并产生值与索引损坏；保留完整 V32 块、将余数逐行走一维拷贝可恢复正确性。。二者在DataCopy尾chunk错误由有效字节数非32B倍数触发，DataCopyPad的逐行、stride、padding和最小DMA卡给出修复边界上存在可执行的直接衔接。
- [多块 DataCopyPad dst 基址非 32B 对齐崩溃](datacopypad_dst_32b.md)（`related`）：《DataCopy尾chunk非32B对齐触发ERR99999》说明Ascend C DataCopy 在 UB↔GM 方向要求 count*sizeof(T) 为 32 字节对齐，否则搬运量对 32B 向下取整。当纯搬运算子尾 chunk 的实际元素数不满足 32B 对齐时，UB→GM 写方向触发 ERR99999、GM→UB 读方向静默丢尾部数据。判别方法：尾部元素数*sizeof(T)%32!=0 即命中。；《多块 DataCopyPad dst 基址非 32B 对齐崩溃》说明多块 DataCopyPad(DataCopyExtParams) 把跨 slice 的 x0/x1 分段搬进 UB 时，若 head 块拷贝写入非 32B 整数倍字节长度，后续 middle/tail 块的 dst 基址随拷贝累积到非 32B 对齐地址，触发 MTE 地址未对齐 → vector core exception (EE9999 / 507035 rtDeviceSynchronizeWithTimeout)。判别方法：多块搬运上板即 EE9999，且 middle dst 基址字节偏移 firstLen*sizeof(T) 对 32 取余非零即命中；修复方向是按 alignUpS 步长重排 UB 为补齐布局，让每块 dst 基址 32B 对齐。。二者在DataCopy尾chunk错误由有效字节数非32B倍数触发，DataCopyPad的逐行、stride、padding和最小DMA卡给出修复边界上存在可执行的直接衔接。
- [多核非对齐 DataCopyPad 写回边界互相覆盖](../precision/multicore_non_aligned_datacopypad_rmw_overlap.md)（`related`）：《DataCopy尾chunk非32B对齐触发ERR99999》说明Ascend C DataCopy 在 UB↔GM 方向要求 count*sizeof(T) 为 32 字节对齐，否则搬运量对 32B 向下取整。当纯搬运算子尾 chunk 的实际元素数不满足 32B 对齐时，UB→GM 写方向触发 ERR99999、GM→UB 读方向静默丢尾部数据。判别方法：尾部元素数*sizeof(T)%32!=0 即命中。；《多核非对齐 DataCopyPad 写回边界互相覆盖》说明相邻核以非 32B 对齐列块执行 DataCopyPad GM 写回时，尾块 RMW 可覆盖邻核边界数据；按 dtype 的 32B 粒度对齐非尾 colTile 可消除竞态。。二者在DataCopy尾chunk错误由有效字节数非32B倍数触发，DataCopyPad的逐行、stride、padding和最小DMA卡给出修复边界上存在可执行的直接衔接。
- [DataCopy 非32字节对齐尾块丢字节](../precision/datacopy_32.md)（`same_topic`）：《DataCopy尾chunk非32B对齐触发ERR99999》说明Ascend C DataCopy 在 UB↔GM 方向要求 count*sizeof(T) 为 32 字节对齐，否则搬运量对 32B 向下取整。当纯搬运算子尾 chunk 的实际元素数不满足 32B 对齐时，UB→GM 写方向触发 ERR99999、GM→UB 读方向静默丢尾部数据。判别方法：尾部元素数*sizeof(T)%32!=0 即命中。；《DataCopy 非32字节对齐尾块丢字节》说明AscendC::DataCopy 按硬件 32 字节块长搬运，count*sizeof(dtype) 非 32B 倍数时向下取整丢弃尾部字节，UB↔GM 尾块元素被写成 0。判别=逐元素对比定位首个 mismatch index，若集中在尾部且 mismatch 数=count−floor(count*sizeof/32)*32/sizeof 即锁定。修复方向 DataCopyPad 显式 blockLen。。二者在DataCopy尾chunk错误由有效字节数非32B倍数触发，DataCopyPad的逐行、stride、padding和最小DMA卡给出修复边界上存在可执行的直接衔接。
<!-- cannbot:related:end -->
