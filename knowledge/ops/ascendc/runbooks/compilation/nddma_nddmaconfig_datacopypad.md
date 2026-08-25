---
type: "Runbook"
title: "NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写"
description: "Ascend950/CANN9.1.0 下 NDDMA DataCopy 的非 32B 对齐尾轴须显式设 NdDmaConfig.loopRpSize 右填充(仅 loop0 进硬件指令)且 UB→GM 回写用 DataCopyPad(DataCopyExtParams) 字节粒度；缺 padding 或用 DataCopy(DataCopyParams)(blockLen 以 32B 块为单位)会触发 DYN_COMPILE_FAILURE。"
tags: ["task.debugging", "topic.data_movement.data_copy", "topic.alignment"]
status: stable
sources: []
created_at: "2026-08-15T09:23:04Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
aliases: ["nddma_out_to_ub_b16"]
---

# NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写

## 现象

在 Ascend950 / CANN 9.1.0 下用 TTK（`python3 -m ttk kernel`）跑 `nd_dma_bw` 算子的 NDDMA verify 套件时，尾轴非 32B 对齐的 transpose/broadcast 用例与对齐用例表现不一致。被排查 kernel（`nd_dma_bw_apt.cpp` 的 `RunTranspose`）当前使用 `kDefaultNdDmaConfig`，其 `loopLpSize/loopRpSize = unsetPad (0xffff)`，即未设任何 padding。对齐尾轴用例基线编译通过，而一批含非对齐尾轴的用例在 TTK info 日志中报 `STATUS: FAIL, PRECISION_STATUS: FAIL, DYN_PERF: DYN_COMPILE_FAILURE, DYN_GOLD: DYN_COMPILE_FAILURE`。排查方向：当尾轴 `D0 × sizeof(T) % 32 != 0` 时 NDDMA 硬件要求 32B 边界对齐，缺 padding 会导致 UB 布局错位 / GM 回写越界 / 动态编译失败。

## 适用场景

- **工程形态**：kernel 直调（validation harness `nd_dma_bw` bandwidth-test op，非 aclnn 注册算子开发）；TTK 动态编译验证。
- **API 路径**：AscendC `DataCopy<T, dim, NdDmaConfig>`（GM→UB NDDMA）与 `DataCopyPad`（UB→GM 回写）；`NdDmaConfig` / `MultiCopyLoopInfo<dim>` / `DataCopyParams` / `DataCopyExtParams` 结构定义于 `asc/include/basic_api/kernel_struct_data_copy.h` 与 `kernel_operator_data_copy_intf.h`，arch35 实现于 `asc/impl/basic_api/dav_3510/kernel_operator_data_copy_impl.h`。
- **验证过的平台与 CANN 版本**：Ascend950（DAV_3510 / arch35）；CANN 9.1.0；vendor 路径 `customize_math`。`platforms: [950]` 严格对应。
- **适用粒度**：`operator_family`——所有使用 NDDMA `DataCopy<T,dim,Config>` + 非 32B 对齐尾轴的算子族。
- **路线优先级**：`recommended_fastpath`——对非 32B 对齐尾轴显式设 `NdDmaConfig.loopRpSize` 并用 `DataCopyPad(DataCopyExtParams)` 字节粒度回写。
- **不适用或未验证场景**：尾轴已 32B 对齐时无需 padding（设了反而向 UB 注入垃圾 0 元素）；a2/a3 平台未实测（arch35 的 padding 契约在 dav_m510 实现中同构存在，推断可迁移但未验证，不写入 platforms）。

## 判别方法

**触发**（tool_observed）：NDDMA transpose/broadcast 用例在 TTK 动态编译验证下报 `STATUS: FAIL` / `DYN_PERF: DYN_COMPILE_FAILURE` / `DYN_GOLD: DYN_COMPILE_FAILURE`，且被排查 kernel 使用 `kDefaultNdDmaConfig`（`loopLpSize/loopRpSize = unsetPad`，未设 padding）跑非 32B 对齐尾轴 `D0`（即 `MultiCopyLoopInfo` 索引 `[0]`，innermost），满足 `D0 × sizeof(T) % 32 != 0`。

**探针**（固定路径，CANN 9.1.0 安装目录）：

