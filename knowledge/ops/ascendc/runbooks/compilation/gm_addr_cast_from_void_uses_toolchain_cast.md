---
type: "Runbook"
title: "dav-3510 GM_ADDR static_cast 编译失败"
description: "dav-3510 ASC 编译器拒绝 void* 到 __gm__ 地址空间指针的 static_cast；direct-launch host 入口改用 GM_ADDR C 风格转换。"
tags: ["task.debugging", "topic.implementation", "topic.data_movement.memory_access"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# dav-3510 GM_ADDR static_cast 编译失败

## 现象

在为 Ascend950 `dav-3510` 构建单文件 direct-launch Ascend C 工程时，开发者已经把 device kernel、tiling 与 PyTorch host 入口写进 `gather.asc`，随后通过远程 helper 触发 CMake/ASC 编译。编译停在 host 函数 `op_gather::gather` 将 `at::Tensor::data_ptr()` 交给 kernel launch 的位置，四个输入都报同一错误：

```text
gather.asc:317:18: error: static_cast from 'void *' to '__gm__ uint8_t *' (aka '__gm__ unsigned char *') casts away qualifiers
auto x_ptr = static_cast<GM_ADDR>(xP.data_ptr());
                 ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
gather.asc:318:20: error: static_cast from 'void *' to '__gm__ uint8_t *' (aka '__gm__ unsigned char *') casts away qualifiers
auto idx_ptr = static_cast<GM_ADDR>(idxP.data_ptr());
                   ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
```

编译器同时展开 `GM_ADDR` 为 `__gm__ uint8_t*`，并指出 `__gm__` 对应 `cce_global` 属性；因此故障发生在 host 指针到 Ascend C GM 地址空间指针的适配层，尚未进入 kernel 运行。

## 适用场景

- 工程形态：Ascend C 单文件 direct-launch / PyTorch 扩展，host 入口直接用 `<<<...>>>` 启动 kernel；
- API 路径：`at::Tensor::data_ptr()` → `GM_ADDR` → 模板 kernel launch；
- 验证过的平台与 CANN 版本：Ascend950 / `dav-3510`，CANN 9.0.1，与 frontmatter `platforms: [950]` 一致；
- 适用粒度：`platform_wide`，结论约束同一 CANN/Bisheng 工具链里的 host→GM 指针转换，不依赖 gather 数学语义；
- 路线优先级：`recommended_fastpath`，这是本轨迹中唯一经编译器验证可通过的 GM_ADDR 转换写法；
- 明确不适用 / 未验证场景：普通 CPU C++ 编译单元、没有 `__gm__` 地址空间限定的指针、CANN 9.0.1 之外版本，以及 A2/A3 工具链均未验证。

## 根因

在 dav-3510 的 ASC 编译单元里，`GM_ADDR` 展开为带 `__gm__`/`cce_global` 地址空间限定的 `uint8_t*`，Bisheng 不接受用 C++ `static_cast` 把普通 `void*` 建立为该限定指针并据此报出 `casts away qualifiers`。

## 解决配方

保留 host 入口的 tensor、metadata、tiling 与 dtype 分发逻辑，只把四个 `data_ptr()` 到 `GM_ADDR` 的转换从 `static_cast<GM_ADDR>(...)` 改成工具链参考形态 `(GM_ADDR)...`。

### before

代码来源说明：修复前完整 `file_write` 经同轨迹中先发生的 UB 分母 exact edit 重建；revision 短哈希 `af67593`，仓库相对路径 `operators/gather/gather.asc`，symbol `op_gather::gather`，行段 274–350。40 位 revision 与精确 blob URL 未在 trace 中恢复，正式发布前需补齐。

```cpp
at::Tensor gather(const at::Tensor& x, const at::Tensor& index, int64_t dim)
{
    TORCH_CHECK(x.dim() == index.dim(),
                "x and index must have the same number of dimensions.");
    TORCH_CHECK(dim >= 0 && dim < x.dim(),
                "dim is out of range [0, x.dim()).");
    TORCH_CHECK(index.scalar_type() == at::kChar || index.scalar_type() == at::kInt ||
                index.scalar_type() == at::kLong,
                "index must be int8/int32/int64.");
    TORCH_CHECK(x.scalar_type() != at::kBool, "gather does not support bool x dtype.");

    const c10::OptionalDeviceGuard guard(x.device());
    auto aclStream = c10_npu::getCurrentNPUStream().stream(false);

    const int64_t ndim = x.dim();
    const int64_t nLead = ndim - 1;

    // permute gather axis to last so each source row is contiguous
    std::vector<int64_t> perm;
    perm.reserve(static_cast<size_t>(ndim));
    for (int64_t i = 0; i < ndim; ++i) if (i != dim) perm.push_back(i);
    perm.push_back(dim);
    std::vector<int64_t> invPerm(static_cast<size_t>(ndim));
    for (int64_t i = 0; i < ndim; ++i) invPerm[perm[i]] = i;

    at::Tensor xP = x.permute(perm).contiguous();
    at::Tensor idxP = index.to(at::kInt).permute(perm).contiguous();  // normalize index to int32
    at::Tensor yP = at::empty(idxP.sizes(), xP.options());

    const int64_t S = x.size(dim);        // gather axis size = xP last dim
    const int64_t L = index.size(dim);    // output row length = idxP last dim
    const int64_t outNumel = index.numel();
    const int64_t numRows = (L == 0) ? 0 : outNumel / L;

    // metadata (CPU -> H2D on the same stream, ordered before the kernel)
    at::Tensor metaCpu = at::empty({META_LEN_I64}, at::device(at::kCPU).dtype(at::kLong));
    int64_t* m = metaCpu.data_ptr<int64_t>();
    build_meta(xP, idxP, dim, ndim, nLead, m);
    at::Tensor metaNpu = metaCpu.to(at::device(x.device()).dtype(at::kLong));

    const int64_t szT = x.element_size();
    GatherTiling t = calc_gather_tiling_params(numRows, S, szT);

    auto x_ptr = static_cast<GM_ADDR>(xP.data_ptr());
    auto idx_ptr = static_cast<GM_ADDR>(idxP.data_ptr());
    auto y_ptr = static_cast<GM_ADDR>(yP.data_ptr());
    auto meta_ptr = static_cast<GM_ADDR>(metaNpu.data_ptr());
    auto tile = static_cast<uint32_t>(t.tileElems);
    auto nl = nLead;
    auto pa = static_cast<int64_t>(t.pathA ? 1 : 0);

    const auto dtype = x.scalar_type();
    if (dtype == at::kHalf) {
        gather_kernel<half><<<t.numBlocks, nullptr, aclStream>>>(
            x_ptr, idx_ptr, y_ptr, meta_ptr, S, L, numRows, t.rowsPerBlock, tile, nl, pa);
    } else if (dtype == at::kFloat) {
        gather_kernel<float><<<t.numBlocks, nullptr, aclStream>>>(
            x_ptr, idx_ptr, y_ptr, meta_ptr, S, L, numRows, t.rowsPerBlock, tile, nl, pa);
    } else if (dtype == at::kBFloat16) {
        gather_kernel<bfloat16_t><<<t.numBlocks, nullptr, aclStream>>>(
            x_ptr, idx_ptr, y_ptr, meta_ptr, S, L, numRows, t.rowsPerBlock, tile, nl, pa);
    } else if (dtype == at::kChar) {  // int8
        gather_kernel<int8_t><<<t.numBlocks, nullptr, aclStream>>>(
            x_ptr, idx_ptr, y_ptr, meta_ptr, S, L, numRows, t.rowsPerBlock, tile, nl, pa);
    } else if (dtype == at::kInt) {
        gather_kernel<int32_t><<<t.numBlocks, nullptr, aclStream>>>(
            x_ptr, idx_ptr, y_ptr, meta_ptr, S, L, numRows, t.rowsPerBlock, tile, nl, pa);
    } else if (dtype == at::kLong) {
        gather_kernel<int64_t><<<t.numBlocks, nullptr, aclStream>>>(
            x_ptr, idx_ptr, y_ptr, meta_ptr, S, L, numRows, t.rowsPerBlock, tile, nl, pa);
    } else {
        TORCH_CHECK(false, "op_gather::gather unsupported dtype: ", dtype);
    }

    at::Tensor y = yP.permute(invPerm).contiguous();
    return y;
}
```

### after

代码来源说明：同一完整函数经 exact edit 重建，并在短哈希 `d71e48f` 固化后再次远程编译；仓库相对路径 `operators/gather/gather.asc`，symbol `op_gather::gather`，行段 274–350。40 位 revision 与精确 blob URL 未在 trace 中恢复，正式发布前需补齐。

```cpp
at::Tensor gather(const at::Tensor& x, const at::Tensor& index, int64_t dim)
{
    TORCH_CHECK(x.dim() == index.dim(),
                "x and index must have the same number of dimensions.");
    TORCH_CHECK(dim >= 0 && dim < x.dim(),
                "dim is out of range [0, x.dim()).");
    TORCH_CHECK(index.scalar_type() == at::kChar || index.scalar_type() == at::kInt ||
                index.scalar_type() == at::kLong,
                "index must be int8/int32/int64.");
    TORCH_CHECK(x.scalar_type() != at::kBool, "gather does not support bool x dtype.");

    const c10::OptionalDeviceGuard guard(x.device());
    auto aclStream = c10_npu::getCurrentNPUStream().stream(false);

    const int64_t ndim = x.dim();
    const int64_t nLead = ndim - 1;

    // permute gather axis to last so each source row is contiguous
    std::vector<int64_t> perm;
    perm.reserve(static_cast<size_t>(ndim));
    for (int64_t i = 0; i < ndim; ++i) if (i != dim) perm.push_back(i);
    perm.push_back(dim);
    std::vector<int64_t> invPerm(static_cast<size_t>(ndim));
    for (int64_t i = 0; i < ndim; ++i) invPerm[perm[i]] = i;

    at::Tensor xP = x.permute(perm).contiguous();
    at::Tensor idxP = index.to(at::kInt).permute(perm).contiguous();  // normalize index to int32
    at::Tensor yP = at::empty(idxP.sizes(), xP.options());

    const int64_t S = x.size(dim);        // gather axis size = xP last dim
    const int64_t L = index.size(dim);    // output row length = idxP last dim
    const int64_t outNumel = index.numel();
    const int64_t numRows = (L == 0) ? 0 : outNumel / L;

    // metadata (CPU -> H2D on the same stream, ordered before the kernel)
    at::Tensor metaCpu = at::empty({META_LEN_I64}, at::device(at::kCPU).dtype(at::kLong));
    int64_t* m = metaCpu.data_ptr<int64_t>();
    build_meta(xP, idxP, dim, ndim, nLead, m);
    at::Tensor metaNpu = metaCpu.to(at::device(x.device()).dtype(at::kLong));

    const int64_t szT = x.element_size();
    GatherTiling t = calc_gather_tiling_params(numRows, S, szT);

    auto x_ptr = (GM_ADDR)xP.data_ptr();
    auto idx_ptr = (GM_ADDR)idxP.data_ptr();
    auto y_ptr = (GM_ADDR)yP.data_ptr();
    auto meta_ptr = (GM_ADDR)metaNpu.data_ptr();
    auto tile = static_cast<uint32_t>(t.tileElems);
    auto nl = nLead;
    auto pa = static_cast<int64_t>(t.pathA ? 1 : 0);

    const auto dtype = x.scalar_type();
    if (dtype == at::kHalf) {
        gather_kernel<half><<<t.numBlocks, nullptr, aclStream>>>(
            x_ptr, idx_ptr, y_ptr, meta_ptr, S, L, numRows, t.rowsPerBlock, tile, nl, pa);
    } else if (dtype == at::kFloat) {
        gather_kernel<float><<<t.numBlocks, nullptr, aclStream>>>(
            x_ptr, idx_ptr, y_ptr, meta_ptr, S, L, numRows, t.rowsPerBlock, tile, nl, pa);
    } else if (dtype == at::kBFloat16) {
        gather_kernel<bfloat16_t><<<t.numBlocks, nullptr, aclStream>>>(
            x_ptr, idx_ptr, y_ptr, meta_ptr, S, L, numRows, t.rowsPerBlock, tile, nl, pa);
    } else if (dtype == at::kChar) {  // int8
        gather_kernel<int8_t><<<t.numBlocks, nullptr, aclStream>>>(
            x_ptr, idx_ptr, y_ptr, meta_ptr, S, L, numRows, t.rowsPerBlock, tile, nl, pa);
    } else if (dtype == at::kInt) {
        gather_kernel<int32_t><<<t.numBlocks, nullptr, aclStream>>>(
            x_ptr, idx_ptr, y_ptr, meta_ptr, S, L, numRows, t.rowsPerBlock, tile, nl, pa);
    } else if (dtype == at::kLong) {
        gather_kernel<int64_t><<<t.numBlocks, nullptr, aclStream>>>(
            x_ptr, idx_ptr, y_ptr, meta_ptr, S, L, numRows, t.rowsPerBlock, tile, nl, pa);
    } else {
        TORCH_CHECK(false, "op_gather::gather unsupported dtype: ", dtype);
    }

    at::Tensor y = yP.permute(invPerm).contiguous();
    return y;
}
```

## 设计决策

- 选择 `(GM_ADDR)tensor.data_ptr()`：同一 dav-3510 编译命令已证明该写法能通过 `__gm__` 地址空间指针检查，且与工程参照中的 launch 形态一致；
- 放弃 `static_cast<GM_ADDR>`：编译器对四个指针一致拒绝，继续保留会阻断整个 `.asc` 翻译单元；
- `reinterpret_cast<GM_ADDR>` 未在本轨迹尝试，不能把它写成等价替代；
- 当前方案属于 `recommended_fastpath`：它只消除 host→GM 指针适配的编译阻塞，不改变 kernel 算法、tiling、dtype 分发或运行性能。

## 系统信息

- 目标：Ascend950PR_957b / `dav-3510`；
- 工具链：CANN 9.0.1，Bisheng/ASC 编译链；
- 工程形态：单文件 `gather.asc` + CMake direct-launch PyTorch 扩展；
- 相关文件：`operators/gather/gather.asc`；
- 相关 symbol：`op_gather::gather`；
- 编译产物：`libop_gather.so`。

## 预防

- 在 direct-launch host 入口审查所有 `data_ptr()`：目标参数若是 `GM_ADDR`，不要机械套用普通 C++ 的 `static_cast`；
- 编译报错同时出现 `void*`、`__gm__ uint8_t*` 与 `cce_global` 时，优先检查地址空间限定转换，而不是修改 kernel 模板参数；
- 在提交前用固化代码状态重新触发一次完整 ASC 编译，避免修复只停留在未提交工作树；
- 若要引入 `reinterpret_cast` 等替代写法，必须用目标 CANN 版本单独编译验证，不能按标准 C++ 直觉推断。

## 验证信号

来源为一次 Ascend950 direct-launch 算子开发中的首次完整实现构建、cast 精确修复和固化提交后复验；以下均为同一 trace 内工具输出。

- 修复工作树后，同一远程 dav-3510 构建完成 `Linking ASC shared library libop_gather.so` 与 `[100%] Built target op_gather`（证据等级: tool_observed；来源平台: 950 / dav-3510）；
- cast 修复固化到提交后再次远程构建，输出 `4 warnings generated`、`[100%] Linking ASC shared library libop_gather.so`、`[100%] Built target op_gather`（证据等级: tool_observed；来源平台: 950 / dav-3510）。

## 失效边界

- 本结论只在 CANN 9.0.1 的 `dav-3510` ASC 编译链实测；其他 CANN/Bisheng 版本可能改变地址空间转换规则；
- A2、A3 未验证，不能从本单轨迹推断相同 cast 行为；
- 若 API 直接返回带正确地址空间限定的类型，或 launch 参数不使用 `GM_ADDR`，本修复不适用；
- C 风格 cast 会弱化普通 C++ 的类型检查，只应局限在工具链要求的 `data_ptr()`→`GM_ADDR` 边界，不应扩散到其他指针转换。

## 坏实践

- 看到普通 C++ 项目偏好 `static_cast`，就不检查 Ascend C 的 `__gm__` 地址空间限定，机械替换所有 C 风格 cast；
- 只看编译输出末尾的 warning 而忽略前面的 `error:`，把未生成目标库误判为构建成功；
- 修复后只在未提交工作树构建一次，不检查 Git 中固化的代码仍是否保留失败写法。

## 误诊

- 该错误发生在 host 入口的指针类型适配，不是 device kernel 的计算、同步、UB 或精度问题；修改 kernel body 不会消除编译器对 `static_cast<GM_ADDR>` 的拒绝。

<!-- cannbot:related:start -->
## 相关

- [Gather 非 dim 维缩小时折叠步长错位](../precision/gather_non_axis_shape_shrink_requires_per_axis_source_strides.md)（`related`）：正确 GM cast 不保证地址计算正确，Gather 仍需按 axis stride 推导。
- [Gather算子快速入门](../../guides/getting_started/quick_start/simt_programming/gather_op_quick_start.md)（`related`）：Gather算子快速入门 与《dav-3510 GM_ADDR static_cast 编译失败》的实质衔接是：Gather 快速入门覆盖 SIMT kernel、host launch 和构建；所连 Gather API、维度/步长/地址空间错例和 SIMT 入口约束都直接作用于该示例的实现或验证。
- [GetPhyAddr const __gm__ 返回不可去 const](getphyaddr_const_gm_const.md)（`related`）：void*→__gm__ 需工具链接受的转换，同时仍必须保留目标 const。
- [Host workspace 需先 CPU 暂存再 H2D](host_workspace_uses_cpu_staging_before_h2d.md)（`related`）：Host workspace 需先 CPU staging 再 H2D，不能把普通 void* 直接当 GM 指针。
- [直调不可用 GET_TILING_DATA_WITH_STRUCT 宏](direct_invoke_unavailable_get_tiling_data_with_struct.md)（`related`）：本卡明确把 void* 到 GM_ADDR/typed __gm__ 的转换列为独立次要编译项；目标卡给出 dav-3510 直调 host 边界上 static_cast 被拒及工具链可接受写法。
- [连续直调异常可用 stream(true) 做同环境 A/B](direct_launch_requires_empty_task_queue_stream.md)（`related`）：指针转换修复后 direct launch 仍需满足 stream/task queue 条件。
- [GM_ADDR 标量不可解引用为 tiling 结构体指针](gm_addr_tiling.md)（`same_topic`）：GM_ADDR 标量不可解引用为 tiling 结构体指针 与《dav-3510 GM_ADDR static_cast 编译失败》的实质衔接是：GM_ADDR 在该入口是 __gm__ uint8_t 标量而非结构体指针；typed __gm__ tiling 指针、Kernel Tiling/GET_TILING_DATA 和地址空间案例给出正确入口与强转边界。
- [混合 SIMT 启动边界用 GM_ADDR 承接地址空间](mixed_simt_launch_boundary_uses_gm_addr.md)（`same_topic`）：《dav-3510 GM_ADDR static_cast 编译失败》明确“dav-3510 ASC 编译器拒绝 void* 到 __gm__ 地址空间指针的 static_cast；direct-launch host 入口改用 GM_ADDR C 风格转换。”；它与《混合 SIMT 启动边界用 GM_ADDR 承接地址空间》的“混合 SIMT 的 host launch 实参先以 GM_ADDR 穿过 __global__ wrapper，再在 device 侧恢复具体 __gm__ 指针，避免地址空间类型转换失败。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
