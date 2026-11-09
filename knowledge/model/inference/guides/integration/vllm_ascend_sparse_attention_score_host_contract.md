---
type: Guide
title: vLLM Ascend SparseAttentionScore：分页索引、FD与Device精度同步合同
description: 核对npu_sparse_attention_score的head-major逻辑块/物理页、逐请求长度、FD分片与合并；按arch22/arch35/FP8解释softmax精度、buffer和事件，定位空输出、TopK16容量及未消费QKV反量化尺度的适配边界。
tags:
- task.implementation
- task.debugging
- topic.attention
- topic.model_adaptation
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_host/sparse_attention_score_tiling.cpp
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_host/sparse_attention_score_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/sparse_attention_score_torch_adpt.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_host/sparse_attention_score_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_host/sparse_attention_score_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_host/op_api/aclnn_sparse_attention_score.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_host/op_api/aclnn_sparse_attention_score.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_host/op_api/sparse_attention_score.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_host/op_api/sparse_attention_score.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/tests/ut/op_host/test_sparse_attention_score_fd_tiling.cpp
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/README.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/docs/sparse_attention_score_design.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_host/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/arch22/kernel_utils.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/arch22/sparse_attention_score_fd_combine_arch22.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/arch22/sparse_attention_score_kernel_arch22.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/arch35/kernel_utils.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/arch35/sparse_attention_score_fd_combine_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/arch35/sparse_attention_score_kernel_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/arch35/sparse_attention_score_kernel_arch35_full_quant.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/arch/arch.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/arch/cross_core_sync.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/arch/local_tensor_buffer.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/arch/resource.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/base_defs.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/coord.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/detail/alignment.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/detail/dependent_false.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/detail/macros.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/detail/tag_to_layout.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/epilogue/block/block_epilogue.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/epilogue/block/block_epilogue_mask2idx_arch35.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/epilogue/block/block_epilogue_online_softmax.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/epilogue/block/block_epilogue_online_softmax_arch35_reg_low_prec.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/epilogue/block/block_epilogue_online_softmax_arch35_reg_low_prec_bf16.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/epilogue/block/block_epilogue_online_softmax_low_prec.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/epilogue/block/block_epilogue_rescale_o.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/epilogue/block/block_epilogue_rescale_o_arch35_reg_high_prec.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/epilogue/block/block_epilogue_rescale_o_low_prec.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/epilogue/dispatch_policy.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/epilogue/tile_common/copy_gm_to_ub.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/epilogue/tile_common/copy_gm_to_ub_tla.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/epilogue/tile_common/copy_ub_to_gm.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/epilogue/tile_common/copy_ub_to_gm_tla.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/epilogue/tile_common/tile_copy.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/gemm/block/block_mmad.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/gemm/block/block_mmad_pv.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/gemm/block/block_mmad_pv_arch35_ABf16_C_to_UB.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/gemm/block/block_mmad_qk.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/gemm/block/block_mmad_qk_arch35_ABf16_C_to_UB.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/gemm/dispatch_policy.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/gemm/gemm_type.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/gemm/helper.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/gemm/tile_common/copy_gm_to_l1_a2.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/gemm/tile_common/copy_gm_to_l1_a5.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/gemm/tile_common/copy_l0c_to_dst.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/gemm/tile_common/copy_l0c_to_gm_a2.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/gemm/tile_common/copy_l0c_to_ub_a5.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/gemm/tile_common/copy_l1_to_l0a_a2.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/gemm/tile_common/copy_l1_to_l0a_a5.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/gemm/tile_common/copy_l1_to_l0b_a2.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/gemm/tile_common/copy_l1_to_l0b_a5.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/gemm/tile_common/tile_copy.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/gemm/tile_common/tile_copy_tla.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/gemm/tile_common/tile_mmad.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/gemm_coord.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/layout/layout.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/layout/matrix.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/layout/vector.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/matrix_coord.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/attn_infra/status.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/kernel_common.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/sparse_attention_score.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/sparse_attention_score_kernel_interface.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/sparse_attention_score_tilingkey.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/tla/int_tuple.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/tla/layout.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/tla/numeric/integer_sequence.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/tla/numeric/integral_constant.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/tla/numeric/math.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/tla/tensor.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/tla/tuple.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/op_kernel/tla/type_traits.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/tests/CMakeLists.txt
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/tests/FLASH_DECODING_GENERALIZED_TEST.md
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/tests/run_bf16_fd_minimal.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/tests/test_bf16.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/tests/test_flash_decoding_generalized.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/tests/test_fp16.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/tests/test_sparse_attention_score_fp8.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/tests/ut/CMakeLists.txt
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/sparse_attention_score/tests/ut/op_host/CMakeLists.txt
  role: evidence
