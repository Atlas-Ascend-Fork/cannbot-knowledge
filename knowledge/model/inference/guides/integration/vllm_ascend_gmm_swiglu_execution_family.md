---
type: Guide
title: vLLM Ascend GMM与SwiGLu融合族：接口门禁、分片workspace与混合核执行
description: 沿GroupedMatmulSwigluQuant及V2区分DAV_2201与DAV_3510 handler、packed INT4描述符、权重列表和scale布局；核对WeightNzV2丢失属性、MSD高低位重建、A4W4 smoothScale、零scale与clamp差异、UB和workspace分片及Cube/Vector同步边界。 补充WeightNzTensorList的A8W8专用入口、列表布局/scale门禁、prefill双workspace及输出offset未写边界。
aliases:
- GroupedMatmulSwigluQuant
- GroupedMatmulSwigluQuantV2
- GroupedMatmulSwigluQuantWeightNzTensorList
- TilingGMMSwigluQuantTensorList
- gmm_dsq_base::GroupedMatmulSwigluQuantBaseHandler
- gmmSwigluQuantV2::GroupedMatmulSwigluQuantBaseHandler
- GMMSwigluQuantPipelineSchedule
- GMMA8W4PreProcess
- GMMA4W4PostProcess
- GroupedMatmulDequantSwigluQuantFusion
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.mixture_of_experts
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant/README.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant/op_host/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant/op_host/grouped_matmul_swiglu_quant_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant/op_host/grouped_matmul_swiglu_quant_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant/op_host/grouped_matmul_swiglu_quant_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant/op_host/grouped_matmul_swiglu_quant_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant/op_host/op_api/aclnn_grouped_matmul_swiglu_quant.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant/op_host/op_api/aclnn_grouped_matmul_swiglu_quant.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant/op_host/op_api/aclnn_grouped_matmul_swiglu_quant_weight_nz.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant/op_host/op_api/grouped_matmul_swiglu_quant.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant/op_host/op_api/grouped_matmul_swiglu_quant.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant/op_kernel/grouped_matmul_swiglu_pipeline.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant/op_kernel/grouped_matmul_swiglu_quant.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant/op_kernel/grouped_matmul_swiglu_quant.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant/op_kernel/grouped_matmul_swiglu_quant_a8w4_msd_mid.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant/op_kernel/grouped_matmul_swiglu_quant_a8w4_msd_post.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant/op_kernel/grouped_matmul_swiglu_quant_a8w4_msd_pre.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant/op_kernel/grouped_matmul_swiglu_quant_split_ws.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant/op_kernel/grouped_matmul_swiglu_quant_utils.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_host/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_host/grouped_matmul_swiglu_quant_v2_base_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_host/grouped_matmul_swiglu_quant_v2_base_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_host/grouped_matmul_swiglu_quant_v2_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_host/grouped_matmul_swiglu_quant_v2_fusion_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_host/grouped_matmul_swiglu_quant_v2_host_utils.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_host/grouped_matmul_swiglu_quant_v2_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_host/grouped_matmul_swiglu_quant_v2_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_host/op_api/aclnn_grouped_matmul_swiglu_quant_v2.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_host/op_api/aclnn_grouped_matmul_swiglu_quant_weight_nz_v2.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_host/op_api/gmm_dsq_base.h
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_host/op_api/grouped_matmul_swiglu_quant_utils.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_host/op_api/grouped_matmul_swiglu_quant_v2.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_host/op_api/grouped_matmul_swiglu_quant_v2_utils.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/arch35/grouped_matmul_swiglu_quant_v2_mxquant.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/arch35/grouped_matmul_swiglu_quant_v2_pertoken_quant.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/arch35/grouped_matmul_swiglu_quant_v2_tiling_key.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/grouped_matmul_swiglu_quant_spilit_fusion.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/grouped_matmul_swiglu_quant_v2.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/grouped_matmul_swiglu_quant_v2_a4w4_mid.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/grouped_matmul_swiglu_quant_v2_a4w4_pipeline.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/grouped_matmul_swiglu_quant_v2_a4w4_post.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/grouped_matmul_swiglu_quant_v2_a8w4_msd_mid.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/grouped_matmul_swiglu_quant_v2_a8w4_msd_pipeline.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/grouped_matmul_swiglu_quant_v2_a8w4_msd_post.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/grouped_matmul_swiglu_quant_v2_a8w4_msd_pre.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/grouped_matmul_swiglu_quant_v2_apt.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_kernel/grouped_matmul_swiglu_quant_v2_utils.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/grouped_matmul_swiglu_quant_v2_torch_adpt.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_host/op_api/aclnn_grouped_matmul_swiglu_quant_v2.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_host/op_api/grouped_matmul_swiglu_quant_v2.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_host/grouped_matmul_swiglu_quant_v2_tiling.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_v2/op_host/grouped_matmul_swiglu_quant_v2_fusion_tiling.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_weight_nz_tensor_list/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_weight_nz_tensor_list/grouped_matmul_swiglu_quant_torch_adpt.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_weight_nz_tensor_list/op_host/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_weight_nz_tensor_list/op_host/grouped_matmul_swiglu_quant_weight_nz_tensor_list.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_weight_nz_tensor_list/op_host/grouped_matmul_swiglu_quant_weight_nz_tensor_list_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_weight_nz_tensor_list/op_host/grouped_matmul_swiglu_quant_weight_nz_tensor_list_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_weight_nz_tensor_list/op_host/grouped_matmul_swiglu_quant_weight_nz_tensor_list_proto.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_weight_nz_tensor_list/op_host/grouped_matmul_swiglu_quant_weight_nz_tensor_list_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_weight_nz_tensor_list/op_host/grouped_matmul_swiglu_quant_weight_nz_tensor_list_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_weight_nz_tensor_list/op_host/op_api/aclnn_grouped_matmul_swiglu_quant_weight_nz_tensor_list.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_weight_nz_tensor_list/op_host/op_api/aclnn_grouped_matmul_swiglu_quant_weight_nz_tensor_list.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_weight_nz_tensor_list/op_host/op_api/grouped_matmul_swiglu_quant_weight_nz_tensor_list.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_weight_nz_tensor_list/op_kernel/grouped_matmul_swiglu_quant_weight_nz_tensor_list.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_weight_nz_tensor_list/op_kernel/grouped_matmul_swiglu_quant_weight_nz_tensor_list.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_weight_nz_tensor_list/op_kernel/grouped_matmul_swiglu_quant_weight_nz_tensor_list_split_ws.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/grouped_matmul_swiglu_quant_weight_nz_tensor_list/op_kernel/grouped_matmul_swiglu_quant_weight_nz_tensor_list_utils.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/gmm/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding_meta.cpp
  role: constraint
