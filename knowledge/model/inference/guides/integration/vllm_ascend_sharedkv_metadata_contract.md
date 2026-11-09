---
type: Guide
title: vLLM Ascend共享KV执行：元数据布局、分页/slot与FP8解包
description: 适配SparseAttnSharedkv与KV量化变体时，区分864/900-word有效结构、8/9字段FA行和1024-word容器；核对AICPU长度来源、mask/window、压缩任务成本、零工作和未初始化尾部，保留Host校验缺口及消费者匹配边界。
  补非量化SWA/CFA/SCFA消费端的slot/页地址、低精度概率与FP32递推、七块L1和双缓冲同步，区分README与实际Host门禁。 补950量化640字节行、E8M0尺度、BF16解包与split-G共享、VF尾块及消费者校验缺口。
tags:
- task.implementation
- task.debugging
- topic.attention
- topic.model_adaptation
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/kv_quant_sparse_attn_sharedkv_metadata.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv_metadata/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv_metadata/README.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv_metadata/op_graph/kv_quant_sparse_attn_sharedkv_metadata_proto.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv_metadata/op_host/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv_metadata/op_host/kv_quant_sparse_attn_sharedkv_metadata_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv_metadata/op_host/op_api/aclnn_kv_quant_sparse_attn_sharedkv_metadata.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv_metadata/op_host/op_api/aclnn_kv_quant_sparse_attn_sharedkv_metadata.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv_metadata/op_host/op_api/l0_kv_quant_sparse_attn_sharedkv_metadata.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv_metadata/op_host/op_api/l0_kv_quant_sparse_attn_sharedkv_metadata.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv_metadata/op_kernel_aicpu/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv_metadata/op_kernel_aicpu/kv_quant_sparse_attn_sharedkv_metadata_aicpu.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv_metadata/op_kernel_aicpu/kv_quant_sparse_attn_sharedkv_metadata_aicpu.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv_metadata/op_kernel_aicpu/kv_quant_sparse_attn_sharedkv_metadata_aicpu.json
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv/op_kernel/sparse_attn_sharedkv_metadata.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv_metadata/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv_metadata/README.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv_metadata/op_api/aclnn_sparse_attn_sharedkv_metadata.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv_metadata/op_api/aclnn_sparse_attn_sharedkv_metadata.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv_metadata/op_api/l0_sparse_attn_sharedkv_metadata.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv_metadata/op_api/l0_sparse_attn_sharedkv_metadata.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv_metadata/op_graph/sparse_attn_sharedkv_metadata_proto.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv_metadata/op_host/sparse_attn_sharedkv_metadata_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv_metadata/op_kernel_aicpu/sparse_attn_sharedkv_metadata_aicpu.cpp
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv_metadata/op_kernel_aicpu/sparse_attn_sharedkv_metadata_aicpu.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv_metadata/op_kernel_aicpu/sparse_attn_sharedkv_metadata_aicpu.json
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv/README.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv/op_host/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv/op_host/sparse_attn_sharedkv_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv/op_host/sparse_attn_sharedkv_proto.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv/op_host/sparse_attn_sharedkv_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv/op_host/sparse_attn_sharedkv_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv/op_kernel/arch32/sparse_attn_sharedkv_scfa_block_cube.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv/op_kernel/arch32/sparse_attn_sharedkv_scfa_block_vector.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv/op_kernel/arch32/sparse_attn_sharedkv_scfa_kernel.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv/op_kernel/arch32/sparse_attn_sharedkv_swa_block_cube.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv/op_kernel/arch32/sparse_attn_sharedkv_swa_block_vector.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv/op_kernel/arch32/sparse_attn_sharedkv_swa_kernel.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv/op_kernel/sparse_attn_sharedkv.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv/op_kernel/sparse_attn_sharedkv_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attn_sharedkv/op_kernel/sparse_attn_sharedkv_template_tiling_key.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/README.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_host/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_host/kv_quant_sparse_attn_sharedkv_check.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_host/kv_quant_sparse_attn_sharedkv_check.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_host/kv_quant_sparse_attn_sharedkv_check_consistancy.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_host/kv_quant_sparse_attn_sharedkv_check_existance.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_host/kv_quant_sparse_attn_sharedkv_check_feature.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_host/kv_quant_sparse_attn_sharedkv_check_single_para.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_host/kv_quant_sparse_attn_sharedkv_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_host/kv_quant_sparse_attn_sharedkv_proto.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_host/kv_quant_sparse_attn_sharedkv_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_host/kv_quant_sparse_attn_sharedkv_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/common/CopyInL1.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/common/FixpipeOut.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/common/buffer.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/common/buffer_manager.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/common/buffers_policy.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/common/matmul.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/common/offset_calculator.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/kv_quant_sparse_attn_sharedkv_common_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/kv_quant_sparse_attn_sharedkv_kvcache.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/kv_quant_sparse_attn_sharedkv_scfa_block_cube.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/kv_quant_sparse_attn_sharedkv_scfa_block_vector.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/kv_quant_sparse_attn_sharedkv_scfa_kernel.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/util_regbase.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/vf/vf_basic_block_aligned128_no_update_scfa.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/vf/vf_basic_block_aligned128_update_scfa.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/vf/vf_basic_block_unaligned128_no_update_scfa.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/vf/vf_basic_block_unaligned128_update_scfa.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/vf/vf_basic_block_unaligned64_no_update_scfa.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/vf/vf_basic_block_unaligned64_update_scfa.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/vf/vf_basic_block_utils.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/vf/vf_flashupdate_new_scfa.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/arch35/vf/vf_mul_sel_softmaxflashv2_cast_nz_scfa.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/kv_quant_sparse_attn_sharedkv.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/kv_quant_sparse_attn_sharedkv_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_quant_sparse_attn_sharedkv/op_kernel/kv_quant_sparse_attn_sharedkv_template_tiling_key.h
  role: implementation
