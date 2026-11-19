---
type: Guide
title: 外部内存进NPU Tensor：from_blob 工厂契约与 DLPack 入口改路由
description: 固定 at_npu::native::from_blob 的设备一致性、deleter 所有权、存储构造与容量计算契约，以及 torch_npu
  导入期对 to/from_dlpack 的补丁路由与静默回退边界。
tags:
- task.implementation
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/from_blob.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/from_blob.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/dlpack.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/api_patches.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/aoti_torch/shim_npu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/TensorFactories.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/DLConvertor.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/from_blob.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/from_blob.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/dlpack.py
  role: implementation
created_at: '2026-11-13T05:24:12Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 外部内存进NPU Tensor：from_blob 工厂契约与 DLPack 入口改路由

## 固定版本与范围

静态审阅 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 `torch_npu/csrc/aten/common/from_blob.cpp`（169 行全文）、`from_blob.h`（113 行全文）与 `torch_npu/utils/dlpack.py`（85 行全文），并定向阅读四个消费者锚点。发布 pin `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 的这三个文件 Git blob 均与主线不同，未逐行比对，版本差异待发布 pin 分区核实。`DLConvertor.cpp` 的 to/fromDLPack dtype 映射与 stride 归一化细节不在本卡（另分区承载），这里只读它对 `from_blob` 的调用锚点。未确认产品与 CANN 配套范围，保持 `draft`、空平台；未导入、运行或创建任何 DLPack 胶囊。存储类方法的产品表见[原生Storage](torch_npu_native_storage_scope.md)，文档层的 DLPack 支持声明见[Tensor元数据卡](torch_npu_native_tensor_layout.md)。

## TensorMaker 的设备一致性与初始化

`TensorMaker::make_tensor()` 是全部七个 `from_blob` 重载的公共落点（from_blob.cpp:95-165）。未显式给 `target_device` 时默认 `PrivateUse1 + c10_npu::current_device()`（:19-21）；`TensorOptions` 携带 device index 时用 `TORCH_CHECK_VALUE` 校验其与数据设备一致，否则报 "Specified device ... does not match device of data ..."（:23-31），随后 `AT_ASSERT` 设备类型必须是 PrivateUse1（:32）并 `maybe_initialize_npu`（:33）。即 from_blob 不做跨设备搬运：指针所在设备与目标设备不一致时直接失败，失败发生在存储构造之前。`NPUGuard` 作用域覆盖后续构造（:37）。

## 所有权与 deleter 的两条路径

传入 `std::function` deleter 时经 `c10::InefficientStdFunctionContext::makeDataPtr(data_, std::move(deleter_), *device_)` 包装（:43-44），释放走宿主侧回调；不传 deleter 时构造空 DataPtr，Tensor 对外部内存不持有所有权（:45-47）。消费者据此分化：AOTI 常量装载、`_weak_ref_tensor` 等走非拥有包装，`fromDLPack` 把 `DLManagedTensor` 的 deleter 包装成 std::function 接管胶囊生命周期（DLConvertor.cpp:290-315）。核对内存归属时应先确认调用点选了哪条路径，而不是按「from_blob」名称统一推断为借用或托管。

## 存储构造、描述符与分配器绑定

存储由 `torch_npu::make_npu_storage_impl(use_byte_size_t, SymInt(size_bytes), data_ptr, allocator, true)` 构造，resizable 固定为 true，随后 `StorageDescHelper::SetDesc` 按 sizes/strides 写 NPU 描述符，再以 `NPUTensorImpl` 建张量并按是否给 strides 走 `set_sizes_and_strides` 或 `set_sizes_contiguous`，storage_offset 最后应用（:49-68）。注意 `TensorMaker` 虽提供 `.allocator()` 链式设置（from_blob.h:33-35），`make_tensor` 从不消费该成员，始终取 `NPUCachingAllocator::get()`（:38）——同一进程内换 allocator 的期望不成立。这与 `Module._construct_storage_from_data_pointer` 的 `make_npu_storage_impl(..., nullptr, false)`（Module.cpp:631-638，空分配器且不可 resize）形成对照：两条外部内存包装路径的生命周期语义不同。workspace 侧的另一构造见[workspace 与 deleter 卡](torch_npu_native_workspace_stream_cache_and_deleters.md)。

## 容量计算与 sizes/strides 边界

`sizes` 先过 `check_size_nonnegative`（:36）。`computeStorageSize` 在给 strides 时用 `at::detail::computeStorageNbytes` 并叠加 `storage_offset*itemsize`（:76-81）；无 strides 时按 `prod(sizes)*itemsize + offset*itemsize` 自行累乘（:84-92），该路径是 size_t 直接乘法，没有独立的上溢检查，超大 sizes 的溢出行为需调用方自行保证。strides 为空数组（而非不传）与不传 strides 都会落入连续分支，但显式传 strides 时不会校验 strides 与 sizes 的语义一致性，只按字节账构造存储。

## Python DLPack 入口的补丁路由

`torch_npu/utils/dlpack.py` 的 `_to_dlpack`/`_from_dlpack` 直接包装 `torch_npu._C._npu_to_dlpack`/`_npu_from_dlpack`，`_from_dlpack` 接受实现 `__dlpack__` 协议的对象或旧式裸胶囊（:8-18）。`_apply_dlpack_patch` 在 torch_npu 导入初始化时经 `torch_npu/_init/patches/api_patches.py` 的 `apply_torch_api_patches()` 安装（api_patches.py:10、16），替换 `torch.utils.dlpack`、`torch.utils` 与 `torch` 三个层面的 `to_dlpack`/`from_dlpack`：`to_dlpack` 仅当 `tensor.device.type == 'npu'` 时改走 `_npu_to_dlpack`，其余张量回原实现（:31-37）；`from_dlpack` 先尝试 `_from_dlpack`，任何异常都整体回退原实现（:44-48）。补丁把替换函数的 `__module__` 改成被补丁模块名以保持内省一致，并把 `to_dlpack`/`from_dlpack` 补进 `torch.__all__`（:36、49、53-85）。失效边界：`from_dlpack` 的 try/except 不区分错误类型，NPU 转换失败（如胶囊 dtype/shape 不受支持）表现为静默落到上游实现，可能随后以不相关的报错浮出；依赖该入口做跨库零拷贝时不能把「未报错」当作「走了 NPU 路线」。何时安装补丁属于 torch_npu 初始化链语义，本卡只固定 `api_patches` 的这一处调用。

## 与文档层支持声明的边界

文档层的 utils.dlpack/torch 页产品表把 `to_dlpack`/`from_dlpack` 列为不支持（见[Tensor元数据卡](torch_npu_native_tensor_layout.md)的 DLPack 清单小节）。源码层面补丁与 C++ 实现存在，说明「文档声明不支持」与「实现路径存在」并存：两者按各自证据层记录，本卡不据补丁存在推导任何跨库胶囊、所有权、流同步或销毁协议已经受支持，也不把文档声明改写为已支持。静态读到的契约以外（真实 DLPack 版本协商、设备同步语义）未验证。

## 消费者锚点

`aoti_torch_create_tensor_from_blob_npu` 在 data 非空时走 from_blob，data 为空（0 尺寸张量）改走 `at::empty_strided`（shim_npu.cpp:41-62）；`_v2` 变体增加 layout 参数，`kMkldnn` 直接拒绝 "do not support mkldnn on npu."，其余转发 `_v1`（:65-93），AOTI 侧消费背景见[静态启动器卡](torch_npu_static_launcher_native_runtime_cpp.md)。`Module._weak_ref_tensor` 用 from_blob 以「存储字节数/元素大小」为 sizes 非拥有重包已有存储指针，再手工回填 sizes/strides/offset 与 `npu_desc_`（Module.cpp:642-654）。`TensorFactories.cpp` 的量化载荷搬运用 `kNoopDeleter` 显式声明非拥有 from_blob 后 `copy_` 并同步（TensorFactories.cpp:95-107）。`DLConvertor.fromDLPack` 按「无 strides（连续，带 deleter 重载）/有 strides」两分支调 from_blob（DLConvertor.cpp:292-315），dtype 映射细节不在本卡。

## Evidence

- [from_blob.cpp](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/from_blob.cpp)（primary）：全文 1-169。
- [from_blob.h](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/from_blob.h)（primary）：全文 1-113。
- [utils/dlpack.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/dlpack.py)（primary）：全文 1-85。
- [api_patches.py 安装点](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/api_patches.py)（implementation）：全文 1-22。
- [Module.cpp 消费锚点](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp)（implementation）：631-654。
- [shim_npu.cpp 消费锚点](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/aoti_torch/shim_npu.cpp)（implementation）：41-93。
- [TensorFactories.cpp 消费锚点](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/TensorFactories.cpp)（implementation）：85-107。
- [DLConvertor.cpp 消费锚点](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/DLConvertor.cpp)（implementation）：290-315。

## 发布 pin 对照（f3ecfe4a）

本节结论来自发布 pin 孪生文件的逐文件比对（比对口径：sha256 → 去空白 → 全空白折叠 token → 注释剥离 token）。

### 等价绑定（结论对发布 pin 直接适用，行号锚不同）

- `torch_npu/utils/dlpack.py`：去空白等价（行尾空白/空行差异）。
- `torch_npu/csrc/aten/common/from_blob.cpp`/`.h`：除整体重排版与包装声明增加 `noexcept` 外，`TensorMaker::make_tensor` 的设备一致性校验、InefficientStdFunctionContext/空 DataPtr 两分支、`NPUCachingAllocator::get()` 固定与 `make_npu_storage_impl` 逻辑逐项一致（主线 169/113 行 → 发布 192/125 行，增量主要为重排版）。本卡契约结论对发布 pin 适用，`noexcept` 只改变包装声明的异常出口，不改变所记录的存储构造语义。

### Evidence（发布 pin 补绑）

- [发布孪生 1](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/from_blob.cpp)（release-twin-binding）：diff 级全文对照（重排版+noexcept）。
- [发布孪生 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/from_blob.h)（release-twin-binding）：diff 级全文对照（重排版+noexcept）。
- [发布孪生 3](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/dlpack.py)（release-twin-binding）：去空白等价。


（本节静态比对，未运行/未编译；结论按文件分列，未列出的文件未比对。）
