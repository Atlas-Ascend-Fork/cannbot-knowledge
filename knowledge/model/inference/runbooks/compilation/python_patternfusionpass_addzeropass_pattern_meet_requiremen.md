---
{
  "type": "Runbook",
  "title": "GE Python PatternFusionPass AddZeroPass：@pattern 表达式与 meet_requirements 按 dtype 判零消除 Add(x,0)（离线 OM 与在线 torchair 双路验证）",
  "description": "在 CANN 9.3.0（Ascend910_9362）上用纯 Python PatternFusionPass 消除恒等 Add(x,0)：@pattern 表达式 inputs[0]+0 描述 Data+Const→Add 拓扑，meet_requirements 读 Const.value 按 dtype 判零（DT_FLOAT 容差 1e-6 / DT_DOUBLE 容差 1e-15 / DT_INT32 精确 0），replacement 透传 inputs[0]。DUMP_GE_GRAPH dump 对比确认 6→4 节点、ATC fusion_result match=1 effect=1；非零常量（1.0）保持原图且编译继续（match=1 effect=0）；自建 ACL runner 离线 OM 与在线 torchair（复用未修改网络脚本）整网输出 baseline vs optimized 均逐位一致。仅 DT_FLOAT 判零分支实测；1e-7 非零值也会被历史主 pass 消除，容差版本不保证严格恒等语义。",
  "tags": [
    "task.implementation",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "a3"
  ]
}
---
# GE Python PatternFusionPass AddZeroPass：@pattern 表达式与 meet_requirements 按 dtype 判零消除 Add(x,0)（离线 OM 与在线 torchair 双路验证）

## 适用场景

- 接口/框架：CANN GE Python 融合 pass——`ge.passes.PatternFusionPass` + `@register_fusion_pass` + `@pattern` 表达式；加载用 `ASCEND_GE_PY_PASS_PATH`（单个 `.py` 文件或目录），离线触发 `pyatc --framework=5`（命令行参数与 `atc` 一致、在当前 Python 解释器进程内运行），在线触发 torchair（`torchair.get_npu_backend` + `torch.compile`）。
- 平台/版本：CANN 9.3.0，soc_version=Ascend910_9362（共享 NPU 机器、`ASCEND_RT_VISIBLE_DEVICES=0` 仅逻辑卡 0），Python 3.11.4，torch_npu 2.7.1.post4；ONNX opset 18 / ir_version 9。
- 目标与工作负载：删除恒等逐元素加法（`z = torch.add(x, 0.0)` / ONNX `Add(x, Constant(0))`）。原始图 `x,Const(0) -> Add0; Add0,y -> Add1 -> Output`，目标图 `Add(x,0)` 消失、后续消费者直连 `x`。工作负载为 2x2 FP32 小图（正例 0.0 / 负例 1.0 / 边界 1e-7 三个 fixture），属功能验证，非吞吐基准。

## 触发与观测

优化目标与判定基准：精确零正例的 dump 中 `Add0` 消失，常量 1.0 负例保持原图且编译继续。下面的历史主 pass 使用浮点容差，1e-7 等近零非零值也会被消除，不能满足“所有非零常量均保留”的严格语义。

pyatc 正例日志（`pyatc.stdout.log`，事件 219 逐字）：

```text
[PythonAddZeroPass] loaded: Python PatternFusionPass registered (stage=BEFORE_INFER_SHAPE, pattern=add_zero)
[PythonAddZeroPass] matched=PythonAddZeroPass_add_zero_pattern captured=x:0 const_dtype=DT_FLOAT const_value=0.0 zero=True
[PythonAddZeroPass] replacement: Add(x, 0) removed, consumers rewired to x
```

负例（Const=1.0，事件 219 逐字）：

```text
[PythonAddZeroPass] matched=PythonAddZeroPass_add_zero_pattern captured=x:0 const_dtype=DT_FLOAT const_value=1.0 zero=False
[PythonAddZeroPass] skip reason: const value 1.0 is not zero
```

离线 dump 节点结构（事件 233 逐字）——run02 正例 `PreRunBegin`（6 节点）：

```text
x [ge:Data] <- ['']
y [ge:Data] <- ['']
zero_const [ge:Const] <- []
add_zero [ge:Add] <- ['x:0', 'zero_const:0']
add_y [ge:Add] <- ['add_zero:0', 'y:0']
Node_Output [ge:NetOutput] <- ['add_y:0']
```

同图 `RunCustomPassBeforeInfershape`（4 节点）：