created_at: '2026-11-03T05:41:21Z'
updated_at: '2026-11-03T05:47:24Z'
platforms: []
aliases:
- SparseAttnSharedkvMetadataCpuKernel
- KvQuantSparseAttnSharedkvMetadataCpuKernel
- aclnnSparseAttnSharedkvMetadataGetWorkspaceSize
- aclnnKvQuantSparseAttnSharedkvMetadataGetWorkspaceSize
- FA_S2_MAX_NUM
scope:
  any_of:
  - all_of:
      framework:
      - vllm
  schema: model.inference.v1
---

# 适配入口与证据范围

固定 Main `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`。本卡逐份读取两套 metadata 的公开 API、L0/GE、AICPU、构建描述，以及两套 Attention 的 metadata 结构头；相同代码按全文差异对照。它解释调度协议，不把尚未在本卡闭合的 Attention Device 执行端、SDK launcher 和实机数值视为已通过。

现有[共享KV概念](../../concepts/kernels/sparse_attn_sharedkv.md)解释 SWA/CFA/SCFA；本卡维护 Main 当前具体生产协议。它也不与 [SparseFlashMla](vllm_ascend_sparse_mla_host_dispatch_contract.md) 或 [QLI](vllm_ascend_quant_lightning_indexer_v2_host_contract.md) 的同样大小 metadata 缓冲互换。

## 双阶段 API 与长度输入

`GetWorkspaceSize` 创建 executor，读取平台 Cube/Vector 核数和 SoC 字符串，把五个长度输入都交给 `l0op::Contiguous` 并检查返回值，再向 executor 添加 AICPU 任务。公开 `ParamsCheck` 当前直接返回成功；五个 proto optional 输入并非在 L0 调用前逐一按空指针跳过。raw `nullptr`、空 tensor 和上层包装器占位对象是否等价，必须核对实际 SDK/调用方，不能从 optional 声明推定。

阶段一把外部 `workspaceSize` 写成零；阶段二仍通过 `CommonOpExecutorRun` 提交到调用者 stream。零 workspace、AICPU JSON 的同步标志都不证明阶段一已经产出可由 Host 读取的 metadata。输入、输出及 executor 的生命周期和后续 stream 顺序仍由接线方维护。GE infer 固定输出 `[1024]`、INT32，并不验证内部协议或长度内容。

