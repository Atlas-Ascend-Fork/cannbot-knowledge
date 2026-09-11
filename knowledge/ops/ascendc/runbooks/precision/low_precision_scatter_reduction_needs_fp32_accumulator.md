---
type: "Runbook"
title: "FP16 scatter 归约逐次回写放大相消误差"
description: "已验证边界仅为 FP16 scatter-add：逐步回写 half 会累积舍入误差，须用 FP32 中间缓冲；BF16、multiply、amin、amax 需分别验证。"
tags: ["task.debugging", "topic.precision", "topic.compute.reduction", "topic.compute.elementwise.type_conversion"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
aliases: ["fp32_accumulator", "scatter_add"]
---

# FP16 scatter 归约逐次回写放大相消误差

## 现象

在 Ascend950 上为自定义 PyTorch 扩展实现 `scatter` 的 `reduce=add` 路径时，`operators/scatter/scatter.asc` 已能编译并通过小规模 pytest；随后通过远端 helper 执行全量 cann-bench 正确性评测：

```text
remote_runner.sh baseline scatter 3 6 eval
```

当时代码把输出张量本身声明为模板类型 `T`。对 FP16 输入，`T=half`，每次随机更新都从 GM 读取一个 `half`，以 `half` 做 `cur + val`，再立即写回 `half`。评测中只有两条 FP16 add 输入失败，原始信号为：

```text
float16[y]: ❌ MERE=2.626815e-05, MARE=0.160997
(threshold=9.765625e-04, mare_threshold=9.765625e-03)

float16[y]: ❌ MERE=1.509420e-05, MARE=0.020576
(threshold=9.765625e-04, mare_threshold=9.765625e-03)
```

这两个结果的 MERE 很小，但 MARE 超过阈值，并同时触发相消位置检查；其余 overwrite、FP32 和整数路径通过。这个信号组合说明问题不是目标地址公式整体错误，而是 FP16 重复读改写在接近相消的位置放大了相对误差。

## 适用场景

- 工程形态：通过 `TORCH_LIBRARY` 注册的自定义 Ascend C kernel，host 入口分配输出后启动单核随机写归约；
- API 路径：FP16 `scatter` / indexed update 的 `add` 读改写路径；`multiply`、`amin`、`amax` 不在本卡结论范围；
- 验证过的平台与版本：`950`（Ascend950PR_957b，NpuArch=dav-3510）/ CANN 9.0.1；
- 适用粒度：`same_operator`；迁移到其他随机写归约前，须先核对目标地址冲突语义、累加顺序和输出 dtype；
- 数值契约：已验证的 FP16 scatter-add 必须避免每次更新都量化回 FP16；FP32 accumulator 是本卡的数值正确性基线；
- 明确不适用：overwrite 纯拷贝无需 FP32 累加；FP32/整数输入不走此修复；BF16 reduce、原子多核归约和 A2/A3 未验证。

## 根因

根因是 FP16 随机写归约把每次中间和都立即量化回 `half`，使逐步舍入误差在相消位置累积并被很小的参考值放大。 原实现的递推是： ```text q₀ = fp16(data) qⱼ₊₁ = fp16(qⱼ + fp16(updateⱼ)) ``` 每一步都会引入舍入项 `eⱼ`，所以最终结果可写为： ```text qₘ = data + Σ updateⱼ + Σ eⱼ ``` 当 `data + Σ updateⱼ` 因正负更新相消而接近 0 时，绝对误差 `|Σeⱼ|` 可能仍小，故 MERE 很低；但相对误差近似为： ```text |Σeⱼ| / |data + Σ updateⱼ| ``` 分母变小后，MARE 会显著升高。修复把递推改为 FP32 中间状态： ```text a₀ = fp32(fp16(data)) aⱼ₊₁ = fp32(aⱼ + fp32(fp16(updateⱼ))) y = fp16(aₘ) ``` 这样只在最终输出时转回 FP16，避免每次随机读改写都进行半精度量化。

## 解决配方

在 host 分发层把 FP16 reduce 单独路由到 FP32 accumulator kernel：

1. 分配与输出同 shape 的 FP32 `yacc`；
2. kernel 的 phase A 将输入 FP16 提升到 FP32；
3. phase B 始终从 `yacc` 读取和写回 FP32 中间值；
4. kernel 完成后只做一次 `y.copy_(yacc)`，把 FP32 结果转回 FP16；
5. FP16 overwrite 保持原来的精确字节拷贝路径，不引入 accumulator。

### before

代码状态：revision `50e9f78`；path `operators/scatter/scatter.asc`；symbol `scatter_kernel<T, IdxT>`；lines 72–119。该完整函数证明 FP16 reduce 的 `cur`、`val`、`nv` 和 `yPtr` 全部是 `T=half`，每轮都写回 half。

```cpp
template <typename T, typename IdxT>
__global__ __aicore__ __vector__ void scatter_kernel(
    GM_ADDR data, GM_ADDR indices, GM_ADDR updates, GM_ADDR y,
    int64_t numData, int64_t numUpdates, int64_t innerSize, int64_t uDimSize,
    int64_t dataDimSize, int32_t reduceMode)
{
    __gm__ T *dataPtr = (__gm__ T *)data;
    __gm__ IdxT *idxPtr = (__gm__ IdxT *)indices;
    __gm__ T *updPtr = (__gm__ T *)updates;
    __gm__ T *yPtr = (__gm__ T *)y;

    // Phase A: y = data (scalar copy). Single in-order stream, no cross-op race.
    for (int64_t i = 0; i < numData; ++i) {
        yPtr[i] = dataPtr[i];
    }

    const int64_t INNER = innerSize;
    const int64_t UDIM = uDimSize;
    const int64_t OUTER_STRIDE = dataDimSize * innerSize;

    // Phase B: scatter. decompose(k) -> (o, i_dim, r); init (0,0,0) at k=0.
    int64_t o = 0, i_dim = 0, r = 0;

    for (int64_t k = 0; k < numUpdates; ++k) {
        IdxT idxVal = idxPtr[k];
        int64_t target = OUTER_STRIDE * o + static_cast<int64_t>(idxVal) * INNER + r;
        T val = updPtr[k];
        if (reduceMode == 0) {
            yPtr[target] = val;                                   // overwrite (last-wins)
        } else {
            T cur = yPtr[target];                                 // read-modify-write
            T nv;
            if (reduceMode == 1)      nv = cur + val;             // add
            else if (reduceMode == 2) nv = cur * val;             // multiply
            else if (reduceMode == 3) nv = (cur < val) ? cur : val; // amin
            else                      nv = (cur > val) ? cur : val; // amax
            yPtr[target] = nv;
        }
        // advance (r -> i_dim -> o): r wraps every INNER steps -> i_dim++;
        // i_dim wraps every UDIM steps -> o++.
        r++;
        if (r >= INNER) {
            r = 0;
            i_dim++;
            if (i_dim >= UDIM) { i_dim = 0; o++; }
        }
    }
}
```

代码状态：revision `50e9f78`；path `operators/scatter/scatter.asc`；symbol `op_scatter::scatter`；lines 135–222。该完整函数证明所有 FP16 请求原先都通过通用 `DISPATCH(half, ...)` 进入上述 native kernel，没有单独的宽精度归约状态。

```cpp
at::Tensor scatter(const at::Tensor& data, int64_t dim,
                   const at::Tensor& indices, const at::Tensor& updates,
                   const c10::optional<c10::string_view>& reduce)
{
    TORCH_CHECK(data.dim() == indices.dim() && data.dim() == updates.dim(),
                "data, indices, updates must have the same number of dimensions.");
    TORCH_CHECK(data.scalar_type() == updates.scalar_type(),
                "data and updates must have the same dtype.");
    TORCH_CHECK(indices.scalar_type() == at::kInt || indices.scalar_type() == at::kLong,
                "indices must be int32 or int64.");
    // PrivateUse1 dispatch only reaches here for NPU tensors; device guard below.

    const c10::OptionalDeviceGuard guard(data.device());
    auto aclStream = c10_npu::getCurrentNPUStream().stream(false);

    int64_t rank = data.dim();
    int64_t ndim = dim;
    if (ndim < 0) ndim += rank;
    TORCH_CHECK(ndim >= 0 && ndim < rank, "dim out of range: ", dim);

    // Verify the closed-form precondition: for all d != dim, u_shape[d]==data_shape[d].
    for (int64_t d = 0; d < rank; ++d) {
        if (d == ndim) continue;
        TORCH_CHECK(indices.size(d) == data.size(d),
                    "indices size must equal data size along non-scatter axis ", d);
    }
    TORCH_CHECK(updates.sizes() == indices.sizes(), "updates shape must equal indices shape.");
    TORCH_CHECK(indices.size(ndim) <= data.size(ndim), "indices size exceeds data size along dim.");

    int32_t reduceMode = encode_reduce(reduce);
    bool isBf16 = (data.scalar_type() == at::kBFloat16);
    TORCH_CHECK(!(isBf16 && reduceMode != 0),
                "bfloat16 + reduce is not supported (no such case in scope).");

    // y allocated empty; the kernel does y = data (phase A) then scatters (phase B)
    // in one launch to avoid any cross-op stream race between a host clone and the
    // kernel's scattered writes.
    at::Tensor y = at::empty(data.sizes(), data.options());

    int64_t numData = data.numel();
    int64_t numUpdates = indices.numel();
    // INNER = product of u_shape[dim+1 .. rank-1]
    int64_t innerSize = 1;
    for (int64_t d = ndim + 1; d < rank; ++d) innerSize *= indices.size(d);
    int64_t uDimSize = indices.size(ndim);
    int64_t dataDimSize = data.size(ndim);

    int64_t numBlocks, blockLength, tileSize;
    std::tie(numBlocks, blockLength, tileSize) = calc_scatter_tiling_params(numUpdates);
    (void)blockLength; (void)tileSize;

    auto data_ptr = (GM_ADDR)data.data_ptr();
    auto idx_ptr = (GM_ADDR)indices.data_ptr();
    auto upd_ptr = (GM_ADDR)updates.data_ptr();
    auto y_ptr = (GM_ADDR)y.data_ptr();

    auto dtype = data.scalar_type();
    auto idx_dtype = indices.scalar_type();
    // dispatch by (data dtype, indices dtype)
    #define DISPATCH(T_CPP, IDX_CPP, DT_ENUM, IDX_ENUM) \
        if (dtype == (DT_ENUM) && idx_dtype == (IDX_ENUM)) { \
            scatter_kernel<T_CPP, IDX_CPP><<<numBlocks, nullptr, aclStream>>>( \
                data_ptr, idx_ptr, upd_ptr, y_ptr, numData, numUpdates, \
                innerSize, uDimSize, dataDimSize, reduceMode); \
            return y; \
        }

    // float32
    DISPATCH(float,    int32_t, at::kFloat,    at::kInt)
    DISPATCH(float,    int64_t, at::kFloat,    at::kLong)
    // float16
    DISPATCH(half,     int32_t, at::kHalf,     at::kInt)
    DISPATCH(half,     int64_t, at::kHalf,     at::kLong)
    // bfloat16: use `half` as a 2-byte container (overwrite only, guarded above).
    DISPATCH(half,     int32_t, at::kBFloat16, at::kInt)
    DISPATCH(half,     int64_t, at::kBFloat16, at::kLong)
    // int32
    DISPATCH(int32_t,  int32_t, at::kInt,      at::kInt)
    DISPATCH(int32_t,  int64_t, at::kInt,      at::kLong)
    // int64
    DISPATCH(int64_t,  int32_t, at::kLong,     at::kInt)
    DISPATCH(int64_t,  int64_t, at::kLong,     at::kLong)
    #undef DISPATCH

    TORCH_CHECK(false, "op_scatter::scatter unsupported dtype combination: data=", dtype,
                " indices=", idx_dtype);
    return y;
}
```

### after

代码状态：revision `b1fc972`；path `operators/scatter/scatter.asc`；symbol `scatter_kernel_f16reduce<TData, IdxT>`；lines 129–165。该完整函数证明 phase A 和所有 reduce 中间读改写均落在 FP32 `yacc`，输入和更新只在读入时从 FP16 提升。

```cpp
template <typename TData, typename IdxT>
__global__ __aicore__ __vector__ void scatter_kernel_f16reduce(
    GM_ADDR data, GM_ADDR indices, GM_ADDR updates, GM_ADDR yacc,
    int64_t numData, int64_t numUpdates, int64_t innerSize, int64_t uDimSize,
    int64_t dataDimSize, int32_t reduceMode)
{
    __gm__ TData *dataPtr = (__gm__ TData *)data;
    __gm__ IdxT *idxPtr = (__gm__ IdxT *)indices;
    __gm__ TData *updPtr = (__gm__ TData *)updates;
    __gm__ float *yaccPtr = (__gm__ float *)yacc;

    // Phase A: yacc = data (promote to fp32).
    for (int64_t i = 0; i < numData; ++i) {
        yaccPtr[i] = static_cast<float>(dataPtr[i]);
    }

    const int64_t INNER = innerSize;
    const int64_t UDIM = uDimSize;
    const int64_t OUTER_STRIDE = dataDimSize * innerSize;
    int64_t o = 0, i_dim = 0, r = 0;

    // Phase B: fp32 accumulate.
    for (int64_t k = 0; k < numUpdates; ++k) {
        IdxT idxVal = idxPtr[k];
        int64_t target = OUTER_STRIDE * o + static_cast<int64_t>(idxVal) * INNER + r;
        float val = static_cast<float>(updPtr[k]);
        float cur = yaccPtr[target];
        float nv;
        if (reduceMode == 1)      nv = cur + val;
        else if (reduceMode == 2) nv = cur * val;
        else if (reduceMode == 3) nv = (cur < val) ? cur : val;
        else                      nv = (cur > val) ? cur : val;
        yaccPtr[target] = nv;
        r++;
        if (r >= INNER) { r = 0; i_dim++; if (i_dim >= UDIM) { i_dim = 0; o++; } }
    }
}
```

代码状态：revision `b1fc972`；path `operators/scatter/scatter.asc`；symbol `op_scatter::scatter`；lines 181–289。该完整函数证明只有 FP16 reduce 被路由到 FP32 accumulator，overwrite 仍走通用 native kernel，并在 kernel 完成后一次转换回 FP16。

```cpp
at::Tensor scatter(const at::Tensor& data, int64_t dim,
                   const at::Tensor& indices, const at::Tensor& updates,
                   const c10::optional<c10::string_view>& reduce)
{
    TORCH_CHECK(data.dim() == indices.dim() && data.dim() == updates.dim(),
                "data, indices, updates must have the same number of dimensions.");
    TORCH_CHECK(data.scalar_type() == updates.scalar_type(),
                "data and updates must have the same dtype.");
    TORCH_CHECK(indices.scalar_type() == at::kInt || indices.scalar_type() == at::kLong,
                "indices must be int32 or int64.");
    // PrivateUse1 dispatch only reaches here for NPU tensors; device guard below.

    const c10::OptionalDeviceGuard guard(data.device());
    auto aclStream = c10_npu::getCurrentNPUStream().stream(false);

    int64_t rank = data.dim();
    int64_t ndim = dim;
    if (ndim < 0) ndim += rank;
    TORCH_CHECK(ndim >= 0 && ndim < rank, "dim out of range: ", dim);

    // Verify the closed-form precondition: for all d != dim, u_shape[d]==data_shape[d].
    for (int64_t d = 0; d < rank; ++d) {
        if (d == ndim) continue;
        TORCH_CHECK(indices.size(d) == data.size(d),
                    "indices size must equal data size along non-scatter axis ", d);
    }
    TORCH_CHECK(updates.sizes() == indices.sizes(), "updates shape must equal indices shape.");
    TORCH_CHECK(indices.size(ndim) <= data.size(ndim), "indices size exceeds data size along dim.");

    int32_t reduceMode = encode_reduce(reduce);
    bool isBf16 = (data.scalar_type() == at::kBFloat16);
    TORCH_CHECK(!(isBf16 && reduceMode != 0),
                "bfloat16 + reduce is not supported (no such case in scope).");

    // y allocated empty; the kernel does y = data (phase A) then scatters (phase B)
    // in one launch to avoid any cross-op stream race between a host clone and the
    // kernel's scattered writes.
    at::Tensor y = at::empty(data.sizes(), data.options());

    int64_t numData = data.numel();
    int64_t numUpdates = indices.numel();
    // INNER = product of u_shape[dim+1 .. rank-1]
    int64_t innerSize = 1;
    for (int64_t d = ndim + 1; d < rank; ++d) innerSize *= indices.size(d);
    int64_t uDimSize = indices.size(ndim);
    int64_t dataDimSize = data.size(ndim);

    int64_t numBlocks, blockLength, tileSize;
    std::tie(numBlocks, blockLength, tileSize) = calc_scatter_tiling_params(numUpdates);
    (void)blockLength; (void)tileSize;

    auto data_ptr = (GM_ADDR)data.data_ptr();
    auto idx_ptr = (GM_ADDR)indices.data_ptr();
    auto upd_ptr = (GM_ADDR)updates.data_ptr();
    auto y_ptr = (GM_ADDR)y.data_ptr();

    auto dtype = data.scalar_type();
    auto idx_dtype = indices.scalar_type();

    // fp16 reduce path: accumulate in fp32 to match the fp64 CPU golden.
    // (overwrite is exact copy and uses the native kernel below.)
    if (dtype == at::kHalf && reduceMode != 0) {
        at::Tensor yacc = at::empty(data.sizes(), data.options().dtype(at::kFloat));
        auto yacc_ptr = (GM_ADDR)yacc.data_ptr();
        if (idx_dtype == at::kInt) {
            scatter_kernel_f16reduce<half, int32_t><<<numBlocks, nullptr, aclStream>>>(
                data_ptr, idx_ptr, upd_ptr, yacc_ptr, numData, numUpdates,
                innerSize, uDimSize, dataDimSize, reduceMode);
        } else if (idx_dtype == at::kLong) {
            scatter_kernel_f16reduce<half, int64_t><<<numBlocks, nullptr, aclStream>>>(
                data_ptr, idx_ptr, upd_ptr, yacc_ptr, numData, numUpdates,
                innerSize, uDimSize, dataDimSize, reduceMode);
        } else {
            TORCH_CHECK(false, "op_scatter::scatter unsupported indices dtype for fp16 reduce: ", idx_dtype);
        }
        y.copy_(yacc);  // fp32 -> fp16 cast (generic cast, not a scatter op)
        return y;
    }

    // dispatch by (data dtype, indices dtype)
    #define DISPATCH(T_CPP, IDX_CPP, DT_ENUM, IDX_ENUM) \
        if (dtype == (DT_ENUM) && idx_dtype == (IDX_ENUM)) { \
            scatter_kernel<T_CPP, IDX_CPP><<<numBlocks, nullptr, aclStream>>>( \
                data_ptr, idx_ptr, upd_ptr, y_ptr, numData, numUpdates, \
                innerSize, uDimSize, dataDimSize, reduceMode); \
            return y; \
        }

    // float32
    DISPATCH(float,    int32_t, at::kFloat,    at::kInt)
    DISPATCH(float,    int64_t, at::kFloat,    at::kLong)
    // float16 (overwrite only here; reduce handled above)
    DISPATCH(half,     int32_t, at::kHalf,     at::kInt)
    DISPATCH(half,     int64_t, at::kHalf,     at::kLong)
    // bfloat16: use `half` as a 2-byte container (overwrite only, guarded above).
    DISPATCH(half,     int32_t, at::kBFloat16, at::kInt)
    DISPATCH(half,     int64_t, at::kBFloat16, at::kLong)
    // int32
    DISPATCH(int32_t,  int32_t, at::kInt,      at::kInt)
    DISPATCH(int32_t,  int64_t, at::kInt,      at::kLong)
    // int64
    DISPATCH(int64_t,  int32_t, at::kLong,     at::kInt)
    DISPATCH(int64_t,  int64_t, at::kLong,     at::kLong)
    #undef DISPATCH

    TORCH_CHECK(false, "op_scatter::scatter unsupported dtype combination: data=", dtype,
                " indices=", idx_dtype);
    return y;
}
```

## 设计决策

- 选择 FP32 独立 accumulator，而不是继续用输出 FP16 张量承载中间态：失败信号集中在相消位置的 MARE，说明必须减少中间量化次数；
- overwrite 不路由到 accumulator：它没有算术归约，字节级写入本身是精确的，增加 FP32 buffer 只会引入无必要的转换；
- FP32 accumulator 是已验证的 FP16 scatter-add 数值基线；它使用额外 FP32 GM 缓冲和一次最终转换，本轨迹没有证明其性能最优；
- 被否路线仅是 FP16 add 的逐次读改写；补偿求和、分段归约、Reg 向量路线、多核冲突处理以及其他 reduce 模式均未验证。

## 系统信息

- 平台：Ascend950PR_957b / dav-3510；
- 工具链：CANN 9.0.1、Bisheng Ascend C 编译器；
- 工程入口：`operators/scatter/scatter.asc`；
- 关键符号：`scatter_kernel`、`scatter_kernel_f16reduce`、`op_scatter::scatter`；
- 验证入口：远端 helper 的 build、test、eval 动作；所有 CANN/NPU 命令在指定容器和物理卡 6 上执行。

## 性能影响

本轨迹没有给出 native FP16 add 逐次回写与 FP32 accumulator 的成对相对性能数据，不能量化性能代价。代码形态上，修复新增一个与输出同 shape 的 FP32 GM 缓冲以及一次最终 FP32→FP16 转换；它是数值正确性基线，不包含性能结论。

## 预防

- 看到 FP16 indexed reduce / scatter-reduce 时，先检查 accumulator 的真实存储 dtype，而不只检查计算表达式是否写了 `float`；
- 若实现每轮都把中间和写回 FP16 GM，按 `qⱼ₊₁=fp16(qⱼ+updateⱼ)` 分析逐步量化，而不是按“最后才 cast”估计误差；
- 正确性评测同时观察 MERE、MARE 和相消兜底；“MERE 很小”不能覆盖相消位置的高 MARE；
- widening 应落在中间状态：输入提升到 FP32、FP32 内完成全部归约、最后一次转回输出 dtype；
- 修复后必须重跑相同全量精度评测，不能通过放宽阈值、删除失败输入或更换 metric 放行。

## 验证信号

来源于一次 Ascend950 scatter 自定义算子开发：修复前全量 cann-bench 正确性评测定位到两条 FP16 add 输入；代码提交后通过同一远端 helper 重新构建、运行测试并重复全量评测。

- 修复前一条 FP16 add 输入为 `MERE=2.626815e-05, MARE=0.160997`，MARE 超过 `0.009765625` 阈值（来源平台: 950；证据等级: tool_observed）；
- 修复前另一条 FP16 add 输入为 `MERE=1.509420e-05, MARE=0.020576`，MARE 超过 `0.009765625` 阈值（来源平台: 950；证据等级: tool_observed）；
- 修复后的代码在 CANN 9.0.1 上构建为 `libop_scatter.so`，构建日志为 0 error；小规模测试为 139 passed（来源平台: 950；证据等级: tool_observed）；
- 同一 helper 重跑全量 cann-bench 后 20/20 通过，最终报告中两条此前失败的 FP16 add 输入精度误差均为 `0.000000`（来源平台: 950；证据等级: tool_observed）。

- 独立复现 R1：修复把 fp16 reduce 从逐次 half 读改写改为 fp32 中间缓冲累加，并在 host 侧最终转换回 fp16；修复后构建 0 error、测试 139 passed。（950，tool_observed）。

## 失效边界

- 只在 950 / dav-3510 / CANN 9.0.1 上验证；A2、A3 与其他 CANN 版本未验证，推断可迁移；
- 只对本轨迹的 FP16 scatter reduce 语义完成闭环；其他 operator family 需要重新核对更新顺序、重复索引与原子冲突；
- BF16 reduce 未实现，不能把 `half` 作为 BF16 算术容器；
- FP32 accumulator 仍不是任意规模累加的无限精度解法；极长归约链、极端动态范围或严格 bit-exact 契约需另行验证；
- 多核/原子 scatter 若改变更新顺序，数值误差与确定性必须单独评估。

## 坏实践

- 让 FP16 输出 GM 同时充当归约 accumulator，每个 update 后都写回 half；这会把一次最终 cast 变成多次中间量化；
- 只看 MERE 很小就判定精度可接受，忽略 MARE 与相消检查；
- 通过调松阈值、删除失败输入、跳过 FP16 reduce 或改参考 oracle 让测试通过；这些是测试侧放松，不是实现修复；
- 把 FP16 scatter-add 的 FP32 accumulator 结论外推到 BF16、multiply、amin 或 amax，或宣传为性能 fast path。

## 误诊

“绝对误差很小，因此 FP16 累加足够”是误诊。相消位置的参考结果接近 0 时，同一绝对误差会对应很高的相对误差；应同时检查 MARE 与相消兜底信号。