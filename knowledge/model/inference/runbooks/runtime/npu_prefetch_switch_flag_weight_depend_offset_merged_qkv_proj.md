---
{
  "type": "Runbook",
  "title": "NPU o_proj 权重预取的执行窗口由 npu_prefetch 的 depend 张量决定：depend=qkv→v_cache_after_scatter 把 CMO 从 QK-Norm 窗口移到与 Fused Attention 并行",
  "description": "NPU 上 LLM 解码层做同层权重预取（`executor.utils.common_utils.npu_prefetch`，Qwen3-8B cann-learning-hub `recipe_qwen3_8b`/GE Graph 教程栈）时，需要选择 CMO（cache maintenance operation）与主路径哪个算子窗口重叠。",
  "tags": [
    "task.implementation",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-20T14:17:04Z",
  "platforms": []
}
---

# NPU o_proj 权重预取的执行窗口由 npu_prefetch 的 depend 张量决定：depend=qkv→v_cache_after_scatter 把 CMO 从 QK-Norm 窗口移到与 Fused Attention 并行

## 适用场景

NPU 上 LLM 解码层做同层权重预取（`executor.utils.common_utils.npu_prefetch`，Qwen3-8B cann-learning-hub `recipe_qwen3_8b`/GE Graph 教程栈）时，需要选择 CMO（cache maintenance operation）与主路径哪个算子窗口重叠。核心规律：CMO 启动时机由 `depend` 张量的产出时刻决定（依赖边定时），预取调用点本身不必移动——预取在独立流上，GE Graph 模式下该流由图运行时管理，不需要模型手动创建 Stream。

## 触发与观测

教程 v3 原设计（source 0 seq 53，notebook 原文）：

```
`depend=qkv`引用merged_qkv_proj的输出，让CMO从qkv_proj完成时刻分叉，在QK-Norm/RoPE/Scatter的VECTOR窗口（~25 us，AI Core与HBM带宽均空闲）内执行完毕；Fused Attention仍使用原始四维`v_cache`，避免改变KV Cache布局。
```

即 CMO 刻意落在 QK-Norm（RMSNorm）/RoPE/Scatter 的 VECTOR 窗口，避免与 Fused Attention 争用 HBM 带宽。用户要求把预取点改到与 Fused Attention 并行（source 0 seq 1）。`npu_prefetch` 签名（source 0 seq 39，`common_utils.py` Line 151）：

```
def npu_prefetch(switch_flag, weight, depend, size, offset=0):
```

修改前 `modeling_qwen.py:437`（source 0 seq 53）：`depend=qkv if self.prefetch_uses_dependency else None,`。

## 探针与操作

- dump notebook 12 cells（source 0 seq 10-20）定位机制描述与 cell 4 的源码校验片段。
- grep `depend=qkv` 全仓确认仅两处需改：`modeling_qwen.py:437` 与 notebook cell 4 校验串（source 0 seq 52-53）。

## 机制与判别

`depend` 指向哪个张量，CMO 就在该张量产出后启动。要与 Fused Attention 并行，把 depend 改成 FA 启动前的最后一个依赖——V 侧 scatter 输出 `v_cache_after_scatter`（`torch_npu.npu_scatter_nd_update_` 返回值）：Scatter 完成 时 CMO 与 FA 同时启动、并行执行，在 FA 读 KV Cache 期间把 o_proj 权重搬入 L2。核心修改只有一行（source 0 seq 70，编辑原文）：

```python
                depend=v_cache_after_scatter if self.prefetch_uses_dependency else None,
```

注释同步更新（source 0 seq 66，newString 原文）：

```python
        # 在融合Attention启动前提交同层o_proj权重预取。以v_cache_after_scatter
        # （V侧npd_scatter_nd_update_的返回值，Fused Attention启动前的最后一个
        # 依赖）作为启动依赖：Scatter完成后CMO与Fused Attention同时启动、并行
        # 执行，在FA读KV Cache期间把o_proj权重搬入L2，供o_proj MatMul使用。
```

判别：调用点仍在 FA 之前提交（顺序断言 prefetch → FA → o_proj 成立），改变的是依赖边而非语句位置；`prefetch_uses_dependency` 开关与 `weight=self.o_proj.weight`、`size=self.prefetch_size` 均不动。

## 验证信号

- tool_observed（静态校验，source 0 seq 96-97）：AST 解析通过；required_fragments 全命中（`weight=self.o_proj.weight` / `depend=v_cache_after_scatter if self.prefetch_uses_dependency else None` / `v_cache_after_scatter = torch_npu.npu_scatter_nd_update_(` / `self.prefetch_target == "self_attn.o_proj"`）；顺序断言 `call_pos < fused_pos < o_proj_pos` 通过，输出 `[OK] cell4 fragment checks pass; order: prefetch -> FA -> o_proj`；notebook JSON 合法（12 cells）且全文不再含 `depend=qkv`。
- 未做设备验证：教程实验（Prefetch 关闭 vs 8 MiB vs 16 MiB 三组）未运行；Agent 明确提示需重启内核后重点观察「8m/16m 组的 Fused Attention 是否因带宽争用劣化」（source 0 seq 109，agent_narrative）——v3 原设计正是为规避该争用才选 QK-Norm 窗口。

## 适用与失效边界

- 已证边界：depend 张量切换的代码语义与静态校验（该教程栈，GE Graph 固定开启 + NPU RMSNorm + Add+RMSNorm 融合）。
- 失效边界：无性能/带宽数据——与 FA 并行是否净收益未测，存在 FA HBM 带宽争用导致劣化的风险（原设计规避点，仅提示未观测）；NPU Graph EX 模式（显式共享侧流 `npugraph_prefetch_stream`）下定时语义未在轨迹中验证。

## 附：断言存档

- NPU 权重预取 CMO 的启动时机由 npu_prefetch(switch_flag, weight, depend, size, offset=0) 的 depend 张量产出时刻决定（依赖边定时），预取调用点位置无需移动：v3 设计 depend=qkv（merged_qkv_proj 输出）使 CMO 在 QK-Norm/RoPE/Scatter 的 VECTOR 窗口（~25 us，AI Core 与 HBM 带宽均空闲）内执行完毕，刻意避开与 Fused Attention 争用 HBM 带宽；GE Graph 模式下预取流由图运行时管理，不需要模型手动创建 Stream