created_at: '2026-11-03T02:18:16Z'
updated_at: '2026-11-03T05:11:47Z'
platforms: []
aliases:
- npu_sparse_attention_score
- SASATiling
- TilingSparseAttentionScore
- aclnnSparseAttentionScoreGetWorkspaceSize
- SparseAttentionScoreFdTilingTest
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend SparseAttentionScore：分页索引、FD与Device精度同步合同

## 适用任务与来源边界

新稀疏GQA模型把Indexer结果接入分页Attention、切换FP8或调优小批decode时，用本卡核对实际Host入口。固定Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，全文读取Torch adapter、OpDef/推形、L2/L0 API、tiling及Host UT共10来源1727行。保持draft与空平台；源码和UT只作数据，未运行上游、编译、JIT或NPU。

该算子与[512维SparseFlashMla](vllm_ascend_sparse_mla_host_dispatch_contract.md)、[量化LightningIndexer V2](vllm_ascend_quant_lightning_indexer_v2_host_contract.md)分别维护输入协议。本卡继续吸收同一固定提交的整个Device族、公共布局/搬运层和测试设计；源码机制已静态分析，真实数值、越界防护、capture/replay与平台执行仍待验证，不能据注册项或UT预期宣布硬件支持、加速或模型精度通过。

## Torch入口：索引轴与分页KV必须一同适配

| 输入 | 当前Torch要求 | 不能由此推出的结论 |
|---|---|---|
| query | 非空TND `[T,Hq,D]`，qInputLayout只能TND | 其他layout字符串或未知rank可执行 |
| key/value | 非空blocked四维 `[blocks,block_size,Hkv,D]` | 仅传kvInputLayout即可转换cache布局 |
| select_idx | INT32三维 `[Hkv,maxQSeqlen,TopK]` | 可直接复用Indexer的`[T,Hkv,K]`输出 |
| block_table | INT32二维 `[B,maxBlocksPerBatch]` | 页ID、可见长度和内存范围已验证 |
| select_num_idx | 可选INT32二维，约定`[Hkv,maxQSeqlen]` | 仅rank检查已覆盖各轴和值域 |
| 两组actual_seq_lengths | 都必须提供且defined | optional API声明意味着当前Torch可省略 |

Hkv必须为正，与K/V及select_idx头轴一致，Hq是Hkv的整数倍；Q/K/V的D相等，K/V块轴等于block_size，block_size与top_k正数。adapter没有逐项核完select_idx末轴与top_k属性相等、maxQSeqlen覆盖实际T、两组长度dtype/内容、页表ID范围及非FP8分支全部dtype。调用者应保存实际shape、dtype、长度和映射，不能将Torch参数检查当完整安全证明。

函数接受kvInputLayout，但当前函数体没有检查或向aclnn转发它。布局来自真实blocked张量，而非字符串自动转换。Indexer输出若为token-major，必须先明确头轴转置及索引究竟表示token还是block，再对照实际Device消费者；本Host阅读没有证明这些坐标可直接互换。

## FP8与scale范围

query为E4M3FN时，Torch要求Q/K/V全为该dtype，q/k/v dequant scale都存在、FP32且四维，inner_precise固定4。这里没有核完scale各轴、数值或量化校准，不能将任意四维scale视为正确。输出默认BF16，可显式FP16；非FP8时输出沿用query dtype。

OpDef列出FP16、BF16以及FP8到FP16/BF16组合，并注册ascend910b、910_93、950配置；这与具体SoC的tiling key分支、已编译Device和实机能力仍有距离。本卡的普通FP8协议不能套用INT8、MXFP8的E8M0分组尺度或其他KV量化格式。

## L2会整理输入，LSE尚未从这个出口交付

`aclnnSparseAttentionScoreGetWorkspaceSize`创建executor，对Q/K/V、select_idx、block_table及存在的optional输入调用Contiguous，再进入L0推形和AICORE launcher。这包括分页K/V，因而本入口不是由IgnoreContiguous承诺的纯view路径：可能产生大cache物化、额外workspace和地址变化。适配图捕获或持久KV时，记录真实拷贝、输出/临时buffer身份、峰值内存和异步寿命，不凭输入页结构承诺零拷贝。

