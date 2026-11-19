---
type: API
title: contrib Prefetcher：二元批次、复用流与耗尽协议
description: 区分非阻塞搬运和实际重叠，保存构造预取、next等待及重复初始化条件。
tags:
- task.lookup
- topic.memory
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-Prefetcher.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-Prefetcher.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-Prefetcher.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/prefetcher.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/prefetcher.py
  role: implementation
created_at: '2026-11-09T19:49:40Z'
updated_at: '2026-11-09T19:49:40Z'
platforms:
- a2
- a3
---

# contrib Prefetcher：二元批次、复用流与耗尽协议

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文页、主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文页及各自实际收录范围。TorchNPU实现分别为发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b与独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，不把两个仓库main当已配套。

默认A2/A3只指页面所列训练系列；推理产品及其他入口的扩展另说明，旧Atlas不自动映射新型号。此批contrib页面没有950DT确认，不由底层算子或框架总览扩展。这里只做静态阅读，没有导入上游、加载模型、运行设备、反向或性能实验；stable不表示运行verified。


## 构造与返回

`Prefetcher(loader,stream=None)`将loader转iterator并立即preload；每批必须恰为(input,target)且两者有.npu(non_blocking=True)，不是任意嵌套dict/list批次的递归搬运器。省略stream时新建NPU Stream，训练多epoch反复创建Prefetcher时应传入复用的显式流，文档目的为避免反复建流的内存问题。

next()让当前流wait_stream预取流，返回已准备的二元组，目标非None时预取下一批；StopIteration使两者为None。源码docstring误植NMS的(k,5)/(k,1)和标签说明，与实际返回无关。target=None也会影响继续预取判断，不是任意无标签loader的完整协议。

## 生命周期与性能

主线中文/英文补全一次初始化及显式流多epoch例，核心两固定实现相同。没有在这几行提供全部跨流存储登记、错误恢复或并发访问保证；non_blocking及等待只描述提交顺序，不证明CPU读取、锁页、拷贝和计算已重叠。

与[原生DataLoader的NPU数据多进程限制](../../guides/torch_npu_native_data_loading.md)分开：CPU加载和设备搬运阶段不同。使用时验收末批、耗尽、复用流和实际吞吐/峰值，未运行数据管线试验。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-Prefetcher.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-Prefetcher.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-Prefetcher.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/prefetcher.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/prefetcher.py)（implementation）