```
ASCEND_HOME=/workspace/wrf/Ascend/cann-9.1.0/x86_64-linux

# 1) 读 NdDmaConfig / MultiCopyLoopInfo 结构定义与 padding 传递链
grep -rn "struct NdDmaConfig\|MultiCopyLoopInfo\|loop0LeftPadSize\|loop0RightPadSize\|set_pad_cnt_nddma" \
    $ASCEND_HOME/asc/impl/basic_api/dav_3510/kernel_operator_data_copy_impl.h

# 2) 读 UB→GM 回写接口与 blockLen 单位语义
grep -n "DataCopyPad.*GlobalTensor\|DataCopySliceUB2GMImpl\|burstLen\|ONE_BLK_SIZE\|unitOfBytes" \
    $ASCEND_HOME/asc/impl/basic_api/dav_3510/kernel_operator_data_copy_impl.h

# 3) TTK 对照：对齐尾轴用例基线应编译 SUCC，非对齐尾轴在缺 padding 时 FAIL
cd /workspace/wrf/validation/ops-test-kit && \
python3 -m ttk kernel -i <verify_csv_with_bins> -t nddma_verify_transpose_last_2d_align \
    --compare stat_rel_err --single-log
python3 -m ttk kernel -i <verify_csv_with_bins> -t nddma_verify_transpose_last_2d_unalign \
    --compare stat_rel_err --single-log
```

**观测**（逐字取自 arch35 实现头与接口头，artifact_verified；TTK 日志取自 tool_observed）：

`DataCopySliceUB2GMImpl`（`kernel_operator_data_copy_impl.h`）：
```cpp
// DataCopyParams: unit of 32Bytes(DataCopy) / Bytes(DataCopyPad)
uint16_t burstLen = intriParams.blockLen * ONE_BLK_SIZE;   // ONE_BLK_SIZE = 32
```

`NdDmaConfig` / `MultiCopyLoopInfo<dim>` 结构契约（`kernel_struct_data_copy.h`）：
```
NdDmaConfig: bool isNearestValueMode; uint16_t loopLpSize (unsetPad=0xffff);
             uint16_t loopRpSize; bool ascOptimize
MultiCopyLoopInfo<dim>: dim∈[1,5], [0]=innermost;
             uint8_t loopLpSize[dim]/loopRpSize[dim] (only loop0 effective)
```

padding 传递链：`config.loopLpSize/loopRpSize`（全局）在非 `unsetPad` 时**覆盖** per-dim `params.loopLpSize[idx]/loopRpSize[idx]`；只有 loop0 的 padding 经 `loop0LeftPadSize/loop0RightPadSize` **直传**硬件指令 `nddma_out_to_ub_b8/b16/b32`；loop1~4 的 padding 被压缩进单一 `padCount` uint64（`set_pad_cnt_nddma(padCount)`，16-bit/loop 槽位，`lpEncodingOffset=16` / `rpEncodingOffset=8`）。

对齐尾轴基线：`nddma_verify_transpose_last_2d_align`（Input Actual Shape `((1,256,256),)` float16）报 `Compilation Result: SUCC`、`Blockdim: 56`。

**判别**（interpretation，根因分析）：NDDMA padding API 契约有三层非显然语义，缺一即触发非对齐失败——

1. **全局覆盖 per-dim**：`NdDmaConfig.loopLpSize/loopRpSize` 是所有维度统一的左/右 padding；非 `unsetPad` 时覆盖 per-dim `MultiCopyLoopInfo.loopLpSize[i]/loopRpSize[i]`，故在 kernel 层设 `loopRpSize = rp` 等于对所有 loop 维统一加右 padding。
2. **仅 loop0 padding 进硬件指令**：CCE `nddma_desc::loop_desc` 的 `lp_size/rp_size` 虽按维度设置，但只有 loop0 的 padding 真正打包进最终硬件指令（`loop0LeftPadSize/loop0RightPadSize` 直传）；loop1~4 仅压缩进 `padCount`。故尾轴（loop0）是 padding 唯一真正生效的维度。
3. **`DataCopyParams.blockLen` 单位 = 32B 块**：UB→GM 回写若用 `DataCopy(DataCopyParams)`，`blockLen` 以 32B 块为单位（`burstLen = blockLen * ONE_BLK_SIZE`），无法表达 sub-32B 长度；非对齐尾轴回写必须改用 `DataCopyPad(DataCopyExtParams)`，其 `blockLen` 以字节为单位（`isDataCopyPad=true → unitOfBytes=1`），`srcStride/dstStride` 仍以 32B 块为单位。

机制链：尾轴 `D0` 非 32B 对齐 → NDDMA 硬件在每次 loop0 迭代写入 `D0 + rp` 个元素到 UB（padding 元素填到 32B 边界）→ UB 内 `loopDstStride[0]` 须计入 padded 大小 → 回写 GM 时须跳过 padding 元素，用 `DataCopyPad(DataCopyExtParams)` 的 `blockLen`(字节) = `D0 × sizeof(T)`、`srcGap` = padding 元素数、`dstGap` = GM 跨块间距。缺 `loopRpSize` 时硬件不自动 padding，会读越界 / UB 布局错位；用 `DataCopy(DataCopyParams)` 回写则 `blockLen` 无法整除非对齐尾轴字节数，截断或越界 → 动态编译失败。

## 验证信号

