---
type: Guide
title: vLLM Ascend融合MC2专家链：三类权重、EP容量与Host缓冲门禁
description: 沿FusedMC2CommImpl与dispatch_ffn_combine追踪INT8、打包INT4和BF16的ACLNN分派，核对调用方输出缓冲、M/K/N/专家列表、HCCL_BUFFSIZE与workspace、stream和MegaMoE容量选择；区分策略回退、薄Host校验与完整通信/Device验证。
aliases:
- torch.ops._C_ascend.dispatch_ffn_combine
- FusedMC2CommImpl.fused_experts
- aclnnDispatchFFNCombine
- aclnnDispatchFFNCombineW4A8
- aclnnDispatchFFNCombineBF16
- DispatchFFNCombineW4A8CheckShapeAndSetTiling
tags:
- task.implementation
- task.debugging
- topic.mixture_of_experts
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/dispatch_ffn_combine_torch_adpt.h
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_host/dispatch_ffn_combine_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_host/dispatch_ffn_combine_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_host/op_api/aclnn_dispatch_ffn_combine.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_host/dispatch_ffn_combine_w4_a8_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_host/dispatch_ffn_combine_w4_a8_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_host/op_api/aclnn_dispatch_ffn_combine_w4_a8.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_host/dispatch_ffn_combine_bf16_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_host/dispatch_ffn_combine_bf16_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_host/op_api/aclnn_dispatch_ffn_combine_bf16.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/moe_comm_method.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/token_dispatcher.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_forward_context.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding_meta.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_host/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_host/dispatch_ffn_combine_proto.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_host/hcom_topo_info.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_host/op_api/aclnn_dispatch_ffn_combine.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_host/tiling_args.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/dispatch_ffn_combine.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/dispatch_ffn_combine.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/dispatch_ffn_combine_kernel.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/dispatch_ffn_combine_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/moe_init_routing_quant_v2/moe_init_routing_quant_v2.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/moe_init_routing_quant_v2/moe_init_routing_quant_v2_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/moe_init_routing_quant_v2/moe_init_routing_v2_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/moe_init_routing_quant_v2/moe_v2_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/moe_init_routing_quant_v2/moe_v2_expert_token_out.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/moe_init_routing_quant_v2/moe_v2_fullload_dynamic_quant.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/moe_init_routing_quant_v2/moe_v2_fullload_quant.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/moe_init_routing_quant_v2/moe_v2_fullload_quant_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/moe_init_routing_quant_v2/moe_v2_gather_dynamic_quant.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/moe_init_routing_quant_v2/moe_v2_gather_out.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/moe_init_routing_quant_v2/moe_v2_gather_quant.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/moe_init_routing_quant_v2/moe_v2_init_routing_fullload.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/moe_init_routing_quant_v2/moe_v2_mrgsort.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/moe_init_routing_quant_v2/moe_v2_mrgsort_out.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/moe_init_routing_quant_v2/moe_v2_sort_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/moe_init_routing_quant_v2/moe_v2_sort_multi_core.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/moe_init_routing_quant_v2/moe_v2_sort_one_core.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/moe_init_routing_quant_v2/moe_v2_src_to_dst_and_gather.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/moe_init_routing_quant_v2/moe_v2_src_to_dst_op.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/moe_init_routing_quant_v2/moe_v2_src_to_dst_with_capacity.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/moe_init_routing_quant_v2/tiling_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/unpermute/moe_token_unpermute.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/unpermute/moe_token_unpermute_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/utils/block_epilogue_pertoken_row.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/utils/block_epilogue_pertoken_swiglu.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/utils/block_epilogue_pertoken_v2.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/utils/block_mmad_preload_async_fixpipe_quant.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/utils/const_args.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/utils/copy_gm_to_l1_custom.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/utils/copy_l0c_to_gm_custom.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/utils/dispatch_policy_custom.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/utils/get_tensor_addr.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/utils/hccl_shmem.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/utils/layout3d.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/utils/moe_distribute_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine/op_kernel/utils/select_helper.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_host/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_host/dispatch_ffn_combine_bf16_proto.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_host/hcom_topo_info.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_host/op_api/aclnn_dispatch_ffn_combine_bf16.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_host/tiling_args.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/dispatch_ffn_combine_bf16.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/dispatch_ffn_combine_bf16.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/dispatch_ffn_combine_bf16_kernel.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/dispatch_ffn_combine_bf16_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/moe_init_routing_v2/moe_init_routing_v2.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/moe_init_routing_v2/moe_init_routing_v2_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/moe_init_routing_v2/moe_v2_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/moe_init_routing_v2/moe_v2_expert_token_out.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/moe_init_routing_v2/moe_v2_gather_out.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/moe_init_routing_v2/moe_v2_init_routing_fullload.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/moe_init_routing_v2/moe_v2_mrgsort.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/moe_init_routing_v2/moe_v2_mrgsort_out.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/moe_init_routing_v2/moe_v2_sort_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/moe_init_routing_v2/moe_v2_sort_multi_core.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/moe_init_routing_v2/moe_v2_sort_one_core.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/moe_init_routing_v2/moe_v2_src_to_dst_op.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/moe_init_routing_v2/moe_v2_src_to_dst_op_simt.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/moe_init_routing_v2/moe_v2_src_to_dst_with_capacity.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/moe_init_routing_v2/tiling_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/unpermute/moe_token_unpermute.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/unpermute/moe_token_unpermute_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/utils/block_epilogue_pertoken_row.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/utils/block_epilogue_pertoken_swiglu.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/utils/block_epilogue_pertoken_v2.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/utils/block_mmad_preload_async_fixpipe_quant.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/utils/const_args.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/utils/copy_gm_to_l1_custom.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/utils/copy_l0c_to_gm_custom.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/utils/dispatch_policy_custom.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/utils/get_tensor_addr.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/utils/hccl_shmem.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/utils/layout3d.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/utils/moe_distribute_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_bf16/op_kernel/utils/select_helper.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_host/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_host/dispatch_ffn_combine_w4_a8_proto.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_host/hcom_topo_info.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_host/op_api/aclnn_dispatch_ffn_combine_w4_a8.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_host/tiling_args.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/dispatch_ffn_combine_w4_a8.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/dispatch_ffn_combine_w4_a8.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/dispatch_ffn_combine_w4_a8_kernel.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/dispatch_ffn_combine_w4_a8_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/moe_init_routing_quant_v2/moe_init_routing_quant_v2.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/moe_init_routing_quant_v2/moe_init_routing_quant_v2_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/moe_init_routing_quant_v2/moe_init_routing_v2_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/moe_init_routing_quant_v2/moe_v2_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/moe_init_routing_quant_v2/moe_v2_expert_token_out.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/moe_init_routing_quant_v2/moe_v2_fullload_dynamic_quant.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/moe_init_routing_quant_v2/moe_v2_fullload_quant.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/moe_init_routing_quant_v2/moe_v2_fullload_quant_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/moe_init_routing_quant_v2/moe_v2_gather_dynamic_quant.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/moe_init_routing_quant_v2/moe_v2_gather_out.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/moe_init_routing_quant_v2/moe_v2_gather_quant.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/moe_init_routing_quant_v2/moe_v2_init_routing_fullload.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/moe_init_routing_quant_v2/moe_v2_mrgsort.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/moe_init_routing_quant_v2/moe_v2_mrgsort_out.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/moe_init_routing_quant_v2/moe_v2_sort_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/moe_init_routing_quant_v2/moe_v2_sort_multi_core.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/moe_init_routing_quant_v2/moe_v2_sort_one_core.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/moe_init_routing_quant_v2/moe_v2_src_to_dst_and_gather.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/moe_init_routing_quant_v2/moe_v2_src_to_dst_op.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/moe_init_routing_quant_v2/moe_v2_src_to_dst_with_capacity.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/moe_init_routing_quant_v2/tiling_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/unpermute/moe_token_unpermute.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/unpermute/moe_token_unpermute_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/utils/block_epilogue_w4a8post_pertoken_swiglu.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/utils/block_epilogue_w4a8post_pertoken_v2.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/utils/block_mmad_w4a4.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/utils/const_args.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/utils/copy_gm_to_l1_custom.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/utils/dispatch_policy_custom.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/utils/get_tensor_addr.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/utils/hccl_shmem.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/utils/layout3d.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/utils/moe_distribute_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mc2/dispatch_ffn_combine_w4_a8/op_kernel/utils/select_helper.hpp
  role: implementation
