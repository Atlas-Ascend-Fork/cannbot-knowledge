---
type: Guide
title: vLLM Ascend 系统调优：TCMalloc、NPU allocator、HCCL 与主机配置
description: 按进程、容器和宿主机区分性能候选；核对 PYTORCH_NPU_ALLOC_CONF 的默认追加、sleep/RL 约束及有效环境，记录
  TCMalloc、队列、通信和 OS 配置的验证与回退条件。
tags:
- task.optimization
- topic.performance.analysis
- topic.memory
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/performance_and_debug/optimization_and_tuning.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/performance_and_debug/optimization_and_tuning.po
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/generate_zh_docs.py
  role: implementation
created_at: '2026-10-29T17:33:00Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T18:12:42Z'
---

# vLLM Ascend 系统调优：TCMalloc、NPU allocator、HCCL 与主机配置


## 适用条件与实验合同

依据 Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 的系统调优文档、allocator 配置函数及 RL 配置消费。固定文档列出候选开关，不提供各硬件/模型的对照数据；整卡没有明确硬件支持集合，保持 draft/空平台，不能作为所有机器通用配置包。

先按[环境配对](../deployment/vllm_ascend_versioned_environment.md)记录驱动、CANN、torch/torch_npu、vLLM/插件、Python 与二进制构建环境，以及 CPU 架构、NUMA/cpuset、设备与网络拓扑。固定模型、图模式、并行、sleep/RL、负载和质量门槛。每次改变一个因素，保存生效值、资源水位、重复结果及恢复方式；[性能基准](vllm_ascend_benchmark_workflow.md)中的正确性、失败率和尾延迟同时验收。

来源的镜像变量含构建模板 `cann_image_tag`，软件源使用 Ubuntu jammy/ports，并带修改 apt 源和 pip 全局镜像的示例。这些是当时配方，不能直接当作任意 OS/架构的前置步骤；本次没有执行容器、安装、全局环境或主机配置修改。

## 先区分配置所在层

| 层级 | 候选及检查点 | 不能由此推出的结论 |
| --- | --- | --- |
| Python 进程/容器 | TCMalloc 的库架构、LD_PRELOAD、进程实际加载；torch_npu 及 HCCL 环境是否传到全部 Worker | 在 shell export、容器规格或启动日志中出现，不证明所有 Worker 使用同值，也不证明性能获益 |
| 框架配置 | 图模式、enable_sleep_mode、RL 配置、CPU 绑定与 allocator 最终值 | 启动输入不等于框架回写后的有效配置 |
| 宿主机 OS / K8s node | CPU governor、swappiness、NUMA balancing、scheduler 参数的可用性和实际值 | 容器内未暴露节点不能直接配置宿主机；只记录配置也不能证明生效范围和收益 |

## NPU allocator：读取最终值，不叠加互斥样例

文档将 `max_split_size_mb:250` 与 `expandable_segments:True` 列为二选一的内存实验。250 的单位是 MB，是该文档的样例值，不能当作所有模型的最佳阈值；功能支持及精确内存语义依赖目标 torch_npu/CANN。

当前 `NPUPlatform.check_and_update_config` 会调用 `_set_pytorch_npu_alloc_env`。其实际规则是：有 model_config 且 `enable_sleep_mode` 为假时，读取 `PYTORCH_NPU_ALLOC_CONF`，未设置时默认 `expandable_segments:True`；已有字符串若不含 expandable_segments、max_split_size_mb、garbage_collection_threshold 三个名称中的任何一个，就追加 `,expandable_segments:True`，再回写进程环境并记日志。

这层实现用子串存在性判断，不解析每项布尔值或全面校验组合。显式 `expandable_segments:False` 会保留；存在 max_split 或 garbage_collection 选项时不自动追加 expandable。源注释声明后二者与 expandable=True 不能并用，但函数不会替用户拆解一个已经写入的冲突组合。应核对目标 allocator 的有效配置与报错，不把“未自动追加”当成“配置已经合法”。

`enable_sleep_mode=True` 时上述函数跳过设置，不能据此断言用户继承的旧值已经删除。另有 `_disable_expandable_segments` 按逗号拆分并移除 stripped 后以 `expandable_segments:` 起始的项，保留其他非空项；`RlConfig.apply` 在 `enabled=True` 时调用它，还将 weight_nz_mode 强制为0、设置 server dev mode，并可使能 batch invariant。两条路径的前提分别记录，不能只凭 sleep 模式或来源通用建议推导所有最终环境。

判断 OOM/碎片问题时保存 allocated/reserved/峰值、KV 预算与图捕获条件；allocator 改动不增加物理 HBM。启用 RL、sleep、切权重或恢复后重新确认配置，不能只做首次普通生成验收。RL/batch invariant 的算子和调度限制见[确定性指南](../integration/vllm_ascend_batch_invariance_validation.md)。

