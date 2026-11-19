---
type: Guide
title: 原生集合通信 NPU 清单：dtype、迁移映射与兼容路线
description: 按 PyTorch2.14 的逐 API 限制区分点对点、归约、Gather 和 AllToAll，不由通用 HCCL 可用推导所有 dtype。
tags:
- task.implementation
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-distributed.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-distributed.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-distributed.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-distributed.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-distributed.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-distributed.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-distributed.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-distributed.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-distributed.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-distributed.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-distributed.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-distributed.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-distributed.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-distributed.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/private_apis.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/private_apis.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/HCCL_EVENT_TIMEOUT.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/HCCL_EVENT_TIMEOUT.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/P2P_HCCL_BUFFSIZE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/P2P_HCCL_BUFFSIZE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/RANK_TABLE_FILE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/RANK_TABLE_FILE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/ROOTINFO_SCALABLE_ENABLE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/ROOTINFO_SCALABLE_ENABLE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_ASYNC_ERROR_HANDLING.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_ASYNC_ERROR_HANDLING.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_BLOCKING_WAIT.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_BLOCKING_WAIT.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_DESYNC_DEBUG.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_DESYNC_DEBUG.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_RANKS_PER_ROOT.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_RANKS_PER_ROOT.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_ENABLE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_ENABLE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_INTERVAL.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_INTERVAL.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_PATH.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_PATH.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/MULTI_STREAM_MEMORY_REUSE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/MULTI_STREAM_MEMORY_REUSE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/NPU_SHMEM_SYMMETRIC_SIZE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/NPU_SHMEM_SYMMETRIC_SIZE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/（beta）TORCH_HCCL_ZERO_COPY.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/（beta）TORCH_HCCL_ZERO_COPY.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/symm_mem/NPUSHMEMExtension.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/register/OptionsManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/nn/functional.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/distributed_patches.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/distributed/nn/functional.py
  role: implementation
created_at: '2026-11-09T06:08:21Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 原生集合通信 NPU 清单：dtype、迁移映射与兼容路线

## 固定版本与范围

