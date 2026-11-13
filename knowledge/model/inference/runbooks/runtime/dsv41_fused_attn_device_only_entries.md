---
{
  "type": "Runbook",
  "title": "dsv41_fused_attn 入口的设备驻留契约与 host 操作审计",
  "description": "源码审阅核对 prefill/decode 入口删除 host 回退分支并显式检查 NPU、int32 与 padded_heads 条件。device-only 指无 host 张量计算/拷贝，仍可能有同步和 launch 开销；未完成性能验证。",
  "tags": [
    "task.implementation",
    "topic.attention"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# dsv41_fused_attn 入口的设备驻留契约与 host 操作审计

## 适用场景

pypto_pro/Ascend 上 vLLM V4.1 fused attention 生产入口的 host 开销治理：要求 host 侧零数据搬运、零算术、零 python 张量循环的 kernel 化改造（dsv41_fused_attn 的 vLLM prefill/decode 入口）。


## 触发与观测
触发/需求：dsv41_fused_attn 的 vLLM prefill/decode 入口 host 开销治理；本轨迹完成删除 host_free=False 回退分支与 host_free 参数本身（0340f9c3）。

## 探针与操作

逐条审计入口中的 torch 调用，并将分配、视图、同步和 kernel launch 分开记录。`synchronize` 可能阻塞 host，不能和 reshape/view 一并称为纯元信息操作。

## 机制与判别
入口契约（完整单元见工件）：所有 operand 必须已在 NPU、ids/positions 必须 int32（校验、绝不隐式转换）、padded_heads ∈ {64,128} 且 ≥ H；不满足显式 ValueError 而非静默回退。两段 device 路径 `STAGE_QKS → pvepi_fused_out`：QKS 一次 launch 完成 Q pad+RoPE+量化、KV 量化、QK、softmax、P 量化（Cube/Vector 段 + 事件 1 操作数发布/事件 0/8 槽位环）；pvepi_fused_out 完成 PV + inverse-RoPE + vLLM out_fp8/out_sf 打包与 lse/max_logits。padded_heads=128 走 nbr=2 虚拟批（t//nbr、(t%nbr)*64），头尾两个 head pad 都在 device 覆盖。

### 补充机制片段
```
    # The host-free entry never copies: every operand must already be on the
    # npu, and the id / position tables must be int32 (validated, never cast).
    for name, x in (("q", q), ("kv", k_all), ("indices", idx),
                    ("token_positions", token_positions),
                    ("cos_sin_cache", cos_sin_cache),
                    ("attn_sink", attn_sink), ("topk_length", topk_length)):
        if x is not None and (not isinstance(x, torch.Tensor)
                              or x.device.type != "npu"):
            raise ValueError(
                f"{name} must already be on the npu device; this host-free "
                "entry never copies inputs to the device")
    if token_positions.dtype != torch.int32:
        raise ValueError(
            f"token_positions must be int32, got {token_positions.dtype}; "
            "the caller must provide int32 and it is never converted")
    if idx.dtype != torch.int32:
        raise ValueError(
            f"indices must be int32, got {idx.dtype}; the caller must provide "
            "int32 and it is never converted")

    # Two-launch device path (``STAGE_QKS -> pvepi_fused_out``).  Both head
    # blocks are covered: ``p == 128`` runs the token-major / half-inner virtual
    # batch (``nbr == 2``), which both stages index with ``t // nbr`` and
    # ``(t % nbr) * 64``.
    return _vllm_prefill_device(
        q, k_all, idx, sm_scale, token_positions, cos_sin_cache,
        n_wv_group, attn_sink, topk_length, p)
```

## 验证信号
源码审阅信号：入口契约与两段 device 路径的代码单元见机制片段：（，客观 tool_result）。

### 结论与证据边界

  删除 dsv41_fused_attn_vllm_prefill/decode 的 host_free=False 回退分支与 host_free 参数后，入口 device-only：前置条件不满足（输入不在 NPU、token_positions/indices 非 int32、padded_heads 不在 {64,128} 或 < H）一律显式 ValueError 报错，不再静默回退 host 路径。

  host 侧只剩 torch.empty/reshape/view（另有 as_strided/transpose 视图操作及 synchronize 同步操作；同步可能阻塞 host）：Q pad/RoPE、KV 量化、QK、softmax、P 量化、PV、inverse-RoPE、out_fp8/out_sf/lse/max_logits 全部在 STAGE_QKS→pvepi_fused_out 两次 kernel launch 内完成；padded_heads=128 走 nbr=2 虚拟批，两个 stage 都用 t//nbr 与 (t%nbr)*64 索引。

## 适用与失效边界
适用：A5 NPU 上独占卡、串行验证的 kernel 入口契约化。失效/边界：(a) 前置条件不满足现在是硬报错——调用方必须保证 int32/设备驻留/padded_heads 合法，不再有 host 兜底；(b) host 审计白名单还含 as_strided/transpose/synchronize（元信息/同步类）；(c) `out_sf` 的 TMA padding 尾字仍未定义（backing buffer 是 torch.empty），需要整段缓冲的调用方必须零分配后拷贝视图。
