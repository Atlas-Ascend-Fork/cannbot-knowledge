---
type: Guide
title: Scalable RootInfo：按 ProcessGroup 分级建链与回退边界
description: 说明 root 数和均衡分组、A2/A3 及 HCCL 接口要求，区分 RankTable 和 TCPStore 分层。
tags:
- task.optimization
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/distributed/communication_strategy/scalable_rootinfo_link_setup.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/ROOTINFO_SCALABLE_ENABLE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_RANKS_PER_ROOT.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/distributed/startup_and_fault_tolerance/torch_npu_run.md
  role: supporting
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/ROOTINFO_SCALABLE_ENABLE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_RANKS_PER_ROOT.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/distributed/communication_strategy/scalable_rootinfo_link_setup.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/HcclCompile.h
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp
  role: supporting
created_at: '2026-11-09T02:56:52Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
---

# Scalable RootInfo：按 ProcessGroup 分级建链与回退边界

## 版本与范围

固定 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`，来源明确仅 A2/A3 训练。不能据此推定所有发布包包含 HcclGetRootInfoScalable/HcclCommInitRootInfoScalable。

## 分组和生效点

ROOTINFO_SCALABLE_ENABLE 默认 0，开启为 1；TORCH_HCCL_RANKS_PER_ROOT 默认 128，合法十进制范围 1..4294967295。按当前 ProcessGroup 的 N 而非全局 world_size 计算：N≤R 仍单 root；N>R 时 K=ceil(N/R)，连续且均衡划 K 组，组大小最多差 1，首个 local rank 为 root。

这不是简单每 R 个硬切一段；例如 N=8、R=3 采用 3/3/2。支持默认域和 new_group 的 DEFAULT 类型域，P2P 仍走旧 RootInfo。通信域懒建链，实际选择可能发生在首次需要它的集合通信。

## 回退与层次

不支持设备上开启会告警回退；支持设备已选中该路径但运行库缺少两个 HCCL 接口则返回不支持错误，不能假定仍自动回退。有效 RankTable 路径优先，不进入该 RootInfo 分级。

torch_npu_run 的 enable_tiered_parallel_tcpstore=True 是启动器 TCPStore 的节点内/节点间分层，默认关闭，属于另一层；不能拿该参数代替 HCCL RootInfo 开关，或把主线启动器的收益当作 HCCL 算子带宽收益。

环境变量需在 worker 启动前设置，进程内首次读取缓存，不支持动态切换；只改变建域方式，不改变后续集合通信调用、缓存和销毁协议。

## 验证

对默认域、子域、N≤R、N>R 和 RankTable/P2P 路径分别核对建域日志及实际 root 分布；比较初始化耗时和稳态数值。本卡未启动集群或通信实验。

## 非法rank配额的处理

中英文配额页对空字符串、0、负数、非数字、带多余字符或超过4294967295的值规定返回参数错误，不将它们当作使用默认128或关闭分级的写法。两页均只列A2/A3，不能从普通RootInfo或其他HCCL环境页列950扩展本功能；有效RankTable和P2P仍保持原路径选择。

## 双语分组例子与启动器边界

英文页独立确认：N=8、R=2时roots为组内local rank 0/2/4/6；R=3时是3/3/2分组、roots 0/3/6。local rank在此指当前ProcessGroup内部的连续编号，不直接等于启动器LOCAL_RANK。不支持产品上的Warning回退与支持产品缺运行库符号时报错，是两个不同分支。

启动器的[分层TCPStore](torch_npu_run_tiered_tcpstore.md)管理worker发现/连接，RootInfo管理HCCL通信域初始化；两项开关彼此不替代，也不由其中一项产品范围推定另一项完整配套。两语言都限定本功能只改变初始化，不改变后续通信、缓存或销毁协议。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/distributed/communication_strategy/scalable_rootinfo_link_setup.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/ROOTINFO_SCALABLE_ENABLE.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_RANKS_PER_ROOT.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/distributed/startup_and_fault_tolerance/torch_npu_run.md)（supporting）

- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/ROOTINFO_SCALABLE_ENABLE.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_RANKS_PER_ROOT.md)（constraint）

- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/distributed/communication_strategy/scalable_rootinfo_link_setup.md)（constraint）

## 文档口径与源码实现的差异

前文小节转述官方文档页承诺；本节按 TorchNPU 源码固定提交 main `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 与 release `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 的静态阅读给出 native 事实，两者不一致处以本节为准。

### 文档名与源码名控制不同路由

`ROOTINFO_SCALABLE_ENABLE` 在主线与发布两版本 的 `torch_npu/` 源码内零出现，main 全仓命中仅剩 docs 页面（中英变量页、菜单、env_variable_list 与开发者笔记）。源码内不存在按该名字分流的逻辑；但这不能推出「该变量被 CANN/HCCL 忽略」——HCCL 库是否另行读取该名字，在 torch_npu 仓源码内不可见，本卡不做断言。

native 建域入口 `createHCCLCommOrigin` 中，真正进入 Scalable 分支的门是（torch_npu/csrc/distributed/ProcessGroupHCCL.cpp:2965-2981）：

- 通信域类型为 DEFAULT（P2P 直接取 -1，不参与分级）；
- `TORCH_HCCL_RANKS_PER_ROOT` 解析值 R 为正；
- `IsA2A3Soc()` 为真，否则仅 Warning 一次并回退原单 root 路径；
- 组大小 N>R，否则仍走单 root。

即 main 实现由「正数 R + DEFAULT + A2/A3 + N>R」触发，而非由文档名开关触发；不设置 RANKS_PER_ROOT 时分级不生效。

源码名 `ROOTINFO_SUBCOMM_ENABLE`（torch_npu/csrc/core/npu/register/OptionsManager.cpp:106-112，`GetBoolTypeOption` 默认 0，`const static bool` 首次读取后进程内缓存）控制的是另一条实验性子通信域派生路由：`createHCCLCommOrigin` 开头（ProcessGroupHCCL.cpp:2953-2963）若该开关开启且为子域（`global_ranks_in_group` 非空），先以 isOrigin=true 尝试 `createHCCLCommSub`；成功则直接返回并警告与 resume 不兼容，仅当其返回 false（`hcclCreateSubCommConfig` 符号缺失、`global_` 全局进程组为空、isOrigin=true 走 `getHcclCommByDevicesFromCache` 缓存取不到可用 global 通信域、`createSubHcclComm` 建出空 subComm 等路径）时才落日志并继续 rootinfo 路由；isOrigin=true 的调用不进入带 try/catch 的 global 通信域获取分支。该调用没有外层 catch 兜底：`createHCCLCommSub` 内 `createSubHcclComm` 与各项 TORCH_CHECK 抛出的异常不会被 createHCCLCommOrigin 捕获，因此不能把回退承诺扩大为「SDK 任何失败都自动回退 rootinfo」。它是独立的内部实验功能，不是 `ROOTINFO_SCALABLE_ENABLE` 的改名或替代，也未出现在公开环境变量文档页中。

### ranks-per-root 的真实默认与接受域

`GetHcclRanksPerRoot`（OptionsManager.cpp:114-128）未设置时返回 -1，不是文档宣称的默认 128；解析用 `strtoll` 按 10 进制读取并做全串校验（`errno==0 && end!=envVal && *end=='\0'`，即不允许未消费后缀），接受 -1 或正数且 ≤ UINT32_MAX，其余（空串、0、-1 以外的负数、非数字、多余字符、超界）TORCH_CHECK 参数错误——并非「所有负值一律报错」，输入文本也不是仅限无符号数字（-1 带负号合法）。文档的 1~4294967295 正数取值域与源码一致；其「0/负数报错」的说法只对 0 与 -1 以外的负数成立：源码把 -1 作为显式合法值接受，默认语义是 -1 即「不启用分级」，文档未写该值；文档「仅开开关、unset RANKS_PER_ROOT 将使用默认 128」的示例在 main native 语义下不会分级。该 getter 无 static 缓存，每次调用重新读环境；实际消费点只有建域（懒建链首次集合通信），而「首次读取缓存」的 const static 模式只出现在 SUBCOMM 开关上。

### ABI 门与分组算法的源码确认

进入 scalable 分支后先过符号门：`hcclCommInitRootInfoScalableExist()`（torch_npu/csrc/distributed/HcclCompile.h:394-403）经 TORCH_NPU_GET_FUNC 一次性探测 `HcclGetRootInfoScalable` 与 `HcclCommInitRootInfoScalable`，任一缺失即 TORCH_CHECK 报 NOT_SUPPORT（ProcessGroupHCCL.cpp:2856-2860），不自动回退——main 源码确认了前文「缺运行库符号时报错，不能假定自动回退」的说法。分组计算 `numRoots=(N-1)/R+1`（溢出安全向上取整）、`baseGroupSize=N/K`、`largerGroupCount=N%K`（ProcessGroupHCCL.cpp:2871-2873）；root 判定 `getRootIndex` 取每个均衡组的首个 rank（ProcessGroupHCCL.cpp:97-122），root 信息经 `hcclGetRootInfoScalable` 生成、通过 TCPStore 键值交换（2457-2490、2885-2904），与文档「连续均衡、组间最多差 1」一致。

### release pin 的范围扫描结论

对 release 对应文件的扫描：release `torch_npu/` 内 `ROOTINFO_SCALABLE_ENABLE`、`TORCH_HCCL_RANKS_PER_ROOT`、`ROOTINFO_SUBCOMM_ENABLE`、`IsSubCommRootInfoEnable`、`GetHcclRanksPerRoot`、`createHCCLCommSub`、`HcclGetRootInfoScalable` 均零命中；release 的 `createHCCLCommOrigin`（ProcessGroupHCCL.cpp:2574 起）直接进入单 root `hcclGetRootInfo` 路径，release 也不携带对应环境变量文档页。这是范围扫描结论：main 的 scalable/subcomm 实现不能反推 release 交付同样行为；完整调用链与版本面证明超出本卡范围。

### 证据

- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp)（primary）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp)（primary）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/HcclCompile.h)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp)（supporting）
