---
type: "Runbook"
title: "Host workspace 需先 CPU 暂存再 H2D"
description: "torch_npu direct-launch host 用输入张量 options 创建 workspace 时继承 NPU device，随后 CPU 代码直接写 device pointer 导致进程崩溃；以 CPU staging 填充并在当前 stream 异步复制到 NPU 后恢复。"
tags: ["task.debugging", "topic.implementation.memory_management"]
status: stable
sources: []
created_at: "2026-08-14T03:54:37Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["a3"]
---

# Host workspace 需先 CPU 暂存再 H2D

## 现象

完整 `gather` kernel 已成功编译链接，但第一个本地 NPU pytest 在 `torch.ops.op_gather.gather` 内使 Python 进程崩溃。把调用缩减为 `float32` 输入、`int32` 索引的 tiny direct-call 并关闭 stdout 缓冲后，进程能打印输入 shape，却在算子返回前停止；结果比较逻辑尚未运行。

## 适用场景

- 工程形态：classic Ascend C 直调 kernel 的编译、链接或运行工程。
- API 路径：`TensorOptions`、`data_ptr`、`non_blocking`、`NPUStream` 所在的 kernel、host 或构建接口链。
- 验证平台与版本：平台 a3；CANN：unknown。
- 适用粒度：`same_operator`，仅迁移到同算子的 host 元数据构造与 H2D 生命周期。
- 路线优先级：`recommended_fastpath`。
- 不适用/停止边界：错误信号、API 契约或数据路径与本卡不一致时停止套用；修复后未闭合原信号则回到根因诊断。

## 根因

`x.options()` 继承输入 `x` 的 NPU device，因此名为 `wsHost` 的张量实际分配在 NPU；CPU 随后通过 `data_ptr<int64_t>()` 写该 device pointer，进程在 host 入口直接崩溃。

## 解决配方

显式用 CPU `TensorOptions` 创建 staging tensor，在 host 填充完整表后以 non-blocking 方式复制到输入 NPU；随后从 device 副本取得 `__gm__` 指针并在同一当前 stream 发射 kernel。`wsDev` 的局部生命周期覆盖 launch。

### before

```cpp
void launch_gather(const at::Tensor &xIn, const at::Tensor &indexIn, int64_t dim, const at::Tensor &y) {
    at::Tensor x = xIn.is_contiguous() ? xIn : xIn.contiguous();
    at::Tensor index = indexIn.is_contiguous() ? indexIn : indexIn.contiguous();
    int32_t ndim = static_cast<int32_t>(x.dim());
    int64_t outNumel = index.numel();

    // contiguous element strides of x
    std::vector<int64_t> xShape(ndim), xStrides(ndim), outShape(ndim);
    for (int32_t i = 0; i < ndim; ++i) {
        xShape[i] = x.size(i);
        outShape[i] = index.size(i);
    }
    xStrides[ndim - 1] = 1;
    for (int32_t i = ndim - 2; i >= 0; --i) {
        xStrides[i] = xStrides[i + 1] * xShape[i + 1];
    }

    // core count (F4.3 runtime query; aborts on failure — no hardcode/fallback)
    uint32_t aiv = QueryAivCores();
    uint32_t numBlocks = static_cast<uint32_t>(std::min<int64_t>(aiv, std::max<int64_t>(outNumel, 1)));
    int64_t perBlock = (outNumel + numBlocks - 1) / numBlocks;

    // copy shape/stride tables to device-readable GM
    at::Tensor wsHost = at::empty({2 * ndim}, x.options().dtype(at::kLong));
    int64_t *wsHostPtr = wsHost.data_ptr<int64_t>();
    for (int32_t i = 0; i < ndim; ++i) {
        wsHostPtr[i] = outShape[i];
        wsHostPtr[ndim + i] = xStrides[i];
    }
    at::Tensor wsDev = wsHost.to(x.device());

    aclrtStream aclStream = c10_npu::getCurrentNPUStream().stream(false);
    __gm__ int64_t *outShapePtr = (__gm__ int64_t *)wsDev.data_ptr<int64_t>();
    __gm__ int64_t *xStridesPtr = outShapePtr + ndim;
    __gm__ int64_t *xShapePtr = xStridesPtr;  // xShape not needed by device; alias safely

    auto xdt = x.scalar_type();
    auto idt = index.scalar_type();
#define LAUNCH(T_TYPE, IDX_TYPE)                                                      \
    LaunchOne<T_TYPE, IDX_TYPE>(x, index, y, dim, ndim, outNumel, numBlocks, perBlock, \
                                outShapePtr, xShapePtr, xStridesPtr, aclStream);      \
    break

#define X_CASE(T_ENUM, T_TYPE)                                            \
    case T_ENUM: {                                                        \
        switch (idt) {                                                   \
            case at::kChar: { LAUNCH(T_TYPE, int8_t); }                  \
            case at::kInt:  { LAUNCH(T_TYPE, int32_t); }                 \
            case at::kLong: { LAUNCH(T_TYPE, int64_t); }                 \
            default: TORCH_CHECK(false, "gather: unsupported index dtype ", idt); \
        }                                                                \
        break;                                                           \
    }

    switch (xdt) {
        X_CASE(at::kChar, int8_t)
        X_CASE(at::kHalf, half)
        X_CASE(at::kFloat, float)
        X_CASE(at::kBFloat16, bfloat16_t)
        X_CASE(at::kInt, int32_t)
        X_CASE(at::kLong, int64_t)
        default:
            TORCH_CHECK(false, "gather: unsupported x dtype ", xdt);
    }
#undef X_CASE
#undef LAUNCH
}
```

