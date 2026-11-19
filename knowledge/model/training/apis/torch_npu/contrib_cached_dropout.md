---
type: API
title: 缓存Dropout：Fairseq别名、预热与共享掩码队列
description: 保存无动态shape、掩码缺失时透传及eval边界，区分Cached与PreGen的状态协议。
tags:
- task.lookup
- topic.memory
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-NpuFairseqDropout.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-NpuFairseqDropout.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-NpuFairseqDropout.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-module-NpuCachedDropout.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-module-NpuCachedDropout.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-module-NpuCachedDropout.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/ensemble_dropout.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/ensemble_dropout.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/_ensemble_dropout.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/_ensemble_dropout.py
  role: implementation
created_at: '2026-11-09T19:49:40Z'
updated_at: '2026-11-09T19:49:40Z'
platforms:
- a2
- a3
---

# 缓存Dropout：Fairseq别名、预热与共享掩码队列

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文页、主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文页及各自实际收录范围。TorchNPU实现分别为发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b与独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，不把两个仓库main当已配套。

默认A2/A3只指页面所列训练系列；推理产品及其他入口的扩展另说明，旧Atlas不自动映射新型号。此批contrib页面没有950DT确认，不由底层算子或框架总览扩展。这里只做静态阅读，没有导入上游、加载模型、运行设备、反向或性能实验；stable不表示运行verified。


## 公共入口及准备阶段

`NpuCachedDropout(p,module_name=None)`和`NpuFairseqDropout`在两固定实现是同一个类。继承nn.Dropout，module_name仅记录身份；页面明确不支持动态shape。forward可接Tensor，或内部使用的[shape,dtype,device]列表：前者应用掩码、后者取掩码。p=0分别返回原Tensor或None。

类级task_dict以(shape,dtype,device,p)索引，初次/队列无掩码时增加请求计数并直接透传输入或返回None；不是第一次forward已经执行标准随机Dropout。主线中文增加enable_dropout_ensemble(model)及两次forward的预热示例，英文没有同等示例，但不改变准备前提。

## Hook和训练状态的边界

enable注册pre-hook等待dropout_stream、post-hook按需求补mask。创建了流，但所读post-hook没有with该流的上下文，不能仅因变量名就报告掩码与计算已在独立流重叠。状态为类级共享，重复启用会重复注册且未返回可统一清理的句柄，不保证不同模型/任务自动隔离或字典自动回收。

**forward没有self.training判断**；p>0且有mask时，eval也不能按普通nn.Dropout习惯认定为恒等。必须按实际模块和调用路线核验，不能只给模型.eval()便宣称推理无随机失活。

## 内部PreGen是不同实现

NpuPreGenDropout在内部模块另定义，按p建立全局大掩码，初始max_mb=16、每次post-hook重生并复位索引，取片长度按128元素对齐后换算bit mask字节；不是缓存队列的别名。其task键不含设备，list输入分支之后仍访问x.shape，超容量当次复用掩码前段并提高后续容量，均不能当任意设备/形状、随机独立性和自动扩容成功的保证。该内部类没有独立产品页，本卡不把公共Cached范围外推成PreGen完整支持承诺。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-NpuFairseqDropout.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-NpuFairseqDropout.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-NpuFairseqDropout.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-module-NpuCachedDropout.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/（beta）torch_npu-contrib-module-NpuCachedDropout.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/(beta)torch_npu-contrib-module-NpuCachedDropout.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/ensemble_dropout.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/ensemble_dropout.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/_ensemble_dropout.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/_ensemble_dropout.py)（implementation）
