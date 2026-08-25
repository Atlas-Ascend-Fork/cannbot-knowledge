---
type: "Runbook"
title: "Gather 双加 LocalTensor 基址导致交错旋转乱码"
description: "Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。"
tags: ["task.debugging", "topic.precision", "topic.compute.indexing", "topic.implementation.memory_management"]
status: stable
sources: []
created_at: "2026-08-14T03:54:37Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["a3"]
aliases: ["byte_offset"]
---

# Gather 双加 LocalTensor 基址导致交错旋转乱码

## 现象

在 Ascend C 直调工程中实现旋转位置编码的 interleaved 分支时，kernel 已能编译，half 分支也通过；但运行覆盖 half/interleaved 与三种 dtype 的额外测试后，interleaved 的三项全部失败，其中 bfloat16 的 MARE 约为 400。随后用已知小输入直接打印结果，golden 与 NPU 输出完全不同，表现为大幅乱码而非普通舍入误差。当时代码用字节表驱动 LocalTensor 版 `Gather`，同时把源 LocalTensor 的 `GetPhyAddr()` 传给 `srcBaseAddr`。

## 适用场景

- 工程形态：classic Ascend C 直调 kernel 的定向精度调试。
- API 路径：`Gather`、`srcBaseAddr`、`LocalTensor`、`GetPhyAddr` 所在的 kernel、host 或构建接口链。
- 验证平台与版本：平台 a3；CANN：unknown。
- 适用粒度：`operator_family`，只迁移卡内同一机制，不外推到未验证 dtype、layout 或执行路径。
- 路线优先级：`recommended_fastpath`。
- 不适用/停止边界：错误信号、API 契约或数据路径与本卡不一致时停止套用；修复后未闭合原信号则回到根因诊断。

## 根因

LocalTensor 参数已经确定了源数据的 UB 基址；该重载的有效寻址可按 `src.LocalBase + srcBaseAddr + offsets[i]` 理解。原代码又把 `src.GetPhyAddr()` 当成 `srcBaseAddr`，于是源基址被计入两次，offset 表无论使用字节还是元素数都只能改变“错读到哪里”，不能消除重复基址。修复后的约定是：offset 表按字节生成，`srcBaseAddr=0`。

## 解决配方

### before

- path: `operators/apply_rotary_pos_emb/apply_rotary_pos_emb.asc`
- symbol: `KernelApplyRotaryPosEmb<T>::ComputeRow`, `BuildInterleavedTables`
- claim: offset 以字节生成，但 Gather 的 srcBaseAddr 再传 LocalTensor 物理地址，形成重复基址

