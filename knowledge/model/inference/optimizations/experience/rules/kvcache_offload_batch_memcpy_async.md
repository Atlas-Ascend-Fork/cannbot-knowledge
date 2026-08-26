---
type: Optimization
title: KV offload block swap 把逐块逐子张量小拷贝聚成一次 aclrtMemcpyBatchAsync（版本门 + srcLoc/dstLoc 契约 + D2D 回退）
description: KV Cache offload 或 prefix 复用的 block swap 会产生大量 HBM↔Host 小拷贝，逐块、逐层调用 memcpy 时固定下发开销会推高 TTFT/TPOT。优化方法是把同方向且非 D2D 的源地址、目标地址和字节数平铺为三个 CPU int64 数组，再用 CANN 8.5 起提供的 aclrtMemcpyBatchAsync 一次提交，将调用开销从 O(n) 降为 O(1)。批量接口必须通过 aclrtMemcpyBatchAttr 的 srcLoc/dstLoc 声明 HOST/DEVICE 位置；CANN 低于 8.5 或 D2D 时回退逐条 aclrtMemcpyAsync。参考实现以编译探测控制能力并提供环境开关，自报 Qwen3-14B TP1 的 TTFT 307→272.82 ms、TPOT 49.96→41.04 ms，未独立复测。
tags:
- task.optimization
- topic.kv_cache
- topic.memory
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/7819
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- a2
---

# KV offload block swap 把逐块逐子张量小拷贝聚成一次 aclrtMemcpyBatchAsync（版本门 + srcLoc/dstLoc 契约 + D2D 回退）

## 适用场景

- 服务化 decode 下做 KV cache offload / prefix 复用：KV cache 要在 NPU HBM 与 CPU host 之间来回 block swap（HBM→host 的 D2H、host→HBM 的 H2D）。
- 每个 swap job 要搬的不是一大块连续内存，而是「若干 block × 每 layer 的 (key_cache, value_cache) 两个子张量」——block、layer、key/value 三个维度相乘后，实际拷贝笔数很大且每笔很小。
- 若实现对每个 (src_tensor, dst_tensor) 逐个提交一次 memcpy，则拷贝路径的瓶颈不在带宽而在**每笔拷贝独立的 API/kernel launch 开销**，笔数越多 launch 累计越重，体现在 TTFT / TPOT 抬高（decode_slow）。
- 前提：昇腾运行时提供批量拷贝原语。**批量拷贝 API `aclrtMemcpyBatchAsync` 属 CANN 8.5+**；更低版本或搬运方向为 device-to-device 时本规则退化为普通逐条异步拷贝。

判断通向本规则：当 offload 路径上「一次搬运 = 成百上千笔小拷贝」且 profile 显示 launch/host 侧开销占比高时，优先把这些同方向的小拷贝聚合成**一次**批量拷贝调用，而不是逐条发。

## 条件 → 优先尝试什么

**条件**：offload block swap 一次要发大量同方向、同为 host↔device 的小 memcpy，且拷贝方向 ≠ D2D，且运行时 CANN ≥ 8.5。
**优先**：把全部小拷贝平铺成三个 CPU 侧 int64 数组（各笔的源指针 / 目的指针 / 字节数），单次调用 `aclrtMemcpyBatchAsync` 一次性提交，削减 launch 次数。
**否则回退**：CANN < 8.5（无该 API）或方向为 D2D 时，逐条 `aclrtMemcpyAsync` 循环——功能等价、只是拿不到批量聚合收益。

### 为何有效（通用机制）

一批 n 笔小拷贝，逐条发要付 n 次 API/kernel launch 的固定开销；批量原语把这 n 笔用一份「指针数组 + 尺寸数组」一次提交，launch 固定开销从 O(n) 降到 O(1)，同时底层仍在同一 stream 上异步完成各笔搬运。小拷贝越碎（block × layer × key/value 维度乘积越大），聚合收益越明显。收益来源是减少小拷贝的 launch 次数。

## 参考实现及其约束（vLLM-Ascend `swap_blocks_batch`）

以下是 vLLM-Ascend（vLLM 的昇腾后端）`OffloadingConnector` / `NPUOffloadingSpec` 路径上的一份参考实现——即 [kv-cache-manager](../../../concepts/frameworks/kv_cache_manager.md) 负责调度的 HBM↔host block swap 步骤。以下接口/版本细节是该参考实现的约束。