AICPU 的 batch 选择优先 `seq_used_q.shape[0]`，再使用 TND 的 `cu_seqlen_q.dim0 - 1`，最后才用 batch 属性。每批实际长度优先 `seq_used_*`，其次 TND 前缀差，最后 max 长度。前缀数组的首值、单调性、末值与 tensor 容量都必须在集成处保证；读取 int32 后转 uint32 的路径不会自动拒绝负长度。

## 两个生产者的门禁差异

| 项目 | 非量化 metadata | KV量化 metadata |
|---|---|---|
| 文档硬件范围 | README 为 A2/A3 | README 为 950 |
| SoC 分支 | 名称包含 Ascend950 才走 950，否则进入 910 分支 | 相同；else 不是其它硬件支持证明 |
| Q heads | 仅 KV layout=BSND 时检查 32/64 | 无条件检查 64/128 |
| KV heads | 1 | 1 |
| layout | Q=BSND/TND，KV=PA_ND/TND/BSND；拒绝 TND Q+BSND KV | 还拒绝 BSND Q+TND KV |
| 必需长度 | TND Q 要 cuQ；分页 KV 要 seqUsedKV | seqUsedKV 对全部 KV layout 必需 |
| window | left/right 均要求非负 | left 非负；BAND 初始化把 nextToken 固定为零 |
| 压缩特征 | hasCmp 时才检查 ratio=4/128、topK=0/512/1024 | 相同 |

两者接受 `ori_mask_mode` 0/3/4。0 是全 K，3 是右下因果，4 是 BAND 并按 S1/S2 差平移窗口。不要采用非量化错误消息中“只能为4”的字面结论。`CheckConsistency()` 当前直接返回 true；存在获取 KV batch 的辅助函数，不等于已完成 Q/K batch 一致性检查。

两者要求输出对象/shape/data 非空、核数非零、batch/maxQ 非负，却没有在该层检查输出实际元素数/INT32 dtype、rank、负 maxK、正 headDim、所有长度数组的 batch 对齐，或核数不超过结构固定的 36/72。`ori_topk`、`cmp_mask_mode`、`has_ori_kv` 被读取，不能据此声称其每个语义都参与此调度器的分支。量化 proto 还声明 kv_quant_mode/tile_size/rope_head_dim，但当前 AICPU Prepare 读取的必需 head 属性只有 Q heads、KV heads、headDim；metadata 本身不完成 KV 量化格式验证。

## 分块、任务成本与空工作

调度先计算 `group=Qheads/KVheads`，按每批 Q 行块和 K 块估计工作，再分配 batch、Q 行，必要的分块辅助代码留在实现中。非量化 910 采用 M=group、S2=512，950 采用 M=64、S2=128。量化 910 采用 `group*(128/group)` 的 M、SCFA 收窄为单 query 行；950 的 N=128 路径采用 M=group 并把 AIC/AIV 核数减半，其他路径按 SCFA/group 对齐 M，S2=128。核数减半发生在非零校验之后，接入时还须确保结果与固定缓冲布局匹配。

每个 Q 块从首/尾 query 的可见窗口推导原 K 范围。压缩可见长度为 `floor((oriLast+1)/ratio)`；CFA 覆盖全部压缩块，SCFA 再取 topK 上限。这里只生成任务区间和成本，不校验真实 sparse index 数值。调度记录的 window S2 与 compressed S2 是组合任务序列坐标，不是可以直接当作原 K token 地址的全局坐标。

窗口和压缩任务使用同一静态成本模型 `6*ceil(M/16)+10*ceil(S2/64)`。这些系数用于分核，不是测得的周期或延迟。正常行和尾行分别计成本；Q/K 空批次为零成本。总工作为零时生产者保留一个 used core，结束 BN 等于 batch*KVheads，M/S2 结束值为零，消费端必须按该空区间处理。

