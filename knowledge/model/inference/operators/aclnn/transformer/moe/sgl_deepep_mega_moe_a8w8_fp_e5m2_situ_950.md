---
type: Operator
title: "DeepEP MegaMoE MXFP8 E5M2 SiTU 950 ACLNN 算子知识"
description: "说明 aclnnMegaMoe 在950上的E5M2双GMM、SiTU分段tanh与动态MX量化、DEFAULT/LINEAR参数支路及MTE/URMA/UBX窗口同步，并保留固定9.2静态限制。"
tags: [task.implementation, task.lookup, topic.data_movement, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/doc/FUSED_DEEP_MOE.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/README.md
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/buffer.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/strategies/fused_strategy.py
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/README.md
    role: primary
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/version.cmake
    role: supporting
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/torch_extension/mega_moe.py
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/torch_extension/csrc/mega_moe.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/torch_extension/cann_ops_transformer/common/aclnn_common.h
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/torch_extension/cann_ops_transformer/common/hccl_common.h
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/common/torch_extension/comm_context.py
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/common/torch_extension/csrc/comm_context.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_api/aclnn_mega_moe.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/mega_moe_def.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/mega_moe_infershape.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/op_tiling/arch35/mega_moe_tiling.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/op_tiling/mega_moe_tiling_host.h
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/op_tiling/arch35_92/mega_moe_tiling_check.h
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/op_tiling/arch35_92/mega_moe_tiling_buffer_calc.h
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35/mega_moe_apt.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35/mega_moe_arch35.h
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35/mega_moe_wave_a8w8.h
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35/mega_moe_layered.h
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35/mega_moe_vf/mega_moe_vf.h
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/mega_moe_tiling.h
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/mega_moe_arch35_92_tiling_key.h
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/common/op_kernel/mc2_moe_context.h
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/common/op_kernel/mc2_kernel_utils.h
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/common/op_kernel/quantize_functions.h
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/common/op_kernel/mc2_exception_dump.h
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/CMakeLists.txt
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/cmake/third_party/ops-tensor.cmake
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/cmake/variables.cmake
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_arch_policy.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_constants.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_types.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_utils.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_gm_layout.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_sync.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_copy.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_gmm_common.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_gmm_epilogue_sync.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_layered_comm.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_mxfp8_utils.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_arch35_92_exception_dump_policy.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_workspace_reset.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_token_quant.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_send_mask.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_expert_count.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_token_dispatch.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_token_dedup.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_token_dispatch_dedup.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_gmm1_activation.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_gmm2_combine.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_gmm2_combine_dedup.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_unpermute.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_layered_dispatch.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_layered_combine.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_layered_combine_send.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/mega_moe_vf/mega_moe_layered_vf.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/gemm/block/block_scheduler_swizzle.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/gemm/tile/copy_gmm1_concat.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/block_epilogue_ub_layout.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/mega_moe_block_epilogue_activation_mx_quant.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/activation/activation_common.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/rowwise_mx_quant.h
    role: implementation
  - resource: https://atomgit.com/cann/ops-tensor/blob/fe1d9908c4eaff2943a3b6cea9c2467b8c427f18/include/blaze/gemm/block/block_mmad_qgmm_mx.h
    role: primary
  - resource: https://atomgit.com/cann/ops-tensor/blob/fe1d9908c4eaff2943a3b6cea9c2467b8c427f18/include/blaze/gemm/policy/dispatch_policy.h
    role: implementation
  - resource: https://atomgit.com/cann/ops-tensor/blob/fe1d9908c4eaff2943a3b6cea9c2467b8c427f18/include/blaze/gemm/block/block_mmad_decl.h
    role: implementation
  - resource: https://atomgit.com/cann/ops-tensor/blob/fe1d9908c4eaff2943a3b6cea9c2467b8c427f18/include/blaze/gemm/utils/common_utils.h
    role: implementation
  - resource: https://atomgit.com/cann/ops-tensor/blob/fe1d9908c4eaff2943a3b6cea9c2467b8c427f18/include/blaze/gemm/utils/layout_utils.h
    role: implementation
  - resource: https://atomgit.com/cann/ops-tensor/blob/fe1d9908c4eaff2943a3b6cea9c2467b8c427f18/include/blaze/gemm/tile/compute.h
    role: implementation
  - resource: https://atomgit.com/cann/ops-tensor/blob/fe1d9908c4eaff2943a3b6cea9c2467b8c427f18/include/blaze/gemm/tile/datamove.h
    role: implementation
  - resource: https://atomgit.com/cann/ops-tensor/blob/fe1d9908c4eaff2943a3b6cea9c2467b8c427f18/include/blaze/gemm/tile/tile_trait.h
    role: implementation
  - resource: https://atomgit.com/cann/ops-tensor/blob/fe1d9908c4eaff2943a3b6cea9c2467b8c427f18/include/blaze/gemm/tile/arch35/copy_gm_to_l1.h
    role: implementation
  - resource: https://atomgit.com/cann/ops-tensor/blob/fe1d9908c4eaff2943a3b6cea9c2467b8c427f18/include/blaze/gemm/tile/arch35/pad_mx_kl1.h
    role: implementation
  - resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/include/tensor_api/arch/cube/mmad_trait.h
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/version.cmake
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/include/tensor_api/arch/cube/cube_copy_trait.h
    role: implementation
  - resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/impl/tensor_api/arch/cube/mmad/mmad_impl/mmad.h
    role: implementation
  - resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/impl/tensor_api/arch/cube/mmad/mmad_impl/instruction.h
    role: implementation
  - resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/impl/tensor_api/arch/cube/l0c_to_ub/copy_impl/l0c_to_ub_data_copy.h
    role: implementation
  - resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/impl/tensor_api/arch/cube/l0c_to_ub/copy_impl/instruction.h
    role: implementation
  - resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/include/basic_api/kernel_operator_sys_var_intf.h
    role: implementation
  - resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/impl/basic_api/dav_3510/kernel_operator_sys_var_impl.h
    role: implementation
  - resource: https://gitcode.com/cann/hccl/blob/f9a2fd998475dcc78d0066660c3be5d8bd2f05bc/include/hccl_mc2.h
    role: primary
  - resource: https://gitcode.com/cann/hccl/blob/f9a2fd998475dcc78d0066660c3be5d8bd2f05bc/src/common/hccl_mc2.cc
    role: implementation
  - resource: https://gitcode.com/cann/hccl/blob/f9a2fd998475dcc78d0066660c3be5d8bd2f05bc/version.cmake
    role: supporting
  - resource: https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/pkg_inc/hcomm/hcomm_res_entity_defs.h
    role: primary
  - resource: https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/coll_communicator_mgr/api_c_adpt/coll_comm_res_c_adpt.cc
    role: implementation
  - resource: https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/coll_communicator_mgr/api_c_adpt/resource/channel_c_adpt.cc
    role: implementation
  - resource: https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/coll_communicator_mgr/resource_mgr/local/my_rank/my_rank.cc
    role: implementation
  - resource: https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/base_comm/resources/endpoint_pairs/channels/aiv/aiv_urma_channel.cc
    role: implementation
  - resource: https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/base_comm/resources/endpoint_pairs/channels/aiv/aiv_urma_transport.cc
    role: implementation
  - resource: https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/version.cmake
    role: supporting
  - resource: https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/include/aicore/hcomm/hcomm.h
    role: primary
  - resource: https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/include/aicore/hcomm/hcomm_common.h
    role: implementation
  - resource: https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/src/aicore/hcomm/common/hcomm_inner_def.h
    role: implementation
  - resource: https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/src/aicore/hcomm/common/hcomm_utils.h
    role: implementation
  - resource: https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/src/aicore/hcomm/impl/hcomm_impl.h
    role: implementation
  - resource: https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/src/aicore/hcomm/impl/platform_v310/hcomm_aiv_urma_def.h
    role: implementation
  - resource: https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/src/aicore/hcomm/impl/platform_v310/hcomm_aiv_urma.h
    role: implementation
  - resource: https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/src/aicore/hcomm/impl/platform_v310/hcomm_aiv_roce_def.h
    role: implementation
  - resource: https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/src/aicore/hcomm/impl/platform_v310/hcomm_aiv_roce.h
    role: implementation
  - resource: https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/scripts/package/build_package.sh
    role: implementation
  - resource: https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/docs/dependencies.md
    role: supporting
  - resource: https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/version.cmake
    role: supporting
  - resource: https://gitcode.com/cann/opbase/blob/de414d06cfb7bf2728a555bfb9fc1d26a4c83792/include/nnopbase/opdev/op_executor.h
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/impl/basic_api/utils/kernel_utils_constants.h
    role: header
  - resource: https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/base_comm/resources/endpoint_pairs/channels/aiv/aiv_ub_mem_channel.cc
    role: implementation
  - resource: https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/base_comm/resources/endpoint_pairs/channels/aiv/aiv_ub_mem_transport.cc
    role: implementation
  - resource: https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/legacy/ascend950/unified_platform/resource/buffer/remote_rma_buffer.cc
    role: implementation
  - resource: https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/legacy/ascend950/unified_platform/resource/buffer/local_ipc_rma_buffer.cc
    role: implementation
  - resource: https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/legacy/ascend950/unified_platform/resource/buffer/exchange_ipc_buffer_dto.h
    role: header
  - resource: https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/legacy/ascend950/unified_platform/resource/mem/user_remote_mem_getter.h
    role: header
  - resource: https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/activation/situglu_activation.h
    role: implementation
created_at: "2026-11-09T17:40:16Z"
updated_at: "2026-11-10T07:12:21Z"
platforms: ["950"]
cann_versions: ["9.2.0"]
---

# DeepEP MegaMoE MXFP8 E5M2 SiTU 950 ACLNN 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | CANN 9.2.0 公开两段式 `aclnnMegaMoeGetWorkspaceSize/aclnnMegaMoe`；SGL `FuseMode.MEGA_MOE=3`、`quant_mode="mx_fp8_e5m2"` |
| 计算语义 | BF16 X 动态分组 MXFP8 E5M2 → Dispatch → E5M2×E5M2 GMM1、FP32累加/Fixpipe到BF16 → FP32 SiTU到BF16 → 动态MXFP8 E5M2 → GMM2到BF16 → Combine、FP32 gates加权累加到BF16 |
| 输入输出 | X[B,H]、Y[B,H] BF16 ND；W1[N,H]、W2[H,N/2] E5M2，ND/ND；E8M0权重scale；ids[B,T] INT32；gates BF16或FP32；counts[L] INT32 |
| 执行类型 | 单个 `mega_moe`、MIX_AIC_1_2：AIC_CUBE双GMM、AIV_VECTOR量化/激活/路由/Unpermute、MTE或AIV URMA/RoCE通信；无SIMT/NDDMA kernel |
| Kernel 路线 | DEFAULT/LINEAR分别命中RunSiTUGLU<BF16,false,false/true>；R-001 MTE Wave（自动dispatch去重0/2）；R-002 Layered URMA；R-003 Layered UBX。ND、INT16/INT32路由索引、full/tail、wave与ring为同族参数 |
| 核心资源 | 通信对象持有自定义CCL窗口，含通信及本地计算区；框架workspace仅libAPI空间；L1 512KiB，L0A/B各64KiB，L0C256KiB；UB按阶段复用，固定GMM1双视图与SDK248KiB预算冲突见限制 |
| 来源闭包 | `source_closed`：入口、Host/POD/router、双GMM的ops-tensor实例、动态MX量化、MTE与分层业务、Host ChannelEntity、asc-comm URMA实现及RoCE不匹配终点均有固定源码。闭包不代表固定来源能成功构建或运行 |
| 验证状态 | 已完成源码闭包检查；本次知识提取未执行编译、真机、数值或性能测试。保留draft，无verified记录 |

## 接口与语义

### 计算语义

B为本rank本次实际token数，C为全rank一致的容量，H为hidden，T为top-k，R为EP大小，E为路由专家总数，L=E/R，N为W1行数，I=N/2。950 Mode3使用W1[N,H]、W2[H,I]的逻辑DN权重；不能套用A3 Mode3或950 Mode1的权重方向。每专家独立二维TensorList和一个三维堆叠TensorList均可达。业务合同要求每token的专家ID有效且不重复，各rank同时进入匹配调用；Host不扫描ID内容。

对BF16向量v，每32元素生成一个E8M0共享指数s和E5M2码q，记为MX(v)=(q,s)。GMM1/2通过MX MMAD联合消费激活与权重的E8M0 scale，并以FP32累加。计算顺序为：

```text
(qX,sX) = MX_E5M2(X_BF16)
C1[e]   = BF16_Fixpipe( MX_Mmad_FP32(qX[e],sX[e],W1_E5M2[e],SW1_E8M0[e]) )
G,U     = split(C1[e], axis=N, width=I)
G'      = min(FP32(G), clampLimit)
U'      = clip(FP32(U), -clampLimit, clampLimit)
A       = BF16_RINT_NO_SAT( TanhApprox(G'*invBeta)*(beta/(1+exp(-G'))) * UpBranch(U') )
(qA,sA) = MX_E5M2(A)
C2[e]   = BF16_Fixpipe( MX_Mmad_FP32(qA,sA,W2_E5M2[e],SW2_E8M0[e]) )
Y[b,:]  = BF16_RINT_SAT( Σ_{k=0..T-1} FP32(C2[e(b,k),row(b,k),:]) * FP32(gates[b,k]) )
```

clampLimit=FP32最大有限值。SiTU_DEFAULT的UpBranch(U)=U，SiTU_LINEAR的UpBranch(U)=lambda*TanhApprox(U*invAlpha)。两者由参数个数决定，属于同一SiTU数学域的有/无up软截断参数支路。SGL `activation="situ"` 映射到CANN `situglu`；Buffer默认beta=4、linear_beta=25，实际下传[4,25]。只显式传None可省略对应键；缺beta由CANN Python补1，缺linear_beta则只传[beta]走DEFAULT。原样字符串 `situglu` 不进入SGL的situ参数dict分支，CANN默认[1]；不能把这些默认都写成1或写成Mode1的SiTU参数。gate/up在GMM1的每个256列逻辑tile内以128列gate、128列up拼接传输，语义仍对应W1前后两半。GMM1 BF16落UB，激活BF16中间舍入之后再MX量化；不能合并成直接FP32→FP8。最终Combine明确先乘再加，不宣称FMA、逐位等价或非有限保证。



SiTU的950实现不是A3高阶Tanh API：`ComputeSituGluTanhPiecewiseApprox` 在FP32寄存器同时求两条表达式，然后按|z|≥0.60000002384185791016选择。设q=z²：

```text
P(z) = z + z*q*(-0.333327681 + q*(0.133152977
                  + q*(-0.0523039624 + q*0.0157396831)))
TanhApprox(z) = (|z| >= 0.60000002384185791016)
                ? 2/(1+exp(-2*z))-1 : P(z)
invBeta = FP32(1/beta); invAlpha = LINEAR ? FP32(1/lambda) : 1
gateFactor = TanhApprox(G'*invBeta) * (beta/(1+exp(-G')))
DEFAULT A = BF16_RINT_NO_SAT(gateFactor*U')
LINEAR  upSoft = lambda*TanhApprox(U'*invAlpha)
LINEAR  A = BF16_RINT_NO_SAT(gateFactor*upSoft)
```

实际以先计算float倒数、再Muls得到z；gate分支先计算beta/denominator再与tanh近似相乘，LINEAR先计算lambda*tanh再与gateFactor相乘。语义公式不承诺把这些次序改成直接除法后的逐位等价。多项式保留MulDstAdd/asc_madd顺序与系数，不能仅写抽象tanh当成完全相同的数值实现。3510未定义__ASC_FTZ__走Reg API，定义__ASC_FTZ__走C API的相同分段式；Reg与C API的Exp/Div/舍入/FTZ不承诺逐位一致。full vector、tail compute mask与store mask分开，补齐输出lane显式写BF16零；随后MX量化仅提交valid row/column。所有gates在最终Combine乘权，本tkw0不在SiTU内预乘。

MX量化从BF16指数位 `bits & 0x7f80` 取每32元素最大值；E5M2格式常数0x0780。共享指数位为max(maxExp,0x0780)-0x0780，E8M0输出为其右移7位；零组输出scale=0且inverse=0；maxExp=0x7f80时scale=0xff、inverse位0x7f81。一般inverse位为0x7f00-shared，shared=0x7f00时特殊取0x0040。BF16乘inverse，再扩展FP32，经SAT/RINT转换到E5M2。该路径与其它DeepEP的per-token FP8 NO_SAT转换不同，不能互换常数、round或scale布局。激活BF16转换自身为NO_SAT/RINT，FTZ C API分支调用 `asc_float2bfloat16_rn`；最终Unpermute为RINT/SAT。

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| context | 一维6156个INT32的POD存储 | INT32 | NPU Tensor拥有24624B Mc2MoeContext字节；内含窗口/channel仍由通信资源对象拥有，不能复制成另一版本POD |
| x/y | [B,H] ND | BF16 | SGL公开1≤B≤C；H∈[1024,8192]且H%64=0；SGL 950使用实际B，不走A3 padding/mask/slice |
| topk_ids | [B,T] ND | INT32 | T∈[1,32]；SGL仅对ids执行.int()；内容有效且同token不重复是调用前提 |
| topk_weights | [B,T] ND | BF16或FP32 | SGL原样传入；950模板使用DTYPE_TOPK_WEIGHTS，BF16在Unpermute显式转FP32，不能按A3硬读FP32 |
| weight1/weight2 | L个[N,H]/[H,I]，或单个[L,N,H]/[L,H,I]；两侧均ND | FLOAT8_E5M2 | N∈[512,8192]、N%256=0；I=N/2；所有专家、W1/W2同dtype/组织形式，不允许混合权重数学域 |
| weight_scales1/2 | 每专家[N,ceil(H/64),2] / [H,ceil(I/64),2]，堆叠时前置L | E8M0、ND | 每32元素一个scale，两scale配对编码K64；末维必须2，列表长度/shape逐侧一致 |
| expert_token_nums | [L] ND | INT32 | 本rank每专家接收计数；总接收量受max_recv上界裁剪边界约束 |
| moe_expert_num / ep_world_size | 标量 | INT64 | R∈[2,1024]，R≤E≤2048，E%R=0，1≤L≤1024 |
| num_max_tokens_per_rank | 标量C | INT64 | SGL由通信对象缓存键固定；Host 0表示取B，否则C≥B，最终C≤UINT32_MAX；Layered不接受零B/零C |
| max_recv_token_num | 标量Mmax | INT64 | SGL传0，Host默认取C·R·min(T,L)；显式值非负且≤UINT32_MAX，只有Layered额外要求不超过该几何上界，并受其INT32容量约束 |
| dispatch_quant_mode / out_dtype | 标量 | INT64 | 当前为4 / E5M2；PyTorch E5M2 dtype编号与GE dtype编号不同，经C++映射，不直接拼数值tiling key |
| activation / activation_params | SGL situ→CANN situglu；[beta]或[beta,lambda] | 字符串/float数组 | beta及可选lambda均有限且>0；SGL默认[4,25]；单参数DEFAULT、双参数LINEAR；SwiGLU为另一独立卡 |
| combine_quant_mode / topk_weights_type / combine_comm_mode | 0 / 0 / 0 | INT64 | SGL未暴露其它值；仍允许Host自动dispatch-only dedup=2，不能因combine_comm_mode=0删去该路线 |
| topo_type / rank_num_per_server | 0/1/2 / domain大小 | INT64 | SymmBuffer实际探测生成；0=MTE，1=URMA，2=URMA+RoCE UBX；domain整除R，MTE取R |
| scales / x_active_mask / mask_buffer | absent | — | 动态MX域不提供预量化scales；SGL 950无active mask。rank mask仅A3扩展边界 |
| bias / shared weights及scale/bias | absent | — | 本MX可执行域必须为空；SGL可以转发bias，但MX C++检查拒绝非空bias。公开CANN较宽shared异构/预量化/去重合同留在API Reference，不混成本数学域 |
| activation_out_dtype / transpose_weight1/2 / weight1_interleave | 未暴露属性 | — | 公开wrapper固定UNDEFINED/false/false/0；Host执行其约束 |

### 入口与版本

入口为ops-transformer公开ACLNN，SGL调用其Python/Torch扩展；SGL仓无Mode3自有ACLNN launcher body。`FUSED_DEEP_MOE.md` Mode3及DeepEP README明确CANN9.2.0，覆盖通用README较早9.0/9.1提示；ops-transformer固定version.cmake为9.2.0，OpDef注册ascend950。`mega_moe_apt.cpp` 以SDK/HCOMM版本头≥90200000开启Layered，以Tensor API版本条件开启主body；缺版本头或宏不成立时对应body被预处理移除，不能称运行支持。

核心依赖是ops-transformer CMake固定fe1d9908的ops-tensor Blaze；CATLASS2是工程其它实现的依赖，本E5M2选中BlockMmad来自ops-tensor，不能把CATLASS A3核心当成950实现。asc-comm9.2分支的头由package脚本映射至 `asc/include/adv_api/hcomm`，实现映射至 `asc/impl/adv_api/detail/hcomm`，comm_api层用符号链接供相对include解析。该映射与HCOMM Host声明比对是源码证据，未安装或二进制ABI实测。与固定SDK9.2的copy trait、与RoCE batch的静态冲突均保留在本卡。

配套公开合同见[DeepEP MegaMoE API](../../../../apis/deepep/deepep_mega_moe.md)。

## Host/Launcher 执行流程

### 参数校验与前处理

SGL MegaMoeStrategy按quant_mode选择dispatch4/E5M2，取W2末维I及实际B，校验非空权重列表并获取按(E,C,T,H,I,量化模式/输出类型)缓存的SymmBuffer。ids转INT32，gates无cast，权重/scale已由调用者准备；本路径无A3 padding、输入mask、结果截片。

Python `npu_mega_moe` 归一化TensorList、activation及默认params；C++ `NpuMegaMoe` 取当前SoC、检查MX输入/非空bias、构造ACL Tensor/TensorList、分配BF16 Y与INT32 counts，原样传gates；E5M2无需FP4 descriptor reinterpret。`ACLNN_CMD` 用当前NPU stream执行workspace查询/分配和第二阶段。ACLNN wrapper判必选指针、E/R正值、maxRecv非负，创建executor，并为缺省动态参数创建相应dtype/format的空TensorList；shared空占位复用主权重dtype/format，仅用于原型匹配，不产生shared计算。转交生成的aclnnInner桥，activation参数的有限性/个数由Host处理。

Host `MegaMoeTilingFuncImplArch35` 按源码顺序：必需tensor指针→不支持optional→attr指针→独立topology/EP/comm/量化/activation/topk attrs→scales判空→weight/scale组织、dtype、format、shape→专家执行模式与E/L/H/N→平台AIC/AIV/UB正值→容量C/Mmax→MTE dedup容量及收益→wave/adaptive buffer→CCL容量→workspace→block/key。任一步GRAPH_FAILED返回到框架，不启动业务body。不能依赖更晚shape检查保护更早的类型/整数转换。

### 参数、Workspace 与生命周期

SymmBuffer空comm_alg优先探测UB_MEM；仅两层快捷条件走MTE。否则从内层向外扩张连续rank的UB域；全R可UB_MEM得topo0；域内需UB_CTP，跨域全UB_RTP得topo1；不使用多channel、连续域且跨域RoCE连通则topo2；不满足组合TORCH_CHECK失败。rank/domain、端点协议和CCL尺寸必须全rank一致。

自定义窗口容量先经 `get_mega_moe_ccl_buffer_size`：实际核数/权重尚未知，`BuildMemoryBudgetParams` 按AIC36、shared4、较窄GELU输出所需的较大wave行预算，以及shared独立W4量化上界计费；本E5M2且topkWeightsPrefetch=false令 `reserveGmm1Output=false`、`reserveCumsum=false`，不同于E4M3分配预算。MTE分别算dedup关闭/开启并取max。这是分配预算，不代表本调用执行shared/GELU。Host随后用实际参数重算所需长度；Layered WorkspaceInitializeUrma仍在其实际布局中单独建立prefix/cumsum，不能用预算开关删除消费者。实际 `framework_workspace = platform.GetLibApiWorkSpaceSize()`，与CCL中的业务数据区不同；kernel不使用workspaceGM装双GMM中间结果。

CCL由CommContextManager经设备大页优先malloc、首次memset0、HcclCommMemReg DEVICE/tag、AIV engine context与channel创建管理。remote tag匹配恢复peer窗口地址。HCOMM将URMA Host channel转换为device ChannelEntity指针；从HCOMM256B头到asc-comm对应字段的映射见POD。`CreateContext` 以at::empty分配6156个INT32的NPU Tensor，拥有24624B POD存储；`CopyContextToTensor` 的from_blob只是栈上Host结构的临时视图，经copy_写入该Tensor。`GetLocalBufferTensor` 才是对CCL窗口的from_blob非拥有视图。POD内的peer/window/channel地址均不转移资源所有权，context及视图消费必须处于通信对象/窗口有效期内；Y/counts为本次Torch输出，executor临时空TensorList及workspace归executor/调用框架。Torch copy_/stream内部保证为框架边界，本次未安装验证。

destroy可见实现先device synchronize，再清空memHandle并free自定义窗口；该层未见显式deregister/channel/engine context释放，不补造释放保证。复用cache命中的GetOrCreateContext只更新默认HCCL窗口size，未重新填充本次fresh CommContext；后续CopyContextToTensor仍从该结构复制地址，属于可见cache-hit边界，未复现故障。不得跨并发调用重用同一带计数/ready的窗口而假设自动隔离。

### 启动图与失败传播

```text
SGL Buffer.fused_deep_moe -> MegaMoeStrategy
 -> ops Python npu_mega_moe -> C++ NpuMegaMoe/ACLNN_CMD
 -> aclnnMegaMoeGetWorkspaceSize -> generated aclnnInner bridge
 -> MegaMoeTilingFuncArch35 -> MegaMoeTilingFuncImplArch35
 -> CommitTilingResult: CCL check, libAPI workspace, CalcTschBlockDim(AIV,AIC,AIV),
                        scheduleMode=1, GET_TPL_TILING_KEY(...)
 -> aclnnMegaMoe(workspace,size,executor,currentStream)
 -> mega_moe<weight/shared/dispatch/out/combine/comm/prefetch/index>
    -> R-001 MegaMoeMteWave -> MegaMoeA8W8Wave
    -> R-002 MegaMoeLayered<...,LayeredUrmaComm>
    -> R-003 MegaMoeLayered<...,LayeredUbxComm> / known fixed-source static mismatch
```

单个MIX kernel内各逻辑AIC配AIV0/AIV1。3510 `GetBlockIdx` 在AIV上等于raw get_block_idx()*get_subblockdim()+get_subblockid()；当前MIX1:2硬件策略另以SubBlockIdx区分0/1角色，不将raw核号和全物理AIV编号混用。当前950明确选择channel backend，KFC兼容前端的HCCL声明/动态Inner转发只作为公共工程接入边界，不宣称执行A3 KFC业务。框架生成的aclnnInner调度桥、硬件asc_mmad_mx/拷贝/门铃原语是明确框架与硬件终点；业务量化、GMM块循环、通信WQE/CQ与同步body均有源码。Host失败、模板/版本无body终点、已见静态接口冲突分开记录，不编造具体codegen诊断或真机错误。

## Route 与参数设计

### 分核与资源计算

记A_q(x)=ceil(x/q)q，d=2当C·T≤32768，否则d=4；ids仍INT32。Mmax=C·R·min(T,L)（SGL maxRecv=0），每专家有效接收M_e≤C·R依赖有效且不重复ID，不能用总Mmax替代该前提。g=max(ceil(4·AIC/ceil(N/256)),ceil(AIC/ceil(H/256)))。MTE若g>0、Mmax>3g·256且combineQuant=0，启用3-wave数据ring：dispatch仅dedup0可ring，activation/GMM2可在dedup0/2 ring。元数据及ready不因ring缩小。Layered全量GM，不启用MTE ring。

GMM1/2逻辑tile均M256×N256；GMM1由两个N128权重半片组成。K0=128，L1数据K256、scale K512，2级L1流水。尾M<256且K>256可计算A16(M)并试探L1K512/更大scale覆盖：两倍数据+两倍scale≤半L1且单scale≤64KiB，scale factor同时受剩余L1、各scale64KiB、floor(K/KL1)、127限制，仅当增加KL1或减少scale轮数才采用；否则回基准。N、K的有效tail由view及K64 padding处理。

MTE SendMask把E连续均分到全部AIV，前E%AIV核多一个expert；给extra/normal两组独立buffer配置。可用UB减reset≤8192B、双输入/双量化输出、2048B MX scratch、累计表后，以Bsend(初值10240)、d字节indices及mask/index ring反推2..6槽，再扩大batch且向下A256。Dispatch固定prefix/count表后，初值Brecv12288，扣dedup预留时必须先扣，再选2..6 record+32B metadata槽及batch；启动轮使用选中槽，稳态只用前两槽并保持地址。Unpermute先以8192个gate item基准选2..6输入槽，再扩大gate batch，full/tail两配置；其精确UB式见R-001。

### Route 选择

以下K(i,c)为 `GET_TPL_TILING_KEY(E5M2,E5M2,4,3,3,0,c,false,i)` 的九字段tuple；权重、gates dtype及ND由输入原型额外注入，不把tuple字段与PyTorch dtype编号混用。i=0为INT16，i=1为INT32；c=0为MTE、c=1为Layered。dedup、activation及topo1/2不单独编码进该key，必须连同POD消费。

| 顺序 | Route | Key/模板 | 精确选择条件与优先级 | 不适用去向 |
|---:|---|---|---|---|
| 1 | R-001 MTE Wave | K(i,0)，i由C·T≤32768裁决 | 当前E5/SiTU公共合同；topo_type=0；Tensor API body可用；ND/ND；dedup经Host自动为0/2 | topo1/2→后续；Host输入不合法失败 |
| 2 | R-002 Layered URMA | K(1,1)、LayeredUrmaComm | topo_type=1；BF16动态MX；域整除R；容量非零、INT32上界；SDK/HCOMM版本宏均≥9.2 | topo2→R-003；版本宏缺失为无body终点 |
| 3 | R-003 Layered UBX | K(1,1)、LayeredUbxComm | topo_type=2；同Layered容量；域内UB_CTP、跨域RoCE；Host实际可生成 | 自有业务body存在；固定asc-comm RoCE batch/Lock/Unlock不匹配，为静态terminal；无可见fallback |

```text
SGL math=mx_fp8_e5m2 + situ/situglu + no shared/prequant/explicit dedup
 -> validate Host contracts
 -> auto topology0: MTE; key index=(C*T<=32768?0:1); auto dedup2 -> capacity/benefit guard -> 2 or0
 -> auto topology1/2: key comm1,index1, Layered-enabled version gate
      -> topo2 LayeredUbxComm (record fixed-source interface conflict)
      -> topo1 LayeredUrmaComm
 -> invalid attrs/layout/capacity: fail; macro/body absent: no operation body
```

### 模板/实现执行矩阵

| Route | key/selector | dtype/shape/platform 完整命中条件 | 执行族与 kernel 节点 | 实际模板/body | 内存与同步特征 | tail/fallback |
|---|---|---|---|---|---|---|
| R-001 | K(0,0)、K(1,0)各覆盖ND、BF16/FP32 gates、dedup0/2 | 950，X/Y BF16，W1/2 E5同类，scale E8M0，公共H/N/E/T/C/Mmax合同，topo0 | AIV准备/MTE → AIC GMM1+AIV0激活量化 → AIC GMM2+AIV1回传 → all-AIV Unpermute | MegaMoeA8W8Wave；Config<false,0,E5,E5,BF16,E8M0,E8M0,false,false,false,false,true> | 3-wave ring条件化；mode4 AIC↔AIV；跨rank窗口计数 | validM/N/K；空专家跳过；公开B≥1；额外原始零shape有Host除零边界 |
| R-002 | K(1,1)，ND、两gates类型 | 同公共合同；topo1；Layered版本宏；B/C>0，C·T/Mmax≤INT32 | AIV URMA mask/relay → AIC GMM1/AIV0激活 → AIC GMM2 → AIV1 URMA Combine → Unpermute | MegaMoeLayered；GMM1 Config末端IsLayered=false/IsWaveFlagGrained=true，GMM2为true/true；LayeredUrmaComm | 全量GM，256行group原子计数；channel Lock→batch/Drain→Unlock | mask tail/count裁剪；5个接收slot；无MTE fallback |
| R-003 | K(1,1)，runtime topo2 | R-002公共形状/版本，domain内CTP、跨domain RoCE | 自有相同MIX图，UBX按peer协议分流；固定依赖在RoCE批处理实例化终点冲突 | MegaMoeLayered<...,LayeredUbxComm>；明确不补造RoCE batch算法 | 共用R-002业务窗口/UB；RoCE已有channel WQE/CQ实现，仅作实际可读边界 | static_assert及缺batch成员，不宣称已复现运行错误 |

### 隐藏性能 Guard

| Guard | Host/Tiling 条件 | Device/资源原因 | 影响 Route | 不满足时去向 | 源码符号 |
|---|---|---|---|---|---|
| 路由索引窄化 | C·T≤32768 | 过滤token/topk位置可用INT16，减少route GM/UB；专家ID仍INT32 | R-001 | INT32模板 | UseInt16TopkIndex/CalcTopkIndexTypeBytes |
| 自动dispatch-only dedup容量 | ceil(C/128)≤min(54KiB/(12T),512,4KiB/4,4KiB/4) | 组描述符/成员表在固定UB内 | R-001 | 清dispatch去重bit→0 | CheckMteDedupCapacity |
| 自动dedup收益 | 预期distinctRank=R(1-(1-1/R)^T)，saved=C·T·(1-distinctRank/T)·H（FP8每元素1B）；R=4比较saved/L与hiddenDim≤2048?0.30MiB:2.10MiB，否则比较saved与60MiB | 只在源码估计通信节省足够时付出预分组/描述符成本；阈值不是本次测量 | R-001 | 清dispatch bit→0 | ApplyDedupBenefitGate |
| ring | topo0、combine0、g>0、Mmax>3g256；dispatch额外dedup0 | 覆盖三个wave生命周期，dedup FIRST fanout需完整输入 | R-001 | 全量各stage GM | CalcCclStageRingConfig |
| GMM2错一wave | B≥4096 | 三角色保持相同延迟/尾部drain，改变重叠调度 | R-001 | 同wave GMM2 | MegaMoeA8W8Wave::Process |
| L2 bypass | 单expert全范围且M≤tileM；本ND路径还需K%256=0；ScaleB片宽2N字节%128=0 | 单次消费可选cache bypass；热wave权重保留 | 全部业务body | 默认cache模式 | GmmKernel Config/weight view |
| Layered H/cap | H%64=0，B/C>0，C·T与最大接收≤INT32 | mask/index/relay、256行group槽布局 | R-002/003 | Host失败 | CheckAndSetNumMaxTokensPerRank/GetMegaMoeCclBufferSize |
| 固定源API差异 | ops-tensor构造gm_to_l1_trait{true}，SDK9.2该trait为空 | 包含的非依赖初始化式与固定SDK声明不相容 | 全部含Cube模板 | 已知静态边界，无源码fallback | CopyGM2L1TraitPreAllocation |
| RoCE批处理差异 | topo2选择roce_，Hcomm要求UB_CTP才支持MakeBatchHandle/Lock/Unlock | 不存在可替代RoCE batch specialization | R-003 | 静态terminal | Hcomm<COMM_PROTOCOL_ROCE>/LayeredUbxComm |

### POD/ABI

以下sizeof/alignof/offset为固定源码自然C++布局推导（64位指针、常规8字节对齐），未执行编译布局验证或安装二进制ABI验证。字段按各自声明逐行列出；数组是一项字段。嵌套字段offset相对其结构首址，不能将“未读取”字段从序列化POD删除。
| 结构 | 字段 | 类型/位宽 | ABI 布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| CclCommLayoutParams(80B/align8) | numMaxTokensPerRank | I64 | 0B | 容量 | SetCclLayoutParams=C | CalcCclCommLayout/numMaxTokensPerRank | 当前域有效 |
| CclCommLayoutParams(80B/align8) | topK | I64 | 8B | 路由槽 | SetCclLayoutParams=T | CalcCclCommLayout/topK | 当前域有效 |
| CclCommLayoutParams(80B/align8) | h | I64 | 16B | 数据宽 | SetCclLayoutParams=H | CalcCclCommLayout/h | 当前域有效 |
| CclCommLayoutParams(80B/align8) | moeExpertPerRank | I64 | 24B | 本地专家 | SetCclLayoutParams=L | CalcCclCommLayout/moeExpertPerRank | 当前域有效 |
| CclCommLayoutParams(80B/align8) | epWorldSize | I64 | 32B | rank | SetCclLayoutParams=R | CalcCclCommLayout/epWorldSize | 当前域有效 |
| CclCommLayoutParams(80B/align8) | yDtypeSize | I64 | 40B | BF16字节 | SetCclLayoutParams=2 | CalcCclCommLayout/yDtypeSize | 当前域有效 |
| CclCommLayoutParams(80B/align8) | elemsPerByte | U32 | 48B | 元素/B | SetCclLayoutParams=1 | QuantRecord/GM布局 | 当前域有效 |
| CclCommLayoutParams(80B/align8) | topkWeightsPrefetch | bool | 52B | 开关 | SetCclLayoutParams=false | 记录中gate区 | inactive，不加入gates |
| CclCommLayoutParams(80B/align8) | isQuantCombine | bool | 53B | 开关 | SetCclLayoutParams=false | Combine窗口 | 无量化Combine |
| CclCommLayoutParams(80B/align8) | topoType | I64 | 56B | 枚举 | SetCclLayoutParams=0/1/2 | CalcCclCommLayout | 三Route不同窗口 |
| CclCommLayoutParams(80B/align8) | serverNum | I64 | 64B | 域数 | R/rankNumPerServer | Layered relay | MTE值仅布局参数 |
| CclCommLayoutParams(80B/align8) | serverCombineReduce | bool | 72B | 开关 | false | Layered布局分支 | inactive |
| CclStageRingConfig(16B/align8) | dispatch | bool | 0B | 开关 | CalcCclStageRingConfig: dedup0才可开 | dispatch rows | Layered全false |
| CclStageRingConfig(16B/align8) | gmm1 | bool | 1B | 开关 | CalcCclStageRingConfig: ring共同条件 | GMM1 rows | Layered全false |
| CclStageRingConfig(16B/align8) | activation | bool | 2B | 开关 | CalcCclStageRingConfig: ring共同条件 | 激活rows | Layered全false |
| CclStageRingConfig(16B/align8) | gmm2 | bool | 3B | 开关 | CalcCclStageRingConfig: ring共同条件 | GMM2 rows | Layered全false |
| CclStageRingConfig(16B/align8) | rows | U64 | 8B | 行 | 3*g*256或0 | stage modulo row | flags/meta不缩小 |
| CclComputeLayoutParams(152B/align8) | ring | CclStageRingConfig | 0B/16B | 嵌套 | CalcCclStageRingConfig | WorkspaceLayout/各stage | 见逐字段表 |
| CclComputeLayoutParams(152B/align8) | topoType | I64 | 16B | 枚举 | Host CheckAndSet*/SetCclLayoutParams=topo0/1/2 | WorkspaceLayout/stage topoType | 跨rank容量需一致 |
| CclComputeLayoutParams(152B/align8) | maxOutputSize | I64 | 24B | 行 | Host CheckAndSet*/SetCclLayoutParams=Mmax | WorkspaceLayout/stage maxOutputSize | 跨rank容量需一致 |
| CclComputeLayoutParams(152B/align8) | h | I64 | 32B | 元素 | Host CheckAndSet*/SetCclLayoutParams=H | WorkspaceLayout/stage h | 跨rank容量需一致 |
| CclComputeLayoutParams(152B/align8) | hiddenDim | I64 | 40B | 元素 | Host CheckAndSet*/SetCclLayoutParams=N | WorkspaceLayout/stage hiddenDim | 跨rank容量需一致 |
| CclComputeLayoutParams(152B/align8) | bs | I64 | 56B | 行 | Host CheckAndSet*/SetCclLayoutParams=B | WorkspaceLayout/stage bs | 本rank实际B，变长bs可不同；C/topK等容量条件仍须跨rank一致 |
| CclComputeLayoutParams(152B/align8) | moeExpertPerRank | I64 | 64B | 专家 | Host CheckAndSet*/SetCclLayoutParams=L | WorkspaceLayout/stage moeExpertPerRank | 跨rank容量需一致 |
| CclComputeLayoutParams(152B/align8) | epWorldSize | I64 | 72B | rank | Host CheckAndSet*/SetCclLayoutParams=R | WorkspaceLayout/stage epWorldSize | 跨rank容量需一致 |
| CclComputeLayoutParams(152B/align8) | aicNum | I64 | 80B | 核 | Host CheckAndSet*/SetCclLayoutParams=平台AIC | WorkspaceLayout/stage aicNum | 跨rank容量需一致 |
| CclComputeLayoutParams(152B/align8) | sharedExpertNum | I64 | 88B | 专家 | Host CheckAndSet*/SetCclLayoutParams=0 | WorkspaceLayout/stage sharedExpertNum | inactive |
| CclComputeLayoutParams(152B/align8) | mGroupsPerWave | I64 | 96B | 256行组 | Host CheckAndSet*/SetCclLayoutParams=g | WorkspaceLayout/stage mGroupsPerWave | 跨rank容量需一致 |
| CclComputeLayoutParams(152B/align8) | combineSyncSlotCountPerExpert | I64 | 104B | 64B槽 | Host CheckAndSet*/SetCclLayoutParams=Layered:max(ceil(CR/256),AIV/2);MTE0 | WorkspaceLayout/stage combineSyncSlotCountPerExpert | 跨rank容量需一致 |
| CclComputeLayoutParams(152B/align8) | serverNum | I64 | 112B | 域 | Host CheckAndSet*/SetCclLayoutParams=R/domain | WorkspaceLayout/stage serverNum | 跨rank容量需一致 |
| CclComputeLayoutParams(152B/align8) | numMaxTokensPerRank | I64 | 120B | 行 | Host CheckAndSet*/SetCclLayoutParams=C | WorkspaceLayout/stage numMaxTokensPerRank | 跨rank容量需一致 |
| CclComputeLayoutParams(152B/align8) | topK | I64 | 128B | 槽 | Host CheckAndSet*/SetCclLayoutParams=T | WorkspaceLayout/stage topK | 跨rank容量需一致 |
| CclComputeLayoutParams(152B/align8) | activationOutputDivisor | U32 | 48B | 除数 | SetCclLayoutParams=2 | I=N/2 | 本SiTU |
| CclComputeLayoutParams(152B/align8) | dedupMode | I32 | 136B | bit模式 | MTE自动0/2；Layered0 | dispatch/fanout | 非显式combine去重 |
| CclComputeLayoutParams(152B/align8) | combineQuant | bool | 140B | 开关 | SetCclLayoutParams=false | WorkspaceLayout/Combine | 当前E5无此分支 |
| CclComputeLayoutParams(152B/align8) | topkWeightsPrefetch | bool | 141B | 开关 | SetCclLayoutParams=false | WorkspaceLayout/量化记录 | 当前E5无此分支 |
| CclComputeLayoutParams(152B/align8) | dispatchFp4 | bool | 142B | 开关 | SetCclLayoutParams=false | WorkspaceLayout/record字节 | 当前E5无此分支 |
| CclComputeLayoutParams(152B/align8) | reserveGmm1Output | bool | 143B | 开关 | SetCclLayoutParams=false | WorkspaceLayout/GMM1 GM | 当前E5无此分支 |
| CclComputeLayoutParams(152B/align8) | reserveCumsum | bool | 144B | 开关 | SetCclLayoutParams=false | WorkspaceLayout/GM前缀 | 当前E5无此分支 |
| CclComputeLayoutParams(152B/align8) | sharedInputIndependent | bool | 145B | 开关 | SetCclLayoutParams=false | WorkspaceLayout/shared输入 | 当前E5无此分支 |
| CclComputeLayoutParams(152B/align8) | sharedInputElementsPerByte | U32 | 148B | 元素/B | SetCclLayoutParams=1 | shared布局 | shared0，不产生slice |
| MegaMoeTilingData(608B/align8) | comm | CclCommLayoutParams | 0B | 80B | SetCclLayoutParams | 通信layout | 逐字段见上 |
| MegaMoeTilingData(608B/align8) | compute | CclComputeLayoutParams | 80B | 152B | CheckAndSet*/SetCclLayoutParams | WorkspaceLayout/Process | 逐字段见上 |
| MegaMoeTilingData(608B/align8) | blockNumPerEP | U32 | 232B | 核 | CheckAndSetPlatformParams=max(1,AIC/R) | 跨核配额 | 实际资源值 |
| MegaMoeTilingData(608B/align8) | blockAivNum | U32 | 236B | 核 | CheckAndSetPlatformParams | 全部AIV分核 | 当前MIX1:2 |
| MegaMoeTilingData(608B/align8) | combineQuantMode | I64 | 240B | 枚举 | CheckAndSetCombineQuantMode=0 | GMM2/Unpermute | 本域0 |
| MegaMoeTilingData(608B/align8) | clampLimit | F32 | 248B | 数值 | SetActivationAttrParams=FLT_MAX | RunSiTUGLU | 正值启用clip |
| MegaMoeTilingData(608B/align8) | moeGmmMode | U8 | 252B | 枚举 | CheckAndSetExpertGmmModes= A8W8 ND | GMM Config | 由weight format |
| MegaMoeTilingData(608B/align8) | sharedGmmMode | U8 | 253B | 枚举 | 共享缺省模式 | shared router | shared0 inactive |
| MegaMoeTilingData(608B/align8) | dispatchBufferConfig | DispatchConfig | 256B | 16B | SetAdaptiveBufferConfigs | DispatchBuffInit | 见子结构 |
| MegaMoeTilingData(608B/align8) | sendMaskConfigForCoreWithExtraExpert | SendConfig | 272B | 16B | SetTopkValidIndexBufferConfigs | SendAndQuantBuffInit | extra核 |
| MegaMoeTilingData(608B/align8) | sendMaskConfigForCoreWithoutExtraExpert | SendConfig | 288B | 16B | SetTopkValidIndexBufferConfigs | SendAndQuantBuffInit | 其余核 |
| MegaMoeTilingData(608B/align8) | sendMaskCoreCountWithExtraExpert | U32 | 304B | 核 | E%AIV | SendAndQuantBuffInit | expert均分余数 |
| MegaMoeTilingData(608B/align8) | unpermuteConfigForFullTokenChunk | UnpermuteConfig | 308B | 24B | SetUnpermuteBufferConfigs | UnpermuteBuffInit | full |
| MegaMoeTilingData(608B/align8) | unpermuteConfigForTailTokenChunk | UnpermuteConfig | 332B | 24B | SetUnpermuteBufferConfigs | UnpermuteBuffInit | tail |
| MegaMoeTilingData(608B/align8) | unpermuteFullTokenChunkCoreCount | U32 | 356B | 核 | SetUnpermuteBufferConfigs | Unpermute配置选择 | 完整chunk数 |
| MegaMoeTilingData(608B/align8) | topkWeightsPrefetch | I32 | 360B | 开关 | CheckAndSetTopkWeightsType=0 | record/模板 | inactive |
| MegaMoeTilingData(608B/align8) | actMode | U8 | 364B | 枚举 | SetActivationAttrParams=SITU | RunGatedActivationTile | 单/双参数均可达 |
| MegaMoeTilingData(608B/align8) | actSubMode | U8 | 365B | 枚举 | SetActivationAttrParams=DEFAULT或LINEAR | RunSiTUGLU<...,false/true> | 按参数个数，不额外编码key |
| MegaMoeTilingData(608B/align8) | activationAlpha | F32 | 368B | lambda | 双参数=activationParams[1]，单参数=0 | LINEAR RunSiTUGLU up软截断 | 单参数Device改用alpha=1且不做up tanh |
| MegaMoeTilingData(608B/align8) | activationBeta | F32 | 372B | beta | activationParams[0] | 两SiTU子模式gate软截断 | Host要求有限且>0 |
| MegaMoeTilingData(608B/align8) | isPerExpertWeightTensor | bool | 376B | 开关 | CheckWeight组织2D/3D | GetExpertTensor | 两组织均可 |
| MegaMoeTilingData(608B/align8) | rankNumPerServer | U32 | 380B | rank/域 | CheckAndSetRankNumPerServer | Layered peer/domain | 必须与context一致 |
| MegaMoeTilingData(608B/align8) | a8w4L1Layout | MegaMoeL1Layout | 384B | 208B | CommitTilingResult/CalcMegaMoeL1Layout | 本E5Generic不读 | producer存在但inactive |
| MegaMoeTilingData(608B/align8) | preQuantTileTokens | U32 | 592B | token | 动态量化=0 | TokenQuant预量化分支 | inactive |
| MegaMoeTilingData(608B/align8) | preQuantStageBytes | U32 | 596B | B | 动态量化=0 | 预量化UB | inactive |
| MegaMoeTilingData(608B/align8) | dispatchTableUbBaseAddr | U32 | 600B | B | SetAdaptiveBufferConfigs=0 | Arch92常驻表 | 950当前分支inactive |
| MegaMoeDispatchBufferConfig(16B/align4) | routeItemsPerBatch | I32 | 0B | item | Calc*BufferConfig=A256(batch) | mask/index循环 | extra/normal可不同；不可固定6 |
| MegaMoeDispatchBufferConfig(16B/align4) | routeBatchCount | I32 | 4B | 轮 | ceil(sendTotal/batch) | SendMask/Dispatch循环 | extra/normal可不同；不可固定6 |
| MegaMoeDispatchBufferConfig(16B/align4) | bufferCount | I32 | 8B | 槽 | 自适应2..6 | slot/event ring | extra/normal可不同；不可固定6 |
| MegaMoeDispatchBufferConfig(16B/align4) | copyBufferBytes | U32 | 12B | B | CalcDispatchCopyBufferBytes | UB槽地址 | extra/normal可不同；不可固定6 |
| MegaMoeSendMaskBufferConfig(16B/align4) | routeItemsPerBatch | I32 | 0B | item | Calc*BufferConfig=A256(batch) | mask/index循环 | extra/normal可不同；不可固定6 |
| MegaMoeSendMaskBufferConfig(16B/align4) | routeBatchCount | I32 | 4B | 轮 | ceil(sendTotal/batch) | SendMask/Dispatch循环 | extra/normal可不同；不可固定6 |
| MegaMoeSendMaskBufferConfig(16B/align4) | bufferCount | I32 | 8B | 槽 | 自适应2..6 | slot/event ring | extra/normal可不同；不可固定6 |
| MegaMoeSendMaskBufferConfig(16B/align4) | bufferBytes | U32 | 12B | B | CalcTopkValidIndexRingSlotBytes | UB槽地址 | extra/normal可不同；不可固定6 |
| MegaMoeUnpermuteBufferConfig(24B/align4) | tokensPerBatch | I32 | 0B | token | gate基准及剩余UB反推 | gate batch | full/tail各自产生 |
| MegaMoeUnpermuteBufferConfig(24B/align4) | inputBufferCount | I32 | 4B | 槽 | clamp(UB/inputSlot,2,6) | MTE2输入ring | full/tail各自产生 |
| MegaMoeUnpermuteBufferConfig(24B/align4) | bf16SlotElementCount | U32 | 8B | BF16元素 | A32(2H)/2 | 输入/输出slot | full/tail各自产生 |
| MegaMoeUnpermuteBufferConfig(24B/align4) | fp32SlotElementCount | U32 | 12B | FP32元素 | A32(4H)/4 | FP32累加 | full/tail各自产生 |
| MegaMoeUnpermuteBufferConfig(24B/align4) | topKWeightsBufferBytes | U32 | 16B | B | A32(4*batch*T) | FP32 gate | full/tail各自产生 |
| MegaMoeUnpermuteBufferConfig(24B/align4) | topKWeightsConversionBufferBytes | U32 | 20B | B | BF16 gate时A32(2*batch*T)，FP32时0 | 转换scratch | full/tail各自产生 |
| MegaMoeL1Layout(208B/align8) | aBufferNum | U64 | 0B | 槽 | CalcMegaMoeL1Layout | A8W4 prologue | 本E5Generic inactive，不拿它计算E5 L1 |
| MegaMoeL1Layout(208B/align8) | bBufferNum | U64 | 8B | 槽 | CalcMegaMoeL1Layout | A8W4 prologue | 本E5Generic inactive，不拿它计算E5 L1 |
| MegaMoeL1Layout(208B/align8) | tileK | U64 | 16B | B/形状按字段 | CalcMegaMoeL1Layout | A8W4 prologue | 本E5Generic inactive，不拿它计算E5 L1 |
| MegaMoeL1Layout(208B/align8) | scaleK | U64 | 24B | B/形状按字段 | CalcMegaMoeL1Layout | A8W4 prologue | 本E5Generic inactive，不拿它计算E5 L1 |
| MegaMoeL1Layout(208B/align8) | aSlotBytes | U64 | 32B | B/形状按字段 | CalcMegaMoeL1Layout | A8W4 prologue | 本E5Generic inactive，不拿它计算E5 L1 |
| MegaMoeL1Layout(208B/align8) | bSlotBytes | U64 | 40B | B/形状按字段 | CalcMegaMoeL1Layout | A8W4 prologue | 本E5Generic inactive，不拿它计算E5 L1 |
| MegaMoeL1Layout(208B/align8) | scaleASlotBytes | U64 | 48B | B/形状按字段 | CalcMegaMoeL1Layout | A8W4 prologue | 本E5Generic inactive，不拿它计算E5 L1 |
| MegaMoeL1Layout(208B/align8) | scaleBSlotBytes | U64 | 56B | B/形状按字段 | CalcMegaMoeL1Layout | A8W4 prologue | 本E5Generic inactive，不拿它计算E5 L1 |
| MegaMoeL1Layout(208B/align8) | aOffsets[6] | U64数组 | 64B | B/形状按字段 | CalcMegaMoeL1Layout | A8W4 prologue | 本E5Generic inactive，不拿它计算E5 L1 |
| MegaMoeL1Layout(208B/align8) | bOffsets[8] | U64数组 | 112B | B/形状按字段 | CalcMegaMoeL1Layout | A8W4 prologue | 本E5Generic inactive，不拿它计算E5 L1 |
| MegaMoeL1Layout(208B/align8) | scaleAOffsets[2] | U64数组 | 176B | B/形状按字段 | CalcMegaMoeL1Layout | A8W4 prologue | 本E5Generic inactive，不拿它计算E5 L1 |
| MegaMoeL1Layout(208B/align8) | scaleBOffsets[2] | U64数组 | 192B | B/形状按字段 | CalcMegaMoeL1Layout | A8W4 prologue | 本E5Generic inactive，不拿它计算E5 L1 |
| Mc2MoeContext(24624B/align8) | epRankId | U32 | 0B | rank | CopyContextToTensor=localRank | peer地址 | <R |
| Mc2MoeContext(24624B/align8) | rankSizePerServer | U32 | 4B | rank/域 | CopyContextToTensor=domain | Layered peer | 与tiling相同 |
| Mc2MoeContext(24624B/align8) | kfcContextAddr | U64 | 8B | 地址 | Host KFC资源 | MTE资源分支 | 950Layered不使用 |
| Mc2MoeContext(24624B/align8) | epHcclBuffer_[1024] | U64[1024] | 16B | 地址 | peer注册窗口 | MTE/Layered GM | 有效前R项 |
| Mc2MoeContext(24624B/align8) | hcommHandle_[1024] | U64[1024] | 8208B | 句柄 | AIV ChannelAcquire compact | GetChannel(peer) | self从列表移除 |
| Mc2MoeContext(24624B/align8) | channelsPerRank | U32 | 16400B | 数 | 0 | multi-channel判定 | SGL single channel |
| Mc2MoeContext(24624B/align8) | enableGroupSend | bool | 16404B | 开关 | false | Layered channel组织 | inactive |
| Mc2MoeContext(24624B/align8) | roceHcclBuffer_[1024] | U64[1024] | 16408B | 地址 | 默认空 | 混合多channel扩展 | 本SGL路线不读 |
| Mc2MoeContext(24624B/align8) | roceBufferSize | U64 | 24600B | B | 默认0 | 混合多channel扩展 | inactive |
| Mc2MoeContext(24624B/align8) | hostStatusTableAddr | U64 | 24608B | 地址 | 默认0 | 状态扩展 | 不当作完成同步 |
| Mc2MoeContext(24624B/align8) | completedRounds | U64 | 24616B | 轮 | 默认U64(-2) | 轮次扩展 | 当前950 body inactive |
| GmBuffer(16B/align8) | offsetBytes | I64 | 0B | B | WorkspaceLayout分配 | base+offset | 未分配offset=-1,size0 |
| GmBuffer(16B/align8) | sizeBytes | I64 | 8B | B | 按slice字节公式 | 有效extent | 未分配offset=-1,size0 |

HCOMM/asc-comm接口的自然布局映射如下；HCOMM reserve首16B被Device解释为队列计数，Host整体清零提供初值，未证明安装包实现相同。URMA union字段相同；RoCE host的dbVendorSpecified与asc-comm的mtuShift等不同，连同batch不匹配单列边界。

| 结构 | 字段 | 类型/位宽 | ABI 布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| ChannelEntity 256B/align8 | abiHeader | CommAbiHeader16B | 0B | 数/地址 | channelDesc.header | 保留头 | 静态字段映射 |
| ChannelEntity 256B/align8 | engine | enum32 | 16B | 数/地址 | COMM_ENGINE_AIV=4 | 引擎 | 静态字段映射 |
| ChannelEntity 256B/align8 | protocol | enum32 | 20B | 数/地址 | UB_CTP=4或RoCE=1 | 协议 | 静态字段映射 |
| ChannelEntity 256B/align8 | localNotifyNum | U32 | 24B | 数/地址 | 资源数量 | 当前无notify | 静态字段映射 |
| ChannelEntity 256B/align8 | remoteNotifyNum | U32 | 28B | 数/地址 | 资源数量 | 当前无notify | 静态字段映射 |
| ChannelEntity 256B/align8 | localBufferNum | U32 | 32B | 数/地址 | PrepareHostChannelEntity | MR检索 | 静态字段映射 |
| ChannelEntity 256B/align8 | remoteBufferNum | U32 | 36B | 数/地址 | PrepareHostChannelEntity | MR检索 | 静态字段映射 |
| ChannelEntity 256B/align8 | sqNum | U32 | 40B | 数/地址 | transport connNum | QP0 | 静态字段映射 |
| ChannelEntity 256B/align8 | cqNum | U32 | 44B | 数/地址 | transport connNum | QP0 | 静态字段映射 |
| ChannelEntity 256B/align8 | localNotifyAddr | ptr64 | 48B | 数/地址 | slab复制 | 当前不读 | 静态字段映射 |
| ChannelEntity 256B/align8 | remoteNotifyAddr | ptr64 | 56B | 数/地址 | slab复制 | 当前不读 | 静态字段映射 |
| ChannelEntity 256B/align8 | localBufferAddr | ptr64 | 64B | 数/地址 | slab复制RegedBufferEntity | RoCE本地key | 静态字段映射 |
| ChannelEntity 256B/align8 | remoteBufferAddr | ptr64 | 72B | 数/地址 | slab复制RegedBufferEntity | URMA remote token | 静态字段映射 |
| ChannelEntity 256B/align8 | sqContextAddr | ptr64 | 80B | 数/地址 | slab复制SqContext | WQE/SQ/DB | 静态字段映射 |
| ChannelEntity 256B/align8 | cqContextAddr | ptr64 | 88B | 数/地址 | slab复制CqContext | CQ及lock地址 | 静态字段映射 |
| ChannelEntity 256B/align8 | sqHead | U32 | 96B | 数/地址 | HCOMM reserve清零 | MakeBatchHandle/BatchCommit | 静态字段映射 |
| ChannelEntity 256B/align8 | sqTail | U32 | 100B | 数/地址 | HCOMM reserve清零 | PollCq entryIdx | 静态字段映射 |
| ChannelEntity 256B/align8 | cqHead | U32 | 104B | 数/地址 | HCOMM reserve清零 | cqe=1请求计数 | 静态字段映射 |
| ChannelEntity 256B/align8 | cqTail | U32 | 108B | 数/地址 | HCOMM reserve清零 | CQ消费计数 | 静态字段映射 |
| ChannelEntity 256B/align8 | reserve[144] | byte[144] | 112B | 数/地址 | HCOMM reserve尾 | 保留 | 静态字段映射 |
| SqContext 128B/align8 | type | enum32 | 0B | 地址/B/数 | SQ_CONTEXT_TYPE_UB_JFS=0 | 协议分支 | union占120B，URMA分支 |
| SqContext 128B/align8 | ubJfs.sqVa | U64 | 8B | 地址/B/数 | DevUbConnection::SetSqContextInfo | SQ基址 | union占120B，URMA分支 |
| SqContext 128B/align8 | ubJfs.headAddr | U64 | 16B | 地址/B/数 | sqPiMem+i*8 | 队列索引区 | union占120B，URMA分支 |
| SqContext 128B/align8 | ubJfs.tailAddr | U64 | 24B | 地址/B/数 | sqCiMem+i*8 | 队列索引区 | union占120B，URMA分支 |
| SqContext 128B/align8 | ubJfs.dbVa | U64 | 32B | 地址/B/数 | SetSqContextInfo | st_dev门铃 | union占120B，URMA分支 |
| SqContext 128B/align8 | ubJfs.jfsID | U32 | 40B | 地址/B/数 | SetSqContextInfo | 保留资源 | union占120B，URMA分支 |
| SqContext 128B/align8 | ubJfs.wqeSize | U32 | 44B | 地址/B/数 | WQE_SIZE | 每BB字节 | union占120B，URMA分支 |
| SqContext 128B/align8 | ubJfs.sqDepth | U32 | 48B | 地址/B/数 | SetSqContextInfo | 环容量 | union占120B，URMA分支 |
| SqContext 128B/align8 | ubJfs.tpID | U32 | 52B | 地址/B/数 | SetSqContextInfo | WQE tpId | union占120B，URMA分支 |
| SqContext 128B/align8 | ubJfs.remoteEID[16] | byte[16] | 56B | 地址/B/数 | SetSqContextInfo | WQE远端EID | union占120B，URMA分支 |
| CqContext 128B/align8 | type | enum32 | 0B | 地址/B/数 | CQ_CONTEXT_TYPE_UB_JFC=0 | 协议 | union占120B，URMA分支 |
| CqContext 128B/align8 | ubJfc.scqVa | U64 | 8B | 地址/B/数 | SetCqContextInfo | CQ基址 | union占120B，URMA分支 |
| CqContext 128B/align8 | ubJfc.headAddr | U64 | 16B | 地址/B/数 | cqPiMem+i*8，首次清零 | 跨核CAS lock | union占120B，URMA分支 |
| CqContext 128B/align8 | ubJfc.tailAddr | U64 | 24B | 地址/B/数 | cqCiMem+i*8 | 索引区 | union占120B，URMA分支 |
| CqContext 128B/align8 | ubJfc.dbVa | U64 | 32B | 地址/B/数 | SetCqContextInfo | CQ回收门铃 | union占120B，URMA分支 |
| CqContext 128B/align8 | ubJfc.jfcID | U32 | 40B | 地址/B/数 | SetCqContextInfo | 资源 | union占120B，URMA分支 |
| CqContext 128B/align8 | ubJfc.cqeSize | U32 | 44B | 地址/B/数 | SetCqContextInfo | PollBatchCq要求≤64B | union占120B，URMA分支 |
| CqContext 128B/align8 | ubJfc.cqDepth | U32 | 48B | 地址/B/数 | SetCqContextInfo | owner轮换/环容量 | union占120B，URMA分支 |
| RegedBufferEntity 64B/align8 | type | enum32 | 0B | 地址/B/码 | REGED_BUFFER_RMA=1 | buffer类型 | union其余字节保留 |
| RegedBufferEntity 64B/align8 | rma.addr | U64 | 8B | 地址/B/码 | registered base | HcommFindBufferIdx | union其余字节保留 |
| RegedBufferEntity 64B/align8 | rma.size | U64 | 16B | 地址/B/码 | registered extent | 范围检查 | union其余字节保留 |
| RegedBufferEntity 64B/align8 | rma.protectionInfo.type | enum32 | 24B | 地址/B/码 | PROTECTION_TYPE_UB=1 | 协议 | union其余字节保留 |
| RegedBufferEntity 64B/align8 | rma.protectionInfo.memInfo.ub.tokenId | U32 | 32B | 地址/B/码 | LocalUbRmaBuffer/remote交换 | WQE token | union其余字节保留 |
| RegedBufferEntity 64B/align8 | rma.protectionInfo.memInfo.ub.tokenValue | U32 | 36B | 地址/B/码 | LocalUbRmaBuffer/remote交换 | WQE tokenValue | union其余字节保留 |

CommAbiHeader四个U32字段version/magicWord/size/reserved位于0/4/8/12B。Host slab按64B对齐依次安放256B实体、每项64B的notify/MR数组、每项128B的SQ/CQ数组和四组每QP8B的PI/CI；共享Jetty可改用endpoint拥有的PI/CI区。Build/PreAlloc/Fill明确管理Host→Device指针重定位及slab释放。

BatchHandle为Device局部对象：channelHandle、SqContext、CqContext、BatchQueueCursor(sqHead/sqTail/cqHead/cqTail/preSqCnt五U32)、BatchRemoteInfo(tokenId/tokenValue/EIDlow/EIDhigh/tpId/reserved)、BatchBuffer(LocalTensor<uint32_t>/capacity)。LocalTensor内部ABI未在该通信头固定，不宣称可跨Host序列化。selected普通read/write的每WQE为48B SQE+16B SGE=64B；notify增加32B并按64B取整到128B。UrmaWqeEntry为packed配置bitfield(odr3/fence1/se1/cqe1/inlineEn1)，不能将配置对象本身误作完整硬件WQE。

SiTU的Device局部参数包不改变608B Host tiling：SituGluParams为20B/align4，五个F32字段clampLimit@0、beta@4、invBeta@8、alpha@12、invAlpha@16。RunGatedActivationTile从Host参数计算invBeta=1/beta；LINEAR计算invAlpha=1/lambda，DEFAULT显式传alpha=invAlpha=1并实例化IsLinear=false。Host先检查个数1或2再读取数组元素，拒绝空、非有限、非正尺度；Device保底除零分支不扩大Host支持域。下表列出同一math中额外selector，三Route均覆盖：

| Route | actMode | actSubMode/参数 | 实际激活body | 数学差异与资源 |
|---|---|---|---|---|
| R-001/R-002/R-003自有body | SITU | DEFAULT，params=[beta]，beta>0有限 | RunSiTUGLU<BF16,false,false> | gate软截断、up原值；同UB/GM/MX scale |
| R-001/R-002/R-003自有body | SITU | LINEAR，params=[beta,lambda]，两者>0有限 | RunSiTUGLU<BF16,false,true> | gate与up均软截断；仅增加寄存器计算，不增加GM/UB slice |


| 结构 | 字段 | 类型/位宽 | ABI 布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| SituGluParams(20B/align4) | clampLimit | F32 | 0B | 值 | SetActivationAttrParams→RunGatedActivationTile | gate/up clamp | FLT_MAX |
| SituGluParams(20B/align4) | beta | F32 | 4B | 尺度 | activationParams[0] | gate soft clamp | 有限且>0 |
| SituGluParams(20B/align4) | invBeta | F32 | 8B | 倒数 | Device 1/beta | gate z | 未实测倒数误差 |
| SituGluParams(20B/align4) | alpha | F32 | 12B | lambda | LINEAR:params[1]；DEFAULT传1 | up soft clamp | DEFAULT实例不执行up tanh |
| SituGluParams(20B/align4) | invAlpha | F32 | 16B | 倒数 | LINEAR:1/lambda；DEFAULT1 | up z | 无额外GM/UB |

### Route 源码闭包

| Route | Key/selector | Host/Tiling producer | POD/参数 | Kernel entry/router | Kernel body/直接依赖 | 构建接线 |
|---|---|---|---|---|---|---|
| R-001 | K(0,0)/K(1,0)，dedup0/2，ND | arch35/mega_moe_tiling.cpp、arch35_92检查/缓冲计算 | MegaMoeTilingData608B及context24624B | arch35/mega_moe_apt.cpp::mega_moe/MegaMoeMteWave | mega_moe_wave_a8w8.h、arch35基类、token dispatch/dedup、GMM1/2 stage、ops-tensor BlockMmad、量化/Unpermute | op_host/CMakeLists.txt注册ascend950，Tensor API宏，auto-sync=off，ops-tensor.cmake固定fe1d |
| R-002 | K(1,1)，topo1 | 相同Host+SymmBuffer topology/channel producer | 同POD，Layered全量workspace、URMA ChannelEntity | mega_moe_apt.cpp::MegaMoeLayered默认LayeredUrmaComm | mega_moe_layered.h、layered dispatch/combine/send、共同Cube/activation、asc-comm URMA WQE/CQ/锁 | SDK/HCOMM版本头≥9.2，asc-comm package路径映射 |
| R-003 | K(1,1)，topo2 | 相同Host+UBX endpoint组合 | 同POD，协议随peer/domain选择 | MegaMoeLayered<...,LayeredUbxComm> | 自有Layered业务已读；asc-comm RoCE channel实现及batch/Lock/Unlock静态不匹配终点 | 同Layered版本宏，固定源码无可替代RoCE batch fallback |

## Kernel 实现

### 公共执行流程

所有业务路线都从context取得local/peer窗口和rank，从同一POD构造CclCommLayout与WorkspaceLayout。每个逻辑AIC的AIV0处理GMM1输出激活与MX量化，AIV1负责接收调度/GMM2 Combine；准备和最终Unpermute使用全部物理AIV。各阶段复用UB但GM元数据/ready维持其完整生命周期。

共同Cube实例为 `GmmKernel::Config<false,0,fp8_e5m2_t,fp8_e5m2_t,bfloat16_t,fp8_e8m0_t,fp8_e8m0_t,false,false,false,Lyr,true>`，选ops-tensor `GroupedMatmulWithScaleMx<0,false,KernelGroupedMmadWithScaleMx>`。`RunGmm1Generic` 将 Lyr 固定为 false，包括Layered调用；只有 `RunGmm2Generic` 传真实 IsLayered（R-001=false，R-002/003=true）。W1/W2只有ND原型，不能因公共模板含NZ就扩大本E5M2公开域。A为ND extended，B为DN extended，scaleA为ND→ZZ2、scaleB为DN→NN2，C为ND extended。BlockSchedulerSwizzle<3,0>按3个M tile组、N列蛇形排列，odd组反转N，边缘validM/N取min，滚动起始核按已分配tile数模AIC。

L1两个256KiB半区：基准A256×256=64KiB，B256×256=64KiB，scaleA/scaleB各256×16=4KiB，每半136KiB；GMM1的B256列由gate/up两个128列组成，不能漏算一半。L0A/B各64KiB以32KiB双缓冲，scale偏移为l0Offset>>4；L0C FP32 NZ16单槽0..256KiB，不启用L0C pingpong。K每次128、尾64，对数据/scale按MX K64布局补齐；absK=0才initWithZero，最后K才UnitFlag UPDATE，其余KEEP。GMM1 IterateNoBias，GMM2 bias关闭。

ops-tensor构造时预置MTE1_MTE2 id0..7、M_MTE1 id4/5，内部MTE2→MTE1→M流水保护L1/L0重用，析构等待这些credit并恢复MMLayout=false。GMM1 ND权重经CopyConcatGM2L1拷贝两半；gate/up的源GM半区跨度为(N/2)·fullK个FP8元素，每行srcDValue=fullK，scaleB源半区按全K对应的ceil(fullK/64)对组织；不是按当前kL1子块重算全权重stride。GMM2 ND权重使用普通DN extended view。公共Gmm1NzWeightView未被本E5M2实例选择。GMM1自有Gmm1OutputView重新生成默认L0C→UB copy trait，未继承上游SplitM trait，双128KiB UB视图按有效M/N提交；SDK最终转asc_mmad_mx、asc_copy_l0c2ub等硬件原语。SDK3510 UB248KiB与两完整视图262144B的静态预算差异单列，不用未证实SplitM解释消去。

共同GMM1模式4交接：AIC Fixpipe发布ready4/5，AIV0 V等待；AIV0处理完成回credit6/7，AIC FIX等credit后覆盖；End排空剩余1/2槽。AIV0激活输出及MX scale写GM后，按N tile原子增加每256行group的64B activationReady；GMM2等待ceil(N/256)。MTE GMM2模式4 ready10/credit11，AIC flag偏移16形成26/27，最多15个pending按PIPE_S回收后drain。Layered改由GM完成计数连接GMM2与Combine。

MTE的950 backend同样固定为channel，而非A3 KFC路径。AivUbMemChannel只负责资源/remote memory查询，其Host Read/Write返回不支持；Device实际用peer映射地址直接MTE。AivUbMemTransport交换LocalIpcRmaBuffer的addr/size/offset/pid/name/memInfo DTO，接收端构造RemoteIpcRmaBuffer：同pid取addr+offset并prefetch；异pid按runtime≥90200000-200和pathMode选择IPC访问link属性，feature不支持回legacy IPC open，默认one-port不支持可尝试multi-port，最终映射地址加offset。GetRemoteUserMems缓存CommMem地址/大小及tag，算子按tag匹配窗口；RemoteIpcRmaBuffer析构只关闭自己打开的IPC映射，LocalIpcRmaBuffer非alias析构销毁memory name。IPC runtime和socket/驱动为资源primitive终点，不能将其误记为Device URMA WQE算法。

### Route R-001：MTE Wave

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| SGL | strategies/fused_strategy.py | MegaMoeStrategy | mx_fp8_e5m2、situ或原样situglu、comm_alg默认 | dispatch4/E5、topo自动 |
| Host | arch35/mega_moe_tiling.cpp | CheckAndSetMteDedupMode/CheckMteDedupCapacityAndBenefit | topo0、combineComm0 | dedup先2后guard降0；不改变key |
| Tiling | arch35_92/mega_moe_tiling_buffer_calc.h | CalcTilingKey | comm0，C·T≤32768 | INT16或INT32路由index实例 |
| Router | arch35/mega_moe_apt.cpp | MegaMoeMteWave | E5权重非FP4 specialization | MegaMoeA8W8Wave ND共族 |

#### Device 数据流

##### 函数级调用链

```text
mega_moe -> MegaMoeMteWave::Init/Process -> MegaMoeA8W8Wave
 -> MegaMoeBase::Init / BindWorkspace / 各stage BuffInit
 -> 全AIV ResetFlagList + TokenQuant + SendMaskCal
 -> count/prefix/GM countReady
 -> AIV1 Dispatch(wave0/1)；dedup2时FIRST/PLAIN/SKIP描述符预处理
 -> 各wave AIC GMM1Generic -> BlockMmad MX
               AIV0 Activation -> RunSiTUGLU -> QuantMx -> GM activationReady
               AIC GMM2 -> AIV1 Combine/MTE远端GM
 -> PIPE_MTE3跨核结束 -> 计数槽清理 -> CrossRankHandshake -> all-AIV Unpermute
```

##### 源码等价伪码

```text
# 伪码，保留三角色与实际交接：
all AIV:
  balanced reset full flag/count ranges in <=2048-int32 batches
  for own token b: load BF16 H -> MX_E5(q,s) -> local quantRecord[b]
  for own expert range: filter ids by expert, write peer route indices using d-byte index
  wait reset/quant/send completion; publish epoch count tag (empty core also participates)
AIV1: wait epoch tags, transpose/prefix counts, export counts, publish countsReady
if dedup2:
  build grouped descriptors FIRST/SKIP/PLAIN and per-item ready;
  if N<=2048 AIV0 joins; wait all joining AIV0 before GMMready
AIV1: pull wave0, wave1; startup depth=HostD then steady depth=2 (same UB addresses)
for matching wave and rolling tile owner:
  AIC: wait dispatchReady; GMM1 tile gate/up -> UBslot pingpong; signal mode4 ready
  AIV0: wait ready; BF16->FP32 SiTU->BF16->MX_E5; store qA/sA;
        release UB credit; increment activationReady for each Ntile
  AIC: wait activationReady >= ceil(N/256); GMM2 Fixpipe -> BF16 GM(ring/full)
  AIV1: wait GMM2 mode4; MTE2 copy GM tile to UB; copy metadata+valid H segment to origin rank combine slot;
        release tile credit
  B>=4096: all three roles defer GMM2 one wave and drain last wave
wait all Combine MTE3; reset own 512B count slots after count consumer done
for peer assigned to this physical AIV, including self:
  write remote rankSync[myRank*64] = mySyncCnt+1; wait local rankSync[peer*64] equals it
update own syncCnt; DSBDDR; PIPE_ALL + all-AIV barrier
Unpermute: for b assigned, for k in [0,T):
  load origin combine[(b*T+k)*H : H] -> BF16->FP32
  acc = acc + value*FP32(gates[b,k]); final BF16 RINT/SAT -> Y[b]
```

dedup2预分组保存每个接收行的组标志、canonical最小topkIndex和(memberRow,topkIndex,flagOffset)三元组；FIRST只跨rank拉一次完整token到本地full dispatch GM，再fanout到同组其它expert；SKIP不重复远端拉取，PLAIN走普通路径。描述符成员数/min在Mmax裁剪之前产生的源码次序保留，不能将其解释为越界输入安全保证。每item ready在描述符MTE3排空后写64B标志，AIV0/AIV1分高16/低16完成域；Dispatch只等待当前batch依赖的chunk，而非每轮全表等待。

#### 内存与数据搬运

##### 资源与搬运表

记record=A32(A256(H)+ceil(H/32))，当前H%64可化为A256(H)+A32(H/32)。该record含FP8数据与E8M0 scale，不含gate。

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| CCL异常头 | localWindow+0 | 60KiB | 诊断区 | MC2异常策略 | 异常读取 | 通信对象 | 不当业务ready |
| rank同步/count | commBase=window+60KiB | 48KiB sync +12KiB syncCnt +1MiB count(2048×512B) | tag/计数 | 所有AIV | count/跨rank等待 | 跨调用复用，退出协议保护 | 64/512B槽 |
| route | 前述区后 | A512(LR·A32(Cd)) | INT16或INT32 | SendMaskCal | Dispatch | 当前调用 | 全专家/源rank表 |
| quant token | route后 | A512(C·record) | E5/E8M0交织 | TokenQuant | peer Dispatch | 到远端消费完成 | record stride |
| combine | quant后 | A512(C·T·2H) | BF16 | 远端AIV1 GMM2 Combine | 本rank Unpermute | 退出同步前不可复用 | token/topk行 |
| dispatch q/s | computeBase | A512(rowsD·H)+A512(rowsD·2ceil(H/64)) | E5、E8M0分离 | Dispatch/Fanout | GMM1 | ring或full | dedup2必须full dispatch |
| activation q/s | 前slice后 | A512(rowsA·I)+A512(rowsA·2ceil(I/64)) | E5、E8M0 | AIV0 | GMM2 | ring或full | 每组ready发布后可读 |
| recv count/meta | 前slice后 | A512(A16(L)·4AIC)+A512(Mmax·32) | I32/32B记录 | count/Dispatch | 两GMM/Combine | 元数据全量 | 不随ring缩小 |
| flags | 累加slice | 2·64Lceil(Mmax/256)+64L·AIC | dispatch/activation/countReady | AIV | AIC/AIV | 本次reset→完成 | 64B槽防伪共享 |
| dedup flags/rowdesc | 条件slice | dedup2:64(1+128R)+A512(4·A8(2+3T)·Mmax) | 组描述符 | 预分组 | FIRST/fanout | 当前调用 | dedup0不分配 |
| GMM2 GM | 对齐slice | A512(2H·rowsG2) | BF16 | GMM2配置/输出路径 | Combine | stage ring/full | 实际GMM2先写BF16 GM，由AIV1 MTE2消费；MTE按ring/full布局保存 |
| L1/L0 | 共同Cube布局 | L1每半136KiB基准；L0A/B64KiB、L0C256KiB | 内部NZ/ZZ/NN、FP32 | GM2L1/MMAD | Fixpipe | 每AIC对象 | stage2和K credit |
| Send/Quant UB | 从0按slice排 | 4Bsend+dBsend+reset≤8192+2048+2record+2(2A128(H))+Dsend·slot+A32(4ceil(RL/AIV)) | I32、d-byte、BF16/E5/scale | VF/TokenQuant | MTE3 | 计数阶段复用前面已死区 | slot=Bsend/8+A32(ceil((Bsend+T-1)/T)d) |
| Dispatch UB | prefix后 | A32(4LR)+A32(dBrecv)+Drecv·record+A32(4L)+32Drecv | indices/record/meta | MTE2/VF | MTE3/GMM ready | 启动D、稳态2 | dedup另预留72KiB |
| dedup UB | A512后的独立预留 | 前期4KiB route+4KiB count+2KiB descAsm+54KiB member=64KiB；后期48KiB descBatch+8KiB fanmeta+8KiB activeList | I32/descriptor | 组构建 | fanout | 分阶段同区复用 | Host预留72KiB |
| GMM1/激活 UB | slot0=0，slot1=131072 | raw 2×128KiB；每slot激活BF16 65536B、FP8 32768B、scale1024B、maxExp2048B、inverse2048B | BF16→FP32寄存器→BF16→E5 | Fixpipe/AIV0 | MX q/s GM | credit6/7后覆写 | raw视图262144B与248KiB冲突 |
| GMM2/Combine UB | tile起64KiB、meta起200KiB | BF16 tile128KiB；每tile最多256×32=8192B meta | BF16/32B路由 | AIV1 MTE2（输入来自GMM2 GM） | 远端MTE3 | 交接credit后可重用 | tile终点192KiB |
| Unpermute UB | 从0按Host配置排 | (Dinput+1)A32(2H)+A32(4H)+A32(4BTgate)+[BF16gate]A32(2BTgate) | D输入+输出BF16、单FP32acc、gates | MTE2/VF | MTE3 Y | full/tail两配置，最后drain | D=2..6；本combine0无scale scratch |

##### 分层内存布局

```mermaid
flowchart LR
  X["BF16 X GM"] --> Q["AIV MX量化 UB"]
  Q --> W["CCL quant record"]
  W --> D["peer MTE Dispatch GM q/s"]
  D --> L1["AIC L1 2×136KiB基准"]
  L1 --> L0["L0A/B 2×32KiB → MX MMAD L0C256KiB"]
  L0 --> V0["Fixpipe → AIV0 BF16 UB"]
  V0 --> A["SiTU + MX → activation GM q/s"]
  A --> L1
  L0 --> G2GM["GMM2 Fixpipe → BF16 GM ring/full"] --> V1["AIV1 MTE2 → BF16 UB tile"]
  V1 --> C["peer CCL combine BF16"]
  C --> U["all-AIV FP32 gates累加"]
  U --> Y["BF16 Y"]
```

```mermaid
block-beta
  columns 2
  raw0["AIV0 raw slot0: 0..128KiB"]:1 raw1["raw slot1:128..256KiB"]:1
  act0["slot+0:BF16 act64KiB"]:1 act1["slot+64KiB:FP8 out32KiB"]:1
  sc["slot+96KiB:E8M0 1KiB"]:1 mx["slot+97KiB:maxExp2KiB+inverse2KiB"]:1
  cmb["AIV1:BF16 combine tile64..192KiB"]:1 md["AIV1:meta200KiB+≤8KiB"]:1
  up["Unpermute: D×A32(2H) inputs"]:1 acc["output A32(2H)+acc A32(4H)+gate buffers"]:1
```

图中各阶段按生命周期复用，raw双视图容量冲突明确保留，不能据图宣称UB总量合法。

##### 字节账、交接边与复用顺序

```text
comm_total = 48KiB +12KiB +1MiB +A512(LR*A32(Cd))
             +A512(C*record)+A512(C*T*2H)
compute_base = A512(60KiB + comm_total)
rowsStage = ring.stage ? 3*g*256 : Mmax
compute_total = 按上表各Allocate实际传入extent顺序追加（数据/scale等片按其显式A512、flags按64B槽、cumsum按A32）；MTE仅在GMM2 output处显式将累计起点及outputBytes补齐A512；
                dedup条件flags/rowdesc；GMM1out/shared slices均inactive(-1,0)
window_required = compute_base + WorkspaceLayout(compute).workspaceSize
framework_workspace = platform.GetLibApiWorkSpaceSize()
UB_send/dispatch/unpermute <= Host实取可用UB（自适应公式）
UB_GMM1_raw_views =262144B > SDK3510 TOTAL_UB_SIZE=253952B（静态限制）
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| quantRecord→peer Dispatch | TokenQuant | b·record，record B | E5/E8M0 | CopyGMToGMPerToken | 准备阶段quant/reset完成后count epoch | CCL对象 | 当前rank/调用匹配 |
| Dispatch→GMM1 | AIV1/Fanout | group数据及64B flag | q/s分离 | AIC | MTE3完成→atomic ready精确行数 | full/ring slice | AIC等当前group所需行 |
| GMM1→AIV0 | Fixpipe | 两128KiB视图 | BF16 | 激活 | mode4 ready4/5，credit6/7 | 每核pingpong | 覆写前等credit；UB冲突未消除 |
| 激活→GMM2 | AIV0 | q/s与64B group flag | E5/E8M0 | AIC | atomic完成Ntile，等待ceil(N/256) | GM full/ring | 保持跨族发布顺序 |
| GMM2→AIV1 | Fixpipe→GM，再由AIV1 MTE2→UB | GM有效tile→UB64..192KiB | BF16 | Combine | ready10/ACK11、AIC偏移16 | GM与UB流水 | pending≤15后回收；尾drain |
| remote Combine→Unpermute | AIV1 | (bT+k)H·2 | BF16 | 源rank AIV | 所有MTE3完成及跨rank握手 | CCL | 参与rank全体同轮，先完成后读 |
| Unpermute输入/输出ring | MTE2/VF | D输入+1输出 | BF16/FP32 | MTE3 | V_MTE2事件0..5，MTE3_V输出事件0 | 当前AIV | 同事件号不同方向；输出覆盖前等及最终drain |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| 初始准备 | reset完成10、token量化8及count epoch | 全AIV，包括空份额 | count/prefix | flags/量化/route GM | reset每批≤2048 INT32，尾mask |
| input准备→Cube | INPUT2/MTE2，MTE2_S | AIV准备 | AIC | 输入可见性 | 有效H及scale行 |
| dedup加入者 | item ready与AIV0/AIV1高低16域 | 预分组核 | Dispatch/GMM开始 | 描述符及fanout完成 | 保留Mmax裁剪次序 |
| L1/L0 | MTE1_MTE2 0..7，M_MTE1 4/5，MTE1_M | BlockMmad | 下轮copy/MMAD | 两级A/B/scale流水 | K128/尾64，L0C首K清零 |
| GMM1激活 | mode4 ready/credit | AIC/AIV0 | 双方对称等待 | UB槽 | BF16 Fixpipe→FP32激活→BF16 NO_SAT/RINT→MX SAT/RINT |
| GMM2输出 | mode4发布GM完成、MTE2消费及MTE3_MTE2 | AIC/AIV1 | 下一tile/覆盖前 | BF16 GM结果、UB与metadata | validN裁剪，远端连续2·validN B |
| count清理/退出 | COUNT9、PIPE_MTE3、跨rank64B sync槽、DSBDDR、all-AIV barrier | 全AIV | Unpermute | 复用count及combine | 不把异常诊断字段当业务同步 |
| final cast | FP32乘/add，BF16 RINT/SAT | VF | Y GM | 1行acc | 全T槽累加，full/tail按B分配；空AIV先return |
| CTRL | 保存后将bit60置0，最后恢复 | Process | VF调用 | 控制模式 | 仅记录位操作，不称全局饱和/非有限保证 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | arch35/mega_moe_tiling.cpp | CheckMteDedupCapacityAndBenefit/SetAdaptiveBufferConfigs | 自动0/2、实际UB与window容量 |
| Kernel entry/router | arch35/mega_moe_apt.cpp | MegaMoeMteWave→MegaMoeA8W8Wave | E5选A8W8，非FP4特化 |
| Device body/helper | arch35/mega_moe_wave_a8w8.h | Process/GMM波次 | startup、滚动核、B≥4096一wave GMM2延迟 |
| Device body/helper | stage/mega_moe_token_dedup.h | FIRST/成员描述符 | 一次远端拉取、本地fanout |
| Device body/helper | stage/mega_moe_gmm1_activation.h | GMM1Generic/Activation | MX双GMM与AIV0 epilogue |
| Device body/helper | ops-tensor block_mmad_qgmm_mx.h | BlockMmad | 实际MX MMAD块循环与L1/L0 event |


### Route R-002：Layered URMA

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Python/Host | mc2/common/torch_extension/csrc/comm_context.cpp | topology resolver | 域内UB_CTP、跨域UB_RTP，域整除R | topo1、每peer紧凑channel表 |
| Tiling | arch35/mega_moe_tiling.cpp | CheckAndSetUrmaDedupMode | combineComm0、combineQuant0、topkWeightsType0 | dedup0、全量GM |
| Router | arch35/mega_moe_apt.cpp | mega_moe | key comm1、BF16 dispatch4、版本宏成立、topo非2 | MegaMoeLayered默认LayeredUrmaComm |
| Core | common/mega_moe_layered_comm.h | LayeredUrmaComm | Hcomm<COMM_PROTOCOL_UB_CTP> | asc-comm3510 URMA specialization |

#### Device 数据流

##### 函数级调用链

```text
MegaMoeLayered(context)::Init -> InitTopology/DispatchLayout/Workspace
 -> SendAndQuantBuffInit/DispatchBuffInit/UnpermuteBuffInit
Process -> ResetState -> ComputeExpertMasks/SendExpertMasks + TokenQuant
 -> 跨rank初始同步 -> PrepareExpertTokenCountTable/PrepareDispatchReceive
 -> ProcessMoeExpertWave
      -> ReceiveDispatchTokenRange / ReceiveDispatchServerPhase
         -> EnsureDispatchSourceReady -> local copy or ReceiveRemoteDispatchBatch
      -> GMM1Generic / RunSiTUGLU<BF16,false,DEFAULT-or-LINEAR> + MX epilogue -> GMM2Generic
      -> ProcessCombineTokenRange -> CombineTokensOfExpert/CombineSend
 -> Drain所有本核拥有peer + Unlock -> CrossRankSyncInWorldSize -> Unpermute
LayeredUrmaComm -> Hcomm<UB_CTP>
 -> MakeBatchHandle -> BatchPostSend -> BatchCommit -> PollBatchCq/Drain
 -> Lock/Unlock (global CAS lock)
```

##### 源码等价伪码

```text
# 伪码，当前shared0/combineComm0，非server-reduce:
all physical AIV:
  reset full flags/counters in bounded batches
  compute per-expert bit masks & counts; send to peer GM
  quantize own actual B rows to local E5/E8M0 record
  drain mask/data preparation; all-AIV barrier; crossrank reuse sync
AIV1 owner(peer) = peer % logicalAIC:
  acquire each owned remote channel lock once
  forward all actual B records to same-in-domain rank of each other domain:
    append relaxed ODR5,cqe0 chunks (<256MiB; inner chunks256MiB-512B)
    append tail 8B ready ODR6,cqe1 from stable GM=1; Commit
  transpose rank-major counts -> expert-major; prefix -> countsReady and wave metadata
  receive first communication wave and lookahead next wave into full dispatch GM
for each communication wave:
  for source domain in local-first order and expert ranges:
    wait source ready (remote Read8B+Drain or local load; cache only confirmed ready)
    mask Gather with stale tail cleared by actual rank count -> topk indices
    local relay: copy through 5 soft record slots
    remote relay: <=256 tokens/batch, 2 WQEs/token for data H + scale 2ceil(H/64)
    Commit; overlap local 32B metadata MTE3 with Drain; publish exact dispatch rows
  AIC/AIV0: consume g-group compute waves, common GMM1+SiTU/MX+GMM2 pipeline
  GMM2 Fix_S -> atomic_add per output-N-tile to assigned 64B group sync slots
  AIV1: wait group sync >=ceil(H/256); send each valid token BF16 2H from full GMM2 GM
        remote requests batch256tokens; local via UB MTE3_S; tailCommit
Drain every owned peer (not only last active), then Unlock
crossrank sync with peer protocol -> all-AIV barrier
Unpermute typed BF16/FP32 gates, FP32 per-topk multiply/add, final BF16_RINT_SAT
```

接收首先按当前expert累计行切片建立PlanTokenWave；通信wave预算至少2个计算wave，计算wave仍由g个256行组控制。接收采用完整GM，避免把MTE 3-wave地址映射套入分层relay。每个peer固定由AIV1逻辑block=peer%AIC拥有；阶段间所有owner、Drain、Unlock保持该归属，退出跨rank同步可按物理AIV重新分配channel使用，前阶段必须已排空并解锁。

真实URMA primitive算法：MakeBatchHandle读取QP0的SQ/CQ context、四个计数和remote MR，按给定remoteAddr只做一次1B范围检索，缓存token/EID；localAddr被忽略。BatchPostSend生成完整6×U64 SQE和一个16B SGE，配置flag显式编码ODR/fence/cqe，普通read/write各一个64B BB；local/remote全extent由caller保证，batch准备不再次验证。准备count受UB容量检查；BatchCommit要求0<count≤UBcap且count<sqDepth，将环形SQ尾/头分成最多两次MTE3拷贝，更新GM sqHead/cqHead、敲SQ门铃、preSqCnt清0。该函数没有outstanding SQ/CQ容量回收；channel版PostSend才含overflow Poll，不能把wrapper“library owns reclamation”注释当已证安全机制。

Drain复用batch第一个64B作为CQ scratch，要求已Commit且CQE size≤64B；按owner位循环MTE2读取CQ，最多1e8次重试，超时或status/substatus错误调用Trap并返回码；成功推进cqTail/sqTail并敲CQ门铃。只包含cqe0请求时不能凭Drain证明其完成；业务用最后ODR6/cqe1 ready请求覆盖前序relaxed payload。selected方法返回值多数由业务wrapper转发但调用处未检查，不应把非零自动写成Host失败返回。

跨核Lock读取CQ context的headAddr为CAS锁地址，AtomicCas(0→1)循环、Nop800退避；Unlock先DCCI四个队列计数16B，再CAS(1→0)。该锁与PIPE_S/MTE3/MTE2 Mutex29分别解决跨核channel状态与核内指令管线顺序；512B Init scratch和64KiB batch区独立。硬件传输、doorbell消费及MR注册runtime是终点，WQE准备/提交/CQ等待不能只写调用名。

#### 内存与数据搬运

##### 资源与搬运表

WorkspaceLayout::Allocate只按传入extent连续追加：offset[i]=Σ前置extent，不隐式补齐起点。Layered的flags/counters为64B槽、cumsum为A32(4LR)·AIC；InitializeUrma调用InitializeGmmIntermediateBuffers(params,true,false)，因此GMM2 output紧接前片、长度2MmaxH，均不额外A512对齐。comm与compute分区不同于MTE的60KiB异常头。

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| comm rankSync/syncCnt | window起 | max(48KiB,64R)+12KiB，后A512 | epoch/计数 | 跨rank同步 | 所有rank | 通信对象 | 64B槽 |
| comm masks | 同步后 | A512(LR·maskSlot)，maskSlot=A32(A256(C·T·4)/4/8)+32 | bitmask+尾部计数 | SendExpertMasks | 各rank接收 | 调用期间 | 尾mask按实际count清理 |
| comm rawcount | 前slice后 | A512(4LR) | INT32 | send/count | 前缀 | 调用期间 | rank→expert转置 |
| relay data | 前slice后 | A512(C·A512(record)·serverNum) | E5/E8M0 record | 本rank/跨域forward | expert owner接收 | stable直到Drain | 每domain容量C，record stride A512 |
| relay ready | 前slice后 | A512(serverNum·C·8) | 8B ready槽 | strong cqe1尾写 | EnsureDispatchSourceReady | 本调用 | ready source GM置1后DSB，不复用短命UB |
| combine send | 前slice后 | A512(C·T·2H) | BF16 | expert rank Combine | 源rankUnpermute | 退出协议 | 无quant/gate payload |
| dispatch/act q/s | computeBase=A512(commTotal)后 | A512(MmaxH)+A512(Mmax·2ceil(H/64))+A512(MmaxI)+A512(Mmax·2ceil(I/64)) | E5/E8M0 | 接收/AIV0 | GMM1/2 | full GM | 不使用ring |
| recvcount/meta/ready | 后续slice | A512(A16(L)4AIC)+A512(32Mmax)+2·64Lceil(Mmax/256)+64L·AIC | 计数/32B metadata | Count/Dispatch/Act | Cube与Combine | reset→使用完成 | full flags |
| combine counters | 后续slice | 64L·max(ceil(CR/256),AIC) | atomic U32槽 | GMM2 Fix_S后 | AIV1 Combine | 当前调用 | M_e≤CR依赖无重复ID |
| count cumsum | 后续slice | A32(4LR)·AIC | INT32 | prefix | 每AIV1 | 当前调用 | 每逻辑核副本 |
| GMM2 output | 紧接cumsum，offset=前置slice实际extent之和 | 2MmaxH（不补齐） | BF16 | AIC Fixpipe | URMA读payload | Drain完成前不覆写 | full GM |
| local mask/queue/snapshot | 后续slice | mask同comm；A512(serverNum·(32+32B))；2048·AIC | metadata/ready cache | 接收调度 | receiver | 只有确认ready才cache | flags与工作队列独立 |
| channel slab | HCOMM设备allocation | 256B头+各A64数组+四组8B/queue索引 | 资源描述符 | Host ChannelEntity builder | asc-comm | HCOMM channel owner | 本算子不free |
| L1/L0 | 共同Cube布局 | 基准每半136KiB、L0A/B各64KiB、L0C256KiB | MX/FP32 | BlockMmad | epilogue | 每AIC对象 | 与R-001共族 |
| Hcomm Init UB | 0..512 | 512B，WQE scratch128B，CQ scratch64B起128 | 控制 | Hcomm::Init | channel版请求/CQ | 核内阶段常驻 | 32B起点 |
| Layered SendMask UB | 512后 | reset≤8192+4Bsend+2·(Bsend/8)+A256(32ceil(RL/AIV)) | I32/mask/count | VF | URMA/MTE3 | 与后续量化复用 | Bsend=floor256(4·剩余/17) |
| TokenQuant UB | 512后 | 2·2A128(H)+2048+2record | BF16/E5/E8M0 | MTE2/VF | relay GM | ring2 | EVENT0/1 |
| Dispatch UB | 512后 | A32(4LR)+5record+A32(4L)+8192B meta+2·4Brecv+Brecv/8 | prefix/record/index/mask | MTE2/URMA/VF | dispatch GM | 5 soft slots | Brecv=floor256(8·剩余/65) |
| WQE batch UB | 184KiB-512..248KiB-512 | 64KiB=1024×64B | SQE/SGE、Drain时CQ scratch | BatchPostSend | BatchCommit/PollBatchCq | 同时仅一个batch准备域 | Drain后覆盖 |
| readyCache UB | 248KiB-512..248KiB | A32(4ceil(R/32))≤512B | bitset | EnsureDispatchSourceReady | 后续接收 | 本次reset | R≤1024 |
| Activation UB | 与共同epilogue一致 | raw2×128KiB、act/output/scale scratch | BF16/E5/E8M0 | AIC/AIV0 | activation GM | mode4 credit | 同248KiB冲突 |
| Unpermute UB | 512后工作区 | 3·2H +3·4H=18H；另gate F32 A32(4BTgate)+可选BF16 A32(2BTgate) | 两输入+输出BF16、两转换+累加FP32 | MTE2/VF | Y | 阶段复用batch/data区但保留512B头 | gateBatch=max(1,min(B,floor((248KiB-512-18H-slack)/(T·(4+2[BF16gate]))))) |

##### 分层内存布局

```mermaid
flowchart LR
  X["BF16 X"] --> Q["AIV MX E5 quant"]
  Q --> Relay["本rank/domain relay GM"]
  Relay --> F["URMA relaxed payload + strong ready"]
  F --> Recv["URMA Read batch → full dispatch q/s GM"]
  Recv --> L1["L1 → L0A/B + MX scales"]
  L1 --> MM["MX MMAD FP32 L0C"]
  MM --> A["AIV0 SiTU/MX → full activation q/s"]
  A --> L1
  MM --> G2["GMM2 BF16 full GM"]
  G2 --> N["Fix_S + 64B atomic group counter"]
  N --> S["AIV1 URMA CombineSend"]
  S --> Out["origin combine GM → Unpermute → Y"]
```

```mermaid
block-beta
  columns 1
  hc["0..512B Hcomm Init scratch"]
  work["512..184KiB-512B 分阶段Send/Quant/Dispatch工作区"]
  batch["184KiB-512B..248KiB-512B WQE batch64KiB；Drain复用首64B"]
  cache["248KiB-512B..248KiB readyCache≤512B"]
  act["AIV0激活阶段：两128KiB raw视图及slot内scratch，存在预算冲突"]
  unp["Unpermute阶段：512B头后18H数据 + gate batch"]
```

##### 字节账、交接边与复用顺序

```text
comm_total = A512(max(48KiB,64R)+12KiB) +mask +rawCount+relayData+ready+combineSend
compute_base=A512(comm_total)
compute_total=full dispatch/act q/s +count/meta/flags +combineCounter+cumsum
              +2MmaxH+localMask+workQueue+readySnapshot（按上表显式extent连续追加，无统一起点对齐）
window_required=compute_base+WorkspaceLayout.workspaceSize
UB_work_limit=184KiB-512B；batch64KiB；readyCache≤512B；Init512B
UB_unpermute=512B+18H+A32(4BTgate)+[BF16gate]A32(2BTgate) <=248KiB
              gatebatch扣独立padding slack(31或62B)
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| relay payload→ready | Forward batch | 每domain B实际record，尾8B ready | E5/E8M0 + U64 | remote source-ready | ODR5 cqe0 payload，ODR6 cqe1尾ready、Commit | payload保持到Drain | 同channel/注册MR，不能只有cqe0 |
| remote read→dispatchReady | ReceiveRemoteDispatchBatch | 每token H数据+2ceil(H/64)scale；32B meta | q/s/meta | GMM1 | BatchCommit→Drain、metadata MTE3完成→atomic rows | per-peer owner | source-ready确认后读 |
| GMM1→Activation→GMM2 | 共同Cube/AIV0 | full GM q/s | BF16→E5 | GMM2 | mode4/activationReady | 当前调用 | 同R-001精度，無MTE ring |
| GMM2→Combine | Fixpipe | group256行、64B counters | BF16 GM | AIV1 | Fix_S后atomic，等待ceil(H/256) | fulloutput直到Drain | S=max(ceil(M_e/256),AIC)；组按商余分配slot |
| Combine→origin | URMA BatchWrite | token2H B | BF16 | 源rankUnpermute | batch尾Commit→Drain所有owned peers→Unlock→crossrank | 注册窗口 | 全rank同轮；不依赖最后一个peer代表全部 |
| WQE UB复用 | BatchPostSend | 64KiB | WQE→CQ scratch | Drain/下一batch | Commit前不可覆盖；Drain读CQ用首64B | 当前channel batch | 连续Commit未见outstanding回收保证 |
| Unpermute输入/输出 | MTE2/VF/MTE3 | 18H+gate batch | BF16/FP32 | Y | V_MTE2 0/1，MTE3_V 2，最后MTE3_S | 当前AIV | 全T、真实B/tail |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Prepare | mask MTE3完成、all-AIV barrier、crossrank reuse sync | 全AIV | 计数/接收 | reset/mask/quant GM | 空B被Host拒绝；实际B之外mask tail清理 |
| channel排他 | CAS锁/Nop800、DCCI counters+CAS unlock | owner(peer%AIC) | 同channel其它核 | SQ/CQ计数 | 返回码未全面消费，不编造自动恢复 |
| WQE生成/提交 | Mutex PIPE_S/MTE3 id29 | BatchPostSend/BatchCommit | doorbell硬件 | UB/SQ | 64B普通WQE，batch<SQdepth |
| ready发布 | ODR6 fence1 cqe1尾写 | relay发送 | EnsureDispatchSourceReady | 前序relaxed数据 | remote Read8B+Drain后cache ready |
| GMM1/GMM2 | mode4、MX Mmad/K event、activationReady | AIC/AIV0 | AIC | 全量q/s | 相同E5/BF16两次舍入与scale格式 |
| GMM2完成组 | Fix_S + atomic group flags | AIC | AIV1等Ntile数 | fullGMM2 GM | 最后M不足256只传有效行 |
| 批量完成 | CQ owner/status poll，最多1e8次 | 硬件CQ | Drain | source与WQE复用 | timeout/status源码Trap；未运行复现 |
| Combine退出 | Drain每owned peer→Unlock→crossrank→all-AIV | AIV1/全部AIV | Unpermute | origin combine完整 | local MTE3_S与remote CQ不同机制 |
| final | gates按真实dtype转换，FP32乘/add，BF16 RINT/SAT | VF | Y | 全T累加 | tail gate batch与空AIV直接返回 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | mc2/common/torch_extension/csrc/comm_context.cpp | topology/channel builder | 自定义注册窗口、domain与compact channels |
| Kernel entry/router | arch35/mega_moe_apt.cpp | MegaMoeLayered默认CommPolicy | topo1与BF16动态MX版本门 |
| Device body/helper | arch35/mega_moe_layered.h | ProcessMoeExpertWave/PlanTokenWave | 全量GM通信wave与g组计算wave |
| Device body/helper | stage/mega_moe_layered_dispatch.h | EnsureDispatchSourceReady/ReceiveRemoteDispatchBatch | relay两级拉取与ready缓存 |
| Device body/helper | stage/mega_moe_layered_combine.h | ProcessCombineTokenRange | 组counter与256token batch回传 |
| External core | asc-comm hcomm_aiv_urma.h | BatchPostSend/BatchCommit/PollBatchCq/Lock | WQE、环形SQ、CQ、跨核锁实际body |

### Route R-003：Layered UBX及固定源静态终点

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host拓扑 | comm_context.cpp | topology resolver | domain内UB_CTP、跨domain RoCE；无混合多channel且域连续 | topo2 |
| Router | arch35/mega_moe_apt.cpp | mega_moe | key comm1且compute.topoType==TOPO_TYPE_URMA_ROCE | LayeredUbxComm |
| 自有通信 | common/mega_moe_layered_comm.h | GetChannel/MakeBatchHandle | peer/domain != self/domain→roce=true | 同步与batch调用双协议runtime分支 |
| 外部实现 | asc-comm impl/hcomm_impl.h | MakeBatchHandle/Lock/Unlock | static_assert protocol必须UB_CTP | RoCE实例静态不匹配，源码终点明确 |

#### Device 数据流

##### 函数级调用链

```text
mega_moe -> MegaMoeLayered<...,LayeredUbxComm>::Process
 -> 相同R-002 Reset/Quant/Mask/Relay/Dispatch/GMM1/Act/GMM2/Combine/Unpermute
 -> LayeredUbxComm::GetChannel(peer): native+roce位
 -> intra-domain: Hcomm<UB_CTP> 全部实际URMA body
 -> inter-domain: Hcomm<ROCE>
      channel Read/Write/Commit/Drain: 有hcomm_aiv_roce.h真实body
      MakeBatchHandle / Lock / Unlock / batch Read/Write/BatchCommit/Drain:
        固定9.2公共转发static_assert或specialization缺成员，未形成可用batch算法
```

##### 源码等价伪码

```text
# 自有业务意图伪码；不表示固定依赖可执行：
ch = { context.hcommHandle[peer>rank ? peer-1 : peer], peer/domain != myDomain }
Init: urma.Init(scratch512); roce.Init(same scratch512)
Lock/Unlock: ch.roce ? roce.Lock/Unlock(native) : urma.Lock/Unlock(native)
MakeBatch: ch.roce ? roce.MakeBatchHandle(native,batch64KiB,remote,localWindow)
                  : urma.MakeBatchHandle(native,batch64KiB,remote)
all Layered business loops and ownership follow R-002
chunk limit = ch.roce ? 2^31 : 256MiB
inner chunk = limit -512B; final chunk <limit
# exact fixed-source terminal:
Hcomm<ROCE>::MakeBatchHandle / Lock / Unlock -> static_assert UB_CTP
RoCE specialization has no batch overloads/BatchCommit; do not fabricate replacement
```

可读channel版RoCE core仍需区别于batch：64B RoceWqeEntry由16B control+32B task+16B data组成，网络序字段写入SQ，remote和local MR全范围验证并选rkey/lkey；预写下一个BB owner为无效，MTE3复制WQE、MTE3_S后推进SQ PI并敲软件/硬件门铃。CQ以owner/opcode检查、最多1e6次轮询，更新CQ/SQ CI及CQ门铃；WriteWithNotify/WriteValue在此specialization返回FAILED。这些是实际源码事实，不能用其存在推导未实现的RoCE batch已闭合可运行。Host RoCE Sq/Cq布局字段与该core还存在差异，未作安装ABI兼容声明。

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| 自有CCL/compute/relay | 与R-002全部slice同公式 | window_required同R-002 | E5/E8M0/BF16/meta | 自有Layered body | 自有GMM/Combine | CommContext owner | 不删除topo2可达域 |
| UB工作/batch/cache | 同R-002 | 512B+工作区+64KiBbatch+≤512Bcache | mixed | 自有scheduler | protocol wrapper | 同阶段复用 | 未证明RoCE batch可用 |
| L1/L0/Activation | 共同Cube与R-002 | 每半136KiB/64KiB/256KiB及双raw槽 | MX/FP32/BF16 | BlockMmad/AIV0 | 双GMM | 同核 | SDK trait与UB限制仍适用 |
| RoCE channel Init scratch | UB0..512，CQ起128 | 512B | WQE64B、CQE结构 | RoCE Init | channel PostSend/PollCq | 核内 | 仅实际channel方法 |
| RoCE资源实体 | HCOMM device slab | 256B及MR/SQ/CQ数组 | Host/Device ABI | AicpuTsRoceChannelV2 builder | RoCE channel core | HCOMM owner | 部分字段差异未验证；不是batch owner |

##### 分层内存布局

```mermaid
flowchart LR
  B["Layered业务：同R-002完整GM与MIX图"] --> P{"peer/domain"}
  P --> U["域内URMA：已读WQE/SQ/CQ/锁"]
  P --> R["跨域RoCE wrapper"]
  R --> C["channel版64B WQE/DB/CQ body存在"]
  R --> F["batch与Lock/Unlock：固定9.2静态不匹配终点"]
```

```mermaid
block-beta
  columns 1
  init["UB0..512B 两协议Init共享scratch"]
  work["同R-002工作区：512..184KiB-512B"]
  bat["同R-002 batch64KiB；RoCE specialization无batch消费者"]
  cache["readyCache≤512B"]
```

##### 字节账、交接边与复用顺序

```text
自有window_required、L1/L0/UB工作区 = R-002逐slice公式
URMA payload/ready WQE bytes = R-002
RoCE channel-only WQE =16+32+16=64B；CQ scratch从UB128B起
RoCE batch 的实际提交/回收字节与同步：固定来源没有对应实现，不从URMA强行继承
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 域内数据/ready | LayeredUbxComm.urma | 同R-002 | q/s/BF16 | URMA batch | 同R-002实际协议 | owner(peer%AIC) | MR/Drain/Unlock条件 |
| 跨域批量调用 | LayeredUbxComm.roce | 自有CCL地址、batch64KiB | 按业务记录 | 未匹配RoCE batch实例 | static_assert/缺成员终点 | 不声称已提交 | 必须有匹配版本core才可称可执行 |
| 已有RoCE channel SQ/CQ | channel PostSend/PollCq | 64B WQE/门铃 | 网络序 | 硬件 | MTE3_S、PI/CI、CQ owner | HCOMM channel | 只覆盖channel方法，非本batch替代 |
| 双GMM公共交接 | 自有AIC/AIV | 同R-002 | BF16/E5 | 自有后续stage | 同共同模式4/ready计数 | 各stage | 构建成功前仅源码意图 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| 自有业务 | 同R-002 wave/flags/gates | Layered scheduler | 双GMM/Unpermute | 相同full GM | E5 SiTU精度不变 |
| 跨域chunk | 2^31上限，中间2^31-512 | wrapper | batch请求 | 连续payload | 保持512B对齐，非协议可用性证明 |
| static terminal | Hcomm protocol static_assert、RoCE缺batch成员 | C++模板实例化 | 不形成可用batch体 | 无真实提交可声明 | 记录源码冲突，不编造编译器报错文本 |
| channel core | MTE3_S、CQ owner与1e6轮询 | 已有RoCE channel方法 | PollCq | SQ/CQ/注册MR | timeout返回FAILED，无真机结论 |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | comm_context.cpp | UBX topology/channel mapping | 连续domain、跨域RoCE |
| Kernel entry/router | arch35/mega_moe_apt.cpp | topo2→LayeredUbxComm | 自有Host可达路线必须保留 |
| Device body/helper | common/mega_moe_layered_comm.h | LayeredUbxComm | 相同业务、按peer保存协议位、RoCE额外localAddr |
| External terminal | asc-comm impl/hcomm_impl.h | Hcomm<ROCE>::MakeBatchHandle/Lock/Unlock | 明确要求UB_CTP的static_assert |
| External readable core | asc-comm hcomm_aiv_roce.h | PostSend/MakeWqe/PollCq | 仅channel版64B WQE/DB/CQ，不替代缺失batch |

## 算子特定优化

### Trick T-001：按阶段分别启用三wave ring

#### 触发与源码依据

- 适用 Route：R-001。
- 触发条件：MTE、combine非量化、g>0、Mmax>3g256；dispatch额外禁止dispatch/combine去重。
- Golden 来源：[mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_gm_layout.h:534-546](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_gm_layout.h#L534-L546)。

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
HOST_DEVICE constexpr CclStageRingConfig CalcCclStageRingConfig(const CclComputeLayoutParams& params)
{
    CclStageRingConfig ring{};
    ring.rows = CalcMemoryRingRows(params.mGroupsPerWave);
    const bool canReuse = params.topoType == TOPO_TYPE_MTE && !params.combineQuant && params.mGroupsPerWave > 0 &&
                          params.maxOutputSize > static_cast<int64_t>(ring.rows);
    // Combine 去重按完整专家消费，专家内缺少逐 tile 进度约束，Dispatch 输入也需全量保存。
    ring.dispatch = canReuse && !IsDispatchDedupOn(params.dedupMode) && !IsCombineDedupOn(params.dedupMode);
    ring.gmm1 = canReuse;
    ring.activation = canReuse;
    ring.gmm2 = canReuse && !IsCombineDedupOn(params.dedupMode);
    return ring;
}
```

#### 机制与设计原因

Host与Device共用CalcCclStageRingConfig。dispatch-only去重需要FIRST跨expert fanout保留全量输入，因此即使activation/GMM2能ring也不缩dispatch。三wave行数来自共同g计算，元数据/flags保持full。

#### 迁移边界

- 适用：相同进度约束的分阶段GM回收。
- 前提：保持当前950/E5M2/SiTU数学域、对应资源与同轮通信合同。
- 失效：改变selector、dtype/scale布局、group进度或owner必须重新推导。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

源码明确在dedup输入上关闭dispatch ring；将所有stage统一取ring会违背该地址/生命周期条件。未运行越界复现。

### Trick T-002：BF16激活中间值直接生成MX数据与scale

#### 触发与源码依据

- 适用 Route：R-001/R-002；R-003自有body同族。
- 触发条件：Gated activation完成、DataTypeOut=E5M2、validRowCount与outputRowStride已确定。
- Golden 来源：[mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/mega_moe_block_epilogue_activation_mx_quant.h:383-388](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/mega_moe_block_epilogue_activation_mx_quant.h#L383-L388)。

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
    Quant::ComputeMaxExp<bfloat16_t>(ubPointers.activationOutput, ubPointers.maxExp, dataCount);
    Quant::ComputeScale<DataTypeOut>(ubPointers.maxExp, ubPointers.quantScale, ubPointers.inverseMxScale, scaleCount);
    if constexpr (IsSameType<DataTypeOut, fp8_e4m3fn_t>::value || IsSameType<DataTypeOut, fp8_e5m2_t>::value) {
        Quant::ComputeFp8Data<bfloat16_t, DataTypeOut, AscendC::RoundMode::CAST_TRUNC, AscendC::RoundMode::CAST_RINT>(
            ubPointers.activationOutput, ubPointers.inverseMxScale, ubPointers.quantOutput, dataCount);
    }
```

#### 机制与设计原因

同一epilogue对BF16 activationOutput先归约每32元素指数，再产生E8M0/inverse并转换E5M2，q与scale分离写入后续GMM2 GM。保留BF16中间舍入；ComputeFp8Data模板中的CAST_TRUNC供源类型分支选择，实际BF16路径最终E5M2 round为CAST_RINT，不可将template名整体解释成输出截断。

#### 迁移边界

- 适用：同量化规则的GMM激活融合。
- 前提：保持当前950/E5M2/SiTU数学域、对应资源与同轮通信合同。
- 失效：改变selector、dtype/scale布局、group进度或owner必须重新推导。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓未提供可验证反例；不能省略BF16中间值或替换成per-token FP8 scalar scale。

### Trick T-003：relaxed payload配strong CQE尾ready

#### 触发与源码依据

- 适用 Route：R-002；R-003域内URMA子段。
- 触发条件：批量relay data写后追加稳定GM的ready通知。
- Golden 来源：[mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_layered_comm.h:30-33](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_layered_comm.h#L30-L33)。

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
static constexpr UrmaWqeEntry LAYERED_RELAXED_WRITE_WQE_CONFIG = {
    .odr = 5, .fence = 1, .se = 0, .cqe = 0, .inlineEn = 0};
static constexpr UrmaWqeEntry LAYERED_STRONG_COMPLETION_WRITE_WQE_CONFIG = {
    .odr = 6, .fence = 1, .se = 0, .cqe = 1, .inlineEn = 0};
```

#### 机制与设计原因

payload用ODR5/fence1/cqe0减少逐块CQE，最后ready改ODR6/fence1/cqe1提供可轮询完成点。BatchCommit只是提交，Drain仅轮询已计入cqHead的完成请求，不能代替缺少CQE的尾通知。ready缓存仅在确认真实非零后设置。

#### 迁移边界

- 适用：同channel顺序及注册MR稳定的批量通信。
- 前提：保持当前950/E5M2/SiTU数学域、对应资源与同轮通信合同。
- 失效：改变selector、dtype/scale布局、group进度或owner必须重新推导。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

源码WriteStrongNbiWithCqe注释明确全部cqe0时Drain无法确认全部完成。不能把ready先发或从短命UB当GM source；未做通信正确性实测。

### Trick T-004：Cube对象构造/析构成对管理L1与L0 credit

#### 触发与源码依据

- 适用 Route：R-001/R-002；R-003自有Cube同族。
- 触发条件：选中ops-tensor GroupedMatmulWithScaleMx BlockMmad。
- Golden 来源：[include/blaze/gemm/block/block_mmad_qgmm_mx.h:100-120](https://atomgit.com/cann/ops-tensor/blob/fe1d9908c4eaff2943a3b6cea9c2467b8c427f18/include/blaze/gemm/block/block_mmad_qgmm_mx.h#L100-L120)。

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
    __aicore__ inline BlockMmad()
    {
#pragma unroll
        for (uint8_t i = 0; i < MTE1_MTE2_EVENT_ID_NUM; ++i) {
            AscendC::SetFlag<AscendC::HardEvent::MTE1_MTE2>(i);
        }
        AscendC::SetFlag<AscendC::HardEvent::M_MTE1>(M_MTE1_FLAG_0);
        AscendC::SetFlag<AscendC::HardEvent::M_MTE1>(M_MTE1_FLAG_1);
        AscendC::SetMMLayoutTransform(true);
    }

    __aicore__ inline ~BlockMmad()
    {
#pragma unroll
        for (uint8_t i = 0; i < MTE1_MTE2_EVENT_ID_NUM; ++i) {
            AscendC::WaitFlag<AscendC::HardEvent::MTE1_MTE2>(i);
        }
        AscendC::WaitFlag<AscendC::HardEvent::M_MTE1>(M_MTE1_FLAG_0);
        AscendC::WaitFlag<AscendC::HardEvent::M_MTE1>(M_MTE1_FLAG_1);
        AscendC::SetMMLayoutTransform(false);
    }
```

#### 机制与设计原因

构造预置MTE1_MTE2 credit0..7及M_MTE1 id4/5，运行过程中A/B/scale双缓冲消费与归还；析构逐项等待，最后关闭MMLayoutTransform。该对象生命期包含流水排空，不能只复用主K循环而丢构造/析构协议。

#### 迁移边界

- 适用：保留相同event域和MMLayout配置的Cube流水。
- 前提：保持当前950/E5M2/SiTU数学域、对应资源与同轮通信合同。
- 失效：改变selector、dtype/scale布局、group进度或owner必须重新推导。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓未提供可验证反例；不能在event未归还时销毁/复用资源。固定SDK trait不匹配仍使本卡保持draft。

### Trick T-005：SiTU按输入幅度选分段tanh近似

#### 触发与源码依据

- 适用 Route：R-001/R-002及R-003自有激活body。
- 触发条件：actMode=SITU，DEFAULT与LINEAR共同调用；FP32 z=gate/beta或up/lambda，beta/lambda满足Host正有限条件。
- Golden 来源：[situglu_activation.h:61-79](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/activation/situglu_activation.h#L61-L79)。

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
{
    AscendC::Reg::Mul(squareReg, zReg, zReg, computeMask);
    AscendC::Reg::Muls(polynomialReg, squareReg, 0.0157396831F, computeMask);
    AscendC::Reg::Adds(polynomialReg, polynomialReg, -0.0523039624F, computeMask);
    AscendC::Reg::MulDstAdd(polynomialReg, squareReg, c2Reg, computeMask);
    AscendC::Reg::MulDstAdd(polynomialReg, squareReg, c1Reg, computeMask);
    AscendC::Reg::Mul(polynomialReg, polynomialReg, squareReg, computeMask);
    AscendC::Reg::MulDstAdd(polynomialReg, zReg, zReg, computeMask);

    AscendC::Reg::Muls(expReg, zReg, -2.0F, computeMask);
    AscendC::Reg::Exp(expReg, expReg, computeMask);
    AscendC::Reg::Adds(expReg, expReg, 1.0F, computeMask);
    AscendC::Reg::Div(temporaryReg, oneReg, expReg, computeMask);
    AscendC::Reg::Muls(temporaryReg, temporaryReg, 2.0F, computeMask);
    AscendC::Reg::Adds(temporaryReg, temporaryReg, -1.0F, computeMask);

    AscendC::Reg::Abs(absReg, zReg, computeMask);
    AscendC::Reg::CompareScalar<float, AscendC::CMPMODE::GE>(compareMask, absReg, 0.60000002384185791016F, computeMask);
    AscendC::Reg::Select(resultReg, temporaryReg, polynomialReg, compareMask);
```

#### 机制与设计原因

小|z|使用九次奇多项式，大|z|使用2/(1+exp(-2z))-1；比较阈值0.60000002384185791016，Select在相同寄存器流选择结果。两侧表达式均在computeMask下计算，不能把Select当成避免另一表达式执行的分支。DEFAULT只对gate计算一次，LINEAR还对up/lambda复用同函数。Reg和3510 FTZ C API分别实现同一分段结构，局部寄存器增加不产生额外GM/UB slice，MX阶段仍消费最终BF16中间值。

#### 迁移边界

- 适用：保留系数、阈值、FMA顺序及BF16中间舍入的950 SiTU。
- 前提：Host先验参数1/2个且尺度正有限，计算/存储tail mask分开。
- 失效：抽象tanh API、A3 Tanh近似或其它阈值不保证当前数值；SwiGLU不是此分段式。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓未提供可验证反例；不能因为数学名称相同就替换A3 Tanh primitive、删除beta/linear分支或跳过BF16到MX的中间舍入。

## 模板与实现对比

| 对比维度 | R-001 MTE Wave | R-002 URMA | R-003 UBX | 设计选择依据 |
|---|---|---|---|---|
| 命中条件/优先级 | topo0、K(i,0)，auto dedup0/2 | topo1、K(1,1) | topo2、K(1,1) | 先自动拓扑再按runtime topo分Layered CommPolicy |
| 执行族/节点图 | 单MIX内MTE peer直接GM | 单MIX内URMA relay/read/write | 自有相同MIX，跨域RoCE存在静态终点 | 同数学，通信实现不同 |
| M/N/K、tile 与 scheduler | 256×256，K128，Swizzle3；B≥4096延迟GMM2 | 同Cube，通信wave≥2计算wave，按g组调度 | 同自有计算 | 权重ND及valid tail参数化 |
| workspace/L1/L0/UB | 3-wave数据ring条件化；60KiB异常头 | full GM、relay/mask/counter/batch64KiB | 业务布局同URMA；RoCE batch无实际消费者 | stage生命周期决定可复用范围 |
| AIC/AIV 或 kernel 交接 | GMM1 UB直达/mode4；GMM2 GM→AIV1 UB/mode4；dispatch/act ready | GMM1 mode4，GMM2 GM+atomic group counter | 自有同URMA | 避免混淆UB与GM交接 |
| 同步、精度与 tail | MTE/PIPE/跨rankepoch，E5/E8M0与BF16舍入 | channel锁/WQE/CQ +跨rankepoch，同数学 | 现有channel body不替代batch | 逐层列明真实primitive |
| fallback/失败边界 | Host容量/dedup降0；零域静态除零边界 | 非法容量失败；batch outstanding未见自动回收 | RoCE batch/Lock/Unlock static不匹配，无可见fallback | source_closed不表示编译/运行正确 |

## 平台差异

| 项目 | A2 | A3 | Ascend 950 |
|---|---|---|---|
| 支持状态 | 本E5M2动态MX数学域不支持 | 本数学域不支持，另有BF16/INT8/INT4 Mode3卡 | OpDef/文档有当前域；固定依赖静态限制保留draft |
| Host/Launcher | 非本arch35 Host | arch22 Host/POD与权重方向不同 | arch35 Host、608B tiling、24624B context、CANN9.2 |
| Kernel/资源 | 不套用 | CATLASS2 A3实现不代替950 | ops-tensor MX BlockMmad、SDK3510、MTE/URMA/UBX自有图；UB与trait冲突见下 |

## 限制与失败边界

- 输入MX量化的ComputeMaxExp/ComputeFp8Data按ceil(H/256)读取两个BF16寄存器，实际UB读域为2·A256(H)字节；单输入slot名义容量为2·A128(H)。H%256为64或128时，Reg load可读入相邻slot/routeRing backing。有效H及H/32 scale的提交/消费域并不证明物理load已由mask缩短；额外组不进入有效K消费，但仍须分别核backing与生命周期，不宣称已观察UB越界或数值故障。

- 本卡范围为SGL实际mx_fp8_e5m2+situ/situglu、shared0/动态MX/combine0/tkw0/显式combineDedup0；保存自动dispatch去重及所有自动拓扑。公开CANN更宽的shared异构、预量化、OAI/step/GELU不是不存在，统一在配套API Reference保存，不把它们冒充本张完整数学覆盖。
- ops-transformer CMake固定ops-tensor fe1d9908；其tile_trait.h以gm_to_l1_trait{true}构造预分配trait，而固定SDK9.2 a63d5261该结构为空。此为源码可见接口不匹配，未编译；不擅用9.3 trait替换或声称9.2安装ABI已验证。
- Gmm1OutputView重建默认copy_l0c_to_ub，未继承上游SplitM；两个256×256 BF16 raw槽到262144B，SDK3510 TOTAL_UB_SIZE为253952B。Host自适应Send/Dispatch/Unpermute预算不能证明该固定raw区域合法。本卡保留原始资源式，不凭注释或假设拆M消去差异，不宣称已观察越界故障。
- UBX topo2确实Host可达，自有完整Layered业务存在；asc-comm9.2 Hcomm对RoCE的MakeBatchHandle/Lock/Unlock要求UB_CTP，RoCE specialization无batch Read/Write/BatchCommit/Drain。已有channel body、相似API或URMA实现不能替代该缺实例；记录静态terminal及可读源码，不制造运行错误或完成保证。
- HCOMM与asc-comm URMA ChannelEntity前缀及reserve计数可按字段映射；这是固定源码映射，不能代表已安装二进制ABI。RoCE SQ/CQ部分字段有差异，未将其判作可用batch ABI。
- asc-comm BatchCommit未见outstanding SQ/CQ回收，只有本批容量/SQdepth检查与环形写入；业务wrapper注释不能当实现。Drain的CQE计数、返回码未全面检查和跨核锁/窗口同轮进入前提必须保留；未做多rank压力或故障注入。
- B=0在MTE Host可被更早校验接受，SetUnpermuteBufferConfigs随后用fullTokenChunkSize=ceil(B/AIV)作除数，存在0/0静态边界；Layered显式拒绝零B。原始shape到uint32转换前缺充分负数/超UINT32守卫的可见边界，不推导已观察codegen/Runtime错误。
- 专家ID不重复/有效、M_e≤CR、各rank同轮调用是业务前提，Host未扫描内容；Mmax裁剪、mask尾域和空专家跳过不扩大为无效/重复ID的公开支持。
- CCL窗口和channel/MR由通信对象拥有；未见本层显式deregister/channel/enginectx释放不能改写为完整对称释放承诺；cache-hit未填fresh context的可见路径也未运行验证。
- SiTU Host只要求beta/lambda正且有限，未进一步保证float倒数或所有中间值有限；invBeta/invAlpha、Exp/Div、两支Select均保留源码次序，不把参数guard当全数值安全证明。
- 最终BF16 gate累加、激活NO_SAT/RINT、MX SAT/RINT、Fixpipe、CTRL bit60原值恢复各自独立；不提供全局饱和、非有限清理或与其它数学域的逐位等价保证。
- 本次仅源码提取，未执行上游、编译、真机、数值、性能或安装测试；没有伪造verified。框架生成桥、硬件intrinsic、注册/IPC runtime的内部实现为明确primitive终点。

## 源码索引

### 链路索引

表中每行只对应一个固定提交文件；上文简写路径均以对应仓为根。header、实现、构建和supporting来源与Frontmatter一致，原文Golden仅用连续真实行。

| 链路阶段 | 文件 | 关键符号 | 支撑内容 |
|---|---|---|---|
| SGL接入 | [sgl/python/deep_ep/doc/FUSED_DEEP_MOE.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/doc/FUSED_DEEP_MOE.md) | Mode 3 / CANN 9.2 | 固定主来源 |
| SGL接入 | [sgl/python/deep_ep/README.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/README.md) | MEGA_MOE 接入 | 版本/支持依据 |
| SGL接入 | [sgl/python/deep_ep/deep_ep/buffer.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/buffer.py) | Buffer.fused_deep_moe | 上文对应调用、布局、同步或边界 |
| SGL接入 | [sgl/python/deep_ep/deep_ep/strategies/fused_strategy.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/deep_ep/strategies/fused_strategy.py) | MegaMoeStrategy | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/README.md](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/README.md) | 950 支持与权重约束 | 固定主来源 |
| 入口/Device | [ops/version.cmake](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/version.cmake) | 9.2.0 | 版本/支持依据 |
| 入口/Device | [ops/mc2/mega_moe/torch_extension/mega_moe.py](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/torch_extension/mega_moe.py) | SymmBuffer/npu_mega_moe | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/torch_extension/csrc/mega_moe.cpp](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/torch_extension/csrc/mega_moe.cpp) | NpuMegaMoe/CalcCclBufferSizeA5 | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/torch_extension/cann_ops_transformer/common/aclnn_common.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/torch_extension/cann_ops_transformer/common/aclnn_common.h) | ACLNN_CMD/描述符 | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/torch_extension/cann_ops_transformer/common/hccl_common.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/torch_extension/cann_ops_transformer/common/hccl_common.h) | HCCL 动态装载 | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/common/torch_extension/comm_context.py](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/common/torch_extension/comm_context.py) | CommContextManager | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/common/torch_extension/csrc/comm_context.cpp](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/common/torch_extension/csrc/comm_context.cpp) | CopyContextToTensor/GetCommProtocol/CheckProtocolSupport/GetHcclCommChannel | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_api/aclnn_mega_moe.cpp](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_api/aclnn_mega_moe.cpp) | aclnnMegaMoeGetWorkspaceSize/aclnnMegaMoe | 上文对应调用、布局、同步或边界 |
| Host/Tiling/构建 | [ops/mc2/mega_moe/op_host/mega_moe_def.cpp](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/mega_moe_def.cpp) | MegaMoe/AddConfig(ascend950) | 上文对应调用、布局、同步或边界 |
| Host/Tiling/构建 | [ops/mc2/mega_moe/op_host/mega_moe_infershape.cpp](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/mega_moe_infershape.cpp) | InferShape | 上文对应调用、布局、同步或边界 |
| Host/Tiling/构建 | [ops/mc2/mega_moe/op_host/op_tiling/arch35/mega_moe_tiling.cpp](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/op_tiling/arch35/mega_moe_tiling.cpp) | MegaMoeTiling | 上文对应调用、布局、同步或边界 |
| Host/Tiling/构建 | [ops/mc2/mega_moe/op_host/op_tiling/mega_moe_tiling_host.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/op_tiling/mega_moe_tiling_host.h) | Host 参数/枚举 | 上文对应调用、布局、同步或边界 |
| Host/Tiling/构建 | [ops/mc2/mega_moe/op_host/op_tiling/arch35_92/mega_moe_tiling_check.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/op_tiling/arch35_92/mega_moe_tiling_check.h) | CheckAndSet* | 上文对应调用、布局、同步或边界 |
| Host/Tiling/构建 | [ops/mc2/mega_moe/op_host/op_tiling/arch35_92/mega_moe_tiling_buffer_calc.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/op_tiling/arch35_92/mega_moe_tiling_buffer_calc.h) | Calc*BufferConfig | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35/mega_moe_apt.cpp](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35/mega_moe_apt.cpp) | mega_moe/MegaMoeMteWave | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35/mega_moe_arch35.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35/mega_moe_arch35.h) | MegaMoeBase | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35/mega_moe_wave_a8w8.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35/mega_moe_wave_a8w8.h) | MegaMoeA8W8Wave | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35/mega_moe_layered.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35/mega_moe_layered.h) | MegaMoeLayered | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35/mega_moe_vf/mega_moe_vf.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35/mega_moe_vf/mega_moe_vf.h) | 路由 VF | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/mega_moe_tiling.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/mega_moe_tiling.h) | MegaMoeTilingData | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/mega_moe_arch35_92_tiling_key.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/mega_moe_arch35_92_tiling_key.h) | 模板 selector | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/common/op_kernel/mc2_moe_context.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/common/op_kernel/mc2_moe_context.h) | Mc2MoeContext | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/common/op_kernel/mc2_kernel_utils.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/common/op_kernel/mc2_kernel_utils.h) | 内核初始化/辅助 | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/common/op_kernel/quantize_functions.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/common/op_kernel/quantize_functions.h) | ComputeMaxExp/ComputeFp8Data | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/common/op_kernel/mc2_exception_dump.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/common/op_kernel/mc2_exception_dump.h) | 异常记录边界 | 上文对应调用、布局、同步或边界 |
| Host/Tiling/构建 | [ops/mc2/mega_moe/op_host/CMakeLists.txt](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_host/CMakeLists.txt) | op_api/ascend950 编译 | 上文对应调用、布局、同步或边界 |
| 构建接线 | [ops/cmake/third_party/ops-tensor.cmake](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/cmake/third_party/ops-tensor.cmake) | OPTENSOR_TAG_ID | 上文对应调用、布局、同步或边界 |
| 构建接线 | [ops/cmake/variables.cmake](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/cmake/variables.cmake) | BLAZE 源路径 | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_arch_policy.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_arch_policy.h) | Arch35Policy | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_constants.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_constants.h) | 资源/flag 常量 | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_types.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_types.h) | 权重与量化类型 | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_utils.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_utils.h) | BalancedDispatch/地址 | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_gm_layout.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_gm_layout.h) | CclComm/WorkspaceLayout | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_sync.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_sync.h) | MTE/原子/屏障 | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_copy.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_copy.h) | GM/UB 搬运 | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_gmm_common.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_gmm_common.h) | GmmKernel::Config/BlockMmadSelector | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_gmm_epilogue_sync.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_gmm_epilogue_sync.h) | AIC↔AIV handshakes | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_layered_comm.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_layered_comm.h) | LayeredUrmaComm/LayeredUbxComm | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_mxfp8_utils.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_mxfp8_utils.h) | QuantMx | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_arch35_92_exception_dump_policy.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/common/mega_moe_arch35_92_exception_dump_policy.h) | 诊断字段 | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_workspace_reset.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_workspace_reset.h) | ResetFlagList | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_token_quant.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_token_quant.h) | TokenQuant | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_send_mask.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_send_mask.h) | SendMaskCal | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_expert_count.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_expert_count.h) | 计数/前缀 | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_token_dispatch.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_token_dispatch.h) | CopyGMToGMPerToken | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_token_dedup.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_token_dedup.h) | dispatch-only 描述符 | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_token_dispatch_dedup.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_token_dispatch_dedup.h) | FIRST/SKIP/PLAIN | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_gmm1_activation.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_gmm1_activation.h) | GMM1Generic/Activation | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_gmm2_combine.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_gmm2_combine.h) | GMM2/Combine | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_gmm2_combine_dedup.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_gmm2_combine_dedup.h) | Dedup 侧 GMM2 复用 | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_unpermute.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_unpermute.h) | Unpermute | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_layered_dispatch.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_layered_dispatch.h) | 分层 relay/拉取 | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_layered_combine.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_layered_combine.h) | 分层完成计数/回传 | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_layered_combine_send.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/stage/mega_moe_layered_combine_send.h) | CombineSend | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/mega_moe_vf/mega_moe_layered_vf.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/mega_moe_vf/mega_moe_layered_vf.h) | mask/prefix VF | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/blaze/gemm/block/block_scheduler_swizzle.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/gemm/block/block_scheduler_swizzle.h) | BlockSchedulerSwizzle<3,0> | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/blaze/gemm/tile/copy_gmm1_concat.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/gemm/tile/copy_gmm1_concat.h) | Gmm1OutputView（NZ分支在本域inactive） | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/block_epilogue_ub_layout.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/block_epilogue_ub_layout.h) | 激活 UB offsets | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/mega_moe_block_epilogue_activation_mx_quant.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/mega_moe_block_epilogue_activation_mx_quant.h) | 激活→MX epilogue | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/activation/activation_common.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/activation/activation_common.h) | BF16 Cast | 上文对应调用、布局、同步或边界 |
| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/rowwise_mx_quant.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/rowwise_mx_quant.h) | 逐行 MX 量化 | 上文对应调用、布局、同步或边界 |
| Cube核心 | [opstensor/include/blaze/gemm/block/block_mmad_qgmm_mx.h](https://atomgit.com/cann/ops-tensor/blob/fe1d9908c4eaff2943a3b6cea9c2467b8c427f18/include/blaze/gemm/block/block_mmad_qgmm_mx.h) | BlockMmad<GroupedMatmulWithScaleMx> | 固定主来源 |
| Cube核心 | [opstensor/include/blaze/gemm/policy/dispatch_policy.h](https://atomgit.com/cann/ops-tensor/blob/fe1d9908c4eaff2943a3b6cea9c2467b8c427f18/include/blaze/gemm/policy/dispatch_policy.h) | GroupedMatmulWithScaleMx | 上文对应调用、布局、同步或边界 |
| Cube核心 | [opstensor/include/blaze/gemm/block/block_mmad_decl.h](https://atomgit.com/cann/ops-tensor/blob/fe1d9908c4eaff2943a3b6cea9c2467b8c427f18/include/blaze/gemm/block/block_mmad_decl.h) | BlockMmad 声明 | 上文对应调用、布局、同步或边界 |
| Cube核心 | [opstensor/include/blaze/gemm/utils/common_utils.h](https://atomgit.com/cann/ops-tensor/blob/fe1d9908c4eaff2943a3b6cea9c2467b8c427f18/include/blaze/gemm/utils/common_utils.h) | 资源/事件常量 | 上文对应调用、布局、同步或边界 |
| Cube核心 | [opstensor/include/blaze/gemm/utils/layout_utils.h](https://atomgit.com/cann/ops-tensor/blob/fe1d9908c4eaff2943a3b6cea9c2467b8c427f18/include/blaze/gemm/utils/layout_utils.h) | DN/scale 布局（本域不选NZ） | 上文对应调用、布局、同步或边界 |
| Cube核心 | [opstensor/include/blaze/gemm/tile/compute.h](https://atomgit.com/cann/ops-tensor/blob/fe1d9908c4eaff2943a3b6cea9c2467b8c427f18/include/blaze/gemm/tile/compute.h) | TileMmad | 上文对应调用、布局、同步或边界 |
| Cube核心 | [opstensor/include/blaze/gemm/tile/datamove.h](https://atomgit.com/cann/ops-tensor/blob/fe1d9908c4eaff2943a3b6cea9c2467b8c427f18/include/blaze/gemm/tile/datamove.h) | 拷贝 trait 路由 | 上文对应调用、布局、同步或边界 |
| Cube核心 | [opstensor/include/blaze/gemm/tile/tile_trait.h](https://atomgit.com/cann/ops-tensor/blob/fe1d9908c4eaff2943a3b6cea9c2467b8c427f18/include/blaze/gemm/tile/tile_trait.h) | CopyGM2L1TraitPreAllocation | 上文对应调用、布局、同步或边界 |
| Cube核心 | [opstensor/include/blaze/gemm/tile/arch35/copy_gm_to_l1.h](https://atomgit.com/cann/ops-tensor/blob/fe1d9908c4eaff2943a3b6cea9c2467b8c427f18/include/blaze/gemm/tile/arch35/copy_gm_to_l1.h) | CopyConcatGM2L1 | 上文对应调用、布局、同步或边界 |
| Cube核心 | [opstensor/include/blaze/gemm/tile/arch35/pad_mx_kl1.h](https://atomgit.com/cann/ops-tensor/blob/fe1d9908c4eaff2943a3b6cea9c2467b8c427f18/include/blaze/gemm/tile/arch35/pad_mx_kl1.h) | PadMxKl1 | 上文对应调用、布局、同步或边界 |
| SDK primitive/边界 | [sdk/include/tensor_api/arch/cube/mmad_trait.h](https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/include/tensor_api/arch/cube/mmad_trait.h) | MMAD_TYPE_MX/MmadTrait | 固定主来源 |
| SDK primitive/边界 | [sdk/version.cmake](https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/version.cmake) | 9.2.0 | 版本/支持依据 |
| SDK primitive/边界 | [sdk/include/tensor_api/arch/cube/cube_copy_trait.h](https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/include/tensor_api/arch/cube/cube_copy_trait.h) | gm_to_l1_trait/dual_dst | 上文对应调用、布局、同步或边界 |
| SDK primitive/边界 | [sdk/impl/tensor_api/arch/cube/mmad/mmad_impl/mmad.h](https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/impl/tensor_api/arch/cube/mmad/mmad_impl/mmad.h) | MX MMAD 字段 | 上文对应调用、布局、同步或边界 |
| SDK primitive/边界 | [sdk/impl/tensor_api/arch/cube/mmad/mmad_impl/instruction.h](https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/impl/tensor_api/arch/cube/mmad/mmad_impl/instruction.h) | asc_mmad_mx | 上文对应调用、布局、同步或边界 |
| SDK primitive/边界 | [sdk/impl/tensor_api/arch/cube/l0c_to_ub/copy_impl/l0c_to_ub_data_copy.h](https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/impl/tensor_api/arch/cube/l0c_to_ub/copy_impl/l0c_to_ub_data_copy.h) | 有效 M/N 与 Fixpipe | 上文对应调用、布局、同步或边界 |
| SDK primitive/边界 | [sdk/impl/tensor_api/arch/cube/l0c_to_ub/copy_impl/instruction.h](https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/impl/tensor_api/arch/cube/l0c_to_ub/copy_impl/instruction.h) | asc_copy_l0c2ub | 上文对应调用、布局、同步或边界 |
| SDK primitive/边界 | [sdk/include/basic_api/kernel_operator_sys_var_intf.h](https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/include/basic_api/kernel_operator_sys_var_intf.h) | GetSubBlockIdx/CTRL | 上文对应调用、布局、同步或边界 |
| SDK primitive/边界 | [sdk/impl/basic_api/dav_3510/kernel_operator_sys_var_impl.h](https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/impl/basic_api/dav_3510/kernel_operator_sys_var_impl.h) | 3510 资源/系统变量 | 上文对应调用、布局、同步或边界 |
| 兼容KFC前端边界 | [hccl/include/hccl_mc2.h](https://gitcode.com/cann/hccl/blob/f9a2fd998475dcc78d0066660c3be5d8bd2f05bc/include/hccl_mc2.h) | HcclCreateOpResCtx 前端 | 固定主来源 |
| 兼容KFC前端边界 | [hccl/src/common/hccl_mc2.cc](https://gitcode.com/cann/hccl/blob/f9a2fd998475dcc78d0066660c3be5d8bd2f05bc/src/common/hccl_mc2.cc) | 动态 Inner 转发 | 上文对应调用、布局、同步或边界 |
| 兼容KFC前端边界 | [hccl/version.cmake](https://gitcode.com/cann/hccl/blob/f9a2fd998475dcc78d0066660c3be5d8bd2f05bc/version.cmake) | 9.2.0 | 版本/支持依据 |
| Host通信资源 | [hcomm/pkg_inc/hcomm/hcomm_res_entity_defs.h](https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/pkg_inc/hcomm/hcomm_res_entity_defs.h) | Host ChannelEntity/SQ/CQ ABI | 固定主来源 |
| Host通信资源 | [hcomm/src/coll_communicator_mgr/api_c_adpt/coll_comm_res_c_adpt.cc](https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/coll_communicator_mgr/api_c_adpt/coll_comm_res_c_adpt.cc) | HcclChannelAcquire/ConvertAivChannelHandlesToDevicePtrs | 上文对应调用、布局、同步或边界 |
| Host通信资源 | [hcomm/src/coll_communicator_mgr/api_c_adpt/resource/channel_c_adpt.cc](https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/coll_communicator_mgr/api_c_adpt/resource/channel_c_adpt.cc) | HcclChannelGetRemoteMems | 上文对应调用、布局、同步或边界 |
| Host通信资源 | [hcomm/src/coll_communicator_mgr/resource_mgr/local/my_rank/my_rank.cc](https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/coll_communicator_mgr/resource_mgr/local/my_rank/my_rank.cc) | MyRank::CreateChannels | 上文对应调用、布局、同步或边界 |
| Host通信资源 | [hcomm/src/base_comm/resources/endpoint_pairs/channels/aiv/aiv_urma_channel.cc](https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/base_comm/resources/endpoint_pairs/channels/aiv/aiv_urma_channel.cc) | BuildChannelEntityToDevice | 上文对应调用、布局、同步或边界 |
| Host通信资源 | [hcomm/src/base_comm/resources/endpoint_pairs/channels/aiv/aiv_urma_transport.cc](https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/base_comm/resources/endpoint_pairs/channels/aiv/aiv_urma_transport.cc) | GetSqContext/GetCqContext/GetHostChannelEntity | 上文对应调用、布局、同步或边界 |
| Host通信资源 | [hcomm/version.cmake](https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/version.cmake) | 9.2.0 | 版本/支持依据 |
| AIV通信核心 | [asccomm/include/aicore/hcomm/hcomm.h](https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/include/aicore/hcomm/hcomm.h) | Hcomm 公共签名/保留接口 | 固定主来源 |
| AIV通信核心 | [asccomm/include/aicore/hcomm/hcomm_common.h](https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/include/aicore/hcomm/hcomm_common.h) | ChannelHandle/CommProtocol | 上文对应调用、布局、同步或边界 |
| AIV通信核心 | [asccomm/src/aicore/hcomm/common/hcomm_inner_def.h](https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/src/aicore/hcomm/common/hcomm_inner_def.h) | ChannelEntity/BatchHandle/WQE/CQE | 上文对应调用、布局、同步或边界 |
| AIV通信核心 | [asccomm/src/aicore/hcomm/common/hcomm_utils.h](https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/src/aicore/hcomm/common/hcomm_utils.h) | MR 范围与 cache/event | 上文对应调用、布局、同步或边界 |
| AIV通信核心 | [asccomm/src/aicore/hcomm/impl/hcomm_impl.h](https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/src/aicore/hcomm/impl/hcomm_impl.h) | Hcomm 转发及 RoCE static_assert | 上文对应调用、布局、同步或边界 |
| AIV通信核心 | [asccomm/src/aicore/hcomm/impl/platform_v310/hcomm_aiv_urma_def.h](https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/src/aicore/hcomm/impl/platform_v310/hcomm_aiv_urma_def.h) | 512B/64B/Mutex29 | 上文对应调用、布局、同步或边界 |
| AIV通信核心 | [asccomm/src/aicore/hcomm/impl/platform_v310/hcomm_aiv_urma.h](https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/src/aicore/hcomm/impl/platform_v310/hcomm_aiv_urma.h) | BatchPostSend/BatchCommit/PollCq/Lock | 上文对应调用、布局、同步或边界 |
| AIV通信核心 | [asccomm/src/aicore/hcomm/impl/platform_v310/hcomm_aiv_roce_def.h](https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/src/aicore/hcomm/impl/platform_v310/hcomm_aiv_roce_def.h) | RoCE specialization | 上文对应调用、布局、同步或边界 |
| AIV通信核心 | [asccomm/src/aicore/hcomm/impl/platform_v310/hcomm_aiv_roce.h](https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/src/aicore/hcomm/impl/platform_v310/hcomm_aiv_roce.h) | channel 版 WQE/DB/CQ | 上文对应调用、布局、同步或边界 |
| AIV通信核心 | [asccomm/scripts/package/build_package.sh](https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/scripts/package/build_package.sh) | adv_api/comm_api 安装路径 | 上文对应调用、布局、同步或边界 |
| AIV通信核心 | [asccomm/docs/dependencies.md](https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/docs/dependencies.md) | 版本与样例范围 | 版本/支持依据 |
| AIV通信核心 | [asccomm/version.cmake](https://atomgit.com/cann/asc-comm/blob/34c83aecfb10c01a79a70d8cc7ec84a7437d437d/version.cmake) | ASCCOMM_VERSION 9.2.0 | 版本/支持依据 |
| executor框架 | [opbase/include/nnopbase/opdev/op_executor.h](https://gitcode.com/cann/opbase/blob/de414d06cfb7bf2728a555bfb9fc1d26a4c83792/include/nnopbase/opdev/op_executor.h) | executor/workspace 生命周期 | 固定主来源 |
| SDK primitive/边界 | [sdk/impl/basic_api/utils/kernel_utils_constants.h](https://gitcode.com/cann/asc-devkit/blob/a63d5261c7c8077a0081e867f43a0e884fec066b/impl/basic_api/utils/kernel_utils_constants.h) | 3510 UB/L1/L0 容量 | 上文对应调用、布局、同步或边界 |
| Host通信资源 | [hcomm/src/base_comm/resources/endpoint_pairs/channels/aiv/aiv_ub_mem_channel.cc](https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/base_comm/resources/endpoint_pairs/channels/aiv/aiv_ub_mem_channel.cc) | AivUbMemChannel::GetRemoteMems | 上文对应调用、布局、同步或边界 |
| Host通信资源 | [hcomm/src/base_comm/resources/endpoint_pairs/channels/aiv/aiv_ub_mem_transport.cc](https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/base_comm/resources/endpoint_pairs/channels/aiv/aiv_ub_mem_transport.cc) | IPC DTO交换/RemoteIpcRmaBuffer构造 | 上文对应调用、布局、同步或边界 |
| Host通信资源 | [hcomm/src/legacy/ascend950/unified_platform/resource/buffer/remote_rma_buffer.cc](https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/legacy/ascend950/unified_platform/resource/buffer/remote_rma_buffer.cc) | RemoteIpcRmaBuffer::OpenIpcMemory/Close | 上文对应调用、布局、同步或边界 |
| Host通信资源 | [hcomm/src/legacy/ascend950/unified_platform/resource/buffer/local_ipc_rma_buffer.cc](https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/legacy/ascend950/unified_platform/resource/buffer/local_ipc_rma_buffer.cc) | LocalIpcRmaBuffer::GetExchangeDto/Grant | 上文对应调用、布局、同步或边界 |
| Host通信资源 | [hcomm/src/legacy/ascend950/unified_platform/resource/buffer/exchange_ipc_buffer_dto.h](https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/legacy/ascend950/unified_platform/resource/buffer/exchange_ipc_buffer_dto.h) | ExchangeIpcBufferDto | 上文对应调用、布局、同步或边界 |
| Host通信资源 | [hcomm/src/legacy/ascend950/unified_platform/resource/mem/user_remote_mem_getter.h](https://gitcode.com/cann/hcomm/blob/95dd5a3f4dd78d05b32fa7a679b8d16f5b3f2cea/src/legacy/ascend950/unified_platform/resource/mem/user_remote_mem_getter.h) | GetRemoteUserMems | 上文对应调用、布局、同步或边界 |

| 入口/Device | [ops/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/activation/situglu_activation.h](https://gitcode.com/cann/ops-transformer/blob/e7da18105f08b06e01ef0fff78f439098d483746/mc2/mega_moe/op_kernel/arch35_92/blaze/epilogue/activation/situglu_activation.h) | RunSiTUGLU / ComputeSituGluTanhPiecewiseApprox | DEFAULT/LINEAR、3510 FTZ与非FTZ实际body |

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | 608B tiling、24624B context及嵌套字段、URMA ChannelEntity静态映射 | 所有offset/位宽/单位、inactive字段和reserve计数别名；LocalTensor不作Host ABI | MegaMoeTilingData/Mc2MoeContext/ChannelEntity |
| 调用顺序 | Prepare→Dispatch→GMM1/Act/MX→GMM2/Combine→同步→Unpermute | 三角色同wave归属、B≥4096延迟、ready后读、Drain全部owner peers | MegaMoeA8W8Wave/MegaMoeLayered::Process |
| workspace/内存 | 自定义CCL同时容纳通信与本地计算区；libAPI workspace分开 | A32/A256/A512、full元数据、ring admission、UB不同阶段复用；固定raw UB冲突 | WorkspaceLayout/CalcCclCommLayout |
| 同步 | mode4 AIC↔AIV、GM atomic行/group ready、MTE退出epoch、URMA锁/WQE/CQ | 构造credit与析构drain成对、PIPE域/事件号、同channel强ready、复用前完成 | Gmm1ActivationSync/BlockMmad/Hcomm |
| 精度与尾块 | BF16中间值→32元素E5 MX→MX Mmad→BF16，typed gates FP32乘/add | scale K64 pair、SAT/NO_SAT及RINT各自阶段、validM/N/K、mask stale tail | RunGatedMxQuantTile/ComputeScale/Unpermute |
| 失败边界 | Host失败/宏无body/已知静态terminal与runtime未验证分别保留 | 不把source_closed当编译/运行通过；不拿SDK9.3或同名RoCE方法补造9.2实现 | CheckAndSet*/Hcomm static_assert/gm_to_l1_trait |
