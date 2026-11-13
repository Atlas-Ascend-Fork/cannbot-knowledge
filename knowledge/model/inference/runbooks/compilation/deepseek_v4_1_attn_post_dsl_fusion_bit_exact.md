---
{
  "type": "Runbook",
  "title": "cannbot-dsl 0.6.0→0.7.1 升级兼容：cannbotdsl.select 缺失的 shim 处理与 ops 模块导入探缺",
  "description": "cannbot-dsl 0.6.0→0.7.1 升级时的 API 兼容处理场景：0.7.1 缺 cannbotdsl.select，需以 arith.select + ValueTreeLayout.reconcile 构造 shim 赋回；同时可用逐个 import ops 模块的方式探缺失符号。",
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
# cannbot-dsl 0.6.0→0.7.1 升级兼容：cannbotdsl.select 缺失的 shim 处理与 ops 模块导入探缺

## 适用场景
cannbot-dsl 0.6.0→0.7.1 升级时的 API 兼容处理场景：0.7.1 缺 cannbotdsl.select，需以 arith.select + ValueTreeLayout.reconcile 构造 shim 赋回；同时可用逐个 import ops 模块的方式探缺失符号。

## 触发与观测
cannbot-dsl 从 0.6.0 升级到 0.7.1 后，cannbotdsl.select 缺失；逐个 import ops 模块时 ops.mixed_quant_sparse_flash_mla 因 cannbotdsl.ops.sync 缺 cube_raw_l1_to_l0a 导入失败，其余 ops 模块导入正常。

## 探针与操作
1) cannbot-dsl 0.7.1 缺 select 时以 arith.select + ValueTreeLayout.reconcile 构造 shim 并逐个 import ops 模块探缺；失败模块及缺失符号见下文验证信号。
2) 分开核对符号可见性与模块导入结果；导入通过不等于算子数值或整网验证通过。

## 机制与判别
cannbot-dsl 0.6.0→0.7.1 升级兼容机制：0.7.1 缺 cannbotdsl.select，需以 arith.select + ValueTreeLayout.reconcile 构造 shim 赋回 cannbotdsl.select；ops.mixed_quant_sparse_flash_mla 因 cannbotdsl.ops.sync 缺 cube_raw_l1_to_l0a 导入失败，其余 ops 模块导入正常。

机制片段：
```bash
source /usr/local/Ascend/ascend-toolkit/set_env.sh 2>/dev/null; python3 - <<'EOF' 2>&1 | tail -12
import cannbotdsl
from cannbotdsl._mlir.dialects import arith

def _select(predicate, true_value, false_value):
    from cannbotdsl.core.frontend.runtime.control_flow import to_mlir_value
    from cannbotdsl.core.frontend.runtime.value_tree_layout import ValueTreeLayout
    pred = to_mlir_value(predicate, context="select predicate")
    layout, lhs, rhs = ValueTreeLayout.reconcile(true_value, false_value)
    return layout.rebuild(tuple(arith.select(pred, a, b) for a, b in zip(lhs, rhs)))

cannbotdsl.select = _select
print("shim applied, hasattr select:", hasattr(cannbotdsl, "select"))

import importlib, pkgutil, ops
failed = []
for m in pkgutil.iter_modules(ops.__path__):
    if m.name.startswith("_"):
        continue
    try:
        importlib.import_module(f"ops.{m.name}")
        print("OK  ops." + m.name)
    except Exception as e:
        failed.append((m.name, repr(e)[:100]))
        print("FAIL ops." + m.name, repr(e)[:100])
print("failed:", len(failed))
EOF
```

## 验证信号
- 来源工具观测：shim 应用输出（hasattr select: True）与 ops 模块逐个导入结果（仅 mixed_quant_sparse_flash_mla 因 cannbotdsl.ops.sync 缺 cube_raw_l1_to_l0a 失败，failed: 1）。

## 适用与失效边界
适用于 cannbot-dsl 0.6.0→0.7.1 升级时的 select shim 处理与 ops 模块导入探缺；轨迹内验证止于 shim 使 cannbotdsl.select 可用与 ops 模块导入行为，其他 API 兼容性未逐项验证。

## 结论与证据边界
- cannbot-dsl 0.6.0→0.7.1 升级兼容：0.7.1 缺 cannbotdsl.select，需以 arith.select + ValueTreeLayout.reconcile 构造 shim 赋回 cannbotdsl.select；ops.mixed_quant_sparse_flash_mla 因 cannbotdsl.ops.sync 缺 cube_raw_l1_to_l0a 导入失败，其余 ops 模块导入正常