### after

```cpp
void launch_gather(const at::Tensor &xIn, const at::Tensor &indexIn, int64_t dim, const at::Tensor &y) {
    at::Tensor x = xIn.is_contiguous() ? xIn : xIn.contiguous();
    at::Tensor index = indexIn.is_contiguous() ? indexIn : indexIn.contiguous();
    int32_t ndim = static_cast<int32_t>(x.dim());
    TORCH_CHECK(ndim >= 1 && ndim <= 8, "gather: x.ndim must be in [1,8], got ", ndim);
    int64_t outNumel = index.numel();

    // contiguous element strides of x
    std::vector<int64_t> xShape(ndim), xStrides(ndim), outShape(ndim);
    for (int32_t i = 0; i < ndim; ++i) {
        xShape[i] = x.size(i);
        outShape[i] = index.size(i);
    }
    xStrides[ndim - 1] = 1;
    for (int32_t i = ndim - 2; i >= 0; --i) {
        xStrides[i] = xStrides[i + 1] * xShape[i + 1];
    }

    // core count (F4.3 runtime query; aborts on failure — no hardcode/fallback)
    uint32_t aiv = QueryAivCores();
    uint32_t numBlocks = static_cast<uint32_t>(std::min<int64_t>(aiv, std::max<int64_t>(outNumel, 1)));
    int64_t perBlock = (outNumel + numBlocks - 1) / numBlocks;

    // shape/stride tables: build on CPU (do NOT dereference an NPU pointer on host), then copy to device.
    at::Tensor wsHost = at::empty({2 * ndim}, at::TensorOptions().device(at::kCPU).dtype(at::kLong));
    int64_t *wsHostPtr = wsHost.data_ptr<int64_t>();
    for (int32_t i = 0; i < ndim; ++i) {
        wsHostPtr[i] = outShape[i];
        wsHostPtr[ndim + i] = xStrides[i];
    }
    // non-blocking H2D copy on the kernel stream; wsDev must outlive the launch.
    at::Tensor wsDev = wsHost.to(x.device(), /*non_blocking=*/true);

    aclrtStream aclStream = c10_npu::getCurrentNPUStream().stream(false);
    __gm__ int64_t *outShapePtr = (__gm__ int64_t *)wsDev.data_ptr<int64_t>();
    __gm__ int64_t *xStridesPtr = outShapePtr + ndim;

    auto xdt = x.scalar_type();
    auto idt = index.scalar_type();
#define LAUNCH(T_TYPE, IDX_TYPE)                                                      \
    LaunchOne<T_TYPE, IDX_TYPE>(x, index, y, dim, ndim, outNumel, numBlocks, perBlock, \
                                outShapePtr, xStridesPtr, aclStream);                  \
    break

#define X_CASE(T_ENUM, T_TYPE)                                            \
    case T_ENUM: {                                                        \
        switch (idt) {                                                   \
            case at::kChar: { LAUNCH(T_TYPE, int8_t); }                  \
            case at::kInt:  { LAUNCH(T_TYPE, int32_t); }                 \
            case at::kLong: { LAUNCH(T_TYPE, int64_t); }                 \
            default: TORCH_CHECK(false, "gather: unsupported index dtype ", idt); \
        }                                                                \
        break;                                                           \
    }

    switch (xdt) {
        X_CASE(at::kChar, int8_t)
        X_CASE(at::kHalf, half)
        X_CASE(at::kFloat, float)
        X_CASE(at::kBFloat16, bfloat16_t)
        X_CASE(at::kInt, int32_t)
        X_CASE(at::kLong, int64_t)
        default:
            TORCH_CHECK(false, "gather: unsupported x dtype ", xdt);
    }
#undef X_CASE
#undef LAUNCH
}
```

