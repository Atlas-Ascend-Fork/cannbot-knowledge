---
{
  "type": "Runbook",
  "title": "DeepSeek-V4.1 预计算 cmp_topk_length 用上界而非实际有效数，与 candidate-filter 语义失配",
  "description": "vllm-ascend DeepSeek-V4.1 的 dsa_v41.py 中，builder 预计算路径的 cmp_topk_length 用 (pos+1)//ratio 再 clamp 到 index_topk 的\"可用压缩行数上界\"，而运行时非预计算路径用 (cmp_indices >= 0).sum() 的实际有效数。candidate-filter 层（index_source > candidate_source 的消费层，绝大多数长上下文层）的实际有效选中数受候选池大小约束可小于该上界，FA 按预计算 length 读到的尾部条目是 -1 填充；若 mixed_quant_sparse_flash_mla 不把 -1 当跳过哨兵则读到无效槽，注意力结果随候选池组成波动——典型\"精度波动\"。无候选过滤时上界==实际值，默认配置可能一直未暴露。两条独立审查轨迹均发现此不一致。",
  "tags": [
    "task.debugging",
    "topic.precision",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-03T12:00:00Z",
  "platforms": [
    "agnostic"
  ]
}
---

# DeepSeek-V4.1 预计算 cmp_topk_length 用上界而非实际有效数，与 candidate-filter 语义失配

## 适用场景

- 模型/框架：DeepSeek V4.1（DSA 注意力：indexer/candidate 过滤 + 混合量化稀疏 FA），vllm-ascend 硬件插件，分支 releases/v0.27.1rc，审查区间 `git log 09220f435~1..HEAD`（共 112 个提交，HEAD=6746201ec）。
- 平台：Ascend NPU（A5 生产：PD 分离 + ACL graph decode + fp8 deepseek_v4_fp8 + block 128 + max-model-len 150000）。
- 工作负载：用户报告"精度波动"；本条与候选过滤（candidate filter）拓扑和长上下文层相关。
- 该不一致由两条独立审查轨迹分别发现（DSA 注意力审查 P1-3 与模型侧审查 P2-2）。

## 触发与观测

触发 = `uses_candidate_filter=True` 的层（拓扑上 `index_source > candidate_source` 的所有消费层，即 24/28/32/36 源的消费者，绝大多数长上下文层）且候选池大小 < index_topk。

审查观测到的客观代码事实（事件 21，dsa_v41.py 1192-2392 行读取，builder 预计算路径逐字）：

```
1797:         cmp_topk_lengths: dict[int, torch.Tensor] = {}
1798:         for r in self._cmp_topk_length_bufs:
1799:             buf = self._cmp_topk_length_bufs[r][:num_tokens]
1800:             valid_length = (pos_i32 + 1) // r
1801:             if index_topk > 0:
1802:                 valid_length = valid_length.clamp_max(index_topk)
1803:             buf.copy_(valid_length.unsqueeze(1).to(torch.int32))
1804:             cmp_topk_lengths[r] = buf
```

运行时非预计算路径（同事件 21，逐字）：

```
1467:         else:
1468:             win_topk_length = (win_indices >= 0).sum(dim=-1).to(torch.int32)
1469:             cmp_topk_length = (
1470:                 torch.zeros_like(win_topk_length)
1471:                 if cmp_indices is None
1472:                 else (cmp_indices >= 0).sum(dim=-1).to(torch.int32)
1473:             )
```

第二条轨迹独立观测到同一 builder 代码（事件 294，dsa_v41.py 1658-1838 行读取，同样逐字包含 1797-1804 行）。

## 探针与操作

核查方式（审查会话实际执行的读取）：读取 `vllm_ascend/attention/dsa_v41.py` 的 `_build_kernel_metadata`（1756-1830 行）与 `_sparse_mla_attention`（1429-1483 行），对照两条路径的 length 来源；过滤源见 `vllm_ascend/ops/triton/prepare_indexer_indices.py:37-39`（把 `selected >= visible` 的槽位置 -1 排到尾部）。

本条为只读审查发现，未实施修复；"预计算时同样按 (selected >= 0).sum() 统计，或在拓扑校验中强制 candidate_topk_blocks * candidate_block_size / ratio >= index_topk"的修复建议未经验证。

## 机制与判别

结论 1：builder 预计算 cmp_topk_length 用 (pos+1)//ratio 再 clamp_max(index_topk) 的"可用压缩行数上界"，运行时非预计算路径用 (cmp_indices >= 0).sum(dim=-1) 的实际有效数，两条路径语义不一致。
- 证据：事件 21 逐字代码（1797-1803 上界 vs 1468-1473 实际计数）；`_sparse_mla_attention` 优先消费预计算值（1461-1466 行）。

结论 2：candidate-filter 层（index_source > candidate_source 的消费层）的实际有效选中数受候选池大小约束可小于该上界，FA 按预计算 length 读到的尾部条目是 -1 填充；若 mixed_quant_sparse_flash_mla 不把 -1 当跳过哨兵则读到无效槽，注意力结果随候选池组成波动；无候选过滤时上界==实际值，默认配置可能一直未暴露。
- 机制：候选池 = `candidate_topk_blocks * candidate_block_size / ratio`，可以 < index_topk；`prepare_indexer_indices` 把越界选择置 -1 排到尾部，预计算 length 不感知这一点。
- 可区分解释分支：
  - 若 FA 算子内部把 -1 当跳过哨兵 → 仅浪费算力，无精度影响。
  - 若不跳过 → 读到 -1 槽位（未定义/OOB）→ 注意力结果错误且随候选池组成波动——典型"精度波动"。
  - win 通道无此问题（两条路径都是实际计数），可作为分层消融的对照。
  - 无候选过滤（或候选池 ≥ topk）时上界==实际值 → 默认配置可能一直未暴露，解释为何波动只在特定拓扑/长上下文负载出现。
- 未验证推断：`mixed_quant_sparse_flash_mla` 对 -1 的实际处理未在轨迹内确认（需算子侧核实）；本条根因可未修复。

## 验证信号

- 信号等级：代码事实（read 工具结果），非运行验证。
- 本轨迹内观测到的客观信号：事件 21（builder 1797-1803 上界逐字 + 运行时 1468-1473 实际计数逐字）、事件 294（第二条轨迹独立读到同一 builder 代码）。
- 平台：Ascend NPU（A5）。双轨迹交叉一致的代码事实。
- 无性能/精度数值结论（只读审查；两条路径的语义对齐与算子 -1 契约均未运行验证）。

## 适用与失效边界

- 适用：DeepSeek-V4.1 使用 builder 预计算 FA 元数据 + candidate filter 的部署（消费层 24/28/32/36 源之外的层）；长上下文（150000）下候选池受限时更易触发。
- 不适用：无 candidate filter 的层/拓扑（上界==实际值）；win 通道（两条路径一致）。
- 版本边界：releases/v0.27.1rc 区间；若后续把预计算改为按 `(selected >= 0).sum()` 统计则本条失效。
- 停止/回退条件：算子侧确认 -1 哨兵被跳过后，本条降级为性能浪费项；否则需按修复建议统一 length 语义。
- 修复方向（未验证）：预计算 `cmp_topk_length` 时同样按 `(selected >= 0).sum()` 统计（可并入 device-metadata 任务），或在拓扑校验中强制 `candidate_topk_blocks * candidate_block_size / ratio >= index_topk`。
