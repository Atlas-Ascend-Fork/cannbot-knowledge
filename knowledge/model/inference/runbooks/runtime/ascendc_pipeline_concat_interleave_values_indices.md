---
{
  "type": "Runbook",
  "title": "AscendC Concat 写 2 倍元素导致 1x 尺寸缓冲潜伏越界（Sort 管线 Cast→Concat→Sort16→Extract）",
  "description": "算子/框架：AscendC 自定义算子（案例：DeepSeek V3.2 KV offload `gather_selection_kv_cache` extended buffer，Ascend 910B3）；凡使用 AscendC Sort 管线（Cast → Concat → Sort16 → Extract）的 kernel。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:03Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": []
}
---

# AscendC Concat 写 2 倍元素导致 1x 尺寸缓冲潜伏越界（Sort 管线 Cast→Concat→Sort16→Extract）

## 适用场景

- 来源为910B3目标的代码评审与头文件检查，不把项目资料中的Atlas标签当作当前实机设备证明。

- 算子/框架：AscendC 自定义算子（案例：DeepSeek V3.2 KV offload `gather_selection_kv_cache` extended buffer，Ascend 910B3）；凡使用 AscendC Sort 管线（Cast → Concat → Sort16 → Extract）的 kernel。
- 场景：topk 排序缓冲（topkSortAlign 尺寸）在 UB 手工布局（sortBuf_ 切区）中分配。

## 触发与观测

- 机制原文（source 0 seq 74）："The AscendC Sort pipeline is: Cast -> Concat (interleave values with indices) -> Sort16 -> Extract. The Concat step takes N values and N indices and writes 2N elements to the output. If the output buffer is only sized for N elements, the extra N elements overwrite adjacent memory."
- 案例行为："Before the 2x fix, `chunkBufLocal` was followed immediately by `sortBuf_[0]` (sortedTopKLocal). When Concat in `SortTopkValues(chunkBufLocal, ...)` writes 2x, it overflows into sortedTopKLocal. But sortedTopKLocal was about to be overwritten by the sort output anyway! This is why it appeared to work -- the overflow was 'harmless' because the victim buffer was immediately overwritten."
- 布局变化后显性破坏："In the SyncAll path, the memory layout changed. `chunkBufLocal` now at 2x topkSortAlign_ (after the fix) was placed at a different offset, and the overflow was corrupting `sortBuf_` containing the previously-sorted topk values that were STILL NEEDED for the merge step. This is why the SyncAll path broke with 1x and needed 2x."

## 探针与操作

- 判别方法：核对 Concat 目标缓冲是否按 2N 预算；检查被越界邻居的生命周期（是否即将被重写）。
- 修复（campaign 已实施，本 trace 评审确认）："Is the 2x fix correct? Yes. The dynamic area is now 11 regions (2 shared + 1 topkIndices + 2 chunkBuf + 5 sortBuf + 1 extra padding = 11 x topkSortAlign_)."
- 残留建议（未实施）：非 SyncAll 原路径仍是 1x——"The 1x code has undefined behavior. In practice, the specific memory layout makes the overflow harmless for the non-SyncAll path, but any future refactoring could expose it."建议加注释记录潜伏越界。

## 机制与判别

- 根因：AscendC Concat（值+索引交织）输出 2N 元素；1x 目的缓冲必越界写入相邻 UB 区。
- 判别信号：同代码"曾经能跑"不代表无越界——victim 恰好即将重写时表现为潜伏；UB 布局重排（如新增 SyncAll 路径）后 victim 变为活跃数据即显性出错。修复后仍能跑不能反证原先无越界。
- 未验证推断：非 SyncAll 路径的 1x 布局"无害性"依赖具体切区顺序，属源码级推断。

## 验证信号

- source_observed：kernel 源码（SetInvalidBlockStatus/SortTopk 区域，source 0 seq 58）+ 修复后 11 区布局与 SyncAll 路径可运行的 campaign 记录（source 0 seq 74）。
- 本 trace 为评审级：无新设备运行，2x 修复的正确性由布局核算与既有运行历史支撑。

## 适用与失效边界

- 适用于：所有 AscendC 手工 UB 布局 + Sort/Concat 管线的 kernel 缓冲预算审查。
- 失效边界：若后续 CANN 版本改变 Concat 语义或提供带边界检查的原语，需重核；"无害越界"结论绑定当前布局顺序。
- 停止条件：凡 Concat 目的缓冲按 1x 分配即应视为缺陷修复，不以"当前能跑"为准。

## 附：断言存档

- AscendC Sort 管线（Cast→Concat→Sort16→Extract）的 Concat 以 2N 元素写目的缓冲：1x 尺寸缓冲必越界；原 TK3 非 SyncAll 路径'能跑'是因为越界 victim（sortedTopKLocal）恰好即将被重写——潜伏越界；SyncAll 路径布局改变后 victim 变为仍需的 sortBuf_ 才显性出错，2x 修复（动态区 11 区）正确。