依据 TorchNPU 固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`，按条目区分A2/A3训练系列与950DT；逐项版本门槛独立核对，不回推至 26.0/PyTorch2.8 发布基线。本文仅静态审阅，没有 NPU 实验。

## 清单的使用边界

本卡以固定提交PyTorch2.14条目为当前说明，按后文核对七版本及产品差异；表中是文档声明的输入范围，不是本卡运行验证，也不替代各通信域、输出容量和参与rank检查。

|操作|清单列出的输入dtype|
|--|--|
|send/recv/isend/irecv、P2POp、broadcast、scatter|BF16/FP16/FP32/FP64、UINT8/INT8/INT16/INT32/INT64、BOOL|
|all_reduce|BF16/FP16/FP32、INT32/INT64、BOOL|
|reduce|BF16/FP16/FP32、UINT8/INT8/INT32/INT64、BOOL|
|all_gather、gather|BF16/FP16/FP32、INT8/INT32、BOOL|
|reduce_scatter|BF16/FP16/FP32、INT8/INT32|
|all_to_all_single、all_to_all|此清单仅列FP32，不用其他操作的BF16支持外推。|

batch_isend_irecv的列表条目按其中Tensor的dtype解释，不把列表本身当Tensor；gather_object是Python Object，scatter_object_list不涉及Tensor dtype。这些不是GE通信图Converter的支持矩阵。

## 实现映射和域配置

ProcessGroupNCCL条目仅在transfer_to_npu迁移机制生效后映射为ProcessGroupHCCL，实际仍是HCCL通信；未启用不能因类名存在就当作NCCL已在NPU运行。

清单为gather、scatter、all_to_all分别说明use_compatible_impl(True)可切换原生一致路线；不能把环境变量页列出的四个算子当作方法开关的完整名单，也不能推导所有通信都被切换。

init_process_group/new_group列hccl_config的buffer与group_name，名称长度不超过32；这些基础字段说明不能证明该配置类所有新字段和硬件组合都支持。建域前配置，已有域不随字典修改重配，详细范围保持独立核对。

- [通信域参数的证据缺口](torch_npu_hccl_pg_options.md)
- [Work.wait与通信内存保护](torch_npu_collective_memory_reuse.md)
- [GE通信图是另一条支持路线](../../inference/guides/optimization/torchair/collective_communication_graph_contract.md)

验证各rank的操作顺序、dtype、shape与数据一致性，再评估通信计算重叠；本文未运行通信。

## 七版本产品、Work与旧Tensor集合入口

同提交2.7.1、2.9至2.14中英文页对上表通信操作均列三类产品；init_process_group/new_group、get_backend/rank/world_size及组rank查询、DeviceMesh及from_group/get_all_groups/get_coordinate/get_group/get_local_rank/get_rank，另列三类产品。探测is_mpi_available/is_nccl_available/is_gloo_available/is_ucc_available/is_torchelastic_launched可调用不证明相应后端实际可用，更不证明NPU由NCCL执行。

is_available/is_initialized、Backend及register_backend中文仅A2/A3、英文明确950DT不支持。PrefixStore及构造/underlying_store、HashStore及构造，Store的构造/append/check/has_extended_api/multi_get/multi_set/timeout，TCPStore的构造/host/libuvBackend/port，FileStore的构造/path也有同样较窄范围；类级Store/TCPStore/FileStore列三类产品不覆盖每个子项。Store其余已列add/compare_set/delete_key/get/num_keys/set/set_timeout/wait列三类产品，不能据名称补全连接、故障恢复或一致性协议。

中文Work及boxed/exception/get_future/is_completed/source_rank/synchronize/wait列三类产品，英文未列该对象；清单不定义这些方法与NPU流事件的完整完成关系，仍按[Work与内存生命周期](torch_npu_collective_memory_reuse.md)处理。send_object_list在中文列三类产品；broadcast_object_list/all_gather_object/gather_object/scatter_object_list两侧列三类产品，Python对象表不提供完整序列化或设备Tensor协议。

all_gather_into_tensor与reduce_scatter_tensor只在同提交2.7.1、2.9..2.12中英文页收录，均列三类产品且world_size不支持3/5/6/7；前者output_tensor仅BF16/FP16/FP32、INT8/INT32、BOOL，后者output仅BF16/FP16/FP32、INT8/INT32。后者还说明A2的prod不支持INT16/BF16，不能因该局部说明出现INT16就反填基础dtype表。2.13/2.14未列这些入口，不推定实际包删除，也不把这组旧限制自动套给所有集合通信。

ReduceOp与小写reduce_op也不是同一dtype表：前者列BF16/FP16/FP32、UINT8/INT8/INT32/INT64、BOOL，后者不列BOOL。DistBackendError/DistNetworkError两侧列三类产品，DistError中文七页列三类产品、英文只在2.7.1/2.11..2.13收录；get_debug_level仅2.13两侧收录、列三类产品，缺项不证明错误或调试能力消失。

## 私有集合入口的支持类型

同提交中英文private_apis列以下入口三产品支持，原文“支持”没有指明各参数映射，不改成所有输入输出的完整类型合同：

| 准确入口 | 来源列出的支持类型 |
| --- | --- |
| torch.distributed._functional_collectives.reduce_scatter_tensor | BF16/FP16/FP32、INT8/32/64 |
| torch.distributed._reduce_scatter_base | FP16/FP32、INT8/32/64 |
| torch.distributed.all_reduce_coalesced、torch.distributed.nn.all_reduce | FP16/FP32、UINT8、INT8/32/64、BOOL、COMPLEX64 |
| torch.distributed._functional_collectives.AsyncCollectiveTensor | BF16/FP16/FP32/FP64、UINT8、INT8/32/64、BOOL、COMPLEX64/128 |

不同命名空间和私有/公开变体不共享同一类型并集；AsyncCollectiveTensor被列入也不独自证明消费时机、隐式等待、跨流或底层存储的完整完成协议。实际Work和内存复用仍按各自实现核对。

## 950DT通信环境条目独立于完整故障流程

同提交中英文环境页明确列以下A2/A3与950DT条目，不由普通通信API支持推导整个Watchdog或建链策略都支持该产品：

| 变量 | 限定合同 |
| --- | --- |
| P2P_HCCL_BUFFSIZE | 默认20MB，0复用默认域、≥1独立域；每域发送/接收各一份，共2倍大小且HCCL独占。TorchNPU7.1默认变化后若OOM，来源给设0的选择，但它会改变域选择；send/recv间隔长需核对建链超时，600秒仅来源建议、需按模型调整 |
| RANK_TABLE_FILE | 默认未配走协商；全路径有效时用文件；不存在回退，存在但内容错不回退、实际通信报错；要求可读JSON且非软链接，详细JSON字段另核 |
| HCCL_EVENT_TIMEOUT | 秒，默认1868，0..2147483647，0永不超时；配置时须大于HCCL_EXEC_TIMEOUT |
| TORCH_HCCL_BLOCKING_WAIT | 默认0，1在Host等待通信完成/错误/超时且不建Watchdog；进程组初始化读取，之后修改不影响已有组；新名优先旧HCCL_BLOCKING_WAIT |
| TORCH_HCCL_STATUS_SAVE_ENABLE/PATH/INTERVAL | ENABLE默认0，PATH默认/tmp，二者在扩展加载前设置；INTERVAL默认2秒、≤0回2、首次缓存；ENABLE=1且存在Watchdog路径才按相应合同采证 |
| TORCH_HCCL_DESYNC_DEBUG | 默认0，1只打印分析不终止，大集群可能卡死；新名优先旧HCCL_DESYNC_DEBUG；PyTorch1.11需同时启用ASYNC_ERROR_HANDLING |

ASYNC_ERROR_HANDLING页未列950，不能据相邻BLOCKING_WAIT支持补齐；Scalable RootInfo两变量只列A2/A3。缺项不等于显式不支持，实际组合需版本配套。周期日志和超时诊断见[状态采证](torch_npu_hccl_status_capture.md)；这里未运行通信、建域或故障注入。

## 950DT跨流保护与对称内存条目

MULTI_STREAM_MEMORY_REUSE中英文环境页列A2/A3及950DT：默认2，0关闭、1擦除recordStream并持弱引用、2省略部分recordStream并持强引用可能延长Tensor寿命、3在1上覆盖提前释放擦标记。模式2异步集合通信返回Work后必须wait，P2P保护回到recordStream；950DT支持条目不允许省略完成依赖或Tensor生命周期。

NPU_SHMEM_SYMMETRIC_SIZE同样列三产品，默认1GiB，正数字节数或K/M/G/T后缀，非法值报错；首次GetShmemSymmetricSize缓存并传给aclshmemx_init_attr或shmem_set_attr，过小会分配失败。它与P2P_HCCL_BUFFSIZE、Device缓存池不是同一容量。

TORCH_HCCL_ZERO_COPY的两语言实验页只列A3，默认0、1还要求expandable_segments=True且不支持TorchAir；不能因对称堆/普通通信支持950DT，把零拷贝也扩到950或A2。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-distributed.md)（primary）

- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-distributed.md)（constraint）

- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-distributed.md)（constraint）

- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-distributed.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-distributed.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-distributed.md)（constraint）

- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-distributed.md)（constraint）

- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-distributed.md)（constraint）

- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-distributed.md)（constraint）

- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-distributed.md)（constraint）

- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-distributed.md)（constraint）

- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-distributed.md)（constraint）

- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-distributed.md)（constraint）

- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-distributed.md)（constraint）

- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/private_apis.md)（primary）

- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/private_apis.md)（constraint）

- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/HCCL_EVENT_TIMEOUT.md)（primary）

- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/HCCL_EVENT_TIMEOUT.md)（constraint）

- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/P2P_HCCL_BUFFSIZE.md)（primary）

- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/P2P_HCCL_BUFFSIZE.md)（constraint）

- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/RANK_TABLE_FILE.md)（primary）

- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/RANK_TABLE_FILE.md)（constraint）

- [固定来源 23](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/ROOTINFO_SCALABLE_ENABLE.md)（primary）

- [固定来源 24](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/ROOTINFO_SCALABLE_ENABLE.md)（constraint）

- [固定来源 25](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_ASYNC_ERROR_HANDLING.md)（primary）

- [固定来源 26](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_ASYNC_ERROR_HANDLING.md)（constraint）

- [固定来源 27](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_BLOCKING_WAIT.md)（primary）

- [固定来源 28](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_BLOCKING_WAIT.md)（constraint）

- [固定来源 29](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_DESYNC_DEBUG.md)（primary）

- [固定来源 30](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_DESYNC_DEBUG.md)（constraint）

- [固定来源 31](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_RANKS_PER_ROOT.md)（primary）

- [固定来源 32](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_RANKS_PER_ROOT.md)（constraint）

- [固定来源 33](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_ENABLE.md)（primary）

- [固定来源 34](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_ENABLE.md)（constraint）

- [固定来源 35](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_INTERVAL.md)（primary）

- [固定来源 36](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_INTERVAL.md)（constraint）

- [固定来源 37](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_PATH.md)（primary）

- [固定来源 38](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/TORCH_HCCL_STATUS_SAVE_PATH.md)（constraint）

- [固定来源 39](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/MULTI_STREAM_MEMORY_REUSE.md)（primary）

- [固定来源 40](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/MULTI_STREAM_MEMORY_REUSE.md)（constraint）

- [固定来源 41](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/NPU_SHMEM_SYMMETRIC_SIZE.md)（primary）

- [固定来源 42](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/NPU_SHMEM_SYMMETRIC_SIZE.md)（constraint）

- [固定来源 43](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/collective_communication/（beta）TORCH_HCCL_ZERO_COPY.md)（primary）

- [固定来源 44](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/collective_communication/（beta）TORCH_HCCL_ZERO_COPY.md)（constraint）

## NPU_SHMEM_SYMMETRIC_SIZE 解析与消费面

`OptionsManager::GetShmemSymmetricSize()`（主线 :771-811，发布 :684-726；去空白后逐字符同构）以 static lambda 一次求值：未配置返回 1 GiB 默认；否则 `sscanf("%lf%c%c")` 解析——匹配 2 项（数字+单后缀 k/K/m/M/g/G/t/T）按 10/20/30/40 位左移；仅匹配 1 项按纯字节数；第 3 字符残留（n==3）或解析失败（n<=0）抛 "NPU_SHMEM_SYMMETRIC_SIZE is invalid."。返回 `ceil(p * (1ULL << scale))`。文档「配置值必须为正数」在实现层不成立：`%lf` 接受负数与 0，负值会得到负 size 且不抛错；小数（如 1.5G→1610612736）也被接受并向上取整。该值首次调用读取后缓存于 static，运行中修改不生效（与文档 NOTE 一致）。

消费链（主线 NPUSHMEMExtension.cpp :19-105）：`initialize_npushmem_with_store` 以 `static bool is_initialized` 做进程级一次（重复调用直接返回）；先 `Aclshmemx_set_conf_store_tls(false, nullptr, 0)`，取 init_size 后按 `Aclshmemx_get_uniqueid_exist()` 二分支——gitcode 路径 rank0 取 uniqueid、经 `NPUStoreExchange("npushmem_ext").all_gather` 广播后 `Aclshmemx_set_attr_uniqueid_args(rank, world_size, init_size, …)` 再 `aclshmemx_init_attr`；shmem 路径对称走 `Shmem_set_attr(rank, world_size, init_size, …)`。init_size 是对称内存堆初始化参数；`aclshmemx_init_attr`/`shmem_set_attr` 的堆语义在 CANN/op-plugin 侧，本卡只锚定 Python 扩展的取值与传递面，npushmem put/get 的 contiguous/rendezvous 约束不在此重述。以上全部为静态阅读，未初始化任何对称内存。

## torch.distributed.nn 的 _AllGatherBase 后向补丁

主线 `torch_npu/_init/patches/distributed_patches.py:52-55` 在 torch_npu 初始化的 distributed 补丁组 `_PUBLIC_API_ALIASES` 表里把 `torch.distributed.nn.functional._AllGatherBase.backward` 整体替换为 `torch_npu.distributed.nn.functional._allgather_base_backward_hccl`（与 gather/batch_isend_irecv 等别名同一安装机制 `_apply_public_api_aliases`）。替换函数（`distributed/nn/functional.py:8-30` 全文）只接受后端 NCCL/XCCL/HCCL，其余后端直接 `RuntimeError("Backend not supported!")`；要求 grad_output 首维可被 world_size 整除，否则报尺寸不整除错误；随后按整除后的尺寸用 `torch.empty` 在同 device/dtype 分配梯度 gx，并调用 `torch.distributed._reduce_scatter_base(gx, grad_output, ReduceOp.SUM, ctx.group)`，返回 `(None, gx, None)`。函数 docstring 自述：上游实现仅支持 NCCL，本版为 NPU 增加 HCCL 支持。

边界：该补丁使 torch.distributed.nn 的 all_gather_base 自动求导路径在 NPU 上由 `_reduce_scatter_base` 承接，但 `_reduce_scatter_base` 的 dtype 合同仍按上文私有入口表（FP16/FP32、INT8/32/64）独立核对，后端字符串与实际 HCCL 建域仍按「实现映射和域配置」处理，不在补丁存在时把 HCCL 当作所有 torch.distributed.nn 入口的默认支持。梯度的实际通信、内存与完成语义按 [Work与通信内存保护](torch_npu_collective_memory_reuse.md) 核对，本节未运行通信。发布版本 f3ecfe4a 对照：同一替换直接写在 `torch_npu/__init__.py:205`（发布版本 无 `_init/patches` 目录，补丁表机制为主线重构）；发布同名 `functional.py` 后端元组仅 `(NCCL, HCCL)`，主线新增 XCCL，其余逐行一致（diff 级全文对照，非逐行语义审阅）。
