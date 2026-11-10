---
{
  "type": "Runbook",
  "title": "fxrt 重构合入 torch-npu 后的模型接入层适配：显式 import torch_npu.fxrt 消除 ModuleNotFoundError",
  "description": "fxrt 框架重构后随 torch_npu wheel 以 torch_npu.fxrt 子包发布且懒加载（仅 import torch_npu 不注册顶层 fxrt 名），旧模型脚本的 fxrt.torch.* 命名空间全部失效报 ModuleNotFoundError。改 3 处模型侧接入层（import torch_npu.fxrt + from fxrt import fx_wrapper、register_fx_wrapper(device, patch_config=False)、变体映射 default→fxrt.fx_backend / converter→fx_converter），并补齐 triton 3.5.0 + triton_ascend 3.2.1（须后装 force-reinstall）与 decorator/attrs/psutil 后，ETA 模型端到端跑通，Precision check pass，落盘 104 个文件。",
  "tags": [
    "task.debugging",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "agnostic"
  ]
}
---

# fxrt 重构合入 torch-npu 后的模型接入层适配（消除 ModuleNotFoundError: No module named 'fxrt'）

## 适用场景

- 模型：ETA 推荐模型（RecSDK `rec_model_zoo_pytorch/behaviour_and_multi_task`，`bash launch_compile.sh`，mode=test_qps、batch 128、`--compile_backend=inductor` + `FX_WRAPPER=1` + `FX_DUMP_DIR` 落盘）。
- 框架：torch 2.13.0+cpu、torch_npu 2.13.0+gitea585a8（自带 `torch_npu.fxrt` 子包）、fx_converter 0.1.dev0+164734d（fxrt 仓 `bash build.sh -c` 产出的独立 wheel）、inductor-npu-ext 0.0.1（torchair AutoFuse）、CANN 9.2.0（cann_0930）。
- 硬件：Atlas 910B3（npu-smi 26.1.0.b050）、aarch64、conda 环境 om2_norm_py311_torch313（Python 3.11）。
- 前提：fxrt 框架重构合入 torch-npu（随 torch_npu wheel 发布、懒加载），不再安装独立 fxrt pip 包；模型脚本仍按旧架构写（`fxrt.torch.*` 命名空间）。

## 触发与观测

- 触发：`bash launch_compile.sh` 报 `ModuleNotFoundError: No module named 'fxrt'`（用户报告，事件 3）。
- 客观复现（事件 85）：`import torch_npu.fxrt` 与 `import fx_converter` 均成功，顶层 `import fxrt` 抛 `ModuleNotFoundError: No module named 'fxrt'`。
- 事件 86 pip list：环境无 fxrt 包，仅有 `torch_npu 2.13.0+gitea585a8`、`fx_converter 0.1.dev0+164734d`、`inductor-npu-ext 0.0.1`、`torch 2.13.0+cpu`。

## 探针与操作

修改单元为模型仓库侧 2 个功能文件（另同步 launch_compile.sh 与 utils/handler.py 的过时注释）：

1. `behaviour_and_multi_task/fxrt_fx_wrapper.py` 的 import。before（事件 24 原文，第 49 行）：

```python
from fxrt.torch import fx_wrapper as fxrt_fx
```

after（事件 144，读回于事件 181）：

```python
# torch_npu 对 fxrt 是懒加载：只 import torch_npu 不会注册顶层 ``fxrt`` 名字，
# 必须显式 import torch_npu.fxrt（其 __init__ 会把自己以顶层名 fxrt 装载，
# 内部 ``fxrt.*`` 绝对导入才能解析）。
import torch_npu.fxrt  # noqa: F401
from fxrt import fx_wrapper as fxrt_fx
```

2. `fx_wrapper_session` 内的注册调用（事件 219）：

```python
    # torch_npu.fxrt 顶层 import 不再自动接管 codegen（新版显式注册），这里的
    # register 就是唯一的安装点。但 `import inductor_npu_ext` 的
    # register_backend_for_device 是整条 DeviceCodegen 替换，会把装上的
    # FxrtFxWrapper 冲掉——fx_wrapper_codegen 一并重置为 None。这里（重）装一次，
    # 消掉导入顺序的不确定性。幂等。patch_config=False：config 的三件套
    # （fx_wrapper/size_asserts/alignment_asserts）由本 session 自己的
    # inductor_config.patch 管理，退出时恢复，不做成进程级。
    if not fxrt_fx.register_fx_wrapper(device=device, patch_config=False):
```

3. `utils/fxrt_backend.py` 变体映射（事件 161）。before（事件 59 原文）：

```python
# variant -> 提供 backend 的模块，每个模块都导出同名的 ``backend``
_VARIANT_MODULES = {
    "default": "fxrt.torch.fx_backend",
    "mlir": "fxrt.torch.fx_mlir_backend",
    "converter": "fxrt.torch.fx_converter_backend",
}
```

after（事件 161）：

```python
_VARIANT_MODULES = {
    "default": "fxrt.fx_backend",
    "converter": "fx_converter",
}
```

配套：`fxrt.torch.ascendc_fx_wrapper` → `fxrt.ascendc_fx_wrapper`（事件 150）等同步修改。

环境侧前置（非模型代码缺陷，但端到端必需）：om2_norm 环境补 `triton 3.5.0` + `triton_ascend 3.2.1`——pip 联装两个包时原生 triton 文件会反向覆盖 ascend 补丁的 `triton/backends/__init__.py`，`import triton` 抛 `ImportError: cannot import name 'Language' from 'triton.backends.compiler'`（事件 409），必须先装 triton、再 force-reinstall triton-ascend（或直接用 gitcode 3.2.1 wheel，事件 419/424）；另需 `decorator`/`attrs`/`psutil`（CANN tbe/tvm 编 autofuse kernel 的依赖，事件 438/445）。

