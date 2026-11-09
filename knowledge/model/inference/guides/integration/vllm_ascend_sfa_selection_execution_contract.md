---
type: Guide
title: vLLM Ascend SFA与Selection缓存：长度前缀、数值流水和驻留更新
description: 串接普通SparseFlashAttention与fused_sparse_attention_overlap的Host、两架构Device及Torch入口，核对512+64分离RoPE、B项TND累积长度、max/sum输出、有效稀疏前缀、驻留TopK/membership计划和原地缓存的发布顺序。 补packed C8/FP8的528/656字节行、672字节UB跨距、四FP32
  scale、NoPE内部补零和统计量声明差异。 补DRAM至HBM首填/稳态融合搬运、MTP1至16路、设备端路径切换与持久缓存写回的所有权边界。 3164固定增量补NoPE512编译特化、544字节UB行、A5向量物理地址表与arch22自适应页窗口、三槽搬运及空query初始化。
tags:
- task.implementation
- task.debugging
- topic.attention
- topic.kv_cache
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_sparse_attention_overlap/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_sparse_attention_overlap/README.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_sparse_attention_overlap/fused_sparse_attention_overlap_torch_adpt.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_sparse_attention_overlap/op_host/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_sparse_attention_overlap/op_host/fused_sparse_attention_overlap_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_sparse_attention_overlap/op_host/fused_sparse_attention_overlap_proto.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_sparse_attention_overlap/op_host/fused_sparse_attention_overlap_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_sparse_attention_overlap/op_host/fused_sparse_attention_overlap_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_sparse_attention_overlap/op_kernel/arch22/fused_sparse_attention_overlap_kernel_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_sparse_attention_overlap/op_kernel/arch22/fused_sparse_attention_overlap_service_cube_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_sparse_attention_overlap/op_kernel/arch22/fused_sparse_attention_overlap_service_vector_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_sparse_attention_overlap/op_kernel/arch35/fused_sparse_attention_overlap_common_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_sparse_attention_overlap/op_kernel/arch35/fused_sparse_attention_overlap_kernel_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_sparse_attention_overlap/op_kernel/arch35/fused_sparse_attention_overlap_kvcache.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_sparse_attention_overlap/op_kernel/arch35/fused_sparse_attention_overlap_service_cube_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_sparse_attention_overlap/op_kernel/arch35/fused_sparse_attention_overlap_service_vector_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_sparse_attention_overlap/op_kernel/arch35/util_regbase.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_sparse_attention_overlap/op_kernel/fused_sparse_attention_overlap.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_sparse_attention_overlap/op_kernel/fused_sparse_attention_overlap_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_sparse_attention_overlap/op_kernel/fused_sparse_attention_overlap_template_tiling_key.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/README.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/docs/aclnnSparseFlashAttention.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/examples/test_aclnn_sparse_flash_attention.cpp
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/op_host/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/op_host/op_api/aclnn_sparse_flash_attention.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/op_host/op_api/aclnn_sparse_flash_attention.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/op_host/sparse_flash_attention_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/op_host/sparse_flash_attention_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/op_host/sparse_flash_attention_tiling.cpp
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/op_host/sparse_flash_attention_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/op_kernel/arch22/sparse_flash_attention_kernel_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/op_kernel/arch22/sparse_flash_attention_service_cube_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/op_kernel/arch22/sparse_flash_attention_service_vector_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_common_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_kernel_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_kvcache.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_service_cube_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_service_vector_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/op_kernel/arch35/util_regbase.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/op_kernel/sparse_flash_attention.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/op_kernel/sparse_flash_attention_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/op_kernel/sparse_flash_attention_template_tiling_key.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_flash_attention/sparse_flash_attention_torch_adpt.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_flash_attention_vllm/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_flash_attention_vllm/README.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_flash_attention_vllm/kv_quant_sparse_flash_attention_vllm_torch_adpt.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_host/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_host/kv_quant_sparse_flash_attention_vllm_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_host/kv_quant_sparse_flash_attention_vllm_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_host/kv_quant_sparse_flash_attention_vllm_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_host/kv_quant_sparse_flash_attention_vllm_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_kernel/arch35/kv_quant_sparse_flash_attention_vllm_common_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_kernel/arch35/kv_quant_sparse_flash_attention_vllm_kernel_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_kernel/arch35/kv_quant_sparse_flash_attention_vllm_kvcache.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_kernel/arch35/kv_quant_sparse_flash_attention_vllm_service_cube_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_kernel/arch35/kv_quant_sparse_flash_attention_vllm_service_vector_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_kernel/kv_quant_sparse_flash_attention_vllm.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_kernel/kv_quant_sparse_flash_attention_vllm_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_kernel/kv_quant_sparse_flash_attention_vllm_kernel_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_kernel/kv_quant_sparse_flash_attention_vllm_service_cube_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_kernel/kv_quant_sparse_flash_attention_vllm_service_vector_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_kernel/kv_quant_sparse_flash_attention_vllm_template_tiling_key.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_scatter_copy_sparse_flash_attention/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_scatter_copy_sparse_flash_attention/README.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_scatter_copy_sparse_flash_attention/fused_scatter_copy_sparse_flash_attention_torch_adpt.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_scatter_copy_sparse_flash_attention/op_host/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_scatter_copy_sparse_flash_attention/op_host/fused_scatter_copy_sparse_flash_attention_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_scatter_copy_sparse_flash_attention/op_host/fused_scatter_copy_sparse_flash_attention_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_scatter_copy_sparse_flash_attention/op_host/fused_scatter_copy_sparse_flash_attention_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_scatter_copy_sparse_flash_attention/op_host/fused_scatter_copy_sparse_flash_attention_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_scatter_copy_sparse_flash_attention/op_host/fused_scatter_copy_sparse_flash_attention_tiling_impl.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_scatter_copy_sparse_flash_attention/op_host/fused_scatter_copy_sparse_flash_attention_tiling_impl.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_scatter_copy_sparse_flash_attention/op_host/op_api/aclnn_fused_scatter_copy_sparse_flash_attention.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_scatter_copy_sparse_flash_attention/op_host/op_api/aclnn_fused_scatter_copy_sparse_flash_attention.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_scatter_copy_sparse_flash_attention/op_kernel/first_fill_scatter_copy_kernel.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_scatter_copy_sparse_flash_attention/op_kernel/fused_scatter_copy_sparse_flash_attention.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_scatter_copy_sparse_flash_attention/op_kernel/sparse_flash_attention_impl/fused_scatter_copy_sparse_flash_attention_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_scatter_copy_sparse_flash_attention/op_kernel/sparse_flash_attention_impl/fused_scatter_copy_sparse_flash_attention_kernel_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_scatter_copy_sparse_flash_attention/op_kernel/sparse_flash_attention_impl/fused_scatter_copy_sparse_flash_attention_service_cube_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_scatter_copy_sparse_flash_attention/op_kernel/sparse_flash_attention_impl/fused_scatter_copy_sparse_flash_attention_service_vector_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_scatter_copy_sparse_flash_attention/op_kernel/sparse_flash_attention_impl/fused_scatter_copy_sparse_flash_attention_template_tiling_key.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_host/kv_quant_sparse_flash_attention_vllm_tiling.cpp
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_kernel/arch35/kv_quant_sparse_flash_attention_vllm_common_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_kernel/arch35/kv_quant_sparse_flash_attention_vllm_kernel_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_kernel/arch35/kv_quant_sparse_flash_attention_vllm_service_cube_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_kernel/arch35/kv_quant_sparse_flash_attention_vllm_service_vector_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_kernel/arch35/qsfa_a5_address_precompute.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_kernel/kv_quant_sparse_flash_attention_vllm.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_kernel/kv_quant_sparse_flash_attention_vllm_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_kernel/kv_quant_sparse_flash_attention_vllm_kernel_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_kernel/kv_quant_sparse_flash_attention_vllm_service_cube_mla.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/csrc/attention/kv_quant_sparse_flash_attention_vllm/op_kernel/kv_quant_sparse_flash_attention_vllm_service_vector_mla.h
  role: implementation
