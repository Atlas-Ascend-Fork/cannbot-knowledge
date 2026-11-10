---
{
  "type": "Runbook",
  "title": "CANN 9.3.0 ge Python Tensor.data 字符串序列化回读精度有限：用 dump value_data 原始字节复核图内常量真值",
  "description": "开发 GE Python 融合 pass 时若发现 meet_requirements 里读到的 Const 值（Tensor.data）与模型文件常量不一致（本例：图内 Const 真值 1e-7，pass 日志打印 const_value=0.0），可用探针解析 DUMP_GE_GRAPH 产物 pbtxt 中 const 节点 value_data 的 content 原始字节并按 dtype 反序列化（struct.unpack）复核：本例字节 95bfd633 证实图内真值为 1.0000000116860974e-07。根因是 CANN 9.3.0 ge/graph/tensor.py 的 Tensor.data 经 C++ 序列化字符串（unflatten_tensor_data/_parse_str_list）回读、精度有限；容差判零（|v|<1e-6）结论不受影响，受影响的是日志显示与依赖精确值的检查。",
  "tags": [
    "task.debugging",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "a3"
  ]
}
---

# CANN 9.3.0 ge Python Tensor.data 字符串序列化回读精度有限：用 dump value_data 原始字节复核图内常量真值

## 适用场景

- 场景：开发 GE Python 融合 pass 时，在 `meet_requirements` 中读 `Const` 节点 `value`（`node.get_attr("value")` 得到 `Tensor`，再取 `tensor.data`）做常量值判断或日志打印，发现日志值与模型文件中的常量不一致。
- 平台/版本：CANN 9.3.0（`ge` 包位于 `$ASCEND_HOME_PATH/python/site-packages/ge`），Ascend910_9362，Python 3.11.4。
- 涉及对象：`ge.graph.Tensor.data`（属性形态；运行时 probe 确认与 `get_data()` 方法并存，事件 93：`Tensor attrs: ['data', 'data_type', 'format', 'get_data', ...]`）。

路径约定：`${SITE_PACKAGES}` 为当前 Python 解释器的 site-packages 目录。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

boundary fixture 的 Const 为 1e-7（事件 223 逐字）：`boundary_tol [('Constant', 'const_node'), ('Add', 'add_zero'), ('Add', 'add_y')] const_value= [1.0000000116860974e-07]`。

但 run05 的 pass 日志（事件 219 逐字）打印：

```text
[PythonAddZeroPass] matched=PythonAddZeroPass_add_zero_pattern captured=x:0 const_dtype=DT_FLOAT const_value=0.0 zero=True
```

`const_value=0.0` 与 fixture 的 1e-7 不符——pass 里的 `const_value` 正是 `_extract_scalar_value(const_tensor.data)` 的回读值，触发『pass 是否把非零常量误判为零』的怀疑。

## 探针与操作

dump 原始字节复核探针（事件 250 原文）：

```bash
cd "$CASE_ROOT/artifacts/evidence" && python3 - <<'EOF'
import re, struct
for run in ('run02_positive_mainpass','run04_negative_mainpass','run05_boundary_mainpass'):
    txt = open(f'{run}/ge_onnx_00000000_graph_0_PreRunBegin.pbtxt').read()
    idx = txt.find('name: "const_node"')
    if idx < 0: idx = txt.find('name: "zero_const"')
    block = txt[idx:idx+6000]
    m = re.search(r'name: "value_data"\s*\n\s*content: "(.*?)"', block, re.S)
    if not m:
        m = re.search(r'name: "value_data"\s*\n\s*s: "(.*?)"', block, re.S)
    if m:
        raw = m.group(1)
        # unescape pbtxt string
        b = raw.encode().decode('unicode_escape').encode('latin1')
        print(run, 'value_data bytes:', b.hex(), '-> float32:', struct.unpack('<f', b[:4])[0])
    else:
        print(run, 'value_data not found')
EOF
```

探针输出（事件 251 逐字）：