- **批量算子 `swap_blocks_batch(src_ptrs, dst_ptrs, sizes, direction)`**（C++）：三个入参都是 **CPU 上的 int64 数组张量**，分别装各笔拷贝的源指针、目的指针、字节数；`direction` 取值 `0=H2D / 1=D2H / 2=D2D`。因为传的是**指针数组而非 NPU 张量**，算子注册在 **CPU backend**（`torch::kCPU`），函数内部在当前 NPU stream 上提交异步拷贝。
- **批量路径的 API 契约（diff 揭示、文档外不易得）**：`aclrtMemcpyBatchAttr` 用 **`srcLoc` / `dstLoc`（类型 `aclrtMemLocation`，字段 `type` = `ACL_MEM_LOCATION_TYPE_HOST` / `_DEVICE`，加一个 `id`）指定内存位置，而不是老式的 `aclrtMemcpyKind`**。H2D 时 `srcLoc`=host、`dstLoc`=device，D2H 相反；device 侧的 `id` 取自 `aclrtGetDevice`。调用形如 `aclrtMemcpyBatchAsync(dst_arr, dest_maxs, src_arr, size_arr, n, &attr, &attrs_index, 1, &fail_index, stream)`，一次完成全部 n 笔。
- **D2D 显式不走批量路径**：代码用 `if (memcpy_kind != ACL_MEMCPY_DEVICE_TO_DEVICE)` 守住，只有非 D2D 才走 batch API；device-to-device 落到 fallback 循环。
- **fallback 循环**：宏 `CANN_MEMCPY_BATCH_ASYNC` 未定义（CANN < 8.5）或方向为 D2D 时，对 n 笔逐条 `aclrtMemcpyAsync(dst, size, src, size, kind, stream)`。
- **编译期能力探测 + 手动开关**：CMake 用 `check_cxx_source_compiles` 编译一段同时引用 `aclrtMemcpyBatchAsync` 与 `aclrtMemcpyBatchAttr.srcLoc` 成员访问的探针，探针编译成功才定义 `CANN_MEMCPY_BATCH_ASYNC`。⚠️ 踩坑：**torch_npu 会 bundle 一份较旧的 `acl_rt.h`**（同处 PR 注释提到 torch_npu 2.9.0 的旧头缺 `aclrtLaunchHostFunc`），所以 CMake 里必须显式优先用 **CANN 自带的 ACL 头**而非 torch_npu 副本，否则探测会因旧头缺符号而误判为不支持。可用环境变量 `VLLM_ASCEND_ENABLE_BATCH_MEMCPY=1/0` 强制启/禁，unset 则走自动探测。
- **Python 侧向量化调用链**（`kv_offload/cpu_npu.py`）：`__init__` 阶段预计算所有子张量的 base `data_ptr()` 与每 block 字节数（`stride(0) * element_size()`）；`transfer_async` 用 numpy 广播**一次性**算出全部 (子张量 × block 对) 的平铺 `all_src / all_dst / all_sizes` 指针数组，再单次调 `swap_blocks_batch`。同方向的连续 transfer 用 `stream.wait_event(last_transfer.end_event)` 在 deque 里串起来，配可复用的 npu.Event 池计时/查询完成。

## 依据（支撑的 case）

一份 case：vLLM-Ascend 的 offload 路径按上法把逐块逐子张量小拷贝聚成单次批量拷贝。仓自报 benchmark（Qwen3-14B、TP=1、bfloat16、`--block-size 128`、`--no-enable-prefix-caching`、`num_cpu_blocks=1000`、multi-turn 8 clients / 24 active conversations）：TTFT 307ms → 272.82ms，TPOT 49.96ms → 41.04ms。⚠️ 数字为 PR 描述自报、无独立复测，仅作方向性佐证，不外推「批量越大越快」等规律。

## 反例 / 边界

- **拷贝方向为 D2D**：批量路径被显式跳过、只能逐条，本规则在 D2D 上不生效。
- **CANN < 8.5**：无 `aclrtMemcpyBatchAsync`，探针编译失败、宏不定义，回退逐条循环。
- **拷贝笔数很少或每笔很大**：launch 固定开销占比低时，聚合收益趋于零；聚合本身有构建指针数组的开销，碎拷贝多才划算。
- **与 [kvcache-offload](../../../concepts/techniques/kvcache_offload.md) 的三段式 host-swap 正交**：本规则治「一次搬运里的很多小拷贝笔数」，host-swap recipe 治「设备只驻单层 + 专用流 D2H 重叠」；同一条 offload 路径可同时用两者。

## Evidence

- diff 事实（vLLM-Ascend merge sha `aa8ac74984e2fbc07afbd19cb367b542ccc964b7`）：批量算子 `swap_blocks_batch`（`csrc/torch_binding.cpp`）、`CANN_MEMCPY_BATCH_ASYNC` 宏、`srcLoc` / `dstLoc` 契约、D2D 不走 batch、CMake `check_cxx_source_compiles` 编译期探测、`VLLM_ASCEND_ENABLE_BATCH_MEMCPY` 开关（`vllm_ascend/envs.py`）、Python `transfer_async` 向量化调用链（`vllm_ascend/kv_offload/cpu_npu.py`）。
- benchmark 数字为 PR 描述自报（doc 披露层）、无独立复测。
- 溯源下探：[vllm-ascend-pr-7819-performance-batch-kvcache-offloading-via-aclrtmemcpybatchasync](https://github.com/vllm-project/vllm-ascend/pull/7819)