L0分配Attention与FP32 LSE两个中间输出；GE推形给Attention等同Q，LSE为`[T,Hq,1]`，未知rank分支只传播`[-2]`。L2只对Attention做ViewCopy，LSE的ViewCopy被注释；Torch也只返回Attention，并传入未定义softmaxLse。公开optional LSE参数与推形存在不代表本调用已导出有效LSE，不能接到依赖LSE的DCP合并中。

阶段一返回workspace和executor并不等于设备完成，阶段二才调用CommonOpExecutorRun并使用指定stream。外部执行器实现未读；跨stream使用结果要保留必要依赖，不能把入队成功写成数值或捕获验收。

## Tiling会采用选择张量的真实几何

SASATiling从query取得T/Hq/D，从block_table取得B和最大块数；随后把Hkv、maxQSeqlen、TopK改为select_idx的三个storage维。这意味着仅记录属性numKeyValueHeads/topK不足以重建最终计划，尤其绕过Torch走raw API时必须检查张量和属性一致性。

scale_value在开区间`(-1e-9,1e-9)`且D>0时改为`1/sqrt(D)`；传0是自动缩放入口，不是Attention分数乘0。Host读取两组长度地址，但所读tiling没有验证长度单调、批间终点、可见KV或页ID内容；也不能据此推断长度数组的具体坐标协议已经由Host检查完毕。

正常任务数为`T*Hkv`，blockDim取与AIC数的最小值，结果0时改1。Host的非950/950分支并不是任意SoC完整兼容证明；特别是GenerateTilingKey在不匹配D/block/dtype时仍返回一个默认FP16 D128 key，不会可靠拒绝所有非法形状。不能把tiling返回成功当越出D128/block128已获得通用实现。

## FD只在小任务门禁内自动选择

FD候选必须同时满足：FP16/BF16，或950上的E4M3FN；inner_precise4、D128、block128、TopK在12..16；Hkv正、Hq是Hkv的整数倍、分组大小G在1..128；maxQSeqlen至少T；任务正且`10*T*Hkv < 3*AIC数`。拆分任务总数`T*Hkv*TopK`还必须大于正常blockDim。TopK1/17或基础任务数等于AIC数走正常计划，不是FD功能异常。

select_num_idx只有放在Host、元素数至少Hkv*maxQSeqlen且数据指针有效时才参与成本估计；否则记录warning并按TopK估计。每个有效计数在成本模型内被截到0..TopK，零计数任务不计成本。这是Host估价的退路，不证明Device忽略该输入、接受任意错误计数或已正确处理全空行。

模型以`ceil(G/16)`、有效块数及launch常数拟合成本，bestCore依据平方根公式取整，再限制到AIC数、32与有效块数。源码注释的0.001微秒单位和拟合常数不是本卡测得的延迟，更不是NPU性能承诺。Host counts的位置/内容改变可能改变计划，应与真实性能和输出比较，而非只追求更多核心。

## FD分片与workspace是同一个协议

Host将全部基础任务各自的TopK区间展平，按每核连续区间切分。一个基础任务只有被核边界切开时才进入combine列表；该任务的partial IDs连续，partialStart/partialCount必须与core任务区间和实际kernel一致。选择有效块数影响分核成本，但区间总长度仍按完整TopK计算，不能擅自在caller压缩成有效块总数后继续沿用旧计划。

FD LSE子步长为`align_up(ceil(G/2),8)`；partial LSE为`partialTaskNum*2*stride*sizeof(float)`，partial O为`partialTaskNum*G*D*sizeof(float)`。这些是中间FP32大小，与公开LSE未交付的事实不冲突。头文件把各offset定义为相对GetUserWorkspace的字节偏移，不能按元素或整个外部workspace基址重新解释。

非950保留identity索引及四类pipeline缓冲，FD partial区在其后512字节对齐；950的FD partial区从identity之后对齐。950非FD则按`blockDim*TopK*blockSize*D*dtype_bytes*2`加identity计算稀疏暂存。最终都加平台libapi workspace；FD和950稀疏分支有最终加法溢出检查，不代表所有此前uint32乘法或所有raw输入都已覆盖。

对应key：非950 FP16/BF16普通20001/20002、FD20003/20004；950普通FP16/BF16为10001/10002、FP8到FP16/BF16为10003/10004，FD对应10005..10008。记录实际key、blockDim、combine/partial计数、workspace与输入身份，才能定位“同shape不同计划”或临时buffer失配。

## 适配与性能诊断的停止点

所读Host UT静态定义950与910B的FP16/BF16 FD/正常key，检查核心区间、combine和partial映射，并列举TopK和任务门禁回退；没有运行UT，UT里的假平台/core也不证明实际硬件和FP8数值已通过。Tiling注册长度/计数输入的数据依赖不构成完整图更新与Device数据访问验证。

