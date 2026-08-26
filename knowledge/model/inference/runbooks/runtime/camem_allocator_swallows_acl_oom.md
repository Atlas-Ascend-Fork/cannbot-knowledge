---
type: Runbook
title: 显存卸载分配器吞掉 ACL OOM 致下游非法地址崩溃：分配点即刻 throw 并按 ACL_ERROR_RT_MEMORY_ALLOCATION 明示 OOM
description: >-
  显存卸载或 KV cache offload 使用直接调用 ACL 的自管 HBM 分配器时，若
  aclrtMallocPhysical 或 aclrtReserveMemAddress 返回 ACL_ERROR_RT_MEMORY_ALLOCATION，
  分配路径却只打印错误并返回空指针，真正的 OOM 会延迟成下游非法地址或段错误。
  应在分配点统一抛出携带 ACL 错误码和源码位置的异常，并为该返回码明示 OOM 语义；
  映射、解映射和释放等其他 ACL 失败也应同样失败关闭。该签名适用于所有直接管理 HBM 的
  offload/swap 路径；若上层捕获异常后不退出进程，仍需显式回收已分配资源。
tags:
- task.debugging
- topic.kv_cache
- topic.memory
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/3932
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 显存卸载分配器吞掉 ACL OOM 致下游非法地址崩溃：分配点即刻 throw 并按 ACL_ERROR_RT_MEMORY_ALLOCATION 明示 OOM

## 信号（现象）

昇腾 NPU 推理进程在一个**看似与显存无关的非法地址访问**处崩溃（读写 `nullptr` / 野指针、segfault），栈顶落在某个下游 kernel 或算子里，看不出根因是「显存不够」。实际起点在上游一个**自管 HBM 的显存分配路径**（sleep-mode / 显存卸载 / KV cache 卸载所用的 CaMem 式分配器），该分配路径在 ACL 内存 API 返回失败时只往 `stderr` 打印一行 `acl Error, code: ...` 便 `return nullptr`（吞错继续），使真正的 OOM 既不在分配点报错、也没有 OOM 语义提示，被延迟并转移到下游解引用那个未成功分配的指针的时刻才暴露。

判读要点：当崩溃点是非法地址访问、且该进程用到 sleep-mode / 显存卸载 / offload-swap 一类**绕过框架显存池、直接调 ACL 驱动内存 API 自管 HBM** 的路径时，优先怀疑是上游 OOM 被吞、而非下游 kernel 本身有 bug。

## 触发条件

- 使用直接调 ACL 驱动内存 API 管理 NPU HBM 的自定义分配器：物理内存分配 `aclrtMallocPhysical`、虚拟地址空间预留 `aclrtReserveMemAddress`、映射 `aclrtMapMem`，以及对应的 `aclrtUnmapMem` / `aclrtFreePhysical` / `aclrtReleaseMemAddress`。这类分配器常见于 sleep-mode（把权重/激活换出到 host 再唤回）、KV cache 卸载等显存卸载路径（[kv-cache-manager](../../concepts/frameworks/kv_cache_manager.md)）。
- 实际 HBM 需求超过物理可用容量：`aclrtMallocPhysical` 或 `aclrtReserveMemAddress` 返回 `ACL_ERROR_RT_MEMORY_ALLOCATION`。
- 分配路径对 ACL 非 0 返回码只 `std::cerr` 打印后 `return`（`return nullptr` / `return void`），没有在分配点中断。

## 根因

C 风格的错误处理在自管内存分配器里退化成**吞错继续**：`aclrtMallocPhysical` / `aclrtReserveMemAddress` 已返回 `ACL_ERROR_RT_MEMORY_ALLOCATION`（即 NPU 侧 OOM——HBM 物理内存分配失败 / 地址空间预留失败），但调用方仅打印日志后返回一个未成功分配的指针（`nullptr` 或未映射地址）。上层拿到这个指针继续走，直到下游某处解引用/访问它，才以非法地址访问的形式崩溃。于是 OOM 的真实症状被延迟并转移到一个看似无关的崩溃点，掩盖了「其实是显存不足」这一根因，根因难以定位。这是一个**根因隐藏 / 错误传播延迟**的失败签名：报错点不是故障点。

`ACL_ERROR_RT_MEMORY_ALLOCATION` 是把「一般 ACL 失败」与「显存不足」区分开的关键返回码——只有它代表 OOM，其它非 0 码是普通 ACL 失败。

