---
type: "Runbook"
title: "DataCopy GM→UB 需 32B 对齐，非对齐 C 统计输出全零"
description: "Ascend950 上 1D GM→UB 用 DataCopy 时若 C*sizeof(dtype) 非 32B 对齐则搬运失败、统计输出全零；应改用 DataCopyPad 处理非对齐。"
tags: ["task.debugging", "topic.precision", "topic.data_movement.data_copy", "topic.alignment"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
aliases: ["GM_to_UB"]
---

# DataCopy GM→UB 需 32B 对齐，非对齐 C 统计输出全零

## 现象

Ascend950（dav-3510，CANN 9.0.0-beta.2）上 `bn_training_update_custom` Branch-4 kernel 修复 507035 崩溃后，18 个 ST 用例中 1 个通过、17 个精度失败。失败模式高度同质：统计输出（`batch_mean`/`batch_variance`/`mean_out`/`variance_out`）**几乎全 0**，且严格按通道轴 C 的对齐性质分流——`C=64`（`64*4=256` 字节，32B 对齐）的用例通过，`C=3`、`C=1`（`12`/`4` 字节，非 32B 对齐）的用例全失败。kernel Phase 1 用 `AscendC::DataCopy(buf, gmIn[i], ...)` 做 1D GM→UB 搬运，把 `(C,)` 张量从 GM 拷到 UB。

## 适用场景

- **工程形态**：kernel 直调（AscendC regbase），Phase 1/标量段对 `(C,)` 1D 张量做 GM→UB 搬运后接 Vector 计算。
- **API 路径**：`AscendC::DataCopy(LocalTensor, GlobalTensor, ...)`（GM→UB 方向）；非对齐替代为 `AscendC::DataCopyPad(LocalTensor, GlobalTensor, DataCopyExtParams, DataCopyPadExtParams<T>)`。
- **验证过的平台与 CANN 版本**：Ascend950 / dav-3510 / CANN 9.0.0-beta.2。
- **适用粒度**：`platform_wide`——dav-3510 上所有用 `DataCopy` 做 1D GM→UB 且 C 可能为非 32B 对齐的算子。
- **路线优先级**：`recommended_fastpath`——凡 1D GM→UB 且 C 不保证 32B 对齐，一律用 `DataCopyPad`（DataCopyExtParams + DataCopyPadExtParams），不用裸 `DataCopy`。
- **不适用或未验证场景**：多维 NDDMA `DataCopy<T, ND, cfg>` 路径不在本卡（NDDMA 有自己的 stride/shape 对齐约束）；UB→GM 方向的 `DataCopyPad` 见解决配方。

## 判别方法

- **触发**：GM→UB 用 `DataCopy`，且 `C * sizeof(dtype) % 32 != 0`（如 fp32 C=3 → 12 字节，fp32 C=1 → 4 字节）。现象是搬运后该 buffer 内容为 0/未写入，下游 Vector（`Muls`/`Sub`/`Sqrt` 等）吃全零输入，统计输出全零；编译过、无 507035。
- **可执行探针**：在怀疑的用例上查 `C * sizeof(dtype) % 32`：余 0 → 对齐（若仍失败查别处）；余非 0 → 命中本规则。也可临时把 C 改成 8 的倍数（fp32）重跑：通过即坐实。
- **原始观测**：C=64 通过、C=3/C=1 全失败且统计输出全 0；切换 `DataCopy`→`DataCopyPad` 后 15/18 通过（剩余 3 个为 FMA 舍入问题，另见他卡）。
- **解释**：`DataCopy`（GM→UB）要求搬运字节数 32B 对齐；非对齐时搬运不生效或写零，UB buffer 留为初始化态（全零），下游 Vector 链产出全零统计。`DataCopyPad` 专为非对齐设计，用 `DataCopyExtParams{blockCount=1, blockLen=字节数, srcStride=0, dstStride=0}` + `DataCopyPadExtParams<T>` 显式描述非对齐块，正确搬运。

## 根因

`DataCopy`（GM→UB）要求搬运字节数 32B 对齐；非对齐时搬运不生效或写零，UB buffer 留为初始化态（全零），下游 Vector 链产出全零统计。

**与相近卡的区分（本卡 novel 贡献）**：另有一张卡（`ascend950_dma_32b_minimum_block_granularity`）描述 950 DMA 的 32B 最小块粒度约束（搬运粒度层面的对齐规则）。本卡的 novel 不在"粒度约束"本身，而在 **多元素非 32B 对齐 1D `(C,)` 张量经 `DataCopy` 搬运后下游统计全零**这一具体失效模式，以及用 `DataCopyExtParams` + `DataCopyPadExtParams` 显式描述非对齐块修复 `DataCopy` 失效的配方——聚焦"非对齐 C → 全零输出"的因果链与 `DataCopyPad` 替换，与那张块的粒度规则互补、不重复。

## 解决配方

参考 `layer_norm_v3` 参考实现（CANN 自带），1D GM→UB 用 `DataCopyPad`：

```cpp
AscendC::DataCopyExtParams ep1;
ep1.blockCount = 1;
ep1.blockLen = static_cast<uint32_t>(C * sizeof(float));  // 字节数，非元素数
ep1.srcStride = 0;
ep1.dstStride = 0;
AscendC::DataCopyPadExtParams<float> padIn;
// GM→UB：
AscendC::DataCopyPad(buf[0].Get<float>(), gmIn[0], ep1, padIn);
```

UB→GM 方向同样用 `DataCopyPad`（首参为 GM 目标）：

```cpp
AscendC::DataCopyPad(gmOut[3], buf[0].Get<float>(), ep1);  // UB→GM，无需 padIn
```

把 Phase 1 全部 6 处 `DataCopy`（GM→UB）替换为上述 `DataCopyPad` 调用即消除非对齐失败。

## 验证信号

本卡验证来源：bn_training_update_custom Branch-4 kernel 调试会话（Ascend950 / CANN 9.0.0-beta.2）。

- C=64（32B 对齐）通过、C=3/C=1（非 32B 对齐）统计输出全 0 失败——按 C 对齐性质精确分流（来源平台：Ascend950；证据等级: tool_observed）
- `layer_norm_v3` 参考实现 GM→UB 用 `DataCopyPad(DataCopyExtParams + DataCopyPadExtParams)`——逐字 CANN 参考源（来源平台：Ascend950；证据等级: tool_observed）

## 预防

- 1D GM→UB 搬运默认用 `DataCopyPad`，不要用裸 `DataCopy`——除非能静态保证 `count*sizeof(dtype)` 恒 32B 对齐。
- review 时 grep `DataCopy(buf.*, gmIn` 形式，对非对齐可能的 C 一律改 `DataCopyPad`。

## 失效边界

- 仅 Ascend950（arch 3510）实测；其他 dav 平台未验证，推断可迁移（32B 对齐是 AscendC DMA 通用约束）——未验证，推断可迁移。
- 多维 NDDMA `DataCopy<T, ND, cfg>` 的对齐/stride 约束不同，本卡不覆盖。

## 坏实践

- 改用例 C 凑 32B 对齐绕过（掩盖问题，生产 shape 仍崩）。
- 放宽统计输出阈值容忍全零（反投机取巧）。

## 误诊

最初怀疑 workspace 大小（见 build 卡 507035）；修 workspace 后崩溃消失但暴露出本对齐问题——两问题同 trace 串联，但根因不同、各一卡。

<!-- cannbot:related:start -->
## 相关

- [DataCopy](../../apis/simd_api/basic_api/memory_vector_compute/data_move/data_copy_gm_to_ub_nddma.md)（`exemplifies`）：DataCopy 与《DataCopy GM→UB 需 32B 对齐，非对齐 C 统计输出全零》的实质衔接是：该 DataCopy 是 GM→UB NDDMA，多维 shape/stride、NdDmaDci 与非对齐 padding 是直接契约；所选故障卡覆盖漏维、stride=0 和 cache 刷新边界。
- [DataCopyPad](../../apis/simd_api/basic_api/memory_vector_compute/data_move/data_copy_pad_gm_to_ub.md)（`exemplifies`）：《DataCopyPad》说明将数据从GM非对齐搬运至UB，可根据需要自行填充数据。；《DataCopy GM→UB 需 32B 对齐，非对齐 C 统计输出全零》说明Ascend950 上 1D GM→UB 用 DataCopy 时若 C*sizeof(dtype) 非 32B 对齐则搬运失败、统计输出全零；应改用 DataCopyPad 处理非对齐。。二者在GM到UB非对齐搬入依赖Pad参数、32B最小DMA和LocalTensor/offset/rightPad合同，UB到GM方向的重载不同上存在可执行的直接衔接。
- [Ascend950 DMA 32B 块最小传输粒度](../compilation/ascend950_dma_32b_minimum_block_granularity.md)（`same_topic`）：DataCopy GM→UB 需 32B 对齐，非对齐 C 统计输出全零：本卡以C字节数非32B倍数复现GM→UB DataCopy静默全零；DataCopyPad是直接修复，32B最小粒度卡解释硬件根因，其余所选卡覆盖Pad参数、尾块初始化/逐行搬运及对向DataCopy尾丢失验证。 目标卡《Ascend950 DMA 32B 块最小传输粒度》补充：Ascend950 GM↔UB DMA 引擎最小传输单元为 32 字节（一个 block，fp32=8 元素）；单 float 标量 DMA 静默失败或报 507015，按 8 元素对齐的 DataCopy 会越界读 GM 致 Segfault。
- [DataCopy 非32字节对齐尾块丢字节](datacopy_32.md)（`same_topic`）：DataCopy GM→UB 需 32B 对齐，非对齐 C 统计输出全零：本卡以C字节数非32B倍数复现GM→UB DataCopy静默全零；DataCopyPad是直接修复，32B最小粒度卡解释硬件根因，其余所选卡覆盖Pad参数、尾块初始化/逐行搬运及对向DataCopy尾丢失验证。 目标卡《DataCopy 非32字节对齐尾块丢字节》补充：AscendC::DataCopy 按硬件 32 字节块长搬运，count*sizeof(dtype) 非 32B 倍数时向下取整丢弃尾部字节，UB↔GM 尾块元素被写成 0。判别=逐元素对比定位首个 mismatch index，若集中在尾部且 mismatch 数=count−floor(count*sizeof/32)*32/sizeof 即锁定。修复方向 DataCopyPad 显式 blockLen。
- [DataCopyPad CopyIn 小输入 32B DMA 越界](../compilation/datacopypad_copyin_32b_dma.md)（`same_topic`）：DataCopy GM→UB 需 32B 对齐，非对齐 C 统计输出全零：本卡以C字节数非32B倍数复现GM→UB DataCopy静默全零；DataCopyPad是直接修复，32B最小粒度卡解释硬件根因，其余所选卡覆盖Pad参数、尾块初始化/逐行搬运及对向DataCopy尾丢失验证。 目标卡《DataCopyPad CopyIn 小输入 32B DMA 越界》补充：DataCopyPad CopyIn 不论 DataCopyExtParams.blockLen 写多少，底层 DMA 引擎按 32 字节（1 DataBlock）粒度读 GM；当 Host 仅按有效元素数分配 < 32B 输入、SetGlobalBuffer(ptr,N) 只声明逻辑可读范围不扩大物理分配时，DMA 实读 32B 越过已映射内存 → device error 507035 / segfault。判别：小输入（有效元素
- [DataCopyPad 加载缺少 Pad 参数导致编译失败](../compilation/datacopypad_gm_to_ub_requires_pad_params.md)（`same_topic`）：DataCopy GM→UB 需 32B 对齐，非对齐 C 统计输出全零：本卡以C字节数非32B倍数复现GM→UB DataCopy静默全零；DataCopyPad是直接修复，32B最小粒度卡解释硬件根因，其余所选卡覆盖Pad参数、尾块初始化/逐行搬运及对向DataCopy尾丢失验证。 目标卡《DataCopyPad 加载缺少 Pad 参数导致编译失败》补充：dav-3510 的 GM 到 UB DataCopyPad 扩展重载需要第四个 Pad 参数，不能照搬 UB 到 GM 的三参数形式。
- [DataCopyPad 尾块改逐行一维搬入](datacopypad_partial_2d_blocks_use_per_row_copy.md)（`same_topic`）：DataCopy GM→UB 需 32B 对齐，非对齐 C 统计输出全零：本卡以C字节数非32B倍数复现GM→UB DataCopy静默全零；DataCopyPad是直接修复，32B最小粒度卡解释硬件根因，其余所选卡覆盖Pad参数、尾块初始化/逐行搬运及对向DataCopy尾丢失验证。 目标卡《DataCopyPad 尾块改逐行一维搬入》补充：2D DataCopyPad 的多块参数未把短块落到 256B UB 行首，会让 LoadAlign 读错行；逐行 blockCount=1 可消除歧义。
- [NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写](../compilation/nddma_nddmaconfig_datacopypad.md)（`same_topic`）：DataCopy GM→UB 需 32B 对齐，非对齐 C 统计输出全零：本卡以C字节数非32B倍数复现GM→UB DataCopy静默全零；DataCopyPad是直接修复，32B最小粒度卡解释硬件根因，其余所选卡覆盖Pad参数、尾块初始化/逐行搬运及对向DataCopy尾丢失验证。 目标卡《NDDMA非对齐尾轴需NdDmaConfig右填充与DataCopyPad回写》补充：Ascend950/CANN9.1.0 下 NDDMA DataCopy 的非 32B 对齐尾轴须显式设 NdDmaConfig.loopRpSize 右填充(仅 loop0 进硬件指令)且 UB→GM 回写用 DataCopyPad(DataCopyExtParams) 字节粒度；缺 padding 或用 DataCopy(DataCopyParams)(blockLen 以 32B 块为单位)会触发 DYN_COMPILE_FAIL
- [arch35 小 per-channel 输出读旧值判别与规避](../compilation/arch35_per_channel.md)（`same_topic`）：《arch35 小 per-channel 输出读旧值判别与规避》处理“arch35 上 DCCI 缓存不一致使 DataCopyPad 对小 per-channel [C] 输出不可靠、TQue GetValue(MTE2→scalar) 读到旧值；判别方法为先 V-launder(Duplicate 0.0f+Add) 到 TBuf 再 GetValue，并用 GlobalTensor::SetValue 直写 GM per-channel 结果。”。《DataCopy GM→UB 需 32B 对齐，非对齐 C 统计输出全零》提供“Ascend950 上 1D GM→UB 用 DataCopy 时若 C*sizeof(dtype) 非 32B 对齐则搬运失败、统计输出全零；应改用 DataCopyPad 处理非对齐。”，其具体合同或探针直接接入arch35 小 per-channel 的 DCCI/Scalar 旧值机制、V-launder 与 SetValue 验证。
<!-- cannbot:related:end -->
