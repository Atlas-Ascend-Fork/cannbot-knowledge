---
type: Guide
title: TorchAir gegraph_check 死锁检查工具链：首跑触发、任务过滤与向量时钟并发判定
description: 补齐 config.debug.deadlock_check 的实现层证据：C++ 首跑钩子门控、过滤/对齐/死锁三工具的输入合同、AIVEC
  核账与向量时钟并发判定及两版差异。
tags:
- task.debugging
- topic.parallelism
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/tools/gegraph_check/deadlock_check.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/tools/gegraph_check/filter_operators.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/tools/gegraph_check/align_trace.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/npu_utils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/static_npu_graph_executor.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/dynamic_npu_graph_executor.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/muti_gear_npu_graph_executor.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/debug_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/tools/aclgraph_check/deadlock_check.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/tools/aclgraph_check/filter_operators.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/tools/aclgraph_check/align_trace.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/configs/compiler_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/deadlock_check.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/dfx/deadlock_check.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/npu_utils.cpp
  role: evidence
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/debug_config.py
  role: evidence
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: evidence
- resource: https://docs.python.org/3/c-api/exceptions.html#c.PyErr_PrintEx
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/npugraphex_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/debug_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/dfx/dfx.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/dfx/dfx.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/tools/aclgraph_check/deadlock_check.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/tools/aclgraph_check/filter_operators.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/tools/aclgraph_check/align_trace.py
  role: implementation
created_at: '2026-11-12T04:17:22Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchAir gegraph_check 死锁检查工具链

主线 TorchAir 的 [多流死锁检测](../torch_npu/torchair_multistream_deadlock_check.md) 开关背后是一条 C++ 首跑钩子加三个离线工具组成的链路：`torchair/npu_graph_executor` 在图首次运行时落盘图任务 JSON 并回调 Python，`python/torchair/tools/gegraph_check/` 里的 `filter_operators.py`、`deadlock_check.py`、`align_trace.py` 负责过滤、判定与可视化。本文按固定主线与发布源码静态读取，未运行工具或复现死锁。

## 触发链：首跑钩子与门控