created_at: '2026-11-03T02:13:26Z'
updated_at: '2026-11-03T05:55:10Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend融合MC2专家链：三类权重、EP容量与Host缓冲门禁

## 接入任务与边界

这里的`dispatch_ffn_combine`把专家分发、FFN与combine放进整条自定义融合入口，不是[Dispatch/Combine V2](../../concepts/techniques/moe_dispatch_combine_v2.md)的“两算子，中间独立GMM”接口。也不将旧[CANN平台回退案例](../../runbooks/runtime/mc2_fused_comm_op_compatibility_fallback.md)中的模型、版本、专家上限直接搬成本入口统一规格。

Main固定ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2。全文读取92行Torch adapter，三族OpDef100/108/93行、tiling343/297/283行、ACLNN包装83/81/83行；框架选择、容量与Meta读取指定有界范围，合计约2.2k关键行。已有owner的共享文件保持原绑定。本卡只闭合Host/框架接口facet，未展开三族完整Device、内部ACLNN生成层、HCCL协议或共享内存同步，未运行编译、通信、NPU、图或精度/性能测试。

OpDef中INT8族注册ascend910b和ascend910_93，W4A8与BF16族只注册ascend910_93。这不是本次硬件支持证明，不从名称MC2或同名MegaMoE推导950/310P也可用；保持draft、空平台及framework=vllm部分Scope。

