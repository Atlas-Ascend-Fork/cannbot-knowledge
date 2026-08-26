---
type: Runbook
title: qwen3-next 上 chunked prefill / prefix caching 特性因 block_size 例外静默失效
description: >-
  vLLM-Ascend 上的 Qwen3-Next 启用 chunked prefill 或 prefix caching 时，特性可能无报错地静默失效。
  两项特性要求 paged KV cache 的 block_size 为 128，但该模型在 128 下调用 get_kv_cache_groups
  存在未解决错误，因此平台特例会恢复原 block_size，形成无法两全的版本边界。诊断时应在
  Platform.check_and_update_config 后核对实际 block_size；短期不应强制改为 128，而应在非刚需时
  关闭 chunked prefill/prefix caching。根本解决需先修复 Qwen3-Next 在 block_size=128 下的
  KV cache 分组错误，再移除模型特例。
tags:
- task.debugging
- topic.kv_cache
- topic.memory
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/4094
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# qwen3-next 上 chunked prefill / prefix caching 特性因 block_size 例外静默失效

## 信号（现象）

在 Ascend NPU 后端（vllm-ascend）上部署 **qwen3-next** 类混合线性注意力模型，同时启用 **chunked prefill** 或 **prefix caching**，观察到这两项特性**不按预期生效**——无显式报错、无崩溃，属于「配置看似接受但功能静默失效（fail silently / may not work correctly）」的处境。

核对是否落在本页范围内：

- 后端是 Ascend NPU（vllm-ascend），推理路径，非 CUDA。
- 模型 `hf_config.model_type == "qwen3_next"`（GatedAttention + GatedDeltaNet 混合注意力，见 [qwen3-next](../../concepts/models/qwen3_next.md)）。
- 触发路径任一命中：`cache_config.enable_prefix_caching` 为真；或 Ascend scheduler 未启用（`not ascend_scheduler_config.enabled`）；或 `ascend_scheduler_config.enable_chunked_prefill` 为真。
- 启动配置中的 `block_size` **不是 128**（比如沿用了默认或按显存/吞吐调过的值）。

若同时满足以上，且发现 chunked prefill / prefix caching 没有带来预期效果，很可能就是本页描述的已知不兼容签名，而非配置写错。**注意这是 qwen3-next 专属**：同后端上其它 `model_type` 的模型在同样路径下会被强制拉到 block_size=128、特性正常。

## 触发条件

Ascend 后端要让 chunked prefill / prefix caching 正常工作，前提是 **KV cache 的 `block_size` 必须为 128**（paged-attention 的 block 粒度，见 [kvcache-offload](../../concepts/techniques/kvcache_offload.md) 中 paged KV cache 布局）。框架在进入上述触发路径时会主动打印告警并把 `cache_config.block_size` 强制设为 128，以满足该前提。

但对 qwen3-next 存在一个**刻意的例外**：框架先记住原始 `block_size`，强制成 128 之后，一旦发现 `model_type == "qwen3_next"`，又把 `block_size` **恢复回原值**。于是 qwen3-next 走到这条路径时，`block_size` 保持配置的原始值——如果原值恰好是 128 则无碍，如果原值≠128，则「block_size 必须为 128」这一前提被特意放弃，chunked prefill / prefix caching 可能静默失效。

## 根因

qwen3-next 无法直接使用 `block_size=128`：在该模型上以 block_size=128 走 KV cache group 划分时，`get_kv_cache_groups` 存在一个**尚未解决的 hidden error**。当前版本的规避手段是「对 qwen3-next 回退 block_size 到原值」，以避开这个 hidden error，代价就是牺牲了 chunked prefill / prefix caching 对 block_size=128 的依赖。

维护者在代码中以 TODO 标记这是临时规避，待 `get_kv_cache_groups` 的 hidden error 从根解决后即移除该 model_type 判断：

```
# TODO(MengqingCao): Remove the model_type check,
# after resolving the hidden error in get_kv_cache_groups.
```