- 开关经 `CompilerConfig` 的 `debug.deadlock_check`（bool，默认 False）进入 debug 组 `as_dict` 的图编译选项；C++ 侧 `CallPythonDeadlockCheck` 按字符串 `"1"` 判定启用，其它值一律视为关闭。
- 触发点只在图首次运行：static、dynamic、muti_gear 三种执行器都在 FastLoad/FastExecute 能力分支内、`FastLoadGraph` 成功之后各调用一次。`RunGraph` 回退分支不调用——运行环境不支持 FastLoad/FastExecute 时，即使开关为真也不产生任何检查产物。
- 落盘前还有两道门：Python 解释器必须已初始化；Session 支持 `GraphDebugJSONPrint`（该支持位是函数内 static，进程内只探测一次）。之后把图任务 JSON 写到 `./debug_output_graph_<图id>_timestamp<本地时间>_pid_<pid>.json`（`./` 为相对路径，经 `std::ofstream` 打开，落点是**进程当前工作目录**，不是源码脚本所在目录），再在 GIL 内 `import torchair._ge_concrete_graph.utils` 并调用 `run_deadlock_check(文件路径)`。
- 容错边界：该函数返回 void，文件打开失败只记错误日志；导入失败、取属性失败或普通 Python 异常经 `PyErr_Print` 打屏后不再向 C++ 传播，不中止本次图执行。但不能据此承诺"任何回调异常都只记日志"：`PyErr_Print` 等价 [`PyErr_PrintEx(1)`](https://docs.python.org/3/c-api/exceptions.html#c.PyErr_PrintEx)，Python C API 文档写明 `SystemExit` 不按普通 traceback 打印，而是按其退出码终止解释器；链路内可达的 `filter_comm_ops` 输入文件缺失分支正是 `sys.exit(1)`，命中时进程以退出码 1 终止。检查是尽力而为的诊断旁路，不是执行前置校验；其同步成本发生在[首次调用](torchair_ge_runtime_binding_and_first_call.md)路径内。

## run_deadlock_check：阈值与两步流水

`run_deadlock_check` 先取 `torch.npu.get_device_limit(当前设备)['vector_core_num']` 作为 AIVEC 总额——阈值就是这一次**设备级**查询的返回值，不是常量 48（文档示例的 48 只是特定设备）；不能把它泛化为自动涵盖所有 scope/stream 级[控核设置](torchair_core_limits_and_determinism.md)，判定只按该查询值计账。绕开它单独命令行调用 `deadlock_check.py` 时 `--aivec-total` 默认 48，需按设备显式指定。随后 `filter_comm_ops(输入, None)` 生成 `<输入>_filtered.json`，再 `deadlock_check(过滤产物, None, aivec_total=阈值)`；两个工具的后缀各自从**自己的输入**派生：对 `foo.json`，过滤产出 `foo_filtered.json`，有风险时最终标注文件是 `foo_filtered_deadlock_check.json` 而非 `foo_deadlock_check.json`，与文档产物清单一致。无风险时只打屏 `No deadlock risks detected` 并返回，不写结果文件。因此不能以"没有 `_deadlock_check.json`"区分"未启用"和"无风险"，要以打屏日志为准。

## 过滤与对齐：输入合同与可视化

`filter_operators.py` 只保留两类任务：控制类（`EVENT_RECORD_`/`MEM_WRITE_VALUE_` 前缀为 record 端、`EVENT_WAIT_`/`MEM_WAIT_VALUE_` 为 wait 端）与通信类（名称以 `aiv_`、`hccl_aiv` 开头，或含 `dispatch`/`combine`，或 ExtendInfo JSON 的 `taskType=="communication"`），其余全部丢弃；通信任务 `Schem Mode≠1` 时打告警。输入文件不存在直接 `sys.exit(1)`；任务缺 `args` 键时 `task.get("args","")` 再 `.get` 会 AttributeError——工具只接受 CANN 图调试 JSON 这种带 args/Task Id 的事件结构，不是任意 Chrome Tracing 文件。

`align_trace.py` 是可选的人工可视化辅助，不参与死锁判定：把每流内 task 重排为 0.2 间隔的逻辑时序，把跨流 WAIT 拉长到与对应 RECORD 右端对齐并右移后续任务，最多迭代 200 轮，不收敛直接 `SystemExit`；对齐后校验数值有限性、流内间隔和配对对齐，任一失败即 `SystemExit`，全部通过才写 `<输入>.aligned.json`，并附 Chrome Tracing flow 箭头事件、清洗名称中的 hash 片段（控制事件保留完整 handle 数字）。死锁检测只用任务名和 args、不依赖 ts/dur，喂原始或对齐 JSON 结果一致；torch_npu 侧独立的 trace 对齐入口见 [对齐轨迹解读](../torch_npu/torch_npu_npugraph_aligned_trace_interpretation.md)。

## 死锁判定：向量时钟并发与 AIVEC 核账

- 虚拟流合并：三个工具都在处理前把 `STREAM_ACTIVE` 激活的虚拟流原地合并回宿主流（改写 ts/tid/Stream Id）；不合并会因流归属错误漏报误报。
- 并发不用时间轴：ts/dur 只是可视化示意；两任务并发当且仅当互不 happens-before，用向量时钟在 record/wait 配对上迭代到不动点，自动覆盖任意深度的传递依赖（如三流链式同步）。
- 候选任务：`Schem Mode==1` 且被判为通信且 AIVEC 占用大于 0。核账规则：`KERNEL_AIVEC` 与 `KERNEL_MIX_AIV` 记 Numblocks，`KERNEL_MIX_AIC` 在 Task Ration 为 0 时记 0、否则 Numblocks×2，`KERNEL_AICORE` 与控制类记 0。
- 风险判定：不同流上两并发通信任务的 AIVEC 之和严格大于总额即记一对冲突；输出把冲突任务名加 `dead_lock_` 前缀、dur 改 49.5 写回标注 JSON，并把配对与任务清单打屏。检测只覆盖这类资源型成对冲突，不证明不存在其它等待环、rank 间不一致或网络故障；成因排查仍按[多流依赖](graph_multistream_dependencies.md)与[调度切分](ge_scheduling_and_static_partition.md)核对。

## 失效边界

- 集成版 `_is_comm_task` 在 ExtendInfo 为空且名称不含 `aiv_`/`dispatch`/`combine` 时引用未赋值局部变量，抛 UnboundLocalError；ExtendInfo 非空时必须是合法 JSON。即一个 `Schem Mode==1` 但名称不像通信又无 ExtendInfo 的任务会让检查中断。
- 判定和落盘都在首跑同步路径上完成，属于首次运行成本的一部分；多流死锁属资源型风险，检测不改变调度，也不会自动修复。

## 版本与独立包差异

- 固定发布 `7c6c754` 没有 `python/torchair/tools/` 目录，`npu_graph_executor` 无 `CallPythonDeadlockCheck`，debug 配置无 `deadlock_check` 项——整条工具链为主线独有；发布版文档级"不支持 dynamic=True"等契约仍以[多流死锁检测](../torch_npu/torchair_multistream_deadlock_check.md)为准。
- 主线独立 npugraph_ex 包在 `tools/aclgraph_check/` 镜像了三工具：`align_trace.py` 与集成版逐字节相同；`deadlock_check.py`、`filter_operators.py` 仅去掉 ExtendInfo `taskType=="communication"` 判定分支（改为纯名称子串判定，因而不再有上述未赋值路径），其余逐行一致。独立包 `options.deadlock_check` 选项存在，但固定主线源码内未检索到这些镜像工具的任何调用方；其文档所述 `torch_compile_debug` 目录下产物的触发链在本次固定源码内未闭合，不能把集成版首跑链推给独立包。

## 相关阅读

- [多流死锁检测：文档级开关契约](../torch_npu/torchair_multistream_deadlock_check.md)
- [GE 调度：通算并行、单流与静态子图阈值](ge_scheduling_and_static_partition.md)
- [图内多流依赖：record/wait 与 Event](graph_multistream_dependencies.md)
- [TorchAir 控核与确定性](torchair_core_limits_and_determinism.md)
- [GE 运行期绑定与首次调用编译时序](torchair_ge_runtime_binding_and_first_call.md)

## 实现来源

- [deadlock_check](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/tools/gegraph_check/deadlock_check.py)（primary）：1–643 全文。
- [filter_operators](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/tools/gegraph_check/filter_operators.py)（primary）：1–309 全文。
- [align_trace](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/tools/gegraph_check/align_trace.py)（primary）：1–557 全文。
- [npu_utils CallPythonDeadlockCheck](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/npu_utils.cpp)（implementation）：290–378。
- [static 执行器首跑触发](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/static_npu_graph_executor.cpp)（implementation）：245–270。
- [dynamic 执行器首跑触发](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/dynamic_npu_graph_executor.cpp)（implementation）：225–245。
- [muti_gear 执行器首跑触发](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/muti_gear_npu_graph_executor.cpp)（implementation）：195–212。
- [run_deadlock_check 与工具导入](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）：20–33、480–498。
- [debug.deadlock_check 选项](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/debug_config.py)（implementation）：104–120。
- [独立包 deadlock_check 镜像](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/tools/aclgraph_check/deadlock_check.py)（implementation）：与集成版全文件 raw diff；差异仅集成版 258–268 对独立版 258–261、集成版 485 对独立版 478。
- [独立包 filter_operators 镜像](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/tools/aclgraph_check/filter_operators.py)（implementation）：与集成版全文件 raw diff；差异仅集成版 168–193/221–222 对独立版 168/217。
- [独立包 align_trace 镜像](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/tools/aclgraph_check/align_trace.py)（implementation）：与集成版 SHA256 相等、逐字节相同。
- [独立包 options.deadlock_check](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/configs/compiler_config.py)（implementation）：50–110。
- [GE 死锁检测文档](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/deadlock_check.md)（constraint）：1–52 全文。
- [npugraph_ex 死锁检测文档](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/dfx/deadlock_check.md)（constraint）：1–49 全文。
- 发布版负向核对（version-difference）：[npu_utils.cpp](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/npu_utils.cpp) 全文件无 CallPythonDeadlockCheck；[debug_config.py](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/debug_config.py) 无 deadlock 项；[utils.py](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py) 无 run_deadlock_check；`python/torchair/tools/` 目录不存在。
## 独立包 deadlock_check 的真实触发链（修正前文未闭合结论）

前文「版本与独立包差异」曾记录：独立包 `options.deadlock_check` 选项存在，但固定源码内未检索到镜像工具的任何调用方，文档产物路径的触发链未闭合。按 dfx 文档组逐页配对重查后修正：调用链存在，此前漏检的方法原因是检索用了 `tools/aclgraph_check` 斜杠形态，而实际导入是点形态 `npugraph_ex.tools.aclgraph_check.*`（utils.py 主线 17–18/发布 16–17）。两固定 pin 的独立包链路同构：

- 选项进入配置：主线独立包 `CompilerConfig.deadlock_check = OptionValue(False)`（npugraph_ex configs/compiler_config.py:58）经 `as_dict` 写入图编译选项（:102）；options 白名单按 `hasattr(config, option)` 校验、未知项 ValueError（:183 起）。发布独立包是 dataclass 平铺字段（npugraphex_config.py:31）经 `OPTIONS_TO_CONFIG_MAP` 映射到 `debug.aclgraph.deadlock_check`（:60），未知项按 ALLOWED_OPTIONS 拒收（:77/:104–123），再由 `_AclGraphDebugConfig.as_dict` 以平铺键 `deadlock_check` 输出（debug_config.py:93/:103）。
- 门控与落盘：AclGraph capture 路径内 `enable_torch_compile_debug = os.getenv("TORCH_COMPILE_DEBUG","0")=="1"`，`enable_deadlock_check = config.get('deadlock_check', …)`（acl_graph.py 主线 1606–1607，缺省 False；发布 :1230–1231，按 `'0'=='1'` 字符串比较）。任一为真即调用 `debug_dump()` 把图任务 JSON 写入 `DebugContext.current_path()`，文件名 `{self.name}_id_{id(graph)}_rank_{device}_pid_{pid}_ts_{ts}.json`（主线 1594–1605/发布 1218–1229）——该目录即 debug_save 子页所述 `torch_compile_debug/run_…/npugraph_ex/model__xx/` 树，`self.name` 是经 cache_info 传递的 AclConcreteGraph 名 `graph_{n}`（独立包自身计数器，npu_fx_compiler.py 主线 652/755、发布 547/630）。
- 判定调用：`run_deadlock_check(res)`（acl_graph.py 主线 1613/发布 1237）→ `filter_comm_ops` + `deadlock_check(aivec_total=torch.npu.get_device_limit(...)['vector_core_num'])`（utils.py 主线 533–538/发布 502–506）——与集成版同一两步流水与设备级阈值；独立包工具与前文已记录的镜像差异不重复。

这与独立包文档页 `npugraph_ex/dfx/deadlock_check.md`（1–49 全文复读）的产物表逐项对应：原始 `.json`、`_filtered.json`、`_filtered_deadlock_check.json` 三件产物即 debug_dump + 两步工具输出，`[RESULT] Deadlock risk detected!` 打屏由判定工具产生。该文档页仅主线 pin 的 dfx/ 目录存在（发布目录清单核对无此页），但发布代码链路存在——文档缺席不是能力缺席，反向亦然；集成页承诺的 `debug_output_graph_*` 落进程当前工作目录属 C++ 首跑链（前文），两条链路互不推导。dfx.md 入口页两 pin 均为仅一行标题的占位页，DFX 聚合实际只由三个子页实现；data_dump/debug_save 两个子页与实现的配对由[独立包设计合同](npugraph_ex_standalone_design_contracts.md)承载。

## 来源与复核范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（implementation）：窗口 1590–1625（debug_dump 1594–1605、门控 1606–1613）。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（implementation）：窗口 1215–1240（debug_dump 1218–1229、门控 1230–1237）。
- [新增来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py)（implementation）：导入 16–18、`run_deadlock_check` 533–538；`insert_save_npugraph_tensor` 490–527 的复读窗口由 dfx 数据 Dump 配对单元登记（见独立包设计合同卡）。
- [新增来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py)（implementation）：导入 16–17、`run_deadlock_check` 502–506、`insert_save_npugraph_tensor` 454–501。
- [新增来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py)（implementation）：`_next_unique_graph_id` 652、AclConcreteGraph 名 753–755；dump 相关窗口 694–726 由独立包设计合同卡登记。
- [新增来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/npu_fx_compiler.py)（implementation）：`_next_unique_graph_id` 547、AclConcreteGraph 名 629–630。
- [新增来源 7](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/npugraphex_config.py)（implementation）：20–123（deadlock_check 字段 31、映射 60、ALLOWED_OPTIONS 77、_process_kwargs_options 104–123）。
- [新增来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/debug_config.py)（implementation）：79–105（`_AclGraphDebugConfig` deadlock_check 93、as_dict 103）。
- [新增来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/dfx/dfx.md)（constraint）：1 行全文，与发布版字节一致。
- [新增来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/dfx/dfx.md)（constraint）：diff 零输出。
- 既有来源补读窗口：npugraph_ex configs/compiler_config.py（58、102、183–210 hasattr 白名单）；docs/zh/npugraph_ex/dfx/deadlock_check.md 主线 1–49 全文（options 表 26–29、产物目录与命名 31–42、打屏样例 44–49）。负向扫描（无截断 rg）：`run_deadlock_check` 在 npugraph_ex 树内除定义与导入外各恰 1 个调用点（acl_graph.py 1613/1237）；`python/torchair` 集成树内除定义（_ge_concrete_graph/utils.py 主线 494/发布对应）与 C++ 回调外无 Python 调用点，与前文集成链一致。发布 dfx/ 目录清单核对：无 deadlock_check.md。全部静态读取，未 import/运行上游。
## 发布独立包工具的JSON键名分化

发布`7c6c754bed00c86ffaaa2a45cb7ac2724f058013`独立包三工具此前只确认存在与链路同构，全文件`diff -w`对齐主线独立包镜像后补齐内容事实：

- `deadlock_check.py`发布版读`args.get("schemMode")`与`args.get("numBlocks")`（主线独立包/集成版读`"Schem Mode"`与`"Numblocks"`）；`filter_operators.py`发布版读`task.get("args",{}).get("schemMode")`（主线`"Schem Mode"`）。两pin均保留`"Task Ration"`、`"Task Type"`、`"Task Id"`、`"Active Stream Id"`原键名。
- 其余差异全部是注释字段拼写（`Schem Mode`→`schemMode`等说明文字）、pylint注释删除与换行排版，判定逻辑、向量时钟与AIVEC核账结构不变。

后果是跨pin混用工具与trace时静默失配：主线工具读发布trace（或反之）时`schemMode`键缺失、`!=1`恒真，候选集为空、报告无死锁而不报错；`numBlocks`缺省0也会改变核账。同pin内工具与debug_dump产物键名配套，无此问题。工具产物的实际生成方与设备侧键名来源仍是运行时口径，本卡不闭合。

## 来源与复核范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/tools/aclgraph_check/deadlock_check.py)（implementation）：1–639全文件与主线独立包`diff -w`；键名差异定位275–278、473–482。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/tools/aclgraph_check/filter_operators.py)（implementation）：1–304全文件与主线独立包`diff -w`；键名差异定位227。
- [新增来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/tools/aclgraph_check/align_trace.py)（implementation）：1–574全文件与主线独立包`diff -w`；仅排版与注释差异。
