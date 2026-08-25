---
type: "Runbook"
title: "嵌套 VF 循环触发 bisheng stack smashing ICE"
description: "Ascend950/arch35/CANN 9.1.0 下 __simd_vf__ 函数体内嵌套 while 循环调用 MicroAPI reg-compute 原语触发 bisheng INFERCHANNEL stack smashing ICE；扁平化为单层循环可消除。"
tags: ["task.debugging", "topic.compilation", "topic.programming_model.execution_model.simd"]
status: stable
sources: []
created_at: "2026-08-18T07:23:27Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
aliases: ["stack_smashing", "nested_loop"]
---

# 嵌套 VF 循环触发 bisheng stack smashing ICE

## 现象

在 ascend950 (dav-3510 / arch35, CANN 9.1.0) 平台用 regbase 范式（`__simd_vf__` 函数 + `asc_vf_call` 调用）实现一个逐元素类算子 kernel 时，`__simd_vf__` 函数体内采用**嵌套循环结构**：外层 `while (remaining > 0)` 逐行迭代，内含两个独立 `while` 子循环，分别在子循环体内调用 MicroAPI reg-compute 原语（`Duplicate` + `StoreAlign` 与 `LoadAlign` + `StoreAlign`）。`./build.sh <pkg>` 进入 ascend950 kernel 生成阶段时，**全 14 个 dtype 实例化同时触发编译器内部崩溃**（非用户代码语法错、无错误行号），原始报错（build 输出）：

```
[ERROR] TBE(2247995,python3):2026-08-05-14:00:48.689.086 [ascend950] Triu_409876e47e64104d68fa5963bdbef2d8 *** stack smashing detected ***: terminated
[ERROR] TBE(2248651,python3):2026-08-05-14:01:00.753.926 [op_compilation.py:311] Exception occured, An error occurred during compile phases of CompileStage.INFERCHANNEL, msg is *** stack smashing detected ***: terminated
```

`*** stack smashing detected ***: terminated` 是 bisheng/clang 前端进程自身的栈溢出崩溃（Internal Compiler Error），发生在 `CompileStage.INFERCHANNEL`（kernel 编译的通道推断步骤），所有 14 dtype 全部失败。

## 适用场景

- **工程形态**：kernel 直调（regbase 范式，`__simd_vf__` 函数经 `asc_vf_call` 调用，`op_kernel/arch35/*.h`）。
- **API 路径**：`__simd_vf__ inline` 函数体内 `while` 循环 + `AscendC::MicroAPI::Duplicate` / `LoadAlign` / `StoreAlign` / `UpdateMask` → bisheng 前端 `CompileStage.INFERCHANNEL` 阶段。
- **验证过的平台与 CANN 版本**：ascend950（DAV_3510 / arch35），CANN 9.1.0（bisheng clang 15.0.5）。与 frontmatter `platforms` 一致。
- **适用粒度**：`platform_wide`（该 CANN/架构下所有 regbase `__simd_vf__` kernel 均适用，与算子语义无关）。
- **路线优先级**：`recommended_fastpath`（扁平化是验证过的可编译解法，同 MicroAPI 调用集扁平后编译通过）。
- **明确不适用 / 未验证场景**：a2 / a3 平台未实测，推断可迁移（bisheng 前端行为应一致）但未验证，见 `## 失效边界`；本卡不覆盖 `AscendC::Reg::*`（Reg:: 命名空间）路线——该路线在本 CANN/架构下整条 banned，见相关既有卡。

## 判别方法

**trigger（触发信号）**：`./build.sh <pkg>` 在 ascend950 kernel 生成阶段对全 dtype 实例化同时报 `*** stack smashing detected ***: terminated`，定位在 `CompileStage.INFERCHANNEL`，无具体源码行号、无用户代码诊断信息（即编译器自身崩溃，非语法/类型错误）。

**probe（可执行判别）**：

1. 确认 ICE 而非普通编译错误：
   ```
   cd operators && ./build.sh <pkg> 2>&1 | grep -E 'stack smashing|INFERCHANNEL|error:|SUCCESS'
   ```
   只命中 `stack smashing ... INFERCHANNEL`、无 `error:` 行号信息 → 是编译器 ICE。