## 先确定策略，再确定具体算子

框架setup只在ep_size>1时注册MC2/FUSED_MC2等实现，单rank只建AllGather。`select_moe_comm_method`在无EP或EP world=1时选AllGather；LoRA+EP先选AllToAll，之后才按hardware profile的通信策略检查token容量、专家密度或world size。

不同策略的谓词不同：FUSED_OR_CAPACITY在MegaMoE可用时优先FUSED_MC2，否则enable_fused_mc2=1且EP≤32也可直接选FUSED_MC2；CAPACITY_AND_WORLD_SIZE还对draft MoE量化组合决定是否跳过MegaMoE，然后在MC2/AllGather/AllToAll间选择。不能把一条策略的阈值概括成所有平台的选择规则。

`use_cann_megamoe`还要求包可用、hardware能力、enable_fused_mc2恰1、MoE、EP启用、1<EP≤64且无LoRA；包存在检测不是所有算子ABI已验证。FusedMC2CommImpl只接受enable_fused_mc2=1，forward中其他值直接ValueError，不是运行失败后自动重试AllToAll。

FUSED_MC2内部又分两条：`_EXTRA_CTX.use_mega_moe`为真走CANN MegaMoE及对称缓冲；否则走本卡自定义`dispatch_ffn_combine`。不能因选中FUSED_MC2就假定已经调用这三族C++源码，亦不能将MegaMoE的mask、布局、容量或激活支持转授本入口。

## 三种weight dtype决定真实ACLNN分派

Torch adapter先访问weight1[0]，按该项dtype选择接口，没有先穷尽列表空值、各专家一致性及w2/scale/bias组合检查。

| 首份weight1 dtype | 实际接口 | 不能省略的区别 |
| --- | --- | --- |
| INT8 | aclnnDispatchFFNCombine | weight为INT8，scale为INT64容器，probs为FP32，optional mask为BOOL |
| INT32 | aclnnDispatchFFNCombineW4A8 | 八枚INT4的INT32打包视图；另传FP32 bias1/bias2与mask |
| 其余 | aclnnDispatchFFNCombineBF16 | 包装的else分支不是任意dtype支持；OpDef限定FP16/BF16权重，不转发mask或swiglu_limit |

W4A8的低层OpDef还列INT4，但这个Torch分派只把INT32识别为W4A8。不能据低层声明将直接INT4 Tensor传入并假定进入同一路。普通[W4A8权重指南](vllm_ascend_w4a8_moe_weight_contract.md)负责真实打包与补偿bias；[MXFP4指南](vllm_ascend_mxfp4_weight_reload_contract.md)的FP4/E8M0存储不是整数INT4的替代品。

