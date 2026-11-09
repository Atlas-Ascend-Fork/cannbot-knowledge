---
type: Guide
title: vLLM Ascend K2Q CSR：五阶段反向索引、MC/SIMT与scratch一致性
description: 把q2k转成按KV块分组的row_ptr/q_ind/slot时，核对Meta→Hist→RowPrefix→TilePrefix→Scatter顺序、concat/round-robin行号与local/global
  query坐标；解释MC/SIMT分组、32lane去重排名和scratch错配、容量、并发边界。
tags:
- task.implementation
- task.debugging
- topic.attention
- topic.model_adaptation
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/README.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_common/op_host/arch35/k2q_csr_tiling_arch35.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_common/op_host/arch35/k2q_csr_tiling_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_common/op_host/k2q_csr_tiling_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_common/op_kernel/arch35/k2q_csr_simt_common_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_common/op_kernel/arch35/k2q_csr_simt_hist_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_common/op_kernel/arch35/k2q_csr_simt_scatter_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_common/op_kernel/k2q_csr_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_common/op_kernel/k2q_csr_mc.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_common/op_kernel/k2q_csr_prefix.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_common/op_kernel/k2q_csr_scratch.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_common/op_kernel/k2q_csr_stage_meta.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_common/op_kernel/k2q_csr_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_hist/op_host/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_hist/op_host/k2q_csr_hist_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_hist/op_host/k2q_csr_hist_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_hist/op_host/k2q_csr_hist_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_hist/op_kernel/common/arch35/k2q_csr_simt_common_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_hist/op_kernel/common/arch35/k2q_csr_simt_hist_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_hist/op_kernel/common/arch35/k2q_csr_simt_scatter_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_hist/op_kernel/common/k2q_csr_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_hist/op_kernel/common/k2q_csr_mc.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_hist/op_kernel/common/k2q_csr_prefix.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_hist/op_kernel/common/k2q_csr_scratch.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_hist/op_kernel/common/k2q_csr_stage_meta.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_hist/op_kernel/common/k2q_csr_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_hist/op_kernel/k2q_csr_hist.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_hist/op_kernel/k2q_csr_hist_apt.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_meta/op_host/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_meta/op_host/k2q_csr_meta_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_meta/op_host/k2q_csr_meta_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_meta/op_host/k2q_csr_meta_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_meta/op_kernel/common/arch35/k2q_csr_simt_common_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_meta/op_kernel/common/arch35/k2q_csr_simt_hist_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_meta/op_kernel/common/arch35/k2q_csr_simt_scatter_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_meta/op_kernel/common/k2q_csr_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_meta/op_kernel/common/k2q_csr_mc.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_meta/op_kernel/common/k2q_csr_prefix.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_meta/op_kernel/common/k2q_csr_scratch.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_meta/op_kernel/common/k2q_csr_stage_meta.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_meta/op_kernel/common/k2q_csr_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_meta/op_kernel/k2q_csr_meta.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_meta/op_kernel/k2q_csr_meta_apt.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_row_prefix/op_host/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_row_prefix/op_host/k2q_csr_row_prefix_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_row_prefix/op_host/k2q_csr_row_prefix_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_row_prefix/op_host/k2q_csr_row_prefix_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_row_prefix/op_kernel/common/arch35/k2q_csr_simt_common_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_row_prefix/op_kernel/common/arch35/k2q_csr_simt_hist_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_row_prefix/op_kernel/common/arch35/k2q_csr_simt_scatter_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_row_prefix/op_kernel/common/k2q_csr_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_row_prefix/op_kernel/common/k2q_csr_mc.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_row_prefix/op_kernel/common/k2q_csr_prefix.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_row_prefix/op_kernel/common/k2q_csr_scratch.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_row_prefix/op_kernel/common/k2q_csr_stage_meta.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_row_prefix/op_kernel/common/k2q_csr_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_row_prefix/op_kernel/k2q_csr_row_prefix.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_row_prefix/op_kernel/k2q_csr_row_prefix_apt.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_scatter/op_host/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_scatter/op_host/k2q_csr_scatter_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_scatter/op_host/k2q_csr_scatter_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_scatter/op_host/k2q_csr_scatter_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_scatter/op_kernel/common/arch35/k2q_csr_simt_common_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_scatter/op_kernel/common/arch35/k2q_csr_simt_hist_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_scatter/op_kernel/common/arch35/k2q_csr_simt_scatter_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_scatter/op_kernel/common/k2q_csr_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_scatter/op_kernel/common/k2q_csr_mc.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_scatter/op_kernel/common/k2q_csr_prefix.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_scatter/op_kernel/common/k2q_csr_scratch.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_scatter/op_kernel/common/k2q_csr_stage_meta.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_scatter/op_kernel/common/k2q_csr_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_scatter/op_kernel/k2q_csr_scatter.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_scatter/op_kernel/k2q_csr_scatter_apt.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_tile_prefix/op_host/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_tile_prefix/op_host/k2q_csr_tile_prefix_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_tile_prefix/op_host/k2q_csr_tile_prefix_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_tile_prefix/op_host/k2q_csr_tile_prefix_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_tile_prefix/op_kernel/common/arch35/k2q_csr_simt_common_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_tile_prefix/op_kernel/common/arch35/k2q_csr_simt_hist_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_tile_prefix/op_kernel/common/arch35/k2q_csr_simt_scatter_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_tile_prefix/op_kernel/common/k2q_csr_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_tile_prefix/op_kernel/common/k2q_csr_mc.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_tile_prefix/op_kernel/common/k2q_csr_prefix.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_tile_prefix/op_kernel/common/k2q_csr_scratch.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_tile_prefix/op_kernel/common/k2q_csr_stage_meta.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_tile_prefix/op_kernel/common/k2q_csr_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_tile_prefix/op_kernel/k2q_csr_tile_prefix.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_tile_prefix/op_kernel/k2q_csr_tile_prefix_apt.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/k2q_csr/k2q_csr_torch_adpt.h
  role: primary