2. 结构判别——grep `__simd_vf__` 函数体内是否存在嵌套 `while`/`for` 且内层循环体含 MicroAPI reg-compute 原语调用：
   ```
   grep -rn "__simd_vf__\|AscendC::MicroAPI::\(Duplicate\|LoadAlign\|StoreAlign\)" operators/<pkg>/op_kernel/
   ```
   命中 `__simd_vf__` + 多层 `while` + 内层 `Duplicate`/`LoadAlign`/`StoreAlign` → 高度怀疑本判别规则。

3. 对照实验——将嵌套循环扁平化为**单层 `while` + 块内标量子循环**（标量子循环只做 mask 运算 `UpdateMask`/`Not`/`And`/`Or`，不含 MicroAPI reg-compute 调用），整块置零 + mask 构建 + 条件 `StoreAlign(keepMask)` 替代两个独立内循环，重新 build：
   ```
   cd operators && ./build.sh <pkg> 2>&1 | grep -E 'stack smashing|error:|SUCCESS'
   ```

**observation（原始观测，tool_observed）**：

- 嵌套版本（trigger pattern，verbatim 恢复自 raw source markdown）：

```cpp
template <typename T>
__simd_vf__ inline void TriuVF(__ubuf__ T* outUb, __ubuf__ T* selfUb,
                               uint32_t tileLen, uint64_t gmOffset,
                               uint64_t mn, uint64_t N, int64_t diagonal)
{
    constexpr uint32_t oneRepElm = GetVecLen() / sizeof(T);
    uint64_t ij0 = gmOffset % mn;
    uint64_t i = ij0 / N;
    uint64_t j = ij0 % N;

    uint32_t outOff = 0;
    uint32_t remaining = tileLen;

    // 逐行: derive start_col, prefix zero + suffix copy.
    while (remaining > 0) {
        int64_t startCol = static_cast<int64_t>(i) + diagonal;
        if (startCol < 0) { startCol = 0; }
        if (startCol > static_cast<int64_t>(N)) { startCol = static_cast<int64_t>(N); }
        uint64_t rowSeg = ((N - j) < static_cast<uint64_t>(remaining))
                              ? (N - j) : static_cast<uint64_t>(remaining);
        uint64_t zeroLen = (j < static_cast<uint64_t>(startCol))
                               ? (static_cast<uint64_t>(startCol) - j) : 0;
        uint64_t copyStart = (static_cast<uint64_t>(startCol) > j)
                                 ? static_cast<uint64_t>(startCol) : j;
        uint64_t copyEnd = j + rowSeg;
        uint64_t copyLen = (copyEnd > copyStart) ? (copyEnd - copyStart) : 0;

        // --- 前缀 Duplicate 零 (mask=0 分支) ---
        uint64_t zOff = 0;
        while (zOff < zeroLen) {
            uint32_t chunk = (zeroLen - zOff < oneRepElm)
                                 ? static_cast<uint32_t>(zeroLen - zOff)
                                 : oneRepElm;
            AscendC::MicroAPI::RegTensor<T> zeroReg;
            AscendC::MicroAPI::Duplicate<T>(zeroReg, static_cast<T>(0));
            uint32_t cnt = chunk;
            AscendC::MicroAPI::MaskReg preg =
                AscendC::MicroAPI::UpdateMask<T>(cnt);
            AscendC::MicroAPI::StoreAlign<T>(outUb + outOff + zOff, zeroReg, preg);
            zOff += chunk;
        }

        // --- 后缀 Copy self (mask=1 分支) ---
        uint64_t cBase = zeroLen;
        uint64_t cOff = 0;
        while (cOff < copyLen) {
            uint32_t chunk = (copyLen - cOff < oneRepElm)
                                 ? static_cast<uint32_t>(copyLen - cOff)
                                 : oneRepElm;
            AscendC::MicroAPI::RegTensor<T> selfReg;
            AscendC::MicroAPI::LoadAlign<T>(selfReg, selfUb + outOff + cBase + cOff);
            uint32_t cnt = chunk;
            AscendC::MicroAPI::MaskReg preg =
                AscendC::MicroAPI::UpdateMask<T>(cnt);
            AscendC::MicroAPI::StoreAlign<T>(outUb + outOff + cBase + cOff,
                                             selfReg, preg);
            cOff += chunk;
        }

        outOff += static_cast<uint32_t>(rowSeg);
        remaining -= static_cast<uint32_t>(rowSeg);
        j += rowSeg;
        if (j >= N) { j = 0; i++; }
    }
}
```

