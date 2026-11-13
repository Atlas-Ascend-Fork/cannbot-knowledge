---
{
  "type": "Runbook",
  "title": "负结果 · dsv41_fused_attn STAGE_FUSED 单 kernel 合并",
  "description": "把 prefill 两段式（QKS+PVEPI）合并为单 kernel 的尝试在数值上失败：对 torch.empty 缓冲做 zero/nan/0xAB 污染探针证明合并路径读取未初始化/陈旧 GM 数据（两段式免疫）。",
  "tags": [
    "task.debugging",
    "topic.attention"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# 负结果 · dsv41_fused_attn STAGE_FUSED 单 kernel 合并

## 适用场景

pypto_pro 单 kernel 合并（少 launch）改造的可行性评估：dsv41_fused_attn prefill 由 QKS+PVEPI 两次 launch 合并为 dsv41_fused_prefill_kernel 一次 launch 的数值正确性与收益判定。


## 触发与观测
触发：`USE_FUSED_PREFILL=True` 下 `test_device_vllm_prefill_matches_reference` 等用例与 golden 比对失败；此前还发现合并重构把 event 8 释放挪到 token 循环外导致 T≥2 死锁（已修复为循环内）。

## 探针与操作
1) GM 缓冲污染探针（关键手段，完整单元见工件）：hook `torch.empty`，对新分配张量按 mode 注入 zero/nan/0xAB，分别以两段式与合并路径运行同一输入并对 golden 求误差——两段式误差不随污染变化（0.089440 恒定、逐字节一致），合并路径 zero 污染 err=1.037164、nan/0xAB err≈1.90e31 且 fp8/sf 不再一致 ⇒ 合并路径的输出依赖未初始化/陈旧 GM 缓冲。4) 已知不可用：UB→L1 直连（探针证实），Vec→Cube 方向不可用、Cube→Vec 可用。

## 机制与判别
判别结构：数值错误 + 污染敏感（读未初始化 GM）；合并路径把 QKS 的 UB 计划与 PVEPI 的输出 epilogue 塞进同一 kernel 的共享地址空间（QKS 计划在上、PVEPI 计划抬到 pv_ub=0x15000），时序耦合更深。

### 补充机制片段
```
def run(mod, use_fused, mode="none"):
    if hasattr(mod, "USE_FUSED_PREFILL"):
        mod.USE_FUSED_PREFILL = bool(use_fused)
    orig = torch.empty
    keep = []
    def hook(*a, **k):
        x = orig(*a, **k)
        if mode == "nan":
            x.view(torch.uint8).fill_(0xAB) if x.dtype.itemsize == 1 else x.fill_(float("nan"))
        elif mode == "zero":
            x.zero_()
        elif mode == "ab":
            x.view(torch.uint8).fill_(0xAB)
        keep.append(x)
        return x
    torch.empty = hook
    try:
        out = mod.dsv41_fused_attn_vllm_prefill(
            q.npu(), kv.npu(), indices.npu(), sm, positions.npu(), cache.npu(),
            h // 8, attn_sink=sink.npu())
        torch.npu.synchronize()
    finally:
        torch.empty = orig
    return [x.cpu() for x in out]
```

## 验证信号
会话终态：清理了探针残留的 build 产物（22 个文件删除）。

### 结论与证据边界

  对 torch.empty 分配的 GM 缓冲做污染探针（zero/nan/0xAB）显示：两段式误差恒为 0.089440 且逐字节一致、不受污染影响；合并路径在 zero 污染下 err 升到 1.037164、nan/0xAB 污染下 err≈1.90e31 且 fp8/sf 与两段式不再一致——合并 kernel 的输出依赖未初始化/陈旧的 GM 缓冲内容。

## 适用与失效边界
适用：判断「合并 launch 是否值得继续投入」的决策证据。失效/边界：污染探针只证明「读未初始化缓冲」，未定位到具体读点（下一步建议：逐级 dump q_pay/kt_pay/v_pay/p_pay/qmx_sc/den_c 中间缓冲对比）。
