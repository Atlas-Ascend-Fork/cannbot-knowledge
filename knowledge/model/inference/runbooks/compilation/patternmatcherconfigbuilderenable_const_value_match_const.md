---
{
  "type": "Runbook",
  "title": "PatternMatcherConfigBuilder.enable_const_value_match 严格二进制常量值匹配的语义边界：Const=1e-7 容差差分实证",
  "description": "在 CANN 9.3.0（Ascend910_9362）上对 AddZeroPass 做 1e-7 边界差分：enable_const_value_match 传入 PatternFusionPass.__init__ 后，matcher 阶段的常量值匹配是严格二进制匹配——Const=1e-7（DT_FLOAT，在主 pass 1e-6 容差内但非精确 0.0）时 strict 变体不命中（fusion_result 无该 pass 记录、dump 图保持原状），同一 fixture 主 pass meet_requirements 容差判零命中并消除（match=1 effect=1，6→4 节点）；Const=0.0 正例 strict 变体同样命中（match=1 effect=1）且整网输出与 baseline 逐位一致。跨 dtype 不命中仅采信 GE README 声明、未实测。",
  "tags": [
    "task.implementation",
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

# PatternMatcherConfigBuilder.enable_const_value_match 严格二进制常量值匹配的语义边界：Const=1e-7 容差差分实证

## 适用场景

- 接口/框架：CANN GE Python `PatternFusionPass` 的 matcher 配置——`PatternMatcherConfigBuilder().enable_const_value_match().build()` 传入 `super().__init__(...)`；`@pattern` 表达式用 `inputs[0] + 0.0`（0.0 为 DT_FLOAT 常量）。构造签名经运行时 inspect 实测：`PatternFusionPass.__init__(self, matcher_config: Optional[PatternMatcherConfig] = None) -> None`（事件 110）。
- 平台/版本：CANN 9.3.0 / Ascend910_9362（逻辑卡 0），Python 3.11.4；离线 `pyatc --framework=5 --soc_version=Ascend910_9362`，ONNX opset 18 / ir_version 9。
- 目标：区分两种匹配严格度的语义——matcher 阶段严格常量值匹配（`enable_const_value_match`）vs `meet_requirements` 阶段按 dtype 容差判零；评估 strict 变体的覆盖面与适用定位。

## 触发与观测

边界 fixture（Const=1e-7，DT_FLOAT，在主 pass 1e-6 容差内但非精确 0.0）上的差分：

- run05（主 pass）日志（事件 219 逐字）：`[PythonAddZeroPass] matched=PythonAddZeroPass_add_zero_pattern captured=x:0 const_dtype=DT_FLOAT const_value=0.0 zero=True` + `[PythonAddZeroPass] replacement: Add(x, 0) removed, consumers rewired to x`。注：日志 `const_value=0.0` 系 `Tensor.data` 回读精度损失，图内真值为 1e-7（dump 原始字节 `95bfd633`，见[CANN 9.3.0 ge Python Tensor.data 字符串序列化回读精度有限：用 dump value_data 原始字节复核图内常量真值](cann_python_tensordata_dump_value_data.md)）。
- run06（strict 变体）日志（事件 219 逐字）：仅 `[PythonAddZeroConstValueMatchPass] loaded: Python PatternFusionPass registered (stage=BEFORE_INFER_SHAPE, pattern=add_zero, matcher_config=const_value_match)`，无 matched 行。
- dump（事件 233）：run05 `RunCustomPassBeforeInfershape` 4 节点（`const_node`+`add_zero` 消失，`add_y <- ['x:0', 'y:0']`）；run06 保持 6 节点原状（`const_node`、`add_zero` 均在）。
- fusion_result（事件 316 逐字）：`run05 ... PythonAddZeroPass: match=1 effect=1`；`run06 ... (no Python pass record)`。

正例（Const=0.0）run03（事件 316）：`PythonAddZeroConstValueMatchPass: match=1 effect=1`。

## 探针与操作

strict 变体 `src/python_add_zero_pass_const_value_match.py`（事件 130 原文，核心段）：

```python
from ge.passes import (
    PassStage,
    PatternFusionPass,
    PatternMatcherConfigBuilder,
    pattern,
    register_fusion_pass,
)


@register_fusion_pass(
    name="PythonAddZeroConstValueMatchPass", stage=PassStage.BEFORE_INFER_SHAPE
)
class PythonAddZeroConstValueMatchPass(PatternFusionPass):
    """Recognize Add(x, 0.0f) with strict const-value-match and replace it with x."""

    def __init__(self):
        super().__init__(
            PatternMatcherConfigBuilder().enable_const_value_match().build()
        )

    @pattern
    def add_zero(self, inputs):
        return inputs[0] + 0.0

    def meet_requirements(self, match_result):
        captured_input = match_result.get_captured_tensor(0)
        print(
            f"[PythonAddZeroConstValueMatchPass] "
            f"matched={match_result.get_pattern_graph_name()} "
            f"captured={captured_input.node.name}:{captured_input.index} "
            f"strict_const_value_match=0.0"
        )
        return True

    def replacement(self, inputs):
        print(
            "[PythonAddZeroConstValueMatchPass] replacement: Add(x, 0.0) "
            "removed, consumers rewired to x"
        )
        return inputs[0]
```

边界/负例 fixture 生成 `artifacts/repro/make_fixtures.py`（事件 166 原文，核心段；正例 fixture 由 `data/torch_gen_onnx.py` 手工构造，不经过 `torch.onnx.export`）：

```python
def build_model(const_value, name):
    x = helper.make_tensor_value_info("x", TensorProto.FLOAT, [2, 2])
    y = helper.make_tensor_value_info("y", TensorProto.FLOAT, [2, 2])
    output = helper.make_tensor_value_info("output", TensorProto.FLOAT, [2, 2])
    const_tensor = helper.make_tensor(
        f"{name}_value", TensorProto.FLOAT, [], [const_value]
    )
    nodes = [
        helper.make_node(
            "Constant", [], ["const_out"], name="const_node", value=const_tensor
        ),
        helper.make_node("Add", ["x", "const_out"], ["add_zero"], name="add_zero"),
        helper.make_node("Add", ["add_zero", "y"], ["output"], name="add_y"),
    ]
    graph = helper.make_graph(nodes, f"add_zero_{name}", [x, y], [output])
    model = helper.make_model(
        graph,
        producer_name="evaluation-agent",
        opset_imports=[helper.make_operatorsetid("", 18)],
        ir_version=9,
    )
    onnx.checker.check_model(model)
    return model


def main():
    out_dir = REPO / "negative_nonzero"
    out_dir.mkdir(parents=True, exist_ok=True)
    onnx.save(build_model(1.0, "nonzero"), out_dir / "model.onnx")

    out_dir = REPO / "boundary_tol"
    out_dir.mkdir(parents=True, exist_ok=True)
    onnx.save(build_model(1e-7, "boundary"), out_dir / "model.onnx")
    print("fixtures written:", REPO / "negative_nonzero", REPO / "boundary_tol")
```

编译触发与主实现相同：`ASCEND_GE_PY_PASS_PATH` 指向 strict 变体文件后 `pyatc --framework=5 --model=model.onnx --soc_version=Ascend910_9362 --output=model`（见[GE Python PatternFusionPass AddZeroPass：@pattern 表达式与 meet_requirements 按 dtype 判零消除 Add(x,0)（离线 OM 与在线 torchair 双路验证）](python_patternfusionpass_addzeropass_pattern_meet_requiremen.md)的 run_case）。

## 机制与判别

`PatternMatcherConfigBuilder().enable_const_value_match().build()` 传入 `PatternFusionPass.__init__` 后，matcher 阶段的常量值匹配是严格二进制匹配：Const=1e-7（DT_FLOAT，在主 pass 1e-6 容差内但非精确 0.0）时 strict 变体不命中——fusion_result 无该 pass 记录、dump 图保持原状；同一 fixture 主 pass 命中并消除（match_times=1 effect_times=1，dump 6→4 节点）。

可区分解释：同一 boundary fixture 上两种结果（run05 消除 vs run06 保留）的唯一变量是 pass 实现（`meet_requirements` 容差判零 vs matcher 严格值匹配），fixture 与编译命令相同。run06 的 fusion_result 连 `match_times` 记录都没有，而 `meet_requirements` 拒绝会留下 `match=1 effect=0` 记录（如 run04 负例），说明过滤发生在 matcher 阶段而非 `meet_requirements`。GE 仓 README 对该行为的描述（事件 28 逐字：『当前 `ConstantMatcher::IsMatch` 的值匹配是严格二进制匹配，不带浮点容差，也不做跨 dtype 归一化』）与本差分结果一致；`ConstantMatcher::IsMatch` 的 C++ 源码未直接读取，机制解释采信 README + 差分实证（未验证推断）。

Const=0.0 正例下 strict 变体同样命中并消除（match_times=1 effect_times=1），整网输出与 baseline 逐位一致。

## 验证信号

（平台：CANN 9.3.0 / Ascend910_9362 / 逻辑卡 0；单次观测）

- 事件 233：run05 dump 6→4 节点（消除）vs run06 dump 保持 6 节点（保留）——同一 fixture 的差分。
- 事件 316：run03 `PythonAddZeroConstValueMatchPass: match=1 effect=1`（正例命中）；run05 `PythonAddZeroPass: match=1 effect=1`；run06 无 Python pass 记录。
- 事件 312：run06 的 events 校验 `consistency_issues: ["未找到目标 pass 的结构化证据: PythonAddZeroConstValueMatchPass"]`——从工具语义确认 fusion_result 中无该 pass 记录。
- 事件 354：strict 变体 OM 整网输出 `strict-variant output identical to baseline: True`（`np.array_equal` 逐位）。

## 适用与失效边界

- strict 变体覆盖面窄于主 pass：容差内非精确 0.0 的浮点（如 1e-7）不命中、图保持原状；需要容差语义时应走 `meet_requirements` 判零路线。
- 定位是 `PatternMatcherConfig`的用法示例，不是主实现的等价替代。
- 跨 dtype 场景（如 DT_INT32 的 0 加 DT_FLOAT 输入）不命中仅为 GE README 声明，本轨迹未实测，采用前需自行验证。
- 常量值匹配的通过标准是二进制严格相等：任何序列化/回读环节的精度损失（如[CANN 9.3.0 ge Python Tensor.data 字符串序列化回读精度有限：用 dump value_data 原始字节复核图内常量真值](cann_python_tensordata_dump_value_data.md)）都可能让『看似相同』的值不匹配。
- 版本边界：CANN 9.3.0 实测（`PatternMatcherConfigBuilder` 仅暴露 `build`/`enable_const_value_match`/`enable_ir_attr_match`，事件 93）；其他版本行为可能变化。
