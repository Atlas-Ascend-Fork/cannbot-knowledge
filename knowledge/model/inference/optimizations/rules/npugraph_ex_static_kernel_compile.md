---
type: Optimization
title: npugraph_ex 静态 Kernel 编译：缓存条件与节点内协调
description: 静态或少量 shape 场景的 static_kernel_compile 配置，说明 LOCAL_WORLD_SIZE、辅助 Gloo
  组、Profiler 冲突与缓存匹配条件。
tags:
- task.optimization
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/static_kernel_compile.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/static_kernel.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/basic/static_kernel_compile.md
  role: constraint
created_at: '2026-11-08T11:58:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 静态 Kernel 编译的启用条件

## 适用与收益来源

模型 shape 固定或种类较少、运行时算子处理开销明显时，可评估 `options={"static_kernel_compile": True}`。它按实际算子 shape 预先产生二进制，代价是额外编译、产物管理和多进程协调；收益必须单独测量。

## 多卡配置

主线默认关闭该功能。自动创建节点内辅助组时，各节点须一致设置实际 `LOCAL_WORLD_SIZE`，避免其他进程读取安装算子库的中间状态。业务只由子通信域运行时，当前主线还允许指定已创建的节点内 Gloo `group_name` 作为 static_kernel_compile_group，成员需与本轮编译参与者一致，调用方维护其生命周期。

指定辅助组的方式不依赖 LOCAL_WORLD_SIZE；与模型持久缓存组合时，加载前要恢复同名同成员组。该选项来自固定主线，不推导发布基线已有同样能力。

## 缓存与冲突

静态 Kernel 缓存复用要求 CANN 和硬件、全部相关算子属性、确定性与 SuperKernel 编译选项一致，且 run 包仍存在；不匹配时重新编译。disable_static_kernel_compile_cache 默认 False，仅开启静态编译时生效。

Profiler 同时配置 record_op_args=True 和 skip_first=0 时，来源明确不支持本功能。分别检查首次编译、命中后启动、稳态时延和输出；不能把静态 Kernel 缓存与 Dynamo/GE 模型缓存视为同一层缓存。回退时关闭静态编译选项，保留可用模型后端；本次未运行编译。

## 版本入口

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)：来源快照、部署配套和实际运行验证分别核对。

## 辅助组顺序、产物与异常退出

所有 rank 应以一致顺序创建 HCCL 业务组及对应 Gloo 辅助组；业务 AllReduce 使用 HCCL，静态编译收集、广播和同步使用节点内 Gloo。多个参与者重叠的子域按来源示例分阶段执行，并在阶段间使用独立协调组同步；不要将一段业务组名直接当作编译辅助组名。辅助组在相关编译完成前须有效，成员严格对应本节点本轮编译参与者。

默认产物位于执行脚本同级目录；同时启用模型缓存且未启用 force_eager 时，位于模型缓存目录。需要相应读写权限，工作目录还需执行权限。static_kernel_cache 保存按 CANN 版本和硬件型号区分的 JSON 映射与并发锁；删除或移动 .run 包也会导致无法命中。disable_static_kernel_compile_cache=True 强制每次重新编译，不是清除 Dynamo 模型缓存。

产物中的全量统计、支持静态编译与实际选中算子是不同集合；启用模型缓存或指定辅助组时不生成 `_opcompile_selected`，实际采用 `_opcompile`，不能据目录缺失判定失败。多卡单次编译只生成一份静态 Kernel run 包。正常流程自动清理临时产物；异常退出后仅处理本次日志指示的 uninstall.sh 或对应 timestamp_pid 临时目录，不能笼统删除其他任务产物。本文没有执行安装、卸载或设备编译。

## 独立包实现补充的缓存和并行度

固定主线独立npugraph_ex静态编译路径已读局部确认：显式Gloo组须为已初始化、包含当前rank的非空group_name，调用方持有生命周期；自动路径按global_rank/LOCAL_WORLD_SIZE成块建组，要求成员一致进入探测和正式组创建。探测失败跳过静态编译不等于整模型验证通过。

算子JSON按原始字节哈希，排序后加入SuperKernel配置、全局deterministic和NPU level；CANN/设备另体现在缓存文件名。共享查询锁、排他更新锁和tmp替换只保障这一路文件访问，不证明产物语义/ABI。模型缓存加载的CANN/确定性/属主检查与普通JSON路径查询不是同一检查，不能互相借用结论。

_compute_opc_compile_jobs正常使用CPU数、未知为1、异常fallback16，文档“默认16”不能当固定值。force_eager+static_kernel路径不从模型缓存提取同一组static_kernel元信息，且按符号值去重；shape集合的记录先于编译调用，不作为成功信号。具体独立包/产物路径和设计差异见[草稿](../../guides/optimization/torchair/npugraph_ex_standalone_design_contracts.md)；此实现证据不扩张已有产品支持范围。

## 发布静态编译与主线子组增量

发布页要求多卡设置一致的LOCAL_WORLD_SIZE，没有主线的显式Gloo辅助组参数与缓存控制表；主线才把此要求限定为自动建组，另列static_kernel_compile_group和disable_static_kernel_compile_cache。不能把主线的子组豁免反向套入发布组合。两版仍有record_op_args=True且skip_first=0的Profiler冲突，默认关闭静态编译，产物中的全量/支持/选中集合分别核对。

## Evidence

- [docs/zh/npugraph_ex/basic/static_kernel_compile.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/static_kernel_compile.md)（primary）
- [docs/zh/overview.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles_en.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/static_kernel.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（implementation）

- [完整页复核来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/basic/static_kernel_compile.md)（constraint）
