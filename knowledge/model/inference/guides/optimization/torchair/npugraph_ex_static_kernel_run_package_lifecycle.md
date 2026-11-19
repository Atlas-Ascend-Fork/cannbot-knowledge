---
type: Guide
title: 静态Kernel包生命周期：加载状态、隔离安装与清理
description: 区分run包需要编译或跳过的条件、安装状态与真实成功，并核对进程所有目录和广播选择路径。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/static_kernel.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/inference/_cache_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/__init__.py
  role: implementation
created_at: '2026-11-10T13:42:34Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 静态Kernel包生命周期：加载状态、隔离安装与清理

## 固定实现和缓存入口

本卡只审TorchAir主线`92e1e967bd35ebc37a442b4a969730bf3cf77a3c`中`npugraph_ex/npugraph_ex/`独立包的静态run包消费者，不推导同仓集成TorchAir或发布软件具有相同隔离/重试行为。产品范围未知，保持draft、空平台；没有加载缓存、反序列化、编译、安装/卸载run包、创建进程组或运行设备。

ModelCacheSaver在启用static_kernel_compile时把use_cache_compile、CANN版本、缓存目录、全局deterministic与NPU等级加入extend_config，FX生成初始化代码将它们写入AclGraph配置并生成更新缓存目录的函数。compile_static_kernel据use_cache_compile分派模型缓存run包加载；force_eager加静态编译时不读取这组模型缓存元数据，走普通编译路线。

普通路线仍先收集JSON再查持久run缓存；模型缓存目录已找到run包时则可直接安装和reselect，不必再走同一dump。缓存字段和锁见[既有设计边界](npugraph_ex_standalone_design_contracts.md)，收集与进程内集合见[算子筛选](npugraph_ex_static_kernel_dump_and_selection.md)，不要把Dynamo模型缓存、JSON映射和已安装kernel当成一层状态。

## NEED_COMPILE与NEED_SKIP的区别

_check_for_load_run_pkg检查元数据/目录存在、当前用户属主、CANN版本和确定性开关；缓存等级非None时才比较NPU等级。检查不通过时，单卡直接return，多卡广播NEED_SKIP；这一消费者没有把所有不匹配都自动转成重新编译。文档建议删缓存重编与自动执行重编是两件事。

通过检查后，_find_and_install_run_pkgs按枚举搜索static_kernel_compile_outputs下的ts*_outputs子目录：

| 搜索状态 | 返回及调用方行为 |
| --- | --- |
| 没有静态输出目录，或没有ts*_outputs子目录 | NEED_COMPILE，进入模型缓存目录内重新编译分支 |
| 子目录中找到run包 | 调安装函数后返回INSTALLED；调用方reselect |
| 有候选输出子目录却遍历不到run包 | 告警并NEED_SKIP，当前调用不自动重编 |

这里没有按时间戳显式排序或证明所选首个含run包的输出目录覆盖任意新shape。普通JSON缓存命中时_match_and_install_run_pkg也先调用安装，再直接返回INSTALLED；查询到路径存在与安装内容验收是不同检查。

## INSTALLED不是全部底层成功的证明

_install_run_packages按run文件内容哈希去重，成功执行安装后才登记_installed_run_pkgs。但安装子进程CalledProcessError在函数内仅warning，外层仍可能继续返回INSTALLED；FileNotFoundError等其它异常不在这一except内统一转换。reselect也捕获异常并warning，不向调用方返回统一成功布尔值。

静态新编译路线先将run包路径写入持久JSON映射，再调用安装，因此“cache updated”早于安装验收。多卡编译root完成该辅助函数后按路径广播/barrier/reselect，没有在该分支把编译/安装/实际kernel采用结果汇总成统一成功票据。barrier完成只证明参与者走到该同步点，不能认证每个kernel已正确安装或被模型采用。

## 安装目的地、选择路径和所有权

模块初始化时，只有存在_aclnn_reselect_static_kernel_with_path且CANN版本检查满足9.1.0才启用_use_process_isolation。该标志在模块级求值，不是每次安装重新协商产品能力。隔离模式为本进程建立`cwd/static_kernel_install/<timestamp>_<pid>`，按PID保存_owned_install_path；_current_install_path另用于kernel选择，可以接收辅助组root广播的路径。

接收的选择路径不成为本进程的安装所有物。后续真正安装时_get_or_create_install_path恢复或新建本PID自己的目录；新建时清空安装哈希集合，再把_current_install_path指向_owned目录。已经安装全部run包而跳过循环时，也会先恢复自己的安装目的地。不能把广播路径、安装目录与JSON缓存的run文件目录混成同一个位置。

非隔离模式直接执行run包，并记录匹配到的uninstall.sh；CANN检查满足9.1.0时安装命令另加-q，是否隔离仍取前述双条件。此处执行命令不证明包语义、ABI、模型数值或性能已通过验证。

## 退出清理边界

独立包的atexit注册_finalize，先torch._dynamo.reset再调uninstall_static_kernel；主线程还注册SIGTERM/SIGINT处理。注册存在不保证强制结束或前一步异常后清理必然执行。

隔离清理只在_owned_install_pid等于本PID且owned路径非None时尝试删除该目录，再只以rmdir尝试删除空父目录；不会因为_current_install_path指向组root就把该接收路径当作自己的目录删除。同一分支重置owned标记、已安装哈希及进程内_compiled_op_set，并最终清空选择路径；删除失败也可能继续清理这些内存标记，不将标记为空当作磁盘清理成功。

非隔离分支执行记录的卸载脚本，CalledProcessError写日志后继续，最后清空_uninstall_paths；所读分支没有同样清空_compiled_op_set。实际异常残留按[静态编译文档](../../../optimizations/rules/npugraph_ex_static_kernel_compile.md)和本次日志处理，不扩成笼统删除共享缓存/其他进程目录的建议。以上均为静态合同，本次未进行任何清理实验。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/static_kernel.py)（primary）：定向范围23–38, 102–156, 193–278, 312–354, 402–434, 437–468, 629–696, 757–835, 941–992, 1198–1268。
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/inference/_cache_compiler.py)（implementation）：定向范围443–471。
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py)（implementation）：定向范围731–761。
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/__init__.py)（implementation）：定向范围30–49。
