---
type: Guide
title: SGLang GE Helper直调Tiling缓存与图捕获地址生命周期
description: 从固定ge_helper.h解释按Tiling类型与设备分区的512记录缓存、完整序列化键、eager预热、溢出路径与Host数据同步。
tags:
- task.implementation
- topic.memory
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/developer_guide/ge_helper_guide.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/ge_helper.h
  role: implementation
created_at: '2026-11-08T11:03:53Z'
updated_at: '2026-11-08T11:06:19Z'
platforms: []
---

# SGLang GE Helper直调Tiling缓存与图捕获地址生命周期

## 适用范围

这是SGLang库内C++ helper的源码reference，不能按同名类直接替代CANN的完整 `gert::TilingContext`。来源未为本helper给出独立的整卡平台支持表，保留draft/平台未定位。接口用于没有 `aclOpExecutor` 持有设备Tiling的直调路线，本次不分析某个算子的完整Host/Device启动图。

## 上下文顺序

先用 `OpDef::SetToContext` 设置支持类型/格式与属性，再按定义顺序 `RegisterTensor`；bool为true表示输入、false表示输出。可选输入仍占同一输入索引空间，不能删去空输入后重编号。helper形状工厂要求origin/storage维数一致且最多4维；这不是所有Ascend C算子的维数上限。

## 缓存键、地址与捕获

`GetTilingTensor<T>` 进入 `TilingTensorCache<T>::Get`，以模板类型分区，再按当前NPU设备索引分区。每个分区最多512条，键为整个 `sizeof(T)` 序列化字节，包括padding；T须trivially copyable且确定性初始化（如 `{}`），否则相同语义也可能产生不同键。

首次eager调用通过 `aclrtMalloc` 分配专用GM，用 `from_blob` 包装并在deleter中 `aclrtFree`，避免该持久区由Torch缓存分配器重映射。缓存命中返回对应slot视图；捕获时只允许已存在的完整配置，不新增记录。每组shape/dtype/optional-input/属性对应的Tiling须先eager预热。

512条满后，新配置eager路径复用分区内持有的 `overflowBuffer` slab，并返回非分配器所有的视图；捕获时拒绝未缓存配置。文档称其为one-shot路径，固定源码实际保留并复用该slab，所以不能据文档推断每次独立分配或跨并发流安全。Host mutex覆盖整个Get中的lookup、插入、上传及流同步，但不保护Get返回后的Device Kernel执行，不能由此证明任意多流复用安全。

`CopyTo_` 在torch_npu当前流提交H2D `aclrtMemcpyAsync` 后同步该流，因为源Tiling可能是栈对象；不能只看到Async调用就声称Host完全异步。缓存命中不重新上传相同配置。

## 失效边界与复核

捕获期间，缓存尚未初始化或配置未命中（包括已满512条）会报错；已有命中仍可取回。eager未命中可以插入，满额时继续走溢出slab。调用方应核对完整序列化是否稳定、设备/类型是否相同、是否在捕获中，以及直接launch传入的Tiling地址由谁持有。helper缺失的 `SetBlockDim/SetTilingKey/GetRawTilingData` 被删除，不能把它当作注册式TilingContext的完整接口。本文未执行编译、捕获、并发或真机测试。
