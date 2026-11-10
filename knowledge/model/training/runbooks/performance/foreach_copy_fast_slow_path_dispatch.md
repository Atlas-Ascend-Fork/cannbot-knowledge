---
type: Runbook
title: "torch._foreach_copy_ 的 fast/slow path 判别与 host 派发收益边界"
description: "ATen/CUDA foreach copy 的形状限制是 self[i]/src[i] 逐对匹配，不要求列表内所有参数同形；异形 FSDP 参数本身不能判定 slow path。CPU/device offload 因设备不同不满足所读 CUDA fast path 的同设备条件；已进入 slow path 时才有逐对 copy_ 调用，实际 host 收益和 DMA 数需运行测量。"
tags:
  - task.debugging
  - topic.data_movement.data_copy
  - topic.performance.analysis
status: draft
sources:
  - resource: https://github.com/pytorch/pytorch/blob/0fabc3ba44823f257e70ce397d989c8de5e362c1/aten/src/ATen/native/ForeachUtils.h
    role: implementation
created_at: '2026-10-29T11:29:22Z'
updated_at: "2026-11-04T02:06:31Z"
platforms: []
---

# torch._foreach_copy_ 的 fast/slow path 判别与 host 派发收益边界

## 适用场景

- 框架：原轨迹读取 PyTorch ATen/CUDA 0929 快照（版本号未读取）。本次修订另在 PyTorch v2.9.0 固定提交 `0fabc3ba44823f257e70ce397d989c8de5e362c1` 的 ForeachUtils.h 核对辅助函数；该补证不是对原快照版本的确认。
- 语境：CPU offload 训练中用 `torch._foreach_copy_` 实现"host 一次调用下发整个 list 的多 tensor swap"以削减 host-bound 时，判定该接口的真实执行形态与收益上限。
- 证据等级：源码静态观测，非设备验证；torch_npu 侧实现是否与 CUDA 源码同构未核对。

## 触发与观测

- 触发：优化目标为"host上一次就可以下发一个list里面多个tensor的swap，来减少hostbound"（用户原话），需要判定 foreach 单次调用的真实执行形态。
- `torch._foreach_copy_` 的 schema 为 `_foreach_copy_(Tensor(a!)[] self, Tensor[] src, bool non_blocking=False) -> ()`（native_functions.yaml:11707），non_blocking 默认 False。grep 输出逐字（保留行号前缀）：

```text
11707:- func: _foreach_copy_(Tensor(a!)[] self, Tensor[] src, bool non_blocking=False) -> ()
```

## 探针与操作

源码级探针：

1. `grep -n "_foreach_copy_" aten/src/ATen/native/native_functions.yaml` 取 schema 与默认参数；
2. `grep -rn "foreach_tensor_copy_list_kernel" aten/src/ATen/native/` 定位 fast/slow 实现；
3. 读 `ForeachBinaryOpList.cu:409-431`（CUDA fast path 判定）与 `ForeachOpsKernels.cpp:384-393`（slow path）。
4. 继续读被调用的 `_check_tensors_share_sizes_and_strides`，不要只按函数名解释“共享形状”。固定提交中的实现是跨列表、按同一下标逐对检查。

## 机制与判别

- 所读 CUDA fast path 入口要求 self/src 满足同设备等限制、src 与 self 列表各自内部同 dtype，并调用辅助函数检查逐对 sizes/strides；不能据此要求列表内每个张量同形。原轨迹读取的调用点如下（保留行号前缀；辅助函数语义由下文固定提交补证）：

```text
409: void foreach_tensor_copy_list_kernel_cuda_(
410:     TensorList self,
411:     TensorList src,
412:     const bool non_blocking) {
413:   check_foreach_api_restrictions(self, src);
414:   if (!(_check_tensors_share_device_and_dtype(
415:             {self, src}, /* skip_dtype_check */ true) &&
416:         std::all_of(
417:             src.cbegin(),
418:             src.cend(),
419:             [&src](const auto& t) -> bool {
420:               return t.dtype() == src[0].dtype();
421:             }) &&
422:         std::all_of(
423:             self.cbegin(),
424:             self.cend(),
425:             [&self](const auto& t) -> bool {
426:               return t.dtype() == self[0].dtype();
427:             }) &&
428:         _check_tensors_share_sizes_and_strides({self, src}))) {
429:     return at::native::foreach_tensor_copy_list_kernel_slow_(
430:         self, src, non_blocking);
431:   }
```