```cpp
    __aicore__ inline void ComputeRow(uint32_t r, GlobalTensor<T>& xGm, GlobalTensor<T>& yGm) {
        uint32_t s = RowToSeqIdx(r);

        // --- CopyIn x ---
        LocalTensor<T> xUb = inQueueX.AllocTensor<T>();
        DataCopyExtParams copyX{1, static_cast<uint32_t>(D_ * sizeof(T)), 0, 0, 0};
        DataCopyPadExtParams<T> padX{false, 0, 0, 0};
        DataCopyPad(xUb, xGm[(uint64_t)r * D_], copyX, padX);
        inQueueX.EnQue(xUb);
        LocalTensor<T> xUbDeq = inQueueX.DeQue<T>();

        // --- CopyIn cos / sin (half-D rows) ---
        LocalTensor<T> cosUb = inQueueCos.AllocTensor<T>();
        DataCopyExtParams copyC{1, static_cast<uint32_t>(halfD_ * sizeof(T)), 0, 0, 0};
        DataCopyPadExtParams<T> padC{false, 0, 0, 0};
        DataCopyPad(cosUb, cosGm[(uint64_t)s * halfD_], copyC, padC);
        inQueueCos.EnQue(cosUb);
        LocalTensor<T> cosUbDeq = inQueueCos.DeQue<T>();

        LocalTensor<T> sinUb = inQueueSin.AllocTensor<T>();
        DataCopyPad(sinUb, sinGm[(uint64_t)s * halfD_], copyC, padC);
        inQueueSin.EnQue(sinUb);
        LocalTensor<T> sinUbDeq = inQueueSin.DeQue<T>();

        // --- Cast x -> fp32 (fp32 input: DataCopy; fp16/bf16: Cast CAST_NONE) ---
        LocalTensor<float> xFp32 = xFp32Buf.Get<float>();
        if constexpr (std::is_same_v<T, float>) {
            DataCopy(xFp32, xUbDeq, DAlignF_);
        } else {
            Cast(xFp32, xUbDeq, RoundMode::CAST_NONE, D_);
        }
        PipeBarrier<PIPE_V>();

        // --- Cast cos/sin -> fp32 ---
        LocalTensor<float> cosHalfF = cosHalfFBuf.Get<float>();
        LocalTensor<float> sinHalfF = sinHalfFBuf.Get<float>();
        if constexpr (std::is_same_v<T, float>) {
            DataCopy(cosHalfF, cosUbDeq, halfDAlignF_);
            DataCopy(sinHalfF, sinUbDeq, halfDAlignF_);
        } else {
            Cast(cosHalfF, cosUbDeq, RoundMode::CAST_NONE, halfD_);
            Cast(sinHalfF, sinUbDeq, RoundMode::CAST_NONE, halfD_);
        }
        PipeBarrier<PIPE_V>();

        LocalTensor<float> cosFullF = cosFullFBuf.Get<float>();
        LocalTensor<float> sinFullF = sinFullFBuf.Get<float>();
        LocalTensor<float> rotF = rotFBuf.Get<float>();

        if (mode_ == 0) {
            // half: cos_full = [cos_half | cos_half] (repeat-2x)
            DataCopy(cosFullF, cosHalfF, halfD_);
            DataCopy(cosFullF[halfD_], cosHalfF, halfD_);
            DataCopy(sinFullF, sinHalfF, halfD_);
            DataCopy(sinFullF[halfD_], sinHalfF, halfD_);
            PipeBarrier<PIPE_V>();
            // rotate_half = concat(-x2, x1): rot[0..h) <- x[h..D) then negate; rot[h..D) <- x[0..h)
            DataCopy(rotF, xFp32[halfD_], halfD_);
            DataCopy(rotF[halfD_], xFp32, halfD_);
            PipeBarrier<PIPE_V>();
            Muls(rotF, rotF, -1.0f, halfD_);   // negate first half -> [-x2 | x1]
            PipeBarrier<PIPE_V>();
        } else {
            // interleaved: cos_full[2k]=cos_full[2k+1]=cos_half[k] via Gather(offExpand[i]=i/2)
            Gather(cosFullF, cosHalfF, offExpandBuf.Get<uint32_t>(),
                   (uint32_t)cosHalfF.GetPhyAddr(), D_);
            Gather(sinFullF, sinHalfF, offExpandBuf.Get<uint32_t>(),
                   (uint32_t)sinHalfF.GetPhyAddr(), D_);
            PipeBarrier<PIPE_V>();
            // rotate_half interleaved: rot[i]=x[i^1], then *signFull[-1,1,-1,1..]
            Gather(rotF, xFp32, offRotBuf.Get<uint32_t>(),
                   (uint32_t)xFp32.GetPhyAddr(), D_);
            PipeBarrier<PIPE_V>();
            Mul(rotF, rotF, signFullBuf.Get<float>(), D_);
            PipeBarrier<PIPE_V>();
        }

        // --- y = x*cos + rot*sin ---
        LocalTensor<float> mulF = mulFBuf.Get<float>();
        LocalTensor<float> yFp32 = yFp32Buf.Get<float>();
        Mul(mulF, xFp32, cosFullF, D_);
        PipeBarrier<PIPE_V>();
        Mul(yFp32, rotF, sinFullF, D_);
        PipeBarrier<PIPE_V>();
        Add(yFp32, yFp32, mulF, D_);
        PipeBarrier<PIPE_V>();

        // --- Cast y -> input dtype (fp32: DataCopy; fp16/bf16: Cast CAST_ROUND) ---
        LocalTensor<T> yUb = outQueueY.AllocTensor<T>();
        if constexpr (std::is_same_v<T, float>) {
            DataCopy(yUb, yFp32, DAlignF_);
        } else {
            Cast(yUb, yFp32, RoundMode::CAST_ROUND, D_);
        }
        outQueueY.EnQue<T>(yUb);
        LocalTensor<T> yUbDeq = outQueueY.DeQue<T>();

        DataCopyExtParams copyY{1, static_cast<uint32_t>(D_ * sizeof(T)), 0, 0, 0};
        DataCopyPad(yGm[(uint64_t)r * D_], yUbDeq, copyY);

        inQueueX.FreeTensor(xUbDeq);
        inQueueCos.FreeTensor(cosUbDeq);
        inQueueSin.FreeTensor(sinUbDeq);
        outQueueY.FreeTensor(yUbDeq);
    }

    __aicore__ inline void BuildInterleavedTables() {
        LocalTensor<uint32_t> offExpand = offExpandBuf.Get<uint32_t>();
        LocalTensor<uint32_t> offRot = offRotBuf.Get<uint32_t>();
        LocalTensor<float> signFull = signFullBuf.Get<float>();
        for (uint32_t i = 0; i < D_; i++) {
            offExpand.SetValue(i, (i / 2) * sizeof(float));           // byte offset
            offRot.SetValue(i, (i ^ 1) * sizeof(float));              // byte offset
            signFull.SetValue(i, ((i & 1U) == 0) ? -1.0f : 1.0f);
        }
        PipeBarrier<PIPE_V>();
    }
```

