---
{
  "type": "Runbook",
  "title": "torchair 内置于 torch_npu：单独 import 失败不代表在线路径不可用（导入顺序探针）",
  "description": "CANN 9.3.0 环境下单独 import torchair 报 ModuleNotFoundError，但 import torch_npu 会自动把 torchair 装入 sys.modules（位于 torch_npu/dynamo/torchair）。环境探测必须用链式导入 import torch_npu; import torchair，否则会把 torchair 在线编译路径误判为框架缺失；本轨迹在线路径实测运行成功。",
  "tags": [
    "task.debugging",
    "task.testing",
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

# torchair 内置于 torch_npu：单独 import 失败不代表在线路径不可用（导入顺序探针）

## 适用场景

- 平台/版本：Ascend910_9362、CANN 9.3.0（`python/site-packages` 含 torch_npu 2.7.1.post4）、Python 3.11.4；宿主 torch 2.7.1+cpu。
- 场景：GE Python pass 的 torchair 在线触发路径（`torch.compile(model, backend=torchair.get_npu_backend(...))`）前的环境可用性探测/体检。
- 缺失信息：独立安装的 torchair 包环境不适用本结论；torch_npu 其他版本未验证。

## 触发与观测

- 触发（事件 47/49）：`python3 -c "import torchair"` → `ModuleNotFoundError: No module named 'torchair'`；据此初判"torchair 缺失（在线脚本稍后会记录为框架问题）"。
- 矛盾信号（事件 122）：随包 check_env.sh 的探测项写法是链式 `import torch_npu; import torchair; import ge, ge.passes`，结果为 `[OK] python: torch_npu → torchair → ge.passes 导入顺序可用`——与单独导入失败矛盾。

## 探针与操作

三段式导入顺序探针（事件 134）：

```
python3 -c "import torch_npu; import torchair; print('chain: torch_npu then torchair OK')" 2>&1 | grep -vE "INFO|ATRACE|\[W" | tail -2; echo "==="; python3 -c "import torchair; print('torchair alone OK')" 2>&1 | grep -vE "INFO|ATRACE|\[W" | tail -2; echo "==="; python3 -c "import torch_npu, sys; print('torchair in sys.modules:', 'torchair' in sys.modules)" 2>&1 | grep -vE "INFO|ATRACE|\[W" | tail -1
```

结果（事件 135）：

```
chain: torch_npu then torchair OK
===
ModuleNotFoundError: No module named 'torchair'
===
torchair in sys.modules: True
```

运行时探测（事件 138/139，check_runtime.py 产物 runtime-probe.json）：`torchair` 模块 `status: PASSED`，`file: /opt/buildtools/Python-3.11.4/lib/python3.11/site-packages/torch_npu/dynamo/torchair/__init__.py`。

torch_npu 2.7.1.post4（CANN 9.3.0 环境）内置 torchair：import torch_npu 会自动把 torchair 装入 sys.modules（torchair.__file__ 位于 torch_npu/dynamo/torchair/__init__.py）；单独 import torchair 报 ModuleNotFoundError: No module named 'torchair' 属正常现象，不代表在线路径不可用。

环境探测的正确写法是链式导入 import torch_npu; import torchair; import ge, ge.passes；只测单独 import torchair 会把在线编译路径误判为框架缺失（本轨迹初判即出错，后经链式探针纠正，在线路径实测运行成功）。

## 机制与判别

- 机制：torchair 不是独立 site-package，而是 torch_npu 的内置子包（`torch_npu/dynamo/torchair`）；`import torch_npu` 的初始化会把它装入 `sys.modules`，此后 `import torchair` 直接命中——导入顺序是唯一判别变量（事件 135 的三段对照）。
- 干扰排除（事件 126/127）：`env -i` 清空环境的再验证连 `import torch_npu` 都失败（干净 shell 缺 buildtools python 的 site-packages 路径），那是另一个问题，不能用来反驳本结论。
- 纠正后果（事件 551/552）：在线路径 `data/torch_forward.py`（torch.compile + torchair backend）实测 `online exit=0`、输出 tensor 正常，且 pass 命中 `matched [MatMul,Add]`——链式探测的判断得到端到端证实。

## 验证信号

全部为单次会话内单次观测，CANN 9.3.0 / torch_npu 2.7.1.post4 / Python 3.11.4：

- 事件 135：chain OK / alone FAIL / `torchair in sys.modules: True`。
- 事件 139：`torchair.__file__ = .../site-packages/torch_npu/dynamo/torchair/__init__.py`（runtime-probe.json，status PASSED）。
- 事件 552：在线编译+推理成功且 pass 命中（`meet_requirements: matched [MatMul,Add] -> guard PASSED`）。

## 适用与失效边界

- 适用：torch_npu 内置 torchair 的部署（本轨迹实测 2.7.1.post4 / CANN 9.3.0）；环境体检脚本、可用性探测逻辑应写链式导入并检查 `sys.modules`，不能只测单独 import。
- 失效边界：独立安装 torchair（pip 包）的环境不存在该现象；`env -i` 等清空环境的探测会引入 site-packages 缺失的另一故障，需先恢复解释器环境。
- 只证明导入可见性与在线路径可用性，未测 torchair 功能面。
- 停止条件：链式导入也失败时，按 torch_npu 安装/解释器环境问题排查，与本规则无关。