created_at: '2026-11-03T05:09:21Z'
updated_at: '2026-11-03T05:44:00Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---
# vLLM Ascend GMM与SwiGLu融合族：接口门禁、分片workspace与混合核执行

## 适配任务与版本边界

新模型将GMM1、反量化、SwiGLu及再次量化融合后，出现shape拒绝、专家映射错误、零输入异常或图内缓冲复用问题时，先识别实际入口与选中模板。本卡接续[普通W4A8加载与活动权重](vllm_ascend_w4a8_moe_weight_contract.md)，不重新定义checkpoint处理；[MXFP4权重](vllm_ascend_mxfp4_weight_reload_contract.md)及[SiTU](vllm_ascend_situ_quant_host_contract.md)也不与整数SwiGLu混用。

固定Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2。49个本族新来源及5份已有W4A8 owner的adapter/API/L0/tiling/fusion来源均已全文阅读，保留共享来源原owner。此前6份Device先做同族差异投影，随后逐份补读完整技术体并核对差异；它们现在有实际全文证据，不再以未显示模板正文充当覆盖。精确SHA与范围随摄取表记录。

本文提供框架集成、内存和执行差异知识，不是完整CV Operator。950的Cgmct kernel/block/scheduler、CANN matmul与向量原语、生成ACLNN/运行时及未展开模板仍待闭合；未构建、运行测试、模型、NPU、图或性能实验，保持draft、空平台、framework=vllm部分Scope。