头文件把 `supportFd` 初始化为 false，已读 Prepare/调度代码没有将其改为 true。因此当前生产路径不能因存在 FD 切分函数就被描述成已开启 FlashDecode；这些函数的拆分数量、除法、固定数组边界若未来开启需单独验证。

## 物理字段不可互换

| 协议 | FA 行数×字段 | FD 行数×字段 | FD起始word | 结构word数 | 外部容器 |
|---|---:|---:|---:|---:|---:|
| 非量化 | 36×8 | 72×8 | 288 | 864 | INT32[1024] |
| KV量化 | 36×9 | 72×8 | 324 | 900 | INT32[1024] |

结构字段为 uint32 位表示；公开张量是 INT32。两者 FA 的前八字段为 enable、BN/M/S2 start、BN/M/S2 end、首个 FD workspace 索引。量化第九字段是 `FA_S2_MAX_NUM`。FD 槽含 enable、BN、M、workspace、split 数、M start、M count，行内仍留一个槽。静态容量断言只证明结构放得进 1024 word，不验证实际平台核数或 tensor 容量。

生产者没有先清零整个容器。非量化只对未使用 FA/FD 行写 enable=0，不能把其它字段和 1024 容器尾部当有效零。量化 N=128 路径把每个逻辑 FA 范围复制到两个相邻物理 core 行，并写第九字段；其他生成分支没有相同的第九字段赋值，消费端必须按实际路径读取。量化减半核数后 FD 生成范围也随之变化，容器其它位置并不自动清零。

没有 ABI 版本标记可以替代精确生产者/消费者配对。新模型 Agent 应记录 operator 名、commit、Q/K layout、head 组、quant 属性、metadata 生成路径和 stream 事件；不能因为都是 INT32[1024] 就在非量化、量化、QLI 或 MLA 之间复用。

## 诊断与待验证边界

接入失败先核对五个 optional 输入在实际 SDK 中的表示、真实 batch/前缀长度、mask/window 和 SoC 分支，再核对八/九字段布局与消费端读偏移。负长度、非单调前缀、超出36/72核数、非预期 heads/layout 应在调用层拒绝；“AICPU返回成功”不足以证明它们安全。量化任务的 half-core 映射、N=128 第九字段，以及未来 FD 开启都是独立验收点。

本卡没有执行 SDK、编译、UT、图捕获或 NPU；没有证实实际精度、异步生命周期、内存越界或性能。硬件标签保持未知。下一步应沿同 commit 的 SharedKV Host tiling 与 Device 消费端闭合这些协议，而非通过增大 metadata 或清零掩盖布局不匹配。

## 非量化消费链：Host、寻址与流水

以下继续全文读取 `sparse_attn_sharedkv` 目录的 Host/注册/六个 arch32 执行头及公共头；SWA 是结构基线，SCFA 逐条核对完整差异。Device 文件放在 arch32 不代表它自动支持所有 SoC：当前 Host `GetNpuInfo` 只接受 ASCEND910B/ASCEND910_93，尽管 OpDef 另列 ascend950，README 也明确950不支持。Agent 应采用实际选中 Host/构建分支，不能采用最宽的注册名作为支持声明。

模板由实际存在的输入选择：oriKV 必须存在；没有 cmpKV/indices 为 SWA，有 cmpKV 而无 cmp indices 为 CFA，二者都有为 SCFA。SCFA 使用专用 kernel，CFA 与 SWA 共用 SWA kernel 的编译分支。Host 和 template selector 都固定 FlashDecode=0；有 FD 源码及 workspace 成员不构成可用 FD 实现。