非Mega框架分支先要求两组scale_bias非None，分配与hidden_states同shape/dtype的out，并沿用构造时按num_local_experts分配的INT32 expert_token_nums。adapter返回这两个调用方缓冲的引用，Meta也只是原样返回，没有独立shape、dtype、分组或通信合法性检查。图推形通过不说明输出缓冲或输入列表匹配。

## M/K/N、专家列表与未做的校验

Host从x的storage shape取M与K，从expert_idx第二维取topK，从首份w1的storage末维推导N。W4A8在weight dtype为INT32时将该末维乘8；这解释了为什么需要打包后的逻辑布局，不能再把末维按普通INT8计算。

动态weight列表仅有一项时，expertPerRank取首份weight的第0维；多项时取列表项数。单个专家Tensor与“聚合一项列表”不能随意互换：Host按列表长度解释不同的专家轴。weight2、scale、bias、probs、id范围和真实物理NZ布局都必须由调用方一致地准备，不能把所读薄Host的shape提取当成完整验证器。

三族显式检查group非空、transB/weightNz属性存在、worldSize属于(0,768]；该数值只是Host属性上限，不是768卡通信已支持。max_output_size被读入maxOutputSize，但所读Host没有完整的正值、最坏接收容量或各rank一致性校验。接口包装固定transB=False、weightNz=True；Host key由1000000加转置位1和NZ位10生成，不能按框架原始view猜真实存储已转换。

INT8/W4A8 mask存在时显式要求一维且长度M；BF16接口不接收该mask。缺少mask不等于padding行自动无效，也不能用“所有rank本地M相同”代替专家实际接收量或全局容量的核验。

## HCCL窗口与workspace分开核算

只有所读INT8 Host有这条HCCL_BUFFSIZE检查：以MiB解析环境变量，缺省200，超uint16范围或解析失败回用默认；要求`3*M*topK*K*sizeof(int8_t)+10MiB`不超过窗口。错误字符串仍写3MB，与实际表达式的10MiB不同，排障应看固定源码表达式。W4A8/BF16两份Host没有同样检查，不代表它们不需要足够的通信缓冲或能接受任意容量。

三族Host workspace均为16MiB系统空间加`max(cocWorkspace,initRoutingWorkspace)`。不同数据路线的cocWorkspace不相同：INT8包含按256行对齐的路由索引、world²×本地专家计数、接收scale、BF16结果和INT8激活；W4A8用max(N,K)和max(K,N/2)描述若干复用暂存；BF16则保留多份输入/中间结果的累加项。不能复制一种dtype的公式估算另一种，更不能把workspace与HCCL窗口当成同一块可互相替代的额度。

W4A8的复用注释将安全性归于GMM1后SyncAll生命周期，本次未展开相应Device证明；这里仅记录Host分配表达式，不宣称已核验alias同步。内部routing子tiling还有固定40个AIV与UB196352等参数，Host读到平台信息不等于已适配任意新芯片资源。

## MegaMoE容量与普通fused容量不是同一个限制

forward_context维护普通MC2/自定义FFN每TP rank容量上限512，MegaMoE为16384，并依据prefill、图capture大小或请求数生成初始容量。某些FUSED策略提前返回，不在该选择分支再次用当前num_tokens和容量比较；配置中的cap不是每条低层入口已有运行时越界检查的证明。

TokenDispatcherWithMC2从固定mc2容量、TP和EP world size构造max_num_tokens_per_rank与global_bs；是否跳过DP allreduce决定global_bs为实际固定上界还是0。MegaMoE对称缓冲按各rank一致的编译配置分配，不能使用当前rank临时token数，后者会使各rank的集体分配不一致。

MegaMoE receive安全上界由`per_rank_cap*EP*min(topK,experts_per_rank)`得到；decode-only节点取该上界，P或PD混合节点使用mega_moe_max_tokens并截到上界，源码警告偏小会影响实际接收。MegaMoE调用前还有本地token数超max_num_tokens_per_rank的明确ValueError；非Mega的自定义调用分支没有同样的局部检查。Agent必须分别记录本地有效行、padding、最坏接收行数和每rank分配，不能只增HCCL_BUFFSIZE解决全部容量问题。

