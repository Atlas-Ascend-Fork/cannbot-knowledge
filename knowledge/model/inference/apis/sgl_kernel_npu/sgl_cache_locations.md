---
type: API
title: SGL缓存槽位映射的打包写入与读出接口
description: 区分cache_loc_assign与update的读写方向、返回别名和16槽位限制，并核对预取存储、UB计费及CANN9.1.0减法重载证据。
tags:
- task.implementation
- topic.kv_cache
- topic.memory
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/cache_locations.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/mem_cache/cache_locations/op_host/cache_loc_host.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/mem_cache/cache_locations/op_kernel/cache_loc_kernel.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/mem_cache/cache_locations/op_kernel/cache_loc_tiling.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/common.h
  role: supporting
- resource: https://gitcode.com/cann/asc-devkit/blob/e5451c7feba11f9e259f4fbc19c4bf82f8c0496c/include/basic_api/kernel_tensor.h
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/e5451c7feba11f9e259f4fbc19c4bf82f8c0496c/impl/basic_api/kernel_tensor_impl.h
  role: implementation
- resource: https://gitcode.com/cann/asc-devkit/blob/e5451c7feba11f9e259f4fbc19c4bf82f8c0496c/impl/basic_api/kernel_operator_symbol_override_impl.h
  role: implementation
- resource: https://gitcode.com/cann/asc-devkit/blob/e5451c7feba11f9e259f4fbc19c4bf82f8c0496c/version.cmake
  role: supporting
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- a2
- a3
- '950'
aliases:
- cache_loc_assign
- cache_loc_update
---

# SGL缓存槽位映射的打包写入与读出接口

## 调用入口

```python
from sgl_kernel_npu.operators.mem_cache import cache_loc_assign, cache_loc_update

def cache_loc_assign(req_pool_indices, token_pool, start_offset, end_offset, out_cache_loc, *, impl="auto"): ...
def cache_loc_update(req_pool_indices, token_pool, start_offset, end_offset, out_cache_loc, *, impl="auto"): ...
```

## 方向与打包

每个请求i对应 `token_pool[req_pool_indices[i],start_offset[i]:end_offset[i]]`，各段依请求顺序拼成紧密缓冲，空段不占空间。

| 接口 | 读取 | 写入及返回别名 |
| --- | --- | --- |
| cache_loc_assign | out_cache_loc里的打包槽位 | token_pool；返回与表共享存储的Tensor。 |
| cache_loc_update | token_pool指定各段 | out_cache_loc；返回与该缓冲共享存储的Tensor。 |

token_pool为同NPU稠密int32二维表，out_cache_loc为连续int32任意shape、按一维访问，元素数至少为各段长度和。req_pool_indices `[B]` 使用int32/int64且行号互异；start/end为int64 `[B]`；req_pool_indices、start_offset、end_offset三个索引向量均须稠密连续，只有[B]形状不足以满足存储合同；end>=start，区间及行号有效，表与打包缓冲不能重叠。

## 原生实现边界与验证

auto选择ascendc，不自动选参考。AscendC每个区间最多16个槽位；从实际起始列向后必须有可读16元素的物理空间。非空Assign还会读后按64字节写回整个16元素窗口，故完整窗口必须可读写且不同核的窗口互不重叠；应保证窗口完全落在各自行内，或独立证明物理写窗口互斥。行号互异不足以保证互斥，例如pool[3,8]的row0/row1从列0开始时，两个有效16项窗口仍重叠。此跨核Assign限制不推广到单核Update。批量和打包长度还受片上容量限制，不能把PyTorch参考能处理长段解释为原生支持长段。

用独立状态分别验证assign再update的往返，检查目标区间外表值和打包尾部哨兵未变；直接比较data_ptr确认别名。覆盖空段、单槽位、16槽位边界及行号选择，不能只根据名称推断方向。

## 源码补充的容量与证据边界

两个方向共用 `CacheLocAssignKernel<T>::PreProcess`：`ProcessForTokenPoolAssign` 与 `ProcessForCacheUpdate` 均调用它，int32/int64行索引两种实例也没有绕过该步骤。除每段固定16元素访问外，PreProcess还用普通DataCopy按向上对齐后的元素数预取整批行号、start/end和整个打包缓冲。因此metadata与打包缓冲的实际storage也须覆盖对应的32字节补齐读取；仅逻辑shape满足B项或打包长度S项，不证明物理补齐区可访问。`cacheLocSize`取逻辑视图的元素数S，不取背后allocation大小。

容量检查与Device真实申请须分开。设 `align32(x)` 表示按字节向上补齐32，`B` 为请求数、`S` 为打包缓冲逻辑元素数；令 `R=align32(4B)`、`O=align32(8B)`、`L=align32(4S)`。以下公式限定B进入Device的uint32成员未截断，且对齐、乘加及InitBuffer参数转换均未溢出或窄化：

```text
Host UB guard = 64 + 3O + 12B + L
Device申请量 = Rreq + 2O + 3R + L + 2*64
Rreq = R（int32行号）或 O（int64行号）
```

Device式按[InitBuffer的32字节补齐契约](../../../../ops/ascendc/apis/simd_api/basic_api/resource_management/t_pipe/init_buffer.md)逐块计费，包含七个TBuf和深度2的64字节token队列，没有扣除未经证明的别名。int64行号路线的两式差为 `64+3*(R-4B)>=64` 字节；因此Host guard通过不等于真实UB需求已获覆盖。该结论是固定源码申请量的静态推导，不是实际内存分配失败或性能观测，也不应推广成int32路线恒有同一差值。

前缀结果依赖SDK的运算符重载。`PreProcess`把start/end转换为int32 LocalTensor后执行`ubCacheLength = ubEndOffsetInt32 - ubStartOffsetInt32`，`GetCacheIdx`再累计其元素定位各段打包起点。单独的SGL固定仓没有该重载实现；补充核对官方asc-devkit **v9.1.0**固定提交`e5451c7feba11f9e259f4fbc19c4bf82f8c0496c`后，`kernel_tensor.h`声明减法返回`SymbolOverrideSub<T>`，`kernel_tensor_impl.h`将赋值转发到`Process(dst)`；`SymbolOverrideSub::Process`实际调用`SubImpl(dst.GetPhyAddr(),src0.GetPhyAddr(),src1.GetPhyAddr(),dst.GetSize())`。因此在这套固定SDK源码中是向既有目标地址写逐元素差值，计算长度取目标LocalTensor的GetSize，不能理解为把目标视图简单重绑到某个地址差。

上述官方版本由同提交`version.cmake`声明9.1.0。这补齐了先前的重载来源缺口，但不证明任意名为9.1.0的二进制SDK都与该源码逐字相同，也不替代Cast/Sub与Scalar消费者的同步、padding及容量检查。本卡只保存接口合同与这项已读补充证据；完整Operator闭包另行按固定SGL+SDK来源分析，没有用PyTorch参考替代原生实现，更没有执行编译或设备复现。

## 固定来源与验证状态

- [mem_cache/cache_locations.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/mem_cache/cache_locations.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