| 检查项 | 当前消费端源码 | 对适配的含义 |
|---|---|---|
| 形状 | Q/KV headDim=512；KV heads=1；Q heads/group 为4倍数 | README 的 N1=64 更窄，未验证其它4倍数正确性 |
| 原 KV 稀疏输入 | 仅 TND Q+PA_ND KV；INT32[T,N2,K]；K正、128对齐且≤2048 | README 称未支持；实现已有分支，应按 commit 单独验收 |
| 压缩选择 | ratio=4/128；SCFA 必须有 cmp indices | K 的检查表达式是 `!(K!=512 || K!=1024)`，恒为false，不能当作成功检查512/1024 |
| 页与长度 | PA页大小为16倍数且≤1024；metadata总元素1024、INT32；sinks FP32[Qheads]必传 | OpDef optional 不表示实际调用可省略；block table内容仍须可信 |
| mask | ori=4、cmp=3，window左右非负 | metadata支持0/3不扩展Attention消费端；README默认127/0也不证明所有非负窗口通过 |
| layout | 源码有BSND/TND/PA_ND分支；TND使用B+1前缀 | README同时出现宽layout表与“仅PA_ND”，需要实测选定组合 |
| LSE | Device可按return标志写FP32 log(sum)+max | README仍称暂不支持；不能宣称接口已验证可返回 |

Host TND 的内部 `bSize` 暂存 cuQ 元素数，部分页/seqUsed校验再使用 bSize−1；Device 通过 metadata 的实际 BN 范围取 `cuQ[b+1]-cuQ[b]`，不能把 Host 临时变量直接当真实 batch。Host多项单参检查为stub，部分错误分支只打印不返回失败；需要上层把 head、数组长度、输出形状及 stride 做成明确合同。GE proto 中 returnSoftmax 的属性索引仍是8，而 Host return 属性索引是10；dtype infer 定义/注册的函数名也不一致。本卡未构建，记录这些源码接线差异供 Agent 核对实际 SDK 生成物，不能以 README 示例存在就推定构建/推形已通过。

## 逻辑页与物理slot

普通 PA 路径先用 `batch*maxBlockNum + logicalToken/pageSize` 查 block table，再计算 `physicalBlock*kvStride + head*D*pageSize + inPage*D + dOffset`，跨页 copy 分段。这里 kvStride 是元素数；不能混用字节 stride。`DataCopyPABySlots` 则把 sparse index 直接解释为物理 slot，按 slot/pageSize 和 slot%pageSize 取地址，绕过 block table；负值在 helper 中钳到slot0，但上游稀疏有效长度遇首个负值即停止，不是任意位置负值的通用mask。

SWA/CFA 的原KV稀疏长度最多 min(indexWidth, actualOriLen)，前缀终止后不再读取剩余slot。SCFA kernel 对 `oriSparseIndices` 明确不消费；即便 Host接受该参数，也不能把它当 SCFA 原KV稀疏选择开关。SCFA 用压缩 indices 过滤负值/超出因果压缩长度的项，再把实际 KV 行收集进四槽 GM merge 环，Cube从这个环读 K/V。PA压缩索引是逻辑 token，再经 cmp block table；BSND/TND采用各自线性偏移。它与原KV direct-slot协议不同。

SCFA 两个 AIV 分担索引收集，通过 MTE2→MTE3 事件控制16行 UB块，按两个地址的正 stride 合并copy，负/过大stride退回逐条copy；无效项被跳过，首项负值可提前停止。随后 Cube/Vector flag6–9维护 gather→QK→softmax→PV→output，另用flag3保护四槽merge环复用。长度、index排序/终止约定及 gather后实际行数必须一起验证，不能把输入K宽度当已收集有效行数。

## 精度、内存与收尾

Q/K/V为同一FP16或BF16类型，K=V。Cube QK 在D=512上分两次256、L0再分128积累FP32；Vector乘softmaxScale，以sinks为初始max、sum=1做在线softmax，概率回写为KV低精度再参与PV。PV为FP32，跨S2块用exp(max_old−max_new)重标定旧累加，最后除sum；输出BF16用RINT、FP16用ROUND，LSE为log(sum)+max。不能用全FP32 softmax/golden替代这条中间舍入链进行严格逐位推断。

每个Cube采用四块QP L1、三块KV L1，L0A/B/C各ping-pong；GM中QK、概率、PV及在线输出四段均按每核两槽分配。SCFA额外有每核四份512×512低精度merge区及有效长度区。Host workspace同时包括SDK库workspace；不是metadata阶段“零workspace”的延伸，也不是可跨并行请求共享的临时区。Kernel三项任务缓存、两次preload/drain，不能删除末尾空轮；硬事件/跨核flag的配对属于缓冲所有权，不等价于Host stream完成事件。

