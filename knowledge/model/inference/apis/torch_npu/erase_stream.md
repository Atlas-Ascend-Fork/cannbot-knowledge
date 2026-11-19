---
type: API
title: erase_stream：移除流标记与有序内存归还
description: 保留event依赖、分配流条件和跳过路径，避免把擦除标记当自动同步。
tags:
- task.lookup
- topic.model_serving
- topic.memory
- topic.precision
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-erase_stream.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-erase_stream.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-erase_stream.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-erase_stream.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/npu/Module.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/core/_exports.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py
  role: implementation
created_at: '2026-11-10T03:38:39Z'
updated_at: '2026-11-14T08:44:18Z'
platforms:
- a2
- '950'
aliases:
- torch_npu.erase_stream
---

# erase_stream：移除流标记与有序内存归还

## 固定版本与复核边界

文档为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda各自收录页；发布对应ascend_26_0_pt28。实现分别为TorchNPU发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b和独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，不把独立main当已配套发行。

产品逐接口/版本限定；950条目如仅DT便不扩PR，旧Atlas不自动映射新型号。静态阅读不表示已调用设备、图捕获、回调、文件解析或性能验证；stable不表示运行verified。未执行上游或加载任何模型、检查点和dump数据。


## 作用和产品

erase_stream(tensor,stream)->None移除record_stream登记的该流使用标记，减少Host下发快于设备时延迟归还造成的内存峰值。发布只列A2训练及旧Atlas训练，main增加950DT；没有A3或950PR的确认。本卡仅A2与主线950DT，不能由普通Stream支持表补齐。

## 必须已有正确依赖

文档要求结合event wait，确保真实使用与后续复用有序；它不是等待所有读写结束的同步函数。发布示例没有wait，主线补event.record/等待，但event.wait是在目标流建立后续依赖，不等于CPU已等待完成，也不能覆盖样例未包含的其他消费者或未来使用。

在能重新使用内存的流上建立对所有真实使用者完成事件的依赖，再移除相应记录；保留分配/使用/复用流关系和Tensor存活协议，不照抄地址相等样例就宣称任意多流安全或峰值必降。

## 两固定实现与静默跳过

Python检查Tensor、Stream类型，C++将存储DataPtr和具体流交CachingAllocator。空指针直接返回，非本缓存分配器deleter的Tensor告警并跳过；找不到已分配block报错。若block原分配流不是该设备当前流，直接返回，不能把返回None当擦除已生效。

实际erase删除stream_uses和相关待处理event计数，计数归零可free_block，本身没有补event wait或查询完成。不要对Host交换/共享/自定义分配Tensor假定此接口一定回收，也不要在未建立正确依赖时去掉record_stream的生命周期保护。两版顶层导出分别由直接导入/主线延迟导出实现，命名空间和底层Allocator限制分开。

## 已有 OpPlugin 7.3.0 文档与版本边界

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 消费流标记移除：torch_npu.erase_stream

### 用途与语义

删除 record_stream 为张量登记的流使用记录；删除前必须保证消费已完成，不能用它替代流间等待。

### 文档签名

```text
torch_npu.erase_stream(tensor, stream) -> None
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2。其他目标产品须另查该版本的支持表。

record_stream 的标记用于保护异步消费者的张量生命周期。提前移除会让内存过早复用；此 API 不是 Event/同步屏障。该文档只明确列出 A2，不能推导 A3 支持。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-erase_stream.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-erase_stream.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-erase_stream.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-erase_stream.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/utils.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/npu/Module.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/core/_exports.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py)（implementation）
