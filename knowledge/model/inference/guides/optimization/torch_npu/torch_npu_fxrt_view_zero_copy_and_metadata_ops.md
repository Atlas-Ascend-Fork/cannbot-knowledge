---
type: Guide
title: FXRT view零拷贝与元数据算子：ref对、存储校验与连续性边界
description: 记录FXRT view算子族经UpdateTensorViewInfo复用输入Storage的零拷贝路径、CheckStorageMatch别名校验、empty_strided仅连续stride限制，以及reshape/alias等元数据算子的推形规则。
tags:
- task.implementation
- topic.memory
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/view.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/view.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/view_base.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/utils/view_utils.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/utils/view_utils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/permute_view.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/permute_view.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/squeeze_view.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/squeeze_view.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/unsqueeze_view.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/unsqueeze_view.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/flatten_view.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/flatten_view.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/narrow_view.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/narrow_view.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/slice_view.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/slice_view.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/chunk_view.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/chunk_view.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/select_view.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/select_view.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/unbind_view.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/unbind_view.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/as_strided_view.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/as_strided_view.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/split_with_size_view.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/split_with_size_view.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/split_tensor_view.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/split_tensor_view.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_contiguous.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_contiguous.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/expand.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/expand.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/composite/clone.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/composite/clone.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/mem/empty.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/mem/empty.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/mem/empty_strided.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/mem/empty_strided.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/mem/memcpy_likes.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/mem/memcpy_likes.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_reshape.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_reshape.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_shape.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_shape.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_alias.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/alias.cpp
  role: implementation
created_at: '2026-11-13T04:14:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# FXRT view零拷贝与元数据算子：ref对、存储校验与连续性边界

## 固定来源与范围

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的FXRT view算子族与元数据/内存分配算子实现。静态阅读，未构建运行；产品与配套矩阵未知，整卡draft、platforms为空。view禁用开关的前端行为见[FXRT推理运行时](torch_npu_fxrt_runtime.md)的FXRT_DISABLE_VIEW_OPS一节，本卡只补C++侧落地。

## view算子不发射kernel

view族（view、permute_view、squeeze_view、unsqueeze_view、flatten_view、narrow_view、slice_view、chunk_view、select_view、unbind_view、as_strided_view、split_with_size_view、split_tensor_view）继承`AclnnViewBase`：`NeedLaunch()`固定false，Launch直接返回SUCCESS，`Init`用`GenerateOutputInputRefPair`声明输出-输入ref对。零拷贝的实现在CalcWorkspace里：按算子各自规则计算新shape/strides/storageOffset后调用`UpdateTensorViewInfo`把输出Tensor元数据指到输入Storage上，再`CheckStorageMatch`逐ref对验证输出Storage指针与输入一致，不一致即异常。这是硬校验：声明了ref却没真正复用存储会在执行前失败，而不是静默复制。

各view的元数据规则不同，不能互相推导：view要求输出shape已静态推断且不含未解析维，`CalculateViewStrides`在输入非连续且目标无法按现有strides表达时抛异常并建议先`.contiguous()`，shape分量小于-1直接拒绝；permute_view先规范负轴、校验dims长度等于输入rank且去重后无重复，再按轴重排输入strides；split族按尺寸表切分首维；squeeze/unsqueeze/flatten/narrow/select/unbind/as_strided各有独立边界条件。这些校验失败都是异常，不是回退到复制。

## CheckOpSupport白名单与view回退的对应

op_support.cpp把view/reshape/unsqueeze/squeeze/flatten/alias、permute_view/permute、slice_view/slice、narrow_view/narrow、getitem_slice、as_strided_view、empty_strided等列入放行白名单并注明理由：这些op在FxConverter走Path C/ViewAlias/恒等旁路，其中permute标注为“Path C Transpose物化（非ViewAlias）”、slice族标注为“Path C SliceV2物化（连续step==1，非ViewAlias）”。**即permute/slice的view形式在白名单中不等于它们总是零拷贝**：注释明确区分了ViewAlias（同地址新StorageShape）与需要物化的路径。这与前端FXRT_DISABLE_VIEW_OPS只对permute_view、split_with_size_view、split_tensor_view三个注册回退项一致；实际是否物化以固定提交的下lowering为准。

## expand与动态shape的交互

AclnnExpand自带InferShape：输出rank/shape由size操作数决定，-1表示保留输入维（PyTorch语义）；输入带symbolic shape且动态时先`EvalSymbolicShape`再取Shape。这是“动态shape模式下先InferShape后CalcWorkspace/Launch”的注释行为，也说明expand不是view：它可能改变size并需要真实广播，输出不与输入共享Storage。

## empty/empty_strided/memcpy_likes与contiguous

`empty`/`empty_like`走aclnnEmpty分配；`empty_strided`显式拒绝非连续stride（`IsContiguousStride`按尾维累积校验，0-size特判），错误信息明说“FXRT现在只支持连续stride”；输出shape与请求size不一致也异常。`memcpy_likes`（copy类）与`clone`、`aclnn_contiguous`分别绑定aclnnInplaceCopy/相关API：contiguous.cpp里有5处分支处理输入连续性 shortcut 与否。也就是说FXRT图内的“分配+复制”本身也是注册算子，经与[执行器缓存](torch_npu_fxrt_aclnn_executor_cache_and_op_registry.md)相同的AclnnExecutor路径下发；跨FXRT→Torch输出复制语义仍以运行时卡的to_torch一节为准。

## op_base元数据算子

`OpReshape`做纯推形：负维只允许一个，按输入Numel反推；`OpShape`/`OpAlias`是no-op元数据算子，OpAlias声明(0,0)ref对且不Launch；aclnn侧的`alias.cpp`同样是10行no-op（Launch返回SUCCESS，无执行器）。它们与aclnn view族的区别是：op_base这些算子不经过aclnn，仅维护IR元数据；选中哪条路由Op枚举与注册表决定（见[注册边界](torch_npu_fxrt_aclnn_executor_cache_and_op_registry.md)）。

## 边界与验证方式

本卡所有零拷贝结论是静态推导：ref对声明+存储指针相等校验保证的是“输出与输入共享Storage”，不保证跨executor重放、ACLGraph捕获或to_torch输出复制后别名仍保留（后两者见运行时卡对应边界）。采用前固定组合，用带padding/偏移/非连续输入逐view核对输出strides/offset与PyTorch eager结果，比较是否发生意外物化（看RT_VLOG与实际拷贝量），并验证CheckStorageMatch失败路径确实在执行前报告。不宣称任何view组合的性能收益。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/view.cpp)（primary）：定向范围1–51。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/view_base.h)（implementation）：定向范围1–98。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/permute_view.cpp)（implementation）：定向范围1–76。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/utils/view_utils.h)（implementation）：定向范围1–46。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/expand.cpp)（implementation）：定向范围1–60。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/mem/empty_strided.cpp)（implementation）：定向范围1–83。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_contiguous.cpp)（implementation）：全文件55行。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_reshape.cpp)（implementation）：全文件57行。
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/composite/clone.cpp)（implementation）：全文件32行。
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/split_with_size_view.cpp)（implementation）：同族抽样78行。