## TCMalloc、下发队列与 CPU affinity

TCMalloc 是 host 内存分配候选，用正确架构的 libtcmalloc 并使 Python/Worker 实际加载。原例将库路径追加到已有 LD_PRELOAD，不能由“追加”推导它必然优先于所有现存 interposer；来源使用 ldd 检查加载路径，也不能仅靠该检查证明所有分配走该库或性能提高。记录启动前原值、实际加载及 host RSS/分配热点，再测请求指标。

`TASK_QUEUE_ENABLE=2` 用于算子下发队列；来源明确会影响内存峰值，内存紧张时可能退化。`CPU_AFFINITY_CONF=1` 是 torch_npu 层候选，文档将它关联 CPU 瓶颈场景，但没有本卡可用的收益实测；不能保证所有 NPU 瓶颈任务无退化。

torch_npu 的 CPU_AFFINITY_CONF 与 Ascend `additional_config.enable_cpu_binding` 是不同控制项。后者包含 taskset、NUMA 页面迁移、IRQ 或 950 cluster/UVB 路径；按[CPU/NUMA 绑定指南](vllm_ascend_cpu_numa_binding.md)检查实际线程、cpuset 和迁移，不把两个开关视为等价，也不盲目叠加互相争用的亲和性设置。

## HCCL：按通信路径选择候选

固定文档提出 `HCCL_OP_EXPANSION_MODE=AIV`，描述为经 AI Vector Core/RoCE 下发的通信模式；另列 HCCL_INTRA_ROCE_ENABLE、HCCL_RDMA_TC、HCCL_RDMA_SL、HCCL_BUFFSIZE，分别关联互联链路、RDMA traffic class、service level 和通信缓存。文档没有给出这些选项在所有目标芯片、拓扑、集合通信实现上的完整合法值/组合或通用推荐数值。

这些属于外部 CANN/HCCL 契约；先核对目标版本、设备互联、实际算法和通信组，再逐项实验。单卡无相应通信负载的测试不能证明多机效果；单个 collective 耗时下降也不证明端到端改善。保留 HCCL/网络错误、通信与计算时间线、端到端尾延迟及精度，不能把任意慢请求都归因于 HCCL_BUFFSIZE。

## 宿主机四项设置：参数赋值与实际效果分开

| 来源候选 | 设置意图 | 验证与解释边界 |
| --- | --- | --- |
| 所有 CPU scaling_governor 设为 performance | 减少频率策略引入的波动 | 先确认 cpufreq 节点/驱动和当前 governor；写入成功不等于所有核始终达到相同最大频率，仍记录实际频率、热/功耗及尾延迟 |
| `vm.swappiness=0`，正文还列0/1 | 降低 swap 倾向 | 参数赋值不等于执行 swapoff；不要据此宣称 swap 已禁用或内存压力消失，记录 swap 活动和 host 内存压力 |
| `kernel.numa_balancing=0` | 在明确 CPU/内存亲和性部署中减少自动迁移 | 需核对显式绑定是否真实生效；不能仅由关闭自动 balancing 推断远端页面已搬到目标 NUMA |
| `kernel.sched_migration_cost_ns=50000`，正文范围50000–100000 ns | 调整任务迁移倾向与局部性 | 与原值比较后才能称增大或减小；节点可能因 OS 版本不提供，样例值不是通用最优值 |

以上在来源中要求宿主机 root；本卡只是候选知识与验证条件，不表示当前环境已经执行或授权部署变更。计划目标机器实验时记录修改范围、原值和逐项恢复步骤，容器生命周期也不能替代宿主机配置恢复。

## 交付、停止与证据缺口

交付配置前后差异、全部 Worker 有效值、资源/拓扑、原始质量和性能记录、采集开销、重复统计与回退结果。出现 OOM、错误增加、质量下降、无可比负载或波动盖过差异时，停止收益结论并恢复该项基线；需要归因再按[服务剖析](vllm_ascend_service_profiling.md)取 trace。

本卡源码覆盖配置追加/移除和有关 RL apply，外部 allocator、TCMalloc、torch_npu 队列与 HCCL 的内部实现未在本批闭合；OS 含义的限制根据实际设置操作推导。没有 NPU、host 调优或下游 Agent A/B 结果，不把文档推荐和源码开关等同优化收益。


## 中文调优来源复核

optimization_and_tuning.po的有效译文已完整读取，保留TCMalloc、AIV/RDMA、宿主机root范围和四项OS设置的相同含义；“禁用交换空间”“保持最高频率”等标题/收益表述仍不是实际swap关闭、频率恒定或通用收益证明，应按本卡观测边界解释。源PO不翻译围栏代码也不能据此判断命令缺失，中文生成器会保留对应代码段。

本批仅复核固定源码与译文的技术语义，不执行上游生成器或宣称线上latest页面与该快照完全相同；硬件、版本和实验要求维持原边界。
