---
type: "Runbook"
title: "b16 提升 fp32 比较后按存储宽度分块会漏掉后半 lane"
description: "2-byte 数据提升为 fp32 比较时，分块宽度必须按比较类型的单 repeat lane 数计算，否则后半 lane 不更新。"
tags: ["task.debugging", "topic.precision", "topic.compute.elementwise.comparison_logic"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
aliases: ["bfloat16_t"]
---

# b16 提升 fp32 比较后按存储宽度分块会漏掉后半 lane

## 现象

在 Ascend950 上开发“2-byte 输入先 `Cast` 到 fp32，再用经典 AscendC `Compare`/`Select` 更新前缀状态”的 kernel 时，干净构建能够通过，4-byte 路径也正确，但 fp16/bf16 的非最内轴多块路径出现部分结果错误。定向探针显示：同一个 128-lane chunk 内，lane 0–63 正确，错误稳定从 lane 64 开始；后半段表现为未更新的旧值或错误索引。

这不是随机同步问题：边界位置固定在比较类型的单 repeat 宽度处。

## 适用场景

- 工程形态：Ascend C kernel 直调，UB 中按 N 轴分块并用经典 Level-2 `Compare`/`Select` 维护向量状态；
- API 路径：`Cast<X, float>` 后调用 `Compare<float>`，输入存储类型为 fp16/bf16；
- 验证过的平台与 CANN 版本：950 / CANN 9.0.1；与 frontmatter `platforms` 一致；
- 适用粒度：`operator_family`，适用于“存储类型与实际比较类型不同”的扫描、极值、条件选择类 kernel；
- 路线优先级：`recommended_fastpath`；按实际计算/比较类型的单 repeat lane 数分块；
- 明确不适用：直接以存储类型参与比较，或 API 明确支持跨多个 repeat 的 count 语义时，不能机械套用本结论。

## 根因

`nC` 按 2-byte 存储类型计算为 `VECTOR_REG_WIDTH / sizeof(X)`，但真正执行比较的是 fp32：`Compare<float>` 的单 repeat lane 数是 `VECTOR_REG_WIDTH / sizeof(float)`。因此 `cn` 可达到 128，而一次 fp32 比较只覆盖 64 lane，lane 64–127 没有完成比较与状态更新。 机制链为： `X` 为 2-byte → 存储视角 `256B / 2B = 128 lane` → `Cast` 后比较类型为 4-byte → 比较视角 `256B / 4B = 64 lane` → 仍传 `cn=128` → 后 64 lane 未由该 Level-2 单 repeat 调用更新。

## 解决配方

分块宽度由“真正执行 `Compare` 的类型”决定，而不是由 GM/UB 存储类型决定。下列代码来自事件流中的真实写入；路径 `cummin.asc`，symbol `KernelCumminChunked<X>::Init`，范围均为完整函数。revision 为轨迹中的修复前/修复后工作树状态，固定 40 位 commit 未在轨迹中恢复。

### before

```cpp
__aicore__ inline void Init(GM_ADDR xGm, GM_ADDR yGm, GM_ADDR idxGm,
                            int64_t M, int64_t R, int64_t N, int64_t mBeg, int64_t mEnd)
{
    M_ = M; R_ = R; N_ = N; mBeg_ = mBeg; mEnd_ = mEnd;
    constexpr uint32_t dSize = sizeof(X);
    constexpr uint32_t nC = VECTOR_REG_WIDTH / dSize;
    nC_ = nC;
    uint32_t bN = nC;
    if (bN < (VECTOR_REG_WIDTH / sizeof(int32_t))) bN = VECTOR_REG_WIDTH / sizeof(int32_t);
    // cur (TQue: MTE2->V sync), outVal/outIdxI64 (TQue: V->MTE3 sync).
    pipe_.InitBuffer(curQue_, 2, bN * dSize);
    pipe_.InitBuffer(outValQue_, 2, bN * dSize);
    pipe_.InitBuffer(outIdxQue_, 2, bN * sizeof(int64_t));
    // V-only running/state buffers (in-order, no cross-pipe sync needed).
    pipe_.InitBuffer(runValBuf_, bN * dSize);
    pipe_.InitBuffer(runIdxBuf_, bN * sizeof(int32_t));
    pipe_.InitBuffer(maskBuf_, bN * sizeof(uint8_t));
    pipe_.InitBuffer(curIdxBuf_, bN * sizeof(int32_t));
    // b16 path: compare in fp32 (classic Compare<half/bf16,LT> misbehaves on
    // multi-chunk; fp32 Compare is reliable). curFp = cast(cur), runVFp = running fp32.
    pipe_.InitBuffer(curFpBuf_, bN * sizeof(float));
    pipe_.InitBuffer(runVFpBuf_, bN * sizeof(float));
    xGm_.SetGlobalBuffer((__gm__ X *)xGm);
    yGm_.SetGlobalBuffer((__gm__ X *)yGm);
    idxGm_.SetGlobalBuffer((__gm__ int64_t *)idxGm);
}
```

### after

```cpp
__aicore__ inline void Init(GM_ADDR xGm, GM_ADDR yGm, GM_ADDR idxGm,
                            int64_t M, int64_t R, int64_t N, int64_t mBeg, int64_t mEnd)
{
    M_ = M; R_ = R; N_ = N; mBeg_ = mBeg; mEnd_ = mEnd;
    constexpr uint32_t dSize = sizeof(X);
    // nC = one vector repeat of the COMPARE type. b16 compares in fp32 (Cast),
    // so its repeat is VECTOR_REG_WIDTH/sizeof(float)=64, NOT /sizeof(b16)=128.
    // 4-byte types also repeat at 64. So nC=64 for all dtypes.
    constexpr uint32_t nC = VECTOR_REG_WIDTH / sizeof(float);
    nC_ = nC;
    uint32_t bN = nC;
    if (bN < (VECTOR_REG_WIDTH / sizeof(int32_t))) bN = VECTOR_REG_WIDTH / sizeof(int32_t);
    // cur (TQue: MTE2->V sync), outVal/outIdxI64 (TQue: V->MTE3 sync).
    pipe_.InitBuffer(curQue_, 2, bN * dSize);
    pipe_.InitBuffer(outValQue_, 2, bN * dSize);
    pipe_.InitBuffer(outIdxQue_, 2, bN * sizeof(int64_t));
    // V-only running/state buffers (in-order, no cross-pipe sync needed).
    pipe_.InitBuffer(runValBuf_, bN * dSize);
    pipe_.InitBuffer(runIdxBuf_, bN * sizeof(int32_t));
    pipe_.InitBuffer(maskBuf_, bN * sizeof(uint8_t));
    pipe_.InitBuffer(curIdxBuf_, bN * sizeof(int32_t));
    // b16 path: compare in fp32 (classic Compare<half/bf16,LT> misbehaves on
    // multi-chunk; fp32 Compare is reliable). curFp = cast(cur), runVFp = running fp32.
    pipe_.InitBuffer(curFpBuf_, bN * sizeof(float));
    pipe_.InitBuffer(runVFpBuf_, bN * sizeof(float));
    xGm_.SetGlobalBuffer((__gm__ X *)xGm);
    yGm_.SetGlobalBuffer((__gm__ X *)yGm);
    idxGm_.SetGlobalBuffer((__gm__ int64_t *)idxGm);
}
```

## 设计决策

- 选择按比较类型分块，因为 `Compare` 才是决定有效 lane 数的指令；存储类型只决定搬运字节数；
- 放弃“按输入 dtype 尽量塞满一个 256B chunk”的方案，因为 `Cast` 后计算宽度已经改变；
- 当前方案属于 `recommended_fastpath`：它不引入额外 fallback，只把 chunk 边界对齐到真实计算 repeat。

## 系统信息

- toolchain：CANN 9.0.1；
- 目标平台：Ascend950PR / dav-3510；
- 相关文件：`cummin.asc`；
- 相关路径：GM/UB 以 2-byte 类型存储，比较路径提升到 fp32，索引状态为 int32。

## 预防

- 任何 `Cast<A,B>` 后接向量 API 的路径，都按 `B` 的 repeat lane 数计算分块；
- 用边界探针检查 `repeat-1`、`repeat`、`repeat+1` 三个位置，而不是只看整张量是否失败；
- 把 `storage_dtype`、`compute_dtype`、`compare_dtype` 分开记录，禁止只保留一个 `dtype` 推导所有 buffer 与 lane 数。

## 验证信号

该知识来自一次 Ascend950 前缀极值 kernel 的多块精度联调：先用干净构建复现边界 lane 错误，再修改分块宽度并重跑逐 lane 探针与全量测试。

- 修复前，2-byte 路径的 row0 正确，后续行从 lane 64 起出现稳定错误（950 / CANN 9.0.1，证据等级: tool_observed）；
- 修复后，同一探针所有行均无错误 lane，边界两侧与参考逐值一致（950 / CANN 9.0.1，证据等级: tool_observed）；
- 修复后 79 项上板测试全部通过（950 / CANN 9.0.1，证据等级: tool_observed）。

## 失效边界

- 结论依赖 Level-2 API 的单 repeat 行为；如果换成显式 repeat 循环或 API 能处理任意 count，应重新按接口契约判断；
- 其他平台注册平台未验证，推断可迁移但必须重新确认 `VECTOR_REG_WIDTH` 与 API repeat 语义；
- 不能把“64 lane”写死为跨平台常量，应保留 `VECTOR_REG_WIDTH / sizeof(compare_type)` 的表达。

## 坏实践

- 用 `sizeof(input_type)` 计算所有向量操作的 lane 数，即使中间已经提升 dtype；
- 只看 chunk 首部几个元素正确就认为整 repeat 正确；
- 把后半 lane 错误误诊为随机同步竞争而不先检查固定边界。

## 误诊

曾先怀疑 b16 `Compare` 本身不可靠以及跨 chunk 队列复用竞争；固定从 lane 64 开始的错误位置最终排除了随机竞争，指向比较类型 repeat 宽度。

<!-- cannbot:related:start -->
## 相关

- [Compares](../../apis/simd_api/basic_api/memory_vector_compute/compare_and_select/compares.md)（`exemplifies`）：《Compares》的任务是“逐元素比较一个tensor中的元素和另一个标量的大小，结果为真的对应比特位为1，否则为0。”。《b16 提升 fp32 比较后按存储宽度分块会漏掉后半 lane》具体提供“2-byte 数据提升为 fp32 比较时，分块宽度必须按比较类型的单 repeat lane 数计算，否则后半 lane 不更新。”，它直接用于Compares 生成标量比较 mask 并由 Select/SetCmpMask/GetCmpMask 消费的链路。
- [Select](../../apis/simd_api/basic_api/reg_vector_compute/mask_reg_compute/select.md)（`exemplifies`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《b16 提升 fp32 比较后按存储宽度分块会漏掉后半 lane》具体提供“2-byte 数据提升为 fp32 比较时，分块宽度必须按比较类型的单 repeat lane 数计算，否则后半 lane 不更新。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [bfloat16类型](../../apis/simt_api/math_functions/bfloat16_type/bfloat16_type.md)（`exemplifies`）：《bfloat16类型》说明bfloat16类型函数总入口，涵盖算术、比较、数学库及精度转换函数，并包含bfloat16x2类型对应函数。；《b16 提升 fp32 比较后按存储宽度分块会漏掉后半 lane》说明2-byte 数据提升为 fp32 比较时，分块宽度必须按比较类型的单 repeat lane 数计算，否则后半 lane 不更新。。二者在bfloat16类型入口的实际使用受全局类型命名、B16边界转换和提升后lane宽度约束，而非由平台或版本过滤上存在可执行的直接衔接。
- [B16 结果大幅偏差 — UNPACK 后补 Reg Cast](b16_unpack_requires_numeric_cast_before_fp32_compute.md)（`related`）：《B16 结果大幅偏差 — UNPACK 后补 Reg Cast》说明Reg 的 B16 UNPACK/PACK 只改变寄存器布局，不替代数值格式转换；显式使用预定义 CastParam trait 完成 B16↔fp32。；《b16 提升 fp32 比较后按存储宽度分块会漏掉后半 lane》说明2-byte 数据提升为 fp32 比较时，分块宽度必须按比较类型的单 repeat lane 数计算，否则后半 lane 不更新。。二者在B16 UNPACK/PACK只改变寄存器分布，显式Reg Cast才做数值转换；Cast trait、lane宽度和边界转换卡共同验证这条链上存在可执行的直接衔接。
- [FP16 算子 Cast 提升-计算-回退链设计](fp16_cast_up_fp32_compute_cast_down_chain.md)（`related`）：FP16 算子 Cast 提升-计算-回退链设计 与《b16 提升 fp32 比较后按存储宽度分块会漏掉后半 lane》的实质衔接是：FP16 提升到 FP32、VF 计算再 RINT 回退要求 Cast 模式、lane 宽、UB 容量和 MTE/Vector 同步一致；相关故障均命中这些步骤。
- [Reg int32→int64 Cast 源目 VL 错配留空索引](int32_to_int64_reg_cast_must_respect_destination_lane_width.md)（`related`）：int32→int64 Cast 同样证明循环步长必须按目标类型 lane 宽度重算，不能沿用源/存储类型的 VL 元素数。
- [b16 running 经 fp32 回转会改写 NaN payload](bit_exact_b16_nan_payload_needs_original_dtype_running_value.md)（`related`）：focal 的比较状态提升为 fp32，因此 chunk 宽度必须按 fp32 repeat 而不是 B16 存储宽度计算；否则后半 lane 不更新会伪装成 payload/索引问题。
- [半精度索引错位—拆分双 int32 掩码](b16_value_mask_must_split_for_two_int32_index_registers.md)（`related`）：若保留 B16 value 的 128-lane 比较域，索引侧必须拆成两组 64-lane mask；它与 focal 的统一 B32 计算是解决同一 lane 数不匹配的另一实现契约。
- [Ascend950 Reg 扫描按 256B 锁定 lane](dav3510_vector_register_width_is_256_bytes.md)（`same_topic`）：Ascend950 Reg 扫描按 256B 锁定 lane 与《b16 提升 fp32 比较后按存储宽度分块会漏掉后半 lane》的实质衔接是：这些卡共同约束 256B RegTensor 的 lane 数、B16/B32 提升后的 mask 宽度以及 LoadAlign/VF 调用范围；所连错例均由按错误数据宽度计算 lane 或目标 VL 导致。
- [B16 比较先升到 B32 锁定索引 lane](b16_value_and_b32_index_masks_need_common_b32_compute.md)（`same_topic`）：两卡共同要求比较计算提升到 fp32 后按 B32 的 64-lane 域组织 value、index 与 mask；否则仍按 B16 128-lane 分块会漏更新后半区。
- [模板内 float→float Cast 使 fp32 分支全错](templated_float_input_must_bypass_same_type_cast.md)（`same_topic`）：模板内 float→float Cast 使 fp32 分支全错 与《b16 提升 fp32 比较后按存储宽度分块会漏掉后半 lane》的实质衔接是：float 到 float 不应进入窄化 Cast，应该保持原值或 Copy；同步、BF16 分阶段、native 类型、VL、舍入与 RmsNorm 案例分别说明真正需要 Cast 时的类型、时序和验证契约。
<!-- cannbot:related:end -->