- 对齐尾轴基线编译通过：`nddma_verify_transpose_last_2d_align` 报 `Compilation Result: SUCC`、`Blockdim: 56`、Input Actual Shape `((1,256,256),)` float16、Tiling Data Parsed Tuple(int32) 含 33 字段（来源平台：Ascend950；证据等级：tool_observed）。
- NDDMA verify 用例批次失败：`nddma_verify_transpose_last_2d_align`、`nddma_verify_broadcast_tail_2d_align`、`nddma_verify_transpose_last_2d_unalign_nd_dma_bw_dup0` 等在 2026-07-24 11:59 报 `STATUS: FAIL, PRECISION_STATUS: FAIL, DYN_PERF: DYN_COMPILE_FAILURE, DYN_GOLD: DYN_COMPILE_FAILURE, DYN_MEM: UNKNOWN`（来源平台：Ascend950；证据等级：tool_observed）。
- arch35 实现头 `DataCopySliceUB2GMImpl`：`burstLen = intriParams.blockLen * ONE_BLK_SIZE`，注释 `DataCopyParams: unit of 32Bytes(DataCopy) / Bytes(DataCopyPad)`（来源平台：Ascend950；证据等级：artifact_verified）。
- `NdDmaConfig`/`MultiCopyLoopInfo` 结构契约：全局 `loopLpSize/loopRpSize` 覆盖 per-dim（`unsetPad=0xffff` 时用 per-dim）；仅 loop0 padding 直传硬件指令 `nddma_out_to_ub_b8/b16/b32`，loop1~4 压缩进 `padCount`（来源平台：Ascend950；证据等级：artifact_verified）。
- `DataCopyPad` UB→GM 重载签名（`DataCopyExtParams` 参）与 `DataCopyParams` 重载并存于接口头 `kernel_operator_data_copy_intf.h`（来源平台：Ascend950；证据等级：artifact_verified）。

> 说明：以上为对 arch35 实现头/接口头的读取观测（artifact_verified）与 TTK 日志（tool_observed），用于判别根因。本 trace 内按此判别对 kernel 补 `loopRpSize` + `DataCopyPad` 回写的修复**未端到端验证通过**（DYN_COMPILE_FAILURE 链未解），"修复后非对齐用例编译/精度通过"的实测信号缺失，不得当作 tool_observed 验证信号使用。

## 坏实践

- 用 `kDefaultNdDmaConfig`（`loopLpSize/loopRpSize = unsetPad`）跑非 32B 对齐尾轴，指望硬件自动对齐——硬件不会自动 padding，会读越界 / UB 布局错位。
- UB→GM 回写用 `DataCopy(DataCopyParams)` 并把 `blockLen` 当元素数或字节数填——`blockLen` 是 32B 块数，非对齐尾轴无法整除，会截断或越界。
- 在 `MultiCopyLoopInfo.loopLpSize[1..4]` / `loopRpSize[1..4]` 上设非零值指望给外层维度 padding——只有 loop0 进硬件指令，外层 padding 仅压缩进 `padCount` 且本场景不需要。

## 失效边界

- 尾轴已 32B 对齐时**不得**设 `loopRpSize`（会向 UB 注入垃圾 0 元素污染数据）。
- a2/a3 平台未实测；arch35（Ascend950）的 padding 契约在 dav_m510 实现中同构存在，推断可迁移但未验证，不写入 platforms。
- `DataCopyPad(DataCopyExtParams)` 的 arch35/5102 专用重载在其他 arch 上签名不同，跨 arch 须重新核对接口。
- 本判别基于 API 契约推导与 TTK 编译失败信号；修复后编译/精度通过的闭环信号缺失。

<!-- cannbot:related:start -->
## 相关