```text
x [ge:Data] <- ['']
y [ge:Data] <- ['']
add_y [ge:Add] <- ['x:0', 'y:0']
Node_Output [ge:NetOutput] <- ['add_y:0']
```

在线 torchair 路径（事件 423 逐字）：baseline 两次 dump 均保持 6 节点（`('arg0_1', 'ge:Data'), ('arg1_1', 'ge:Data'), ('Const', 'ge:Const'), ('Add', 'ge:Add'), ('Add_1', 'ge:Add'), ('NetOutput', 'ge:NetOutput')`）；optimized 的 `PreRunBegin` 6 节点 → `RunCustomPassBeforeInfershape` 4 节点（`('arg0_1', 'ge:Data'), ('arg1_1', 'ge:Data'), ('Add_1', 'ge:Add'), ('NetOutput', 'ge:NetOutput')`）。

## 探针与操作

主实现 `src/python_add_zero_pass.py`（事件 127 原文，核心段）：

```python
from math import fabs

from ge.graph.types import DataType
from ge.passes import (
    PassStage,
    PatternFusionPass,
    pattern,
    register_fusion_pass,
)

_FLOAT_ZERO_TOLERANCE = 1e-6
_DOUBLE_ZERO_TOLERANCE = 1e-15


def _extract_scalar_value(value):
    """Peel nested single-element lists down to a scalar; None if not scalar."""
    while isinstance(value, list):
        if len(value) != 1:
            return None
        value = value[0]
    return value


def _is_tensor_value_equal_to_zero(tensor):
    """Return True only when the Const tensor holds a supported-dtype zero."""
    scalar_value = _extract_scalar_value(tensor.data)
    if scalar_value is None:
        return False
    if tensor.data_type == DataType.DT_FLOAT:
        return fabs(float(scalar_value)) < _FLOAT_ZERO_TOLERANCE
    if tensor.data_type == DataType.DT_DOUBLE:
        return fabs(float(scalar_value)) < _DOUBLE_ZERO_TOLERANCE
    if tensor.data_type == DataType.DT_INT32:
        return int(scalar_value) == 0
    return False


@register_fusion_pass(name="PythonAddZeroPass", stage=PassStage.BEFORE_INFER_SHAPE)
class PythonAddZeroPass(PatternFusionPass):
    """Recognize Add(x, 0) and replace it with x using explicit Const validation."""

    @pattern
    def add_zero(self, inputs):
        return inputs[0] + 0

    def meet_requirements(self, match_result):
        captured_input = match_result.get_captured_tensor(0)
        for node in match_result.get_matched_nodes():
            if node.type != "Const":
                continue
            try:
                const_tensor = node.get_attr("value")
                const_dtype = const_tensor.data_type.name
                const_value = _extract_scalar_value(const_tensor.data)
                is_zero = _is_tensor_value_equal_to_zero(const_tensor)
            except (RuntimeError, AttributeError) as exc:
                print(
                    f"[PythonAddZeroPass] skip: failed to read Const value, "
                    f"reason={exc}"
                )
                return False
            print(
                f"[PythonAddZeroPass] matched={match_result.get_pattern_graph_name()} "
                f"captured={captured_input.node.name}:{captured_input.index} "
                f"const_dtype={const_dtype} const_value={const_value} zero={is_zero}"
            )
            if not is_zero:
                if const_dtype not in ("DT_FLOAT", "DT_DOUBLE", "DT_INT32"):
                    print(
                        f"[PythonAddZeroPass] skip reason: unsupported const "
                        f"dtype {const_dtype}"
                    )
                elif const_value is None:
                    print(
                        "[PythonAddZeroPass] skip reason: const value is not a "
                        "scalar"
                    )
                else:
                    print(
                        f"[PythonAddZeroPass] skip reason: const value "
                        f"{const_value} is not zero"
                    )
                return False
            return True
        print(
            "[PythonAddZeroPass] skip reason: no Const node found in matched "
            "subgraph"
        )
        return False

    def replacement(self, inputs):
        print(
            "[PythonAddZeroPass] replacement: Add(x, 0) removed, consumers "
            "rewired to x"
        )
        return inputs[0]
```

编译矩阵的加载/触发函数（`artifacts/evidence/run_pyatc_matrix.sh`，事件 181 原文；环境段见[ASCEND_OPP_PATH 覆盖符号链接镜像私有 OPP 致 pyatc ONNX 导入 E13010：二分定位后改用默认共享 OPP](ascend_opp_path_opp_pyatc_onnx_e13010.md)的 after 版本——不要覆盖 `ASCEND_OPP_PATH`）：

