---
type: "Runbook"
title: "507035 C 超 per_buf_elems 致 Phase1 UB 越界"
description: "Ascend950 上 Phase 1 对 (C,) 张量单发 DataCopyPad 写入 per_buf_bytes 容量的 UB buffer，当 C > per_buf_elems 时越界触发 507035；须按 per_buf_elems 分 chunk 循环。"
tags: ["task.debugging", "topic.data_movement.data_copy", "topic.memory"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
aliases: ["UB_overflow", "chunk_loop"]
---

# 507035 C 超 per_buf_elems 致 Phase1 UB 越界

## 现象

Ascend950（dav-3510，arch 3510，CANN 9.0.0-beta.2）上 `bn_training_update_custom` 黑盒全量执行：正向 418 条、负向 6 条。70 条 FAIL 高度同质——全部 `x_shape=(22, 19686, 1, 1, 4)`（5D fp16，通道轴 C=19686），5 路输出全部 `NO_OUTPUT`（算子未产出任何输出）。其余 348 条 PASS 的 C 均 `<= 12696`。C++ `tests/aclnn` 复现用例 `case_repro_large_C_19686_fp16` 报 `[ACL err] 507035 at aclrtSynchronizeStream`。编译过、无 workspace 越界（workspace 已修），崩溃发生在 kernel Phase 1 对 `(C,)` 张量的 `DataCopyPad`/Vector 操作。

## 适用场景

- **工程形态**：kernel 直调（AscendC regbase broadcast），Phase 1 对 1D `(C,)` 张量做 GM→UB 搬运 + Vector 链 + UB→GM 回写，UB buffer 按 `per_buf_bytes = (ub_size/kPhysNodes) & ~31` 切分。
- **API 路径**：`AscendC::DataCopyPad(buf, gmIn, ep1, padIn)`（GM→UB，`ep1.blockLen = C*sizeof(float)`）；`AscendC::Muls/Mul/Sub/Sqrt/Div/Add`（count=C）；修复为 `for (off=0; off<C; off+=per_buf_elems)` 分 chunk、count 用 `n=min(C-off, per_buf_elems)`。
- **验证过的平台与 CANN 版本**：Ascend950 / dav-3510 / CANN 9.0.0-beta.2（`ub_size=253952`，`kPhysNodes=5`，`per_buf_bytes=50784`，`per_buf_elems=12696`）。
- **适用粒度**：`operator_family`——所有用 `TBuf` 切 `per_buf_bytes` 装 `(C,)` 张量、C 可超 `per_buf_elems` 的 broadcast/stateful 算子。
- **路线优先级**：`recommended_fastpath`——凡 `(C,)` 段 C 无上界保证，Phase 1 必须按 `per_buf_elems` 分 chunk 循环，仅 core 0 执行（结果落 GM 由 SyncAll 共享）。
- **不适用或未验证场景**：C 有静态上界且 `<= per_buf_elems` 时不需分 chunk；`TQue` 流水模式（本卡用 `TBuf`）的切分策略不同，未验证。

## 根因

Phase 1 对每个 `(C,)` 张量单发调用 `AscendC::DataCopyPad(buf[0].Get<float>(), gmIn[0], ep1, padIn)`，其中 `ep1.blockLen = C * sizeof(float)`，但 `buf[0]` 仅 `per_buf_bytes` 字节。`per_buf_bytes = (ub_size / kPhysNodes) & ~31 = (253952 / 5) & ~31 = 50784` 字节 = 12696 个 fp32。当 `C = 19686 > 12696`，`DataCopyPad` 写 `19686*4 = 78744` 字节到 `50784` 字节 buffer → UB 越界 → 507035 向量核异常 → kernel 立即崩在 Phase 1（处理 `mean` 之前），5 路输出全 `NO_OUTPUT`。`mean=+inf` 是该批黑盒用例的特征但不是触发根因。

机制链（算式）：`per_buf_bytes = (ub_size / kPhysNodes) & ~31 = (253952/5) & ~31 = 50784 & ~31 = 50784`；`per_buf_elems = 50784 / 4 = 12696`；`C = 19686 > 12696` → 越界 `19686 - 12696 = 6990` 个 fp32（27960 字节）。

## 解决配方

把 Phase 1（Compute + Store）整体包到 `if (GetBlockIdx() == 0)` 内、按 `per_buf_elems` 分 chunk 循环：每 chunk 取 `n = min(C - off, per_buf_elems)`，`ep1c.blockLen = n*sizeof(float)`，GM 读写用 `gmIn[i][off]` / `gmOut[j][off]` 偏移，Vector count 用 `n`。Phase 2 与 SyncAll 不变。

before（Phase 1 单发，C 直传，`ep1.blockLen = C*sizeof(float)`，越界）：

```cpp
// ===== Phase 1 Compute (all cores, PipeBarrier sync) =====
AscendC::DataCopyPad(buf[0].Get<float>(), gmIn[0], ep1, padIn);
AscendC::PipeBarrier<PIPE_ALL>();
AscendC::Muls(buf[1].Get<float>(), buf[0].Get<float>(), td->num_rec, C);

AscendC::PipeBarrier<PIPE_ALL>();
AscendC::DataCopyPad(buf[0].Get<float>(), gmIn[1], ep1, padIn);
AscendC::PipeBarrier<PIPE_ALL>();
AscendC::Muls(buf[2].Get<float>(), buf[0].Get<float>(), td->num_rec, C);

AscendC::Mul(buf[0].Get<float>(), buf[1].Get<float>(), buf[1].Get<float>(), C);
AscendC::Sub(buf[0].Get<float>(), buf[2].Get<float>(), buf[0].Get<float>(), C);
AscendC::Maxs(buf[0].Get<float>(), buf[0].Get<float>(), 0.0f, C);
AscendC::Adds(buf[2].Get<float>(), buf[0].Get<float>(), td->epsilon, C);
static constexpr AscendC::SqrtConfig hpSqrt = {AscendC::SqrtAlgo::PRECISION_0ULP_FTZ_FALSE};
AscendC::Sqrt<float, hpSqrt>(buf[2].Get<float>(), buf[2].Get<float>(), static_cast<int32_t>(C));

AscendC::PipeBarrier<PIPE_ALL>();
AscendC::DataCopyPad(buf[3].Get<float>(), gmIn[2], ep1, padIn);
AscendC::PipeBarrier<PIPE_ALL>();
static constexpr AscendC::DivConfig hpDiv = {AscendC::DivAlgo::PRECISION_0ULP_FTZ_FALSE};
AscendC::Div<float, hpDiv>(buf[3].Get<float>(), buf[3].Get<float>(), buf[2].Get<float>(), static_cast<int32_t>(C));

AscendC::Mul(buf[2].Get<float>(), buf[3].Get<float>(), buf[1].Get<float>(), C);

AscendC::PipeBarrier<PIPE_ALL>();
AscendC::DataCopyPad(buf[4].Get<float>(), gmIn[3], ep1, padIn);
AscendC::PipeBarrier<PIPE_ALL>();
AscendC::Sub(buf[4].Get<float>(), buf[4].Get<float>(), buf[2].Get<float>(), C);

AscendC::Muls(buf[2].Get<float>(), buf[0].Get<float>(), td->batch_var_scalar, C);

// ===== Phase 1 Store (core 0 only, PipeBarrier sync) =====
if (AscendC::GetBlockIdx() == 0) {
    AscendC::PipeBarrier<PIPE_ALL>();
    AscendC::DataCopyPad(gmOut[3], buf[0].Get<float>(), ep1); // batch_variance
    AscendC::DataCopyPad(gmOut[2], buf[1].Get<float>(), ep1); // batch_mean
    AscendC::DataCopyPad(gmWs[0], buf[3].Get<float>(), ep1);  // ws multiplier
    AscendC::DataCopyPad(gmWs[1], buf[4].Get<float>(), ep1);  // ws addend

    AscendC::PipeBarrier<PIPE_ALL>();
    AscendC::Muls(buf[0].Get<float>(), buf[1].Get<float>(), td->factor, C);
    AscendC::PipeBarrier<PIPE_ALL>();
    AscendC::DataCopyPad(buf[1].Get<float>(), gmIn[4], ep1, padIn);
    AscendC::PipeBarrier<PIPE_ALL>();
    AscendC::Muls(buf[1].Get<float>(), buf[1].Get<float>(), td->factor_reverse, C);
    AscendC::Add(buf[0].Get<float>(), buf[0].Get<float>(), buf[1].Get<float>(), C);
    AscendC::PipeBarrier<PIPE_ALL>();
    AscendC::DataCopyPad(gmOut[0], buf[0].Get<float>(), ep1); // mean_out

    AscendC::PipeBarrier<PIPE_ALL>();
    AscendC::Muls(buf[0].Get<float>(), buf[2].Get<float>(), td->factor, C);
    AscendC::PipeBarrier<PIPE_ALL>();
    AscendC::DataCopyPad(buf[1].Get<float>(), gmIn[5], ep1, padIn);
    AscendC::PipeBarrier<PIPE_ALL>();
    AscendC::Muls(buf[1].Get<float>(), buf[1].Get<float>(), td->factor_reverse, C);
    AscendC::Add(buf[0].Get<float>(), buf[0].Get<float>(), buf[1].Get<float>(), C);
    AscendC::PipeBarrier<PIPE_ALL>();
    AscendC::DataCopyPad(gmOut[1], buf[0].Get<float>(), ep1); // variance_out
}
```

after（Phase 1 按 `per_buf_elems` 分 chunk、仅 core 0）：

```cpp
// ===== Phase 1 (core 0 only, tiled over C in chunks) =====
// Phase 1 processes (C,) tensors. When C > per_buf_elems
// (= per_buf_bytes / sizeof(float)), the per-UB-buffer cannot hold all C
// elements at once. Tile over C: each chunk loads/stores a slice.
// Only core 0 runs Phase 1 (results -> GM, visible to all cores via SyncAll below).
static constexpr AscendC::SqrtConfig hpSqrt = {AscendC::SqrtAlgo::PRECISION_0ULP_FTZ_FALSE};
static constexpr AscendC::DivConfig hpDiv = {AscendC::DivAlgo::PRECISION_0ULP_FTZ_FALSE};
int64_t per_buf_elems = td->per_buf_bytes / (int64_t)sizeof(float);
AscendC::DataCopyPadExtParams<float> padIn;
AscendC::DataCopyExtParams ep1c;
ep1c.blockCount = 1; ep1c.srcStride = 0; ep1c.dstStride = 0;

if (AscendC::GetBlockIdx() == 0) {
    for (int64_t off = 0; off < C; off += per_buf_elems) {
        int64_t n = (C - off < per_buf_elems) ? (C - off) : per_buf_elems;
        ep1c.blockLen = static_cast<uint32_t>(n * sizeof(float));
        int32_t ni = static_cast<int32_t>(n);

        // --- Phase 1 Compute (per chunk) ---
        AscendC::DataCopyPad(buf[0].Get<float>(), gmIn[0][off], ep1c, padIn);
        AscendC::PipeBarrier<PIPE_ALL>();
        AscendC::Muls(buf[1].Get<float>(), buf[0].Get<float>(), td->num_rec, ni);

        AscendC::PipeBarrier<PIPE_ALL>();
        AscendC::DataCopyPad(buf[0].Get<float>(), gmIn[1][off], ep1c, padIn);
        AscendC::PipeBarrier<PIPE_ALL>();
        AscendC::Muls(buf[2].Get<float>(), buf[0].Get<float>(), td->num_rec, ni);

        AscendC::Mul(buf[0].Get<float>(), buf[1].Get<float>(), buf[1].Get<float>(), ni);
        AscendC::Sub(buf[0].Get<float>(), buf[2].Get<float>(), buf[0].Get<float>(), ni);
        AscendC::Maxs(buf[0].Get<float>(), buf[0].Get<float>(), 0.0f, ni);
        AscendC::Adds(buf[2].Get<float>(), buf[0].Get<float>(), td->epsilon, ni);
        AscendC::Sqrt<float, hpSqrt>(buf[2].Get<float>(), buf[2].Get<float>(), ni);

        AscendC::PipeBarrier<PIPE_ALL>();
        AscendC::DataCopyPad(buf[3].Get<float>(), gmIn[2][off], ep1c, padIn);
        AscendC::PipeBarrier<PIPE_ALL>();
        AscendC::Div<float, hpDiv>(buf[3].Get<float>(), buf[3].Get<float>(), buf[2].Get<float>(), ni);

        AscendC::Mul(buf[2].Get<float>(), buf[3].Get<float>(), buf[1].Get<float>(), ni);

        AscendC::PipeBarrier<PIPE_ALL>();
        AscendC::DataCopyPad(buf[4].Get<float>(), gmIn[3][off], ep1c, padIn);
        AscendC::PipeBarrier<PIPE_ALL>();
        AscendC::Sub(buf[4].Get<float>(), buf[4].Get<float>(), buf[2].Get<float>(), ni);

        AscendC::Muls(buf[2].Get<float>(), buf[0].Get<float>(), td->batch_var_scalar, ni);

        // --- Phase 1 Store (per chunk) ---
        AscendC::PipeBarrier<PIPE_ALL>();
        AscendC::DataCopyPad(gmOut[3][off], buf[0].Get<float>(), ep1c); // batch_variance
        AscendC::DataCopyPad(gmOut[2][off], buf[1].Get<float>(), ep1c); // batch_mean
        AscendC::DataCopyPad(gmWs[0][off], buf[3].Get<float>(), ep1c);  // ws multiplier
        AscendC::DataCopyPad(gmWs[1][off], buf[4].Get<float>(), ep1c);  // ws addend

        AscendC::PipeBarrier<PIPE_ALL>();
        AscendC::Muls(buf[0].Get<float>(), buf[1].Get<float>(), td->factor, ni);
        AscendC::PipeBarrier<PIPE_ALL>();
        AscendC::DataCopyPad(buf[1].Get<float>(), gmIn[4][off], ep1c, padIn);
        AscendC::PipeBarrier<PIPE_ALL>();
        AscendC::Muls(buf[1].Get<float>(), buf[1].Get<float>(), td->factor_reverse, ni);
        AscendC::Add(buf[0].Get<float>(), buf[0].Get<float>(), buf[1].Get<float>(), ni);
        AscendC::PipeBarrier<PIPE_ALL>();
        AscendC::DataCopyPad(gmOut[0][off], buf[0].Get<float>(), ep1c); // mean_out

        AscendC::PipeBarrier<PIPE_ALL>();
        AscendC::Muls(buf[0].Get<float>(), buf[2].Get<float>(), td->factor, ni);
        AscendC::PipeBarrier<PIPE_ALL>();
        AscendC::DataCopyPad(buf[1].Get<float>(), gmIn[5][off], ep1c, padIn);
        AscendC::PipeBarrier<PIPE_ALL>();
        AscendC::Muls(buf[1].Get<float>(), buf[1].Get<float>(), td->factor_reverse, ni);
        AscendC::Add(buf[0].Get<float>(), buf[0].Get<float>(), buf[1].Get<float>(), ni);
        AscendC::PipeBarrier<PIPE_ALL>();
        AscendC::DataCopyPad(gmOut[1][off], buf[0].Get<float>(), ep1c); // variance_out
    }
}
```

GM 偏移用 `GlobalTensor::operator[]`：`gmIn[0][off]` 返回 `__gm__ float&`，可作 `DataCopyPad` 的 GM 源/目的（与 Phase 2 NDDMA `gmX[o]` 同模式）。`hpSqrt`/`hpDiv` 移到循环外 `static constexpr`。`SyncAll` 屏障不变（Phase 1 结果落 GM，Phase 2 全核读）。

## 验证信号

本卡验证来源：bn_training_update_custom 黑盒失败用例修复会话（Ascend950 / CANN 9.0.0-beta.2）。

- 黑盒失败分布：70 条 FAIL 全部 C=19686，348 条 PASS 全部 C ≤ 12696——按 C 与 per_buf_elems 关系精确分流（来源平台：Ascend950；证据等级: tool_observed）
- Phase 1 before/after 完整函数级代码——逐字 trace 事件（来源平台：Ascend950；证据等级: tool_observed）

## 预防

- 凡 `(C,)` 段 C 无静态上界，Phase 1 一律按 `per_buf_elems` 分 chunk 循环，`ep1c.blockLen = n*sizeof(float)`、Vector count 用 `n`、GM 用 `[]offset`。
- tiling 设 `per_buf_bytes` 字段供 kernel 查询，kernel 用 `td->per_buf_bytes / sizeof(float)` 算 chunk 大小，不硬编码 12696。
- review 时查 Phase 1 是否有 `blockLen = C*sizeof(float)` 且 C 无上界——有则标风险。

## 失效边界

- 仅 Ascend950（arch 3510，`ub_size=253952`）实测；其他 dav 平台 `ub_size`/`kPhysNodes` 不同，`per_buf_elems` 值不同，须按目标平台算——未验证，推断可迁移。
- `TQue` 流水模式的切分策略不同，本卡（`TBuf` 单发 chunk 循环）不覆盖。

## 坏实践

- 在黑盒用例里把 C=19686 的用例 skip/剔除（反投机取巧——掩盖 UB 容量 bug）。
- 缩小 BlockDim 到 1 绕过多核（runtime-debug skill 明令禁止；性能严重退化且不修根因）。
- 把 `per_buf_bytes` 硬编码成 12696（迁移到其他 `ub_size` 平台即失效）。

## 误诊

- 初判怀疑 `mean=+inf`（running state 输入）触发 VEC_ERROR——但 Phase 1 在处理 `mean` 之前就崩，`mean=+inf` 是该批用例的特征不是根因。
- 与 build 卡 507035（workspace RESERVED_WORKSPACE）同错误码但不同根因：本卡是 kernel 侧 UB 越界（Phase 1 容量），那张是 host 侧 GM workspace 越界（workspace 大小）。两卡同 507035 但代码路径与修复层不同，各一卡。

<!-- cannbot:related:start -->
## 相关

- [507035 — Host 按逻辑行宽预算导致 UB 溢出](ub_budget_uses_aligned_physical_width_507035.md)（`same_topic`）：焦点处理Phase1 中 C 超出 per_buf_elems 导致 UB 地址越界的预算故障；507035 — Host 按逻辑行宽预算导致 UB 溢出正文说明“Host tiling 用逻辑 D 估算 UB，而 Device 按对齐 stride 分配；统一预算公式后 20 个实测用例通过”。候选与焦点共享 UB 容量/slot 预算机制，能直接修正切分因子、物理宽度或双缓冲计数。
- [507035 — 三队列 float32 tile 超 UB](507035_float32_tile_ub.md)（`same_topic`）：焦点处理Phase1 中 C 超出 per_buf_elems 导致 UB 地址越界的预算故障；507035 — 三队列 float32 tile 超 UB正文说明“Ascend950/dav-3510 上多 TQue+双缓冲+大固定 tile 的 float32 Reg kernel 运行期抛 ACL 507035；用同环境对照算子+缩 tile 探针二分定位为每核 UB 超额，而非 D2H 拷贝故障”。候选与焦点共享 UB 容量/slot 预算机制，能直接修正切分因子、物理宽度或双缓冲计数。
- [ACL 507035 — 完整 a0 统计缓冲超过 UB](ub_slices_reduction_axis_scratch_buffers_507035.md)（`same_topic`）：焦点处理Phase1 中 C 超出 per_buf_elems 导致 UB 地址越界的预算故障；ACL 507035 — 完整 a0 统计缓冲超过 UB正文说明“ARA 按完整尾轴乘积分配 fp32 max/sum 缓冲会在大 a0 时超过 UB；须对 a0 再切 tile 并逐 tile 完成三趟归约”。候选与焦点共享 UB 容量/slot 预算机制，能直接修正切分因子、物理宽度或双缓冲计数。
- [ACLNN 507015 — tiling UB 漏算 kIdxBuf 下溢](aclnn_507015_tiling_ub_kidxbuf.md)（`same_topic`）：焦点处理Phase1 中 C 超出 per_buf_elems 导致 UB 地址越界的预算故障；ACLNN 507015 — tiling UB 漏算 kIdxBuf 下溢正文说明“cloud_sparse_inverse_conv3d_with_matmul ST 触发 507015 device error type 3；根因为 tiling 侧 CalcUbMaxTaskNum 未镜像 kernel 侧 kIdxBuf_/BLOCK_SIZE 且 ui”。候选与焦点共享 UB 容量/slot 预算机制，能直接修正切分因子、物理宽度或双缓冲计数。
- [FP16 double-buffer UB 预算漏乘 2 致 VEC_ERROR](fp16_double_buffer_ub_budget_queue_vs_tbuf_multiplier.md)（`same_topic`）：焦点处理Phase1 中 C 超出 per_buf_elems 导致 UB 地址越界的预算故障；FP16 double-buffer UB 预算漏乘 2 致 VEC_ERROR正文说明“FusedBiasLeakyRelu arch35 tiling 在 FP16+double buffer 路径计算 ubFactor 时，bytesPerElem 未对 Queue 部分乘以 DOUBLE_BUFFER_MULTIPLIER，导致 ubFactor 高估、UB ”。候选与焦点共享 UB 容量/slot 预算机制，能直接修正切分因子、物理宽度或双缓冲计数。
- [FindSplitAxis 误传 total_slots 致 slot 翻倍](../precision/findsplitaxis_total_slots_slot.md)（`same_topic`）：焦点处理Phase1 中 C 超出 per_buf_elems 导致 UB 地址越界的预算故障；FindSplitAxis 误传 total_slots 致 slot 翻倍正文说明“Broadcast 类算子 tiling 把 total_slots(=kPhysNodes*2) 当作 phys_nodes 传入 FindSplitAxis，函数内部再乘 2，per_buf_bytes 被腰斩一半、tile 循环翻倍，TilingData 写出值与内部切分粒”。候选与焦点共享 UB 容量/slot 预算机制，能直接修正切分因子、物理宽度或双缓冲计数。
- [Reduce work buf 额外占 UB 致 507035](reduce_work_buf_ub_507035.md)（`same_topic`）：焦点处理Phase1 中 C 超出 per_buf_elems 导致 UB 地址越界的预算故障；Reduce work buf 额外占 UB 致 507035正文说明“Ascend950 上为 ReduceSum/ReduceMax 单独开 fp32 work buffer，N>=14336 时 UB 总占用超限，kernel 启动后访问越界 UB 区触发 device error type 3 error code 507035。判别=缩小复”。候选与焦点共享 UB 容量/slot 预算机制，能直接修正切分因子、物理宽度或双缓冲计数。
- [count超4096仅前4288元算正确的精度阈值](../precision/count_4096_4288.md)（`same_topic`）：焦点处理Phase1 中 C 超出 per_buf_elems 导致 UB 地址越界的预算故障；count超4096仅前4288元算正确的精度阈值正文说明“逐元素融合算子在 Ascend950 上 count>4096 时仅前 4288 个元素正确、正确率×count 恒等于 4288 的精度阈值诊断判别”。候选与焦点共享 UB 容量/slot 预算机制，能直接修正切分因子、物理宽度或双缓冲计数。
- [postReduceUbSize 不足致 Phase2 读破坏](euclidean_norm_group_post_reduce_ub_size_phase2_chunk.md)（`same_topic`）：焦点处理Phase1 中 C 超出 per_buf_elems 导致 UB 地址越界的预算故障；postReduceUbSize 不足致 Phase2 读破坏正文说明“branch-3/4 group 路径 postReduceUbSize 只装每 chunk A 大小，Phase 2 把 aTotal 拆多 chunk 且 srcStride 非零，blockLen 非 32B 对齐时 workspace 读破坏；修复 enlarge pos”。候选与焦点共享 UB 容量/slot 预算机制，能直接修正切分因子、物理宽度或双缓冲计数。
<!-- cannbot:related:end -->