新模型先把head-major选择、实际cache dtype/scale、长度与页身份闭合；再确认L2整理输入和LSE出口是否满足框架；最后比较普通与FD的输出、临时内存和端到端时延。下文给出Device的实际消费者；源码级路径分析不替代全空选择、FP8误差、异步执行器与graph捕获的运行验收。

## Device消费者：长度是逐请求长度，索引是逻辑块

arch22、arch35及arch35 full-quant入口都把两组actual lengths按逐请求长度使用：扫描并累加Q长度以定位global token所属请求，再用该请求的KV长度计算`historyLen = kvLen - qLen`。它们不是带首零的cu-prefix数组。`select_idx`按`[kvHead,globalQToken,TopK]`取值，值是逻辑块号，经`block_table[batch,logicalId]`转换为物理块。`maxQSeqlen`必须覆盖全局T；不能把每请求local token坐标直接拼成此轴。

一个任务对应一个token和一个KV head，组内`G=Hq/Hkv`个Q head连续读取且共享所选块。K/V真实地址为`physicalId*(blockSize*Hkv*D)+kvHead*D`，页内行跨距是`Hkv*D`；不是把各head的cache独立连续铺开。当前块的有效长度是`(historyLen+localQ)%blockSize+1`，其余所选块通常按整块处理。

| 入口 | 有效块数和可见性处理 | 调用方仍须保证 |
|---|---|---|
| arch22、arch35普通dtype | 读取有效计数，过滤负logical ID；没有照搬Host成本模型的0..TopK截断，也不逐项过滤未来正logical ID | 计数合法、每项因果可见、logical/table/physical ID均在实际容量内 |
| arch35 full-quant | 将计数限制0..TopK；还过滤超过当前可见逻辑块数的ID，尾块截取实际行数 | 页表自身长度、物理ID与cache容量合法；不能以逻辑过滤代替物理访问验证 |

三个主核均有`validPhysicalIds[16]`、`validTileSize[16]`局部数组。Host允许TopK17回退普通key，Host UT也只断言key；这不能证明17个有效块的Device存储安全。新模型应把当前使用范围限制在已核清容量内，另行验证更大TopK，不能把“退出FD”当“进入任意TopK通用实现”。

普通任务计数为0或过滤后没有有效块时直接continue，未承诺把O置零。FD中被拆成多个partial的空片有`WriteNeutralPartial`，写零O和极小float LSE；未拆分任务仍可沿普通空任务路径返回。不能据局部neutral分支推导所有全空输入输出为零；测试保留非严格xfail，也没有构成修复证据。

## 架构、精度和同步差异矩阵

`__CCE_AICORE__==220/310`是编译架构分支；其中310选择arch35，不能因数字相同就标为310P平台。入口设置MIX AIC/AIV并使用GetUserWorkspace。实际kernel key与上文Host映射一致，但匹配key仍要求对应编译产物存在。

| 路径 | QK/P与softmax | PV与输出更新 | 暂存与协作 |
|---|---|---|---|
| arch22 | QK结果S写GM FP32；scale/max/exp/sum使用FP32，P转FP16/BF16 | PV及滚动O使用FP32，末步归一化后转输出dtype | GM三阶段S/P/OTmp/update；先发两步，FIX→Vector→MTE3→Cube事件配对，FD后SyncAll再combine |
| arch35 FP16 | QK通过Fixpipe到UB FP16；scale、max、exp与当前和包含半精度阶段，持久max/sum及校正使用FP32 | PV到UB FP32，滚动重缩放和最终除法FP32 | 两组S/OTmp UB槽、三组L1 P槽；mode4分发给两个AIV，另一子核flag ID加16 |
| arch35 BF16 | QK及scale后S为BF16；专用BF16 epilogue将max、减法/exp、当前sum提高到FP32，P再转BF16 | 同上 | 不应照旧design文档把BF16路径全部max/exp/sum写成BF16 |
| arch35 E4M3FN输入 | Q/K/V/P为FP8，QK S/输出选FP16或BF16；P计算后乘448并RINT/SAT转FP8，sum仍取未乘448的exp | PV累加FP32，最终结果除sum并乘`1/448` | 使用相同资源/流水分工；这一补偿只对应P的448，不能代替Q/K/V反量化尺度 |

arch22主入口选`EpilogueAtlasA2OnlineSoftmax<OUT_ONLY,float>`和float rescale；同目录half specialization虽已阅读，并不意味着这个入口接受inner_precise1并实际使用它。arch35的FP16/BF16有各自specialization；`inner_precise`注释、旧文档描述和当前模板实例化冲突时，应记录实际类型链。