### after

- path: `operators/apply_rotary_pos_emb/apply_rotary_pos_emb.asc`
- symbol: `KernelApplyRotaryPosEmb<T>::ComputeRow`, `BuildInterleavedTables`
- claim: 保留字节 offset，把 LocalTensor Gather 的附加基址置 0

```cpp
    __aicore__ inline void ComputeRow(uint32_t r, GlobalTensor<T>& xGm, GlobalTensor<T>& yGm) {
        uint32_t s = RowToSeqIdx(r);

        // --- CopyIn x ---
        LocalTensor<T> xUb = inQueueX.AllocTensor<T>();
        DataCopyExtParams copyX{1, static_cast<uint32_t>(D_ * sizeof(T)), 0, 0, 0};
        DataCopyPadExtParams<T> padX{false, 0, 0, 0};
        DataCopyPad(xUb, xGm[(uint64_t)r * D_], copyX, padX);
        inQueueX.EnQue(xUb);
        LocalTensor<T> xUbDeq = inQueueX.DeQue<T>();

        // --- CopyIn cos / sin (half-D rows) ---
        LocalTensor<T> cosUb = inQueueCos.AllocTensor<T>();
        DataCopyExtParams copyC{1, static_cast<uint32_t>(halfD_ * sizeof(T)), 0, 0, 0};
        DataCopyPadExtParams<T> padC{false, 0, 0, 0};
        DataCopyPad(cosUb, cosGm[(uint64_t)s * halfD_], copyC, padC);
        inQueueCos.EnQue(cosUb);
        LocalTensor<T> cosUbDeq = inQueueCos.DeQue<T>();

        LocalTensor<T> sinUb = inQueueSin.AllocTensor<T>();
        DataCopyPad(sinUb, sinGm[(uint64_t)s * halfD_], copyC, padC);
        inQueueSin.EnQue(sinUb);
        LocalTensor<T> sinUbDeq = inQueueSin.DeQue<T>();

        // --- Cast x -> fp32 (fp32 input: DataCopy; fp16/bf16: Cast CAST_NONE) ---
        LocalTensor<float> xFp32 = xFp32Buf.Get<float>();
        if constexpr (std::is_same_v<T, float>) {
            DataCopy(xFp32, xUbDeq, DAlignF_);
        } else {
            Cast(xFp32, xUbDeq, RoundMode::CAST_NONE, D_);
        }
        PipeBarrier<PIPE_V>();

        // --- Cast cos/sin -> fp32 ---
        LocalTensor<float> cosHalfF = cosHalfFBuf.Get<float>();
        LocalTensor<float> sinHalfF = sinHalfFBuf.Get<float>();
        if constexpr (std::is_same_v<T, float>) {
            DataCopy(cosHalfF, cosUbDeq, halfDAlignF_);
            DataCopy(sinHalfF, sinUbDeq, halfDAlignF_);
        } else {
            Cast(cosHalfF, cosUbDeq, RoundMode::CAST_NONE, halfD_);
            Cast(sinHalfF, sinUbDeq, RoundMode::CAST_NONE, halfD_);
        }
        PipeBarrier<PIPE_V>();

        LocalTensor<float> cosFullF = cosFullFBuf.Get<float>();
        LocalTensor<float> sinFullF = sinFullFBuf.Get<float>();
        LocalTensor<float> rotF = rotFBuf.Get<float>();

        if (mode_ == 0) {
            // half: cos_full = [cos_half | cos_half] (repeat-2x)
            DataCopy(cosFullF, cosHalfF, halfD_);
            DataCopy(cosFullF[halfD_], cosHalfF, halfD_);
            DataCopy(sinFullF, sinHalfF, halfD_);
            DataCopy(sinFullF[halfD_], sinHalfF, halfD_);
            PipeBarrier<PIPE_V>();
            // rotate_half = concat(-x2, x1): rot[0..h) <- x[h..D) then negate; rot[h..D) <- x[0..h)
            DataCopy(rotF, xFp32[halfD_], halfD_);
            DataCopy(rotF[halfD_], xFp32, halfD_);
            PipeBarrier<PIPE_V>();
            Muls(rotF, rotF, -1.0f, halfD_);   // negate first half -> [-x2 | x1]
            PipeBarrier<PIPE_V>();
        } else {
            // interleaved: cos_full[2k]=cos_full[2k+1]=cos_half[k] via Gather(offExpand[i]=i/2 bytes)
            Gather(cosFullF, cosHalfF, offExpandBuf.Get<uint32_t>(),
                   (uint32_t)0, D_);
            Gather(sinFullF, sinHalfF, offExpandBuf.Get<uint32_t>(),
                   (uint32_t)0, D_);
            PipeBarrier<PIPE_V>();
            // rotate_half interleaved: rot[i]=x[i^1], then *signFull[-1,1,-1,1..]
            Gather(rotF, xFp32, offRotBuf.Get<uint32_t>(),
                   (uint32_t)0, D_);
            PipeBarrier<PIPE_V>();
            Mul(rotF, rotF, signFullBuf.Get<float>(), D_);
            PipeBarrier<PIPE_V>();
        }

        // --- y = x*cos + rot*sin ---
        LocalTensor<float> mulF = mulFBuf.Get<float>();
        LocalTensor<float> yFp32 = yFp32Buf.Get<float>();
        Mul(mulF, xFp32, cosFullF, D_);
        PipeBarrier<PIPE_V>();
        Mul(yFp32, rotF, sinFullF, D_);
        PipeBarrier<PIPE_V>();
        Add(yFp32, yFp32, mulF, D_);
        PipeBarrier<PIPE_V>();

        // --- Cast y -> input dtype (fp32: DataCopy; fp16/bf16: Cast CAST_ROUND) ---
        LocalTensor<T> yUb = outQueueY.AllocTensor<T>();
        if constexpr (std::is_same_v<T, float>) {
            DataCopy(yUb, yFp32, DAlignF_);
        } else {
            Cast(yUb, yFp32, RoundMode::CAST_ROUND, D_);
        }
        outQueueY.EnQue<T>(yUb);
        LocalTensor<T> yUbDeq = outQueueY.DeQue<T>();

        DataCopyExtParams copyY{1, static_cast<uint32_t>(D_ * sizeof(T)), 0, 0, 0};
        DataCopyPad(yGm[(uint64_t)r * D_], yUbDeq, copyY);

        inQueueX.FreeTensor(xUbDeq);
        inQueueCos.FreeTensor(cosUbDeq);
        inQueueSin.FreeTensor(sinUbDeq);
        outQueueY.FreeTensor(yUbDeq);
    }

    __aicore__ inline void BuildInterleavedTables() {
        LocalTensor<uint32_t> offExpand = offExpandBuf.Get<uint32_t>();
        LocalTensor<uint32_t> offRot = offRotBuf.Get<uint32_t>();
        LocalTensor<float> signFull = signFullBuf.Get<float>();
        for (uint32_t i = 0; i < D_; i++) {
            offExpand.SetValue(i, (i / 2) * sizeof(float));           // byte offset within src
            offRot.SetValue(i, (i ^ 1) * sizeof(float));              // byte offset within src
            signFull.SetValue(i, ((i & 1U) == 0) ? -1.0f : 1.0f);
        }
        PipeBarrier<PIPE_V>();
    }
```

