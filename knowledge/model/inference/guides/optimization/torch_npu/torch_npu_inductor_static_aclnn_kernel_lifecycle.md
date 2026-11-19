---
type: Guide
title: torch_npu Inductor 静态 aclnn kernel：私有开关、dump→op_compiler→安装→reselect→卸载
description: 记录 _use_static_aclnn_kernel 私有开关的四个消费点、StaticKernelCompiler 生命周期与异常边界、安全路径检查、C++ dump/reselect 绑定语义，及主线 mlir logger 与 with_path 绑定的版本差异。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/npu_static_kernel.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/aclnn/__init__.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/core/runtime_lifecycle.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/wrapper.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_graph_tree.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_graph_tree.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/interface/AclInterface.cpp
  role: header
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_use_static_kernel.py
  role: example
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_npu_static_kernel.py
  role: example
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/npu_static_kernel.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/aclnn/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/wrapper.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_graph_tree.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/npu/Module.cpp
  role: implementation
created_at: '2026-11-12T05:41:05Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu Inductor 静态 aclnn kernel：私有开关、dump→op_compiler→安装→reselect→卸载

## 固定版本与适用范围

两版都有`torch_npu/_inductor/npu_static_kernel.py`（主线 155 行/发布 151 行，全文读+完整 raw diff）与`npu/aclnn/__init__.py`（两版逐字节一致，sha256 相同），`Module.cpp`都暴露`_aclop_start_dump/_aclop_stop_dump/_aclnn_reselect_static_kernel`。差异：主线另有`_aclnn_reselect_static_kernel_with_path`绑定与对应测试；退出卸载主线在`_init/core/runtime_lifecycle.py`、发布内联在`torch_npu/__init__.py`的`_npu_shutdown`。这是 torch_npu 仓内 Inductor 路线的静态化通道，与 TorchAir 独立包 npugraph_ex 的静态 kernel 流（[收集与筛选](../torchair/npugraph_ex_static_kernel_dump_and_selection.md)、[编译配置](../../../optimizations/rules/npugraph_ex_static_kernel_compile.md)、run 包生命周期卡）是**不同实现**，两卡的门槛与失败边界互不可套用。本次纯静态阅读：未执行 dump、未调用 op_compiler、未安装 run 包、未改任何环境。draft、platforms 为空。

## 私有开关与其消费点

`torch_npu/npu/aclnn/__init__.py`模块级定义`_use_static_aclnn_kernel = False`。仓内没有任何生产路径的启用赋值点；Python 侧的显式赋值只在测试里（`test/_inductor/test_use_static_kernel.py`设`torch_npu.npu.aclnn._use_static_aclnn_kernel = True`并同设`triton.cudagraph_trees = False`）。没有 env、config 或公开 API 文档化该开关——它是实验态内部标志，不承诺任何版本兼容。该文件其余内容（`allow_hf32` ContextProp、AclnnModule PropModule 包装）属 HF32 面，见既有卡。四个消费点：

| 消费点 | 行为 |
| --- | --- |
| Inductor wrapper 代码生成（两版） | 见下节“生成代码注入” |
| 图树捕获 warmup（两版，`npu/_graph_tree.py`） | `_record` 的 warmup 段在标志为真时把`wrapped_function.model(new_inputs)`整个包进`StaticKernelCompiler`上下文 |
| 旧式 npugraphify warmup（两版，`utils/_graph_tree.py`） | 同上包裹旁流 warmup（见[npugraphs backend 卡](torch_npu_npugraphs_backend_wiring_and_legacy_capture.md)） |
| 进程退出卸载（两版） | `_npu_shutdown`在标志为真时调`uninstall_static_kernel()` |

## StaticKernelCompiler 生命周期

| 阶段 | 实际动作与失败边界 |
| --- | --- |
| 构造 | `safe_resolve_output_dir(build_dir)`（见下节）；结果目录名`<YYYYmmddHHMMSSffffff>_<pid>_kernel_aot_optimization_build_outputs`，无 build_dir 时锚定当前工作目录 |
| `__enter__` | `torch_npu._C._aclop_start_dump(str(result_root))` |
| `__exit__`（异常路径） | 先无条件`_aclop_stop_dump()`；检测到异常只 log ERROR/INFO 并 return（返回 None→异常**继续向上传播**，单测以 MockException 断言传播；仅跳过编译阶段） |
| `__exit__`（正常路径） | 选`result_root`下`*_debug`目录中 mtime 最新者；无目录或目录无`*.json`则 log error 后 return（跳过编译，不抛错）。随后子进程执行`op_compiler -p <debug_dir> -v <device_name> -l info -j 4 -o <result_root>`；`CalledProcessError`只 log error 并 return（吞掉，不上抛）；其他异常类型不在该层捕获 |
| 安装 | 对每个`*.run`执行该脚本；成功后`save_uninstall_info(<去 .run 名>)`并调`torch_npu.npu._aclnn_reselect_static_kernel()`；仅`subprocess.CalledProcessError`是 log error 后继续处理其余包——`FileNotFoundError`/`PermissionError`等其他异常、`save_uninstall_info`里缺`ASCEND_HOME_PATH`的 KeyError、reselect 抛错都不在该层捕获，会中断安装循环向上传播，不能把“单个安装失败继续”扩成任何安装失败都继续 |