created_at: '2026-11-03T06:21:07Z'
updated_at: '2026-11-03T06:25:08Z'
platforms: []
aliases:
- npu_sparse_flash_attention
- npu_fused_sparse_attention_overlap
- RunAllCoreSelectionUpdate
- ProcessSetResidentSelectionRow
- PrepareExternalSelectionPlan
- BuildSetResidentSelectionPlan
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend SFA与Selection缓存：长度前缀、数值流水和驻留更新

## 适用任务与证据范围

固定Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2。本卡聚合普通SFA与Selection缓存重叠两族44来源的Host/API/推形、Torch adapter、arch22/arch35完整程序及文档语义。代码按完整去注释结构投影阅读；相同实现先阅读基线再核全部差异，类名与族名归一只用于定位复用程序，不消除真实分支。README原文与API HTML/空白投影分别记录，不把程序投影称为原始全文。

真实主题检索的相邻入口为[SparseMLA](vllm_ascend_sparse_mla_host_dispatch_contract.md)、[SparseAttentionScore](vllm_ascend_sparse_attention_score_host_contract.md)、[量化KV](vllm_ascend_kv_quant_format_contract.md)与[分层offload](vllm_ascend_sparse_layerwise_offload.md)；它们分别维护另一组输入ABI、索引布局、量化格式和传输控制。这里补普通SFA及驻留Selection执行语义，不能用相似名字替换实际算子。没有执行上游、UT、编译或NPU，不给平台、全模型、数值或性能verified结论。