## stream、缓冲寿命与回退裁决

三份ACLNN外层包装在弱符号NnopbaseSetHcclServerType可用时选择MTE，再把调用方stream传给内部执行函数；它们没有在所读包装中显式同步，也没有捕获错误后自动切普通MC2/AllToAll。Python返回或Meta返回原缓冲，不是跨stream消费者已经可安全复用、销毁或改写这些存储的证明。

MC2 group名来自实际device_group backend；[HCCL睡眠恢复指南](vllm_ascend_sleep_hccl_graph_recovery.md)继续负责group销毁/刷新和MegaMoE上下文重绑。Host的group非空检查不证明名字仍指向有效通信域，图内捕获的地址也不能在恢复后继续盲用。

适配Agent先用所选hardware policy、EP/TP、LoRA/draft量化资格决定合法路线，再核对真实weight dtype/格式、scale/bias、expert id与输出缓冲、接收容量和窗口。无法满足时在执行前选择明确的非融合方案并保证所有rank同一集体序列；不要在部分rank已进入通信后局部重试另一条路径。完整Device/HCCL协议、零rank/高偏斜、图重放与失败恢复仍须专项实验，正确后才比较通信/计算重叠与端到端时延。


## 三族Device入口、路由与共享窗口的源码补充

补充检查同一固定Main中`csrc/mc2`剩余131条路径，按SHA相同内容复用后为106种字节。小型CMake、ABI/tiling结构和入口直接阅读；较大的routing、GMM与epilogue文件以整份结构投影核对定义、分支、常量和调用，再展开下面涉及的通信、mask、workspace、量化与unpermute选段。来源表区分直接阅读与投影，不把投影输入覆盖全文件等同逐行穷尽Device算法。原Host段落保留；本节扩展接入与排障facet，仍不是完整Operator、完整HCCL协议、全部Device模板或外部Catlass/CANN实现的闭包。

### 分派键与实际编译路线

三族`op_host/CMakeLists.txt`明确添加`-DHCCL_COMM`、`-DCATLASS_ARCH=2201`和自动同步编译选项，并按CANN安装路径探测AscendC include，存在Catlass目录时才加入其include。这是所读构建配置，不是本次编译成功或芯片支持证明。族目录仅在存在下级CMake时递归，非test/benchmark构建移除tests目录；文件在树内不证明它进入当前产物。

Device入口均声明MIX_AIC_1_2，但实际实例化不同：

| 族 | 本文件实际分发的key | 模板与接入差异 |
| --- | --- | --- |
| INT8 | 1000010 | `DispatchFFNCombine<int8_t,...,false,true>`，接收mask与swigluLimit |
| W4A8 | 1000010 | `DispatchFFNCombineW4A8<...,false,true>`，另接两组辅助bias；内部INT4布局和激活拆分不同 |
| BF16 | 1000000/1000001/1000010/1000011 | 分别对应transB/NZ为false/false、true/false、false/true、true/true；入口不接mask或swigluLimit |

这些入口未给未匹配key提供另一条计算fallback。Host能表达转置属性，不代表INT8/W4A8 Device也实例化了BF16四个key。三份proto的InferShape/InferDataType只忽略context后返回GRAPH_SUCCESS，没有设置输出shape/dtype；必须继续依赖真实接口和缓冲合同，不能以该返回值证明图元数据或输入有效。

### 各实现文件的职责与数据契约

