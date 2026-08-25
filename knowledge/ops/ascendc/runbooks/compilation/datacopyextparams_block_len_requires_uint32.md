---
type: "Runbook"
title: "DataCopyExtParams blockLen 窄化编译失败"
description: "DataCopyExtParams 的 blockLen 接收 uint32_t，模板表达式 D* sizeof(T) 须显式窄化后再做 DataCopyPad。"
tags: ["task.debugging", "topic.data_movement.data_copy", "topic.implementation"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# DataCopyExtParams blockLen 窄化编译失败

## 现象

在 Ascend950 `dav-3510` 的 Flash 单文件算子工程中构建 `rms_norm.asc` 时，Kernel 的 `Process`、`CopyIn`、`CopyOut` 都用 `D_ * sizeof(T)` 初始化 `AscendC::DataCopyExtParams::blockLen`。Bisheng 在实例化 `KernelRmsNorm<half>` 时对三处分别报出：

```text
error: non-constant-expression cannot be narrowed from type 'unsigned long'
to 'uint32_t' (aka 'unsigned int') in initializer list [-Wc++11-narrowing]
```

这不是 DataCopyPad 的对齐或 stride 故障；构建在 C++ 列表初始化阶段即失败，尚未生成可运行 Kernel。

## 适用场景

- 工程形态：Ascend950 Flash / Kernel 直调单文件工程的 ASC 编译；
- API 路径：`AscendC::DataCopyExtParams` → `AscendC::DataCopyPad`，模板 Kernel 以元素数乘 `sizeof(T)` 计算字节长度；
- 验证过的平台与 CANN 版本：950 / CANN 9.0.1；
- 适用粒度：`operator_family`，适用于任意模板化 AscendC 搬运函数用运行期元素数计算 `blockLen` 的场景；
- 路线优先级：`recommended_fastpath`，在构造参数边界显式转换为 API 的精确字段类型；
- 明确不适用：数值无法证明落入 `uint32_t` 的超大搬运量；这种情况不能只靠强转，必须先做范围检查或拆分搬运。

## 根因

DataCopyExtParams::blockLen 是 uint32_t；D*sizeof(T) 提升为 size_t/unsigned long，列表初始化禁止隐式窄化。

## 解决配方

在 `DataCopyExtParams` 的构造边界把字节数显式转换为 `uint32_t`；三个调用点属于同一根因，必须一致修改。以下代码均 verbatim 恢复自 trace。

### before

revision：`35f5c62`（trace 中可见的初始实现短 revision）；path：`operators/rms_norm/rms_norm.asc`；symbols/line ranges：`KernelRmsNorm<T>::Process` 189–209、`CopyIn` 212–222、`CopyOut` 233–241；支撑结论：三处 `blockLen` 都由 `size_t` 表达式隐式初始化。

```cpp
    __aicore__ inline void Process()
    {
        AscendC::DataCopyExtParams gCopy{1, D_ * sizeof(T), 0, 0, 0};
        AscendC::DataCopyPadExtParams<T> gPad{false, 0, 0, 0};
        auto gammaLocal = gammaQueue_.AllocTensor<T>();
        AscendC::DataCopyPad(gammaLocal, gammaGm_, gCopy, gPad);
        gammaQueue_.EnQue(gammaLocal);
        auto gammaT = gammaQueue_.DeQue<T>(); // persistent across tiles

        for (uint32_t t = 0; t < numTiles_; ++t) {
            uint32_t mTcur = mT_;
            if (t + 1 == numTiles_) {
                mTcur = rowCount_ - t * mT_; // last partial tile
            }
            uint32_t rowBase = t * mT_;
            CopyIn(rowBase, mTcur);
            Compute(mTcur, gammaT);
            CopyOut(rowBase, mTcur);
        }
        gammaQueue_.FreeTensor(gammaT);
    }

    __aicore__ inline void CopyIn(uint32_t rowBase, uint32_t mTcur)
    {
        AscendC::DataCopyExtParams copy{1, D_ * sizeof(T), 0, 0, 0};
        AscendC::DataCopyPadExtParams<T> pad{false, 0, 0, 0};
        auto xLocal = inQueueX_.AllocTensor<T>();
        // ACC-003: per-row DataCopyPad, placed at UB offset r*dAlign (32B-aligned).
        for (uint32_t r = 0; r < mTcur; ++r) {
            AscendC::DataCopyPad(xLocal[r * dAlign_], xGm_[(rowBase + r) * D_], copy, pad);
        }
        inQueueX_.EnQue(xLocal);
    }

    __aicore__ inline void CopyOut(uint32_t rowBase, uint32_t mTcur)
    {
        AscendC::DataCopyExtParams copy{1, D_ * sizeof(T), 0, 0, 0};
        auto yLocal = outQueueY_.DeQue<T>();
        for (uint32_t r = 0; r < mTcur; ++r) {
            AscendC::DataCopyPad(yGm_[(rowBase + r) * D_], yLocal[r * dAlign_], copy);
        }
        outQueueY_.FreeTensor(yLocal);
    }
```

### after

revision：构建修复工作树状态（trace 未返回该汇总提交的 40 位 SHA）；path：`operators/rms_norm/rms_norm.asc`；symbols/line ranges：`KernelRmsNorm<T>::Process` 189–209、`CopyIn` 212–222、`CopyOut` 233–241；支撑结论：API 边界的显式类型转换消除三处窄化。

```cpp
    __aicore__ inline void Process()
    {
        AscendC::DataCopyExtParams gCopy{1, static_cast<uint32_t>(D_ * sizeof(T)), 0, 0, 0};
        AscendC::DataCopyPadExtParams<T> gPad{false, 0, 0, 0};
        auto gammaLocal = gammaQueue_.AllocTensor<T>();
        AscendC::DataCopyPad(gammaLocal, gammaGm_, gCopy, gPad);
        gammaQueue_.EnQue(gammaLocal);
        auto gammaT = gammaQueue_.DeQue<T>(); // persistent across tiles

        for (uint32_t t = 0; t < numTiles_; ++t) {
            uint32_t mTcur = mT_;
            if (t + 1 == numTiles_) {
                mTcur = rowCount_ - t * mT_; // last partial tile
            }
            uint32_t rowBase = t * mT_;
            CopyIn(rowBase, mTcur);
            Compute(mTcur, gammaT);
            CopyOut(rowBase, mTcur);
        }
        gammaQueue_.FreeTensor(gammaT);
    }

    __aicore__ inline void CopyIn(uint32_t rowBase, uint32_t mTcur)
    {
        AscendC::DataCopyExtParams copy{1, static_cast<uint32_t>(D_ * sizeof(T)), 0, 0, 0};
        AscendC::DataCopyPadExtParams<T> pad{false, 0, 0, 0};
        auto xLocal = inQueueX_.AllocTensor<T>();
        // ACC-003: per-row DataCopyPad, placed at UB offset r*dAlign (32B-aligned).
        for (uint32_t r = 0; r < mTcur; ++r) {
            AscendC::DataCopyPad(xLocal[r * dAlign_], xGm_[(rowBase + r) * D_], copy, pad);
        }
        inQueueX_.EnQue(xLocal);
    }

    __aicore__ inline void CopyOut(uint32_t rowBase, uint32_t mTcur)
    {
        AscendC::DataCopyExtParams copy{1, static_cast<uint32_t>(D_ * sizeof(T)), 0, 0, 0};
        auto yLocal = outQueueY_.DeQue<T>();
        for (uint32_t r = 0; r < mTcur; ++r) {
            AscendC::DataCopyPad(yGm_[(rowBase + r) * D_], yLocal[r * dAlign_], copy);
        }
        outQueueY_.FreeTensor(yLocal);
    }
```

## 设计决策

- 选择在 `DataCopyExtParams` 构造边界转换，而不把 `D_` 改成 `size_t`：`D_` 同时参与 Kernel 索引和 mask 计算，扩大其类型会把影响扩散到更多接口；
- 三处相同表达式一次性修复，避免 gamma、输入、输出搬运在不同模板实例化路径上重复暴露同一错误；
- 当前方案是 `recommended_fastpath`；若搬运字节数可能超过 `UINT32_MAX`，应改成范围检查与多次搬运，而不是继续采用该强转。

## 系统信息

- 工具链：CANN 9.0.1，Bisheng ASC 编译器；
- 目标：Ascend950PR / `dav-3510`；
- 相关文件：`operators/rms_norm/rms_norm.asc`；
- 相关 API：`DataCopyExtParams`、`DataCopyPadExtParams`、`DataCopyPad`。

## 预防

- 用花括号初始化 AscendC 参数结构体时，逐字段核对 SDK 声明的整数宽度；
- 含 `sizeof` 的表达式默认按 `size_t` 传播，传入 32 位字段前先做上界验证并显式转换；
- 模板 Kernel 至少实例化一种 16 位 dtype，让 `sizeof(T)` 参与的窄化在构建阶段暴露。

## 验证信号

来源说明：该结论来自 Ascend950 Flash 算子的远端 CANN 9.0.1 构建；初始构建对三个符号给出同类窄化诊断，精确替换后下一次构建不再出现该诊断，并继续推进到后续独立错误。

- 三处 `non-constant-expression cannot be narrowed ... to uint32_t` 诊断在修复后的下一轮构建中消失（来源平台：950；证据等级: tool_observed）。
- 完成其余独立构建修复后，`libop_rms_norm.so` 显示 `[100%] Built target op_rms_norm`（来源平台：950；证据等级: tool_observed）。

## 失效边界

- 显式转换只在已证明字节数不超过 `uint32_t` 时正确；超大连续搬运应拆分；
- 其他版本若 `DataCopyExtParams::blockLen` 字段宽度变化，须以目标 SDK 头文件为准；
- A2/A3 未在本轨迹验证，不能由本卡推断其编译器诊断完全相同。

## 坏实践

- 把诊断当作“编译器过严”并关闭 narrowing 检查：这会掩盖参数截断风险；
- 只修复其中一个 DataCopyPad 路径：其他 dtype 或搬运方向仍会在模板实例化时失败。

## 误诊

该错误发生在列表初始化类型检查阶段，与 32B DMA 对齐、`srcStride`/`dstStride` 或运行时越界无关；先查字段类型，不要先改搬运布局。

<!-- cannbot:related:start -->
## 相关

- [DataCopy](../../apis/simd_api/basic_api/memory_vector_compute/data_move/data_copy_gm_and_ub_highdim_split.md)（`exemplifies`）：DataCopy 与《DataCopyExtParams blockLen 窄化编译失败》的实质衔接是：该 DataCopy 用 DataCopyParams 做 GM/UB 高维切分；slice/continuous 对照、高维 API 分类和 blockLen 窄化故障共同说明何时选用及参数类型边界。
- [DataCopyPad](../../apis/simd_api/basic_api/memory_vector_compute/data_move/data_copy_pad_ub_to_gm.md)（`exemplifies`）：该案例补充 blockLen 必须保持 uint32_t，和 blockCount 的窄类型形成逐字段初始化约束。
- [DataCopyPad rightPad 字段为 uint8_t](datacopypad_rightpad_uint8_t.md)（`related`）：DataCopyExtParams blockLen 窄化编译失败 与《DataCopyPad rightPad 字段为 uint8_t》的实质衔接是：本故障和 blockCount/rightPad 卡都发生在 AscendC 参数结构体列表初始化的精确整数宽度不匹配；DataCopyPad 是 DataCopyExtParams 的直接消费接口，其他 stride、对齐或队列故障不是同一编译根因。
- [DataCopy尾chunk非32B对齐触发ERR99999](datacopy_chunk_32b_err99999.md)（`related`）：《DataCopy尾chunk非32B对齐触发ERR99999》说明Ascend C DataCopy 在 UB↔GM 方向要求 count*sizeof(T) 为 32 字节对齐，否则搬运量对 32B 向下取整。当纯搬运算子尾 chunk 的实际元素数不满足 32B 对齐时，UB→GM 写方向触发 ERR99999、GM→UB 读方向静默丢尾部数据。判别方法：尾部元素数*sizeof(T)%32!=0 即命中。；《DataCopyExtParams blockLen 窄化编译失败》说明DataCopyExtParams 的 blockLen 接收 uint32_t，模板表达式 D* sizeof(T) 须显式窄化后再做 DataCopyPad。。二者在DataCopy尾chunk错误由有效字节数非32B倍数触发，DataCopyPad的逐行、stride、padding和最小DMA卡给出修复边界上存在可执行的直接衔接。
- [EfficientTransferApi](../../guides/operator_practice/simd_operator_optimization/memory_access/efficient_transfer_api.md)（`related`）：EfficientTransferApi：指南要求用DataCopyExtParams一次表达blockCount/blockLen/stride；相邻搬运指南解释非连续与大块策略，blockLen类型runbook和NDDMA dstStride卡给出参数落地时的编译/偏移验证。 目标卡《DataCopyExtParams blockLen 窄化编译失败》补充：DataCopyExtParams 的 blockLen 接收 uint32_t，模板表达式 D* sizeof(T) 须显式窄化后再做 DataCopyPad。
- [DataCopyExtParams 运行时块数窄化编译失败](datacopyextparams_block_count_requires_uint16.md)（`same_topic`）：DataCopyExtParams blockLen 窄化编译失败 与《DataCopyExtParams 运行时块数窄化编译失败》的实质衔接是：本故障和 blockCount/rightPad 卡都发生在 AscendC 参数结构体列表初始化的精确整数宽度不匹配；DataCopyPad 是 DataCopyExtParams 的直接消费接口，其他 stride、对齐或队列故障不是同一编译根因。
- [DataCopyPad 加载缺少 Pad 参数导致编译失败](datacopypad_gm_to_ub_requires_pad_params.md)（`same_topic`）：焦点处理DataCopyPad GM→UB 扩展重载的 Pad 参数签名；DataCopyExtParams blockLen 窄化编译失败正文界定“DataCopyExtParams 的 blockLen 接收 uint32_t，模板表达式 D* sizeof(T) 须显式窄化后再做 DataCopyPad”。候选是 DataCopyPad API、相反方向重载、参数窄化与 rightPad 类型的同一签名决策。
<!-- cannbot:related:end -->
