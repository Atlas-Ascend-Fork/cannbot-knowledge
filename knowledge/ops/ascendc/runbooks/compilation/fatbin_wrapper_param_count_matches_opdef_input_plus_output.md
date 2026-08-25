---
type: "Runbook"
title: "advance_step in-place kernel FATBIN wrap"
description: "ascend950 FATBIN wrapper 按声明输入+输出数量生成调用，in-place kernel 缺输出参数致 CCEC 编译失败、.o 缺失。"
tags: ["task.debugging", "topic.implementation.operator_registration", "topic.compilation"]
status: stable
sources: []
created_at: "2026-08-18T03:30:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
aliases: ["add_kernel_sources", "MulAddDst"]
---

# advance_step in-place kernel FATBIN wrap

## 现象

在 Ascend950PR（CANN 9.0.0）上为 `advance_step` 算子补齐 `op_host/advance_step_def.cpp` 的 4 个 `Output(...)` 声明后，执行 `bash build.sh --pkg --soc=ascend950 --ops=advance_step -j16`，FATBIN 阶段直接失败。报错原文（来自 build 日志 tool 输出）：

```
[ERROR] ... Exception: An error occurred during compile phases of CompileStage.FATBIN,
msg is ld.lld: error: cannot open /workspace/cann/ops-nn/scripts/kernel/binary_script/
kernel_meta_AdvanceStep_52f00e7e9250348bc94f9de4b551b94c_high_performance/kernel_meta/
AdvanceStep_52f00e7e9250348bc94f9de4b551b94c_high_performance_1.o: No such file or directory
ld.lld: error: cannot open .../AdvanceStep_52f00e7e9250348bc94f9de4b551b94c_high_performance_2.o: No such file or directory
[ERROR] ... Op[AdvanceStep] of index[0] compile failed,
kernelName: AdvanceStep_52f00e7e9250348bc94f9de4b551b94c_high_performance.
```

即 `.o` 中间产物从未生成，ld.lld 在 FATBIN 链接阶段找不到它。进一步查 CCEC 编译日志（`build/binary/ascend950/bin/build_logs/advance_step_binary_high_performance.json_0.log`）发现根因：FATBIN 生成的 wrapper kernel 调用 `advance_step()` 时传了 14 个实参（8 input + 4 output + workspace + tiling），但 kernel 函数只声明 10 个形参（8 input + workspace + tiling，没有 output 参数）。

`advance_step` 是 in-place 算子（输出覆写输入 buffer），原 kernel 作者据此省略了 output 形参；但 ascend950 FATBIN wrapper 是按 `OpDef` 声明的 input+output 总数自动生成调用点的，不会为 in-place 语义省略 output 参数。

## 适用场景

- **工程形态**：构建（ops-nn `build.sh --pkg --soc=ascend950`，FATBIN/CCEC kernel 预编译）。
- **API 路径**：`op_kernel/<op>.cpp` 的 `extern "C" __global__ __aicore__ void <op>(GM_ADDR ...)` kernel 入口签名 + `op_host/<op>_def.cpp` 的 `OpDef` Output 声明。
- **验证过的平台与 CANN 版本**：Ascend950PR / CANN 9.0.0（`ascend950` AddConfig）。
- **适用粒度**：`operator_family`（所有在 ascend950 上走 FATBIN 预编译、且输出与输入共用 buffer 的 in-place 算子均适用）。
- **路线优先级**：`recommended_fastpath`（按 OpDef 声明补齐 output 形参是 build 系统的契约要求，非可选）。
- **不适用/未验证场景**：aclnn 两段式通路（不经 FATBIN wrapper 直接调 kernel）不在本卡范围；ascend910b / ascend910_93 的 FATBIN 行为本 trace 未验证（推断同构，标注"未验证，推断可迁移"于失效边界）。

## 根因

ascend950 FATBIN 阶段为 kernel 自动生成一个 wrapper，wrapper 的调用实参数 = `OpDef` 声明的 input 数 + output 数 + workspace + tiling。当 `OpDef` 声明了 4 个 Output、而 kernel 函数签名因 in-place 语义省略了 output 形参时，CCEC 编译 wrapper 时出现 `no matching function for call` / `candidate function not viable: requires 10 arguments, but 14 were provided`，CCEC 编译失败 → `.o` 不生成 → ld.lld 报 `cannot open ...o`。根因是**kernel 签名必须与 OpDef 声明的 input+output 总数对齐**，in-place 语义不能作为省略 output 形参的理由。

## 解决配方

### Before（原版 10 参数，无 output 形参）

`op_kernel/advance_step.cpp`（verbatim 取自 trace file_read 事件）：

```cpp
extern "C" __global__ __aicore__ void advance_step(GM_ADDR input_tokens, GM_ADDR sampled_token_ids,
                                                   GM_ADDR input_positions, GM_ADDR seq_lens, GM_ADDR slot_mapping,
                                                   GM_ADDR block_tables, GM_ADDR spec_token, GM_ADDR accepted_num,
                                                   GM_ADDR workspace, GM_ADDR tiling)
{
    GET_TILING_DATA(tilingData, tiling);

    GM_ADDR userWs = nullptr;

    if (TILING_KEY_IS(1)) {
        KernelAdvanceStep<int64_t> op;
        op.Init(input_tokens, sampled_token_ids, input_positions, seq_lens, slot_mapping, block_tables, userWs,
                &tilingData);
        op.Process();
    } else if (TILING_KEY_IS(2)) {
        TPipe Pipe;
        KernelAdvanceStepSpec<int64_t> op;
        op.Init(input_tokens, sampled_token_ids, input_positions, seq_lens, slot_mapping, block_tables, spec_token,
                accepted_num, userWs, &tilingData, &Pipe);
        op.Process();
    }
}
```

