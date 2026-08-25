---
type: "Runbook"
title: "fp32 UB 非 VL 拷贝须用带掩码 Reg"
description: "fp32 UB 局部 DataCopy 在非 vector-length 元素数上产生轴相关错误；使用 UpdateMask 的 Reg load/store 复制尾块。"
tags: ["task.debugging", "topic.precision", "topic.implementation.masking", "topic.programming_model.execution_unit.vector"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# fp32 UB 非 VL 拷贝须用带掩码 Reg

## 现象

非末轴 fp32 三遍规约在 b16 已通过后仍出现大误差。定向探针显示：同一实现中，内层连续长度恰为 fp32 VL 整倍数时 `maxdiff≈2e-8`，只增加一个元素就变成 `7.62e-1`；其他非 VL 长度出现 `1.69e+0`、`1.33e+0`。这把根因从规约和多核切分缩小到 fp32 UB→UB 局部复制的尾块。

## 适用场景

- 工程形态：Ascend950 Reg 直调 kernel；
- API 路径：`AscendC::DataCopy(LocalTensor, LocalTensor, count)` 用于 fp32 UB 局部复制；
- 验证过的平台与版本：950 / CANN 9.0.1；
- 适用粒度：`platform_wide`；
- 路线优先级：`recommended_fastpath`；
- 明确不适用：GM↔UB 的 `DataCopyPad`，或已证明 LocalTensor DataCopy 支持任意 count 的其他 SDK/API overload。

## 根因

该路径的 classic fp32 UB local `DataCopy` 没有按有效元素 mask 处理最后一个不足 VL 的寄存器块；当 count 不是 VL 整倍数时，尾部复制污染后续规约。VL 整倍数全部正确、非整倍数稳定失败，而相同计算换成 `UpdateMask(remaining)` 的 Reg load/store 后恢复，形成了机制闭环。

## 解决配方

把 UB→UB fp32 局部复制改成按 VL 循环的 masked Reg copy；逻辑 count 控制最后一个 mask，物理 buffer 另行按 VL 扩容。

### before

```cpp
__aicore__ inline __ubuf__ float *LoadRowFp32(int64_t off)
{
    AscendC::DataCopyExtParams cp{
        1, static_cast<uint32_t>(a0_ * sizeof(T)), 0, 0, 0};
    AscendC::DataCopyPadExtParams<T> pad;
    rowInLocal_ = inQueueRow_.AllocTensor<T>();
    AscendC::DataCopyPad(rowInLocal_, xGm_[off], cp, pad);
    inQueueRow_.EnQue(rowInLocal_);
    rowInLocal_ = inQueueRow_.DeQue<T>();
    auto fp32Local = rowFp32Buf_.Get<float>();
    if constexpr (std::is_same<T, float>::value) {
        AscendC::DataCopy(fp32Local, rowInLocal_, a0_);
    } else {
        AscendC::Cast<float, T>(
            fp32Local, rowInLocal_, AscendC::RoundMode::CAST_NONE, castCount_);
    }
    AscendC::PipeBarrier<PIPE_V>();
    return (__ubuf__ float *)fp32Local.GetPhyAddr();
}
```

### after

```cpp
__simd_vf__ inline void copy_fp32_vf(__ubuf__ float *dst, __ubuf__ float *src,
                                     uint32_t count, uint32_t chunkCount)
{
    constexpr uint32_t VL = AscendC::VECTOR_REG_WIDTH / sizeof(float);
    AscendC::Reg::RegTensor<float> reg;
    for (uint32_t c = 0; c < chunkCount; ++c) {
        uint32_t off = c * VL;
        uint32_t rem = count - off;
        AscendC::Reg::MaskReg mask = AscendC::Reg::UpdateMask<float>(rem);
        AscendC::Reg::LoadAlign<float, AscendC::Reg::LoadDist::DIST_NORM>(
            reg, src + off);
        AscendC::Reg::StoreAlign<float, AscendC::Reg::StoreDist::DIST_NORM_B32>(
            dst + off, reg, mask);
    }
}

__aicore__ inline __ubuf__ float *LoadRowFp32(int64_t off)
{
    AscendC::DataCopyExtParams cp{
        1, static_cast<uint32_t>(a0_ * sizeof(T)), 0, 0, 0};
    AscendC::DataCopyPadExtParams<T> pad;
    rowInLocal_ = inQueueRow_.AllocTensor<T>();
    AscendC::DataCopyPad(rowInLocal_, xGm_[off], cp, pad);
    inQueueRow_.EnQue(rowInLocal_);
    rowInLocal_ = inQueueRow_.DeQue<T>();
    auto fp32Local = rowFp32Buf_.Get<float>();
    if constexpr (std::is_same<T, float>::value) {
        constexpr uint32_t VL = AscendC::VECTOR_REG_WIDTH / sizeof(float);
        uint32_t cc = (castCount_ + VL - 1) / VL;
        asc_vf_call<copy_fp32_vf>(
            (__ubuf__ float *)fp32Local.GetPhyAddr(),
            (__ubuf__ float *)rowInLocal_.GetPhyAddr(), castCount_, cc);
    } else {
        AscendC::Cast<float, T>(
            fp32Local, rowInLocal_, AscendC::RoundMode::CAST_NONE, castCount_);
    }
    AscendC::PipeBarrier<PIPE_V>();
    return (__ubuf__ float *)fp32Local.GetPhyAddr();
}
```

## 设计决策

- 采用显式 masked copy：把尾块语义写进代码，避免依赖 LocalTensor DataCopy 的隐含粒度；
- 输入和输出都替换：只修输入仍会在输出 local copy 重新污染；末轴 fp32 输出也复用同一 VF；
- 当前路线：`recommended_fastpath`。

## 预防

- 对局部 copy 做 `VL-1 / VL / VL+1` 三点探针；
- 当“整倍数全对、非整倍数全错”时，优先查尾 mask 与物理分配；
- 输入、输出、跨 TPosition 中间 copy 三处要一起审计。

## 验证信号

来源为一次 Ascend950 fp32 非末轴规约的局部复制修复：

- VL 整倍数场景 `maxdiff=2.24e-08/2.98e-08`，非整倍数场景为 `7.62e-01/1.69e+00/1.33e+00`（来源平台: 950；证据等级: tool_observed）；
- 输入/输出/末轴输出统一改 masked Reg copy 后，多组非 VL 场景降到 `4.47e-08/5.96e-08/7.45e-09`（来源平台: 950；证据等级: tool_observed）；
- 最终 pytest 58/58、cann-bench 20/20 通过（来源平台: 950；证据等级: tool_observed）。

## 失效边界

本结论来自 CANN 9.0.1 dav-3510 的特定 LocalTensor DataCopy 路径，不能外推为所有 DataCopy overload 的通用契约。A2/A3 未验证（未验证，推断可迁移）。

## 坏实践

- 只把 count 上取整后继续 DataCopy：会把无效元素当有效数据复制，不能替代 tail mask；
- 只修输入不修输出：结果会在 V→VECOUT 的 local copy 再次损坏。

## 误诊

曾将 fp32 ARA 错误归因于多 slab、多核或 TQue buffer 生命周期；定向长度探针证明 a1 改变不影响结果，真正分界是 a0 是否为 VL 整倍数。

<!-- cannbot:related:start -->
## 相关

- [AscCopy](../../apis/simd_api/c_api/vector_compute/asc_copy.md)（`exemplifies`）：AscCopy 与《fp32 UB 非 VL 拷贝须用带掩码 Reg》的实质衔接是：AscCopy 是 UB→UB 搬运；basic Copy、UB 搬运指南和 Reg Copy提供连续、高维/掩码入口，非整 VL 的 fp32 案例说明何时必须改用 masked Reg load/store。
- [AscUpdateMask](../../apis/simd_api/c_api/reg/reg_data_types/asc_update_mask.md)（`exemplifies`）：fp32 UB 非 VL 拷贝须用带掩码 Reg 与《AscUpdateMask》的实质衔接是：非 VL fp32 UB copy 的修复正文直接调用 UpdateMask、Reg Load/Store；所选 API 与 const/mask 故障卡约束同一尾块实现。
- [Copy](../../apis/simd_api/basic_api/memory_vector_compute/data_move/copy_ub_to_ub_continuous.md)（`exemplifies`）：Copy 与《fp32 UB 非 VL 拷贝须用带掩码 Reg》的实质衔接是：该 Copy 是 32B 对齐的 UB 连续搬运；DataCopy 对应入口、UB-UB 搬运指南、AscCopy 与非 VL 掩码故障共同说明通路、对齐和尾块边界。
- [Load](../../apis/simd_api/basic_api/reg_vector_compute/reg_data_load/load.md)（`exemplifies`）：fp32 UB 非 VL 拷贝须用带掩码 Reg 与《Load》的实质衔接是：非 VL fp32 UB copy 的修复正文直接调用 UpdateMask、Reg Load/Store；所选 API 与 const/mask 故障卡约束同一尾块实现。
- [Reg数据搬出](../../apis/simd_api/basic_api/reg_vector_compute/reg_data_store/reg_data_store.md)（`exemplifies`）：fp32 UB 非 VL 拷贝须用带掩码 Reg 与《Reg数据搬出》的实质衔接是：非 VL fp32 UB copy 的修复正文直接调用 UpdateMask、Reg Load/Store；所选 API 与 const/mask 故障卡约束同一尾块实现。
- [Store](../../apis/simd_api/basic_api/reg_vector_compute/reg_data_store/store.md)（`exemplifies`）：fp32 UB 非 VL 拷贝须用带掩码 Reg 与《Store》的实质衔接是：非 VL fp32 UB copy 的修复正文直接调用 UpdateMask、Reg Load/Store；所选 API 与 const/mask 故障卡约束同一尾块实现。
- [reg数据搬入](../../apis/simd_api/c_api/reg/reg_load/reg_load.md)（`exemplifies`）：fp32 UB 非 VL 拷贝须用带掩码 Reg 与《reg数据搬入》的实质衔接是：非 VL fp32 UB copy 的修复正文直接调用 UpdateMask、Reg Load/Store；所选 API 与 const/mask 故障卡约束同一尾块实现。
- [reg数据搬出](../../apis/simd_api/c_api/reg/reg_store/reg_store.md)（`exemplifies`）：焦点处理Reg 数据搬出中对齐、非对齐与带 mask store 的选择；fp32 UB 非 VL 拷贝须用带掩码 Reg正文说明“fp32 UB 局部 DataCopy 在非 vector-length 元素数上产生轴相关错误；使用 UpdateMask 的 Reg load/store 复制尾块”。候选把总览中的 store 选择落到 Basic Reg 对应接口或真实非 VL/交错 mask 故障。
- [Reg API int8 DIST_PACK_B32 交错零](reg_api_int8_dist_pack_b32.md)（`related`）：《Reg API int8 DIST_PACK_B32 交错零》说明Ascend950 Reg API 用 StoreAlign<int8_t, DIST_PACK_B32> 配 float 粒度 UpdateMask 做 fp32→int8 量化时输出每隔一字节插零；用小 shape debug 脚本打印 y[0] 与参考逐元素对照即可判别。；《fp32 UB 非 VL 拷贝须用带掩码 Reg》说明fp32 UB 局部 DataCopy 在非 vector-length 元素数上产生轴相关错误；使用 UpdateMask 的 Reg load/store 复制尾块。。二者在DIST_PACK_B32的存储分布与float到int8 Cast、UpdateMask和StoreAlign/Pack位宽必须一致，否则产生隔字节零上存在可执行的直接衔接。
- [Reg LoadAlign 不接受 const __ubuf__ 指针](../compilation/reg_loadalign_requires_nonconst_ubuf_pointer.md)（`same_topic`）：fp32 UB 非 VL 拷贝须用带掩码 Reg 与《Reg LoadAlign 不接受 const __ubuf__ 指针》的实质衔接是：非 VL fp32 UB copy 的修复正文直接调用 UpdateMask、Reg Load/Store；所选 API 与 const/mask 故障卡约束同一尾块实现。
- [UpdateMask 引用参数拒绝 const — 改用可修改左值](../compilation/updatemask_requires_mutable_uint32_lvalue.md)（`same_topic`）：fp32 UB 非 VL 拷贝须用带掩码 Reg 与《UpdateMask 引用参数拒绝 const — 改用可修改左值》的实质衔接是：非 VL fp32 UB copy 的修复正文直接调用 UpdateMask、Reg Load/Store；所选 API 与 const/mask 故障卡约束同一尾块实现。
<!-- cannbot:related:end -->