```bash
run_case() {
  local name="$1" fixture="$2" pass_file="${3:-}"
  local dir="$EVID/$name"
  rm -rf "$dir"; mkdir -p "$dir"
  cp "$SRC/$fixture/model.onnx" "$dir/model.onnx"
  if [[ -n "$pass_file" ]]; then
    export ASCEND_GE_PY_PASS_PATH="$pass_file"
  else
    unset ASCEND_GE_PY_PASS_PATH
  fi
  ( cd "$dir" && pyatc --framework=5 --model=model.onnx \
      --soc_version="$SOC_VERSION" --output=model \
      > pyatc.stdout.log 2>&1 )
  local rc=$?
  echo "[$name] pyatc rc=$rc"
  ls "$dir" | grep -c "\.pbtxt$" | xargs -I{} echo "[$name] pbtxt dumps: {}"
  return 0
}
```

离线整网输出的 ACL 运行（自建 runner；构建命令 `g++ -O2 -std=c++17 -fPIE -pie -I"$ASCEND_HOME_PATH/include" acl_om_runner.cpp -o acl_om_runner -L"$ASCEND_HOME_PATH/lib64" -lascendcl`，事件 331；调用命令事件 342 原文）：

```bash
python3 "$SKILL_ROOT/scripts/run_om.py" \
  --runner "$A/runner/acl_om_runner" \
  --model "$A/evidence/run01_positive_baseline/model.om" \
  --source-model "$A/evidence/run01_positive_baseline/model.onnx" \
  --output-dir "$A/om-runs/baseline" \
  --input "$A/om-runs/input_x.bin" --input "$A/om-runs/input_y.bin" \
  --context-json "$A/om-runs/context.json" --device 0 --warmup 5 --runs 30 2>&1 | tail -3
```

在线 torchair 验证（事件 418 原文；`torch_online_run.py` 复用未修改的 `data/torch_forward.py` 的 `Model`，输入与离线一致的固定种子 `.bin`）：

```bash
( cd online/dumps-optimized && export ASCEND_GE_PY_PASS_PATH="$CASE_ROOT/src/python_add_zero_pass.py" && python3 "$CASE_ROOT/artifacts/repro/torch_online_run.py" "$CASE_ROOT/artifacts/online/optimized.npy" > "$CASE_ROOT/artifacts/online/optimized.log" 2>&1 ); echo "optimized rc=$?"
```

## 机制与判别

在 CANN 9.3.0（Ascend910_9362）上，Python `PatternFusionPass` 用 `@pattern` 表达式 `inputs[0] + 0` 匹配 `Data + Const -> Add` 拓扑、`meet_requirements` 读 `Const.value` 按 dtype 判零、`replacement` 透传 `inputs[0]`，可在 `BEFORE_INFER_SHAPE` 阶段消除 DT_FLOAT 的 `Add(x, 0.0)`（dump 6→4 节点，fusion_result match_times=1 effect_times=1）；判零代码同时实现 DT_FLOAT 容差 1e-6 / DT_DOUBLE 容差 1e-15 / DT_INT32 精确 0 三档，本轨迹仅实测 DT_FLOAT 分支。

证据链：pattern 命中（事件 219 日志）→ 图变换（事件 233 dump 对比：`add_zero`+`zero_const` 消失、`add_y` 改吃 `x:0`）→ 官方计数（事件 316 fusion_result：`PythonAddZeroPass: match=1 effect=1`）→ 整网输出一致（事件 350/365/423）。可区分解释：输出一致既可能因 pass 恒等消除、也可能因两侧编译链差异抵消——对照证据显示两侧 atc 默认链同等启用 fp16 UB 融合（`TbeEltwiseCastFusionPass effect=1` 两侧一致），且在线路径输出与 numpy FP32 `x+y` 最大绝对误差为 0.0，支持本次精确零样本的输出等价；不能证明容差范围内的非零常量消除仍为恒等改写；离线 OM 输出与 numpy fp32 的约 1.6e-4 差异两侧相同，与本 pass 无关（此归因为推断，判定依据是同管线内逐位一致）。

非零常量（Const=1.0）时 `meet_requirements` 返回 False，dump 图保持原状且编译继续（fusion_result match_times=1 effect_times=0）。

整网输出 baseline vs optimized 逐位一致：离线 OM（自建 ACL runner，device 0，warmup 5 / runs 30）与在线 torchair（复用未修改的 `data/torch_forward.py`）两条路径均成立；在线 pass 日志确认在 torchair 真实图上命中（`captured=arg0_1:0 ... zero=True`）。

