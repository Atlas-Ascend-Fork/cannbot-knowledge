---
{
  "type": "Runbook",
  "title": "ASCEND_OPP_PATH 覆盖符号链接镜像私有 OPP 致 pyatc ONNX 导入 E13010：二分定位后改用默认共享 OPP",
  "description": "共享 NPU 机器上把 ASCEND_OPP_PATH 覆盖为符号链接镜像的私有 OPP 目录（.private-opp，公共文件均为指向共享 CANN OPP 的只读软链）后，pyatc --framework=5 编译 ONNX（opset 18）在解析阶段报 Not_Supported_Operator(E13010)（ai.onnx::18::Add 无算子插件注册），6 次编译全部 rc=255 且不产出 dump/OM。单变量二分排除 opset 与 DUMP_GE_GRAPH 因素（默认 OPP 下 opset 9–18 全部成功；仅 OPP 覆盖复现失败）。修复为移除 ASCEND_OPP_PATH 覆盖、使用 set_env.sh 默认共享只读 OPP（ASCEND_CUSTOM_OPP_PATH 保留无害）后，6 次编译全部产出 OM+dump+fusion_result，图对比与 case-matrix 全部通过。适用于纯 Python pass（ASCEND_GE_PY_PASS_PATH）场景。",
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

# ASCEND_OPP_PATH 覆盖符号链接镜像私有 OPP 致 pyatc ONNX 导入 E13010：二分定位后改用默认共享 OPP

## 适用场景

- 场景：在共享 CANN 机器上用私有 OPP 目录树做 pass 隔离试跑时，用 `pyatc --framework=5` 离线编译 ONNX（Python pass 场景：`ASCEND_GE_PY_PASS_PATH` + `pyatc` 同进程加载）。
- 平台/版本：CANN 9.3.0（`ASCEND_HOME_PATH=${LOCAL_PATH_1}`），soc_version=Ascend910_9362，ONNX opset 18 / ir_version 9，Python 3.11.4。
- 隔离背景：批跑环境注入 `ASCEND_OPP_PATH=$CASE_ROOT/.private-opp` 与 `ASCEND_CUSTOM_OPP_PATH=$CASE_ROOT/.private-opp/vendors/evaluation_trial`；`.private-opp` 内 `Ascend/bin/built-in/conf/include/lib64/...` 均为指向共享 `cann-9.3.0/opp/` 的只读符号链接（`lrwxrwxrwx`，事件 178），仅 `vendors/` 可写。本例为纯 Python pass，不向 OPP 安装任何产物。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_2}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

首轮 6 次 pyatc 编译全部失败（事件 185 逐字）：

```text
[run01_positive_baseline] pyatc rc=255
[run01_positive_baseline] pbtxt dumps: 0
[run02_positive_mainpass] pyatc rc=255
[run02_positive_mainpass] pbtxt dumps: 0
...（run03–run06 同样 rc=255、0 个 dump）
```

`pyatc.stdout.log` 关键报错（事件 192 逐字，保留原始行号）：

```text
100: [PID: 1380209] 2026-10-17-11:23:00.753.435 Not_Supported_Operator(E13010): No operator plugin is registered for Op: add_zero, optype: ai.onnx::18::Add.
101:     Solution: 1. If the operator is a custom operator, register related deliverables.
102: 2. If the operator is a built-in operator, install the package that supports this operator version.
103: TraceBack (most recent call last):
104:         Origin 'ai.onnx::18::Add' for op 'add_zero' is not registered. Fix: make the plugin's domain and opsets cover this origin (plugin path: ASCEND_CUSTOM_OPP_PATH).[FUNC:Prechecker][FILE:onnx_parser.cc][LINE:745]
```

`check_result.json`（事件 196）：`zero_const`（Constant）success，`add_zero`/`add_y` 两个 `ai.onnx::18::Add` 均 failed，cause 为 `"The type is not supported."`；共享 OPP 与私有 OPP 的 `vendors/` 均为空（排除 vendors 内容差异）。

## 探针与操作

失败路线（before，事件 181 原文——**不可采用**）：

```bash
source "$ASCEND_HOME_PATH/set_env.sh"
# restore batch-injected private OPP isolation paths (set_env.sh resets them)
export ASCEND_OPP_PATH="$CASE_ROOT/.private-opp"
export ASCEND_CUSTOM_OPP_PATH="$CASE_ROOT/.private-opp/vendors/evaluation_trial"
export DUMP_GE_GRAPH=1
export ASCEND_SLOG_PRINT_TO_STDOUT=1
export ASCEND_GLOBAL_LOG_LEVEL=3
```

排除 opset 因素的探针（事件 199/200）：对 opset 9/11/13/16/18 各生成同构 ONNX，在默认 OPP（不覆盖）下编译，全部 `rc=0` 产出 OM。

单变量二分探针（事件 203 原文）：

```bash
cd "$CASE_ROOT/artifacts/evidence/diag" && for variant in a b c; do
  ( source "$ASCEND_HOME_PATH/set_env.sh" 2>/dev/null
    [[ $variant == a ]] && export DUMP_GE_GRAPH=1
    [[ $variant == b ]] && export ASCEND_OPP_PATH="$CASE_ROOT/.private-opp"
    [[ $variant == c ]] && { export DUMP_GE_GRAPH=1; export ASCEND_OPP_PATH="$CASE_ROOT/.private-opp"; }
    pyatc --framework=5 --model=model_opset18.onnx --soc_version=Ascend910_9362 --output=variant_$variant > variant_$variant.log 2>&1 )
  echo "variant $variant: rc=$? om=$(ls variant_$variant.om 2>/dev/null || echo none) err=$(grep -c 'is not registered' variant_$variant.log || true)"
done; ls -la ${LOCAL_PATH_2} 2>/dev/null
```