### After（14 参数，补 4 个 `GM_ADDR *_out` 形参）

`op_kernel/advance_step.cpp`（verbatim 取自 trace file_read 事件；output 形参插入在 `accepted_num` 与 `workspace` 之间）：

```cpp
extern "C" __global__ __aicore__ void advance_step(GM_ADDR input_tokens, GM_ADDR sampled_token_ids,
                                                   GM_ADDR input_positions, GM_ADDR seq_lens, GM_ADDR slot_mapping,
                                                   GM_ADDR block_tables, GM_ADDR spec_token, GM_ADDR accepted_num,
                                                   GM_ADDR input_tokens_out, GM_ADDR input_positions_out,
                                                   GM_ADDR seq_lens_out, GM_ADDR slot_mapping_out,
                                                   GM_ADDR workspace, GM_ADDR tiling)
{
    GET_TILING_DATA(tilingData, tiling);

    GM_ADDR userWs = nullptr;

    int64_t numSeqs = tilingData.numSeqs;
    auto* inTokens = (__gm__ int64_t*)input_tokens;
    auto* outTokens = (__gm__ int64_t*)input_tokens_out;
    auto* inPositions = (__gm__ int64_t*)input_positions;
    auto* outPositions = (__gm__ int64_t*)input_positions_out;
    auto* inSeqLens = (__gm__ int64_t*)seq_lens;
    auto* outSeqLens = (__gm__ int64_t*)seq_lens_out;
    auto* inSlotMapping = (__gm__ int64_t*)slot_mapping;
    auto* outSlotMapping = (__gm__ int64_t*)slot_mapping_out;
    for (int64_t i = GetBlockIdx(); i < numSeqs; i += GetBlockNum()) {
        outTokens[i] = inTokens[i];
        outPositions[i] = inPositions[i];
        outSeqLens[i] = inSeqLens[i];
        outSlotMapping[i] = inSlotMapping[i];
    }
    PipeBarrier<PIPE_ALL>();

    if (TILING_KEY_IS(1)) {
        KernelAdvanceStep<int64_t> op;
        op.Init(input_tokens_out, sampled_token_ids, input_positions_out, seq_lens_out, slot_mapping_out,
                block_tables, userWs, &tilingData);
        op.Process();
    } else if (TILING_KEY_IS(2)) {
        TPipe Pipe;
        KernelAdvanceStepSpec<int64_t> op;
        op.Init(input_tokens_out, sampled_token_ids, input_positions_out, seq_lens_out, slot_mapping_out,
                block_tables, spec_token, accepted_num, userWs, &tilingData, &Pipe);
        op.Process();
    }
}
```

注意 after 版本同时把 `op.Init` 的前四个 buffer 参数从 input 切换为 `*_out`（见 DRAFT-build-03 的 buffer 别名根因），这是同一文件的另一处独立修复；本卡只覆盖签名参数对齐这一根因。

## 验证信号

- 补齐 4 个 output 形参后，`build.sh --pkg --soc=ascend950` FATBIN 阶段通过、CCEC 生成 `.o`，`[SUCCESS] Build package success!`（来源平台：950；证据等级: tool_observed）。
- custom module 安装返回 `SUCCESS`（来源平台：950；证据等级: tool_observed）。

## 失效边界

- ascend910b / ascend910_93 的 FATBIN wrapper 行为：未验证，推断可迁移（同一 build 系统按 OpDef 生成 wrapper 的机制应一致，但本 trace 仅在 ascend950 实测）。
- aclnn 两段式通路不经 FATBIN wrapper，本卡不适用。
- 若 OpDef 的 Output 声明数与 kernel output 形参数再次不一致（例如后续新增 output），会以同样的 `requires N arguments, but M were provided` 复现。

<!-- cannbot:related:start -->
## 相关

- [MulAddDst](../../apis/simd_api/basic_api/memory_vector_compute/composite_compute/mul_add_dst.md)（`exemplifies`）：本卡的 in-place 输出复用语义可由 MulAddDst 这类显式 dst 累加接口对照，但 wrapper 形参数仍必须保留声明的 output。
- [ld.lld cannot open _mix_aiv 报错判别](ld_lld_cannot_open_mix_aiv.md)（`related`）：《advance_step in-place kernel FATBIN wrap》明确“ascend950 FATBIN wrapper 按声明输入+输出数量生成调用，in-place kernel 缺输出参数致 CCEC 编译失败、.o 缺失。”；它与《ld.lld cannot open _mix_aiv 报错判别》的“cube/vec 双段编译下 ld.lld 报 cannot open _mix_aiv_*.o 实为 AIV 编译阶段失败、.o 未生成，需过滤链接噪声定位真实 AIV 编译错误。”在实际调用参数、数据流或结果校验上直接衔接。
- [optional input 未连接触发 InferShape 失败](optional_input_infershape.md)（`related`）：optional input 卡说明 OpDef 声明会改变框架生成的输入上下文；与本卡共同强调 wrapper/上下文严格服从 OpDef 参数契约。
- [qgmm_mx FP4 fatbin 缺失致 107000](qgmm_mx_fp4_fatbin_107000.md)（`related`）：QGMM 案例同样通过 FATBIN/CCEC 日志追到中间 .o 未生成，可复用“先查真正编译错误而非 ld.lld 噪声”的诊断顺序。
<!-- cannbot:related:end -->
