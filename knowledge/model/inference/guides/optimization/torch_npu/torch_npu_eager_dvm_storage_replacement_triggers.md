---
type: Guide
title: Eager DVM存储层flush触发点：set_族换储、resize重分配与指针重定向
description: 固定主线三处storage层LazyFusionFlush触发（SetNpu/ResizeNpu.h/ChangeDataPtr）的门条件、发布负向与Storage.resize_钩子入口，闭合audit遗留的触发组合账。
tags:
- task.optimization
- topic.memory
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/SetNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/SetNpu.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/ResizeNpu.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/ResizeNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/ChangeDataPtr.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUHooksInterface.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/SetNpu.cpp
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/ResizeNpu.h
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/ChangeDataPtr.cpp
  role: constraint
created_at: '2026-11-12T17:12:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Eager DVM存储层flush触发点：set_族换储、resize重分配与指针重定向

## 固定版本与范围

主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 `csrc/aten/common/SetNpu.cpp`（143 行）、`ResizeNpu.h`（152 行）、`ChangeDataPtr.cpp`（68 行）、`ResizeNpu.cpp`（62 行）、`NPUHooksInterface.cpp`（74 行）全文/定向阅读；发布 pin `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 三文件均存在但 `LazyFusionFlush|lazy_fusion` 零命中（负向 rg）——**存储层 flush 触发全部为主线能力**。flush 语义本体（Manager/池/输出分配保护）由[融合提交卡](torch_npu_eager_dvm_flush_workspace_and_allocation_reentry.md)、元数据命中由[元数据别名卡](torch_npu_eager_dvm_metadata_alias_and_view_lifetime.md)、开关与启用面由[Eager 融合卡](torch_npu_eager_lazy_fusion.md)持有；本卡只闭合 storage 层触发点组合（audit-d 遗留账：SetNpu/ResizeNpu/ChangeDataPtr 触发组合未逐一成卡）。

## 三处触发点

| 触发点 | 位置 | 门条件 | 保护的失效资源 |
|---|---|---|---|
| set_ 族换储 | `set_storage_nd_npu`（SetNpu.cpp:6-25，flush :13-21） | 旧 storage impl 非空且 ≠ 新 storage impl，且 `lazy_fusion::IsEnabled()` 且旧 storage `lazy_fusion_data_!=nullptr` | 旧存储上挂起的 DVM Store——self 若持最后引用，旧存储将被释放 |
| resize 重分配 | `storage_resize_npu`（ResizeNpu.h:19-95，flush :31-39） | `lazy_fusion::IsEnabled()` 且该 storage `lazy_fusion_data_!=nullptr`（在 resizable/base 格式检查之后、`allocator()->allocate` 之前） | Store 节点持有的当前 data_ptr（重分配后失效） |
| 指针重定向 | `npu_change_data_ptr`（ChangeDataPtr.cpp:9-67，flush :56-61） | 同上门条件（dst storage），在 `set_data_ptr(std::move(aim_data_ptr))` 之前 | Store 节点引用的当前 data_ptr 即将被改指 src 内偏移 |

三处共用同一谓词（开关开 + storage 已登记 lazy_fusion_data_），差异只在被替换的资源；flush 本身是全局 `LazyFusionFlush()`，不做按 storage 的选择性提交（选择性命中语义见元数据别名卡的 MatchTensorMeta/MatchDvmOp，与此不冲突：这里 flush 全部挂起图）。

## set_ 族的收敛与 StorageDesc 分支

四个 `NPUNativeFunctions::set_` 重载与 `set_tensor_with_storage_format`（SetNpu.cpp:104-140）全部经 `set_storage_nd_npu` 收敛：先 flush 旧储（上表门），再 `at::native::checkSetStorage` + `set_storage_offset` + `resize_nd_npu`。set_(Storage) 三分支的 StorageDesc 处理：`CheckDescInit(src)` 成立则 CopyDesc；否则 `CheckStorageDesc`（storage_offset==0、连续、元素数与 src.nbytes/itemsize 相等）成立时 SetDesc(self,size,stride)，退化时 SetDesc 一维 `{new_size},{1}`——desc 初始化与 flush 互不替代。`set_(self)` 无参版分配 0 字节新储（allocate(0)+make_npu_storage_impl），`TORCH_INTERNAL_ASSERT(dtype==self.dtype())` 只在事后断言 dtype 未变。`set_tensor_with_storage_format` 由 Python 绑定 `set_storage_with_format_(Storage source)`（Module.cpp:1819-1838）暴露：TypedStorage dtype 优先于 desc.data_type_，dtype 视图 itemsize 不一致时按新 dtype 重算 numel 再 set（:104-140），fresh tensor 的空 storage 无 lazy_fusion_data_，flush 分支自然不触发。

## Storage.resize_ 上游钩子

`NPUHooksInterface::resizePrivateUse1Bytes`（NPUHooksInterface.cpp:42-56）是上游 Storage 字节级 resize 的 PrivateUse1 入口：base 格式与 itemsize>0 双 TORCH_CHECK 后转 `storage_resize_npu(..., force_refresh=true)`——即上游路径的 storage 缩放同样经过上表第二触发点；force_refresh 分支的 desc 重算/D2D 搬运语义由[out 准备卡](torch_npu_out_preparation_resize_and_overlap.md)持有。`resize_` 张量面（ResizeNpu.cpp:12-38）本身无 flush：格式转 base、`resize_impl_npu_` 尺寸一致早退、增长才进 maybe_resize_storage_npu 触发第二点；deterministic 三开关联合时对新增段确定性填充（fill_resize_deterministic_）。

## 与既有卡的配对

- storage_resize_npu 的 flush/分配/搬运/deterministic 段：[out 准备卡](torch_npu_out_preparation_resize_and_overlap.md):112 已持（含发布无 flush 步的差异）；本卡补齐其上游 Storage 钩子入口。
- npu_change_data_ptr 的 dtype 门/字节混用边界检查/组合 API 面：[组合张量卡](../../../apis/torch_npu/combine_tensors.md):77-79 已持（含发布无 flush 分支）；本卡把其 flush 归入统一触发组合。
- set_ 族换储 flush 与 set_tensor_with_storage_format 的 desc 分支为本卡新增闭合项（canonical/staged 全树 rg set_storage_nd_npu 此前零命中）。

## 边界

静态口径：未验证任何 flush 实际执行、旧存储释放时序、GIL/并发组合；发布 pin 三文件同位但零 flush 分支，`set_`/resize/指针重定向在发布走同一 C++ 路径而不同 DVM 语义。`NPUFunctions/CachingHostAllocator` 等消费面不在本卡。
