---
type: Guide
title: 静态Kernel收集与筛选：临时捕获、去重和失败信号
description: 核对独立包dump流限核恢复、算子JSON选择与编译前已见集合，区分目录、选中项和成功工件。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/static_kernel.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: implementation
created_at: '2026-11-10T13:42:34Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 静态Kernel收集与筛选：临时捕获、去重和失败信号

## 独立包入口与已有配置的分工

本卡只绑定TorchAir主线`92e1e967bd35ebc37a442b4a969730bf3cf77a3c`中的`npugraph_ex/npugraph_ex/`独立包，说明收集到待编译算子集合的实际消费者。不要套到同仓`python/torchair/`同名文件或发布实现。产品、Profiler冲突及辅助Gloo组前提复用[静态编译配置](../../../optimizations/rules/npugraph_ex_static_kernel_compile.md)，不新增支持矩阵；平台未知，保持draft、空平台。

AclGraph普通首调在预热后、正式图捕获准备期间按static_kernel_compile调用compile_static_kernel；force_eager路线也通过run_eagerly_compile调用。首调与符号shape登记已由[捕获首调](npugraph_ex_restored_capture_keys_and_first_call.md)及[捕获控制](npugraph_ex_capture_controls.md)解释，本卡不把这些登记重复当作编译完成信号。

## dump是一次临时图捕获

_fx_func_run取得当前流和其限核值，新建同设备dump_stream并保存该流原限核；仅两者不同时给dump_stream应用源流限核。随后开启_aclop_start_dump，在新NPUGraph的`capture_error_mode="relaxed"`捕获区调用fx_func，供静态编译收集算子信息；该函数没有replay临时图或返回模型结果。

源码将此设计说明为Host侧信息收集，目标是覆盖真正capture中的算子，包括图机制生成的算子。本次只静态审Python调用，不把注释扩成全部自定义Host副作用隔离、所有native动作或设备执行均已验证的保证。额外的FX调用、流/图初始化及dump仍属于启动准备成本，不能称为零成本缓存查询。

finally按顺序停止dump、reset临时图，限核不同时再恢复dump_stream的原值。流来自池，不能认为删除Python流对象会清空限核。清理步骤没有各自独立try；若前一步抛异常，不能保证其后的reset或恢复一定执行。

单卡和多卡调用者捕获dump异常并warning后仍继续选择JSON目录，不是统一立即终止整套静态编译。因此dump失败、存在目录、发现JSON和完整收集成功是不同事实；也可能仅剩部分或debug信息，不能只凭后续日志认证覆盖了整模型。

## 选中目录和进程内集合不同于成功工件

| 情况 | 选择逻辑 |
| --- | --- |
| 有_opcompile目录，非模型缓存且无显式辅助组 | 取枚举到的第一个目录，get_compile_dir生成本PID的_opcompile_selected，按进程内集合筛选 |
| 模型缓存或显式辅助组 | 使用完整的第一个_opcompile目录；显式组不把一个进程的已见集合当作另一组root已有产物的证明 |
| 没有_opcompile目录 | 回退第一个_debug目录；没有候选或最终没有JSON则跳过op_compiler |

get_compile_dir把算子JSON原始字节哈希与规范化SuperKernel配置字符串拼成compile_key。复制JSON成功后就加入全局_compiled_op_set，发生在op_compiler、run包安装及reselect之前；编译失败没有在这条分支回滚集合。后续普通选择可把同key视为已处理，不能把集合或“already compiled”日志当作成功清单或自动重试保证。

这份进程内key与持久run缓存不是同一key；本函数没有把全局确定性开关/等级作为独立字段加入compile_key，不据此认证任意配置变更会自动完整失效。持久缓存身份的CANN/设备、确定性与锁仍按[既有实现边界](npugraph_ex_standalone_design_contracts.md)分别核对。

## 黑名单、跨卡合并与真正编译

黑名单按JSON文件名包含非空字符串匹配，不按IR语义或正则匹配。普通筛选和跨卡合并把匹配项复制到_blacklist；完整_opcompile分支尝试移动。移动失败只warning，不能把黑名单当作所有异常下的强制隔离保证；_debug回退也未在选择函数重新应用同一过滤。

多卡root按JSON原始字节哈希去重并复制到_gathered，相同文件名而不同内容会加计数后缀避免覆盖。这证明的是字节级合并，不是任意语义等价算子去重。没有JSON则跳过，不能从目录数量推算实际选中算子数。

static_compile构造op_compiler命令，指定目录、设备名、并行job数及可选SuperKernel参数；CANN版本检查满足9.0.0时另加-f true。只对CalledProcessError告警并返回False，其它异常不在此统一吞掉；True表示该子进程调用通过，不等于run包安装、kernel选中或模型数值验证通过。安装与加载状态见[run包生命周期](npugraph_ex_static_kernel_run_package_lifecycle.md)。本次没有执行dump、编译、安装或设备实验。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/static_kernel.py)（primary）：定向范围23–27, 312–354, 382–411, 437–626, 700–732, 1050–1117, 1150–1170, 1290–1347。
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（implementation）：定向范围1178–1205, 2036–2052。