## Host允许矩阵与编译键取交集

| 入口 | 输入与Host门禁 | 真正编译/消费的边界 |
|---|---|---|
| 普通SFA | query BSND/TND，KV可同layout或PA_BSND；FP16/BF16，NoPE/V维512；MLA attention_mode=2；KV heads1，G为1..64或128 | arch22支持分块稀疏、可不带RoPE；arch35要求独立64维query/key RoPE，sparse_block_size只能1 |
| Selection overlap | Torch将query最后轴分为512 NoPE及64 RoPE，以full KV作为key且value别名同key | 固定模板仅FLASH_DECODE=0、TND、PA_BSND、V_TEMPLATE、IS_SPLIT_G=0；不能将Host较宽shape枚举当编译支持 |

普通SFA sparse_block_size须为[1,128]二次幂；PA页大小为16倍数且<=1024，并可被稀疏块大小整除。sparse_mode只0或右下causal 3，pre/next_tokens仅INT64_MAX。Host根据稀疏块<=4选择V_TEMPLATE，否则C_TEMPLATE；zero S2的局部替换1024不代表Torch接受空KV，Torch先拒绝query/key/value/indices的numel=0。

普通OpDef的AutoContiguous意味着可能整理/复制输入，不支持随意用非连续页view保留原写端与图地址。它不同于SparseMLA的IgnoreContiguous+真实page-stride合同。本族Device地址按连续页大小与维度乘积计算，不能直接搬入有padding的跨组件cache视图。

文档宣称A2/A3/950和图模式支持，源码架构只接DAV_2201/DAV_3510；这是声明及静态分支，没有当前设备运行证据。README有RoPE layout文字错位、heads离散枚举等差异，以具体Host检查与当前模板交集作适配输入，而不是放宽其中任一层。

## B项累积长度与输出统计量

普通SFA的TND长度是B项累积末值，不含前导0。batch数从query长度tensor元素数取；第0请求用length[0]，后续用相邻差和前一项作offset。它不同于SparseMLA的B+1 cu_seqlens协议。PA KV长度是每请求实际长度；TND KV也是B项累积末值。Host主要检查存在性、dtype与容量，没有遍历每个值证明单调、末值、页容量与全部索引合法，caller负责这些值域。

Torch返回attention、softmax_max、softmax_sum三项；return_softmax_lse只是该开关的名字。True时统计量FP32，BSND轴[B,Nkv,S,G]，TND轴[Nkv,T,G]；False时两个空tensor。它们是max与sum，不是已经相加得到的logsumexp，跨rank合并仍需`max+log(sum)`及相应权重。arch35代码逐项输出该max/sum，不继承SparseMLA单LSE输出约定。

API wrapper在False且两统计量都nullptr时创建临时TensorHolder；固定实现的holder局部作用域在调用InnerGetWorkspaceSize之前结束，留下需要SDK/实际调用确认的描述符寿命风险。Torch路径本身传真实空tensor，不能把它与裸nullptr路径视为同一验收证据。样例又使用float Host缓冲构建FP16 tensor、给不同输出示意shape；样例不是golden，也未在本次执行。

## 两架构的数值与缓冲流水

arch22按query行分核、3份RunInfo预取/排空，S2基础块通常512。V_TEMPLATE将所选token的NoPE/RoPE搬入四槽GM工作区，并分别保存两AIV搬运的有效数量；无效尾部清零后还需把对应QK列置为负大值，不能认为KV零值本身就是softmax mask。C_TEMPLATE通过TopK块游标和块内offset直接做分页/连续搬运；稀疏块ID乘sparse_block_size才是token坐标，取不到数据的causal前缀单独输出0。

