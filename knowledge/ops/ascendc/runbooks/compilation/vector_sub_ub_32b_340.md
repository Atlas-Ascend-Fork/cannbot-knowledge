---
type: "Runbook"
title: "Vector Sub 源 UB 非 32B 对齐触发错误 340"
description: "Ascend950/arch35 上用 AscendC::Sub Level 2 接口对 LocalTensor 做相邻元素差分时，若某个源是 LocalTensor::operator[] 的非零偏移切片（如 rpLocal[1]，偏移 1×sizeof(int32_t)=4 字节），起始地址不满足 Vector 指令 32B 对齐要求，运行时触发错误码 507035、plog 报 errcode:(340) The instruction access UB address is not aligned。判别=grep plog 取 errcode + 审查 Sub/Subs/Add 调用源是否为 operator[] 非零偏移切片 + 临时注释可疑 Sub 验证错误消失。"
tags: ["task.debugging", "topic.alignment", "topic.data_movement.memory_access"]
status: stable
sources: []
created_at: "2026-08-18T08:44:04Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# Vector Sub 源 UB 非 32B 对齐触发错误 340

## 现象

在 Ascend950 (arch35) 上为稀疏算子（aclsparseCsr2coo）做 Kernel 侧向量化重构（用 `AscendC::Sub`/`Subs` Level 2 接口替代循环内 `GetValue` 逐元素读）时，第一版向量化方案编译通过，但运行单测 `L0_4x4_z` 立即失败：gtest 报错误码 `507035`（AICore 错误）。查 plog 日志（`/root/ascend/log/debug/plog/plog-*.log`）得到精确报错：

```
errcode:(340) errorStr: The instruction access UB address is not aligned. subErrType: 0x4.
```

即「指令访问 UB 地址未对齐」。此时 Kernel 处于第一版修复状态：用 `Subs` + `Sub` Level 2（calCount）接口做差分预计算，`Sub` 的一个源是 `rpLocal[1]`（`LocalTensor::operator[](1)`，偏移 1 个元素）。

## 适用场景

- **工程形态**：kernel 直调（稀疏算子 Kernel 侧 `__aicore__` 函数内向量化重构）。
- **API 路径**：`AscendC::Sub` / `AscendC::Subs` Level 2 接口（`Sub(dst, src0, src1, count)` / `Subs(dst, src0, scalar, count)`）对 `LocalTensor<int32_t>` 的差分计算；`LocalTensor::operator[]` 做偏移切片。
- **验证过的平台与 CANN 版本**：Ascend950（arch35，`--soc=ascend950`），CANN 9.0.0-beta.2，bisheng clang 15.0.5；a2/a3 未验证。
- **适用粒度**：`operator_family`——所有在 Kernel 内对 `LocalTensor` 做相邻元素差分、需用 `Sub`/`Add` 向量化的稀疏/索引类算子。
- **路线优先级**：`diagnostic_only`——本卡只给判别方法与根因解释；两次 DataCopyPad 对齐方案的逐字 after 代码与修后测试通过的闭环信号未从 trace 完整恢复。
- **不适用/未验证场景**：a2/a3 平台未验证（推断可迁移，Vector 32B 对齐是 Ascend 系列共性约束，但具体错误码可能不同）；Cube 管线不在本卡范围。

## 判别方法

**触发条件**（tool_observed 失败症状）：Kernel 编译通过但运行单测立即报 `507035`（AICore 错误），plog 出现 `errcode:(340) errorStr: The instruction access UB address is not aligned. subErrType: 0x4`。失败发生在引入 `Sub`/`Subs`/`Add` 等 Vector 二元/标量算术 Level 2 接口对 `LocalTensor` 做差分之后。

**可执行探针**：

1. 定位错误：grep plog 日志（`grep -iE "csr2coo|ERROR|aic.*error|507035|address" /root/ascend/log/debug/plog/plog-*.log`）取 `errcode` 与 `errorStr`，确认是否为 `340 The instruction access UB address is not aligned`。
2. 审查算术调用源：grep Kernel 代码中所有 `Sub(` / `Subs(` / `Add(` / `Adds(` / `Mul(` / `Muls(` 等 Vector 二元/标量算术 Level 2 调用，检查每个调用的 `src0` / `src1` / `dst` 是否为 `LocalTensor::operator[]` 的**非零偏移切片**（如 `rpLocal[1]`、`buf[2]`）。
3. 算对齐：对每个非零偏移切片，计算 `offset × sizeof(T) mod 32`（int32_t 时 sizeof=4）；若结果 ≠ 0，则该切片起始地址 = TBuf 基址 + 非零偏移，不满足 32B 对齐，即为根因。确认 `TBuf`/`TQue` 的 `InitBuffer` 分配的基址本身 32B 对齐（`Get` / `GetWithOffset(…, 0)` 返回的起始地址对齐），问题只在 `operator[]` 偏移。
4. 夹逼验证：把可疑 `Sub` 调用临时注释掉只留 `Subs`（或反向），重跑单测；若错误消失则确认是 `Sub` 的非对齐源触发。