created_at: '2026-11-03T05:16:16Z'
updated_at: '2026-11-03T05:16:16Z'
platforms: []
aliases:
- npu_k2q_csr
- K2qCsrPipelineMc
- K2qCsrStageMeta
- K2qCsrSimtHist
- K2qCsrSimtScatter
- K2qCsrRowPrefixKernel
- K2qCsrTilePrefixKernel
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend K2Q CSR：五阶段反向索引、MC/SIMT与scratch一致性

## 用于稀疏Attention的反向邻接表适配

当模型已有按query选KV块的`q2k[H,T,topk]`，而下游需要按KV块枚举query时，本族生成CSR反向关系。它只转换索引，不计算Attention score、不读取K/V、不执行softmax，也不把逻辑块映射为物理页。模型调用实例见[MiniMax-M3稀疏后端](vllm_ascend_minimax_m3_sparse_backend_contract.md)的Split KV prefill；不能据这个用例推导全部模型都应使用相同order或query坐标。

固定Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，完整阅读整个90路径族：45份唯一正文，9个common文件分别在原目录及五个stage目录各有一份逐字同SHA副本。重复副本按完整内容相等复用，保留各编译入口；C++使用去注释/空白投影审阅，README/CMake全文读取。没有执行上游、构建、UT、JIT或NPU；保持draft和空平台。本卡是固定执行链的集成与诊断知识，未建立外部aclnn执行器、SDK或真实平台的完整Operator验证。

## 输入与输出坐标必须共同冻结

| 对象 | 真实协议 | 适配要点 |
|---|---|---|
| q2k | INT32 `[H,T,topk]`，head-major，值为请求内逻辑KV块ID | 负值及超出有效row map的值被忽略；重复ID仍是多条边，slot保留各自来源槽 |
| cu_seqlens | INT32 `[B+1]`，Q前缀，逐请求token归属由相邻区间确定 | 不是SparseAttentionScore的逐请求长度数组；首零/终点T/单调和请求数需由caller保证 |
| cu_block_lens | INT32 `[B+1]`，逐请求逻辑KV块数前缀 | 末值为total_rows，各差值最大值为max_kv；不是token长度或物理页表 |
| row_ptr | INT32 `[H,total_rows+1]` | 每个head从0开始的行边界；最后元素为该head有效边总数，不同head不累计到一起 |
| q_ind、slot | INT32 `[H,T*topk]`，先填-1 | 每行只消费row_ptr规定的区间，尾部容量保持-1；slot是原query的TopK槽号，不是物理cache slot |