arch22不仅做通用在线softmax：AmlaVecCompute按max与ln2构造指数修正、量化到KV dtype，保留系数和末轮分母；另一路将指数变化乘8388608并转INT32，对MM2共享存储做原子整数加，Cube再配合FP32原子累加。首轮有特定bias位型初始化，后续syncV1NupdateC2/C2V1顺序保护读写。最终把绝对值>1e10等不满足比较的中间结果选0，再除Amla分母并cast。移植时不能把这些原子/同步删掉当作普通FP32 sum，也不把该截断当作所有NaN/Inf已数值正确。

arch35以64×128块运行，NoPE512与RoPE64拼成576维QK，BMM2仍输出512。Q一个L1槽，KV三槽，P复用L1，BMM1双UB槽/BMM2单槽，gather三GM槽；split-G共享gather槽但不同半head消费。三份RunInfo、PRELOAD_NUM=2，末尾排空和无负载核的flag15配对不可省略。Host只传FLASH_DECODE=0且splitKVFlag初始False，本族存在FD辅助字段/潜在代码不证明启用了通用S2分核FD。

arch35的Vec搬运实际拼key的NoPE与key_rope，BMM2从该NoPE区域取值；虽然接口有独立value且Host核shape/dtype，不能据此认定任意不同key/value值在该MLA-absorb路径被分别消费。实际模型通常用共享latent；接入非共享V的新模型必须沿消费点检查并做数值验收。

## 稀疏有效前缀与分页安全

所有调用者须给有效非负前缀、后跟负padding，不支持任意内部空洞。arch22 C_TEMPLATE在-1停止并维护TopK块内游标；arch35部分路径用二分查找首个负值，搬运可在成对-1时结束。正ID、物理block ID、实际KV长度与块表容量仍必须由producer约束，局部负值检查不等于通用越界保护。

arch22 V_TEMPLATE的页取址可核token阈值并组合相邻搬运；跨页、过大/负stride、尾部超出causal范围时回退单份搬运。arch35配对搬运先算物理页再拼576维暂存，快速路径与尾部路径检查不同。适配Agent应保存逻辑token ID、稀疏槽、block-table页号和元素offset四种单位，不能将一份TopK工作区直接当紧凑KV页。

## Selection缓存：身份、命中与发布

overlap Torch helper要求selection_topk_block_size=1；TopK 3D直接使用或contiguous，4D展平为[T,Nkv,K]。它可能新分配query实际长度ones与selection实际长度；只有提供的full_q_actual_seq元素数恰等于query首维且连续时才复用。因此不要用该便捷helper隐含支持任意prefill批坐标。单row、status连续且容量足够时，selection实际长度直接别名status的第K槽，生命周期与状态存储绑定。

arch22内部驻留planner只在PA、V_TEMPLATE、两稀疏粒度1、0<K<=2048、页与容量为正、status至少K+1、membership至少16400项时进入。status记录每槽token ID及尾部有效数量；membership用16376项token→slot映射，加对齐和8个控制项。状态身份是当前请求/逻辑row/页映射，不是shape相同即可跨请求复用。

先探测前4项，再比较全行可判同位置全命中；集合命中还要求前次有效数等于K、可见KV长度处于map容量内、ready marker正确，并检查全部成员。否则排序当前TopK与驻留status，优先保留同row槽，再找同group其他KV-head的来源，分配可替换槽。存在INT32→FP32排序/比较步骤，token大值的精确性不能从INT32接口自动推得；超map容量的fallback与数值精确范围需真实数据验收。

小更新阈值64：普通小miss可同步从full cache复制；在map可保留、有效数仍满K等条件下可发布稀疏更新计划；大更新写紧凑计划再由gather消费。紧凑INT16正值表示命中slot+1，负值表示待更新目标slot的负编码，0表示无效；稀疏计划改为destination+1/token+1成对值。两者不是同一种数组格式。status可先写，实际数据仍由后续CopyOutSelectionUpdateFromKvMerge更新，所以仅观察status/actual_seq不能证明cache数据已经就绪。

Process先让全部AIV执行RunAllCoreSelectionUpdate，再SyncAll<false>，之后进入Attention流水；循环内先gather并发出syncV0C1，再处理Selection回写。复用该buffer到另一stream/图回放前仍需外部依赖，不能用某个单核marker取代全调用完成。cache页、status和membership都是原地输入，OpDef AutoContiguous与真实allocator/注册地址必须对应；复制后的临时输入是否能承担预期原地副作用需沿框架调用确认。

