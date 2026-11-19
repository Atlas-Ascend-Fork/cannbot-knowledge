---
type: Guide
title: TorchAir 图异常定界：FX/GE 图导出与 run_eagerly
description: 用图结构与 run_eagerly 分离图转换和执行异常，明确 GE 调试配置的生效范围以及导图产物含义。
tags:
- task.debugging
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/graph_dump.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/run_eagerly.md
  role: supporting
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/debug_save.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/dfx/debug_save.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/python_log_print.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/cplus_log_print.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/dfx/debug_save.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/debug_save.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/python_log_print.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/cplus_log_print.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/core/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/tng_status.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/include/logger.h
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/figures/graph_compile_6.png
  role: example
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/SECURITY_README.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/SECURITY_README_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/SECURITY_README.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/CONTRIBUTING_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/CONTRIBUTING.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/graph_dump.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/run_eagerly.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/core/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/core/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/_cache_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/__init__.py
  role: implementation
created_at: '2026-11-08T11:58:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# TorchAir 图结构与执行定界

## 输入和操作

保留同一版本、同输入的 Eager 输出、编译错误和模型配置。设置 TorchAir logger 为 DEBUG 可查看原生 FX 图；在构造 backend 前设置 `config.debug.graph_dump.type="pbtxt"` 和 graph_dump.path，导出构图信息。

type 可选 py、txt 或 pbtxt，一次不能同时导出三种格式，多次赋值以后一次为准；目录须存在且可读写。原始与优化后的 dynamo 图产物包含 graph、rank、pid 等身份，比较时保持对应关系；这类产物与 GE 编译/执行后的完整图不是同一个阶段。

## 分离图转换与执行

`config.debug.run_eagerly=True` 可在 GE 执行前用 Eager 执行 FX graph。开启后，GE 图模式相关功能配置不生效，所以此结果用于定界，不能报告为 GE 优化后的性能。

若 FX Eager 结果已异常，先审阅图前端和输入；若该路径正确而 GE 异常，再核对 Converter 和执行阶段。此顺序是依据功能职责形成的排查方法，具体故障仍需实际证据。

## 收尾

比对准确节点、输出与配置后关闭调试选项，重新验证正常后端。本文是固定主线操作说明，未在设备采集图或运行模型。

## 版本入口

- [软件栈来源与适用性](../../../concepts/frameworks/ascend_software_stack_baselines.md)：来源快照、部署配套和实际运行验证分别核对。

## 发布版自动收集与日志生效时机

固定发布子模块 7c6c754bed00c86ffaaa2a45cb7ac2724f058013 的 A2/A3 路线支持 TORCH_COMPILE_DEBUG=1 自动收集 Dynamo/AOT/各 Pass 图和日志，但只支持框架提供的后端，不支持自定义 backend。GE 要在 import torchair/from torchair import logger 前设置，否则可能缺少 torchair/debug.log；C++ TNG_LOG_LEVEL 同样应在导入前设置，默认 3(ERROR)，0 为 DEBUG，4 为 EVENT。

npugraph_ex 的 output_code.py 是编译后 FX 执行结构；Capture 算子执行图 JSON 还要求配套 CANN≥8.5.0，文件缺失先核对版本。不要把结构文件存在当作已经 Capture/Replay 成功。Python logger 的 EVENT_LEVEL 是关键流程耗时级别，不与普通 DEBUG 级别混同。

- [真实 Tensor 数据的 Dump 模式](torchair_data_dump_modes.md)
- [图内异步打印](../../../apis/torchair/npu_print.md)

## 主线 npugraph_ex 的产物变化

固定主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 将日志与 Pass 产物放在 npugraph_ex 目录；分布式运行目录追加 rank 标识，并要求脚本开头 import npugraph_ex。Capture 运行实例的原始 *.json 与可视化用 *.aligned.json 要配套 CANN≥8.5.0；两者与 output_code.py、AOT 前后 FX 图处于不同阶段。

主线 compile_fx 入口可收集 Debug 信息，但缺少 AOT 前 dynamo_out_graph.txt 是接口阶段造成的正常边界，不应直接判断为收集失败。该能力与本卡发布版本“只支持框架后端”的说明分别适用，不能混成所有版本通用规则。