验证命令（trace 中原样执行）：

## 设计决策

- 选择“字节 offset + 零附加基址”，因为小输入探针直接验证了该组合与 golden 精确一致。
- 曾把 offset 从字节改为元素下标，但保留物理地址基址后输出仍错误；这排除了“只改 offset 单位”的方案。
- 当前方案属于 `recommended_fastpath`：它恢复正确寻址，未引入额外搬运。

## 预防

- 使用 LocalTensor 版索引 API 前，把地址拆成“张量自身基址、API 附加基址、offset 单位”三项逐一核对。
- 用递增小输入与非对称 cos/sin 构造手算探针；乱码数量级远大于舍入误差时先查寻址。
- offset 单位变更必须与基址语义分开验证，不要一次同时改两项后凭通过猜根因。

## 验证信号

以下信号均来自本次开发会话修复前后的实际构建、运行或评测输出。

- 修复前：bfloat16 gather 定向比较出现 MERE=4.64、MARE=400 的大幅错误。（来源平台：a3；证据等级: tool_observed）。
- 修复后：修正基址后 half/interleaved、三种 dtype 的 9 个 extra-shape 用例全部通过。（来源平台：a3；证据等级: tool_observed）。

## 失效边界

- 只验证了 classic dav-2201 路径的 LocalTensor Gather；不能把 `srcBaseAddr=0` 无条件迁移到以裸地址或 GlobalTensor 为源的重载。
- offset 为字节的结论绑定本次 API 重载；换签名后必须重新核对声明。
- 其他注册平台未验证；推断可迁移前须用同样的小输入探针确认。