- 嵌套版本 build：全 14 dtype 报 `*** stack smashing detected ***: terminated` @ `CompileStage.INFERCHANNEL`（来源平台：950；证据等级：tool_observed，build 输出）。
- 扁平化版本 build：`stack smashing` 消失，`EXIT=0`、14 个 `.o` 产出（来源平台：950；证据等级：tool_observed）。

**interpretation（根因解释）**：bisheng/clang 前端在 `INFERCHANNEL` 通道推断步骤处理 `__simd_vf__` 函数内**嵌套控制流**（外层逐行 `while` + 内层逐块 `while` 子循环）时栈深度超限，导致编译器进程 `stack smashing` 崩溃。触发条件是"嵌套循环体 + MicroAPI reg-compute 原语调用链"的组合，而非任一具体 API：扁平化后同样的 `Duplicate` / `LoadAlign` / `StoreAlign` 调用编译通过，证明根因是控制流嵌套结构。仅含标量/mask 运算的子循环（无 MicroAPI reg-compute 调用）不触发 ICE。

## 验证信号

来源说明：本判别规则来自一次 ascend950 regbase 算子开发会话，嵌套循环版本全 dtype 触发 INFERCHANNEL stack smashing ICE，扁平化为单层循环 + mask 操作后同套 MicroAPI 调用编译通过。

- 嵌套版本 build：全 14 dtype `*** stack smashing detected ***: terminated` @ `CompileStage.INFERCHANNEL`（来源平台：950；证据等级：tool_observed）
- 扁平化版本 build：ICE 消除，`EXIT=0`，14 个 `.o` 产出（来源平台：950；证据等级：tool_observed）

## 失效边界

- a2 / a3 平台：未实测，推断可迁移（bisheng 前端行为预期一致）但未验证，不得据此刻入 frontmatter `platforms`。
- 标量子循环（mask 构建中的 `while(remaining>0)`，仅 `UpdateMask`/`Not`/`And`/`Or`）不含 MicroAPI reg-compute 原语调用，不触发 ICE；仅"嵌套循环 + 内层 reg-compute 原语"组合才触发。
- 更高 CANN 版本若修复 bisheng INFERCHANNEL 栈深度处理，可能解禁——未验证。
- 本卡不覆盖 `AscendC::Reg::*`（Reg:: 命名空间）路线，该路线在本 CANN/架构下整条 banned（exit 139 / exit 70），与本卡 MicroAPI 路线不同。

## 坏实践

- 在 `__simd_vf__` 函数内用嵌套 `while`/`for` 循环并在内层循环体调用 MicroAPI reg-compute 原语（`Duplicate`/`LoadAlign`/`StoreAlign`）——这是触发 ICE 的结构，应扁平化为单层循环。
- 用 `__simd_callee__` 辅助函数封装 `Duplicate` 再从主循环调用——同样构成 `asc_vf_call` → `__simd_vf__` → `__simd_callee__` + reg-compute 调用链，仍触发 ICE。
- 见到 `stack smashing` 无行号报错误以为是环境/工具链故障而重装 CANN——实则是源码控制流嵌套结构触发编译器栈溢出。

## 误诊

- 初始怀疑 ICE 由 `reinterpret_cast<RegTensor<T>&>(zeroReg)`（double 分支）触发：移除 double 分支后全 14 dtype 仍 ICE，证明 `reinterpret_cast` 非根因（来源平台：950；证据等级：tool_observed，build 输出）。
- 初始怀疑 `Duplicate` 本身触发 ICE：扁平化后同样的 `Duplicate` 调用编译通过，证明根因是嵌套循环结构而非具体 API（来源平台：950；证据等级：tool_observed）。