## 同名接口的能力不能合并

| 路线 | 所读实际门禁 | 输出与分组 |
| --- | --- | --- |
| V1 A8W8 | INT8 x；INT8权重storage必须NZ；weight_scale为FP32/FP16/BF16 | INT8 `[M,N/2]`、FP32 `[M]`；groupList为累计边界 |
| V1 A8W4 MSD | INT8 x、INT4权重或INT32 packed容器；UINT64 weight_scale；辅助矩阵参与重建 | 相同INT8/FP32输出；per-channel或K分组scale |
| V2 DAV_2201 handler | 在上述基础上区分A8W4与A4W4、单聚合Tensor与专家TensorList | group_list_type=0累计、1计数由相应tiling/Device解释；A4W4可有smoothScale |
| V2 DAV_3510 handler | 单份weight及scale列表；模式0 per-token或2 MX，dequant_mode必须等于quant_mode；拒绝NZ | per-token为FP32 scale；MX为E8M0 `[M,ceil((N/2)/64),2]` |

V1校验N为偶数且N≤10240；K在A8W8要求小于65536、A8W4小于20000，等于上界也拒绝。这里N是SwiGLu前宽度，不能把错误日志中的“after halve”当成放宽一倍的依据。README列ND/NZ、更多输出和未来bias/offset公式，但当前OpDef、ACLNN及模板共同决定真实可走组合；注册列出某dtype也不代替接口校验。

V2普通API以当前NpuArch选择DAV_2201或DAV_3510 handler，无匹配项返回参数不合法；SOC注册表不等于本卡全硬件验证。950 handler禁止非空weightAssistMatrix、bias、smoothScale及tuningConfig；MX只接受FP8×FP8或FP4×FP4，per-token接受INT8同型、HiFloat8同型或E4/E5交叉组合。MX要求两类scale均E8M0；per-token x_scale为FP32，INT8权重scale可FP16/BF16/FP32，FP8/HiFloat8权重scale为BF16/FP32。FP4要求K为偶数且不等于2，FP4输出还要求N≥4且被4整除。

950 MX的weight/scale为`[E,K,N]`与`[E,ceil(K/64),N,2]`，转置时对应`[E,N,K]`与`[E,N,ceil(K/64),2]`；x_scale为`[M,ceil(K/64),2]`。权重和scale必须具有一致转置模式，x/x_scale不接受一般转置。MX要求groupList长度等于E；per-token的相应shape函数不同，不能把MX专门校验当成全部模式的共同保证。

## Torch包装、WeightNzV2与descriptor副作用

当前自定义Torch adapter总是先按weight_scale首份尾宽分配INT8输出和FP32行scale，再调用WeightNzV2。它没有把quant_dtype及transpose_weight传给ACLNN；不能以更底层950原生模式的能力宣称这个自定义包装已开放FP8/MX输出。

还需区分两段转发：普通V2 API的builder显式SetQuantAttr及SetBias；WeightNzV2的builder没有SetQuantAttr、SetBias或SetTransposeAttr，虽然函数签名带quantMode及bias。后者传给handler的这些字段仍为ParamsBase默认quantMode=0、quantDtype=0、bias=nullptr、transposeWeight=false，不能由adapter参数存在推导handler已收到。部分handler后续还会从stride重新识别转置，这不等于遗漏字段已被完整补回。

WeightNzV2会在完整handler校验之前原位改ACL Tensor的storageShape/storageFormat及部分viewFormat：单Tensor按groupList专家数、首份scale和x推导5维NZ，列表按每份推导4维NZ。它没有重排真实字节。packed INT32→INT4处理也会将逻辑宽放大8倍并修改dtype；V2对末两轴转置布局还改选扩展轴、stride及NZ storageShape，INT64 scale描述符改为UINT64。这里均不是数值重新量化或通用格式转换。

调用者应预先保证列表非空、每份weight/scale/辅助矩阵对应、实际字节和view/storage一致。旧handler部分循环反复检查第0份A8W8权重，format检查也先看第0份，不能把参数校验成功当成所有专家异构布局均已验证。V1还有进程级isEnableWeightAssistanceMatrix/dequantMode变量，本函数没有为每次调用重置它们；混合调用、并发和重用时的状态隔离未验证，不假设每个请求都等于首次调用。