## External Plan与arch35区别

arch22可按external marker读另一physical row、direct row stride及paired-copy标志。命中槽来自计划，未命中从Full cache加载，回写还要修正物理页顺序造成的配对源次序；直接把TopK顺序当KV暂存顺序可能写错槽。内部map ready、普通plan、稀疏plan、external plan是不同状态，复用前应清理/刷新实际控制字段，不能只改一个ready位。

arch35不运行arch22那套完整驻留planner。它仅在external marker、计划覆盖当前chunk、非负offset且总范围不超过16384控制边界时消费外部计划；正命中slot无法取到有效Selection地址时退回Full读取并将对应计划改负，随后回写miss。缺失或非法external计划走普通Full gather，不等于已经同步更新完整驻留map。README把该族统一描述为Selection更新，不能据此为两架构套相同内部状态机。

适配时分别保存实际族/arch/key、TopK前缀、full与selection页表、status尾计数、map容量/marker/计划格式、所有输入的地址与别名，再验证首次miss、全命中、顺序变化同集合、<=64/>64更新、可见长度跨16376、空工作、连续请求与图刷新。当前未执行这些场景；性能优化应先证明状态与输出正确，再测planner、gather及Attention重叠收益。


## Packed C8/FP8变体：格式与选路

继续阅读KvQuantSparseFlashAttentionVllm余19来源的完整程序/README，复用前述SFA与[量化SharedKV](vllm_ascend_sharedkv_metadata_contract.md)已读程序再审全部新差异。它的query在一份tensor中拼NoPE与可选RoPE，KV把scale放入每行，不能套用普通SFA的独立RoPE输入，也不能套另一族448维NoPE+E8M0 scale。有效V来自反量化后的512维NoPE，输出始终512；独立value参数/scale保留字段不是已经证明任意独立V被消费。

| rope_head_dim | query末轴，16位元素 | packed KV每行，8位元素/字节 | 四FP32 scale起点 |
|---|---|---|---|
| 0 | 512 | 528=512量化NoPE+16 scale | 512字节 |
| 64 | 576 | 656=512量化NoPE+128 RoPE+16 scale | 640字节 |

每128个NoPE值共享一个FP32 scale，共四个；量化只覆盖NoPE。Host要求key/value quant mode=2、combine mode=1、tile_size=128、MLA attention_mode=2、RoPE维0/64，不能接受OpDef某些默认mode=1/0代替真实必要参数。A2/A3仅INT8，heads为1/2/4/8/16/32/64/128、稀疏块1/2/4/8/16；950另收E4M3FN/HiFloat8与G=48，稀疏块只能1，HiFloat8固定TopK2048且保留RoPE64。无分页时Q/KV layout需一致，分页页大小仍16对齐、<=1024并可被稀疏块整除。编译只选V_TEMPLATE/FLASH_DECODE=0；C_TEMPLATE和FD潜在实现不扩大可达矩阵。

## C8反量化与缓冲复用

arch22先聚合packed行，INT8→FP16→FP32，再乘行内四个FP32 scale，按BF16 CAST_RINT或FP16 CAST_ROUND回到计算dtype，转NZ写四槽KV merge GM。RoPE数据单独按16位视图取出；RoPE0时内部64维区域补零，query搬入L1也补零，保留原576维QK分块而非要求caller伪造64维输入。该路径不使用前述普通SFA的AMLA整数指数修正，改用显式在线softmax max/sum/exp与FP32 partial输出缓存，末轮除sum；两实现不能仅按函数同名交换原子/同步步骤。

arch35 packed GM步幅按528/656实际行长，搬入UB仍保留672字节跨距；每轮NoPE量化数据与scale都用该UB步幅，scale起点按实际packed尾16字节算。INT8先转half再FP32，FP8按相应类型cast，再乘FP32 scale并回计算dtype。NoPE0的RoPE UB区与query NZ区都主动清零，避免上一请求残留；外部QK scale_value仍由caller给定，不随去掉RoPE自动重算。

非split-G的arch35直接把反量化KV写L1，split-G才通过三槽GM共享后拷入L1，因此Host仅G>64额外分配该gather GM不是漏配的直接证据。L1/UB/GM阶段、逻辑分核和实际输入行长仍须一起核对，不能按一个全局“672”决定allocator页大小。block-table、TopK与B项累积长度合同继续适用；正索引/物理页容量不因支持量化就得到通用验证。