二分结果（事件 204 逐字）：`variant a: rc=0 om=variant_a.om err=0`；`variant b: rc=255 om=none err=2`；`variant c: rc=255 om=none err=2`。

修复（after，事件 211 原文）：

```bash
source "$ASCEND_HOME_PATH/set_env.sh"
# NOTE: do NOT override ASCEND_OPP_PATH with the .private-opp mirror here.
# Diagnosed in artifacts/evidence/diag: with ASCEND_OPP_PATH=$CASE_ROOT/.private-opp
# the ONNX parser fails E13010 (no operator plugin registered for ai.onnx::18::Add)
# because the mirror lacks the CANN-install-relative plugin layout. This case is a
# pure Python pass (ASCEND_GE_PY_PASS_PATH) and installs nothing into OPP, so the
# default read-only shared OPP (set by set_env.sh) is used for compilation.
# ASCEND_CUSTOM_OPP_PATH stays at the batch-injected private vendor dir (harmless,
# verified by diag variant a).
export DUMP_GE_GRAPH=1
export ASCEND_SLOG_PRINT_TO_STDOUT=1
export ASCEND_GLOBAL_LOG_LEVEL=3
```

## 机制与判别

`pyatc --framework=5` 编译 ONNX（opset 18）时，若 `ASCEND_OPP_PATH` 被覆盖为符号链接镜像的私有 OPP 目录（公共文件均为指向共享 CANN OPP 的只读符号链接），ONNX 解析阶段即失败：`Not_Supported_Operator(E13010): No operator plugin is registered for Op: add_zero, optype: ai.onnx::18::Add.`，rc=255、不产出任何 dump/OM。

二分对照排除 opset 与 DUMP_GE_GRAPH 因素：opset 9/11/13/16/18 在默认 OPP 下全部 rc=0 产出 OM；仅覆盖 `ASCEND_OPP_PATH` 的 variant rc=255（2 处 `is not registered`），仅开 `DUMP_GE_GRAPH` 的 variant rc=0。

机制推断（未完全验证）：`.private-opp` 虽为符号链接镜像，但 ONNX 算子注册插件按 CANN 安装相对布局解析，镜像缺少该安装上下文导致 `ai.onnx::18::Add` 无插件注册；具体缺失的相对路径/注册文件未进一步定位。`ASCEND_CUSTOM_OPP_PATH` 指向私有 vendor 目录本身无害（variant a 通过）。

修复为移除 `ASCEND_OPP_PATH` 覆盖、使用 `set_env.sh` 默认共享只读 OPP（`ASCEND_CUSTOM_OPP_PATH` 指向私有 vendor 目录已验证无害）后，6 次 pyatc 编译全部产出 OM + dump + fusion_result.json，5 组 dump 图对比全部 PASSED，最终 case-matrix 25/25 步 PASSED。

## 验证信号

（平台：CANN 9.3.0 / Ascend910_9362 / 逻辑卡 0；单次观测）

- 事件 185：修复前 6 次 pyatc 全部 rc=255、0 个 pbtxt dump。
- 事件 192：E13010 报错原文（`No operator plugin is registered for Op: add_zero, optype: ai.onnx::18::Add.` + `Origin 'ai.onnx::18::Add' ... is not registered`，onnx_parser.cc Prechecker）。
- 事件 200：opset 9/11/13/16/18 在默认 OPP 下全部 rc=0 产出 OM（排除 opset 因素）。
- 事件 204：二分对照——a（仅 DUMP_GE_GRAPH）rc=0、b（仅 ASCEND_OPP_PATH 覆盖）rc=255 err=2、c（两者）rc=255 err=2。
- 事件 215：修复后 6 次编译全部产出 `model.om` + 13 个 dump pbtxt + `fusion_result.json`。
- 事件 301：5 组 dump 图结构对比全部 PASSED。
- 事件 437：最终 case-matrix 25/25 步 PASSED、validation-report `status: PASSED | gate: PASS`。

## 适用与失效边界

- 适用组合：纯 Python pass（`ASCEND_GE_PY_PASS_PATH`，不落盘到 OPP）+ 私有 OPP 符号链接镜像隔离。结论是编译期不要覆盖 `ASCEND_OPP_PATH`；保留 `set_env.sh` 默认共享只读 OPP 即可满足隔离（pass 不写 OPP）。
- 不适用：C++ `.so` pass 必须安装到私有 OPP `vendors/` 的场景——需要真正的 OPP 安装布局（含算子注册 deliverables），此时 E13010 报错的 Solution 1（register related deliverables）才是正解；该路线本轨迹未验证。
- 失效条件：需要向私有 OPP 写入文件、或共享 OPP 本身缺算子包（报错 Solution 2 情形）。
- 版本边界：CANN 9.3.0 单版本观测；`ASCEND_OPP_PATH` 的解析语义在其他版本可能不同，跨版本使用前用事件 203 的二分探针复核。