<!-- cannbot:related:start -->
## 相关

- [VF调用](../../apis/simd_api/basic_api/reg_vector_compute/vf_call/vf_call.md)（`exemplifies`）：嵌套 VF 循环触发编译器 stack smashing，给出复杂循环结构在 __simd_vf__ 后端 lowering 中的失败信号。
- [AR 跨块循环放在 __simd_vf__ 只执行首块](../precision/simd_vf_chunk_loop_must_be_driven_by_aicore_wrapper.md)（`related`）：两卡都要求把跨 chunk/row 循环移到 __aicore__ wrapper：focal 为避免 INFERCHANNEL 嵌套循环 ICE，目标卡为避免单次 VF 只执行首块，分别覆盖编译与运行边界。
- [RegBase VF __simd_vf__ 路线致 bisheng 编译崩溃](regbase_vf_simd_vf_bisheng_exit139_banned.md)（`related`）：focal 明确只覆盖 MicroAPI 嵌套控制流且扁平后可编译；目标卡覆盖 AscendC::Reg::* 路线本身的 exit139/70。先识别命名空间可决定是扁平化还是换 API 路线。
- [__simd_vf__ if constexpr 致 hoisted 报错](simd_vf_if_constexpr_lowering_banned_exit_70.md)（`related`）：《__simd_vf__ if constexpr 致 hoisted 报错》说明dav-3510 上某 Reg __simd_vf__ 实现使用 if constexpr 与 constexpr trait 时，bisheng 后端报 Unsupported Inst must be hoisted 并退出 70；记录源码定位与编译边界，不提供未完成的 fallback 实现。；《嵌套 VF 循环触发 bisheng stack smashing ICE》说明Ascend950/arch35/CANN 9.1.0 下 __simd_vf__ 函数体内嵌套 while 循环调用 MicroAPI reg-compute 原语触发 bisheng INFERCHANNEL stack smashing ICE；扁平化为单层循环可消除。。二者在该编译失败锁定__simd_vf__中的if constexpr/trait lowering，同类模板隔离、helper/VF边界与后端崩溃用于交叉验证上存在可执行的直接衔接。
- [arch35 __aicore__ 调 LocalMemBar 报 507035](arch35_aicore_localmembar_507035.md)（`related`）：《arch35 __aicore__ 调 LocalMemBar 报 507035》处理“Ascend950PR (arch35/dav_c310) 上 Reg::LocalMemBar<VEC_STORE,VEC_LOAD> 是 __simd_callee__ 函数，须在 __simd_vf__ (VF) 调用上下文内使用；从常规 __aicore__ kernel 函数直接调用触发运行时 507035 (AIV 错误)。本 trace 两次独立调用（旧 4-buffer 代码、新 5-buffer 重排代码）均 507035。作为 count-based Compare→Select mask 隐患的最小 sync 修复手段 banned。”。《嵌套 VF 循环触发 bisheng stack smashing ICE》明确提供“Ascend950/arch35/CANN 9.1.0 下 __simd_vf__ 函数体内嵌套 while 循环调用 MicroAPI reg-compute 原语触发 bisheng INFERCHANNEL stack smashing ICE；扁平化为单层循环可消除。”，其参数、调用或验证步骤直接接入LocalMemBar 507035 的 Compare/Select 调用触发、屏障约束和可执行替代。
- [simd_vf 互调导致 helper 编译失败](simd_vf_helpers_use_simd_callee.md)（`related`）：simd_vf 互调导致 helper 编译失败 与《嵌套 VF 循环触发 bisheng stack smashing ICE》的实质衔接是：顶层 __simd_vf__ 只能调用 __simd_callee__ helper；asc_vf_call、执行限定符、kernel/VF 指南和相邻 VF 编译故障共同固定三层调用结构。
<!-- cannbot:related:end -->