```text
run02_positive_mainpass value_data bytes: 00000000 -> float32: 0.0
run04_negative_mainpass value_data bytes: 0000803f -> float32: 1.0
run05_boundary_mainpass value_data bytes: 95bfd633 -> float32: 1.0000000116860974e-07
```

已安装 `ge` 包的回读实现定位（事件 259 逐字）：

```text
${SITE_PACKAGES}/ge/graph/tensor.py:289:            return unflatten_tensor_data(data_str, self.shape)
${SITE_PACKAGES}/ge/graph/tensor.py:384:def unflatten_tensor_data(tensor_data: str, shape: List[int]) -> "TensorLike":
```

`_parse_str_list` 把 `'[1, 2, 3]'` 形式的字符串解析为 Python 列表（事件 262，`tensor.py:355-373`），即 `Tensor.data` 的值来自对 C++ 侧序列化字符串的解析。

## 机制与判别

CANN 9.3.0 的 ge Python `Tensor.data` 属性经 C++ 侧序列化字符串回读，精度有限：图内 Const 真值为 1e-7（dump `value_data` 原始字节 `95bfd633`）时回读显示 0.0，pass 日志打印 `const_value=0.0` 与 fixture 实际值 1e-7 不符。

复核探针：解析 dump pbtxt 中 const 节点 `value_data` 的 `content` 原始字节并 `struct.unpack('<f', ...)` 反序列化，可区分『图内常量真值』与『Python 回读显示值』；本例判零结论不受影响（|1e-7|<1e-6 与回读 0.0 同判为零），受影响的只是日志显示与依赖 `Tensor.data` 精确值的检查。

可区分解释分支：

- 分支 A（被证伪）：『pass 把非零常量误判为零』——dump 原始字节证明图内常量确为 1e-7，而主 pass 判零本就是容差语义（|v|<1e-6），1e-7 命中容差是预期行为，不是误判；负例 1.0 回读仍为 1.0（事件 251 run04），判断不变。
- 分支 B（被采信）：『`Tensor.data` 回读精度损失导致显示值失真』——同图原始字节 `95bfd633`（1e-7）与回读 0.0 的分离、`tensor.py:289/384` 的字符串解析实现支持该解释。
- 未验证推断：C++ 侧序列化的具体格式（如定点 6 位小数）未直接观测；除 1e-7→0.0 外的精度边界（如 1e-6 量级值的回读误差）未系统扫描。

## 验证信号

（平台：CANN 9.3.0 / Ascend910_9362 / 逻辑卡 0；单次观测）

- 事件 219：run05 日志 `const_value=0.0 zero=True`（回读显示值）。
- 事件 223：fixture 常量 `1.0000000116860974e-07`（ONNX 侧真值）。
- 事件 251：dump `value_data` 原始字节 `95bfd633 -> float32: 1.0000000116860974e-07`（图内真值）；同批 run02 `00000000 -> 0.0`、run04 `0000803f -> 1.0`。
- 事件 259/262：`ge/graph/tensor.py:289/384` 的 `unflatten_tensor_data(data_str, ...)` 与 `_parse_str_list` 字符串解析实现。
- 事件 316：run05 fusion_result `PythonAddZeroPass: match=1 effect=1`——与容差判零预期一致（若为误判零，负例 run04 应同样被消除，实际 effect=0）。

## 适用与失效边界

- 适用于 CANN 9.3.0 的 `ge.graph.Tensor.data` / `get_data()` 回读路径；其他版本序列化格式可能变化，跨版本需用同一探针重验。
- 需要常量精确值（而非容差判断）的守卫、断言或日志，应以 dump pbtxt 的 `value_data` 原始字节为准，不要信任 `Tensor.data` 的回读小数。
- 该精度损失会让『精确值断言』（如 `assert tensor.data == 1e-7`）假失败；容差判断（本例 1e-6）在本观测范围内不受影响，但容差量级与回读精度相当时（约 1e-6 以下）边界行为未验证。
- 停止/回退条件：若未来版本 `Tensor.data` 改为二进制精确回读，本诊断不适用；用事件 251 的探针输出与回读值比对即可确认。
