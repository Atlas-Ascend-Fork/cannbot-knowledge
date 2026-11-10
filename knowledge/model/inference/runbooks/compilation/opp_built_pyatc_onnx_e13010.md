---
{
  "type": "Runbook",
  "title": "私有 OPP 树 built-in 符号链接导致 pyatc ONNX 插件不加载（E13010）的定位与修复",
  "description": "CANN 9.3.0 下 ASCEND_OPP_PATH 指向的私有 OPP 树若 built-in 是指向共享 opp/built-in 的符号链接，pyatc 解析 ONNX 时所有 ONNX 框架插件都不被加载，每个算子报 E13010 not registered。受控实验与 LD_DEBUG 证实判别点是符号链接本身；改为真实目录+逐项符号链接后同环境编译成功，共享文件零改动。",
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

# 私有 OPP 树 built-in 符号链接导致 pyatc ONNX 插件不加载（E13010）的定位与修复

## 适用场景

- 平台/版本：Ascend910_9362（aarch64）、CANN 9.3.0（`ASCEND_HOME_PATH=${LOCAL_PATH_1}`）、pyatc/atc CLI 离线编译 ONNX（`--framework=5`，opset 17 模型）。
- 场景：共享 NPU 机器上的隔离试跑/评测批次——`ASCEND_OPP_PATH` 指向 case 私有 OPP 目录树（如 `$CASE_ROOT/.private-opp`），公共文件用符号链接指回共享 CANN OPP；`ASCEND_CUSTOM_OPP_PATH` 指向私有 vendors 子目录。
- 目标：让私有 OPP 树下 pyatc 能正常解析 ONNX 并完成编译。
- 缺失信息：私有 OPP 树由批跑系统预置，预置脚本不在本轨迹内；本轨迹只覆盖 CANN 9.3.0 一版的实测。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_2}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_3}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_4}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_5}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_6}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

baseline 编译（未加载任何 pass，事件 153/154）：

```
pyatc --framework=5 --model=.../model.onnx --soc_version=Ascend910_9362 --output=.../model_baseline
→ exit=255，ATC run failed
```

日志原文（事件 161）：

```
Not_Supported_Operator(E13010): No operator plugin is registered for Op: /MatMul, optype: ai.onnx::17::MatMul.
        Solution: 1. If the operator is a custom operator, register related deliverables.
Origin 'ai.onnx::17::MatMul' for op '/MatMul' is not registered. Fix: make the plugin's domain and opsets cover this origin (plugin path: ASCEND_CUSTOM_OPP_PATH).[FUNC:Prechecker][FILE:onnx_parser.cc][LINE:745]
```

check_result.json（事件 157）：`/MatMul`、`/Add` 均 `result: failed`、cause `code: 1, "The type is not supported"`，三个 `Input` 均 success——即全部 ONNX 计算算子解析失败，而非个别算子问题。

私有树结构（事件 208）：`.private-opp` 下 `Ascend/bin/built-in/conf/include/lib64/scene.info/script/test-ops/version.info` 全部是指向共享 `opp/` 对应项的**符号链接**，仅 `vendors/` 是真实目录。

结论（失败特征）：CANN 9.3.0 下，ASCEND_OPP_PATH 指向的私有 OPP 树中 built-in 若是指向共享 opp/built-in 的符号链接，pyatc --framework=5 解析 ONNX 时所有 ONNX 框架插件（liboponnx_plugin_*.so）都不会被加载，check_result.json 对每个 ONNX 算子报 "The type is not supported"，日志报 Not_Supported_Operator(E13010): No operator plugin is registered for Op: /MatMul, optype: ai.onnx::17::MatMul。

## 探针与操作

排除分支（判别非 opset、非插件内容、非 ASCEND_CUSTOM_OPP_PATH）：

- 插件内容探针（事件 174/178）：`strings liboponnx_plugin_legacy.so | grep "ai.onnx::[0-9]+::MatMul"` 列出 `ai.onnx::8` 至 `ai.onnx::18::MatMul`、`ai.onnx::14` 至 `ai.onnx::18::Add`——插件确实注册了目标 opset。
- 一致性探针（事件 204）：私有树与真实 OPP 的 `liboponnx_plugin_math.so` md5 完全一致（`8317397417f24e06cd2b9b6b4c724b0c`），其余插件大小逐字节相同。
- 环境变量对照（事件 211/212）：`env -u ASCEND_CUSTOM_OPP_PATH` 后依旧 E13010。
- 真实 OPP 对照（事件 215/216）：`env ASCEND_OPP_PATH="$ASCEND_HOME_PATH/opp" ASCEND_CUSTOM_OPP_PATH="$ASCEND_HOME_PATH/opp/vendors"` 编译 `exit=0`，产出 `model_baseline.om`。
- 加载观测（事件 284/285）：`LD_DEBUG=libs` 显示私有 OPP 失败进程对 `liboponnx` **零次**加载尝试；同一命令指向真实 OPP 时 5 个 `liboponnx_plugin_*.so`（transformer/cv/math/nn/legacy）全部 `calling init`。

该故障与 opset 支持无关：liboponnx_plugin_legacy.so 内已注册 ai.onnx::17::MatMul 与 ai.onnx::17::Add，私有树与真实 OPP 的插件 md5 完全一致；LD_DEBUG=libs 显示失败进程对 liboponnx 插件零次加载尝试，而 ASCEND_OPP_PATH 指向真实 OPP 时 5 个 liboponnx_plugin_*.so 全部正常 init。

受控判别实验（在 /tmp 复刻一个 OPP 根：`Ascend` 为真实目录、其余顶层项为符号链接、`vendors` 为空真实目录；两组唯一差异是 `built-in` 的形态）。符号链接组先执行 `ln -s "$ASCEND_HOME_PATH/opp/built-in" opptest/real/built-in`，再运行（事件 296）：