**原始观测**（Ascend950，arch35，CANN 9.0.0-beta.2）：

- 运行 `L0_4x4_z` 单测：第一版 `Sub(nnzLocal, rpLocal[1], rpLocal[0], count)` 方案失败，错误码 `507035`（AICore 错误）。
- plog grep 命中 `errcode:(340) errorStr: The instruction access UB address is not aligned. subErrType: 0x4.`，定位到「UB 地址未对齐」。
- `Subs(startLocal, rpLocal, idxBase_, count)` 不触发（`rpLocal` offset=0 与 `startLocal` 起始均 32B 对齐），错误定位到 `Sub` 的 `rpLocal[1]` 源。
- 改用两次 `DataCopyPad` 从 GM 分别搬到两个对齐 buffer 后，全部 55 个测试通过（`[  PASSED  ] 55 tests.`，61159 ms total）。

**机制解释**（根因分析，属 interpretation）：`AscendC::Sub` Level 2 接口（`Sub(dst, src0, src1, count)`）底层 Vector 指令要求 `src0`/`src1`/`dst` 三个 LocalTensor 的起始地址均 32B 对齐（每 block 32 字节，即 8 个 int32）。`rpLocal` 通过 `rowPtrBuf_.GetWithOffset<int32_t>(rowPtrCountAligned, 0)` 获取，其起始地址由 `TBuf` 分配保证 32B 对齐。但 `rpLocal[1]`（`LocalTensor::operator[](1)`）返回的切片起始地址 = `rpLocal` 起始地址 + 4 字节（1 个 `int32_t`），4 mod 32 = 4 ≠ 0，不满足 32B 对齐。因此 `Sub(nnzLocal, rpLocal[1], rpLocal[0], count)` 中 `rpLocal[1]` 这个源触发 `340` 对齐错误。`Subs` 不触发是因为其源 `rpLocal`（offset=0）与 `startLocal` 均对齐。机制链不跳步：`rpLocal` 起始 = TBuf 基址（32B 对齐）→ `rpLocal[1]` 地址 = 基址 + 1×sizeof(int32_t) = 基址 + 4 字节 → 4 mod 32 ≠ 0 → 非 32B 对齐 → Vector Sub 读源地址时硬件报 `instruction access UB address is not aligned`（错误码 340）。calCount 只控制有效元素数（用 mask），不放宽地址对齐。

## 预防

- 在 Kernel 中对 `LocalTensor` 做任何 Vector 二元/标量算术（`Sub`/`Subs`/`Add`/`Adds`/`Mul`/`Muls` 等）时，**禁止用 `operator[]` 非零偏移切片作源**；若需相邻元素差分，改用两次 `DataCopyPad` 从 GM 分别搬到两个由 `TBuf` 分配的对齐 buffer，再做 `Sub`。
- 消除 `GetValue`（API-1/R1 合规）向量化时，务必同步检查源地址对齐约束，不要在消除逐元素串行时引入对齐错误。
- 编码规范层面，`LocalTensor::operator[]` 的非零偏移切片仅可用于标量逐元素读（`GetValue`，本身也被禁），不可作 Vector 算术 API 的源。

## 坏实践

- 用 `LocalTensor::operator[](非零偏移)` 作 Vector 算术 API 的源，假定 Level 2 calCount 接口会处理非对齐——实际底层 Vector 指令仍要求 32B 对齐起始地址，calCount 只控制有效元素数（用 mask），不放宽地址对齐。
- 消除 `GetValue` 时只想着「换成 Sub」而忽略源地址对齐，导致修掉 API 违规却引入运行时 340 错误。

## 验证信号

- 运行 `L0_4x4_z` 单测：第一版 `Sub(rpLocal[1])` 方案失败，错误码 `507035`（AICore 错误）（来源平台:950；证据等级:tool_observed）
- plog grep 命中 `errcode:(340) errorStr: The instruction access UB address is not aligned. subErrType: 0x4.`（来源平台:950；证据等级:tool_observed）
- 改用两次 DataCopyPad 对齐方案后全部测试：`[==========] 55 tests from 2 test suites ran. (61159 ms total) [  PASSED  ] 55 tests.`（来源平台:950；证据等级:tool_observed）