空可见KV或空Q分支会初始化相应输出，所写LSE为零；这是一条具体约定，不是数学上空集logsumexp=-inf的通用规则。未使用core先读enable再退出，但初始化阶段已读取各自start/end；必须保持容器容量和合法core索引。源码里存在非分页地址的子块偏移差异、固定sinks缓冲上限128及SCFA gather/有效长度细节，尚无实机证据证明扩大heads、layout或稀疏宽度安全。下一次验证应覆盖真实page/slot、空行、尾行、负index、窗口边缘和图重放，不能只验一个非空密集case。

## 950 KV量化执行链

本节全文吸收 `kv_quant_sparse_attn_sharedkv` 的剩余 Host、arch35 执行端、局部common和六种VF分支。它使用自己目录中的buffer/offset/matmul辅助层；不能仅因同名头而套用别处helper的同步或布局。前述未闭合Attention Device范围在这两个SharedKV目录已完成源码阅读；SDK实现、构建实例化、模型实际调用与NPU验收仍未完成，不是完整Operator验证。

## 固定格式与真正生效的门禁

Host只允许950、PA_ND KV、Q=BF16、Q heads64/128、KV heads1、Q的D=512，KV物理D=640、tile=64、RoPE D=64、quant_mode=1。页大小16对齐且≤1024；压缩indices K明确检查512/1024，TND时检查T、BSND时检查S。TND batch先取seqUsedKV元素数，checker再以ori block table首维作为batch并要求cuQ元素为B+1、seqUsedKV元素为B。KV前缀输入现在明确拒绝非空，不能沿非量化TND KV分支传入。

每行640个FP8存储元素实质是混合字节协议：起始128字节为64个BF16 RoPE，接448字节E4M3 NoPE，再从offset576读7个E8M0尺度，最后补齐至640。每64个NoPE元素共用尺度。Vector将E8M0→BF16→FP32，E4M3→FP32后乘尺度，再RINT到BF16；RoPE按BF16位复制。解包后的512维把448维NoPE放前、64维RoPE放后，并写成NZ的17行UB步幅，再搬到L1/GM。因此外部FP8 dtype、内部混合字段以及计算维度是三个层次，不能把640全部作为FP8数值解码，或把Q的维顺序错配。

`KvQuantSASTilingCheck::Process`只调用SinglePara、Existence、Feature；虽然`check_consistancy.cpp`提供输出/KV一致性方法，当前主入口没有调用该组。部分dtype表允许INT8，而OpDef和Device入口固定E4M3，不能据此扩大INT8支持。metadata只检查对象存在，没有在该消费者层验证1024元素/INT32/rank。`ori_sparse_indices`会设置全局hasOriSparseIndices，但未配套完成单参校验；它只应在已核清的SWA分支使用，不能与SCFA任意混配。

ReturnLSE proto仍按属性8取bool，但当前return属性在更后的位置；Device入口也没有把softmax_lse传到计算实例，实际不能推定有效LSE。名为`GetSinks`的parser辅助函数未接入Parse；真正sinks存在性/元素数检查位于checker。应沿实际调用图判断校验覆盖，不能从函数名称推断所有方法都已运行。

## gather、物理地址与有效行

SWA的原KV离散分支把索引解释为物理slot，跳过block table，并在首负值处截取有效前缀；压缩SCFA的索引通常是逻辑压缩token，经cmp block table映射。非稀疏窗口/CFA按每32行任务、两AIV分半，再拆跨页copy。稀疏分支两项成对copy，可合并正且小于INT32_MAX的stride；否则逐项copy。每次最多16行送入解包队列，写完才发布L1/GM所有权。

当前`GetkeyOffset`只拒绝负索引；`CopyInKvSparse`计算的`s2IdLimit`没有用于上界拒绝。因此不能把因果长度裁剪工作数量当作每个选中index的合法性证明。有效值必须在前、-1尾部终止，选中token/slot及block table物理值必须由调用方保障；有洞的负值、越界正值、重复slot及非预期排序需要单独验证。解包实际收集行数可能小于分配的S2行数，不能把未写L1/GM尾部当零或有效KV。

