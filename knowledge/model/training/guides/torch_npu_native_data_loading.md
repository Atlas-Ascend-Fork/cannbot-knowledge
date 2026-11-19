---
type: Guide
title: 原生数据加载的NPU多进程限制与dtype清单边界
description: 说明固定版本DataLoader对NPU数据的限制，区分CPU加载、目录dtype措辞及Prefetcher流复用。
tags:
- task.optimization
- topic.data_pipeline
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-utils-data.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-utils-data.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-utils-data.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-utils-data.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-utils-data.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-utils-data.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-utils-data.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_module.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/prefetcher.py
  role: example
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-utils-data.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-utils-data.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-utils-data.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-utils-data.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-utils-data.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-utils-data.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-utils-data.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-Prefetcher.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-Prefetcher.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-Prefetcher.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/prefetcher.py
  role: implementation
created_at: '2026-11-09T07:31:16Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 原生数据加载的NPU多进程限制与dtype清单边界

## 固定来源与版本边界

依据PyTorch仓主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的原生支持页。页面分别对应PyTorch 2.7.1、2.9.0、2.10.0、2.11.0、2.12.0、2.13.0、2.14.0，相关条目的限制文本已逐版本提取核对；这不是同一安装包同时兼容所有版本的证明，也不补出未列出的2.8行为。

产品页确认A2/A3训练系列及950DT的下列条目。仅以固定来源记录已声明范围与实现边界，未运行上游代码、训练或设备实验；来源文档的“已验证”不作为本卡新增 verified 事件。

## 优化前先区分数据所在设备

七个版本DataLoader条目均写明不支持多进程加载NPU数据，num_workers只0。该条件不能省略“NPU数据”后扩大成所有CPU数据读取/预处理都必须单进程；CPU loader、Host到Device搬运和设备上的数据访问是不同阶段。

同提交模块补丁保留_MultiProcessingDataLoaderIter初始化：非空可见设备配置下先尝试NPU同步、调整线程亲和性，再调用原迭代器并恢复亲和性；它没有把所有CPU多进程迭代改成单进程。这个静态入口也不证明NPU Tensor可安全跨worker传递，不能反向取消支持表限制。

## dtype文字不能跨层套用

DataLoader条目写dataset仅FP32；2.14的相邻条目另列Dataset输入支持FP16/FP32/FP64及多种整数、Subset的dataset为INT64、DistributedSampler的dataset为INT32、default_collate的batch为FP64/INT64/BOOL等限制。它们不是一套可直接拼成“整个数据管线必须某单一dtype”的规则。

dataset、data_source或batch可能是Python容器/对象，支持表没有在这些条目中完整给出嵌套Tensor与CPU/NPU位置的定义。按文档记录该窄声明，超出声明的组合另核对；不要为了满足相邻Sampler文字把所有样本、索引和标签一并cast到浮点。清单的未列产品/接口表示尚未纳入验证，不自动等于运行时绝对禁止。

## Prefetcher的具体协议

同提交contrib Prefetcher只处理loader每次返回的(input,target)二元组，分别调用.npu(non_blocking=True)。默认构造一个NPU stream；类注释说明反复初始化时应传入可复用stream，防止反复创建造成内存问题。它不是任意嵌套batch的通用递归搬运器。

next()先让当前stream等待预取stream，取出当前二元组，再预取下一批；初始化即触发一次预取。non_blocking=True和单独stream只是该实现的异步提交方式，不是实际数据源、pinned内存、生命周期和计算流水已重叠的性能证明。

## 验证

分别测CPU读取/预处理、拼batch、pinning、Host到Device搬运与计算；确认worker内是否创建/持有NPU Tensor及真实dtype。使用Prefetcher还要检查二元组协议、最后一批和重复初始化。对目标版本的端到端吞吐与峰值内存做比较，不能仅按num_workers或non_blocking一个开关判断优化成功。

- [pinned memory参数的独立条件](../../inference/guides/optimization/torch_npu/torch_npu_pinned_memory_options.md)

## 完整数据工具与英文产品表

七版本中英文页对random_split、IterableDataset/TensorDataset/ConcatDataset/ChainDataset、default_convert、get_worker_info和BatchSampler列三类产品。StackDataset中文仅A2/A3、英文明确950不支持；IterDataPipe/MapDataPipe仅2.13/2.14收录，也中文仅A2/A3、英文950不支持，不由DataLoader类表扩展这些对象。

其余局部类型表两侧一致：Dataset.input为FP16/FP32/FP64、UINT8/INT8/INT16/INT32/INT64；Subset.dataset、Sampler.data_source和_utils.collate.collate.batch为INT64；SequentialSampler/RandomSampler.data_source、SubsetRandomSampler.indices及WeightedRandomSampler.weights为FP32；DistributedSampler.dataset为INT32；default_collate.batch为FP64/INT64/BOOL。这些条目不提供整个Python容器/嵌套Tensor的统一类型规则，特别不将名为indices的来源FP32文字改写成所有模型索引都应转FP32。

上述支持表没有pin_memory、worker生命周期和NPU预取的完整合同，DataLoader对NPU数据num_workers=0的条件继续适用；CPU数据多进程与设备搬运分别验收。

## 预取器的版本化API合同

[contrib Prefetcher接口](../apis/torch_npu/contrib_prefetcher.md)补充OpPlugin发布/主线中英文产品页、耗尽二元返回与重复初始化流要求；该API限定A2/A3，不由本原生指南的其他条目扩大到950DT。non_blocking和wait顺序仍需真实管线验收。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-utils-data.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-utils-data.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-utils-data.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-utils-data.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-utils-data.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-utils-data.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-utils-data.md)（primary）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_module.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/prefetcher.py)（example）

- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-utils-data.md)（constraint）

- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-utils-data.md)（constraint）

- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-utils-data.md)（constraint）

- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-utils-data.md)（constraint）

- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-utils-data.md)（constraint）

- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-utils-data.md)（constraint）

- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-utils-data.md)（constraint）

- [固定来源 17](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-Prefetcher.md)（constraint）

- [固定来源 18](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-Prefetcher.md)（primary）

- [固定来源 19](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-Prefetcher.md)（constraint）

- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/prefetcher.py)（implementation）
