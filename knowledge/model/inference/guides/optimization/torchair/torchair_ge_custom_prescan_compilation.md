---
type: Guide
title: GE自定义预编译：候选筛选、依赖缓存与动态库
description: 解释主线自定义算子预扫描到Schema注册、回调文件、Converter和g++加载的次序，区分跳过、失败与实际运行验收。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/custom_op_compiler.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/custom_op_pre_scan.py
  role: implementation
created_at: '2026-11-10T10:43:14Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE自定义预编译：候选筛选、依赖缓存与动态库

## 固定版本与证据层次

全文核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c的custom_op_pre_scan.py、custom_op_compiler.py。发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013没有这两个相同路径，路径缺失不作为其他入口能力否定。本卡限定预扫描与编译加载编排，未全文覆盖三个codegen实现和回调执行层，产品矩阵未知，保持draft与空平台。

本次未导入上游、调用依赖探测、生成或编译代码、加载动态库、执行缓存或设备实验。文档级[零交付件回调边界](ge_custom_op_callback_boundaries.md)与本卡的内部编排合同分别使用。

## 依赖检查缓存的是本进程探测结果

_check_python_path_deps依次尝试导入ExternalStream、ge.custom_op的get_execute_ctx/register_op_impl及ge.runtime.TensorPlacement，仅捕获ImportError，缺项警告并缓存False，成功缓存True；后续调用直接复用结果。没有在这里执行stream切换、回调或读取GE Tensor，也没有逐项校验完整ABI和运行能力。

缓存False不意味着后续环境变化会在同一函数自动重新探测；本模块没有公开刷新步骤。C++路线不经过相同Python依赖门槛，不能把一条路线的跳过扩大到所有自定义算子。

## 候选筛选有优先级

prescan_and_compile_custom_ops只看call_function节点：Triton mutation HOP直接RuntimeError，functional HOP先检查Python依赖再收集spec。auto_functionalized_v2仅在args[0]为OpOverload时解出真实目标；不符合即跳过。

普通候选须is_custom_op，排除_SPECIAL_TARGETS，去重，并先尊重目标上的_ge_converter及_get_converter结果。有既有GE IR也跳过自动回调；不是见到自定义namespace就重新生成代码。

_is_ge_ir_registered把算子名称去掉尾部functional后按下划线转大驼峰，查询get_registered_ir_def。SUCCESS表示已有IR，ERROR表示未查到，可继续；若返回其他状态或捕获RuntimeError/AttributeError/KeyError/IndexError，则返回原因并在预扫描中警告跳过。不能把“查询失败”和“确认没有IR”合并成同一种自动生成条件，也不能凭名称映射证明所有原型都一致。

determine_callback_path决定Python/C++或跳过；该分类函数的完整实现另行审阅。本文件只对Python候选再次检查Python依赖，随后两类各按target.name排序，Python在前，记录C++索引，抽取Schema与合成GE名字。

## Schema注册、Python回调与Converter按顺序建立

Triton spec先validate，新增spec加入待注册Schema；已有发布路由复用时不生成空工件。有schemas才generate_cpp_source并compile_and_load，即使只有Python回调也可能需要C++ REG_OP注册，不能把Python路线说成从不调用g++。

成功返回的CDLL存入_compiled_libs防止引用被回收；再为Python目标生成回调文件，为新增Triton spec生成对应文件，之后注册普通callback Converter，再发布Triton spec并确保HOP Converter注册。生成目录与运行期扫描机制的注释不替代codegen/GE实际加载实现验证。

Triton发布函数在此被调用不等于整个预扫描是一个原子事务；前面的编译加载或文件生成可能已发生，没有统一撤销所有步骤的代码。日志的Batch compiled计数也不是设备数值/性能通过记录。

## 进程级临时目录与实际编译命令

_ensure_cpp_dir首次用带PID前缀的mkdtemp建唯一目录，之后同进程多图复用；源码没有退出清理，注释依赖临时目录清理。这里没有加锁，注释假定主线程串行预扫描，不能据此宣称任意并发调用均安全。

compile_and_load发现Torch路径、按需发现TorchNPU路径，从ASCEND_HOME_PATH取CANN路径；缺CANN路径直接报错，找不到TorchNPU只返回None并不在此立即拒绝。随后写name.cpp/name.so，构造g++参数数组并subprocess.run，timeout=120、check=False，非零返回码包装stderr或stdout为RuntimeError；超时异常没有同样的局部包装。

命令固定-shared、-fPIC、-O2，C++标准委托get_torch_cxx_standard；始终含Torch/CANN include及库路径和CANN库，has_cpp_ops时额外加Torch库，发现TorchNPU时再加其头文件/库/rpath。False只去掉某些C++执行依赖，不表示整个命令完全不依赖Torch信息。

成功后ctypes.CDLL以RTLD_GLOBAL|RTLD_NOW加载，并把对象交调用方保存。库文件存在、编译成功、动态链接成功、REG_OP注册、Converter存在和回调实际正确执行，是不同验收阶段；固定graph_id后缀也不是跨进程通用的可迁移工件身份。

## 验证与相邻主题

按顺序核对候选是否被跳过、依赖缓存状态、已有Converter/IR查询结果、路由、Schema、生成源文件和命令、动态链接、Python文件加载及最终Converter。需要运行正确性和性能结论时，仍须在匹配软件栈验证真实自定义算子和回调；本次只读源码，没有执行以上步骤。

- [FX编译入口与预扫描调用位置](torchair_fx_compiler_pipeline.md)
- [自动函数化与内部mock](torchair_ge_auto_functionalized_views.md)
- [IR装配与兼容检查](torchair_ge_ir_assembly_compatibility.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/custom_op_compiler.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/custom_op_pre_scan.py)（implementation）
