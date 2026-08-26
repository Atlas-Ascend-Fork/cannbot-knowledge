---
type: Optimization
title: Ascend hybrid KV cache（多 block_size 分组）与 context parallelism 共存：放开 CUDA 专属禁令 + lcm(各组 block_size)*dcp*pcp 对齐
description: Ascend NPU 上 hybrid KV cache（同一模型内多种 block size 的 KV-cache 分组，典型如 MLA 全局注意力层 + sliding-window/SWA-MLA 局部注意力层混合）与 context parallelism（decode_context_parallel_size / prefill_context_parallel_size > 1）可以共存。上游 vLLM 引入的「hybrid KV cache groups 不支持 context parallelism」是面向 CUDA 后端的假设性约束，对 Ascend 不成立——因为 Ascend 对 MLA 层与 SWA-MLA 层的 CP 是各层独立实现的，不同 block size 的分组在 CP 下可各自对齐。规则：Ascend + 多个 block size 不一致的 KV cache group + dcp/pcp>1 时，不接受上游禁令，改用 Ascend 版 resolve_kv_cache_block_sizes，scheduler block size = lcm(各组 block_size) * dcp * pcp（对上游 block_size*dcp*pcp 行为的推广）；单分组退化为 block_size*dcp*pcp，无 CP 回落上游原实现。参考实现以全局 monkeypatch 覆盖 vllm.v1.core.kv_cache_utils.resolve_kv_cache_block_sizes（并同步 patch engine core 中的直接 import 引用），新增 vllm_ascend/patch/platform/patch_kv_cache_utils.py。约束：仅在 Ascend 后端确实为相关层独立实现 CP 的前提下成立，不外推为任意后端任意混合分组都可 CP。适用于 vllm-ascend、Atlas A3 场景的 backend_incompatibility 与 kvcache-offload 优化决策。
tags:
- task.optimization
- topic.attention
- topic.parallelism
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/8899
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# Ascend hybrid KV cache（多 block_size 分组）与 context parallelism 共存：放开 CUDA 专属禁令 + lcm(各组 block_size)*dcp*pcp 对齐

## 适用场景

- 场景：在 Ascend NPU 上同时启用 **hybrid KV cache**（同一模型内存在多种 block size 的 KV-cache 分组，典型如 [MLA](../../../concepts/modules/mla.md) 全局注意力层 + sliding-window/SWA-MLA 局部注意力层混合）与 **context parallelism**（`decode_context_parallel_size > 1` 或 `prefill_context_parallel_size > 1`）。
- 前提/信号：升级到含上游 vLLM「hybrid KV cache groups 不支持 context parallelism」这条限制的版本后，调度侧解析 block size 的逻辑会因为「多个 block size 分组 + dcp/pcp>1」这一组合直接报错或拒绝启动。表面看像是「该组合不被支持」，实际上这是一条**面向 CUDA 后端的假设性约束**，在 Ascend 上不成立。
- 判断：遇到上游对该组合的硬禁令时，不应据此判定该组合在 Ascend 上无法正常启动——是否受限取决于该后端是否为相关层独立实现 CP。

## 规则（条件 → 做什么 · 依据）

### 条件
Ascend 后端 + 存在多个 KV cache group（各组 block size 不一致）+ `dcp` 或 `pcp` > 1。

### 做什么
不接受上游「多分组 + CP 不兼容」的禁令，改用 Ascend 版的 block size 解析逻辑，按下式计算 scheduler block size：

```
scheduler_block_size = lcm(各组 block_size) * dcp * pcp
```

- 多分组 + CP：取所有 group 的 block size 的最小公倍数（lcm）再乘以 `dcp * pcp`，作为统一的 scheduler block size。lcm 保证各组分别在 CP 下对齐时有一个公共对齐粒度。
- 单分组（`len(groups) <= 1`）：退化为 `block_size * dcp * pcp`。
- 无 CP（`dcp == 1 且 pcp == 1`）：回落到上游原始实现，不介入。

这是对「上游引入该禁令之前」行为（`block_size * dcp * pcp`）的推广——把单一 block size 推广到多组的 lcm，从而在保持既有单组语义的同时覆盖多组场景。

### 依据
Ascend 对全局 MLA 层与局部 SWA-MLA 层的 context parallelism 是**各层独立实现**的：不同 block size 的分组在 CP 下各自对齐、互不牵制，因此不同分组共存并不会破坏 CP 的正确性。这正是上游 CUDA 假设不适用于 Ascend 的原因——上游对该组合整体禁用，可理解为其未针对混合分组各自独立处理 CP；Ascend 侧已经具备各层独立的 CP 实现，只需一个公共对齐粒度（lcm）即可让多组共存。

### 反例 / 边界
- 这条规则只在 Ascend 后端**确实为相关层独立实现了 CP** 的前提下成立。不要外推成「任意后端、任意混合分组都可开 CP」——对没有做各层独立 CP 实现的后端（含上游 CUDA 路径），上游的禁令是正确的。
- 适用面限定为 Ascend 的 MLA / SWA-MLA CP 实现范围；出现新的注意力层类型或新的分组来源时，需重新确认其 CP 是否同样独立实现，再决定是否纳入 lcm 对齐。

## 参考实现（及其约束）

参考实现以**全局 monkeypatch** 覆盖上游调度侧解析 KV cache block size 的函数（`resolve_kv_cache_block_sizes`），并同步替换 engine core 中直接 import 的引用，使新逻辑对所有调用点生效。核心分支如下：

```python
dcp = vllm_config.parallel_config.decode_context_parallel_size
pcp = vllm_config.parallel_config.prefill_context_parallel_size
groups = kv_cache_config.kv_cache_groups
if len(groups) <= 1:
    bs = cache_config.block_size * dcp * pcp
    return bs, bs
if dcp != 1 or pcp != 1:
    group_block_sizes = [g.kv_cache_spec.block_size for g in groups]
    scheduler_block_size = math.lcm(*group_block_sizes) * dcp * pcp
    return scheduler_block_size, scheduler_block_size
return _orig_resolve_kv_cache_block_sizes(kv_cache_config, vllm_config)
```

约束（属于该参考实现、非技术本身的限制）：
- 这是一个「放开某后端专属禁令」的 patch，其正确性**系于 Ascend 后端为相关层独立实现了 CP** 这一前提；换后端或换实现即不再成立。
- 该 patch 以全局函数替换落位，落位方式可更规范，但只影响 patch 挂载方式，不改变上述 `lcm(各组 block_size) * dcp * pcp` 的对齐语义。
- 该组合下的 KV cache 组织仍走各层自身的分页/写入路径，与 [KV cache offload](../../../concepts/techniques/kvcache_offload.md) 等其它 KV 管理机制正交——本规则只解决 scheduler block size 对齐，不改变各组内部的 KV 存取。

## Evidence

- 合并态 diff 新增 `vllm_ascend/patch/platform/patch_kv_cache_utils.py`，其中含上述 `lcm(各组 block_size) * dcp * pcp` 分支；文件 docstring 说明 Ascend 独立实现 MLA/SWA-MLA 的 CP、故放开上游禁令。
- 溯源：[vllm-ascend-pr-8899-misc-main2main-upgrade-vllm-to-0427](https://github.com/vllm-project/vllm-ascend/pull/8899)，合并 commit sha `7fd2cede36c6d661e0f06ddfb35502659639660e`，文件 `vllm_ascend/patch/platform/patch_kv_cache_utils.py`。
