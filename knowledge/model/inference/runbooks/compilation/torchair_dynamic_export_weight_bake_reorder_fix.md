---
{
  "type": "Runbook",
  "title": "TorchAir dynamo_export(dynamic=True) 权重位置错位：Data-first 稳定排序 + specialize_float 修复",
  "description": "动态 B/S 导出的 AIR 权重冻结错位：torchair 2.12.0 _convert_data_to_const 按位置（export_graph.op[i]）烘焙权重，动态路径 SymInt 抽取链（Shape/Const/Gather）使 op list 交错，把 Gather 擦成权重 Const、真实 pos/length Data 被擦掉。工程内修复：bind_converter 内调用 _reorder_data_nodes_first() 把 root Data 按 index 稳定前移（protobuf 原地 sort 保持 Tensor.node 引用），再以 specialize_float=True 阻止 86 个 Python float 提升为 f64 输入。",
  "tags": [
    "task.debugging",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# TorchAir dynamo_export(dynamic=True) 权重位置错位：Data-first 稳定排序 + specialize_float 修复

## 适用场景

适用于基于 torchair dynamo_export(dynamic=True) 做动态 shape（B/S 可变）整模 AIR 导出时，出现权重未冻结、真实输入 Data 被擦掉、或导出图多出大量 f64 标量输入的场景（StartLux/Qwen3.5 类模型、Ascend GE 适配工程）。


## 触发与观测
动态导出的 AIR 行为异常：pbtxt 中真实 position_ids/actual_seq_lengths Data 消失、9 份模型权重仍是 Data；或 3 输入契约被 86 个 f64 隐式标量输入破坏。

### 结论与证据边界

工程内最小修复（不动系统包）：在 core/exporters/torchair.py 的 bind_converter 里调用 _reorder_data_nodes_first()——把无输入的 root Data 节点按 index 属性稳定前移到 GE op list 前部（RepeatedCompositeFieldContainer.sort 原地排序、pre-sort Tensor.node 引用保持有效已验证、静态导出 Data 本就在前故为 no-op），恢复位置对齐；再用 torch._dynamo.config.specialize_float=True（导出进程内）阻止 dynamic=True 把模型 86 个 Python float 属性（RMSNorm eps 49 + GDR gated-norm eps 18 + Q/Knorm eps 12 + full-attn scaling 6 + min_score）提升为 f64 图输入。排序后的中间态与最终验证层级分开记录，见验证信号；未确认最终 Data 数量，重建分数不算本次设备重跑。

## 探针与操作
1) 带权重最小动态 module 复现 + 仪器化导出记录 inputs 类型/shape/id→weight_name 与每个 Data op 对应关系（repro-both.json）；2) protobuf 容器特性验证（RepeatedCompositeFieldContainer.sort 原地有效、pre-sort 引用 mutation 仍可序列化）；3) 流式读取 5GB pbtxt 统计 Data 节点构成。

## 机制与判别
见上方结论原文与下方机制片段；判别性证据与边界适用讨论见“适用与失效边界”节。

### 补充机制片段

```
def _reorder_data_nodes_first():
    """Stable in-place partition moving root Data nodes to the op-list front.

    The installed torchair 2.12.0 export path
    (torchair/_utils/export_utils.py::_convert_data_to_const) bakes weight
    inputs POSITIONALLY: runtime input i replaces export_graph.op[i] with a
    weight Const. With dynamic=True the SymInt extraction chain
    (Shape/Const/Gather) is emitted right after Data(input_ids), shifting the
    Data block, so that bake clobbers the wrong ops and erases real input Data
    nodes (minimal repro + instrumented evidence:
    work/startlux-validation/p4-dynamic/repro/repro-both.json). Root Data
    nodes have no inputs, so moving them to the front ordered by their index
    attribute is topologically equivalent and restores the position<->input
    alignment the bake assumes. RepeatedCompositeFieldContainer.sort is
    in-place; pre-sort Tensor.node references stay valid (verified). Static
    exports already have Data first in input order, making this a no-op.
    """
    from torchair.ge._ge_graph import get_default_ge_graph
    ops = get_default_ge_graph().op

    def order(op):
        if op.type == "Data":
            return (0, op.attr["index"].i if "index" in op.attr else 0)
        return (1, 0)

    ops.sort(key=order)
```

### 补充机制片段

```
        if x.node.type != "Data":
            raise ValueError(f"{logical}: expected direct graph Data")
        x.node.attr["_ge_adapter_name"].s = logical.encode()
        # All Data nodes are created during input processing before the body
        # conversion reaches the bind_input nodes; re-partitioning here (after
        # every logical-name mark) leaves the graph aligned for torchair's
        # positional weight bake. See _reorder_data_nodes_first above.
        _reorder_data_nodes_first()
        return x
```

### 补充机制片段

```
    def export_spec(self):
        # dynamo_export(dynamic=True) otherwise lifts every Python float the
        # wrapper uses (attn.scaling, min_score, g eps 1e-6, scale, softplus
        # thresholds...) into f64 graph INPUTS - 86 of them on this model -
        # breaking the 3-input contract; the static route bakes them as
        # constants. specialize_float is a public torch dynamo config; the
        # build worker is a single-purpose export process.
        import torch as _torch
        _torch._dynamo.config.specialize_float = True
        inputs = [{"name": "input_ids", "dtype": "int64", "shape": [-1, -1], "dynamic_dims": [0, 1]},
                  {"name": "position_ids", "dtype": "int64", "shape": [-1, -1], "dynamic_dims": [0, 1]},
                  {"name": "actual_seq_lengths", "dtype": "int32", "shape": [-1], "dynamic_dims": [0]}]
        return {"format": "torch", "model": self.wrapper, "io": {**self.io, "inputs": inputs}}
```

## 验证信号

分阶段看待证据：

1. Data-first 稳定排序之后，来源用户报告 pbtxt 有 89 个 Data（3 个真实输入 + 86 个 f64），322 个权重已正确转成 Const。这是仍存在隐式标量输入的中间态，不是 specialize_float 生效后的最终节点数量。
2. 随后加入进程内 `specialize_float=True`。来源保留了 eager isolation 的布尔检查及 infer-ge-all 27 个用例的通过报告。
3. 该记录还说明：两次 isolation 补跑因共享设备 OOM 失败，infer-ge-all 部分使用保留的 raw scores 重建；这些重建结果不计为本次重新执行的设备验证。没有最终 Data 数量的独立观测，不能编造“86 个标量全部消除”的节点计数。

## 适用与失效边界
适用：安装版 torchair 2.12.0 动态导出（缺陷为按位置烘焙权重）。修复是工程导出边界的 Data-first 稳定排序 + 进程内 specialize_float=True，不动系统包、静态导出 no-op。局限：两次补跑 isolation 的重跑因共享设备 OOM 失败，infer-ge-all 段由首轮保留的 raw scores 重建（无阈值放宽、标记 reconstructed）；specialize_float 改的是导出 worker 进程全局 config（单用途进程可接受）。
