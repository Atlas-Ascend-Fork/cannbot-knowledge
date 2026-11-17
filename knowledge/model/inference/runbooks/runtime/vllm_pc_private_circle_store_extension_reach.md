---
{
  "type": "Runbook",
  "title": "vLLM 私有 KV 环回放：预算不足时的本地 defer 守卫",
  "description": "保留本地命中回放的完整守卫与预算改写逻辑；不据压缩摘要宣称 UT 通过，也不把 store 扩展路径的分析写成已复现污染。",
  "tags": [
    "task.debugging",
    "topic.kv_cache"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# vLLM 私有 KV 环回放：预算不足时的本地 defer 守卫

## 适用场景

vllm-ascend 请求私有 KV 环的本地命中分支；请求保存了 private_circle_hit_blocks 和 private_circle_hit_length。具体设备未知。

## 触发与观测

命中长度回退后，当前步分配的 token 数可能不足以覆盖完整 warm-up 区间，需要在采用命中块前检查预算。

## 探针与操作

核对 stash 的生成、replay_start 和 full_hit，再读完整守卫与调用方的释放/重试处理。下方函数只展示本地分支，不证明其他命中来源也经过它。

源码函数单元（依赖所属模块上下文）：

```python
def _restore_full_hit_for_adoption(
    request: Request, args: tuple, kwargs: dict
) -> tuple[tuple, dict] | None:
    """Restore the full hit length when the stashed hit blocks are adopted.

    ``_patched_get_computed_blocks`` reported the rolled-back start to the
    scheduler (token budget), but the shared planes must adopt every hit
    block. Rewrite the allocate contract to the full hit: the warm-up rows
    before the original hit boundary need no new blocks (their shared-plane
    writes are masked by the model runner).

    Returns None when this step's chunk cannot cover the whole warm-up
    window: the caller defers the request, so the warm-up rows always land
    in one full-budget chunk (the one-shot replay mask/plan state and the
    ring commit invariant both rely on that).
    """
    stashed_blocks = getattr(request, "private_circle_hit_blocks", None)
    stashed_hit = getattr(request, "private_circle_hit_length", None)
    if stashed_blocks is None or stashed_hit is None:
        return args, kwargs
    replay_start = int(kwargs.get("num_new_computed_tokens") or 0)
    full_hit = int(stashed_hit)
    rollback = max(0, full_hit - replay_start)
    if args:
        num_new_tokens = args[0]
    else:
        num_new_tokens = kwargs.get("num_new_tokens")
    if isinstance(num_new_tokens, int) and 0 < num_new_tokens <= rollback:
        # A budget-tail chunk cannot hold the warm-up rows; deferring (rather
        # than adopting with an unrewritten token count) keeps the cache
        # commit inside the actually-scheduled range.
        return None
    kwargs = dict(kwargs)
    kwargs["new_computed_blocks"] = stashed_blocks
    kwargs["num_new_computed_tokens"] = full_hit
    if isinstance(num_new_tokens, int) and num_new_tokens > rollback:
        # Defense in depth: never reduce a positive allocation to zero (the
        # upstream allocator rejects that without external KV).
        if args:
            args = (num_new_tokens - rollback, *args[1:])
        else:
            kwargs["num_new_tokens"] = num_new_tokens - rollback
    return args, kwargs
```

## 机制与判别

所读函数先计算 rollback=max(0, full_hit-replay_start)。当正的 num_new_tokens 不超过 rollback 时返回 None；预算足够时恢复完整命中信息并扣除回放行数。调用方还需正确释放本步预留和处理重试。

## 验证信号

原始工具输出包含该函数的完整源码。所谓 23 passed 只在压缩摘要中出现，未绑定原始 UT 输出，因此本卡仅记源码/静态核对，不记 cpu_reference 或真实引擎污染复现。

## 适用与失效边界

不外推到 store 扩展命中或异步加载分支。defer 的公平性、重试预算、饥饿及资源释放仍需集成测试；没有真实引擎/NPU 的污染或修复验证。