- [DataCopy](../../apis/simd_api/basic_api/memory_vector_compute/data_move/data_copy_gm_to_ub_nddma.md)（`exemplifies`）：《DataCopy》给出“多维数据搬运接口，支持自由配置搬入的维度信息及对应的Stride。”；该约束/探针可直接复现、解释或前置验证《NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写》中的“Ascend950/CANN9.1.0 下 NDDMA DataCopy 的非 32B 对齐尾轴须显式设 NdDmaConfig.loopRpSize 右填充(仅 loop0 进硬件指令)且 UB→GM 回写用 DataCopyPad(DataCopyExtParams) 字节粒度；缺 padding 或用 DataCopy(DataCopyParams)(blockLen 以 32B 块为单位)会触发 DYN_COMPILE_FAILURE。”。
- [DataCopyPad](../../apis/simd_api/basic_api/memory_vector_compute/data_move/data_copy_pad_ub_to_gm.md)（`exemplifies`）：《DataCopyPad》明确“将数据从UB非对齐搬运至GM。”；它与《NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写》的“Ascend950/CANN9.1.0 下 NDDMA DataCopy 的非 32B 对齐尾轴须显式设 NdDmaConfig.loopRpSize 右填充(仅 loop0 进硬件指令)且 UB→GM 回写用 DataCopyPad(DataCopyExtParams) 字节粒度；缺 padding 或用 DataCopy(DataCopyParams)(blockLen 以 32B 块为单位)会触发 DYN_COMPILE_FAILURE。”在实际调用参数、数据流或结果校验上直接衔接。
- [GmUbDataMove](../../apis/simd_api/basic_api/data_move_guide/gm_ub_data_move.md)（`exemplifies`）：GmUbDataMove 与《NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写》的实质衔接是：GM↔UB 总览按连续、高维、切片、ND2NZ/NZ2ND、NDDMA 和 DataCopyPad 选择通路；所选 NDDMA 卡逐一约束 padding、维度和 stride。
- [Transpose](../../apis/simd_api/adv_api/tensor_transform/transpose.md)（`exemplifies`）：《Transpose》处理“对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。”。《NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写》明确提供“Ascend950/CANN9.1.0 下 NDDMA DataCopy 的非 32B 对齐尾轴须显式设 NdDmaConfig.loopRpSize 右填充(仅 loop0 进硬件指令)且 UB→GM 回写用 DataCopyPad(DataCopyExtParams) 字节粒度；缺 padding 或用 DataCopy(DataCopyParams)(blockLen 以 32B 块为单位)会触发 DYN_COMPILE_FAILURE。”，其参数、调用或验证步骤直接接入Transpose 的 Tiling、转置搬运、布局转换和轴顺序验证。
- [DataCopy尾chunk非32B对齐触发ERR99999](datacopy_chunk_32b_err99999.md)（`related`）：《DataCopy尾chunk非32B对齐触发ERR99999》说明Ascend C DataCopy 在 UB↔GM 方向要求 count*sizeof(T) 为 32 字节对齐，否则搬运量对 32B 向下取整。当纯搬运算子尾 chunk 的实际元素数不满足 32B 对齐时，UB→GM 写方向触发 ERR99999、GM→UB 读方向静默丢尾部数据。判别方法：尾部元素数*sizeof(T)%32!=0 即命中。；《NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写》说明Ascend950/CANN9.1.0 下 NDDMA DataCopy 的非 32B 对齐尾轴须显式设 NdDmaConfig.loopRpSize 右填充(仅 loop0 进硬件指令)且 UB→GM 回写用 DataCopyPad(DataCopyExtParams) 字节粒度；缺 padding 或用 DataCopy(DataCopyParams)(blockLen 以 32B 块为单位)会触发 DYN_COMPILE_FAILURE。。二者在DataCopy尾chunk错误由有效字节数非32B倍数触发，DataCopyPad的逐行、stride、padding和最小DMA卡给出修复边界上存在可执行的直接衔接。
- [NDDMA 最内层 srcStride=0 广播读越界](../precision/nddma_srcstride_0.md)（`related`）：srcStride 修正只能保证取数位置，非 32B 尾轴还需 loopRpSize 和字节粒度 DataCopyPad 回写；该卡补齐 NDDMA 广播修复后的对齐/搬出约束。
- [RANK大于5时NDDMA漏维只解释accum错误](../precision/rank_5_nddma_accum_var.md)（`related`）：该卡说明 NDDMA 只把最内层 loop0 padding 送入硬件，外层与尾轴需显式配置，强化不能假设描述符自动覆盖所有维度和边界。
- [DataCopy GM→UB 需 32B 对齐，非对齐 C 统计输出全零](../precision/datacopy_gm_to_ub_non_32b_aligned_silent_zero.md)（`same_topic`）：DataCopy GM→UB 需 32B 对齐，非对齐 C 统计输出全零：本卡以C字节数非32B倍数复现GM→UB DataCopy静默全零；DataCopyPad是直接修复，32B最小粒度卡解释硬件根因，其余所选卡覆盖Pad参数、尾块初始化/逐行搬运及对向DataCopy尾丢失验证。 目标卡《NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写》补充：Ascend950/CANN9.1.0 下 NDDMA DataCopy 的非 32B 对齐尾轴须显式设 NdDmaConfig.loopRpSize 右填充(仅 loop0 进硬件指令)且 UB→GM 回写用 DataCopyPad(DataCopyExtParams) 字节粒度；缺 padding 或用 DataCopy(DataCopyParams)(blockLen 以 32B 块为单位)会触发 DYN_COMPILE_FAIL
- [NDDMA 快速路径 C=1 中间轴漏维判别](../precision/nddma_c_1.md)（`same_topic`）：NDDMA 快速路径 C=1 中间轴漏维判别 与《NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写》的实质衔接是：这些 NDDMA 卡围绕维序、stride、padding 与高 rank 配置解释同一快速路径漏维/越界机制。
<!-- cannbot:related:end -->
