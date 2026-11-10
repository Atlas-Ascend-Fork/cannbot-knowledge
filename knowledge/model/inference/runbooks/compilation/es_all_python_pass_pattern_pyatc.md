---
{
  "type": "Runbook",
  "title": "es_all 环境变量不跨命令保留导致 Python 融合 pass pattern 静默构建失败（pyatc 同命令内联修复）",
  "description": "逐条执行的 shell 命令间 export 不保留；pyatc 未在同一条命令内带上公共 es_all 的 PYTHONPATH/LD_LIBRARY_PATH 时，ge.es.math 回退到 CANN 内置 es_math（无 GEMM/Add/MatMul），@pattern 构建异常被桥接层吞掉，pyatc 仍编译成功但零融合。直接调用 patterns() 可显形异常；环境变量与 pyatc 内联同命令后融合恢复（fusion_result match=1 effect=1）。",
  "tags": [
    "task.debugging",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-03T12:00:00Z",
  "platforms": [
    "a3"
  ]
}
---

# es_all 环境变量不跨命令保留导致 Python 融合 pass pattern 静默构建失败（pyatc 同命令内联修复）

## 适用场景

- 平台/版本：Ascend910_9362、CANN 9.3.0、Python 3.11.4、pyatc CLI（`$ASCEND_HOME_PATH/bin/pyatc`，进程内加载 Python pass）；公共 es_all wheel 位于 `GE_ES_API_PYTHONPATH`/`GE_ES_API_LIB_DIR` 注入的路径（本例为 evaluation-agent 公共 `reference/es-api-runtime/cann-9.2.0` 产物）。
- 场景：通过 `ASCEND_GE_PY_PASS_PATH` 加载 Python PatternFusionPass，用 `ge.es`（es_all）的 GEMM/Add/MatMul/BatchMatMulV2 wrapper 构建 pattern/replacement；运行命令由 agent/编排工具逐条下发。
- 缺失信息：shell 环境由哪一层（工具沙箱/会话包装）逐命令重置，轨迹内未查明，只见其现象。

## 触发与观测

- 静默失败态（事件 311/312）：pyatc 加载 pass 后 `optimized exit=0`、`ATC run success`，但 pass 日志只有：

```
[PythonFuseMatMulAndAddPass] module loaded from ASCEND_GE_PY_PASS_PATH, registering for stage BEFORE_INFER_SHAPE
[PythonFuseMatMulAndAddPass] pattern defined: MatMul(a, b) + c
```

第二个 `pattern defined: BatchMatMulV2(a, b) + c` 与所有 `meet_requirements`/`replacement` 行缺失；日志无任何 traceback/错误（事件 316）。dump 对比（事件 318/327）：`PreRunBegin` 与 `RunCustomPassBeforeInfershape` 均为 `ge:BatchMatMulV2 + ge:Add`，节点数 6→6，零融合。
- 环境持久性探针（事件 349/350/352/353）：命令 A `export FOO_PERSIST_TEST=hello123` 后，命令 B 读到 `FOO_PERSIST_TEST=GONE`；`PYTHONPATH` 中也不含 `es-api-runtime`——export 不跨命令保留。
- 模块解析观测（事件 345/346）：`import ge.es.nn` OK，`import ge.es.math` 解析到 `.../cann-9.3.0/python/site-packages/es_math/__init__.py`（CANN 内置，不含 GEMM/Add/MatMul），`import ge.es.all` 直接 `ModuleNotFoundError: No module named 'ge.es.all'`。

结论（失败特征）：公共 es_all 的 PYTHONPATH/LD_LIBRARY_PATH（GE_ES_API_PYTHONPATH/GE_ES_API_LIB_DIR）在逐条执行的 shell 命令间不保留，export 的变量下一条命令即失效；pyatc 不在同一条命令内带上它们时，ge.es.math 解析到 CANN 内置 es_math（不含 GEMM/Add/MatMul），@pattern 构建抛 "ES API missing: MatMul, Add, GEMM"，异常被桥接层吞掉——pyatc 仍 exit=0、ATC run success，但无任何融合发生，可观测信号只有 pass 日志缺少 meet_requirements/replacement 行。

## 探针与操作

诊断探针（事件 341，在同一解释器内直接调用 patterns() 让被吞异常显形）：

```
export ASCEND_GE_PY_PASS_PATH="$CASE_ROOT/src/python_fuse_matmul_add_pass.py"; python3 -c "
import sys
sys.path.insert(0, '$CASE_ROOT/src')
import python_fuse_matmul_add_pass as m
inst = m.PythonFuseMatMulAndAddPass()
try:
    pats = inst.patterns()
    print('patterns() returned', len(pats), 'patterns')
except Exception as e:
    import traceback; traceback.print_exc()
" 2>&1 | grep -vE "^\[INFO\]|^\[WARNING\]|ATRACE" | head -25
```

结果（事件 342）：`RuntimeError: [PythonFuseMatMulAndAddPass] ES API missing: MatMul, Add, GEMM. Source CANN env first; ...`——正是 pyatc 运行中被吞掉的异常。结合事件 346 的 `ge.es.math.__file__` 指向内置 es_math，可确认加载的是哪一份 ES API。

诊断探针：在同一解释器里直接实例化 pass 类并调用 patterns() 可让被吞掉的异常显形（RuntimeError: ES API missing: MatMul, Add, GEMM）；对照 import ge.es.math 的 __file__（内置 site-packages 的 es_math 与公共 es_all wheel 路径不同）可区分实际加载的是哪一份 ES API。

修复（事件 356，环境变量与 pyatc 同一条命令内联）：

```
export PYTHONPATH="$GE_ES_API_PYTHONPATH:$PYTHONPATH" && export LD_LIBRARY_PATH="$GE_ES_API_LIB_DIR:$LD_LIBRARY_PATH" && export ASCEND_GE_PY_PASS_PATH="$CASE_ROOT/src/python_fuse_matmul_add_pass.py" && export DUMP_GE_GRAPH=1 && pyatc --framework=5 --model="$CASE_ROOT/artifacts/onnx/model.onnx" --soc_version=Ascend910_9362 --output="$CASE_ROOT/artifacts/pyatc-optimized/model_optimized"
```

修复：把 export PYTHONPATH="$GE_ES_API_PYTHONPATH:$PYTHONPATH"、export LD_LIBRARY_PATH="$GE_ES_API_LIB_DIR:$LD_LIBRARY_PATH"、export ASCEND_GE_PY_PASS_PATH 与 pyatc 放进同一条命令执行；修后两个 @pattern 均定义、meet_requirements/replacement 被调用，pyatc 生成的 fusion_result.json 记录 PythonFuseMatMulAndAddPass match_times=1 effect_times=1。

## 机制与判别

- 静默链路：pass 源码里 `from ge.es.math import GEMM, Add, MatMul` 因内置 es_math 存在但缺 GEMM 而抛 ImportError → 回退 `from ge.es.all import ...` 也 ModuleNotFoundError → 符号置 None（导入不报错）→ 真正构建 pattern 时 `_require_es_apis()` 抛 RuntimeError → 桥接层（`ge.passes` 的 pattern 收集路径，事件 334/338）把异常吞掉，pass 列表为空 → 编译继续、无融合。异常被推迟到 `_require_es_apis` 是导入回退设计的副作用。
- 判别变量是**加载哪一份 ES API**（内置 es_math vs 公共 es_all wheel），而区分手段是 `ge.es.math.__file__`；环境变量是否带上由"同命令内联"唯一决定。
- 可区分解释分支：(a) pattern 写错（op type 不匹配）——被 dump 排除（图本身有 BatchMatMulV2+Add 结构，事件 323/327）；(b) pass 未注册/未加载——被日志"module loaded ... registering"排除（事件 312）；(c) ES API 缺失——由 patterns() 直调证实（事件 342）。
- 反证：修复仅改环境变量内联方式（同一 pass 源码、同一 ONNX），融合即恢复（事件 357/361），支持归因。

## 验证信号

全部为单次会话内单次观测，Ascend910_9362 / CANN 9.3.0 / Python 3.11.4：

- 事件 312/316/327：失败态——exit=0、无错误日志、dump 零融合（修复前基线）。
- 事件 342：patterns() 直调显形 `RuntimeError: ... ES API missing: MatMul, Add, GEMM`。
- 事件 346：`ge.es.math` 解析到内置 `site-packages/es_math`；`ge.es.all` 不存在。
- 事件 350/353：export 变量下一条命令即 GONE（环境不持久）。
- 事件 357：修复后 pass 日志出现 `pattern defined: BatchMatMulV2(a, b) + c`、`meet_requirements: matched [BatchMatMulV2,Add] -> guard PASSED`、`replacement called`、`replacement built: GEMM(a, b, c, alpha=1.0, beta=1.0)`，`ATC run success`。
- 事件 361/365：dump 显示 `ge:BatchMatMulV2+ge:Add → ge:GEMM`，GEMM 直接消费 x/y/z。
- 事件 544：fusion_result.json `PythonFuseMatMulAndAddPass {'effect_times': '1', 'match_times': '1'}`。

## 适用与失效边界

- 适用：agent/编排工具逐条下发命令的执行环境（本轨迹为 opencode bash 工具）；公共 es_all 与 CANN 内置 es_math 并存、且内置版缺 GEMM/Add/MatMul 的 CANN 9.3.0 部署。
- 检查清单化用法：凡 pyatc/在线编译命令涉及 es_all，`PYTHONPATH`/`LD_LIBRARY_PATH` 必须与触发命令同条内联；持久化方案（写入 case 内 env 文件并逐命令 source）未在本轨迹验证。
- 失效边界：若环境的 PYTHONPATH 本身已含 es_all（如 EVAL 注入的解释器），本问题不出现；若 CANN 内置 es_math 未来补齐 GEMM/Add/MatMul，"缺失"症状也会消失，但环境不持久问题仍在。
- 静默性警示：该故障不会让编译失败，只能靠 pass 日志的 hooks 行缺失或 fusion_result.json 无条目察觉——验证流程必须显式检查这两处。
- 停止条件：内联环境变量后 patterns() 直调仍报 ES API missing 时，转向 es_all wheel 本身（是否存在/是否含目标算子）排查。
