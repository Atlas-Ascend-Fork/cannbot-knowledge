---
type: Guide
title: TorchNPU pg_options：按通信域配置 HCCL
description: 说明 hccl_config 名称映射、优先级、不继承规则及创建后不可重配边界。
tags:
- task.design
- topic.parallelism
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/distributed/parameter_configuration/setting_HCCL_communicator_parameter.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/distributed/distributed_overview.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/distributed/（beta）torch-distributed-ProcessGroupHCCL.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/distributed/parameter_configuration/setting_HCCL_communicator_parameter.md
  role: constraint
created_at: '2026-11-09T02:11:09Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# TorchNPU pg_options：按通信域配置 HCCL

## 版本与范围

依据固定 TorchNPU 主线文档，不把新字段回推到 26.0 发布版本。来源没有为各字段提供完整平台支持表，本卡为 draft，实际可用项必须随 TorchNPU、HCCL/CANN 和硬件核对。

## 配置契约

创建 torch_npu._C._distributed_c10d.ProcessGroupHCCL.Options()，设置 hccl_config 字典，在 init_process_group/new_group 时通过 pg_options 传入。必须在建域前配置；修改原字典不会重新配置已存在的域。新域不会自动继承默认域的 hccl_config，需要单独传。

字典使用 Python 参数名：hccl_buffer_size→hcclBufferSize、group_name→hcclUdi、hccl_exec_timeout→hcclExecTimeOut、hccl_algo→hcclAlgo。不要直接写结构体成员名。来源例子的 buffer 单位为 MB，超时为秒；其他字段范围与特殊“未配置”值按对应安装版本的 HCCL 文档核验，不能复制当前主线表当作发布版全字段清单。

有效的域级配置优先于相应环境变量，其次才是默认值。例如 HCCL_BUFFSIZE=200、某域 hccl_buffer_size=100，该域用 100MB，其他未单独配置的域仍用全局值。字符串超长会截断并告警。group_name 不是 hcclCommName；hcclCommName/hcclDeterministic 由框架处理。相同 hccl_buffer_name 还会在同设备复用通信流，应核对并发顺序。

## 验证

各 rank 以一致顺序建域，记录各域的 ranks、配置和实际初始化日志，检查 buffer/算法/超时是否作用于预期域。仅静态核对，未运行 HCCL。

- [通信内存复用](torch_npu_collective_memory_reuse.md)


## 平台证据分层

同候选 OpPlugin 的 ProcessGroupHCCL 基础构造器页列出 A2/A3 等产品，但这不是 hccl_config 各字段及其 HCCL 依赖的支持表。构造器可用、字段存在、建域配置实际生效三者分别核验，因此本卡仍保留草稿。RankTable 与 RootInfo 路径选择也不由域级配置字典自动替代。

- [RankTable 文件与回退](torch_npu_ranktable_communication_init.md)
- [Scalable RootInfo](torch_npu_scalable_rootinfo.md)

## 初始化副作用与重建不等于重配

- [get_hccl_comm_name 的惰性初始化和内存副作用](../apis/torch_npu/get_hccl_comm_name.md)
- [reinit_process_group 的分支范围及返回差异](../apis/torch_npu/reinit_process_group.md)

这些基础接口的产品页和实现不证明 hccl_config 所有字段生效，也不证明更改原 Options 后已存在的域自动采用新配置。本卡仍为 draft。

## 固定主线的十二项映射与内部字段

两语言完整参数表如下；只表达本提交的Python键到结构体字段映射，不表示安装的HCCL已支持全部字段。

| hccl_config键 | HcclCommConfig字段 |
| --- | --- |
| hccl_buffer_size | hcclBufferSize |
| group_name | hcclUdi |
| qos_traffic_class | hcclRdmaTrafficClass |
| qos_service_level | hcclRdmaServiceLevel |
| hccl_sdma_qos | hcclQos |
| hccl_op_expansion_mode | hcclOpExpansionMode |
| hccl_exec_timeout | hcclExecTimeOut |
| hccl_algo | hcclAlgo |
| hccl_retry_enable | hcclRetryEnable |
| hccl_retry_params | hcclRetryParams |
| hccl_buffer_name | hcclBufferName |
| hccl_sym_win_max_mem_size_per_rank | hcclSymWinMaxMemSizePerRank |

字段类型会校验；值域、默认和表示未配置的特殊值委托给匹配安装版本的HcclCommConfig说明，不能从此表补造。hccl_world_rank_id/hccl_job_id是NSLB场景由框架处理的内部字段，不要求用户手配；group_name仍映射Udi而非CommName。

样例默认域200MB/500秒、子域100MB/600秒和allreduce算法字符串只演示差异化配置，不能当作推荐容量或超时。所有rank按相同顺序new_group，示例先销毁子域再销毁默认域。相同hccl_buffer_name复用通信流不等于证明任意缓冲区都可别名或容量足够；RankTable内部切分全局HCCL域也不改变Python新域不继承hccl_config这一规则。本卡继续draft。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/distributed/parameter_configuration/setting_HCCL_communicator_parameter.md)（primary）

- [本卡补充来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/distributed/distributed_overview.md)（supporting）

- [本卡补充来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/distributed/（beta）torch-distributed-ProcessGroupHCCL.md)（constraint）

- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/distributed/parameter_configuration/setting_HCCL_communicator_parameter.md)（constraint）
