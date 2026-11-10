---
type: Runbook
title: "torch_npu 源码目录下 import 触发 _C circular import 的判别与规避"
description: "在 torch_npu 源码树（如 cann/ops-transformer 的 pytorch/ 子目录）内运行 Python 时，本地未编译的 torch_npu 包遮蔽 site-packages 安装版，torch 2.9.0 后端扩展自动加载报 ImportError: cannot import name '_C'；切到源码目录外执行导入即可正常加载。"
tags:
  - task.debugging
  - topic.implementation.debugging
status: draft
sources: []
created_at: "2026-10-29T10:53:31Z"
updated_at: "2026-11-06T09:40:40Z"
platforms: []
---

# torch_npu 源码目录下 _C circular import 判别与规避

## 适用场景

- 框架：torch 2.9.0+cpu（启用后端扩展自动加载 _import_device_backends）、torch_npu 2.9.0.post6（site-packages 安装）、torchair；Python 3.11.4（/opt/buildtools）。
- 环境：Linux 容器；工作目录位于 torch_npu 源码树内（${SOURCE_CHECKOUT}，其下存在未编译的 torch_npu/ Python 包，无 _C 扩展产物）。
- 目标与工作负载：在源码仓内执行任何 import torch / import torch_npu 的脚本或用例；本问题属 Python 导入层，复现不依赖 NPU 硬件。
- 缺失信息：硬件型号与 CANN 配置未记录（与本问题的复现无直接依赖）。

路径约定：`${SOURCE_CHECKOUT}` 为包含未编译 `torch_npu/` 包的源码检出目录；`${TORCH_NPU_PACKAGE}` 为该目录内的 `torch_npu` 包目录；`${OUTSIDE_SOURCE_DIR}` 为源码树外不含同名包的工作目录。按本地环境设置变量，代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

在 torch_npu 源码目录（${SOURCE_CHECKOUT}）内执行导入检查：

```bash
python -c "import torch, torch_npu, torchair; print(torch.__version__, torch_npu.__version__)" 2>&1; npu-smi info 2>&1 | head -20
```

逐字关键输出（节选）：

```
  File "${TORCH_NPU_PACKAGE}/__init__.py", line 41, in <module>
    import torch_npu.npu
  File "${TORCH_NPU_PACKAGE}/npu/__init__.py", line 154, in <module>
    from torch_npu.utils import _should_print_warning
  File "${TORCH_NPU_PACKAGE}/utils/__init__.py", line 4, in <module>
    from torch_npu import _C
ImportError: cannot import name '_C' from partially initialized module 'torch_npu' (most likely due to a circular import) (${TORCH_NPU_PACKAGE}/__init__.py)

The above exception was the direct cause of the following exception:

RuntimeError: Failed to load the backend extension: torch_npu. You can disable extension auto-loading with TORCH_DEVICE_BACKEND_AUTOLOAD=0.
/usr/bin/bash: npu-smi: command not found
```

在 torch_npu 源码目录（${SOURCE_CHECKOUT}）内执行 python 导入 torch、torch_npu、torchair 时，报 ImportError: cannot import name '_C' from partially initialized module 'torch_npu' (most likely due to a circular import) (${TORCH_NPU_PACKAGE}/__init__.py)，随后 RuntimeError: Failed to load the backend extension: torch_npu. You can disable extension auto-loading with TORCH_DEVICE_BACKEND_AUTOLOAD=0.，触发链路为 torch/__init__.py:2833 _import_device_backends → torch_npu/__init__.py:41 import torch_npu.npu → torch_npu/npu/__init__.py:154 from torch_npu.utils import _should_print_warning → torch_npu/utils/__init__.py:4 from torch_npu import _C 失败。

## 探针与操作

1) 确认 site-packages 安装清单（命令使用绝对路径，不受当前目录影响）：

```bash
ls /opt/buildtools/Python-3.11.4/lib/python3.11/site-packages/ | grep -i -E "torch|npu" ; pip list 2>/dev/null | grep -i -E "torch|npu|air"
```

site-packages 中确认存在 torch 2.9.0+cpu 与 torch_npu 2.9.0.post6 安装（dist-info 目录与 pip list 均列出，另含 torchaudio 2.11.0+cpu、torchvision 0.22.1、npu_ops_transformer 1.0.0）。