全局hasOriSparseIndices还会影响取index和地址的helper，而不仅是SWA模板分支。SCFA同时传原KV离散索引可能改变压缩gather的索引来源，源码没有建立这种组合的完整合同；Agent应拒绝自动把两个开关相乘。

## split-G、共享内存和同步

64 heads使用一个64×128基本块；128 heads设置`SPLIT_G=1`，相邻两个Cube分别处理go=0/64，同一metadata逻辑任务复制到两行。Vector稀疏解包分成四份，经每对Cube共享的三槽GM缓存交给两边Cube重读；这与非量化四槽merge环不同。每对workspace为 `3*128*512*sizeof(BF16)`，Host按AIC核数右移一位分配，另加SDK workspace。

量化metadata的第九字段在这里有确切用途：split-G路径先读`FA_S2_MAX_NUM`，即使某core enable=0，AIV也要完成对应次数的flag15配对；有工作核在任务结束后补足剩余次数。删除“空核”或提前退出剩余flag可能破坏核对之间同步。普通路径不读取第九字段，解释了生产者非N128分支未写它的限制。metadata中的S2 start/end虽被读取，主执行循环实际按本地可见区间展开；不能据字段存在就启用任意FD分片。

AIV先把共享tiling写SSBUF并以mode4/PIPE_S的flag15通知Cube；Cube读取这份参数后才初始化坐标。L1分配器固定512KiB，P双缓冲、right三缓冲；Q单缓冲、K另三缓冲；L0A/B各64KiB、L0C256KiB，内部再按16/32/128KiB分槽。UB里QK结果双缓冲、PV结果单缓冲及V0/V1队列各有固定容量。BufferManager只递增字节offset、不检查容量，FreeBuffer为空；模板里的通用4槽/2×2策略也不能被当作本实例的动态allocator。

buffer事件ID按构造顺序在16个范围循环，mode4下两个AIV使用额外16偏移。AIC/AIV必须保持同一构造和Get/GetReused顺序，前向/后向/BOTH三种策略的Set/Wait不通用。源码含GM后向同步的保留invalid方向、未统一调用UnInit等细节，不能脱离当前调用路线复用辅助模板。主循环仍有三份RunInfo、末尾两轮drain；更改循环/跳空行时需连同这些事件与SSBUF发布检查。

## 数值递推与尾块

Q和解包K/V都为BF16，QK与PV用FP32累加。MatmulK将D分128、MatmulN将输出512维分块，LoadData在310/310R6/5102宏下采用不同步幅/转置门禁；主实例仍只由950 Host准入。Fixpipe把结果双目的写到两AIV的UB。VF严格限定FP32输入和BF16概率输出，按S2=128、1–64、65–127分别处理；未更新/更新旧max各一份。尾部通过真实N mask、极小负值或masked reduce排除，不能把全部128位置一律相同处理。

在线max/sum使用FP32，exp概率按CAST_ROUND/SAT压到BF16 NZ，PV后用`MulDstAdd`重标定旧累加；最后除sum，输出CAST_ROUND到BF16。sinks按初始max/sum=1接入。128-head的go偏移与sinks切片、短尾中的有效行和NZ padding都应做专门数值对照；本卡不把“128分支存在”写成模型精度通过。

当任一batch的Q长度大于KV长度，AIV先清整个输出并同步；TND Q长度来自cuQ差，seqUsedQ仅在更后执行参数处可能覆盖，二者不能悄然矛盾。没有触发needInit时跳过的空任务是否覆盖所有输出位置仍需检查，不能把空任务无计算推断为输出已清零。量化主实例未产生有效LSE；NaN/Inf、异步buffer生命周期、越界和性能均尚无硬件证据。适配验收至少应分别覆盖64/128 heads、三种模板、S2尾≤64/65–127/128、真实负/越界索引、Q>KV及图重放。