## 修法

核心原则：**分配失败必须在分配点立即以异常中断，携带足够定位信息，并对 OOM 给出明确语义**。

- 把分配器中所有「`cerr` 打印 + `return`」的吞错分支改为在原地 `throw`（如 C++ `throw std::runtime_error(...)`），使分配失败立即中断执行、不再把失败指针传给下游。
- 异常消息里带上失败的 ACL error code 与 `__FILE__:__LINE__`，让崩溃直接指向真正的分配点。
- 对 OOM 做专门分支：当 `error_code == ACL_ERROR_RT_MEMORY_ALLOCATION` 时，在异常消息里追加显式 OOM 语义（如 `(OOM: Out of Memory, allocation failed)`），使日志一眼可判读为显存不足，而非泛泛的 acl 失败。物理内存分配与虚拟地址预留两处都要覆盖。
- 分配器里其余 ACL 调用（映射 `aclrtMapMem`、释放 `aclrtUnmapMem` / `aclrtFreePhysical` / `aclrtReleaseMemAddress`、粒度查询 `aclrtMemGetAllocationGranularity`），以及未设置 malloc/free 回调等异常分支，也应统一从「打印 + return」改为 `throw`，避免在其它路径重演吞错。
- 句柄释放取决于异常是否直接令进程退出：若异常直接令进程退出，已预留但未映射的物理内存句柄随进程结束由系统回收，此路径无需在异常路径手工 free；若上层 catch 后不退出，则句柄仍需显式释放，不可外推为「所有失败路径都不用 free」。

## 参考实现及其约束

参考 vllm-ascend（[vLLM](../../concepts/frameworks/kv_cache_manager.md) 的昇腾 NPU 后端插件，对齐 vLLM v0.11.0）的 CaMem 分配器 `csrc/camem_allocator.cpp`——即 sleep-mode / 显存卸载路径所用的分配器，涉及 `create_and_map` / `unmap_and_release` / `my_malloc` / `my_free` 四个函数。合并态修复的关键片段（`my_malloc` 内虚拟地址预留处，物理分配 `aclrtMallocPhysical` 处同形）：

```cpp
error_code = aclrtReserveMemAddress(&d_mem, alignedSize, 0, nullptr, 0);
if (error_code != 0) {
  if (error_code == ACL_ERROR_RT_MEMORY_ALLOCATION) {
    throw std::runtime_error("aclrtReserveMemAddress failed with acl error code: " +
      std::to_string(error_code) + "(OOM: Out of Memory, allocation failed) " +
      __FILE__ + ":" + std::to_string(__LINE__));
  } else {
    throw std::runtime_error("aclrtReserveMemAddress failed with acl error code: " +
      std::to_string(error_code) + " " + __FILE__ + ":" + std::to_string(__LINE__));
  }
}
```

约束与边界：本失败签名（自管 HBM 分配器吞掉 OOM → 下游非法地址崩溃）适用于任何直接用 ACL 驱动内存 API 自管 HBM 的分配路径（[ascendc](../../concepts/frameworks/ascendc.md) 侧自管内存、其它 offload / swap 实现同理）；`csrc/camem_allocator.cpp` 与 `create_and_map` / `unmap_and_release` / `my_malloc` / `my_free` 四个函数名仅为参考实现定位。修复保证：显存分配失败在分配点即刻带 OOM 语义中断，不再延迟到下游非法地址访问崩溃。

## Evidence

- `diff 事实`（vllm-project/vllm-ascend@892f1ee30fc7a7075c897b82f3c0906ddea1dda4，merged 2025-11-04）：`csrc/camem_allocator.cpp` 确将 `cerr + return` 改为 `throw std::runtime_error`，确有 `ACL_ERROR_RT_MEMORY_ALLOCATION` 专属 OOM 分支（`aclrtMallocPhysical` 与 `aclrtReserveMemAddress` 两处）。
- `PR 描述`：吞错导致「等到访问一个非法地址时才崩溃」的因果链由 PR 描述明述（'interrupted when the video memory application fails, rather than waiting until an illegal address is accessed'）。
- 溯源下探：[vllm-ascend-pr-3932-quality-enhancement-immediately-interrupt-execution-when-memory-oom](https://github.com/vllm-project/vllm-ascend/pull/3932)