`order_method=0`按batch顺序拼接各请求KV块，row为`cu_block_lens[b]+logicalBlock`。`order_method=1`按level轮转：先所有含block0的请求，再所有含block1的请求，依次生成紧凑row。rowMap的存储仍为`[B,max_kv]`，无效尾格为-1。不能改变order后继续复用按另一种行号解释的下游metadata。

`q_global_offset=0`通常写`qAbs-cu_seqlens[b]`，为请求内query编号；非零写全局qAbs。B1/concat快速路径直接写qAbs，依赖规范首零前缀使两者等价。不要让q_ind的局部/全局含义与下游假设脱节，也不能把-1改成0，否则会制造block0关联。

## 五个独立kernel构成同一事务

Torch adapter先检查三个输入defined、INT32及q2k三维，order只能0/1；把输入contiguous。它没有完整验证三个tensor同设备、两组cu长度一致、单调性/首尾值、显式统计与实际设备值一致或所有int32容量。若total_rows或max_kv任一为负，就把cu_block_lens复制CPU并重算两项；两者都显式非负时跳过该D2H，但这是一项caller承诺，不能传猜测值来换取性能。

| 顺序 | 生产/消费 | 并行分配 |
|---|---|---|
| Meta | cu前缀→tokenBatch、rowMap，并清零rowCounts | 仅core0，先完成后续方可依赖 |
| Hist | q2k→每group/head/row计数tileCounts；累加rowCounts | 每group一个AIV，每个group覆盖连续Q区间、内部遍历head |
| RowPrefix | rowCounts→每head row_ptr排他前缀和 | 按head分核 |
| TilePrefix | row_ptr+tileCounts→每group/head/row绝对写入起点absBase | 按row区间分核，group顺序累计 |
| Scatter | 重读q2k，按absBase及组内cursor输出q_ind/slot | MC或950 SIMT，必须与Hist使用相同group划分 |

各stage均为AIV_ONLY，输出scratch参数在Device中常被忽略，实际原位更新输入scratch。OpDef的AutoContiguous和公开输出别名不能替代对生成aclnn接口、原位别名和跨stream依赖的实核。adapter按上述顺序`EXEC_NPU_CMD`，本族没有跨stream外部事务锁；同一scratch不能由两个请求并发重用。

## Scratch和分组是跨阶段ABI

设`R=total_rows`，`G=numGroups`。持久scratch先存`B*max_kv`个rowMap INT32，再存T个tokenBatch，后面为`G*H*R`个tileCounts、同大小absBase，以及`H*R`个rowCounts；adapter用max(H,1)、max(R,1)避免零分配，实际字节还需乘4。另分配row_ptr与两份H*T*topk输出，并有逐stage系统workspace。Host每stage申请16MiB加`4*(B*max_kv+T)`；这不是全部显存峰值，也不是设备核的UB预算。

MC的G取min(T,AIV数)，T非正时1；每组连续ceil(T/G)个query。SIMT按至少约256 query一组的策略限制G，重新按ceil划分，通常更少。实际AIV查询失败报错，不静默假定32/64。SIMT只在Host识别SoC ASCEND950且请求use_simt时保留；其他SoC强制MC。源码注册910b、910_93、950仅是编译分支声明，不能代替本机SDK/硬件成功。