未验证推断：`DT_DOUBLE`/`DT_INT32` 判零分支未实测；除 `torch.add(x, 0.0)` 与手构 ONNX 外的其他前端写法未实测。

## 验证信号

（平台：CANN 9.3.0 / Ascend910_9362 / 逻辑卡 0；以下均为本轨迹单次观测）

- 事件 219：pyatc 各运行 pass 日志——run02/run05 `zero=True` + `replacement`，run04 `zero=False` + `skip reason: const value 1.0 is not zero`。
- 事件 233：6 次运行 dump 节点结构——run02/run03/run05 的 `add_zero`+Const 消失、`add_y <- ['x:0', 'y:0']`（6→4 节点）；run01/run04/run06 图保持原状。
- 事件 316：fusion_result 官方计数——run02 `PythonAddZeroPass: match=1 effect=1`、run04 `match=1 effect=0`、run05 `match=1 effect=1`。
- 事件 350：离线 OM 输出比较 `status: PASSED`、`baseline==optimized exact: True`（`np.array_equal` 逐位）。
- 事件 365：在线输出 `identical: True`、`max abs err vs numpy fp32 x+y: 0.0`。
- 事件 423：在线 dump diff（baseline 不变 / optimized 6→4 节点）+ 在线 `fusion_result {'PythonAddZeroPass': {'effect_times': '1', 'match_times': '1'}}` + 在线输出 `identical: True`。
- 事件 437：最终 case-matrix 25/25 步 PASSED、validation-report `status: PASSED | gate: PASS`、ruff CLEAN。
- 结构性收益（L0 图层，非端到端性能）：删 1 Add + 1 Const + 1 中间 Tensor、零新增节点；L1/msprof 未运行，无时延/吞吐数据（2x2 模型不具性能代表性）。

## 适用与失效边界

- 精确 `Add(x,0)` 才是本卡已验证的恒等消除样例。历史代码对 DT_FLOAT 使用 1e-6、DT_DOUBLE 使用 1e-15 容差，会把近零非零加法改为透传；这属于近似优化，误差是否可接受须由业务预算和精度验证决定。
- 需要严格保留非零常量时，采用 [严格常量值匹配](patternmatcherconfigbuilderenable_const_value_match_const.md)，并直接核对真实常量值。当前版本 `Tensor.data` 对 1e-7 存在回读成 0.0 的观测，不能仅把本地比较改为 `== 0` 就声称已解决序列化精度问题。

- 判零分支中 `DT_DOUBLE`（容差 1e-15）与 `DT_INT32`（精确 0）未在本轨迹实测（fixture 均为 DT_FLOAT）；跨 dtype 常量是否进入该 pattern 未验证，采用前需自测。
- `Tensor.data` 回读存在字符串序列化精度损失（见[CANN 9.3.0 ge Python Tensor.data 字符串序列化回读精度有限：用 dump value_data 原始字节复核图内常量真值](cann_python_tensordata_dump_value_data.md)）：依赖 `Tensor.data` 做精确值（而非容差）判断的守卫会被显示值误导；本 pass 的 1e-6 容差判零在本观测范围内不受影响。
- 仅验证 `torch.add(x, 0.0)` 与手构 ONNX `Add(x, Constant(0))` 两种产生该拓扑的写法；含控制边、嵌套子图、动态输入输出个数的结构 PatternFusionPass 不可表达，需 graph 路线。
- 回退/失败行为：负例与不命中必须保持原图可编译（run04 已验证）；读 Const 失败（RuntimeError/AttributeError）时实现按『skip 打印 + 返回 False』保持原图。
- 版本边界：`register_fusion_pass(*, name, stage, kind=None)` 为关键字参数、`name` 全局唯一；`PassStage.BEFORE_INFER_SHAPE` 为 CANN 9.3.0 实测，replacement 后仍进入 GE 统一 shape 推导。
- 编译环境边界：不要把 `ASCEND_OPP_PATH` 覆盖为符号链接镜像的私有 OPP（会导致 ONNX 导入 E13010，见[ASCEND_OPP_PATH 覆盖符号链接镜像私有 OPP 致 pyatc ONNX 导入 E13010：二分定位后改用默认共享 OPP](ascend_opp_path_opp_pyatc_onnx_e13010.md)）；纯 Python pass 用 `set_env.sh` 默认共享只读 OPP 即可。