## 坏实践

- 把 `GetPhyAddr()` 机械地填入名为 base address 的参数，而忽略 LocalTensor 已携带地址。
- 看到乱码就把 offset 从字节改成元素；本次实测说明这只改变错误读址，未修复双加基址。

## 误诊

这类大幅乱码不是普通 fp16/bf16 舍入问题；先定位索引寻址，再讨论精度策略。

<!-- cannbot:related:start -->
## 相关

- [AscGather](../../apis/simd_api/c_api/reg/reg_load/asc_gather.md)（`exemplifies`）：《Gather 双加 LocalTensor 基址导致交错旋转乱码》处理“Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。”。《AscGather》明确提供“根据索引位置index将源操作数src按元素收集到目的操作数dst中。”，其参数、调用或验证步骤直接接入Gather 的 base 地址、byte offset、重复偏移故障和地址计算合同。
- [AscGather](../../apis/simd_api/c_api/vector_compute/asc_gather.md)（`exemplifies`）：《Gather 双加 LocalTensor 基址导致交错旋转乱码》处理“Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。”。《AscGather》明确提供“将src按照src_offset给定的偏移按元素收集到dst中。”，其参数、调用或验证步骤直接接入Gather 的 base 地址、byte offset、重复偏移故障和地址计算合同。
- [Gather](../../apis/simd_api/basic_api/memory_vector_compute/scatter_gather/gather.md)（`exemplifies`）：《Gather 双加 LocalTensor 基址导致交错旋转乱码》处理“Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。”。《Gather》明确提供“根据基地址和地址偏移张量确定索引，将输入张量中对应元素收集到结果张量中，支持前n个数据和高维切分计算。”，其参数、调用或验证步骤直接接入Gather 的 base 地址、byte offset、重复偏移故障和地址计算合同。
- [Gather](../../apis/simd_api/basic_api/reg_vector_compute/reg_data_load/gather_discrete.md)（`exemplifies`）：《Gather 双加 LocalTensor 基址导致交错旋转乱码》处理“Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。”。《Gather》明确提供“根据索引值index将源操作数按元素收集到目的操作数dstReg中，index中每个元素表示相对于baseAddr的元素位置，支持多种数据类型组合。”，其参数、调用或验证步骤直接接入Gather 的 base 地址、byte offset、重复偏移故障和地址计算合同。
- [Gather](../../apis/simd_api/basic_api/reg_vector_compute/scatter_operations/gather.md)（`exemplifies`）：《Gather》说明根据索引值将源操作数按元素收集到目的操作数中，支持b8、b16、b32数据类型。；《Gather 双加 LocalTensor 基址导致交错旋转乱码》说明Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。。二者在Reg Gather的index和baseAddr寻址合同与C API等价接口、维序/步长及LocalTensor基址故障直接对应上存在可执行的直接衔接。
- [GetBaseAddr](../../apis/simd_api/basic_api/resource_management/t_pipe/get_base_addr.md)（`exemplifies`）：《Gather 双加 LocalTensor 基址导致交错旋转乱码》处理“Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。”。《GetBaseAddr》明确提供“根据传入的logicPos（逻辑抽象位置）获取该位置的基础地址，只在CPU调试场景下生效。通常用于计算Tensor在logicPos的偏移地址。”，其参数、调用或验证步骤直接接入Gather 的 base 地址、byte offset、重复偏移故障和地址计算合同。
- [GetPhyAddr](../../apis/simd_api/basic_api/data_structures/global_tensor/get_phy_addr.md)（`exemplifies`）：《Gather 双加 LocalTensor 基址导致交错旋转乱码》处理“Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。”。《GetPhyAddr》明确提供“GlobalTensor::GetPhyAddr 接口，用于获取全局数据的物理地址，支持全平台。”，其参数、调用或验证步骤直接接入Gather 的 base 地址、byte offset、重复偏移故障和地址计算合同。
- [GetPhyAddr](../../apis/simd_api/basic_api/data_structures/local_tensor/get_phy_addr.md)（`exemplifies`）：《Gather 双加 LocalTensor 基址导致交错旋转乱码》处理“Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。”。《GetPhyAddr》明确提供“返回LocalTensor的地址或指定偏移量后的地址。”，其参数、调用或验证步骤直接接入Gather 的 base 地址、byte offset、重复偏移故障和地址计算合同。
- [LocalTensor](../../apis/simd_api/basic_api/data_structures/local_tensor/local_tensor.md)（`exemplifies`）：LocalTensor 已封装源基址时 Gather 的 srcBaseAddr 只能传相对字节偏移；该卡证明重复传物理基址会二次加址，补充了 LocalTensor 与 Gather 的地址契约。
- [SetAddrWithOffset](../../apis/simd_api/basic_api/data_structures/local_tensor/set_addr_with_offset.md)（`exemplifies`）：《Gather 双加 LocalTensor 基址导致交错旋转乱码》处理“Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。”。《SetAddrWithOffset》明确提供“设置带有偏移的Tensor地址。用于快速获取定义一个Tensor，同时指定新Tensor相对于旧Tensor首地址的偏移。偏移的长度为旧Tensor的元素个数。”，其参数、调用或验证步骤直接接入Gather 的 base 地址、byte offset、重复偏移故障和地址计算合同。
- [Gather算子快速入门](../../guides/getting_started/quick_start/simt_programming/gather_op_quick_start.md)（`related`）：《Gather 双加 LocalTensor 基址导致交错旋转乱码》处理“Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。”。《Gather算子快速入门》明确提供“本入门示例基于Ascend C SIMT实现一维Gather算子，带你快速上手实践，涵盖Device端核函数实现、Host端调用以及编译运行的完整流程，帮助开发者建立整体认知。”，其参数、调用或验证步骤直接接入Gather 的 base 地址、byte offset、重复偏移故障和地址计算合同。
- [按序列位缓存 cos/sin 并让 q/k 共享搬运](../performance/cache_position_coefficients_across_shared_inputs.md)（`related`）：The cached RoPE implementation uses Gather to expand interleaved cos/sin; this runbook supplies the required byte-offset plus zero-additional-base addressing contract.
- [Gather 非 dim 维缩小时折叠步长错位](gather_non_axis_shape_shrink_requires_per_axis_source_strides.md)（`same_topic`）：《Gather 双加 LocalTensor 基址导致交错旋转乱码》处理“Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。”。《Gather 非 dim 维缩小时折叠步长错位》明确提供“torch.gather 的 DMA 与 SIMT 路线都必须按逐维 xstride 和输出坐标寻址；非 dim 维允许缩小，不能折叠成假定 extent 相等的 outer 步长。”，其参数、调用或验证步骤直接接入Gather 的 base 地址、byte offset、重复偏移故障和地址计算合同。
- [gather 扁平偏移公式 dim 上方形状错配](gather_dim.md)（`same_topic`）：《Gather 双加 LocalTensor 基址导致交错旋转乱码》处理“Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。”。《gather 扁平偏移公式 dim 上方形状错配》明确提供“AscendC gather kernel 用扁平公式 outer*x_block_+idx_val*x_inner_+inner 计算 x 偏移，outer 取自 index 坐标系却用 x 的 x_block_ 缩放；当 index 与 x 在 dim 之上某维形状不同时外层坐标错位，致该 case 大面积 mismatch，dim=0 时公式退化为正确故多用例不暴露。”，其参数、调用或验证步骤直接接入Gather 的 base 地址、byte offset、重复偏移故障和地址计算合同。
- [分块 wrapper 与 VF callee 不可重复叠加 offset](wrapper_and_vf_callee_must_not_double_apply_chunk_offset.md)（`same_topic`）：《Gather 双加 LocalTensor 基址导致交错旋转乱码》处理“Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。”。《分块 wrapper 与 VF callee 不可重复叠加 offset》明确提供“asc_vf_call 已传入按 chunk 前移的 UB 指针时，VF callee 再加同一 offset 会从第二块开始按双倍偏移读错数据。”，其参数、调用或验证步骤直接接入Gather 的 base 地址、byte offset、重复偏移故障和地址计算合同。
- [多维 Gather 部分 case 错 — LUT 维序反了](gather_lut_coordinate_decode_must_start_from_last_dimension.md)（`same_topic`）：《Gather 双加 LocalTensor 基址导致交错旋转乱码》处理“Gather 已由 LocalTensor 提供源基址时，srcBaseAddr 再传物理地址会重复加基址；保持字节偏移并传 0 可恢复交错旋转。”。《多维 Gather 部分 case 错 — LUT 维序反了》明确提供“C-contiguous 多维坐标必须从末维逆序解码；host LUT 是正确性回退而非快路，SIMT 可用同一逆序规则在线解码。”，其参数、调用或验证步骤直接接入Gather 的 base 地址、byte offset、重复偏移故障和地址计算合同。
<!-- cannbot:related:end -->