- slow path（foreach_tensor_copy_list_kernel_slow_，ForeachOpsKernels.cpp:384-393）为 C++ 循环逐对 `self[i].copy_(src[i], non_blocking)`，non_blocking 逐对透传。读取输出逐字（保留行号前缀，自 383 行注释起）：

```text
383: // _foreach_copy_
384: void foreach_tensor_copy_list_kernel_slow_(
385:     TensorList self,
386:     TensorList src,
387:     const bool non_blocking) {
388:   check_foreach_api_restrictions(self, src);
389:
390:   for (const auto i : c10::irange(self.size())) {
391:     self[i].copy_(src[i], non_blocking);
392:   }
393: }
```

- 形状判别：固定提交中的辅助函数对每个 j 比较 `tensorLists[0][j]` 与其他列表的 `[j]`，stride 检查忽略大小为 1 的维度。例如 self/src 各有一个 `[2]` 和一个 `[3,4]` 张量，只要对应项符合条件，列表内部异形本身不会触发该检查失败；是否最终进入 fast path 仍取决于设备、dtype、layout、dense 等其他条件。
- offload 判别：真正的 CPU↔CUDA 拷贝因 self/src 设备不同，不满足此 CUDA 入口的同设备条件；这与同设备 FSDP 参数形状不同是两个问题。torch_npu 的路由需另外核对。
- 收益边界：只有已确认进入所读 slow path，才能从循环推出 N 次 C++ `copy_` 调用。外层一次 foreach 调用可能减少 Python 层逐 tensor 调用开销，但源码调用次数不等于驱动入队数或 DMA 数；实际收益和传输行为须由目标后端 profiler 验证。

## 验证信号

原轨迹为 macOS 本地分析机读取 0929 源码快照，本次补证为固定提交辅助函数复核；以下均为源码观测，没有 CUDA/NPU 运行验证：

- native_functions.yaml:11707：`_foreach_copy_(Tensor(a!)[] self, Tensor[] src, bool non_blocking=False) -> ()`，non_blocking 默认 False（tool_observed，单次）；
- ForeachBinaryOpList.cu:409-431：原轨迹观察到 fast path 条件调用点与 slow path 回退；其中辅助函数的含义须读其实现，不能由调用点推断全列表同形；
- ForeachOpsKernels.cpp:384-393：slow path 逐对 `self[i].copy_(src[i], non_blocking)`、non_blocking 逐对透传（tool_observed，单次）；
- 本次修订补证：固定提交 ForeachUtils.h 的 `_check_tensors_share_sizes_and_strides` 为逐对比较，纠正“异形参数必然 slow path”的旧判断。该检查是源码复核，未执行 CUDA/NPU 性能实验。

未观测：NPU 上 foreach 的实际派发行为与 host 计数（torch_npu 实现未核对）；host 各层 µs 级成本数字无实测。

## 适用与失效边界

- 适用于所读 0929 快照的 ATen/CUDA 源码语义；torch_npu 的 `_foreach_copy_` 是否同构（是否有 fused NPU kernel、slow path 是否同样透传 non_blocking）未核对，跨后端使用前须先在目标后端验证。
- 同设备、各列表内同 dtype 且对应张量 sizes/strides 匹配的组，不能仅因列表内部异形就排除 fast path；还须核对该版本入口的其他条件。
- 一次外层调用不能外推为一条 DMA，也不能证明 DMA 数必然与逐 tensor 调用相同。N 次 `copy_` 的静态结论仅适用于已进入所读 slow path 的情况。
- 本卡不含任何实测性能结论（无 baseline/对比数据）；PyTorch 版本演进可能改变 fast path 条件或 slow path 实现，跨版本使用前须重新核对源码。