QK的L1 Q通常只加载一次，K/V按物理块分批进入L1，L1→L0按元素类型/布局选择LoadData；8bit转置分支还区分M是否按C0对齐，不能把FP16的16元素分形参数照搬给FP8的32元素C0。L0C使用FP32累加，Fixpipe决定落GM/UB及输出cast。arch35 QK、PV共享L0A/B，前缀stage计数交错分配；QK和PV各占L0C半区。修改预发深度、G/D、tile或buffer数必须同时重算这些计数及资源范围，不能只调Host tile。

`LocalTensorBuffer`的A2实现由TPipe初始化资源，A5直接构造对应TPosition本地tensor；资源常量为A2 UB192KiB/L0C128KiB、A5 UB256KiB/L0C256KiB，两者L1均512KiB、L0A/B各64KiB。它们是本提交的静态容量假设，不是任意芯片可用空间。公共`GetBufferByByte`只是按字节偏移取view，不额外检查各分区是否重叠。布局和TLA tile helper保留父stride、累计coord并延迟计算offset，不会把非连续布局自动物化为连续内存。

同步需按实际生产者和消费者检查。arch35 QK Fixpipe的双AIV就绪、softmax写L1 P后的mode4通知、PV释放P和Vector释放OTmp均有独立flag；无数据子核也会wait/set以维持配对。不能删除空分支同步作为“减少等待”。输出写回复用go缓冲，最后一步等V→MTE3后复制；FD则写FP32 partial O与`log(sum)+max`，不是直接交付公开LSE。

## FD合并保持子核行归属与稳定归约

合并核按基础任务、partial和head行tile读取FP32 partial O/LSE，求跨片最大LSE，以`exp(lse-max)/sum(exp(lse-max))`加权partial O。arch22固定最多16片，arch35最多32片；单次行tile最多8个head、D128。padding LSE填极小float。arch22与arch35对G很小时的子核行分割不同，必须沿实际writer映射取LSE，不能只复用相同的partial字节大小。

结果累加仍为FP32，BF16使用RINT、FP16使用CAST_NONE。合并完成前partial O、LSE和各片写入必须保持有效，跨任务复用或省掉SyncAll会改变依赖；测试中的跨基础任务重复100次检查是需要运行的验收设计，不能引用为本次已通过。未读外部AscendC实现/硬件内存一致性与动态并发行为仍不是本卡的静态证明范围。

## FP8尺度消费与测试证据的具体缺口

Torch要求传入Q/K/V dequant scale，与Device已消费它们是两个问题。当前full-quant主核调用的是不带`deqScalar`的QK/PV overload；参数对象虽然保存尺度地址，所选路径未读取它们。公共BMM/Fixpipe确实另有带deqScalar的PER_TENSOR overload，但其存在不能补上当前入口的调用。`tools/fix_mmad_deq.py`只是从BSA文本抽取overload的维护脚本，也不能证明主核已接线。

`test_sparse_attention_score_fp8.py`直接把输入转FP8，构造全1尺度，CPU golden也使用FP8值转FP32而未应用非单位尺度；实际NPU调用没有转发这些尺度。这组测试的设计不能验证Torch adapter要求的非单位反量化合同。适配Agent应先核对实际Python/extension入口和ABI，再设计Q/K/V各自非单位、不同块尺度、零/非有限值及饱和输入的数值比较，未知行为保持阻断，不把P的448补偿解释为三组尺度已支持。

BF16/FP16测试含因果block生成、非顺序物理映射、变长多batch、prefill→decode、长KV与固定seed；`assertRtolEqual`阈值0.007是测试设置。FD通用测试另用FP32数学golden、relative L1≤0.02、cosine≥0.999并检查shape/dtype/finite；TopK17明确`check_cpu_golden=False`。设计文档的历史NPU结果和误差数值只属上游记载，本次没有运行或复现，也不扩大当前Scope。

本次追加87份来源（83 ingest、4已读skip），共25891行；整族阅读采用完整C++正文的去注释/空白投影、已读同族的完整差异，以及Python完整AST正文投影（去文档串/日志，保留条件、参数表、数学、assert与实际调用）；FP16测试以明确dtype/名称替换后的BF16 AST做全量diff，FP8测试亦对已读AST做全量diff。三个只有空namespace的copy占位头与文本修补工具已完整读后明确skip；其余来源按各自实现、约束或测试证据吸收。这样闭合的是固定源码族的执行知识，不是已验证的完整Operator或全平台性能结论。