失败探路（不可采用）：手工验证脚本用 `sys.path.insert(0, os.path.abspath('../..'))` 会解析到 `RecSDK/utils` 遮蔽 `rec_model_zoo_pytorch/utils`（事件 200/204/206 报 `No module named 'utils.fxrt_backend'`）；须按 eta.py 自身 root_path 逻辑用 `sys.path.append(os.path.abspath('..'))`。

## 机制与判别

- 结论：fxrt 框架重构合入 torch-npu 后，模型侧必须显式 `import torch_npu.fxrt` 注册顶层 `fxrt` 名字，并把 `from fxrt.torch import fx_wrapper` 改为 `from fxrt import fx_wrapper`、`install_torch_npu_fx_wrapper(device)` 改为 `register_fx_wrapper(device, patch_config=False)`，ModuleNotFoundError 随之消除。
  - 机制：`torch_npu/fxrt/__init__.py`（事件 44）在包名不是 `fxrt` 时用 `importlib.util.spec_from_file_location("fxrt", ...)` 把自身以顶层名 `fxrt` 重新装载进 `sys.modules`，此后 `fxrt.*` 绝对导入才能解析；torch_npu 对 fxrt 懒加载，仅 `import torch_npu` 不触发。
  - `patch_config=False` 的原因：`register_fx_wrapper` 默认（patch_config=True）进程级置位 inductor config 三件套（fx_wrapper/size_asserts/alignment_asserts），破坏 session 退出恢复语义；改由 session 自己的 `inductor_config.patch` 管理（事件 218→223 验证退出后恢复）。
- 结论：backend 变体映射改为 default→`fxrt.fx_backend`、converter→`fx_converter`（mlir 变体已随重构删除、显式报 ValueError），default/converter 后端实测可加载。
  - 机制：GE Convert 后端独立为 fx_converter wheel（入口 `from fx_converter import backend`），`fx_mlir_backend` 在 torch-npu 中已不存在（事件 103/127）。`FX_DUMP_DIR` 落盘路径（`_make_dump_backend` → `load_fxrt_backend()`）与 `--compile_backend=fxrt`（handler.py:625）共用该映射；该文件是模型仓库自己的接入层（`rec_model_zoo_pytorch/utils/`），不是 torch-npu 源码（事件 473 的解释，基于代码阅读）。
- 结论：适配并补齐环境依赖后模型端到端跑通：日志出现 `Precision check pass!` 与 `[fxrt] 使用 fxrt.fx_backend.backend 作为 torch.compile 后端`；本次单次观测 QPS 11976、AVG Latency 10.19ms，无同会话可比基线。
  - 混杂变量：模型脚本适配与 triton/triton-ascend/decorator 环境补装同时发生，QPS 变化不能归因单一改动。旧环境日志（事件 227，om2_dynamicshape + 旧独立 fxrt 包）QPS 6054，环境/版本组合不同，不可直接比较。

## 验证信号

（平台：Atlas 910B3 + CANN 9.2.0 + torch_npu 2.13.0+gitea585a8；证据等级：会话内单次观测）

- 事件 187：`import fxrt_fx_wrapper OK`，`register_fx_wrapper` 可达，env cfg 解析正常。
- 事件 208：default/converter backend 函数加载成功，`mlir -> ValueError OK`。
- 事件 223：session 内 `fx_wrapper_codegen: FxrtFxWrapper`、`in-session: fx_wrapper=True size_asserts=False`，退出后 `after-session: fx_wrapper=False size_asserts=False`（恢复语义保留）。
- 事件 452/456：端到端 run（run3）0 Traceback、进程正常退出、`Report json file saved in ../reports/eta`。
- 事件 459/463：`Precision check pass!`、`[fxrt] 使用 fxrt.fx_backend.backend 作为 torch.compile 后端`、QPS 11976 / AVG Latency 10.19ms（单次观测）、FX_DUMP_DIR 落盘 104 个文件。

## 适用与失效边界

- 适用于自带 fxrt 子包的 torch_npu（实测 2.13.0+gitea585a8）；`--disable_fxrt` 构建或不含 `torch_npu/fxrt` 的版本会在 `import torch_npu.fxrt` 处失败。
- 仅覆盖 default（fxrt.fx_backend）与 converter（fx_converter）两变体；`FXRT_BACKEND_VARIANT=mlir` 显式 ValueError。
- converter 变体要求已装 torch_npu 的 `FxrtFxWrapper` 带 `requires_autofuse_adapter` 标志，否则 HOP metadata 的 `adapter_path` 指向不存在的文件、Convert 失败（判定探针见 [autofuse_adapter.so 未生成的根因判别：requires_autofuse_adapter 标志探针（已装 wheel 落后于源码）](autofuse_adapterso_requires_autofuse_adapter_wheel.md)）。
- triton-ascend 必须在 triton 之后 force-reinstall；3.2.0 与 triton 3.5.0 联装有 backends 覆盖缺陷（事件 409），gitcode 3.2.1 wheel 已含 `ignored_dirs = {"nvidia", "amd"}` 跳过逻辑。
- QPS/延迟为本次单次观测（test_qps 虚拟数据、batch 128、dynamic_batch），不构成通用性能承诺。
