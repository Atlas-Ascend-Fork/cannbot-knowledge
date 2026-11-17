---
{
  "type": "Runbook",
  "title": "FXRT cold 缓存失败：比对副作用节点、生产者与 DCE 调用点",
  "description": "在相同 rank 对比图、生成代码和写入者，定位无谓词 DCE 可能移除 in-place HOP 的差异；修复后的设备闭环未完成。",
  "tags": [
    "task.debugging",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# FXRT cold 缓存失败：比对副作用节点、生产者与 DCE 调用点

## 适用场景

FXRT/Inductor/OM2 的 DSV4 推理 cold/warm 缓存排查；需要同 rank、相同模型与对应构建产物。

## 触发与观测

失败运行报 MTE 非法 GM 地址及后续通信失败。生成代码中某些缓冲区有分配和消费，却没有预期的写入者。

## 探针与操作

同 rank 比较 FX 图、post-fusion IR 和 output_code.py；按节点统计 compiled_kernel_wrapper_mutation，确认缓冲区的生产者，然后比较 DCE 调用点。不要用跨 rank 的 vocab 偏移差异替代构建差异。

源码函数单元（依赖所属模块上下文）：

```python
def _rewrite_rank1_elewise_cmp_(gm: GraphModule) -> None:
    """Keep rank-1 DSV4 token-mask elewise at [1, N] through Cast.

    GreaterEqual tiling logs ``custom inputs shape [N] error`` on 1D int masks.
    Cast tiling logs ``non_custom inputs shape error`` on the squeezed 1D bool
    that used to sit after that lift. Official Path C ge/Cast ST stays rank-2:
    unsqueeze once, run cmp/logical_and/cast/mul/sub at [1, N], squeeze only
    at non-elewise consumers (embedding / split / invert / graph output).
    """
    graph = gm.graph
    unsqueeze = _aten_unsqueeze()
    squeeze = _aten_squeeze_dim()
    changed = False
    for node in list(graph.nodes):
        if not _keeps_rank2_elewise(node) or not node.args:
            continue
        changed = _lift_rank1_elewise_node_(graph, node, unsqueeze) or changed
    while _propagate_rank2_example_meta_(graph):
        changed = True
    changed = _bypass_squeeze_for_rank2_elewise_(graph) or changed
    changed = _bypass_redundant_unsqueeze_(graph) or changed
    while _propagate_rank2_example_meta_(graph):
        changed = True
    changed = _insert_boundary_squeeze_(graph, squeeze) or changed
    if changed:
        graph.eliminate_dead_code()
        graph.lint()
        gm.recompile()
```

同版本构建的调用点对照：

```text
==== eliminate_dead_code call sites: bfd476e5 (PASS) ====
bfd476e5:fxrt/python/fxrt/torch/fx_layout_legalize.py:1238:        graph.eliminate_dead_code(_is_impure_layout_node)

==== eliminate_dead_code call sites: f67e1241 (FAIL) ====
f67e1241:fxrt/python/fxrt/torch/fx_layout_legalize.py:1238:        graph.eliminate_dead_code(_is_impure_layout_node)
f67e1241:fxrt/python/fxrt/torch/fx_to_c_graph.py:947:        graph.eliminate_dead_code()
```

## 机制与判别

本次构建对照发现，失败构建比通过构建多一处无谓词 graph.eliminate_dead_code()。两组运行的 wrapper 节点与写入者差异支持沿副作用节点被删除的路径继续排查；这不能把所有 MTE 错误都归为 DCE，也不证明任意名称带谓词的调用都安全。

## 验证信号

所采四个通过 rank 的 ckw 计数均为 10，四个失败 rank 均为 0；源码 grep 同时给出带谓词与新增无谓词调用点。修复后的 cold→warm 设备验收没有在该记录内完成。

## 适用与失效边界

需在匹配版本中确认哪些节点具有副作用，以及谓词是否完整覆盖它们。补谓词后仍须检查写先于读、cold 通过和 warm 缓存复用；不要把现有相关性写成修复成功。