**当前静态一致性风险必须在新接入时先解决/验证：** adapter按原始use_simt选择G并分配scratch，但Meta阶段固定useSimt=0，使用MC的G计算rowCounts地址；950 Hist/Scatter又可使用SIMT G。两种G不同时，Meta清零rowCounts的位置可能与后续消费和adapter容量不一致。非950把请求SIMT降为MC也不会反向调整adapter已分配的G。不能仅因Host允许fallback就称scratch自动兼容；应记录各stage真实G、偏移、容量，并在匹配的入口上核对多query、多core情况。本次没有运行越界复现。

Meta还在Device重读cu_block_lens求实际max_kv，更新自己的rowMap行宽；其他stage和scratch分段仍用Host显式值。若caller显式统计错误，这一步不会整体修复分配和ABI，反而可能形成不同rowMap步长或覆盖tokenBatch。必须保证显式max_kv和total_rows等于前缀的真实统计，不能把“Device重算”当校验或容量自动扩展。

## MC与SIMT保持边语义，但资源和分支不同

MC在UB维护整行hist/cursor，按Q tile复制q2k。B1/concat直接把合法值当row，省rowMap和tokenBatch加载，并启用8192边双Q buffer；其他情况使用2048边。scatter批量缓存64个位置，q值/slot的UB槽按8个INT32间隔布置，再执行逐点DataCopyPad；局部PipeBarrier和MTE顺序是复用前提。Hist在G>1时通过AtomicAdd汇总rowCounts，G1直接copy；前置清零不可删。

SIMT hist按线程跨步遍历边，用GM原子计数；scatter把连续Q分到最多4个warp（每warp32 lane），先统计各warp的row数量，再形成warp前缀。TopK≤32时同query每lane一个槽，经shuffle比较同row、位掩码popcount求重复ID的排名，由leader推进cursor；TopK>32改为每warp lane0串行遍历。不能把≤32的warp并行特性外推到任意TopK，也不能去掉重复ID认为等价。

SIMT默认THREAD_NUM1024，FPGA分支256；活跃scatter warp最多4，其余线程仍参加清零和ThreadBarrier。partBase按row数缩减warp数量以期控制在96KiB，但降到1个warp后不继续拒绝更大的row表。MC同样分配多个完整R长度UB buffer；Host的CalcTileEdges有UB估算，MC实际又以固定2048/8192覆盖tile策略。它们不构成任意R/T/TopK的资源安全证明，需要按实际分支计算总UB、prefix两份R向量及输出计数的int32上限。

MC按group、query、slot顺序排放，SIMT用warp前缀与同row槽排名保留边的来源。任务分组和具体路径变化时，下游应以row_ptr/q_ind/slot表达的邻接关系为合同，数值或布局测试若要求完全逐元素排序相同还需专门证明。正负越界ID过滤不能代替cu/tokenBatch合法性：MC通路对bi的防护与SIMT不相同，未初始化或错误cu导致的token归属不能视为已安全处理。

## 构建副本、诊断顺序与尚未核清的范围

父CMake在configure时把common同步到五stage的op_kernel/common，并移除opc src_copy的binary*.done戳以防旧空目录缓存；修改原common后必须确保实际编译副本一致。本固定快照中九组副本SHA完全相等，但未来版本/构建目录不能凭同名推导相同。各stage选不同opFile，950的Hist/Scatter apt显式分流SIMT，Meta/Prefix仍走其公共实现；不能只安装其中一个stage就认为整链可调用。

模型适配先固定q2k轴、cu前缀、order与q_global_offset；再核验Host/Meta/Hist/Prefix/Scatter一致的G和scratch offsets；随后覆盖空T/空R、变长batch、重复ID、-1、非零非法ID、多query/多core、TopK跨32、两种order与两种query坐标。性能诊断另记录D2H、contiguous副本、五次launch、R/G决定的scratch和UB、原子冲突与scatter写粒度。这里只给源码机制，没有吞吐或时延收益值。

实际Python调用方、外部aclnn executor实现、生成API的原位别名、实机线程/缓存一致性以及直接UT运行未在此90路径族内闭合；上述静态风险不应被当作已复现缺陷或已修复。已有MiniMax-M3卡负责模型调用及Split KV边界，本卡新增底层CSR整链知识，不重分配其原owner。
