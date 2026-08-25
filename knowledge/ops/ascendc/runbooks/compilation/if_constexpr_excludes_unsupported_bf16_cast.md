---
type: "Runbook"
title: "BiSheng bf16 类型转换失败——隔离模板实例化"
description: "运行时 guard 不能阻止通用分发宏实例化不支持的 BF16 规约模板；为更新型 dtype 使用独立模板入口。"
tags: ["task.debugging", "topic.compute.elementwise.type_conversion"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# BiSheng bf16 类型转换失败——隔离模板实例化

## 现象

在 Ascend950 的 CANN 9.0.1 环境中构建一个 `scatter.asc` 单文件直调工程时，host 分发函数把 update 与 reduce 共用一个 `LAUNCH_SCATTER(T, IDXT, ACC_REDUCE)` 宏。为 `bfloat16_t` 分支传入 `ACC_REDUCE=float` 后，运行构建命令，BiSheng 在 device 后端直接失败：

```text
fatal error: error in backend: not support bf16 type cast
bisheng: error: clang frontend command failed with exit code 70 (use -v to see invocation)
gmake[2]: *** [CMakeFiles/op_scatter.dir/build.make:76: CMakeFiles/op_scatter.dir/scatter.asc.o] Error 1
gmake[1]: *** [CMakeFiles/Makefile2:83: CMakeFiles/op_scatter.dir/all] Error 2
gmake: *** [Makefile:91: all] Error 2
```

当时代码已经在运行时用 `isUpdate` 和 `TORCH_CHECK(isUpdate, ...)` 限制 BF16 只走 update，但同一个宏体仍写出了 BF16 reduce 的全部 kernel specialization。

## 适用场景

- 工程形态：Ascend C 单文件 kernel 直调工程，host 侧以 C++ 模板宏分发 data dtype、index dtype 与计算 dtype；
- API 路径：host 入口通过 `<<<..., aclStream>>>` 实例化 device kernel，device 内对 `bfloat16_t` 做模板化 `static_cast<float>`；
- 验证过的平台与 CANN 版本：950 / CANN 9.0.1；
- 适用粒度：`operator_family`，适用于“某 dtype 只支持 update，而同一分发宏还包含 reduce/cast specialization”的不规则更新或混合 dtype 算子；
- 路线优先级：`recommended_fastpath`，在契约明确 BF16 只需 update 时，用 update-only 模板入口从编译期消除不支持的 specialization；
- 明确不适用：如果契约要求 BF16 reduce，本配方不能把该能力静默删掉；应另行实现并上板验证受支持的 BF16↔FP32 转换路径。

## 根因

C++ 模板实例化发生在编译期：运行时的 `if (isUpdate)` 或 `TORCH_CHECK(isUpdate, ...)` 不会阻止编译器实例化宏体中已经写出的 `scatter_kernel<float, bfloat16_t, ...>` reduce 分支；该 specialization 进入 device 代码的 `static_cast<float>(bfloat16_t)` 后触发 BiSheng 后端不支持的 BF16 类型转换。

机制链为：

1. host 的 BF16 分支展开 `LAUNCH_SCATTER(bfloat16_t, ..., float)`；
2. 宏展开文本同时包含 update、add、multiply、amax、amin 五组 kernel specialization；
3. 即使 `isUpdate` 在运行时恒真，四个 reduce specialization 仍进入编译；
4. reduce kernel 将 `T=bfloat16_t` 的更新值转换成 `AccT=float`；
5. BiSheng 编译 device specialization 时遇到不支持的 BF16 cast，构建在运行前即失败。

## 解决配方

不要只在通用宏外增加运行时 guard。为 update-only dtype 定义一个只含 update specialization 的独立宏，使不支持的 reduce specialization 根本不进入翻译单元。

### before

代码证据：revision 为编译失败前的未提交轨迹快照；path=`operators/scatter/scatter.asc`；symbol=`op_scatter::scatter`。以下函数由事件流 Write/Edit 逐版本重放，verbatim 保留：

```cpp
at::Tensor scatter(const at::Tensor& data, int64_t dim, const at::Tensor& indices,
                   const at::Tensor& updates, const std::optional<std::string>& reduce)
{
    TORCH_CHECK(data.dim() == indices.dim(), "data and indices must have the same number of dims");
    TORCH_CHECK(data.dim() == updates.dim(), "data and updates must have the same number of dims");
    TORCH_CHECK(data.scalar_type() == updates.scalar_type(),
                "data and updates must share dtype, got ", data.scalar_type(), " vs ", updates.scalar_type());
    TORCH_CHECK(indices.scalar_type() == at::kInt || indices.scalar_type() == at::kLong,
                "indices must be int32 or int64, got ", indices.scalar_type());
    TORCH_CHECK(data.is_contiguous(), "data must be contiguous");
    TORCH_CHECK(indices.is_contiguous(), "indices must be contiguous");
    TORCH_CHECK(updates.is_contiguous(), "updates must be contiguous");
    for (int64_t d = 0; d < data.dim(); ++d) {
        TORCH_CHECK(indices.size(d) <= data.size(d), "indices size must be <= data size on each axis");
        TORCH_CHECK(updates.size(d) == indices.size(d), "updates shape must match indices shape");
    }

    const c10::OptionalDeviceGuard guard(data.device());
    auto aclStream = c10_npu::getCurrentNPUStream().stream(false);

    auto dtype = data.scalar_type();
    auto idxDtype = indices.scalar_type();
    int32_t mode = reduce_mode(reduce);
    bool isUpdate = (mode == MODE_UPDATE);
    int64_t ndim = data.dim();
    int32_t dimN = normalize_dim(dim, ndim);
    int64_t numIndices = indices.numel();

    // Accumulator dtype: T for update; float for fp16/bf16 reduce (matches torch's
    // upcast); T (native) for fp32/int32/int64 reduce.
    at::ScalarType accDtype = dtype;
    if (!isUpdate && (dtype == at::kHalf || dtype == at::kBFloat16)) {
        accDtype = at::kFloat;
    }

    // Seed acc = data (copy), upcast to accDtype for reduce. clone guarantees a
    // writeable copy (data.to may alias when dtype is unchanged).
    at::Tensor acc = data.clone().to(accDtype);
    // torch_npu may run the DMA copy/cast (and any preceding H2D copies of the
    // inputs) on a different stream than the kernel launch. Sync the device so the
    // kernel never races the producer of the buffers it reads.
    c10_npu::npuSynchronizeDevice();

    ScatterParams params{};
    params.numIndices = numIndices;
    params.ndim = static_cast<int32_t>(ndim);
    params.dim = dimN;
    for (int64_t d = 0; d < ndim; ++d) {
        params.shape[d] = indices.size(d);
    }
    fill_contig_strides(data, ndim, params.dataStrides);
    for (int64_t d = 0; d < SCATTER_PARAMS_MAX_DIM; ++d) {
        params.coord0[d] = 0;
    }

    auto acc_ptr = (GM_ADDR)acc.data_ptr();
    auto idx_ptr = (GM_ADDR)indices.data_ptr();
    auto upd_ptr = (GM_ADDR)updates.data_ptr();

// For (data dtype T, index dtype IDXT): update -> kernel<T,T,IDXT,UPDATE>;
// reduce -> kernel<ComputeType<T>, T, IDXT, MODE>.
#define LAUNCH_SCATTER(T, IDXT, ACC_REDUCE)                                                 \
    do {                                                                                    \
        if (isUpdate) {                                                                    \
            scatter_kernel<T, T, IDXT, MODE_UPDATE><<<1, nullptr, aclStream>>>(            \
                acc_ptr, idx_ptr, upd_ptr, params);                                        \
        } else {                                                                            \
            switch (mode) {                                                                 \
                case MODE_ADD:                                                             \
                    scatter_kernel<ACC_REDUCE, T, IDXT, MODE_ADD><<<1, nullptr, aclStream>>>( \
                        acc_ptr, idx_ptr, upd_ptr, params); break;                         \
                case MODE_MUL:                                                             \
                    scatter_kernel<ACC_REDUCE, T, IDXT, MODE_MUL><<<1, nullptr, aclStream>>>( \
                        acc_ptr, idx_ptr, upd_ptr, params); break;                         \
                case MODE_AMAX:                                                            \
                    scatter_kernel<ACC_REDUCE, T, IDXT, MODE_AMAX><<<1, nullptr, aclStream>>>( \
                        acc_ptr, idx_ptr, upd_ptr, params); break;                         \
                case MODE_AMIN:                                                            \
                    scatter_kernel<ACC_REDUCE, T, IDXT, MODE_AMIN><<<1, nullptr, aclStream>>>( \
                        acc_ptr, idx_ptr, upd_ptr, params); break;                         \
                default: TORCH_CHECK(false, "invalid reduce mode");                        \
            }                                                                               \
        }                                                                                   \
    } while (0)

    if (dtype == at::kFloat) {
        if (idxDtype == at::kInt) { LAUNCH_SCATTER(float, int32_t, float); }
        else { LAUNCH_SCATTER(float, int64_t, float); }
    } else if (dtype == at::kHalf) {
        if (idxDtype == at::kInt) { LAUNCH_SCATTER(half, int32_t, float); }
        else { LAUNCH_SCATTER(half, int64_t, float); }
    } else if (dtype == at::kBFloat16) {
        // bf16 <-> float cast is not supported in device code; restrict to update
        // (the eval only exercises bf16 in update mode anyway).
        TORCH_CHECK(isUpdate, "bfloat16 only supports reduce=None/update");
        if (idxDtype == at::kInt) { LAUNCH_SCATTER(bfloat16_t, int32_t, float); }
        else { LAUNCH_SCATTER(bfloat16_t, int64_t, float); }
    } else if (dtype == at::kInt) {
        if (idxDtype == at::kInt) { LAUNCH_SCATTER(int32_t, int32_t, int32_t); }
        else { LAUNCH_SCATTER(int32_t, int64_t, int32_t); }
    } else if (dtype == at::kLong) {
        TORCH_CHECK(isUpdate, "int64 only supports reduce=None/update");
        if (idxDtype == at::kInt) { LAUNCH_SCATTER(int64_t, int32_t, int64_t); }
        else { LAUNCH_SCATTER(int64_t, int64_t, int64_t); }
    } else {
        TORCH_CHECK(false, "unsupported data dtype: ", dtype);
    }
#undef LAUNCH_SCATTER

    // Kernel done before the final cast (which reads acc via DMA on the torch stream).
    c10_npu::npuSynchronizeDevice();
    at::Tensor y = (accDtype == dtype) ? acc : acc.to(dtype);
    return y;
}
```

### after

代码证据：revision=`b7d5ac2`（trace 仅提供短 Git 哈希）；path=`operators/scatter/scatter.asc`；symbol=`op_scatter::scatter`。它支撑“更新专用宏不实例化 BF16 reduce kernel”的结论。以下函数 verbatim 取自修复后的事件流：

```cpp
at::Tensor scatter(const at::Tensor& data, int64_t dim, const at::Tensor& indices,
                   const at::Tensor& updates, const std::optional<std::string>& reduce)
{
    TORCH_CHECK(data.dim() == indices.dim(), "data and indices must have the same number of dims");
    TORCH_CHECK(data.dim() == updates.dim(), "data and updates must have the same number of dims");
    TORCH_CHECK(data.scalar_type() == updates.scalar_type(),
                "data and updates must share dtype, got ", data.scalar_type(), " vs ", updates.scalar_type());
    TORCH_CHECK(indices.scalar_type() == at::kInt || indices.scalar_type() == at::kLong,
                "indices must be int32 or int64, got ", indices.scalar_type());
    TORCH_CHECK(data.is_contiguous(), "data must be contiguous");
    TORCH_CHECK(indices.is_contiguous(), "indices must be contiguous");
    TORCH_CHECK(updates.is_contiguous(), "updates must be contiguous");
    for (int64_t d = 0; d < data.dim(); ++d) {
        TORCH_CHECK(indices.size(d) <= data.size(d), "indices size must be <= data size on each axis");
        TORCH_CHECK(updates.size(d) == indices.size(d), "updates shape must match indices shape");
    }

    const c10::OptionalDeviceGuard guard(data.device());
    auto aclStream = c10_npu::getCurrentNPUStream().stream(false);

    auto dtype = data.scalar_type();
    auto idxDtype = indices.scalar_type();
    int32_t mode = reduce_mode(reduce);
    bool isUpdate = (mode == MODE_UPDATE);
    int64_t ndim = data.dim();
    int32_t dimN = normalize_dim(dim, ndim);
    int64_t numIndices = indices.numel();

    // Accumulator dtype: T for update; float for fp16/bf16 reduce (matches torch's
    // upcast); T (native) for fp32/int32/int64 reduce.
    at::ScalarType accDtype = dtype;
    if (!isUpdate && (dtype == at::kHalf || dtype == at::kBFloat16)) {
        accDtype = at::kFloat;
    }

    // Seed acc = data (copy), upcast to accDtype for reduce. clone guarantees a
    // writeable copy (data.to may alias when dtype is unchanged).
    at::Tensor acc = data.clone().to(accDtype);
    // torch_npu may run the DMA copy/cast (and any preceding H2D copies of the
    // inputs) on a different stream than the kernel launch. Sync the device so the
    // kernel never races the producer of the buffers it reads.
    c10_npu::npuSynchronizeDevice();

    ScatterParams params{};
    params.numIndices = numIndices;
    params.ndim = static_cast<int32_t>(ndim);
    params.dim = dimN;
    for (int64_t d = 0; d < ndim; ++d) {
        params.shape[d] = indices.size(d);
    }
    fill_contig_strides(data, ndim, params.dataStrides);
    for (int64_t d = 0; d < SCATTER_PARAMS_MAX_DIM; ++d) {
        params.coord0[d] = 0;
    }

    auto acc_ptr = (GM_ADDR)acc.data_ptr();
    auto idx_ptr = (GM_ADDR)indices.data_ptr();
    auto upd_ptr = (GM_ADDR)updates.data_ptr();

// For (data dtype T, index dtype IDXT): update -> kernel<T,T,IDXT,UPDATE>;
// reduce -> kernel<ComputeType<T>, T, IDXT, MODE>.
#define LAUNCH_SCATTER(T, IDXT, ACC_REDUCE)                                                 \
    do {                                                                                    \
        if (isUpdate) {                                                                    \
            scatter_kernel<T, T, IDXT, MODE_UPDATE><<<1, nullptr, aclStream>>>(            \
                acc_ptr, idx_ptr, upd_ptr, params);                                        \
        } else {                                                                            \
            switch (mode) {                                                                 \
                case MODE_ADD:                                                             \
                    scatter_kernel<ACC_REDUCE, T, IDXT, MODE_ADD><<<1, nullptr, aclStream>>>( \
                        acc_ptr, idx_ptr, upd_ptr, params); break;                         \
                case MODE_MUL:                                                             \
                    scatter_kernel<ACC_REDUCE, T, IDXT, MODE_MUL><<<1, nullptr, aclStream>>>( \
                        acc_ptr, idx_ptr, upd_ptr, params); break;                         \
                case MODE_AMAX:                                                            \
                    scatter_kernel<ACC_REDUCE, T, IDXT, MODE_AMAX><<<1, nullptr, aclStream>>>( \
                        acc_ptr, idx_ptr, upd_ptr, params); break;                         \
                case MODE_AMIN:                                                            \
                    scatter_kernel<ACC_REDUCE, T, IDXT, MODE_AMIN><<<1, nullptr, aclStream>>>( \
                        acc_ptr, idx_ptr, upd_ptr, params); break;                         \
                default: TORCH_CHECK(false, "invalid reduce mode");                        \
            }                                                                               \
        }                                                                                   \
    } while (0)

// Update-only dtypes (bf16/int64): no reduce instantiation (bf16<->float cast and
// int64 reduce are unsupported / unused by the eval).
#define LAUNCH_UPDATE_ONLY(T, IDXT)                                                         \
    do {                                                                                    \
        TORCH_CHECK(isUpdate, "this dtype only supports reduce=None/update");              \
        scatter_kernel<T, T, IDXT, MODE_UPDATE><<<1, nullptr, aclStream>>>(                \
            acc_ptr, idx_ptr, upd_ptr, params);                                            \
    } while (0)

    if (dtype == at::kFloat) {
        if (idxDtype == at::kInt) { LAUNCH_SCATTER(float, int32_t, float); }
        else { LAUNCH_SCATTER(float, int64_t, float); }
    } else if (dtype == at::kHalf) {
        if (idxDtype == at::kInt) { LAUNCH_SCATTER(half, int32_t, float); }
        else { LAUNCH_SCATTER(half, int64_t, float); }
    } else if (dtype == at::kBFloat16) {
        if (idxDtype == at::kInt) { LAUNCH_UPDATE_ONLY(bfloat16_t, int32_t); }
        else { LAUNCH_UPDATE_ONLY(bfloat16_t, int64_t); }
    } else if (dtype == at::kInt) {
        if (idxDtype == at::kInt) { LAUNCH_SCATTER(int32_t, int32_t, int32_t); }
        else { LAUNCH_SCATTER(int32_t, int64_t, int32_t); }
    } else if (dtype == at::kLong) {
        if (idxDtype == at::kInt) { LAUNCH_UPDATE_ONLY(int64_t, int32_t); }
        else { LAUNCH_UPDATE_ONLY(int64_t, int64_t); }
    } else {
        TORCH_CHECK(false, "unsupported data dtype: ", dtype);
    }
#undef LAUNCH_SCATTER
#undef LAUNCH_UPDATE_ONLY

    // Kernel done before the final cast (which reads acc via DMA on the torch stream).
    c10_npu::npuSynchronizeDevice();
    at::Tensor y = (accDtype == dtype) ? acc : acc.to(dtype);
    return y;
}
```

## 设计决策

1. 选择编译期隔离，而不是继续添加运行时 guard：根因发生在模板实例化阶段，只有从源码中移除不支持的 specialization 才能阻止 BiSheng 进入 BF16 cast 后端路径。
2. 保留通用 `LAUNCH_SCATTER` 给真正支持规约的 dtype；只为契约中的 update-only dtype 增加 `LAUNCH_UPDATE_ONLY`，避免把所有类型都降级。
3. 未采用“让 BF16 reduce 继续编译但在运行时拒绝”的候选，因为它正是失败版本，运行时根本到达不了。
4. 当前方案属于 `recommended_fastpath`，但仅对 update-only 契约成立；BF16 reduce 是未实现能力，不得宣称已支持。

## 预防

- 审查模板分发时按“宏展开后有哪些 specialization”检查，不按运行时输入会走哪条分支检查。
- 对受限 dtype 建独立的 compile-time 路由；不要依赖 `if`、`switch` 或 `TORCH_CHECK` 消除不支持的 device 模板。
- 在加入新 dtype 后做一次全翻译单元构建；BiSheng 会编译 host 分发中可见的所有 device specialization。
- 如果需要 BF16 reduce，先核验目标 CANN/架构的转换 API，再增加独立实现与上板用例；不能通过跳过必需用例或放宽测试掩盖缺失能力。

## 验证信号

来源说明：该闭环来自 Ascend950 Flash 直调工程的一次 host dispatch 重构；同一 CANN 9.0.1 / BiSheng 工具链先观测到 BF16 cast 后端失败，随后只改变模板分发形态并重新构建。

- 修复前构建出现 `fatal error: error in backend: not support bf16 type cast`，并由 BiSheng 以 exit code 70 退出（来源平台: 950；证据等级: tool_observed）。
- 加入 `LAUNCH_UPDATE_ONLY`、将 BF16 更新分支改为只实例化 `MODE_UPDATE` 后，构建输出 `[100%] Built target op_scatter`（来源平台: 950；证据等级: tool_observed）。

## 失效边界

- 本配方只解决“契约确实不要求该 dtype 的 reduce，但通用模板误实例化 reduce”的编译失败。
- 如果 BF16 reduce 是必需语义，update-only 路由只会显式拒绝，不能替代 BF16↔FP32 的受支持转换实现。
- A2/A3 未验证；编译器支持矩阵可能不同，不能从 950 结果直接外推。
- trace 只保留最终提交的短哈希，正式落库前若要求 40 位 revision，curator 应补固定 commit 或将该候选 defer。

## 坏实践

- 只在 BF16 分支前写 `TORCH_CHECK(isUpdate, ...)`，却继续调用包含 reduce specialization 的通用宏：这是运行时检查，无法改变编译期实例化集合。
- 把额外 dtype×reduce 用例标成 skip 并据此宣称“编译问题解决”：skip 不是 device 编译修复，本卡验证只采用 BiSheng 的失败/成功构建输出。
- 通过修改测试容差掩盖 compiler backend error：编译错误发生在测试运行之前，容差与它无关。

## 误诊

“运行时不会走 BF16 reduce 分支，所以编译器不会生成它”是错误假设。模板是否实例化取决于翻译单元中写出的 specialization，不取决于运行时 `mode`。

<!-- cannbot:related:start -->
## 相关

- [FP16 算子 Cast 提升-计算-回退链设计](../precision/fp16_cast_up_fp32_compute_cast_down_chain.md)（`related`）：FP16 算子 Cast 提升-计算-回退链设计 与《BiSheng bf16 类型转换失败——隔离模板实例化》的实质衔接是：FP16 提升到 FP32、VF 计算再 RINT 回退要求 Cast 模式、lane 宽、UB 容量和 MTE/Vector 同步一致；相关故障均命中这些步骤。
- [__simd_vf__ if constexpr 致 hoisted 报错](simd_vf_if_constexpr_lowering_banned_exit_70.md)（`related`）：《__simd_vf__ if constexpr 致 hoisted 报错》说明dav-3510 上某 Reg __simd_vf__ 实现使用 if constexpr 与 constexpr trait 时，bisheng 后端报 Unsupported Inst must be hoisted 并退出 70；记录源码定位与编译边界，不提供未完成的 fallback 实现。；《BiSheng bf16 类型转换失败——隔离模板实例化》说明运行时 guard 不能阻止通用分发宏实例化不支持的 BF16 规约模板；为更新型 dtype 使用独立模板入口。。二者在该编译失败锁定__simd_vf__中的if constexpr/trait lowering，同类模板隔离、helper/VF边界与后端崩溃用于交叉验证上存在可执行的直接衔接。
- [bisheng 不支持 bf16 标量强转时用位布局精确提升到 fp32](bf16_scalar_to_fp32_bit_extension.md)（`related`）：当 BF16 reduce 确实必须实现时，位扩展卡给出已上板的 bf16→fp32 标量转换，补足本卡明确留下的“不能只删 specialization”分支。
- [bisheng 单模板跨字宽分支 segfault 判别](bisheng_segfault.md)（`related`）：两卡都定位模板实例化阶段的跨 dtype 失败；该卡用独立模板入口隔离不支持 BF16 Cast，本卡进一步证明跨字宽分支需物理拆类。
- [三元返回 B16 让 cast 失效触发 i64 setcc](ternary_b16_return_penetrates_float_cast.md)（`related`）：比较与 Cast 都会被运行时 dtype guard 之外的模板实例化提前触发；该卡补充必须在编译期剔除不支持 B16 设备表达式的共同约束。
- [BF16 标量 cast 后端失败—改用位序键](bf16_scalar_compare_by_raw_bits.md)（`same_topic`）：BF16 标量 cast 后端失败—改用位序键 与《BiSheng bf16 类型转换失败——隔离模板实例化》的实质衔接是：位序键是 BF16 标量 cast 失败的直接替代；所选卡补充同一后端限制、B16→B32 比较宽度及 NaN 显式选择。
- [bf16 未编译剔除触发 backend Cannot select](if_constexpr_excludes_unsupported_bf16_compare.md)（`same_topic`）：bf16 未编译剔除触发 backend Cannot select 的核心契约是“运行时 dtype 分支仍实例化 bf16 标量比较，BiSheng backend Cannot select；用 if constexpr 编译期剔除不支持分支”；BiSheng bf16 类型转换失败——隔离模板实例化 补充“运行时 guard 不能阻止通用分发宏实例化不支持的 BF16 规约模板；为更新型 dtype 使用独立模板入口”。
<!-- cannbot:related:end -->