V2 Device的动态TensorList参数不是直接权重地址：GetTensorAddr读取首个uint64偏移，移到其指针表再按expert索引取实际GM地址。聚合与列表通过isSingleTensor选择偏移及scale/辅助矩阵地址；不能用一个普通连续Tensor裸指针替代此元数据协议。MSD的每个K分组首次写FP16结果、后续累加；TP/EP重新组织列表时需保留每个专家和K组的对应关系。

## 分组有效行与量化数值

V1使用groupList末项作为有效M，逐专家用相邻累计边界差求行数；V2计数路线则求和并在扫描中构造累计位置。Host主要检查长度、维度及shape，不读取并完整证明设备上counts非负、累计单调、总和不超容量。调用方必须保持专家顺序和有效行边界。README明确未覆盖的输出容量尾部不更新、不初始化；这不是全零padding，不能直接交后续GMM。

MSD前处理将INT8激活拆成floor(x/16)的高4位和低4位减8的有符号分量，分别写入交替workspace；中间Cube按K分组scale计算两份FP16结果。后处理先以高结果×16加低结果重建，再加weight assistance matrix，再乘该行x_scale，之后才SwiGLu和动态INT8量化。辅助矩阵因此不等于在最终反量化结果上直接追加的普通bias，不能调整其顺序或套SiTU的bias合同。

A4W4没有MSD激活预处理或辅助矩阵相加；Cube直接消费INT4 x，后处理将FP16累加结果转FP32、乘token scale、SwiGLu，再可选乘smoothScale，最后量化。smoothScale可为每专家一个值`[E]`或每专家每输出通道`[E,N/2]`；二维分支逐通道GetValue/SetValue，记录了额外工作但未证明实际瓶颈。不能向A8W8/A8W4传同一smoothScale后期待自动忽略或相同数学。

limited/swigluLimit为0时不clamp；正值在所读普通A8W8及V2后处理里将右半夹到[-limit,limit]、左半只做上限截断，再按实际SwiGLu参数顺序执行。V1 MSD后处理没有对应clamp步骤，不把它和V2视作逐位等价。SiTU的beta与linear_beta不是此处的SwiGLu limit。

所读V1普通/MSD及V2 A4W4/key3动态量化取absmax/127，再除scale，没有SiTU K3那样scale≤0置1的保护；零行数与全零数值是不同边界。V1通用cast经FP32→FP16→INT8的RINT，并对局部偏移0或16 mod32分别处理；key3则经INT32 RINT、FP16 ROUND、INT8 TRUNC。任意偶数宽、尾部对齐、零scale与NaN/Inf仍需验证，不用Host放行替代数值参考，也不把这条观察推广到未读Cgmct epilogue。

## workspace、UB与混合核调度

V1普通A8W8的用户workspace按64MiB预算计算mLimit，超过2×mLimit容量选key1分片，否则key0；另加16MiB系统空间。MSD的mLimit按半份预算除以`K+4N`计算，分别保留双份拆分激活及双份两行FP16结果。V2 Base为A4W4改用每行2N字节FP16结果，无MSD激活区；不能统一按INT32 `[M,N]`估显存。

V2 INT8 fusion选key3，Host workspace为`4*M*N+20MiB`，UB行因子按N<4600、4600≤N<8192及其余分别取4、2、1。Base只接受INT4权重，key2为MSD，A4W4非转置/转置选key4/5；这些key与950模板key不是同一编码空间。Host模板优先级还受平台是否报告BF16 L1-to-BT intrinsic控制，不能只从函数名V2推断路径。

UB按各阶段分别核对。MSD前处理有输入、两份INT4、FP16及复用FP32临时区；后处理容量约束按`8.5*row*N+4*align8(row)+6N+64`估算。A4W4的Host把首项系数改4.5，实际后处理不分配辅助矩阵队列。SwiGLu/归约临时区、scale行对齐及队列深度不能只用输出INT8字节数替代。

