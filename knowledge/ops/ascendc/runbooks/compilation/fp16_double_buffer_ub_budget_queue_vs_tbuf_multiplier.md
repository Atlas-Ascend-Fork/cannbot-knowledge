---
type: "Runbook"
title: "FP16 double-buffer UB 预算漏乘 2 致 VEC_ERROR"
description: "FusedBiasLeakyRelu arch35 tiling 在 FP16+double buffer 路径计算 ubFactor 时，bytesPerElem 未对 Queue 部分乘以 DOUBLE_BUFFER_MULTIPLIER，导致 ubFactor 高估、UB 溢出 ~29%，大 shape fp16 用例触发 VEC_ERROR。"
tags: ["task.debugging", "topic.implementation.tiling", "topic.memory"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# FP16 double-buffer UB 预算漏乘 2 致 VEC_ERROR

## 现象

对 ops-nn 仓库的 `FusedBiasLeakyRelu`（路径 `ops-nn/activation/fused_bias_leaky_relu`）跑 TTK v2 全量 271 用例（`ops-test-kit/fused_bias_leaky_relu/fused_bias_leaky_relu_kernel_cases_v2.csv`），在 Ascend950PR + CANN 9.0.0 下，3 个 FP16 大 shape 用例全部失败：

- `fblr_perf_fp16_18M`，shape (6000, 3000)=18M，tiling_key=1（double buffer）
- `fblr_perf_fp16_33M`，shape (2048, 2048, 8)=33M，tiling_key=1
- `fblr_edge_large_1d_fp16_float16`，shape (1000000,)=1M，tiling_key=1

三者的 `dyn_precision` 都是 `NO_OUTPUT`，`metrics: {'dyn': {}, 'cst': {}, 'bin': {}}`，TTK 的 `ttk-error.log` 显式记录 `VEC_ERROR encountered`（来源 `rts_interface.py:832`）。这 3 个用例在 2026-08-01 的旧安装下全部 `PASS`，重新编译安装 ops-nn 算子后开始失败。FP32 路径与小 shape（tiling_key=0，single buffer）FP16 用例不受影响。

HBM 充足（131072 MB 仅用几 GB，`rtMalloc` 均成功），排除 OOM；多卡健康状态排查后，在健康 device 上仍复现，确认是算子 tiling 代码问题。

## 适用场景

- **工程形态**：ops-nn 算子仓开发（ops-registry-invoke 体系），TTK（ops-test-kit）kernel 模式精度/执行验证。
- **API 路径**：`op_host/arch35/fused_bias_leaky_relu_tiling_arch35.cpp` 的 `FusedBiasLeakyReluTilingFunc`；kernel 侧 FP16 走 Cast 通路（x/bias cast 到 fp32 计算、再 cast 回 fp16），Queue 用 `BUFFER_NUM=2` double buffer。
- **验证过的平台与 CANN 版本**：Ascend950PR（ascend950），CANN 9.0.0（`/usr/local/Ascend/cann-9.0.0`）。仅 950 实测。
- **适用粒度**：`operator_family`——同一 tiling 范式（Queue+Cast 混合 UB 预算、Queue 受 double buffer 翻倍而 TBuf 单份）的 FP16 element-wise 算子。
- **路线优先级**：`recommended_fastpath`——对任何「Queue 走 double buffer、同时存在非 Queue 的 TBuf/cast 单份 buffer」的 tiling，UB 预算必须按 Queue 与 TBuf 分别计倍数。
- **不适用或未验证场景**：FP32 路径（无 cast buffer，受影响不同，本卡未覆盖其正确性证明）；a2/a3 平台未验证，推断可迁移（见 `## 失效边界`）；single buffer（tiling_key=0）路径不受本 bug 影响。

## 根因

`FusedBiasLeakyReluTilingFunc` 在 FP16 分支按下式估每元素 UB 占用：

```
bytesPerElem = TENSOR_NUM * TYPE_SIZE_FP16 + FP16_CAST_BUF_NUM * TYPE_SIZE_FP32
             = 3 * 2 + 3 * 4 = 18 bytes/elem
ubFactor     = FloorAlign(FloorDiv(ubSize, bytesPerElem), ubBlockSize)
             = FloorAlign(262144 / 18, ...) ≈ 14096
```

但 kernel 在 double buffer 模式下，3 个 Queue（x/bias/y 的 GM↔UB 搬运 buffer）各占 **2 份**（`BUFFER_NUM=2`），而 3 个 Cast buffer（`xFp32/biasFp32/yFp32`，TBuf）是单份。真实每元素占用：

```
bytesPerElem_real = 3 queues * 2 (double buffer) * TYPE_SIZE_FP16
                  + 3 cast bufs * 1 * TYPE_SIZE_FP32
                  = 3*2*2 + 3*4 = 24 bytes/elem
ubFactor_real     = FloorAlign(262144 / 24, ...) ≈ 10912
```

按错误的 18 bytes/elem 算出 `ubFactor≈14096`，远大于正确的 10912；UB 实际需求 `14096 * 24 = 338304 bytes` 超过 UB 容量 `262144 bytes`，溢出 `76160 bytes (29.1%)`，运行时 Vector 核执行越界触发 `VEC_ERROR`。

机制链点破：FP16 路径的 UB 预算里，**Queue 部分受 double buffer 翻倍、Cast(TBuf) 部分不翻倍**——这两类 buffer 的倍数不同，必须分别按各自倍数相加，不能把 Queue 与 TBuf 混在一起按单一倍数计。

## 解决配方

修复 `op_host/arch35/fused_bias_leaky_relu_tiling_arch35.cpp` 的 UB 预算计算。before/after 均为 `FusedBiasLeakyReluTilingFunc` 内 typeSize/ubBlockSize/blockFactor/useDoubleBuffer 之后的 UB 预算段（函数级 verbatim，取自 trace 的 file_read 事件）。

before（修复前，trace event 713/714 的 file_read 原文）：

```cpp
    int64_t typeSize = (dataType == ge::DT_FLOAT16) ? TYPE_SIZE_FP16 : TYPE_SIZE_FP32;
    int64_t ubBlockSize = BLOCK_ALIGN_BYTES / typeSize;

    int64_t blockFactor = CeilAlign(CeilDiv(totalNum, coreNum), ubBlockSize);
    int64_t usedCoreNum = CeilDiv(totalNum, blockFactor);

    // FP16 path needs extra Cast buffers (xFp32, biasFp32, yFp32) at FP32 size
    bool isFp16 = (dataType == ge::DT_FLOAT16);
    int64_t extraBuf = isFp16 ? FP16_CAST_BUF_NUM : 0;
    int64_t totalBufNum = TENSOR_NUM + extraBuf;

    int64_t loopCountIfDouble = CeilDiv(blockFactor,
        static_cast<int64_t>(ubSize) / typeSize / (totalBufNum * DOUBLE_BUFFER_MULTIPLIER));
    uint64_t useDoubleBuffer = (loopCountIfDouble >= DOUBLE_BUFFER_THRESHOLD) ? 1 : 0;

    // UB budget: TENSOR_NUM buffers at typeSize + extraBuf buffers at FP32 size
    int64_t bufferCount = totalBufNum * (useDoubleBuffer ? DOUBLE_BUFFER_MULTIPLIER : 1);
    int64_t ubFactor;
    if (isFp16) {
        // FP16: 3 queues × sizeof(half) + 3 cast bufs × sizeof(float) = 3×2 + 3×4 = 18 bytes per element
        int64_t bytesPerElem = TENSOR_NUM * TYPE_SIZE_FP16 + FP16_CAST_BUF_NUM * TYPE_SIZE_FP32;
        ubFactor = FloorAlign(FloorDiv(static_cast<int64_t>(ubSize), bytesPerElem), ubBlockSize);
    } else {
        ubFactor = FloorAlign(FloorDiv(static_cast<int64_t>(ubSize) / typeSize, bufferCount), ubBlockSize);
    }
```

after（修复后，trace event 959 的 file_read 原文）：

```cpp
    int64_t typeSize = (dataType == ge::DT_FLOAT16) ? TYPE_SIZE_FP16 : TYPE_SIZE_FP32;
    int64_t ubBlockSize = BLOCK_ALIGN_BYTES / typeSize;

    int64_t blockFactor = CeilAlign(CeilDiv(totalNum, coreNum), ubBlockSize);
    int64_t usedCoreNum = CeilDiv(totalNum, blockFactor);

    // FP16 path needs extra Cast buffers (xFp32, biasFp32, yFp32) at FP32 size
    bool isFp16 = (dataType == ge::DT_FLOAT16);
    int64_t extraBuf = isFp16 ? FP16_CAST_BUF_NUM : 0;
    int64_t totalBufNum = TENSOR_NUM + extraBuf;

    int64_t loopCountIfDouble = CeilDiv(blockFactor,
        static_cast<int64_t>(ubSize) / typeSize / (totalBufNum * DOUBLE_BUFFER_MULTIPLIER));
    uint64_t useDoubleBuffer = (loopCountIfDouble >= DOUBLE_BUFFER_THRESHOLD) ? 1 : 0;

    // UB budget: TENSOR_NUM queue buffers (doubled if double buffer) + extraBuf cast bufs (single)
    int64_t queueBufNum = TENSOR_NUM * (useDoubleBuffer ? DOUBLE_BUFFER_MULTIPLIER : 1);
    int64_t ubFactor;
    if (isFp16) {
        // FP16: queue buffers × sizeof(half) + cast bufs × sizeof(float)
        // Queue buffers are doubled in double buffer mode; cast bufs (TBuf) are single
        int64_t bytesPerElem = queueBufNum * TYPE_SIZE_FP16 + FP16_CAST_BUF_NUM * TYPE_SIZE_FP32;
        ubFactor = FloorAlign(FloorDiv(static_cast<int64_t>(ubSize), bytesPerElem), ubBlockSize);
    } else {
        ubFactor = FloorAlign(FloorDiv(static_cast<int64_t>(ubSize) / typeSize, queueBufNum), ubBlockSize);
    }
```

关键差异：

1. 把 `bufferCount`（按 `totalBufNum` 整体翻倍，会把不该翻倍的 Cast buffer 也翻倍）改为 `queueBufNum = TENSOR_NUM * (useDoubleBuffer ? 2 : 1)`，只对 Queue 部分翻倍。
2. FP16 分支 `bytesPerElem` 的 Queue 项用 `queueBufNum`（已含 double buffer 倍数），Cast 项 `FP16_CAST_BUF_NUM * TYPE_SIZE_FP32` 保持单份。
3. FP32 分支同步用 `queueBufNum`（FP32 无 Cast buffer，整体即 Queue 数）。

重编安装：`source /usr/local/Ascend/cann-9.0.0/bin/setenv.bash && bash build.sh --ops=fused_bias_leaky_relu --soc=ascend950 --pkg -j16`（workdir `/workspace/cann/ops-nn`），随后安装到 `opp/vendors/custom_nn` 并清 TTK/atc kernel cache。

## 系统信息

- **工具链**：CANN 9.0.0（`/usr/local/Ascend/cann-9.0.0`），TTK `python3 -m ttk`。
- **目标平台**：Ascend950PR（ascend950），8 卡 131072 MB HBM。
- **相关文件**（与事件流实际读写一一对应）：
  - `ops-nn/activation/fused_bias_leaky_relu/op_host/arch35/fused_bias_leaky_relu_tiling_arch35.cpp`（修复点，事件 713/714 read before、717 edit、959 read after）
  - `ops-nn/activation/fused_bias_leaky_relu/op_kernel/arch35/fused_bias_leaky_relu.h`（kernel 侧 BUFFER_NUM/TENSOR_NUM 定义，事件 707 read）
  - `ops-nn/activation/fused_bias_leaky_relu/op_kernel/arch35/fused_bias_leaky_relu_tiling_data.h`、`..._tiling_key.h`
  - `ops-test-kit/fused_bias_leaky_relu/fused_bias_leaky_relu_golden_plugin.py`（golden，本卡不涉及）
- **常量**：`TENSOR_NUM=3`、`FP16_CAST_BUF_NUM=3`、`TYPE_SIZE_FP16=2`、`TYPE_SIZE_FP32=4`、`DOUBLE_BUFFER_MULTIPLIER=2`、`DOUBLE_BUFFER_THRESHOLD=2`、`BLOCK_ALIGN_BYTES=32`。

## 设计决策

- **为何 Queue 与 Cast buffer 倍数不同**：Queue 是 GM↔UB 的搬运 buffer，kernel 用 `BUFFER_NUM=2` 做双缓冲以重叠搬运与计算，运行时各占 2 份 UB；Cast buffer（`xFp32/biasFp32/yFp32`）是 kernel 内 `TBuf`，单份即可，不随 double buffer 翻倍。UB 预算必须分别按各自倍数累加。
- **被放弃的写法**：原 `bufferCount = totalBufNum * (useDoubleBuffer ? 2 : 1)` 把 Queue 与 Cast 一起翻倍——在 FP32 路径（无 Cast buffer）下碰巧等价，但 FP16 路径下既错误（漏乘 Queue）又自相矛盾（Cast 也被翻倍），是 bug 来源。
- **为何不改 kernel**：kernel 的 `BUFFER_NUM=2` 是性能需要（搬运/计算重叠），不应削弱；正确做法是在 tiling 侧如实反映 kernel 的 buffer 占用。
- **路线归属**：`recommended_fastpath`——任何 Queue+TBuf 混合的 UB 预算都应按此分别计倍数，不是 fallback。

## 验证信号

修复后重编安装并重跑原 VEC_ERROR 用例（TTK `ttk op` 子命令，fp16 + tiling_key=1 大 shape）：

- 修复前：`fblr_perf_fp16_18M`、`fblr_perf_fp16_33M`、`fblr_edge_large_1d_fp16_float16` 均 `dyn_precision=NO_OUTPUT`、`metrics: {'dyn': {}, 'cst': {}, 'bin': {}}`，`ttk-error.log` 记录 `VEC_ERROR encountered`（来源平台：950；证据等级: tool_observed）。
- 修复后：`fblr_perf_fp16_18M` 不再 NO_OUTPUT，产生精度指标 `MERE=0.00019371121015865356`（threshold 0.0009765625，通过）、`MARE=0.1033301055431366`（该 case 残留的 golden dtype 不匹配是另一独立问题）（来源平台：950；证据等级: tool_observed）。
- 小 shape `fblr_edge_smallval_float16`（fp16 + tiling_key=0，single buffer）修复前后均不触发 VEC_ERROR，与本根因无关（来源平台：950；证据等级: tool_observed）。

## 性能影响

本卡为 runtime 正确性修复，无性能故事（修复前直接 VEC_ERROR 无输出，修复后才可比较）。未验证精度影响（精度影响由后续 golden dtype 修复独立处理）。

## 预防

- 写 tiling UB 预算时，先列清 kernel 侧每类 buffer 的份数（Queue 是否 double buffer、TBuf 是否单份），再分别按倍数累加 `bytesPerElem`，禁止把 Queue 与 TBuf 混按单一倍数。
- 对 FP16 + Cast 通路，单独走 `bytesPerElem = queueBufNum * sizeof(half) + castBufNum * sizeof(float)` 分支，而非套用 FP32 的 `bufferCount` 公式。
- TTK 出现 `VEC_ERROR` + `NO_OUTPUT` + 大 shape + 特定 tiling_key 时，优先核对 tiling 的 UB/GM 预算算式，而不是先怀疑设备健康或 OOM。

## 失效边界

- **未验证，推断可迁移**：a2/a3 平台未实测；同 tiling 范式（Queue double buffer + Cast TBuf 单份）的 FP16 element-wise 算子推断可迁移，但 UB 容量、`DOUBLE_BUFFER_THRESHOLD`、`BLOCK_ALIGN_BYTES` 在不同 arch 可能不同，迁移时需用目标 arch 的 `GetCoreMemSize(UB)` 与 kernel buffer 定义复核算式。
- **不覆盖**：FP32 路径、single buffer 路径的正确性证明；Cast buffer 是否真为 TBuf 单份的 kernel 侧 verbatim 证据（event 707 read 被 redact）。

## 坏实践

- 把 `bufferCount = totalBufNum * (useDoubleBuffer ? 2 : 1)` 当万能公式套到 FP16 Cast 通路——对 FP32 碰巧等价，对 FP16 既有「Queue 漏乘」又有「Cast 误乘」，掩盖性强。
- TTK 见 `VEC_ERROR`/`NO_OUTPUT` 就先怀疑设备 Alarm 或 OOM，未先核对 tiling UB 算式。

## 误诊

本 trace 在定位本根因前曾长时间误诊为 `compile info not contain [_pattern]` / `INVALID_TILING`：因删除 `opp/vendors/customize` 目录破坏环境、以及 ops-nn `build.sh --ops=fused_bias_leaky_relu` 在 build 目录残留了 advance_step 的旧 `libcust_opmaster_rt2.0.so`（`FusedBiasLeakyRelu` count=0）所致。期间 agent 一度尝试修改公共 `asc_op_compile_base/asc_op_compiler/op_tiling.py` 注入 `_pattern`，被用户驳回「别的算子可以编译，不要修改公共代码」。真正解法是清理 build 目录残留 .so 后重编安装，与本次 UB 根因无关，记录于此供下个 agent 跳过该弯路。

<!-- cannbot:related:start -->
## 相关

- [GetCoreMemSize](../../apis/utils_api/platform_info/platform_ascend_c/get_core_mem_size.md)（`exemplifies`）：GetCoreMemSize 与《FP16 double-buffer UB 预算漏乘 2 致 VEC_ERROR》的实质衔接是：GetCoreMemSize 为 host tiling 提供各层容量；ReserveLocalMemory 会改变可用 UB，Matmul 空间查询与 UB 预算故障直接消费该值。
- [ACLNN 507015 — tiling UB 漏算 kIdxBuf 下溢](aclnn_507015_tiling_ub_kidxbuf.md)（`related`）：focal 漏算 kIdxBuf 与 padding，目标卡漏算 Queue 的 double-buffer 倍数；两者共同要求按 buffer 类别和实际份数镜像 Kernel，而非使用统一 per-element 近似式。
- [DoubleBuffer](../../guides/technical_appendix/concepts_and_terms/performance_optimization/double_buffer.md)（`related`）：开启双缓冲会让 Queue/TBuf 物理占用乘二；该 runbook 给出漏乘导致 UB 越界和 VEC_ERROR 的实测预算边界。
- [DoubleBuffer场景](../../guides/operator_practice/simd_operator_impl/vector_programming/double_buffer_scenario.md)（`related`）：FP16 double-buffer UB 预算漏乘 2 致 VEC_ERROR 与《DoubleBuffer场景》的实质衔接是：focal 的漏乘项正是 TQue/TBuf 数量×double-buffer depth×dtype字节数；DoubleBuffer文档、InitBuffer、GetCoreMemSize和按dtype分配案例共同完成预算与验证。
- [HardSwish 逐元素 kernel 的 TQue 双缓冲实现配方](elementwise_tque_double_buffer_inplace_recipe.md)（`related`）：HardSwish 逐元素 kernel 的 TQue 双缓冲实现配方 负责“ascend910b 上 HardSwish 算子的可复用实现：2 个 TQue in-place、单 tile 快速路径、5 指令序列、remainder 均衡分块；15 测试点全部 Pass”；FP16 double-buffer UB 预算漏乘 2 致 VEC_ERROR 负责“FusedBiasLeakyRelu arch35 tiling 在 FP16+double buffer 路径计算 ubFactor 时，bytesPerElem 未对 Queue 部分乘以 DOUBLE_BUFFER_MULTIPLIER，导致 ubFactor 高估、UB 溢出 ~29%，大 shape fp16 用例触发 VEC_ERROR”。
- [TQue InitBuffer 须传深度和 uint32 长度](tque_initbuffer_requires_depth_and_uint32_length.md)（`related`）：FP16 double-buffer UB 预算漏乘 2 致 VEC_ERROR 与《TQue InitBuffer 须传深度和 uint32 长度》的实质衔接是：focal 的漏乘项正是 TQue/TBuf 数量×double-buffer depth×dtype字节数；DoubleBuffer文档、InitBuffer、GetCoreMemSize和按dtype分配案例共同完成预算与验证。
- [tmpBuffer 分配步长≠访问步长触发 UB 越界 341](tmpbuffer_ub_341.md)（`related`）：tmpBuffer 分配步长≠访问步长触发 UB 越界 341 与《FP16 double-buffer UB 预算漏乘 2 致 VEC_ERROR》的衔接是：四个案例都把 UB 预算、分块或对齐计算与实际访问跨度不一致定位为越界根因，可复用‘按访问类型和对齐重算最大偏移’的验证方法。
- [开启DoubleBuffer](../../guides/operator_practice/simd_operator_optimization/pipeline_scheduling/enable_double_buffer.md)（`related`）：FP16 double-buffer UB 预算漏乘 2 致 VEC_ERROR 与《开启DoubleBuffer》的实质衔接是：focal 的漏乘项正是 TQue/TBuf 数量×double-buffer depth×dtype字节数；DoubleBuffer文档、InitBuffer、GetCoreMemSize和按dtype分配案例共同完成预算与验证。
- [507035 C 超 per_buf_elems 致 Phase1 UB 越界](datacopypad_phase1_chunk_loop_per_buf_elems_507035.md)（`same_topic`）：焦点处理Phase1 中 C 超出 per_buf_elems 导致 UB 地址越界的预算故障；FP16 double-buffer UB 预算漏乘 2 致 VEC_ERROR正文说明“FusedBiasLeakyRelu arch35 tiling 在 FP16+double buffer 路径计算 ubFactor 时，bytesPerElem 未对 Queue 部分乘以 DOUBLE_BUFFER_MULTIPLIER，导致 ubFactor 高估、UB ”。候选与焦点共享 UB 容量/slot 预算机制，能直接修正切分因子、物理宽度或双缓冲计数。
- [507035 — Host 按逻辑行宽预算导致 UB 溢出](ub_budget_uses_aligned_physical_width_507035.md)（`same_topic`）：FP16 double-buffer UB 预算漏乘 2 致 VEC_ERROR 与《507035 — Host 按逻辑行宽预算导致 UB 溢出》的实质衔接是：focal 的漏乘项正是 TQue/TBuf 数量×double-buffer depth×dtype字节数；DoubleBuffer文档、InitBuffer、GetCoreMemSize和按dtype分配案例共同完成预算与验证。
- [按 dtype 分配 UB 必须匹配 tiling 预算](dtype_conditional_ub_allocation_matches_tiling_budget.md)（`same_topic`）：FP16 double-buffer UB 预算漏乘 2 致 VEC_ERROR 与《按 dtype 分配 UB 必须匹配 tiling 预算》的实质衔接是：focal 的漏乘项正是 TQue/TBuf 数量×double-buffer depth×dtype字节数；DoubleBuffer文档、InitBuffer、GetCoreMemSize和按dtype分配案例共同完成预算与验证。
<!-- cannbot:related:end -->