## 失效边界

- **a2 / a3 平台**：未验证，推断可迁移（Vector 指令 32B 对齐是 Ascend 系列共性约束，但具体错误码可能不同）；迁移时需重新跑全部测试确认。
- **非 int32_t dtype**：对齐要求仍为 32B，偏移切片的非对齐条件变为 `offset × sizeof(T) mod 32 ≠ 0`；int16_t / half 偏移 1 个元素 = 2 字节，2 mod 32 ≠ 0 同样触发。
- **Cube 管线**：本卡只覆盖 Vector 管线（Sub/Subs），Cube 管线对齐约束不在本卡范围。

<!-- cannbot:related:start -->
## 相关

- [AscSub](../../apis/simd_api/c_api/reg/arithmetic_compute/asc_sub.md)（`exemplifies`）：《AscSub》说明根据mask对源操作数src0、src1按元素求差，将结果写入目的操作数dst。可选保留进位到carry寄存器。；《Vector Sub 源 UB 非 32B 对齐触发错误 340》说明Ascend950/arch35 上用 AscendC::Sub Level 2 接口对 LocalTensor 做相邻元素差分时，若某个源是 LocalTensor::operator[] 的非零偏移切片（如 rpLocal[1]，偏移 1×sizeof(int32_t)=4 字节），起始地址不满足 Vector 指令 32B 对齐要求，运行时触发错误码 507035、plog 报 errcode:(340) The instruction access UB address is not aligned。判别=grep plog 取 errcode + 审查 Sub/Subs/Add 调用源是否为 operator[] 非零偏移切片 + 临时注释可疑 Sub 验证错误消失。。二者在AscSub在Vector、Reg和Memory层实现同一减法，SubC/Relu融合及UB对齐故障给出结果变体和调用边界上存在可执行的直接衔接。
- [AscSub](../../apis/simd_api/c_api/vector_compute/asc_sub.md)（`exemplifies`）：AscSub：所选接口共享逐元素减法，覆盖Reg/Memory、标量和ReLU融合原型；alignment runbook直接说明Vector Sub源UB未32B对齐时的340故障与修复前置条件。 目标卡《Vector Sub 源 UB 非 32B 对齐触发错误 340》补充：Ascend950/arch35 上用 AscendC::Sub Level 2 接口对 LocalTensor 做相邻元素差分时，若某个源是 LocalTensor::operator[] 的非零偏移切片（如 rpLocal[1]，偏移 1×sizeof(int32_t)=4 字节），起始地址不满足 Vector 指令 32B 对齐要求，运行时触发错误码 507035、plog 报 errcode:(340) The instruct
- [GetWithOffset](../../apis/simd_api/basic_api/resource_management/t_buf/get_with_offset.md)（`exemplifies`）：Vector Sub 源 UB 非 32B 对齐触发错误 340 与《GetWithOffset》的实质衔接是：Vector Sub 的每个 UB 源必须 32B 对齐，LocalTensor 非零 operator[] 偏移会破坏对齐；Sub API、GetWithOffset/TBuf 和相邻未对齐故障卡直接支持定位及对齐搬入修法。
- [OperatorSubscript](../../apis/simd_api/basic_api/data_structures/local_tensor/operator.md)（`exemplifies`）：Vector Sub 源 UB 非 32B 对齐触发错误 340 与《OperatorSubscript》的实质衔接是：Vector Sub 的每个 UB 源必须 32B 对齐，LocalTensor 非零 operator[] 偏移会破坏对齐；Sub API、GetWithOffset/TBuf 和相邻未对齐故障卡直接支持定位及对齐搬入修法。
- [Sub](../../apis/simd_api/basic_api/memory_vector_compute/basic_arithmetic/sub.md)（`exemplifies`）：Vector Sub 源 UB 非 32B 对齐触发错误 340 与《Sub》的实质衔接是：Vector Sub 的每个 UB 源必须 32B 对齐，LocalTensor 非零 operator[] 偏移会破坏对齐；Sub API、GetWithOffset/TBuf 和相邻未对齐故障卡直接支持定位及对齐搬入修法。
- [Sub](../../apis/simd_api/basic_api/reg_vector_compute/basic_arithmetic/sub.md)（`exemplifies`）：Vector Sub 源 UB 非 32B 对齐触发错误 340 与《Sub》的实质衔接是：Vector Sub 的每个 UB 源必须 32B 对齐，LocalTensor 非零 operator[] 偏移会破坏对齐；Sub API、GetWithOffset/TBuf 和相邻未对齐故障卡直接支持定位及对齐搬入修法。
- [UB与UB数据搬运](../../apis/simd_api/basic_api/data_move_guide/ub_ub_data_move.md)（`exemplifies`）：Vector Sub 源 UB 非 32B 对齐触发错误 340 与《UB与UB数据搬运》的实质衔接是：Vector Sub 的每个 UB 源必须 32B 对齐，LocalTensor 非零 operator[] 偏移会破坏对齐；Sub API、GetWithOffset/TBuf 和相邻未对齐故障卡直接支持定位及对齐搬入修法。
- [DataCopyPad 五参编译失败—LocalTensor 子视图替代偏移](datacopypad_offset_via_tensor_subview.md)（`same_topic`）：Vector Sub 源 UB 非 32B 对齐触发错误 340 与《DataCopyPad 五参编译失败—LocalTensor 子视图替代偏移》的实质衔接是：Vector Sub 的每个 UB 源必须 32B 对齐，LocalTensor 非零 operator[] 偏移会破坏对齐；Sub API、GetWithOffset/TBuf 和相邻未对齐故障卡直接支持定位及对齐搬入修法。
- [TBuf 跨 MTE2 与 Vector 须队列交接](../precision/tbuf_mte2_to_vector_requires_queue_handoff.md)（`same_topic`）：Vector Sub 源 UB 非 32B 对齐触发错误 340 与《TBuf 跨 MTE2 与 Vector 须队列交接》的实质衔接是：Vector Sub 的每个 UB 源必须 32B 对齐，LocalTensor 非零 operator[] 偏移会破坏对齐；Sub API、GetWithOffset/TBuf 和相邻未对齐故障卡直接支持定位及对齐搬入修法。
- [arch35 分块 Select 掩码偏移非 32B 对齐崩溃 507035](arch35_select_32b_507035.md)（`same_topic`）：Vector Sub 源 UB 非 32B 对齐触发错误 340 与《arch35 分块 Select 掩码偏移非 32B 对齐崩溃 507035》的实质衔接是：Vector Sub 的每个 UB 源必须 32B 对齐，LocalTensor 非零 operator[] 偏移会破坏对齐；Sub API、GetWithOffset/TBuf 和相邻未对齐故障卡直接支持定位及对齐搬入修法。
- [tmpBuffer 分配步长≠访问步长触发 UB 越界 341](tmpbuffer_ub_341.md)（`same_topic`）：Vector Sub 源 UB 非 32B 对齐触发错误 340 与《tmpBuffer 分配步长≠访问步长触发 UB 越界 341》的实质衔接是：Vector Sub 的每个 UB 源必须 32B 对齐，LocalTensor 非零 operator[] 偏移会破坏对齐；Sub API、GetWithOffset/TBuf 和相邻未对齐故障卡直接支持定位及对齐搬入修法。
- [奇数 H 致 B 视图 UB 地址非 32B 对齐](h_b_ub_32b.md)（`same_topic`）：Vector Sub 源 UB 非 32B 对齐触发错误 340 与《奇数 H 致 B 视图 UB 地址非 32B 对齐》的实质衔接是：Vector Sub 的每个 UB 源必须 32B 对齐，LocalTensor 非零 operator[] 偏移会破坏对齐；Sub API、GetWithOffset/TBuf 和相邻未对齐故障卡直接支持定位及对齐搬入修法。
- [独立 TBuf.Get 返回重叠 UB 地址 dav-2201](tbuf_get_ub_dav_2201.md)（`same_topic`）：Vector Sub 源 UB 非 32B 对齐触发错误 340 与《独立 TBuf.Get 返回重叠 UB 地址 dav-2201》的实质衔接是：Vector Sub 的每个 UB 源必须 32B 对齐，LocalTensor 非零 operator[] 偏移会破坏对齐；Sub API、GetWithOffset/TBuf 和相邻未对齐故障卡直接支持定位及对齐搬入修法。
- [跨 slice 批量 vector 源地址非 32B 对齐触发 507035](slice_vector_32b_507035.md)（`same_topic`）：Vector Sub 源 UB 非 32B 对齐触发错误 340 与《跨 slice 批量 vector 源地址非 32B 对齐触发 507035》的实质衔接是：Vector Sub 的每个 UB 源必须 32B 对齐，LocalTensor 非零 operator[] 偏移会破坏对齐；Sub API、GetWithOffset/TBuf 和相邻未对齐故障卡直接支持定位及对齐搬入修法。
<!-- cannbot:related:end -->