即：这不是「block_size 配错了」，而是「qwen3-next × (chunked prefill / prefix caching) × Ascend 后端」当前版本无法两全的**已知不兼容**——一边是特性要求的 block_size=128，一边是 `get_kv_cache_groups` 在该布局下报错，只能二选一。

> `get_kv_cache_groups` 为何在 qwen3-next + block_size=128 下报 hidden error，上游未展开细节；此处按维护者 TODO 记为「已知、未解决」。「fail silently / may not work correctly」的后果表述为现象佐证、非维护者确认的根因（来源归属见 Evidence 节）。

## 修法

- **不要靠调 `block_size` 来救**：框架会对 qwen3-next 主动保留原值，无法经 `block_size` 调到 128；即便硬拉到 128 也会撞上 `get_kv_cache_groups` 的 hidden error。
- **短期规避**：接受「当前版本 qwen3-next 上 chunked prefill / prefix caching 不可靠」这一事实，评估是否必须开这两项特性。若不是刚需，关闭它们、走非 chunked / 非 prefix-caching 路径部署 qwen3-next，避免落入静默失效区间。
- **诊断确认**：在触发路径下打印 `cache_config.block_size`，若对 qwen3-next 观测到它**保持原始值而非被拉到 128**，即确认命中本签名（其它模型此处应为 128）。
- **根本解**：从根解决 `get_kv_cache_groups` 在 block_size=128 下对 qwen3-next 的 hidden error（维护者 TODO 记为待办）；解决后即可移除 model_type 例外，让 qwen3-next 也走统一的 block_size=128 路径，chunked prefill / prefix caching 恢复可靠。
- 配置层面 `block_size` / `enable_prefix_caching` / chunked prefill 开关的语义与推导，另见统一推理配置体系 [inference-config](../../concepts/techniques/inference_config.md)。

## 参考实现及其约束

Ascend 后端在 `vllm_ascend/platform.py::Platform.check_and_update_config` 中的 set-and-revert 逻辑：

```python
if cache_config.enable_prefix_caching or \
    not ascend_scheduler_config.enabled or \
    getattr(ascend_scheduler_config, "enable_chunked_prefill", False):
    logger.warning(
        "If chunked prefill or prefix caching is enabled, block size must be set to 128."
    )
    origin_block_size = cache_config.block_size
    cache_config.block_size = 128
    # TODO(MengqingCao): Remove the model_type check, after resolving the hidden error in get_kv_cache_groups.
    if model_config and model_config.hf_config.model_type == "qwen3_next":
        logger.warning(
            "When running qwen3-next model, block_size needs to be restored to its original value."
        )
        cache_config.block_size = origin_block_size
```

约束（属于该参考实现的当前限制，不是技术本身的限制）：

- 只对 `model_type == "qwen3_next"` 生效；判据是 HF config 的 `model_type` 字符串精确匹配。
- 只在 chunked prefill / prefix caching 触发路径内生效；不走该路径时无此例外。
- 是**临时规避**：随维护者解决 `get_kv_cache_groups` hidden error 后该分支会被移除，届时行为会变——不要把「qwen3-next 保留原 block_size」当成长期契约。
- 无 before→after 性能/精度数字（上游仅记录 CI passed）；本条价值在「模型 × 特性 × 后端」的已知不兼容签名，不在收益数字。

## Evidence

- 合并态 diff：[vllm-ascend-pr-4094-v0-11-0-core-restore-scheduling-logic-under-default-configuration](https://github.com/vllm-project/vllm-ascend/pull/4094)
- 一手代码：`vllm_ascend/platform.py::Platform.check_and_update_config`，merge commit `ebd45b659631c5cad72655aed2f53d5edd21a76e`（V0.11.0-core，cherry-pick），`origin_block_size` 保留/恢复逻辑 + `get_kv_cache_groups` TODO 注释均在该段。
- 现象佐证：该 PR 的 AI review 评论（gemini-code-assist bot，针对 `platform.py` 该段）指出对 qwen3_next 若原 block_size≠128，chunked prefill / prefix caching「may not work correctly / could fail silently」——作现象佐证，非维护者确认。