MSD调度先发第0轮前处理，再令第n轮Cube、第n+1轮前处理与第n−1轮后处理交错，两个workspace按奇偶切换；A4W4去掉前处理，仍交错Cube与上一轮后处理。TPipe Reset/Destroy和SyncAll必须与旧轮次资源最后使用对应，不能提前复用workspace或合并缓冲而忽略这些顺序。

V2 key3采用另一协议：Cube通过PIPE_FIX发送0x8，Vector等待后再读GM结果；Vector即使本轮无有效行也进入相应等待及SyncAll。每14轮Vector发0x9、Cube等待作为反向节流。无活跃行核不等于可删除同步参与。V1普通先Cube完成再Vector，split-workspace另有MTE3_MTE2、V_MTE3及跨轮SyncAll。V1构建开cce-auto-sync，V2明确关；不能以复制V1屏障或改编译开关代替V2同步合同。

V2 A4W4的singleN调优要求正tuning值、per-channel、足够N并限定NZ，按任务占用率0.95目标搜索；读取tuningConfig的代码要求元素数大于1才取首项。还尝试在L1容纳全部A、必要时减baseM。这是固定源码启发式，不是吞吐或精度保证，不能把单元素配置“已传入”当成已启用。

950入口临时将overflow控制位设0并在末尾恢复；仅实例化不转置A、可转置B的组合。per-token中间DequantType由1→FP16、27→BF16、其余→FP32分派，INT8输入的Cube累加为INT32，其余为FP32。Cgmct还接收rowLen、ubAvail及workspace；这些wrapper已读，内部完整tile、epilogue、跨核同步与数值闭包仍待后续来源，不能继承2201的资源公式或零scale结论。

## Agent应记录与验证的证据

先记录实际Python→Torch→ACLNN symbol、架构handler、每份Tensor的逻辑/storage shape及stride、packed dtype、dequant/quant属性、group编码与有效M，再记录选中tiling key、baseM/N/K、mLimit、workspace字节和UB行因子。遇到拒绝先修接口与布局，不通过改descriptor、丢scale/辅助矩阵或全零初始化掩盖上游错误。

用固定版本非零参考分别检查MSD重建、辅助矩阵顺序、clamp、smoothScale、全零和非对齐尾部，保留有效行掩码。之后验证图重放、并发、流/事件及双workspace的读者寿命，正确性通过才比较准备、GMM、激活量化、通信和端到端时间。本文没有真实设备精度、性能收益或所有硬件/模型支持结果。


## WeightNzTensorList是独立A8W8实现

本节追加全文阅读该专用目录16份来源及GMM根CMake，不将它混成前述V2 handler。Torch binding确实注册Tensor[] weight/weight_scale到PrivateUse1，Meta与adapter都从weight[0]逻辑第1维推N、分配INT8 `[M,N/2]`、FP32 `[M]` scale和`[M]` output_offset。列表必须非空；API能接受某种4D私有view，不证明该Torch/Meta的二维取宽假设也正确。

专用OpDef只注册ascend910b/ascend910_93，x/weight均INT8，不接受W4A8 packed INT32；weight_scale为FP32/FP16/BF16，x_scale在OpDef及Device均FP32。虽然ACLNN前置dtype白名单另列FP16/BF16 x_scale，Device仍把它解释为float指针；应取各层交集，不把前置放行当作cast已经发生。

### 列表对应、NZ描述符与未写输出

ACLNN从第一份weight_scale推N，要求N偶数、N/2<=4096、K<65536；每份weight逻辑可为`[K,N]`或私有view的`[N/32,K/16,16,32]`，对应scale必须`[N]`。groupList一维长度<=weight列表长度，x/x_scale/output/output_scale分别匹配M/K/N。它没有在取第0项前证明列表非空，也未先证明weight_scale列表长度与weight相同，调用者应显式保证两列表及group专家索引对应。

外层GetWorkspaceSize先要求每份weight storage rank4，再原位把StorageFormat设FRACTAL_NZ，二维view设ND、四维view设NZ，随后才做完整检查。此操作没有重排内存；原storage padding、维度、每份实际NZ内容和stride仍须正确。普通检查只从第一份storage format决定NZ放行，并不替所有专家证明物理布局。