## 声明与实现的窄差异

固定Host头将KEY_DEQUANT_SCALE_INPUT_INDEX和VALUE_DEQUANT_SCALE_INPUT_INDEX都写为3，实际是sparse_indices输入序号；检查只借这些局部tensor指针判存在，Device反量化实际读取行内scale。将文档“预留scale参数”接成独立scale方案前，必须核该索引及实际消费，不把此存在性检查当独立scale已校验。

README写950只应False、不返回统计量；同一固定Device代码却在returnSoftmaxLse时初始化并写出softmax_max/sum，query输出轴也由推形/adapter生成。保留文档与代码差异，不能以静态分支就宣称950 LSE已通过；非950也需检查有效query、空/全mask和packed key/value实际语义。Host错误日志还存在从query长度desc取KV错误dtype信息的分支，诊断应保存原输入描述，避免只照报错文案换错tensor。

量化新模型先核全局/当前层RoPE配置是否一致、页allocator按真实528/656字节布局、scale是FP32原字节而非数值转换后的8位量、slot/page/TopK身份与有效长度，再分INT8/E4M3FN/HiFloat8、RoPE0/64和返回统计量做独立参考验收。源码README提到测试入口和图用例只作为待执行路线，本次未运行，不把紧凑输入与零RoPE的等价或图性能描述为本次测量结果。

## 融合卸载搬运：首填和稳态是不同事务

FusedScatterCopySparseFlashAttention新增19份来源沿同族完整程序对照，入口只编译TND/PA_BSND/V、FLASH_DECODE=0，Host注册910B/910_93；README也只声明A2/A3。本节不外推950或任意稀疏Attention。它把DRAM读、HBM持久写回和Attention合进一次调用，和前文Selection/membership计划不是同一个状态机。

Torch入口固定NoPE512、RoPE64、KV head1、页128、TopK2048，Q heads8/16/32/64/128；query为[T,N,512]，RoPE[T,N,64]，B>0且B<=T<=16B。B项query累计终点须形成每请求1..16行的严格递增分段、末项=T；第r行可见KV为该请求最后一行KV长度减去剩余未来query行数。TopK槽/source是[T,1,2048]，逐行miss前缀长度[T]；首次填充清单是[B,32768]的source/destination及[B]有效计数，不能把两种前缀混用。HBM缓存[blocks,128,1,512/64]、DRAM源[blocks,128,512/64]，所有metadata INT32，所有浮点同为FP16或BF16，输出预分配且同query形状；接口返回None并原地改HBM。

除DRAM两源外需同NPU/连续；DRAM源可为同NPU或已注册、设备可寻址的连续CPU view。Torch仅检查CPU/NPU与连续性，普通CPU tensor通过这一局部判断不代表完成了Host注册。Host parser后直接做fused检查与DoOpTiling；类内另有只收T=B/4B的CheckDecodeOnly，但该包装入口不调用其checker，不能把它当当前有效MTP限制。Host强制key=1并在通用tiling结构后追加copyCap/missCap/HBM与DRAM列数四个uint32；相同前缀结构不构成ABI可互换证明。

## 设备选路、同步与持久写回

任一请求miss_counts>=num_cache_tokens，就令整个batch走first-fill；cache_tokens=0且miss=0也满足该条件。AIV按每请求有效清单搬运，所有参与核随后SyncAll<false>，AIV Reset pipe，才运行非source-aware Attention。稳态则走source-aware gather，每query TopK前缀从DRAM读取并写指定HBM slot，后缀从HBM读取，同时把数据送入Attention的四槽GM merge缓冲。该分支选择在Device读metadata，不能以capture时走稳态就假定replay永远同路径，也不能在同步完成前复用页表/清单/注册Host存储。

First-fill以512+64个16位值为一行、双队列预读，按逻辑token/slot右移7查DRAM/HBM页表。它检查活动ID非负、逻辑列范围及物理页号非负，未证明物理页号小于实际分配页数。运行时跳过非法项不具备回滚语义，其他项可能已经写入；caller还必须保证目的slot唯一或写入一致、源/目的生命周期与图地址稳定，失败后不能仅保留旧membership就继续服务。