## 设计决策

1. staging tensor 必须显式指定 `at::kCPU`；变量名不能代替 device placement。
2. 完成 host 填充后再发起 non-blocking H2D，避免为小表加入全局同步；复制与 kernel launch 使用当前 torch_npu 执行序列。
3. `wsDev` 保持为 `launch_gather` 局部变量直到 kernel launch 返回；若改为跨 stream 或延迟消费，必须重新验证 allocator/stream 生命周期。
4. after 同时删除未使用的 `xShapePtr` 参数并限制 `ndim` 在 `[1,8]`；二者是邻接清理，不是本次崩溃根因。

## 系统信息

- Toolchain：CANN 9.2.0、bisheng、torch_npu；平台：a3/dav-2201；
- 输入与 index 均为 NPU tensor，shape/stride 表由 C++ host 计算；
- kernel 通过 `__gm__ int64_t*` 读取复制后的 workspace。

## 完整代码

解决配方已给出完整 `launch_gather` before/after，覆盖 workspace 的创建、host 填充、H2D、device 指针拆分与 kernel launch。

## 预防

- 对每个 host 侧 `data_ptr()` 写入点，先检查 tensor 的 `device()`；输入派生 options 默认继承 device。
- host 构造的小型控制表使用显式 CPU staging，再复制到目标 NPU。
- 异步复制后把 device tensor 的生命周期覆盖到同 stream 的最后一个 consumer。
- tiny direct-call 应在算子调用前后打印并关闭缓冲，用来区分 host 入口崩溃与结果比较失败。

## 验证信号

以下信号均来自本次开发会话修复前后的实际构建、运行或评测输出。

- 修复前：host workspace 路径发生 segmentation fault，EXIT=139。（来源平台：a3；证据等级: tool_observed）。
- 修复后：重新链接后 none/add 两条路径 allclose=true、EXIT=0。（来源平台：a3；证据等级: tool_observed）。
- 修复后：扩展用例逐项 OK，最终 DONE、EXIT=0。（来源平台：a3；证据等级: tool_observed）。

## 失效边界

- 本轨迹只验证当前 stream 的 H2D 与 launch；跨 stream 或缓存 workspace 到函数外需要额外事件与生命周期管理。
- 不要把该修复扩大为 pinned host memory 性能结论；轨迹没有比较 pageable 与 pinned staging。
- `ndim` 边界检查与删除未用参数虽然同补丁落地，但不能作为崩溃修复的必要条件。
- 其他平台注册平台与 CANN/torch_npu 版本未复测。

## 坏实践

- 用 `x.options()` 创建名为 host 的 tensor，再假设它位于 CPU。
- 在 CPU 代码中直接写 NPU tensor 的 `data_ptr()`。
- 为隐藏崩溃而删除异步路径或加入全局 synchronize，却不修正 device placement。