x、x_scale、groupList经Contiguous，weight及weight_scale列表没有同样通用转换；各weight OriginalShape被设为当前ViewShape。L0分配两个中间输出，调用InferShape和AICore launcher，再ViewCopy到用户output/scale。bias、offset、outputOffset非空仅WARNING，根本没有转给L0或Device；Torch分配的output_offset因此未由该算子写入，不能当成有效量化zero point读取。空输出/group/scale在参数检查后可返回workspace0，不代表空weight列表能走安全空路径。

Device通过GetTensorAddr读取动态TensorList的首uint64偏移，再索引专家GM指针表；这与连续`[E,K,N]`裸buffer不同。TP/EP重新分片必须同时保留专家顺序、weight/scale子地址和group累计边界。groupList为prefix-sum，INT64值在若干Cube步骤窄化为INT32；需要单调、非负、末项有效M<=容量以及数值范围，Host没有读全部设备值证明这些条件。

### 双workspace与混合核调度

Host用MatmulApiTiling配置GM ND INT8 A、GM NZ INT8 B、GM ND INT32 C、无bias；baseM/N=128/256，Device静态配置singleM/N/K=128/512/7168、basicK128、stepKa/Kb4、depthA1/B1为8。所读MatmulImpl使用这些静态参数，不能只看Host TCubeTiling就假设所有Device调优值自动继承。

普通用户workspace预算256MiB；只有group数128、M>=16384且(K,N)为(2048,1536)/(4096,3072)时标isPreFill，改预算64MiB。mLimit=预算/(2*4*N)，总workspace为16MiB系统空间加`min(M,2*mLimit)*N*4`。M>2*mLimit选key1分片，否则key0，两者都设置batch schedule。这个prefill是固定shape白名单，不等于scheduler语义中的所有prefill请求。

key0先完成全部专家Cube工作，在SyncAll后由Vector反量化/激活量化；key1按mLimit在两块INT32 workspace间交替，追踪跨片expert起止和全局行偏移。isPreFill令允许领先轮数parallelNum=2，否则1；Cube复用前、Vector读取前及尾部按对应条件SyncAll，闲核也应保留同步参与。不能只因某核无有效行就删屏障，或把两块workspace合并成一块。

Vector侧每块分配深度1的INT32输出、FP32 channel scale、INT8输出、8行对齐scale队列，另固定1024个FP32 reduce workspace和32B cast scratch；TPipe Reset发生在分块资源重建。整行/UB行因子由Host CalRows及AscendC三个临时区查询估算，不应仅按INT8输出容量判断可装载。N尾部、maxProcessRowNum>0和DataCopy字段窄化需按实际shape验证。

### 数值和状态边界

Cube累加INT32转FP32，先乘每token FP32 x_scale，再按当前专家列表加载/转换channel scale。跨专家时更新scale，重复累计边界代表空专家；group扫描必须与实际有效行一致。随后右半夹[-limit,limit]、左半只截上限，再以源码参数顺序`SwiGLU(workspace,right,left,beta=1)`调用；激活具体左右数学仍应匹配实际AscendC版本，不能拿同名Python函数替代。

动态scale为每行amax/127，没有全零置1guard；FP32经FP16 RINT再INT8 RINT。cast helper只处理目的偏移0 mod32或16 mod32，其他偏移没有分支；中间SwiGLu DataCopy还按H/8整除搬运。因此接口N偶数的检查不足以证明所有任意偶数尾宽均正确，须覆盖H非16倍数、零/极值及NaN/Inf。output_offset未写与动态scale为0是两个不同问题。

入口声明MIX_AIC_1_2，cce-auto-sync明确off，先SetOverflow(1)却未在本入口恢复。复用至图或相邻kernel前须核对控制寄存器约定及外部运行时恢复；本次没有观察实际状态污染。weight仅单M块时设L2 bypass，split路径多M块再设normal，这是启发式而非性能收益证据。

本节已提炼这条专用路径的完整自有Host/Device源码；外部MatmulImpl、SwiGLu/量化基础API、生成executor及真实图/并发仍未作完整CV/VV生产或NPU验证。原V1/V2的来源owner和此前边界保留，本节不扩大整卡平台或verified状态。