## 主线GE自动收集、rank目录与日志优先级

主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的GE debug_save页继续要求使用框架npu_backend且在导入TorchAir/logger前设置TORCH_COMPILE_DEBUG=1；图示分为AOT前、AOT后、公共Pass后FX与GE优化前/各Pass后结构，不是所有文件都代表同一阶段。目录中的model__0、forward/backward用于区分编译单元，不能由示例带loss.backward便认定任意训练图已支持。

主线分布式目录增加-rank_<rank_id>。core/utils.py在导入时安装get_debug_dir包装，但实际取rank时检查dist是否已初始化；未初始化返回原目录，不能保证所有启动阶段产物都带rank。_init_debug_logging在后端/缓存编译入口初始化torchair/debug.log，Python与C++写到该位置；入口阶段、导入时环境、当前rank初始化都会影响实际文件。导入后再改环境不应被当作受支持的完整初始化路线，即使某次后续调用仍创建了文件。

C++的TNG_LOG_LEVEL在静态初始化时读取，取0/1/2/3/4分别为DEBUG/INFO/WARNING/ERROR/EVENT。显式设置优先于TORCH_COMPILE_DEBUG；空值或非法值回退ERROR，因此TORCH_COMPILE_DEBUG=1并不保证覆盖已有TNG_LOG_LEVEL=3或空值。未显式设置TNG且debug=1时才回退DEBUG。C++的EVENT只在配置4时启用，不能把0理解为包含全部专门事件计时；ERROR始终可输出。

Python logger默认ERROR，debug环境在模块导入时令其为DEBUG；EVENT_LEVEL实际为35，使用Python日志阈值，不能与C++整数4互换。Dynamo/AOT日志用torch._logging.set_logs独立配置，TorchAir logger.setLevel不自动开启所有Dynamo重编译日志。先按阶段采集，再比较对应rank、模型和Pass，不能把图文件存在当作执行成功或性能收益。

发布与主线的Python/C++日志页正文相同；GE debug页主线增加rank目录说明，图示两快照字节一致并已查看。本次未启用环境变量、导入上游或采集设备日志。

## 根安全声明的公开边界与图文件身份

两快照安全声明称GE结构Dump默认关闭、所生成图文件默认600；这是其描述的生成路径，不保证所有Debug日志、复制/归档、FX数据或后端产物继承同一权限。参考权限表是最大权限建议，不把umask的数字大小当权限严格程度。本次未改权限、开启Dump或读取产物。

TorchAir正式接口仅Python，二进制内部动态库符号不是直接对外服务；有文档且符合公开约定才按公开接口消费。ROOT声明的TNG_LOG_LEVEL与Python logging条目不替代本卡已读代码的优先级与导入时机。发布安全声明把graph_dump字段误写dtype，主线修为type；不要把同名文字当有效配置别名。

贡献页的txt/pbtxt/py格式和旧dynamo_timestamp命名仅描述对应导图阶段，不把py导图“可运行”当没有CANN/版本依赖的独立部署物，也不执行导出的代码。源码构建会下载依赖并执行shell、Dump/推理数据可能占用内存和磁盘；这些是实际依赖/资源检查项，不把错误退出唯一归因为某一资源问题。

## Evidence

- [docs/zh/ascend_ir/features/basic/graph_dump.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/graph_dump.md)（primary）
- [docs/zh/ascend_ir/features/basic/run_eagerly.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/run_eagerly.md)（supporting）
- [docs/zh/overview.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [本轮补充来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/debug_save.md)（constraint）

- [本轮补充来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/dfx/debug_save.md)（constraint）

- [本轮补充来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/python_log_print.md)（constraint）

- [本轮补充来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/cplus_log_print.md)（constraint）

- [本轮补充来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/dfx/debug_save.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/debug_save.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/python_log_print.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/cplus_log_print.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/core/utils.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/tng_status.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/include/logger.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/figures/graph_compile_6.png)（example）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/SECURITY_README.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/SECURITY_README_en.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/SECURITY_README.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/CONTRIBUTING_en.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/CONTRIBUTING.md)（constraint）

- [完整页复核来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/graph_dump.md)（constraint）

