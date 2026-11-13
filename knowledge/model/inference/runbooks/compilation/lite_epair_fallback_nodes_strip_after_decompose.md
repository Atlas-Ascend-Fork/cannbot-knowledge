---
{
  "type": "Runbook",
  "title": "Lite EPAIR 导出 fallback 节点：run_decompositions 重插入 assert 使早 strip 失效 + fallback 普查探针",
  "description": "qwen3.5 torch_delegate Lite EPAIR 导出报 cannot contain fallback or unannotated node: torch.ops.aten._assert_tensor_metadata.default。根因：convert_graph 在 _optimize_and_convert 之前调用 _strip_assert_tensor_metadata(ep)，但其内部 ep.run_decompositions() 重新导出 EP 会重新插入 assert 节点，早 strip 被覆盖。",
  "tags": [
    "task.debugging",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "a3"
  ]
}
---
# Lite EPAIR 导出 fallback 节点：run_decompositions 重插入 assert 使早 strip 失效 + fallback 普查探针

## 适用场景

适用于 torch_delegate Lite EPAIR（Ascend910_9362 目标）导出转换中出现 fallback/unannotated node 报错的分析，以及需要对大体积 ep json 做 fallback 节点普查的场景。


## 触发与观测
convert_epair 阶段报 LiteConversionError: Lite EPAIR conversion cannot contain fallback or unannotated node: torch.ops.aten._assert_tensor_metadata.default（随后 type_as 同类报错）。

### 结论与证据边界

Lite EPAIR 转换报 torch_delegate.lite_context.LiteConversionError: Lite EPAIR conversion cannot contain fallback or unannotated node: torch.ops.aten._assert_tensor_metadata.default 的根因：TorchAirGEConverter.convert_graph 在调用 _optimize_and_convert 之前执行 _strip_assert_tensor_metadata(ep)，但 _optimize_and_convert 内部 ep.run_decompositions(decomp_table=...) 会重新导出 EP 并重新插入 _assert_tensor_metadata 断言节点，早 strip 被覆盖；validate_lite_result 在最终 JSON 中发现未转换 assert 节点报错。对最终 formated_ep_json_with_ascend_ir.json（243317532 bytes）的普查：541 个 source="" fallback 节点，唯一 target 5 类——366×aten._assert_tensor_metadata.default、90×aten.pad.default、61×aten.type_as.default、18×aten.conv1d.default、6×aten._scaled_dot_product_flash_attention_for_cpu.default。

## 探针与操作
1) inspect.getsource(TorchAirGEConverter.convert_graph) 看时序（_strip_assert_tensor_metadata 在 _optimize_and_convert 之前）；2) 对 243MB formated_ep_json_with_ascend_ir.json 跑 fallback 普查脚本（ascend_ir.source=='' 的 target 计数）。

## 机制与判别
见上方结论原文与下方机制片段；判别性证据与边界适用讨论见“适用与失效边界”节。

### 补充机制片段

```
    def convert_graph(self, ep: ExportedProgram) -> ExportedProgram:
        """使用 torchair 的 _optimize_and_convert API 转换图"""
        logger.info("Starting graph conversion using torchair._optimize_and_convert...")

        compiler_config = self._create_compiler_config()

        logger.debug(f"Whitelist decompositions: {len(self._config.whitelist_decompositions)} ops")
        decomps = {}
        table = default_decompositions()

        # 从白名单添加decomposition
        for op in self._config.whitelist_decompositions:
            if op in table:
                decomps[op] = table[op]
                logger.debug(f"Added {op} to decomps from whitelist")

        _strip_assert_tensor_metadata(ep)

        # 调用 torchair API
        self._ge_graph_ascend = _optimize_and_convert(
            ep,
            config=compiler_config,
            custom_decompositions=decomps
        )

        # 获取 torchair ascend_ir_map 并转换为本地 NodeIR
        torchair_ir_map = self._ge_graph_ascend.ascend_ir_map
        self._ascend_ir_map = {
            name: _convert_torchair_node_ir(ir)
            for name, ir in torchair_ir_map.items()
        }

        logger.info(f"Conversion complete: {len(self._ascend_ir_map)} nodes with ascend_ir")

        return self._ge_graph_ascend.optimized
```

### 补充机制片段

```
import json
from collections import Counter

with open('qwen3_5_demo/output/qwen3_5_0_8b/extra/formated_ep_json_with_ascend_ir.json', 'r') as f:
    data = json.load(f)

nodes = data.get('graph_module', {}).get('graph', {}).get('nodes', [])

fallback_nodes = []
for node in nodes:
    ascend_ir = node.get('ascend_ir', {})
    if isinstance(ascend_ir, dict) and ascend_ir.get('source') == '':
        target = node.get('target', '<unknown>')
        fallback_nodes.append(target)

print(f"Total fallback nodes: {len(fallback_nodes)}")
print(f"\nUnique targets ({len(set(fallback_nodes))}):")
print("=" * 60)

for target, count in Counter(fallback_nodes).most_common():
    print(f"{count:4d} x {target}")
```

## 验证信号
普查输出（工具结果）：Total fallback nodes: 541，366×_assert_tensor_metadata + 90×pad + 61×type_as + 18×conv1d + 6×_scaled_dot_product_flash_attention_for_cpu。早 strip 无效由该计数直接证明（strip 已执行但最终 JSON 仍有 366 个 assert 节点）。

## 适用与失效边界
适用：torch_delegate Lite 导出链（run_decompositions 会 re-export EP 重插 assert 是 PyTorch 导出机制行为）。局限：另一处已实施修复（lite_export_context 需在导入 torch_npu/torchair 前初始化、两阶段子进程隔离导出）未纳入本条。
