---
type: Guide
title: RankTable 建链：文件选择、回退与错误配置
description: 说明全局域及子域建链、文件缺失与内容错误的不同结果，区分初始化与稳态通信。
tags:
- task.optimization
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/distributed/communication_strategy/ranktable_link_setup.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/RANK_TABLE_FILE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/appendix/runtimeerror_Inner_Error.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/RANK_TABLE_FILE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/appendix/runtimeerror_Inner_Error.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/RuntimeError.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/RuntimeError.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/distributed/communication_strategy/ranktable_link_setup.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/flowchart_for_creating_a_communicator_using_a_ranktable_file.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/flowchart_for_creating_a_communicator_using_a_ranktable_file.png
  role: constraint
created_at: '2026-11-09T02:56:52Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
---

# RankTable 建链：文件选择、回退与错误配置

## 版本与范围

依据 TorchNPU 固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 RankTable 文档和环境变量页，选取 A2/A3 训练。具体 JSON 字段与 HCCL 版本配套另行核验，不从主线链接替代安装版本说明。

## 选择路径

RANK_TABLE_FILE 未设走默认协商；全路径有效时用预置 rank/IP/设备信息建立全局通信域，子通信域由全局域切分。文件不存在时回退默认协商；文件存在但内容错误时不会自动回退，可能到实际通信时才报错。

因此仅看进程已启动或 init_process_group 返回不能证明 RankTable 已被正确采用。文件须为可读 JSON、不能是软链接，所有节点的映射需与真实 rank、IP 和设备一致。

## 调优与诊断

RankTable 作用于建域，不自动提升每次 AllReduce 的带宽。分别测 worker 启动、首个通信触发的建域和稳态算子；保留有效路径和错误日志，不通过无限增大超时掩盖内容错误或缺 rank。

来源建议特定无协商建链超时场景核对 HCCL_CONNECT_TIMEOUT；仍先检查文件映射和所有 rank 参与。恢复默认路径应移除环境变量并重启相应 worker，不能只修改一个进程的配置。

- [Scalable RootInfo 的不同路径](torch_npu_scalable_rootinfo.md)
- [域级参数创建时机](torch_npu_hccl_pg_options.md)

## Inner Error的超时阶段差异

同一主线的RuntimeError附录针对RANK_TABLE_FILE场景、operator name指向通信算子的“The Inner Error ...”说明：原协商方式在socket协商与之后建链分别使用HCCL_CONNECT_TIMEOUT；RankTable跳过socket协商，直接建链且仍只使用该建链超时。因此原流程成功而RankTable超时是一个可能分支，不能只按相同总墙钟时间认定两者等价。

该页建议在原超时基础上加30秒，例如120改150，适用于这一已定位的阶段差异。它不是所有通信Inner Error都加30秒的通用修法，也不替代rank/IP映射、参与进程和实际日志核查。修改后用新worker比较首个建链是否完成；稳态带宽收益仍不能由超时改变推出。本卡已阅读附录文字，截图的独立核对见后文；未复现故障。

## 截图身份与异步栈线索

中英文附录截图内容逐字节相同；图中“The Inner Error”标出的current working operator name为HcclBatchSendRecv，并提示异步调用可能使stacktrace不准确。该样例只能作为保留实际通信算子、首错和所有rank日志的线索，不能据当前打印位置认定首发故障就在同步调用处，也不能把其历史时间、Python版本与路径作为当前运行环境。

RANK_TABLE_FILE环境页明确列950DT，但本指南还包含独立建链策略来源，整卡继续保持A2/A3范围；950环境入口的文件和回退条件见[原生集合通信指南](torch_npu_native_collective_constraints.md)。本卡只查看固定截图和文档，没有执行通信或复现故障。

## 建链图的惰性时机与配置层次

两语言流程图分别查看：init_process_group创建Python/框架通信组，图中在首个集合通信才创建全局HCCL通信域；new_group之后首次子域通信再从全局域切分。图中的dist.allreduce是示意标签，不能作为可执行Python接口名；这里也不据图推定所有device_id/初始化模式都只能惰性建域。

“几乎与集群规模无关”是该建链方案的来源描述，未给本卡集群测量。应分别记录启动、首次建域和稳态通信，不把图示切分理解为new_group自动继承默认pg_options，也不把外部ranktable JSON规范视作已全部摄取。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/distributed/communication_strategy/ranktable_link_setup.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/RANK_TABLE_FILE.md)（constraint）

- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/appendix/runtimeerror_Inner_Error.md)（constraint）

- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/RANK_TABLE_FILE.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/appendix/runtimeerror_Inner_Error.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/RuntimeError.png)（constraint）

- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/RuntimeError.png)（constraint）

- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/distributed/communication_strategy/ranktable_link_setup.md)（constraint）

- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/flowchart_for_creating_a_communicator_using_a_ranktable_file.png)（constraint）

- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/flowchart_for_creating_a_communicator_using_a_ranktable_file.png)（constraint）
