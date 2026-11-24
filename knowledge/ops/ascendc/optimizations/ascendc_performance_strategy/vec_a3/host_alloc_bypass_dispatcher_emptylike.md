---
type: Optimization
title: host 侧输出分配绕过 dispatcher（empty_like/empty_generic 直构 TensorImpl）
description: 用StorageImpl+TensorImpl直接构造输出，替代empty_like/empty的dispatcher分配路径
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-host-alloc-bypass-dispatcher-emptylike.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：host 侧输出分配绕过 dispatcher（empty_like/empty_generic 直构 TensorImpl）

> 单一优化点：自定义 pybind 入口用 StorageImpl+TensorImpl 直接构造输出张量，替代 `at::empty_like`（保形输出）或 `torch::empty`（微小输出）的完整 dispatcher 链，消除 host 固定开销。

## 1. 原理
at::empty_like 走完整 dispatcher 链（BackendSelect → NPU empty → TensorFactory 包装），其中多层 TypePtr/DispatchKeySet 解析与 autograd 包装对纯计算入口是冗余的。直接 StorageImpl+TensorImpl 构造只保留 allocator 调用与最简元数据填充，省 4-6us/次。

## 2. 性能问题模式
- 自定义算子经 pybind（或等效 C++ 入口）调用，输出每次新分配；
- profiling 显示端到端时间 >> kernel 设备时间（host 固定开销主导，端到端 ÷ kernel > 4x）；
- 分段实测 `at::empty_like`/`torch.empty_like` 端到端占比 >15%（本例 6.6us/17us=39%）。

## 3. 正确性红线
- key_set 必须复制自输入 x（含 backend key + autograd key），否则后续 aten 派发异常；
- DataPtr 自带 device，Storage/TensorImpl 的 device 由其推导，勿手填；
- resizable=true 保持 caching allocator 回收语义。

## 4. 泛化条件
- **适用**：可推广至一切单输出自定义入口算子；自定义 pybind/扩展入口可改输出分配路径。含**微小输出**（0/1/常数个元素，如 size/标量 tensor）形态——用 `at::detail::empty_generic(size, allocator, key_set, dtype, nullopt)` 直构。
- **不适用**：算子必须走 dispatcher（需 autograd/require_grad 输出、torch.compile 兼容、out= 复用变体）；多输出/复杂 stride 输出（需走标准 empty 路径保证语义）；无输入 tensor 可借 key_set 的场景；训练态需要 grad 的输出；大输出。

## 5. 实施步骤
1. `#include <torch_npu/csrc/core/npu/NPUCachingAllocator.h>`（torch 侧等价 CUDACachingAllocator）。
2. 构造函数：
   ```cpp
   const int64_t nbytes = x.numel() * x.element_size();
   auto *alloc = c10_npu::NPUCachingAllocator::get();
   auto storage = c10::make_intrusive<c10::StorageImpl>(
       c10::StorageImpl::use_byte_size_t(), nbytes,
       alloc->allocate(nbytes), alloc, /*resizable=*/true);
   auto y = at::detail::make_tensor<c10::TensorImpl>(
       c10::Storage(std::move(storage)), x.key_set(), x.dtype());
   y.unsafeGetTensorImpl()->set_sizes_contiguous(x.sizes());
   ```
3. 以该张量替代 `at::empty_like(x)`。微小输出变体：
   ```cpp
   #include <ATen/EmptyTensor.h>
   auto y = torch::Tensor(at::detail::empty_generic(
       at::IntArrayRef{static_cast<int64_t>(n)},
       x.storage().allocator(),  // NPU allocator from a live NPU tensor
       x.key_set(),              // same dispatch keys as input
       at::kLong, std::nullopt));
   ```

## 6. LLM 前置问题
- 算子输出是否需要 autograd/require_grad 语义或 out= 变体（必须走 dispatcher 时不可用）？
- 是否为多输出或复杂 stride 输出？
- 分段 profiling 是否确认 empty_like 占端到端 >15%？
- 入口是否为自定义 pybind/C++ 扩展，可自由修改输出分配路径？

## 7. 验收标准
- build + 精度全过；实测战绩（910B3）：端到端 17.2-18.5 → 10.0-14.5us；geo_speedup 1.03-1.16 → 1.465-1.701；kernel 设备时间不变（证明收益全部来自 host 分配路径）。微小输出变体：每调用 wall 24.5 → 16.3us（-33%），geo 12.457 → 19.146x，精度 20/20（bit-exact int64）。
- 改动量级：基础策略（host 侧局部改动）。

## 检索卡（短卡）

动作：用StorageImpl+TensorImpl直接构造输出，替代empty_like/empty的dispatcher分配路径
适用：单输出自定义算子，且pybind或扩展入口允许修改输出分配路径
限制：必须复制输入的backend及autograd key_set，否则后续ATen派发异常
范围：单输出pybind/扩展入口，包括0、1或常数元素输出
检索词：StorageImpl、TensorImpl、empty_like、dispatcher、BackendSelect、TensorFactory
机会：pybind/C++入口每次分配输出，且端到端时间明显高于设备kernel时间
