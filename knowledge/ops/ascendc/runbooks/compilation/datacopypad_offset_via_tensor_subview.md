---
type: "Runbook"
title: "DataCopyPad 五参编译失败—LocalTensor 子视图替代偏移"
description: "CANN 9.0.1 的 GM→UB DataCopyPad 不接收第五个目标偏移参数；先对 LocalTensor 取元素偏移子视图，再调用四参数重载。"
tags: ["task.debugging", "topic.data_movement.data_copy", "topic.implementation"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# DataCopyPad 五参编译失败—LocalTensor 子视图替代偏移

## 现象

在 Ascend950 Flash kernel 的 `LoadCosTile` 中，把每行 GM 数据依次搬入同一块 UB tile。初始代码尝试把目标行偏移作为 `DataCopyPad` 第五个参数传入：

```text
error: no matching function for call to 'DataCopyPad'
candidate function template not viable: requires 4 arguments, but 5 were provided
```

编译器同时列出 GM→UB 的 `DataCopyPad(const LocalTensor<T> &dst, ...)` 候选，但这些候选只接受四个参数。错误在 fp32 分支的 cos/sin 搬入点首先出现；相同的五参写法也存在于 fp16/bf16 原始输入分支。

## 适用场景

- 工程形态：Flash kernel 直调工程，在 `.asc` kernel 类中把多行 GM 数据搬入连续的 UB tile；
- API 路径：`AscendC::LocalTensor<T>`、`AscendC::GlobalTensor<T>`、`AscendC::DataCopyExtParams`、`AscendC::DataCopyPadExtParams<T>` 与 GM→UB `AscendC::DataCopyPad`；
- 验证过的平台与 CANN 版本：950 / CANN 9.0.1；与 frontmatter `platforms` 一致；
- 适用粒度：`platform_wide`，结论约束的是该工具链下 GM→UB `DataCopyPad` 的重载形态，与 RoPE 数学语义无关；
- 路线优先级：`recommended_fastpath`，先把元素偏移编码进 `LocalTensor` 子视图，再调用四参数重载；
- 明确不适用 / 未验证场景：Local→GM、Local→Local 的其他重载，以及其他 CANN 版本均未在本轨迹中隔离验证。

## 根因

CANN 9.0.1 的 GM→UB `DataCopyPad` 重载不接收独立的第五个目标偏移参数，目标 UB 偏移必须先编码进传入的 `LocalTensor` 子视图。

机制链为：

1. 原调用形态是 `DataCopyPad(dst, src, copyParams, padParams, dstOffset)`，实参个数为 5；
2. 编译器可见候选要求 4 个参数，因此在重载决议阶段直接失败，尚未进入 kernel 运行；
3. `dst[(int64_t)i * d2]` 把第 `i` 行的元素偏移编码进目标 `LocalTensor`；
4. 随后调用 `DataCopyPad(dstSubview, src, copyParams, padParams)`，实参个数与 GM→UB 重载一致。

## 解决配方

保留每行独立的 GM 源地址计算，把目标偏移从不存在的第五个参数移到 `LocalTensor::operator[]` 形成的子视图中。fp32 与 fp16/bf16 两条模板分支必须一起修改，避免只修当前实例化到的 dtype。

### before

代码证据：revision=`未提交的首次完整工作树写入`；path=`operators/apply_rotary_pos_emb/apply_rotary_pos_emb.asc`；symbol=`KernelApplyRotaryPosEmb<T>::LoadCosTile`；lines=`284-314`。该完整函数支撑“五参数调用位于两条 dtype 分支”的结论。

```cpp
    __aicore__ inline void LoadCosTile(uint32_t rowOff, uint32_t rows)
    {
        uint32_t d2 = static_cast<uint32_t>(halfD_);
        if constexpr (std::is_same<T, float>::value) {
            auto cL = cosfQ_.AllocTensor<float>();
            auto sL = sinfQ_.AllocTensor<float>();
            AscendC::DataCopyExtParams cp{1, d2 * static_cast<uint32_t>(sizeof(float)), 0, 0, 0};
            AscendC::DataCopyPadExtParams<float> pad{false, 0, 0, 0};
            for (uint32_t i = 0; i < rows; ++i) {
                int64_t gr = rowStart_ + static_cast<int64_t>(rowOff) + static_cast<int64_t>(i);
                int64_t s = compute_s(gr, sLen_, nHeads_, layout_);
                AscendC::DataCopyPad(cL, cosGm_[s * d2], cp, pad, (int64_t)i * d2);
                AscendC::DataCopyPad(sL, sinGm_[s * d2], cp, pad, (int64_t)i * d2);
            }
            cosfQ_.EnQue(cL);
            sinfQ_.EnQue(sL);
        } else {
            auto cR = cosRawQ_.AllocTensor<T>();
            auto sR = sinRawQ_.AllocTensor<T>();
            AscendC::DataCopyExtParams cp{1, d2 * static_cast<uint32_t>(sizeof(T)), 0, 0, 0};
            AscendC::DataCopyPadExtParams<T> pad{false, 0, 0, 0};
            for (uint32_t i = 0; i < rows; ++i) {
                int64_t gr = rowStart_ + static_cast<int64_t>(rowOff) + static_cast<int64_t>(i);
                int64_t s = compute_s(gr, sLen_, nHeads_, layout_);
                AscendC::DataCopyPad(cR, cosGm_[s * d2], cp, pad, (int64_t)i * d2);
                AscendC::DataCopyPad(sR, sinGm_[s * d2], cp, pad, (int64_t)i * d2);
            }
            cosRawQ_.EnQue(cR);
            sinRawQ_.EnQue(sR);
        }
    }
```

### after

代码证据：revision=`修复后工作树，随后纳入轨迹所示短提交 6c6eecf；40 位 SHA 未提供`；path=`operators/apply_rotary_pos_emb/apply_rotary_pos_emb.asc`；symbol=`KernelApplyRotaryPosEmb<T>::LoadCosTile`；lines=`284-314`。该函数由首次完整写入与四条逐字替换机械恢复，支撑“子视图 + 四参数重载”的修复结论。

```cpp
    __aicore__ inline void LoadCosTile(uint32_t rowOff, uint32_t rows)
    {
        uint32_t d2 = static_cast<uint32_t>(halfD_);
        if constexpr (std::is_same<T, float>::value) {
            auto cL = cosfQ_.AllocTensor<float>();
            auto sL = sinfQ_.AllocTensor<float>();
            AscendC::DataCopyExtParams cp{1, d2 * static_cast<uint32_t>(sizeof(float)), 0, 0, 0};
            AscendC::DataCopyPadExtParams<float> pad{false, 0, 0, 0};
            for (uint32_t i = 0; i < rows; ++i) {
                int64_t gr = rowStart_ + static_cast<int64_t>(rowOff) + static_cast<int64_t>(i);
                int64_t s = compute_s(gr, sLen_, nHeads_, layout_);
                AscendC::DataCopyPad(cL[(int64_t)i * d2], cosGm_[s * d2], cp, pad);
                AscendC::DataCopyPad(sL[(int64_t)i * d2], sinGm_[s * d2], cp, pad);
            }
            cosfQ_.EnQue(cL);
            sinfQ_.EnQue(sL);
        } else {
            auto cR = cosRawQ_.AllocTensor<T>();
            auto sR = sinRawQ_.AllocTensor<T>();
            AscendC::DataCopyExtParams cp{1, d2 * static_cast<uint32_t>(sizeof(T)), 0, 0, 0};
            AscendC::DataCopyPadExtParams<T> pad{false, 0, 0, 0};
            for (uint32_t i = 0; i < rows; ++i) {
                int64_t gr = rowStart_ + static_cast<int64_t>(rowOff) + static_cast<int64_t>(i);
                int64_t s = compute_s(gr, sLen_, nHeads_, layout_);
                AscendC::DataCopyPad(cR[(int64_t)i * d2], cosGm_[s * d2], cp, pad);
                AscendC::DataCopyPad(sR[(int64_t)i * d2], sinGm_[s * d2], cp, pad);
            }
            cosRawQ_.EnQue(cR);
            sinRawQ_.EnQue(sR);
        }
    }
```

## 设计决策

- 选择 `LocalTensor` 子视图承载目标元素偏移，是因为工具链暴露的 GM→UB 重载本身只有四个参数；该形态保留原有 copy/pad 参数与逐行源地址计算。
- 没有改成四次单独 buffer 或另建临时 tensor；这些方案会改变现有 UB 生命周期，且轨迹没有验证其必要性。
- 当前方案标为 `recommended_fastpath`：它是本轨迹中唯一被编译、pytest 与最终评测共同验证的重载写法，但不宣称对其他 CANN 版本性能最优。

## 系统信息

- toolchain：远端 CANN 9.0.1，编译器头文件来自 `x86_64-linux/asc/impl/basic_api/kernel_operator_data_copy_intf_impl.h`；
- 平台：Ascend950PR_957b，NpuArch=dav-3510，物理卡 6；
- 工程形态：单文件 `.asc` Flash direct-launch 共享库；
- 相关文件：`operators/apply_rotary_pos_emb/apply_rotary_pos_emb.asc`。

## 性能影响

本轨迹没有对五参写法与子视图写法做可运行的成对 profiling；五参写法无法通过编译，因此不作性能收益结论。

## 预防

- 写 GM→UB `DataCopyPad` 前先按当前 CANN 头文件确认重载参数个数；
- 多行写入同一 UB tile 时，把目标偏移表达成 `LocalTensor` 子视图，不要凭其他 API 经验添加第五个 offset；
- 模板分支中的同类调用一次性全查，避免只修当前报错的 fp32 实例而遗漏 fp16/bf16 分支；
- 编译日志出现 `requires 4 arguments, but 5 were provided` 时先查重载形态，而不是调整 blockLen 或 pad 数值。

## 验证信号

来源说明：这条知识来自一次 dav-3510 Flash 算子首次远端构建失败；四处 `DataCopyPad` 调用改为目标子视图后，与同批 dtype 命名空间修复一起重编并继续完成真机验证。

- 修复后远端构建输出 `[100%] Built target op_apply_rotary_pos_emb`（950，证据等级: tool_observed）；
- 修复后的共享库在真机 pytest 中 52/52 通过（950，证据等级: tool_observed）；
- 最终 cann-bench 20/20 用例通过（950，证据等级: tool_observed）。

## 失效边界

- 本卡只验证 CANN 9.0.1 下 GM→UB `DataCopyPad`；其他搬运方向的重载须重新查签名；
- `LocalTensor` 下标按元素偏移使用，不能把字节偏移不经换算直接代入；
- A2/A3 与其他 CANN 版本未验证，若 API 仍暴露相同四参签名则推断可迁移（未验证，推断可迁移）。

## 坏实践

- 把 `dstOffset` 当成所有 `DataCopyPad` 重载都支持的通用第五参数；编译器会在重载决议阶段拒绝，运行时参数调整无法补救。
- 只修编译器最先实例化的 fp32 分支；模板的其他 dtype 分支稍后实例化时仍会再次失败。

## 误诊

无证据表明 blockLen、32B 对齐或 padding 数值导致本次错误；原始错误明确发生在参数个数不匹配的重载决议阶段。

<!-- cannbot:related:start -->
## 相关

- [DataCopyPad](../../apis/simd_api/basic_api/memory_vector_compute/data_move/data_copy_pad_gm_to_ub.md)（`exemplifies`）：《DataCopyPad》说明将数据从GM非对齐搬运至UB，可根据需要自行填充数据。；《DataCopyPad 五参编译失败—LocalTensor 子视图替代偏移》说明CANN 9.0.1 的 GM→UB DataCopyPad 不接收第五个目标偏移参数；先对 LocalTensor 取元素偏移子视图，再调用四参数重载。。二者在GM到UB非对齐搬入依赖Pad参数、32B最小DMA和LocalTensor/offset/rightPad合同，UB到GM方向的重载不同上存在可执行的直接衔接。
- [LocalTensor构造函数](../../apis/simd_api/basic_api/data_structures/local_tensor/local_tensor_constructor.md)（`exemplifies`）：《LocalTensor构造函数》处理“LocalTensor构造函数。”。《DataCopyPad 五参编译失败—LocalTensor 子视图替代偏移》明确“CANN 9.0.1 的 GM→UB DataCopyPad 不接收第五个目标偏移参数；先对 LocalTensor 取元素偏移子视图，再调用四参数重载。”，可直接用于核对LocalTensor 的默认/静态地址构造、LocalMemAllocator 构造路径及错误实参诊断。
- [SetAddrWithOffset](../../apis/simd_api/basic_api/data_structures/local_tensor/set_addr_with_offset.md)（`exemplifies`）：该 API 给出以元素 offset 建立 LocalTensor 地址视图的正式接口，可作为 focal 中 operator[] 子视图方案的显式地址偏移替代，并提醒 offset 单位是元素而非字节。
- [DataCopyPad UB→GM 四参调用导致编译失败](datacopypad_ub_to_gm_has_no_pad_params.md)（`related`）：该卡进一步说明 GM→UB 四参数 load 不接受第五个目标 offset，偏移要由 LocalTensor 子视图承载；与 focal 共同给出方向、arity、offset 三步调用判别。
- [DataCopyPad rightPad 字段为 uint8_t](datacopypad_rightpad_uint8_t.md)（`related`）：GM→UB 四参数结构确定后，PadExtParams 的 rightPadding 字段类型仍可能独立阻断编译；该卡补充了 focal 调用链中 padding 结构的字段契约。
- [DataCopyPad 尾块改逐行一维搬入](../precision/datacopypad_partial_2d_blocks_use_per_row_copy.md)（`related`）：DataCopyPad 尾块改逐行一维搬入 与《DataCopyPad 五参编译失败—LocalTensor 子视图替代偏移》的衔接是：这些候选直接解释 DataCopy/DataCopyPad 的 blockCount、行跨度、32B/256B 粒度、padding 与地址偏移；它们可用于判断短二维行何时必须退化为逐行复制。
- [DataCopyPad 无匹配重载 LocalTensor 实参不一致](datacopypad_localtensor.md)（`related`）：两卡共同给出 DataCopyPad `no matching function` 的分诊边界：一个由第五个偏移实参造成，另一个由 LocalTensor/GlobalTensor 元素类型不一致造成。
- [多块 DataCopyPad dst 基址非 32B 对齐崩溃](datacopypad_dst_32b.md)（`related`）：focal 用 LocalTensor 子视图改变实际 UB 目标基址；该卡给出后续多块搬运必须继续核对 32B 目标地址对齐的运行期约束，避免编译通过后转为 507035。
- [DataCopyPad 加载缺少 Pad 参数导致编译失败](datacopypad_gm_to_ub_requires_pad_params.md)（`same_topic`）：两卡处理同一个 GM→UB overload 契约：缺少 Pad 参数是三参错误，多传目标 offset 是五参错误；合法调用固定为四参，offset 由 tensor 视图承担。
- [Vector Sub 源 UB 非 32B 对齐触发错误 340](vector_sub_ub_32b_340.md)（`same_topic`）：Vector Sub 源 UB 非 32B 对齐触发错误 340 与《DataCopyPad 五参编译失败—LocalTensor 子视图替代偏移》的实质衔接是：Vector Sub 的每个 UB 源必须 32B 对齐，LocalTensor 非零 operator[] 偏移会破坏对齐；Sub API、GetWithOffset/TBuf 和相邻未对齐故障卡直接支持定位及对齐搬入修法。
<!-- cannbot:related:end -->
