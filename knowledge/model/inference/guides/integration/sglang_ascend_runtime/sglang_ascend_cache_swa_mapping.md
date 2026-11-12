---
type: Guide
title: SGLang NPU滑窗KV映射的分配、清除与释放顺序
description: 说明NPU分页分配器、decode scatter映射、is_cuda兼容别名规避、SWA先释放和请求ring不返还分页空闲池的边界。
tags:
- task.implementation
- topic.kv_cache
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/allocator/swa.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/allocator_npu.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/allocator/paged.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/base_prefix_cache.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/common.py
  role: supporting
created_at: '2026-11-08T12:20:19Z'
updated_at: '2026-11-08T12:27:46Z'
platforms: []
---

# SGLang NPU滑窗KV映射的分配、清除与释放顺序

page_size>1时优先平台get_paged_allocator_cls，否则NPU用NPUPagedTokenToKVPoolAllocator，FULL与SWA分配器分开。full_to_swa映射用int64，零为padding，末尾-1处理无prefix的last_loc。decode两边都分配成功才更新映射，NPU用int64列索引的npu_scatter_nd_update_；返回FULL位置给上层。

free不是幂等接口，必须先free_swa再free_full，因为SWA依赖当前映射，后续缓存操作可能重指同一FULL槽。NPU clear mapping用直接赋0，避免当前aclnnIndexFill开销；这属于后端实现选择，不可推广为CUDA同样更快。

_free_swa_pages要求start_pos页对齐，从每页代表位置取得映射。只有非NPU且Tensor.is_cuda才用CUDA专门路径，因为transfer_to_npu会把is_cuda别名到is_npu。NPU走非CUDA逻辑，检查peer映射后转换页号并清除映射；分组释放先保存解析后的值，不延后读取可能已经改写的映射。

每请求SWA ring槽属于request，不从分页池借，free_swa/free_swa_segment不向分页空闲列表返还；可用增长容量由FULL限制，ring成本按request slots计量。混淆两种所有权会虚增available_size甚至重复分配。

验证分配-命中-淘汰-重取-请求结束的完整序列，覆盖padding、组内重映射、页切边界和ring；检查slot/page单位、计数上界与输出精度。已有[is_cuda误分派规则](/model/inference/optimizations/anti_patterns/npu_tensor_is_cuda_not_cuda_npu_discriminant.md)解释通用原因，本卡限定当前SGLang释放实现。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