```
cd ${LOCAL_PATH_2} && env ASCEND_OPP_PATH=${LOCAL_PATH_3} pyatc --framework=5 --model="$CASE_ROOT/artifacts/onnx/model.onnx" --soc_version=Ascend910_9362 --output=${LOCAL_PATH_4} >/dev/null 2>&1; echo "symlink-built-in: exit=$?"
```

结果（事件 297）：`symlink-built-in: exit=255`。真实目录组（事件 300）：

```
rm built-in && mkdir built-in && for item in $(ls "$ASCEND_HOME_PATH/opp/built-in/"); do ln -s "$ASCEND_HOME_PATH/opp/built-in/$item" built-in/$item; done
```

同命令随后以 `--output=${LOCAL_PATH_5}` 重跑，结果（事件 301）：`realdir-built-in: exit=0` 且 `${LOCAL_PATH_6}` 产出（OM produced）。

修复（应用到 case 私有树，事件 307，仅改私有树内部结构、共享文件零改动、数据零复制）：

```
cd "$CASE_ROOT/.private-opp" && rm built-in && mkdir built-in && for item in $(ls "$ASCEND_HOME_PATH/opp/built-in/"); do ln -s "$ASCEND_HOME_PATH/opp/built-in/$item" "built-in/$item"; done
```

修复前后结构均留有证据：`artifacts/private-opp-builtin-before.txt`（事件 304/305：`built-in -> .../cann-9.3.0/opp/built-in` 符号链接）与 `artifacts/private-opp-builtin-after.txt`（事件 308：真实目录 + data/framework/op_graph/op_impl/op_proto 逐项符号链接）。轨迹内未执行回退恢复命令；如需恢复按 before 证据重建符号链接即可（此为推导，未在轨迹内执行）。

## 机制与判别

- GE 仓源码链（事件 229/230/233/234，`ge/parser/parser/common/tbe_plugin_loader.cc`）：`IsNewOppPathStruct(opp_path)` 用 `mmIsDir((opp_path + kBuiltIn).c_str()) == EN_OK` 判定新旧 OPP 结构；判为旧结构时 `GetCustomOpPath` 走 `GetOppPluginPathOld`，在 `opp/framework/...` 旧路径下找插件。而 CANN 9.3.0 新结构的 ONNX 插件实际位于 `opp/built-in/framework/onnx/`，旧路径下不存在——所以一个插件都找不到，报 E13010。这与 LD_DEBUG"零次加载尝试"（事件 285）一致。
- 未验证的内部归因：生产版 `mmIsDir` 拒绝目录符号链接的具体系统调用语义**未直接观测**——GE 仓内只找到 `tests/.../mmpa_stub.cc` 的 opendir 版测试桩（事件 241/242，opendir 会跟随符号链接），生产实现位于闭源/未获取的 mmpa 库。因此"IsNewOppPathStruct 因符号链接判旧结构"是据源码 + 受控实验的推断；硬证据是受控实验的判别结果与 LD_DEBUG 观测。
- 判别要点（可区分解释）：built-in 一层的**形态**（符号链接 vs 真实目录）是唯一判别变量；built-in 内部子项（framework 等）为符号链接不影响（事件 301）。
- 修复后同环境（保留原私有 `ASCEND_OPP_PATH`/`ASCEND_CUSTOM_OPP_PATH`）baseline `exit=0`、`ATC run success`、产出 `model_baseline.om`（事件 308）。

修复只需把私有 OPP 树的 built-in 由符号链接改为真实目录、目录内逐项符号链接到原共享子目录，数据零复制、共享文件零改动；受控实验证实判别点：built-in 为符号链接时 pyatc exit=255，built-in 为真实目录（内部子项为符号链接）时 exit=0 且产出 OM。

## 验证信号

全部为单次会话内的单次观测，平台 Ascend910_9362 / CANN 9.3.0：

- 事件 161/157：失败态 E13010 + check_result 全算子 not supported（修复前基线）。
- 事件 285：LD_DEBUG=libs——私有 OPP 0 次 liboponnx 加载尝试 vs 真实 OPP 5 个插件 init。
- 事件 297/301：受控实验——symlink-built-in exit=255 vs realdir-built-in exit=0 + OM produced。
- 事件 308：修复后 baseline pyatc exit=0、ATC run success、model_baseline.om 产出。
- 事件 312/357：修复后 optimized（加载 Python pass）exit=0，pass 全钩子触发。
- 事件 544：fusion_result.json 记录 `PythonFuseMatMulAndAddPass {'effect_times': '1', 'match_times': '1'}`。
- 事件 552：torchair 在线编译运行成功（同一修复后的私有 OPP 环境）。

## 适用与失效边界

- 适用：私有/沙箱 OPP 树用符号链接聚合共享 CANN OPP 的场景（隔离试跑、评测批次、容器挂载）。
- 判别点只在 OPP 根下 `built-in` 一层的形态；`built-in` 内部子项符号链接可用（这正是修复方案，事件 301）。
- 版本边界：仅实测 CANN 9.3.0；旧版 OPP 结构（无 built-in 层）或其他版本的 `mmIsDir` 行为未验证。
- 停止/转向条件：改为真实目录后仍 E13010 时，问题不在结构判定，应转向插件内容/opset 覆盖排查（事件 174/178 的 strings 探针）或 ASCEND_CUSTOM_OPP_PATH 指向的自定义 deliverables。
- 共享 CANN 安装目录只读约束下本修复仍然成立（不触碰共享文件）；若环境允许写共享树，也不应据此方案之外的任何共享树改动。