## 误诊

该崩溃发生在 kernel 返回前；在这条轨迹中不是 index 越界、dtype 分派或数值容差导致。

<!-- cannbot:related:start -->
## 相关

- [GetUserWorkspace](../../apis/simd_api/basic_api/resource_management/workspace/get_user_workspace.md)（`exemplifies`）：GetUserWorkspace 与《Host workspace 需先 CPU 暂存再 H2D》的实质衔接是：GetUserWorkspace 与 SetSysWorkSpace 分离用户区和系统区；workspace 指南、Matmul workspace 设置及 host staging/偏移故障说明地址从 host 到 kernel 的使用边界。
- [UpdateKfcWorkspace](../../apis/simd_api/basic_api/cube_group_mgmt/kfc_workspace/update_kfc_workspace.md)（`exemplifies`）：UpdateKfcWorkspace 与《Host workspace 需先 CPU 暂存再 H2D》的实质衔接是：UpdateKfcWorkspace 为 KfcWorkspace/CubeResGroupHandle 推进消息区地址，构造、Get 与 workspace 系统/用户分区共同约束 GM 空间生命周期和 host 传递。
- [RunOpApi 后缺 synchronize 致 .to 越序错](runopapi_requires_synchronize_before_tensor_ops.md)（`related`）：《RunOpApi 后缺 synchronize 致 .to 越序错》说明cummin 算子 op_plugin 在 OpCommand::RunOpApi 后、idx32.to(kInt64) 前缺 synchronize，导致 .to 在 kernel 完成前执行而产生错误输出；判别要点是 RunOpApi 后对同一输出张量的 torch 操作前须显式 sync。；《Host workspace 需先 CPU 暂存再 H2D》说明torch_npu direct-launch host 用输入张量 options 创建 workspace 时继承 NPU device，随后 CPU 代码直接写 device pointer 导致进程崩溃；以 CPU staging 填充并在当前 stream 异步复制到 NPU 后恢复。。二者在RunOpApi及异步H2D/临时张量操作只有在同一输出的后续Torch操作前建立设备完成点才安全上存在可执行的直接衔接。
- [at::zeros 异步零初始化跨 stream 覆盖 kernel 写出](../precision/at_zeros_stream_kernel.md)（`related`）：《at::zeros 异步零初始化跨 stream 覆盖 kernel 写出》说明kernel 直调算子的 host 层用 allocate_xpu_zeros_like（at::zeros）在 torch 默认 stream 异步零初始化输出 tensor，kernel launch 走 XpuRuntimeManager::get_ins<aclrtStream> 的 xpu_ops stream，两 stream 无同步；批量高负载下零初始化在 kernel 写入之后完成，整段 GM 写入覆盖 kv_a_out new 区。判别=BUGDIAG 按 region 分桶报 hist_zr=0 new_zr 非零 + 源码审查命中 allocate_xpu_zeros_like 且 kernel 在异 stream。；《Host workspace 需先 CPU 暂存再 H2D》说明torch_npu direct-launch host 用输入张量 options 创建 workspace 时继承 NPU device，随后 CPU 代码直接写 device pointer 导致进程崩溃；以 CPU staging 填充并在当前 stream 异步复制到 NPU 后恢复。。二者在at::zeros和直调kernel位于不同stream且无依赖，设备同步或同stream staging是防止零初始化覆盖写出的直接修复上存在可执行的直接衔接。
- [dav-3510 GM_ADDR static_cast 编译失败](gm_addr_cast_from_void_uses_toolchain_cast.md)（`related`）：Host workspace 需先 CPU staging 再 H2D，不能把普通 void* 直接当 GM 指针。
- [半精度 shadow 跨流竞态 — 转换与 kernel 两侧做设备同步](../precision/torch_npu_async_temporaries_need_completion_before_raw_kernel.md)（`related`）：Host workspace 卡解决 CPU 暂存到设备的所有权，目标卡进一步证明异步 H2D 临时张量在 raw kernel 读取前必须完成并保活。
<!-- cannbot:related:end -->