| 文件子族 | 已提取的职责 | 适配时保留的区别 |
| --- | --- | --- |
| `dispatch_ffn_combine*.h`与tiling结构 | 从Host tiling还原M/K/N、topK、expertPerRank、listLen和接收容量，构造Catlass布局与GMM参数 | INT8的L1/L0 tile为128×256×512和128×256×128；W4A8为128×256×1024和128×256×256，不能照搬同一临时空间或调度推算 |
| `moe_init_routing*_tiling.h`、`tiling_base.h` | 选择full-load、单核/多核排序、dropless/drop-capacity及按列分片 | 量化族还有quantMode与smoothType；BF16没有同一量化PostTiling过程。源码常量不是任意shape已被完整校验的证据 |
| `sort_one_core`、`sort_multi_core`、`mrgsort*`与`sort_base` | 专家索引排序、分段多路归并、行映射及专家计数初始化 | 合并2/3/4列表和尾块有独立分支；部分SyncAll在KT测试宏下省略，不能据测试代码形状断言实际设备全局同步已验证 |
| `expert_token_out`、`src_to_dst*`、`gather_out` | count/cumsum输出、原始行到展开行映射、容量裁剪和gather | count标志2与cumsum标志1不同；drop-capacity有按expertCapacity保留和补零路径；BF16还有SIMT映射实现，不由同名文件推导所有版本字节相同 |
| `fullload_quant*`、`fullload_dynamic_quant`、`gather_quant`、`gather_dynamic_quant` | 常规量化、逐行动态量化、smooth及大列循环 | full-load受排序空间、UB剩余和列宽限制，不能按“小batch”一个条件替代全部谓词；输入与scale的物理位置需要和后续搬运协议一致 |
| `block_mmad*`、`dispatch_policy_custom`、`copy_*`、`select_helper`、`get_tensor_addr` | 多级预取/事件、NZ布局构造、Fixpipe反量化与TensorList地址解引用 | INT8/BF16的preload与W4的per-channel INT4 callback分别实现；TensorList取地址不是列表长度/生命周期验证器 |
| `block_epilogue*`与`unpermute` | GMM结果与per-token scale组合、SwiGLU/再量化、按rank/expert切片写回及TopK加权还原 | BF16、INT8和W4的scale、辅助矩阵、clip参数及同步路线不同，不能只复用函数名或结构相近的拷贝 |
| `hccl_shmem`、`moe_distribute_base`、`hcom_topo_info`、`const_args`/`layout3d` | HCCL资源结构、窗口寻址、状态字、缓存维护、rank通信统计与拓扑接口 | 拓扑头主要声明接口，内联erase只说明其map清理；不能视为外部HCCL实现、所有声明可达性或实际通信恢复已完成 |

量化routing的key由full-load分支`20000+quantMode*1000`，或普通分支`10000+quantMode*1000+dropPadMode*100+(totalLength>sortLoopMaxElement)*10`生成。Device再按具体key挑full-load、单核或多核排序和不同gather实现。这里的内部routing key与外层1000010不是同一个分派空间。

`MoeV2GatherDynamicQuant::Compute`的选定路径先按需转FP32和乘smooth，再取绝对最大值/127作逐行scale，将输入除scale，经half CAST_TRUNC再转INT8 CAST_ROUND；没有在该选段对全零行scale加入epsilon。全零、极小值、尾列与smooth组合应纳入数值验证，不能因源码有ReduceMax就认为与另一实现的round/零值政策等价。部分多列路径和full-load另有实现，不能从这个函数概括全部分支。

### 输入mask会改写专家索引，容量截断不等于无损接收

INT8的`ApplyXActiveMask`在mask非空时按token读取BOOL，把inactive行的全部TopK expert id改为`EP*expertPerRank`，随后写回原expertIdx GM并SyncAll；W4A8也有同职责实现。它不是只在临时mask副本上做过滤。调用方若需要复用路由id，须明确索引缓冲所有权、图重放时重新生成及其他消费者顺序；不能以Python schema只返回out和counts推导输入不会被改写。BF16入口没有该mask参数，不能借用此机制处理其padding。

GMM1/GMM2及dispatch/combine按maxOutputSize对各专家前缀和、rowStart与rows做截断，超过容量的部分不会仅因调整本rank窗口就自动重新分配。expert计数、实际接收行、被截断区间和最终有效输出需要分别核对，不能把“没有越过已分配GM”解释为无丢token或跨rank数值正确。

### HCCL窗口、工作区别名与同步顺序