`op_compiler`是从 PATH 找的外部工具，仓内不自带；其存在性与各参数语义未在本次静态阅读中验证，不能当作必然可用。dump/编译/安装均未运行。

## 安全路径检查（safe_resolve_output_dir）

build_dir 非空时：含空字节`\x00`→ValueError；路径任一部分为`..`→ValueError；从锚点起逐段检查**已存在**且为符号链接的中间目录→ValueError（含新式“已存在才查”，最终`resolve(strict=False)`失败→ValueError）。相对路径锚定`Path.cwd().resolve()`。结果目录 mkdir 失败→RuntimeError（主线捕`OSError`超集，发布捕`(PermissionError, OSError)`——语义等价因 PermissionError 是 OSError 子类）。单测覆盖 dot-dot、null byte、symlink、只读目录、绝对路径各分支。

## 生成代码注入（Inductor wrapper）

wrapper 头部（`write_triton_header_once`）注入`has_initialized = False`（`autotune_at_compile_time`开时同注到 kernel_autotune_calls）。`write_prefix`在标志为真时生成模块级：`global has_initialized`→`if not has_initialized:`→导入并构造`StaticKernelCompiler`、`__enter__()`、置`has_initialized = True`——首个 wrapper 建编译器，同模块后续 wrapper 跳过。`generate_return`在返回前生成`if not has_initialized:`→`exc_info=(None, None, None)`→`<变量>.__exit__(*exc_info)`。两点如实记录：主线生成的变量名拼写为`static_kernel_complier`（prefix 与 return 两处一致的可运行拼写，非笔误一处一处不一致那种情况；发布拼`static_kernel_compiler`）；return 处的守卫条件按字面是“未初始化才退出”，静态阅读无法断言该分支在运行期何时为真——冒烟测试只断言编译输出与 eager 数值相等，不断言退出/安装实际发生。不据字面守卫反推设计意图。

## C++ 绑定语义

- `_aclop_start_dump(path)`/`_aclop_stop_dump()`（两版）：固定`dump_type=0x1`，转调`AclopStartDumpArgs/StopDumpArgs`（`AclInterface.cpp`从`libascend_dump`动态加载`aclopStartDumpArgs/aclopStopDumpArgs`符号；符号缺失返回`ACL_ERROR_FEATURE_UNSUPPORTED`，取到后才调）。
- `_aclnn_reselect_static_kernel()`（两版）：先`emptyAllNPUStream()`（失败 TORCH_CHECK 抛）；`task_queue_enable == 2`时经`OpCommand::RunOpApiV2("reselect_static_kernel", ...)`执行并再次清空队列，否则直接调用。主线每次调用现读 task queue 开关，发布用`static const`缓存首次值——进程内该开关变化后两版行为不同。
- `_aclnn_reselect_static_kernel_with_path(path)`（仅主线）：参数须字符串、不含空字节、`realpath`可解析且必须为目录，否则 TORCH_CHECK 抛（测试断言四种错误文本）；后续同样清队列+按 task queue 分支。
- `AclopDumpContext`（`npu_static_kernel.py`内 8 行 helper）：调用`torch_npu._C._aclop_start_dmp`——该符号不在`Module.cpp`绑定表（两版逐字核对），且仓内无任何消费者。按固定源码事实记录：这个 helper 若被使用会 AttributeError，不是已验证可用的功能。

## 卸载与版本差异汇总

`save_uninstall_info`按`{ASCEND_HOME_PATH}/../*/opp/static_kernel/ai_core/<name>/uninstall.sh`glob 取**第一个**匹配写入**单一全局**槽位——每次保存都覆盖旧值，找不到匹配也覆盖为 None（退出时静默跳过）；因此多次安装后退出卸载只卸最后记录的一个槽位，不是全部已装包。`uninstall_static_kernel`执行该脚本（仅 CalledProcessError 只 log），finally 无条件把变量复位 None——再次卸载需重新安装时重新记录。退出接线：主线`runtime_lifecycle._npu_shutdown`（由`_initialize_runtime_lifecycle`注册 atexit）与发布`torch_npu/__init__.py._npu_shutdown`+`atexit.register`都在卸载前检查标志。`npu_static_kernel.py`其余差异：主线按`TORCHINDUCTOR_NPU_BACKEND==mlir`选择 ascend_npu_ir logger（否则 config logger），发布固定 config logger；`raise ... from e`链与`%s`惰性格式化属风格差异。

## 边界

- 开关私有、测试门控（`runIfVersion(max="2.13")`）：不宣称任何产品路径默认启用，也不宣称它与 npugraph_ex 独立包的静态 kernel 产物互兼容（同一 CANN 目录但选择/去重/黑名单逻辑完全不同）。
- `op_compiler`、`.run` 安装器、`ASCEND_HOME_PATH` 布局均为外部契约，本次只覆盖调用侧；reselect 后的实际 kernel 选择行为在 C++/运行时侧，不在本卡范围。
- 除单测断言（路径拒绝、异常传播、with_path 参数校验、no-path 卸载静默）外，无任何运行验证；冒烟测试不断言静态 kernel 真正生效。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/npu_static_kernel.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/aclnn/__init__.py)（primary）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_npu_static_kernel.py)（example）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/npu_static_kernel.py)（implementation）
