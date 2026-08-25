---
type: "Runbook"
title: "507035 — 三队列 float32 tile 超 UB"
description: "Ascend950/dav-3510 上多 TQue+双缓冲+大固定 tile 的 float32 Reg kernel 运行期抛 ACL 507035；用同环境对照算子+缩 tile 探针二分定位为每核 UB 超额，而非 D2H 拷贝故障。"
tags: ["task.debugging", "topic.memory", "topic.tiling"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
aliases: ["TPipe::InitBuffer"]
---

# 507035 — 三队列 float32 tile 超 UB

## 现象

在 Ascend950PR_9579（NpuArch dav-3510）上为 masked_scale（`y = x * mask * scale`）写了一个**纯 float32、用 AscendC::Reg API** 的 kernel：3 个 `TQue`（inQueueX_ / inQueueMaskF_ / outQueueZ_，均 `PIPELINE_DEPTH=2`），tiling 固定 `FIXED_TILE_ELEMS=16384`。编译、`bash build.sh --install` 均成功；运行本地 `pytest tests/masked_scale/` 时**全量失败**，报：

```
FAILED ...::test_masked_scale_operator[shape5-dtype_combo1] - RuntimeError: copy_between_host_and_device_opapi:torch_npu/csrc/aten/ops/op_api/CopyKernelOpApi.cpp:57 NPU function error: device error type 3, error code is 507035
...
================== 80 failed, 1 passed, 14 warnings in 11.76s ==================
```

错误名 `copy_between_host_and_device_opapi` 极具误导性（看似 D2H 拷贝失败）。用 32 元素 / 8 元素最小用例复现，`torch.npu.synchronize()` 直接抛 507035；同进程同环境调用 `cann_bench.exp(x)`（同仓 exp 算子，1024×1024 float32）正常返回 `exp OK: tensor([[1.6654, 3.2601], ...])`，排除 NPU 硬件/驱动故障。最终把 `FIXED_TILE_ELEMS` 从 16384 改为 4096 后，32 元素与 1M 元素用例均 OK，本地 81 passed。

## 适用场景

- **工程形态**：ops-direct-invoke-flash 核函数构建（直接 Launch，非 aclnn 算子仓），`__global__ __aicore__ __vector__` kernel + `AscendC::Reg` 向量计算。
- **API 路径**：`AscendC::TQue<TPosition,DEPTH>` + `pipe_.InitBuffer(que, DEPTH, tileSize*sizeof(T))` + `AscendC::Reg::LoadAlign/Mul/Muls/StoreAlign`；`asc_vf_call<...>` 进 `__simd_vf__` 函数。
- **验证平台与版本**：Ascend950PR_9579 / NpuArch dav-3510（CANN 9.1.0，tikcpp impl 路径 `/home/developer/Ascend/cann-9.1.0/x86_64-linux/tikcpp/tikcfw/impl/dav_3510/`）。仅此平台实测。
- **适用粒度**：`operator_family`——任何在 dav-3510 上用多 TQue + 双缓冲 + 大固定 tile 的元素级 elementwise Reg kernel 都可能踩同一 UB 超额。
- **路线优先级**：`recommended_fastpath`——把 tile 纳入 UB 预算约束（见判别方法机制解释），从源头避免 507035。
- **不适用/未验证场景**：a2/a3 未验证（推断可迁移，见失效边界）；非 dav-3510 平台的 UB 容量不同，算式需按目标平台重算。

## 判别方法

**触发条件**：在 dav-3510 上运行多 TQue + 双缓冲 + 大固定 tile 的 float32 Reg kernel，`build.sh` 编译成功、`pytest` 运行期抛 `RuntimeError: copy_between_host_and_device_opapi ... device error type 3, error code is 507035`，且最小用例（8/32 元素）`torch.npu.synchronize()` 同样抛 507035。错误名指向 D2H 拷贝路径，具有强误导性——需用下述探针二分定位真正根因。

**可执行探针**（三步二分）：
1. **同环境对照算子**：同进程同环境调用一个已知正常的同仓算子（如 `cann_bench.exp(x)`，1024×1024 float32），看是否正常返回。
   - 若 exp 正常 → 排除 NPU 硬件/驱动故障，问题在自家 kernel。
   - 若 exp 也报错 → 先查硬件/驱动，不在本卡范围。
2. **最小用例复现**：用 8/32 元素最小输入跑 `torch.npu.synchronize()`，确认 507035 仍复现（排除大 shape 才触发的边界）。
3. **tile 缩减对照**：把 tiling 函数的 `FIXED_TILE_ELEMS` 从 16384 改为 4096，重编重跑同一 pytest：
   - 若缩 tile 后 507035 消失、全量 passed → 确诊根因为 UB 容量超额。
   - 若缩 tile 后仍 507035 → 排除 UB 预算，改查 TBuf 生命周期 / GM 越界等其他 507035 路径。

```cpp
// 探针改动点（tiling 函数内，单行常量）：
//   constexpr static uint32_t FIXED_TILE_ELEMS = 16384;  // 触发 507035
constexpr static uint32_t FIXED_TILE_ELEMS = 4096;      // 探针：缩 tile 后通过
```

**原始观测**（Ascend950/dav-3510，masked_scale float32 Reg kernel，单 trace 多轮）：
- tile=16384 时 `pytest tests/masked_scale/` 80 failed/1 passed，全部 `RuntimeError: ... error code is 507035`；32/8 元素最小用例 `torch.npu.synchronize()` 同样抛 507035。
- 同进程 `cann_bench.exp(x)`（1024×1024 float32）返回 `exp OK: tensor([[1.6654, 3.2601], [0.3272, 1.2985]])`，证明 NPU 硬件正常。
- tile=4096 后 32 元素与 1M 元素用例均 OK，本地 `pytest tests/masked_scale/` `81 passed, 14 warnings in 19.22s`。
- 官方评测 `run_evaluation.sh --operator MaskedScale` 精度 20/20 通过。

**机制解释**：dav-3510 每核 UB 容量有限（本 trace 推算为 256 KiB）。该 kernel 的 UB 占用为：

```
UB占用 = 队列数 × PIPELINE_DEPTH × FIXED_TILE_ELEMS × sizeof(元素)
       = 3        × 2               × 16384          × 4 B
       = 393216 B = 384 KiB  > 256 KiB（每核 UB 上限）
```

三个 TQue（x/mask/z 各一）× 双缓冲 × 16384 元素 × float32(4B) = 384 KiB，超过每核 UB；`pipe_.InitBuffer` 在编译期无法静态拒绝（tile 是 `constexpr` 但 UB 预算约束未在 API 层强制），运行期 kernel launch 后硬件访问越界 UB，最终以 `device error type 3, error code 507035` 经 D2H 拷贝路径抛出。把 tile 降到 4096 后：

```
3 × 2 × 4096 × 4 B = 98304 B = 96 KiB  < 256 KiB  → 通过
```

注意 `copy_between_host_and_device_opapi` 是错误呈现路径，不是根因——真正越界的是 kernel 对 UB 的访问，D2H 只是把 device 上已发生的 507035 传播回 host。这是 507035 在 dav-3510 上的多义性：同一错误码可由 UB 超额、TBuf 未初始化、GM 越界等多种根因触发，必须用上述「对照算子 + 最小用例 + 缩 tile」三步探针二分定位，不可凭错误名直判。

## 验证信号

- tile=16384 时 `pytest tests/masked_scale/` 80 failed/1 passed，全部 `RuntimeError: ... error code is 507035`；32/8 元素最小用例 `torch.npu.synchronize()` 同样 507035（来源平台：Ascend950/dav-3510；证据等级: tool_observed）
- 同进程 `cann_bench.exp(x)`（1024×1024 float32）返回 `exp OK: tensor([[1.6654, 3.2601], [0.3272, 1.2985]])`，证明 NPU 硬件正常（来源平台：Ascend950/dav-3510；证据等级: tool_observed）
- tile=4096 后 32 元素与 1M 元素用例均 `OK`，本地 `pytest tests/masked_scale/` `81 passed, 14 warnings in 19.22s`（来源平台：Ascend950/dav-3510；证据等级: tool_observed）
- 官方评测 `run_evaluation.sh --operator MaskedScale` 精度 20/20 通过（来源平台：Ascend950/dav-3510；证据等级: tool_observed）

## 失效边界

- 仅 Ascend950/dav-3510 实测；a2/a3 未验证，推断可迁移——但每核 UB 容量按目标平台规格重算后才能确定安全 tile。
- UB 预算算式随队列数、`PIPELINE_DEPTH`、dtype 字节数变化；若改双缓冲为单缓冲或减队列数，tile 上限可上调，需重新代入 `Nqueue×DEPTH×tile×sizeof(T) ≤ UB`。
- `copy_between_host_and_device_opapi` 错误名对本根因有强误导性；其他 507035 路径（如真 TBuf 未初始化、GM 越界）不归本卡，需独立判别。

## 误诊

agent 第一次命中 507035 时（kernel 含 `TBuf<VECCALC> tmpMaskFloat_` 用于 b16→float Cast），从 common-failure-modes 文档套用为「TBuf::Get<T>() 未在与 InitBuffer 相同的 `if constexpr` guard 内」，于是**移除整个 TBuf、把 b16→float 转换移到 plugin 侧 `x.to(torch::kFloat32)`**，重编后 507035 原样复现（80 failed/1 passed）。误判点：把 507035 等同于 TBuf 生命周期问题，忽略了 UB 预算这个更上游的约束。真正排障拐点是本卡判别方法的三步探针：同环境 `cann_bench.exp` 正常 → 问题在自家 kernel → 缩小 tile 立即通过，证明根因是 UB 容量而非 TBuf。

## 坏实践

- 把 507035 一律套用 common-failure-modes 的「TBuf Get() 未初始化」条目而盲改 TBuf，掩盖了 UB 预算这个真因，浪费一轮 rebuild+test。507035 在 dav-3510 上是多义信号，必须用最小用例 + 同环境对照算子 + 缩 tile 三步探针二分定位。
- 见 `copy_between_host_and_device_opapi` 错误名就归因为 D2H 拷贝故障——它只是 507035 的传播路径，真正越界发生在 kernel 对 UB 的访问。

## 预防

写多 TQue + 双缓冲 + 大固定 tile 的 elementwise Reg kernel 前，先代入 `Σ(队列数 × DEPTH × tileSize × sizeof(dtype)) ≤ 每核 UB` 选 tile；不要把 `copy_between_host_and_device_opapi`/507035 默认归因为 TBuf 生命周期或 D2H 拷贝，先用同环境已知正常算子（如 exp）排除硬件、再缩 tile 验证 UB 假设。

<!-- cannbot:related:start -->
## 相关

- [InitBuffer](../../apis/simd_api/basic_api/resource_management/t_pipe/init_buffer.md)（`exemplifies`）：507035 — 三队列 float32 tile 超 UB 与《InitBuffer》的实质衔接是：这些卡共享可复算的 UB 根因：队列/工作缓冲数量、对齐物理宽度或分块超过每核预算；TPipe InitBuffer是实际乘入 depth×bytes 的资源申请点。
- [TBufPool简介](../../apis/simd_api/basic_api/resource_management/t_buf_pool/t_buf_pool_intro.md)（`exemplifies`）：TBufPool简介 与《507035 — 三队列 float32 tile 超 UB》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
- [TBuf简介](../../apis/simd_api/basic_api/resource_management/t_buf/t_buf_intro.md)（`exemplifies`）：TBuf简介 与《507035 — 三队列 float32 tile 超 UB》的实质衔接是：TBuf 的构造、InitBuffer、Get/GetWithOffset 共同定义 UB 临时缓冲的分配与类型化取用；所连案例分别验证参数签名、地址独立性、容量预算和 helper 传参约束。
- [Cube tile k/n 超 L1/L0 上限报 INVALID_TILE](cube_tile_k_n_l1_l0_invalid_tile.md)（`related`）：该卡用缩 tile 二分定位 UB 超额，和 L1/L0 INVALID_TILE 一起提供各级片上存储容量越界的判别边界。
- [tmpBuffer 分配步长≠访问步长触发 UB 越界 341](tmpbuffer_ub_341.md)（`related`）：tmpBuffer 分配步长≠访问步长触发 UB 越界 341 与《507035 — 三队列 float32 tile 超 UB》的衔接是：四个案例都把 UB 预算、分块或对齐计算与实际访问跨度不一致定位为越界根因，可复用‘按访问类型和对齐重算最大偏移’的验证方法。
- [按 dtype 分配 UB 必须匹配 tiling 预算](dtype_conditional_ub_allocation_matches_tiling_budget.md)（`related`）：该卡提供缩 tile 后 507035 消失的容量探针，可在本卡计算 B_live 前快速确认错误属于 UB 超额而不是 GM 地址或同步。
- [避免TPipe在对象内创建和初始化](../../guides/operator_practice/simd_operator_optimization/overhead_optimization/avoid_tpipe_init_in_object.md)（`related`）：把 TPipe/多队列移出对象前仍需核算 UB；该卡提供 InitBuffer 累加定位 UB 超限的方法。
- [507035 C 超 per_buf_elems 致 Phase1 UB 越界](datacopypad_phase1_chunk_loop_per_buf_elems_507035.md)（`same_topic`）：焦点处理Phase1 中 C 超出 per_buf_elems 导致 UB 地址越界的预算故障；507035 — 三队列 float32 tile 超 UB正文说明“Ascend950/dav-3510 上多 TQue+双缓冲+大固定 tile 的 float32 Reg kernel 运行期抛 ACL 507035；用同环境对照算子+缩 tile 探针二分定位为每核 UB 超额，而非 D2H 拷贝故障”。候选与焦点共享 UB 容量/slot 预算机制，能直接修正切分因子、物理宽度或双缓冲计数。
- [507035 — Host 按逻辑行宽预算导致 UB 溢出](ub_budget_uses_aligned_physical_width_507035.md)（`same_topic`）：507035 — 三队列 float32 tile 超 UB 与《507035 — Host 按逻辑行宽预算导致 UB 溢出》的实质衔接是：这些卡共享可复算的 UB 根因：队列/工作缓冲数量、对齐物理宽度或分块超过每核预算；TPipe InitBuffer是实际乘入 depth×bytes 的资源申请点。
- [ACL 507035 — 完整 a0 统计缓冲超过 UB](ub_slices_reduction_axis_scratch_buffers_507035.md)（`same_topic`）：507035 — 三队列 float32 tile 超 UB 与《ACL 507035 — 完整 a0 统计缓冲超过 UB》的实质衔接是：这些卡共享可复算的 UB 根因：队列/工作缓冲数量、对齐物理宽度或分块超过每核预算；TPipe InitBuffer是实际乘入 depth×bytes 的资源申请点。
- [ACLNN 507015 — tiling UB 漏算 kIdxBuf 下溢](aclnn_507015_tiling_ub_kidxbuf.md)（`same_topic`）：507035 — 三队列 float32 tile 超 UB 与《ACLNN 507015 — tiling UB 漏算 kIdxBuf 下溢》的实质衔接是：这些卡共享可复算的 UB 根因：队列/工作缓冲数量、对齐物理宽度或分块超过每核预算；TPipe InitBuffer是实际乘入 depth×bytes 的资源申请点。
- [Reduce work buf 额外占 UB 致 507035](reduce_work_buf_ub_507035.md)（`same_topic`）：507035 — 三队列 float32 tile 超 UB 与《Reduce work buf 额外占 UB 致 507035》的实质衔接是：这些卡共享可复算的 UB 根因：队列/工作缓冲数量、对齐物理宽度或分块超过每核预算；TPipe InitBuffer是实际乘入 depth×bytes 的资源申请点。
<!-- cannbot:related:end -->