`HcclShmem`在HCCL_COMM分支从GetHcclContext读取localUsrRankId、rankSize及winSize，并使用localWindowsIn/remoteRes的windowsIn寻址；非HCCL分支才使用独立SHMEM初始化与700MiB常量。不能以SHMEM_MEM、MAX_RANK_SIZE或Host worldSize单独证明真实HCCL窗口和rank拓扑。带offset/rank的重载只检查起始offset和rank范围，没有验证完整拷贝长度；无参数和单rank重载也不是通用边界验证器。

三族PeermemInfo将输入从0开始，per-token scale基址置于`AlignUp(winSize/3,512)`，combine输出紧随其后1MiB，专家计数矩阵从`winSize-2MiB`起；同步状态又使用末1MiB中的偏移。实际容量、对齐、矩阵和状态保留区域必须一起核对。Host头中的3MiB/204MiB常量并不能替代这些实际Device寻址，也不能仅据其名字认定本路径一定使用了对应绝对地址。

INT8 AIC分支先GMM1，再等V2C后GMM2；AIV负责routing、计数交换、拉远端token、SwiGLU和combine。INT8在`M*topK<=4096`时选CombineV2，否则选CombineV1，不能把一个shape的通信/计算重叠外推到另一分支。GMM与SwiGLU通过C2V/V2C和分组标志交接，末端先combine和清计数，再跨rank同步，最后按expandedRowIdx和probs做unpermute。BF16/W4还用subblock0发送状态、另一subblock等待状态并还原token的V2同步路线，不能把本地SyncAll当作全部rank的完成信号。

INT8的ptrC/ptrC2、ptrA/ptrPermutedToken共用地址；W4的两份GMM结果及两份INT4激活也分别复用，并按max(N,K)等表达式预留相应空间；BF16则给对应结果/激活分别推进workspaceOffset。原Host段记录的别名现在有明确Device对应关系，但本次没有证明所有事件交错、跨stream、空专家与图重放条件下均安全。改变tiling、分组粒度或事件时，必须连同这些存储寿命一起重建依赖图。

W4A8的FetchAndPreprocessInt8ToInt4把动态INT8激活拆成高低两部分：高部经乘1/16和CAST_FLOOR，低部由0x0F0F掩码并减8形成有符号INT4；后级epilogue把高部结果乘16、加低部和每输出通道辅助矩阵，再乘per-token scale。辅助bias不是可任意删掉的普通线性bias；它与[W4A8权重补偿](vllm_ascend_w4a8_moe_weight_contract.md)的制备合同配套。W4的IsSyncTask按剩余专家任务数为正2次幂选择交接点，也不是INT8/BF16固定epilogueGranularity的等价调度。

### Agent必须单独核验的边界

`CrossRankSync`通过缓存清理/失效后的状态轮询和SyncAll推进代数；V2使用0/1浮点状态切换、按rank收集后求和等待。所读轮询没有统一超时或失败转交策略，不能把通信错误当成某个rank可独自重试的普通函数异常。INT8计数allgather循环枚举dstEpIdx，但写端实际`shmem(localTokenPerExpertOffset,coreIdx)`传的是coreIdx；这应在具体EP/核分配下核实，不能仅从循环变量名字断言所有rank写址已正确，也不能在未执行时宣称已观察到死锁或数值故障。

unpermute按expandedRowIdx选择展开token，PROBS=true时在FP32累加TopK加权结果，再按目标dtype写回；它不代替expert id、有效映射和probs的输入验证。其小tiling直接做`m/topK`、除coreNum以及按tokens_splited_length继续除法，没有在该helper里完整处理零值。适配Agent应先证明空batch、过少token、零topK/核数已由可达caller排除或另走分支，再设计真实测试，不把此处未见保护直接写成所有运行路径必然崩溃。

验证先保存实际dtype/物理NZ、两组scale/bias、EP/核数、routing key、outer key、mask前后索引、maxOutputSize、winSize与全部共享区间，再验证空/高偏斜专家、非零INT4重建、不同Combine分支、stream与图重放。排查时分别定位路由排序、跨rank计数、远端搬运、GMM/epilogue与unpermute；没有编译、NPU、通信、精度或性能实测，不用本节替代完整算子producer或收益结论。