- [完整页复核来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/run_eagerly.md)（constraint）


## debug.log初始化机制：发布import期急切与主线后端入口延迟

本节用两 pin `python/torchair/core/utils.py` 全文（发布 79 行、主线 135 行）加 AST 比较固定该差异，并为『发布版自动收集与日志生效时机』的时序承诺补上源码绑定。

发布版在模块导入时急切初始化：`_torchair_debug_log_path = _create_debug_log_paths()` 在 import 当刻执行——TORCH_COMPILE_DEBUG=1 时创建 `<torch._dynamo debug 目录>/torchair/debug.log`、调用 `_torchair.SetDebugLogPath` 传给 C++，并把该路径作为 `file=` 传入 `_get_logger`，FileHandler 随 import 挂上；环境变量未在导入前设置则得到 None，且发布模块内没有第二次初始化入口（两 pin 的 python/ 树 rg 确认 `_create_debug_log_paths` 与 `SetDebugLogPath` 无其他调用方）。这把发布 debug_save.md“方法二”注意事项（导入后才设置环境变量会缺失 torchair/debug.log）从文档承诺绑定到源码机制：缺失在该模块内是必然结果，不只是经验观察。

主线改为延迟初始化：模块级 `logger` 以 `file=None` 创建，但日志级别在导入时即固定（第 133–135 行：`TORCH_COMPILE_DEBUG=1` 时 DEBUG，否则 ERROR）；`_init_debug_logging()` 在 `npu_fx_compiler.get_npu_backend`（1056 行，函数体首句）与 `inference/_cache_compiler.py`（704 行）调用时，先经 `_create_debug_log_paths()` 重读环境变量并调用 `_torchair.SetDebugLogPath`（第 23 行）把路径传给 C++，再创建 debug.log 并挂 FileHandler——C++ 路径与 Python 文件都在后端入口延迟初始化，不是只在 import 期设置；`_set_dynamo_run_dir_name()` 在包导入（`torchair/__init__.py:55`）时检查环境并通过 `_TORCHAIR_RUN_NAME_PATCHED` 幂等安装 get_debug_dir 的 rank 后缀包装。AST 比较：两 pin 的 `_create_debug_log_paths`、`_get_logger`、`_EventLogger`、`_MillisecAndMicrosecFormatter` 完全相同，差异集中在主线新增 `_init_debug_logging`、`_set_dynamo_run_dir_name` 两个函数与模块级赋值（`_torchair_debug_log_path=None`+`_TORCHAIR_RUN_NAME_PATCHED` 取代发布的急切调用）。静态字面观察：主线该文件导入清单不含 warnings，`_set_dynamo_run_dir_name` 的 ImportError 分支引用 `warnings.warn` 按字面将 NameError——未运行验证；独立包主线副本已正确 import warnings。

版本边界：发布版“导入后设置环境变量导致 debug.log 缺失”在模块内无补救路径；主线后端构造可同时补救 Python FileHandler 与 C++ `SetDebugLogPath` 路径——两者都在延迟初始化里经 `_create_debug_log_paths()` 重读环境后设置。但 logger 级别已在导入期固定：导入后才设置环境变量的进程，其 TorchAir logger 仍为 ERROR，只有延迟路径创建的文件会补上；get_debug_dir 的 rank 后缀包装也只在导入期由 `_set_dynamo_run_dir_name` 检查环境安装，导入后置位不再补装，但没有上游证据时不得把所有 dynamo 输出目录断言为永久固定于导入期环境。不能把任一版本的时序写成两版本通用规则。独立包两 pin 各持 core/utils.py 副本并呈同样急切/延迟分化，其 design 文档承诺核对另见[独立包设计合同](../torchair/npugraph_ex_standalone_design_contracts.md)。

## 固定来源与核验范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/core/utils.py)（implementation）：1–135 完整读取。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/core/utils.py)（implementation）：1–79 完整读取。
- [新增来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)（implementation）：1050–1060 定向窗口（get_npu_backend 内 _init_debug_logging 调用）。
- [新增来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/_cache_compiler.py)（implementation）：29、704 单行定位。
- [新增来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/__init__.py)（implementation）：28–29、55 单行定位。