Attention的缓存语义是：cache_tokens=0时只计算连续可见tail；cache_tokens>=2048且<=visibleKV时计算2048个稀疏slot加[cache_tokens,visibleKV) tail；其余关系落入无有效范围，不能当通用小TopK实现。TopK的-1会终止当前有效前缀，不能在中间放洞期待后续仍被消费。source-aware路径按512 token tile、32行gather、两UB bank组织；miss存在时默认按batch/query相位错开四个tile，NANOVLLM_SFA_CANONICAL_SOURCE_TILES宏可关闭该重排。该顺序优化不改变caller提供的slot/source配对。

持久写回复用已读取的UB行，打包保存物理destination offset与5位UB行号；可将有序相邻两行合并为一次两块搬运。事件保证本地预读/写回缓冲复用，但跨query/core对同一持久slot的写入仍需要上层协议。tail按页边界连续搬运；MTP可见长度、cache容量与slot映射必须同时一致，不能只验证最终HBM包含某token。头文件还保留stage1/stage2 P/M/L合并程序，但公开entry只实例化normal stage，不能据模板存在就宣称公开支持两阶段调用。

新模型/性能Agent应先分别验首次填充、稳态全命中/全miss/混合、同batch单请求触发全batch首填、异构1..16行与跨页tail，再验图内metadata切换、重复slot和失效注册内存处理。README的测试入口和典型时延是来源提供的特定910_93/BF16配置信息，本次未运行，不作为可移植性能阈值或硬件通过证据。

## 固定3164增量：NoPE编译特化与地址预计算

本节仅比较ceac→3164adc8fe75892fbf7f99f524bb72fddf1e6efd的11个完整程序delta，保留上文ceac合同。新增NO_ROPE编译特化改变真实QK维：528字节packed行对应query/计算512，不再依赖64维补零；带RoPE仍576。arch35 NoPE的UB packed stride缩为544，带RoPE仍672；arch22 NoPE反量化结果以连续ND512写GM，再由专用ND→L1搬运，带RoPE仍分NoPE/RoPE NZ。GM ring预算中的576保留槽大小不能当新版逻辑计算维或allocator packed宽度。

arch35只为INT8、分页、sparse_mode3、正的二次幂页、K>0且UB预算通过时打开IS_VEC_S2PHYADDR；split-G带RoPE明确禁止，split-G无RoPE可选。准入按向512字节对齐的页表加align128(K)*(4+8) <=248KiB，Host和Device共用CanPrecomputeAddresses。Host额外分配queryRows*K*8字节GM地址表；预计算在正常UB初始化前临时占用TPipe，参与/空负载AIV都SyncAll后Reset，不能绕过无工作核同步或与后续UB同时复用。

地址预计算把稀疏ID乘稀疏块、用页大小shift取页号，Gather物理页，Mull/AddC显式组装64位字节offset，-1与尾部写全1哨兵。依query可见KV长度选有效prefix，含TND query末值协议；表本身以uint32视图存64位地址，消费时reinterpret int64。正索引和实际物理页容量仍需producer保证，vectorized gather没有因此获得通用越界校验。与普通按需路径的成对读取、哨兵块和有效计数应分别验，不能把无RoPE带来的节省写成实测性能结论。

arch22新增三槽MTE2 packed缓冲、对齐的int64成对读TopK和512-token NoPE地址缓存。只有NoPE/PA/V、稀疏块1、页128、S2块512、非S2跨核split且页表有效时考虑预计算；K>=256且页表宽>256或K>2560选adaptive类型。小表/窗口缓存为1024项，较大范围可借8192项buffer或逐页gather，query地址结果容量1536项，不足时转segment预计算或原按需搬运。窗口身份依batch与范围，绝非跨调用通用TLB。

该路径对token与物理页值做局部范围检测，并在token范围<=2^24时用FP32 min/max，否则标量处理；有效负padding仍须位于尾部，二分截断不能接受中间洞。多个路径依128页与32/512粒度组织，不得把宏支持更广页形状解释为此快路全部启用。Host另把arch22 usedCoreNum限制到实际query行数，减少空核但不改变源的硬件准入矩阵。

输出初始化也收窄：TND只清实际末值之后的padding query行；arch35对有效但空S2的query另ClearEmptyQueryOutput，returnSoftmaxLse和needInit决定具体清零路线。捕获时全有工作、回放时空query/空稀疏前缀必须按新版route单测，不能复用ceac“全输出预清”假设。这里读取的是版本delta，未重新宣称整文件raw全文或新版本数值/图/性能已通过。
