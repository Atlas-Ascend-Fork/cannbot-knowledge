---
type: Guide
title: vLLM Ascend 进程与通信补丁：rank、原地语义和全局绑定
description: 核对MultiprocExecutor的TP×PP×PCP与进程清理、310P广播/int64归约的真实返回语义，以及Torch accelerator、EP/SP和EC示例的全局替换边界。
aliases:
- AscendMultiprocExecutor
- AscendWorkerProc
- NullHandle
- communication_adaptation_310p
tags:
- task.implementation
- task.debugging
- topic.parallelism
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_multiproc_executor.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_distributed.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_parallel_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_torch_accelerator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_example_connector.py
  role: implementation
created_at: '2026-11-03T05:17:15Z'
updated_at: '2026-11-03T05:17:15Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 进程与通信补丁：rank、原地语义和全局绑定

## 固定来源与补丁身份

按 ceac1a2 五个补丁整文件AST投影读取全部程序，未导入/应用补丁、启动子进程、通信或NPU。全局模块属性、已导入引用与对象实例不一定同步改变；适配Agent必须记录真实进程中被调用的类/函数和导入顺序。以下仅为源码兼容合同，不是通用硬件支持或已执行回归。

## MP world/rank与启动失败清理

AscendMultiprocExecutor要求world_size=TP×PP×PCP，且world能被nnodes_within_dp整除；local_world_size取配置，不自动等于TP。global_start_rank=local_world_size×node_rank_within_dp，driver按rank%TP==0选，不能把每节点local0等同唯一driver。

仅node_rank_within_dp=0创建广播队列和汇聚response queues；remote队列从peer worker取得。全部worker ready、队列ready后才post-init。fork时传递并关闭继承fd，子进程daemon=False；初始化未success的finally关闭death writers并确保已起worker终止，不意味着外部所有库资源都已回滚。output_rank在成功路径末确定。

文件替换multiproc_executor.MultiprocExecutor，并在cli.serve已导入时更新该模块同名引用；它不扫描任意已from-import的消费者。类存在不证明安装entrypoint已经使用它。worker进程仍以Native WorkerProc.worker_main为target，子类负责构造参数，不是复制另一套主循环。

## 310P通信适配必须核对返回值与副作用

仅DISTRIBUTED_COMMUNICATION_ADAPTATION能力开启时，模块替换torch.distributed及distributed_c10d的broadcast/all_reduce。CPU broadcast委托原函数；设备broadcast用all_gather后copy到原tensor，async_op=True也在同步gather结束后返回wait为空的NullHandle，并非真实异步Work。

设备broadcast里root先从group_src/src计算，但gather后索引用的是src；group内/全局rank及group_src不应凭签名假定与原生一致。int64 all_reduce更须谨慎：非int64委托原函数；int64用gather后返回新Tensor，SUM为stack.sum，MAX还经过CPU NumPy再放回设备，没有把结果copy回输入，也没有按async_op返回Work。仅SUM/MAX，其余拒绝。依赖原生in-place/None/Work合同的caller必须先检查；这是静态差异，未运行复现，不提供盲目替换修复。

## 其他全局兼容面

ParallelConfig.use_sequence_parallel_moe被替成property：只有列明all2all_backend、EP开启且TP>1才真。后端名单包含多套Native选项，不证明每个在Ascend已具备设备实现，仍须核实际MoE通信分派。

torch.accelerator.empty_cache/memory_stats/memory_reserved/reset_peak_memory_stats/get_memory_info分别绑定NPU接口，empty_cache wrapper无参数；多后端共进程、后导入替换或不同签名调用不能当已兼容。清cache也不释放仍被Tensor/图引用的内存。

ECExampleConnector consumer加载改用current_platform设备类型与实际device index，从safetensors读取ec_cache并放入encoder_cache；非consumer委托原函数。它是本地示例文件路径，不自动变成远端池化、完整失败重算或已认证输出。metadata先assert类型，后面的None日志分支不代替类型校验。

验收记录所有进程rank、driver、队列端点、最终符号identity、collective输入是否改变及返回类型、group_src、async等待、int64算子与混合设备。失败先定位ABI/导入绑定，不能把进程ready、NullHandle.wait返回或同shape误当通信/数值正确，再开展性能实验。
