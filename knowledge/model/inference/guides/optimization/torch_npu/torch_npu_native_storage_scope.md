---
type: Guide
title: 原生Storage：类型视图、复制与950DT方法边界
description: 保留Typed/Untyped及量化Storage的类方法差异，结合NPU复制补丁说明共享存储与dtype角色。
tags:
- task.implementation
- topic.memory
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-Storage.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-Storage.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-Storage.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-Storage.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-Storage.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-Storage.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-Storage.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-Storage.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-Storage.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-Storage.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-Storage.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-Storage.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-Storage.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-Storage.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/storage.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/api_patches.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-Storage.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-Storage.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-Storage.md
  role: constraint
created_at: '2026-11-09T13:09:41Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 原生Storage：类型视图、复制与950DT方法边界

## 固定版本与范围

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 中PyTorch2.7.1、2.9至2.14的中英文原生支持页及所指实现；收录/缺项、类/方法与产品标记分别保留，不将文档版本差异直接视为实际发行历史。产品为各条目明列的A2/A3训练系列与950DT，不扩展950PR，也不推导主线与26.0/PyTorch2.8或其他主线已配套。支持表不替代完整参数、底层能力和设备验证，未执行上游或NPU实验。

## Typed与Untyped的产品表

中英文2.9/2.10/2.14导言提示TypedStorage及有类型Storage已弃用、优先UntypedStorage；其余页未重复这段提示，不解释为弃用撤销。两类主条目均列三类产品，不能由此推定全部转换、共享、文件或IPC方法可用。

UntypedStorage的bool/byte/char/clone/copy_/cpu/cuda/data_ptr/device/double/element_size/filename/fill_/float/from_buffer/from_file/get_device/half/int/is_cuda/is_pinned/long/nbytes/new/pin_memory/resizable/resize_/short/size/to/type/untyped列三类产品。bfloat16/byteswap/complex_double/complex_float/is_shared/is_sparse/is_sparse_csr/share_memory_/tolist中文只列A2/A3、英文明确950不支持。

TypedStorage相似方法按自身表消费：filename/is_shared/bfloat16/complex转换中文仅列A2/A3、英文明确950不支持，is_sparse/tolist却列三类产品；中文列resizable而英文未列。TypedStorage.cuda中文列三类产品，英文明确A2/A3不支持、950支持，与UntypedStorage.cuda不同。保留语言/方法差异，不把CUDA页前缀替换规则自动套到Storage的方法，也不将is_cuda可查询改写成NPU存储就是CUDA存储。

英文另对UntypedStorage的float8_e4m3fn/float8_e5m2/float8_e4m3fnuz/float8_e5m2fnuz，以及TypedStorage的float8_e4m3fn/float8_e4m3fnuz/float8_e5m2明确三类产品均不支持；hpu/is_hpu与UntypedStorage.mps也列均不支持，TypedStorage.share_memory_英文同样全不支持、中文未列。这不等于所有FP8 Tensor算子或所有共享路线都不支持。

## 有类型Storage的具体例外

Double/Float/Half/Long/Int/Short/Char/Byte/BoolStorage及dtype项列三类产品；BFloat16/ComplexDouble/ComplexFloat/QUInt8/QInt8Storage中文仅列A2/A3，英文明确950不支持。QUInt8.dtype说明uint8，QInt8.dtype的self仅int8。

QInt32Storage英文类级三类均不支持、dtype却列A2/A3支持并限制self INT32，中文没有独立类级表。QUInt4x2/QUInt2x4Storage类列三类产品，dtype却中文仅列A2/A3、英文950不支持，self列UINT8。类、dtype属性与实际数值类型不是同一合同，不能由名字推导量化Kernel、打包布局或任意转换已可用。

## 固定NPU补丁的复制语义

utils/storage.py为NPU UntypedStorage.cpu构造临时Tensor，再执行.cpu().untyped_storage()；非NPU调用原函数。它不是单凭名称就能认定共享原设备存储、零拷贝或无需同步的Host视图。

TypedStorage._deepcopy补丁以_cdata在memo的torch分组缓存已克隆UntypedStorage；构造的Tensor dtype与self.dtype不同时先view(self.dtype)，clone后恢复原NPU格式，最后按当前self.dtype重新包装同一memo存储。这里的view不是数值to转换；目标是同一存储的不同dtype视图各保留自己的dtype且共享一次克隆结果，不能无条件给每个视图独立复制或把描述符dtype当作全部逻辑视图dtype。未运行deepcopy或访问活跃地址。

旧权重重建函数按storage_offset/size/stride设置Tensor并恢复requires_grad和hooks，按RE_MAP_CPU、Fake模式及存储格式信息分支处理；来源告警建议用PyTorch2.1及以上重新保存旧文件。这只是所读重建路径，不是任意检查点的兼容或加载配方，本文未反序列化任何文件。

## 共享与验收边界

_add_storage_methods还安装_share_npu_/_new_shared_npu/_release_ipc_counter_npu及Typed包装，它们主要转发C++。私有入口存在不提供完整跨进程所有权、格式、计数器或自定义分配器IPC合同，继续按[分配器与IPC证据缺口](torch_npu_custom_allocator_and_ipc.md)核对，不能用普通share_memory_表替代。

固定真实Storage类型、dtype视图、设备、alias和消费者，比对复制后的字节/值、共享关系与生命周期，再比较分配和搬运开销。data_ptr、nbytes和dtype属性可调用不证明某个算子或序列化全流程可用。

## OpPlugin旧式NPU Storage列表的边界

两固定OpPlugin版本及主线英文另列Bool/Byte/Short/Long/Int/Half/Char/Double/FloatStorage，说明调用与torch.Storage相似，只给外部通用链接，没有逐方法、平台、所有权和序列化合同。该九项列表不覆盖前文Typed/Untyped、共享、弃用及950DT方法例外，也不据列表未含BF16判定整个NPU不支持BF16 Tensor。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-Storage.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-Storage.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-Storage.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-Storage.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-Storage.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-Storage.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-Storage.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-Storage.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-Storage.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-Storage.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-Storage.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-Storage.md)（primary）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-Storage.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-Storage.md)（constraint）
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/storage.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/api_patches.py)（implementation）

- [固定来源 17](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/torch_npu-Storage.md)（constraint）

- [固定来源 18](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-Storage.md)（primary）

- [固定来源 19](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-Storage.md)（constraint）