2) 切到源码目录外重跑导入探针（workdir=${OUTSIDE_SOURCE_DIR}）：

```bash
python -c "import torch_npu, torchair; print('torch_npu', torch_npu.__version__, torch_npu.__file__); print('torchair', torchair.__file__)" 2>&1
```

逐字关键输出：

```
[W1022 11:15:01.603698924 FunctionLoader.cpp:48] Warning: LD_PRELOAD detected, FunctionLoader prefers RTLD_DEFAULT for symbol resolution. (function operator())
torch_npu 2.9.0.post6 /opt/buildtools/Python-3.11.4/lib/python3.11/site-packages/torch_npu/__init__.py
torchair /opt/buildtools/Python-3.11.4/lib/python3.11/site-packages/torch_npu/dynamo/torchair/__init__.py
```

将工作目录切到源码目录外（workdir ${OUTSIDE_SOURCE_DIR}）后，同一解释器环境导入成功：torch_npu 2.9.0.post6 加载自 /opt/buildtools/Python-3.11.4/lib/python3.11/site-packages/torch_npu/__init__.py，torchair 加载自 /opt/buildtools/Python-3.11.4/lib/python3.11/site-packages/torch_npu/dynamo/torchair/__init__.py。

规避方式：在源码目录外运行脚本/用例（本轨迹已验证有效）。报错信息另提示可用 TORCH_DEVICE_BACKEND_AUTOLOAD=0 禁用自动加载（仅提示，本轨迹未实测该开关）。

## 机制与判别

- 源码目录内：当前目录优先进入 sys.path，`import torch_npu` 解析到本地未编译源码包（无 _C 扩展模块），在 torch_npu/utils/__init__.py:4 `from torch_npu import _C` 处失败，表现为 circular import 形态的 ImportError，进而 torch 后端扩展自动加载整体失败；traceback 中的模块路径（${TORCH_NPU_PACKAGE}/...）直接表明本次导入解析到源码树内包而非 site-packages。
- 源码目录外：同一解释器环境成功加载 site-packages 的 torch_npu 2.9.0.post6 与 torchair。
- 分支判别：若是 site-packages 安装损坏或版本不兼容，目录外导入同样会失败——实际成功；目录外导入成功而源码目录内导入失败，两次探针使用同一解释器环境（/opt/buildtools Python 3.11.4）与相同导入目标（torch_npu、torchair），实质差异是当前目录（源码树内 vs 外），故判别失败原因为源码目录内未编译的本地 torch_npu 包（无 _C 扩展产物）遮蔽 site-packages，而非安装损坏。

## 验证信号

- 源码目录内导入失败：ImportError _C circular import + RuntimeError Failed to load the backend extension: torch_npu（tool_observed，单次）。
- 目录外导入成功：torch_npu 2.9.0.post6 与 torchair 均加载自 /opt/buildtools/Python-3.11.4/lib/python3.11/site-packages（tool_observed，单次）。
- site-packages 安装清单完整：dist-info 目录与 pip list 均列出 torch 2.9.0+cpu 与 torch_npu 2.9.0.post6（tool_observed，单次）。
- 平台：Linux 容器，Python 3.11.4（/opt/buildtools），torch 2.9.0+cpu，torch_npu 2.9.0.post6；证据等级均为 tool_observed，单次对照观测，无重复测量，未涉及设备测试。

## 适用与失效边界

- 适用于 torch 2.9.0 的后端扩展自动加载机制（_import_device_backends）与含未编译 torch_npu/ Python 包的源码树布局（本例 cann/ops-transformer 仓 pytorch/ 子目录）。
- 规避方式“目录外运行”已在本轨迹验证；TORCH_DEVICE_BACKEND_AUTOLOAD=0 仅来自报错提示，未实测。
- “当前目录优先进入 sys.path”的解析顺序本轮未直接打印验证，该机制解释由 traceback 模块路径（…/pytorch/torch_npu/__init__.py）与目录外成功对照推断得出。
- 未验证：源码树完成完整编译（存在 _C 产物）后源码目录内是否可正常导入；其他 torch/torch_npu 版本组合；conda/虚拟环境布局差异。
- 失效情形：若源码目录外导入也报 _C 相关错误，则属 site-packages 安装损坏，本卡不适用。
